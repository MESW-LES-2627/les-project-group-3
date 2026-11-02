import type { Metadata } from "next";
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { Suspense } from "react";

import { auth } from "@/lib/auth";
import { backendUrl } from "@/lib/backend";
import { ProfileForm } from "./profile-form";

export const metadata: Metadata = {
  title: "Profile | Patas",
};

type UserProfile = {
  id: string;
  name: string;
  email: string;
  is_platform_admin: boolean;
};

async function getProfile(token: string): Promise<UserProfile> {
  const response = await fetch(`${backendUrl()}/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Unable to load profile: backend returned ${response.status}`);
  }

  return (await response.json()) as UserProfile;
}

async function ProfileContent() {
  const requestHeaders = await headers();
  const session = await auth.api.getSession({ headers: requestHeaders });

  if (!session) {
    redirect("/login");
  }

  const { token } = await auth.api.getToken({ headers: requestHeaders });
  const profile = await getProfile(token);

  return (
    <section className="rounded-2xl border border-line bg-surface p-6 shadow-sm sm:p-8">
      <ProfileForm initialName={profile.name} email={profile.email} />
    </section>
  );
}

export default function ProfilePage() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-8 px-4 py-10 sm:px-6 sm:py-14">
      <div>
        <p className="mb-3 inline-flex items-center gap-2 text-xs font-bold uppercase text-leaf">
          <span className="size-2 rounded-full bg-sunlight" />
          Settings
        </p>
        <h1 className="text-3xl font-bold text-forest sm:text-4xl">
          Citizen profile
        </h1>
        <p className="mt-2 text-sm text-muted">
          Manage your personal details. Your name will be visible on any animal listings you publish.
        </p>
      </div>

      <Suspense fallback={<p>Loading profile…</p>}>
        <ProfileContent />
      </Suspense>
    </main>
  );
}

