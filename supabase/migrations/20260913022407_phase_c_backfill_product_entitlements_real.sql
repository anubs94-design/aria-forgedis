-- Phase C — Backfill réel product_entitlements depuis clients legacy
-- Règles :
--   facility     -> 1 entitlement facility/facility
--   kids_solo    -> 1 entitlement kids/kids_solo
--   kids_famille -> 1 entitlement kids/kids_famille
--   industrial   -> 1 entitlement industrial/industrial (sujet = entreprise si existe, sinon user)
--   tous         -> 3 entitlements : facility + kids/kids_solo + industrial
--   admin/forgedis -> 0 entitlement (accès admin, pas produit ARIA)
--   gratuit      -> 0 entitlement
--   sans_auth    -> migration différée (pas de user_id réel)

INSERT INTO public.product_entitlements
  (user_id, product, plan, status, source, starts_at, metadata)
SELECT
  u.id AS user_id,
  unnested.product,
  unnested.plan,
  'active'::text AS status,
  'migration'::text AS source,
  now() AS starts_at,
  jsonb_build_object(
    'backfill', true,
    'legacy_forfait', c.forfait,
    'email', c.email,
    'migration_date', now()
  ) AS metadata
FROM public.clients c
JOIN auth.users u ON lower(u.email) = lower(c.email)
CROSS JOIN LATERAL (
  SELECT *
  FROM (VALUES
    ('facility',    'facility',    'facility'),
    ('kids_solo',   'kids',        'kids_solo'),
    ('kids_famille','kids',        'kids_famille'),
    ('industrial',  'industrial',  'industrial'),
    ('tous',        'facility',    'facility'),
    ('tous',        'kids',        'kids_solo'),
    ('tous',        'industrial',  'industrial')
  ) AS t(forfait_key, product, plan)
  WHERE t.forfait_key = c.forfait
) AS unnested
WHERE c.forfait IN ('facility','kids_solo','kids_famille','industrial','tous')
  AND c.actif = true
ON CONFLICT DO NOTHING;

SELECT product, plan, source, COUNT(*) as nb
FROM public.product_entitlements
GROUP BY product, plan, source
ORDER BY product, plan;
