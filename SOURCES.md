# Sources

Checked on 14 November 2026. Verification levels:

- **Page**: read on the published elastic.co page.
- **Repo/Spec**: read in Elastic's public docs source or the Kibana OpenAPI specification.
- **Tested**: I ran it. `TEST_LOG.md` says where.
- **Unverified**: could not be confirmed. Check before you rely on it.

Short form: `docs` = https://www.elastic.co/docs

## Trial and deployment type

| Fact | Level | Source |
|---|---|---|
| The trial lasts 14 days and includes one Hosted deployment and three Serverless projects. No credit card. | Page | docs/deploy-manage/deploy/elastic-cloud/create-an-organization, https://www.elastic.co/cloud/cloud-trial-overview |
| "Trial deployments run on the latest version of the Elastic Stack." "Machine learning nodes are available up to 4GB RAM." | Page | same docs page |
| "Token usage for LLMs and other ML models is restricted during the trial period." No number is published. | Page | same docs page |
| Serverless has no native users: "user authentication is managed at the Elastic Cloud organization level". A second user means inviting a second organisation member. Hosted has native users (`POST /_security/user/<name>`). | Page | Serverless FAQ; docs/deploy-manage/users-roles |
| Hosted has an AWS Zurich region, `aws-eu-central-2`. | Page | docs/reference/cloud/cloud-hosted/regions |

## Semantic search

| Fact | Level | Source |
|---|---|---|
| `semantic_text` default endpoint: "On Elastic Cloud Hosted deployments running Elastic Stack 9.4+ and on Serverless, the inference_id parameter defaults to .jina-embeddings-v5-text-small and runs on EIS." The docs advise pinning `inference_id` because the default can change. | Page | docs/reference/elasticsearch/mapping-reference/semantic-text-setup-configuration |
| Default chunking: "documents are split into sentences and grouped in sections up to 250 words with 1 sentence overlap". Configurable with `chunking_settings`. | Page | docs/explore-analyze/elastic-inference/inference-api |
| Querying: "Match query: The recommended method for querying semantic_text fields." The `semantic` query is called legacy. | Page | docs/reference/elasticsearch/mapping-reference/semantic-text-search-retrieval |
| ELSER is English-only: "If you want to perform semantic search on non-English language documents, use the E5 model." | Page | docs/explore-analyze/machine-learning/nlp/ml-nlp-elser |
| `.multilingual-e5-small-elasticsearch` is a preconfigured endpoint "recommended for non-English language texts". It runs on ML nodes. | Page | docs/explore-analyze/elastic-inference/inference-api |
| Elastic Inference Service (EIS) offers multilingual Jina embedding models (`jina-embeddings-v5-text-small`, `-nano`, `jina-embeddings-v3`), EU region available, data retention 0 days. | Page | docs/explore-analyze/elastic-inference/eis-supported-models |
| E5-small ranks a German policy poorly for a French or Italian question in this corpus (cross-language success@5: 22%). | Tested | `TEST_LOG.md` |
| With `.jina-embeddings-v5-text-small` and three fused result lists, cross-language success@5 is 100% on the 20-question set. | Tested on Cloud | `TEST_LOG.md` |

## Hybrid retrieval

| Fact | Level | Source |
|---|---|---|
| `rrf` retriever: child `retrievers`, `rank_constant` (default 60), `rank_window_size` (default 10). | Page + Tested | docs/reference/elasticsearch/rest-apis/retrievers/rrf-retriever |
| Hybrid with `semantic_text`: a `standard` retriever with `match` on the semantic field next to a `standard` keyword retriever. | Page + Tested | docs/solutions/search/hybrid-semantic-text |
| RRF needs the Enterprise subscription level (included in the trial). | Page | https://www.elastic.co/subscriptions |
| `_rank_eval` with a `retriever`: not documented. The evaluation here is a small Python script instead. | Repo/Spec | Elasticsearch API specification |

## Language handling

| Fact | Level | Source |
|---|---|---|
| "A language identification model is provided in your cluster, which you can use in an inference processor of an ingest pipeline by using its model ID (lang_ident_model_1)." | Page + Tested | docs/explore-analyze/machine-learning/nlp/ml-nlp-lang-ident |
| Built-in `german`, `french`, `italian` analyzers: stop words, light stemmer; French and Italian add elision; none includes a decompounder or `asciifolding`. | Page | docs/reference/text-analysis/analysis-lang-analyzer |
| `dictionary_decompounder` works with an inline `word_list`. `hyphenation_decompounder` needs a pattern file on every node (on Hosted: a bundle upload). | Page | same section |
| Language detection agreed with the declared language for all 1,281 documents. | Tested | `TEST_LOG.md` |

## Document-level security

