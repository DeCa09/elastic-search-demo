# Deck outline: 10 slides, 30 minutes

Format per slide: headline, visual, speaker notes, German key terms, time.
Headlines are full sentences. Someone who reads only the headlines should get the story.

**Every number about Privatbank Albisgrat AG is an assumption.** The bank is invented. Assumptions are marked *(A)* and listed at the end. In the role play, say "as you told us in discovery".

## Time plan

| # | Slide | Minutes | Running total |
|---|---|---|---|
| 1 | Title and panel roles | 1:30 | 1:30 |
| 2 | Customer and pain | 3:00 | 4:30 |
| 3 | Desired outcomes | 1:30 | 6:00 |
| 4 | Architecture | 3:00 | 9:00 |
| 5 | Why Elastic | 2:00 | 11:00 |
| 6 | Live demo | 12:00 | 23:00 |
| 7 | Business value | 3:00 | 26:00 |
| 8 | Roadmap | 2:00 | 28:00 |
| 9 | Next steps | 1:00 | 29:00 |
| | Buffer | 1:00 | 30:00 |
| 10 | Appendix | Q&A only | |

Checkpoints: **in the demo by 11:00, out of it by 23:00.** If you are late at slide 6, shorten slides 8 and 9, never the demo.

Your own introduction before the deck: 90 seconds. Five years building production systems, customer-facing AI/ML work with large enterprises in Switzerland and Germany. One line that earns the room: "I have built multilingual semantic search on Elasticsearch and agentic RAG for a regulator in Europe, so I know where these projects fail: relevance across languages, permissions, and trust in the answer. That is what I will show." Never name that customer.

---

## Slide 1. Title and roles (1:30)

**Headline:** From "ask a colleague in Zurich" to "ask in your own language": a compliance assistant for Privatbank Albisgrat

**Visual:** Title left. Four role cards right.

| Panellist | Role today | You will see |
|---|---|---|
| [RVP name] | COO, executive sponsor | Risk, efficiency, cost |
| [Senior Manager SA name] | Head of Compliance | Your team's day after this |
| [Director SA name] | CISO | Access rights, residency, the LLM |
| [Principal SA name] | Lead Platform Engineer | Ingestion, relevance, scale |

**Speaker notes:** "Thank you for your time. To make this concrete I will treat you as the Albisgrat team we met in discovery. [Name], COO. [Name], Head of Compliance. [Name], CISO. [Name], Lead Platform Engineer. Is that all right? Thirty minutes: what we heard, what we propose, a live demo, the business case, the next step. Please interrupt."

**German:** Vielen Dank für Ihre Zeit. Rollenverteilung. Unterbrechen Sie mich gerne.

---

## Slide 2. Customer and pain (3:00)

**Headline:** Today a compliance question at Albisgrat takes hours, and the answer may come from an outdated policy

**Visual:** The broken process as a flow, with three numbers under it.

```
Question in Geneva (French) → Search SharePoint, intranet, PDF folders → Nothing: the rule is in German
   → E-mail a colleague in Zurich → Wait → Answer, perhaps from the old version
```

- **About 40 minutes** per research question *(A)*
- **3 places** to search, each in one language, none aware of the others
- **2 audit findings** last year where staff used a superseded policy *(A)*

Box "Landscape": about 400 compliance and front-office staff in Zurich, Geneva and Lugano *(A)*; policies written in the language of the author; regulation in German, French and Italian; SharePoint, an intranet and file shares.

**Speaker notes:** "Let me play back what we heard. Correct me. You have about 400 people who need rules every day: regulation, and your own directives. They sit in three places. A directive is written once, in the language of its author. So when a relationship manager in Geneva asks in French, the search finds French documents. The answer is in a German directive from Zurich. She e-mails a colleague and waits. [To Head of Compliance] Your team is that colleague. [To COO] Twice last year, an audit found people working from a superseded policy. [To CISO] And you told us: whatever we build, an internal investigation memo must never appear for someone who should not see it. Did I get that right?"

Pause. Use their corrections later.

**German:** Rechtsfrage, Weisung, veraltete Version, Prüfungsfeststellung, Sprachgrenze, "Habe ich das richtig verstanden?"

---

## Slide 3. Desired outcomes (1:30)

**Headline:** Four outcomes, one for each pain

| Pain today | Outcome you asked for |
|---|---|
| ❌ Three places, each in one language | ✅ One search, across German, French, Italian and English |
| ❌ About 40 minutes per question | ✅ An answer in minutes, in the language of the question |
| ❌ Outdated versions, no proof of source | ✅ Every answer cites document and section; only versions in force |
| ❌ Confidential content must not leak | ✅ Each person sees only what their role allows, enforced by the system |

One line underneath: "And your data stays where you decide."

