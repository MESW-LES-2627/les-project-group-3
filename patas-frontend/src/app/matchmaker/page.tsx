import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { FormSkeleton } from "@/components/matchmaker/form-skeleton";
import { MatchmakerSavedList } from "@/components/matchmaker/matchmaker-saved-list";
import { MatchmakerProfileForm } from "@/components/matchmaker/matchmaker-profile-form";
import { MatchmakerSwipeFeed } from "@/components/matchmaker/matchmaker-swipe-feed";
import { getMatchmakerProfile } from "@/lib/matchmaker-api";
import { getSavedAnimals, getSwipeFeed } from "@/lib/matchmaker-swipes-api";

import {
  deleteProfileAction,
  recordSwipeAction,
  removeSavedAnimalAction,
  saveProfileAction,
  swipeFeedAction,
} from "./actions";
import { requestToAdoptAction } from "@/app/animals/[id]/actions";

export const metadata: Metadata = {
  title: "Matchmaker | Patas",
};

async function SavedProfileForm() {
  const saved = await getMatchmakerProfile();
  return (
    <MatchmakerProfileForm
      saved={saved}
      save={saveProfileAction}
      remove={deleteProfileAction}
    />
  );
}

function MatchmakerTabs({ selected }: { selected: MatchmakerTab }) {
  const tabs: { id: MatchmakerTab; label: string }[] = [
    { id: "profile", label: "Edit profile" },
    { id: "swipe", label: "Swipe animals" },
    { id: "saved", label: "Saved animals" },
  ];
  return (
    <nav
      aria-label="Matchmaker"
      className="mb-8 grid grid-cols-3 gap-1 border-b border-line"
    >
      {tabs.map((tab) => (
        <Link
          key={tab.id}
          href={tab.id === "profile" ? "/matchmaker" : `/matchmaker?tab=${tab.id}`}
          aria-current={selected === tab.id ? "page" : undefined}
          className={`-mb-px flex min-h-11 min-w-0 items-center justify-center border-b-2 px-1 text-center text-sm font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest sm:px-3 ${
            selected === tab.id
              ? "border-forest text-forest"
              : "border-transparent text-muted hover:text-forest"
          }`}
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  );
}

type MatchmakerTab = "profile" | "swipe" | "saved";

function requestedTab(value: string | string[] | undefined): MatchmakerTab {
  const tab = Array.isArray(value) ? value[0] : value;
  return tab === "swipe" || tab === "saved" ? tab : "profile";
}

async function SwipeTab() {
  const profile = await getMatchmakerProfile();
  if (profile === null) {
    return (
      <section className="rounded-2xl border border-dashed border-line bg-surface px-6 py-10 text-center">
        <h2 className="text-xl font-semibold text-forest">
          Create your Matchmaker profile first
        </h2>
        <p className="mt-2 text-sm text-muted">
          We use your home and routine to put the best-fitting animals first.
        </p>
        <Link
          href="/matchmaker"
          className="mt-5 inline-flex min-h-11 items-center rounded-xl bg-forest px-5 text-sm font-semibold text-white hover:bg-leaf focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
        >
          Create profile
        </Link>
      </section>
    );
  }
  const feed = await getSwipeFeed();
  if (!feed.ok) {
    return (
      <p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">
        {feed.message}
      </p>
    );
  }
  return (
    <MatchmakerSwipeFeed
      initialAnimals={feed.animals}
      loadMore={swipeFeedAction}
      swipe={recordSwipeAction}
    />
  );
}

async function SavedTab() {
  const saved = await getSavedAnimals();
  if (!saved.ok) {
    return (
      <p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">
        {saved.message}
      </p>
    );
  }
  return (
    <MatchmakerSavedList
      initialAnimals={saved.animals}
      remove={removeSavedAnimalAction}
      request={requestToAdoptAction}
    />
  );
}

function LoadingPanel({ tab }: { tab: MatchmakerTab }) {
  if (tab === "profile") return <FormSkeleton />;
  return <p className="text-sm text-muted">Loading Matchmaker...</p>;
}

function TabContent({ tab }: { tab: MatchmakerTab }) {
  if (tab === "swipe") return <SwipeTab />;
  if (tab === "saved") return <SavedTab />;
  return <SavedProfileForm />;
}

function PageSkeleton() {
  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6 sm:py-14">
      <p className="text-sm text-muted">Loading Matchmaker...</p>
    </main>
  );
}

async function MatchmakerContent({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const tab = requestedTab((await searchParams).tab);
  const titles: Record<MatchmakerTab, { title: string; description: string }> = {
    profile: {
      title: "Tell us about your home",
      description:
        "Answer these once and the Matchmaker can suggest animals that fit your life. You can change your answers whenever you like.",
    },
    swipe: {
      title: "Find your best fit",
      description:
        "Meet animals ranked for your home. Swipe right to save one, or left to pass.",
    },
    saved: {
      title: "Animals you saved",
      description:
        "Come back to your saved animals and send an adoption request when you are ready.",
    },
  };
  const page = titles[tab];

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6 sm:py-14">
      <header className="mb-10 max-w-2xl">
        <h1 className="text-3xl font-semibold text-forest sm:text-4xl">{page.title}</h1>
        <p className="mt-3 text-base leading-7 text-muted">{page.description}</p>
      </header>
      <MatchmakerTabs selected={tab} />
      <Suspense fallback={<LoadingPanel tab={tab} />}>
        <TabContent tab={tab} />
      </Suspense>
    </main>
  );
}

export default function MatchmakerPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <MatchmakerContent searchParams={searchParams} />
    </Suspense>
  );
}
