-- p0_rls_stripe_events_close_public_select
DROP POLICY IF EXISTS select_stripe_ev ON public.stripe_events;
DROP POLICY IF EXISTS insert_stripe_ev ON public.stripe_events;