**Speaker notes:** "So success is this. One place. An answer in minutes, in my language, even if the rule is in another. Every answer traceable to the document and the section, and only from versions in force. [To CISO] And permissions enforced by the engine, not by a prompt."

**German:** Zielbild, Quellenangabe, gültige Fassung, Berechtigungen, Datenhoheit.

---

## Slide 4. Architecture (3:00)

**Headline:** One index, two ways to search it, permissions built in, an AI agent on top

**Visual:** `diagrams/architecture.svg`, full slide, with the four ❌ → ✅ callouts.

**Speaker notes:** Left to right, then the callouts.
- "Sources: Swiss federal law from Fedlex in four languages, and your internal documents. Later, connectors for SharePoint and the intranet bring documents with their permissions."
- "Ingest: a built-in model detects the language of each document. The text goes to the analyzer for that language, so German compounds are split and French elisions are handled. The same text is split into chunks and embedded with a multilingual model. That is one field type in Elastic, `semantic_text`. No separate embedding pipeline."
- "One index holds both: keyword fields per language and the vectors. Plus the metadata that matters to you: version, validity, access groups, source link."
- "Search is hybrid: keyword and semantic results merged with reciprocal rank fusion. [To Engineer] Keyword finds the exact article number. Semantic finds the meaning across languages. RRF needs no score tuning."
- "[To CISO] Document-level security sits in the engine. Every query, including the AI agent's, runs with the rights of the person asking."
- "On top, the AI agent. It may only answer from what the search returned, and it must cite."

Features to name: ingest pipelines with language identification, language analyzers, `semantic_text`, retrievers with RRF, document-level security, Agent Builder, Elastic Inference Service.

**German:** Zielarchitektur, Spracherkennung, hybride Suche, Berechtigungen auf Dokumentebene, KI-Agent.

---

## Slide 5. Why Elastic (2:00)

**Headline:** Why Elastic: relevance, permissions and AI in one platform that runs where you decide

**Visual:** Three columns: the alternative, what it does well, what is missing for Albisgrat.

| Alternative | Good at | The gap for you |
|---|---|---|
| A standalone vector database | Storing and searching vectors | Keyword search, language analysis, document-level permissions and the agent are separate products you integrate and secure |
| A SaaS enterprise assistant | Fast start, good inside its own suite | You do not control relevance, cannot measure it on your questions, and have less choice of data location and model |
| Keyword-only intranet search | Exact terms | Fails across languages and on questions asked in everyday words |

Bottom line: "Elastic: keyword and vector search in one engine, permissions in that engine, an agent on top, in the region and with the model you choose."

**Speaker notes:** "You have three other options. A vector database is good at vectors. But your problem is not vectors. It is article numbers, three languages, permissions and versions, and a vector database leaves those to you. An enterprise assistant gets you started fast. But you cannot tune or measure its relevance on your own questions, and [to CISO] you have less say over where data and model run. Keyword search is what you have. Elastic gives you all of it in one engine. I will show you a measurement, not a claim."

Be fair. Say what each alternative is good at first.

**German:** Relevanz, Berechtigungen, eine Plattform, Datenstandort, Messbarkeit.

---

## Slide 6. Live demo (12:00)

**Headline:** A question from Geneva, in French, about a rule written in Zurich

**Visual:** One sentence and four steps.

> "You will see a French question fail in keyword search, succeed in hybrid search, get an answer with citations, and return different sources for two different people."

Keyword fails → Hybrid finds it → Answer with citations → Same question, two users

**Speaker notes:** Say the sentence. "Everything is live on Elastic Cloud. The law texts are real Swiss federal law. The bank documents are fictional." Follow `RUNBOOK.md`.

**German:** Live-Demo, "Sie sehen gleich...".

---

## Slide 7. Business value (3:00)

**Headline:** Pilot targets: minutes instead of 40, answers across languages, no outdated sources

**Visual:** Before/after table.

| | Today *(A)* | Target with Elastic | Why we believe it |
|---|---|---|---|
| Time per research question | About 40 minutes | About 10 minutes *(A)* | Demo. Docusign: "could take hours… now takes less than a minute" |
| Cross-language questions answered in the top 5 | EVAL_KEYWORD_CROSS | EVAL_HYBRID_CROSS | Our test set of 20 judged questions (`eval/RESULTS.md`) |
| Outdated policy versions in results | Possible | Filtered out | Demo: validity filter |
| Places to search | 3 | 1 | One index |
| Restricted content | Depends on where the file sits | Enforced per person, also for the AI | Demo: two users |

Bottom line: "About 13,800 hours a year returned to compliance and front office *(A)*. Worth about CHF 750,000 a year at half adoption *(A)*. We measure it in the pilot."

