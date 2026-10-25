# H4 notes
- q257: quote line layout; run_hours per piece, est_material is line total, unit_price per piece.
- q261: key-linked won NEW quotes (sales_orders.quote_id) -> job on same part. Job routing est == quote est (setup + run/pc x qty) exactly at every WC (route_over_quote 1.000), job qty == quote qty on all. Actual/quote >=1 everywhere except lathe 0.942 (117 ops): laser 1.009, brake 1.024, mill 1.052, paint 1.066, assembly 1.128, weld 1.277. Premise of H4 fails for new parts.
- q265: the low ratios (~0.72-0.87, orient q80) come from REPEAT jobs: actual/est falls with nth job of part (laser 0.958 -> 0.739, brake 1.001 -> 0.741, weld 1.223 -> 0.917; inspect flat ~1.06). Learning curve on unchanged routing. Caveat: "first job in data" may not be first ever for parts made before 2016.
- q268: non-weld first-job ratio 1.01-1.079 every year; weld 1.215-1.329, drifting up.
- q266/q267/q270: hit rate does NOT fall with hours per $ material; Q1 0.2224 vs Q5 0.265; within customer-year slope +0.0143 (corr 0.0199). Non-material share: flat 0.2356-0.2653. Dead end for the pricing->hit-rate link.
- work_date truncation irrelevant: hours summed per op.
- Side finding: weld underestimated on new parts by ~1,004.5 h/yr on key-linked sample only (q271).
