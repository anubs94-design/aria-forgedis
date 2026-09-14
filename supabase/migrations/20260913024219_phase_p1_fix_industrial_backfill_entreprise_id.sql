-- P1 : corriger le backfill Industrial — sujet doit être entreprise_id, pas user_id
-- Trouver l'entitlement Industrial backfillé avec user_id et le corriger si une entreprise correspond

DO $$
DECLARE
  v_ent RECORD;
  v_email text;
  v_entreprise_id uuid;
BEGIN
  FOR v_ent IN
    SELECT e.id, e.user_id, e.metadata
    FROM public.product_entitlements e
    WHERE e.product = 'industrial'
      AND e.user_id IS NOT NULL
      AND e.source = 'migration'
  LOOP
    v_email := (v_ent.metadata ->> 'email');
    IF v_email IS NULL THEN
      SELECT email INTO v_email FROM public.profiles WHERE id = v_ent.user_id;
    END IF;

    IF v_email IS NOT NULL THEN
      SELECT id INTO v_entreprise_id
      FROM public.entreprises
      WHERE lower(email_contact) = lower(v_email)
      LIMIT 1;

      IF v_entreprise_id IS NOT NULL THEN
        UPDATE public.product_entitlements
        SET
          user_id       = NULL,
          entreprise_id = v_entreprise_id,
          metadata = metadata || jsonb_build_object('migration_correction', 'industrial_moved_to_entreprise_id', 'original_user_id', v_ent.user_id)
        WHERE id = v_ent.id;
        RAISE NOTICE 'Industrial ent % corrige: user_id -> entreprise_id %', v_ent.id, v_entreprise_id;
      ELSE
        UPDATE public.product_entitlements
        SET metadata = metadata || jsonb_build_object('migration_note', 'no_entreprise_found_deferred', 'email', v_email)
        WHERE id = v_ent.id;
        RAISE NOTICE 'Industrial ent % : pas d entreprise pour %, migration differee', v_ent.id, v_email;
      END IF;
    END IF;
  END LOOP;
END;
$$;

SELECT id, product, plan, status, source,
  CASE WHEN user_id IS NOT NULL THEN 'user_id' ELSE 'entreprise_id' END as sujet_type,
  metadata->>'migration_note' as note
FROM public.product_entitlements
WHERE product = 'industrial'
ORDER BY created_at;
