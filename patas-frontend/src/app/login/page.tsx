import Link from "next/link";
import { Suspense } from "react";

import { RedirectIfAuthenticated } from "@/components/redirect-if-authenticated";
import { LoginForm } from "./login-form";

export default function LoginPage() {
  return (
    <main className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center gap-6 px-4 py-16">
      <Suspense fallback={<p>Loading…</p>}>
        <RedirectIfAuthenticated>
          <h1 className="text-2xl font-semibold">Log in</h1>
          <LoginForm />
          <p className="text-sm">
            New here?{" "}
            <Link href="/register" className="underline">
              Create an account
            </Link>
          </p>
        </RedirectIfAuthenticated>
      </Suspense>
    </main>
  );
}
