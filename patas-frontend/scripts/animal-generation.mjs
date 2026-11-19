import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";

export const NEXT = process.env.NEXT_URL ?? "http://localhost:3000";
export const API = process.env.FASTAPI_URL ?? "http://localhost:8000";
export const PASSWORD = "demo-password-123";

export async function expectStatus(response, expectedStatus, action) {
  if (response.status !== expectedStatus) {
    throw new Error(
      `${action} failed (HTTP ${response.status}): ${await response.text()}`,
    );
  }
  return response;
}

const DEMO_ACCOUNTS = [
  { name: "Ana Demo", email: "ana.demo@example.com" },
  { name: "Bruno Demo", email: "bruno.demo@example.com" },
  { name: "Carla Demo", email: "carla.demo@example.com" },
];

const FIRST_NAMES = [
  "Amigo", "Balu", "Biscoito", "Bolota", "Bruma", "Canela", "Figo",
  "Kiko", "Luna", "Mel", "Milo", "Nala", "Nina", "Pipoca", "Sol",
];
const DISTRICTS = [
  "aveiro", "beja", "braga", "braganca", "castelo_branco", "coimbra",
  "evora", "faro", "guarda", "leiria", "lisboa", "portalegre", "porto",
  "santarem", "setubal", "viana_do_castelo", "vila_real", "viseu",
  "acores", "madeira",
];
const SPECIES = ["dog", "cat", "other"];
const SEXES = ["male", "female", "unknown"];
const NEUTERING = ["yes", "no", "unknown"];
const SIZES = ["small", "medium", "large"];
const ENERGY = ["low", "moderate", "high"];
const COMPATIBILITY = ["yes", "no", "with_supervision", "unknown"];
const FIRST_TIME = ["yes", "no", "with_support", "unknown"];

function randomItem(items) {
  return items[Math.floor(Math.random() * items.length)];
}

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

export function generateRandomAnimal(index = 0) {
  const district = randomItem(DISTRICTS);
  const species = randomItem(SPECIES);
  const suffix = randomInt(1000, 9999);
  const name = `${randomItem(FIRST_NAMES)} ${suffix}${index ? `-${index}` : ""}`;
  const ageInMonths = Math.random() < 0.12 ? null : randomInt(2, 180);

  return {
    name,
    species,
    age_in_months: ageInMonths,
    sex: randomItem(SEXES),
    is_neutered: randomItem(NEUTERING),
    district,
    size: randomItem(SIZES),
    activity_level: randomItem(ENERGY),
    space_requirement: randomItem(SIZES),
    shedding: randomItem(ENERGY),
    grooming_needs: randomItem(ENERGY),
    behaves_well_with_children: randomItem(COMPATIBILITY),
    behaves_well_with_dogs: randomItem(COMPATIBILITY),
    behaves_well_with_cats: randomItem(COMPATIBILITY),
    behaves_well_with_other_animals: randomItem(COMPATIBILITY),
    training_needs: randomItem(ENERGY),
    tolerance_for_time_alone: randomItem(ENERGY),
    noise_level: randomItem(ENERGY),
    suitable_for_first_time_owners: randomItem(FIRST_TIME),
    special_care_notes: "Generated demo listing. Confirm care requirements before adoption.",
    other_details: `Randomly generated ${species} for demo catalog testing.`,
  };
}

export const generateAnimal = generateRandomAnimal;

export function generateRandomAnimals(count = 100) {
  assert.ok(Number.isInteger(count) && count >= 0, "animal count must be a non-negative integer");
  return Array.from({ length: count }, (_, index) =>
    generateRandomAnimal(index + 1),
  );
}

export const generateAnimals = generateRandomAnimals;

async function tokenFor(owner) {
  const post = async (path, body) => {
    for (let attempt = 1; ; attempt++) {
      const response = await fetch(`${NEXT}/api/auth/${path}`, {
        method: "POST",
        headers: { "content-type": "application/json", origin: NEXT },
        body: JSON.stringify(body),
      });
      if (response.status !== 429 || attempt === 5) return response;
      const seconds = Number(response.headers.get("x-retry-after") ?? 10);
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
  await expectStatus(response, 200, `sign in ${owner.email}`);
  const cookies = response.headers
    .getSetCookie()
    .map((cookie) => cookie.split(";")[0])
    .join("; ");
  const tokenResponse = await fetch(`${NEXT}/api/auth/token`, {
    headers: { cookie: cookies },
  });
  await expectStatus(tokenResponse, 200, `obtain token for ${owner.email}`);
  return (await tokenResponse.json()).token;
}

export async function seedRandomAnimals(count = 100) {
  const accounts = [];
  for (const owner of DEMO_ACCOUNTS) {
    const token = await tokenFor(owner);
    const me = await (
      await fetch(`${API}/me`, { headers: { authorization: `Bearer ${token}` } })
    ).json();
    accounts.push({ owner, me, authorization: `Bearer ${token}` });
  }

  let created = 0;
  for (const animal of generateRandomAnimals(count)) {
    const account = randomItem(accounts);
    const response = await fetch(`${API}/animals`, {
      method: "POST",
      headers: {
        authorization: account.authorization,
        "content-type": "application/json",
      },
      body: JSON.stringify(animal),
    });
    assert.equal(response.status, 201, `publish ${animal.name} failed: ${await response.text()}`);
    created++;
  }
  return created;
}

const isDirectRun =
  process.argv[1] &&
  pathToFileURL(process.argv[1]).href === import.meta.url;

if (isDirectRun) {
  const countArg = process.argv.findIndex((argument) => argument === "--animals");
  const count = countArg >= 0 ? Number(process.argv[countArg + 1]) : 100;
  assert.ok(Number.isInteger(count) && count >= 0, "--animals must be a non-negative integer");
  const created = await seedRandomAnimals(count);
  console.log(`Added ${created} randomly generated animal(s).`);
}