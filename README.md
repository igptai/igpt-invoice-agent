# iGPT Invoice/Receipt Extraction Agent

This repo contains an example of an **invoice/receipt extraction agent** built on top of the `igptai` client.

The agent sends a single, carefully designed **system prompt** plus a **strict JSON schema** to iGPT’s `recall.ask()` endpoint. iGPT then searches the user’s connected data (e.g., email messages and their attachments such as PDF/HTML) and returns a **validated JSON** payload containing extracted invoices/receipts.

## What the agent does (exactly)

1. **Loads credentials**
   - Reads `IGPT_API_KEY` and `IGPT_API_USER` from environment variables.
   - If missing, prompts securely using `getpass` (so the key isn’t echoed in your terminal).

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

## Requirements

- Python **>= 3.8**

## Setup

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

4. Run:
```bash
python3 app.py
```
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
        "query_terms": ['invoice', 'receipt', 'payment', 'order', 'subscription', 'renewal']
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
        "source_attachment_filenames": ["InvoiceINV-10492.pdf" ],
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