import { NextResponse } from "next/server";

import { backendUrl } from "@/lib/backend";
import { bearerToken } from "@/lib/matchmaker-api";

export async function POST(request: Request) {
  const token = await bearerToken();
  const body = await request.json().catch(() => ({ content_type: "image/jpeg" }));

  const response = await fetch(`${backendUrl()}/animals/presigned-url`, {
    method: "POST",
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    return NextResponse.json(
      { error: "Unable to prepare upload" },
      { status: response.status },
    );
  }

  return NextResponse.json(await response.json());
}
