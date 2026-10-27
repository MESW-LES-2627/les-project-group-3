"use client";

export default function MatchmakerError({ reset }: { reset: () => void }) {
  return (
    <main className="mx-auto flex w-full max-w-xl flex-1 flex-col items-start justify-center gap-4 px-4 py-16">
      <h1 className="text-2xl font-semibold text-forest">
        We couldn&apos;t load your profile
      </h1>
      <p className="text-muted">Please try again in a moment.</p>
      <button
        type="button"
        onClick={reset}
        className="inline-flex min-h-11 items-center rounded-xl bg-forest px-5 text-sm font-semibold text-white transition hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
      >
        Try again
      </button>
    </main>
  );
}
