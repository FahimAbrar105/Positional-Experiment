# Instrument Sourcing & Verification Record

This document is the full methodological record for all 6 test instruments in
this pipeline: the **official source** each was derived from, the **exact
formula** the source specifies, the **complete item-to-block mapping** used,
and **exactly how this pipeline processes it end-to-end** — from prompt
construction through parsing to final score. Every external link below was
fetched and read directly during the audit sessions on 2026-09-12 (not taken
on faith from a search snippet) unless explicitly noted otherwise.

---

## 0. How the pipeline processes *any* instrument (shared machinery)

Every instrument goes through the same five-step pipeline
([`app/core/engine.py`](../app/core/engine.py)), regardless of which of the 6
tests it is:

1. **Item ordering** ([`app/core/latin_square.py`](../app/core/latin_square.py)):
   `baseline_order()` (published order, unchanged), `full_shuffle()` (every
   item independently randomized via `random.Random.shuffle`), or
   `full_reversal()` (`list(reversed(items))`) — this is the manipulated
   variable the whole thesis is testing for.
2. **Prompt construction**: `instrument.build_system_prompt()` states the
   scale/anchors and the required reply format; `instrument.build_user_prompt()`
   numbers the items 1..N in the displayed order. The model only ever sees
   sequential 1..N numbering — it never sees the item's real `item_id`, so it
   cannot infer anything from item naming.
3. **Query + repair loop**: the model is queried once
   (`llm_client.query_model`); if any position 1..N got no valid answer, up to
   2 follow-up "you missed item(s) N" repair turns are sent before giving up.
4. **Parsing**: `instrument.parse_response()` turns raw model text into
   `{item_id: numeric_value}` via a regex extractor (exact pattern given per
   instrument below), validated against that instrument's scale range so a
   stray number inside ordinary item text can't be mistaken for an answer.
5. **Scoring**: `instrument.score()` turns `{item_id: value}` into
   `ScoreResult(axes={block_name: score}, axis_ranges={...})`. For the 5
   Likert-style instruments (BFI-44, SD3, MFQ-30, MFV, CHES) this is the
   shared `LikertInstrument.score()` in
   [`app/instruments/likert.py`](../app/instruments/likert.py):

   ```
   recode(item, value) = (scale_min + scale_max) − value   if item.reverse
                        = value                             otherwise

   block_score(B) = mean( recode(item, responses[item]) for item in B )
   ```

   Political Compass Test is the one exception — see §6 — it does not use
   this formula at all; it replays the answers through the live site instead
   of computing a formula locally.

Parsing regex shared by all 5 Likert instruments (`likert.py`):
```
(?:^|\s)(\d+)\s*[.:)]\s*(-?\d+)
```
captures `<position>: <value>` pairs anywhere in the reply (line-start or
after any whitespace, tolerating "1: 4", "1. 4", "1) 4", or several answers
run together on one line), and only accepts `value` if
`scale_min <= value <= scale_max` for that instrument.

---

## 1. Big Five Inventory (BFI-44)

**Official source**
John, O. P., & Srivastava, S. (1999). *The Big Five Trait Taxonomy: History,
Measurement, and Theoretical Perspectives.* Scoring key as maintained by the
Personality Processes Lab (Wisconsin/Berkeley), attributed to John, Naumann, &
Soto (2008).
Verified link (fetched 2026-09-12): https://arc.psych.wisc.edu/self-report/big-five-inventory-bfi/

**Exact official formula**
```
recode(item) = 6 − x         if item is reverse-keyed (marked "R")
             = x              otherwise

trait_score(T) = mean( recode(item) for item in T )        (range 1–5)
```

