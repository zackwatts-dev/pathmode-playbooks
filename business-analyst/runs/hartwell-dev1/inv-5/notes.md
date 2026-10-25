# H5 notes
- q224: shipped lines with no invoice line, by ship year 2016-2025: 434-627 lines/yr; 0 zero-price lines. 2025 within-window = 490 lines / 271,314.82, so the hypothesis's 1.2M for 2025 comes from lines with ship_day > 2520.
- q226: 4,985 lines ship_day<=2520 (2,840,528.65) + 947 lines ship_day>2520 (932,590.69, end effect, excluded). In-window: WMS sale for 4,751 = 4,985 - 234 special (special never hits WMS) -> every non-special line confirmed shipped.
- Dead end (re-bill): 69 lines have another invoice line with the same order+SKU, but q229 shows all 70 matches are a different order line billed for its own shipped qty, 0 billed for the combined qty. So no re-bills.
- q232: rate 0.194% of 2,563,485 shipped lines; flat by year (0.181-0.216%), branch (0.166-0.219%), fulfilment. Channel: counter 1.124%, email 0.155%, phone 0.148%, edi 0, web 0. Only manually keyed channels.
- q235/q236: all 48 inside reps have some; counter median 1.122% per rep, max 1.636%; top rep overall is 0.359%. Not concentrated in people.
- q238: 4,950 orders, 2,244 customers, max 26 lines per customer; top 50 customers = 613 lines. 3,655 lines have an invoice for the same order raised within +/-1 day of ship (the line was left off an invoice that was raised); 1,139 lines on orders with no invoice. 156 in last 85 days.
- q240: 4,009 of those invoices: 4,008 header = lines (so the missing line is not in the header), 3,956 paid at header amount. 16 lines later returned, 48 have memo on order.
- q243: 2016-2024, 4,495 lines, 2,569,213.83, avg 285,468.20/yr (min 252,827.81, max 348,493.66), standard cost 213,944.60/yr, 0.1948% of billed.
- q244: counter 137,555.05/yr, email 109,830.29, phone 38,082.86.