| Fact | Level | Source |
|---|---|---|
| Roles take a `query` per index; the query can be a template using `{{_user.metadata...}}`. Platinum or Enterprise level. | Page + Tested | docs/deploy-manage/users-roles/cluster-or-deployment-auth/controlling-access-at-document-field-level |
| With document-level security, "the multi_match query does not support specifying fields using wildcards". The queries here list fields one by one. | Page | same page |
| No documented limitation for document-level security with `semantic_text` or retrievers. In the test, a restricted document never appeared for the restricted user in keyword, semantic or hybrid search. | Tested | `TEST_LOG.md` |

## The chat experience

| Fact | Level | Source |
|---|---|---|
| "Playground was deprecated in Elastic Stack 9.4 and removed in 9.6. It is unavailable in Elastic Serverless. Use Agent Builder (generally available since 9.3) instead." | Page | docs/solutions/search/rag/playground |
| Agent Builder: custom tools of type `index_search`, `esql`, `workflow`, `mcp`; custom agents with instructions and a tool list; APIs `POST /api/agent_builder/tools`, `/agents`, `/converse`, `/converse/async`. The default model on the trial deployment was `anthropic-claude-5-sonnet`. | Repo/Spec + Tested on Cloud | Kibana OpenAPI specification |
| "Tools execute Elasticsearch requests with the privileges of the current user or API key." | Page | docs/explore-analyze/ai-features/agent-builder/permissions |
| Kibana feature privilege for chat: `agentBuilder` (read). Elasticsearch cluster privilege `monitor_inference` for the managed LLM. | Page + Tested (role accepted) | same page |
| "Agent Builder uses Elastic Managed LLMs running on the Elastic Inference Service (EIS)… requires zero setup." | Page | docs/explore-analyze/ai-features/agent-builder/models |
| Managed LLM: "The LLMs are configured for zero data retention: none of the prompts or outputs are stored by the service provider." Some individual models in the supported-models table list a longer retention, so check the model you select. | Page | docs/reference/kibana/connectors-kibana/elastic-managed-llm, eis-supported-models |
| Own LLM: inference endpoints of type `chat_completion` for OpenAI, Azure, Amazon Bedrock, Google, Mistral, Anthropic and OpenAI-compatible local servers. The older LLM connectors are deprecated. | Page | docs/explore-analyze/ai-features/llm-guides/llm-connectors |

## Data

| Fact | Level | Source |
|---|---|---|
| Law texts come from Fedlex, the publication platform for Swiss federal law. Each record keeps its source URL. | Tested | https://www.fedlex.admin.ch, `data/fetch_public.py` |
| Swiss acts and ordinances are not protected by copyright (Copyright Act, SR 231.1, Art. 5 para. 1 let. a). | Unverified wording | Read Art. 5 on https://www.fedlex.admin.ch/eli/cc/1993/1798_1798_1798/de before you rely on it |
| FINMA circulars are **not** in the dataset. FINMA's legal notice says: "Für die Reproduktion jeglicher Elemente ist die schriftliche Zustimmung der Urheberrechtsträger im Voraus einzuholen." Internal documents mention a circular by name only. | Page | https://www.finma.ch/de/rechtliches/ |
| Laws used: Data Protection Act (SR 235.1), Data Protection Ordinance (235.11), Anti-Money Laundering Act (955.0), Banking Act (952.0), FINMA Anti-Money Laundering Ordinance (955.033.0). German, French, Italian; English where Fedlex has it. | Tested | `data/public/fedlex.jsonl` |
| The 26 internal documents are synthetic. The bank "Privatbank Albisgrat AG" is invented; a name search in the Swiss commercial register (zefix.ch) on 14 November 2026 found no such company. The article references inside the synthetic documents were not checked against the law texts. | Tested (name search) | `data/internal/` |

## Customer stories (quoted from the pages)

| Customer | What the page says | Source |
|---|---|---|
| EY | "EY puts Elastic at the heart of GenAI experience for financial sector". "Approximately 10-15% gains in accuracy across various document and extraction methods". "Elastic's RAG setup was able to produce results 3 times faster when compared to Native RAG approaches". | https://www.elastic.co/customers/ey |
| Docusign | "Docusign uses generative AI to accelerate agreement management with Elastic". "Traditionally, this could take hours. With Navigator and Elasticsearch, it now takes less than a minute". | https://www.elastic.co/customers/docusign |
| BBVA | "BBVA transforms global banking operations with Elasticsearch". "10x improvement in query response times". "serving 80 million customers across more than 25 countries". A search story, not a GenAI story. | https://www.elastic.co/customers/bbva |

These three were read by a research pass on 14 November 2026. Read the pages again before the interview and use the numbers exactly as written.
