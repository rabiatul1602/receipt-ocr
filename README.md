# 🧾 Receipt OCR — Total Amount Extractor
Extracts the total amount from receipt images using EasyOCR and spatial proximity matching. Designed to handle the layout inconsistency of Malaysian thermal receipts, where total keywords and their amounts are often on separate lines.


## Overview

A Jupyter Notebook pipeline that reads receipt images and extracts the **total amount charged** — the single most critical field for claims automation. Built lean: no cloud APIs, no training overhead, runs fully local.

---

## Engine Decision

| Engine | Verdict | Reason |
|--------|---------|--------|
| EasyOCR | ✅ Chosen | Best number accuracy on thermal receipts |
| Tesseract | ❌ Rejected | Fails on bold receipt fonts — misses numbers |
| Google Cloud Vision | ❌ Rejected | Requires paid deposit, not viable |

---

## Preprocessing Findings

| Technique | Verdict | Reason |
|-----------|---------|--------|
| Raw image | ✅ Best | Baseline, cleanest number reads |
| Upscale only | ✅ Acceptable | Minor improvement on small text |
| Upscale + Binarization | ❌ Rejected | Destroys thermal receipt output entirely |

> **Rule:** When in doubt, feed the raw image. Less is more with thermal receipts.

---

## Extraction Strategy

### The Core Problem
Receipt layouts are inconsistent — the total amount is not always printed on the same line as the keyword. It can appear to the right, or on the line below.

### The Solution — Spatial Anchoring
Rather than parsing text on the same line as "TOTAL", we locate the amount whose **vertical position on the page is closest** to the TOTAL keyword. This makes the extractor layout-agnostic.

```
TOTAL ←── keyword detected here (y = 430)
59,00 ←── closest amount by y-distance ✅ picked
69,00 ←── further away ❌ skipped
```

### Keyword Coverage
Malaysian receipts use various synonyms for total. The keyword list is an evolving registry:

- English — `TOTAL`, `AMOUNT DUE`, `CREDIT CARD`, `DEBIT CARD`
- Malay — `JUMLAH`, `AMAUN BAYARAN`, `TUNAI`, `BAKI`, `KREDIT KAD`

> This list expands as new receipt formats are encountered in the wild.

---

## Design Principles

**Fix upstream, not downstream**
Bad OCR is addressed at the source — better preprocessing or model improvement. Output is never silently corrected.

**Trust confidence scores**
Every detection comes with a confidence value. Low-confidence results are flagged for human review, not auto-accepted.

**Spatial over textual**
Bounding box position is more reliable than text layout for varied receipt formats. Always anchor by geometry.

---

## Current Scope

| Field | Status |
|-------|--------|
| Total amount | ✅ In scope |
| Date | 🔜 Next |
| Store name | 🔜 Next |
| Line items | ⏳ Future |

---

## Roadmap

- [ ] Finalise Malaysian receipt keyword synonyms
- [ ] Graceful fallback when no keyword or amount is detected
- [ ] Validate extraction across diverse receipt samples
- [ ] Wrap into single reusable function `extract_total(image_path)`
- [ ] Evaluate fine-tuning if accuracy plateaus on edge cases
