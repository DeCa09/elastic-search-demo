#!/usr/bin/env python3
"""Build the company-brain demo on an Elasticsearch Serverless project.

Commands:
  sources   create and load the three source indices (knowledge, outsourcing inventory, incidents)
  ai-index  create the AI Index and write the curated Knowledge Indicators
  agents    create the two agents: one that reads Knowledge Indicators first, one baseline
  workflow  create and run the Kibana Workflow that writes the index profiles with an LLM
  all       sources + ai-index + agents (hand-written index profiles; run "workflow" after it)
  status    show what exists
  delete    remove everything this script created

Standard library only. Settings come from the environment (BRAIN_ELASTICSEARCH_URL,
BRAIN_KIBANA_URL, BRAIN_API_KEY; scripts/brain.sh loads .env first).
"""

import glob
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ES_URL = os.environ.get("BRAIN_ELASTICSEARCH_URL", "").rstrip("/")
KIBANA_URL = os.environ.get("BRAIN_KIBANA_URL", "").rstrip("/")
API_KEY = os.environ.get("BRAIN_API_KEY", "")

# Reuse the index definition of the first demo for the knowledge index.
os.environ.setdefault("ELASTICSEARCH_URL", ES_URL)
os.environ.setdefault("KIBANA_URL", KIBANA_URL)
os.environ.setdefault("ELASTIC_API_KEY", API_KEY)
sys.path.insert(0, os.path.join(ROOT, "elastic"))
import setup_search  # noqa: E402

KNOWLEDGE = "albisgrat-knowledge"
INVENTORY = "albisgrat-outsourcing-inventory"
INCIDENTS = "albisgrat-incidents"
AI_INDEX = "ai-index-idx-albisgrat"
KI_TOOL = "albisgrat.brain.query_ki"
AGENT_BRAIN = "albisgrat-brain"
AGENT_BASELINE = "albisgrat-baseline"


class ApiError(Exception):
    def __init__(self, status, body):
        super().__init__("HTTP %s: %s" % (status, body[:700]))
        self.status = status
        self.body = body


def http(base, method, path, body=None, ok_missing=False, ndjson=False, timeout=300):
    headers = {"Authorization": "ApiKey " + API_KEY,
               "Content-Type": "application/x-ndjson" if ndjson else "application/json"}
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


def bulk(index, docs, id_field):
    lines = []
    for d in docs:
        lines.append(json.dumps({"index": {"_index": index, "_id": d[id_field]}}))
        lines.append(json.dumps(d, ensure_ascii=False))
    for i in range(0, len(lines), 400):
        out = es("POST", "/_bulk", "\n".join(lines[i:i + 400]) + "\n", ndjson=True, timeout=900)
        if out.get("errors"):
            bad = [it["index"]["error"] for it in out["items"] if it["index"].get("error")]
            sys.exit("Bulk errors in %s: %s" % (index, json.dumps(bad[0])[:400]))
    es("POST", "/%s/_refresh" % index)


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# ------------------------------------------------------------------ sources

def field(ftype, description):
    return {"type": ftype, "meta": {"description": description}}


INVENTORY_MAPPING = {
    "_meta": {"description": "Outsourcing inventory of Privatbank Albisgrat (fictional): one row per "
                             "outsourcing arrangement with an external provider. Structured register: "
                             "data location, approvals, contract and review dates, cost. No policy text."},
    "dynamic": "strict",
    "properties": {
        "arrangement_id": field("keyword", "Arrangement id, e.g. OUT-003"),
        "service": field("keyword", "What is outsourced, e.g. CRM hosting"),
        "provider_code": field("keyword", "Provider code name, e.g. Provider C"),
        "provider_type": field("keyword", "cloud, it_services, payments or print"),
        "contains_client_data": field("boolean", "True if client data (CID) is processed"),
        "data_location": field("keyword", "Where data is stored: CH, EU or US"),
        "approved_management": field("boolean", "Approved by executive board (Geschäftsleitung)"),
        "approved_ciso": field("boolean", "Approved by the CISO"),
        "approved_compliance": field("boolean", "Signed off by Compliance"),
        "board_approval_eu": field("boolean", "Board of directors approved EU/EEA storage"),
        "contract_signed": field("date", "Date the contract was signed"),
        "last_review": field("date", "Date of the last annual review"),
        "business_owner_dept": field("keyword", "Department of the business owner"),
        "criticality": field("keyword", "high, medium or low"),
        "status": field("keyword", "active, planned or terminated"),
        "annual_cost_chf": field("long", "Yearly cost in Swiss francs"),
        "office": field("keyword", "Zurich, Geneva or Lugano"),
    },
}

