-- Étendre stripe_events avec états transactionnels pour idempotence correcte
ALTER TABLE public.stripe_events
  ADD COLUMN IF NOT EXISTS status text DEFAULT 'completed'
    CHECK (status IN ('processing', 'completed', 'failed')),
  ADD COLUMN IF NOT EXISTS last_error text,
  ADD COLUMN IF NOT EXISTS attempt_count integer DEFAULT 1,
  ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

UPDATE public.stripe_events SET status = 'completed' WHERE status IS NULL;

DROP TRIGGER IF EXISTS trg_stripe_events_updated_at ON public.stripe_events;
CREATE TRIGGER trg_stripe_events_updated_at
  BEFORE UPDATE ON public.stripe_events
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'stripe_events'
ORDER BY ordinal_position;
