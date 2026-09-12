# FORGEDIS public redesign — handoff Claude

Branch préparée par Charlie : `forgedis-public-redesign`.

## Ce qui est déjà préparé

- `index.html` : nouvelle Home FORGEDIS, Consulting prioritaire, ARIA présenté comme technologie propriétaire.
- `consulting.html` : nouvelle page Consulting + tarifs vérifiés + interface NEXORA de qualification/devis.
- `facility.html` : nouvelle page Facility selon la maquette validée.
- `kids.html` : nouvelle page Kids orientée cours/progression + tarifs Solo/Famille vérifiés.
- `industrial.html` : nouvelle page Industrial + interface de création de devis avec ARIA et aperçu en direct.
- `mentions-legales.html` : même texte GitHub existant, nouvelle identité visuelle.
- `confidentialite.html` : même texte GitHub existant, nouvelle identité visuelle.
- `forgedis-v2.css` : design system public commun Jour/Nuit.
- `forgedis-v2.js` : thème Jour/Nuit + menu mobile.
- `nexora-quote.js` : scaffold frontend sûr pour la qualification NEXORA, sans hallucination de prix.

## Règles de vérité

1. Ne pas réinventer le design : cette branche est la base d'intégration.
2. NEXORA apparaît uniquement dans Consulting.
3. Facility, Kids et Industrial utilisent ARIA, jamais NEXORA.
4. Ne pas inventer prix, témoignages, intégrations, clients, certifications ou métriques.
5. Industrial : conserver/réutiliser le moteur de devis réel présent dans l'application déployée. Ne pas recréer une logique concurrente.
6. Kids : conserver la logique réelle de cours/progression. Ne pas transformer le produit en chatbot générique.
7. Les actions sensibles Industrial restent soumises aux permissions existantes.

## Tarifs autorisés

### Consulting
- Diagnostic : 290 €
- Sites/outils : dès 590 €
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
- Ne pas afficher « jusqu'à 4 profils » ou d'autres différences de forfait non confirmées.

### Industrial
- Dès 64 €/mois
- Selon effectifs
- 14 jours gratuits
- Ne pas inventer de grille supplémentaire.

## Blocage principal avant mise en ligne

Le dépôt GitHub canonique ne contient actuellement pas les fichiers applicatifs référencés par `_redirects` :

- `aria_senior_v2.html`
- `aria_kids_v2.html`
- `aria_industrial_v1.html`

Ils peuvent encore exister dans le déploiement Netlify de production. Avant tout déploiement :

1. Inventorier la production Netlify actuelle.
2. Récupérer/sauvegarder ces trois fichiers et tout fichier associé qui n'existe pas dans GitHub.
3. Réintégrer ces fichiers dans le paquet de déploiement ou dans le dépôt si approprié.
4. Ne jamais lancer un déploiement qui supprimerait ces applications.

## Important — pages juridiques

La version publique actuellement indexée de la politique de confidentialité est plus complète que le fichier GitHub historique : elle contient notamment bases légales, sous-traitants, transferts hors UE, sécurité, spécificités Facility/Kids/Industrial et droits RGPD détaillés.

Au moment de la mise en ligne :

- conserver le DESIGN de `confidentialite.html` préparé dans cette branche ;
- mais reprendre le TEXTE COMPLET de la version juridique actuellement en production s'il est toujours plus récent ;
- ne supprimer aucune section juridique existante ;
- ne changer aucun engagement RGPD sans validation humaine.

Même règle pour toute CGV/CGU ou page légale présente en production mais absente du dépôt actuel : préserver le texte, appliquer uniquement le design FORGEDIS.

## NEXORA Consulting

`nexora-quote.js` est volontairement un scaffold frontend de qualification. Il sait :

- recueillir un besoin libre ;
- sélectionner une catégorie de prestation ;
- afficher uniquement les prix vérifiés ;
- afficher « Sur étude » pour Autre ;
- construire une synthèse provisoire.

Il ne prétend pas être le moteur IA final. Si une API NEXORA réelle existe, connecter l'interface à cette API sans supprimer les garde-fous tarifaires.

## Industrial devis

La page vitrine préparée montre :

client → discussion avec ARIA → devis en construction → contrôle → validation → envoi → suivi.

La maquette ne doit pas devenir la source de vérité du moteur métier. Le vrai `aria_industrial_v1.html` doit être audité et son système de devis réutilisé/adapté.

## Tests obligatoires avant production

Vérifier au minimum :

- `/`
- `/consulting.html`
- `/facility.html`
- `/kids.html`
- `/industrial.html`
- `/senior`
- `/kids`
- `/industrial`
- `/portail`
- `/admin`
- `/confidentialite.html`
- `/mentions-legales.html`

Tester : Jour/Nuit, desktop, mobile, clavier, reduced motion, formulaires Netlify, Stripe, authentification, Supabase, routes, console, 404, SEO/canonical.

## Déploiement

Ne déployer qu'après audit complet du paquet de production actuel. La mission de Claude est maintenant principalement :

1. récupérer les fichiers applicatifs manquants ;
2. connecter les interfaces préparées aux fonctions existantes ;
3. préserver les textes juridiques plus récents de production ;
4. tester ;
5. publier sans perte de fonctionnalité.
