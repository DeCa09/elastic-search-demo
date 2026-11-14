# Demo runbook: 12 minutes

**Session:** Tuesday 24 November 2026, 13:00 to 14:00 CET. Preflight at 12:30 and 12:55.

**Story in one sentence:** a relationship manager in Geneva asks in French about a rule that exists only in a German directive; keyword search misses it, hybrid search finds it, the AI agent answers in French with citations, and a compliance officer asking the same thing gets one more source that the relationship manager must never see.

**Tested or not.** The search queries, the permissions at search level, the version filter, the evaluation and the agent's answers were tested on your Elastic Cloud deployment on 14 November. Not tested: logging in to Kibana as the two demo users, and the agent's answer when the *relationship manager* asks (I could only call the agent with the admin key). Do `SETUP.md` step 4 first. Click names come from Kibana 9.5; correct them here after your first walk-through.

## People and pains

| Panellist | Plays | Short |
|---|---|---|
| RVP | COO, executive sponsor | **COO** |
| Senior Manager SA | Head of Compliance | **HoC** |
| Director SA | CISO | **CISO** |
| Principal SA | Lead Platform Engineer | **ENG** |

| Pain | Short |
|---|---|
| Rules scattered over three places, search works in one language only | **P1** |
| Hours per question | **P2** |
| Outdated versions circulate, answers have no source | **P3** |
| Confidential content must not leak, least of all through an AI | **P4** |

## Before the session

**The evening before**
- [ ] `scripts/preflight.sh` is green.
- [ ] Record the backup video and screenshots (`FALLBACK.md`).
- [ ] Laptop on power, notifications off.

**30 minutes before (12:30)**
- [ ] `scripts/preflight.sh` is green.
- [ ] In the relationship manager window, ask the agent the warm-up question: `Welche Weisung regelt Geschenke und Einladungen?` It should answer with D-05 and a citation. This also warms up the model.

**5 minutes before (12:55)**
- [ ] **Window A, normal browser:** logged in as `relationship_manager`. Zoom 125%. Two tabs: (1) **Dev Tools > Console** with the four queries from `demo/console-queries.md` already pasted, (2) the **AI Agent** chat with the agent "Albisgrat Compliance Assistant" selected and a new, empty conversation.
- [ ] **Window B, private window or second browser:** logged in as `compliance_officer`. One tab: the AI Agent chat, same agent, new conversation. Give this window a different size or theme so the panel can tell the two apart.
- [ ] A note with the questions below, ready to paste.
- [ ] Terminal in the project folder (fallback for the search moments).
- [ ] `eval/RESULTS.md` open in a viewer, or the appendix slide A1.
- [ ] Backup video and screenshots open in another window.

## The 12 minutes

