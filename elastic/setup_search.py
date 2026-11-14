#!/usr/bin/env python3
"""Build the search demo in Elasticsearch and Kibana.

Commands:
  index     create the ingest pipeline and the index (strict mapping). Deletes an existing index.
  ingest    bulk-index the public law texts and the internal documents
  security  create the role and the two demo users (document-level security)
  agent     create the Agent Builder tool and agent (the RAG experience)
  all       index + ingest + security + agent
  status    check every piece; exit code 1 if something is missing
  delete    remove everything this script created

Uses only the Python standard library. Reads settings from the environment
(scripts/*.sh load .env first). Never prints secrets.
"""

import glob
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import queries  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ES_URL = os.environ.get("ELASTICSEARCH_URL", "").rstrip("/")
KIBANA_URL = os.environ.get("KIBANA_URL", "").rstrip("/")
API_KEY = os.environ.get("ELASTIC_API_KEY", "")
INDEX = os.environ.get("INDEX_NAME", "albisgrat-knowledge")
PIPELINE = INDEX + "-ingest"
INFERENCE_ID = os.environ.get("INFERENCE_ID", ".jina-embeddings-v5-text-small")
ROLE = "albisgrat_knowledge_reader"
USERS = {
    # username: (full name, groups, env var with the password)
    "compliance_officer": ("Clara Keller (Compliance Officer, fictional)",
                           ["all_staff", "compliance"], "COMPLIANCE_OFFICER_PASSWORD"),
    "relationship_manager": ("Remo Rossi (Relationship Manager, fictional)",
                             ["all_staff", "front_office"], "RELATIONSHIP_MANAGER_PASSWORD"),
}
TOOL_ID = "albisgrat.knowledge_search"
AGENT_ID = "albisgrat-compliance-assistant"
LEXICAL_FIELDS = ["title^2", "body_de", "body_fr", "body_it", "body_en"]

# Words the German decompounder may split compounds into ("Kundendaten" -> kunden + daten).
DE_WORDS = [
    "auslagerung", "kunde", "kunden", "daten", "dienstleister", "genehmigung", "geldwäscherei",
    "bank", "geheimnis", "schutz", "sicherheit", "bearbeitung", "auftrag", "bearbeiter",
    "bekanntgabe", "ausland", "vertrag", "risiko", "analyse", "meldung", "pflicht", "konto",
    "eröffnung", "aufbewahrung", "frist", "löschung", "anbieter", "beziehung", "geschäft",
    "verdacht", "identifizierung", "video", "sanktion", "berater", "person", "sorgfalt",
    "prüfung", "personen", "verletzung", "auskunft", "begehren", "transaktion", "überwachung",
    "berechtigte", "wirtschaftlich", "vermögen", "herkunft", "interessen", "konflikt",
]

INSTRUCTIONS = """You are the compliance knowledge assistant of Privatbank Albisgrat AG, a fictional Swiss private bank.

Rules:
1. Always search the knowledge base with the tool before you answer. Make two searches at the same time: one in the language of the question and one in German, because most internal directives are written in German. Do not search again unless both return nothing useful.
2. Answer only from the documents the tool returns. If they do not contain the answer, say so. Never use your own knowledge of law or banking.
3. Cite every statement. After each point, name the source in square brackets: for internal documents the document number, version and section, for law the article. Examples: [W-12 v3.0, section 4] or [Art. 9 DSG].
4. Use only versions that are in force. If a document says it is superseded or no longer valid, do not use its rules; mention in one line that an outdated version exists.
5. If a memo or temporary rule changes what a directive says, state that first and cite it.
6. Be brief: at most six short bullet points and at most 150 words. Then a list "Sources" with one line per source: title, version or article, valid-from date.
7. Answer in the language of the question.
8. Access control is done by the system, not by you. Every document the tool returns is one the current user is allowed to read, including documents marked confidential: use them like any other source. Never hold a document back because of its confidentiality label, and never speculate about documents you cannot see."""


class ApiError(Exception):
    def __init__(self, status, body):
        super().__init__("HTTP %s: %s" % (status, body[:700]))
        self.status = status
        self.body = body