INCIDENTS_MAPPING = {
    "_meta": {"description": "Incident register of Privatbank Albisgrat (fictional): one row per security "
                             "or operational incident in 2026, with category, severity, whether it was "
                             "reported within 24 hours, and the related outsourcing arrangement if any."},
    "dynamic": "strict",
    "properties": {
        "incident_id": field("keyword", "Incident id, e.g. INC-2026-017"),
        "date": field("date", "Date of the incident"),
        "category": field("keyword", "data_breach, phishing, outage, access_violation"),
        "severity": field("keyword", "low, medium or high"),
        "office": field("keyword", "Zurich, Geneva or Lugano"),
        "language": field("keyword", "Language of the summary: de, fr or it"),
        "related_arrangement_id": field("keyword", "Join key: arrangement_id in the inventory"),
        "reported_within_24h": field("boolean", "True if reported internally within 24 hours"),
        "status": field("keyword", "open or closed"),
        "summary": field("text", "One sentence in German, French or Italian"),
    },
}


def create_sources():
    print("Source indices")
    # 1. knowledge index: same definition as demo 1, minus the shard setting Serverless forbids.
    body = setup_search.index_body()
    body["settings"].pop("number_of_shards", None)
    body["mappings"]["_meta"] = {"description":
        "Knowledge base of Privatbank Albisgrat (fictional): Swiss federal law (data protection, "
        "anti-money laundering, banking) by article in German, French, Italian and English, and the "
        "bank's internal policies, procedures and memos. Text documents with versions and validity."}
    docs = setup_search.load_documents()
    existing = es("GET", "/%s/_count" % KNOWLEDGE, ok_missing=True)
    if existing and existing["count"] == len(docs) and "--force" not in sys.argv:
        docs = []   # already loaded; pass --force to rebuild
    else:
        es("PUT", "/_ingest/pipeline/" + setup_search.PIPELINE, setup_search.pipeline_body())
        es("DELETE", "/" + KNOWLEDGE, ok_missing=True)
        es("PUT", "/" + KNOWLEDGE, body)
    for i in range(0, len(docs), 40):
        lines = []
        for d in docs[i:i + 40]:
            lines.append(json.dumps({"index": {"_index": KNOWLEDGE, "_id": d["id"]}}))
            lines.append(json.dumps(d, ensure_ascii=False))
        out = es("POST", "/_bulk", "\n".join(lines) + "\n", ndjson=True, timeout=900)
        if out.get("errors"):
            bad = [it["index"]["error"] for it in out["items"] if it["index"].get("error")]
            sys.exit("Bulk errors: %s" % json.dumps(bad[0])[:400])
    es("POST", "/%s/_refresh" % KNOWLEDGE)
    info("%s: %d documents" % (KNOWLEDGE, es("GET", "/%s/_count" % KNOWLEDGE)["count"]))

    for index, mapping, path, key in (
            (INVENTORY, INVENTORY_MAPPING, "outsourcing_inventory.jsonl", "arrangement_id"),
            (INCIDENTS, INCIDENTS_MAPPING, "incidents.jsonl", "incident_id")):
        es("DELETE", "/" + index, ok_missing=True)
        es("PUT", "/" + index, {"mappings": mapping})
        bulk(index, read_jsonl(os.path.join(HERE, "data", path)), key)
        info("%s: %d rows" % (index, es("GET", "/%s/_count" % index)["count"]))


# ----------------------------------------------------------------- AI index

def ki(ki_id, ki_type, title, description, content, tags, attributes=None, uri=None):
    doc = {"_id": ki_id, "@timestamp": "2026-11-18T00:00:00Z", "type": ki_type, "title": title,
           "description": description, "content": content, "tags": tags,
           "attributes": attributes or {}}
    if uri:
        doc["references"] = {"uri": uri}
    return doc


