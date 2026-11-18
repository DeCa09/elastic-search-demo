# Second demo: a company brain on Elasticsearch

The first demo answers questions from documents. This one shows an agent that knows **where the bank's knowledge lives and what its terms mean** before it searches. It uses Elastic's AI Index and Knowledge Indicators, as described in the Elasticsearch Labs article "Building context in Elasticsearch: how AI Indices power smarter agents using fewer tokens" (11 August 2026).

**In one sentence:** the same bank, three data sources instead of one, and a layer of pre-computed context that lets the agent answer with a third of the tokens in half the time.

It runs on a separate **Elasticsearch Serverless** project (`albisgrat-brain`), because AI Indices exist only on Serverless today. The first demo on the Hosted deployment is not touched.

## What is in it

| Piece | Name | What it is |
|---|---|---|
| Source index | `albisgrat-knowledge` | The first demo's index: 1,255 law articles and 26 internal documents |
| Source index | `albisgrat-outsourcing-inventory` | 24 fictional outsourcing arrangements: provider, data location, approvals, review dates |
| Source index | `albisgrat-incidents` | 43 fictional incidents in 2026, some linked to an arrangement |
| AI Index | `ai-index-idx-albisgrat` | 43 Knowledge Indicators (see below) |
| Workflow | `albisgrat-index-profile-ki` | A Kibana Workflow: reads each index's mapping and samples, asks an LLM for a profile, writes it to the AI Index |
| Tool | `albisgrat.brain.query_ki` | One hybrid ES\|QL query (keyword and semantic, fused) over the AI Index |
| Agent | Albisgrat Company Brain | Reads Knowledge Indicators first, then queries the right index |
| Agent | Albisgrat Baseline (no context) | Same model and data, no Knowledge Indicators. For comparison |

The four kinds of Knowledge Indicator:

| Type | Count | Example | Made by |
|---|---|---|---|
| Index profile | 3 | "The outsourcing inventory holds facts about arrangements, not the rules" | The workflow, with an LLM |
| Policy register | 23 | "W-12: version 3.0 is in force since 1 July 2025; 2.0 is withdrawn" | Script, from the documents' own metadata |
| Glossary | 12 | "outsourcing = Auslagerung = externalisation = esternalizzazione" | Hand-written |
| Business definition | 5 | "A review is overdue when the last review is more than 12 months ago (W-12, section 8)" | Hand-written |

Some inventory rows break the bank's directive W-12 on purpose, so the agent has something to find: OUT-003 and OUT-014 (client data in the EU without board approval), OUT-019 (client data in the US), OUT-002, OUT-007 and OUT-010 (review overdue), OUT-021 (no CISO approval).

## Result

Three questions, in English, German and French. Each needs a structured source and a rule from a policy. "Correct" means the answer names exactly the records computed from the data files.

| | Baseline, no context | With Knowledge Indicators |
|---|---|---|
| Correct answers | 3 of 3 | 3 of 3 |
| Tool calls per question | 6.0 | 4.3 |
| Tokens per question | 176,000 | 60,000 |
| Seconds per question | 51 | 25 |

Details in `RESULTS.md`, full answers in `answers/`.

**Read this with care.**
- Both agents were right. The gain is cost and speed, not accuracy. On three easy-to-check questions a capable model finds its way without help; it just pays for the exploration.
- One run per question. Agents are not deterministic: the baseline's cost ranged from 57,000 to 348,000 tokens.
- On the French question the agent with Knowledge Indicators made more tool calls than the baseline (8 against 6) because it guessed a field name wrong and retried.
- Two of the three "with Knowledge Indicators" runs used hand-written index profiles, one used the profiles the workflow generated. Both gave correct answers.

## Setup

The project `albisgrat-brain` already holds everything. To rebuild it, or build it elsewhere:

1. Create an **Elasticsearch Serverless** project and an API key in it.
2. Add three lines to `.env`:

   | Variable | Value |
   |---|---|
   | `BRAIN_ELASTICSEARCH_URL` | The project's Elasticsearch endpoint |
   | `BRAIN_KIBANA_URL` | The project's Kibana endpoint |
   | `BRAIN_API_KEY` | The encoded API key |

3. Build it:

```bash
scripts/brain.sh all
```

4. Generate the index profiles with the workflow (about 2 minutes, uses the LLM):

```bash
scripts/brain.sh workflow
```

5. Check:

```bash
scripts/brain.sh status
```