def http(base, method, path, body=None, ok_missing=False, run_as=None, ndjson=False, timeout=600):
    headers = {"Authorization": "ApiKey " + API_KEY,
               "Content-Type": "application/x-ndjson" if ndjson else "application/json"}
    if run_as:
        headers.update(queries.auth_headers(run_as))
    if base == KIBANA_URL:
        headers["kbn-xsrf"] = "true"
    data = None
    if body is not None:
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
    req = urllib.request.Request(base + path, method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as err:
        if ok_missing and err.code == 404:
            return None
        raise ApiError(err.code, err.read().decode(errors="replace"))


def es(method, path, body=None, **kw):
    return http(ES_URL, method, path, body, **kw)


def kb(method, path, body=None, **kw):
    return http(KIBANA_URL, method, path, body, **kw)


def info(msg):
    print("  " + msg)


# -------------------------------------------------------------------- index

def index_body():
    text = lambda analyzer: {"type": "text", "analyzer": analyzer}
    keyword = {"type": "keyword"}
    return {
        "settings": {
            "number_of_shards": 1,
            "default_pipeline": PIPELINE,
            "analysis": {
                "filter": {
                    "de_stop": {"type": "stop", "stopwords": "_german_"},
                    "de_decompound": {"type": "dictionary_decompounder", "word_list": DE_WORDS,
                                      "min_subword_size": 4},
                    "de_stem": {"type": "stemmer", "language": "light_german"},
                    "fr_elision": {"type": "elision", "articles_case": True,
                                   "articles": ["l", "m", "t", "qu", "n", "s", "j", "d", "c",
                                                "jusqu", "quoiqu", "lorsqu", "puisqu"]},
                    "fr_stop": {"type": "stop", "stopwords": "_french_"},
                    "fr_stem": {"type": "stemmer", "language": "light_french"},
                    "it_elision": {"type": "elision", "articles_case": True,
                                   "articles": ["c", "l", "all", "dall", "dell", "nell", "sull",
                                                "coll", "pell", "gl", "agl", "dagl", "degl", "negl",
                                                "sugl", "un", "m", "t", "s", "v", "d"]},
                    "it_stop": {"type": "stop", "stopwords": "_italian_"},
                    "it_stem": {"type": "stemmer", "language": "light_italian"},
                },
                "analyzer": {
                    # German: split compounds, fold umlauts, stem.
                    "de_text": {"type": "custom", "tokenizer": "standard",
                                "filter": ["lowercase", "de_stop", "de_decompound",
                                           "german_normalization", "de_stem"]},
                    # French and Italian: remove elisions (l'avion -> avion), stem, fold accents.
                    "fr_text": {"type": "custom", "tokenizer": "standard",
                                "filter": ["fr_elision", "lowercase", "fr_stop", "fr_stem",
                                           "asciifolding"]},
                    "it_text": {"type": "custom", "tokenizer": "standard",
                                "filter": ["it_elision", "lowercase", "it_stop", "it_stem",
                                           "asciifolding"]},
                    "title_text": {"type": "custom", "tokenizer": "standard",
                                   "filter": ["lowercase", "asciifolding"]},
                },
            },
        },
        "mappings": {
            "dynamic": "strict",
            "properties": {
                "id": keyword,
                "title": text("title_text"),
                # The original text. Copied into the semantic field, which chunks and embeds it.
                "body": {"type": "text", "index": False, "copy_to": "body_semantic"},
                "body_de": text("de_text"),
                "body_fr": text("fr_text"),
                "body_it": text("it_text"),
                "body_en": text("english"),
                "body_semantic": {
                    "type": "semantic_text",
                    "inference_id": INFERENCE_ID,
                    "chunking_settings": {"strategy": "sentence", "max_chunk_size": int(os.environ.get("CHUNK_WORDS", "250")),
                                          "sentence_overlap": 1},
                },
                "language": keyword,
                "language_detected": keyword,
                "language_confidence": {"type": "float"},
                "doc_type": keyword,
                "source": keyword,
                "source_url": keyword,
                "section": keyword,
                "law": keyword,
                "law_title": {"type": "text", "index": False},
                "sr_number": keyword,
                "doc_number": keyword,
                "version": keyword,
                "department": keyword,
                "supersedes": keyword,
                "valid_from": {"type": "date"},
                "valid_to": {"type": "date"},
                "is_current": {"type": "boolean"},
                "allowed_groups": keyword,
            },
        },
    }


def pipeline_body():
    return {
        "description": "Detect the language, then copy the text into the field for that language.",
        "processors": [
            {"inference": {
                "model_id": "lang_ident_model_1",
                "field_map": {"body": "text"},
                "target_field": "_lang",
                "inference_config": {"classification": {"num_top_classes": 1}},
                "ignore_failure": True,
            }},
            {"script": {
                "description": "Use the detected language when it is one of ours and confident. "
                               "Otherwise keep the language the source system declared.",
                "source": """
                    String declared = ctx.language;
                    String detected = null;
                    double conf = 0;
                    if (ctx._lang != null && ctx._lang.predicted_value != null) {
                      detected = ctx._lang.predicted_value;
                      if (ctx._lang.prediction_probability != null) {
                        conf = ((Number) ctx._lang.prediction_probability).doubleValue();
                      }
                    }
                    ctx.language_detected = detected;
                    ctx.language_confidence = conf;
                    String lang = declared;
                    if (detected != null && conf >= 0.8 && ['de','fr','it','en'].contains(detected)) {
                      lang = detected;
                    }
                    if (lang == null) { lang = 'de'; }
                    ctx.language = lang;
                    ctx['body_' + lang] = ctx.body;
                    ctx.remove('_lang');
                """,
            }},
        ],
    }


def create_index():
    print("Index and ingest pipeline")
    es("PUT", "/_ingest/pipeline/" + PIPELINE, pipeline_body())
    info("pipeline %s" % PIPELINE)
    es("DELETE", "/" + INDEX, ok_missing=True)
    es("PUT", "/" + INDEX, index_body())
    info("index %s (semantic field uses %s)" % (INDEX, INFERENCE_ID))


# ------------------------------------------------------------------- ingest

def load_documents():
    docs = []
    with open(os.path.join(ROOT, "data", "public", "fedlex.jsonl"), encoding="utf-8") as f:
        for line in f:
            if line.strip():
                docs.append(json.loads(line))
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "internal", "*.json"))):
        with open(path, encoding="utf-8") as f:
            docs.append(json.load(f))
    return docs


