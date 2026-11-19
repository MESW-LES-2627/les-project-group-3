import { describe, expect, it } from "vitest";
import {
  formValues,
  isAnimalId,
  MAX_PHOTO_BYTES,
  parseAnimalForm,
  photosToUpload,
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

  it("reads a form that left out the name and the species as empty text", () => {
    const description = parsed({});

    expect(description.name).toBe("");
    expect(description.species).toBe("");
  });

  it("collects the uploaded photo URLs and drops blanks", () => {
    const data = form({ name: "Bolt", species: "dog" });
    data.append("photo_urls", "https://media.example/bolt-1.jpg");
    data.append("photo_urls", "   ");
    data.append("photo_urls", "https://media.example/bolt-2.png");

    const result = parseAnimalForm(data);
    if (!("description" in result)) {
      throw new Error(`expected a description, got: ${result.error}`);
    }
    expect(result.description.photo_urls).toEqual([
      "https://media.example/bolt-1.jpg",
      "https://media.example/bolt-2.png",
    ]);
  });

  it("treats a form without photos as having none", () => {
    expect(parsed({ name: "Bolt", species: "dog" }).photo_urls).toEqual([]);
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

describe("photosToUpload", () => {
  const small = (name: string) => ({ name, size: 1000 });

  it("keeps every file that fits", () => {
    const files = [small("a"), small("b")];

    expect(photosToUpload(files, 0)).toEqual({ accepted: files, skipped: false });
  });

  it("skips a file over 5 MB", () => {
    const big = { name: "big", size: MAX_PHOTO_BYTES + 1 };

    expect(photosToUpload([small("a"), big], 0)).toEqual({
      accepted: [small("a")],
      skipped: true,
    });
  });

  it("accepts a file of exactly 5 MB", () => {
    const edge = { name: "edge", size: MAX_PHOTO_BYTES };

    expect(photosToUpload([edge], 0).accepted).toEqual([edge]);
  });

  it("only takes as many as fit next to the photos already there", () => {
    const files = [small("a"), small("b"), small("c")];

    expect(photosToUpload(files, 8)).toEqual({
      accepted: [small("a"), small("b")],
      skipped: true,
    });
  });

  it("takes none when the animal already has ten photos", () => {
    expect(photosToUpload([small("a")], 10)).toEqual({
      accepted: [],
      skipped: true,
    });
  });
});
