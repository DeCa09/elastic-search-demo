# Q&A preparation

Ten minutes of questions. The panel scores composure, honesty and depth.

**How to answer.** Repeat the concern in one sentence. Answer in 2 to 4 sentences, answer first. Then check: "Does that answer it?"

**When you do not know:** "I do not know that for certain and I would rather not guess. I will confirm it by tomorrow." The panel are Elastic employees. A confident wrong statement about their product is the worst outcome.

**Your strongest card is the measurement.** You ran a judged test, found that the small embedding model failed across languages, and changed the design. Tell that story whenever relevance comes up. It shows method, not marketing.

Product facts are from Elastic's docs, checked on 14 November 2026 (`SOURCES.md`). Do not quote prices from memory.

---

## COO / executive sponsor (RVP)

**What does this cost?**
Three things drive the cost: the size of the deployment, which follows the number of documents and queries; the embedding model; and LLM tokens per answer. For 400 users and a policy library this is a small deployment. I will not give a number before the pilot has measured real usage. The pilot is sized to stay small on purpose.

**CHF 750,000 a year is a nice number. Why should I believe it?**
You should test it, not believe it. It rests on 150 frequent users, four questions a week and 30 minutes saved, and I already count only half. In the pilot we time real questions before and after with your compliance team. If the saving is 10 minutes instead of 30, you will see that after six weeks, not after a year.

**What happens when the assistant gives a wrong answer to a relationship manager?**
The design assumes it can happen. The agent may only answer from documents it retrieved, it must cite document and section, and it must say "not found" when the sources are silent. The citation is the control: the adviser clicks through to the directive. For high-risk topics we can route the answer to compliance for review instead of showing it directly.

**Why not wait for Microsoft to solve this in Copilot?**
Copilot is strong inside Microsoft 365, and you will probably use it there. Your compliance knowledge is wider: federal law, regulator publications, policy versions, restricted memos. You need to control and measure relevance on those, and to decide where data and model run. The two can coexist: the agent has an API, so it can be called from Teams.

**How fast can we be live?**
A pilot with the compliance team in six weeks: two weeks to connect sources and build the test set, two to tune, two to run with users. The longest lead time is usually not technology. It is agreeing who may see what.

---

## Head of Compliance (Senior Manager SA)

**How do I know it uses the current version of a policy?**
Every document carries its validity dates and a flag for "in force". The search filters on that flag, so superseded versions are not retrieved unless someone asks for history. In the demo I showed the old version of the outsourcing directive ranking first without the filter and disappearing with it. The agent's sources list shows the valid-from date.

**Can it interpret the law for us?**
No, and it should not. It finds the relevant articles and directives and summarises what they say, with citations. Interpretation and the decision stay with your team. I would put that sentence in the user guidance on day one.

**What if a rule exists only in German and someone asks in Italian?**
That is the case the design is built for. The semantic search works on meaning across languages, and the agent answers in the language of the question while citing the German source. I measured this on a test set. With a small embedding model it failed in most cases; with the stronger multilingual model it worked. So the model choice is tested, not assumed. See `eval/RESULTS.md` for the numbers.

**Who maintains this? My team has no engineers.**
Your team owns two things only: which documents are in scope, and the test questions with their correct answers. Platform engineering runs the ingestion. When a new directive is published it is indexed with its metadata, and the old version is marked as superseded.

**Can I see what people ask?**
Yes, if your works council and data protection officer agree. Queries can be logged and analysed: frequent questions, questions with no good answer. That list tells you where a policy is missing or unclear. I would anonymise it by default.

---

## CISO (Director SA)

**How do you guarantee the restricted memo never appears for the wrong person?**
Access is enforced in Elasticsearch with document-level security, not in the prompt and not in the application. A user's role carries a filter built from their groups, and every query runs with it, including the agent's searches. Elastic's docs state that agent tools execute with the privileges of the current user. A document the user may not read is never retrieved, so the LLM never sees it.

