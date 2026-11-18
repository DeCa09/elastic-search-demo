#!/usr/bin/env python3
"""Generate the two fictional structured datasets for the company-brain demo.

  outsourcing_inventory.jsonl  the bank's register of outsourcing arrangements
  incidents.jsonl              the incident register

Everything is invented. Providers have code names only. The output is deterministic
(fixed seed) and committed, so you only run this to change the data.
A few rows break the bank's own directive W-12 on purpose; the demo questions find them.
"""
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
random.seed(2026)

SERVICES = [
    ("Core banking backup", "cloud", True, "high"), ("E-mail archiving", "cloud", True, "high"),
    ("CRM hosting", "cloud", True, "high"), ("Client reporting portal", "cloud", True, "high"),
    ("Payroll processing", "it_services", False, "medium"), ("Statement printing", "print", True, "medium"),
    ("Card payment processing", "payments", True, "high"), ("Video identification", "cloud", True, "high"),
    ("Market data feed", "it_services", False, "low"), ("Document scanning", "it_services", True, "medium"),
    ("Sanctions screening service", "cloud", True, "high"), ("Service desk tooling", "cloud", False, "low"),
    ("Translation service", "it_services", False, "low"), ("Portfolio analytics", "cloud", True, "medium"),
    ("Website hosting", "cloud", False, "low"), ("Secure e-mail gateway", "cloud", True, "high"),
    ("Telephony recording", "cloud", True, "medium"), ("HR recruiting platform", "cloud", False, "low"),
    ("Data warehouse test environment", "cloud", True, "medium"), ("Tax reporting", "it_services", True, "medium"),
    ("Client onboarding app", "cloud", True, "high"), ("Physical archive storage", "it_services", True, "low"),
    ("Collaboration suite", "cloud", False, "medium"), ("Transaction monitoring engine", "cloud", True, "high"),
]
DEPTS = ["Operations", "IT Security", "Front Office", "Compliance", "Legal", "Finance"]
OFFICES = ["Zurich", "Geneva", "Lugano"]

# arrangement index -> deliberate deviation from directive W-12
EU_NO_BOARD = {2, 13}        # client data in the EU without approval of the Verwaltungsrat
US_LOCATION = {18}           # client data outside CH and EU/EEA: not allowed at all
MISSING_CISO = {20}          # contract signed without CISO approval
OVERDUE_REVIEW = {1, 6, 9}   # last review more than 12 months ago
EU_WITH_BOARD = {3}          # client data in the EU, properly approved

inventory = []
for i, (service, ptype, cid, crit) in enumerate(SERVICES):
    n = i + 1
    location = "CH"
    board = False
    if i in EU_NO_BOARD or i in EU_WITH_BOARD:
        location, board = "EU", i in EU_WITH_BOARD
    if i in US_LOCATION:
        location = "US"
    if not cid and random.random() < 0.4:
        location = random.choice(["EU", "CH"])
    signed = "%d-%02d-%02d" % (random.choice([2022, 2023, 2024, 2025]), random.randint(1, 12), random.randint(1, 28))
    review = "2025-%02d-%02d" % (random.randint(1, 10), random.randint(1, 28)) if i in OVERDUE_REVIEW \
        else "2026-%02d-%02d" % (random.randint(1, 10), random.randint(1, 28))
    status = "planned" if i in (20,) else "active"
    inventory.append({
        "arrangement_id": "OUT-%03d" % n,
        "service": service,
        "provider_code": "Provider %s" % chr(ord("A") + i),
        "provider_type": ptype,
        "contains_client_data": cid,
        "data_location": location,
        "approved_management": True,
        "approved_ciso": i not in MISSING_CISO,
        "approved_compliance": True,
        "board_approval_eu": board,
        "contract_signed": signed,
        "last_review": review,
        "business_owner_dept": random.choice(DEPTS),
        "criticality": crit,
        "status": status,
        "annual_cost_chf": random.choice([18000, 42000, 65000, 90000, 120000, 240000, 310000]),
        "office": random.choice(OFFICES),
    })

SUMMARIES = {
    "data_breach": ["Unmaskierte Kundendaten in einer Testumgebung entdeckt.",
                    "Courriel contenant des données clients envoyé au mauvais destinataire.",
                    "Documento con dati dei clienti trovato su una stampante condivisa."],
    "phishing": ["Phishing-Mail von Mitarbeitenden gemeldet, kein Klick.",
                 "Tentative d'hameçonnage ciblant le service clientèle.",
                 "E-mail di phishing con allegato sospetto bloccata."],
    "system_outage": ["Ausfall des Kundenportals während 40 Minuten.",
                      "Indisponibilité de la messagerie sécurisée.",
                      "Interruzione del servizio di identificazione video."],
    "access_violation": ["Zugriff eines Dienstleisters ausserhalb des bewilligten Zeitfensters.",
                         "Compte de support du prestataire resté actif après la fin du mandat.",
                         "Accesso amministrativo non registrato nel giornale."],
}
CLOUD_IDS = [r["arrangement_id"] for r in inventory if r["provider_type"] == "cloud"]

incidents = []
for n in range(1, 43):
    cat = random.choices(list(SUMMARIES), weights=[3, 5, 4, 2])[0]
    month = random.randint(1, 10)
    related = random.choice(CLOUD_IDS) if cat in ("system_outage", "access_violation") or \
        (cat == "data_breach" and random.random() < 0.5) else None
    lang = random.randint(0, 2)
    late = cat == "data_breach" and random.random() < 0.3
    incidents.append({
        "incident_id": "INC-2026-%03d" % n,
        "date": "2026-%02d-%02d" % (month, random.randint(1, 28)),
        "category": cat,
        "severity": random.choices(["low", "medium", "high"], weights=[5, 4, 2])[0],
        "office": OFFICES[lang],
        "language": ["de", "fr", "it"][lang],
        "related_arrangement_id": related,
        "reported_within_24h": not late,
        "status": random.choice(["closed", "closed", "closed", "open"]),
        "summary": SUMMARIES[cat][lang],
    })
# The incident behind the confidential memo of demo 1 (Projekt Enzian).
incidents.append({"incident_id": "INC-2026-043", "date": "2026-03-17", "category": "data_breach",
                  "severity": "high", "office": "Zurich", "language": "de",
                  "related_arrangement_id": "OUT-019", "reported_within_24h": False, "status": "closed",
                  "summary": "Unmaskierte Kundendaten von 312 Kunden während 9 Tagen in einer Testumgebung bei einem Cloud-Anbieter."})

for name, rows in (("outsourcing_inventory.jsonl", inventory), ("incidents.jsonl", incidents)):
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("%s: %d rows" % (name, len(rows)))
