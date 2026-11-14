#!/usr/bin/env python3
"""The demo queries: keyword-only and hybrid (keyword + semantic, fused with RRF).

Used by scripts/ask.sh (terminal view of the demo queries) and eval/run_eval.py.
The same request bodies are in demo/console-queries.md for Kibana Dev Tools.

Usage:
  python3 elastic/queries.py keyword "question" [--as USER] [--current] [--size N] [--json]
  python3 elastic/queries.py hybrid  "question" [--as USER] [--current] [--size N] [--json]
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request

ES_URL = os.environ.get("ELASTICSEARCH_URL", "").rstrip("/")
API_KEY = os.environ.get("ELASTIC_API_KEY", "")
INDEX = os.environ.get("INDEX_NAME", "albisgrat-knowledge")
# Listed one by one: with document-level security, multi_match does not accept field wildcards.
LEXICAL_FIELDS = ["title^2", "body_de", "body_fr", "body_it", "body_en"]
SOURCE = ["title", "language", "doc_type", "section", "doc_number", "version", "valid_from",
          "is_current", "allowed_groups", "source_url"]
PASSWORDS = {"compliance_officer": "COMPLIANCE_OFFICER_PASSWORD",
             "relationship_manager": "RELATIONSHIP_MANAGER_PASSWORD"}


def lexical(question):
    return {"multi_match": {"query": question, "fields": LEXICAL_FIELDS, "type": "best_fields"}}


def current_filter(current_only):
    return [{"term": {"is_current": True}}] if current_only else []


def keyword_body(question, size=5, current_only=False):
    """What the bank has today: words must match, in the language they were typed."""
    return {
        "size": size,
        "_source": SOURCE,
        "query": {"bool": {"must": [lexical(question)], "filter": current_filter(current_only)}},
    }


def hybrid_body(question, size=5, current_only=False):
    """Keyword and multilingual semantic search, combined with reciprocal rank fusion."""
    rrf = {
        "retrievers": [
            {"standard": {"query": lexical(question)}},
            {"standard": {"query": {"match": {"body_semantic": {"query": question}}}}},
        ],
        "rank_window_size": 50,
        "rank_constant": 60,
    }
    if current_only:
        rrf["filter"] = current_filter(True)
    return {
        "size": size,
        "_source": SOURCE,
        "retriever": {"rrf": rrf},
        "highlight": {"fields": {"body_semantic": {"type": "semantic", "number_of_fragments": 1,
                                                    "order": "score"}}},
    }


def search(body, user=None):
    if user:
        password = os.environ.get(PASSWORDS[user], "")
        auth = "Basic " + base64.b64encode(("%s:%s" % (user, password)).encode()).decode()
    else:
        auth = "ApiKey " + API_KEY
    req = urllib.request.Request(
        "%s/%s/_search" % (ES_URL, INDEX), method="POST", data=json.dumps(body).encode(),
        headers={"Authorization": auth, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as err:
        sys.exit("Search failed, HTTP %s: %s" % (err.code, err.read().decode(errors="replace")[:500]))


def run(mode, question, size=5, current_only=False, user=None):
    body = keyword_body(question, size, current_only) if mode == "keyword" \
        else hybrid_body(question, size, current_only)
    return search(body, user)


def show(result):
    hits = result["hits"]["hits"]
    if not hits:
        print("  (no results)")
    for rank, hit in enumerate(hits, 1):
        s = hit["_source"]
        flags = []
        if "all_staff" not in s.get("allowed_groups", []):
            flags.append("RESTRICTED")
        if s.get("is_current") is False:
            flags.append("OUTDATED")
        version = (" v" + s["version"]) if s.get("version") else ""
        print("  %d. [%s] %s%s  %s" % (rank, s["language"], s["title"][:78], version,
                                       " ".join(flags)))
        fragment = (hit.get("highlight") or {}).get("body_semantic")
        if fragment:
            print("       \"%s...\"" % " ".join(fragment[0].split())[:150])


def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[0] not in ("keyword", "hybrid"):
        sys.exit(__doc__)
    mode, question = args[0], args[1]
    user = args[args.index("--as") + 1] if "--as" in args else None
    size = int(args[args.index("--size") + 1]) if "--size" in args else 5
    if user and user not in PASSWORDS:
        sys.exit("--as must be compliance_officer or relationship_manager")
    result = run(mode, question, size, "--current" in args, user)
    if "--json" in args:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    who = user or "admin (API key)"
    print("%s search as %s%s: %s" % (mode.upper(), who,
                                     ", current versions only" if "--current" in args else "",
                                     question))
    show(result)


if __name__ == "__main__":
    main()