**Where do the groups come from? You typed them by hand.**
In the demo, yes: two users with a `groups` attribute. In production the groups come from your identity provider through SAML or OIDC role mapping, and the role uses a template on the user's attributes. So there is one role, not one per group. Source permissions are synced with the documents; Elastic's SharePoint connector supports that, and I would verify the details for your SharePoint version in the workshop.

**Where is the data, and where does the LLM run?**
The index is in the region you choose. Elastic Cloud Hosted has an AWS Zurich region. Embeddings can be computed inside your deployment, or on the Elastic Inference Service, which has EU regions. The managed LLM is configured for zero data retention according to Elastic's documentation, but it uses third-party model providers. If that is not acceptable, you connect your own model, including one you host yourself.

**Does our data train a model?**
No. Elastic's model table states "No" for training use for every managed model. Retention differs per model, so we would select one listed with zero days and an EU region, and write that into the security concept.

**What about prompt injection, a document that tells the AI to ignore its rules?**
It is a real risk for any retrieval system. Three controls here: the agent can only read, it cannot act; it only sees documents the user may already read, so an injection cannot widen access; and internal documents come from controlled sources. For external content I would add scanning at ingest. I would not claim it is solved.

**Is there an audit trail?**
Elasticsearch has audit logging for authentication and data access, and conversations are stored per user. What you keep and for how long is a policy decision. I would confirm the exact audit events for agent conversations before promising a specific report.

**Can an administrator see everything?**
A superuser can, as in any system. You limit that with separate admin roles, audit logging of admin access, and, where needed, a separate deployment or space for the most sensitive material.

---

## Lead Platform Engineer (Principal SA)

**Walk me through the mapping.**
Strict mapping. One keyword-search text field per language with its own analyzer: German with a dictionary decompounder, normalisation and a light stemmer; French and Italian with elision, stemmer and accent folding. One `semantic_text` field fed by `copy_to` from the original text. Keyword fields for language, document type, validity, access groups, and a date for valid-from.

**Why one field per language instead of one analyzer?**
Because stemming and stop words are language-specific, and a German decompounder would damage French tokens. An ingest pipeline detects the language with the built-in identification model and copies the text into the right field. The declared language from the source is the fallback when detection is unsure.

**How do you chunk?**
Laws are split by article before indexing, because the article is the unit people cite. Inside a record, `semantic_text` chunks by sentence up to 250 words with one sentence overlap, which is the default. I tested 80-word chunks; it did not help. I would test section-level records for long policies next.

**Which embedding model, and why?**
I started with the built-in multilingual E5-small because it runs inside the deployment. On my judged set it did well within one language and badly across languages: a French question did not find the German directive. The stronger multilingual model on the Elastic Inference Service is the default for `semantic_text` on current Hosted versions. My conclusion: choose the model by measurement on your own questions, and keep the endpoint configurable.

**Why RRF and not a weighted score?**
BM25 scores and vector similarities are on different scales, and they shift with the corpus. RRF only uses ranks, so there is nothing to calibrate, which suits a pilot. Once we have a judged set of a few hundred questions, a linear combination or a reranker may do better, and we can measure that.

**Would you add a reranker?**
Probably, as a second stage on the top 50. Elastic has a `text_similarity_reranker` retriever and multilingual rerankers on its inference service. It adds latency and cost per query, so I would add it only if the test set shows a gain.

**How did you evaluate?**
Twenty hand-judged questions in four languages, three kinds: same-language keywords, same-language questions, cross-language questions. Metrics: answer in the top 5, precision at 5, nDCG at 10, zero-result rate. It is small. It is enough to catch a wrong model choice, and it did.

**How does this scale to millions of documents?**
Vectors dominate memory. The levers are quantisation, which Elasticsearch supports for dense vectors, fewer dimensions, and filtering before the vector search. The keyword side scales as Elasticsearch always has. For a policy library this is far from any limit; for the whole bank's documents I would size it on a sample.