def index_profiles():
    """Hand-written routing profiles. `scripts/brain.sh workflow` can regenerate them with an LLM."""
    return [
        ki("profile-" + KNOWLEDGE, "index_metadata_entry", "Knowledge base: law and internal policies",
           "Index profile. Text documents: Swiss federal law by article and the bank's policies, "
           "procedures and memos. Does NOT contain: the list of outsourcing arrangements, incidents, "
           "numbers or statuses.",
           "Backing index: %s. Use it for what a rule says: requirements, approvals, deadlines, "
           "definitions in law or internal directives. Search by meaning with "
           "MATCH(body_semantic, \"question\"), in any language. Filter is_current == true to get "
           "versions in force. Key fields: title, body, language, doc_type, doc_number, version, "
           "is_current, valid_from, source_url. Example: FROM %s METADATA _score | WHERE "
           "MATCH(body_semantic, \"Auslagerung Kundendaten Genehmigung\") AND is_current == true | "
           "SORT _score DESC | KEEP title, version, body | LIMIT 5" % (KNOWLEDGE, KNOWLEDGE),
           ["index-profile", KNOWLEDGE], {"source_index": KNOWLEDGE}),
        ki("profile-" + INVENTORY, "index_metadata_entry", "Outsourcing inventory",
           "Index profile. Structured register of the bank's outsourcing arrangements. Does NOT "
           "contain: the rules themselves (see the knowledge base) or incidents.",
           "Backing index: %s. Use it for which arrangements exist and their facts: provider, data "
           "location (CH, EU, US), client data yes or no, approvals, contract and review dates, cost, "
           "status. Query with ES|QL filters and STATS, not text search. Key fields: arrangement_id, "
           "service, provider_code, provider_type, contains_client_data, data_location, "
           "approved_management, approved_ciso, approved_compliance, board_approval_eu, last_review, "
           "status. Example: FROM %s | WHERE contains_client_data == true AND data_location != \"CH\" "
           "| KEEP arrangement_id, service, data_location, board_approval_eu" % (INVENTORY, INVENTORY),
           ["index-profile", INVENTORY], {"source_index": INVENTORY}),
        ki("profile-" + INCIDENTS, "index_metadata_entry", "Incident register 2026",
           "Index profile. Structured register of security and operational incidents in 2026. Does "
           "NOT contain: provider details (join to the outsourcing inventory) or the reporting rules.",
           "Backing index: %s. Use it for counts and lists of incidents by category, severity, office "
           "or month, and whether they were reported within 24 hours. related_arrangement_id joins "
           "to arrangement_id in %s. Example: FROM %s | WHERE category == \"data_breach\" | STATS "
           "n = COUNT(*) BY reported_within_24h" % (INCIDENTS, INVENTORY, INCIDENTS),
           ["index-profile", INCIDENTS], {"source_index": INCIDENTS}),
    ]


def policy_register():
    """One entry per internal document number, derived from the documents' own metadata."""
    by_number = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "internal", "*.json"))):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        by_number.setdefault(d["doc_number"], []).append(d)
    out = []
    for number, versions in sorted(by_number.items()):
        versions.sort(key=lambda d: d["valid_from"])
        current = [d for d in versions if d["is_current"]][-1]
        old = [d for d in versions if not d["is_current"]]
        restricted = "all_staff" not in current["allowed_groups"]
        content = ("%s is \"%s\". Version in force: %s, valid from %s. Language: %s. Type: %s. "
                   "Owner: %s. %s%s Find the text in index %s with doc_number == \"%s\" AND "
                   "is_current == true."
                   % (number, current["title"], current["version"], current["valid_from"],
                      current["language"], current["doc_type"], current["department"],
                      "Withdrawn versions that must not be used: %s. "
                      % ", ".join("%s (valid until %s)" % (d["version"], d["valid_to"]) for d in old)
                      if old else "",
                      "Restricted to the compliance group. " if restricted else "",
                      KNOWLEDGE, number))
        out.append(ki("policy-" + number, "policy_register_entry", "%s: %s" % (number, current["title"]),
                      "Policy register entry: which version of %s is in force and where to find it."
                      % number, content, ["policy-register", number, current["language"]],
                      {"doc_number": number, "current_version": current["version"],
                       "valid_from": current["valid_from"], "language": current["language"],
                       "withdrawn_versions": [d["version"] for d in old],
                       "restricted": restricted}))
    return out


