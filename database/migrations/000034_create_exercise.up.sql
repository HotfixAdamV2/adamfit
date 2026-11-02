/*
    Migration: 000034_create_exercise (up)

    What:
        Creates the new exercise table: each user's own, fully editable
        list of exercises, with type, equipment and instructions, and
        attaches fx_trg_set_updated_at.

    Why:
        Users log workouts against their own exercise list. Each user
        starts with a copy of standard_exercise (see 000038) and can then
        add, edit or remove exercises freely. Replaces the placeholder
        dropped in 000024.

    Notes:
        - Deleting an exercise in the app sets is_active to FALSE instead
          of removing the row, so future workout logs that use it keep
          working.
        - Names are unique per user among active exercises only, ignoring
          case, so a removed exercise's name can be reused. That needs a
          partial unique index (unq_exercise_user_id_exercise_name, on
          (user_id, LOWER(exercise_name)) WHERE is_active), because
          constraints cannot have a WHERE clause or an expression. To use
          it as an ON CONFLICT target, repeat the WHERE:
              ON CONFLICT (user_id, LOWER(exercise_name)) WHERE is_active
        - standard_exercise_id records which standard exercise a row was
          copied from (NULL for exercises the user created). ON DELETE
          SET NULL keeps the user's copy if the standard row is removed.
        - exercise_type and equipment reference the lookup tables (000025,
          000027) with ON UPDATE CASCADE, the same as standard_exercise.
        - Muscle tags live in exercise_muscle_group (000035), the picture
          in exercise_image (000037).
*/

-- Create sequence
CREATE SEQUENCE seq_exercise_exercise_id AS INT
    INCREMENT BY 1
    MINVALUE 1
    START WITH 1
    NO CYCLE;

-- Create the table
CREATE TABLE exercise (
    -- Fields
    exercise_id INTEGER NOT NULL DEFAULT nextval('seq_exercise_exercise_id'),
    user_id INTEGER NOT NULL,
    exercise_name VARCHAR(100) NOT NULL,
    exercise_type VARCHAR(20) NOT NULL,
    equipment VARCHAR(20) NOT NULL,
    instructions TEXT,
    standard_exercise_id INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    CONSTRAINT pk_exercise_exercise_id PRIMARY KEY (exercise_id),
    CONSTRAINT fk_exercise_user_id FOREIGN KEY (user_id)
        REFERENCES app_user (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_exercise_exercise_type FOREIGN KEY (exercise_type)
        REFERENCES exercise_type (type_code) ON UPDATE CASCADE,
    CONSTRAINT fk_exercise_equipment FOREIGN KEY (equipment)
        REFERENCES equipment (equipment_code) ON UPDATE CASCADE,
    CONSTRAINT fk_exercise_standard_exercise_id FOREIGN KEY (standard_exercise_id)
        REFERENCES standard_exercise (standard_exercise_id) ON DELETE SET NULL,
    CONSTRAINT chk_exercise_exercise_name CHECK (LENGTH(TRIM(exercise_name)) > 0)
);

ALTER SEQUENCE seq_exercise_exercise_id OWNED BY exercise.exercise_id;

-- Create indexes
CREATE UNIQUE INDEX unq_exercise_user_id_exercise_name
    ON exercise (user_id, LOWER(exercise_name))
    WHERE is_active;

CREATE INDEX idx_exercise_user_id ON exercise (user_id);

-- Trigger assignments
CREATE TRIGGER trg_exercise_set_updated_at
    BEFORE UPDATE ON exercise
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_set_updated_at();

-- Give grants
-- None needed: the master role owns the table.
