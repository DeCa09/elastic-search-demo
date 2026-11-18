# late-breaches

Agent: Baseline, no context

Question: Quelles violations de la sécurité des données ont été annoncées en retard cette année, et lesquelles concernent un prestataire externe ?

Expected records: INC-2026-023, INC-2026-043

Tools called: platform.core.index_explorer, platform.core.search, platform.core.get_index_mapping, platform.core.generate_esql, platform.core.execute_esql, platform.core.search

---

Excellent ! J'ai maintenant toutes les informations nécessaires. Voici ma réponse :

## Violations de la sécurité des données annoncées en retard en 2026

Deux violations de la sécurité des données ont été annoncées en retard cette année (non signalées dans les 24 heures) :

### 1. **INC-2026-023** (4 janvier 2026)
- **Description** : Données clients non masquées découvertes dans un environnement de test
- **Bureau** : Zurich
- **Sévérité** : faible
- **Statut** : fermé
- **Prestataire externe** : Non (aucun arrangement lié)

### 2. **INC-2026-043** (17 mars 2026) ⚠️
- **Description** : Données clients non masquées de 312 clients pendant 9 jours dans un environnement de test chez un fournisseur cloud
- **Bureau** : Zurich
- **Sévérité** : élevée
- **Statut** : fermé
- **Prestataire externe** : **Oui - OUT-019** (Provider S, service cloud pour environnement de test data warehouse, données localisées aux États-Unis)

**L'incident INC-2026-043 concerne donc un prestataire externe** et représente la violation la plus grave avec 312 clients affectés sur une période de 9 jours.
