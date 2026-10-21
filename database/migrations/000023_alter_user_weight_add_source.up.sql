/*
    Migration: 000023_alter_user_weight_add_source (up)

    What:
        Adds a source column to user_weight, recording where each weigh-in
        came from, with a check constraint limiting it to known sources.

    Why:
        Weigh-ins can now be synced from Google Health (Fitbit) as well as
        entered by hand. The app needs to tell them apart, for example to
        show where a value came from or to decide whether a sync may
        overwrite a row.

    Notes:
        - Allowed values: 'manual' and 'google_health'.
        - The default is 'manual', so every existing row becomes 'manual'
          and existing inserts that do not set source keep working.
        - The one-row-per-user-per-day rule
          (unq_user_weight_user_id_weigh_date) is unchanged, so a synced
          value and a manual value for the same day share one row.
*/

ALTER TABLE user_weight
    ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'manual',
    ADD CONSTRAINT chk_user_weight_source
        CHECK (source IN ('manual', 'google_health'));
