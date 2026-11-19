"use client";

import { startTransition, useActionState, type FormEvent } from "react";
import { USERNAME_RULE } from "@/lib/username";
import { updateProfile, type ProfileFormState } from "./actions";

type ProfileFormProps = {
  initialName: string;
  initialUsername: string;
  email: string;
};

const initialState: ProfileFormState = {};

export function ProfileForm({
  initialName,
  initialUsername,
  email,
}: ProfileFormProps) {
  const [state, formAction, isPending] = useActionState(
    updateProfile,
    initialState
  );

  // React resets a form after running its `action`, which would put the old
  // username back over a refused one; `action` is only the pre-hydration fallback.
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    startTransition(() => formAction(form));
  }

  return (
    <form action={formAction} onSubmit={submit} className="flex flex-col gap-6">
      {state.error && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        >
          {state.error}
        </div>
      )}

      {state.success && (
        <div
          role="status"
          className="rounded-xl border border-leaf/30 bg-leaf/10 p-4 text-sm text-forest"
        >
          Profile updated successfully!
        </div>
      )}

      <div>
        <label
          htmlFor="email"
          className="block text-sm font-medium text-forest"
        >
          Email address
        </label>
        <input
          id="email"
          type="email"
          value={email}
          readOnly
          disabled
          className="mt-2 w-full rounded-xl border border-line bg-surface/50 px-4 py-2.5 text-sm text-muted shadow-sm cursor-not-allowed"
        />
        <p className="mt-1 text-xs text-muted">Email cannot be changed.</p>
      </div>

      <div>
        <label
          htmlFor="name"
          className="block text-sm font-medium text-forest"
        >
          Full name
        </label>
        <input
          id="name"
          name="name"
          type="text"
          defaultValue={initialName}
          required
          className="mt-2 w-full rounded-xl border border-line bg-surface px-4 py-2.5 text-sm text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest"
        />
      </div>

      <div>
        <label
          htmlFor="username"
          className="block text-sm font-medium text-forest"
        >
          Username
        </label>
        <input
          id="username"
          name="username"
          type="text"
          defaultValue={initialUsername}
          required
          minLength={3}
          maxLength={30}
          autoComplete="username"
          aria-describedby="username-rule"
          className="mt-2 w-full rounded-xl border border-line bg-surface px-4 py-2.5 text-sm text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest"
        />
        <p id="username-rule" className="mt-1 text-xs text-muted">
          {USERNAME_RULE} Nobody else can have it.
        </p>
      </div>

      <div className="flex justify-end pt-2">
        <button
          type="submit"
          disabled={isPending}
          className="inline-flex min-h-11 items-center justify-center rounded-xl bg-forest px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-50"
        >
          {isPending ? "Saving..." : "Save changes"}
        </button>
      </div>
    </form>
  );
}
