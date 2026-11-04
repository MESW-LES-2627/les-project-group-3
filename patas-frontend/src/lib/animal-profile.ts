import type { Option } from "@/lib/matchmaker-profile";

export const ANIMAL_SEX = ["male", "female", "unknown"] as const;
export const NEUTERED_STATUS = ["yes", "no", "unknown"] as const;
export const ANIMAL_SIZE = ["small", "medium", "large"] as const;
export const ENERGY_LEVEL = ["low", "moderate", "high"] as const;
export const ANIMAL_COMPATIBILITY = [
  "yes",
  "no",
  "with_supervision",
  "unknown",
] as const;
export const FIRST_TIME_OWNER_SUITABILITY = [
  "yes",
  "no",
  "with_support",
  "unknown",
] as const;

export const SPECIES_OPTIONS = [
  { value: "dog", label: "Dog" },
  { value: "cat", label: "Cat" },
  { value: "other", label: "Other" },
] as const;

// Portugal's 18 mainland districts and its two autonomous regions.
export const DISTRICT_OPTIONS = [
  { value: "aveiro", label: "Aveiro" },
  { value: "beja", label: "Beja" },
  { value: "braga", label: "Braga" },
  { value: "braganca", label: "Bragança" },
  { value: "castelo_branco", label: "Castelo Branco" },
  { value: "coimbra", label: "Coimbra" },
  { value: "evora", label: "Évora" },
  { value: "faro", label: "Faro" },
  { value: "guarda", label: "Guarda" },
  { value: "leiria", label: "Leiria" },
  { value: "lisboa", label: "Lisboa" },
  { value: "portalegre", label: "Portalegre" },
  { value: "porto", label: "Porto" },
  { value: "santarem", label: "Santarém" },
  { value: "setubal", label: "Setúbal" },
  { value: "viana_do_castelo", label: "Viana do Castelo" },
  { value: "vila_real", label: "Vila Real" },
  { value: "viseu", label: "Viseu" },
  { value: "acores", label: "Açores" },
  { value: "madeira", label: "Madeira" },
] as const;

export function districtLabel(district: string): string {
  return DISTRICT_OPTIONS.find((d) => d.value === district)?.label ?? district;
}

export const ANIMAL_SEX_OPTIONS: readonly Option<(typeof ANIMAL_SEX)[number]>[] =
  [
    { value: "male", label: "Male", phrase: "male" },
    { value: "female", label: "Female", phrase: "female" },
    { value: "unknown", label: "Unknown", phrase: "unknown sex" },
  ];

export const NEUTERED_OPTIONS: readonly Option<
  (typeof NEUTERED_STATUS)[number]
>[] = [
  { value: "yes", label: "Yes", phrase: "neutered" },
  { value: "no", label: "No", phrase: "not neutered" },
  {
    value: "unknown",
    label: "Unknown",
    phrase: "neuter status unknown",
  },
];

export const SIZE_OPTIONS: readonly Option<(typeof ANIMAL_SIZE)[number]>[] = [
  { value: "small", label: "Small", phrase: "small" },
  { value: "medium", label: "Medium", phrase: "medium" },
  { value: "large", label: "Large", phrase: "large" },
];

export const ACTIVITY_OPTIONS: readonly Option<
  (typeof ENERGY_LEVEL)[number]
>[] = [
  {
    value: "low",
    label: "Low",
    description: "Mostly calm, with short walks or gentle play",
    phrase: "low",
  },
  {
    value: "moderate",
    label: "Moderate",
    description: "Regular daily walks or play",
    phrase: "moderate",
  },
  {
    value: "high",
    label: "High",
    description: "Needs longer or more frequent activity",
    phrase: "high",
  },
];

export const SPACE_OPTIONS: readonly Option<(typeof ANIMAL_SIZE)[number]>[] = [
  {
    value: "small",
    label: "Small",
    description: "Comfortable in a smaller living space",
    phrase: "small",
  },
  {
    value: "medium",
    label: "Medium",
    description: "Needs room to move and play",
    phrase: "medium",
  },
  {
    value: "large",
    label: "Large",
    description: "Needs plenty of room to move",
    phrase: "large",
  },
];

