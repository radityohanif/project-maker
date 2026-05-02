from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from pdf_to_png.cli import app
from pdf_to_png.core.converter import convert_all, convert_pdf
from pdf_to_png.core.models import OutputMode
from pdf_to_png.core.scanner import scan_pdfs
from pdf_to_png.core.validator import validate

runner = CliRunner()


def create_test_pdf(path: Path, num_pages: int = 1) -> Path:
    """Create a simple test PDF with the given number of pages."""
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")

    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for _ in range(num_pages):
        doc.new_page(width=200, height=200)
    doc.save(str(path))
    doc.close()
    return path


class TestScanner:
    def test_scan_single_pdf_file(self, tmp_path: Path) -> None:
        pdf = create_test_pdf(tmp_path / "test.pdf")
        result = scan_pdfs(pdf, recursive=True)
        assert result == [pdf]

    def test_scan_directory_single_pdf(self, tmp_path: Path) -> None:
        create_test_pdf(tmp_path / "test.pdf")
        result = scan_pdfs(tmp_path, recursive=True)
        assert len(result) == 1
        assert result[0].name == "test.pdf"

    def test_scan_directory_multiple_pdfs(self, tmp_path: Path) -> None:
        create_test_pdf(tmp_path / "a.pdf")
        create_test_pdf(tmp_path / "b.pdf")
        result = scan_pdfs(tmp_path, recursive=True)
        assert len(result) == 2
        assert [p.name for p in result] == ["a.pdf", "b.pdf"]

    def test_scan_directory_recursive(self, tmp_path: Path) -> None:
        create_test_pdf(tmp_path / "root.pdf")
        create_test_pdf(tmp_path / "sub1" / "a.pdf")
        create_test_pdf(tmp_path / "sub2" / "b.pdf")
        result = scan_pdfs(tmp_path, recursive=True)
        assert len(result) == 3
        assert {p.name for p in result} == {"root.pdf", "a.pdf", "b.pdf"}

    def test_scan_directory_non_recursive(self, tmp_path: Path) -> None:
        create_test_pdf(tmp_path / "root.pdf")
        create_test_pdf(tmp_path / "sub" / "nested.pdf")
        result = scan_pdfs(tmp_path, recursive=False)
        assert len(result) == 1
        assert result[0].name == "root.pdf"

    def test_scan_empty_directory(self, tmp_path: Path) -> None:
        result = scan_pdfs(tmp_path, recursive=True)
        assert result == []

    def test_scan_non_pdf_file_raises(self, tmp_path: Path) -> None:
        txt = tmp_path / "test.txt"
        txt.write_text("not a pdf")
        with pytest.raises(ValueError, match="not a PDF"):
            scan_pdfs(txt)


