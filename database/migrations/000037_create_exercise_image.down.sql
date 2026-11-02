/*
    Migration: 000037_create_exercise_image (down)

    What:
        Drops the exercise_image table and its trigger.

    Why:
        Reverts 000037_create_exercise_image.

    Notes:
        - Data loss: every uploaded exercise picture is deleted.
*/

DROP TABLE exercise_image;
