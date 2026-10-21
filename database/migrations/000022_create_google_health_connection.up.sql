/*
    Migration: 000022_create_google_health_connection (up)

    What:
        Creates the google_health_connection table: one row per user
        holding that user's Google Health (Fitbit) OAuth state, and
        attaches fx_trg_set_updated_at.

    Why:
        The app syncs weigh-ins from Google Health. Each user signs in to
        Google once; the refresh token is kept so later syncs can get new
        access tokens without asking again. The OAuth redirect from Google
        opens a fresh Streamlit session, so the pending login's state value
        must live in the database rather than in st.session_state.

    Notes:
        - user_id is the primary key: a user has at most one connection.
          It is not auto-incremented (it comes from app_user), so no
          sequence is needed.
        - refresh_token, access_token and their expiry are NULL until the
          user connects, and are cleared again on disconnect.
        - Tokens are stored in plain text because this is a local,
          single-user database. Refresh tokens are secrets: never log,
          print or display them.
        - granted_scopes is space-separated, exactly as Google returns it.
        - oauth_state is a random one-time value for a pending login,
          looked up when Google redirects back. It is unique so a lookup
          finds exactly one user; multiple NULLs are allowed. Clear it
          (and oauth_state_expires_at) once it has been used.
        - The primary key and unique constraint indexes cover all lookups,
          so no extra indexes are needed.
        - Rows are removed automatically if their user is deleted.
*/

-- Create the table
CREATE TABLE google_health_connection (
    -- Fields
    user_id INTEGER NOT NULL,
    refresh_token TEXT,
    access_token TEXT,
    access_token_expires_at TIMESTAMPTZ,
    granted_scopes TEXT,
    oauth_state VARCHAR(100),
    oauth_state_expires_at TIMESTAMPTZ,
    connected_at TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    CONSTRAINT pk_google_health_connection_user_id PRIMARY KEY (user_id),
    CONSTRAINT fk_google_health_connection_user_id FOREIGN KEY (user_id)
        REFERENCES app_user (user_id) ON DELETE CASCADE,
    CONSTRAINT unq_google_health_connection_oauth_state UNIQUE (oauth_state)
);

-- Trigger assignments
CREATE TRIGGER trg_google_health_connection_set_updated_at
    BEFORE UPDATE ON google_health_connection
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_set_updated_at();

-- Give grants
-- None needed: the master role owns the table.
