from enum import StrEnum


class Species(StrEnum):
    DOG = "dog"
    CAT = "cat"
    OTHER = "other"


class AdoptionStatus(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
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


class District(StrEnum):
    # Portugal's 18 mainland districts and its two autonomous regions.
    AVEIRO = "aveiro"
    BEJA = "beja"
    BRAGA = "braga"
    BRAGANCA = "braganca"
    CASTELO_BRANCO = "castelo_branco"
    COIMBRA = "coimbra"
    EVORA = "evora"
    FARO = "faro"
    GUARDA = "guarda"
    LEIRIA = "leiria"
    LISBOA = "lisboa"
    PORTALEGRE = "portalegre"
    PORTO = "porto"
    SANTAREM = "santarem"
    SETUBAL = "setubal"
    VIANA_DO_CASTELO = "viana_do_castelo"
    VILA_REAL = "vila_real"
    VISEU = "viseu"
    ACORES = "acores"
    MADEIRA = "madeira"
