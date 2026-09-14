-- Remplacer la contrainte deferrable par une non-deferrable pour ON CONFLICT
ALTER TABLE public.product_entitlements
  DROP CONSTRAINT IF EXISTS uq_entitlement_stripe_sub;

DROP INDEX IF EXISTS idx_ent_stripe_sub_unique;
CREATE UNIQUE INDEX idx_ent_stripe_sub_unique
  ON public.product_entitlements (stripe_subscription_id)
  WHERE stripe_subscription_id IS NOT NULL;

SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'product_entitlements' AND indexname = 'idx_ent_stripe_sub_unique';