def warm_up():
    """Start the embedding model before the first bulk request (first start can take minutes)."""
    for attempt in range(40):
        try:
            es("POST", "/_inference/" + INFERENCE_ID, {"input": "Aufwärmen"}, timeout=300)
            return
        except (ApiError, urllib.error.URLError, TimeoutError) as err:
            if attempt == 0:
                info("waiting for the embedding model %s to start..." % INFERENCE_ID)
            time.sleep(8)
            last = err
    sys.exit("The embedding model did not start: %s" % last)


def ingest(batch=40):
    print("Ingest")
    docs = load_documents()
    warm_up()
    start = time.time()
    errors = 0
    for i in range(0, len(docs), batch):
        lines = []
        for d in docs[i:i + batch]:
            lines.append(json.dumps({"index": {"_index": INDEX, "_id": d["id"]}}))
            lines.append(json.dumps(d, ensure_ascii=False))
        out = es("POST", "/_bulk", "\n".join(lines) + "\n", ndjson=True, timeout=900)
        if out.get("errors"):
            for item in out["items"]:
                err = item["index"].get("error")
                if err:
                    errors += 1
                    if errors <= 3:
                        info("ERROR %s: %s" % (item["index"]["_id"], json.dumps(err)[:300]))
        done = min(i + batch, len(docs))
        if done % 200 < batch or done == len(docs):
            info("%d / %d documents, %ds" % (done, len(docs), time.time() - start))
    es("POST", "/%s/_refresh" % INDEX)
    count = es("GET", "/%s/_count" % INDEX)["count"]
    info("indexed %d documents in %ds, %d errors" % (count, time.time() - start, errors))
    if errors:
        sys.exit("Some documents failed. Fix the errors above and run again.")


# ----------------------------------------------------------------- security

def role_body():
    # One role for everyone. The document filter comes from the user's own groups
    # (user metadata), so new groups need no new roles.
    dls = {"template": {"source":
           "{\"terms\": {\"allowed_groups\": {{#toJson}}_user.metadata.groups{{/toJson}}}}"}}
    return {
        "elasticsearch": {
            "cluster": ["monitor_inference"],
            "indices": [{"names": [INDEX], "privileges": ["read", "view_index_metadata"],
                         "query": json.dumps(dls)}],
        },
        "kibana": [{"spaces": ["default"], "base": [],
                    # enterpriseSearch is the Elasticsearch home page Kibana opens after login.
                    # Without it a demo user lands on "Application not found".
                    "feature": {"agentBuilder": ["read"], "dev_tools": ["all"],
                                "discover_v2": ["read"], "enterpriseSearch": ["read"]}}],
    }


def create_security():
    print("Role and users")
    body = role_body()
    try:
        kb("PUT", "/api/security/role/" + ROLE, body)
    except ApiError as err:
        # Older or newer Kibana may not know one of the feature names. Fall back to the minimum.
        if err.status != 400:
            raise
        body["kibana"][0]["feature"] = {"agentBuilder": ["read"], "dev_tools": ["all"]}
        kb("PUT", "/api/security/role/" + ROLE, body)
    info("role %s (document-level security from user metadata 'groups')" % ROLE)
    for name, (full_name, groups, env) in USERS.items():
        password = os.environ.get(env, "")
        if len(password) < 8:
            sys.exit("%s must be set in .env (at least 8 characters)" % env)
        es("PUT", "/_security/user/" + name,
           {"password": password, "roles": [ROLE], "full_name": full_name,
            "metadata": {"groups": groups}})
        info("user %s, groups %s" % (name, ", ".join(groups)))


# -------------------------------------------------------------------- agent

