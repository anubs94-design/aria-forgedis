-- Ajouter pending_auth au CHECK status de product_entitlements
-- Nécessaire pour les checkout sans compte Auth correspondant

ALTER TABLE public.product_entitlements
  DROP CONSTRAINT IF EXISTS product_entitlements_status_check;

ALTER TABLE public.product_entitlements
  ADD CONSTRAINT product_entitlements_status_check
  CHECK (status IN ('trialing','active','past_due','suspended','canceled','expired','pending_auth'));

SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'public.product_entitlements'::regclass
  AND conname LIKE '%status%';
