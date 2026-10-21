/*
    Migration: 000001_create_exercise (up)

    What:
        Creates the fit.exercise table.

    Why:
        Placeholder table used to prove the migration pipeline and the
        Streamlit-to-Postgres connection work end to end. It will grow
        into the real exercise catalogue later.
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
