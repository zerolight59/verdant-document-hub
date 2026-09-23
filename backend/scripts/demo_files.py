"""Deterministic, fictional sample files. No third-party downloads or company data."""

from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


def _literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def demo_pdf(title: str, project: str, version: int, lines: list[str]) -> bytes:
    """Create a readable two-page PDF with a sample schematic and revision notes."""
    streams = []
    for page in (1, 2):
        commands = [
            "0.96 0.98 0.96 rg 0 0 612 792 re f",
            "0.13 0.36 0.26 rg 0 700 612 92 re f",
        ]

        def text(value, x, y, size=11, color="0.15 0.23 0.19", commands=commands):
            commands.append(f"{color} rg BT /F1 {size} Tf {x} {y} Td ({_literal(value)}) Tj ET")

        text("VERDANT / FICTIONAL DEMONSTRATION", 36, 755, 13, "1 1 1")
        text(title[:68], 36, 724, 16, "1 1 1")
        text(project[:85], 36, 670, 11)
        text(f"Revision {version}  |  Page {page} of 2", 36, 647, 10)
        text("NOT FOR ENGINEERING, PROCUREMENT OR SAFETY DECISIONS", 36, 620, 9)
        if page == 1:
            text("Purpose and document scope", 36, 579, 16)
            for index, line in enumerate(lines[:7]):
                text(line[:88], 36, 550 - index * 22, 11)
            text("Illustrative assembly / workflow map", 36, 360, 14)
            for x, label in ((40, "Input"), (225, "Document"), (410, "Decision")):
                commands.append(f"0.88 0.93 0.89 rg {x} 270 160 62 re f")
                text(label, x + 35, 296, 13)
            commands.extend(
                ["0.35 0.55 0.40 RG 1.5 w 200 301 m 225 301 l S", "385 301 m 410 301 l S"]
            )
            text("Example values are invented to demonstrate the document workflow.", 36, 227, 10)
        else:
            text("Revision notes and reader checklist", 36, 579, 16)
            notes = [
                f"Current revision: {version}. Previous versions remain available in Verdant.",
                "Confirm the document title and selected version before reviewing.",
                "Read the change summary beside the file reader.",
                "Compare versions side by side when an earlier file exists.",
                "Record written feedback before requesting changes.",
                "Submit a new version after making the requested corrections.",
                "Only the assigned reviewer may approve this project document.",
                "An approval in this sample is fictional, not engineering certification.",
            ]
            for index, line in enumerate(notes):
                text(line, 36, 540 - index * 32, 11)
        text("DEMO DATA ONLY  |  Generated locally by Verdant's optional showcase seed", 36, 45, 9)
        streams.append("\n".join(commands).encode("ascii", errors="replace"))
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 6 0 R >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 7 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    objects += [
        f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream"
        for stream in streams
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(output)


def demo_docx(title: str, lines: list[str]) -> bytes:
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" '
            'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Override PartName="/word/document.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.'
            'wordprocessingml.document.main+xml"/>'
            "</Types>",
        )
        archive.writestr(
            "_rels/.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>",
        )
        body = "".join(
            f"<w:p><w:r><w:t>{escape(line)}</w:t></w:r></w:p>"
            for line in [title, "FICTIONAL DEMO - NOT FOR OPERATIONAL USE", *lines]
        )
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body>{body}</w:body></w:document>",
        )
    return stream.getvalue()


def demo_xlsx() -> bytes:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Fictional comparison"
    for row in [
        ["DEMO ONLY - invented values", "", "", ""],
        ["Candidate", "Mass index", "Cost index", "Decision note"],
        ["Alloy A", 72, 110, "Lightweight example"],
        ["Alloy B", 85, 96, "Balanced example"],
        ["Alloy C", 100, 83, "Baseline example"],
    ]:
        sheet.append(row)
    stream = BytesIO()
    workbook.save(stream)
    workbook.close()
    return stream.getvalue()
