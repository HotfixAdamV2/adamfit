/*
    Migration: 000025_create_exercise_type (up)

    What:
        Creates the exercise_type lookup table: the kinds of exercise
        (strength, cardio).

    Why:
        standard_exercise and exercise (000031, 000034) reference this
        table with a foreign key, so adding a type is one INSERT rather
        than a change to CHECK constraints on two tables. The app uses the
        type to decide what to log (sets and reps, or time and distance)
        and whether muscle tags apply.

    Notes:
        - type_code is a natural primary key (no sequence), like
          serving_unit.unit_code. It is the value stored in
          standard_exercise.exercise_type and exercise.exercise_type, so
          exercises stay readable without a join.
        - sort_order is the order the app lists types in.
*/

-- Create the table
CREATE TABLE exercise_type (
    -- Fields
    type_code VARCHAR(20) NOT NULL,
    type_name VARCHAR(30) NOT NULL,
    sort_order SMALLINT NOT NULL DEFAULT 0,
    -- Constraints
    CONSTRAINT pk_exercise_type_type_code PRIMARY KEY (type_code),
    CONSTRAINT unq_exercise_type_type_name UNIQUE (type_name)
);

-- Give grants
-- None needed: the master role owns the table.
