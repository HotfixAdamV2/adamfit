/*
    Migration: 000002_seed_exercise (down)

    What:
        Removes the dummy exercises inserted by the up migration.

    Why:
        Reverts 000002_seed_exercise.
*/

DELETE FROM exercise
WHERE exercise_name IN (
    'Barbell Squat',
    'Bench Press',
    'Deadlift',
    'Overhead Press',
    'Pull-Up'
);
