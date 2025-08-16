from fastapi import APIRouter, File, UploadFile
from app.ocr import extract_text_and_total

router = APIRouter()

@router.post("/ocr")
async def read_ocr(file: UploadFile = File(...)):
    result = await extract_text_and_total(file)
    return result
