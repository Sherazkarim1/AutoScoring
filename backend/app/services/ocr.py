import io
import json
import uuid
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

import easyocr
import fitz
import numpy as np
from PIL import Image

from app.config import settings

ALLOWED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
ALLOWED_PDF_TYPES = {".pdf"}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_TYPES | ALLOWED_PDF_TYPES


@dataclass
class OCRLine:
    text: str
    confidence: float


@dataclass
class OCRPage:
    page_number: int
    text: str
    confidence: float
    lines: list[OCRLine]
    preview_filename: Optional[str] = None


@dataclass
class OCRResult:
    full_text: str
    average_confidence: float
    word_count: int
    page_count: int
    pages: list[OCRPage]
    low_confidence_words: list[str]
    file_type: str
    source_filename: str
    stored_path: Optional[str] = None
    ocr_engine: str = "easyocr"

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, data: str) -> "OCRResult":
        payload = json.loads(data)
        pages = [
            OCRPage(
                page_number=p["page_number"],
                text=p["text"],
                confidence=p["confidence"],
                lines=[OCRLine(**line) for line in p["lines"]],
                preview_filename=p.get("preview_filename"),
            )
            for p in payload["pages"]
        ]
        return cls(
            full_text=payload["full_text"],
            average_confidence=payload["average_confidence"],
            word_count=payload["word_count"],
            page_count=payload["page_count"],
            pages=pages,
            low_confidence_words=payload["low_confidence_words"],
            file_type=payload["file_type"],
            source_filename=payload["source_filename"],
            stored_path=payload.get("stored_path"),
            ocr_engine=payload.get("ocr_engine", "easyocr"),
        )


