# ADR 0013: Compatibility scoring: two strategies over a fit graph

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-02 |
| **Scope** | US-10 (see how well an animal fits my home); the scoring of an animal against a Matchmaker profile |
| **Related** | [0008-matchmaker-profile](0008-matchmaker-profile.md), [0011-animal-match-profile](0011-animal-match-profile.md), [0005-fetch-animal-data](0005-fetch-animal-data.md), [MatchingAlgorithms](../../research/MatchingAlgorithms.md) |

## Context

ADR 0008 stores an adopter's answers and ADR 0011 translates an animal onto the
same scales, both so that scoring could come later. US-10 is that scoring: for one
animal, tell the adopter how well it fits their home, and why. The score has to be
explainable, because an adopter must be able to read the reasons behind a number,
and the team has no data on past adoptions, so nothing can be learned from outcomes.

A single weighted average is not enough. It cannot say that one serious mismatch
should sink an otherwise good match, and it cannot let the adopter choose how
demanding to be. The story was also narrowed during design: the first plan was a
ranked swipe page with pass and save. It became a score and its reasons on the
animal page, so that the algorithm and one real surface are delivered in this
iteration (decision 10). Ranking the catalog and remembering passes and saves are
left for later.

All numbers below are **placeholders**. They are business rules that the team has
to agree (AGENTS.md section 6), and they are gathered in one file so that review
and change are cheap (decision 4).

## Decisions

1. **A separate package.** The code lives in `models/compatibility/`, so it can
   depend on `animal` and `matchmaker_profile` without either of them depending on
   it. This avoids an import cycle.
2. **Strategy, template method and factory.**
   `CompatibilityStrategy.evaluate(adopter, animal) -> CompatibilityResult` is the
   interface. `FitGraphStrategy` is an abstract skeleton that runs the shared steps
   (decision 5) and leaves four policy choices to its subclasses, `LooseFitStrategy`
   and `StrictFitStrategy` (decision 6). `strategy_for(mode)` maps a
   `CompatibilityMode` to a strategy, and an unknown value raises
   `InvalidCompatibilityMode`, so callers never name a strategy class.
3. **A fit graph kept as flat data.** `FitGraph` holds the seven dimensions
   (the nodes) and three interactions (the edges) as plain tuples, with
   `assess`, `penalties` and `total_penalty`. It is a graph conceptually, but
   scoring is a single pass with no traversal, so a graph library or an adjacency
   structure would add machinery without a use. A strategy receives the graph, so a
   different graph can be passed in.
4. **Every business number lives in `rules.py`.** Pair tables, weights, which
   dimensions are critical or safety, maximum penalties, the cap and all wording
   are in `models/compatibility/rules.py`. `fit_graph.py` only wires them. Tests
   spell the tables out cell by cell, independently of the code.
5. **The shared pipeline.** For one adopter and one animal:
   1. Assess each dimension that applies to the adopter, giving a fit from 0 to 1,
      or no fit when the owner left the answer blank.
   2. Value the blanks with the strategy's `missing_fit`.
   3. Hide the animal if any safety dimension has fit 0 (decision 7), or if the
      strategy's own rule says so.
   4. Compute the base, the weighted average of the fits.
   5. Let the strategy turn the base into a score, then subtract the edge penalties
      times the strategy's `edge_strength`.
   6. Clamp to 0 to 100 and round half up (`CompatibilityResult.scored`).
6. **The two modes.**

   | | Loose ("flexible") | Strict |
   | :-- | :-- | :-- |
   | Blank owner answer counts as | 0.5 | 0.25 |
   | Score | `100 x base` | `100 x base x (1 - 0.5 x (1 - weakest))` |
   | Edge penalties | half | full |
   | Also hides the animal | no | a critical dimension with fit 0 |

   `weakest` is the lowest fit among the critical dimensions the owner answered, or
   1 if there are none. The strength 0.5 (`WEAKEST_LINK_STRENGTH`) was 1.0 in the
   first version, where one half-fit halved the whole score and an animal that fit
   well scored 46. It was softened after a manual test.
7. **A blank answer is never a "no".** It never hides an animal, and in strict it
   never counts as the weakest link, because that would let an owner who skipped a
   field cap an otherwise perfect animal. It costs only through the average, at the
   strategy's blank value. The only hard exclusion common to both modes is an
   explicit "not safe" for a household member the adopter has.
