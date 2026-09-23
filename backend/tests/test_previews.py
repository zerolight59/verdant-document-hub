from zipfile import ZipFile

import pytest
from fastapi import HTTPException
from openpyxl import Workbook

from app.services.preview_service import preview_content


def test_docx_text_preview(tmp_path):
    path = tmp_path / "notes.docx"
    with ZipFile(path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="urn:word"><w:p><w:t>Research notes</w:t></w:p></w:document>',
        )
    assert preview_content(path)["sections"][0]["text"] == "Research notes"


def test_presentation_order(tmp_path):
    path = tmp_path / "slides.pptx"
    with ZipFile(path, "w") as archive:
        for index in (10, 2, 1):
            archive.writestr(
                f"ppt/slides/slide{index}.xml",
                f'<a:slide xmlns:a="urn:slide"><a:t>Slide {index}</a:t></a:slide>',
            )
    sections = preview_content(path)["sections"]
    assert [s["text"] for s in sections] == ["Slide 1", "Slide 2", "Slide 10"]


def test_spreadsheet_values_not_formula_execution(tmp_path):
    path = tmp_path / "data.xlsx"
    workbook = Workbook()
    workbook.active.append(["Material", "Strength"])
    workbook.active.append(["Steel", 500])
    workbook.active.append(["Formula", "=1+1"])
    workbook.save(path)
    workbook.close()
    rows = preview_content(path)["sections"][0]["rows"]
    assert rows[1] == ["Steel", "500"]
    assert rows[2] == ["Formula", ""]


def test_entity_expansion_rejected(tmp_path):
    path = tmp_path / "unsafe.docx"
    with ZipFile(path, "w") as archive:
        archive.writestr(
            "word/document.xml", '<!DOCTYPE x [<!ENTITY x SYSTEM "file:///secret">]><x>&x;</x>'
        )
    with pytest.raises(HTTPException) as error:
        preview_content(path)
    assert error.value.status_code == 422


def test_malformed_office_rejected(tmp_path):
    path = tmp_path / "broken.docx"
    path.write_bytes(b"not an Office archive")
    with pytest.raises(HTTPException) as error:
        preview_content(path)
    assert error.value.status_code == 422


def test_csv_row_limit(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("\n".join(f"{i},value" for i in range(2500)))
    assert len(preview_content(path)["sections"][0]["rows"]) == 2000
