# FORGEDIS — Handoff Claude / harmonisation fonctionnelle

**À exécuter seulement après lecture intégrale de :**
- `FORGEDIS_ARCHITECTURE_HARMONISATION.md`
- `FORGEDIS_ARCHITECTURE_CHECKS.md`

## Mission

Harmoniser comptes, navigation, abonnements, Stripe, Supabase ARIA, applications ARIA et pont Consulting/NEXORA sans casser le design validé.

Le mot d’ordre est **LOGIQUE** : aucun patch local qui augmente l’incohérence globale.

## Règles absolues

1. Ne rien déployer en production avant triple vérification verte.
2. Ne pas fusionner Supabase ARIA et Supabase NEXORA.
3. Ne pas inventer de prix, Product ID ou Price ID.
4. Ne jamais attribuer Facility par fallback pour un produit Stripe inconnu.
5. Ne jamais exposer de service role key au navigateur.
6. Ne pas supprimer de données legacy avant backfill + comparaison + période de compatibilité.
7. Ne pas refaire le design des vitrines ; préserver les HTML visuels validés.
8. GitHub doit être la source canonique : aucun fichier fonctionnel uniquement local ou uniquement dans le package Netlify.
9. Les droits d’accès doivent être vérifiés côté serveur.
10. Industrial doit rester isolé par entreprise/tenant et permissions.

## Étape 0 — STOP si GitHub n’est pas complet

Avant tout code fonctionnel :
- pull `forgedis-public-redesign` ;
- vérifier le SHA HEAD ;
- réintégrer et committer les vrais fichiers récupérés du déploiement actuel (`portail.html`, connexions, inscriptions, dashboards, apps et dépendances) qui ne sont pas encore dans GitHub ;
- comparer les hashes du dossier local au commit GitHub ;
- créer un Deploy Preview depuis CE commit seulement.

Aucun développement d’auth/portail tant que cette étape n’est pas verte.

## Étape 1 — matrice avant modification

Produire dans le repo `FORGEDIS_WIRING_MATRIX.md` avec :
- toutes les pages/CTA ;
- destination réelle ;
- app ciblée ;
- table/API appelée ;
- auth requise ;
- produit/plan attendu ;
- Price ID Stripe attendu ;
- entitlement attendu ;
- redirect succès/échec.

Produire `FORGEDIS_DATA_MIGRATION_MAP.md` :
- Auth -> profiles -> clients -> abonnements -> entreprises -> salariés ;
- lignes correspondantes/non correspondantes ;
- aucune donnée personnelle en clair dans le rapport ; utiliser UUID masqués/compteurs.

## Étape 2 — sécurité P0 d’abord

Auditer tout accès frontend direct à `public.clients` et `stripe_events`.

Avant de fermer les policies permissives, remplacer toute dépendance légitime par backend/RPC sécurisé.

Puis, via migration versionnée :
- retirer lecture/écriture anonyme de `clients` ;
- retirer lecture publique de `stripe_events` ;
- conserver le backend service-role ;
- ne créer que des policies `authenticated` minimales si elles sont réellement nécessaires.

Tests obligatoires : anon, utilisateur A, utilisateur B, admin, presse, Facility, Kids, Industrial.

## Étape 3 — entitlement canonique, migration additive

Ajouter une couche d’entitlements suivant la spécification architecture. Ne supprimer aucune colonne legacy.

Backfill en mode dry-run d’abord :
- calcul ancien droit ;
- calcul nouveau droit ;
- rapport de divergence ;
- zéro bascule tant qu’une divergence inexpliquée existe.

Ensuite seulement, faire lire le portail/backend depuis la nouvelle source canonique.

## Étape 4 — Stripe

Inventaire live vérifié au moment de l’audit :

Facility :
- Product `prod_UhHh3dtBPIED6i`
- Price payant 12,99 € : `price_1Tht8LI54RQfwJiYNUvxbLzd`
- Price 0 € historique actif : `price_1Tomp0I54RQfwJiYr3qI18Ua`

Kids Solo :
- Product `prod_UrdvcsgXqxJbK2`
- Price `price_1TrudbI54RQfwJiY4k26O7dG` = 9,99 €/mois, trial 14 j

