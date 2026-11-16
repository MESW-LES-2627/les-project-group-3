# ADR 0023: Republishing an animal

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-16 |
| **Scope** | US-19 (#65, republish my animal); the republishing half of AT-21 (#75) |
| **Related** | [0012-owner-animals-and-unpublishing](0012-owner-animals-and-unpublishing.md), [0014-editing-an-animal](0014-editing-an-animal.md), [0017-adoption-base](0017-adoption-base.md), [0019-requesting-to-adopt](0019-requesting-to-adopt.md), [AdoptionPipeline](../../domain/AdoptionPipeline.md) |

## Context

An owner can unpublish an available animal (ADR 0012), which closes its open
requests (ADR 0017). The pipeline already has the way back, "Unavailable →
Available", but nothing implemented it, so a paused listing had to be created
again.

## Decisions

1. **`Animal.republish(by_user_id)` is the reverse of `unpublish`.** It checks the
   owner first (`AnimalUnauthorized`, 403), then moves unavailable to available
   through `_move`. A reserved or adopted animal is refused with
   `InvalidAnimalTransition` (409): it was never unpublished, and adopted is final
   (D5). Republishing an available animal changes nothing, as unpublishing twice
   does.
2. **No event.** No request changes when an animal comes back, so nothing has to
   react. The requests closed by unpublishing stay closed, and their applicants can
   ask again, because only an open or accepted request blocks a new one (ADR 0019).
   If former applicants are later told the animal is back, an `AnimalRepublished`
   event is where that hooks in.
3. **`POST /animals/{id}/republish`** mirrors the unpublish endpoint: 401 for a
   visitor, 404 for an unknown animal, 403 and 409 as above. The use case locks the
   animal row (ADR 0014, decision 6), so a republish that meets an edit waits for it
   instead of writing the old fields back.
4. **The Republish button takes the Unpublish button's place** on *My animals* for
   an unpublished animal. It asks for no confirmation: republishing hides nothing
   and can be undone. Each button has its own server action (`unpublishAnimalAction`,
   `republishAnimalAction`), and both call one helper that differs only in the
   endpoint and the wording.

## Consequences

* (+) A paused listing comes back with its data and history; nothing is created
  again.
* (−) Former applicants are not told the animal is back; they find it in the
  catalog.
* (−) Like Unpublish, the button reports an error with `alert()` until the quality
  and clean-up task (#58) replaces it.
