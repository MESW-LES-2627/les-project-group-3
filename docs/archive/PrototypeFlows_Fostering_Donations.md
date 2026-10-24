# Prototyping Flows: Temporary Fostering & Donations

This document outlines the core UI/UX "Happy Paths" required for the MVP prototype, plus the main alternative paths and open questions. Terms are defined in [Glossary](../domain/Glossary.md); transitions were in the Vision-era `StateMachines.md` (removed; see git history).

## Preconditions (shared foundations)

Both modules depend on the foundation features from Sprint 1:
* A **verified Association** exists and Association Staff can log in (Staff are linked to that Association and only see its data).
* At least one **Animal** is registered by the Association (location `At Shelter`, adoption status `Available`).
* Citizens can register and log in.

## Module A: Solidarity Wishlist (Donations)

### Association Flow (Back-Office)
1. **Navigate to Wishlist:** Staff opens the Wishlist management tab.
2. **Create Need:** Staff adds a new `WishlistItem` (e.g., "Fleece Blankets") and sets a `targetQuantity`. The target is a soft goal that sets the item's priority; it is not a limit.
3. **Confirm Pledges:** Staff views pending pledges and clicks "Confirm Receipt" when items arrive. The pledge becomes `Confirmed` and the item's confirmed quantity increases.
4. **Release Pledges:** Staff clicks "Release" on old unfulfilled pledges. The pledge becomes `Released` and its quantity no longer counts toward the item's coverage.
5. **Close Item:** When the association has enough, Staff clicks "Close". The item disappears from the public wishlist and takes no new pledges; pledges still in `Pledged` status can be confirmed or released. Staff can reopen it later.

### Citizen Flow
1. **Browse Wishlist:** Any Visitor or Citizen views the reverse marketplace of needed items, ordered by priority (High first), with each item's target, confirmed and pledged quantities.
2. **Make a Pledge:** A logged-in Citizen selects an item, specifies any quantity (there is no upper limit while the item is listed), and clicks "Pledge". A Visitor who clicks "Pledge" is asked to log in or register first.
3. **Instructions:** The UI displays drop-off instructions or the shipping address (no online payments required).
4. **My Pledges:** The Citizen can see their pledges and their status (`Pledged`, `Confirmed`, `Released`).

### Alternative paths
* Target covered: the item shows as covered (Low priority) but stays listed and keeps accepting pledges until Staff closes it.
* Item closed while a donor is pledging: the pledge is refused with a message that the item is no longer needed.

## Module B: Parametric Temporary Fostering

### Citizen Flow (Profile Setup)
1. **Enable Fostering:** Citizen goes to their account settings and activates the `FosterProfile` role.
2. **Set Parameters:** Citizen fills out a form detailing their `HousingConditions` (e.g., garden, apartment), accepted species, maximum animal size, number of simultaneous animals, and availability window (one-off or ongoing).
3. **Pause/Resume:** Citizen can mark the profile inactive (e.g., on holiday) so they no longer appear in searches.

### Association Flow (Assignment)
1. **Identify Need:** Staff identifies an animal needing temporary shelter.
2. **Search Engine:** Staff opens the Parametric Fostering Engine and filters available families by matching the animal's needs against the families' parameters. Families already at capacity or outside their availability window are excluded.
3. **Propose Assignment:** Staff selects a family. A `FosterAssignment` is created as `Proposed` and the family is notified (email + in-app). The animal's location does not change yet.
4. **Family Accepts:** The family accepts the proposal. The assignment becomes `Accepted` and the system updates the animal's location to `Awaiting Pickup`.
5. **Confirm Pickup:** When the family arrives at the shelter and takes the animal, Staff clicks "Confirm Pickup". The assignment becomes `Active` and the location becomes `In Foster Home`.
6. **Return to Shelter:** When fostering ends, Staff clicks "Confirm Return". The assignment becomes `Completed` and the location returns to `At Shelter`.

### Alternative paths
* **Family declines:** the assignment becomes `Declined`; nothing changes for the animal; Staff returns to the search results.
* **Family cancels or no-show:** the assignment becomes `Cancelled` and the animal's location returns from `Awaiting Pickup` to `At Shelter`.
* **Staff withdraws a pending proposal:** the assignment becomes `Cancelled`.
* **Fostered animals stay adoptable:** a fostered animal can remain `Available` and keep receiving applications while `In Foster Home`.


