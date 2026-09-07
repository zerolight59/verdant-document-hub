from seed import small_pdf


def test_demo_pdf_is_a_valid_pdf_container():
    content = small_pdf(["Verdant", "Document preview"])
    assert content.startswith(b"%PDF-1.4")
    assert content.endswith(b"%%EOF\n")
    assert b"xref" in content
