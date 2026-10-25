# H9 notes

- q285: win by customer discount band flat 0.417-0.4394 except discount 0 (0.3625, 19,002 quotes). Discount doesn't track win.
- q309: zero-discount weakness is concentrated: 2 mixed-trade Troy customers, 7,418 quotes, win 0.2819. Outside Troy zero-disc ≈ others.
- q302: customer win rate vs discount corr -0.0105 (2,099 customers with >=50 quotes). DEAD END for discount as the driver.
- q299: customer heterogeneity real: var 0.01267 vs binomial 0.00222.
- q303: trade is the driver: commercial 0.3172, mixed 0.4047, residential 0.4937.
- q292/q308: rep SD raw 0.0295; discount only 0.0272; trade 0.0272; trade+branch 0.0174; +size 0.0172; +discount band 0.0128 (likely overfit: small cells absorb individual customers).
- q295: residual rep effect stable across time halves (corr 0.6459) but not across disjoint customer halves (0.1994) -> rep "effect" is carried by specific customers, not rep-wide behaviour (interpretation).
- q304: Troy lowest branch 0.378, 17% zero-disc quotes.
- Markdowns: quoted = list*(1-cust disc)*(1-md) (q316). Markdowns ~only on equipment quoted after discontinued_on (q318), share rises 2023+ (q319).
- Like-for-like (quotes with past-discontinued SKUs): md 0.4265 (66,471) vs none 0.4354 (64,922) (q323); within customer -0.0022 (q327), within SKU -0.0044 (q328); no dose response (q331).
- Data concern: 190 md quotes w/o discontinued SKU, 0 wins, days 1729-2268 (q338).
- Markdown reaches order: 32,846/32,846 lines same md (q335).
- $ on won quotes: 15,306,356.71 over 10y; 4,454,984.04 in 2025; 3y avg 3,163,084.84 (q332, q336).
- Rep md share vs residual win corr 0.0789 (q339) - no.
