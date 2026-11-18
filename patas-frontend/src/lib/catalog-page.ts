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

export type PagerLinks = {
  previous: number | null;
  next: number | null;
  label: string | null;
};

// Where Previous and Next lead, and "Page X of Y"; null when one page holds
// everything. Past the end, Previous goes back to the last page.
export function pager(page: number, total: number): PagerLinks | null {
  const pages = pageCount(total);
  if (pages === 1 && page === 1) {
    return null;
  }
  return {
    previous: page > 1 ? Math.min(page - 1, pages) : null,
    next: page < pages ? page + 1 : null,
    label: page <= pages ? `Page ${page} of ${pages}` : null,
  };
}

// null when the header is missing or not a count, so the page can fall back.
export function totalFromHeader(value: string | null): number | null {
  return value !== null && /^[0-9]+$/.test(value) ? Number(value) : null;
}
