/*
    Migration: 000026_seed_exercise_type (down)

    What:
        Removes the seeded exercise types.

    Why:
        Reverts 000026_seed_exercise_type.
*/

DELETE FROM exercise_type;
