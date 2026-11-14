# Elastic search and GenAI demo kit

Everything for the Elastic Solutions Architect panel interview (**Tuesday 24 November 2026, 13:00 to 14:00 CET**): a multilingual, permission-aware compliance assistant for a fictional Swiss private bank, built on Elasticsearch, with a 12-minute runbook, a deck outline, an architecture diagram, an evaluation and Q&A preparation.

This kit is independent of the observability demo in `DeCa09/elastic-panel-demo`.

**Story:** a relationship manager in Geneva asks in French about a rule that exists only in a German directive. Keyword search misses it. Hybrid search finds it. The AI agent answers in French with citations. A compliance officer asking the same question gets one more source: a confidential memo the relationship manager never sees.

## Read in this order

| File | What it is |
|---|---|
| `README.md` | This page: status, decisions, open points |
| `SETUP.md` | What exists on your deployment and the 30 minutes left for you |
| `RUNBOOK.md` | The 12-minute demo, minute by minute, with talk track, German terms and the questions |
| `FALLBACK.md` | What to do when something fails; how to record the backups |
| `DECK.md` | 10-slide outline with speaker notes, timings and the value table |
| `QA_PREP.md` | Questions per panel role, alternatives, customer stories, land and expand |
| `eval/RESULTS.md` | Keyword vs hybrid on 20 judged questions |
| `diagrams/architecture.svg` | Architecture diagram for slide 4 |
| `SOURCES.md` | Every product fact with its source |
| `TEST_LOG.md` | What was run, where, and what is untested |

## Decisions, and what changed from the brief

| Topic | Decision | Why |
|---|---|---|
| Deployment | **Elastic Cloud Hosted**, AWS Frankfurt, 9.5.6. Trial started 14 November, runs to about 28 November | Hosted has built-in users, which the two-login permission moment needs. Serverless has none |
| RAG experience | **Agent Builder**: a custom agent with one index search tool | Playground is deprecated (9.4) and removed (9.6). The AI Assistant is deprecated too |
| Embedding model | **`.jina-embeddings-v5-text-small`** on the Elastic Inference Service | ELSER is English-only. The built-in E5-small failed the cross-language test |
| Retrieval | RRF over **three** lists: keyword, semantic, semantic on internal documents only | With two lists the German directive was buried under four language versions of the same law articles |
| Public data | Swiss federal law from **Fedlex** only: data protection, anti-money laundering, banking | FINMA's site terms require written consent for reproduction, so no FINMA circulars |
| Customer | "Privatbank Albisgrat AG", invented | No such company in the Swiss commercial register on 14 November 2026 |
| Permissions | One role with a templated document filter, two users with `groups` | Scales to a directory without one role per group |

## The four demo moments, as tested on Cloud

1. **Keyword fails.** French question, five French results, the German directive is absent.
2. **Hybrid finds it.** Same question: "Weisung W-12" version 3.0 at rank 1.
3. **Answer with citations.** The agent answers in French in about 40 seconds, each point cited to a section of the German directive.
4. **Permissions.** At search level the restricted memo is rank 1 for the compliance officer and absent for the relationship manager. With full access the agent leads with the memo's interim rule.
5. **Versions (extra).** The withdrawn version 2.0 ranks first until the validity filter is on.

## Evaluation

20 hand-judged questions in German, French, Italian and English.

| | Keyword only | Hybrid |
|---|---|---|
| Answer in the top 5 | 60% | 100% |
| nDCG@10 | 0.36 | 0.76 |
| Cross-language questions, answer in the top 5 | 22% | 100% |

Small set, and the retrieval was tuned on it. It shows direction, not proof. Details in `TEST_LOG.md`.

## Not tested

- Logging in to Kibana as the two demo users, and the agent chat under their role.
- The agent's answer when the relationship manager asks (it must leave out the memo).
- How many agent answers the trial's LLM limit allows. Four worked.

`SETUP.md` step 4 covers the first two. Do it first.

## Quick start on your Mac

```bash
cp .env.example .env        # then fill it in, see SETUP.md step 2
```

```bash
scripts/setup.sh security
```

```bash
scripts/preflight.sh
```

## Rules of this project

- Secrets live only in `.env`, which git ignores.
- The trial is free. The agent uses Elastic's managed LLM within the trial's limit. Nothing here costs money unless you subscribe or connect a paid model of your own.
- Law texts keep their Fedlex source URLs. Internal documents are fictional and say so in their first line.
