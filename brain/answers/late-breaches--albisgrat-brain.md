# late-breaches

Agent: With Knowledge Indicators

Question: Quelles violations de la sécurité des données ont été annoncées en retard cette année, et lesquelles concernent un prestataire externe ?

Expected records: INC-2026-023, INC-2026-043

Tools called: albisgrat.brain.query_ki, platform.core.execute_esql, platform.core.execute_esql, platform.core.execute_esql, platform.core.execute_esql, platform.core.execute_esql, platform.core.execute_esql, platform.core.execute_esql

---

Parfait ! Je vois que le champ est `provider_code` et non `provider`. Maintenant je peux combiner les informations pour la réponse finale.

Basé sur mes requêtes, j'ai trouvé :

## Violations de la sécurité des données annoncées en retard en 2026

| Incident ID | Date | Sévérité | Description | Prestataire externe |
|------------|------|----------|-------------|---------------------|
| **INC-2026-023** | 04.01.2026 | Faible | Données client non masquées découvertes dans un environnement de test | Non |
| **INC-2026-043** | 17.03.2026 | Élevée | Données client non masquées de 312 clients pendant 9 jours dans un environnement de test chez un fournisseur cloud | **Oui** (OUT-019, Provider S, US) |

### Violation concernant un prestataire externe :
- **INC-2026-043** : Cette violation implique l'arrangement externe OUT-019 (Data warehouse test environment, Provider S, localisation US)

**Basé sur :** index albisgrat-incidents, albisgrat-outsourcing-inventory, Knowledge Indicators (définition "Late-reported data breach" selon P-11)
