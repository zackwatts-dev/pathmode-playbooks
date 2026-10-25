# H1 working notes

- q92: confirmed yearly rise in markdown share/avg and recorded-markdown $ (4.38M 2022 -> 13.26M 2025, qty_ordered basis).
- q95: rise is seasonal (Q2/Q3 high) and steps up from 2023. avg markdown-when-any was exactly 0.42 every quarter of 2022: looks like a rule, not discretion.
- q96: markdowns ONLY on equipment. parts/refrigeration/supplies = 0 in both 2022 and 2025.
- q99: values are a ladder 0.021 steps up to 0.42 cap.
- q105: all 84,092 marked-down lines are equipment lines ordered on/after the SKU's discontinued_on; 0 markdowns elsewhere; 373 post-disc lines have none (first month).
- q106: three discontinuation waves: 2015-01-01 (132 SKUs), 2023-01-01 (132), 2025-01-01 (130, all R-410A).
- q114: markdown = 2.1 points per ~21 operating days since discontinuation, capped at 42% after ~20 months. Same for every line.
- q120: 0 of 328,178 equipment SKU-days have more than one markdown value -> no customer/rep/branch discretion. So the H1 cross-sectional test (people whose rate went up) only measures SKU mix.
- q109: DEAD QUERY: left join bug (counted all lines); don't use.
- q118/q129: discontinued SKUs are still bought on stock and special POs years after discontinuation (2015 wave bought every year 2016-2025).
- q124: post-disc lines at/below standard cost; 2023 wave GM -11.9% in 2025.
- q127: 2023 wave volume fell 16,108 lines (2022) -> 5,757 (2023) then rose to 10,602 (2025) as markdown deepened: some volume response, but still below pre-disc level.
- q135/q138: KEY: markdown_pct is recorded on special/transfer/short lines but the price isn't cut (price/list ~0.83 same as normal). Only stock lines are priced down (0.551 of list). So most of the H1 "markdown dollars" are recorded but never applied.
- q139: applied (stock) markdown $ 1.32M 2022 -> 5.38M 2025; GP on marked-down stock lines -0.77M 2022 -> -2.49M 2025.
- q136: quote win rate on lines with markdown is no higher than on lines without (2025 0.441 vs 0.446). Win rate flat 0.42-0.45 throughout.
- q141: 12 branches, change in applied markdown rate vs order growth corr -0.09 (none). vs revenue -0.81 (mechanical: markdown cuts revenue).
- q145: stock units of discontinued SKUs bought ~ equal to sold: 2025 bought 10,001 (11.21M std cost), sold 11,866 from stock, 9,437 below cost.
- Caveat: unit_cost is one standard per SKU; PO cost = std cost (map q68) so buy price is that.