| Time | Show and click | Say | Pain / role | German key terms |
|---|---|---|---|---|
| **0:00** | **Window A, Console.** Point at the top right: the user is `relationship_manager`. | "I am now Remo, a relationship manager in Geneva. A client project wants to move client data to an external IT provider. Remo wants to know who has to approve that. He asks the way he speaks: in French." | P1 / HoC | Kundenberater, Rechtsfrage |
| **0:30** | **Run query 1 (keyword).** Read the titles aloud. | "This is the search you have today. It matches words. Five results, all French: a complaints procedure, data protection articles. None of them answers the question. The answer exists. It is in a directive written in Zurich, in German. Keyword search cannot know that 'prestataire' and 'Dienstleister' mean the same." | P1, P2 / HoC, COO | Stichwortsuche, Sprachgrenze |
| **1:30** | **Run query 2 (hybrid).** Point at result 1: `[de] Weisung W-12: Auslagerung und Cloud-Nutzung`, version 3.0. Then the highlighted passage under it. | "Same question, same index, a different query. First result: Weisung W-12, version 3.0, the German directive on outsourcing. Found by meaning, across the language border." | P1, P2 / HoC | hybride Suche, Bedeutung statt Wortlaut |
| **2:15** | Stay on query 2. Point at the three blocks inside `retrievers`. | "[ENG] What happens here: three result lists, merged with reciprocal rank fusion. One: classic keyword search with an analyzer per language. Two: semantic search on a multilingual embedding, which is one field type, `semantic_text`. Three: semantic search on your own directives only, because a law article that exists in four languages would otherwise fill the top four places. No custom code. One query." | P1 / ENG | Analyzer, Vektorsuche, RRF |
| **3:15** | **Window A, tab 2: AI Agent.** Paste question A. Press Enter. While it works (about 40 seconds), keep talking. | "Remo does not want a result list. He wants an answer. This is Elastic's Agent Builder. I gave the agent one tool, a search on this index, and one page of instructions: answer only from what you find, cite document and section, say so if you find nothing. It runs on Elastic's managed LLM. It could equally run on a model you host." | P2, P3 / HoC, COO | KI-Agent, Quellenangabe |
| **4:15** | **Read the answer.** Point at: the language (French), one citation such as `[W-12 v3.0, section 4]`, the line about the outdated version, the source list. | "The answer is in French. The source is German. Every point names the section it comes from. It tells Remo that an older version exists and must not be used. [HoC] Your team no longer has to be the search engine. They stay the authority: the directive is one click away." | P2, P3 / HoC | Abschnitt, gültige Fassung, nachvollziehbar |
| **5:15** | **Window A, agent, new conversation.** Paste question B. Enter. **Immediately switch to Window B** (compliance officer), paste the same question B, Enter. | "[CISO] Now your concern. The same question, asked by two people. On the left Remo, the relationship manager. On the right Clara, a compliance officer. Same agent, same index, same second." | P4 / CISO | Berechtigungen |
| **6:15** | **Window A.** Read the first bullet: three approvals under W-12. **Window B.** Read the first bullet: the interim rule from the confidential memo. Point at the memo in Clara's source list. Point out that it is absent in Remo's. | "Remo is told: three approvals, as the directive says. Clara is told one more thing first: since an internal investigation in April, every new cloud project also needs the Head of Compliance. That comes from a confidential memo. Remo's answer does not mention it, because for Remo that document does not exist." | P4 / CISO, HoC | vertrauliches Memo, Untersuchung |
| **7:15** | **Window A, Console.** Run `GET _security/_authenticate`. Point at `metadata.groups`. | "[CISO] This is not a prompt that says 'please do not reveal'. It is document-level security in Elasticsearch. Each document lists the groups that may read it. Each user carries groups. The engine filters before anything is retrieved, so the language model never sees the memo. In production the groups come from your directory. One role, not one per group." | P4 / CISO, ENG | Berechtigungen auf Dokumentebene, Verzeichnisdienst |
| **8:15** | **Window A, Console. Run query 3 (permission query).** Result 1 is `W-12 … v2.0`, marked `is_current: false`. | "[HoC] One more risk you named: old versions. Same question as a plain search. The first result is version 2.0 of the directive. Withdrawn in June 2025. It allowed storing client data in the EU without extra approval. That is how an audit finding happens." | P3 / HoC, COO | veraltete Fassung, Prüfungsfeststellung |
| **9:00** | **Run query 4** (same query with the filter `is_current: true`). Version 2.0 is gone, 3.0 is first. | "Every document carries its validity. One filter, and only versions in force are searched. The agent does the same and tells the user that an older version exists." | P3 / HoC | Gültigkeit, in Kraft |
| **9:45** | **Show `eval/RESULTS.md`** (or appendix slide A1). Point at "Answer in the top 5": 60% and 100%. Then the row "cross-language question": 22% and 100%. | "[ENG, COO] One demo proves little. So I measured. Twenty questions in four languages, judged by hand. Keyword search has the answer in the top five for 60%. Hybrid: 100%. For questions asked in another language than the document: 22% against 100%. Two honest notes. Twenty questions show direction, not proof. And my first embedding model failed this test, so I changed it. In the pilot we build this set with your compliance team from real questions." | P1, P2 / ENG, COO | Messung, Testfragen, Relevanz |
| **11:00** | Leave the table on screen. Recap. | "Four pains, four answers. One: one search across four languages. Two: an answer in under a minute instead of an e-mail to Zurich. Three: every answer cites its source, and only versions in force. Four: permissions enforced by the engine, for the search and for the AI." | P1 to P4 / all | Zusammenfassung |
| **11:30** | Back to the slides (slide 7). | "Let me put numbers on that." | | Geschäftswert |
| **12:00** | **End of demo.** | | | |

### Hard time checks

