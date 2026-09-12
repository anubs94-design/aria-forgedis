# FORGEDIS — Vérifications architecture

Ce fichier complète `FORGEDIS_ARCHITECTURE_HARMONISATION.md`.

## Check 1 — Cohérence structurelle
- [ ] GitHub, dossier de travail et preview contiennent les mêmes fichiers fonctionnels.
- [ ] `portail.html` et toutes les pages de connexion/inscription nécessaires sont versionnées dans GitHub.
- [ ] `ARIA` a une signification de navigation identique sur toutes les pages.
- [ ] Supabase ARIA gère l’identité et les droits ARIA ; Supabase NEXORA reste séparé.
- [ ] Une couche d’entitlements canonique remplace les lectures concurrentes `profiles.plan`, `clients.forfait`, `clients.produits[]`, `abonnements.plan` pour décider l’accès.
- [ ] Industrial reste entreprise/tenant-aware.

## Check 2 — Sécurité et paiements
- [ ] `public.clients` n’est plus lisible/modifiable anonymement.
- [ ] `stripe_events` n’est plus lisible publiquement.
- [ ] Aucun token ARIA/service key n’est exposé au navigateur.
- [ ] Le webhook n’attribue jamais Facility par fallback à un produit inconnu.
- [ ] Le mapping Product/Price Stripe est une allowlist serveur.
- [ ] Idempotence webhook persistante en base.
- [ ] Événements de cycle de vie paiement/abonnement couverts.
- [ ] Isolation inter-entreprises Industrial testée.
- [ ] NEXORA interne n’est jamais accessible directement depuis le frontend public.

## Check 3 — E2E utilisateur
Pour Facility, Kids Solo, Kids Famille et Industrial :
- [ ] CTA vitrine correct.
- [ ] création de compte.
- [ ] connexion / déconnexion / récupération.
- [ ] essai.
- [ ] Checkout.
- [ ] webhook.
- [ ] entitlement.
- [ ] portail.
- [ ] accès produit.
- [ ] paiement échoué.
- [ ] annulation / expiration.
- [ ] réactivation.
- [ ] multi-produit.
- [ ] mobile + desktop.
- [ ] zéro erreur console bloquante.
- [ ] zéro lien cassé.

Production interdite tant que les trois checks ne sont pas verts.
