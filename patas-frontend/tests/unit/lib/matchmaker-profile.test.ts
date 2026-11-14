import { describe, expect, it } from "vitest";
import {
  ANSWER_KEYS,
  EMPTY_DRAFT,
  answeredCount,
  draftFrom,
  firstUnanswered,
  isComplete,
  isMatchmakerAnswers,
  matchesSaved,
  sentence,
  type Draft,
  type MatchmakerAnswers,
} from "@/lib/matchmaker-profile";

const saved: MatchmakerAnswers = {
  housing: "apartment",
  time_away: "half_day",
  activity: "moderate",
  experience: "some",
  has_children: false,
  has_dogs: true,
  has_cats: false,
};

describe("isMatchmakerAnswers", () => {
  it("accepts a complete profile", () => {
    expect(isMatchmakerAnswers(saved)).toBe(true);
  });

  it("rejects a value outside the options and a mistyped yes or no", () => {
    expect(isMatchmakerAnswers({ ...saved, housing: "castle" })).toBe(false);
    expect(isMatchmakerAnswers({ ...saved, has_dogs: "yes" })).toBe(false);
  });

  it("rejects a profile with an answer missing, and things that are not objects", () => {
    const { has_cats: _missing, ...incomplete } = saved;
    void _missing;
    expect(isMatchmakerAnswers(incomplete)).toBe(false);
    expect(isMatchmakerAnswers(null)).toBe(false);
    expect(isMatchmakerAnswers("apartment")).toBe(false);
  });
});

describe("draftFrom", () => {
  it("starts empty when nothing is saved", () => {
    expect(draftFrom(null)).toEqual(EMPTY_DRAFT);
  });

  it("starts from the saved answers", () => {
    expect(draftFrom(saved)).toEqual(saved);
  });

  it("returns a copy, so editing the draft never changes the empty draft or the saved answers", () => {
    const fromNothing = draftFrom(null);
    fromNothing.housing = "house_with_yard";
    expect(EMPTY_DRAFT.housing).toBeNull();

    const fromSaved = draftFrom(saved);
    fromSaved.housing = "house_with_yard";
    expect(saved.housing).toBe("apartment");
  });
});

describe("how far the form is", () => {
  it("counts the answered questions", () => {
    expect(answeredCount(EMPTY_DRAFT)).toBe(0);
    expect(answeredCount({ ...EMPTY_DRAFT, housing: "apartment" })).toBe(1);
    expect(answeredCount(saved)).toBe(ANSWER_KEYS.length);
  });

  it("is complete only when every question is answered, and a false answer counts", () => {
    expect(isComplete(saved)).toBe(true);
    expect(isComplete({ ...saved, has_cats: null })).toBe(false);
    expect(isComplete(EMPTY_DRAFT)).toBe(false);
  });

  it("points at the first unanswered question in the order the form asks them", () => {
    expect(firstUnanswered(EMPTY_DRAFT)).toBe("housing");
    expect(firstUnanswered({ ...saved, has_dogs: null, activity: null })).toBe(
      "has_dogs",
    );
    expect(firstUnanswered(saved)).toBeNull();
  });
});

describe("matchesSaved", () => {
  it("is true when the draft holds exactly the saved answers", () => {
    expect(matchesSaved(draftFrom(saved), saved)).toBe(true);
  });

  it("is false once one answer changes", () => {
    const edited: Draft = { ...draftFrom(saved), has_children: true };
    expect(matchesSaved(edited, saved)).toBe(false);
  });

  it("with nothing saved, only an empty draft matches", () => {
    expect(matchesSaved(EMPTY_DRAFT, null)).toBe(true);
    expect(matchesSaved({ ...EMPTY_DRAFT, housing: "apartment" }, null)).toBe(
      false,
    );
  });
});

describe("sentence", () => {
  function answerTexts(draft: Draft) {
    return sentence(draft).flatMap((segment) =>
      segment.kind === "answer" ? [[segment.key, segment.text]] : [],
    );
  }

  it("leaves every answer empty while nothing is answered", () => {
    const texts = answerTexts(EMPTY_DRAFT);

    expect(texts).toHaveLength(ANSWER_KEYS.length);
    expect(texts.every(([, text]) => text === null)).toBe(true);
  });

  it("fills each answer with its own wording", () => {
    const filled = Object.fromEntries(answerTexts(saved));

    expect(Object.values(filled).every((text) => typeof text === "string")).toBe(
      true,
    );
    // Different answers read differently, so the panel can show what changed.
    const other = Object.fromEntries(
      answerTexts({ ...saved, housing: "house_with_yard" }),
    );
    expect(other.housing).not.toBe(filled.housing);
    expect(other.time_away).toBe(filled.time_away);
  });

  it("words a yes and a no of the household differently", () => {
    const withDogs = Object.fromEntries(answerTexts({ ...saved, has_dogs: true }));
    const withoutDogs = Object.fromEntries(
      answerTexts({ ...saved, has_dogs: false }),
    );

    expect(withDogs.has_dogs).toBe("dogs");
    expect(withoutDogs.has_dogs).toBe("no dogs");
  });

  it("reads as one sentence when it is all put together", () => {
    const text = sentence(saved)
      .map((segment) => segment.text)
      .join("");

    expect(text.startsWith("I live in ")).toBe(true);
    expect(text.endsWith("experience with animals.")).toBe(true);
  });
});
