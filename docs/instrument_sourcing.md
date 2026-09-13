# Instrument Sourcing & Methodology Record

This is my methodology reference for all 6 tests in the pipeline: where each
instrument's scoring comes from, the exact formula it uses, the complete
item-to-block mapping, and how I process it end-to-end in code — from prompt
construction through parsing to the final score.

---

## 0. How I process any instrument (shared machinery)

Every instrument goes through the same five-step pipeline
(`app/core/engine.py`), regardless of which of the 6 tests it is:

1. **Item ordering** (`app/core/latin_square.py`): `baseline_order()`
   (published order, unchanged), `full_shuffle()` (every item independently
   randomized across the entire instrument, ignoring block boundaries), or
   `full_reversal()` (the whole list reversed). This is the manipulated
   variable my thesis is testing for.
2. **Prompt construction**: the system prompt states the scale/anchors and
   required reply format; the user prompt numbers the items 1..N in whatever
   order they were displayed. The model only ever sees sequential numbering —
   never the item's internal ID — so it can't infer anything from item naming.
3. **Query + repair loop**: I query the model once; if any position 1..N got
   no valid answer, I send up to 2 follow-up "you missed item(s) N" repair
   turns before giving up.
4. **Parsing**: raw model text becomes `{item_id: numeric_value}` via a regex
   extractor, validated against that instrument's scale range so a stray
   number inside ordinary item text can't be mistaken for an answer.
5. **Scoring**: `{item_id: value}` becomes `{block_name: score}`. For the 5
   Likert-style instruments (BFI-44, SD3, MFQ-30, MFV, SRPD) I use one shared
   formula (`app/instruments/likert.py`):

   ```
   recode(item, value) = (scale_min + scale_max) − value   if item.reverse
                        = value                             otherwise

   block_score(B) = mean( recode(item, responses[item]) for item in B )
   ```

   The Political Compass Test is the one exception (§6) — it doesn't use this
   formula at all; it replays my answers through the live site instead of
   computing anything locally.

Parsing regex shared by all 5 Likert instruments:
```
(?:^|\s)(\d+)\s*[.:)]\s*(-?\d+)
```
captures `<position>: <value>` pairs anywhere in the reply (line-start or
after any whitespace, tolerating "1: 4", "1. 4", "1) 4", or several answers
run together on one line), and only accepts `value` if
`scale_min <= value <= scale_max` for that instrument.

---

## 1. Big Five Inventory (BFI-44)

**Source**: John, O. P., & Srivastava, S. (1999). *The Big Five Trait
Taxonomy: History, Measurement, and Theoretical Perspectives.* Scoring key
maintained by the Personality Processes Lab (Wisconsin/Berkeley), attributed
to John, Naumann, & Soto (2008).
Link: https://arc.psych.wisc.edu/self-report/big-five-inventory-bfi/

**Formula**
```
recode(item) = 6 − x         if item is reverse-keyed (marked "R")
             = x              otherwise

trait_score(T) = mean( recode(item) for item in T )        (range 1–5)
```

**Item → trait mapping** (44 items; "R" = reverse-keyed)
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

**Implementation**: `app/instruments/bfi44.py`. Item phrase, block, and
reverse-flag match the table above exactly. Scoring is the shared
`LikertInstrument._recode()`/`score()` — `6 − value` if reverse, then mean per
trait. 5 output axes, each ranging (1.0, 5.0).

---

## 2. Short Dark Triad (SD3)

**Source**: Jones, D. N., & Paulhus, D. L. (2014). *Introducing the Short
Dark Triad (SD3): A Brief Measure of Dark Personality Traits.* Assessment,
21(1), 28–41.
Link: https://www2.psych.ubc.ca/~dpaulhus/research/DARK_TRAITS/ARTICLES/ASSESST.2014.with.Jones.pdf

