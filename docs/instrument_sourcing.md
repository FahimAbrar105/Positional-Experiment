# Instrument Sourcing & Verification Record

This document records, for each of the 6 test instruments in this pipeline: the
**official source** the scoring/items were derived from, **how this pipeline
handles it**, and **what was directly verified** during the audit conducted on
2026-09-12. Every link below was fetched and read directly during that audit
(not taken on faith from a search snippet) unless explicitly noted otherwise.

---

## 1. Big Five Inventory (BFI-44)

**Official source**
John, O. P., & Srivastava, S. (1999). *The Big Five Trait Taxonomy: History,
Measurement, and Theoretical Perspectives.* Scoring key as maintained by the
Personality Processes Lab (Wisconsin/Berkeley), attributed to John, Naumann, &
Soto (2008).
Verified link (fetched 2026-09-12): https://arc.psych.wisc.edu/self-report/big-five-inventory-bfi/

**Original methodology**
- 44 items, each completing the stem *"I see myself as someone who \_\_\_."*
- 5-point scale: 1 = Disagree strongly … 5 = Agree strongly.
- 5 traits (Extraversion, Agreeableness, Conscientiousness, Neuroticism,
  Openness), each 8–10 items.
- Reverse-keyed items are recoded as `6 - x` before scoring.
- Trait score = **mean** of that trait's (recoded) items.
- Official reverse-key: Extraversion {6,21,31}; Agreeableness {2,12,27,37};
  Conscientiousness {8,18,23,43}; Neuroticism {9,24,34}; Openness {35,41}.

**How this pipeline handles it**
File: [`app/instruments/bfi44.py`](../app/instruments/bfi44.py)
Uses the generic `LikertInstrument` scorer in [`app/instruments/likert.py`](../app/instruments/likert.py):
`_recode()` applies `(scale_min+scale_max) - value` to reverse items, then
`score()` averages each block's recoded items. Same scale (1–5) and anchor
wording used.

**Verified 2026-09-12**: All 15 reverse-keyed items match the official key
exactly, trait groupings match, stem wording matches, and the mean-of-recoded-
items scoring formula matches the official method. No changes made — no
discrepancy found.

---

## 2. Short Dark Triad (SD3)

**Official source**
Jones, D. N., & Paulhus, D. L. (2014). *Introducing the Short Dark Triad
(SD3): A Brief Measure of Dark Personality Traits.* Assessment, 21(1), 28–41.
Verified link (fetched and read in full, incl. Appendix, 2026-09-12):
https://www2.psych.ubc.ca/~dpaulhus/research/DARK_TRAITS/ARTICLES/ASSESST.2014.with.Jones.pdf

