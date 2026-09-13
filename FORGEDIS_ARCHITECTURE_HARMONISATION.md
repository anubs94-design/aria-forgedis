# FORGEDIS — Architecture d’harmonisation comptes, produits, abonnements et NEXORA

**Statut : spécification d’architecture auditée — aucune migration production appliquée par ce document.**

## 1. Principe directeur

Le mot d’ordre est **LOGIQUE** : aucune correction locale ne doit augmenter l’incohérence globale. Le système doit être pensé comme un arbre : un tronc d’identité et de droits, puis des branches produits indépendantes mais cohérentes.

Objectif utilisateur :

```text
Visiteur
  -> choisit un produit et un forfait
  -> crée ou retrouve UN compte FORGEDIS
  -> paiement/essai vérifié côté serveur
  -> droit produit (entitlement)
  -> portail FORGEDIS
  -> accès uniquement aux produits autorisés
```

NEXORA reste séparé des comptes ARIA. Il peut recevoir des demandes Consulting via une API contrôlée, jamais par accès direct du navigateur à la base interne NEXORA.

---

## 2. Deux Supabase, deux responsabilités

### Supabase ARIA — `aria-forgelis`

Responsabilité cible :
- Supabase Auth = identité du compte FORGEDIS.
- `profiles` = profil public/compte, pas source de vérité de paiement.
- droits produits = couche d’entitlements dédiée.
- Stripe = source de vérité commerciale sur les abonnements payants.
- Relay/backend = autorité serveur qui vérifie JWT + droits avant accès.
- données Facility/Kids/Industrial restent dans ce projet selon leur périmètre métier.

### Supabase NEXORA — `nexora`

Responsabilité cible :
- Consulting interne ;
- clients Consulting ;
- missions ;
- agents/orchestrateur ;
- documents ;
- audit ;
- exécutions ;
- knowledge/quality/permissions.

**Interdit :** fusionner les deux projets, partager une service role key entre eux, ou faire du navigateur public un client privilégié de NEXORA.

---

## 3. Problème actuel : plusieurs sources de vérité

ARIA possède aujourd’hui plusieurs représentations concurrentes d’un même droit :

- `auth.users` : identité ;
- `profiles.produit` et `profiles.plan` ;
- `clients.forfait`, `clients.actif`, `clients.produits[]` ;
- `abonnements.plan`, `abonnements.status` ;
- `entreprises.plan`, `entreprises.statut_paiement` pour Industrial.

Cette duplication crée des contradictions possibles. La réponse à « à quoi cet utilisateur a-t-il accès ? » doit devenir déterministe.

### Règle cible

1. `auth.users` = **identité canonique**.
2. `profiles` = **profil utilisateur**, 1:1 avec Auth.
3. `product_entitlements` = **source canonique des droits d’accès ARIA**.
4. Stripe = **source commerciale canonique** pour les abonnements payants ; le webhook projette l’état Stripe dans `product_entitlements`.
5. `clients` devient une table **legacy/opérationnelle** pour les tokens et données historiques, jamais une autorité publique de droits.
6. `entreprises` reste la ressource métier Industrial ; l’accès d’une personne à une entreprise passe par une relation utilisateur/entreprise, puis par l’entitlement Industrial de l’entreprise.

---

## 4. Modèle cible d’entitlement

Migration additive recommandée, sans supprimer les structures actuelles avant validation :

```text
product_entitlements
- id uuid PK
- user_id uuid NULL -> profiles(id)
- entreprise_id uuid NULL -> entreprises(id)
- product text NOT NULL            # facility | kids | industrial
- plan text NOT NULL               # facility | kids_solo | kids_famille | industrial_* ...
- status text NOT NULL             # trialing | active | past_due | suspended | canceled | expired
- source text NOT NULL             # stripe | trial | admin | press | migration
- starts_at timestamptz
- ends_at timestamptz
- stripe_customer_id text NULL
- stripe_subscription_id text NULL
- stripe_price_id text NULL
- stripe_product_id text NULL
- metadata jsonb
- created_at timestamptz
- updated_at timestamptz
```

Contraintes :
- exactement un sujet : `user_id` XOR `entreprise_id` ;
- `facility` et `kids` sont normalement portés par `user_id` ;
- `industrial` est normalement porté par `entreprise_id` ;
- aucun droit ne dépend d’un bouton masqué ou d’une valeur locale dans le navigateur ;
- chaque accès applicatif est vérifié côté serveur.

Le nom exact de la table peut être ajusté, mais la responsabilité ne doit pas être diluée dans `profiles`, `clients` et `abonnements` simultanément.

---

## 5. Situation réelle observée avant migration

