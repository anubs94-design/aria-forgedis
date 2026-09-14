-- 20260913154439_phase_g_fix_portal_context_v2.sql
-- Correction get_portal_context() live :
-- sal.user_id (pas sal.email qui n'existe pas dans salaries)
-- Industrial exclu des entitlements directs par user_id
-- Industrial : dirigeant_id = auth.uid() OR salaries.user_id = auth.uid() AND actif=true
-- Appliquée via MCP Supabase le 2026-09-13.

CREATE OR REPLACE FUNCTION public.get_portal_context()
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
  v_uid            uuid := auth.uid();
  v_email          text;
  v_entitlements   jsonb;
  v_ind            jsonb;
  v_legacy_forfait text;
BEGIN
  IF v_uid IS NULL THEN RETURN '{"error":"unauthenticated"}'::jsonb; END IF;
  SELECT email INTO v_email FROM public.profiles WHERE id = v_uid;

  SELECT jsonb_agg(jsonb_build_object('product',product,'plan',plan,'status',status,'ends_at',ends_at))
  INTO v_entitlements FROM public.product_entitlements
  WHERE user_id = v_uid AND product != 'industrial'
    AND status IN ('trialing','active') AND (ends_at IS NULL OR ends_at > now());

  SELECT jsonb_agg(jsonb_build_object('product',pe.product,'plan',pe.plan,'status',pe.status,'ends_at',pe.ends_at,'source','entreprise'))
  INTO v_ind FROM public.entreprises ent
  JOIN public.product_entitlements pe ON pe.entreprise_id = ent.id
  WHERE (ent.dirigeant_id = v_uid OR EXISTS (
    SELECT 1 FROM public.salaries sal
    WHERE sal.entreprise_id = ent.id AND sal.user_id = v_uid AND sal.actif = true))
    AND pe.status IN ('trialing','active') AND (pe.ends_at IS NULL OR pe.ends_at > now());

  IF v_ind IS NOT NULL AND jsonb_array_length(v_ind) > 0 THEN
    v_entitlements := COALESCE(v_entitlements,'[]'::jsonb) || v_ind;
  END IF;

  IF v_entitlements IS NOT NULL AND jsonb_array_length(v_entitlements) > 0 THEN
    RETURN jsonb_build_object('user_id',v_uid,'products',v_entitlements,'source','product_entitlements');
  END IF;

  SELECT forfait INTO v_legacy_forfait FROM public.clients WHERE email=v_email AND actif=true LIMIT 1;
  IF v_legacy_forfait IS NOT NULL AND v_legacy_forfait NOT IN ('gratuit','admin','forgedis','tous') THEN
    RETURN jsonb_build_object('user_id',v_uid,'products',jsonb_build_array(jsonb_build_object(
      'product', CASE v_legacy_forfait WHEN 'facility' THEN 'facility' WHEN 'kids_solo' THEN 'kids'
        WHEN 'kids_famille' THEN 'kids' WHEN 'industrial' THEN 'industrial' ELSE NULL END,
      'plan',v_legacy_forfait,'status','active','ends_at',NULL)),
      'source','legacy_clients','migration_note','backfill_pending');
  END IF;

  RETURN jsonb_build_object('user_id',v_uid,'products','[]'::jsonb,'source','none');
END;$$;

REVOKE ALL ON FUNCTION public.get_portal_context() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.get_portal_context() FROM anon;
GRANT EXECUTE ON FUNCTION public.get_portal_context() TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_portal_context() TO service_role;
