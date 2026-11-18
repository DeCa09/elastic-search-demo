# location

Agent: Baseline, no context

Question: Which outsourcing arrangements store client data outside Switzerland, and does our directive allow each of them?

Expected records: OUT-003, OUT-004, OUT-014, OUT-019

Tools called: platform.core.search, platform.core.search, platform.core.search, platform.core.search, platform.core.list_indices, platform.core.search, platform.core.search, platform.core.search, platform.core.generate_esql, platform.core.execute_esql

---

Perfect! Now I have all the information needed to answer the question. Let me provide a clear summary.

Based on your data, **four outsourcing arrangements** store client data outside Switzerland:

## EU Storage (permitted with board approval):

1. **OUT-003** – CRM hosting (Provider C)
   - Location: EU
   - Board approval: **No** ❌

2. **OUT-004** – Client reporting portal (Provider D)
   - Location: EU
   - Board approval: **Yes** ✓

3. **OUT-014** – Portfolio analytics (Provider N)
   - Location: EU
   - Board approval: **No** ❌

## US Storage (prohibited):

4. **OUT-019** – Data warehouse test environment (Provider S)
   - Location: US
   - Board approval: **No** ❌

---

### Compliance Assessment per Directive W-12, Section 5:

**Directive rule:** Client-identifying data may only be stored in Switzerland. Storage in the EU or EEA requires prior board approval (*Verwaltungsrat*). Other countries are prohibited.

**Result:**
- **OUT-004**: ✓ Compliant (EU with board approval)
- **OUT-003**: ❌ Non-compliant (EU without board approval)
- **OUT-014**: ❌ Non-compliant (EU without board approval)
- **OUT-019**: ❌ Non-compliant (US storage is prohibited regardless of approval)
