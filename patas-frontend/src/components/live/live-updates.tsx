import { headers } from "next/headers";

import { LiveConnection } from "@/components/live/live-connection";
import { auth } from "@/lib/auth";

// US-21: only a signed-in person listens, and only when live updates are set up.
// Without ABLY_API_KEY (local development, CI) no connection is even attempted:
// everything still works, and pages show what changed on reload.
export async function LiveUpdates() {
  if (!process.env.ABLY_API_KEY) {
    return null;
  }
  const session = await auth.api.getSession({ headers: await headers() });
  return session ? <LiveConnection userId={session.user.id} /> : null;
}