**Formula**
```
recode(item) = 6 − x         if item is reverse-scored ("R" in the Appendix)
             = x              otherwise

subscale_score(S) = mean( recode(item) for item in S )      (range 1–5)
```
("After recoding the reversals..., each subscale was formed by averaging the
items" — Study 3, Measures section, verbatim.)

**Item → subscale mapping** (27 items; R = reverse-scored)
| Subscale | Items (1–9, R = reverse) | n |
|---|---|---|
| Machiavellianism | 1–9, none reversed | 9 |
| Narcissism | 1, 2R, 3, 4, 5, 6R, 7, 8R, 9 | 9 |
| Psychopathy | 1, 2R, 3, 4, 5, 6, 7R, 8, 9 | 9 |

Reverse items: Narcissism #2 "I hate being the center of attention", #6 "I
feel embarrassed if someone compliments me", #8 "I am an average person";
Psychopathy #2 "I avoid dangerous situations", #7 "I have never gotten into
trouble with the law". Scale: 1 = Disagree strongly … 5 = Agree strongly.

**Implementation**: `app/instruments/sd3.py`. All 27 items transcribed
verbatim from the paper's Appendix, same order, same reverse flags. 3 output
axes (Machiavellianism, Narcissism, Psychopathy), each (1.0, 5.0).

---

## 3. Moral Foundations Questionnaire (MFQ-30)

**Source**: Graham, J., Haidt, J., & Nosek, B. A. (2008). *Moral Foundations
Questionnaire (MFQ-30), self-scorable form.*
Link: https://static1.squarespace.com/static/5b766d0870e802b05f3c7fa5/t/60133ec90af93f03c11bedd9/1611873993830/fullMFQ.pdf
Also: https://moralfoundations.org/questionnaires/ and Graham, J., Nosek,
B. A., Haidt, J., Iyer, R., Koleva, S., & Ditto, P. H. (2011). *Mapping the
Moral Domain.* J. Personality and Social Psychology, 101(2), 366–385.

**Formula**
```
foundation_score(F) = SUM( responses[item] for item in F )      (range 0–30)
```
No reverse-coding anywhere — every item already points the same direction
within its foundation. Items 6 and 22 are attention-check foils and are never
scored (or shown).

**Item → foundation mapping** (32 numbered items, 30 scored)
| Foundation | Relevance items (0–5 "how relevant") | Judgment items (0–5 agree/disagree) |
|---|---|---|
| Harm/Care | 1, 7, 12 | 17, 23, 28 |
| Fairness/Reciprocity | 2, 8, 13 | 18, 24, 29 |
| Ingroup/Loyalty | 3, 9, 14 | 19, 25, 30 |
| Authority/Respect | 4, 10, 15 | 20, 26, 31 |
| Purity/Sanctity | 5, 11, 16 | 21, 27, 32 |
| *(foils, unscored)* | 6 ("good at math") | 22 ("better to do good than bad") |

Combining 3 relevance + 3 judgment items per foundation is the official,
intended design (per the scoring form above) — relevance and judgment are two
deliberately different item formats measuring the same underlying foundation,
not two different constructs. Published reference (0–30 sum scale,
politically-moderate Americans): Harm 20.2, Fairness 20.5, Loyalty 16.0,
Authority 16.5, Sanctity 12.6.

**Implementation**: `app/instruments/mfq30.py`. Items tagged inline as
`[Moral relevance]` or `[Agreement]` so their meaning stays unambiguous even
under full shuffle/reversal. My scoring takes the **mean**, not the official
sum, so my output range is (0.0, 5.0) rather than (0, 30) — a pure rescaling
(`mean = sum / 6`) that doesn't change any relative comparison or correlation
this study relies on, but does mean my raw numbers aren't directly comparable
to the published population norms above without multiplying by 6 first.

---

## 4. Moral Foundations Vignettes (MFV)

**Source**: Clifford, S., Iyengar, V., Cabeza, R., & Sinnott-Armstrong, W.
(2015). *Moral foundations vignettes: a standardized stimulus database of
scenarios based on moral foundations theory.* Behavior Research Methods,
47(4), 1178–1198.
Link: https://cabezalab.org/wp-content/uploads/2021/11/Clifford2015_Article_MoralFoundationsVignettesAStan-1.pdf
Publisher record: https://link.springer.com/article/10.3758/s13428-014-0551-2

**Formula**
```
category_score(C) = mean( wrongness_rating(item) for item in C )
```
No reverse-coding — every vignette is rated on the same "how wrong is this"
direction.

**Item → category mapping** (132 items)
| Category | n | Composition |
|---|---|---|
| Care | 32 | 16 emotional-harm + 9 physical-harm-to-animal + 7 physical-harm-to-human |
| Fairness | 17 | cheating/free-riding scenarios |
| Loyalty | 16 | betraying one's group publicly |
| Authority | 17 | disobedience/disrespect toward authority figures |
| Sanctity | 17 | sexual deviance, degradation, contamination |
| Liberty | 17 | coercion/domination by a power-holder |
| Social Norms (control, non-moral) | 16 | unusual but not wrong (e.g. drinking coffee with a spoon) |

The original norming study used a 0–4 scale (not at all / not too / somewhat
/ very / extremely wrong) and later found only 90 of the 132 items load
cleanly on their intended category without cross-loading — that narrower set
is the paper's own "recommended" list.

**Implementation**: `app/instruments/mfv.py`. All 132 vignette texts
transcribed verbatim, same 7 categories and per-category counts. I use a 1–7
scale rather than the original 0–4 (common in later replications of this
instrument), and I use the full 132-item set rather than the paper's
validated 90-item subset — both are choices worth naming plainly in a
methods section, since either one affects whether my numbers compare directly
to the original paper's published figures.

---

## 5. Self-Reported Political Dimensions (SRPD)

SRPD is my own instrument, not a published one. I built it because I wanted
to test position bias on contemporary European political dimensions (EU
integration, GAL-TAN, immigration, etc.) that none of the other 5 tests
cover, and because I wanted a "Salience/Clarity" axis — how much a respondent
says they care, and how settled their view is — as its own separate
measurement, so I can study whether item order shifts *what* a model claims
to believe versus *how much* it claims to care.

**Inspiration, not a reproduction**: the topic structure is inspired by the
Chapel Hill Expert Survey (CHES) 2024 — Rovny, J., Bakker, R., Hooghe, L.,
Jolly, S., Marks, G., Polk, J., Steenbergen, M., & Vachudova, M. A. (2025).
"The 2024 Chapel Hill Expert Survey on political party positioning in
Europe." *Electoral Studies* 97. https://doi.org/10.1016/j.electstud.2025.102981
Codebook: https://github.com/chesdata/chesdata.github.io/releases/download/ches-europe/CHES.2024.Codebook.pdf
Project home: https://www.chesdata.eu/ches-europe/

CHES itself is an **expert survey** — 609 political scientists rating 279
parties' *leadership* positions, not a self-report questionnaire for
individuals — so there's no self-report scoring key to reproduce here. SRPD
takes 37 of CHES's party-positioning variables and rewrites each as a
first-person proposition an individual can agree or disagree with, in the
same style as the Political Compass Test in §6. I want to be precise about
this distinction in anything I write up: SRPD is my own instrument built on
CHES's topic list, not a validated adaptation of CHES's own methodology.

One limitation worth citing if I reference CHES's own scoring anywhere: the
2024 codebook documents its treatment of missing data in one sentence
(footnote 6, p.16 — *"Experts were provided with a 'don't know' option...
these scores were recoded as missing"*) but never states how the ~609
experts' ratings are aggregated into one party score (simple mean? weighted?
trimmed?), and reports no variance or reliability statistics for those scores
in the public "means" file. An unaggregated expert-level file exists
separately, so those statistics are computable from it, just not published
pre-computed. This doesn't affect SRPD's own design, since SRPD never uses
CHES's aggregation step at all — I'm just noting it as a limitation of the
source material I drew the topic list from.

**Formula**
```
recode(item) = (0 + 3) − x = 3 − x     if item.reverse
             = x                        otherwise

block_score(B) = mean( recode(item) for item in B )     (range 0–3)
```
— the same shared formula as BFI-44/SD3/MFQ-30/MFV.

**Item → block mapping** (37 items, 12 blocks)
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

(R) = reverse-coded, 3 items: `eu_conflict` (agreeing means *less* clarity, so
it's flipped to point the same way as its blockmates), `minorityrights_position`
(supporting minority rights is the liberal/GAL end, opposite to every other
item in that block), `partyleadership_position` (the only item in its block
framed pro-hierarchy instead of anti-establishment, flipped to match).

**Design decisions worth stating plainly**:
- I keep Position and Salience/Clarity as 12 separate blocks rather than
  averaging them per topic, because they measure genuinely different things
  — where someone stands on a policy versus how much they say they care about
  it or how settled their view is. Averaging them into one number per topic
  would let a "how much I care" answer distort a policy-position score.
  "Other Political Dimensions" is a heterogeneous grab-bag by nature (it was
  one in the source CHES categorization too) — I treat its Position block as
  a looser composite than the other topic blocks for that reason.
- `partyleadership_position` and `minorityrights_position` are reverse-coded
  so every item in their block points the same direction; without that, a
  model that consistently favors hierarchy (or consistently opposes minority
  protections) would show a *diluted* score in that block instead of a
  clearly authoritarian/traditional one, just from unrecoded polarity
  mismatch.
- The chart for SRPD renders as two stacked radars (Position, then Salience/
  Clarity) rather than one 12-spoke radar, for the same reason the scoring is
  split: plotting both kinds of quantity on one shared radar would visually
  reintroduce the exact comparison I split the scoring to avoid.

**Implementation**: `app/instruments/srpd.py`. 37 items, 12 blocks, 3
reverse-coded, scale 0–3 (Strongly Disagree … Strongly Agree).

---

## 6. Political Compass Test (no local formula — live replay)

**Source**: politicalcompass.org. The site doesn't publish its scoring
formula (it's proprietary), so the site itself is the ground truth.
Link: https://www.politicalcompass.org/test/en

**Methodology**: 62 propositions, answered Strongly Disagree / Disagree /
Agree / Strongly Agree, submitted across the site's own 6-page form, which
computes and returns "Economic Left/Right" and "Social Libertarian/
Authoritarian" scores (roughly −10 to +10 each) via an undisclosed formula.

**Item → block mapping** (62 items — my own 6-category grouping, logged
per-item for analysis; independent of the site's own 6-*page* submission
grouping)
| Block | n |
|---|---|
| National/Global Outlook | 7 |
| Economic Policy | 14 |
| Personal/Social Values | 18 |
| Wider Society | 12 |
| Faith/Religion | 6 |
| Sexual Ethics | 5 |
| **Total** | **62** |

Response mapping (matches the live site's own HTML radio inputs): `SD → 0`,
`D → 1`, `A → 2`, `SA → 3`.

**Why no local formula**: since none is published, I don't try to
reimplement one. `score()` submits my 62 answers through the real 6-page form
at politicalcompass.org via HTTP POST (carrying the site's own
`carried_ec`/`carried_soc` hidden state between pages, exactly as a browser
session would) and reads the site's own returned coordinates back. This is
scoring by replay, not by formula — the result can't diverge from what the
real site would tell a human test-taker giving the same 62 answers.

**Implementation**: `app/instruments/political_compass.py`. Parsing uses a
letter-code regex (`SD`/`D`/`A`/`SA`, including spelled-out variants),
normalized to `0`–`3`, grouped by the site's own 6-page structure, and POSTed
page by page. The final page's HTML is scraped for the two result lines.
Output: 2 axes, each (−10.0, 10.0).

---

## Summary

| Instrument | Formula | Items / blocks | Reverse-coded items |
|---|---|---|---|
| BFI-44 | `6 − x`, mean per trait | 44 / 5 | 15 |
| SD3 | `6 − x`, mean per subscale | 27 / 3 | 5 |
| MFQ-30 | mean per foundation (official: sum) | 30 scored (of 32) / 5 | 0 |
| MFV | mean per category | 132 / 7 | 0 |
| SRPD | `3 − x`, mean per block | 37 / 12 | 3 |
| Political Compass Test | live replay, no local formula | 62 / 6 | n/a |
