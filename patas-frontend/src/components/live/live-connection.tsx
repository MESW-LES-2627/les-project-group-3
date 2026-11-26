"use client";

import * as Ably from "ably";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { ToastStack, type ShownToast } from "@/components/live/toast-stack";
import { liveBus } from "@/lib/live-bus";
import { liveChannel, parseLiveEvent, toastFor } from "@/lib/live-events";

const TOAST_MS = 6000;

type Props = { userId: string };

// US-21: one live connection per tab, kept in the layout so it survives navigation.
// It hands every event to the tab's bus (the chat listens there) and turns someone
// else's message into a toast on any other page.
export function LiveConnection({ userId }: Props) {
  const pathname = usePathname();
  // The page the person is on when an event arrives, not when the connection opened.
  const pathnameRef = useRef(pathname);
  useEffect(() => {
    pathnameRef.current = pathname;
  }, [pathname]);

  const [toasts, setToasts] = useState<ShownToast[]>([]);
  const dismiss = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  useEffect(() => {
    const client = new Ably.Realtime({
      authUrl: "/api/ably/token",
      clientId: userId,
    });
    const timers = new Set<ReturnType<typeof setTimeout>>();

    // The first connection needs no catch-up: the page has just loaded everything.
    let connectedBefore = false;
    client.connection.on("connected", () => {
      if (connectedBefore) {
        liveBus.emit({ name: "reconnected" });
      }
      connectedBefore = true;
    });

    const channel = client.channels.get(liveChannel(userId));
    void channel.subscribe((message) => {
      const event = parseLiveEvent(message.name ?? "", message.data);
      if (event === null) {
        return;
      }
      liveBus.emit(event);
      const toast = toastFor(event, pathnameRef.current, userId);
      if (toast) {
        const id = crypto.randomUUID();
        setToasts((current) => [...current, { id, ...toast }]);
        const timer = setTimeout(() => {
          timers.delete(timer);
          dismiss(id);
        }, TOAST_MS);
        timers.add(timer);
      }
    });

    return () => {
      for (const timer of timers) {
        clearTimeout(timer);
      }
      client.close();
    };
  }, [userId, dismiss]);

  return <ToastStack toasts={toasts} onDismiss={dismiss} />;
}