GLOSSARY = [
    ("outsourcing", "Auslagerung", "externalisation", "esternalizzazione",
     "Handing a function or data to an external provider. Governed by W-12."),
    ("client data (CID)", "Kundendaten", "données clients", "dati dei clienti",
     "Client-identifying data. In the inventory: contains_client_data."),
    ("service provider", "Dienstleister", "prestataire", "fornitore di servizi",
     "External company that performs an outsourced service. In the inventory: provider_code."),
    ("approval", "Genehmigung", "approbation", "approvazione",
     "Formal sign-off. In the inventory: approved_management, approved_ciso, approved_compliance."),
    ("executive board", "Geschäftsleitung", "direction générale", "direzione generale",
     "The bank's management. Not the board of directors."),
    ("board of directors", "Verwaltungsrat", "conseil d'administration", "consiglio di amministrazione",
     "Supervisory board. Must approve client data in the EU/EEA. In the inventory: board_approval_eu."),
    ("data breach", "Verletzung der Datensicherheit", "violation de la sécurité des données",
     "violazione della sicurezza dei dati", "In the incident register: category == data_breach. Governed by P-11."),
    ("directive", "Weisung", "directive", "direttiva", "Internal binding policy, numbered W-nn or D-nn."),
    ("money laundering", "Geldwäscherei", "blanchiment d'argent", "riciclaggio di denaro",
     "Governed by the Anti-Money Laundering Act (GwG, LBA, LRD)."),
    ("banking secrecy", "Bankkundengeheimnis", "secret bancaire", "segreto bancario",
     "Art. 47 Banking Act (BankG, LB, LBCR)."),
    ("annual review", "jährliche Überprüfung", "revue annuelle", "revisione annuale",
     "Yearly check of an outsourcing arrangement. In the inventory: last_review."),
    ("relationship manager", "Kundenberater", "conseiller à la clientèle", "consulente alla clientela",
     "Front-office adviser."),
]

DEFINITIONS = [
    ("def-review-overdue", "Review overdue",
     "An outsourcing arrangement's review is overdue when status is active and last_review is more "
     "than 12 months before today. Basis: W-12 v3.0 section 8 requires an annual review. ES|QL: FROM "
     "%s | WHERE status == \"active\" AND last_review < NOW() - 12 months | KEEP arrangement_id, "
     "service, last_review" % INVENTORY),
    ("def-data-location-compliant", "Data location compliant",
     "For arrangements with contains_client_data == true: data_location CH is compliant. EU is "
     "compliant only if board_approval_eu == true. Any other location (for example US) is never "
     "compliant. Basis: W-12 v3.0 section 5. Arrangements without client data are not restricted. "
     "ES|QL for violations: FROM %s | WHERE contains_client_data == true AND (data_location == "
     "\"US\" OR (data_location == \"EU\" AND board_approval_eu == false)) | KEEP arrangement_id, "
     "service, data_location, board_approval_eu" % INVENTORY),
    ("def-fully-approved", "Fully approved arrangement",
     "An arrangement is fully approved only when approved_management, approved_ciso and "
     "approved_compliance are all true. Basis: W-12 v3.0 section 4 requires all three before a "
     "contract is signed. ES|QL for gaps: FROM %s | WHERE NOT (approved_management AND approved_ciso "
     "AND approved_compliance) | KEEP arrangement_id, service, status" % INVENTORY),
    ("def-late-reported-breach", "Late-reported data breach",
     "A data breach is reported late when category == \"data_breach\" and reported_within_24h == "
     "false. Basis: procedure P-11 requires internal reporting within 24 hours. ES|QL: FROM %s | "
     "WHERE category == \"data_breach\" AND reported_within_24h == false" % INCIDENTS),
    ("def-material-outsourcing", "Material outsourcing (wesentliche Auslagerung)",
     "At Privatbank Albisgrat an outsourcing is material (German: wesentliche Auslagerung, French: "
     "externalisation essentielle, Italian: esternalizzazione essenziale) when it is active, contains "
     "client data, and either its criticality is high or its annual cost is CHF 200,000 or more. "
     "This is the Compliance definition used for reporting to the board. Criticality alone is not "
     "enough. ES|QL: FROM %s | WHERE status == \"active\" AND contains_client_data == true AND "
     "(criticality == \"high\" OR annual_cost_chf >= 200000) | KEEP arrangement_id, service, "
     "criticality, annual_cost_chf" % INVENTORY),
    ("def-reportable-incident", "Reportable incident (meldepflichtiger Vorfall)",
     "At Privatbank Albisgrat an incident is reportable to the executive board (German: "
     "meldepflichtiger Vorfall, French: incident à annoncer, Italian: incidente da segnalare) when it "
     "is a data_breach with severity medium or high, or an access_violation of any severity. "
     "Phishing attempts and system outages are not reportable. Quarters follow the calendar year. "
     "ES|QL: FROM %s | WHERE (category == \"data_breach\" AND severity IN (\"medium\", \"high\")) "
     "OR category == \"access_violation\" | KEEP incident_id, date, category, severity" % INCIDENTS),
    ("def-cloud-incident", "Cloud-related incident",
     "An incident is cloud-related when related_arrangement_id is set and the arrangement with that "
     "arrangement_id in %s has provider_type == \"cloud\". Two steps: first FROM %s | WHERE "
     "related_arrangement_id IS NOT NULL | STATS n = COUNT(*) BY related_arrangement_id; then check "
     "provider_type for those ids in %s." % (INVENTORY, INCIDENTS, INVENTORY)),
]


