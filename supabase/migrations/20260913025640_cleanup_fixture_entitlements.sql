-- Supprimer uniquement les 3 entitlements fixture (stripe_subscription_id LIKE 'sub_FIXTURE%')
-- Les 4 entitlements migration (source='migration', stripe_subscription_id=null) sont préservés

DELETE FROM public.product_entitlements
WHERE stripe_subscription_id LIKE 'sub_FIXTURE%'
  AND source = 'stripe';

DELETE FROM public.stripe_events
WHERE event_id LIKE 'evt_FIXTURE%';

SELECT source, COUNT(*) as nb FROM public.product_entitlements GROUP BY source;
SELECT COUNT(*) as stripe_events_fixtures_restants FROM public.stripe_events WHERE event_id LIKE 'evt_FIXTURE%';
