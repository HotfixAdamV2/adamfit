/*
    Migration: 000001_create_exercise (down)

    What:
        Drops the fit.exercise table and its sequence.

    Why:
        Reverts 000001_create_exercise.
*/

DROP TABLE exercise;
