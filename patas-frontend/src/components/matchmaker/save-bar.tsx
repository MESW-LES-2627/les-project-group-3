import { CircleAlert, CircleCheck, LoaderCircle } from "lucide-react";

// `announce` is true only for the result of an action (saved, deleted, failed):
// those are read out by screen readers; the running count and status are not.
export type BarMessage = {
  tone: "neutral" | "success" | "error";
  text: string;
  announce: boolean;
};

type SaveBarProps = { message: BarMessage; pending: boolean };

export function SaveBar({ message, pending }: SaveBarProps) {
  const Icon =
    message.tone === "success"
      ? CircleCheck
      : message.tone === "error"
        ? CircleAlert
        : null;
  const failed = message.tone === "error";

  return (
    <div className="sticky bottom-0 z-10 border-t border-line bg-background pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 lg:col-span-2">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div
          className={`flex min-w-0 items-center text-sm font-medium ${
            failed ? "text-red-700" : "text-forest"
          }`}
        >
          {Icon && (
            <Icon
              aria-hidden="true"
              className={`mr-2 size-4 shrink-0 ${failed ? "" : "text-leaf"}`}
            />
          )}
          <p>{message.announce ? null : message.text}</p>
          <p role="status">
            {message.announce && !failed ? message.text : null}
          </p>
          <p role="alert">{message.announce && failed ? message.text : null}</p>
        </div>
        <button
          type="submit"
          disabled={pending}
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-forest px-5 text-sm font-semibold text-white transition-colors duration-150 hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-60"
        >
          {pending && (
            <LoaderCircle
              aria-hidden="true"
              className="size-4 motion-safe:animate-spin"
            />
          )}
          {pending ? "Saving…" : "Save my profile"}
        </button>
      </div>
    </div>
  );
}
