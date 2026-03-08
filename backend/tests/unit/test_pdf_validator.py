from __future__ import annotations

import io

import pikepdf

from app.adapters.driven.security.pdf_validator import PDFValidator, ValidationResult


def _minimal_pdf() -> bytes:
    pdf = pikepdf.Pdf.new()
    pdf.add_blank_page(page_size=(612, 792))
    buf = io.BytesIO()
    pdf.save(buf)
    pdf.close()
    return buf.getvalue()


class TestValidationResultDataclass:
    def test_valid(self):
        r = ValidationResult(valid=True)
        assert r.valid is True
        assert r.error is None

    def test_invalid_with_error(self):
        r = ValidationResult(valid=False, error="bad")
        assert r.valid is False
        assert r.error == "bad"


class TestPDFValidatorMagicBytes:
    def test_valid_pdf(self):
        validator = PDFValidator(max_size_mb=50)
        result = validator.validate(_minimal_pdf())
        assert result.valid is True

    def test_invalid_magic_bytes(self):
        validator = PDFValidator(max_size_mb=50)
        result = validator.validate(b"NOT_A_PDF_FILE_CONTENT")
        assert result.valid is False
        assert "magic bytes" in result.error


class TestPDFValidatorSize:
    def test_oversized_file(self):
        validator = PDFValidator(max_size_mb=1)
        pdf_data = _minimal_pdf()
        oversized = pdf_data + b"\x00" * (2 * 1024 * 1024)
        result = validator.validate(oversized)
        assert result.valid is False
        assert "size" in result.error.lower()


class TestPDFValidatorEncrypted:
    def test_encrypted_pdf_with_user_password(self):
        pdf = pikepdf.Pdf.new()
        pdf.add_blank_page(page_size=(612, 792))
        buf = io.BytesIO()
        pdf.save(
            buf,
            encryption=pikepdf.Encryption(owner="owner", user="user", R=4),
        )
        pdf.close()

        validator = PDFValidator(max_size_mb=50)
        result = validator.validate(buf.getvalue())
        assert result.valid is False

    def test_encrypted_pdf_owner_only(self):
        pdf = pikepdf.Pdf.new()
        pdf.add_blank_page(page_size=(612, 792))
        buf = io.BytesIO()
        pdf.save(
            buf,
            encryption=pikepdf.Encryption(owner="secret", user="", R=4),
        )
        pdf.close()

        validator = PDFValidator(max_size_mb=50)
        result = validator.validate(buf.getvalue())
        assert result.valid is False
        assert "ncrypt" in result.error


class TestPDFValidatorDangerousElements:
    def test_embedded_javascript(self):
        pdf = pikepdf.Pdf.new()
        pdf.add_blank_page(page_size=(612, 792))
        pdf.Root["/Names"] = pdf.make_indirect(
            pikepdf.Dictionary(
                {
                    "/JavaScript": pikepdf.Dictionary(
                        {
                            "/Names": pikepdf.Array(
                                [
                                    pikepdf.String("evil"),
                                    pikepdf.Dictionary(
                                        {
                                            "/S": pikepdf.Name("/JavaScript"),
                                            "/JS": pikepdf.String("app.alert('xss')"),
                                        }
                                    ),
                                ]
                            )
                        }
                    )
                }
            )
        )
        buf = io.BytesIO()
        pdf.save(buf)
        pdf.close()

        validator = PDFValidator(max_size_mb=50)
        result = validator.validate(buf.getvalue())
        assert result.valid is False
        assert "dangerous" in result.error.lower() or "JavaScript" in result.error

    def test_launch_key_in_page(self):
        pdf = pikepdf.Pdf.new()
        pdf.add_blank_page(page_size=(612, 792))
        pdf.pages[0].obj["/Launch"] = pikepdf.Dictionary({"/F": pikepdf.String("/bin/sh")})
        buf = io.BytesIO()
        pdf.save(buf)
        pdf.close()

        validator = PDFValidator(max_size_mb=50)
        result = validator.validate(buf.getvalue())
        assert result.valid is False
        assert "Launch" in result.error

    def test_suspicious_action_in_open_action(self):
        pdf = pikepdf.Pdf.new()
        pdf.add_blank_page(page_size=(612, 792))
        pdf.Root["/OpenAction"] = pdf.make_indirect(
            pikepdf.Dictionary(
                {
                    "/A": pikepdf.Dictionary(
                        {
                            "/S": pikepdf.Name("/Launch"),
                        }
                    ),
                }
            )
        )
        buf = io.BytesIO()
        pdf.save(buf)
        pdf.close()

        validator = PDFValidator(max_size_mb=50)
        result = validator.validate(buf.getvalue())
        assert result.valid is False
        assert "Launch" in result.error


class TestPDFValidatorCleanPDF:
    def test_clean_multipage_pdf(self):
        pdf = pikepdf.Pdf.new()
        for _ in range(5):
            pdf.add_blank_page(page_size=(612, 792))
        buf = io.BytesIO()
        pdf.save(buf)
        pdf.close()

        validator = PDFValidator(max_size_mb=50)
        result = validator.validate(buf.getvalue())
        assert result.valid is True
        assert result.error is None
