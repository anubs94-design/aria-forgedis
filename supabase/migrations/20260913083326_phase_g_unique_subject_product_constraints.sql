-- P0 : Un seul entitlement par sujet + produit
-- Index UNIQUE partiels (supportent ON CONFLICT dans PostgreSQL)

DROP INDEX IF EXISTS idx_ent_user_product_unique;
CREATE UNIQUE INDEX idx_ent_user_product_unique
  ON public.product_entitlements (user_id, product)
  WHERE user_id IS NOT NULL;

DROP INDEX IF EXISTS idx_ent_entreprise_product_unique;
CREATE UNIQUE INDEX idx_ent_entreprise_product_unique
  ON public.product_entitlements (entreprise_id, product)
  WHERE entreprise_id IS NOT NULL;

DROP INDEX IF EXISTS idx_pending_claims_sub_unique;
CREATE UNIQUE INDEX idx_pending_claims_sub_unique
  ON public.pending_entitlement_claims (stripe_subscription_id)
  WHERE stripe_subscription_id IS NOT NULL;

SELECT indexname, indexdef FROM pg_indexes
WHERE tablename IN ('product_entitlements','pending_entitlement_claims')
  AND indexname LIKE '%unique%'
ORDER BY tablename, indexname;
