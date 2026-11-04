// Demo data through the real application: registers 3 demo users with Better-Auth,
// exchanges each session for a JWT and publishes Diogo's sample animals through
// POST /animals. Safe to re-run: existing users sign in, existing animals are skipped.
// Needs the stack running. Usage: pnpm seed:demo
import assert from "node:assert/strict";

const NEXT = process.env.NEXT_URL ?? "http://localhost:3000";
const API = process.env.FASTAPI_URL ?? "http://localhost:8000";
// Local demo only: never use these accounts outside a development database.
const PASSWORD = "demo-password-123";

const OWNERS = [
  {
    name: "Ana Demo",
    email: "ana.demo@example.com",
    animals: [
      {
        name: "Milo",
        species: "cat",
        age_in_months: 18,
        sex: "male",
        is_neutered: "yes",
        postal_code: "4000-001",
        district: "porto",
        size: "small",
        activity_level: "moderate",
        space_requirement: "small",
        shedding: "moderate",
        grooming_needs: "moderate",
        behaves_well_with_children: "yes",
        behaves_well_with_dogs: "with_supervision",
        behaves_well_with_cats: "yes",
        behaves_well_with_other_animals: "with_supervision",
        training_needs: "low",
        tolerance_for_time_alone: "moderate",
        noise_level: "low",
        suitable_for_first_time_owners: "yes",
        special_care_notes: "Keep fresh water available.",
        other_details: "Enjoys sunny window spots and quiet play.",
      },
      {
        name: "Luna",
        species: "dog",
        age_in_months: 30,
        sex: "female",
        is_neutered: "yes",
        postal_code: "4000-001",
        district: "porto",
        size: "medium",
        activity_level: "high",
        space_requirement: "medium",
        shedding: "moderate",
        grooming_needs: "low",
        behaves_well_with_children: "yes",
        behaves_well_with_dogs: "yes",
        behaves_well_with_cats: "with_supervision",
        behaves_well_with_other_animals: "with_supervision",
        training_needs: "moderate",
        tolerance_for_time_alone: "moderate",
        noise_level: "moderate",
        suitable_for_first_time_owners: "with_support",
        special_care_notes: "Needs daily walks and regular play.",
        other_details: "Friendly and food motivated.",
      },
    ],
  },
  {
    name: "Bruno Demo",
    email: "bruno.demo@example.com",
    animals: [
      {
        name: "Pipoca",
        species: "other",
        age_in_months: 8,
        sex: "female",
        is_neutered: "unknown",
        postal_code: "1100-001",
        district: "lisboa",
        size: "small",
        activity_level: "moderate",
        space_requirement: "small",
        shedding: "low",
        grooming_needs: "low",
        behaves_well_with_children: "with_supervision",
        behaves_well_with_dogs: "unknown",
        behaves_well_with_cats: "unknown",
        behaves_well_with_other_animals: "yes",
        training_needs: "low",
        tolerance_for_time_alone: "low",
        noise_level: "low",
        suitable_for_first_time_owners: "with_support",
        special_care_notes: "Needs a secure enclosure and daily interaction.",
        other_details: "A curious small companion animal.",
      },
      {
        name: "Nina",
        species: "cat",
        age_in_months: null,
        sex: "female",
        is_neutered: "yes",
        postal_code: "1100-001",
        district: "lisboa",
        size: "small",
        activity_level: "low",
        space_requirement: "small",
        shedding: "low",
        grooming_needs: "low",
        behaves_well_with_children: "with_supervision",
        behaves_well_with_dogs: "unknown",
        behaves_well_with_cats: "yes",
        behaves_well_with_other_animals: "unknown",
        training_needs: "low",
        tolerance_for_time_alone: "moderate",
        noise_level: "low",
        suitable_for_first_time_owners: "yes",
        special_care_notes: "Age is unknown; arrange a veterinary check-up.",
        other_details: "A calm indoor cat.",
      },
    ],
  },
  {
    name: "Carla Demo",
    email: "carla.demo@example.com",
    animals: [
      {
        name: "Bobby",
        species: "dog",
        age_in_months: 60,
        sex: "male",
        is_neutered: "no",
        postal_code: "1000-001",
        district: "lisboa",
        size: "large",
        activity_level: "moderate",
        space_requirement: "large",
        shedding: "high",
        grooming_needs: "moderate",
        behaves_well_with_children: "yes",
        behaves_well_with_dogs: "with_supervision",
        behaves_well_with_cats: "no",
        behaves_well_with_other_animals: "with_supervision",
        training_needs: "moderate",
        tolerance_for_time_alone: "high",
        noise_level: "moderate",
        suitable_for_first_time_owners: "with_support",
        special_care_notes: "Use a lead on walks around unfamiliar animals.",
        other_details: "Loves long walks and settling in a quiet home.",
      },
      {
        name: "Cenoura",
        species: "other",
        age_in_months: 12,
        sex: "unknown",
        is_neutered: "unknown",
        postal_code: "1000-001",
        district: "lisboa",
        size: "small",
        activity_level: "low",
        space_requirement: "small",
        shedding: "low",
        grooming_needs: "low",
        behaves_well_with_children: "with_supervision",
        behaves_well_with_dogs: "unknown",
        behaves_well_with_cats: "unknown",
        behaves_well_with_other_animals: "yes",
        training_needs: "low",
        tolerance_for_time_alone: "low",
        noise_level: "low",
        suitable_for_first_time_owners: "with_support",
        special_care_notes: "Provide suitable bedding and fresh vegetables.",
        other_details: "A gentle small companion animal.",
      },
    ],
  },
];

