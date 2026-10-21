/*
    Migration: 000023_alter_user_weight_add_source (down)

    What:
        Drops chk_user_weight_source and the source column from
        user_weight.

    Why:
        Reverts 000023_alter_user_weight_add_source.

    Notes:
        - Synced weigh-ins are kept; only the record of their source is
          lost.
*/

ALTER TABLE user_weight
    DROP CONSTRAINT chk_user_weight_source,
    DROP COLUMN source;
