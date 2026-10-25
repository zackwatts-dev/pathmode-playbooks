# H5 notes
- q130: base split excl -R. Over-PO: full 13,901 ($3,149,433.24), to_po 5,911 ($1,371,706.45), unpaid 309. Freight-only (no line excess) bills: 6,115 short-paid to PO, rest full.
- q138: per vendor, over-PO bill rate 0.0454-0.0618 for all 44; full-pay rate 0.624-0.771. Vendors 1-4 (OEM) = 0.8061 of full-paid excess.
- q168: OEM 0.5547 of PO value but 0.8058 of excess -> driven by high unit cost (avg $1,183.94 vs ~$93-107), not by vendor behaviour (bill-count rate flat).
- q147: stock qty-over lines 3,631: receipt qty = PO on all 3,631, = billed on 0. Special lines have no receipt (can't verify). Cost-over ratio 1.03-1.08 band, 501 distinct ratios.
- q149: price-increase test FAILED to support price increase: P(next bill same sku over | over) 0.0288 vs base 0.0249; same higher cost repeated 3/425. One-off, not persistent.
- q157: full-pay rate ~0.70 regardless of year, type, purpose, excess size, freight, pay terms. Freight-only bills too (0.699). No visible attribute decides it.
- q163: sizing 10 yrs: $314,943.32/yr line excess paid; stock qty excess paid (unreceived per WMS) $83,949.04/yr; freight paid $207,629.02/yr; total $522,572.34/yr.
Dead ends: vendor concentration in behaviour (rate is uniform); price-increase pattern; any rule for short-pay.
Caveat: such uniform rates (5%, 70%) look generated; the "match" control appears to be a random 30% enforcement.