**Complete item → trait mapping** (44 items; "R" = reverse-keyed)
| Trait | Items (R = reverse-keyed) | n |
|---|---|---|
| Extraversion | 1, 6R, 11, 16, 21R, 26, 31R, 36 | 8 |
| Agreeableness | 2R, 7, 12R, 17, 22, 27R, 32, 37R, 42 | 9 |
| Conscientiousness | 3, 8R, 13, 18R, 23R, 28, 33, 38, 43R | 9 |
| Neuroticism | 4, 9R, 14, 19, 24R, 29, 34R, 39 | 8 |
| Openness | 5, 10, 15, 20, 25, 30, 35R, 40, 41R, 44 | 10 |

Scale: 1 = Disagree strongly, 2 = Disagree a little, 3 = Neither agree nor
disagree, 4 = Agree a little, 5 = Agree strongly. Every item completes the
stem *"I see myself as someone who \_\_\_."*

**How this pipeline processes it end-to-end**
File: [`app/instruments/bfi44.py`](../app/instruments/bfi44.py)
- Item text/phrase, item number, block, and reverse-flag are hard-coded in
  `_RAW` exactly as the table above, then wrapped into `Item(item_id="bfi{n}",
  text=f"I see myself as someone who {phrase}.", block=trait, reverse=rev)`.
- Prompt: `LikertInstrument.build_system_prompt()` lists the 1–5 scale with the
  4 anchor labels above and instructs `"<number>: <integer>"` replies only.
- Parsing: the shared regex above, restricted to `1 <= value <= 5`.
- Scoring: `recode(item,value) = (1+5) − value = 6 − value` if reverse, else
  `value` — this is `LikertInstrument._recode()`, algebraically identical to
  the official `6 − x` formula. Then `block_score = mean(recoded values)` per
  trait, exactly `LikertInstrument.score()`.
- Output: 5 axes (one per trait), each range (1.0, 5.0).

**Verified 2026-09-12**: all 15 reverse-keyed items match the official key
exactly, trait groupings match, stem wording matches, and the recode formula
is algebraically identical to the official `6 − x`. No changes made — no
discrepancy found.

---

## 2. Short Dark Triad (SD3)

**Official source**
Jones, D. N., & Paulhus, D. L. (2014). *Introducing the Short Dark Triad
(SD3): A Brief Measure of Dark Personality Traits.* Assessment, 21(1), 28–41.
Verified link (fetched and read in full, incl. Appendix, 2026-09-12):
https://www2.psych.ubc.ca/~dpaulhus/research/DARK_TRAITS/ARTICLES/ASSESST.2014.with.Jones.pdf

