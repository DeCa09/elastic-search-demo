# location

Agent: With Knowledge Indicators

Question: Which outsourcing arrangements store client data outside Switzerland, and does our directive allow each of them?

Expected records: OUT-003, OUT-004, OUT-014, OUT-019

Tools called: albisgrat.brain.query_ki, platform.core.execute_esql, platform.core.execute_esql

---

Excellent! I now have all the information needed to answer the question. Let me provide a clear summary.

## Outsourcing arrangements storing client data outside Switzerland

Four arrangements store client data outside Switzerland:

| Arrangement | Service | Location | Board Approval EU | Status | Compliant? |
|-------------|---------|----------|-------------------|---------|------------|
| **OUT-003** | CRM hosting | EU | No | Active | ❌ **No** |
| **OUT-004** | Client reporting portal | EU | Yes | Active | ✅ **Yes** |
| **OUT-014** | Portfolio analytics | EU | No | Active | ❌ **No** |
| **OUT-019** | Data warehouse test environment | US | No | Active | ❌ **No** |

### Directive rules (W-12 v3.0, section 5):
- **Switzerland**: Client data may be stored in CH (allowed)
- **EU/EEA**: Storage permitted **only with board approval**
- **Other countries** (including US): **Not permitted** under any circumstances

### Summary:
- **1 compliant**: OUT-004 (has required board approval for EU storage)
- **3 non-compliant**: 
  - OUT-003 and OUT-014 store data in EU without board approval
  - OUT-019 stores data in US, which is prohibited entirely

**Based on:** albisgrat-outsourcing-inventory, albisgrat-knowledge (W-12 v3.0), Knowledge Indicators business definition "Data location compliant"
