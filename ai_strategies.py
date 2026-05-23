import random
from copy import deepcopy


def _format_factor(label, value):
    return f"{label} {value:+.0f}"


def _top_factor_strings(factors, limit=3):
    ranked = sorted(factors, key=lambda item: abs(item[1]), reverse=True)
    return [_format_factor(label, value) for label, value in ranked[:limit]]


class BaseAIStrategy:
    """Strategy interface for computer-controlled turns."""

    name = "base"

    def choose_move(self, game, player, legal_moves, capture_trace=False):
        raise NotImplementedError

    def buy_stocks(self, game, player):
        raise NotImplementedError

    def explain_stock_plan(self, game, player, limit=3):
        return None


class BeginnerAIStrategy(BaseAIStrategy):
    """Behavior-parity strategy: random move and conservative broad buying."""

    name = "beginner"

    def choose_move(self, game, player, legal_moves, capture_trace=False):
        shuffled = list(legal_moves)
        random.shuffle(shuffled)
        selected = shuffled[0]

        if capture_trace:
            game.ai_last_trace = {
                "strategy": self.name,
                "selected_move": selected,
                "selection_mode": "random",
                "selected_factors": ["random selection +0"],
                "ranked_moves": [
                    {
                        "move": move,
                        "score": 0.0,
                        "factors": ["random selection +0"],
                    }
                    for move in shuffled
                ],
            }

        return selected

    def buy_stocks(self, game, player):
        purchases = []

        for symbol in sorted(game.active_companies.keys()):
            company = game.active_companies[symbol]
            max_affordable = player.cash_on_hand // company.share_price
            if max_affordable <= 0:
                continue

            shares_to_buy = min((max_affordable // 2) + 1, 20)
            if shares_to_buy <= 0:
                continue

            player.portfolio[company.symbol] += shares_to_buy
            player.cash_on_hand -= shares_to_buy * company.share_price
            purchases.append((company.name, shares_to_buy))

        if purchases:
            name, shares = purchases[-1]
            game.last_action = f"Autopilot purchased {shares} shares of {name}"
        else:
            game.last_action = "Autopilot skipped stock purchases"

    def explain_stock_plan(self, game, player, limit=3):
        active_symbols = sorted(game.active_companies.keys())
        if not active_symbols:
            return "Stock logic: no active companies to buy this turn."

        samples = []
        for symbol in active_symbols[:limit]:
            company = game.active_companies[symbol]
            max_affordable = int(player.cash_on_hand // company.share_price)
            target = min((max_affordable // 2) + 1, 20) if max_affordable > 0 else 0
            samples.append(f"{symbol} (${company.share_price:,} -> target about {target} shares)")

        return (
            "Stock logic: beginner buys broadly in alphabetical order, usually around half of what is "
            "affordable for each company (cap 20), without reserve tuning. "
            f"Examples this turn: {', '.join(samples)}."
        )


class IntermediateAIStrategy(BaseAIStrategy):
    """Heuristic strategy focused on growth, favorable mergers, and dividends."""

    name = "intermediate"

    def choose_move(self, game, player, legal_moves, capture_trace=False):
        best_move = legal_moves[0]
        best_score = float("-inf")
        ranked = []
        factors_by_move = {}

        for move in legal_moves:
            if capture_trace:
                score, factors = self._score_move(game, player, move, explain=True)
                factors_by_move[move] = _top_factor_strings(factors)
                ranked.append((move, score))
            else:
                score = self._score_move(game, player, move)
            if score > best_score:
                best_score = score
                best_move = move

        # Preserve some unpredictability so it doesn't feel robotic.
        selection_mode = "best-score"
        selected_move = best_move
        if random.random() < 0.2:
            selected_move = random.choice(legal_moves)
            selection_mode = "random-override"

        if capture_trace:
            if not ranked:
                ranked = [(move, self._score_move(game, player, move)) for move in legal_moves]
            ranked_entries = sorted(ranked, key=lambda item: item[1], reverse=True)
            game.ai_last_trace = {
                "strategy": self.name,
                "selected_move": selected_move,
                "selection_mode": selection_mode,
                "selected_factors": factors_by_move.get(selected_move, []),
                "ranked_moves": [
                    {
                        "move": move,
                        "score": score,
                        "factors": factors_by_move.get(move, []),
                    }
                    for move, score in ranked_entries
                ],
            }

        return selected_move

    def _score_move(self, game, player, move, explain=False):
        nsew = game.map.nsew(move)
        score = 0.0
        factors = []

        def add_factor(label, value):
            nonlocal score
            score += value
            factors.append((label, value))

        if game.touches_multiple_companies(nsew):
            add_factor("merger", 1300)
            companies = [game.active_companies[s] for s in nsew.companies]
            winner, loser = game._select_merger_pair(companies)
            add_factor("winner stake", player.portfolio.get(winner.symbol, 0) * 25)
            add_factor("loser stake", player.portfolio.get(loser.symbol, 0) * 15)
            add_factor("opponent winner stake", -sum(
                p.portfolio.get(winner.symbol, 0)
                for p in game.players
                if p is not player
            ) * 4)
        elif game.touches_exactly_one_company(nsew):
            symbol = next(iter(nsew.companies))
            add_factor("expansion", 900)
            add_factor("owned shares", player.portfolio.get(symbol, 0) * 10)
            add_factor("company size", game.active_companies[symbol].outposts * 8)
        elif game.can_form_new_company(nsew):
            add_factor("new company", 700)
        else:
            add_factor("isolated outpost", 120)

        add_factor("adjacent stars", nsew.stars * 500)
        add_factor("adjacent outposts", nsew.outposts * 100)

        if explain:
            return score, factors
        return score

    def buy_stocks(self, game, player):
        purchases = []
        reserve = max(500, int(player.net_worth * 0.1))

        while True:
            ranked = self._rank_affordable_companies(game, player, reserve)
            if not ranked:
                break

            _, company = ranked[0]
            player.portfolio[company.symbol] += 1
            player.cash_on_hand -= company.share_price
            purchases.append(company.symbol)

            if len(purchases) >= 30:
                break

        if purchases:
            counts = {}
            for symbol in purchases:
                counts[symbol] = counts.get(symbol, 0) + 1
            summary = ", ".join(f"{qty}x {symbol}" for symbol, qty in sorted(counts.items()))
            game.last_action = f"Computer purchased: {summary}"
        else:
            game.last_action = "Computer skipped stock purchases"

    def _rank_affordable_companies(self, game, player, reserve):
        ranked = []

        for symbol in sorted(game.active_companies.keys()):
            company = game.active_companies[symbol]
            if player.cash_on_hand - company.share_price < reserve:
                continue

            score = self._score_company_purchase(game, player, company)
            ranked.append((score, company))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return ranked

    def _rank_affordable_companies_explained(self, game, player, reserve):
        ranked = []

        for symbol in sorted(game.active_companies.keys()):
            company = game.active_companies[symbol]
            if player.cash_on_hand - company.share_price < reserve:
                continue

            score, details = self._score_company_purchase(game, player, company, explain=True)
            ranked.append((score, company, details))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return ranked

    def _score_company_purchase(self, game, player, company, explain=False):
        dividend_value = 0.05 * company.share_price
        owned = player.portfolio.get(company.symbol, 0)
        expansion_chances = 0

        for coord in game.map.empty_squares():
            nsew = game.map.nsew(coord)
            if nsew.companies == {company.symbol}:
                expansion_chances += 1

        split_proximity = max(0, company.share_price - 2600) / 400
        concentration_penalty = owned * 6

        total_score = (
            dividend_value
            + (expansion_chances * 40)
            + (owned * 10)
            + (split_proximity * 120)
            - concentration_penalty
        )

        if explain:
            return total_score, {
                "share_price": company.share_price,
                "dividend_signal": dividend_value,
                "expansion_chances": expansion_chances,
                "expansion_signal": expansion_chances * 40,
                "owned": owned,
                "ownership_signal": owned * 10,
                "split_signal": split_proximity * 120,
                "concentration_penalty": concentration_penalty,
            }

        return total_score

    def explain_stock_plan(self, game, player, limit=3):
        reserve = max(500, int(player.net_worth * 0.1))
        ranked = self._rank_affordable_companies_explained(game, player, reserve)

        if not ranked:
            return (
                f"Stock logic: keep about ${reserve:,} in reserve; no company met affordability "
                "plus reserve constraints this turn."
            )

        explanations = []
        for score, company, details in ranked[:limit]:
            explanations.append(
                f"{company.symbol} (${details['share_price']:,}, score {score:.0f}): "
                f"dividend {details['dividend_signal']:.0f}, expansion lanes {details['expansion_chances']} "
                f"(+{details['expansion_signal']:.0f}), owned {details['owned']} "
                f"(+{details['ownership_signal']:.0f}), split pressure +{details['split_signal']:.0f}, "
                f"concentration -{details['concentration_penalty']:.0f}"
            )

        return (
            f"Stock logic: keeps about ${reserve:,} in reserve and ranks companies by value signals. "
            f"Top priorities: {'; '.join(explanations)}."
        )


class AdvancedAIStrategy(IntermediateAIStrategy):
    """One-ply tactical strategy with opponent reply suppression."""

    name = "advanced"

    def choose_move(self, game, player, legal_moves, capture_trace=False):
        best_move = legal_moves[0]
        best_score = float("-inf")
        ranked = []
        details_by_move = {}

        for move in legal_moves:
            if capture_trace:
                score, details = self._one_ply_score(game, player, move, explain=True)
                ranked.append((move, score))
                details_by_move[move] = details
            else:
                score = self._one_ply_score(game, player, move)
            if score > best_score:
                best_score = score
                best_move = move

        if capture_trace:
            if not ranked:
                ranked = [(move, self._one_ply_score(game, player, move)) for move in legal_moves]
            ranked_entries = sorted(ranked, key=lambda item: item[1], reverse=True)
            selected_details = details_by_move.get(best_move, {})
            base_factors = selected_details.get("base_factors", [])
            components = selected_details.get("components", {})

            component_factors = [
                ("net worth delta", components.get("immediate_delta", 0.0) * 1.4),
                ("opponent pressure", -components.get("opponent_best", 0.0) * 0.5),
            ]

            game.ai_last_trace = {
                "strategy": self.name,
                "selected_move": best_move,
                "selection_mode": "one-ply",
                "selected_factors": _top_factor_strings(base_factors + component_factors),
                "ranked_moves": [
                    {
                        "move": move,
                        "score": score,
                        "factors": _top_factor_strings(
                            details_by_move.get(move, {}).get("base_factors", [])
                        ),
                    }
                    for move, score in ranked_entries
                ],
                "selected_components": components,
            }

        return best_move

    def _one_ply_score(self, game, player, move, explain=False):
        if explain:
            base_score, base_factors = self._score_move(game, player, move, explain=True)
        else:
            base_score = self._score_move(game, player, move)
            base_factors = []

        try:
            simulated = deepcopy(game)
        except Exception:
            if explain:
                return base_score, {
                    "base_factors": base_factors,
                    "components": {
                        "base_score": base_score,
                        "immediate_delta": 0.0,
                        "opponent_best": 0.0,
                    },
                }
            return base_score

        try:
            simulated.display.display_new_company = lambda *args, **kwargs: None
            simulated.display.any_to_continue = lambda *args, **kwargs: None
            simulated.display.display_map = lambda *args, **kwargs: None
            simulated.display.display_two_for_one = lambda *args, **kwargs: None
            simulated.display.display_merger = lambda *args, **kwargs: None
            simulated.headless = True
            simulated.interactive = False

            player_index = next(
                idx
                for idx, p in enumerate(game.players)
                if p.name == player.name
            )
            sim_player = simulated.players[player_index]

            before_net_worth = sim_player.net_worth
            simulated.play_move(sim_player, move)
            simulated.pay_dividends(sim_player)
            immediate_delta = sim_player.net_worth - before_net_worth

            next_index = (player_index + 1) % len(simulated.players)
            opponent = simulated.players[next_index]

            opp_legal = simulated._get_legal_moves(simulated.map)
            opponent_best = max(
                self._score_move(simulated, opponent, opponent_move)
                for opponent_move in opp_legal
            )

            final_score = base_score + (immediate_delta * 1.4) - (0.5 * opponent_best)
            if explain:
                return final_score, {
                    "base_factors": base_factors,
                    "components": {
                        "base_score": base_score,
                        "immediate_delta": immediate_delta,
                        "opponent_best": opponent_best,
                    },
                }
            return final_score
        except Exception:
            if explain:
                return base_score, {
                    "base_factors": base_factors,
                    "components": {
                        "base_score": base_score,
                        "immediate_delta": 0.0,
                        "opponent_best": 0.0,
                    },
                }
            return base_score


def build_ai_strategy(difficulty):
    normalized = (difficulty or "beginner").strip().lower()
    if normalized == "intermediate":
        return IntermediateAIStrategy()
    if normalized == "advanced":
        return AdvancedAIStrategy()
    return BeginnerAIStrategy()
