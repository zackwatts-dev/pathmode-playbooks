You grade one finding from an AI analyst against the answer key of a simulated business. The analyst never saw the key. You have the `query` tool on a read-only database holding the simulation's truth tables (schema `truth`) and the same warehouse the analyst queried.

The answer key:

{
 "business": "Wendlow Fabrication & Machine (simulated job shop), 2016-2025, run 9",
 "source": "pathmode-corpus simulations/fabricator/grading/truth-summary.md, BUILD.md (runs 8 and 9) and the truth database (schema truth in the grader's database)",
 "problems": [
  {
   "id": "P1",
   "name": "Slow quotes losing work",
   "mechanism": "Quotes sent late win far less often (within 2 working days about 34%, 5+ days about 18%). Since runs 8-9 the delay comes mostly from how requests are handled: the quotes inbox is read and keyed twice a week, and about 40% of new requests are missing a revision, quantity or drawing, found only when an estimator opens the request to price it, after which it waits for the buyer's answer. The two estimator vacancies (2021-04, 2024-03) add to it.",
   "shows_in": "rfqs (received_on, entered_on), quotes (sent dates, outcomes), the mail log",
   "truth": "about 237 new requests a year (20%) lost because the quote came after the buyer decided (2023-25)",
   "dollars_a_year": null
  },
  {
   "id": "P2",
   "name": "Estimates that drift on some families",
   "mechanism": "Welding on families 3 and 4 runs about 1.03-1.07x the shop standard and about 1.2-1.4x each estimator's estimate; precision machining (family 5) runs under. The re-quotes copy the old estimates forward.",
   "shows_in": "quote line estimated hours by work centre against labour clock-ins by job and operation",
   "truth": "weld true/estimated about 1.22-1.44 on families 3-4 for every estimator; family 5 about 0.86-0.96",
   "dollars_a_year": null
  },
  {
   "id": "P3",
   "name": "Due dates promised without a capacity check",
   "mechanism": "Due dates are promised from a standard lead time; when the bottleneck work centre (laser and brake in 2016 and 2019-21, weld from 2022) is loaded, lines go late.",
   "shows_in": "sales order promised dates against shipments, and labour by work centre",
   "truth": "on time 78% (welding lines) in 2016 and 76-83% in 2021, against 93-99% in other years",
   "dollars_a_year": null
  },
  {
   "id": "P4",
   "name": "Material increases eaten between quote and purchase",
   "mechanism": "Steel bought after the quote at higher prices; repeat orders keep the old price; the surcharge clause recovers little.",
   "shows_in": "quote material cost against purchase-order cost by order, with the steel price index",
   "truth": "$3,029,316 of material over quote in 2021 (by year bought), $769,433 in 2018; 2019-20 and 2023-24 under",
   "dollars_a_year": null
  },
  {
   "id": "P5",
   "name": "Engineering changes that don't reach the floor",
   "mechanism": "A revision arrives by email that names no job, after the traveller is printed, or while engineering is behind; the job is built to the old revision; some escape to the customer as returns.",
   "shows_in": "drawing revisions, ECOs and the jobs logged against them, scrap reports, inspections, returns",
   "truth": "305 jobs built to an old revision (170 email named no job, 91 traveller already printed, 44 engineering behind); 81 escaped to the customer",
   "dollars_a_year": null
  },
  {
   "id": "P6",
   "name": "Know-how in one or two people",
   "mechanism": "The senior CAM programmer left in 2022 (programs and first articles suffer: first-article failures roughly doubled); the senior estimator's departure in 2024 slowed quotes.",
   "shows_in": "CAM programs by author, inspections (first articles), quote turnaround by period",
   "truth": "senior programmer wrote 64-108 programs a year through 2021, 59 in 2022, none after",
   "dollars_a_year": null
  }
 ]
}