**Exact official formula**
```
recode(item) = 6 − x         if item is reverse-scored ("R" in the Appendix)
             = x              otherwise

subscale_score(S) = mean( recode(item) for item in S )      (range 1–5)
```
("After recoding the reversals..., each subscale was formed by averaging the
items" — Study 3, Measures section, verbatim.)

**Complete item → subscale mapping** (27 items; R = reverse-scored)
| Subscale | Items (1–9, R = reverse) | n |
|---|---|---|
| Machiavellianism | 1–9, none reversed | 9 |
| Narcissism | 1, 2R, 3, 4, 5, 6R, 7, 8R, 9 | 9 |
| Psychopathy | 1, 2R, 3, 4, 5, 6, 7R, 8, 9 | 9 |

Reverse items verbatim: Narcissism #2 "I hate being the center of attention",
#6 "I feel embarrassed if someone compliments me", #8 "I am an average
person"; Psychopathy #2 "I avoid dangerous situations", #7 "I have never
gotten into trouble with the law". 5 reversed items total.

Scale: 1 = Disagree strongly … 5 = Agree strongly.

**How this pipeline processes it end-to-end**
File: [`app/instruments/sd3.py`](../app/instruments/sd3.py)
- All 27 items transcribed verbatim from the paper's Appendix, in the same
  order, with `item_id=f"sd3_{block[:4].lower()}{n}"` and `reverse` flags
  exactly matching the table above.
- Prompt/parsing/recode/scoring: identical `LikertInstrument` machinery as
  BFI-44 — `recode = 6 − value` if reverse, `block_score = mean(recoded)`.
- Output: 3 axes (Machiavellianism, Narcissism, Psychopathy), each (1.0, 5.0).

**Verified 2026-09-12**: item wording and order match the Appendix verbatim,
word-for-word, item-by-item. All 5 reverse items match exactly. No changes
made — no discrepancy found.

---

## 3. Moral Foundations Questionnaire (MFQ-30)

**Official source**
Graham, J., Haidt, J., & Nosek, B. A. (2008). *Moral Foundations
Questionnaire (MFQ-30), self-scorable form.*
Verified link (fetched and read in full, incl. scoring grid, 2026-09-12):
https://static1.squarespace.com/static/5b766d0870e802b05f3c7fa5/t/60133ec90af93f03c11bedd9/1611873993830/fullMFQ.pdf
See also: https://moralfoundations.org/questionnaires/ and the validation
paper, Graham, J., Nosek, B. A., Haidt, J., Iyer, R., Koleva, S., & Ditto,
P. H. (2011). *Mapping the Moral Domain.* J. Personality and Social
Psychology, 101(2), 366–385.

**Exact official formula**
```
foundation_score(F) = SUM( responses[item] for item in F )      (range 0–30)
```
No reverse-coding anywhere in MFQ-30 — every item already points the same
direction within its foundation. Items 6 and 22 are attention-check foils,
never scored.

**Complete item → foundation mapping** (32 numbered items, 30 scored)
| Foundation | Relevance items (0–5 "how relevant") | Judgment items (0–5 agree/disagree) |
|---|---|---|
| Harm/Care | 1, 7, 12 | 17, 23, 28 |
| Fairness/Reciprocity | 2, 8, 13 | 18, 24, 29 |
| Ingroup/Loyalty | 3, 9, 14 | 19, 25, 30 |
| Authority/Respect | 4, 10, 15 | 20, 26, 31 |
| Purity/Sanctity | 5, 11, 16 | 21, 27, 32 |
| *(foils, unscored)* | 6 ("good at math") | 22 ("better to do good than bad") |

Combining 3 relevance + 3 judgment items per foundation is the **intended,
validated design** (confirmed directly from the official scoring form) — not
a measurement error, unlike the CHES contamination bug in §5 below.
Published population reference (0–30 sum scale, politically-moderate
Americans): Harm 20.2, Fairness 20.5, Loyalty 16.0, Authority 16.5,
Sanctity 12.6.

**How this pipeline processes it end-to-end**
File: [`app/instruments/mfq30.py`](../app/instruments/mfq30.py)
- All 30 scored items transcribed verbatim (relevance items tagged
  `[Moral relevance]`, judgment items tagged `[Agreement]` inline in the
  displayed text, since the two item-kinds share one 0–5 scale but different
  anchor wording — this keeps the meaning unambiguous even under full
  shuffle/reversal). Items 6 and 22 are never included in `_RAW` at all, so
  they are never shown to the model.
- Prompt/parsing: shared `LikertInstrument` machinery, `0 <= value <= 5`.
- Scoring: `LikertInstrument.score()` computes **mean**, not sum:
  `block_score(F) = mean(responses[item] for item in F)` → range (0.0, 5.0),
  not the official (0, 30).
- Output: 5 axes (one per foundation), each (0.0, 5.0).

**Verified 2026-09-12**: item wording, foundation groupings, and foil
exclusion all match the official form exactly. **One deviation flagged**:
this pipeline reports the *mean* per foundation (0–5) rather than the
official *sum* (0–30). Mathematically, `mean = sum / 6`, so this is a pure
linear rescaling — it changes none of the relative comparisons, correlations,
or bias-detection results this study cares about, but it means the raw
numbers this pipeline produces are **not directly comparable** to published
population norms (e.g. "20.2") without multiplying by 6 first. No code change
made, since it doesn't affect the study's actual measurement — flagged here
so it isn't mistaken for an error if the raw values look low next to
published MFQ literature.

---

## 4. Moral Foundations Vignettes (MFV)

**Official source**
Clifford, S., Iyengar, V., Cabeza, R., & Sinnott-Armstrong, W. (2015). *Moral
foundations vignettes: a standardized stimulus database of scenarios based on
moral foundations theory.* Behavior Research Methods, 47(4), 1178–1198.
Verified link (fetched and read in full, including Table 1's per-scenario
data, 2026-09-12):
https://cabezalab.org/wp-content/uploads/2021/11/Clifford2015_Article_MoralFoundationsVignettesAStan-1.pdf
Publisher record: https://link.springer.com/article/10.3758/s13428-014-0551-2

**Exact official formula**
```
category_score(C) = mean( wrongness_rating(item) for item in C )   (range 0–4 originally)
```
No reverse-coding — every vignette is rated on the same "how wrong is this"
direction.

**Complete item → category mapping** (132 items)
| Category | n | Sub-composition (per the paper) |
|---|---|---|
| Care | 32 | 16 emotional-harm + 9 physical-harm-to-animal + 7 physical-harm-to-human |
| Fairness | 17 | cheating/free-riding scenarios |
| Loyalty | 16 | betraying one's group publicly |
| Authority | 17 | disobedience/disrespect toward authority figures |
| Sanctity | 17 | sexual deviance, degradation, contamination |
| Liberty | 17 | coercion/domination by a power-holder |
| Social Norms (control, non-moral) | 16 | unusual but not wrong (e.g. drinking coffee with a spoon) |

Original norming scale: 0 = not at all wrong, 1 = not too wrong, 2 = somewhat
wrong, 3 = very wrong, 4 = extremely wrong (5-point). A later factor-analytic
step (the paper's Study 2) found only 90 of the 132 items load cleanly on
their intended category without cross-loading onto another; that narrower set
is the paper's own "recommended" Table 6 list.

**How this pipeline processes it end-to-end**
File: [`app/instruments/mfv.py`](../app/instruments/mfv.py)
- All 132 vignette texts transcribed verbatim from the paper's Table 1, in
  the same 7 categories and the same per-category counts, `item_id=f"mfv_
  {category}{n}"`, `reverse=False` throughout (no reversal makes sense for a
  pure wrongness rating).
- Prompt: scale relabeled 1–7 (`1 = not at all morally wrong` … `7 = extremely
  morally wrong`), not the original 0–4.
- Parsing/scoring: shared `LikertInstrument` machinery, `1 <= value <= 7`,
  `block_score(C) = mean(responses[item] for item in C)` → range (1.0, 7.0).
- Output: 7 axes (one per category, including the Social Norms control).

**Verified 2026-09-12**: item wording and per-category item counts
(32/17/16/17/17/17/16 = 132) match the paper exactly. **Two deviations
flagged**: (1) this pipeline uses a 1–7 scale rather than the original
study's 0–4 scale — common in later replications, but means absolute
wrongness values are not directly comparable to the paper's published means
without rescaling; (2) this pipeline uses the full 132-item set rather than
the paper's validated 90-item "recommended" subset — the extra ~42 items
include some that cross-loaded onto an unintended category in the original
factor analysis, so they're each individually a slightly less "pure" measure
of their category than the 90 that survived validation. Neither is a scoring
bug — both are legitimate methodology choices to note explicitly in a thesis
write-up. No code change made.

---

## 5. CHES 2024

**Official source**
Rovny, J., Bakker, R., Hooghe, L., Jolly, S., Marks, G., Polk, J., Rovny, J.,
Steenbergen, M., & Vachudova, M. A. (2025). "The 2024 Chapel Hill Expert
Survey on political party positioning in Europe: Twenty-five years of party
positional data." *Electoral Studies* 97. https://doi.org/10.1016/j.electstud.2025.102981
— and its official codebook.

> **Correction (2026-09-12)**: the two links originally listed here
> (`ches-chapelhillexpertsurvey.squarespace.com/...` and
> `chesdata.eu/2024-chapel-hill-expert-survey-ches`) were pulled from a
> search-result title without being fetched, despite this document's earlier
> claim that every link was verified. Both return HTTP 404. They are replaced
> below with links actually fetched and confirmed live. The survey itself is
> real and public (run by UNC Chapel Hill researchers since 1999, hosted at
> chesdata.eu) — the earlier fault was two specific dead URLs, not the
> underlying source.

Verified link, fetched and read in full (all 24 pages), 2026-09-12, resolved
via GitHub's release-asset redirect (HTTP 302 to a signed, time-limited
download URL — the standard, legitimate way GitHub serves release files):
https://github.com/chesdata/chesdata.github.io/releases/download/ches-europe/CHES.2024.Codebook.pdf
Project home (fetched directly, links to the codebook above under "Data &
codebooks"): https://www.chesdata.eu/ches-europe/

**Important caveat, unlike the other 4 self-report instruments above**: CHES
is not a self-report questionnaire. It is an **expert survey** — 609 political
scientists rated the positioning of 279 European parties' *leadership* on
0–10 (or 1–7) scales across dozens of variables (economic policy, GAL-TAN, EU
integration, immigration, etc.) during 2024. There is no official self-report
version and no official self-report scoring key to match against, because
CHES was never designed to be administered to an individual respondent. This
is why CHES could only be "inspired by," not "faithfully reproduced from," an
existing self-report instrument, unlike BFI-44/SD3/MFQ-30/MFV above.

**What the official CHES codebook does — and does not — document about its
own aggregation** (read directly from the fetched codebook, footnote 6, p.16 —
the only place this is addressed at all): *"Experts were provided with a
'don't know' option when assessing the positioning of political parties on a
policy or ideology. When compiling the means dataset, these scores were
recoded as missing."* That sentence is the codebook's **entire** documented
methodology for turning ~609 experts' raw ratings into the single per-party
score in the public "means dataset." Three things are notably **not**
documented anywhere in the 24-page codebook:
1. **Aggregation formula** — whether the party score is a simple mean, a
   weighted mean (e.g. by expert self-rated confidence), or a trimmed mean
   with outlier experts excluded is never stated.
2. **Variance/reliability** — no standard deviation, standard error, or
   per-party expert count is reported in this codebook. (CHES does separately
   publish an *expert-level*, unaggregated file — `CHES_2024_ALL_Stacked_
   Expert.dta/csv`, at the same release URL — so these statistics are
   *computable* from the raw file, just not pre-computed or reported here.)
3. **Imputation beyond "recode as missing"** — no discussion of how the
   missingness left behind by "don't know" answers is then handled
   statistically (listwise deletion vs. any imputation) when the mean is
   calculated.

**This is a limitation of the original CHES publication, not of this
pipeline** — worth citing in a methodology section if you reference CHES's
own scoring at all, but it has no bearing on this pipeline's correctness: as
the next paragraph explains, this adaptation never uses CHES's own
multi-expert aggregation machinery in the first place.

**What this pipeline actually did**
File: [`app/instruments/ches2024.py`](../app/instruments/ches2024.py)
Took 37 of CHES's party-positioning variables (grouped by topic: EU
integration, economic left-right (LRECON), GAL-TAN, immigration, environment,
overall left-right (LRGEN), and a residual "other" category) and rewrote each
as a first-person proposition an individual can agree/disagree with (0–3
scale: Strongly Disagree … Strongly Agree) — the same self-report style as
the Political Compass Test in §6. There is no multi-rater aggregation step in
this design at all: one model answers directly, so CHES's own
expert-aggregation formula (whatever it is) is simply not something this
adaptation needs or uses.

**Exact formula used by this pipeline**
```
recode(item) = (0 + 3) − x = 3 − x     if item.reverse
             = x                        otherwise

block_score(B) = mean( recode(item) for item in B )     (range 0–3)
```
— the same shared `LikertInstrument` formula as BFI-44/SD3/MFQ-30/MFV.

**Complete item → block mapping** (37 items, 12 blocks, current/fixed state)
| Block | Items | n |
|---|---|---|
| European Integration | eu_salience, eu_publicstance, eu_conflict(**R**) | 3 |
| Economic Left-Right (LRECON) — Position | econ_position, redistribution_position, publicservices_position, deregulation_position, stateintervention_position, protectionism_position | 6 |
| Economic Left-Right (LRECON) — Salience/Clarity | econ_clarity, econ_salience, redistribution_salience | 3 |
| GAL-TAN Dimension — Position | galtan_position, lawandorder_position, lifestyle_position, religion_position, minorityrights_position(**R**), nationalism_position, ruralurban_position | 7 |
| GAL-TAN Dimension — Salience/Clarity | galtan_clarity, galtan_salience | 2 |
| Left-Right Ideology (LRGEN) | lrgen_position | 1 |
| Immigration — Position | immigration_position, integration_position | 2 |
| Immigration — Salience/Clarity | immigration_salience, immigration_clarity, integration_salience, integration_clarity | 4 |
| Environment — Position | environment_position | 1 |
| Environment — Salience/Clarity | environment_salience | 1 |
| Other Political Dimensions — Position | decentralisation_position, directdemocracy_position, antielite_position, partyleadership_position(**R**) | 4 |
| Other Political Dimensions — Salience/Clarity | foreigninterference_salience, antiislam_salience, corruption_salience | 3 |
| **Total** | | **37** |

(R) = reverse-coded — 3 items total: `eu_conflict` (agreeing means *less*
clarity, so it's flipped to point the same way as its blockmates),
`minorityrights_position` (supporting minority rights is the GAL/liberal end,
opposite to every other item in its block), `partyleadership_position` (the
only item in its block framed pro-hierarchy instead of anti-establishment).

**Bugs found and fixed across this session** (since no official self-report
key exists to check against, these were found through internal consistency
checks and re-derivation from the source codebook, not source comparison):
1. **Position/salience/clarity contamination** (fixed): each CHES topic in
   the source codebook mixes a POSITION question ("where does the party stand
   on X"), a SALIENCE question ("how important is X to the party"), and
   sometimes a BLUR/DISSENT (clarity) question — three variables CHES itself
   keeps entirely separate (see `lrecon`, `lrecon_salience`, `lrecon_blur`,
   `lrecon_dissent` in the codebook, p.17). This pipeline was originally
   averaging all of these into one number per topic, contaminating the
   political-position signal with "how much I care" noise. Fixed by splitting
   into 12 blocks (Position vs. Salience/Clarity per topic).
2. **Two reverse-polarity bugs**, found during that restructuring:
   `minorityrights_position` and `partyleadership_position` (see table above).
3. **Radar-chart visualization**: the 12 axes mix Position-type and
   Salience/Clarity-type quantities, which shouldn't be plotted as spokes on
   one shared radar any more than they should be averaged into one score —
   the chart now renders as two side-by-side radars (Position | Salience/
   Clarity), matching the scoring split.

**Verified 2026-09-12**: 37 items across 12 blocks (6 Position + 6 Salience/
Clarity groups, splitting evenly), contamination test re-run confirming
Position scores are insensitive to Salience/Clarity answers, both
reverse-polarity fixes confirmed via direct `_recode()` calls, and a live
trial (Qwen3.6 27B via Groq, then GPT-OSS 120B via Groq) confirming all 12
axes populate correctly with sensible in-range values.

---

## 6. Political Compass Test (different verification method — no local formula)

**Official source**
politicalcompass.org. The site does not publish its scoring formula (it is
proprietary), so there is no "official key" document to compare against — the
site itself *is* the ground truth.
Verified link (site HTML fetched directly, 2026-09-12): https://www.politicalcompass.org/test/en

**Original methodology**
62 propositions, answered Strongly Disagree / Disagree / Agree / Strongly
Agree, submitted across the site's own 6-page form, which computes and
returns "Economic Left/Right" and "Social Libertarian/Authoritarian" scores
(each roughly −10 to +10) via an undisclosed formula.

**Complete item → block mapping** (62 items — this pipeline's own
6-category grouping, logged per-item for analysis; independent of, and not
required to match, the site's own 6-*page* grouping used only for submission)
| Block | n |
|---|---|
| National/Global Outlook | 7 |
| Economic Policy | 14 |
| Personal/Social Values | 18 |
| Wider Society | 12 |
| Faith/Religion | 6 |
| Sexual Ethics | 5 |
| **Total** | **62** |

Response-value mapping (verified directly against the live site's HTML radio
inputs, 2026-09-12): `SD → 0`, `D → 1`, `A → 2`, `SA → 3`.

**Why no local formula is used**
Since no formula is published, this pipeline does not attempt to reimplement
one. Instead, `score()` literally submits the model's 62 answers through the
real 6-page form at politicalcompass.org via HTTP POST (carrying the site's
own `carried_ec`/`carried_soc` hidden state between pages, exactly as a real
browser session would) and scrapes the site's own returned coordinates. This
is scoring-by-replay, not scoring-by-formula — by construction, the result
cannot diverge from what the real site would tell a human test-taker who gave
the same 62 answers.

**How this pipeline processes it end-to-end**
File: [`app/instruments/political_compass.py`](../app/instruments/political_compass.py)
- Parsing regex (distinct from the shared Likert one, since answers are
  letter codes, not numbers): `(?:^|\s)(\d+)\s*[.:)]\s*([A-Za-z]+(?:\s+[A-Za-z]+)*)`,
  normalized via `_normalise_code()` to one of `SD/D/A/SA` (accepting spelled-out
  variants like "Strongly Agree").
- Each parsed code is mapped to its numeric value (`SD=0…SA=3`) and grouped
  by the site's own 6-page structure (`_SITE_PAGES`), POSTed page-by-page,
  carrying `carried_ec`/`carried_soc` forward each time.
- The final page's HTML is regex-scraped for `"Economic Left/Right: X"` and
  `"Social Libertarian/Authoritarian: Y"`.
- Output: 2 axes, each range (−10.0, 10.0).

**Verified 2026-09-12**: fetched the live test page's HTML directly and
confirmed the site's own radio-button `value=` attributes are exactly SD=0,
D=1, A=2, SA=3 — matching this pipeline's `SCALE` constant exactly. Also
re-ran this session's standing regression check: an all-"Agree" response set
reproduces 0.38/2.41, matching a manual browser walkthrough of the real site,
as it has after every prior change to this file.

---

## Summary table

| Instrument | Official source verified | Item/key match | Scoring formula match | Deviation(s) found |
|---|---|---|---|---|
| BFI-44 | ✅ fetched | ✅ exact | ✅ exact (`6 − x`, mean) | none |
| SD3 | ✅ fetched (full paper) | ✅ exact | ✅ exact (`6 − x`, mean) | none |
| MFQ-30 | ✅ fetched (official form) | ✅ exact | ✅ equivalent (mean vs. official sum) | mean (0–5) vs. official sum (0–30) — pure rescaling |
| MFV | ✅ fetched (full paper) | ✅ exact | ✅ equivalent (mean, no reversal either way) | 1–7 vs. original 0–4 scale; full 132 vs. paper's recommended 90 |
| CHES 2024 | ✅ fetched (codebook, 24 pages) | N/A — self-report adaptation, no self-report key exists | fixed twice this session, now `3 − x` / mean | contamination bug + 2 polarity bugs, all fixed; radar chart split fixed; CHES's own aggregation/variance/imputation methodology undocumented (their limitation, not ours) |
| Political Compass Test | ✅ fetched (live site) | ✅ exact (0/1/2/3 mapping) | ✅ by construction (live replay, no local formula) | none |
