-- ============================================================================
-- Patas - Plataforma Colaborativa de Protecao Animal
-- Baseline Database Schema, Full-Text Search (GIN) & Triggers (PostgreSQL 16)
--
-- Aligned with: docs/domain/DomainModel.md, docs/domain/StateMachines.md, docs/domain/Glossary.md
-- ============================================================================

------------------------------------------------------------
-- SCHEMA CREATION
------------------------------------------------------------
DROP SCHEMA IF EXISTS patas CASCADE;
CREATE SCHEMA patas;
SET search_path TO patas;

------------------------------------------------------------
-- HELPER FUNCTIONS (used by CHECK constraints)
------------------------------------------------------------
-- PostgreSQL does not allow subqueries inside CHECK constraints, so array
-- validation is wrapped in an IMMUTABLE function.
CREATE FUNCTION text_array_has_no_blank(arr text[]) RETURNS boolean AS $$
    SELECT NOT EXISTS (
        SELECT 1 FROM unnest(arr) AS element
        WHERE char_length(btrim(element)) = 0
    );
$$ LANGUAGE sql IMMUTABLE;

------------------------------------------------------------
-- ENUMERATED TYPES
------------------------------------------------------------

-- Association Verification (StateMachines section 7)
CREATE TYPE verification_status AS ENUM (
    'pending',
    'verified',
    'rejected',
    'suspended'
);

-- Matchmaker questionnaire
CREATE TYPE activity_level AS ENUM (
    'low',
    'moderate',
    'high'
);

CREATE TYPE housing_type AS ENUM (
    'apartment',
    'house_no_yard',
    'house_with_yard'
);

CREATE TYPE time_away AS ENUM (
    'few_hours',
    'half_day',
    'most_of_day'
);

CREATE TYPE experience_level AS ENUM (
    'none',
    'some',
    'experienced'
);

-- Animal attributes
CREATE TYPE species AS ENUM (
    'dog',
    'cat',
    'other'
);

CREATE TYPE animal_size AS ENUM (
    'small',
    'medium',
    'large'
);

-- Animal Adoption Status (StateMachines section 1)
CREATE TYPE adoption_status AS ENUM (
    'available',
    'reserved',
    'in_trial',
    'adopted',
    'unavailable'
);

-- Animal Location (StateMachines section 2)
CREATE TYPE animal_location AS ENUM (
    'at_shelter',
    'awaiting_pickup',
    'in_foster_home',
    'with_adopter'
);

-- Adoption Application (StateMachines section 3)
CREATE TYPE application_status AS ENUM (
    'submitted',
    'screening',
    'on_hold',
    'interview',
    'trial_period',
    'completed',
    'rejected',
    'withdrawn',
    'closed'
);

-- Trial Period (StateMachines section 4)
CREATE TYPE trial_status AS ENUM (
    'requested',
    'approved',
    'active',
    'succeeded',
    'failed',
    'declined',
    'cancelled'
);



-- Foster Assignment (StateMachines section 5)
CREATE TYPE foster_assignment_status AS ENUM (
    'proposed',
    'accepted',
    'active',
    'completed',
    'declined',
    'cancelled'
);

-- Wishlist Item and Pledge (StateMachines section 6)
CREATE TYPE wishlist_item_status AS ENUM (
    'active',
    'closed'
);

CREATE TYPE pledge_status AS ENUM (
    'pledged',
    'confirmed',
    'released'
);

-- Notifications (email + in-app)
CREATE TYPE notification_type AS ENUM (
    'application_status_changed',
    'trial_updated',
    'foster_assignment_updated',
    'pledge_updated',
    'association_verification_updated'
);

------------------------------------------------------------
-- TABLES AND CONSTRAINTS
------------------------------------------------------------

-- 1. ASSOCIATIONS (Aggregate Root: Organization)
CREATE TABLE associations (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    name text NOT NULL,
    verification_status verification_status NOT NULL DEFAULT 'pending',
    default_trial_fee numeric(12, 2) NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT associations_pkey PRIMARY KEY (id),
    CONSTRAINT associations_name_not_blank_check CHECK (char_length(btrim(name)) > 0),
    CONSTRAINT associations_default_trial_fee_non_negative_check CHECK (default_trial_fee >= 0)
);

