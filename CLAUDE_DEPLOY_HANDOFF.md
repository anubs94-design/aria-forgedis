# FORGEDIS PUBLIC REDESIGN — HANDOFF CLAUDE

Branch de travail : `forgedis-public-redesign`

## AUTORITÉ VISUELLE ABSOLUE

Les cinq maquettes validées par Victor sont la référence visuelle absolue : Home, Consulting, ARIA Facility, ARIA Kids, ARIA Industrial.

RÈGLE D’OR : **le site doit reproduire les maquettes, pas les réinterpréter.**

Ne pas refaire le design. Ne pas moderniser à ta manière. Ne pas remplacer une composition par un template. Ne pas simplifier un bloc parce qu’un composant standard serait plus facile.

Les photographies peuvent être remplacées par des images HD différentes uniquement si elles produisent le même effet visuel : même sujet, cadrage comparable, position du personnage comparable, direction du regard compatible, même équilibre texte/image, ambiance et lumière proches.

INTERDIT : utiliser les maquettes aplaties comme grandes images de page, découper/étirer des morceaux basse définition des maquettes, ou déformer une photo pour la faire rentrer.

Le HTML/CSS doit rester réel : textes, boutons, interfaces, cartes, chats, devis, tarifs et navigation sont des éléments DOM accessibles et responsive.

## FICHIERS DE DESIGN À CONSERVER

- `forgedis-v3.css` : système visuel principal de la refonte.
- `forgedis-v3-fixes.css` : corrections responsive, thème sombre et reduced-motion.
- `forgedis-v2.js` : gestion thème/menu ; il charge les fixes V3 sur les pages V3.
- `nexora-quote.js` : scaffold frontend sécurisé de NEXORA Consulting.

Ne pas revenir au rendu abstrait de `forgedis-v2.css`.

## PAGES PUBLIQUES PRÉPARÉES

- `index.html` : Home correspondant à la maquette validée.
- `consulting.html` : Consulting + NEXORA.
- `facility.html` : ARIA Facility.
- `kids.html` : ARIA Kids, orienté cours/progression.
- `industrial.html` : ARIA Industrial avec démonstration de création de devis.
- `confidentialite.html` : politique complète actuellement connue, restylée dans la nouvelle identité.
- `mentions-legales.html` : texte légal conservé, nouvelle identité.

## RÈGLE DE NON-RÉGRESSION

L’ancien HTML est une source de fonctions et de contenu. Aucun accès utile ne doit disparaître sous prétexte de design.

Éléments obligatoires à préserver :

- `Se connecter` → `portail.html` ;
- accès ARIA Facility `/senior` ;
- accès ARIA Kids `/kids` ;
- accès ARIA Industrial `/industrial` ;
- paiements/Stripe existants dans les applications ;
- authentification ;
- Supabase ;
- formulaires Netlify ;
- changement de langue si présent dans les applications ;
- routes, redirections et fonctionnalités produit existantes ;
- contenus juridiques plus récents présents en production.

Si une fonction existante ne rentre pas naturellement dans la composition, l’intégrer sans casser la maquette. Ne jamais la supprimer silencieusement.

## ARCHITECTURE DE MARQUE

- FORGEDIS = masterbrand.
- FORGEDIS Consulting = activité de conseil/service.
- ARIA = famille produit : Facility / Kids / Industrial.
- NEXORA = **Consulting uniquement**.

INTERDIT : mettre NEXORA dans Facility, Kids ou Industrial.

## TARIFS AUTORISÉS

### Consulting
- Diagnostic : 290 €
- Sites / outils : dès 590 €
- Automatisations : dès 590 €
- Solutions IA : dès 990 €
- Outils métier : dès 1 490 €
- Projets complexes : sur étude
- Accompagnement : dès 99 €/mois

### Facility
- 12,99 €/mois
- 14 jours gratuits

### Kids
- Solo : 9,99 €/mois
- Famille : 14,99 €/mois
- 14 jours gratuits
- Synchronisation cloud chiffrée optionnelle pour Famille : confirmée.
- Ne pas inventer un nombre de profils, de limites de compte ou d’inclusions non vérifiées.

### Industrial
- dès 64 €/mois
- selon effectifs
- 14 jours gratuits
- ne pas inventer de grille supplémentaire.

## NEXORA — CONSULTING

L’interface publique doit rester un assistant de qualification/devis et non exposer arbitrairement l’outil interne complet.

Règles :

1. Toujours permettre une réponse libre.
2. Toujours proposer `Autre — décrire mon projet`.
3. Prix automatique uniquement si une règle tarifaire vérifiée correspond.
4. Hors catalogue / complexe : `Sur étude` ou validation humaine.
5. Victor / FORGEDIS conserve l’autorité finale sur les devis non standards.
6. Ne jamais halluciner un prix.
7. Les valeurs de projets visibles dans la maquette/dashboard sont des exemples visuels, pas des clients réels.

Si une API NEXORA réelle existe, connecter l’interface à celle-ci sans retirer ces garde-fous.

## ARIA INDUSTRIAL — CRITIQUE

Le dépôt GitHub ne contient pas actuellement `aria_industrial_v1.html`, alors que `/industrial` y redirige.

Victor a confirmé que **le vrai moteur de devis Industrial est directement codé dans le HTML de l’application**.

Donc :

- ne pas considérer la démonstration de `industrial.html` comme moteur métier ;
- récupérer et auditer le `aria_industrial_v1.html` actuellement déployé ;
- réutiliser son moteur de devis, ses permissions, validations et logique métier ;
- ne pas créer de moteur concurrent ;
- conserver le contrôle humain pour les actions sensibles.

