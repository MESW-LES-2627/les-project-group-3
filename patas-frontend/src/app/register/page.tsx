import Link from "next/link";
import { Suspense } from "react";

import { RedirectIfAuthenticated } from "@/components/redirect-if-authenticated";
import { RegisterForm } from "./register-form";

export default function RegisterPage() {
  return (
    <main className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center gap-6 px-4 py-16">
      <Suspense fallback={<p>Loading…</p>}>
        <RedirectIfAuthenticated>
          <h1 className="text-2xl font-semibold">Create your account</h1>
          <RegisterForm />
          <p className="text-sm">
            Already registered?{" "}
            <Link href="/login" className="underline">
              Log in
            </Link>
          </p>
        </RedirectIfAuthenticated>
      </Suspense>
    </main>
  );
}