- **1:15 and query 1 or 2 did not run in Kibana:** switch to the terminal and run `scripts/ask.sh keyword "…" --as relationship_manager`, then `hybrid`. Same result, plain text.
- **5:00 and the agent has not answered question A:** say "the model is taking its time, let me show you yesterday's answer", show screenshot 04, and go on to the permission step.
- **8:00 and you are still on permissions:** skip `_authenticate`. Go to the version step.
- **10:00 and you have not reached the evaluation:** skip the version step's second query. The evaluation is worth more.
- **11:30:** stop wherever you are and give the recap.

## The questions

Keep these in a note you can paste from.

**Console queries 1 to 4:** in `demo/console-queries.md`. Paste all four into the Console before the session.

**Question A (agent, as relationship manager, French):**
```
Quelles exigences s'appliquent lorsque nous confions des données de clients à un fournisseur cloud ?
```
Tested answer (14 November, 36 seconds): six bullets in French, each citing a section of W-12 v3.0 (risk analysis, three approvals, data location Switzerland, encryption with keys held by the bank, contract content, inventory), a note that version 2.0 is withdrawn, and a source list with W-12, Art. 8 and 9 LPD and Art. 47 LB.

**Question B (agent, both users, German):**
```
Dürfen wir jetzt ein neues Projekt starten, das Kundendaten an einen Cloud-Anbieter auslagert? Welche Genehmigungen brauchen wir?
```
Tested answer with full access (47 seconds): the first bullet is the interim rule from the confidential memo (until 31 December 2026, additional approval by the Leiterin Compliance), then the three approvals under W-12 v3.0. Expected for the relationship manager: the same answer without the first bullet and without the memo in the sources. **Check this yourself in rehearsal.**

**Backup question (if question A gives a weak answer):**
```
Wie lange müssen Kundenunterlagen nach Ende der Geschäftsbeziehung aufbewahrt werden?
```
Expected: 10 years, citing Weisung W-18 v2.0 and Art. 7 GwG. The search behind it is tested (rank 1); the agent's answer to it is not.

**English version of question A, if the session is in English:**
```
Which requirements apply when we outsource client data to a cloud provider?
```
Tested (66 seconds with the first, longer instructions): an English answer citing the German directive section by section.

### If the agent answers poorly

Say: "Good moment. The agent is only as good as what it retrieves, so let me show you what it retrieved." Then:

1. Open the reasoning or tool steps of the answer in the chat and show the documents it found. If W-12 is there, the retrieval worked and the wording is the issue: ask the backup question.
2. If it answered without sources or from general knowledge, say so plainly: "That answer is not grounded. I would not accept it." Run query 2 in the Console to show the search does find the directive. Honesty here scores better than defending a bad answer.
3. If the agent is unavailable (trial token limit, model error): `FALLBACK.md`, case B.

## After the demo

Nothing to reset. The demo changes no data. Start new conversations before the next run so old answers are not on screen.

## Numbers to fill in after your first rehearsal

| Number | My test on your deployment | Your rehearsal |
|---|---|---|
| Seconds for the agent's answer to question A | 36 | ____ |
| Seconds for the agent's answer to question B | 47 | ____ |
| Relationship manager's answer to question B leaves out the memo | not tested | ____ |
| Full index rebuild (`scripts/reset.sh`) | 27 s for the index | ____ |

## German glossary

| English | German |
|---|---|
| Compliance question | Compliance-Anfrage, Rechtsfrage |
| Directive, policy | Weisung, Richtlinie |
| Outsourcing | Auslagerung |
| Client data | Kundendaten |
| Service provider | Dienstleister |
| Approval | Genehmigung, Freigabe |
| Version in force / outdated version | gültige Fassung / veraltete Fassung |
| Source, citation | Quelle, Quellenangabe |
| Keyword search | Stichwortsuche, Volltextsuche |
| Semantic search | semantische Suche |
| Hybrid search | hybride Suche |
| Relevance | Relevanz, Trefferqualität |
| Document-level security | Berechtigungen auf Dokumentebene |
| Access rights | Zugriffsrechte |
| Confidential | vertraulich |
| Audit finding | Prüfungsfeststellung |
| Data residency | Datenstandort, Datenhaltung in der Schweiz |
| Hallucination | Halluzination, erfundene Antwort |
| Grounded answer | belegte Antwort |
| Banking secrecy | Bankkundengeheimnis |
| Money laundering | Geldwäscherei |
| Relationship manager | Kundenberater |
| Pilot | Pilot, Machbarkeitsnachweis |
