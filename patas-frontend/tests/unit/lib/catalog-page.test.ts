import { describe, expect, it } from "vitest";

import { catalogPage, pageCount, totalFromHeader } from "@/lib/catalog-page";

describe("catalogPage", () => {
  it("reads a page number from the URL", () => {
    expect(catalogPage({ page: "3" })).toBe(3);
  });

  it.each([undefined, "0", "-1", "two", "1.5", "007", "9999999", ["2", "3"]])(
    "shows the first page for %j",
    (page) => {
      expect(catalogPage({ page })).toBe(1);
    },
  );
});

describe("pageCount", () => {
  it.each([
    [0, 1],
    [1, 1],
    [24, 1],
    [25, 2],
    [300, 13],
  ])("%i animals make %i pages", (total, pages) => {
    expect(pageCount(total)).toBe(pages);
  });
});

describe("totalFromHeader", () => {
  it("reads the count", () => {
    expect(totalFromHeader("300")).toBe(300);
    expect(totalFromHeader("0")).toBe(0);
  });

  it.each([null, "", "-1", "many", "3.5"])("is null for %j", (value) => {
    expect(totalFromHeader(value)).toBeNull();
  });
});
