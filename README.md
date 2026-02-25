## 👋 Welcome to the iGPT Invoice Extraction Agent!

This repository shows how to extract invoices and receipts from email using a single API call to [iGPT](https://www.igpt.ai). The agent connects to iGPT using an API key, scans email threads and PDF attachments, and returns structured, deduplicated invoice data as validated JSON.

No MIME parsing, OCR pipeline, or attachment handling code. 

Just a prompt, a schema, and the iGPT API.

```python
from igptai import IGPT

client = IGPT(api_key="...", user="...")
result = client.recall.ask(input=SYSTEM_PROMPT, output_format=OUTPUT_FORMAT)
# → validated JSON: vendor, amount, dates, line items, payment status, source provenance
```

Returns structured, schema-validated JSON in ~3 seconds, even across large inboxes.

The project is designed for easy customization and extension, allowing you to:

- Target different document types (contracts, SOWs, purchase orders)
- Adjust extraction rules and output schemas
- Plug into any orchestration framework (LangChain, LangGraph, CrewAI)

## Why This Is Hard Without iGPT

Email threads contain 10-15x duplicate content from nested quoting. Attachments disagree with body text. Invoices get forwarded, CC'd, and duplicated across inboxes. Renewals look like invoices but aren't always. PDFs require document extraction and normalization. Most teams end up building custom Gmail API logic, PDF parsing pipelines, and deduplication layers from scratch. This repo skips all of that.

**Use this pattern to:** sync SaaS invoices into QuickBooks or Xero, track renewals across shared finance inboxes, reconcile subscription charges from forwarded receipts, or power an autonomous finance agent.

## 🚀 Features

- 📎 **Attachment-aware extraction** — Reads PDF and HTML invoices attached to emails, not just email body text
- 🧹 **Automatic deduplication** — Stable `dedupe_key` per invoice prevents double-counting across forwarded or CC'd threads
- 📐 **Strict JSON schema** — Output validated against a JSON schema server-side, so downstream systems can trust the structure
- 🔗 **Source provenance** — Each invoice record includes the source message ID, subject, sender, timestamp, and attachment filenames
- 🔒 **User-scoped isolation** — Each API call is isolated to the authenticated user's data
- ⚡ **Single API call** — The entire extraction runs through one `recall.ask()` call

## Architecture


![diagram (1)](/assets/diagram.svg)



**Connect** your email datasource → **Ask** iGPT to extract invoices using a system prompt + JSON schema → **Get back** validated, structured invoice records with source provenance.

---

## How It Works

1. **Loads credentials**
   - Reads `IGPT_API_KEY` and `IGPT_API_USER` from environment variables.
   - If missing, prompts securely using `getpass` (so the key isn't echoed in your terminal).

2. **Creates an iGPT client**
   - `client = IGPT(api_key=..., user=...)`

3. **Checks whether you already have datasources connected**
   - If no datasources are connected yet, the agent requests an authorization URL.
   - The run stops and prints the authorization URL so you can connect your data, then you re-run the script.

4. **Runs an extraction request**
   - Calls:
     - `client.recall.ask(input=SYSTEM_PROMPT, output_format=OUTPUT_FORMAT)`
   - `SYSTEM_PROMPT` tells the model to:
     - find invoice-like documents (invoices, receipts, renewals with totals, refunds/credit memos)
     - treat invoice attachments as the source of truth when they disagree with the email text
     - use `dedupe_key` as a stable, normalized unique key to detect duplicate emails or files for the same invoice
     - leave any unavailable fields as `null` (never infer missing values)
     - standardize dates/currency/amount formats for consistency
     - classify each record into a fixed `invoice_type` enum

5. **Returns strict JSON**
   - `OUTPUT_FORMAT` enforces a strict schema:
     - top-level keys: `run_metadata` and `invoices`
     - each invoice includes vendor info, amounts, dates, payment status, provenance fields (message id/subject/from/received timestamp), attachment filenames, and optional notes
   - `app.py` prints either the error response or the structured output.

---

## 📂 Repo Structure

```
├── app.py                  # Entry point: runs the agent
├── igpt/
│   ├── __init__.py         # Exports IgptAgent, SYSTEM_PROMPT, OUTPUT_FORMAT
│   ├── agent.py            # IgptAgent class: auth check → extraction → output
│   ├── prompts.py          # System prompt defining extraction rules
│   └── schema.py           # JSON schema enforcing output structure
├── requirements.txt
├── LICENSE.txt
└── .gitignore
```

---

## 🛠️ Setup

**Requirements:** Python >= 3.8

1. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
python3 -m pip install -r requirements.txt
```

3. Set environment variables:
```bash
export IGPT_API_KEY="your-igpt-api-key"
export IGPT_API_USER="your-igpt-api-user"
```
If they are not set, `app.py` will prompt you via `getpass`.

You can create your iGPT API key [here](https://igpt.ai/hub/apikeys/).

4. Run:
```bash
python3 app.py
```

---

## Output

On success, the program prints a JSON object shaped like:

- `run_metadata`: when the run was generated + optional search metadata
- `invoices`: array of extracted invoice/receipt records, each matching the schema in `schema.py`

### Output example

> Note: values below are illustrative. Fields may be `null` if not explicitly present in the source.

```json
{
    "run_metadata": {
        "generated_at_utc": "2026-01-22T14:52:59Z",
        "date_range": "2025-01-01..2026-01-22",
        "query_terms": ["invoice", "receipt", "payment", "order", "subscription", "renewal"]
    },
    "invoices": [{
        "invoice_type": "subscription",
        "vendor_name": "Example SaaS Inc.",
        "vendor_domain": "example.com",
        "vendor_billing_email": "billing@example.com",
        "invoice_number": "INV-10492",
        "order_id": null,
        "invoice_date": "2026-01-10",
        "due_date": null,
        "service_period_start": "2026-01-10",
        "service_period_end": "2026-02-10",
        "plan_name": "Pro",
        "billing_interval": "monthly",
        "seats": 5,
        "usage_window_start": null,
        "usage_window_end": null,
        "description": "Pro plan subscription (5 seats)",
        "currency": "USD",
        "subtotal_amount": 100.0,
        "discount_amount": null,
        "tax_amount": 0.0,
        "total_amount": 100.0,
        "payment_status": "paid",
        "paid_date": "2026-01-10",
        "payment_method": "Visa **** 4242",
        "line_items": [{
            "description": "Pro plan (5 seats) - Jan 10, 2026 to Feb 10, 2026",
            "quantity": 5,
            "unit_price_amount": 20.0,
            "amount": 100.0
        }],
        "source_id": "msg01HZYXABC123",
        "source_subject": "Your Example SaaS receipt (INV-10492)",
        "source_from": "Example SaaS Billing billing@example.com",
        "source_occurred_at_utc": "2026-01-10T08:15:22Z",
        "source_attachment_filenames": ["InvoiceINV-10492.pdf"],
        "source_filename": null,
        "extraction_notes": [
            "Evidence(invoice_date): attachment:InvoiceINV-10492.pdf -> \"Invoice Date: Jan 10, 2026\"",
            "Evidence(total_amount): attachment:InvoiceINV-10492.pdf -> \"Total: $100.00\"",
            "Evidence(paid_date): emailbody -> \"Payment processed on Jan 10, 2026\"",
            "Attachment values preferred over email body where conflicts occurred."
        ],
        "dedupe_key": "example.com_inv-10492"
    }]
}
```

---

## 🔧 Customization

**Change what gets extracted** — Edit `igpt/prompts.py` to target different document types (contracts, SOWs, purchase orders) or adjust extraction rules.

**Change the output shape** — Edit `igpt/schema.py` to add or remove fields. iGPT enforces the schema server-side, so your output will always match.

**Add a date range** — Limit extraction to a specific time window to improve performance and control. For example, restrict to the last 7 days or a fixed range like `2026-02-01..2026-02-24`.

**Add custom query terms** — Focus on messages containing specific keywords or vendors (e.g., `renewal`, `payment confirmation`, `Apple Inc`, `Figma`) to narrow extraction scope.

**Extend invoice types** — Add entries to the `invoice_type` enum in the system prompt if your business requires additional billing model classifications beyond the defaults.

**Add to an existing agent** — The core extraction is a single function call:

```python
from igptai import IGPT

client = IGPT(api_key="...", user="...")
result = client.recall.ask(
    input="<your prompt>",
    output_format={"schema": your_json_schema}
)
```

Works with any orchestration framework (LangChain, LangGraph, CrewAI) or standalone.

## 💡 Ideas for What to Build Next

**Store the data** — Save results to a database, push to an ERP system, or export to CSV for further analysis.

**Build a dashboard** — Monitor monthly spend across vendors, track active subscriptions, or visualize payment trends over time.

**Automate it** — Run extraction on a daily or weekly schedule and store results as they come in. Set up alerts when an invoice exceeds a threshold. Auto-approve low-value invoices below a set amount. Create reminders before `service_period_end` dates to catch upcoming renewals.

---

## 🔗 Related

- [iGPT Python SDK](https://github.com/igptai/igptai-python) — `pip install igptai`
- [iGPT Node.js SDK](https://github.com/igptai/igptai-node) — `npm install igptai`
- [API Documentation](https://docs.igpt.ai) — Full endpoint reference
- [Playground](https://igpt.ai/hub/playground) — Try queries interactively before writing code

---

## License

MIT
