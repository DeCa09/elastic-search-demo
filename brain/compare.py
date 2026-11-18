#!/usr/bin/env python3
"""Ask the same questions to two agents and compare them.

  albisgrat-brain     reads Knowledge Indicators from the AI Index first
  albisgrat-baseline  same model, same data, no Knowledge Indicators

For each run it records tool calls, LLM calls, tokens, seconds, and whether the answer names
exactly the right records. The right records are computed here from the data files, not judged
by a model. Writes brain/RESULTS.md and brain/answers/*.md.

Every run uses the LLM. Three questions for two agents is six agent runs.
Usage: scripts/brain.sh compare [question-id ...]
"""

import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
KIBANA_URL = os.environ.get("BRAIN_KIBANA_URL", "").rstrip("/")
API_KEY = os.environ.get("BRAIN_API_KEY", "")
AGENTS = [("albisgrat-baseline", "Baseline, no context"), ("albisgrat-brain", "With Knowledge Indicators")]
TODAY = os.environ.get("BRAIN_TODAY", time.strftime("%Y-%m-%d"))


def rows(name):
    with open(os.path.join(HERE, "data", name), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def questions():
    inv, inc = rows("outsourcing_inventory.jsonl"), rows("incidents.jsonl")
    year_ago = "%d%s" % (int(TODAY[:4]) - 1, TODAY[4:])
    abroad = [r for r in inv if r["contains_client_data"] and r["data_location"] != "CH"]
    overdue = [r for r in inv if r["status"] == "active" and r["last_review"] < year_ago]
    late = [r for r in inc if r["category"] == "data_breach" and not r["reported_within_24h"]]
    return [
        {"id": "location", "language": "en",
         "question": "Which outsourcing arrangements store client data outside Switzerland, and does "
                     "our directive allow each of them?",
         "expected": sorted(r["arrangement_id"] for r in abroad), "pattern": r"OUT-\d{3}",
         "note": "Not allowed: %s. Allowed (EU with board approval): %s." % (
             ", ".join(r["arrangement_id"] for r in abroad
                       if r["data_location"] != "EU" or not r["board_approval_eu"]),
             ", ".join(r["arrangement_id"] for r in abroad
                       if r["data_location"] == "EU" and r["board_approval_eu"]))},
        {"id": "overdue", "language": "de",
         "question": "Bei welchen aktiven Auslagerungen ist die jährliche Überprüfung überfällig?",
         "expected": sorted(r["arrangement_id"] for r in overdue), "pattern": r"OUT-\d{3}",
         "note": "Overdue means last review more than 12 months ago (W-12 v3.0, section 8)."},
        {"id": "late-breaches", "language": "fr",
         "question": "Quelles violations de la sécurité des données ont été annoncées en retard cette "
                     "année, et lesquelles concernent un prestataire externe ?",
         "expected": sorted(r["incident_id"] for r in late), "pattern": r"INC-2026-\d{3}",
         "note": "Late means not reported within 24 hours (P-11). With a provider: %s." % (
             ", ".join("%s (%s)" % (r["incident_id"], r["related_arrangement_id"])
                       for r in late if r["related_arrangement_id"]) or "none")},
    ]


def ask(agent_id, question):
    body = json.dumps({"input": question, "agent_id": agent_id}).encode()
    req = urllib.request.Request(
        KIBANA_URL + "/api/agent_builder/converse/async", method="POST", data=body,
        headers={"Authorization": "ApiKey " + API_KEY, "kbn-xsrf": "true",
                 "Content-Type": "application/json"})
    start = time.time()
    out = {"tool_calls": [], "answer": "", "llm_calls": 0, "input_tokens": 0, "output_tokens": 0}
    event = None
    with urllib.request.urlopen(req, timeout=600) as resp:
        for raw in resp:
            line = raw.decode("utf-8", errors="replace").rstrip("\n")
            if line.startswith("event: "):
                event = line[7:]
            elif line.startswith("data: ") and event:
                try:
                    data = json.loads(line[6:]).get("data", {})
                except ValueError:
                    continue
                if event == "tool_call":
                    out["tool_calls"].append(data.get("tool_id", "?"))
                elif event == "message_complete":
                    out["answer"] = data.get("message_content", "")
                elif event == "round_complete":
                    usage = (data.get("round") or {}).get("model_usage") or {}
                    for key in ("llm_calls", "input_tokens", "output_tokens"):
                        out[key] = usage.get(key, 0)
    out["seconds"] = round(time.time() - start)
    return out


def grade(answer, q):
    found = sorted(set(re.findall(q["pattern"], answer)))
    missing = [x for x in q["expected"] if x not in found]
    extra = [x for x in found if x not in q["expected"]]
    return {"found": found, "missing": missing, "extra": extra, "correct": not missing and not extra}


def main():
    if not KIBANA_URL or not API_KEY:
        sys.exit("Set BRAIN_KIBANA_URL and BRAIN_API_KEY")
    args = sys.argv[1:]
    only_brain = "--only-brain" in args      # skip the baseline, which uses far more tokens
    wanted = [a for a in args if not a.startswith("--")]
    all_qs = questions()
    os.makedirs(os.path.join(HERE, "answers"), exist_ok=True)
    cache_path = os.path.join(HERE, "answers", "runs.json")
    cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
    for q in [q for q in all_qs if not wanted or q["id"] in wanted]:
        for agent_id, label in AGENTS:
            if only_brain and agent_id != "albisgrat-brain":
                continue
            print("asking %s: %s" % (agent_id, q["id"]), flush=True)
            try:
                run = ask(agent_id, q["question"])
            except Exception as err:  # noqa: BLE001
                run = {"tool_calls": [], "answer": "ERROR: %s" % err, "llm_calls": 0,
                       "input_tokens": 0, "output_tokens": 0, "seconds": 0}
            run.update(grade(run["answer"], q))
            run.update({"agent": agent_id, "label": label, "date": TODAY})
            cache["%s|%s" % (q["id"], agent_id)] = run
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=1)
            with open(os.path.join(HERE, "answers", "%s--%s.md" % (q["id"], agent_id)), "w",
                      encoding="utf-8") as f:
                f.write("# %s\n\nAgent: %s\n\nQuestion: %s\n\nExpected records: %s\n\n"
                        "Tools called: %s\n\n---\n\n%s\n"
                        % (q["id"], label, q["question"], ", ".join(q["expected"]),
                           ", ".join(run["tool_calls"]), run["answer"]))

    # Report every run on record, including earlier ones.
    results, qs = [], []
    for q in all_qs:
        for agent_id, label in AGENTS:
            run = cache.get("%s|%s" % (q["id"], agent_id))
            if run:
                run = dict(run, q=q)
                results.append(run)
                if q not in qs:
                    qs.append(q)

    out = ["# Company brain: with and without Knowledge Indicators", "",
           "Same questions, same data, same model. One agent reads Knowledge Indicators from the AI "
           "Index first; the baseline explores the indices by itself. \"Correct\" means the answer names "
           "exactly the records computed from the data files. Runs from %s. Where a question has no "
           "baseline row, the baseline was not run for it, to save tokens."
           % ", ".join(sorted({r["date"] for r in results})), "",
           "| Question | Agent | Correct | Tool calls | LLM calls | Tokens | Seconds |",
           "|---|---|---|---|---|---|---|"]
    for r in results:
        detail = "yes" if r["correct"] else "no (%s)" % "; ".join(
            x for x in ("missing " + ", ".join(r["missing"]) if r["missing"] else "",
                        "wrong " + ", ".join(r["extra"]) if r["extra"] else "") if x)
        out.append("| %s (%s) | %s | %s | %d | %d | %s | %d |" % (
            r["q"]["id"], r["q"]["language"], r["label"], detail, len(r["tool_calls"]),
            r["llm_calls"], format(r["input_tokens"] + r["output_tokens"], ","), r["seconds"]))
    out += ["", "## Per agent (averages per question)", "",
            "| Agent | Correct | Tool calls | Tokens | Seconds |", "|---|---|---|---|---|"]
    for agent_id, label in AGENTS:
        mine = [r for r in results if r["agent"] == agent_id]
        if not mine:
            continue
        n = float(len(mine))
        out.append("| %s | %d of %d | %.1f | %s | %d |" % (
            label, sum(r["correct"] for r in mine), len(mine),
            sum(len(r["tool_calls"]) for r in mine) / n,
            format(int(sum(r["input_tokens"] + r["output_tokens"] for r in mine) / n), ","),
            sum(r["seconds"] for r in mine) / n))
    out += ["", "## The questions", ""]
    for q in qs:
        out += ["- **%s**: %s  " % (q["id"], q["question"]),
                "  Expected: %s. %s" % (", ".join(q["expected"]), q["note"])]
    out += ["", "Agents are not deterministic. One run per question shows direction, not proof. "
            "The full answers are in `brain/answers/`."]
    text = "\n".join(out) + "\n"
    with open(os.path.join(HERE, "RESULTS.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print("\n" + text)


if __name__ == "__main__":
    main()
