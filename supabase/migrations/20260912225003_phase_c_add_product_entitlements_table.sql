-- phase_c_add_product_entitlements_table
CREATE TABLE IF NOT EXISTS public.product_entitlements (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               uuid REFERENCES public.profiles(id) ON DELETE CASCADE,
  entreprise_id         uuid REFERENCES public.entreprises(id) ON DELETE CASCADE,
  product               text NOT NULL CHECK (product IN ('facility','kids','industrial')),
  plan                  text NOT NULL,
  status                text NOT NULL DEFAULT 'trialing'
                          CHECK (status IN ('trialing','active','past_due','suspended','canceled','expired','pending_auth')),
  source                text NOT NULL CHECK (source IN ('stripe','trial','admin','press','migration')),
  starts_at             timestamptz,
  ends_at               timestamptz,
  stripe_customer_id    text,
  stripe_subscription_id text,
  stripe_price_id       text,
  stripe_product_id     text,
  metadata              jsonb DEFAULT '{}',
  created_at            timestamptz DEFAULT now(),
  updated_at            timestamptz DEFAULT now(),
  CONSTRAINT entitlement_subject_xor CHECK (
    (user_id IS NOT NULL AND entreprise_id IS NULL)
    OR (user_id IS NULL AND entreprise_id IS NOT NULL)
  )
);
CREATE INDEX IF NOT EXISTS idx_entitlements_user_active
  ON public.product_entitlements (user_id, product, status) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_entitlements_entreprise_active
  ON public.product_entitlements (entreprise_id, product, status) WHERE entreprise_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_entitlements_stripe_sub
  ON public.product_entitlements (stripe_subscription_id) WHERE stripe_subscription_id IS NOT NULL;
ALTER TABLE public.product_entitlements ENABLE ROW LEVEL SECURITY;
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$;
DROP TRIGGER IF EXISTS trg_entitlements_updated_at ON public.product_entitlements;
CREATE TRIGGER trg_entitlements_updated_at
  BEFORE UPDATE ON public.product_entitlements
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
