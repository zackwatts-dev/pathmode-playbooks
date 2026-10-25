# H1 working notes

- q128: markdowns exist on equipment every year since 2016 (~$3.6-4.2M/yr by the q103 formula), none on parts/refrigeration/supplies. Split ~evenly across R-410A / R-454B / no refrigerant even in 2016-2022. Depth fixed 0.42 2017-2022.
- q131: two regimes: flat 0.42, and graded steps of 0.021 (2023+).
- q139/q145: the flat 0.42 is a SKU attribute. 132 SKUs (44 R-410A, 44 R-454B, 44 none) with discontinued_on 2015-01-01; another 132 (44/44/44) discontinued 2023-01-01 joined during 2024; 129 R-410A SKUs discontinued 2025-01-01 graded in 2025. Never-marked-down: 130 R-454B + 130 none + 1 R-410A, no discontinued_on.
- q150: markdown = 2.1% per month since discontinued_on, cap 42% at month 20; min=max within every cohort-month, zero exceptions -> no channel/rep/customer variation possible. Pricing rule, not people.
- q156: by cohort; 2015 cohort still ~5,700 lines/yr in 2025, negative static-cost margin.
- q160: discontinued SKUs are still being bought: stock and special POs every year, 2023 cohort stock buying recovers in 2024-25. 2025 R-410A cohort buying stops in 2025 (the only real wind-down).
- q169/q171: IMPORTANT: special and transfer lines carry markdown_pct but price isn't reduced (price/list ~0.83 same as unmarked). Only stock lines are actually priced down. So q103's markdown dollars overstate: the flag-only part is $6.6M of $12.0M in 2025 (q174).
- q174/q180: real (stock-line) markdown 2022 $1.32M -> 2025 $5.38M, +$4.06M. 2023 cohort $3.45M (R-410A 0.98M, R-454B 1.07M, none 1.40M), 2025 R-410A cohort $0.64M, 2015 cohort flat $1.28M.
- Dead ends: channel/taken_by/account-manager comparison is moot (rate deterministic by SKU-month). Stock-age test not run: restocking (q160) makes "aging stock" moot.
- Data concern: none of the records addressed to an AI were seen in this stage.
