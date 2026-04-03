import easyocr
import cv2
import numpy as np
import re

# Inisialisasi reader
reader = easyocr.Reader(['id', 'en'], gpu=False)

def preprocess_image(img):
    # Grayscale sederhana untuk meningkatkan akurasi OCR
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return gray

def extract_total_from_text(raw_text):
    """
    Strategi Baru: Cari angka terakhir yang muncul setelah kata kunci penting.
    """
    # 1. Bersihkan text agar menjadi satu baris panjang
    clean_content = raw_text.replace('\n', ' ').upper()
    
    # 2. Cari semua angka yang polanya seperti nominal uang (4-7 digit)
    all_amounts = re.findall(r"(?:RP|IDR)?[\s\.]*([\d\.,]+)", clean_content)
    
    valid_numbers = []
    for amt in all_amounts:
        # Menghilangkan titik dan koma
        num_only = re.sub(r"[.,\s]", "", amt)
        if 4 <= len(num_only) <= 7: 
            valid_numbers.append(int(num_only))

    # 3. Ambil angka terakhir yang valid sebagai total
    if valid_numbers:
        return valid_numbers[-1]

    return None

async def extract_text_and_total(file):
    image_bytes = await file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    processed = preprocess_image(img)

    # Jalankan OCR
    results = reader.readtext(processed, paragraph=True)

    # Mengambil teks mentah dari hasil OCR
    full_text_list = [res[1] for res in results]
    raw_text = "\n".join(full_text_list)
    
    # Ekstrak total dari teks yang sudah diproses
    total = extract_total_from_text(raw_text)

    return {
        "raw_text": raw_text,
        "total": total,
        "status": "success"
    }