# Patas: MVP

Patas is a web platform where anyone can publish an animal for adoption and anyone
can find the one that fits their home. The whole adoption happens inside the platform.

## Users

| User | What they can do |
| :-- | :-- |
| Visitor | Browse the catalog, view animal profiles, take the Matchmaker quiz |
| Registered user | Everything a visitor can, plus publish animals (owner) and adopt (adopter); the same account can be both |
| Administrator | Handle reports, suspend users, remove listings |

## Features

### Accounts
- Register, log in and log out
- See and edit my profile

### Animals
- Publish an animal: name, species, age, size, sex, district, description, photos
- Describe the animal's compatibility (children, dogs, cats, energy, space)
- Edit and unpublish my animals
- "My animals" list
- Public catalog with filters (species, size, age group, district, compatibility)
- Animal profile page

### Matchmaker
- Lifestyle quiz (visitors: kept only for the session)
- Saved Matchmaker profile for registered users, including household (children, dogs, cats)
- Compatibility score for each animal, with the reasons for it

### Adoption
- Request to adopt by sending a first message; my Matchmaker profile is attached
- One conversation per request between the owner and the applicant
  - Text and photos (only the two participants can see the photos)
  - Request cards from the owner: home photos, other pets' photos, propose a meeting
  - Guidelines panel with suggested questions and safety tips
- Owner accepts one applicant; the animal becomes reserved
- Handover checklist; the adoption is completed when both sides confirm
- Adoption Tracker: timeline of each request
- Owner's list of requests received, grouped by status
- My requests list (adopter)

The adoption flow is detailed in [AdoptionPipeline](../domain/AdoptionPipeline.md).

### Notifications
- In-app notifications for status changes and new messages
- Email notifications for the same events

### Moderation
- Report a listing, a user or a message
- Administrator handles reports, suspends users, removes listings

## Quality
- Responsive layout and basic accessibility
- Personal data visible only to the people involved (GDPR)
- Runs fully in Docker with no external service required
- Demo seed data loaded through the application
