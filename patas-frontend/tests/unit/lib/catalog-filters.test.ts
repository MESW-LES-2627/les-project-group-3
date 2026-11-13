import { describe, expect, it } from "vitest";
import { catalogFilters, catalogQuery } from "@/lib/catalog-filters";

describe("catalogFilters", () => {
  it("keeps the values the catalog accepts", () => {
    expect(
      catalogFilters({
        species: "dog",
        size: "small",
        district: "aveiro",
        age_group: "senior",
      }),
    ).toEqual({
      species: "dog",
      size: "small",
      district: "aveiro",
      age_group: "senior",
    });
  });

  it("drops a value the backend would reject, so an edited URL still shows the catalog", () => {
    expect(catalogFilters({ species: "dragon", size: "small" })).toEqual({
      size: "small",
    });
  });

  it("drops a repeated parameter, which arrives as an array", () => {
    expect(catalogFilters({ species: ["dog", "cat"] })).toEqual({});
  });

  it("ignores parameters that are not filters and missing ones", () => {
    expect(catalogFilters({ page: "2", species: undefined })).toEqual({});
  });
});

describe("catalogQuery", () => {
  it("is empty without filters, so the URL has no stray question mark", () => {
    expect(catalogQuery({})).toBe("");
  });

  it("builds the query string of the chosen filters", () => {
    expect(catalogQuery({ species: "dog", size: "small" })).toBe(
      "?species=dog&size=small",
    );
  });

  it("leaves out a filter that is undefined", () => {
    expect(catalogQuery({ species: "cat", size: undefined })).toBe(
      "?species=cat",
    );
  });
});
