import * as Ably from "ably";
import { headers } from "next/headers";
import { NextResponse } from "next/server";

import { auth } from "@/lib/auth";
import { liveChannel } from "@/lib/live-events";

// US-21: the browser asks here for an Ably token. The token can only subscribe to the
// signed-in person's own channel: it can neither publish nor listen to anyone else's,
// whatever the code in the browser does. The API key never leaves the server.
export async function GET() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) {
    return NextResponse.json({ error: "Not signed in" }, { status: 401 });
  }
  const key = process.env.ABLY_API_KEY;
  if (!key) {
    return NextResponse.json(
      { error: "Live updates are off" },
      { status: 503 },
    );
  }

  const rest = new Ably.Rest({ key });
  const tokenRequest = await rest.auth.createTokenRequest({
    clientId: session.user.id,
    capability: { [liveChannel(session.user.id)]: ["subscribe"] },
  });
  return NextResponse.json(tokenRequest);
}
