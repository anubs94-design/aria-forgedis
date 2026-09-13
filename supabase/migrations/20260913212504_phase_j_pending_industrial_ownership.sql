
-- 20260913212504_phase_j_pending_industrial_ownership.sql
-- Table pour lier un paiement Industrial (avant Auth) à son futur dirigeant.
-- Scénario : checkout Stripe avant création de compte Auth Supabase.
-- Réclamable au premier login JWT via /client-token ou endpoint dédié.

CREATE TABLE IF NOT EXISTS public.pending_industrial_ownership (
    id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email                  text NOT NULL,
    entreprise_id          uuid NOT NULL REFERENCES public.entreprises(id) ON DELETE CASCADE,
    stripe_subscription_id text,
    stripe_customer_id     text,
    status                 text NOT NULL DEFAULT 'pending'
                           CHECK (status IN ('pending', 'claimed', 'expired')),
    created_at             timestamptz NOT NULL DEFAULT now(),
    claimed_at             timestamptz,
    metadata               jsonb DEFAULT '{}',
    CONSTRAINT pio_email_entreprise_unique UNIQUE (email, entreprise_id)
);

CREATE INDEX IF NOT EXISTS pio_email_idx ON public.pending_industrial_ownership(email);
CREATE INDEX IF NOT EXISTS pio_status_idx ON public.pending_industrial_ownership(status);

ALTER TABLE public.pending_industrial_ownership ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_full_pio" ON public.pending_industrial_ownership
    FOR ALL TO service_role USING (true) WITH CHECK (true);

REVOKE ALL ON public.pending_industrial_ownership FROM anon, authenticated;
GRANT ALL ON public.pending_industrial_ownership TO service_role;
