/*
    Migration: 000031_create_standard_exercise (up)

    What:
        Creates the standard_exercise table: the starter list of
        exercises with their type, equipment and short instructions.

    Why:
        Every user gets their own editable copy of this list when their
        account is created (see 000038). Keeping the template in its own
        table means new users always start from the same, curated list.
        Like standard_food, it is managed by hand, not by the app.

    Notes:
        - exercise_type must be a type_code in exercise_type (000025) and
          equipment an equipment_code in equipment (000027). ON UPDATE
          CASCADE means renaming a code updates every exercise using it.
        - Names are unique ignoring case, through the unique index
          unq_standard_exercise_exercise_name on LOWER(exercise_name).
        - Muscle tags live in standard_exercise_muscle_group (000032).
*/

-- Create sequence
CREATE SEQUENCE seq_standard_exercise_standard_exercise_id AS INT
    INCREMENT BY 1
    MINVALUE 1
    START WITH 1
    NO CYCLE;

-- Create the table
CREATE TABLE standard_exercise (
    -- Fields
    standard_exercise_id INTEGER NOT NULL DEFAULT nextval('seq_standard_exercise_standard_exercise_id'),
    exercise_name VARCHAR(100) NOT NULL,
    exercise_type VARCHAR(20) NOT NULL,
    equipment VARCHAR(20) NOT NULL,
    instructions TEXT,
    -- Constraints
    CONSTRAINT pk_standard_exercise_standard_exercise_id PRIMARY KEY (standard_exercise_id),
    CONSTRAINT fk_standard_exercise_exercise_type FOREIGN KEY (exercise_type)
        REFERENCES exercise_type (type_code) ON UPDATE CASCADE,
    CONSTRAINT fk_standard_exercise_equipment FOREIGN KEY (equipment)
        REFERENCES equipment (equipment_code) ON UPDATE CASCADE,
    CONSTRAINT chk_standard_exercise_exercise_name CHECK (LENGTH(TRIM(exercise_name)) > 0)
);

ALTER SEQUENCE seq_standard_exercise_standard_exercise_id OWNED BY standard_exercise.standard_exercise_id;

-- Create indexes
CREATE UNIQUE INDEX unq_standard_exercise_exercise_name
    ON standard_exercise (LOWER(exercise_name));

-- Give grants
-- None needed: the master role owns the table.
