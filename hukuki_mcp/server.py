"""Unified FastMCP app: Yargı içtihat tools + Bedesten mevzuat + cache aliases."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import List, Optional

from pydantic import Field

ROOT = Path(__file__).resolve().parents[1]
YARGI = ROOT / "vendor" / "yargi-mcp"
MEVZUAT = ROOT / "vendor" / "mevzuat-mcp"
sys.path.insert(0, str(YARGI))
sys.path.insert(0, str(MEVZUAT))

from fastmcp import Context  # noqa: E402

from mcp_server_main import (  # noqa: E402
    app,
    bedesten_client_instance,
    get_bedesten_document_markdown,
    search_anayasa_unified,
    search_bedesten_unified,
)
from bedesten_mcp_module.enums import BirimAdiEnum  # noqa: E402
from bedesten_mcp_module.models import BedestenCourtTypeEnum, BedestenDocumentMarkdown  # noqa: E402

from bedesten_client import BedestenClient  # noqa: E402  # mevzuat vendor

from hukuki_mcp.cache import IctihatCache  # noqa: E402

CACHE = IctihatCache(ROOT / "data" / "ictihat.sqlite")
_mevzuat_client = BedestenClient(enable_cache=False)


def get_mcp_app():
    return app


@app.tool(
    name="ictihat_ara",
    description=(
        "Yargıtay, Danıştay, yerel hukuk, istinaf ve KYB kararlarında Bedesten Solr araması. "
        "Boşluk OR sayılır: birden çok kavramı zorunlu kılmak için + veya AND kullan. "
        "Varsayılan mahkemeler Yargıtay+Danıştay; ISTINAFHUKUK açıkça eklenmeli. "
        "2–5 hukuki terime damıt; kullanıcı cümlesini yapıştırma. Türkçe karakterleri koru."
    ),
)
async def ictihat_ara(
    ctx: Context,
    phrase: str = Field(..., description="Solr ifadesi. Ör. +\"etkin pişmanlık\" +\"nitelikli dolandırıcılık\""),
    court_types: List[BedestenCourtTypeEnum] = Field(
        default=["YARGITAYKARARI", "DANISTAYKARAR"],
        description="YARGITAYKARARI, DANISTAYKARAR, YERELHUKUK, ISTINAFHUKUK, KYB",
    ),
    pageNumber: int = Field(1, ge=1),
    birimAdi: BirimAdiEnum = Field("ALL"),
    kararTarihiStart: str = Field("", description="Karar tarihi başlangıç YYYY-MM-DD"),
    kararTarihiEnd: str = Field("", description="Karar tarihi bitiş YYYY-MM-DD"),
) -> dict:
    return await search_bedesten_unified(
        ctx,
        phrase=phrase,
        court_types=court_types,
        pageNumber=pageNumber,
        birimAdi=birimAdi,
        kararTarihiStart=kararTarihiStart,
        kararTarihiEnd=kararTarihiEnd,
    )


@app.tool(
    name="ictihat_getir",
    description="Bedesten documentId ile kararın tam metnini Markdown getirir. Tekrarlarda yerel SQLite cache kullanılır.",
)
async def ictihat_getir(
    documentId: str = Field(..., description="ictihat_ara sonucundaki documentId"),
) -> dict:
    documentId = (documentId or "").strip()
    if not documentId:
        raise ValueError("documentId boş olamaz.")
    hit = CACHE.get_ictihat(documentId)
    if hit:
        return {
            "documentId": documentId,
            "markdown_content": hit["markdown"],
            "cache_hit": True,
            "fetched_at": hit["fetched_at"],
        }
    doc: BedestenDocumentMarkdown = await get_bedesten_document_markdown(documentId)
    markdown = getattr(doc, "markdown_content", None) or str(doc)
    meta = doc.model_dump() if hasattr(doc, "model_dump") else {}
    if markdown and not str(markdown).startswith("ERROR"):
        CACHE.put_ictihat(documentId, markdown, metadata=meta)
    return {
        "documentId": documentId,
        "markdown_content": markdown,
        "cache_hit": False,
        "source_url": meta.get("source_url"),
        "mime_type": meta.get("mime_type"),
    }


@app.tool(
    name="aym_ictihat_ara",
    description="Anayasa Mahkemesi kararları (norm denetimi ve bireysel başvuru). Operatörsüz düz Türkçe kelimeler.",
)
async def aym_ictihat_ara(
    decision_type: str = Field(..., description="norm_denetimi veya bireysel_basvuru"),
    keywords: List[str] = Field(default_factory=list, description="Düz Türkçe kelimeler, operatör yok"),
    page_to_fetch: int = Field(1, ge=1, le=100),
    results_per_page: int = Field(10, ge=1, le=100),
):
    return await search_anayasa_unified(
        decision_type=decision_type,  # type: ignore[arg-type]
        keywords=keywords,
        page_to_fetch=page_to_fetch,
        results_per_page=results_per_page,
    )


@app.tool(
    name="mevzuat_ara",
    description=(
        "mevzuat.gov / Bedesten mevzuat araması. Kanun numarası biliyorsan mevzuat_no kullan, uydurma. "
        "phrase içinde AND/OR çalışmaz; +terim kullan. Sıralama Resmî Gazete tarihidir."
    ),
)
async def mevzuat_ara(
    phrase: str = Field("", description="İçerik tam metin (Solr). +zorunlu, -hariç, tırnak=öbek"),
    mevzuat_adi: str = Field("", description="Başlıkta arama; kanun numarası yazma"),
    mevzuat_no: Optional[str] = Field(None, description="Örn. 6098, 6698 — emin değilsen boş bırak"),
    mevzuat_tur: Optional[str] = Field(None, description="KANUN, KHK, YONETMELIK, TEBLIGLER, MULGA, virgülle birden çok"),
    page: int = Field(1, ge=1),
    page_size: int = Field(20, ge=1, le=50),
) -> dict:
    tur_list = None
    if mevzuat_tur:
        tur_list = [t.strip() for t in mevzuat_tur.split(",") if t.strip()]
    result = await _mevzuat_client.search_documents(
        phrase=phrase,
        mevzuat_adi=mevzuat_adi,
        mevzuat_no=mevzuat_no,
        mevzuat_tur_list=tur_list,
        page=page,
        page_size=page_size,
    )
    docs = []
    for d in result.documents:
        dumped = d.model_dump(by_alias=False)
        docs.append(dumped)
        CACHE.remember_mevzuat(
            str(dumped.get("mevzuat_id")),
            str(dumped.get("mevzuat_no")) if dumped.get("mevzuat_no") is not None else None,
            dumped.get("mevzuat_adi"),
            None,
        )
    return {
        "documents": docs,
        "total_results": result.total_results,
        "error_message": result.error_message,
        "note": "mevzuat_id sonraki mevzuat_getir çağrısı içindir; id uydurma.",
    }


@app.tool(
    name="mevzuat_getir",
    description="mevzuat_id ile tam metni CANLI çeker (kalıcı metin cache yok). id_type: mevzuat.",
)
async def mevzuat_getir(
    mevzuat_id: str = Field(..., description="mevzuat_ara sonucundaki mevzuat_id"),
) -> dict:
    mevzuat_id = (mevzuat_id or "").strip()
    if not mevzuat_id:
        raise ValueError("mevzuat_id boş olamaz.")
    content = await _mevzuat_client.get_document_content(mevzuat_id)
    text = content.content or ""
    digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]
    prev = CACHE.remember_mevzuat(mevzuat_id, None, None, digest)
    return {
        "mevzuat_id": mevzuat_id,
        "content": text,
        "mime_type": content.mime_type,
        "error_message": content.error_message,
        "content_hash": digest,
        "text_changed_since_last_fetch": bool(prev),
        "live": True,
    }


@app.tool(
    name="mevzuat_icinde_ara",
    description="Tek mevzuat belgesi içinde anahtar kelime (madde bazında). Büyük harf AND/OR/NOT bedesten search_plain ile sınırlı olabilir.",
)
async def mevzuat_icinde_ara(
    mevzuat_id: str = Field(...),
    keyword: str = Field(..., description="Aranacak ifade"),
) -> dict:
    text_doc = await _mevzuat_client.get_document_plain_text(mevzuat_id)
    body = text_doc if isinstance(text_doc, str) else getattr(text_doc, "content", "") or str(text_doc)
    # live fetch — do not treat cache as current law
    digest = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()[:16]
    CACHE.remember_mevzuat(mevzuat_id, None, None, digest)
    needle = keyword.lower()
    hits = []
    for i, line in enumerate(body.splitlines()):
        if needle in line.lower():
            hits.append({"line": i + 1, "text": line.strip()[:500]})
            if len(hits) >= 25:
                break
    return {"mevzuat_id": mevzuat_id, "keyword": keyword, "hits": hits, "live": True}


@app.tool(
    name="semantik_ictihat_ara",
    description=(
        "YALNIZ yerel cache üzerindeki FTS. 11 milyonluk külliyat değil. "
        "Tam künye/tarih için ictihat_ara kullan, sonra ictihat_getir ile doğrula."
    ),
)
async def semantik_ictihat_ara(
    query: str = Field(..., description="Cache FTS sorgusu"),
    limit: int = Field(10, ge=1, le=50),
) -> dict:
    rows = CACHE.search_fts(query, limit=limit)
    return {
        "results": rows,
        "note": "Bu, biriken kararların yerel dizinidir. Canlı Bedesten için ictihat_ara.",
    }


def main() -> None:
    app.run()


if __name__ == "__main__":
    main()
