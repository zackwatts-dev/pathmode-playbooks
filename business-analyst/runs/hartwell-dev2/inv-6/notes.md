# H4 notes
- q269: all 1,429 '-R' bills pair 1:1 with an original on same PO, invoice no = original||'-R', same amount, original 10-29 operating days earlier (median 19).
- q271: 963 '-R' paid; all 963 originals also paid. 466 '-R' unpaid (462 with paid original, 4 both unpaid). No PO has >1 receipt (nrec 0 or 1) -> no second delivery justifies a second bill. nrec=0 rows are mostly special POs (never received in WMS by design).
- q274: special 327 paid / stock 636 paid. Total paid on those POs exceeds PO value by $419,965.33 / $2,329,787.92.
- q275: steady each year 2016-2025, 81-107 paid per year, paid rate 0.5817-0.7357; '-R' share of all bills 0.356%-0.418%.
- q279: spread across all 44 vendors (rate 0.24%-0.64% of each vendor's bills); dollars concentrated in vendor 1 (37.96% of paid $) because its bills are large, not because rate is higher. Hypothesis's "concentrated in vendors" support doesn't hold on rate.
- q280/q283/q284/q290: vendor credits only vendors 1-4; 2 exact-amount matches are the same credit 221, different sku, >1,000 days later -> coincidence. Even counting every same-vendor same-sku credit within 120 days: 39 credits $56,580.26. Credits never equal qty x product cost (q284) -- they look like RTV credits, not bill corrections.
- q287: $2,732,286.38 paid, $273,228.64/yr; unpaid 466: 451 past terms (apparently caught/held), 15 not yet due ($21,759.97) at risk.
- q294: paid vs unpaid not explained by terms, gap, or amount (rates 0.64-0.70 everywhere) -> catching looks random. Dead end for a rule.
- Caveat: system-generated look (exact amounts, fixed suffix, steady rate). Could be how the source records a re-sent invoice; but payment is real in the ledger.
