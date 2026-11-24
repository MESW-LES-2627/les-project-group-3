from enum import StrEnum


class HandoverItem(StrEnum):
    """What the two sides can tick off while an adoption is accepted.

    Only the keys live here. The wording and the legal guidance for each item are
    shown by the frontend (ADR 0028).
    """

    VACCINATION_BOOKLET = "vaccination_booklet"
    MICROCHIP_TRANSFER = "microchip_transfer"
    CARE_NOTES = "care_notes"
    ADOPTION_TERMS = "adoption_terms"
