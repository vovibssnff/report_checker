from __future__ import annotations

import io

import pikepdf

from app.config import settings
from app.core.domain.value_objects import ValidationResult

_PDF_MAGIC = b"%PDF-"

_DANGEROUS_KEYS = {
    "/JS",
    "/JavaScript",
    "/Launch",
    "/EmbeddedFile",
    "/EmbeddedFiles",
    "/RichMedia",
    "/XFA",
}

_SUSPICIOUS_ACTIONS = {
    "/Launch",
    "/URI",
    "/SubmitForm",
    "/ImportData",
}


class PDFValidator:
    def __init__(self, max_size_mb: int = settings.MAX_FILE_SIZE_MB) -> None:
        self._max_size_bytes = max_size_mb * 1024 * 1024

    def validate(self, data: bytes) -> ValidationResult:
        if not data.startswith(_PDF_MAGIC):
            return ValidationResult(valid=False, error="File does not start with PDF magic bytes")

        if len(data) > self._max_size_bytes:
            return ValidationResult(
                valid=False,
                error=f"File exceeds maximum size of {self._max_size_bytes // (1024 * 1024)} MB",
            )

        try:
            pdf = pikepdf.open(io.BytesIO(data))
        except Exception:
            return ValidationResult(valid=False, error="Failed to parse PDF structure")

        if pdf.is_encrypted:
            pdf.close()
            return ValidationResult(valid=False, error="Encrypted or password-protected PDFs are not allowed")

        reason = self._scan_objects(pdf)
        pdf.close()

        if reason is not None:
            return ValidationResult(valid=False, error=reason)

        return ValidationResult(valid=True)

    def _scan_objects(self, pdf: pikepdf.Pdf) -> str | None:
        for page in pdf.pages:
            result = self._check_dict(page.obj)
            if result is not None:
                return result

        if "/Names" in pdf.Root:
            result = self._check_dict(pdf.Root["/Names"])
            if result is not None:
                return result

        if "/AcroForm" in pdf.Root:
            result = self._check_dict(pdf.Root["/AcroForm"])
            if result is not None:
                return result

        if "/OpenAction" in pdf.Root:
            result = self._check_dict(pdf.Root["/OpenAction"])
            if result is not None:
                return result

        return None

    def _check_dict(self, obj: pikepdf.Object) -> str | None:
        if not isinstance(obj, pikepdf.Dictionary):
            return None

        for key in obj.keys():  # noqa: SIM118 (explicit .keys() for mypy)
            key_str = str(key)
            if key_str in _DANGEROUS_KEYS:
                return f"Potentially dangerous PDF element: {key_str}"

            if key_str == "/AA" or key_str == "/A":
                action = obj[key]
                if isinstance(action, pikepdf.Dictionary) and "/S" in action:
                    action_type = str(action["/S"])
                    if action_type in _SUSPICIOUS_ACTIONS:
                        return f"Suspicious PDF action: {action_type}"

        return None