def create_agent():
    print("Agent Builder: tool and agent")
    tool = {
        "id": TOOL_ID,
        "type": "index_search",
        "description": "Search the knowledge base of Privatbank Albisgrat: Swiss federal law "
                       "(data protection, anti-money laundering, banking) in German, French, "
                       "Italian and English, and the bank's internal policies, procedures and "
                       "memos. Use it for every question about rules, obligations and policies.",
        "tags": ["albisgrat", "compliance"],
        "configuration": {"pattern": INDEX},
    }
    agent = {
        "id": AGENT_ID,
        "name": "Albisgrat Compliance Assistant",
        "description": "Answers compliance questions in German, French, Italian or English, "
                       "only from Swiss law and the bank's own policies, with citations.",
        "labels": ["compliance", "demo"],
        "avatar_color": "#BFDBFF",
        "avatar_symbol": "AC",
        "configuration": {"instructions": INSTRUCTIONS,
                          "tools": [{"tool_ids": [TOOL_ID, "platform.core.get_document_by_id"]}]},
    }
    kb("DELETE", "/api/agent_builder/agents/" + AGENT_ID, ok_missing=True)
    kb("DELETE", "/api/agent_builder/tools/" + TOOL_ID, ok_missing=True)
    kb("POST", "/api/agent_builder/tools", tool)
    info("tool %s" % TOOL_ID)
    kb("POST", "/api/agent_builder/agents", agent)
    info("agent %s" % AGENT_ID)


# ------------------------------------------------------------ status/delete

def status():
    problems = 0

    def line(good, text):
        nonlocal problems
        if not good:
            problems += 1
        print("  %s  %s" % ("OK   " if good else "FAIL ", text))

    expected = len(load_documents())
    try:
        count = es("GET", "/%s/_count" % INDEX)["count"]
    except ApiError:
        count = -1
    line(count == expected, "index %s: %s documents (expected %d)" % (INDEX, count, expected))

    try:
        es("POST", "/_inference/" + INFERENCE_ID, {"input": "test"}, timeout=120)
        line(True, "embedding endpoint %s answers" % INFERENCE_ID)
    except Exception as err:  # noqa: BLE001
        line(False, "embedding endpoint %s: %s" % (INFERENCE_ID, str(err)[:120]))

    restricted = {"query": {"bool": {"must_not": {"term": {"allowed_groups": "all_staff"}}}}}
    for name, (_, groups, env) in USERS.items():
        try:
            total = es("GET", "/%s/_count" % INDEX, run_as=name)["count"]
            secret = es("POST", "/%s/_count" % INDEX, restricted, run_as=name)["count"]
            want_secret = "compliance" in groups
            good = total > 0 and ((secret > 0) == want_secret)
            line(good, "user %s: sees %d documents, %d restricted" % (name, total, secret))
        except Exception as err:  # noqa: BLE001
            line(False, "user %s: %s" % (name, str(err)[:120]))

    try:
        agent = kb("GET", "/api/agent_builder/agents/" + AGENT_ID, ok_missing=True)
        tool = kb("GET", "/api/agent_builder/tools/" + TOOL_ID, ok_missing=True)
        line(bool(agent and tool), "Agent Builder agent and tool: %s"
             % ("present" if agent and tool else "missing"))
    except ApiError as err:
        line(False, "Agent Builder: %s" % str(err)[:120])
    return problems


def delete_all():
    print("Deleting demo objects")
    for call in (lambda: kb("DELETE", "/api/agent_builder/agents/" + AGENT_ID, ok_missing=True),
                 lambda: kb("DELETE", "/api/agent_builder/tools/" + TOOL_ID, ok_missing=True),
                 lambda: kb("DELETE", "/api/security/role/" + ROLE, ok_missing=True),
                 lambda: es("DELETE", "/" + INDEX, ok_missing=True),
                 lambda: es("DELETE", "/_ingest/pipeline/" + PIPELINE, ok_missing=True)):
        try:
            call()
        except ApiError as err:
            info("skipped: %s" % str(err)[:100])
    for name in USERS:
        es("DELETE", "/_security/user/" + name, ok_missing=True)
    info("done")


def main():
    if not ES_URL or not KIBANA_URL or not API_KEY:
        sys.exit("ELASTICSEARCH_URL, KIBANA_URL and ELASTIC_API_KEY must be set (see .env.example)")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"index": [create_index], "ingest": [ingest], "security": [create_security],
             "agent": [create_agent],
             "rebuild": [create_index, ingest],
             "all": [create_index, ingest, create_security, create_agent]}
    try:
        if cmd in steps:
            for step in steps[cmd]:
                step()
        elif cmd == "status":
            sys.exit(1 if status() else 0)
        elif cmd == "delete":
            delete_all()
        else:
            sys.exit(__doc__)
    except ApiError as err:
        sys.exit("API error during '%s': %s" % (cmd, err))
    except urllib.error.URLError as err:
        sys.exit("Cannot reach Elastic: %s" % err.reason)


if __name__ == "__main__":
    main()