État relevé lors de l’audit :
- 6 comptes Supabase Auth ARIA ;
- 6 lignes `profiles` ;
- 10 lignes `clients` ;
- 1 ligne `abonnements` ;
- 2 `entreprises` ;
- 2 `salaries` ;
- seulement 4 utilisateurs Auth sur 6 correspondent actuellement à une ligne `clients` par email ;
- plusieurs lignes `clients` sont historiques et n’ont pas de compte Auth associé.

Conséquence : **ne jamais supprimer ou fusionner brutalement `clients` avec `profiles`.** Une table de correspondance/migration doit être produite avant écriture.

---

## 6. Sécurité ARIA — priorité P0

La table `public.clients` a RLS activé mais possède actuellement des policies permissives équivalentes à :
- SELECT : `true` ;
- INSERT : `true` ;
- UPDATE : `true`.

Elle contient notamment email, token ARIA, forfait, statut actif, `produits[]`, données Kids, tokens d’installation et rappels.

**Avant mise en production du nouveau parcours compte :**
- supprimer l’exposition directe anonyme de `clients` ;
- révoquer les privilèges inutiles `anon` ;
- le frontend public ne doit pas lire `clients` directement ;
- les opérations privilégiées passent par Relay/backend avec service role ;
- créer uniquement les RPC/policies minimales nécessaires si un accès direct authentifié est réellement requis ;
- `stripe_events` ne doit pas être lisible publiquement ;
- les tables RLS sans policy sont par défaut fermées : ne pas ajouter de policy simplement pour faire disparaître un warning ; vérifier d’abord si elles doivent rester backend-only.

La correction RLS doit être testée contre Facility, Kids, Industrial, presse et admin avant application production.

---

## 7. Stripe réel — inventaire et logique cible

Le compte Stripe live FORGEDIS contient actuellement des produits actifs correspondant notamment à :

### Facility
- produit : `prod_UhHh3dtBPIED6i` — Aria Facility ;
- prix payant actif : `price_1Tht8LI54RQfwJiYNUvxbLzd` = 12,99 €/mois ;
- un ancien/autre prix actif à 0 € existe aussi sur le même produit (`price_1Tomp0I54RQfwJiYr3qI18Ua`).

**Risque :** ne jamais sélectionner le prix Facility par « default price » implicite. Utiliser un mapping serveur explicite du Price ID payant attendu.

### Kids
- Solo : `prod_UrdvcsgXqxJbK2` / `price_1TrudbI54RQfwJiY4k26O7dG` = 9,99 €/mois, essai Stripe 14 jours ;
- Famille : `prod_UrdxZxTDPHxJrJ` / `price_1TrufbI54RQfwJiYeD5fbW7b` = 14,99 €/mois, essai Stripe 14 jours.

### Industrial
Architecture tarifaire active observée :
- base entreprise : 49 €/mois (`price_1Txb8dI54RQfwJiYhVgtBFWP`) ;
- salarié 1–5 : 15 €/mois/unité ;
- salarié 6–15 : 12 €/mois/unité ;
- salarié 16–49 : 10 €/mois/unité ;
- salarié 50+ : 8 €/mois/unité ;
- site additionnel : 25 €/mois ;
- sauvegarde cloud : 7 €/mois ;
- poste sur mesure : 15 €/mois.

Cela explique le « dès 64 €/mois » : base 49 € + 1 salarié tranche 1–5 à 15 €.

Il existe également un produit générique `Aria Industrial` sans prix par défaut. L’implémentation doit choisir une seule génération tarifaire canonique, probablement les composants explicites ci-dessus, et désactiver l’ambiguïté logique côté code avant ventes réelles.

### Situation live

Au moment de l’audit :
- 0 Customer Stripe live ;
- 0 Subscription Stripe live.

C’est une fenêtre favorable pour harmoniser l’architecture avant acquisition client, sans migration d’abonnements actifs existants.

---

## 8. Webhook Stripe — logique obligatoire

Endpoint Stripe live observé :
`https://aria-forgelis.onrender.com/stripe-webhook`

Événements actuellement inscrits :
- `checkout.session.completed` ;
- `invoice.payment_succeeded` ;
- `customer.subscription.deleted`.

La logique cible doit couvrir au minimum les transitions nécessaires à l’entitlement :
- création/confirmation de souscription ;
- `customer.subscription.updated` ;
- paiement réussi ;
- paiement échoué / `past_due` ;
- annulation avec accès conservé jusqu’à `current_period_end` si applicable ;
- suppression/fin réelle ;
- éventuels remboursements si leur effet métier est défini.

### Interdit

Le webhook actuel ne doit plus contenir un fallback :

```text
produit inconnu -> facility
```

La règle doit devenir :

```text
(price_id, product_id, metadata) reconnus -> mapping explicite -> entitlement
inconnu/incohérent -> aucune attribution -> log + alerte + réponse contrôlée
```

Les Price IDs doivent être une allowlist serveur ou une table de catalogue versionnée, pas une déduction fragile par description.

