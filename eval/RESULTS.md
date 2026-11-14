# Evaluation: keyword search vs hybrid search

20 judged queries in German, French, Italian and English. Index: albisgrat-knowledge. Embedding endpoint: .jina-embeddings-v5-text-small.

| Metric | Keyword only | Hybrid (keyword + semantic, RRF) |
|---|---|---|
| Answer in the top 5 (success@5) | 60% | 100% |
| Precision@5 | 0.47 | 0.90 |
| nDCG@10 | 0.36 | 0.76 |
| Queries with zero results | 0% | 0% |

## Answer in the top 5, by kind of query

| Kind of query | Queries | Keyword only | Hybrid |
|---|---|---|---|
| cross-language question | 9 | 22% | 100% |
| same-language keywords | 4 | 100% | 100% |
| same-language question | 7 | 86% | 100% |

## Per query (rank of the first relevant document)

| Id | Lang | Kind | Keyword | Hybrid | Query |
|---|---|---|---|---|---|
| q01 | fr | cross-language question | not in top 10 | rank 2 | Qui doit donner son accord avant de confier des données de clients à un prestataire informatique externe ? |
| q02 | it | cross-language question | not in top 10 | rank 2 | Chi deve approvare il trasferimento dei dati dei clienti a un fornitore esterno? |
| q03 | en | cross-language question | not in top 10 | rank 1 | Who must approve outsourcing of client data to an external provider? |
| q04 | de | same-language keywords | rank 1 | rank 1 | Auslagerung Kundendaten Genehmigung |
| q05 | de | same-language question | rank 3 | rank 1 | Wie lange müssen Kundenunterlagen nach Ende der Geschäftsbeziehung aufbewahrt werden? |
| q06 | fr | cross-language question | rank 3 | rank 3 | Combien de temps faut-il conserver les documents des clients après la fin de la relation ? |
| q07 | fr | same-language keywords | rank 1 | rank 1 | annonce violation sécurité des données PFPDT |
| q08 | de | cross-language question | rank 4 | rank 4 | Innert welcher Frist muss eine Verletzung der Datensicherheit intern gemeldet werden? |
| q09 | it | same-language question | rank 2 | rank 1 | Quando devo comunicare un sospetto di riciclaggio di denaro all'Ufficio di comunicazione? |
| q10 | de | same-language question | rank 8 | rank 2 | Wann muss ein Verdacht auf Geldwäscherei der Meldestelle gemeldet werden? |
| q11 | fr | same-language question | rank 3 | rank 1 | Quelle est la valeur maximale d'un cadeau que je peux accepter d'un client ? |
| q12 | de | cross-language question | not in top 10 | rank 2 | Bis zu welchem Betrag darf ich Geschenke von Kunden annehmen? |
| q13 | it | same-language question | rank 1 | rank 1 | Posso lavorare da remoto dall'estero? |
| q14 | fr | cross-language question | not in top 10 | rank 1 | Puis-je travailler à distance depuis l'étranger ? |
| q15 | de | same-language keywords | rank 1 | rank 1 | PEP Genehmigung Geschäftsleitung |
| q16 | it | cross-language question | not in top 10 | rank 4 | Chi approva una relazione d'affari con una persona politicamente esposta? |
| q17 | fr | same-language question | rank 4 | rank 1 | Dans quel délai faut-il répondre à une réclamation d'un client ? |
| q18 | en | cross-language question | not in top 10 | rank 5 | How do we handle a data subject access request? |
| q19 | de | same-language question | rank 4 | rank 1 | Unter welchen Voraussetzungen dürfen Personendaten ins Ausland bekanntgegeben werden? |
| q20 | fr | same-language keywords | rank 3 | rank 2 | violation du secret bancaire peine |

This is a small, hand-judged set, and the retrieval was tuned on it. It shows direction, not statistical proof. Run it again after every change to analyzers, chunking or the embedding model, and add fresh questions before you trust a gain.
