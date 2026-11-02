/*
    Migration: 000024_drop_exercise (up)

    What:
        Drops the placeholder exercise table from 000001 (seeded with
        dummy rows in 000002), together with its sequence
        seq_exercise_exercise_id and index idx_exercise_muscle_group.

    Why:
        The placeholder only proved the migration pipeline worked. It is
        replaced by the real exercise library (000025 to 000038), where
        each user owns their own exercises and muscle groups are a proper
        table. The new exercise table (000034) reuses the name, so the old
        one has to go first.

    Notes:
        - The table only ever held the five dummy rows from 000002, so no
          real data is lost.
        - The sequence is OWNED BY exercise.exercise_id and the index
          belongs to the table, so DROP TABLE removes both.
*/

DROP TABLE exercise;