class TestConverter:
    def test_convert_single_page_grouped(self, tmp_path: Path) -> None:
        pdf = create_test_pdf(tmp_path / "input" / "test.pdf", num_pages=1)
        out_dir = tmp_path / "output"
        results = convert_pdf(pdf, out_dir, OutputMode.grouped)
        assert len(results) == 1
        assert results[0].name == "test_1.png"
        assert results[0].parent.name == "test"
        assert results[0].exists()

    def test_convert_multipage_grouped(self, tmp_path: Path) -> None:
        pdf = create_test_pdf(tmp_path / "input" / "test.pdf", num_pages=3)
        out_dir = tmp_path / "output"
        results = convert_pdf(pdf, out_dir, OutputMode.grouped)
        assert len(results) == 3
        assert [p.name for p in results] == ["test_1.png", "test_2.png", "test_3.png"]
        assert all(p.exists() for p in results)

    def test_convert_single_page_flat(self, tmp_path: Path) -> None:
        pdf = create_test_pdf(tmp_path / "input" / "test.pdf", num_pages=1)
        out_dir = tmp_path / "output"
        results = convert_pdf(pdf, out_dir, OutputMode.flat)
        assert len(results) == 1
        assert results[0].name == "test_1.png"
        assert results[0].parent == out_dir
        assert results[0].exists()

    def test_convert_multipage_flat(self, tmp_path: Path) -> None:
        pdf = create_test_pdf(tmp_path / "input" / "test.pdf", num_pages=3)
        out_dir = tmp_path / "output"
        results = convert_pdf(pdf, out_dir, OutputMode.flat)
        assert len(results) == 3
        assert results[0].parent == out_dir
        assert all(p.exists() for p in results)

    def test_convert_with_stem_suffix(self, tmp_path: Path) -> None:
        pdf = create_test_pdf(tmp_path / "input" / "test.pdf", num_pages=1)
        out_dir = tmp_path / "output"
        results = convert_pdf(pdf, out_dir, OutputMode.flat, stem_suffix="_1")
        assert len(results) == 1
        assert results[0].name == "test_1_1.png"

    def test_convert_sanitizes_unsafe_chars(self, tmp_path: Path) -> None:
        pdf = create_test_pdf(tmp_path / "input" / "test@file!.pdf", num_pages=1)
        out_dir = tmp_path / "output"
        results = convert_pdf(pdf, out_dir, OutputMode.flat)
        assert len(results) == 1
        assert "test_file_" in results[0].name
        assert "@" not in results[0].name


class TestConvertAll:
    def test_convert_all_single(self, tmp_path: Path) -> None:
        pdf1 = create_test_pdf(tmp_path / "input" / "doc.pdf", num_pages=1)
        out_dir = tmp_path / "output"
        results = convert_all([pdf1], out_dir, OutputMode.grouped)
        assert pdf1 in results
        assert len(results[pdf1]) == 1

    def test_convert_all_multiple_grouped(self, tmp_path: Path) -> None:
        pdf1 = create_test_pdf(tmp_path / "input" / "a.pdf", num_pages=1)
        pdf2 = create_test_pdf(tmp_path / "input" / "b.pdf", num_pages=1)
        out_dir = tmp_path / "output"
        results = convert_all([pdf1, pdf2], out_dir, OutputMode.grouped)
        assert len(results) == 2
        assert all(len(imgs) == 1 for imgs in results.values())

    def test_convert_all_collision_handling_flat(self, tmp_path: Path) -> None:
        pdf1 = create_test_pdf(tmp_path / "input" / "report.pdf", num_pages=1)
        pdf2 = create_test_pdf(tmp_path / "input" / "other" / "report.pdf", num_pages=1)
        out_dir = tmp_path / "output"
        results = convert_all([pdf1, pdf2], out_dir, OutputMode.flat)
        names = {p.name for imgs in results.values() for p in imgs}
        # First report gets no suffix, second gets _1
        assert "report_1.png" in names
        assert "report_1_1.png" in names
        assert len(names) == 2


class TestValidator:
    def test_validate_single_pdf(self, tmp_path: Path) -> None:
        pdf = create_test_pdf(tmp_path / "test.pdf")
        validate(pdf, recursive=True)  # should not raise

    def test_validate_directory_with_pdf(self, tmp_path: Path) -> None:
        create_test_pdf(tmp_path / "test.pdf")
        validate(tmp_path, recursive=True)  # should not raise

    def test_validate_nonexistent_path(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="does not exist"):
            validate(tmp_path / "nonexistent.pdf")

    def test_validate_non_pdf_file(self, tmp_path: Path) -> None:
        txt = tmp_path / "test.txt"
        txt.write_text("not a pdf")
        with pytest.raises(ValueError, match="not a PDF"):
            validate(txt)

    def test_validate_empty_directory(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="No PDF files found"):
            validate(tmp_path, recursive=True)

    def test_validate_directory_with_no_pdfs_recursive_false(self, tmp_path: Path) -> None:
        create_test_pdf(tmp_path / "sub" / "test.pdf")
        with pytest.raises(ValueError, match="No PDF files found"):
            validate(tmp_path, recursive=False)


