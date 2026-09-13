-- 20260913154458_phase_h_fix_industrial_admin_tous.sql
-- Décision explicite entitlement Industrial legacy 'tous' :
-- Compte laurentjack = accès admin interne FORGEDIS, non commercial.
-- Source changée en 'admin'. Ne figure plus dans les droits commerciaux.

UPDATE public.product_entitlements
SET source='admin',
    metadata=metadata || '{"admin_decision":"internal_forgedis_access","decided_at":"2026-09-13","note":"forfait_tous_admin_non_commercial"}'::jsonb
WHERE id='b98f8790-a583-4c02-8262-5c249d22d29f' AND product='industrial';
