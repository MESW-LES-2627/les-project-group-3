import Link from "next/link";
import { headers } from "next/headers";

import { auth } from "@/lib/auth";

import { LogoutButton } from "./logout-button";

export async function SiteHeader() {
  const session = await auth.api.getSession({ headers: await headers() });

  return (
    <header className="border-b border-line bg-surface">
      <div className="mx-auto flex min-h-[4.5rem] w-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link
          href="/animals"
          aria-label="Patas home"
          className="flex shrink-0 items-center gap-3 rounded-lg focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-forest"
        >
          <span className="grid size-10 place-items-center rounded-xl bg-forest text-lg font-bold text-white">
            P
          </span>
          <span className="text-xl font-bold text-forest">Patas</span>
        </Link>

        <nav aria-label="Main navigation" className="hidden sm:block">
          <Link
            href="/animals"
            className="text-sm font-medium text-muted transition hover:text-forest"
          >
            Browse animals
          </Link>
        </nav>

        <div className="flex shrink-0 items-center gap-3 sm:gap-5">
          {session ? (
            <>
              <span className="hidden max-w-40 truncate text-sm text-muted md:block">
                {session.user.name ? `Hello, ${session.user.name}` : "Welcome back"}
              </span>
              <LogoutButton />
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm font-semibold text-forest transition hover:text-leaf"
              >
                Log in
              </Link>
              <Link
                href="/register"
                className="inline-flex min-h-10 items-center justify-center rounded-xl bg-forest px-4 text-sm font-semibold text-white transition hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
              >
                Join Patas
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}