# Stories in this increment

This iteration delivered the adoption pipeline, the Matchmaker swiping feed, animal photos, unique usernames, quality infrastructure, and staging deployment.

## Adoption pipeline

| Story | Issue | Acceptance tests | ADR | Status |
| :-- | :-- | :-- | :-- | :-- |
| Adoption base — application aggregate, states, events | [#57](https://github.com/MESW-LES-2627/les-project-group-3/issues/57) | AT-21 (unpublish closes requests) [#75](https://github.com/MESW-LES-2627/les-project-group-3/issues/75) | [0017](../../architecture/adr/0017-adoption-base.md) | Done |
| Request to adopt | US-14 [#60](https://github.com/MESW-LES-2627/les-project-group-3/issues/60) | AT-16 [#70](https://github.com/MESW-LES-2627/les-project-group-3/issues/70) | [0019](../../architecture/adr/0019-requesting-to-adopt.md) | Done |
| See requests for my animals (owner) | US-15 [#61](https://github.com/MESW-LES-2627/les-project-group-3/issues/61) | AT-17 [#71](https://github.com/MESW-LES-2627/les-project-group-3/issues/71) | [0020](../../architecture/adr/0020-seeing-and-withdrawing-my-requests.md) | Done |
| Accept or decline a request | US-16 [#62](https://github.com/MESW-LES-2627/les-project-group-3/issues/62) | AT-17 [#71](https://github.com/MESW-LES-2627/les-project-group-3/issues/71), AT-18 [#72](https://github.com/MESW-LES-2627/les-project-group-3/issues/72) | [0020](../../architecture/adr/0020-seeing-and-withdrawing-my-requests.md) | Done |
| See and withdraw my requests (adopter) | US-17 [#63](https://github.com/MESW-LES-2627/les-project-group-3/issues/63) | AT-19 [#73](https://github.com/MESW-LES-2627/les-project-group-3/issues/73) | [0020](../../architecture/adr/0020-seeing-and-withdrawing-my-requests.md) | Done |
| Confirm handover | US-18 [#64](https://github.com/MESW-LES-2627/les-project-group-3/issues/64) | AT-20 [#74](https://github.com/MESW-LES-2627/les-project-group-3/issues/74) | — | Done |
| Republish my animal | US-19 [#65](https://github.com/MESW-LES-2627/les-project-group-3/issues/65) | AT-21 (republishing half) [#75](https://github.com/MESW-LES-2627/les-project-group-3/issues/75) | [0023](../../architecture/adr/0023-republishing.md) | Done |

## Matchmaker & catalog

| Story | Issue | Acceptance tests | ADR | Status |
| :-- | :-- | :-- | :-- | :-- |
| Browse animals and swipe (Matchmaker feed) | US-11 [#59](https://github.com/MESW-LES-2627/les-project-group-3/issues/59) | AT-14 [#68](https://github.com/MESW-LES-2627/les-project-group-3/issues/68), AT-15 [#69](https://github.com/MESW-LES-2627/les-project-group-3/issues/69) | [0026](../../architecture/adr/0026-matchmaker-swiping.md) | Done |
| Upload animal photos | US-13 [#67](https://github.com/MESW-LES-2627/les-project-group-3/issues/67) | — | — | Done |

## User management

| Story | Issue | Acceptance tests | ADR | Status |
| :-- | :-- | :-- | :-- | :-- |
| Choose a unique username | US-20 [#66](https://github.com/MESW-LES-2627/les-project-group-3/issues/66) | AT-22 [#76](https://github.com/MESW-LES-2627/les-project-group-3/issues/76) | [0024](../../architecture/adr/0024-usernames.md) | Done |

## Quality & infrastructure

| Task | Issue | ADR | Status |
| :-- | :-- | :-- | :-- |
| Test layout — unit, integration, acceptance | #79 | [0018](../../architecture/adr/0018-test-layout.md) | Done |
| Quality pipeline — coverage, mutation, audit, deploy gate | #82, #83 | [0021](../../architecture/adr/0021-quality-pipeline.md) | Done |
| Staging deployment and branch promotion | #84 | [0022](../../architecture/adr/0022-staging-deployment.md) | Done |
| Quality and clean-up — shared dialog, catalog paging, drop postal code | #58 | [0025](../../architecture/adr/0025-quality-and-clean-up.md) | Done |
