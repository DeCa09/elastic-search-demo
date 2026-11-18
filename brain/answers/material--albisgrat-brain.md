# material

Agent: With Knowledge Indicators

Question: Welche unserer Auslagerungen gelten als wesentliche Auslagerungen? Liste die IDs auf.

Expected records: OUT-001, OUT-002, OUT-003, OUT-004, OUT-006, OUT-007, OUT-008, OUT-010, OUT-011, OUT-016, OUT-019, OUT-024

Tools called: albisgrat.brain.query_ki, platform.core.execute_esql

---

Folgende Auslagerungen gelten als **wesentliche Auslagerungen**:

• **OUT-001** – Core banking backup (hohe Kritikalität)
• **OUT-002** – E-mail archiving (hohe Kritikalität)
• **OUT-003** – CRM hosting (hohe Kritikalität)
• **OUT-004** – Client reporting portal (hohe Kritikalität)
• **OUT-006** – Statement printing (CHF 310'000)
• **OUT-007** – Card payment processing (hohe Kritikalität)
• **OUT-008** – Video identification (hohe Kritikalität)
• **OUT-010** – Document scanning (CHF 240'000)
• **OUT-011** – Sanctions screening service (hohe Kritikalität)
• **OUT-016** – Secure e-mail gateway (hohe Kritikalität)
• **OUT-019** – Data warehouse test environment (CHF 310'000)
• **OUT-024** – Transaction monitoring engine (hohe Kritikalität)

**Basierend auf:** Index albisgrat-outsourcing-inventory; Knowledge Indicator "Material outsourcing (wesentliche Auslagerung)" – Definition gemäss Compliance: aktiv, enthält Kundendaten, und entweder hohe Kritikalität oder Jahreskosten ≥ CHF 200'000.
