-- 20260913155948_phase_h_acquire_stripe_event_v2_returning.sql
-- acquire_stripe_event v2 : INSERT...RETURNING garantit l'exclusivité atomique.
-- Seul le worker ayant réellement inséré la ligne reçoit 'acquired'.
-- Appliquée via MCP Supabase le 2026-09-13.

CREATE OR REPLACE FUNCTION public.acquire_stripe_event(
  p_event_id   text,
  p_event_type text,
  p_lease_sec  integer DEFAULT 300
)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
  v_inserted_id text;
  v_row         stripe_events%ROWTYPE;
  v_now         timestamptz := now();
  v_stale       boolean;
BEGIN
  INSERT INTO public.stripe_events(event_id,event_type,status,attempt_count,processed_at)
  VALUES (p_event_id,p_event_type,'processing',1,v_now)
  ON CONFLICT (event_id) DO NOTHING
  RETURNING event_id INTO v_inserted_id;

  IF v_inserted_id IS NOT NULL THEN
    RETURN jsonb_build_object('result','acquired','attempt',1);
  END IF;

  SELECT * INTO v_row FROM public.stripe_events WHERE event_id=p_event_id FOR UPDATE;

  IF v_row.status='completed' THEN
    RETURN jsonb_build_object('result','completed','event_id',p_event_id);
  END IF;

  v_stale := (COALESCE(v_row.updated_at,v_row.processed_at) < v_now-(p_lease_sec*interval'1 second'));
  IF v_row.status='processing' AND NOT v_stale THEN
    RETURN jsonb_build_object('result','busy','event_id',p_event_id);
  END IF;

  UPDATE public.stripe_events
  SET status='processing',attempt_count=v_row.attempt_count+1,last_error=NULL,updated_at=v_now
  WHERE event_id=p_event_id;

  RETURN jsonb_build_object('result','acquired','attempt',v_row.attempt_count+1);
END;
$$;

REVOKE ALL ON FUNCTION public.acquire_stripe_event(text,text,integer) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.acquire_stripe_event(text,text,integer) FROM anon;
REVOKE EXECUTE ON FUNCTION public.acquire_stripe_event(text,text,integer) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.acquire_stripe_event(text,text,integer) TO service_role;