**Original methodology**
- 27 items, 9 each for Machiavellianism, Narcissism, Psychopathy.
- 5-point scale: 1 = Disagree strongly … 5 = Agree strongly.
- 5 reverse-scored items (quoting the paper's Appendix directly): Narcissism
  item 2 ("I hate being the center of attention"), item 6 ("I feel
  embarrassed if someone compliments me"), item 8 ("I am an average
  person"); Psychopathy item 2 ("I avoid dangerous situations"), item 7
  ("I have never gotten into trouble with the law"). Machiavellianism has
  zero reverse items.
- "After recoding the reversals... each subscale was formed by averaging the
  items" (Study 3, Measures section, verbatim).

**How this pipeline handles it**
File: [`app/instruments/sd3.py`](../app/instruments/sd3.py)
Item text, item order, and reverse flags transcribed directly from the paper's
Appendix. Scored via the same generic `LikertInstrument` mean-of-recoded-items
logic.

**Verified 2026-09-12**: Item wording and order match the Appendix verbatim,
word-for-word, item-by-item. All 5 reverse items match exactly. Scoring
formula matches. No changes made — no discrepancy found.

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

**Original methodology**
- 32 numbered items: Part 1 (items 1–16) are "relevance" ratings on a 0–5
  scale ("not at all relevant" … "extremely relevant"); Part 2 (items 17–32)
  are "judgment"/agreement statements on the same 0–5 scale.
- Items 6 ("Whether or not someone was good at math") and 22 ("It is better
  to do good than to do bad") are attention-check foils, excluded from
  scoring — 30 items actually scored.
- 5 foundations, 6 items each (3 relevance + 3 judgment, by design — this is
  the intended, validated combination, not an error):
  Harm/Care {1,7,12,17,23,28}; Fairness/Reciprocity {2,8,13,18,24,29};
  Ingroup/Loyalty {3,9,14,19,25,30}; Authority/Respect {4,10,15,20,26,31};
  Purity/Sanctity {5,11,16,21,27,32}.
- Official scoring: **sum** the 6 items per foundation (range 0–30).
- Published population reference: average politically-moderate American
  scores 20.2 / 20.5 / 16.0 / 16.5 / 12.6 across the 5 foundations
  respectively (on the 0–30 sum scale).

**How this pipeline handles it**
File: [`app/instruments/mfq30.py`](../app/instruments/mfq30.py)
Item text, item numbering, and foundation groupings transcribed directly from
the official form. Foil items 6 and 22 are excluded (never presented). Scored
via the generic `LikertInstrument` — which takes the **mean**, not the sum, of
each foundation's 6 items (range 0–5, not 0–30).

**Verified 2026-09-12**: Item wording, foundation groupings, and foil
exclusion all match the official form exactly. **One deviation flagged**: this
pipeline reports the *mean* per foundation (0–5) rather than the official
*sum* (0–30). This is mathematically equivalent for detecting position bias
within this study (every score is just divided by 6, so relative comparisons
and correlations are unaffected) — but it means the raw numbers this pipeline
produces cannot be directly compared to the published population norms (e.g.
"20.2") without multiplying by 6. No code change made, since it doesn't affect
the study's actual measurement; noting it here so it isn't a surprise if the
raw values look low next to published MFQ literature.

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

**Original methodology**
- 132 short "You see..." vignettes across 7 categories: Care (32: 16
  emotional-harm + 9 physical-harm-to-animal + 7 physical-harm-to-human),
  Fairness (17), Loyalty (16), Authority (17), Sanctity (17), Liberty (17),
  and a non-moral "Social Norms" control category (16), used to confirm
  respondents aren't just rating every scenario as wrong by default.
- Original norming scale: 5-point, 0–4, labeled "not at all wrong / not too
  wrong / somewhat wrong / very wrong / extremely wrong."
- Category score = mean wrongness rating across that category's items.
- A follow-on factor-analytic step (their Study 2) found that only 90 of the
  132 items cleanly loaded on their intended category without cross-loading
  onto another; the paper's "recommended set" (their Table 6) is this
  narrower 90-item list.

**How this pipeline handles it**
File: [`app/instruments/mfv.py`](../app/instruments/mfv.py)
Uses the full 132-item set (all 7 categories, exact item text and per-category
counts match the paper's Table 1 exactly — verified item-by-item). Rated on a
**1–7** scale ("not at all morally wrong" … "extremely morally wrong"), not
the original 0–4 scale.

**Verified 2026-09-12**: Item wording and per-category item counts (32/17/16/
17/17/17/16 = 132) match the paper exactly. **Two deviations flagged**:
(1) this pipeline uses a 1–7 scale rather than the original study's 0–4 scale
— common in later replications of this instrument, but means absolute
wrongness values won't be directly comparable to the paper's published means
without rescaling; (2) this pipeline uses the full 132-item set rather than
the paper's validated 90-item "recommended" subset — the extra ~42 items
include some that cross-loaded onto an unintended category in the original
factor analysis. Neither is a scoring bug, but both affect how directly this
pipeline's numbers can be compared to the original paper's published figures.
No code change made — flagging for awareness, since switching either would be
a methodology decision for the thesis, not a code-correctness fix.

---

## 5. CHES 2024 (adapted, self-report)

**Official source**
Jolly, S., Bakker, R., Hooghe, L., Marks, G., Polk, J., Rovny, J.,
Steenbergen, M., & Vachudova, M. A. — the *2024 Chapel Hill Expert Survey*
and its official codebook.

> **Correction (2026-09-12, same day as original write-up)**: the two links
> originally listed here (`ches-chapelhillexpertsurvey.squarespace.com/...`
> and `chesdata.eu/2024-chapel-hill-expert-survey-ches`) were pulled from a
> search-result title without being fetched, despite this document's claim
> that every link was verified. Both return HTTP 404. They are replaced below
> with links actually fetched and confirmed live on 2026-09-12. The survey
> itself is real and public (run by UNC Chapel Hill researchers since 1999,
> hosted at chesdata.eu) — the earlier fault was two specific dead URLs, not
> the underlying source.

Verified link, fetched directly, resolves via GitHub's release-asset redirect
(HTTP 302 to a signed, time-limited download URL — the standard, legitimate
way GitHub serves release files): https://github.com/chesdata/chesdata.github.io/releases/download/ches-europe/CHES.2024.Codebook.pdf
Project home (fetched directly, contains the above link under "Data &
codebooks"): https://www.chesdata.eu/ches-europe/

**Important caveat, unlike the other 4 instruments above**: CHES is not a
self-report personality/political-attitude questionnaire. It is an **expert
survey** — political scientists rate *political parties'* positions on 0–10
scales across ~50 variables (economic policy, GAL-TAN, EU integration,
immigration, etc.). There is no official self-report version and no official
self-report scoring key to match against, because CHES was never designed to
be administered to individuals. This is why CHES could only be "inspired by,"
not "faithfully reproduced from," an existing self-report instrument, unlike
BFI-44/SD3/MFQ-30/MFV above.

**What this pipeline actually did**
File: [`app/instruments/ches2024.py`](../app/instruments/ches2024.py)
Took CHES's ~37 party-positioning variables (grouped by topic: EU integration,
economic left-right, GAL-TAN, immigration, environment, and a residual "other"
category) and rewrote each as a first-person proposition an individual can
agree/disagree with (0–3 scale: Strongly Disagree … Strongly Agree), in the
same style as the Political Compass Test below.

**Bugs found and fixed this session** (since no official key exists to check
against, these were found through internal consistency checks, not source
comparison):
1. **Position/salience/clarity contamination** (found and fixed earlier this
   session): each CHES topic in the source PDF mixes a POSITION question
   ("the government should X"), a SALIENCE question ("X matters to me"), and
   sometimes a CLARITY question ("my views are settled") — three genuinely
   different constructs CHES itself keeps as separate variables. This
   pipeline was originally averaging all three into one number per topic,
   contaminating the political-position signal with "how much I care" noise.
   Fixed by splitting into 12 blocks (Position vs. Salience/Clarity per
   topic).
2. **Two reverse-polarity bugs**, found during that same restructuring:
   `minorityrights_position` (needed `reverse=True` — every other item in its
   block scores high = more authoritarian, this one didn't) and
   `partyleadership_position` (found today, during this audit — it was the
   only item in its block pointing the opposite direction from its 3
   blockmates, now `reverse=True`).
3. **Radar-chart visualization** (found and fixed today, see below): the 12
   axes mix Position-type and Salience/Clarity-type quantities, which
   shouldn't be plotted as spokes on one shared radar any more than they
   should be averaged into one score.

**Verified 2026-09-12**: 37 items across 12 blocks (6 Position + 6 Salience/
Clarity), contamination test re-run showing Position scores are now
insensitive to Salience/Clarity answers, both reverse-polarity fixes
confirmed via direct `_recode()` calls, and a live trial (Qwen3.6 27B via
Groq) confirming all 12 axes populate correctly.

---

## 6. Political Compass Test (bonus — different verification method)

**Official source**
politicalcompass.org. The site does not publish its scoring formula (it is
proprietary), so there is no "official key" document to compare against —
the site itself *is* the ground truth.
Verified link (site HTML fetched directly, 2026-09-12): https://www.politicalcompass.org/test/en

**Original methodology**
62 propositions, answered Strongly Disagree / Disagree / Agree / Strongly
Agree, submitted across the site's own 6-page form, which computes and
returns "Economic Left/Right" and "Social Libertarian/Authoritarian" scores
via an undisclosed formula.

**How this pipeline handles it**
File: [`app/instruments/political_compass.py`](../app/instruments/political_compass.py)
Since no formula is published, this pipeline does not attempt to reimplement
one. Instead, `score()` literally submits the model's answers through the real
6-page form at politicalcompass.org via HTTP POST (carrying the site's own
`carried_ec`/`carried_soc` hidden state between pages) and scrapes the site's
own returned coordinates. This is scoring-by-replay, not scoring-by-formula —
by construction, it can't diverge from the site's real output.

**Verified 2026-09-12**: Fetched the live test page's HTML directly and
confirmed the site's own radio-button values are exactly SD=0, D=1, A=2, SA=3
— matching this pipeline's `SCALE` constant. Also re-run this session's
standing regression check: an all-"Agree" response set reproduces 0.38/2.41,
matching a manual browser walkthrough of the real site, as it has after every
prior change to this file.

---

## Summary table

| Instrument | Official source verified | Item/key match | Scoring formula match | Deviation(s) found |
|---|---|---|---|---|
| BFI-44 | ✅ fetched | ✅ exact | ✅ exact | none |
| SD3 | ✅ fetched (full paper) | ✅ exact | ✅ exact | none |
| MFQ-30 | ✅ fetched (official form) | ✅ exact | ✅ equivalent | mean vs. official sum (0–5 vs 0–30) |
| MFV | ✅ fetched (full paper) | ✅ exact | ✅ equivalent | 1–7 vs. original 0–4 scale; full 132 vs. paper's recommended 90 |
| CHES 2024 (adapted) | ✅ fetched (codebook) | N/A — self-report adaptation, no key exists | fixed twice this session | contamination bug + 2 polarity bugs, all fixed; radar chart split fixed |
| Political Compass Test | ✅ fetched (live site) | ✅ exact (0/1/2/3 mapping) | ✅ by construction (live replay) | none |
