from enum import StrEnum


class Species(StrEnum):
    DOG = "dog"
    CAT = "cat"
    OTHER = "other"


class AdoptionStatus(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    IN_TRIAL = "in_trial"
    ADOPTED = "adopted"
    UNAVAILABLE = "unavailable"


class AnimalSex(StrEnum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class NeuteredStatus(StrEnum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class AnimalSize(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class AnimalCompatibility(StrEnum):
    YES = "yes"
    NO = "no"
    WITH_SUPERVISION = "with_supervision"
    UNKNOWN = "unknown"


class FirstTimeOwnerSuitability(StrEnum):
    YES = "yes"
    NO = "no"
    WITH_SUPPORT = "with_support"
    UNKNOWN = "unknown"