8. **Dimensions and interactions.**

   Dimensions (fit 0 to 1, weight in brackets). The household ones only count when
   the adopter has that member:
   * `activity` (1): asymmetric, a more energetic animal fits worse than a calmer
     one. Low against low is 1.0, low against moderate 0.5, low against high 0.2,
     moderate against low 0.8, moderate against high 0.5, high against low 0.6,
     high against moderate 0.8.
   * `time_alone` (1): a ceiling. Away longer than the animal tolerates is 0.5 one
     step over and 0.0 two steps over.
   * `experience` (1) and `space` (1): floors. Needing more than the adopter has is
     0.5 one step short and 0.0 two steps short. Housing is read as space offered
     (ADR 0011 decision 5).
   * `children`, `dogs`, `cats` (2 each): safe is 1.0, not safe is 0.0.

   Interactions (points taken off, each never firing on a blank answer):
   * training needs against experience: at most 15 (moderate against none 7.5,
     high against none 15, high against some 7.5);
   * noise level against housing: at most 10 (moderate in an apartment 5, high in
     an apartment 10, high in a house without a yard 5);
   * a baby animal against time away and experience: at most 15, the average of how
     long the adopter is away and how little experience they have. Only a baby
     triggers it.

   The total of all interactions is capped at 25, so a hard match still scores
   apart from a hopeless one.
9. **A derived life stage.** `AnimalMatchProfile` gains `training_needs`,
   `noise_level` and `life_stage`. The life stage is derived from the age in
   months: a baby is under 12, a senior is 96 or more, the same for dogs and cats,
   and an unknown age gives none. This amends ADR 0011: the animal-side values
   without an adopter counterpart are now `size`, `training_needs`, `noise_level`
   and `life_stage`, and the animal response exposes the three new fields.
10. **One animal, on request.**
    `GET /animals/{animal_id}/compatibility?mode=loose|strict` requires login, and
    `mode` defaults to loose. It returns `{mode, score, is_compatible, reasons}`,
    where each reason is `{text, kind}` and `kind` is strength, concern or unknown.
    An unknown or unpublished animal is a 404, the caller's own animal and an
    unknown mode are 422, and a caller without a Matchmaker profile is 409.
    `CompatibilityService.assess` reads the animal and the profile in a plain
    read-only session and delegates to the strategy. Nothing is stored, the mode is
    never persisted, and one user's choice never affects another.
11. **The frontend asks on a button press.** A "Calculate my fit" button on the
    animal page (a client component) calls a Server Action, which calls the
    endpoint with the user's token. The browser never calls the API (ADR 0005). A
    visitor sees an invitation to log in and the owner sees nothing.
12. **No cache.** Scoring costs about 40 microseconds per animal, measured over
    1,000 animals, so one request for one animal is negligible. A score is
    recomputed each time and cannot go stale.

## Consequences

* **Positive:** a score always comes with reasons, and the reasons are tagged, so
  the frontend can group them without parsing text.
* **Positive:** a rule changes in one file, and the tests that spell the tables out
  fail loudly when a number moves.
* **Positive:** a third mode, or a different graph, is a new subclass or a new
  argument, not a change to the pipeline.
* **Positive:** no migration and no new table. The feature adds one endpoint and
  three response fields.
* **Negative:** every number is a placeholder. The tables, weights, thresholds and
  caps are guesses until the team agrees them, and the strict softening shows how
  sensitive the result is to one constant.
* **Negative:** the blank values (0.5 and 0.25) and the hard exclusion only for an
  explicit "not safe" are policy choices that favour showing animals over hiding
  them. The team may prefer the opposite.
* **Negative:** an animal that is not suitable is shown on its own page with a
  banner, and is not hidden. This is a product decision to confirm.
* **Negative:** there is no ranking. An adopter must open each animal and press the
  button, so finding the best animal is slower than the original swipe idea.
* **Out of scope:** ranking or sorting the catalog by fit, passing and saving
  animals, a shortlist, the score on cards in the catalog, caching, and the
  user-facing names of the modes ("Flexible" and "Strict" are placeholders).

## Alternatives considered

* **One weighted-average strategy.** The first plan. It cannot express "one serious
  mismatch sinks the match", and it gives the adopter no way to be more demanding.
* **A real graph with traversal.** Nothing is traversed. A single pass over the
  dimensions and the interactions is simpler to read and to test.
* **Machine learning.** There is no outcome data to learn from, and the result must
  be explained to the adopter.
* **Storing or caching scores.** They would need invalidation whenever a profile or
  an animal changes, to save microseconds.
* **A ranked swipe page, or scores on the catalog.** The original story, deferred
  to keep this iteration to the algorithm and one surface that works end to end.
* **The browser calling the API directly.** It needs CORS and a token in
  JavaScript, against ADR 0005.

## To confirm with the team

Each of these is a placeholder or a product choice, and is listed in
`models/compatibility/rules.py` or the code that reads it:

- [ ] The fit tables and the weights (decision 8).
- [ ] The life-stage thresholds, 12 and 96 months (decision 9).
- [ ] The blank values, 0.5 in loose and 0.25 in strict (decision 6).
- [ ] The edge maxima 15, 10 and 15, and the cap of 25 (decision 8).
- [ ] The weakest-link strength, 0.5 (decision 6).
- [ ] Which dimensions are critical and which are safety (decision 4).
- [ ] Showing a not-suitable animal with a banner, and giving the owner no score
      on their own animal (decisions 7 and 10).
- [ ] The names shown to the user for the two modes.
