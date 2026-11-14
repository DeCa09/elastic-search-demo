# Setup

**Where things stand (14 November 2026).** Your Elastic Cloud Hosted deployment `albisgrat-demo` already holds the finished demo: index, 1,281 documents, role, two users and the agent. I built and tested it there. What is left for you is about 30 minutes: get the project on your Mac, set your own passwords for the two demo users, log in as each, and rehearse.

Steps marked ⚠️ are things I could not test from my side.

## What exists

| Piece | Name | Made by |
|---|---|---|
| Index | `albisgrat-knowledge`, strict mapping, 1,281 documents | `scripts/setup.sh index` and `ingest` |
| Ingest pipeline | `albisgrat-knowledge-ingest`: language detection, routing to the per-language field | `scripts/setup.sh index` |
| Embeddings | `semantic_text` field on `.jina-embeddings-v5-text-small` (Elastic Inference Service) | index mapping |
| Role | `albisgrat_knowledge_reader`: document-level security from the user's `groups` | `scripts/setup.sh security` |
| Users | `compliance_officer` (groups `all_staff`, `compliance`), `relationship_manager` (groups `all_staff`, `front_office`) | `scripts/setup.sh security` |
| Agent | "Albisgrat Compliance Assistant" with one search tool on the index | `scripts/setup.sh agent` |

## 0. The trial clock

You started the trial on **14 November 2026**. It runs 14 days, so until about **28 November**. The interview is on Tuesday 24 November, day 11. That leaves 4 days of margin.

The observability demo can use the same trial: a trial includes one Hosted deployment (this one) and three Serverless projects.

LLM usage is limited during the trial and the limit is not published. One agent answer used about 45,000 input tokens in my tests. Rehearse the agent part a handful of times, not dozens.

## 1. Get the project on your Mac

```bash
git clone https://github.com/DeCa09/elastic-search-demo.git
```

```bash
cd elastic-search-demo
```

You need `python3` (3.9 or newer, standard library only) and `curl`. No Docker is needed for the Cloud demo.

## 2. Fill in `.env`

```bash
cp .env.example .env
```

| Variable | Value |
|---|---|
| `KIBANA_URL` | Your Kibana endpoint, without a trailing slash |
| `ELASTICSEARCH_URL` | Your Elasticsearch endpoint. Remove `:443` at the end if it is there |
| `ELASTIC_API_KEY` | The encoded value of your `demo-setup` API key. If you no longer have it, create a new key in **Stack Management > API keys** |
| `INFERENCE_ID` | Leave `.jina-embeddings-v5-text-small` |
| `COMPLIANCE_OFFICER_PASSWORD` | A password you choose, at least 8 characters |
| `RELATIONSHIP_MANAGER_PASSWORD` | Another password you choose |

Never put these values in a document or a chat.

## 3. Set your passwords for the two demo users

The users exist, but with random passwords I generated and did not keep for you. This command sets yours:

```bash
scripts/setup.sh security
```

Then check everything:

```bash
scripts/preflight.sh
```

Green means the index, the embedding model, both users, the agent and the demo queries all work from your Mac.

## 4. Log in as the two users

Both logins and the agent chat were confirmed on 14 November. Still to check: Dev Tools for both users.

1. Open a **second browser** (or a private window) and go to your Kibana URL.
2. On the login page choose **Log in with Elasticsearch** (not the Elastic Cloud login). User `relationship_manager`, your password.
3. In a third window or another browser profile, do the same as `compliance_officer`.
4. In each window check two things:
   - **Dev Tools > Console** opens. Run `GET _security/_authenticate`. You see the username and, under `metadata`, the groups.
   - The **AI Agent** chat opens (button in the top bar) and the agent **Albisgrat Compliance Assistant** can be selected.

If the agent chat is missing or the agent is not listed for these users, the role needs a wider Kibana privilege. In `elastic/setup_search.py`, function `role_body`, change `"agentBuilder": ["read"]` to `"agentBuilder": ["all"]` and run `scripts/setup.sh security` again. Tell me if that happens so the kit is corrected.

## 5. Try the four moments

Search moments, in the terminal:

```bash
scripts/ask.sh keyword "Qui doit donner son accord avant de confier des données de clients à un prestataire informatique externe ?" --as relationship_manager
```

```bash
scripts/ask.sh hybrid "Qui doit donner son accord avant de confier des données de clients à un prestataire informatique externe ?" --as relationship_manager
```

The keyword search returns French documents only. The hybrid search puts the German "Weisung W-12" first.

The same queries for Kibana are in `demo/console-queries.md`. The agent questions are in `RUNBOOK.md`.

## 6. Evaluation

```bash
scripts/evaluate.sh
```

It runs the 20 judged questions in `eval/judged_queries.json` with keyword-only and hybrid search and writes `eval/RESULTS.md`. Result on your deployment on 14 November: answer in the top 5 for 60% (keyword) against 100% (hybrid).

## 7. Reset

```bash
scripts/reset.sh
```

Deletes the index and rebuilds everything: pipeline, index, documents, role, users, agent. On your deployment the rebuild of the index took 27 seconds. Use it if you changed documents or broke something. You do not need it between rehearsals: the demo changes no data.

## 8. Rebuilding from nothing

If the deployment is lost, create a new **Hosted** deployment (the sign-up flow pushes Serverless; the Hosted form is at https://cloud.elastic.co/deployments/create), update `.env`, and run:

```bash
scripts/setup.sh all
```

Hosted, not Serverless, because Hosted has built-in users. The permission moment needs two logins, and on Serverless a second login means a second Elastic Cloud account.

To refresh the law texts from Fedlex (not needed; the texts are in `data/public/fedlex.jsonl`):

```bash
python3 data/fetch_public.py
```

## 9. Plan B: local stack

`local-stack/docker-compose.yml` starts Elasticsearch and Kibana 9.5.6 in Docker with a local trial licence. Create `local-stack/.env` with `ES_LOCAL_PASSWORD`, `KIBANA_LOCAL_PASSWORD` and `KIBANA_ENCRYPTION_KEY`, run `docker compose up -d` in that folder, then point `.env` at `http://localhost:9200` and `http://localhost:5601` with `INFERENCE_ID=.multilingual-e5-small-elasticsearch`.

Two limits, both measured: the local E5 model is weak across languages (the French question does not find the German directive), and there is no LLM, so the agent cannot answer. Use it only to work on mappings or scripts offline.

## 10. After the interview

```bash
scripts/setup.sh delete
```

Then delete the deployment in the Elastic Cloud console. The trial ends by itself and costs nothing.

## Files

| File | Purpose |
|---|---|
| `data/public/fedlex.jsonl` | 1,255 law articles with source URLs |
| `data/internal/*.json` | 26 fictional internal documents |
| `data/fetch_public.py` | Downloads and splits the law texts |
| `elastic/setup_search.py` | Index, pipeline, ingest, role, users, agent |
| `elastic/queries.py` | The keyword and hybrid queries |
| `demo/console-queries.md` | The same queries for Kibana Dev Tools |
| `demo/demo_queries.json` | The demo questions |
| `eval/` | Judged questions, evaluation script, results |
| `scripts/` | `setup.sh`, `reset.sh`, `preflight.sh`, `ask.sh`, `evaluate.sh` |
