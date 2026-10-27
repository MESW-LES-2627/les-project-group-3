from enum import StrEnum

# Each scale is declared from lowest to highest. An animal and a Matchmaker profile
# describe the same dimension with the same scale, so scoring can compare them.


class EnergyLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class ExperienceLevel(StrEnum):
    NONE = "none"
    SOME = "some"
    EXPERIENCED = "experienced"
