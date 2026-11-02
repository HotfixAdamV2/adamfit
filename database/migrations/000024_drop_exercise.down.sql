/*
    Migration: 000024_drop_exercise (down)

    What:
        Recreates the placeholder exercise table exactly as 000001 made it
        (sequence, table, index) and re-inserts the five dummy rows from
        000002.

    Why:
        Reverts 000024_drop_exercise, so the database is back in the state
        000023 left it in.

    Notes:
        - Data loss: the table holds only the dummy rows, which are
          re-inserted. Nothing from the new exercise library survives a
          rollback past this point (000034 to 000038 must already be
          rolled back, since they drop the new exercise table).
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
    exercise_name VARCHAR(100) NOT NULL,
    muscle_group VARCHAR(50),
    -- Constraints
    CONSTRAINT pk_exercise_exercise_id PRIMARY KEY (exercise_id),
    CONSTRAINT unq_exercise_exercise_name UNIQUE (exercise_name)
);

ALTER SEQUENCE seq_exercise_exercise_id OWNED BY exercise.exercise_id;

-- Create an index
CREATE INDEX idx_exercise_muscle_group ON exercise (muscle_group);

-- Restore the dummy rows from 000002
INSERT INTO exercise (
    exercise_name,
    muscle_group
)
VALUES
    ('Barbell Squat', 'Legs'),
    ('Bench Press', 'Chest'),
    ('Deadlift', 'Back'),
    ('Overhead Press', 'Shoulders'),
    ('Pull-Up', 'Back');