**Document-level security and vector search: any catch?**
Elastic documents no limitation for `semantic_text` or retrievers. Two documented points: `multi_match` cannot use field wildcards under document-level security, so I list the fields; and relevance scores are computed without the role filter. In my test the restricted memo never appeared for the restricted user in keyword, semantic or hybrid search.

**Playground or Agent Builder?**
Agent Builder. Playground is deprecated since 9.4 and removed in 9.6. The agent in the demo is a custom agent with one index search tool and instructions that force grounding and citations. It is created through the Kibana API, so it is versioned like code.

**What did not work?**
Three things. E5-small failed across languages. FINMA circulars could not be used because FINMA's site terms require written consent for reproduction, so the dataset is federal law only. And the hyphenation decompounder needs a pattern file on every node, so I used the dictionary decompounder with a small domain word list.

---

## Why not a standalone vector database?

A vector database does one part well: storing and searching vectors. Your problem has five parts: exact keyword search for article numbers and names, language analysis, vectors, permissions per document, and an agent. With a vector database the other four are separate products that you integrate, secure and keep in sync. Here they are one engine and one access model. If you already ran a vector database at scale I would look at keeping it; you do not.

## Why not Microsoft Copilot or another SaaS enterprise assistant?

They are quick to start and convenient where your content already lives in their suite. Three differences for a bank. Control of relevance: here you can see and tune how results are ranked and measure it on your own questions. Scope: regulation, versioned policies and restricted memos from several systems, with one permission model. Choice: region, embedding model and LLM are your decision, including a model you host. I would position this as the specialist system for compliance knowledge, reachable from the tools people already use.

## Why not just improve the intranet keyword search?

You should, and this does: the keyword side here has proper analysis for German, French and Italian. But keyword search cannot answer a French question from a German document, and it cannot answer a question asked in everyday words. On my test set, keyword search and hybrid search tie on keyword queries and differ on questions.

---

## Social proof: real Elastic customers

Numbers are quoted from elastic.co. Read the pages again before the interview.

| Customer | What Elastic's page says | Use it for | Link |
|---|---|---|---|
| **EY** | "EY puts Elastic at the heart of GenAI experience for financial sector". "Approximately 10-15% gains in accuracy across various document and extraction methods". "Elastic's RAG setup was able to produce results 3 times faster when compared to Native RAG approaches". | RAG on documents in financial services. | https://www.elastic.co/customers/ey |
| **Docusign** | "Docusign uses generative AI to accelerate agreement management with Elastic". "Traditionally, this could take hours. With Navigator and Elasticsearch, it now takes less than a minute". | Time per question on legal-style documents. | https://www.elastic.co/customers/docusign |
| **BBVA** | "BBVA transforms global banking operations with Elasticsearch". "10x improvement in query response times". "serving 80 million customers across more than 25 countries". | A large European bank trusts Elasticsearch at scale. Say clearly it is a search story, not a GenAI story. | https://www.elastic.co/customers/bbva |

---

## Land and expand

**Land (6 weeks): compliance.** Thirty users. Regulation plus the policy library, with permissions. A judged question set built from real questions. Success criteria agreed up front: 80% of test questions answered in the top 5, a clean permission test, time per question halved. Sponsor: COO. Champion: Head of Compliance. Gatekeeper to win early: CISO.

**Expand (two quarters): the people who ask compliance.** Relationship managers first, then IT support and onboarding, each with their own sources. Every new group adds users without adding a new system. The agent moves into the intranet and Teams through its API.

**Platform (later): company-wide knowledge.** One search and one permission model for the bank's knowledge. The same platform and skills also run observability and security. Mention it once as an option. This presentation is about search.

**Why this order works:** the first users are the ones with the pain and the authority to judge answers; every step reuses the index, the access model and the test method.

---

## Questions to ask the panel

- "As the Albisgrat team: what would you need to see after six weeks to extend this to the relationship managers?"
- "Which worries you more, a wrong answer or a leaked document?"
- Out of role, at the end: "Where do search and GenAI projects in the DACH region most often get stuck after a good demo?"
