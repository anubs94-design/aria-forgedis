-- Table dédiée aux droits en attente de compte Auth
-- Pas de user_id : la contrainte XOR de product_entitlements reste intacte
CREATE TABLE IF NOT EXISTS public.pending_entitlement_claims (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email                 text NOT NULL,
  product               text NOT NULL CHECK (product IN ('facility','kids','industrial')),
  plan                  text NOT NULL,
  stripe_customer_id    text,
  stripe_subscription_id text,
  stripe_price_ids      text[],
  status                text NOT NULL DEFAULT 'pending'
                          CHECK (status IN ('pending','claimed','expired')),
  created_at            timestamptz DEFAULT now(),
  updated_at            timestamptz DEFAULT now(),
  metadata              jsonb DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_pending_claims_email ON public.pending_entitlement_claims (lower(email));
CREATE INDEX IF NOT EXISTS idx_pending_claims_sub   ON public.pending_entitlement_claims (stripe_subscription_id);
ALTER TABLE public.pending_entitlement_claims ENABLE ROW LEVEL SECURITY;
DROP TRIGGER IF EXISTS trg_pending_claims_updated_at ON public.pending_entitlement_claims;
CREATE TRIGGER trg_pending_claims_updated_at
  BEFORE UPDATE ON public.pending_entitlement_claims
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.product_entitlements
  DROP CONSTRAINT IF EXISTS uq_entitlement_stripe_sub;
ALTER TABLE public.product_entitlements
  ADD CONSTRAINT uq_entitlement_stripe_sub
  UNIQUE (stripe_subscription_id)
  DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.entreprises
  DROP CONSTRAINT IF EXISTS entreprises_statut_paiement_check;
ALTER TABLE public.entreprises
  ADD CONSTRAINT entreprises_statut_paiement_check
  CHECK (statut_paiement IN ('essai','trialing','actif','impaye','suspendu','resilie'));

SELECT conname, pg_get_constraintdef(oid) AS def
FROM pg_constraint
WHERE conrelid IN (
  'public.pending_entitlement_claims'::regclass,
  'public.product_entitlements'::regclass,
  'public.entreprises'::regclass
)
AND conname IN (
  'uq_entitlement_stripe_sub',
  'entreprises_statut_paiement_check'
)
ORDER BY conname;