### Idempotence

`stripe_events.event_id` unique existe déjà. La DB doit être l’autorité d’idempotence, pas uniquement le set mémoire du processus. Le traitement doit enregistrer/vérifier l’event de façon transactionnelle ou atomique avant/après projection selon un protocole déterministe.

---

## 9. Essais gratuits

Un seul modèle d’essai doit être choisi par produit et documenté.

État actuel :
- Kids utilise des prices Stripe avec `trial_period_days = 14` ;
- Facility expose « 14 jours gratuits » sur le site mais son prix 12,99 € n’a pas de trial Stripe ;
- Facility possède aussi un prix 0 € historique/actif ;
- Industrial affiche 14 jours gratuits mais les composants tarifaires observés n’ont pas de trial Stripe.

**Il ne faut pas mélanger :** essai applicatif dans Supabase, abonnement Stripe trialing, et prix Stripe gratuit comme trois façons concurrentes de représenter le même état.

Recommandation :
- abonnement payant Stripe + statut `trialing` lorsque la carte est prise au démarrage ; ou
- entitlement `trial` côté ARIA sans Stripe lorsqu’aucune carte n’est prise, puis Checkout explicite pour conversion.

Le choix UX final peut différer par produit, mais une seule autorité doit déterminer l’accès à un instant donné.

---

## 10. Portail FORGEDIS unique

Le bouton **Se connecter** doit avoir la même signification partout : ouvrir le portail FORGEDIS.

Après authentification :

```text
JWT Supabase Auth
 -> backend /me ou /portal-context
 -> profil + entitlements actifs
 -> portail affiche les produits autorisés
 -> chaque bouton produit demande/obtient un accès serveur valide
```

Exemples :
- aucun entitlement -> écran de découverte/essai ;
- Facility uniquement -> carte Facility ;
- Kids Famille -> carte Kids avec plan Famille ;
- Facility + Kids -> deux cartes ;
- Industrial dirigeant -> carte Industrial et entreprise ;
- admin/presse -> vue explicitement marquée et contrôlée.

Le portail ne doit jamais deviner le produit à partir de la page d’origine ni rediriger tous les comptes vers Facility.

---

## 11. Navigation publique ARIA

`ARIA` dans le header doit toujours signifier la même chose.

Solution recommandée :
- desktop : dropdown accessible « ARIA » -> Facility / Kids / Industrial ;
- mobile : sous-menu équivalent ;
- option complémentaire : `aria.html`/section hub si nécessaire plus tard.

**Interdit :** `ARIA` -> Facility sur Home, `ARIA` -> Kids sur Kids, `ARIA` -> Industrial sur Industrial.

Les CTA produit restent spécifiques :
- Facility -> démarrage Facility ;
- Kids -> choix Solo/Famille puis parcours Kids ;
- Industrial -> configurateur/qualification d’effectif puis Checkout/onboarding Industrial.

---

## 12. Industrial

Industrial est différent des offres individuelles :
- entitlement principal porté par l’entreprise ;
- un dirigeant/utilisateur possède une relation à l’entreprise ;
- les salariés héritent de droits métier déterminés par `salaries`, rôle, niveau, équipe et permissions ;
- l’état d’abonnement de l’entreprise est contrôlé serveur avant accès ;
- les prix par effectifs/options doivent être calculés à partir d’un catalogue serveur explicite ;
- la quantité et les composants facturés doivent pouvoir être réconciliés avec Stripe.

Le moteur de devis métier Industrial reste distinct du devis commercial/abonnement Stripe.

---

## 13. NEXORA public

Le `nexora-quote.js` public actuel est un assistant déterministe 6 étapes. Il ne doit pas obtenir une service key NEXORA ni écrire directement dans le Supabase NEXORA.

Architecture cible :

```text
nexora-quote.js
 -> endpoint public FORGEDIS/Consulting
 -> validation + rate limit + anti-abus
 -> création d’un lead/devis brouillon
 -> éventuel pont serveur vers NEXORA
 -> audit NEXORA
```

Une demande publique ne devient jamais automatiquement une mission validée ou un engagement commercial ferme.

---

## 14. Source canonique de déploiement

Une seule chaîne autorisée :

```text
GitHub canonique
 -> commit SHA identifié
 -> Deploy Preview
 -> tests automatiques + manuels
 -> production
```

Aucun fichier indispensable (`portail.html`, connexion, app, script auth, etc.) ne doit exister uniquement dans le dossier local de Claude ou uniquement dans un paquet Netlify CLI.

Avant tout nouveau travail fonctionnel :
1. récupérer les fichiers de production manquants ;
2. les committer dans GitHub sur la branche de travail ;
3. confirmer que le package preview est construit depuis ce même commit ;
4. interdire un `--prod` tant que les tests ne sont pas validés.

