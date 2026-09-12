# FORGEDIS — Statut audit architecture

Audit en trois passes réalisé avant exécution fonctionnelle.

1. **Cohérence structurelle** : séparation ARIA/NEXORA validée ; besoin d’une source canonique d’entitlements confirmé ; GitHub doit redevenir la source de déploiement unique.
2. **Sécurité + paiements** : exposition RLS de `clients` et `stripe_events` identifiée ; mapping Stripe explicite et suppression du fallback Facility requis ; catalogue Stripe live vérifié.
3. **Migration + parcours E2E** : migration additive et réversible imposée ; portail unique multi-produit ; Industrial tenant-aware ; triple test E2E obligatoire avant production.

**Décision :** architecture prête pour exécution contrôlée par Claude après synchronisation des fichiers fonctionnels manquants dans GitHub. Production interdite jusqu’aux checks verts.
