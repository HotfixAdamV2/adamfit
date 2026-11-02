/*
    Migration: 000025_create_exercise_type (down)

    What:
        Drops the exercise_type table.

    Why:
        Reverts 000025_create_exercise_type.
*/

DROP TABLE exercise_type;
