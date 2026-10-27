import { CircleAlert } from "lucide-react";

// An inline error: an icon plus text, so it never relies on colour alone.
export function FieldError({
  id,
  children,
}: {
  id: string;
  children: React.ReactNode;
}) {
  return (
    <p
      id={id}
      className="mt-2 flex items-center gap-1.5 text-sm font-medium text-red-700"
    >
      <CircleAlert aria-hidden="true" className="size-4 shrink-0" />
      {children}
    </p>
  );
}
