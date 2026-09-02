from pathlib import Path

from hukuki_mcp.cache import IctihatCache


def test_put_get_and_fts(tmp_path: Path):
    cache = IctihatCache(tmp_path / "t.sqlite")
    assert cache.get_ictihat("d1") is None
    cache.put_ictihat("d1", "Etkin pişmanlık hükümleri uygulandı.", {"esas": "2020/1"})
    hit = cache.get_ictihat("d1")
    assert hit["cache_hit"] is True
    assert "pişmanlık" in hit["markdown"]
    rows = cache.search_fts("pişmanlık")
    assert rows and rows[0]["document_id"] == "d1"


def test_mevzuat_hash_change(tmp_path: Path):
    cache = IctihatCache(tmp_path / "t.sqlite")
    assert cache.remember_mevzuat("m1", "6098", "TBK", "aaa") is None
    prev = cache.remember_mevzuat("m1", "6098", "TBK", "bbb")
    assert prev == "aaa"