class TestCLI:
    def test_cli_version(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_cli_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Convert PDF" in result.output

    def test_cli_generate_single_pdf_grouped(self, tmp_path: Path) -> None:
        pdf = create_test_pdf(tmp_path / "test.pdf", num_pages=1)
        out_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "-i",
                str(pdf),
                "-o",
                str(out_dir),
                "--mode",
                "grouped",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Done:" in result.output
        assert (out_dir / "test" / "test_1.png").exists()

    def test_cli_generate_single_pdf_flat(self, tmp_path: Path) -> None:
        pdf = create_test_pdf(tmp_path / "test.pdf", num_pages=1)
        out_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "-i",
                str(pdf),
                "-o",
                str(out_dir),
                "--mode",
                "flat",
            ],
        )
        assert result.exit_code == 0, result.output
        assert (out_dir / "test_1.png").exists()

    def test_cli_generate_directory_scan(self, tmp_path: Path) -> None:
        create_test_pdf(tmp_path / "a.pdf", num_pages=1)
        create_test_pdf(tmp_path / "b.pdf", num_pages=1)
        out_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "-i",
                str(tmp_path),
                "-o",
                str(out_dir),
                "--mode",
                "grouped",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "2 PNG" in result.output
        assert (out_dir / "a" / "a_1.png").exists()
        assert (out_dir / "b" / "b_1.png").exists()

    def test_cli_generate_no_pdfs_found(self, tmp_path: Path) -> None:
        out_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "-i",
                str(tmp_path),
                "-o",
                str(out_dir),
            ],
        )
        assert result.exit_code == 1
        assert "No PDF files found" in result.output

    def test_cli_generate_non_recursive(self, tmp_path: Path) -> None:
        create_test_pdf(tmp_path / "root.pdf", num_pages=1)
        create_test_pdf(tmp_path / "sub" / "nested.pdf", num_pages=1)
        out_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "-i",
                str(tmp_path),
                "-o",
                str(out_dir),
                "--no-recursive",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "1 PNG" in result.output
        assert (out_dir / "root" / "root_1.png").exists()
        assert not (out_dir / "nested").exists()

    def test_cli_validate_ok(self, tmp_path: Path) -> None:
        pdf = create_test_pdf(tmp_path / "test.pdf")
        result = runner.invoke(app, ["validate", "-i", str(pdf)])
        assert result.exit_code == 0, result.output
        assert "OK" in result.output

    def test_cli_validate_no_pdfs(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["validate", "-i", str(tmp_path)])
        assert result.exit_code == 1
        assert "Invalid:" in result.output

    def test_cli_generate_invalid_input(self, tmp_path: Path) -> None:
        out_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "-i",
                str(tmp_path / "nonexistent"),
                "-o",
                str(out_dir),
            ],
        )
        assert result.exit_code != 0


class TestIntegration:
    def test_full_workflow_single_pdf(self, tmp_path: Path) -> None:
        pdf = create_test_pdf(tmp_path / "report.pdf", num_pages=2)
        out_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "-i",
                str(pdf),
                "-o",
                str(out_dir),
                "--mode",
                "grouped",
            ],
        )
        assert result.exit_code == 0
        assert (out_dir / "report" / "report_1.png").exists()
        assert (out_dir / "report" / "report_2.png").exists()

    def test_full_workflow_multiple_pdfs(self, tmp_path: Path) -> None:
        create_test_pdf(tmp_path / "doc1.pdf", num_pages=1)
        create_test_pdf(tmp_path / "doc2.pdf", num_pages=2)
        out_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            [
                "generate",
                "-i",
                str(tmp_path),
                "-o",
                str(out_dir),
                "--mode",
                "flat",
                "--recursive",
            ],
        )
        assert result.exit_code == 0
        assert "3 PNG" in result.output
        assert (out_dir / "doc1_1.png").exists()
        assert (out_dir / "doc2_1.png").exists()
        assert (out_dir / "doc2_2.png").exists()
