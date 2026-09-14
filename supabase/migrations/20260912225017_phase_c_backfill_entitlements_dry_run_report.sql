-- Phase C — Backfill dry-run : calculer les entitlements depuis clients + abonnements
-- Ne modifie rien — rapport de correspondance uniquement.

-- Comptes clients avec forfait non-gratuit (source legacy)
-- On ne log que les compteurs, jamais de données personnelles.
DO $$
DECLARE
  total_clients       integer;
  facility_count      integer;
  kids_solo_count     integer;
  kids_famille_count  integer;
  industrial_count    integer;
  gratuit_count       integer;
  admin_count         integer;
  autres_count        integer;
  abonnements_count   integer;
BEGIN
  SELECT COUNT(*) INTO total_clients FROM public.clients;
  SELECT COUNT(*) INTO facility_count     FROM public.clients WHERE forfait = 'facility';
  SELECT COUNT(*) INTO kids_solo_count    FROM public.clients WHERE forfait = 'kids_solo';
  SELECT COUNT(*) INTO kids_famille_count FROM public.clients WHERE forfait = 'kids_famille';
  SELECT COUNT(*) INTO industrial_count   FROM public.clients WHERE forfait = 'industrial';
  SELECT COUNT(*) INTO gratuit_count      FROM public.clients WHERE forfait = 'gratuit';
  SELECT COUNT(*) INTO admin_count        FROM public.clients WHERE forfait IN ('admin','forgedis','tous');
  SELECT COUNT(*) INTO autres_count       FROM public.clients WHERE forfait NOT IN ('facility','kids_solo','kids_famille','industrial','gratuit','admin','forgedis','tous');
  SELECT COUNT(*) INTO abonnements_count  FROM public.abonnements;

  RAISE NOTICE 'BACKFILL DRY-RUN — clients: % total | facility:% kids_solo:% kids_famille:% industrial:% gratuit:% admin:% autres:% | abonnements:%',
    total_clients, facility_count, kids_solo_count, kids_famille_count,
    industrial_count, gratuit_count, admin_count, autres_count, abonnements_count;
END;
$$;

-- Vérifier que product_entitlements est vide (migration additive, rien écrasé)
SELECT COUNT(*) AS entitlements_count FROM public.product_entitlements;
