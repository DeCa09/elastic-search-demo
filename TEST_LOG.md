# Test log

Date: 14 November 2026.

## Where the tests ran

| Environment | What | Used for |
|---|---|---|
| **Your Elastic Cloud Hosted deployment** `albisgrat-demo`, AWS Frankfurt, version 9.5.6 | Index with `.jina-embeddings-v5-text-small` on the Elastic Inference Service; Agent Builder with the default managed LLM (`anthropic-claude-5-sonnet`) | Everything below marked Cloud |
| Local stack, Elasticsearch and Kibana 9.5.6 in Docker, local trial licence | Index with `.multilingual-e5-small-elasticsearch` | First build, comparison of embedding models |

I called your deployment through this session's network proxy with the API key you entered in the secure form. I never saw the key. Because the proxy owns the `Authorization` header, I tested "as a demo user" by impersonation (Elasticsearch "run as" with the admin key), not by logging in with the users' passwords, and I could not open Kibana in a browser as those users.

## Results on Cloud

| # | Test | Result |
|---|---|---|
| 1 | `setup_search.py index`: pipeline and strict index created | Pass |
| 2 | `ingest`: 1,281 documents with language detection and Jina embeddings | Pass, 0 errors, 24 s (27 s including index creation) |
| 3 | `security`: role with templated document-level security, two users | Pass |
| 4 | Document counts per user: compliance officer 1,281 (2 restricted), relationship manager 1,279 (0 restricted) | Pass |
| 5 | Moment 1, keyword search with the French question: five French documents, the German directive absent | Pass |
| 6 | Moment 2, hybrid search with the same question: Weisung W-12 v3.0 at rank 1 | Pass |
| 7 | Moment 4 at search level: restricted memo at rank 1 for the compliance officer, absent for the relationship manager | Pass |
| 8 | Version moment: W-12 v2.0 (outdated) at rank 1 without filter; gone with `is_current: true` | Pass |
| 9 | `agent`: tool and agent created through the Kibana API | Pass |
| 10 | Agent, English question A: English answer, each point cited to a section of the German directive, outdated version flagged, memo rule included (admin key sees everything) | Pass, 66 s |
| 11 | Agent, French question A after shortening the instructions: French answer with section citations and a source list | Pass, 36 s |
| 12 | Agent, German question B: interim rule from the confidential memo first, then the three approvals | Pass, 47 s |
| 13 | `preflight.sh` | Pass |
| 14 | Evaluation, 20 judged questions | See below |

## Evaluation (Cloud, Jina embeddings)

| Metric | Keyword only | Hybrid |
|---|---|---|
| Answer in the top 5 | 60% | 100% |
| Precision@5 | 0.47 | 0.90 |
| nDCG@10 | 0.36 | 0.76 |
| Zero results | 0% | 0% |
| Cross-language questions, answer in the top 5 (9 questions) | 22% | 100% |

How the hybrid design got there, on the same 20 questions:

| Setup | Cross-language, answer in top 5 | nDCG@10, all questions |
|---|---|---|
| Keyword only | 22% | 0.36 |
| Hybrid, two lists (keyword + semantic), E5-small, local | 22% | 0.53 |
| Hybrid, two lists, Jina v5, Cloud | 44% | 0.64 |
| Hybrid, three lists (adds semantic on internal documents only), Jina v5, Cloud | 100% | 0.76 |

**Read this with care.** I added the third list after seeing the results on these same 20 questions, so the set was used both to tune and to score. Most cross-language questions also have an internal document as their answer, which the third list favours. The direction is real; the size of the gain will be smaller on fresh questions. Say that if asked. A pilot needs a larger set and a part of it held back.

## What the tests changed in the design

1. **Embedding model.** E5-small could not match a French or Italian question to the German directive (semantic rank beyond 100). Jina v5 brought it to about rank 10. The default endpoint is now Jina v5 on the Elastic Inference Service.
2. **Three result lists.** Law articles exist in up to four languages, and each version takes a place in the list. A separate semantic list for internal documents brought the directive to rank 1 or 2.
3. **Chunk size.** 80-word chunks instead of 250 did not help with E5-small. The default stayed.
4. **FINMA circulars dropped.** FINMA's site terms require written consent for reproduction. The dataset is federal law from Fedlex plus synthetic documents.
5. **Agent instructions.** Shorter answers (150 words, six bullets) cut the response time from 66 to about 40 seconds. A rule to state memos and temporary rules first made the permission moment clear.
6. **Agent retrieval.** The agent's built-in index search tool writes its own queries. It does not use the three-list query from `elastic/queries.py`. It found the right documents in every test, helped by the instruction to search in the question's language and in German.

## Confirmed by you on your Mac and in Kibana (14 November)

| # | Test | Result |
|---|---|---|
| C1 | `scripts/setup.sh security` and `scripts/preflight.sh` from your Mac, with the two users' own passwords | Pass, all nine checks |
| C2 | Login to Kibana as `relationship_manager` | Failed at first with "Application not found": the role lacked the Elasticsearch home page. Fixed by adding `enterpriseSearch: read` to the role. Then pass |
| C3 | Agent, French question A, as admin, after the instruction change | Pass. The interim rule from the confidential memo comes first, cited |
| C4 | Agent, French question A, as `relationship_manager` | Pass. Same requirements from W-12 v3.0, no interim rule, no memo in the sources, no hint that a memo exists |

One earlier run as admin showed the model holding the memo back by its own choice and saying so. The agent's instructions now state that access control is done by the system and that every returned document may be used.

## Not tested: do these first

| # | Untested | Risk | Where |
|---|---|---|---|
| U1 | Logging in to Kibana as `compliance_officer`, and opening Dev Tools as either demo user | Low. The relationship manager login and agent chat work (see below) | `SETUP.md` 4 |
| U2 | The agent's answer to question B (the German one) as each of the two users, side by side | Low. Question A is confirmed for both views (see below) | `RUNBOOK.md` |
| U4 | The backup question's agent answer | Low | `RUNBOOK.md` |
| U5 | How many agent answers the trial's LLM limit allows | Unknown. Four answers worked | `FALLBACK.md` |
| U6 | Click names in the runbook | Low. Correct them in your first walk-through | `RUNBOOK.md` |
| U7 | `local-stack/` on a Mac, and the local stack after my last script changes | Low. Plan B only | `SETUP.md` 9 |
| U8 | Article references inside the synthetic documents against the real law texts | Low for the demo. The agent cites what the documents say | `data/internal/` |
| U9 | The 12 minutes with you speaking | Rehearse with a timer at least three times | `RUNBOOK.md` |
