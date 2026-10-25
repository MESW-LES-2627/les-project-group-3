function Block({ className }: { className: string }) {
  return (
    <div className={`rounded-xl bg-line motion-safe:animate-pulse ${className}`} />
  );
}

// Shaped like the form, so the page does not jump when the real one arrives.
export function FormSkeleton() {
  return (
    <div role="status">
      <span className="sr-only">Loading your profile…</span>
      <div
        aria-hidden="true"
        className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_20rem]"
      >
        <div className="space-y-12 lg:col-start-1 lg:row-start-1">
          {[0, 1, 2].map((section) => (
            <div key={section} className="space-y-4">
              <Block className="h-7 w-48" />
              <Block className="h-4 w-80 max-w-full" />
              <div className="grid gap-3 sm:grid-cols-3">
                <Block className="h-28" />
                <Block className="h-28" />
                <Block className="h-28" />
              </div>
            </div>
          ))}
        </div>
        <Block className="hidden h-72 lg:col-start-2 lg:row-start-1 lg:block" />
      </div>
    </div>
  );
}
