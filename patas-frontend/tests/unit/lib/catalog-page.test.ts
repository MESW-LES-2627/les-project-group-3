import { describe, expect, it } from "vitest";

import {
  catalogPage,
  pageCount,
  pager,
  totalFromHeader,
} from "@/lib/catalog-page";

describe("catalogPage", () => {
  it.each([
    ["1", 1],
    ["3", 3],
    ["13", 13],
    ["999999", 999999],
  ])("reads page %s from the URL", (page, number) => {
    expect(catalogPage({ page })).toBe(number);
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

describe("pager", () => {
  it.each([0, 1, 24])("is hidden when %i animals fit on page 1", (total) => {
    expect(pager(1, total)).toBeNull();
  });

  it("has only Next on the first page", () => {
    expect(pager(1, 25)).toEqual({ previous: null, next: 2, label: "Page 1 of 2" });
  });

  it("has both in the middle", () => {
    expect(pager(2, 49)).toEqual({ previous: 1, next: 3, label: "Page 2 of 3" });
  });

  it("has only Previous on the last page", () => {
    expect(pager(2, 25)).toEqual({ previous: 1, next: null, label: "Page 2 of 2" });
  });

  it("leads back to the last page from past the end, with no label", () => {
    expect(pager(5, 25)).toEqual({ previous: 2, next: null, label: null });
    expect(pager(2, 0)).toEqual({ previous: 1, next: null, label: null });
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
