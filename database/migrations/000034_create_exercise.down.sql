/*
    Migration: 000034_create_exercise (down)

    What:
        Drops the exercise table, its sequence, indexes and trigger.

    Why:
        Reverts 000034_create_exercise.

    Notes:
        - Data loss: every user's exercises are deleted, including ones
          they created themselves. 000035 to 000038 must be rolled back
          first (golang-migrate does this in order).
*/

DROP TABLE exercise;
