-- phase_d_stripe_price_catalog
CREATE TABLE IF NOT EXISTS public.stripe_price_catalog (
  price_id    text PRIMARY KEY,
  product_id  text NOT NULL,
  product     text NOT NULL CHECK (product IN ('facility','kids','industrial')),
  plan        text NOT NULL,
  amount_cts  integer,
  currency    text DEFAULT 'eur',
  active      boolean DEFAULT true,
  notes       text,
  created_at  timestamptz DEFAULT now()
);
ALTER TABLE public.stripe_price_catalog ENABLE ROW LEVEL SECURITY;
CREATE POLICY stripe_catalog_select ON public.stripe_price_catalog FOR SELECT USING (true);
INSERT INTO public.stripe_price_catalog (price_id, product_id, product, plan, amount_cts, notes) VALUES
  ('price_1Tht8LI54RQfwJiYNUvxbLzd','prod_UhHh3dtBPIED6i','facility','facility',1299,'Facility 12,99€/mois'),
  ('price_1Tomp0I54RQfwJiYr3qI18Ua','prod_UhHh3dtBPIED6i','facility','facility_historique',0,'Facility 0€ legacy'),
  ('price_1TrudbI54RQfwJiY4k26O7dG','prod_UrdvcsgXqxJbK2','kids','kids_solo',999,'Kids Solo 9,99€/mois'),
  ('price_1TrufbI54RQfwJiYeD5fbW7b','prod_UrdxZxTDPHxJrJ','kids','kids_famille',1499,'Kids Famille 14,99€/mois'),
  ('price_1Txb8dI54RQfwJiYhVgtBFWP','prod_industrial_base','industrial','industrial_base',4900,'Industrial base 49€/mois'),
  ('price_1Txb8kI54RQfwJiYZrHbuF4p','prod_industrial_base','industrial','industrial_sal_t1',1500,'Industrial salarié T1'),
  ('price_1Txb8tI54RQfwJiYoPExEr7M','prod_industrial_base','industrial','industrial_sal_t2',1200,'Industrial salarié T2'),
  ('price_1Txb91I54RQfwJiYkdgk1zZg','prod_industrial_base','industrial','industrial_sal_t3',1000,'Industrial salarié T3'),
  ('price_1Txb9AI54RQfwJiYZwFEzbnU','prod_industrial_base','industrial','industrial_sal_t4',800,'Industrial salarié T4'),
  ('price_1Txb9II54RQfwJiY87wN2go3','prod_industrial_base','industrial','industrial_site',2500,'Industrial site add.'),
  ('price_1Txb9QI54RQfwJiYjTzdob0k','prod_industrial_base','industrial','industrial_cloud',700,'Industrial cloud'),
  ('price_1Txb9YI54RQfwJiYyv4JmYJL','prod_industrial_base','industrial','industrial_poste',1500,'Industrial poste')
ON CONFLICT (price_id) DO NOTHING;
