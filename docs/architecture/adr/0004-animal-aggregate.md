# ADR 0004: Animal aggregate in the MVP

| | |
| :-- | :-- |
| **Status** | Accepted |
| **Date** | 2026-10-17 |
| **Scope** | A1 (create) and A2 (list), vertical prototype |
| **Related** | [MVPVision](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/product/MVPVision.md), [VerticalPrototypeSpec](../../integrations/vertical-prototype/VerticalPrototypeSpec.md), ADR 0001 |

## Context

The MVP is a peer-to-peer marketplace: any registered user publishes animals
(MVPVision MD1, MD2, MD4). `database/create.sql`, [DomainModel](../../archive/DomainModel.md) and
[StateMachines](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/domain/StateMachines.md) still describe the association model and the location state,
so the `animals` table is defined by Alembic (migration `0003`), not by `create.sql`.

## Decisions

1. **The owner is a User (MD2).** `animals.owner_id` references `patas.users`
   with `ON DELETE RESTRICT`. There is no Association or Publisher entity.
   Later, associations are added by creating one publisher per user and repointing
   `owner_id`.
2. **One state machine (MD4).** The table has `adoption_status` and no `location`.
   `AdoptionStatus` lists the five values of the database enum but has no
   transitions yet. The State pattern arrives with the feature that changes the
   status (applications), not before (`AGENTS.md` §2).
3. **Rich domain, not an anemic record.** `Animal` is a dataclass that enforces its
   own invariants in the constructor: the name is trimmed and not blank, and the
   age is unknown or at least 0. `Animal.publish` is the only way to create a new
   listing: it generates the id (`uuid4`, no database default) and starts the animal
   `available`. The database repeats the name and age rules as `CHECK`s.
4. **Slice-minimum schema.** `id`, `owner_id`, `name`, `species`, `age_in_months`
   (nullable), `adoption_status` (default `available`), `created_at`, `updated_at`
   (the `set_updated_at` trigger). Size, temperament, compatibility, photos,
   description and the search vector are not here. Each is an additive migration
   made by the feature that needs it (catalog filters, compatibility profile).
5. **Native PostgreSQL enums** `patas.species` (`dog`, `cat`, `other`) and
   `patas.adoption_status`, named as in `create.sql`. The database rejects any
   other value.
6. **The catalog read is `list_all()`:** every animal of every owner, newest first
   (`created_at DESC, id`). There is no status filter yet because only `available`
   is reachable. Whether `reserved` or `adopted` animals appear is a business rule to
   align with the team when status transitions exist.
7. **Persistence follows ADR 0001 §7:** no ORM, SQL written by hand in the repository,
   explicit row mapping, and the caller owns the transaction.

## Consequences

* (+) The next features (`POST /animals`, `GET /animals`, the frontend) build on a
  tested contract: the invariants are checked in the domain and in the database.
* (+) The id exists before the insert, so a service can use it without a round trip.
* (+) `owner_id` makes "my animals" (A1) a simple `WHERE` later.
* (-) Native enums need a `CAST` in the raw SQL, and adding a value needs
  `ALTER TYPE ... ADD VALUE`.
* (-) `create.sql`, [DomainModel](../../archive/DomainModel.md) and [StateMachines](https://github.com/MESW-LES-2627/les-project-group-3/blob/iter-0/docs/domain/StateMachines.md) still describe the
  association model; reconciling them is a separate task.
* (-) Until the State pattern lands, nothing prevents an invalid status change,
  which is acceptable because nothing changes the status yet.
* (-) `animals` has no index on `owner_id` or `created_at` yet. Add them when the
  owner's list or a large catalog needs them.
* (-) Two animals added in the same transaction share `created_at`; `id` only makes
  their order deterministic.
