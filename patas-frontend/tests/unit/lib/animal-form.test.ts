import { describe, expect, it } from "vitest";
import {
  formValues,
  isAnimalId,
  parseAnimalForm,
  rejectionMessage,
  type AnimalDescription,
} from "@/lib/animal-form";

function form(fields: Record<string, string | Blob>): FormData {
  const data = new FormData();
  for (const [name, value] of Object.entries(fields)) {
    data.append(name, value);
  }
  return data;
}

function parsed(fields: Record<string, string | Blob>): AnimalDescription {
  const result = parseAnimalForm(form(fields));
  if (!("description" in result)) {
    throw new Error(`expected a description, got: ${result.error}`);
  }
  return result.description;
}

describe("parseAnimalForm: age", () => {
  it.each(["-1", "1.5", "abc", "1e3", "99999999999999999999"])(
    "rejects the age %s",
    (age) => {
      const result = parseAnimalForm(
        form({ name: "Bolt", species: "dog", age_in_months: age }),
      );
      expect(result).toEqual({
        error: "Age must be a whole number of months, zero or greater.",
      });
    },
  );

  it("treats an empty age as not given", () => {
    expect(parsed({ name: "Bolt", species: "dog", age_in_months: "  " }))
      .toMatchObject({ age_in_months: null });
  });

  it("accepts zero and a whole number of months", () => {
    expect(parsed({ name: "B", species: "dog", age_in_months: "0" }))
      .toMatchObject({ age_in_months: 0 });
    expect(parsed({ name: "B", species: "dog", age_in_months: "24" }))
      .toMatchObject({ age_in_months: 24 });
  });
});

describe("parseAnimalForm: other fields", () => {
  it("turns a blank optional field into null and trims a filled one", () => {
    const description = parsed({
      name: "Bolt",
      species: "dog",
      sex: "  female ",
      size: "   ",
    });
    expect(description.sex).toBe("female");
    expect(description.size).toBeNull();
    expect(description.district).toBeNull();
  });

  it("refuses a file where text is expected", () => {
    const result = parseAnimalForm(
      form({
        name: "Bolt",
        species: "dog",
        sex: new Blob(["x"]),
      }),
    );
    expect(result).toEqual({
      error: "Please submit text values for the animal details.",
    });
  });
});

describe("formValues", () => {
  it("shows a cleared field as empty text and numbers as text", () => {
    const description = parsed({
      name: "Bolt",
      species: "dog",
      age_in_months: "24",
    });
    const values = formValues(description);
    expect(values.name).toBe("Bolt");
    expect(values.age_in_months).toBe("24");
    expect(values.sex).toBe("");
  });
});

describe("isAnimalId", () => {
  it("accepts a UUID", () => {
    expect(isAnimalId("3f2b8c1e-4d5a-4b6c-8d7e-9f0a1b2c3d4e")).toBe(true);
  });

  it.each(["", "123", "not-a-uuid", "3f2b8c1e-4d5a-4b6c-8d7e-9f0a1b2c3d4eX"])(
    "rejects %j",
    (id) => {
      expect(isAnimalId(id)).toBe(false);
    },
  );
});

describe("rejectionMessage", () => {
  it("shows a rule error the domain sent as text", async () => {
    const response = Response.json({ detail: "Name is required" }, { status: 422 });
    expect(await rejectionMessage(response)).toBe("Name is required");
  });

  it("falls back to a generic message for FastAPI's list of type errors", async () => {
    const response = Response.json(
      { detail: [{ loc: ["body", "name"], msg: "field required" }] },
      { status: 422 },
    );
    expect(await rejectionMessage(response)).toBe("Invalid animal data");
  });
});
