import streamlit as st
import easyocr
import cv2
import numpy as np
import re
from PIL import Image

# ── config ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="resit-ocr", page_icon="🧾", layout="centered")

TOTAL_KEYWORDS = [
    'total', 'grand total', 'total amount', 'amount due', 'amount payable',
    'net total', 'subtotal', 'balance due', 'total payable',
    'debit card', 'credit card', 'kredit card', 'cash', 'tunai',
    'e-wallet', 'touch n go', 'grab pay', 'boost', 'maybank qr',
    'jumlah', 'jumlah besar', 'jumlah bayaran', 'jumlah keseluruhan',
    'amaun', 'amaun bayaran', 'amaun perlu dibayar', 'amaun dibayar',
    'baki', 'baki perlu dibayar', 'bayaran', 'dibayar', 'diterima',
    'jml', 'amt', 'ttl',
]
AMOUNT_PATTERN = r'\d{1,6}[.,]\d{2}'

# ── reader (cached so it only loads once) ─────────────────────────────────────
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

# ── core logic ────────────────────────────────────────────────────────────────
def find_total(results_detail, y_tolerance=80):
    keyword_lines = []
    amount_lines = []

    for bbox, text, conf in results_detail:
        top_y = min(p[1] for p in bbox)
        text_lower = text.lower()
        if any(kw in text_lower for kw in TOTAL_KEYWORDS):
            keyword_lines.append((top_y, text))
        if re.search(AMOUNT_PATTERN, text):
            amount_lines.append((top_y, text, conf))

    if not amount_lines:
        return None, "no_amounts_found", None, None, None

    if not keyword_lines:
        fallback = max(amount_lines, key=lambda x: x[0])
        raw = re.search(AMOUNT_PATTERN, fallback[1]).group()
        return raw, "keyword_not_found_used_last_amount", None, fallback[2], fallback[1]

    results_out = []
    for kw_y, kw_text in keyword_lines:
        dist, closest = min(
            ((abs(a[0] - kw_y), a) for a in amount_lines), key=lambda x: x[0]
        )
        if dist > y_tolerance:
            continue
        raw = re.search(AMOUNT_PATTERN, closest[1]).group()
        results_out.append((raw, "ok", kw_text, closest[2], closest[1]))

    if not results_out:
        return None, "keyword_found_no_nearby_amount", None, None, None

    return max(results_out, key=lambda x: x[3])  # highest confidence


def extract_from_upload(uploaded_file):
    file_bytes = np.frombuffer(uploaded_file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    reader = load_reader()
    results = reader.readtext(img, detail=1)
    return results

# ── UI ────────────────────────────────────────────────────────────────────────
st.title("🧾 resit-ocr")
st.caption("Upload a receipt — get the total amount.")

uploaded = st.file_uploader(
    "Drop a receipt image here",
    type=["jpg", "jpeg", "png"],
    label_visibility="collapsed",
)

if uploaded:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.image(Image.open(uploaded), caption="Uploaded receipt", use_container_width=True)

    with col2:
        with st.spinner("Reading receipt..."):
            uploaded.seek(0)
            results = extract_from_upload(uploaded)
            total, status, keyword, conf, raw_line = find_total(results)

        st.markdown("### Result")

        if status == "ok":
            st.metric(label=f"Total  ·  matched on **{keyword}**", value=f"RM {total}")
            if conf and conf < 0.6:
                st.warning(f"Low confidence ({conf:.0%}) — verify manually.")
            else:
                st.success(f"Confidence: {conf:.0%}")

        elif status == "keyword_not_found_used_last_amount":
            st.metric(label="Total  ·  no keyword found, used last amount", value=f"RM {total}")
            st.warning("No total keyword detected. Showing the last amount on the receipt — verify manually.")

        elif status == "no_amounts_found":
            st.error("No amounts found in this receipt. Try a clearer photo.")

        elif status == "keyword_found_no_nearby_amount":
            st.error("Found a total keyword but no amount nearby. Layout may be unusual.")

        if raw_line:
            st.markdown("---")
            st.caption(f"Raw OCR line: `{raw_line}`")

    # debug expander — useful while testing
    with st.expander("All OCR lines (debug)"):
        for bbox, text, conf in results:
            flag = "🔑" if any(kw in text.lower() for kw in TOTAL_KEYWORDS) else \
                   "💰" if re.search(AMOUNT_PATTERN, text) else "·"
            st.text(f"{flag}  [{conf:.2f}]  {text}")