export const SHEDDING_OPTIONS: readonly Option<
  (typeof ENERGY_LEVEL)[number]
>[] = [
  {
    value: "low",
    label: "Low",
    description: "Very little hair around the home",
    phrase: "low",
  },
  {
    value: "moderate",
    label: "Moderate",
    description: "Some loose hair; regular cleaning helps",
    phrase: "moderate",
  },
  {
    value: "high",
    label: "High",
    description: "Frequent or heavy shedding",
    phrase: "high",
  },
];

export const GROOMING_OPTIONS: readonly Option<
  (typeof ENERGY_LEVEL)[number]
>[] = [
  {
    value: "low",
    label: "Low",
    description: "Rarely, if ever; occasional basic care",
    phrase: "low",
  },
  {
    value: "moderate",
    label: "Moderate",
    description: "Regular brushing or routine upkeep",
    phrase: "moderate",
  },
  {
    value: "high",
    label: "High",
    description: "Frequent brushing, trimming, or professional grooming",
    phrase: "high",
  },
];

export const TRAINING_OPTIONS: readonly Option<
  (typeof ENERGY_LEVEL)[number]
>[] = [
  {
    value: "low",
    label: "Low",
    phrase: "low",
  },
  {
    value: "moderate",
    label: "Moderate",
    phrase: "moderate",
  },
  {
    value: "high",
    label: "High",
    phrase: "high",
  },
];

export const TIME_ALONE_OPTIONS: readonly Option<
  (typeof ENERGY_LEVEL)[number]
>[] = [
  {
    value: "low",
    label: "Low",
    description: "Struggles with being left alone",
    phrase: "low",
  },
  {
    value: "moderate",
    label: "Moderate",
    description: "Can manage a few hours with preparation",
    phrase: "moderate",
  },
  {
    value: "high",
    label: "High",
    description: "Can stay alone for longer periods",
    phrase: "high",
  },
];

export const NOISE_OPTIONS: readonly Option<
  (typeof ENERGY_LEVEL)[number]
>[] = [
  {
    value: "low",
    label: "Low",
    description: "Usually quiet",
    phrase: "low",
  },
  {
    value: "moderate",
    label: "Moderate",
    description: "Vocal at times",
    phrase: "moderate",
  },
  {
    value: "high",
    label: "High",
    description: "Often vocal",
    phrase: "high",
  },
];

export const COMPATIBILITY_OPTIONS: readonly Option<
  (typeof ANIMAL_COMPATIBILITY)[number]
>[] = [
  {
    value: "yes",
    label: "Yes",
    phrase: "yes",
  },
  {
    value: "no",
    label: "No",
    phrase: "no",
  },
  {
    value: "with_supervision",
    label: "With supervision",
    phrase: "with supervision",
  },
  {
    value: "unknown",
    label: "Unknown",
    phrase: "unknown",
  },
];

export const FIRST_TIME_OWNER_OPTIONS: readonly Option<
  (typeof FIRST_TIME_OWNER_SUITABILITY)[number]
>[] = [
  {
    value: "yes",
    label: "Yes",
    description: "Likely a good fit for a first-time owner",
    phrase: "yes",
  },
  {
    value: "no",
    label: "No",
    description: "Experience with animals is recommended",
    phrase: "no",
  },
  {
    value: "with_support",
    label: "With support",
    description: "A new owner may benefit from guidance",
    phrase: "with support",
  },
  {
    value: "unknown",
    label: "Unknown",
    phrase: "unknown",
  },
];

export const OPTIONAL_ANIMAL_FIELDS = [
  "sex",
  "is_neutered",
  "postal_code",
  "district",
  "size",
  "activity_level",
  "space_requirement",
  "shedding",
  "grooming_needs",
  "behaves_well_with_children",
  "behaves_well_with_dogs",
  "behaves_well_with_cats",
  "behaves_well_with_other_animals",
  "training_needs",
  "tolerance_for_time_alone",
  "noise_level",
  "suitable_for_first_time_owners",
  "special_care_notes",
  "other_details",
] as const;
