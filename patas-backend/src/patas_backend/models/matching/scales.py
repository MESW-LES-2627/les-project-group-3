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


class TimeAway(StrEnum):
    # An adopter's time away from home, and the longest an animal can be left alone
    # (scoring reads the animal side as a ceiling).
    FEW_HOURS = "few_hours"
    HALF_DAY = "half_day"
    MOST_OF_DAY = "most_of_day"
