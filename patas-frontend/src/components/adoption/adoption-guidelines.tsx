import { ADOPTION_GUIDELINES } from "@/lib/adoption-guidelines";

// Read-only suggestions for both sides of an accepted request (US-24, ADR 0027).
export function AdoptionGuidelines({ open = false }: { open?: boolean }) {
  return (
    <details open={open} className="rounded-xl bg-leaf/5 p-4">
      <summary className="cursor-pointer text-sm font-semibold text-forest focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest">
        Before the handover: {ADOPTION_GUIDELINES.length} suggested steps
      </summary>
      <ol className="mt-3 grid list-decimal gap-3 pl-5 text-sm text-forest">
        {ADOPTION_GUIDELINES.map((step) => (
          <li key={step.title}>
            <span className="font-semibold">{step.title}</span>
            <ul className="mt-1 grid list-disc gap-1 pl-4 text-muted">
              {step.points.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </li>
        ))}
      </ol>
    </details>
  );
}
