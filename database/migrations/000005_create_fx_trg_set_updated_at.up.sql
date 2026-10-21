/*
    Migration: 000005_create_fx_trg_set_updated_at (up)

    What:
        Creates the trigger function fx_trg_set_updated_at, and attaches it
        to app_user and user_weight so updated_at is refreshed on every
        UPDATE.

    Why:
        updated_at should always be accurate without relying on the
        application to remember to set it. The function is generic, so
        future tables only need a new trg_ assignment.
*/

-- Trigger function
CREATE FUNCTION fx_trg_set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

-- Trigger assignments
CREATE TRIGGER trg_app_user_set_updated_at
    BEFORE UPDATE ON app_user
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_set_updated_at();

CREATE TRIGGER trg_user_weight_set_updated_at
    BEFORE UPDATE ON user_weight
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_set_updated_at();
