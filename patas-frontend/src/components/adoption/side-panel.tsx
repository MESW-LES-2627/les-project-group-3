"use client";

import { useId, useState, type ReactNode } from "react";

type Props = {
  title: string;
  children: ReactNode;
};

// A panel beside the chat that collapses into a tab on the chat's edge (US-21). On a
// small screen it is a button above the chat that opens the panel over it.
export function SidePanel({ title, children }: Props) {
  const [open, setOpen] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const panelId = useId();
  const mobileId = useId();

  return (
    <>
      {/* Small screens: a button above the chat, the panel opens over it. */}
      <div className="order-first lg:hidden">
        <button
          type="button"
          aria-expanded={mobileOpen}
          aria-controls={mobileId}
          onClick={() => setMobileOpen((value) => !value)}
          className="w-full rounded-xl bg-leaf/5 px-4 py-3 text-left text-sm font-semibold text-forest ring-1 ring-line focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
        >
          {title} {mobileOpen ? "▴" : "▾"}
        </button>
        {mobileOpen ? (
          <div
            id={mobileId}
            className="fixed inset-x-4 top-24 bottom-4 z-40 overflow-y-auto rounded-2xl bg-surface p-4 shadow-xl ring-1 ring-line"
          >
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-forest">{title}</h2>
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                aria-label={`Close ${title}`}
                className="rounded-lg px-2 text-lg leading-none text-muted hover:text-forest focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
              >
                ×
              </button>
            </div>
            {children}
          </div>
        ) : null}
      </div>

      {/* Large screens: a column beside the chat, or a tab on its edge. */}
      {open ? (
        <aside
          id={panelId}
          aria-label={title}
          className="hidden h-[32rem] w-80 shrink-0 flex-col rounded-2xl bg-surface ring-1 ring-line lg:flex"
        >
          <div className="flex items-center justify-between border-b border-line px-4 py-3">
            <h2 className="text-sm font-semibold text-forest">{title}</h2>
            <button
              type="button"
              aria-expanded
              aria-controls={panelId}
              onClick={() => setOpen(false)}
              aria-label={`Collapse ${title}`}
              className="rounded-lg px-2 text-muted hover:text-forest focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
            >
              ◂
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4">{children}</div>
        </aside>
      ) : (
        <button
          type="button"
          aria-expanded={false}
          aria-controls={panelId}
          onClick={() => setOpen(true)}
          className="hidden h-[32rem] w-10 shrink-0 items-center justify-center rounded-r-2xl bg-leaf/10 text-sm font-semibold text-forest ring-1 ring-line hover:bg-leaf/20 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest lg:flex"
        >
          <span className="[writing-mode:vertical-rl]">{title} ▸</span>
        </button>
      )}
    </>
  );
}
