"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { authClient } from "@/lib/auth-client";
import { USERNAME_RULE } from "@/lib/username";

import { checkUsername, claimUsername } from "./actions";

export function RegisterForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [claimFailed, setClaimFailed] = useState(false);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setPending(true);
    const form = new FormData(event.currentTarget);
    const username = String(form.get("username"));
    const check = await checkUsername(username);
    if (!check.ok) {
      setPending(false);
      setError(check.error);
      return;
    }
    const { error } = await authClient.signUp.email({
      name: String(form.get("name")),
      email: String(form.get("email")),
      password: String(form.get("password")),
    });
    if (error) {
      setPending(false);
      setError(error.message ?? "Registration failed");
      return;
    }
    // Someone may have taken it since the check: the account exists with a
    // username made from the name, which can be changed on the profile.
    const claim = await claimUsername(username);
    setPending(false);
    if (!claim.ok) {
      setClaimFailed(true);
      setError(`Your account was created, but: ${claim.error}`);
      return;
    }
    router.replace("/animals");
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <label className="flex flex-col gap-1 text-sm">
        Name
        <input
          name="name"
          type="text"
          required
          autoComplete="name"
          className="rounded border border-neutral-400 px-3 py-2"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Username
        <input
          name="username"
          type="text"
          required
          minLength={3}
          maxLength={30}
          autoComplete="username"
          aria-describedby="username-rule"
          className="rounded border border-neutral-400 px-3 py-2"
        />
        <span id="username-rule" className="text-xs text-neutral-600">
          {USERNAME_RULE} Others see it next to your name.
        </span>
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Email
        <input
          name="email"
          type="email"
          required
          autoComplete="email"
          className="rounded border border-neutral-400 px-3 py-2"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Password (at least 8 characters)
        <input
          name="password"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          className="rounded border border-neutral-400 px-3 py-2"
        />
      </label>
      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
          {claimFailed && (
            <>
              {" "}
              <Link href="/profile" className="underline">
                Choose another one on your profile.
              </Link>
            </>
          )}
        </p>
      )}
      <button
        type="submit"
        disabled={pending}
        className="rounded bg-neutral-900 px-3 py-2 text-white disabled:opacity-50"
      >
        {pending ? "Creating account…" : "Create account"}
      </button>
    </form>
  );
}
