/*
    Migration: 000002_seed_exercise (up)

    What:
        Inserts a handful of dummy exercises.

    Why:
        Gives the Streamlit app something to display while testing the
        database connection. Dummy data only.
*/

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