Kids Famille :
- Product `prod_UrdxZxTDPHxJrJ`
- Price `price_1TrufbI54RQfwJiYeD5fbW7b` = 14,99 €/mois, trial 14 j

Industrial composants :
- base 49 € : `price_1Txb8dI54RQfwJiYhVgtBFWP`
- salarié T1 15 € : `price_1Txb8kI54RQfwJiYZrHbuF4p`
- salarié T2 12 € : `price_1Txb8tI54RQfwJiYoPExEr7M`
- salarié T3 10 € : `price_1Txb91I54RQfwJiYkdgk1zZg`
- salarié T4 8 € : `price_1Txb9AI54RQfwJiYZwFEzbnU`
- site additionnel 25 € : `price_1Txb9II54RQfwJiY87wN2go3`
- cloud 7 € : `price_1Txb9QI54RQfwJiYjTzdob0k`
- poste sur mesure 15 € : `price_1Txb9YI54RQfwJiYyv4JmYJL`

Ne pas modifier Stripe depuis cette liste sans relire l’API live ; ces IDs servent de référence d’audit.

Créer un mapping serveur explicite Price ID -> product/plan. Pas de fallback.

Mettre l’idempotence sur `stripe_events` au centre du traitement.

Étendre les événements nécessaires pour état complet : subscription updated, payment failed/past_due, paid, deleted/end, selon architecture retenue.

Décider et documenter un modèle d’essai unique par produit avant code.

## Étape 5 — portail unique

`Se connecter` sur toutes les vitrines -> `portail.html`.

Le portail :
1. authentifie via Supabase Auth ;
2. appelle un endpoint serveur de contexte ;
3. reçoit les entitlements autorisés ;
4. affiche les cartes produit correspondantes ;
5. ne redirige jamais arbitrairement vers Facility ;
6. supporte zéro, un ou plusieurs produits.

Les pages connexion spécifiques peuvent rester temporairement comme compatibilité, puis devenir des wrappers/redirects cohérents.

## Étape 6 — navigation ARIA

Sur toutes les vitrines :
- `ARIA` = même dropdown accessible Facility / Kids / Industrial ;
- desktop + mobile ;
- aucun lien ARIA dépendant de la page courante.

## Étape 7 — parcours produit

Facility : vitrine -> essai/abonnement -> compte -> entitlement -> app `/senior`.

Kids : vitrine -> choix Solo/Famille -> compte -> Checkout/trial -> entitlement -> app `/kids`.

Industrial : vitrine -> configuration effectif/options -> validation serveur des quantités/prix -> compte entreprise -> Checkout -> entitlement entreprise -> `/industrial`.

Le moteur de devis métier Industrial reste séparé du calcul d’abonnement Stripe.

## Étape 8 — NEXORA public

Ne pas connecter `nexora-quote.js` directement à Supabase NEXORA.

Créer seulement un endpoint public contrôlé si nécessaire : validation, rate limit, création brouillon/lead, puis pont serveur vers NEXORA.

Aucune demande publique ne devient automatiquement une mission validée ou un devis ferme.

## Étape 9 — triple vérification

Exécuter les trois checklists de `FORGEDIS_ARCHITECTURE_CHECKS.md`.

En plus :
- tests anti-cross-account ;
- tests anti-cross-tenant Industrial ;
- produit Stripe inconnu ;
- event Stripe dupliqué ;
- webhook rejoué après redémarrage ;
- paiement échoué ;
- annulation fin de période ;
- accès multi-produit ;
- compte Auth sans client legacy ;
- client legacy sans Auth ;
- presse/admin.

## Livrable final Claude

Répondre uniquement après tests avec :

`HARMONISATION PREVIEW PRÊTE`

Puis :
- SHA GitHub exact ;
- URL preview ;
- migrations ajoutées ;
- fichiers récupérés/committés ;
- matrice CTA/routes ;
- résultats Check 1 / Check 2 / Check 3 ;
- résultat RLS ;
- résultat Stripe ;
- résultat Facility/Kids/Industrial ;
- résultat portail multi-produit ;
- résultat NEXORA isolation ;
- erreurs console restantes ;
- risques non résolus.

**Ne pas faire `--prod`.**
