from fastapi import APIRouter, File, UploadFile, HTTPException
from app.ocr import extract_text_and_total
import httpx
import logging

# Setup logging untuk memantau proses
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# --- KONFIGURASI BACKEND TS ---
# Ganti dengan URL API Node.js/TS kamu (misal: http://localhost:3000 atau URL production)
TS_BACKEND_URL = "http://your-ts-backend-api.com/v1/bills/process-ocr"
# Token rahasia agar hanya Python kamu yang bisa nembak ke Backend TS
INTERNAL_AUTH_TOKEN = "YUPAY_SECRET_KEY_123" 

@router.post("/ocr")
async def read_ocr(file: UploadFile = File(...)):
    # 1. Validasi format file
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File harus berupa gambar (png/jpg/jpeg)")

    try:
        # 2. Jalankan proses OCR (yang sudah kita fix tadi)
        logger.info(f"Memulai proses OCR untuk file: {file.filename}")
        result = await extract_text_and_total(file)

        if result["total"] is None:
            logger.warning("OCR berhasil tapi gagal menemukan angka nominal (total)")

        # 3. KIRIM DATA KE BACKEND TS (Node.js)
        # Kita menggunakan httpx secara asynchronous agar tidak memblokir proses lain
        async with httpx.AsyncClient() as client:
            try:
                # Menyiapkan data yang akan dikirim
                payload = {
                    "merchant_info": "Detected from OCR", # Bisa dikembangkan lagi
                    "raw_text": result["raw_text"],
                    "total_amount": result["total"],
                    "filename": file.filename,
                    "status": result["status"]
                }

                # Hit API Backend TS
                response = await client.post(
                    TS_BACKEND_URL,
                    json=payload,
                    headers={"Authorization": f"Bearer {INTERNAL_AUTH_TOKEN}"},
                    timeout=10.0 # Timeout 10 detik
                )
                
                # Cek apakah Backend TS sukses menerima
                if response.status_code == 200:
                    logger.info("Berhasil sinkronisasi data ke Backend TS")
                    result["synced_to_ts"] = True
                else:
                    logger.error(f"Backend TS menolak data: {response.status_code}")
                    result["synced_to_ts"] = False

            except Exception as e:
                logger.error(f"Gagal menghubungi Backend TS: {str(e)}")
                result["synced_to_ts"] = False

        return result

    except Exception as e:
        logger.error(f"Error pada sistem OCR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal: {str(e)}")