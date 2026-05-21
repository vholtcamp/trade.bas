import random
from copy import deepcopy


class BaseAIStrategy:
    """Strategy interface for computer-controlled turns."""

    name = "base"

    def choose_move(self, game, player, legal_moves):
        raise NotImplementedError

    def buy_stocks(self, game, player):
        raise NotImplementedError


class BeginnerAIStrategy(BaseAIStrategy):
    """Behavior-parity strategy: random move and conservative broad buying."""

    name = "beginner"

    def choose_move(self, game, player, legal_moves):
        shuffled = list(legal_moves)
        random.shuffle(shuffled)
        return shuffled[0]

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


class IntermediateAIStrategy(BaseAIStrategy):
    """Heuristic strategy focused on growth, favorable mergers, and dividends."""

    name = "intermediate"

    def choose_move(self, game, player, legal_moves):
        best_move = legal_moves[0]
        best_score = float("-inf")

        for move in legal_moves:
            score = self._score_move(game, player, move)
            if score > best_score:
                best_score = score
                best_move = move

        # Preserve some unpredictability so it doesn't feel robotic.
        if random.random() < 0.2:
            return random.choice(legal_moves)
        return best_move

    def _score_move(self, game, player, move):
        nsew = game.map.nsew(move)
        score = 0.0

        if game.touches_multiple_companies(nsew):
            score += 1300
            companies = [game.active_companies[s] for s in nsew.companies]
            winner, loser = game._select_merger_pair(companies)
            score += player.portfolio.get(winner.symbol, 0) * 25
            score += player.portfolio.get(loser.symbol, 0) * 15
            score -= sum(
                p.portfolio.get(winner.symbol, 0)
                for p in game.players
                if p is not player
            ) * 4
        elif game.touches_exactly_one_company(nsew):
            symbol = next(iter(nsew.companies))
            score += 900
            score += player.portfolio.get(symbol, 0) * 10
            score += game.active_companies[symbol].outposts * 8
        elif game.can_form_new_company(nsew):
            score += 700
        else:
            score += 120

        score += nsew.stars * 500
        score += nsew.outposts * 100
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

    def _score_company_purchase(self, game, player, company):
        dividend_value = 0.05 * company.share_price
        owned = player.portfolio.get(company.symbol, 0)
        expansion_chances = 0

        for coord in game.map.empty_squares():
            nsew = game.map.nsew(coord)
            if nsew.companies == {company.symbol}:
                expansion_chances += 1

        split_proximity = max(0, company.share_price - 2600) / 400
        concentration_penalty = owned * 6

        return (
            dividend_value
            + (expansion_chances * 40)
            + (owned * 10)
            + (split_proximity * 120)
            - concentration_penalty
        )


class AdvancedAIStrategy(IntermediateAIStrategy):
    """One-ply tactical strategy with opponent reply suppression."""

    name = "advanced"

    def choose_move(self, game, player, legal_moves):
        best_move = legal_moves[0]
        best_score = float("-inf")

        for move in legal_moves:
            score = self._one_ply_score(game, player, move)
            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def _one_ply_score(self, game, player, move):
        base_score = self._score_move(game, player, move)

        try:
            simulated = deepcopy(game)
        except Exception:
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

            return base_score + (immediate_delta * 1.4) - (0.5 * opponent_best)
        except Exception:
            return base_score


def build_ai_strategy(difficulty):
    normalized = (difficulty or "beginner").strip().lower()
    if normalized == "intermediate":
        return IntermediateAIStrategy()
    if normalized == "advanced":
        return AdvancedAIStrategy()
    return BeginnerAIStrategy()
