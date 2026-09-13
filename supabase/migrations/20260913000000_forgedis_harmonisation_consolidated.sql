-- phase_p0_stripe_events_idempotence_v2 : états transactionnels
ALTER TABLE public.stripe_events
  ADD COLUMN IF NOT EXISTS status text DEFAULT 'completed'
    CHECK (status IN ('processing','completed','failed')),
  ADD COLUMN IF NOT EXISTS last_error text,
  ADD COLUMN IF NOT EXISTS attempt_count integer DEFAULT 1,
  ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();
UPDATE public.stripe_events SET status='completed' WHERE status IS NULL;
DROP TRIGGER IF EXISTS trg_stripe_events_updated_at ON public.stripe_events;
CREATE TRIGGER trg_stripe_events_updated_at
  BEFORE UPDATE ON public.stripe_events
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- phase_c_backfill_product_entitlements_real
INSERT INTO public.product_entitlements (user_id, product, plan, status, source, starts_at, metadata)
SELECT u.id, unnested.product, unnested.plan, 'active', 'migration', now(),
  jsonb_build_object('backfill',true,'legacy_forfait',c.forfait,'migration_date',now())
FROM public.clients c
JOIN auth.users u ON lower(u.email) = lower(c.email)
CROSS JOIN LATERAL (
  SELECT * FROM (VALUES
    ('facility','facility','facility'),('kids_solo','kids','kids_solo'),
    ('kids_famille','kids','kids_famille'),('industrial','industrial','industrial'),
    ('tous','facility','facility'),('tous','kids','kids_solo'),('tous','industrial','industrial')
  ) AS t(forfait_key,product,plan)
  WHERE t.forfait_key = c.forfait
) AS unnested
WHERE c.forfait IN ('facility','kids_solo','kids_famille','industrial','tous') AND c.actif = true
ON CONFLICT DO NOTHING;

-- cleanup_fixture_entitlements
DELETE FROM public.product_entitlements WHERE stripe_subscription_id LIKE 'sub_FIXTURE%' AND source='stripe';
DELETE FROM public.stripe_events WHERE event_id LIKE 'evt_FIXTURE%';

-- phase_f_pending_entitlement_claims
CREATE TABLE IF NOT EXISTS public.pending_entitlement_claims (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email                 text NOT NULL,
  product               text NOT NULL CHECK (product IN ('facility','kids','industrial')),
  plan                  text NOT NULL,
  stripe_customer_id    text,
  stripe_subscription_id text,
  stripe_price_ids      text[],
  status                text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','claimed','expired')),
  created_at            timestamptz DEFAULT now(),
  updated_at            timestamptz DEFAULT now(),
  metadata              jsonb DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_pending_claims_email ON public.pending_entitlement_claims (lower(email));
CREATE UNIQUE INDEX IF NOT EXISTS idx_pending_claims_sub_unique
  ON public.pending_entitlement_claims (stripe_subscription_id) WHERE stripe_subscription_id IS NOT NULL;
ALTER TABLE public.pending_entitlement_claims ENABLE ROW LEVEL SECURITY;
DROP TRIGGER IF EXISTS trg_pending_claims_updated_at ON public.pending_entitlement_claims;
CREATE TRIGGER trg_pending_claims_updated_at
  BEFORE UPDATE ON public.pending_entitlement_claims
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- phase_g_unique_subject_product_constraints
DROP INDEX IF EXISTS idx_ent_user_product_unique;
CREATE UNIQUE INDEX idx_ent_user_product_unique
  ON public.product_entitlements (user_id, product) WHERE user_id IS NOT NULL;
DROP INDEX IF EXISTS idx_ent_entreprise_product_unique;
CREATE UNIQUE INDEX idx_ent_entreprise_product_unique
  ON public.product_entitlements (entreprise_id, product) WHERE entreprise_id IS NOT NULL;
DROP INDEX IF EXISTS idx_ent_stripe_sub_unique;
CREATE UNIQUE INDEX idx_ent_stripe_sub_unique
  ON public.product_entitlements (stripe_subscription_id) WHERE stripe_subscription_id IS NOT NULL;

-- Corrections CHECK contraintes
ALTER TABLE public.entreprises
  DROP CONSTRAINT IF EXISTS entreprises_statut_paiement_check;
ALTER TABLE public.entreprises
  ADD CONSTRAINT entreprises_statut_paiement_check
  CHECK (statut_paiement IN ('essai','trialing','actif','impaye','suspendu','resilie'));

-- phase_p0_add_pending_auth_status
ALTER TABLE public.product_entitlements
  DROP CONSTRAINT IF EXISTS product_entitlements_status_check;
ALTER TABLE public.product_entitlements
  ADD CONSTRAINT product_entitlements_status_check
  CHECK (status IN ('trialing','active','past_due','suspended','canceled','expired','pending_auth'));