The finding (its cited queries' SQL and results follow it):

{
 "id": "F10",
 "hypothesis": "H11",
 "title": "Wrong-revision scrap sits almost entirely on jobs that a new drawing revision missed: 99 of 137 reports are on 248 jobs where a revision arrived mid-job and no ECO was logged against the job. Release lag alone explains only 34. About $69,682/yr at cost, including fit/dimension/nonconforming credits",
 "conclusion": "Observed, released jobs only, 2015-11 to 2025-12: all 137 'wrong revision' scrap reports were filed after a revision newer than the one issued had been received (q378). Every one scrapped the whole job quantity, none of those jobs shipped, and all 137 had a remake on the same sales-order line (q388). 34 reports are on the 82 jobs released on a revision older than the latest one received by the release date (q355). 99 are on 248 jobs released on the current revision where a newer revision was received before the job completed and no ECO was logged against the job: 39.919% of those jobs. The comparison groups are 4 of 709 mid-job-revision jobs with an ECO (0.564%) and 0 of 51,122 jobs with no mid-job revision (q359). The gap between no-ECO and ECO jobs holds within the same 43 customers (40.3% v 0.7%) and the same 65 parts (48.1% v 1.1%) (q394). It holds whether or not engineering released the revision before the job finished (44.0% v 0.7% where it did, 31.3% v 0.0% where it didn't), with similar median job lengths (q380). It also holds where an ECO for the same revision was logged against a sibling job: 26 of those 49 jobs still have wrong-revision scrap (q381). Separately, returns go to different jobs from the scrap. None of the 137 scrapped jobs has a return, and all 81 return authorisations are on other jobs (q388). 57 of the 58 fit/dimension/nonconforming returns and 80 of the 81 credit memos are on other at-risk jobs that shipped (q359, q361, q384). Valued at cost, the scrapped runs cost $331,519 in material and $60,427 in labour (2,420 hours at the average pay rate of $24.97, unloaded). Adding $304,873 of fit/dimension/nonconforming credits gives $69,682/yr over 10 years: $39,195 from scrap and $30,487 from credits (q387, q393). The pattern appears in every year from 2016 to 2025 (q363). Interpretation: the main pattern is a revision that arrives while a job is open and is not tied to that job by an ECO. Revisions that reach the floor late at release are a smaller part. The control should be per job and run at receipt: when a revision is received, check every open job for the part. Also hold release of new jobs while a received revision is still unreleased.",
 "dollars_a_year": 69682.0,
 "size_query": "q393",
 "claims": [
  {
   "text": "All 137 wrong-revision reports (2,852 pieces; the code has no variant spellings) were filed after a revision newer than the one issued had been received. Each scrapped the full job quantity. None of those jobs shipped or has a return, and all 137 have a remake on the same SO line.",
   "queries": [
    "q377",
    "q378",
    "q388"
   ]
  },
  {
   "text": "Jobs released on a revision older than the latest received by the release date: 82. 34 of them have wrong-revision scrap (982 pieces). Current-revision jobs on parts with revisions: 103 of 52,079. Jobs on parts with no revisions: 0 of 24,463. The 82 depends on the definition: 136 if logged date is the reference, 347 if the reference is the job's creation date. None of these reconciles with q26's 158.",
   "queries": [
    "q353",
    "q355",
    "q392"
   ]
  },
  {
   "text": "Mid-job revision with no ECO on the job: 99 of 248 jobs with wrong-revision scrap (39.919%). With an ECO: 4 of 709 (0.564%). No mid-job revision: 0 of 51,122.",
   "queries": [
    "q359"
   ]
  },
  {
   "text": "The no-ECO v ECO gap holds within customers (43 customers: 93 of 231, 40.3%, v 4 of 613, 0.7%) and within parts (65 parts: 38 of 79, 48.1%, v 1 of 88, 1.1%). It holds where the revision was released before completion (74 of 168, 44.0%, v 4 of 548, 0.7%) and after (25 of 80, 31.3%, v 0 of 161). Median job length is 24 v 25 days and 11 v 11. No mid-job revision has an unlinked ECO. Where an ECO for the same revision was on a sibling job, 26 of 49 jobs still had wrong-revision scrap; where no ECO existed for the revision, 73 of 199 did.",
   "queries": [
    "q380",
    "q381",
    "q394"
   ]
  },
  {
   "text": "Credits: 81 memos total $381,885, one per return authorisation, with no fan-out in the join. 80 of the 81 are on at-risk jobs ($110,705 superseded-at-release, $260,898 mid-job without an ECO, $10,283 on all other jobs). 57 of the 58 fit/dimension/nonconforming returns are on at-risk jobs. These jobs are different from the scrapped ones.",
   "queries": [
    "q361",
    "q384",
    "q388",
    "q393"
   ]
  },
  {
   "text": "Size at cost: 133 at-risk jobs have wrong-revision scrap, worth $544,560 at PO price, which equals those jobs' full revenue. Their cost is $331,519 material plus $60,427 labour, $391,946 in total (72.0% of the price value). Adding $304,873 of fit/dimension/nonconforming credits gives $69,682/yr over 10 years ($39,195 scrap, $30,487 credits), against $84,943/yr originally at PO price. The top 10 jobs hold 34.6% of the scrap value; the median job is $2,077.",
   "queries": [
    "q365",
    "q387",
    "q393"
   ]
  },
  {
   "text": "Not a single period: superseded-at-release jobs run 4-11 a year and mid-job-without-ECO jobs 9-41 a year from 2016 to 2025. ECO coverage of mid-job revisions is 67.4%-82.7% a year with no trend. None of the 181 open jobs is classed as at risk.",
   "queries": [
    "q363",
    "q392"
   ]
  }
 ],
 "confidence": "medium",
 "not_evidence_of": "That parts were physically made to the wrong drawing: 'wrong revision' is a self-entered code, and the revision actually machined is not recorded. That logging an ECO causes the protection: the ECO and the avoided scrap may share a cause, namely someone noticing the revision in time. That returns on at-risk jobs were caused by the revision: they are on different jobs from the scrap, 23 of the 81 are coded 'per buyer', and return reasons are reported by the buyer. That $69,682/yr is fully avoidable. Credits are an upper bound. Labour at an unloaded average wage is roughly a floor. Remaking returned parts is not included. Any person's conduct: a missing ECO is a pattern in how changes are recorded.",
 "could_not_tell": "Whether the floor used old prints or the job packet was never updated. When the scrapped pieces were made relative to the revision's arrival, since labour work_date is a posting date. Loaded labour and overhead cost. Why 51 jobs were issued a revision older than one already released. The exact split between superseded-at-release and mid-job, which depends on the reference date (82 v 136) and does not reconcile with q26's 158; the combined at-risk population is the more robust object. Separating 'ECO protects' from 'ECO records that the change was caught' would need timestamps on when job packets and travellers were updated, and revision checks at first article or final inspection.",
 "next_step": "When a revision is received (not when it is released), list every open job for that part and require an ECO or an explicit disposition for each job. An ECO on one sibling job is not enough. Hold release of new jobs for a part while a received revision is unreleased. Record the revision checked at first article. Then track wrong-revision scrap on mid-job-revision jobs, with and without a per-job disposition, to see whether the control works.",
 "incomplete": false
}

[
 {
  "id": "q377",
  "sql": "SELECT reason_code, count(*) n, sum(quantity) q FROM shop_scrap_reports GROUP BY 1 ORDER BY n DESC, reason_code",
  "columns": [
   "reason_code",
   "n",
   "q"
  ],
  "row_count": 8,
  "rows": [
   [
    "dimension out of tolerance",
    15446,
    19398
   ],
   [
    "operator error",
    6557,
    10134
   ],
   [
    "material",
    4102,
    6268
   ],
   [
    "other",
    4067,
    6024
   ],
   [
    "weld defect",
    231,
    1218
   ],
   [
    "paint or finish",
    228,
    969
   ],
   [
    "wrong revision",
    137,
    2852
   ],
   [
    "first article",
    34,
    68
   ]
  ],
  "error": null
 },
 {
  "id": "q378",
  "sql": "WITH s AS (SELECT sr.scrap_id, sr.job_id, sr.reported_on, sr.quantity, j.part_id, j.released_on, j.completed_on, j.revision_issued\n FROM shop_scrap_reports sr JOIN erp_jobs j USING(job_id) WHERE sr.reason_code='wrong revision'),\nx AS (SELECT s.*,\n (SELECT min(r.received_on) FROM eng_drawing_revisions r WHERE r.part_id=s.part_id AND r.received_on>s.released_on AND r.received_on<=coalesce(s.completed_on,'9999')) first_mid_rev,\n (SELECT min(r.released_on) FROM eng_drawing_revisions r WHERE r.part_id=s.part_id AND r.received_on>s.released_on AND r.received_on<=coalesce(s.completed_on,'9999')) first_mid_rev_rel,\n (SELECT min(e.logged_on) FROM eng_ecos e WHERE e.job_id=s.job_id) eco_on,\n (SELECT max(r.revision) FROM eng_drawing_revisions r WHERE r.part_id=s.part_id AND r.received_on<=s.reported_on) rev_at_scrap\n FROM s)\nSELECT CASE WHEN first_mid_rev IS NULL THEN 'no_mid_rev' WHEN reported_on>=first_mid_rev THEN 'scrap_after_mid_rev_received' ELSE 'scrap_before_mid_rev' END timing,\n CASE WHEN eco_on IS NULL THEN 'no_eco' WHEN eco_on<=reported_on THEN 'eco_before_scrap' ELSE 'eco_after_scrap' END eco_t,\n (rev_at_scrap>revision_issued) newer_rev_existed_at_scrap,\n count(*) n, sum(quantity) q, min(reported_on) mn, max(reported_on) mx\nFROM x GROUP BY ALL ORDER BY ALL",
  "columns": [
   "timing",
   "eco_t",
   "newer_rev_existed_at_scrap",
   "n",
   "q",
   "mn",
   "mx"
  ],
  "row_count": 5,
  "rows": [
   [
    "no_mid_rev",
    "eco_before_scrap",
    true,
    1,
    7,
    "2021-12-09",
    "2021-12-09"
   ],
   [
    "no_mid_rev",
    "no_eco",
    true,
    33,
    975,
    "2016-05-12",
    "2025-11-18"
   ],
   [
    "scrap_after_mid_rev_received",
    "eco_after_scrap",
    true,
    1,
    16,
    "2016-11-29",
    "2016-11-29"
   ],
   [
    "scrap_after_mid_rev_received",
    "eco_before_scrap",
    true,
    3,
    67,
    "2019-08-22",
    "2024-04-29"
   ],
   [
    "scrap_after_mid_rev_received",
    "no_eco",
    true,
    99,
    1787,
    "2016-02-01",
    "2025-11-12"
   ]
  ],
  "error": null
 },
 {
  "id": "q388",
  "sql": "WITH s AS (SELECT job_id, sum(quantity) q FROM shop_scrap_reports WHERE reason_code='wrong revision' GROUP BY 1),\nsj AS (SELECT j.job_id, j.line_id, j.quantity, s.q FROM erp_jobs j JOIN s USING(job_id)),\nra AS (SELECT job_id, reason FROM erp_return_authorisations)\nSELECT count(*) wr_jobs, count(*) FILTER (WHERE q=quantity) full_job_scrapped,\n count(*) FILTER (WHERE job_id IN (SELECT job_id FROM ra)) wr_jobs_with_ra,\n count(*) FILTER (WHERE job_id IN (SELECT job_id FROM ra WHERE reason IN ('does not fit','wrong dimensions','nonconforming'))) wr_jobs_with_fit_ra,\n count(*) FILTER (WHERE line_id IN (SELECT line_id FROM erp_jobs WHERE kind='remake')) wr_jobs_with_remake_on_line,\n count(*) FILTER (WHERE job_id IN (SELECT job_id FROM erp_shipment_lines)) wr_jobs_shipped,\n (SELECT count(*) FROM ra WHERE job_id NOT IN (SELECT job_id FROM s)) ra_on_jobs_without_wr,\n (SELECT round(avg(hourly),2) FROM hr_pay_rates) avg_hourly_all_rows,\n (SELECT round(sum(quantity),0) FROM shop_scrap_reports WHERE reason_code='wrong revision') wr_pieces\nFROM sj",
  "columns": [
   "wr_jobs",
   "full_job_scrapped",
   "wr_jobs_with_ra",
   "wr_jobs_with_fit_ra",
   "wr_jobs_with_remake_on_line",
   "wr_jobs_shipped",
   "ra_on_jobs_without_wr",
   "avg_hourly_all_rows",
   "wr_pieces"
  ],
  "row_count": 1,
  "rows": [
   [
    137,
    137,
    0,
    0,
    137,
    0,
    81,
    24.97,
    2852
   ]
  ],
  "error": null
 },
 {
  "id": "q353",
  "sql": "WITH j AS (\n SELECT j.job_id, j.part_id, j.kind, j.released_on, j.revision_issued,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on<=j.released_on),'A') rec_rev,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.released_on<=j.released_on),'A') rel_rev\n FROM erp_jobs j WHERE j.released_on IS NOT NULL)\nSELECT kind,\n CASE WHEN revision_issued=rec_rev THEN 'a_current' WHEN revision_issued=rel_rev THEN 'b_lag_window' WHEN revision_issued<rel_rev THEN 'c_older_than_released' ELSE 'd_newer' END cls,\n count(*) jobs, max(length(revision_issued)) maxlen\nFROM j GROUP BY ALL ORDER BY kind, cls",
  "columns": [
   "kind",
   "cls",
   "jobs",
   "maxlen"
  ],
  "row_count": 5,
  "rows": [
   [
    "order",
    "a_current",
    76238,
    1
   ],
   [
    "order",
    "b_lag_window",
    31,
    1
   ],
   [
    "order",
    "c_older_than_released",
    50,
    1
   ],
   [
    "remake",
    "a_current",
    304,
    1
   ],
   [
    "remake",
    "c_older_than_released",
    1,
    1
   ]
  ],
  "error": null
 },
 {
  "id": "q355",
  "sql": "WITH j AS (\n SELECT j.job_id, j.part_id, j.released_on, j.revision_issued,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on<=j.released_on),'A') rec_rev,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.released_on<=j.released_on),'A') rel_rev,\n  (SELECT count(*) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id)>0 has_revs\n FROM erp_jobs j WHERE j.released_on IS NOT NULL),\nc AS (SELECT *, CASE WHEN revision_issued=rec_rev THEN 'a_current' WHEN revision_issued=rel_rev THEN 'b_lag_window' ELSE 'c_older_than_released' END cls FROM j),\ns AS (SELECT job_id, count(*) n, sum(quantity) q FROM shop_scrap_reports WHERE reason_code='wrong revision' GROUP BY 1),\nra AS (SELECT job_id, count(*) n FROM erp_return_authorisations WHERE reason IN ('does not fit','wrong dimensions','nonconforming') GROUP BY 1),\nra_all AS (SELECT job_id, count(*) n FROM erp_return_authorisations GROUP BY 1)\nSELECT cls, has_revs, count(*) jobs, count(s.job_id) jobs_wr_scrap, coalesce(sum(s.n),0) wr_reports, coalesce(sum(s.q),0) wr_pieces,\n round(100.0*count(s.job_id)/count(*),3) pct_jobs_wr, coalesce(sum(ra.n),0) fit_dim_nc_returns, coalesce(sum(ra_all.n),0) all_returns\nFROM c LEFT JOIN s USING(job_id) LEFT JOIN ra USING(job_id) LEFT JOIN ra_all USING(job_id)\nGROUP BY ALL ORDER BY cls, has_revs",
  "columns": [
   "cls",
   "has_revs",
   "jobs",
   "jobs_wr_scrap",
   "wr_reports",
   "wr_pieces",
   "pct_jobs_wr",
   "fit_dim_nc_returns",
   "all_returns"
  ],
  "row_count": 4,
  "rows": [
   [
    "a_current",
    false,
    24463,
    0,
    0,
    0,
    0.0,
    0,
    0
   ],
   [
    "a_current",
    true,
    52079,
    103,
    103,
    1870,
    0.198,
    40,
    58
   ],
   [
    "b_lag_window",
    true,
    31,
    14,
    14,
    380,
    45.161,
    7,
    9
   ],
   [
    "c_older_than_released",
    true,
    51,
    20,
    20,
    602,
    39.216,
    11,
    14
   ]
  ],
  "error": null
 },
 {
  "id": "q392",
  "sql": "WITH j AS (\n SELECT j.job_id, j.part_id, j.released_on, j.created_on, j.completed_on, j.revision_issued, p.revision part_rev,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on<=j.released_on),'A') rec_rev,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on<=j.created_on),'A') rec_rev_created,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.logged_on<=j.released_on),'A') log_rev,\n  (SELECT count(*) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on>j.released_on AND r.received_on<=coalesce(j.completed_on,'9999')) mid,\n  (SELECT count(*) FROM eng_ecos e WHERE e.job_id=j.job_id) ecos\n FROM erp_jobs j JOIN erp_customer_parts p USING(part_id) WHERE j.released_on IS NOT NULL)\nSELECT count(*) FILTER (WHERE revision_issued<>rec_rev) sup_at_release,\n count(*) FILTER (WHERE revision_issued<>rec_rev_created) sup_vs_created,\n count(*) FILTER (WHERE revision_issued<>log_rev) sup_vs_logged,\n count(*) FILTER (WHERE revision_issued<>coalesce(part_rev,'A')) diff_from_part_master,\n count(*) FILTER (WHERE revision_issued<rec_rev OR mid>0) older_or_mid,\n count(*) FILTER (WHERE completed_on IS NULL AND (revision_issued<>rec_rev OR (mid>0 AND ecos=0))) at_risk_open,\n count(*) FILTER (WHERE completed_on IS NULL) open_jobs,\n (SELECT count(*) FROM erp_jobs WHERE released_on IS NULL) unreleased_jobs\nFROM j",
  "columns": [
   "sup_at_release",
   "sup_vs_created",
   "sup_vs_logged",
   "diff_from_part_master",
   "older_or_mid",
   "at_risk_open",
   "open_jobs",
   "unreleased_jobs"
  ],
  "row_count": 1,
  "rows": [
   [
    82,
    347,
    136,
    35189,
    1039,
    0,
    181,
    106
   ]
  ],
  "error": null
 },
 {
  "id": "q359",
  "sql": "WITH j AS (\n SELECT j.job_id, j.part_id, j.released_on, j.completed_on, j.revision_issued,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on<=j.released_on),'A') rec_rev,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.released_on<=j.released_on),'A') rel_rev,\n  (SELECT count(*) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on>j.released_on AND r.received_on<=coalesce(j.completed_on,'9999')) mid_job_revs,\n  (SELECT count(*) FROM eng_ecos e WHERE e.job_id=j.job_id) ecos\n FROM erp_jobs j WHERE j.released_on IS NOT NULL\n   AND EXISTS (SELECT 1 FROM eng_drawing_revisions r WHERE r.part_id=j.part_id)),\nc AS (SELECT *, CASE WHEN revision_issued=rec_rev THEN 'a_current' ELSE 'bc_superseded' END cls,\n   CASE WHEN mid_job_revs>0 THEN 'rev_mid_job' ELSE 'no_mid' END mid, CASE WHEN ecos>0 THEN 'eco' ELSE 'no_eco' END eco FROM j),\ns AS (SELECT job_id, count(*) n, sum(quantity) q FROM shop_scrap_reports WHERE reason_code='wrong revision' GROUP BY 1),\nra AS (SELECT job_id, count(*) n FROM erp_return_authorisations WHERE reason IN ('does not fit','wrong dimensions','nonconforming') GROUP BY 1)\nSELECT cls, mid, eco, count(*) jobs, count(s.job_id) jobs_wr, coalesce(sum(s.q),0) wr_pieces, round(100.0*count(s.job_id)/count(*),3) pct, coalesce(sum(ra.n),0) fit_returns\nFROM c LEFT JOIN s USING(job_id) LEFT JOIN ra USING(job_id) GROUP BY ALL ORDER BY ALL",
  "columns": [
   "cls",
   "mid",
   "eco",
   "jobs",
   "jobs_wr",
   "wr_pieces",
   "pct",
   "fit_returns"
  ],
  "row_count": 6,
  "rows": [
   [
    "a_current",
    "no_mid",
    "eco",
    396,
    0,
    0,
    0.0,
    0
   ],
   [
    "a_current",
    "no_mid",
    "no_eco",
    50726,
    0,
    0,
    0.0,
    0
   ],
   [
    "a_current",
    "rev_mid_job",
    "eco",
    709,
    4,
    83,
    0.564,
    1
   ],
   [
    "a_current",
    "rev_mid_job",
    "no_eco",
    248,
    99,
    1787,
    39.919,
    39
   ],
   [
    "bc_superseded",
    "no_mid",
    "eco",
    1,
    1,
    7,
    100.0,
    0
   ],
   [
    "bc_superseded",
    "no_mid",
    "no_eco",
    81,
    33,
    975,
    40.741,
    18
   ]
  ],
  "error": null
 },
 {
  "id": "q380",
  "sql": "WITH j AS (\n SELECT j.job_id, j.part_id, j.released_on, j.completed_on, j.revision_issued,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on<=j.released_on),'A') rec_rev,\n  (SELECT min(r.received_on) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on>j.released_on AND r.received_on<=coalesce(j.completed_on,'9999')) mid_rec,\n  (SELECT min(r.released_on) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on>j.released_on AND r.received_on<=coalesce(j.completed_on,'9999')) mid_rel,\n  (SELECT count(*) FROM eng_ecos e WHERE e.job_id=j.job_id) ecos\n FROM erp_jobs j WHERE j.released_on IS NOT NULL),\nc AS (SELECT *, CASE WHEN mid_rel<=coalesce(completed_on,'9999') THEN 'rev_released_before_done' ELSE 'rev_released_after_done' END relt,\n   CASE WHEN ecos>0 THEN 'eco' ELSE 'no_eco' END eco FROM j WHERE revision_issued=rec_rev AND mid_rec IS NOT NULL),\ns AS (SELECT job_id, count(*) n FROM shop_scrap_reports WHERE reason_code='wrong revision' GROUP BY 1)\nSELECT eco, relt, count(*) jobs, count(s.job_id) jobs_wr, round(100.0*count(s.job_id)/count(*),1) pct,\n round(median(date_diff('day', released_on::date, completed_on::date)),0) med_job_days,\n round(median(date_diff('day', mid_rec::date, completed_on::date)),0) med_days_rev_to_done,\n round(median(date_diff('day', mid_rec::date, mid_rel::date)),0) med_rev_rec_to_rel\nFROM c LEFT JOIN s USING(job_id) GROUP BY ALL ORDER BY ALL",
  "columns": [
   "eco",
   "relt",
   "jobs",
   "jobs_wr",
   "pct",
   "med_job_days",
   "med_days_rev_to_done",
   "med_rev_rec_to_rel"
  ],
  "row_count": 4,
  "rows": [
   [
    "eco",
    "rev_released_after_done",
    161,
    0,
    0.0,
    11.0,
    1.0,
    4.0
   ],
   [
    "eco",
    "rev_released_before_done",
    548,
    4,
    0.7,
    25.0,
    11.0,
    4.0
   ],
   [
    "no_eco",
    "rev_released_after_done",
    80,
    25,
    31.3,
    11.0,
    0.0,
    4.0
   ],
   [
    "no_eco",
    "rev_released_before_done",
    168,
    74,
    44.0,
    24.0,
    10.0,
    4.0
   ]
  ],
  "error": null
 },
 {
  "id": "q381",
  "sql": "WITH j AS (\n SELECT j.job_id, j.part_id, j.released_on, j.completed_on, j.revision_issued,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on<=j.released_on),'A') rec_rev,\n  (SELECT count(*) FROM eng_ecos e WHERE e.job_id=j.job_id) ecos,\n  (SELECT count(*) FROM eng_ecos e JOIN eng_drawing_revisions r USING(rev_id) WHERE r.part_id=j.part_id AND r.received_on>j.released_on AND r.received_on<=coalesce(j.completed_on,'9999')) ecos_for_mid_rev,\n  (SELECT count(*) FROM eng_ecos e JOIN eng_drawing_revisions r USING(rev_id) WHERE r.part_id=j.part_id AND r.received_on>j.released_on AND r.received_on<=coalesce(j.completed_on,'9999') AND e.job_id IS NULL) unlinked_ecos_for_mid_rev,\n  (SELECT count(*) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on>j.released_on AND r.received_on<=coalesce(j.completed_on,'9999')) mid\n FROM erp_jobs j WHERE j.released_on IS NOT NULL),\ns AS (SELECT job_id, count(*) n FROM shop_scrap_reports WHERE reason_code='wrong revision' GROUP BY 1)\nSELECT (ecos>0) job_has_eco, (ecos_for_mid_rev>0) rev_has_any_eco, (unlinked_ecos_for_mid_rev>0) rev_has_unlinked_eco, count(*) jobs, count(s.job_id) jobs_wr,\n (SELECT count(*) FROM eng_ecos WHERE job_id IS NULL) total_unlinked_ecos, (SELECT count(*) FROM eng_ecos) total_ecos\nFROM j LEFT JOIN s USING(job_id) WHERE revision_issued=rec_rev AND mid>0 GROUP BY ALL ORDER BY ALL",
  "columns": [
   "job_has_eco",
   "rev_has_any_eco",
   "rev_has_unlinked_eco",
   "jobs",
   "jobs_wr",
   "total_unlinked_ecos",
   "total_ecos"
  ],
  "row_count": 3,
  "rows": [
   [
    false,
    false,
    false,
    199,
    73,
    6643,
    7761
   ],
   [
    false,
    true,
    false,
    49,
    26,
    6643,
    7761
   ],
   [
    true,
    true,
    false,
    709,
    4,
    6643,
    7761
   ]
  ],
  "error": null
 },
 {
  "id": "q394",
  "sql": "WITH j AS (\n SELECT j.job_id, j.part_id, p.customer_id, j.released_on, j.completed_on, j.revision_issued,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on<=j.released_on),'A') rec_rev,\n  (SELECT count(*) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on>j.released_on AND r.received_on<=coalesce(j.completed_on,'9999')) mid,\n  (SELECT count(*) FROM eng_ecos e WHERE e.job_id=j.job_id) ecos\n FROM erp_jobs j JOIN erp_customer_parts p USING(part_id) WHERE j.released_on IS NOT NULL),\nm AS (SELECT j.*, (ecos>0) has_eco, job_id IN (SELECT job_id FROM shop_scrap_reports WHERE reason_code='wrong revision') wr FROM j WHERE revision_issued=rec_rev AND mid>0),\nboth_c AS (SELECT customer_id FROM m GROUP BY 1 HAVING count(DISTINCT has_eco)=2),\nboth_p AS (SELECT part_id FROM m GROUP BY 1 HAVING count(DISTINCT has_eco)=2)\nSELECT 'customers_with_both' scope, has_eco, count(DISTINCT customer_id) units, count(*) jobs, count(*) FILTER (WHERE wr) jobs_wr, round(100.0*count(*) FILTER (WHERE wr)/count(*),1) pct\nFROM m WHERE customer_id IN (SELECT customer_id FROM both_c) GROUP BY ALL\nUNION ALL\nSELECT 'parts_with_both', has_eco, count(DISTINCT part_id), count(*), count(*) FILTER (WHERE wr), round(100.0*count(*) FILTER (WHERE wr)/count(*),1)\nFROM m WHERE part_id IN (SELECT part_id FROM both_p) GROUP BY ALL\nORDER BY 1,2",
  "columns": [
   "scope",
   "has_eco",
   "units",
   "jobs",
   "jobs_wr",
   "pct"
  ],
  "row_count": 4,
  "rows": [
   [
    "customers_with_both",
    false,
    43,
    231,
    93,
    40.3
   ],
   [
    "customers_with_both",
    true,
    43,
    613,
    4,
    0.7
   ],
   [
    "parts_with_both",
    false,
    65,
    79,
    38,
    48.1
   ],
   [
    "parts_with_both",
    true,
    65,
    88,
    1,
    1.1
   ]
  ],
  "error": null
 },
 {
  "id": "q361",
  "sql": "WITH j AS (\n SELECT j.job_id, j.part_id, j.line_id, j.released_on, j.revision_issued, j.kind,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on<=j.released_on),'A') rec_rev,\n  (SELECT count(*) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on>j.released_on AND r.received_on<=coalesce(j.completed_on,'9999')) mid_job_revs,\n  (SELECT count(*) FROM eng_ecos e WHERE e.job_id=j.job_id) ecos\n FROM erp_jobs j WHERE j.released_on IS NOT NULL),\nc AS (SELECT *, CASE WHEN revision_issued<>rec_rev THEN 'superseded_at_release' WHEN mid_job_revs>0 AND ecos=0 THEN 'rev_mid_job_no_eco' ELSE 'other' END cls FROM j),\ns AS (SELECT sr.job_id, sum(sr.quantity) q, sum(sr.quantity*l.unit_price) val FROM shop_scrap_reports sr JOIN erp_jobs jj USING(job_id) JOIN erp_so_lines l ON l.line_id=jj.line_id WHERE reason_code='wrong revision' GROUP BY 1),\ncr AS (SELECT ra.job_id, ra.reason, sum(cm.amount) amt, count(DISTINCT cm.credit_id) n FROM erp_return_authorisations ra\n   JOIN erp_shipment_lines sl ON sl.job_id=ra.job_id JOIN erp_invoices i ON i.shipment_id=sl.shipment_id JOIN erp_credit_memos cm ON cm.invoice_id=i.invoice_id\n   GROUP BY 1,2)\nSELECT cls, count(*) jobs, coalesce(sum(s.q),0) wr_pieces, round(coalesce(sum(s.val),0),0) wr_scrap_value,\n round(coalesce(sum(cr.amt) FILTER (WHERE cr.reason IN ('does not fit','wrong dimensions','nonconforming')),0),0) fit_credit,\n coalesce(sum(cr.n) FILTER (WHERE cr.reason IN ('does not fit','wrong dimensions','nonconforming')),0) fit_credits_n,\n round(coalesce(sum(cr.amt),0),0) all_credit, coalesce(sum(cr.n),0) all_credits_n\nFROM c LEFT JOIN s USING(job_id) LEFT JOIN cr USING(job_id) GROUP BY ALL ORDER BY cls",
  "columns": [
   "cls",
   "jobs",
   "wr_pieces",
   "wr_scrap_value",
   "fit_credit",
   "fit_credits_n",
   "all_credit",
   "all_credits_n"
  ],
  "row_count": 3,
  "rows": [
   [
    "other",
    76294,
    83,
    18458.0,
    10283.0,
    1,
    10283.0,
    1
   ],
   [
    "rev_mid_job_no_eco",
    248,
    1787,
    452946.0,
    212788.0,
    39,
    260898.0,
    57
   ],
   [
    "superseded_at_release",
    82,
    982,
    91614.0,
    92086.0,
    18,
    110705.0,
    23
   ]
  ],
  "error": null
 },
 {
  "id": "q384",
  "sql": "WITH ra_per_job AS (SELECT job_id, count(*) n FROM erp_return_authorisations GROUP BY 1),\ncm_job AS (SELECT cm.credit_id, cm.amount, cm.reason cm_reason, sl.job_id FROM erp_credit_memos cm JOIN erp_invoices i USING(invoice_id) JOIN erp_shipment_lines sl ON sl.shipment_id=i.shipment_id)\nSELECT (SELECT count(*) FROM erp_credit_memos) cms, (SELECT round(sum(amount),0) FROM erp_credit_memos) cm_total,\n (SELECT count(*) FROM ra_per_job WHERE n>1) jobs_multi_ra,\n (SELECT count(*) FROM cm_job) cm_job_rows, (SELECT count(DISTINCT credit_id) FROM cm_job) cm_distinct,\n (SELECT count(*) FROM cm_job WHERE job_id NOT IN (SELECT job_id FROM erp_return_authorisations)) cm_on_job_without_ra,\n (SELECT string_agg(r || ':' || n, '; ' ORDER BY r) FROM (SELECT cm_reason r, count(*) n FROM cm_job GROUP BY 1)) cm_reasons,\n (SELECT string_agg(r || ':' || n, '; ' ORDER BY r) FROM (SELECT reason r, count(*) n FROM erp_return_authorisations GROUP BY 1)) ra_reasons,\n (SELECT count(*) FROM (SELECT job_id FROM erp_shipment_lines GROUP BY 1 HAVING count(*)>1)) jobs_multi_ship",
  "columns": [
   "cms",
   "cm_total",
   "jobs_multi_ra",
   "cm_job_rows",
   "cm_distinct",
   "cm_on_job_without_ra",
   "cm_reasons",
   "ra_reasons",
   "jobs_multi_ship"
  ],
  "row_count": 1,
  "rows": [
   [
    81,
    381885.0,
    0,
    81,
    81,
    0,
    "return:81",
    "does not fit:14; nonconforming:21; per buyer:23; wrong dimensions:23",
    858
   ]
  ],
  "error": null
 },
 {
  "id": "q393",
  "sql": "SELECT round(2420*24.97,0) labour_cost_at_avg_wage, round(331519+2420*24.97,0) scrap_cost, round((331519+2420*24.97+304873)/10,0) per_year_cost_basis,\n round(100.0*(331519+2420*24.97)/544560,1) cost_pct_of_price, round((544560+304873)/10,0) original_per_year,\n round(304873.0/10,0) credits_per_year, round((331519+2420*24.97)/10,0) scrap_cost_per_year,\n 381885-(10283+260898+110705) credit_reconcile_diff",
  "columns": [
   "labour_cost_at_avg_wage",
   "scrap_cost",
   "per_year_cost_basis",
   "cost_pct_of_price",
   "original_per_year",
   "credits_per_year",
   "scrap_cost_per_year",
   "credit_reconcile_diff"
  ],
  "row_count": 1,
  "rows": [
   [
    60427.0,
    391946.0,
    69682.0,
    72.0,
    84943.0,
    30487.0,
    39195.0,
    -1
   ]
  ],
  "error": null
 },
 {
  "id": "q365",
  "sql": "WITH j AS (\n SELECT j.job_id, j.line_id, j.released_on, j.revision_issued, p.customer_id,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on<=j.released_on),'A') rec_rev,\n  (SELECT count(*) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on>j.released_on AND r.received_on<=coalesce(j.completed_on,'9999')) mid_job_revs,\n  (SELECT count(*) FROM eng_ecos e WHERE e.job_id=j.job_id) ecos\n FROM erp_jobs j JOIN erp_customer_parts p USING(part_id) WHERE j.released_on IS NOT NULL),\nrisk AS (SELECT * FROM j WHERE revision_issued<>rec_rev OR (mid_job_revs>0 AND ecos=0)),\ns AS (SELECT sr.job_id, sum(sr.quantity*l.unit_price) val FROM shop_scrap_reports sr JOIN erp_jobs jj USING(job_id) JOIN erp_so_lines l ON l.line_id=jj.line_id WHERE reason_code='wrong revision' GROUP BY 1),\ncr AS (SELECT ra.job_id, sum(cm.amount) amt FROM erp_return_authorisations ra JOIN erp_shipment_lines sl ON sl.job_id=ra.job_id JOIN erp_invoices i ON i.shipment_id=sl.shipment_id JOIN erp_credit_memos cm ON cm.invoice_id=i.invoice_id\n   WHERE ra.reason IN ('does not fit','wrong dimensions','nonconforming') GROUP BY 1),\ntot AS (SELECT count(*) jobs, sum(coalesce(s.val,0)) scrap_val, sum(coalesce(cr.amt,0)) credit_val FROM risk LEFT JOIN s USING(job_id) LEFT JOIN cr USING(job_id)),\ncust AS (SELECT customer_id, sum(coalesce(s.val,0)) v FROM risk LEFT JOIN s USING(job_id) GROUP BY 1)\nSELECT jobs, round(scrap_val,0) scrap_val, round(credit_val,0) credit_val, round((scrap_val+credit_val)/10,0) per_year_10y,\n (SELECT count(*) FROM cust WHERE v>0) cust_with_wr,\n (SELECT round(100*sum(v)/(SELECT sum(v) FROM cust),1) FROM (SELECT v FROM cust ORDER BY v DESC, customer_id LIMIT 5)) top5_share_pct\nFROM tot",
  "columns": [
   "jobs",
   "scrap_val",
   "credit_val",
   "per_year_10y",
   "cust_with_wr",
   "top5_share_pct"
  ],
  "row_count": 1,
  "rows": [
   [
    330,
    544560.0,
    304873.0,
    84943.0,
    37,
    51.0
   ]
  ],
  "error": null
 },
 {
  "id": "q387",
  "sql": "WITH j AS (\n SELECT j.job_id, j.part_id, j.line_id, j.quantity jq, j.released_on, j.completed_on, j.revision_issued,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on<=j.released_on),'A') rec_rev,\n  (SELECT count(*) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on>j.released_on AND r.received_on<=coalesce(j.completed_on,'9999')) mid,\n  (SELECT count(*) FROM eng_ecos e WHERE e.job_id=j.job_id) ecos\n FROM erp_jobs j WHERE j.released_on IS NOT NULL),\nrisk AS (SELECT * FROM j WHERE revision_issued<>rec_rev OR (mid>0 AND ecos=0)),\ns AS (SELECT sr.job_id, sum(sr.quantity) q FROM shop_scrap_reports sr WHERE reason_code='wrong revision' GROUP BY 1),\nv AS (SELECT r.job_id, s.q, r.jq, l.quantity lq, l.unit_price, s.q*l.unit_price val,\n   (SELECT sum(pl.amount) FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) WHERE po.job_id=r.job_id) mat,\n   (SELECT sum(hours) FROM shop_labour_entries le WHERE le.job_id=r.job_id AND rework=0) lab_h\n  FROM risk r JOIN s USING(job_id) JOIN erp_so_lines l ON l.line_id=r.line_id),\nrk AS (SELECT *, row_number() OVER (ORDER BY val DESC, job_id) rn FROM v)\nSELECT count(*) jobs_with_wr, round(sum(val),0) scrap_val_price, round(median(val),0) med_job_val,\n round(100*sum(val) FILTER (WHERE rn<=10)/sum(val),1) top10_jobs_share,\n count(*) FILTER (WHERE q>jq) scrap_gt_jobqty,\n round(sum(q*mat/jq),0) scrap_material_cost,\n round(sum(q*lab_h/jq),0) scrap_labour_hours,\n round(sum(unit_price*jq),0) job_revenue_these_jobs, round(sum(mat),0) mat_these_jobs, round(sum(lab_h),0) labh_these_jobs\nFROM rk",
  "columns": [
   "jobs_with_wr",
   "scrap_val_price",
   "med_job_val",
   "top10_jobs_share",
   "scrap_gt_jobqty",
   "scrap_material_cost",
   "scrap_labour_hours",
   "job_revenue_these_jobs",
   "mat_these_jobs",
   "labh_these_jobs"
  ],
  "row_count": 1,
  "rows": [
   [
    133,
    544560.0,
    2077.0,
    34.6,
    0,
    331519.0,
    2420.0,
    544560.0,
    331519.0,
    2420.0
   ]
  ],
  "error": null
 },
 {
  "id": "q363",
  "sql": "WITH j AS (\n SELECT j.job_id, j.part_id, j.line_id, j.released_on, j.revision_issued, p.customer_id,\n  coalesce((SELECT max(revision) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on<=j.released_on),'A') rec_rev,\n  (SELECT count(*) FROM eng_drawing_revisions r WHERE r.part_id=j.part_id AND r.received_on>j.released_on AND r.received_on<=coalesce(j.completed_on,'9999')) mid_job_revs,\n  (SELECT count(*) FROM eng_ecos e WHERE e.job_id=j.job_id) ecos\n FROM erp_jobs j JOIN erp_customer_parts p USING(part_id) WHERE j.released_on IS NOT NULL),\nc AS (SELECT *, CASE WHEN revision_issued<>rec_rev THEN 'superseded' WHEN mid_job_revs>0 AND ecos=0 THEN 'mid_no_eco' WHEN mid_job_revs>0 THEN 'mid_eco' ELSE 'other' END cls FROM j),\ns AS (SELECT job_id, sum(quantity) q FROM shop_scrap_reports WHERE reason_code='wrong revision' GROUP BY 1)\nSELECT substr(released_on,1,4) yr, count(*) FILTER (WHERE cls='superseded') sup_jobs, count(*) FILTER (WHERE cls='mid_no_eco') mid_no_eco_jobs, count(*) FILTER (WHERE cls='mid_eco') mid_eco_jobs,\n round(100.0*count(*) FILTER (WHERE cls='mid_eco')/nullif(count(*) FILTER (WHERE cls IN ('mid_eco','mid_no_eco')),0),1) pct_mid_with_eco,\n count(s.job_id) jobs_wr, coalesce(sum(s.q),0) wr_pieces, count(DISTINCT customer_id) FILTER (WHERE cls IN ('superseded','mid_no_eco')) cust_at_risk\nFROM c LEFT JOIN s USING(job_id) GROUP BY 1 ORDER BY 1",
  "columns": [
   "yr",
   "sup_jobs",
   "mid_no_eco_jobs",
   "mid_eco_jobs",
   "pct_mid_with_eco",
   "jobs_wr",
   "wr_pieces",
   "cust_at_risk"
  ],
  "row_count": 11,
  "rows": [
   [
    "2015",
    0,
    1,
    3,
    75.0,
    0,
    0,
    1
   ],
   [
    "2016",
    10,
    27,
    115,
    81.0,
    11,
    284,
    17
   ],
   [
    "2017",
    9,
    41,
    86,
    67.7,
    26,
    626,
    18
   ],
   [
    "2018",
    7,
    27,
    66,
    71.0,
    12,
    213,
    14
   ],
   [
    "2019",
    11,
    31,
    64,
    67.4,
    17,
    381,
    21
   ],
   [
    "2020",
    7,
    21,
    62,
    74.7,
    14,
    310,
    17
   ],
   [
    "2021",
    11,
    27,
    85,
    75.9,
    18,
    313,
    15
   ],
   [
    "2022",
    6,
    20,
    63,
    75.9,
    7,
    100,
    21
   ],
   [
    "2023",
    8,
    23,
    71,
    75.5,
    14,
    203,
    16
   ],
   [
    "2024",
    9,
    21,
    51,
    70.8,
    15,
    265,
    13
   ],
   [
    "2025",
    4,
    9,
    43,
    82.7,
    3,
    157,
    9
   ]
  ],
  "error": null
 }
]

Decide:
- "full": it identifies a planted problem's mechanism (what happens and where it shows in the business) with evidence from the records;
- "partly": the right effect with a wrong or missing cause, or one part of a two-part problem;
- "true, not planted": it matches no planted problem, and the truth tables confirm it;
- "wrong": the truth contradicts it;
- "unverifiable": the truth tables can't settle it.
Query the truth to check the finding's main claim and its size. Every number you write must come from your own queries, cited.

Save `grade.json`: {"finding": "F10", "grade": "full | partly | true, not planted | wrong | unverifiable", "problem": "the key's problem id, or null", "truth_queries": ["t3"], "why": "two or three sentences with the truth's numbers"}
