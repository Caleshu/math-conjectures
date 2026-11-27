from datetime import date

from app.sources.base import PaperRecord
from app.sources.identifiers import normalize_arxiv_id, normalize_doi, normalize_title, parse_identifier
from app.sources.registry import dedupe


def test_parse_identifier_variants():
    assert parse_identifier("arXiv:1009.3304").value == "1009.3304"
    assert parse_identifier("https://arxiv.org/abs/1009.3304v1").value == "1009.3304"
    assert parse_identifier("https://arxiv.org/pdf/2101.00001v2").kind == "arxiv"
    assert parse_identifier("1009.3304").kind == "arxiv"
    assert parse_identifier("math/0601001").value == "math/0601001"
    d = parse_identifier("https://doi.org/10.1016/J.DISC.2006.05.001")
    assert (d.kind, d.value) == ("doi", "10.1016/j.disc.2006.05.001")
    assert parse_identifier("W1641604556").kind == "openalex"
    assert parse_identifier("https://example.org/paper.pdf").kind == "url"
    assert parse_identifier("not an id").kind == "unknown"


def test_normalizers():
    assert normalize_doi("doi:10.1000/ABC.") == "10.1000/abc"
    assert normalize_arxiv_id("arXiv:1009.3304v3") == "1009.3304"
    assert normalize_title("Parity balance of the $i$-th  dimension edges!") == normalize_title(
        "parity balance of the i-th dimension edges")


def test_cross_source_dedupe_merges_fields():
    a = PaperRecord(source="arxiv", title="Parity balance of the $i$-th dimension edges", arxiv_id="1009.3304",
                    pdf_url="https://arxiv.org/pdf/1009.3304")
    b = PaperRecord(source="openalex", title="Parity balance of the i-th dimension edges",
                    doi="10.48550/arxiv.1009.3304", openalex_id="W1", cited_by_count=3, published_date=date(2010, 9, 17))
    c = PaperRecord(source="crossref", title="Something else entirely", doi="10.1/x")
    out = dedupe([a, b, c])
    assert len(out) == 2
    merged = out[0]
    assert merged.openalex_id == "W1" and merged.cited_by_count == 3 and merged.arxiv_id == "1009.3304"
    assert merged.raw["merged_sources"] == ["arxiv", "openalex"]


def test_upsert_deduplicates_by_arxiv_doi(tmp_path):
    from app.db import session_scope
    from app.services.papers import upsert_paper

    with session_scope() as db:
        p1, created1 = upsert_paper(db, PaperRecord(source="arxiv", title="A test paper on hypercubes",
                                                    arxiv_id="9999.00001"), "test")
        p2, created2 = upsert_paper(db, PaperRecord(source="openalex", title="A Test Paper on Hypercubes",
                                                    doi="10.48550/arxiv.9999.00001", abstract="filled later"), "test")
        assert created1 and not created2 and p1.id == p2.id
        assert p1.abstract == "filled later"  # gap filled, nothing overwritten
