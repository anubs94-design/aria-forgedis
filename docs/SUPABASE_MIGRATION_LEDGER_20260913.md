# Supabase migration ledger — 13 September 2026

This file is documentary only and must never be executed as a migration.

The canonical migration history for the FORGEDIS harmonisation is represented by the timestamped SQL files under `supabase/migrations/`, matching the live `supabase_migrations.schema_migrations` ledger.

Rules:
- Never rewrite a migration already applied in Supabase.
- Corrections use a new migration with a new timestamp.
- Do not run `supabase db push` when the repository migration sequence and the live ledger differ.
- The live ledger is the source used to restore historical migration SQL when reconciling source control.