def create_ai_index():
    print("AI Index")
    es("DELETE", "/" + AI_INDEX, ok_missing=True)
    es("PUT", "/" + AI_INDEX)   # the ai-index-idx- prefix applies Elastic's managed mapping
    docs = index_profiles() + policy_register()
    for en, de, fr, it, note in GLOSSARY:
        docs.append(ki("glossary-" + en.replace(" ", "-").replace("(", "").replace(")", ""),
                       "glossary_entry", "%s = %s = %s = %s" % (en, de, fr, it),
                       "Glossary: the same term in English, German, French and Italian.",
                       "English: %s. German: %s. French: %s. Italian: %s. %s" % (en, de, fr, it, note),
                       ["glossary"], {"en": en, "de": de, "fr": fr, "it": it}))
    for def_id, title, content in DEFINITIONS:
        docs.append(ki(def_id, "business_definition", title,
                       "Business definition: how the bank computes \"%s\"." % title.lower(), content,
                       ["definition"]))
    lines = []
    for d in docs:
        doc_id = d.pop("_id")
        lines.append(json.dumps({"index": {"_index": AI_INDEX, "_id": doc_id}}))
        lines.append(json.dumps(d, ensure_ascii=False))
    out = es("POST", "/_bulk", "\n".join(lines) + "\n", ndjson=True, timeout=600)
    if out.get("errors"):
        bad = [it["index"]["error"] for it in out["items"] if it["index"].get("error")]
        sys.exit("Bulk errors: %s" % json.dumps(bad[0])[:500])
    es("POST", "/%s/_refresh" % AI_INDEX)
    counts = es("POST", "/%s/_search" % AI_INDEX,
                {"size": 0, "aggs": {"t": {"terms": {"field": "type"}}}})
    info("%s: %s" % (AI_INDEX, ", ".join("%s %d" % (b["key"], b["doc_count"])
                                          for b in counts["aggregations"]["t"]["buckets"])))


# ------------------------------------------------------------------- agents

KI_QUERY = (
    "FROM %s METADATA _id, _index, _score "
    "| FORK (WHERE MATCH(content, ?question) OR MATCH(title, ?question) | SORT _score DESC | LIMIT 15) "
    "(WHERE MATCH(content.semantic, ?question) OR MATCH(description.semantic, ?question) "
    "| SORT _score DESC | LIMIT 15) "
    "| FUSE | SORT _score DESC | KEEP type, title, content | LIMIT 8" % AI_INDEX)