COMMENT ON TABLE associations IS
    'Animal protection organization that manages animals, applications, and wishlists.';
COMMENT ON COLUMN associations.name IS 'Public display name of the association.';
COMMENT ON COLUMN associations.verification_status IS
    'Platform Administrator verification. Only verified associations may publish animals (enforced by the application layer).';
COMMENT ON COLUMN associations.default_trial_fee IS
    'Default Foster-to-Adopt trial fee. Copied into trial_periods.fee_amount at approval time.';

-- 2. USERS (Aggregate Root: Citizen)
CREATE TABLE users (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    name text NOT NULL,
    email text UNIQUE NOT NULL,
    is_platform_admin boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT users_name_not_blank_check CHECK (char_length(btrim(name)) > 0),
    CONSTRAINT users_email_not_blank_check CHECK (char_length(btrim(email)) > 0),
    CONSTRAINT users_email_format_check CHECK (position('@' in email) > 1)
);

COMMENT ON TABLE users IS
    'Registered citizen. Visitor is unauthenticated and has no row.';
COMMENT ON COLUMN users.email IS
    'Unique login identity; case-insensitive lookups supported via idx_users_email_lower.';
COMMENT ON COLUMN users.is_platform_admin IS
    'AdminRole: verifies associations and moderates globally.';

