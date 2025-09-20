
## Goals

- Ingest **authoritative legal/regulatory texts** (Lovdata, Skatteetaten, Altinn)
- Normalize them into structured tables (`law`, `law_section`, `rate_table`, `spec_node`)
- Generate **gold JSONL** datasets ready for LoRA fine-tuning (glossary + synthetic chats)
- Provide a clean, extensible ingestion pipeline that grows with new data sources (e.g., bank feeds, invoices)

## Next Steps

1. Implement parsers for Lovdata HTML, SAF-T docs, and Altinn pages.
2. Run ingestion scripts to populate `bronze/` and `silver/`.
3. Export **gold JSONL** for training (`tax_glossary`, `accounting_glossary`, `client_synth_chat`).
