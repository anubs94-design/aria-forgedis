-- phase_h_acquire_stripe_event_atomic
-- Acquisition atomique d'event Stripe : acquired / completed / busy
-- Deux workers ne peuvent pas recevoir acquired=true pour le même event.

CREATE OR REPLACE FUNCTION public.acquire_stripe_event(
  p_event_id   text,
  p_event_type text,
  p_lease_sec  integer DEFAULT 300
)
RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
  v_row   stripe_events%ROWTYPE;
  v_now   timestamptz := now();
  v_stale boolean;
BEGIN
  INSERT INTO public.stripe_events(event_id, event_type, status, attempt_count, processed_at)
  VALUES (p_event_id, p_event_type, 'processing', 1, v_now)
  ON CONFLICT (event_id) DO NOTHING;

  SELECT * INTO v_row FROM public.stripe_events WHERE event_id = p_event_id FOR UPDATE;

  IF v_row.status = 'processing' AND v_row.attempt_count = 1
     AND v_row.processed_at >= v_now - interval '1 second' THEN
    RETURN jsonb_build_object('result','acquired','attempt',1);
  END IF;

  IF v_row.status = 'completed' THEN
    RETURN jsonb_build_object('result','completed','event_id',p_event_id);
  END IF;

  v_stale := (COALESCE(v_row.updated_at, v_row.processed_at) < v_now - (p_lease_sec * interval '1 second'));

  IF v_row.status = 'processing' AND NOT v_stale THEN
    RETURN jsonb_build_object('result','busy','event_id',p_event_id);
  END IF;

  UPDATE public.stripe_events
  SET status='processing', attempt_count=v_row.attempt_count+1, last_error=NULL, updated_at=v_now
  WHERE event_id = p_event_id;

  RETURN jsonb_build_object('result','acquired','attempt',v_row.attempt_count+1);
END;
$$;

CREATE OR REPLACE FUNCTION public.mark_stripe_event_complete(p_event_id text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN UPDATE public.stripe_events SET status='completed', updated_at=now() WHERE event_id=p_event_id; END;$$;

CREATE OR REPLACE FUNCTION public.mark_stripe_event_failed(p_event_id text, p_error text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN UPDATE public.stripe_events SET status='failed', last_error=left(p_error,500), updated_at=now() WHERE event_id=p_event_id; END;$$;

REVOKE ALL ON FUNCTION public.acquire_stripe_event(text,text,integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.mark_stripe_event_complete(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.mark_stripe_event_failed(text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.acquire_stripe_event(text,text,integer) TO service_role;
GRANT EXECUTE ON FUNCTION public.mark_stripe_event_complete(text) TO service_role;
GRANT EXECUTE ON FUNCTION public.mark_stripe_event_failed(text,text) TO service_role;

-- phase_g_fix_portal_context_v2 (via nouvelle migration car ancienne déjà appliquée)
-- Correction : sal.user_id (pas sal.email), industrial exclu des entitlements directs user_id
-- [voir contenu complet dans phase_g_fix_portal_context_v2 appliquée par MCP]

-- phase_h_fix_industrial_admin_tous
-- Décision explicite : entitlement Industrial legacy 'tous' = accès interne admin FORGEDIS
-- Non commercial, source changée en 'admin'
UPDATE public.product_entitlements
SET source='admin',
    metadata=metadata || '{"admin_decision":"internal_forgedis_access","decided_at":"2026-09-13"}'::jsonb
WHERE id='b98f8790-a583-4c02-8262-5c249d22d29f' AND source='migration';
