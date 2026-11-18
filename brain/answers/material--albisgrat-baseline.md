# material

Agent: Baseline, no context

Question: Welche unserer Auslagerungen gelten als wesentliche Auslagerungen? Liste die IDs auf.

Expected records: OUT-001, OUT-002, OUT-003, OUT-004, OUT-006, OUT-007, OUT-008, OUT-010, OUT-011, OUT-016, OUT-019, OUT-024

Tools called: platform.core.index_explorer, platform.core.search, platform.core.get_index_mapping, platform.core.generate_esql, platform.core.execute_esql

---

Basierend auf den Daten im Outsourcing-Inventar gelten folgende Auslagerungen als **wesentliche Auslagerungen** (Kritikalität: high):

- **OUT-001** – Core banking backup
- **OUT-002** – E-mail archiving
- **OUT-003** – CRM hosting
- **OUT-004** – Client reporting portal
- **OUT-007** – Card payment processing
- **OUT-008** – Video identification
- **OUT-011** – Sanctions screening service
- **OUT-016** – Secure e-mail gateway
- **OUT-021** – Client onboarding app
- **OUT-024** – Transaction monitoring engine

Insgesamt haben wir **10 wesentliche Auslagerungen**.
