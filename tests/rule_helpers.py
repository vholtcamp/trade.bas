from trade_objects import Company, OUTPOST, STAR


def place_outpost(game, coord):
    """Place an outpost on the board for deterministic setup."""
    game.map[coord] = OUTPOST


def place_star(game, coord):
    """Place a star on the board for deterministic setup."""
    game.map[coord] = STAR


def found_company(game, player, coord):
    """Create a company as if the given coordinate were the played founding square."""
    return Company(game, player, game.map.nsew(coord))


def play(game, player, coord):
    """Thin wrapper around play_move for concise tests."""
    game.play_move(player, coord)


def only_active_company(game):
    """Return the sole active company; caller should ensure there is exactly one."""
    return next(iter(game.active_companies.values()))


def all_companies_obey_price_quantum(game):
    """Invariant helper: every active company price aligns with its quantum."""
    return all(
        c.share_price % c.price_quantum == 0
        for c in game.active_companies.values()
    )

def force_company(game, player, center):
    """
    Test helper: force-create a real company at `center`
    using normal creation logic.
    """
    nsew = game.map.nsew(center)
    return Company(game, player, nsew)