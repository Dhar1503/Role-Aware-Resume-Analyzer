"""Document loading, format errors and layout evidence."""

import pytest

from resume_analyzer.extraction.document import (
    UnreadableDocumentError, UnsupportedFormatError, count_garbled, detect_column_gutters, load_document,
)


# --- unsupported and malformed input --------------------------------------------

@pytest.mark.parametrize("filename, needle", [
    ("resume.doc", ".docx"), ("resume.png", "no text layer"), ("resume.odt", "Unsupported"), ("resume", "Unsupported"),
])
def test_unsupported_formats_are_rejected_with_guidance(filename, needle):
    with pytest.raises(UnsupportedFormatError, match=needle):
        load_document(b"anything", filename)


@pytest.mark.parametrize("data, filename, needle", [
    (b"", "resume.pdf", "empty"),
    (b"hello world, not a pdf", "resume.pdf", "not a PDF"),
    (b"%PDF-1.4\n%%garbage that is not a real pdf", "resume.pdf", "could not be"),
    (b"plain text pretending", "resume.docx", "not a Word document"),
    (b"   \n\n  ", "resume.txt", "no text"),
    (b"\x00\x01\x02binary", "resume.txt", "does not look like a text file"),
])
def test_malformed_files_raise_readable_errors(data, filename, needle):
    with pytest.raises(UnreadableDocumentError, match=needle):
        load_document(data, filename)


def test_bytes_need_a_filename():
    with pytest.raises(ValueError):
        load_document(b"data")


def test_missing_path():
    with pytest.raises(UnreadableDocumentError, match="Could not read"):
        load_document("does/not/exist.pdf")


def test_txt_decodes_utf16_and_cp1252():
    doc = load_document("Priya Sharma\nSkills: Python".encode("utf-16"), "r.txt")
    assert doc.lines[0].text == "Priya Sharma"
    doc = load_document("Café résumé\nSkills".encode("cp1252"), "r.txt")
    assert doc.lines[0].text == "Café résumé"


# --- layout evidence from the generated samples ----------------------------------------

def test_every_sample_loads(docs):
    assert set(docs) == {"clean_pdf", "clean_docx", "plain_txt", "two_column_pdf", "table_pdf",
                         "creative_pdf", "messy_docx", "scanned_pdf"}


def test_column_gutter_only_in_two_column_layout(docs):
    assert docs["two_column_pdf"].pages[0].column_gutters
    assert 0.25 < docs["two_column_pdf"].pages[0].column_gutters[0] < 0.4
    for key in ("clean_pdf", "table_pdf", "creative_pdf"):     # right-aligned dates and tables are not columns
        assert all(not p.column_gutters for p in docs[key].pages), key


def test_reading_order_agreement(docs):
    assert docs["clean_pdf"].reading_order_similarity >= 0.9
    assert docs["two_column_pdf"].reading_order_similarity < 0.75


def test_tables_detected(docs):
    assert docs["table_pdf"].table_count == 2
    assert docs["clean_pdf"].table_count == 0          # borderless date alignment is not a table
    assert docs["messy_docx"].table_count == 1


def test_scanned_pdf_has_no_text_layer(docs):
    page = docs["scanned_pdf"].pages[0]
    assert page.char_count == 0 and page.image_area_ratio > 0.9


def test_docx_hidden_zones(docs):
    doc = docs["messy_docx"]
    assert doc.textbox_words > 0
    assert "priya.sharma@gmail.com" in doc.header_footer_text
    assert "priya.sharma@gmail.com" in doc.text             # a human sees it...
    assert "priya.sharma@gmail.com" not in doc.ats_text     # ...a simple ATS does not
    assert "Python" not in doc.ats_text                     # skills live in the text box


def test_docx_fonts_and_page_count(docs):
    doc = docs["clean_docx"]
    assert doc.page_count == 1
    assert any(l.style.startswith("Heading") for l in doc.lines)


def test_docx_stale_page_count_is_replaced_by_estimate():
    import io
    import docx
    d = docx.Document()                               # template's app.xml says <Pages>1</Pages>
    for _ in range(300):
        d.add_paragraph("Built and shipped a distributed caching layer for the payments service")
    buf = io.BytesIO()
    d.save(buf)
    doc = load_document(buf.getvalue(), "long.docx")
    assert doc.page_count >= 6 and doc.page_count_estimated


def test_pdf_page_count(docs):
    assert docs["clean_pdf"].page_count == 1
    assert docs["creative_pdf"].page_count == 2


# --- unit-level helpers ------------------------------------------------------------------

def _word(x0, x1, top, text="word"):
    return {"x0": x0, "x1": x1, "top": top, "bottom": top + 10, "text": text}


def test_gutter_detection_on_synthetic_columns():
    two_cols = [w for row in range(40) for w in (_word(40, 150, 20 + row * 15), _word(220, 540, 20 + row * 15))]
    assert detect_column_gutters(two_cols, 595) != []


def test_right_aligned_dates_are_not_columns():
    words = []
    for row in range(40):
        top = 20 + row * 15
        if row % 4 == 0:        # entry line: title ... date
            words += [_word(40, 200, top), _word(480, 555, top)]
        else:                   # full-width bullet; word breaks fall at different x on every line
            shift = (row * 17) % 50
            words += [_word(x, x + 45, top) for x in range(40 + shift, 560, 50)]
    assert detect_column_gutters(words, 595) == []


@pytest.mark.parametrize("text, expected", [
    ("de(cid:12)ned the scope", (1, 0)),
    ("(cid:127) Built REST APIs", (0, 1)),
    ("Phone  +91 98765", (0, 1)),
    ("Python (cid:127) Built", (0, 1)),          # interleaved column bullet is still a symbol
    ("clean text", (0, 0)),
])
def test_garbled_glyph_classification(text, expected):
    assert count_garbled(text) == expected
