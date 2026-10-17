Answer with JSON only, no other text, in exactly this shape:

{"category": "service_request | purchase_order | quote_request | schedule_change | invoice_question | complaint | approval | certificate_request | vendor_or_marketing | other",
 "urgency": "emergency | today | this_week | no_action",
 "route_to": "who should handle it",
 "summary": "one sentence",
 "needs_reply": true or false,
 "draft_reply": "the draft, or an empty string",
 "flags": ["anything a person must check"]}