To repeat the comparison (six agent runs; the baseline is expensive):

```bash
scripts/brain.sh compare
```

Add `--only-brain` to skip the baseline. Results from earlier runs are kept.

## A five-minute demo

Log in to the Serverless project's Kibana with your Elastic Cloud account. This demo needs one login only.

| Time | Show | Say |
|---|---|---|
| 0:00 | **Agents > Albisgrat Baseline.** Ask question 1 (below). While it works, open the tool steps. | "Same bank, but now three data sources. This agent knows nothing about them. Watch it explore: list indices, read mappings, try queries." |
| 1:15 | The answer, and the number of steps it took. | "It gets there. It took about ten tool calls and over a minute, and it re-learns all of this for every question." |
| 1:30 | **Discover**, ES\|QL: `FROM ai-index-idx-albisgrat \| KEEP type, title, content \| LIMIT 50` | "This is an AI Index: an ordinary Elasticsearch index with a naming convention. It holds Knowledge Indicators: what each index is for, which policy version is in force, what our terms mean in four languages, how we define 'overdue'." |
| 2:15 | **Workflows > albisgrat-index-profile-ki.** Show the four steps. | "Nobody wrote the index profiles by hand. A Kibana Workflow reads the mapping and a few samples, asks an LLM for a profile, and writes it here. The definitions and the glossary are the part your experts own." |
| 3:00 | **Agents > Albisgrat Company Brain.** Ask the same question 1. | "Same model, same data. This agent reads the Knowledge Indicators first." |
| 3:30 | The answer: OUT-003, OUT-014 and OUT-019 not allowed, OUT-004 allowed, with the section of W-12. The steps: one context lookup, then the queries. | "Three tool calls, about 20 seconds. It applied your rule, section 5 of W-12, to your register." |
| 4:15 | `RESULTS.md` or a slide with the table above. | "Over three questions: the same correct answers, a third of the tokens, half the time. I ran each question once, so this is direction, not proof." |
| 4:45 | | "The first demo was finding and citing documents. This is the step after: a context layer the agents share. It is where the company-wide knowledge platform on the roadmap slide comes from." |

**Question 1 (English):**
```
Which outsourcing arrangements store client data outside Switzerland, and does our directive allow each of them?
```

**Question 2 (German):**
```
Bei welchen aktiven Auslagerungen ist die jährliche Überprüfung überfällig?
```
Expected: OUT-002, OUT-007, OUT-010.

**Question 3 (French):**
```
Quelles violations de la sécurité des données ont été annoncées en retard cette année, et lesquelles concernent un prestataire externe ?
```
Expected: INC-2026-023 and INC-2026-043; the second involves OUT-019.

If you show only one agent to save time, show the Company Brain and quote the baseline's numbers from the table.

## How it compares with Snowflake's Cortex Sense

Same idea: give agents a maintained layer of context instead of letting them explore. Different stage. Going by Snowflake's announcement (30 June 2026), Cortex Sense mines that context automatically from query history, transformation models and BI metrics, ranks conflicting signals and asks a human to settle conflicts. Here the pipeline is built by hand from Elastic's primitives: an index, a workflow, a query. Elastic's article says a setup agent and a feedback loop from agent traces are the production path; they are not part of this demo.

What Elastic adds that fits a bank: the context sits in the same engine as the documents, with the same hybrid search and the same document-level security, in a region you choose.

## Tested and not tested

Tested on the Serverless project (Elasticsearch 9.7.0, 18 November 2026): the three source indices, the AI Index and its 43 Knowledge Indicators, the hybrid query over the AI Index, the workflow (one run, 107 seconds, three profiles written), both agents, and the comparison (seven agent runs).

Not tested:
- The five-minute flow in the Kibana interface. I used the APIs only, so the click names above are my best reading.
- `scripts/brain.sh` from your Mac. The same Python ran from my side.
- Document-level security on this project. This demo uses one login. Permissions are the first demo's subject.
- How much of the trial's LLM allowance is left. The seven agent runs here used about 750,000 tokens, 530,000 of them in the three baseline runs. The workflow run is on top of that and was not measured.

## Honest limits

- The Knowledge Indicators for definitions and glossary are hand-written. That is realistic for a pilot, and it is the maintenance cost of this approach.
- A wrong Knowledge Indicator makes the agent confidently wrong. In production each one needs an owner and a review date.
- AI Indices are Serverless-only today. Elastic's article says they will come to stack releases later.
