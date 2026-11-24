# ADR 0028: Handover checklist on an accepted request

| | |
| :-- | :-- |
| **Status** | Proposed |
| **Date** | 2026-11-24 |
| **Scope** | US-25 (#117); AT-26 (#132) |
| **Related** | [0017-adoption-base](0017-adoption-base.md), [0020-seeing-and-withdrawing-my-requests](0020-seeing-and-withdrawing-my-requests.md), [0027-adoption-guidelines](0027-adoption-guidelines.md) |

## Context

Once a request is accepted, the owner and the adopter hand the animal over. US-25
asks for a checklist of what to hand over that both of them can tick. An item ticked
by one stays ticked after reloading, the checklist never blocks the handover, and
after the adoption it shows as it was left and can no longer be changed.

The ticks are state shared by two people, so unlike the guidelines (ADR 0027) they
need the backend. The checklist should also say how to do each thing and, where a
legal rule applies, what it is.

## Decisions

1. **The ticks live in the `AdoptionApplication` aggregate.** It gets
   `handover_checked: frozenset[HandoverItem]`, stored in one column,
   `handover_checked text[] NOT NULL DEFAULT '{}'` (migration `0012`), like
   `animals.photo_urls`. It does not record who ticked or when: AT-26 does not ask
   for it.
2. **The State pattern decides when, the aggregate decides who.**
   `set_handover_item` is refused by the base `ApplicationState`
   (`InvalidTransition`, a 409) and applied only by `AcceptedState`. Only the owner or
   the applicant may tick; anyone else gets a 404, like the other adoption endpoints.
   The database agrees, with a CHECK like the one for the confirmations: nothing is
   ticked while a request is `open` or `closed`. Ticks stay when a request ends as
   declined, withdrawn or adopted.
3. **The keys are a backend enum, the words are a frontend constant.**
   `HandoverItem` holds four keys (`vaccination_booklet`, `microchip_transfer`,
   `care_notes`, `adoption_terms`). The title, the legal rule and the steps for each
   live in `src/lib/handover-checklist.ts`, like the guidelines. The domain refuses an
   unknown key, and a new item needs no migration. The two lists of keys are kept in
   step by hand, and a test pins the four.
4. **One endpoint, and no `GET`.** `PUT /applications/{id}/handover/{item}` with
   `{checked: bool}` returns the ticked items. The page reads the state from the two
   request lists, which now carry `handover_checked`. The use case takes the locks in
   the order of ADR 0017, decision 8 (animal, then application), so two ticks at once
   both stay and a tick queued behind the confirmation that adopts is refused.
5. **The checklist never blocks.** `confirm_handover` does not read it.
6. **The legal guidance was checked on 24 November 2026.**
   * Read in full: the SIAC transfer declaration (2025): the transfer needs the consent
     of both holders and must be reported within 15 days, "regardless of the reason
     (adoption, sale, etc.)". Also the Government's note on the registration of
     companion animals and the DECO guide: microchip and SIAC registration are
     mandatory for dogs, cats and ferrets.
   * **Not read:** Portaria 264/2013, which makes rabies vaccination mandatory for dogs
     over 3 months and voluntary for cats. It comes from search summaries of the
     Diário da República.
   * **No legal source found** for "adoption is not a sale". It stays a Patas rule and
     says so.
   * The SIAC form asks for ID, tax number and address of both people, and Patas never
     shows contact details, so the checklist tells them to do the transfer outside the
     chat: on the SIAC website or with a vet, parish council or municipality.
   * The microchip item applies to dogs, cats and ferrets. For other animals the person
     ticks it to skip it, so the list is the same for every species.

## Pending team agreement

`AGENTS.md` section 6 asks for business rules to be agreed with the team before they
are implemented. The code already follows these proposals:

* The four items, and their order.
* The legal text: the 15 days, the SIAC wording, and the rabies rule (to be checked
  against the Portaria itself).
* Tick-to-skip for animals that are not dogs, cats or ferrets, instead of a list that
  varies by species.
* Whether the vet-cost reimbursement mentioned in the guidelines needs a line here too.

## Consequences

* (+) The rule "only while accepted" is written once, in the State pattern, and the
  database repeats it.
* (+) A new item is a key in the enum and an entry in the constant: no migration, no
  endpoint.
* (-) The ticks do not say who made them or when. Adding that later turns the column
  into rows or a `jsonb` map, with a migration.
* (-) The wording and the legal text change only with a frontend deploy, and the law
  can change after the date it was checked.
* (-) `handover_checked` is in both request lists even when the person only opens one
  request.
* (-) The checklist is the same for every species, so a rabbit's adopter skips one
  item by ticking it.
* (-) The two lists of keys, backend and frontend, are kept in step by hand.
* The automated part of AT-26 for the checklist is `test_at_26_...`: it goes through
  the endpoints to the database. A teammate who did not write it follows the bullets
  in a browser.

## Alternatives considered

* **A separate `HandoverChecklist` aggregate, one row per ticked item.** There would be
  no lost update, but refusing ticks after the adoption means reading another
  aggregate's status, so more code and more coupling for a 2-point story.
* **Recording who ticked and when.** It gives context to both sides, but AT-26 does not
  ask for it, and it turns the column into rows.
* **A checklist that varies by species.** It is more exact for the microchip item, but
  it takes the animal's species to the request lists and makes the checklist depend on
  it, a larger design than the story needs.
* **A `GET` for the checklist.** One more endpoint to keep in step with the lists the
  page already loads.
