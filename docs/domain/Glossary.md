# Glossary

Terms used in code, stories and conversations. Features are in [MVP](../product/MVP.md);
the adoption flow is in [AdoptionPipeline](AdoptionPipeline.md).

## People
- **Visitor:** not logged in. Browses the catalog, views animal profiles, takes the Matchmaker quiz.
- **User:** registered user. The same account can be an owner and an applicant.
- **Owner:** the user who published an animal.
- **Applicant:** a user who sent an adoption request for someone else's animal.
- **Administrator:** platform operator. Handles reports, suspends users, removes listings.

## Animals
- **Animal:** an animal published by its owner, with its profile (name, species, age, size,
  sex, district, description, photos) and compatibility profile.
- **Compatibility Profile:** who the animal can live with (children, dogs, cats) and what it
  needs (energy, space). Feeds the catalog filters and the Matchmaker.
- **Catalog:** the public list of published animals, with filters.
- **Unpublish:** the owner removes the animal from the catalog; its data is kept.
- **Adoption Status:** Available, Reserved, In Trial, Adopted, Unavailable.

## Matchmaker
- **Matchmaker:** suggests animals from a lifestyle quiz.
- **Matchmaker Profile:** a user's saved quiz answers, including household (children, dogs,
  cats). Visitors' answers are kept only for the session.
- **Compatibility Score:** how well an animal fits a Matchmaker Profile, with the reasons.

## Adoption
- **Adoption Application:** an applicant's request to adopt one animal ("request" in the UI).
  Starts with the applicant's first message.
- **Application Status:** Open, Accepted, In Trial, Adopted, Declined, Withdrawn, Closed.
- **Conversation:** the chat of one application. Only the applicant and the owner take part.
- **Request Card:** a one-tap request from the owner in the conversation (home photos,
  other pets' photos, propose a meeting).
- **Guidelines Panel:** suggested questions and safety tips next to the conversation. Advisory only.
- **Foster-to-Adopt Trial:** optional period where the applicant takes the animal home before
  the adoption is final. The owner approves it.
- **Handover:** the moment the animal goes to the applicant. The adoption is complete when
  both sides confirm it.
- **Handover Checklist:** vaccination booklet, SIAC microchip transfer, food and habits notes,
  adoption terms.
- **Adoption Tracker:** the timeline of an application, built from its status changes.

## Platform
- **Notification:** in-app and email message sent on a status change or a new message.
- **Report:** a complaint about a listing, a user or a message, handled by the Administrator.
