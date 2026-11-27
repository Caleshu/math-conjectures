"""Live integration tests against public APIs. Run with `pytest -m network`; excluded by default
in CI via `-m 'not network'`."""
import pytest

from app.sources.arxiv import ArxivSource
from app.sources.base import SearchQuery
from app.sources.openalex import OpenAlexSource

pytestmark = pytest.mark.network


def test_arxiv_get_demo_paper():
    r = ArxivSource().get("1009.3304")
    assert r and "Hamiltonian cycles of the hypercube" in r.title
    assert r.authors == ["Feliú Sagols", "Guillermo Morales-Luna"] and "math.CO" in r.categories


def test_arxiv_subject_search():
    rs = ArxivSource().search(SearchQuery(text="hypercube hamiltonian", subject="graph theory", limit=5))
    assert rs and all(r.arxiv_id for r in rs)


def test_openalex_finds_arxiv_record():
    r = OpenAlexSource().find_arxiv("1009.3304", "Parity balance of the $i$-th dimension edges in Hamiltonian cycles of the hypercube")
    assert r and r.openalex_id
