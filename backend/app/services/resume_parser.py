from fastapi import HTTPException, UploadFile

from app.services.text_processing import normalize_whitespace


async def parse_resume(file: UploadFile) -> str:
    raw = await file.read()
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()

    if filename.endswith(".txt") or "text/plain" in content_type:
        return normalize_whitespace(raw.decode("utf-8", errors="ignore"))

    if filename.endswith(".pdf") or "pdf" in content_type:
        try:
            from pypdf import PdfReader
            import io

            reader = PdfReader(io.BytesIO(raw))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            parsed = normalize_whitespace(text)
            if parsed:
                return parsed
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=(
                    "PDF parsing requires a text-based PDF and the pypdf package. "
                    f"Install backend requirements or upload a .txt resume. Details: {exc}"
                ),
            ) from exc

    raise HTTPException(status_code=415, detail="Upload a PDF or plain text resume.")
