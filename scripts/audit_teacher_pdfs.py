"""Inspect every generated PDF page and sample print geometry (pypdf/pdfplumber)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pypdf import PdfReader
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grade", action="append", choices=["6", "7", "9"])
    args = parser.parse_args()
    report = {"pdfs": 0, "pages": 0, "geometry_sample_pdfs": 0, "empty_pages": []}
    for grade in args.grade or ["6", "7", "9"]:
        folder = ROOT/"teacher"/grade
        manifest = json.loads((folder/"print-manifest.json").read_text())
        samples = {"001", f"{len(manifest['lessons']):03d}"}
        # Include the longest student and teacher documents, plus a mid-year pack.
        for name in ["handout.pdf", "teacher.pdf"]:
            samples.add(Path(max(manifest["lessons"], key=lambda e: e["files"][name]["pages"])["directory"]).name)
        samples.add(f"{len(manifest['lessons'])//2:03d}")
        for entry in manifest["lessons"]:
            directory = ROOT/"teacher"/entry["directory"]
            for name, expected in entry["files"].items():
                target = directory/name
                reader = PdfReader(target, strict=True)
                assert len(reader.pages) == expected["pages"], target
                for page_number, page in enumerate(reader.pages, 1):
                    assert abs(float(page.mediabox.width)-595.276) < 1, target
                    assert abs(float(page.mediabox.height)-841.89) < 1, target
                    text = page.extract_text()
                    assert "\ufffd" not in text, (target, page_number, "replacement glyph")
                    assert len(text.strip()) > 35, (target, page_number, "nearly empty page")
                    report["pages"] += 1
                report["pdfs"] += 1
                if directory.name in samples:
                    with pdfplumber.open(target) as document:
                        for number, page in enumerate(document.pages, 1):
                            for char in page.chars:
                                assert char["x0"] >= 40 and char["x1"] <= page.width-40, (target, number, char)
                                assert char["top"] >= 25 and char["bottom"] <= page.height-20, (target, number, char)
                    report["geometry_sample_pdfs"] += 1
        print(f"Grade {grade}: PDF parse, page text and sample print geometry passed", flush=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
