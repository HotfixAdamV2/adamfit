/*
    Migration: 000005_create_fx_trg_set_updated_at (down)

    What:
        Drops the updated_at triggers and the fx_trg_set_updated_at function.

    Why:
        Reverts 000005_create_fx_trg_set_updated_at.
*/

DROP TRIGGER trg_user_weight_set_updated_at ON user_weight;

DROP TRIGGER trg_app_user_set_updated_at ON app_user;

DROP FUNCTION fx_trg_set_updated_at();