async function tokenFor(owner) {
  const post = async (path, body) => {
    for (let attempt = 1; ; attempt++) {
      const response = await fetch(`${NEXT}/api/auth/${path}`, {
        method: "POST",
        headers: { "content-type": "application/json", origin: NEXT },
        body: JSON.stringify(body),
      });
      if (response.status !== 429 || attempt === 5) {
        return response;
      }
      // Better-Auth allows 3 sign-in/sign-up requests per 10 s per IP in production.
      const seconds = Number(response.headers.get("x-retry-after") ?? 10);
      console.log(`rate limited by Better-Auth, waiting ${seconds}s`);
      await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
    }
  };
  let response = await post("sign-in/email", { email: owner.email, password: PASSWORD });
  if (!response.ok) {
    response = await post("sign-up/email", {
      name: owner.name,
      email: owner.email,
      password: PASSWORD,
    });
  }
  assert.ok(response.ok, `could not sign in ${owner.email}: ${await response.text()}`);
  const cookie = response.headers
    .getSetCookie()
    .map((c) => c.split(";")[0])
    .join("; ");
  const { token } = await (
    await fetch(`${NEXT}/api/auth/token`, { headers: { cookie } })
  ).json();
  return token;
}

const catalog = await (await fetch(`${API}/animals`)).json();
for (const owner of OWNERS) {
  const token = await tokenFor(owner);
  const authorization = `Bearer ${token}`;
  const me = await (await fetch(`${API}/me`, { headers: { authorization } })).json();
  for (const animal of owner.animals) {
    if (catalog.some((a) => a.owner_id === me.id && a.name === animal.name)) {
      console.log(`skip ${animal.name} (already published by ${owner.email})`);
      continue;
    }
    const response = await fetch(`${API}/animals`, {
      method: "POST",
      headers: { authorization, "content-type": "application/json" },
      body: JSON.stringify(animal),
    });
    assert.equal(response.status, 201, `publish ${animal.name} failed: ${await response.text()}`);
    console.log(`published ${animal.name} for ${owner.email}`);
  }
}
console.log(`Demo users log in with password "${PASSWORD}".`);
