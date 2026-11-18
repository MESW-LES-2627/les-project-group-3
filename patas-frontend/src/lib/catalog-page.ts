// Paging of the catalog (ADR 0025): the backend sends 24 animals a page and the
// number that match in all in X-Total-Count.
export const CATALOG_PAGE_SIZE = 24;

// Anything but a whole number from 1 shows the first page, like an unknown filter.
export function catalogPage(
  params: Record<string, string | string[] | undefined>,
): number {
  const value = params.page;
  return typeof value === "string" && /^[1-9][0-9]{0,5}$/.test(value)
    ? Number(value)
    : 1;
}

export function pageCount(total: number): number {
  return Math.max(1, Math.ceil(total / CATALOG_PAGE_SIZE));
}

// null when the header is missing or not a count, so the page can fall back.
export function totalFromHeader(value: string | null): number | null {
  return value !== null && /^[0-9]+$/.test(value) ? Number(value) : null;
}
