-- P0/P1 hardening: one Industrial ownership claim per Stripe subscription.
CREATE UNIQUE INDEX IF NOT EXISTS uq_pending_industrial_ownership_stripe_subscription
ON public.pending_industrial_ownership (stripe_subscription_id)
WHERE stripe_subscription_id IS NOT NULL;
