-- 20260913155919_phase_h_revoke_stripe_rpc_public_access.sql
-- Révoquer l'accès PUBLIC/anon/authenticated aux RPC Stripe SECURITY DEFINER.
-- Résultat vérifié : anon=false, authenticated=false, service_role=true.

REVOKE ALL ON FUNCTION public.acquire_stripe_event(text,text,integer) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.acquire_stripe_event(text,text,integer) FROM anon;
REVOKE EXECUTE ON FUNCTION public.acquire_stripe_event(text,text,integer) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.acquire_stripe_event(text,text,integer) TO service_role;

REVOKE ALL ON FUNCTION public.mark_stripe_event_complete(text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.mark_stripe_event_complete(text) FROM anon;
REVOKE EXECUTE ON FUNCTION public.mark_stripe_event_complete(text) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.mark_stripe_event_complete(text) TO service_role;

REVOKE ALL ON FUNCTION public.mark_stripe_event_failed(text,text) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.mark_stripe_event_failed(text,text) FROM anon;
REVOKE EXECUTE ON FUNCTION public.mark_stripe_event_failed(text,text) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.mark_stripe_event_failed(text,text) TO service_role;
