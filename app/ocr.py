import pytesseract
import cv2
import numpy as np
import re

# --- Fungsi preprocessing gambar ---
def preprocess_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Adaptive threshold lebih fleksibel
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 31, 9)
    # Hilangkan noise
    blur = cv2.medianBlur(thresh, 3)
    return blur

# --- Ekstraksi total dari teks OCR ---
def extract_total_from_text(text: str):
    # Regex dengan variasi ejaan 'Total'
    patterns = [
        r"(?:Total|Totel|Totol|Tota1|Grand\s*Total|Jumlah\s*Bayar|Amount)[:\s]*Rp?[\s]*([\d.,]+)",
        r"Sub\s*total[:\s]*Rp?[\s]*([\d.,]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            raw_number = match.group(1)
            cleaned = raw_number.replace(".", "").replace(",", "")
            return cleaned

    # --- Fallback ---
    # Ambil angka terbesar tapi filter hanya angka < 8 digit (biar ga keambil nomor HP)
    all_numbers = re.findall(r"[\d.,]+", text)
    candidates = []
    for num in all_numbers:
        n = num.replace(".", "").replace(",", "")
        try:
            val = int(n)
            if 1000 <= val <= 99999999:  # filter nominal realistis
                candidates.append(val)
        except:
            continue

    if candidates:
        return str(max(candidates))

    return None

# --- Fungsi utama ---
async def extract_text_and_total(file):
    image_bytes = await file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    processed = preprocess_image(img)
    config = "--oem 3 --psm 6"
    text = pytesseract.image_to_string(processed, lang="eng", config=config)

    total = extract_total_from_text(text)
    return {
        "raw_text": text,
        "total": total
    }