Les noms, dates, montants et société visibles dans la vitrine de démonstration sont des données fictives de présentation.

## ARIA KIDS

Ne pas transformer Kids en chatbot générique.

Conserver le fonctionnement réel autour des cours, exercices, devoirs, progression, scanner et contrôle parental.

Ne pas inventer de différences Solo/Famille non confirmées.

## ARIA FACILITY

Conserver les fonctions existantes utiles : pilotage vocal, aide à la navigation, anti-arnaques, accompagnement famille et rappels si elles sont présentes dans l’application réelle.

## PAGES JURIDIQUES

La politique de confidentialité complète a été réintégrée dans `confidentialite.html`.

Avant publication, comparer encore avec la version actuellement en production. Si la production contient un texte juridique plus récent ou une page réglementaire supplémentaire :

- conserver le texte le plus récent ;
- appliquer seulement la présentation FORGEDIS ;
- ne supprimer aucune section ;
- ne modifier aucun engagement juridique sans validation humaine.

Même règle pour CGV, CGU ou autres pages publiques réglementaires éventuellement présentes uniquement en production.

## BLOCAGE ABSOLU AVANT DÉPLOIEMENT

Le dépôt GitHub canonique ne contient pas au minimum :

- `aria_senior_v2.html`
- `aria_kids_v2.html`
- `aria_industrial_v1.html`

et certains fichiers `/portail` / `/admin` peuvent également exister uniquement dans le déploiement Netlify actuel.

**NE PAS DÉPLOYER LE CONTENU DU DÉPÔT TEL QUEL EN PRODUCTION.**

Un déploiement incomplet pourrait supprimer les applications actuellement accessibles.

Avant tout déploiement :

1. Inventorier intégralement le déploiement Netlify de production actuel.
2. Récupérer/sauvegarder tous les fichiers présents en production mais absents de GitHub.
3. Identifier `portail.html`, `admin.html` et tous les fichiers applicatifs associés.
4. Comparer leurs dépendances JS/CSS/assets/API.
5. Réintégrer les fichiers nécessaires dans le paquet final sans modifier leur logique métier avant audit.
6. Vérifier `_redirects` et `_headers`.

## IMAGES

Les URLs photo actuellement présentes dans les vitrines servent d’assets HD de remplacement sélectionnés pour conserver l’effet des maquettes.

Pour la production, il est préférable de :

1. télécharger légalement les sources utilisées ;
2. conserver une copie source HD ;
3. générer AVIF/WebP aux dimensions adaptées ;
4. utiliser `srcset` / `sizes` ;
5. préserver exactement le cadrage visuel validé (`object-fit`, `object-position`) ;
6. ne jamais étirer une image ;
7. ne jamais substituer une autre photographie sans nécessité.

L’optimisation ne doit pas changer la composition.

## PROCÉDURE DE VALIDATION — OBLIGATOIRE

### Étape A — récupération

Récupérer la production actuelle et reconstruire un paquet complet qui contient à la fois :

- vitrines redesignées ;
- applications existantes ;
- portail/auth ;
- assets ;
- fichiers légaux ;
- redirects/headers.

### Étape B — PREVIEW UNIQUEMENT

Créer d’abord un **Netlify Deploy Preview / déploiement non-production**.

NE PAS publier sur `forgedis.fr` à cette étape.

### Étape C — contrôle visuel

À 1024 px de largeur desktop, réaliser une capture pleine page de :

- Home
- Consulting
- Facility
- Kids
- Industrial

Comparer chaque capture côte à côte avec sa maquette de référence.

Contrôler :

- hauteur et ordre de chaque section ;
- positions et proportions ;
- photographie et cadrage ;
- taille/retours à la ligne des titres ;
- espaces blancs ;
- couleurs ;
- CTA ;
- cards ;
- NEXORA ;
- interface Kids ;
- chatbot/devis Industrial ;
- footer.

Si un écart important existe, corriger le site. **Ne pas modifier la maquette pour justifier l’écart.**

### Étape D — contrôle fonctionnel

Tester au minimum :

- `/`
- `/consulting.html`
- `/facility.html`
- `/kids.html`
- `/industrial.html`
- `/senior`
- `/kids`
- `/industrial`
- `/portail`
- `/admin` si présent
- `/confidentialite.html`
- `/mentions-legales.html`

Tester :

- `Se connecter` ;
- authentification ;
- Stripe ;
- Supabase ;
- formulaires Netlify ;
- moteur de devis Industrial ;
- navigation ;
- mobile ;
- clavier ;
- thème Jour/Nuit ;
- reduced motion ;
- console navigateur ;
- 404 ;
- canonical/SEO ;
- absence de liens morts.

### Étape E — contrôle qualité

- aucune image étirée ;
- aucune maquette utilisée comme capture géante ;
- aucun texte inventé présenté comme fait ;
- aucune fausse recommandation client ;
- aucun prix non vérifié ;
- pas de NEXORA hors Consulting ;
- pas de régression juridique ;
- responsive propre ;
- images optimisées ;
- WCAG 2.2 AA dans la mesure applicable ;
- performance raisonnable ;
- aucune erreur console.

### Étape F — production

La production n’est autorisée qu’après validation du preview et des contrôles ci-dessus.

Ne jamais lancer directement un déploiement production depuis la branche sans récupération préalable des applications absentes du dépôt.

## PRINCIPE FINAL

**Le code s’adapte à la maquette. La maquette ne s’adapte pas au code.**

Et la refonte visuelle ne doit jamais provoquer une perte de fonction existante.