BRAIN_INSTRUCTIONS = """You are the company brain of Privatbank Albisgrat AG, a fictional Swiss private bank. You answer questions that need facts from the bank's registers and rules from its policies.

How to work:
1. First call the tool that retrieves Knowledge Indicators, once, with the user's question. Knowledge Indicators tell you which index holds what, which policy version is in force, what the bank's terms mean in four languages, and how the bank defines its measures. Trust them: do not inspect mappings or list indices.
2. Then query the indices the Knowledge Indicators point to, with ES|QL. Use the definitions and example queries they give. Query each index at most twice.
3. Answer only from query results. Name every arrangement or incident by its id. Cite the policy and section a rule comes from, as given in the Knowledge Indicators or the policy text.
4. Be brief: a short table or at most six bullet points, then one line "Based on:" listing the indices and Knowledge Indicators you used.
5. Answer in the language of the question."""

BASELINE_INSTRUCTIONS = """You are an assistant for Privatbank Albisgrat AG, a fictional Swiss private bank. You answer questions from the bank's Elasticsearch indices whose names start with "albisgrat-". You do not know in advance what they contain: explore them with your tools, then answer only from query results. Name every arrangement or incident by its id and cite the policy a rule comes from. Be brief. Answer in the language of the question."""

PLATFORM_QUERY_TOOLS = ["platform.core.execute_esql", "platform.core.search"]
PLATFORM_EXPLORE_TOOLS = ["platform.core.list_indices", "platform.core.get_index_mapping",
                          "platform.core.generate_esql", "platform.core.index_explorer"]


def create_agents():
    print("Agents")
    for agent_id in (AGENT_BRAIN, AGENT_BASELINE):
        kb("DELETE", "/api/agent_builder/agents/" + agent_id, ok_missing=True)
    kb("DELETE", "/api/agent_builder/tools/" + KI_TOOL, ok_missing=True)
    kb("POST", "/api/agent_builder/tools", {
        "id": KI_TOOL, "type": "esql",
        "description": "Retrieve Knowledge Indicators: pre-computed context about the bank's data. "
                       "Returns which index answers the question, the policy version in force, "
                       "glossary terms and business definitions with example queries. Call this "
                       "first, once, before any other tool.",
        "tags": ["albisgrat", "context"],
        "configuration": {"query": KI_QUERY, "params": {
            "question": {"type": "string",
                         "description": "The user's question, plus key terms in German if it is "
                                        "in another language."}}}})
    info("tool %s" % KI_TOOL)
    kb("POST", "/api/agent_builder/agents", {
        "id": AGENT_BRAIN, "name": "Albisgrat Company Brain",
        "description": "Answers questions across the bank's registers and policies. Reads "
                       "Knowledge Indicators from the AI Index first.",
        "labels": ["demo", "brain"], "avatar_color": "#BFDBFF", "avatar_symbol": "CB",
        "configuration": {"instructions": BRAIN_INSTRUCTIONS,
                          "tools": [{"tool_ids": [KI_TOOL] + PLATFORM_QUERY_TOOLS}]}})
    info("agent %s (with Knowledge Indicators)" % AGENT_BRAIN)
    kb("POST", "/api/agent_builder/agents", {
        "id": AGENT_BASELINE, "name": "Albisgrat Baseline (no context)",
        "description": "Same model and data, no Knowledge Indicators. Explores the indices itself.",
        "labels": ["demo", "baseline"], "avatar_color": "#E4E4E4", "avatar_symbol": "BL",
        "configuration": {"instructions": BASELINE_INSTRUCTIONS,
                          "tools": [{"tool_ids": PLATFORM_QUERY_TOOLS + PLATFORM_EXPLORE_TOOLS}]}})
    info("agent %s (baseline)" % AGENT_BASELINE)


WORKFLOW_ID = "albisgrat-index-profile-ki"


