# Patas: Product Vision Board

**Horizon:** the current academic MVP. The [MVP specification](../product/MVP.md)
defines its detailed scope. The longer-term ideas are kept separately in
[long-term vision](Vision.md) and are not commitments for
this release.

## Vision

Make responsible animal adoption clearer and easier by helping people find
animals that fit their home, communicate directly, and follow each adoption
request through handover, all in one web platform.

## Target Group

- **Primary:** people looking to adopt an animal and individuals publishing an
  animal for adoption. A registered user may be both.
- **Secondary:** visitors exploring animals before registering, and platform
  administrators responsible for moderation.

## Needs

1. **Adopters** need trustworthy animal information, help assessing household
   compatibility, and a clear way to apply and follow progress.
2. **Animal owners** need to publish and manage listings, review requests, and
   coordinate with applicants without losing the conversation or its context.
3. **Both parties** need a shared understanding of request status, a private
   communication channel, and a clear way to confirm handover.

## Product

1. A public, filterable animal catalog with a lifestyle Matchmaker that explains
   compatibility.
2. Self-service animal listings that owners can create, edit, and unpublish.
3. Adoption requests with participant-only conversations, shared request
   context, and an owner-managed process.
4. An Adoption Tracker with status notifications and a handover checklist that
   both parties confirm.

## Business Goals

Patas is an academic MVP, not a commercial service; no revenue or adoption-rate
claim is assumed. Its goals are to demonstrate user value and validate the
product with evidence:

1. **Demonstrate the complete core journey:** verify the flow from finding an
   animal through a request to handover confirmation with end-to-end tests.
2. **Reduce uncertainty during an application:** target that every adoption
   status change notifies the applicant, and check in usability sessions that
   adopters can find an animal and apply, while owners can review and progress a
   request, without assistance.
3. **Keep the result usable as a project deliverable:** run the MVP in Docker
   without requiring an external service.

These are goals to validate, not claims of measured real-world impact. Actual
adoption outcomes, reduced returns, and long-term association workload are
outside the evidence available for this MVP.

## Non-goals for the MVP

- Multi-association management or association verification.
- Fostering or Foster-to-Adopt, volunteer scheduling, and donation wishlists.
- Legal adoption contracts, and veterinary record management.
- Guaranteeing an animal-family match or claiming to prevent adoption returns.
