# Fallback plan

Rule for the day: **the panel scores how you handle a failure.** Name the problem in one sentence, switch to the backup, keep the story and the clock. Never debug live for more than 30 seconds.

One sentence for every case:

> "Live systems do this. I recorded this exact flow yesterday on the same deployment, so let me show you that and keep to time."

## The backups

| Backup | What it is | Use it when |
|---|---|---|
| **Terminal** | `scripts/ask.sh` runs the same search queries as plain text | Kibana's Console misbehaves |
| **Screenshots** | Eight numbered screenshots in one PDF | One screen fails, most likely the agent |
| **Recording** | One video of the 12 minutes, no sound; you narrate live | Elastic Cloud, the network or the laptop fails |

Make the screenshots and the recording the evening before, on the real deployment.

## How to record the backups (30 minutes)

1. Run `scripts/preflight.sh`. Green.
2. Set up the two browser windows exactly as in `RUNBOOK.md`. Start new agent conversations.
3. **Record.** On macOS press `Shift + Command + 5`, choose "Record Selected Portion", select the area with both windows, **Options > Microphone: None**, click **Record**.
4. Walk through the whole runbook at normal speed without speaking. Pause two seconds on each thing you would point at.
5. Stop with the button in the menu bar. Save as `recordings/demo-backup.mov` (`recordings/` is in `.gitignore`).
6. Watch it once. No password, API key or private data may be visible. If something is, record again.
7. **Screenshots**, one per step (`Shift + Command + 4`):

   | File | Shows |
   |---|---|
   | `01-keyword-fails.png` | Query 1: French results only |
   | `02-hybrid-finds.png` | Query 2: Weisung W-12 v3.0 first |
   | `03-agent-working.png` | Agent chat after sending question A |
   | `04-agent-answer-french.png` | The French answer with section citations |
   | `05-two-users.png` | Both windows side by side with the answers to question B |
   | `06-authenticate-groups.png` | `GET _security/_authenticate` with the groups |
   | `07-outdated-version.png` | Query 3: version 2.0 first; query 4: gone |
   | `08-evaluation.png` | The table from `eval/RESULTS.md` |

8. Select the eight files in Finder > right-click > Quick Actions > Create PDF. Keep it open in Preview on the day.
9. Copy the video and the PDF to a second device.

## What to do when something fails

### Case A. The Console does not run a query, or Kibana is slow

Switch to the terminal. Same queries, same results, as text:

```bash
scripts/ask.sh keyword "Qui doit donner son accord avant de confier des données de clients à un prestataire informatique externe ?" --as relationship_manager
```

```bash
scripts/ask.sh hybrid "Qui doit donner son accord avant de confier des données de clients à un prestataire informatique externe ?" --as relationship_manager
```

For the permission step, run the hybrid query once `--as compliance_officer` and once `--as relationship_manager` with the German question from `demo/demo_queries.json` (`permission_question`). The restricted memo is marked `RESTRICTED` and appears only for the compliance officer. Add `--current` for the version step.

Say: "The UI is slow, so here is the same API call from my terminal. It is the same engine."

### Case B. The agent is slow, wrong or unavailable

- **Slow (over 60 seconds):** keep talking through the architecture of the agent, then show screenshot 04 and move on. Come back if it finishes.
- **Weak answer:** follow "If the agent answers poorly" in `RUNBOOK.md`.
- **Error, or the trial's LLM limit is reached:** show screenshots 04 and 05. Say: "The trial account limits LLM usage and I have reached that limit. These are yesterday's answers on the same data." Then show the permission step with the search queries (case A), which do not need the LLM. The proof of permissions is the search, not the chat.
- **The relationship manager's answer mentions the memo:** stop and say so. "That should not happen and I will not explain it away." Run the two search queries to show the engine does filter. Then check afterwards whether the wrong window was used. (If this ever happens in rehearsal, tell me before the interview.)

### Case C. One of the two logins fails

Do the permission step from one window with the terminal queries (case A) for the two users. Or open a private window and log in again with **Log in with Elasticsearch**. Keep both passwords in your password manager, not on a sticky note that the screen share can show.

### Case D. No network, Elastic Cloud unreachable, laptop trouble

1. Play `recordings/demo-backup.mov` full screen and narrate it with the runbook's talk track.
2. If playback fails too, walk through the PDF.
3. Keep the same time checks. A narrated recording that ends on time is a good demo.

### Case E. You are running over

Cut in this order: `_authenticate` (7:15), the second version query (9:00), the technical explanation of the three lists (2:15). Never cut: keyword fails, hybrid finds, the cited answer, the two users, the evaluation table, the recap.

## The 3 biggest risks and how they are covered

| Risk | Likelihood | Cover |
|---|---|---|
| 1. The agent is slow or blocked (36 to 66 seconds per answer in my tests; trial LLM limit unknown) or words an answer differently on the day | Medium | Talk track written for the wait; submit both permission questions before reading either; screenshots 04 and 05; backup question; the search queries prove the same points without the LLM |
| 2. The two-user moment fails in Kibana: a login does not work, the role cannot open the agent chat, or the relationship manager's agent answer differs from what I expect (this part I could not test) | Medium until you have rehearsed it once | `SETUP.md` step 4 on day one; terminal queries per user as proof at search level; screenshot 05 |
| 3. The environment is gone: trial ends about 28 November, deployment paused or unreachable, Wi-Fi | Low, but total | 4 days of margin; preflight at 12:30 and 12:55; recording and PDF on a second device; `scripts/setup.sh all` rebuilds a new deployment in minutes |
