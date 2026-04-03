import easyocr
import cv2
import numpy as np
import re

# Inisialisasi reader secara global agar tidak boros memory/waktu
# 'id' untuk Bahasa Indonesia, 'en' untuk English
reader = easyocr.Reader(['id', 'en'], gpu=False) 

def preprocess_image(img):
    """
    Untuk EasyOCR, grayscale dan sedikit denoising sudah cukup membantu.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Menghilangkan noise tipis
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    return denoised

def extract_total_from_text(results):
    """
    results: output dari reader.readtext() berupa list of tuples
    """
    full_text = " ".join([res[1] for res in results]).upper()
    
    # List untuk menampung semua angka yang ditemukan
    candidates = []

    # 1. Cari berdasarkan keyword 'TOTAL' atau 'JUMLAH'
    for i, res in enumerate(results):
        text = res[1].upper()
        if any(key in text for key in ["TOTAL", "GRAND", "JUMLAH", "AMOUNT", "BAYAR"]):
            # Cari angka di sekitar keyword (baris yang sama atau 2 baris setelahnya)
            for j in range(i, min(i + 3, len(results))):
                sub_text = results[j][1]
                # Regex ambil angka saja
                num_str = re.sub(r"[^\d]", "", sub_text)
                if num_str and 3 < len(num_str) < 9: # Nominal ribuan - puluhan juta
                    return int(num_str)

    # 2. Fallback: Ambil angka terbesar (biasanya total ada di bawah dan paling besar)
    for res in results:
        num_str = re.sub(r"[^\d]", "", res[1])
        if num_str and 3 < len(num_str) < 9:
            candidates.append(int(num_str))

    return max(candidates) if candidates else None

async def extract_text_and_total(file):
    image_bytes = await file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Preprocessing ringan
    processed = preprocess_image(img)

    # EasyOCR membaca teks
    # detail=1 memberikan koordinat dan confidence level
    results = reader.readtext(processed)

    # Gabungkan semua teks untuk raw_text
    raw_text = "\n".join([res[1] for res in results])
    
    # Ambil nominal total
    total = extract_total_from_text(results)

    return {
        "raw_text": raw_text,
        "total": total,
        "status": "success"
    }