def run_workflow():
    """Create the Kibana Workflow that profiles each source index with an LLM, run it, and wait.
    It overwrites the three hand-written index profiles with generated ones. Uses the LLM."""
    import time
    print("Workflow")
    with open(os.path.join(HERE, "workflow-index-profiles.yaml"), encoding="utf-8") as f:
        yaml_text = f.read()
    existing = kb("GET", "/api/workflows/workflow/" + WORKFLOW_ID, ok_missing=True)
    if existing:
        out = kb("PUT", "/api/workflows/workflow/" + WORKFLOW_ID, {"yaml": yaml_text})
    else:
        out = kb("POST", "/api/workflows/workflow", {"id": WORKFLOW_ID, "yaml": yaml_text})
    if not out.get("valid", True):
        sys.exit("Kibana says the workflow is not valid. Open it under Workflows to see why.")
    info("workflow %s saved" % WORKFLOW_ID)
    run = kb("POST", "/api/workflows/workflow/%s/run" % WORKFLOW_ID, {"inputs": {}})
    execution = run["workflowExecutionId"]
    for _ in range(60):
        state = kb("GET", "/api/workflows/executions/" + execution)
        if state.get("status") not in ("pending", "running", "waiting"):
            break
        time.sleep(6)
    info("run %s after %ds" % (state.get("status"), (state.get("duration") or 0) / 1000))
    es("POST", "/%s/_refresh" % AI_INDEX)
    found = es("POST", "/%s/_count" % AI_INDEX, {"query": {"term": {"tags": "generated-by-workflow"}}})
    info("%d index profiles generated by the workflow" % found["count"])


def upsert_definitions():
    """Write the business definitions again without touching the other Knowledge Indicators."""
    print("Business definitions")
    lines = []
    for def_id, title, content in DEFINITIONS:
        d = ki(def_id, "business_definition", title,
               "Business definition: how the bank computes \"%s\"." % title.lower(), content,
               ["definition"])
        d.pop("_id")
        lines.append(json.dumps({"index": {"_index": AI_INDEX, "_id": def_id}}))
        lines.append(json.dumps(d, ensure_ascii=False))
    out = es("POST", "/_bulk", "\n".join(lines) + "\n", ndjson=True)
    if out.get("errors"):
        sys.exit("Bulk errors: %s" % json.dumps(out["items"][0])[:400])
    es("POST", "/%s/_refresh" % AI_INDEX)
    info("%d definitions written" % len(DEFINITIONS))


def status():
    for index in (KNOWLEDGE, INVENTORY, INCIDENTS, AI_INDEX):
        try:
            info("%-34s %d documents" % (index, es("GET", "/%s/_count" % index)["count"]))
        except ApiError:
            info("%-34s missing" % index)
    for agent_id in (AGENT_BRAIN, AGENT_BASELINE):
        found = kb("GET", "/api/agent_builder/agents/" + agent_id, ok_missing=True)
        info("agent %-28s %s" % (agent_id, "present" if found else "missing"))


def delete_all():
    for agent_id in (AGENT_BRAIN, AGENT_BASELINE):
        kb("DELETE", "/api/agent_builder/agents/" + agent_id, ok_missing=True)
    kb("DELETE", "/api/agent_builder/tools/" + KI_TOOL, ok_missing=True)
    kb("DELETE", "/api/workflows/workflow/" + WORKFLOW_ID, ok_missing=True)
    for index in (KNOWLEDGE, INVENTORY, INCIDENTS, AI_INDEX):
        es("DELETE", "/" + index, ok_missing=True)
    info("deleted")


def main():
    if not ES_URL or not KIBANA_URL or not API_KEY:
        sys.exit("Set BRAIN_ELASTICSEARCH_URL, BRAIN_KIBANA_URL and BRAIN_API_KEY (see .env.example)")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"sources": [create_sources], "ai-index": [create_ai_index], "agents": [create_agents],
             "workflow": [run_workflow], "definitions": [upsert_definitions],
             "all": [create_sources, create_ai_index, create_agents]}
    try:
        if cmd in steps:
            for step in steps[cmd]:
                step()
        elif cmd == "status":
            status()
        elif cmd == "delete":
            delete_all()
        else:
            sys.exit(__doc__)
    except ApiError as err:
        sys.exit("API error during '%s': %s" % (cmd, err))


if __name__ == "__main__":
    main()
