Some notes on the computer thinking process and how this might impact your strategy.

---

## Computer Players

Computer opponents always choose from the same five legal moves offered to human players each turn. They have no hidden map information, no ability to preview future offers, and no ability to sell stock. The difference between difficulty levels is entirely in *how* they evaluate those choices.

### How moves are chosen

**Beginner** picks a move at random from the five legal options. No preference is given to any move type.

**Intermediate** scores each of the five legal moves and usually picks the highest-scoring one, with a 20% chance of choosing randomly instead (keeping it from being fully predictable). The scoring strongly favors moves that trigger mergers, with a bonus for owning shares in the surviving company and an additional boost for owning shares in the company being absorbed. Expanding an existing company scores next highest, with extra weight if the computer owns shares in it and if the company already covers a lot of ground. Founding a new company scores lower, and isolated outpost placements score lowest. Adjacent stars and outposts add meaningful bonuses on top of any base score.

**Advanced** uses the same core scoring as Intermediate but replaces the random override with a one-step simulation: for each candidate move, it plays out the move on a copy of the board, measures the immediate change to its own net worth, then estimates how strong the next opponent's best response would be. The final score rewards moves that increase immediate wealth while penalizing moves that leave an opponent with strong follow-up options. Advanced never randomizes.

### How stock is purchased

**Beginner** iterates through all active companies alphabetically and buys up to 20 shares in each, spending roughly half of what it could afford per company. It does not maintain a cash reserve and does not evaluate which companies are likely to grow.

**Intermediate** and **Advanced** share the same purchase logic. They always keep a cash reserve of at least 10% of their net worth (minimum $500) and buy one share at a time from the highest-ranked affordable company, repeating until no attractive option remains (or 30 shares have been purchased). Companies are ranked by a score that combines current dividend yield, the number of open expansion squares adjacent to that company, a bonus for proximity to the $3,000 split threshold, and a penalty for already owning a lot of the same stock (to discourage over-concentration).

### What this means for human players

- **Against Beginner**: the computer's moves are unpredictable but not strategic. Focus on your own position. It will spread its money broadly across all companies rather than targeting the most valuable ones, so early ownership in growing companies compounds faster for you.

- **Against Intermediate and Advanced**: the computer actively prioritizes mergers where it holds a stake, expansion of companies it owns, and companies approaching a split. Claiming expansion squares near a company the computer holds before it can reach them is one of the most effective ways to slow it down. Similarly, investing early in a company the computer is also buying into lets you ride the same growth curve; but if the computer holds significantly more shares, it benefits more from the same price increase.

- **On stock**: the Intermediate and Advanced computer maintains a cash reserve and concentrates on value companies rather than spreading thin. Watching which companies it is accumulating — visible in the portfolio display each turn — gives a useful signal for which companies are likely to grow. Following the computer into a fast-growing company early is often sound strategy; competing against it in the same stock in the late game, when shares are expensive and the split threshold approaches, is where the concentration penalty logic means it may start diversifying while you could double down.

### Optional AI Thinking Visibility

You can optionally expose computer reasoning during interactive games with human players.

- **Summary mode**: adds a concise factor summary to the computer turn status line, showing the selected move and strongest scoring factors.
- **Detailed mode**: keeps the map visible and prints top ranked candidate moves, scores, and major factors below the map/portfolio view.

Both modes are explainability layers only. They do **not** change strategy weights, move legality, or purchase behavior.