class OCRService:
    """Extract text from scanned papers, photos, and PDFs.

    Printed question papers use EasyOCR. Handwritten student papers use TrOCR
    on line crops detected by EasyOCR (TrOCR reads one line at a time).
    """

    def __init__(self):
        self._reader: Optional[easyocr.Reader] = None
        self._trocr_processor = None
        self._trocr_model = None
        self._trocr_failed = False
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @property
    def reader(self) -> easyocr.Reader:
        if self._reader is None:
            self._reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        return self._reader

    def _load_trocr(self):
        if self._trocr_model is not None or self._trocr_failed:
            return
        try:
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel

            name = settings.trocr_model
            self._trocr_processor = TrOCRProcessor.from_pretrained(name)
            self._trocr_model = VisionEncoderDecoderModel.from_pretrained(name)
            self._trocr_model.eval()
        except Exception:
            self._trocr_failed = True
            self._trocr_processor = None
            self._trocr_model = None

    def _save_bytes(self, content: bytes, suffix: str) -> str:
        filename = f"{uuid.uuid4().hex}{suffix}"
        path = self.upload_dir / filename
        path.write_bytes(content)
        return filename

    def _pdf_to_images(self, pdf_bytes: bytes) -> list[bytes]:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        images: list[bytes] = []
        for page in doc:
            pix = page.get_pixmap(dpi=200, alpha=False)
            images.append(pix.tobytes("png"))
        doc.close()
        return images

    def _load_image_bytes(self, content: bytes) -> np.ndarray:
        image = Image.open(io.BytesIO(content))
        if image.mode != "RGB":
            image = image.convert("RGB")
        return np.array(image)

    def _ocr_image(self, image_input: bytes | np.ndarray) -> tuple[str, float, list[OCRLine], list[str]]:
        if isinstance(image_input, bytes):
            image_array = self._load_image_bytes(image_input)
        else:
            image_array = image_input

        detections = self.reader.readtext(image_array)
        lines: list[OCRLine] = []
        low_confidence: list[str] = []

        for _bbox, text, confidence in detections:
            cleaned = text.strip()
            if not cleaned:
                continue
            conf = float(confidence)
            lines.append(OCRLine(text=cleaned, confidence=round(conf, 4)))
            if conf < 0.55:
                low_confidence.extend(cleaned.split())

        page_text = " ".join(line.text for line in lines)
        avg_conf = sum(line.confidence for line in lines) / len(lines) if lines else 0.0
        return page_text, avg_conf, lines, low_confidence

    def _recognize_line_trocr(self, crop: np.ndarray) -> str:
        if self._trocr_model is None or self._trocr_processor is None:
            return ""
        import torch

        if crop.size == 0 or crop.shape[0] < 8 or crop.shape[1] < 8:
            return ""
        image = Image.fromarray(crop).convert("RGB")
        pixel_values = self._trocr_processor(images=image, return_tensors="pt").pixel_values
        with torch.no_grad():
            generated_ids = self._trocr_model.generate(pixel_values)
        text = self._trocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return (text or "").strip()

    def _ocr_image_trocr(self, image_input: bytes | np.ndarray) -> tuple[str, float, list[OCRLine], list[str]]:
        self._load_trocr()
        if self._trocr_failed:
            return self._ocr_image(image_input)

        if isinstance(image_input, bytes):
            image_array = self._load_image_bytes(image_input)
        else:
            image_array = image_input

        detections = self.reader.readtext(image_array)
        detections = sorted(
            detections,
            key=lambda item: (min(p[1] for p in item[0]), min(p[0] for p in item[0])),
        )
        lines: list[OCRLine] = []
        low_confidence: list[str] = []

        for bbox, easy_text, confidence in detections:
            xs = [point[0] for point in bbox]
            ys = [point[1] for point in bbox]
            pad = 4
            x1 = max(0, int(min(xs) - pad))
            x2 = min(image_array.shape[1], int(max(xs) + pad))
            y1 = max(0, int(min(ys) - pad))
            y2 = min(image_array.shape[0], int(max(ys) + pad))
            crop = image_array[y1:y2, x1:x2]
            trocr_text = self._recognize_line_trocr(crop)
            cleaned = trocr_text or str(easy_text).strip()
            if not cleaned:
                continue
            conf = float(confidence)
            lines.append(OCRLine(text=cleaned, confidence=round(conf, 4)))
            if conf < 0.55:
                low_confidence.extend(cleaned.split())

        page_text = " ".join(line.text for line in lines)
        avg_conf = sum(line.confidence for line in lines) / len(lines) if lines else 0.0
        return page_text, avg_conf, lines, low_confidence

    def extract_from_file(
        self,
        content: bytes,
        filename: str,
        store_file: bool = True,
        engine: str = "easyocr",
    ) -> OCRResult:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{ext}'. Allowed: PDF, JPG, PNG, WEBP."
            )

        requested = (engine or "easyocr").lower()
        use_trocr = requested == "trocr"
        stored_path = self._save_bytes(content, ext) if store_file else None
        pages: list[OCRPage] = []
        all_low_confidence: list[str] = []

        if ext in ALLOWED_PDF_TYPES:
            image_bytes_list = self._pdf_to_images(content)
            file_type = "pdf"
        else:
            image_bytes_list = [content]
            file_type = "image"

        for index, image_bytes in enumerate(image_bytes_list, start=1):
            preview_filename = self._save_bytes(image_bytes, ".png")
            if use_trocr:
                text, confidence, lines, low_words = self._ocr_image_trocr(image_bytes)
            else:
                text, confidence, lines, low_words = self._ocr_image(image_bytes)
            all_low_confidence.extend(low_words)
            pages.append(
                OCRPage(
                    page_number=index,
                    text=text,
                    confidence=round(confidence, 4),
                    lines=lines,
                    preview_filename=preview_filename,
                )
            )

        used_engine = "trocr" if use_trocr and not self._trocr_failed else "easyocr"
        full_text = "\n\n".join(page.text for page in pages if page.text).strip()
        word_count = len(full_text.split()) if full_text else 0
        avg_confidence = (
            sum(page.confidence for page in pages) / len(pages) if pages else 0.0
        )

        return OCRResult(
            full_text=full_text,
            average_confidence=round(avg_confidence, 4),
            word_count=word_count,
            page_count=len(pages),
            pages=pages,
            low_confidence_words=sorted(set(all_low_confidence))[:25],
            file_type=file_type,
            source_filename=filename,
            stored_path=stored_path,
            ocr_engine=used_engine,
        )


@lru_cache
def get_ocr_service() -> OCRService:
    return OCRService()