---

## 15. Ordre de migration imposé

### Phase A — synchronisation et inventaire
1. synchroniser GitHub / dossier Claude / preview Netlify ;
2. committer tous les fichiers auth/portail/apps nécessaires ;
3. générer la matrice de toutes les routes et CTA ;
4. générer la matrice des tables/colonnes qui portent un produit, plan, abonnement ou droit ;
5. exporter un état de référence des comptes sans exposer les secrets.

### Phase B — sécurité P0
1. identifier tout accès frontend direct à `clients` ;
2. déplacer ces accès vers backend/RPC sécurisé si nécessaire ;
3. fermer les policies publiques `clients` ;
4. fermer l’exposition publique `stripe_events` ;
5. activer/ajuster les policies strictes et tester tous les rôles ;
6. activer la protection de mots de passe compromis Supabase si compatible avec le plan/configuration.

### Phase C — modèle canonique
1. ajouter la couche d’entitlements de façon additive ;
2. backfill avec rapport de correspondance ;
3. zéro suppression de données ;
4. comparer ancien droit vs nouveau droit compte par compte ;
5. tant qu’une divergence existe, ne pas basculer la lecture applicative.

### Phase D — Stripe
1. créer une allowlist serveur Product/Price -> product/plan ;
2. supprimer le fallback Facility ;
3. rendre idempotence DB autoritaire ;
4. couvrir les transitions abonnement/paiement ;
5. décider et unifier le modèle d’essai ;
6. pour Industrial, utiliser les composants de prix explicitement et valider les quantités côté serveur.

### Phase E — portail et routes
1. portail FORGEDIS unique ;
2. route `/me`/contexte portail ;
3. ARIA dropdown/hub cohérent ;
4. CTA d’essai/achat produit explicites ;
5. redirections post-login basées sur entitlements, pas sur un HTML spécifique.

### Phase F — applications
1. Facility ;
2. Kids ;
3. Industrial ;
4. presse/admin ;
5. NEXORA public -> backend Consulting séparé.

### Phase G — suppression du legacy
Seulement après une période d’observation et comparaison :
- déprécier les colonnes redondantes ;
- ne supprimer une source legacy que lorsqu’aucun code ne la lit/écrit et que les tests de migration sont verts.

---

## 16. Invariants de sécurité et de logique

Chaque changement doit préserver :
- un utilisateur = une identité Auth ;
- un droit = une source canonique ;
- un paiement = un événement Stripe vérifié ;
- un produit inconnu = refus, jamais fallback ;
- un abonnement inactif = accès refusé côté serveur ;
- une entreprise Industrial = isolation par `entreprise_id` ;
- aucune service role key dans le navigateur ;
- NEXORA interne séparé d’ARIA ;
- aucune modification production avant preview et tests ;
- aucune perte des comptes historiques ;
- aucun prix inventé ;
- aucune redirection dépendant implicitement de la page depuis laquelle l’utilisateur s’est connecté.

---

## 17. Triple vérification obligatoire avant production

### Vérification 1 — cohérence structurelle
- une seule source par responsabilité ;
- schéma de dépendances sans cycle incohérent ;
- GitHub = package preview ;
- aucune route vers fichier absent ;
- aucun doublon d’identité ou entitlement non expliqué ;
- matrices produit/plan/price complètes.

### Vérification 2 — sécurité et données
- RLS et grants testés en `anon`, `authenticated`, admin/backend ;
- tentative de lecture du token d’un autre utilisateur impossible ;
- tentative de modifier forfait/actif depuis navigateur impossible ;
- isolation Industrial inter-entreprises ;
- webhook Stripe signé + idempotent ;
- aucun Product/Price inconnu accepté ;
- NEXORA inaccessible depuis le frontend public hors endpoints explicitement prévus.

### Vérification 3 — parcours utilisateur de bout en bout
Pour Facility, Kids Solo, Kids Famille et Industrial :
- visite vitrine ;
- CTA ;
- création compte ;
- login/logout/récupération ;
- essai ;
- Checkout ;
- webhook ;
- apparition entitlement ;
- portail ;
- accès app ;
- paiement échoué ;
- annulation ;
- expiration ;
- réactivation ;
- multi-produit ;
- mobile/desktop ;
- aucune erreur console ;
- aucun lien cassé.

**Production interdite si une seule des trois vérifications échoue.**

---

## 18. Critère final d’acceptation

Le système est harmonisé uniquement si cette phrase est vraie sans exception cachée :

> « FORGEDIS sait qui est l’utilisateur, quels produits ou entreprises lui appartiennent, pourquoi il y a accès, jusqu’à quand, quel paiement justifie ce droit, et chaque application vérifie ce droit au bon endroit côté serveur. »

Tout changement qui ne rapproche pas le système de cette propriété doit être rejeté ou différé.
