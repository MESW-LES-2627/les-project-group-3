import Link from "next/link";

// From an accepted request to its own page, where the conversation lives (ADR 0027).
export function OpenConversationLink({ applicationId }: { applicationId: string }) {
  return (
    <Link
      href={`/requests/${encodeURIComponent(applicationId)}`}
      className="inline-flex min-h-11 items-center justify-center rounded-xl border border-line bg-surface px-5 text-sm font-semibold text-forest transition hover:border-forest focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
    >
      Open conversation
    </Link>
  );
}
