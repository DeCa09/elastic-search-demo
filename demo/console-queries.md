# Queries for Kibana Dev Tools

Open **Dev Tools > Console** and paste the block you need. Press the green arrow (or Cmd + Enter) to run it.
The same queries run in the terminal with `scripts/ask.sh`. This file is generated from `elastic/queries.py`.

## 1. Keyword search (what the bank has today)

```
POST albisgrat-knowledge/_search
{
  "size": 5,
  "_source": [
    "title",
    "language"
  ],
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "Qui doit donner son accord avant de confier des données de clients à un prestataire informatique externe ?",
            "fields": [
              "title^2",
              "body_de",
              "body_fr",
              "body_it",
              "body_en"
            ],
            "type": "best_fields"
          }
        }
      ],
      "filter": []
    }
  }
}
```
## 2. Hybrid search: keyword + multilingual semantic, fused with RRF

```
POST albisgrat-knowledge/_search
{
  "size": 5,
  "_source": [
    "title",
    "language",
    "is_current",
    "allowed_groups"
  ],
  "retriever": {
    "rrf": {
      "retrievers": [
        {
          "standard": {
            "query": {
              "multi_match": {
                "query": "Qui doit donner son accord avant de confier des données de clients à un prestataire informatique externe ?",
                "fields": [
                  "title^2",
                  "body_de",
                  "body_fr",
                  "body_it",
                  "body_en"
                ],
                "type": "best_fields"
              }
            }
          }
        },
        {
          "standard": {
            "query": {
              "match": {
                "body_semantic": {
                  "query": "Qui doit donner son accord avant de confier des données de clients à un prestataire informatique externe ?"
                }
              }
            }
          }
        }
      ],
      "rank_window_size": 50,
      "rank_constant": 60
    }
  },
  "highlight": {
    "fields": {
      "body_semantic": {
        "type": "semantic",
        "number_of_fragments": 1,
        "order": "score"
      }
    }
  }
}
```
## 4. Permissions: run this once as compliance_officer and once as relationship_manager

```
POST albisgrat-knowledge/_search
{
  "size": 6,
  "_source": [
    "title",
    "language",
    "version",
    "is_current",
    "allowed_groups"
  ],
  "retriever": {
    "rrf": {
      "retrievers": [
        {
          "standard": {
            "query": {
              "multi_match": {
                "query": "Welche Anforderungen gelten für die Auslagerung von Kundendaten an einen Cloud-Anbieter?",
                "fields": [
                  "title^2",
                  "body_de",
                  "body_fr",
                  "body_it",
                  "body_en"
                ],
                "type": "best_fields"
              }
            }
          }
        },
        {
          "standard": {
            "query": {
              "match": {
                "body_semantic": {
                  "query": "Welche Anforderungen gelten für die Auslagerung von Kundendaten an einen Cloud-Anbieter?"
                }
              }
            }
          }
        }
      ],
      "rank_window_size": 50,
      "rank_constant": 60
    }
  }
}
```
## 5. Versions: only documents that are in force (remove the "filter" line to see the outdated version return)

```
POST albisgrat-knowledge/_search
{
  "size": 4,
  "_source": [
    "title",
    "version",
    "valid_from",
    "is_current"
  ],
  "retriever": {
    "rrf": {
      "retrievers": [
        {
          "standard": {
            "query": {
              "multi_match": {
                "query": "Dürfen Kundendaten in der EU gespeichert werden?",
                "fields": [
                  "title^2",
                  "body_de",
                  "body_fr",
                  "body_it",
                  "body_en"
                ],
                "type": "best_fields"
              }
            }
          }
        },
        {
          "standard": {
            "query": {
              "match": {
                "body_semantic": {
                  "query": "Dürfen Kundendaten in der EU gespeichert werden?"
                }
              }
            }
          }
        }
      ],
      "rank_window_size": 50,
      "rank_constant": 60,
      "filter": [
        {
          "term": {
            "is_current": true
          }
        }
      ]
    }
  }
}
```
## Useful extras

Show how a German compound is analysed (decompounding and stemming):

```
POST albisgrat-knowledge/_analyze
{ "field": "body_de", "text": "Kundendaten" }
```

Show the language the ingest pipeline detected:

```
POST albisgrat-knowledge/_search
{ "size": 3, "_source": ["title", "language", "language_detected", "language_confidence"],
  "query": { "term": { "source": "internal" } } }
```

Show who I am and which groups drive my document access:

```
GET _security/_authenticate
```