**Speaker notes:** "[To COO] The 'today' numbers are yours or our assumptions. The second row is not an assumption. I measured it on a small test set this week: 20 questions in four languages, judged by hand. It is small, and it shows direction, not proof. In the pilot we build that set with your compliance team from real questions. Time per question: Docusign reports going from hours to under a minute for agreement search. I plan with 40 minutes to 10 for you. That is 13,800 hours a year across 150 frequent users. I count half of it."

The calculation (appendix, show only if asked):
- Frequent users: 150 *(A)*. Questions per user per week: 4 *(A)*. Working weeks: 46.
- Minutes saved per question: 30 *(A)*. Hours: 150 × 4 × 46 × 0.5 = 13,800.
- Loaded cost per hour: CHF 110 *(A)*. Full value CHF 1.52 million. At 50% adoption *(A)*: about CHF 760,000.
- Not counted: the cost of an audit finding or a missed obligation.

**German:** Geschäftswert, Zeit pro Anfrage, Annahmen, "Wir messen es im Piloten".

---

## Slide 8. Roadmap (2:00)

**Headline:** Land with compliance, expand to advisers, then one knowledge platform

| Land: pilot (6 weeks) | Expand (two quarters) | Platform (later) |
|---|---|---|
| Compliance team, 30 users | Relationship managers, IT support, onboarding | Company-wide knowledge search |
| Regulation plus the policy library; SharePoint connector with permissions | More sources: intranet, file shares, ticket system | Observability and security on the same platform and skills |
| Judged question set built with your team | Feedback loop, relevance reviews each quarter | The agent in the intranet and in Teams through the API |
| **Success:** 80% of test questions answered in the top 5; no restricted document in the wrong hands in a permission test; time per question halved | **Success:** 150 frequent users, adoption above 50% | **Success:** agreed later |

**Speaker notes:** "We start small: the compliance team, six weeks, with success criteria we agree today. The first two weeks build the test set from real questions, because that is how we prove relevance to you. Then advisers, IT support and onboarding. Later the same platform can serve the whole bank, and the same Elastic skills cover observability and security. That is a later decision."

**German:** Pilot, Erfolgskriterien, schrittweise Einführung, Wissensplattform.

---

## Slide 9. Next steps (1:00)

**Headline:** Three decisions today start the pilot in two weeks

1. **Agree pilot scope and success criteria.** Head of Compliance and me. This week.
2. **Security workshop, two hours:** data location, access model, which LLM. CISO and me. Next week.
3. **Name two engineers and give read access to the policy library.** Lead Platform Engineer. Next week.

**Speaker notes:** "[To COO] Three things. Scope and criteria with your Head of Compliance. Two hours with your CISO on data location, access and the model, before any document moves. And two engineers with read access to the policy library. Can we agree on these today? What would stop us?" Stop talking.

**German:** Nächste Schritte, Verantwortliche, "Was würde uns aufhalten?"

---

## Slide 10. Appendix for Q&A (not presented)

| Slide | Content |
|---|---|
| A1 Evaluation | The table from `eval/RESULTS.md`: keyword vs hybrid, by kind of question. How the set was judged. Why 20 questions is direction, not proof. |
| A2 Chunking and embeddings | One record per article or policy; `semantic_text` chunks of up to 250 words with one sentence overlap; which model and why; what I measured with the smaller model. |
| A3 Multilingual handling | Language detection at ingest; one keyword field per language; decompounding for German; one multilingual vector space. |
| A4 Security and residency | Document-level security from user groups; how groups sync from the directory; regions (Hosted: AWS Zurich); where embeddings and the LLM run. |
| A5 LLM and hallucination control | Agent instructions: answer only from retrieved sources, cite, say "not found". Managed LLM with zero data retention, or your own model. |
| A6 Scale and cost | What drives cost: documents, vector dimensions, queries, LLM tokens. Quantisation for vectors. Sized in the pilot. |
| A7 Value model | The calculation behind slide 7. |
| A8 References | EY, Docusign, BBVA, with links. |

---

## All assumptions in one place

| Assumption | Value | Used on |
|---|---|---|
| Staff who need rules daily | about 400 | 2 |
| Frequent users | 150 | 7 |
| Research questions per frequent user per week | 4 | 7 |
| Time per question today | 40 minutes | 2, 7 |
| Time per question, target | 10 minutes | 7 |
| Working weeks per year | 46 | 7 |
| Loaded cost per hour | CHF 110 | 7 |
| Adoption counted in the value | 50% | 7 |
| Audit findings last year from superseded policies | 2 | 2 |
| Places to search today | 3 | 2, 7 |

Not assumptions: the evaluation numbers (measured, see `eval/RESULTS.md`) and the customer quotes (from elastic.co, see `SOURCES.md`).
