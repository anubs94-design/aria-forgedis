# FORGEDIS — Wiring Matrix (état avant harmonisation)

SHA de référence : 88cb8115e0b325ef437a60b0b12fb0d5174528a5
Généré : 2026-09-13

## Pages vitrines — Navigation header

| Page | Lien nav | Destination | Problème |
|------|----------|-------------|---------|
| Toutes | ARIA | page courante (facility/kids/industrial selon page) | ❌ incohérent |
| Toutes | Consulting | consulting.html | ✅ |
| Toutes | Se connecter | portail.html | ⚠️ portail = Facility uniquement |
| index.html | ARIA | facility.html | ❌ |
| kids.html | ARIA | kids.html | ❌ |
| industrial.html | ARIA | industrial.html | ❌ |

## Pages vitrines — CTA principaux

| Page | CTA | Destination | Auth requise | Entitlement attendu | Price ID |
|------|-----|-------------|--------------|---------------------|----------|
| index.html | Parler de votre projet | consulting.html#contact | non | - | - |
| index.html | Découvrir ARIA | - | non | - | - |
| facility.html | Essayer ARIA | /senior | oui (token) | facility | price_1Tht8LI54RQfwJiYNUvxbLzd |
| facility.html | Essayer gratuitement 14j | /senior | oui (token) | facility/gratuit | - |
| kids.html | Essayer ARIA | /kids | oui (token) | kids_solo ou kids_famille | price_1TrudbI54RQfwJiY4k26O7dG / price_1TrufbI54RQfwJiYeD5fbW7b |
| kids.html | Essayer gratuitement 14j | /kids | oui (token) | kids | - |
| industrial.html | Accéder à ARIA | /industrial | oui (token) | industrial | price_1Txb8dI54RQfwJiYhVgtBFWP + composants |
| industrial.html | Créer mon devis dans ARIA | /industrial | oui (token) | industrial | - |
| consulting.html | Démarrer par un diagnostic | #contact / NEXORA | non | - | 290€ (hors Stripe) |

## Pages auth — flux et redirections

| Page | Supabase | Relay | Redirect succès | Redirect échec | Problème |
|------|----------|-------|-----------------|----------------|---------|
| portail.html (=connexion.html) | dvlrilkl | /client-token | /dashboard-facility.html ou /admin.html | même page | ❌ redirige tout vers Facility |
| connexion-kids.html | dvlrilkl | /client-token-kids | /admin.html ou /app-kids.html | même page | ✅ |
| connexion-industrial.html | dvlrilkl | aucun | / | / | ❌ redirige vers accueil |
| inscription-facility.html | dvlrilkl | aucun | page succès inline | même page | ⚠️ pas de Checkout Stripe |
| inscription-kids.html | dvlrilkl | aucun | / | même page | ❌ redirige vers accueil |
| inscription-industrial.html | dvlrilkl | aucun | / | même page | ❌ redirige vers accueil |

## Applications ARIA réelles — vérification accès

| Route | App | Supabase | Relay | Stripe | Vérif serveur |
|-------|-----|----------|-------|--------|---------------|
| /senior | aria-facility.html (44KB) | non direct | non visible | non | ⚠️ pas de vérif visible |
| /kids | app-kids.html (606KB) | dvlrilkl | /client-token-kids | oui | ✅ relay vérifie forfait |
| /industrial | aria_industrial_v1.html (47KB) | non direct | non | oui (Stripe direct) | ⚠️ pas de relay |
| /hub | index.html | - | - | - | - |
| /admin | admin.html (57KB) | dvlrilkl | - | - | ✅ email allowlist |

## Stripe — mapping actuel vs cible

| Produit | Product ID | Price ID payant | Forfait webhook actuel | Forfait cible |
|---------|------------|-----------------|----------------------|---------------|
| Facility | prod_UhHh3dtBPIED6i | price_1Tht8LI54RQfwJiYNUvxbLzd | fallback (tout inconnu) | explicit mapping |
| Facility 0€ | prod_UhHh3dtBPIED6i | price_1Tomp0I54RQfwJiYr3qI18Ua | ❌ ambiguïté | désactiver ou exclure |
| Kids Solo | prod_UrdvcsgXqxJbK2 | price_1TrudbI54RQfwJiY4k26O7dG | kids_solo | kids_solo |
| Kids Famille | prod_UrdxZxTDPHxJrJ | price_1TrufbI54RQfwJiYeD5fbW7b | kids_famille | kids_famille |
| Industrial base | - | price_1Txb8dI54RQfwJiYhVgtBFWP | industrial | industrial |
| Industrial salarié T1 | - | price_1Txb8kI54RQfwJiYZrHbuF4p | industrial | industrial |
| Industrial salarié T2 | - | price_1Txb8tI54RQfwJiYoPExEr7M | industrial | industrial |
| Industrial salarié T3 | - | price_1Txb91I54RQfwJiYkdgk1zZg | industrial | industrial |
| Industrial salarié T4 | - | price_1Txb9AI54RQfwJiYZwFEzbnU | industrial | industrial |
| Industrial site add. | - | price_1Txb9II54RQfwJiY87wN2go3 | industrial | industrial |
| Industrial cloud | - | price_1Txb9QI54RQfwJiYjTzdob0k | industrial | industrial |
| Industrial poste | - | price_1Txb9YI54RQfwJiYyv4JmYJL | industrial | industrial |

## Problèmes identifiés — priorité

| # | Type | Description |
|---|------|-------------|
| P0 | Sécurité | RLS clients permissif (SELECT/INSERT/UPDATE anonyme) |
| P0 | Sécurité | stripe_events lisible publiquement |
| P0 | Logique | webhook fallback : produit inconnu → Facility |
| P1 | Navigation | ARIA header → page courante (pas de dropdown) |
| P1 | Auth | portail.html → Facility uniquement, pas multi-produit |
| P1 | Auth | connexion-industrial → redirect / (accueil) |
| P1 | Auth | inscription-industrial/kids → redirect / (accueil) |
| P1 | Stripe | Prix Facility 0€ actif et ambigu |
| P2 | E2E | Facility : pas de vérif relay côté app |
| P2 | E2E | Industrial : pas de relay, vérif Stripe uniquement côté client |
| P2 | Essais | Modèle essai non unifié (Stripe trial vs Supabase vs prix 0€) |