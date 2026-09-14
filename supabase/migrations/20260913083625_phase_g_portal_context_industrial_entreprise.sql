-- Mettre à jour get_portal_context pour inclure Industrial via entreprise_id
CREATE OR REPLACE FUNCTION public.get_portal_context()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_user_id       uuid := auth.uid();
  v_email         text;
  v_result        jsonb := '{"products": [], "source": "none"}'::jsonb;
  v_entitlements  jsonb;
  v_legacy_forfait text;
BEGIN
  IF v_user_id IS NULL THEN
    RETURN '{"error": "unauthenticated"}'::jsonb;
  END IF;

  SELECT email INTO v_email FROM public.profiles WHERE id = v_user_id;

  SELECT jsonb_agg(jsonb_build_object(
    'product', product, 'plan', plan, 'status', status, 'ends_at', ends_at
  ))
  INTO v_entitlements
  FROM public.product_entitlements
  WHERE user_id = v_user_id
    AND status IN ('trialing', 'active')
    AND (ends_at IS NULL OR ends_at > now());

  DECLARE v_ent_industrial jsonb;
  BEGIN
    SELECT jsonb_agg(jsonb_build_object(
      'product', e2.product, 'plan', e2.plan, 'status', e2.status,
      'ends_at', e2.ends_at, 'source', 'entreprise'
    ))
    INTO v_ent_industrial
    FROM public.entreprises ent
    JOIN public.product_entitlements e2 ON e2.entreprise_id = ent.id
    WHERE (
      lower(ent.email_contact) = lower(v_email)
      OR EXISTS (
        SELECT 1 FROM public.salaries sal
        WHERE sal.entreprise_id = ent.id AND lower(sal.email) = lower(v_email)
      )
    )
      AND e2.status IN ('trialing', 'active')
      AND (e2.ends_at IS NULL OR e2.ends_at > now());

    IF v_ent_industrial IS NOT NULL AND jsonb_array_length(v_ent_industrial) > 0 THEN
      IF v_entitlements IS NULL THEN
        v_entitlements := v_ent_industrial;
      ELSE
        v_entitlements := v_entitlements || v_ent_industrial;
      END IF;
    END IF;
  END;

  IF v_entitlements IS NOT NULL AND jsonb_array_length(v_entitlements) > 0 THEN
    RETURN jsonb_build_object(
      'user_id', v_user_id,
      'products', v_entitlements,
      'source', 'product_entitlements'
    );
  END IF;

  SELECT forfait INTO v_legacy_forfait
  FROM public.clients
  WHERE email = v_email AND actif = true
  LIMIT 1;

  IF v_legacy_forfait IS NOT NULL
     AND v_legacy_forfait NOT IN ('gratuit','admin','forgedis','tous') THEN
    RETURN jsonb_build_object(
      'user_id', v_user_id,
      'products', jsonb_build_array(jsonb_build_object(
        'product',
        CASE v_legacy_forfait
          WHEN 'facility'     THEN 'facility'
          WHEN 'kids_solo'    THEN 'kids'
          WHEN 'kids_famille' THEN 'kids'
          WHEN 'industrial'   THEN 'industrial'
          ELSE NULL
        END,
        'plan', v_legacy_forfait,
        'status', 'active',
        'ends_at', NULL
      )),
      'source', 'legacy_clients',
      'migration_note', 'backfill_pending'
    );
  END IF;

  RETURN jsonb_build_object('user_id', v_user_id, 'products', '[]'::jsonb, 'source', 'none');
END;
$$;

REVOKE ALL ON FUNCTION public.get_portal_context() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.get_portal_context() FROM anon;
GRANT EXECUTE ON FUNCTION public.get_portal_context() TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_portal_context() TO service_role;
