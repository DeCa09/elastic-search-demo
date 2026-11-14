#!/usr/bin/env python3
"""Compare keyword-only search with hybrid search on a small judged query set.

Reads eval/judged_queries.json. Each query lists the documents that answer it.
"law:235.1:art_9" means that article in any language version.
Metrics, per search mode:
  success@5     share of queries with at least one relevant document in the top 5
  precision@5   relevant documents in the top 5, divided by 5 (or by the number of relevant
                documents when there are fewer than 5)
  nDCG@10       ranking quality over the top 10 (1.0 is perfect)
  zero results  share of queries that return nothing

Writes eval/RESULTS.md. Usage: scripts/evaluate.sh
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "elastic"))
import queries  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def is_relevant(doc_id, relevant):
    for r in relevant:
        if r.startswith("law:"):
            _, sr, art = r.split(":")
            if doc_id.startswith("fedlex-%s-" % sr) and doc_id.endswith("-" + art):
                return True
        elif doc_id == r:
            return True
    return False


def concept(doc_id, relevant):
    """Language versions of one article count once."""
    for r in relevant:
        if r.startswith("law:"):
            _, sr, art = r.split(":")
            if doc_id.startswith("fedlex-%s-" % sr) and doc_id.endswith("-" + art):
                return r
        elif doc_id == r:
            return r
    return None


def score(ids, relevant):
    seen, gains = set(), []
    for doc_id in ids:
        c = concept(doc_id, relevant)
        if c and c not in seen:
            seen.add(c)
            gains.append(1)
        else:
            gains.append(0)
    top5 = gains[:5]
    dcg = sum(g / math.log2(i + 2) for i, g in enumerate(gains[:10]))
    ideal = sum(1 / math.log2(i + 2) for i in range(min(len(relevant), 10)))
    return {
        "success5": 1.0 if any(top5) else 0.0,
        "p5": sum(top5) / float(min(5, len(relevant))),
        "ndcg10": dcg / ideal if ideal else 0.0,
        "zero": 1.0 if not ids else 0.0,
    }


def main():
    with open(os.path.join(HERE, "judged_queries.json"), encoding="utf-8") as f:
        judged = json.load(f)["queries"]
    modes = ["keyword", "hybrid"]
    totals = {m: {"success5": 0, "p5": 0, "ndcg10": 0, "zero": 0} for m in modes}
    groups = {}
    rows = []
    for q in judged:
        row = [q["id"], q["language"], q["kind"]]
        for mode in modes:
            result = queries.run(mode, q["query"], size=10)
            ids = [h["_id"] for h in result["hits"]["hits"]]
            s = score(ids, q["relevant"])
            for k in s:
                totals[mode][k] += s[k]
            g = groups.setdefault((q["kind"], mode), {"n": 0, "success5": 0})
            g["n"] += 1
            g["success5"] += s["success5"]
            first = next((i + 1 for i, d in enumerate(ids) if is_relevant(d, q["relevant"])), None)
            row.append("rank %d" % first if first else ("no results" if not ids else "not in top 10"))
        rows.append(row + [q["query"]])

    n = float(len(judged))
    out = ["# Evaluation: keyword search vs hybrid search", "",
           "%d judged queries in German, French, Italian and English. "
           "Index: %s. Embedding endpoint: %s." % (len(judged), queries.INDEX,
                                                   os.environ.get("INFERENCE_ID", "?")), "",
           "| Metric | Keyword only | Hybrid (keyword + semantic, RRF) |", "|---|---|---|"]
    labels = [("success5", "Answer in the top 5 (success@5)"), ("p5", "Precision@5"),
              ("ndcg10", "nDCG@10"), ("zero", "Queries with zero results")]
    for key, label in labels:
        fmt = "%.0f%%" if key in ("success5", "zero") else "%.2f"
        vals = [(totals[m][key] / n) * (100 if key in ("success5", "zero") else 1) for m in modes]
        out.append("| %s | %s | %s |" % (label, fmt % vals[0], fmt % vals[1]))
    out += ["", "## Answer in the top 5, by kind of query", "",
            "| Kind of query | Queries | Keyword only | Hybrid |", "|---|---|---|---|"]
    for kind in sorted({k for k, _ in groups}):
        k, h = groups[(kind, "keyword")], groups[(kind, "hybrid")]
        out.append("| %s | %d | %.0f%% | %.0f%% |" % (kind, k["n"], 100 * k["success5"] / k["n"],
                                                     100 * h["success5"] / h["n"]))
    out += ["", "## Per query (rank of the first relevant document)", "",
            "| Id | Lang | Kind | Keyword | Hybrid | Query |", "|---|---|---|---|---|---|"]
    for r in rows:
        out.append("| %s | %s | %s | %s | %s | %s |" % tuple(r))
    out += ["", "This is a small, hand-judged set. It shows direction, not statistical proof. "
            "Run it again after every change to analyzers, chunking or the embedding model."]
    text = "\n".join(out) + "\n"
    with open(os.path.join(HERE, "RESULTS.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
