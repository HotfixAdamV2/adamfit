/*
    Migration: 000033_seed_standard_exercise (down)

    What:
        Removes the seeded standard exercises and their muscle tags.

    Why:
        Reverts 000033_seed_standard_exercise.

    Notes:
        - Like 000010's down, this clears the whole table, including any
          standard exercises added by hand later.
*/

DELETE FROM standard_exercise_muscle_group;

DELETE FROM standard_exercise;
