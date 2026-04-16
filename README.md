# trade
Port of Star Traders Kaypro II game from BASIC to Python
* NOTE: This is primarily to get some experience working with GitHub, Git, and Atom.
If you find this project, you should likely look elsewhere for excellent Git/coding form. :)

Notes:
* In the original, a company could be created that would trigger a merge, but the
coordinate of the new company was not added to the map until after the merger, meaning
a company could be created with 0 coordinates. This behavior is maintained in this version.

* The original settled merger ties by alphabetical order, while this version goes with
longevity (whichever company was founded earlier will triumph, given equal territories). 

TODO - Explore whether always going with age shifts gameplay in a non-fun direction, Options suggested by CoPilot:
* Hybrid tie break: 1. Company Size, 2. Age, 3. Alphabetical
* Age decay: Pre round 20, older company winds; post-round 20, alphabetical wins [could also say younger would win to mirror upstart market conditions] 
* Bonus compensation: Give late-founded companies a slightly larger founder bonus (e.g., +6 shares instead of +5 after turn X).
This counterweights age dominance economically rather than procedurally.
