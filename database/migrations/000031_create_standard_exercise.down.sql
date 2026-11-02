/*
    Migration: 000031_create_standard_exercise (down)

    What:
        Drops the standard_exercise table, its sequence and index.

    Why:
        Reverts 000031_create_standard_exercise.
*/

DROP TABLE standard_exercise;
