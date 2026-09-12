# FORGEDIS — Execution Gate

Claude ne doit commencer les modifications fonctionnelles qu’après :

- lecture de `FORGEDIS_ARCHITECTURE_HARMONISATION.md` ;
- lecture de `FORGEDIS_ARCHITECTURE_CHECKS.md` ;
- lecture de `FORGEDIS_CLAUDE_EXECUTION_HANDOFF.md` ;
- synchronisation complète des fichiers auth/portail/apps dans GitHub ;
- confirmation qu’aucun changement production n’est effectué ;
- création d’un preview uniquement.

Si l’un de ces points est faux : **STOP, rapporter le blocage, ne pas bricoler de contournement local.**