-- 3. MATCHMAKER PROFILES (Lifestyle Questionnaire: 1-to-1 extension)
CREATE TABLE matchmaker_profiles (
    user_id uuid NOT NULL,
    activity activity_level NOT NULL,
    housing housing_type NOT NULL,
    time_away time_away NOT NULL,
    experience experience_level NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT matchmaker_profiles_pkey PRIMARY KEY (user_id),
    CONSTRAINT matchmaker_profiles_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

COMMENT ON TABLE matchmaker_profiles IS
    'Saved lifestyle questionnaire of a Citizen. Visitors answers are session-only and never stored. updated_at tracks preference freshness.';

-- 4. VOLUNTEER PROFILES (Role profile: preference tags)
CREATE TABLE volunteer_profiles (
    user_id uuid NOT NULL,
    preferences text[] NOT NULL DEFAULT ARRAY[]::text[],
    CONSTRAINT volunteer_profiles_pkey PRIMARY KEY (user_id),
    CONSTRAINT volunteer_profiles_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT volunteer_profiles_preferences_not_blank_check
        CHECK (text_array_has_no_blank(preferences))
);

COMMENT ON TABLE volunteer_profiles IS
    'Role: Citizen who offers time for walks, socialization, or operational shifts.';

-- 5. FOSTER PROFILES (Role profile: parametric fostering)
CREATE TABLE foster_profiles (
    user_id uuid NOT NULL,
    housing_conditions text NOT NULL,
    accepted_species species[] NOT NULL,
    max_size animal_size NOT NULL,
    max_simultaneous_animals integer NOT NULL DEFAULT 1,
    available_from date NOT NULL DEFAULT current_date,
    available_until date,
    is_active boolean NOT NULL DEFAULT true,
    CONSTRAINT foster_profiles_pkey PRIMARY KEY (user_id),
    CONSTRAINT foster_profiles_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT foster_profiles_housing_conditions_not_blank_check
        CHECK (char_length(btrim(housing_conditions)) > 0),
    CONSTRAINT foster_profiles_accepted_species_not_empty_check
        CHECK (cardinality(accepted_species) > 0),
    CONSTRAINT foster_profiles_max_simultaneous_positive_check
        CHECK (max_simultaneous_animals > 0),
    CONSTRAINT foster_profiles_availability_window_check
        CHECK (available_until IS NULL OR available_until >= available_from)
);

COMMENT ON TABLE foster_profiles IS
    'Role: Citizen registered as a Foster Family. Parameters feed the Parametric Fostering Engine.';
COMMENT ON COLUMN foster_profiles.available_until IS
    'End of the availability window. NULL means ongoing availability.';
COMMENT ON COLUMN foster_profiles.is_active IS
    'FALSE hides the family from engine searches (e.g., on holiday) without deleting the profile.';

-- 6. ASSOCIATION MEMBERSHIPS (Staff Join Table, StaffProfile in the domain model)
CREATE TABLE association_memberships (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    association_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT association_memberships_pkey PRIMARY KEY (id),
    CONSTRAINT association_memberships_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT association_memberships_association_id_fkey
        FOREIGN KEY (association_id) REFERENCES associations (id) ON DELETE RESTRICT,
    CONSTRAINT association_memberships_user_id_association_id_key
        UNIQUE (user_id, association_id)
);

COMMENT ON TABLE association_memberships IS
    'Links a User to an Association as Staff. Enforces data isolation between associations. created_at marks when membership began.';

-- 7. ANIMALS (Aggregate Root: Pet under shelter care)
CREATE TABLE animals (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    association_id uuid NOT NULL,
    name text NOT NULL,
    species species NOT NULL,
    age_in_months integer,
    size animal_size,
    temperament text,
    compatibility jsonb NOT NULL DEFAULT '{}'::jsonb,
    photos text[] NOT NULL DEFAULT ARRAY[]::text[],
    description text,
    tsvectors tsvector,
    adoption_status adoption_status NOT NULL DEFAULT 'available',
    location animal_location NOT NULL DEFAULT 'at_shelter',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT animals_pkey PRIMARY KEY (id),
    CONSTRAINT animals_association_id_fkey
        FOREIGN KEY (association_id) REFERENCES associations (id) ON DELETE RESTRICT,
    CONSTRAINT animals_name_not_blank_check CHECK (char_length(btrim(name)) > 0),
    CONSTRAINT animals_age_non_negative_check CHECK (age_in_months IS NULL OR age_in_months >= 0),
    CONSTRAINT animals_photos_not_blank_check CHECK (text_array_has_no_blank(photos)),
    CONSTRAINT animals_compatibility_is_object_check CHECK (jsonb_typeof(compatibility) = 'object')
);

COMMENT ON TABLE animals IS
    'Pet under the care of an Association. Two independent state dimensions: adoption_status and location.';
COMMENT ON COLUMN animals.compatibility IS
    'Extensible behavioral profile and compatibility criteria (good_with_*, needs_yard, energy_level, etc.) for catalog filters and Matchmaker. Indexed via GIN jsonb_path_ops.';
COMMENT ON COLUMN animals.photos IS 'Photo URLs in display order.';
COMMENT ON COLUMN animals.description IS
    'Free-form story and behavioral notes; full-text indexed and parsed for Matchmaker.';

-- 8. FOSTER ASSIGNMENTS (Entity inside Animal: temporary fostering history)
CREATE TABLE foster_assignments (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    animal_id uuid NOT NULL,
    foster_user_id uuid NOT NULL,
    status foster_assignment_status NOT NULL DEFAULT 'proposed',
    start_date date,
    end_date date,
    internal_notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT foster_assignments_pkey PRIMARY KEY (id),
    CONSTRAINT foster_assignments_animal_id_fkey
        FOREIGN KEY (animal_id) REFERENCES animals (id) ON DELETE CASCADE,
    CONSTRAINT foster_assignments_foster_user_id_fkey
        FOREIGN KEY (foster_user_id) REFERENCES foster_profiles (user_id) ON DELETE RESTRICT,
    CONSTRAINT foster_assignments_dates_check
        CHECK (start_date IS NULL OR end_date IS NULL OR end_date >= start_date),
    CONSTRAINT foster_assignments_active_has_start_check
        CHECK (status NOT IN ('active', 'completed') OR start_date IS NOT NULL)
);

COMMENT ON TABLE foster_assignments IS
    'Temporary fostering history of an animal. Starts as a proposal that the family must accept. At most one open assignment per animal (partial index).';
COMMENT ON COLUMN foster_assignments.start_date IS 'Set when staff confirm pickup.';
COMMENT ON COLUMN foster_assignments.end_date IS 'Set when the animal is returned or handed to an adopter.';

-- 9. ADOPTION APPLICATIONS (Aggregate Root: Formal adoption process)
CREATE TABLE adoption_applications (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    applicant_id uuid NOT NULL,
    animal_id uuid NOT NULL,
    status application_status NOT NULL DEFAULT 'submitted',
    submitted_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT adoption_applications_pkey PRIMARY KEY (id),
    CONSTRAINT adoption_applications_applicant_id_fkey
        FOREIGN KEY (applicant_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT adoption_applications_animal_id_fkey
        FOREIGN KEY (animal_id) REFERENCES animals (id) ON DELETE RESTRICT
);

COMMENT ON TABLE adoption_applications IS
    'Formal adoption process. Active uniqueness and single-reservation rules enforced via partial indexes. Status history tracked in application_status_changes.';

-- 10. APPLICATION STATUS HISTORY (Append-only, source of the Adoption Tracker timeline)
CREATE TABLE application_status_changes (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    application_id uuid NOT NULL,
    from_status application_status,
    to_status application_status NOT NULL,
    changed_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT application_status_changes_pkey PRIMARY KEY (id),
    CONSTRAINT application_status_changes_application_id_fkey
        FOREIGN KEY (application_id) REFERENCES adoption_applications (id) ON DELETE CASCADE
);

COMMENT ON TABLE application_status_changes IS
    'Append-only status history. from_status is NULL for the initial submission. Feeds the Adoption Tracker timeline.';

-- 11. APPLICATION NOTES (Private staff notes across the application lifecycle)
CREATE TABLE application_notes (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    application_id uuid NOT NULL,
    author_id uuid NOT NULL,
    note text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT application_notes_pkey PRIMARY KEY (id),
    CONSTRAINT application_notes_application_id_fkey
        FOREIGN KEY (application_id) REFERENCES adoption_applications (id) ON DELETE CASCADE,
    CONSTRAINT application_notes_author_id_fkey
        FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT application_notes_note_not_blank_check CHECK (char_length(btrim(note)) > 0)
);

COMMENT ON TABLE application_notes IS
    'Private notes added by Association Staff during screening, interview, or follow-up. Never exposed to the applicant.';

-- 12. TRIAL PERIODS (Foster-to-Adopt window inside Application, own lifecycle)
CREATE TABLE trial_periods (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    application_id uuid NOT NULL,
    status trial_status NOT NULL DEFAULT 'requested',
    start_date date,
    end_date date,
    fee_amount numeric(12, 2) NOT NULL DEFAULT 0,
    is_fee_paid boolean NOT NULL DEFAULT false,
    payment_reference text,
    outcome_notes text,
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT trial_periods_pkey PRIMARY KEY (id),
    CONSTRAINT trial_periods_application_id_fkey
        FOREIGN KEY (application_id) REFERENCES adoption_applications (id) ON DELETE CASCADE,
    CONSTRAINT trial_periods_application_id_key UNIQUE (application_id),
    CONSTRAINT trial_periods_dates_check
        CHECK (start_date IS NULL OR end_date IS NULL OR end_date >= start_date),
    CONSTRAINT trial_periods_fee_amount_non_negative_check CHECK (fee_amount >= 0)
);

COMMENT ON TABLE trial_periods IS
    'Foster-to-Adopt trial. The adopter requests it; the association approves or declines. Dates are set when the trial becomes active.';
COMMENT ON COLUMN trial_periods.fee_amount IS
    'Copied from associations.default_trial_fee at approval time; later changes do not affect existing trials.';
COMMENT ON COLUMN trial_periods.payment_reference IS 'Payment reference (e.g., Stripe test mode).';
COMMENT ON COLUMN trial_periods.outcome_notes IS 'Optional closing notes or outcome details upon completion or failure.';

-- 13. TRIAL CHECK-INS (Append-only Follow-up Log)
CREATE TABLE trial_check_ins (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    trial_period_id uuid NOT NULL,
    note text NOT NULL,
    logged_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT trial_check_ins_pkey PRIMARY KEY (id),
    CONSTRAINT trial_check_ins_trial_period_id_fkey
        FOREIGN KEY (trial_period_id) REFERENCES trial_periods (id) ON DELETE CASCADE,
    CONSTRAINT trial_check_ins_note_not_blank_check CHECK (char_length(btrim(note)) > 0)
);

COMMENT ON TABLE trial_check_ins IS
    'Append-only follow-up notes logged during an active trial period (logged_at).';

-- 14. WISHLIST ITEMS (Aggregate Root: Material need, no hard limits)
CREATE TABLE wishlist_items (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    association_id uuid NOT NULL,
    item_name text NOT NULL,
    target_quantity integer NOT NULL,
    status wishlist_item_status NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT wishlist_items_pkey PRIMARY KEY (id),
    CONSTRAINT wishlist_items_association_id_fkey
        FOREIGN KEY (association_id) REFERENCES associations (id) ON DELETE RESTRICT,
    CONSTRAINT wishlist_items_item_name_not_blank_check
        CHECK (char_length(btrim(item_name)) > 0),
    CONSTRAINT wishlist_items_target_quantity_positive_check
        CHECK (target_quantity > 0)
);

COMMENT ON TABLE wishlist_items IS
    'In-kind need published by an Association. Stays open for pledges until staff close it.';
COMMENT ON COLUMN wishlist_items.target_quantity IS
    'Soft target that drives priority. It is NOT a limit: no constraint caps the pledged quantity.';
COMMENT ON COLUMN wishlist_items.status IS
    'Closed items are hidden and take no new pledges (enforced by the application layer); existing pledges can still be confirmed or released.';

-- 15. PLEDGES (Commitment to provide wishlist items)
CREATE TABLE pledges (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    wishlist_item_id uuid NOT NULL,
    user_id uuid NOT NULL,
    quantity integer NOT NULL,
    status pledge_status NOT NULL DEFAULT 'pledged',
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pledges_pkey PRIMARY KEY (id),
    CONSTRAINT pledges_wishlist_item_id_fkey
        FOREIGN KEY (wishlist_item_id) REFERENCES wishlist_items (id) ON DELETE CASCADE,
    CONSTRAINT pledges_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT pledges_quantity_positive_check CHECK (quantity > 0)
);

COMMENT ON TABLE pledges IS
    'Citizen commitment to provide a quantity of an item. Confirmed or released as a whole. created_at tracks commitment timestamp.';

-- 16. NOTIFICATIONS (In-app notifications driven by domain events)
CREATE TABLE notifications (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    recipient_id uuid NOT NULL,
    type notification_type NOT NULL,
    message text NOT NULL,
    read_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT notifications_pkey PRIMARY KEY (id),
    CONSTRAINT notifications_recipient_id_fkey
        FOREIGN KEY (recipient_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT notifications_message_not_blank_check CHECK (char_length(btrim(message)) > 0)
);

COMMENT ON TABLE notifications IS
    'In-app notifications created by domain events. read_at is NULL until seen by the user.';

-- * ====================================================
-- * Views (derived values, never stored)
-- * ====================================================

-- Wishlist progress: confirmed = received, pledged = promised, committed = both.
-- coverage = committed / target; priority orders the public wishlist (High first).
-- Thresholds: High below 50%, Medium 50% to below 100%, Low at 100% or more.
CREATE VIEW wishlist_item_progress AS
SELECT
    w.id AS wishlist_item_id,
    w.association_id,
    w.item_name,
    w.status,
    w.target_quantity,
    q.confirmed_quantity,
    q.pledged_quantity,
    q.confirmed_quantity + q.pledged_quantity AS committed_quantity,
    GREATEST(0, w.target_quantity - q.confirmed_quantity) AS remaining_to_target,
    round((q.confirmed_quantity + q.pledged_quantity)::numeric / w.target_quantity, 4) AS coverage,
    CASE
        WHEN (q.confirmed_quantity + q.pledged_quantity) * 2 < w.target_quantity THEN 'high'
        WHEN (q.confirmed_quantity + q.pledged_quantity) < w.target_quantity THEN 'medium'
        ELSE 'low'
    END AS priority
FROM wishlist_items w
CROSS JOIN LATERAL (
    SELECT
        COALESCE(SUM(p.quantity) FILTER (WHERE p.status = 'confirmed'), 0)::integer AS confirmed_quantity,
        COALESCE(SUM(p.quantity) FILTER (WHERE p.status = 'pledged'), 0)::integer AS pledged_quantity
    FROM pledges p
    WHERE p.wishlist_item_id = w.id
) q;

COMMENT ON VIEW wishlist_item_progress IS
    'Derived wishlist quantities, coverage and priority. Targets are soft: nothing here blocks a pledge.';

-- * ====================================================
-- * Index Creation
-- * ====================================================
-- Note: Foreign key indexes are managed automatically by the ORM/Alembic layer.

-- 1. Case-insensitive fast lookup for authentication
CREATE UNIQUE INDEX idx_users_email_lower
    ON users USING btree (lower(email));

-- 2. Domain Lifecycle Invariant: At most 1 ACTIVE application per applicant per animal
CREATE UNIQUE INDEX idx_adoption_applications_one_open_per_applicant_animal
    ON adoption_applications (applicant_id, animal_id)
    WHERE status NOT IN ('completed', 'rejected', 'withdrawn', 'closed');

-- 3. Reservation rule: only ONE application per animal can be in Interview or Trial Period
CREATE UNIQUE INDEX idx_adoption_applications_one_reserving_per_animal
    ON adoption_applications (animal_id)
    WHERE status IN ('interview', 'trial_period');

-- 4. Fostering rule: at most ONE open foster assignment per animal
CREATE UNIQUE INDEX idx_foster_assignments_one_open_per_animal
    ON foster_assignments (animal_id)
    WHERE status IN ('proposed', 'accepted', 'active');

-- * ====================================================
-- * Full Text Search Index Creation (GIN)
-- * ====================================================

-- Optimized search trigger: recalculates tsvectors ONLY if name, species, or description changes.
-- Normal status/location/timestamp transitions do not trigger GIN re-indexing.
CREATE OR REPLACE FUNCTION animal_search_update() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        NEW.tsvectors = (
            setweight(to_tsvector('portuguese', COALESCE(NEW.name, '')), 'A') ||
            setweight(to_tsvector('portuguese', COALESCE(NEW.species::text, '')), 'B') ||
            setweight(to_tsvector('portuguese', COALESCE(NEW.description, '')), 'C')
        );
    ELSIF TG_OP = 'UPDATE' THEN
        IF (NEW.name <> OLD.name OR NEW.species <> OLD.species OR NEW.description IS DISTINCT FROM OLD.description) THEN
            NEW.tsvectors = (
                setweight(to_tsvector('portuguese', COALESCE(NEW.name, '')), 'A') ||
                setweight(to_tsvector('portuguese', COALESCE(NEW.species::text, '')), 'B') ||
                setweight(to_tsvector('portuguese', COALESCE(NEW.description, '')), 'C')
            );
        END IF;
    END IF;
    RETURN NEW;
END $$
LANGUAGE plpgsql;

CREATE TRIGGER trigger_animal_search_update
BEFORE INSERT OR UPDATE ON animals
FOR EACH ROW
EXECUTE FUNCTION animal_search_update();

CREATE INDEX idx_animals_search ON animals USING GIN (tsvectors);

-- Fast JSONB containment queries (@>) for catalog filtering and Matchmaker
CREATE INDEX idx_animals_compatibility_gin ON animals USING GIN (compatibility jsonb_path_ops);

-- * ====================================================
-- * Triggers (Selective updated_at Maintenance)
-- * ====================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_associations_set_updated_at
    BEFORE UPDATE ON associations
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trigger_users_set_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trigger_matchmaker_profiles_set_updated_at
    BEFORE UPDATE ON matchmaker_profiles
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trigger_animals_set_updated_at
    BEFORE UPDATE ON animals
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trigger_foster_assignments_set_updated_at
    BEFORE UPDATE ON foster_assignments
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trigger_adoption_applications_set_updated_at
    BEFORE UPDATE ON adoption_applications
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trigger_trial_periods_set_updated_at
    BEFORE UPDATE ON trial_periods
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trigger_wishlist_items_set_updated_at
    BEFORE UPDATE ON wishlist_items
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();
