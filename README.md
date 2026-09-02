# hukuki-arastirma

Kişisel (ticari olmayan) hukuki araştırma MCP sunucusu.

Canlı kaynak: Adalet Bakanlığı Bedesten ve mevzuat.gov veritabanları (açık `yargi-mcp` / `mevzuat-mcp` istemcileri).
Yerel SQLite: çekilmiş içtihat tam metinleri. Kanun/madde metni her seferinde **canlı** çekilir.

Bu, Yargı PRO kopyası değildir. 11 milyonluk külliyat indirilmez. Semantik arama yalnızca biriken cache üzerindedir.

## Gereksinimler

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) önerilir

Bağımlılıklar yargi-mcp ile uyum için kilitli: `fastmcp==2.13.3`, `mcp==1.22.0`, `pydantic<2.12`. FastMCP 4 henüz uyumlu değil.

```bash
cd hukuki-arastirma
uv venv
uv pip install -e ".[dev]"
```

## Çalıştırma

**Stdio** (bu Grok Bot sohbeti, Cursor MCP, Claude Desktop):

```bash
uv run python -m hukuki_mcp
```

**HTTP** (Grok.com özel MCP ve ChatGPT custom connector: herkese açık HTTPS `/mcp` gerekir; ofis PC’sinde localhost yetmez):

```bash
uv run uvicorn hukuki_mcp.asgi:app --host 127.0.0.1 --port 8000
```

MCP yolu: `http://127.0.0.1:8000/mcp`

Ofis + ev: private depoyu `git clone` / `git pull`. `data/ictihat.sqlite` şu an repoda (küçük ofis külliyatı). Büyüyünce VPS veya ayrı sync düşünülür; `-wal`/`-journal` git’te yok.

## Cursor MCP örneği

`~/.cursor/mcp.json` (yolu kendi klonuna göre düzelt):

```json
{
  "mcpServers": {
    "hukuki-arastirma": {
      "command": "uv",
      "args": ["run", "python", "-m", "hukuki_mcp"],
      "cwd": "/ABSOLUTE/PATH/hukuki-arastirma"
    }
  }
}
```

Grok.com ve ChatGPT tarafı: Custom connector = public `https://…/mcp`. Yerel sunucuyu internete açmak için ileride VPS veya tünel. Bu sohbet, ofis PC’sindeki yerel sunucuya tünelsiz bağlanabilir.

ChatGPT Plus/Pro ve ücretli Grok, özel bağlayıcı için genelde gerekir.

## Tercih edilen araçlar

- `ictihat_ara` / `ictihat_getir`
- `aym_ictihat_ara`
- `mevzuat_ara` / `mevzuat_getir` / `mevzuat_icinde_ara`
- `semantik_ictihat_ara` — yalnız yerel cache FTS

Skill: `skills/yargi-legal-research-guide/SKILL.md` (sorguları 2–5 terime damıt; Solr’da boşluk OR; `ISTINAFHUKUK` açıkça eklenmeli).

## Lisans

MIT. `vendor/` altında Said Sürücü’nün MIT `yargi-mcp` ve `mevzuat-mcp` kaynakları. Bkz. `NOTICE`.
