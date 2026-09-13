
-- 20260913160000_phase_i_donnees_salaries_table.sql
-- Table canonique pour données métier salarié Industrial
-- Remplace la RPC inexistante sauvegarder_donnees_salarie
-- Utilisée par /sauvegarder (POST)

CREATE TABLE IF NOT EXISTS public.donnees_salaries (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    salarie_id    uuid NOT NULL REFERENCES public.salaries(id) ON DELETE CASCADE,
    donnees       jsonb NOT NULL DEFAULT '{}',
    updated_at    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT donnees_salaries_salarie_id_unique UNIQUE (salarie_id)
);

CREATE INDEX IF NOT EXISTS donnees_salaries_salarie_id_idx ON public.donnees_salaries(salarie_id);

ALTER TABLE public.donnees_salaries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_full" ON public.donnees_salaries
    FOR ALL TO service_role USING (true) WITH CHECK (true);

REVOKE ALL ON public.donnees_salaries FROM anon, authenticated;
GRANT ALL ON public.donnees_salaries TO service_role;
