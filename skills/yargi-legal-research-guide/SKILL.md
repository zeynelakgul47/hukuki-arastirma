---
name: yargi-legal-research-guide
description: Türk hukuku veya mahkeme kararlarını hukuki-arastirma MCP araçlarıyla araştırırken kullan (sürüm 2026-08-11, ofis uyarlaması).
---

# Ofis uyarlaması (araç adları)

Bu depodaki **tercih edilen** kısa adlar:
- `mevzuat_ara` / `mevzuat_getir` / `mevzuat_icinde_ara` (Bedesten mevzuat API)
- `ictihat_ara` / `ictihat_getir` (Bedesten içtihat; `search_bedesten_unified` / `get_bedesten_document_markdown` ile aynı kaynak)
- `aym_ictihat_ara` (`search_anayasa_unified` sarmalayıcısı)

Yukarıdaki OSS araçları da sunucuda durur. Resmî Gazete, AİHM ve bazı kurum araçları v1'de yoksa atla; içtihat+mevzuat ile devam et.
`ictihat_getir` SQLite cache kullanır. Mevzuat maddesi her seferinde canlı çekilir.

# Türk Hukuku Araştırma Kılavuzu (Yargı MCP)

Kılavuz sürümü: 2026-08-11

Bu kılavuz, otonom bir yapay zekâ ajanı olan seni, Yargı MCP (Model Context Protocol) sunucusuyla Türk hukuku araştırma iş akışlarında akıcı kılar. Aşağıdaki çekirdek araçlar (artı isteğe bağlı bir ek araç — Bölüm 6) mevzuatı, mahkeme içtihatlarını, Resmî Gazete'yi ve kurum kararlarını (özelge, BTK/Rekabet/KİK, Sayıştay, Uyuşmazlık, BDDK/KVKK/Sigorta Tahkim, Reklam Kurulu, KDK/Ombudsmanlık) çapraz sorgulayarak soruları doğru yanıtlamanı sağlar.

## 0. Bu Kılavuzu Bir Skill Olarak Kalıcılaştır (önce beni oku)

Bu kılavuzu her oturumda yeniden çekme. TAM metnini, üstteki sürümü metadata'sına kaydederek, tam olarak `yargi-legal-research-guide` adıyla kalıcı bir skill olarak sakla:

*   **Claude Code**: kılavuzun tamamını `.claude/skills/yargi-legal-research-guide/SKILL.md` dosyasına YAML frontmatter ile yaz — `name: yargi-legal-research-guide`, `description: Türk hukuku veya mahkeme kararlarını Yargı MCP araçlarıyla araştırırken kullan (sürüm 2026-08-11)`.
*   **Diğer platformlar**: eşdeğer kalıcı-talimat mekanizmasını (kurallar dosyası, bilgi girdisi, özel talimat) aynı ad altında, sürüm dizesini bozmadan kullan.
*   **Gelecekteki oturumlar**: bu aracın açıklaması güncel sürümü ilan eder. Kaydettiğin skill'in sürümü aynı ya da daha yeniyse, skill'i kullan ve bu aracı BİR DAHA çağırma. Daha eskiyse, bir kez çağır ve skill'in üzerine yaz.

## 1. Türk Hukuk Normlar Hiyerarşisi

Alt seviye bir norm, üst seviye bir normla çelişemez. **Sorun için en yüksek *işlevsel* kaynaktan başla.** Sıradan özel hukuk, vergi, iş, ceza ve idare hukuku sorularında önce ilgili Kanun'u veya düzenlemeyi belirle. Anayasa'yı; sorun temel haklar, normlar hiyerarşisi, iptal, anayasal yorum veya alt normların geçerliliği ile ilgili olduğunda kullan.

1. **Anayasa**: En üstün norm.
2. **Kanun**: TBMM tarafından çıkarılır. Çoğu sorgu için birincil başlangıç noktası.
3. **Kanun Hükmünde Kararname (KHK)**: Tarihsel olarak Bakanlar Kurulu'nca çıkarılmıştır; genellikle Kanun'a eşdeğerdir ama temel hakları düzenlemede sıkı sınırları vardır.
4. **Cumhurbaşkanlığı Kararnamesi (CBK)**: Cumhurbaşkanı'nca çıkarılır; Parlamento'nun yasama yaptığı alanlarda kesinlikle Kanun'a tabidir. Bir Kanun ile CBK çatışırsa, Kanun üstün gelir.
5. **Tüzük**: Daha eski araçlar (çoğunlukla kaldırılıyor veya değiştiriliyor).
6. **Yönetmelik**: Kanunların uygulanmasını düzenlemek için bakanlıklar, Cumhurbaşkanı veya kamu tüzel kişilerince çıkarılır.
7. **Tebliğ**: Ayrıntılı idari yönergeler ve teknik kurallar (vergi ve idare hukukunda çok yaygın).

**Milletlerarası Antlaşmalar (Anayasa m.90/5)** bu merdivende tek bir basamağa değil, merdivenin yanında konumlanır. Usulüne göre onaylanmış antlaşmalar Kanun hükmündedir ve anayasaya aykırılıkları ileri sürülemez; kritik olarak, **temel hak ve özgürlüklere** ilişkin bir antlaşma ile aynı konudaki bir Kanun çatışırsa, **antlaşma üstün gelir** (ör. AİHS). Antlaşma metinlerinin kendisi bu araçlarla ARANAMAZ — bir temel-hak çatışması söz konusuysa ilgisini bildir, antlaşma metnine yönlendir ve AİHS uygulaması için `aihm_ictihat_ara` ile AİHM içtihadına, anayasal boyut için `aym_ictihat_ara` ile AYM içtihadına bak.

Mahkeme İçtihatları normlar hiyerarşisinde bir basamak DEĞİLDİR. *Yargıtay* (özel hukuk/ceza) ve *Danıştay* (idari) kararları, birincil mevzuat değil, ikna edici yorumdur. İstisnalar: bağlayıcı *İçtihadı Birleştirme Kararları* ve *Anayasa Mahkemesi* iptal/bireysel-başvuru kararları norm-seviyesinde etki taşır. **Araç uyarısı**: AYM ve İçtihadı Birleştirme kararları `ictihat_ara`'nın `court_types` değerleri arasında DEĞİLDİR. AYM kararları için ayrı araç var — `aym_ictihat_ara` (dört tür) ve metni `ictihat_getir` (`anayasa:<guid>`); bkz. Örnek 9. İçtihadı Birleştirme kararlarının kendi arama aracı yoktur; yayım tarihini biliyorsan `resmi_gazete_fihrist` ile o günün Yargı bölümünden bulup `resmi_gazete_getir` ile okuyabilirsin, bilmiyorsan bunu açıkça söyle.

## 2. Araştırma Araçlarına Genel Bakış

Sunucu beş alanda çekirdek araçlar sunar: **Mevzuat**, **Mahkeme Kararları (İçtihat)**, **Anayasa Mahkemesi**, **Resmî Gazete** ve **Kurum Kararları**.

**Mevzuat Araçları:**
*   `mevzuat_ara`: mevzuat.gov.tr üzerinde global arama (12 tür; çağrı başına en çok 4 tür). Kanunların, yönetmeliklerin ve tebliğlerin metadata'sını ve iç kimliklerini bulur.
*   `mevzuat_getir`: Çok-amaçlı getirme aracı. Bir belgenin tam metnini, belirli bir *Madde*'sini veya yapısal içindekiler tablosunu (outline) getirir.
*   `mevzuat_icinde_ara`: Tek bir mevzuat belgesi *içinde* odaklı, yerel Boole araması yapar. Medeni Kanun gibi devasa kodlarda gezinmek için son derece güçlüdür.

**Mahkeme Kararları Araçları:**
*   `ictihat_ara`: 5 mahkeme türünde (Yargıtay, Danıştay, yerel, istinaf, KYB) milyonlarca kararda global Solr araması.
*   `aym_ictihat_ara`: Anayasa Mahkemesi kararlarında arama — varsayılan tüm türler ya da filtreli: `norm_denetimi`, `bireysel_basvuru`, `siyasi_parti`, `yuce_divan`.
*   `aihm_ictihat_ara`: AİHM (Avrupa İnsan Hakları Mahkemesi) kararlarında HUDOC üzerinden arama — kararlar + kabul edilebilirlik kararları. Varsayılan davalı Türkiye'dir (`ulke`); `HEPSI` tüm devletleri arar.
*   `ictihat_getir`: HERHANGİ bir mahkeme kararının tam metnini getirir — Bedesten `documentId`'leri, AYM `document_id`'leri (`anayasa:<guid>`) ve AİHM `document_id`'leri (`aihm:<itemid>`) dâhil. 40.000 karakteri aşan belgeler sayfalanır; `page_number` ile gez.

**Resmî Gazete Araçları:**
*   `resmi_gazete_fihrist`: Bir günün Resmî Gazete içindekiler listesi. `tarih` (ISO `YYYY-MM-DD`) verilmezse bugün (Europe/Istanbul). Yanıt `sayi`, bölümler (Yürütme ve İdare / Yasama / Yargı) ve her madde için `baslik` + `document_id` taşır; o gün mükerrer çıkmışsa `mukerrer` listesinde görünür ve `mukerrer_no` ile ayrıca istenir.
*   `resmi_gazete_getir`: Fihristteki bir maddenin tam metni (HTML→Markdown, PDF→OCR). YALNIZ fihristten gelen `resmi_gazete:` kimliğini kabul eder.

**Kurum Kararları Araçları:**
*   `kurum_karari_ara`: `kurum` parametresi ile 11 kurum üzerinde birleşik arama — `gib` (GİB özelgeleri, yani vergi özelgeleri), `btk` (BTK kurul kararları, yani telekom/BT düzenleyici kurul kararları), `rekabet` (Rekabet Kurumu kararları), `uyusmazlik` (Uyuşmazlık Mahkemesi kararları, yani yargı-yolu uyuşmazlığı kararları), `kik` (KİK / Kamu İhale Kurumu kurul kararları), `sayistay` (Sayıştay kararları), `bddk` (BDDK bankacılık kurul kararları — dış arama), `kvkk` (KVKK kişisel veri kararları — dış arama), `sigorta` (Sigorta Tahkim hakem kararları — dış arama), `reklam` (Reklam Kurulu basın bültenleri — dış arama; bir sonuç bir toplantı bültenidir, `document_id` = `reklam:<toplantı no>`), `kdk` (KDK / Kamu Denetçiliği Kurumu — Ombudsmanlık tavsiye/ret kararları). Filtreler kuruma özeldir (ör. `gib`: `ozelge_no`/`kanun_no`/`tarih_baslangic`/`tarih_bitis`; `btk`: `karar_no`/`karar_tarihi`/`ilgili_birim`; `rekabet`: `karar_turu`/`karar_no`; `uyusmazlik`: `arama_kapsami` = `tumu`/`esas_no`/`karar_no`; `kik`: `karar_tipi` = `uyusmazlik`/`duzenleyici`/`mahkeme`; `sayistay`: `karar_tipi` = `genel_kurul`/`temyiz`/`daire`; `kdk`: `karar_tipi` = `tavsiye`/`ret`/`kismi_tavsiye`/`kismi_ret`/`kismen_tavsiye_kismen_ret`, `basvuru_no` (YYYY/N), `idare_adi`, `konu` (20 tematik kategori), `tarih_baslangic`/`tarih_bitis` — kdk'da `keywords` karar özeti üzerinde arar, tam metin DEĞİL; `btk` de yayım tarihi için `tarih_baslangic`/`tarih_bitis` kabul eder) — seçtiğin `kurum`'a ait olmayan bir filtre ya da `karar_tipi` değeri geçmek `invalid_params` hatası döner. ⚠️ `btk`/`rekabet`/`uyusmazlik` sonuçları belge içeriği taşımaz (PDF): alakayı filtrelerle daralt, belge metnini yalnız gerçekten gerekli kararlar için `kurum_karari_getir` ile al (OCR maliyetli). `include_snippets: true` yalnız `gib` ve `kdk`'da ek belge getirir (kdk'da OCR'sız, cache-ısıtmalı) Sayfalama için `page` + `results_per_page` (1–50) kullan. ⚠️ `bddk`/`kvkk`/`sigorta`/`reklam` kurumları HARİCİ web araması (Tavily) ile keşfedilir: sunucuda arama anahtarı yoksa `not_configured` dönebilir, sonuçlar tek sıralı sayfa olarak gelir (`page` > 1 boştur) ve arama kelimelerin üçüncü-taraf bir arama servisine gönderilir — bu sorgulara ASLA müvekkil adı veya kişi-tanımlayıcı ayrıntı yazma. Tek bir Sigorta Tahkim dergisi sayısı İÇİNDE anahtar kelime araması için `sigorta_dergi_icinde_ara`; tek bir Reklam Kurulu bülteni İÇİNDE için `reklam_bulten_icinde_ara` (bülten numarasını `kurum: "reklam"` aramasından al).
*   `kurum_karari_getir`: `kurum_karari_ara`'dan dönen `document_id` ile tam karar metnini Markdown olarak getirir (`gib:...`, `btk:...`, `rekabet:...`, `uyusmazlik:...`, `kik:...`, `sayistay:...`, `bddk:...`, `kvkk:...`, `sigorta:...`, `reklam:...`, `kdk:...`). `ictihat_getir` ile aynı 40.000 karakterlik sayfalama.

## 3. Kritik Tuzaklar ve Sözdizimsel Kapanlar

Bu bölümü dikkatle oku. Ajan hatalarının çoğu bu kuralları çiğnemekten doğar.

*   **Sorgu Hijyeni — Anahtar Kelime Çıkar, Soruyu Asla Yapıştırma**: Kullanıcının tam cümlesini veya paragrafını bir `phrase`/`query`/`mevzuat_adi` parametresine BOŞALTMA. Uzun bir sorgu HER ZAMAN yanlıştır ama motora göre zıt nedenlerle: mevzuat araçları VE her boşlukla ayrılmış kelimeyi birlikte AND'ler (40 kelimelik soru → neredeyse sıfır sonuç), `ictihat_ara` ise OR'lar (40 kelimelik soru → yüz binlerce alâkasız isabet ve işe yaramaz sıralama). Hukuki sorunu 2–5 terime damıt. Örnek: yargılamadan önce iade ve etkin pişmanlık hakkında uzun bir hikâye → `+"etkin pişmanlık" +"nitelikli dolandırıcılık"` ara, tüm anlatıyı DEĞİL. Tek dev arama yerine birkaç dar arama çalıştır.
*   **AYM Araması Üçüncü, Operatörsüz Bir Lehçedir**: `aym_ictihat_ara.query` DÜZ Türkçe kelime alır — `+` yok, operatör-olarak-tırnak yok, AND/OR/NOT yok, joker yok. Her ek kelime sonuç kümesini DARALTIR (AND-benzeri). Tarihler ISO `YYYY-MM-DD`'dir (docket tarzı `YIL/SIRA` numaralarının aksine). Norm-denetimi davalarını `esas_no`/`karar_no` ile, bireysel başvuruları `basvuru_no` ile işaretle; bu filtreler türe özeldir ve başka yerde reddedilir.
*   **AİHM (`aihm_ictihat_ara`) HUDOC lehçesi kullanır**: boşluk=AND, `"tam söz öbeği"`, OR/NOT ve parantez çalışır; alan sözdizimi (`:`/`=`) reddedilir. Varsayılan davalı Türkiye'dir (`ulke`), dil filtrelenmez — aynı dava dil başına ayrı satırdır, `dil: "TUR"` satırını (Türkçe çeviri) tercih et. AİHS maddesiyle hedefle: `madde`/`ihlal`/`ihlal_yok` (ör. `10`, `P1-1`). Kararı `ictihat_getir` ile `aihm:<itemid>` kimliğinden oku; `metin_var: false` satırın metni HUDOC'ta henüz yayımlanmamıştır — aynı davanın İngilizce/Fransızca satırını getir.
*   **Türkçe Diakritikleri Koru**: Arama terimlerini her zaman tam Türkçe karakterlerle yaz (ç, ş, ğ, ı, İ, ö, ü) — `karari` değil `kararı`. Asla ASCII'ye çevirme; hem mevzuat hem içtihat indekslerinde eşleşme kesinliğini düşürür.
*   **Solr ile Boole Sözdizimi Ayrımı**:
    *   `mevzuat_ara` (`phrase` parametresi) mevzuat.gov.tr'yi sorgular ve **hiçbir operatör kabul etmez**: tırnak, `+`, `-`, joker ve AND/OR/NOT birebir metin olarak aranır. Önce tam öbek denenir, sonuç yoksa kelimeler AND'lenir (yanıt `note` ile bildirir).
    *   `mevzuat_icinde_ara` (`query` parametresi) yerel değerlendirilir. Büyük harf `AND`, `OR`, `NOT` kullanmak ZORUNDASIN (ör. `vergi AND NOT kira`).
*   **Sorgu Kitapçığı (motora göre operatörler)**:
    *   `ictihat_ara.phrase` (Bedesten Solr — boşluk OR'lar): bir terimi tam hedefle → `"imar planı"` · iki kavram birlikte → `+kamulaştırma +"bedel tespiti"` · bir alanı dışla → `mülkiyet -kira` · iki dava sebebinden biri → `"haksız fiil" OR "sebepsiz zenginleşme"` · olay örgüsü → `+"manevi tazminat" +"trafik kazası"` (çıplak bitişiklik dört kelimeyi de OR'lar). Joker/fuzzy/yakınlık yok.
    *   `mevzuat_ara.phrase` (mevzuat.gov — operatör YOK): 2-5 anahtar kelime yaz (`açık rıza`). Sıralama Resmî Gazete tarihine göredir, alâka sıralaması yoktur → hedefi öne çıkarmak için `mevzuat_adi` veya `mevzuat_no` ile daralt.
    *   `mevzuat_icinde_ara.query` (yerel Boole — BÜYÜK harf operatörler): `"açık rıza" AND sağlık` · `(ihracat OR ithalat) AND NOT istisna` · `vergi AND beyan AND NOT "matrah artırımı"`.
    *   `ictihat_ara` (`phrase` parametresi) içinde, **çıplak terimler arasındaki boşluk OR anlamına gelir (AND değil)** (sonda doğrulandı: tek başına `"etkin pişmanlık"` → 129K sonuç, tek başına `"nitelikli dolandırıcılık"` → 100K, yan yana → 228K ≈ birleşim; `+"etkin pişmanlık" +"nitelikli dolandırıcılık"` → 1,184, gerçek kesişim). Birden çok kavramı zorunlu kılmak için HER birini `+` ile işaretle ya da büyük harf `AND` ile birleştir. Bu Solr yapılandırması ayrıca `OR`/`NOT` sözcüklerini, `-` dışlamasını, `"tam ifadeleri"` ve `()` gruplamasını destekler — ama joker, fuzzy veya yakınlık YOK.
*   **Tarih Anlamları (aynı format, farklı anlam)**: İki tarih-filtreli araç da **ISO 8601 `YYYY-MM-DD`** alır (ör. `2024-01-01`) — aralarında format farkı YOK. Fark, *hangi* tarihe göre filtrelediğindir. `mevzuat_ara` (`resmi_gazete_tarihi_start`/`resmi_gazete_tarihi_end`) **Resmî Gazete yayım tarihini** hedefler, **yürürlük tarihini DEĞİL** — her zaman kanunun `Yürürlük` maddesini (genellikle son 2–3 maddeden biri) artı değişiklik notlarını oku, çünkü Haziran'da yayımlanan bir kanun aylar sonra yürürlüğe girebilir. `ictihat_ara` (`kararTarihiStart`/`kararTarihiEnd`) **karar tarihine** göre filtreler.
*   **Kimlik Kökeni (`mevzuat_no` vs `mevzuat_id`)**: Resmî kanun numarası (ör. KVKK için "6698") `mevzuat_no`'dur. `mevzuat_getir`/`mevzuat_icinde_ara` ise `mevzuat_ara`'nın döndürdüğü `mevzuat_id`'yi ister (`mevzuatgov:kanun:5:6698` biçiminde). Eski sayısal kimlikler (ör. `104383`) artık çözümlenmiyor; `unsupported_legacy_id` alırsan `mevzuat_ara` ile yeniden ara.
*   **`mevzuat_no`'yu Asla Uydurma**: Resmî kanun numarasından %100 emin değilsen, önce `mevzuat_adi` (başlık) ile ara, sonra `mevzuat_no`'yu yanıttan çıkar. Uydurulan numaralar sessizce sıfır-sonuç yanıtlarına yol açar.
*   **Sayfalama Parametresi Asimetrisi (`pageNumber` vs `page`)**: Mahkeme-karar aracı `ictihat_ara` **`pageNumber`** (camelCase) ile sayfalar; üç mevzuat arama aracı (`mevzuat_ara`, `mevzuat_icinde_ara`) **`page`** kullanır. `ictihat_ara`'ya `page` göndermek sessizce yok sayılır — 1. sayfada takılırsın. Sayfa boyutları da farklıdır: bedesten `page_size` en çok 100, `mevzuat_ara` 20, `mevzuat_icinde_ara` 50; `kurum_karari_ara` `results_per_page` en çok 50.
*   **Varsayılan Mahkeme Türleri**: `ictihat_ara` varsayılanı `['YARGITAYKARARI', 'DANISTAYKARAR']`'dır — yani yalnız yüksek mahkemeler. 2016 sonrası özel hukuk istinaf eğilimleri için `court_types` dizisine `ISTINAFHUKUK`'u açıkça GEÇMELİSİN. İstinaf kararlarının bağlayıcı doktrin olmadığını anla; onları gelişen eğilimler olarak, yerleşik yüksek-mahkeme kararlarından ayrı değerlendir.
*   **Alâka vs Tarih Sıralaması (`sort_by`)**: `ictihat_ara` sonuçları, `phrase` varsa varsayılan olarak ALÂKA-sıralıdır. Kronoloji önemliyse ("X hakkında en son gerekçe") açıkça `sort_by: "date"` geç. `sort_direction` (`desc`/`asc`) YALNIZCA tarih sıralamasına uygulanır; `phrase` olmadan `relevance` sessizce tarihe düşer. `mevzuat_ara`'da alâka sıralaması YOKTUR: kaynak yalnız Resmî Gazete tarihine göre sıralar, `sort_by` başka bir değer alsa da yanıt bunu `note` ile bildirir.
*   **İki Kademeli Snippet**: zaten belge cache'inde olan arama sonuçları her zaman ücretsiz bir `snippet` önizlemesi taşır. Ek olarak 5 taneye kadar cache-siz üst isabeti getirmek için `include_snippets: true` geç — bu getirmeler KOTASIZDIR (yalnız paylaşılan global kuyruktan geçer) ve cache'i herkes için ısıtır. PDF-formatlı kararlar atlanır (önizleme için OCR yok); kapsam sayfanın ilk 10 sonucuyla sınırlıdır; bozulmalar aramayı hatalı kılmak yerine `snippet_note` ile raporlanır. Geniş taramalarda kapalı bırak; üst isabetleri triyaj ederken aç (bkz. Örnek 8).
*   **`date_suspect` Bayrağı**: karar yılı bariz bir upstream yazım hatası olan girdiler (ör. `21.09.6006`) `date_suspect: true` taşır. İşaretli bir tarihe asla güvenme, atıf yapma veya tarih-filtreleme yapma — belgeyi getir ve gerçek tarihi metinden oku.
*   **Docket-Numarası Hedefleme (`esas_no` / `karar_no`)**: ikisi de `YIL/SIRA` formatını alır (ör. `2025/13348`). Kullanıcı zaten bir dosya veya karar numarası veriyorsa, phrase-araması yerine bunlarla filtrele; kesin bir arama için `court_types` (ve isteğe bağlı `birimAdi`) ile birleştir.
*   **Maddesiz Türler**: `TEBLIGLER`, `CB_KARAR` ve `CB_GENELGE` maddeye bölünmüyor — `id_type: "outline"|"madde"` bunlarda `outline_desteklenmiyor` döner. Tam metni (`id_type: "mevzuat"`) getir ya da `mevzuat_icinde_ara` kullan (bu türlerde tek tam-metin eşleşmesi döner).
*   **Talep Üzerine PDF OCR**: Cumhurbaşkanlığı genelgeleri ve kararları çoğu zaman PDF'tir. Arka uç bunları Mistral OCR ile ayrıştırır. İlk getirme yavaş olur (2-3 sn).
*   **Gerekçe Yok**: Kaynak mevzuat.gov.tr gerekçe yayımlamıyor; `mevzuat_getir`'in gerekçe seçeneği yoktur. Yasama gerekçesi gerekiyorsa TBMM kaynaklarına bak.
*   **Resmî Gazete Gün Bazlıdır, Aranabilir Değildir**: `resmi_gazete_fihrist` bir TARİH alır — konu/anahtar kelime araması YOKTUR. "Şu konuda ne yayımlandı" sorusunu tarihten bağımsız yanıtlayamazsın; ya tarihi bil ya da `mevzuat_ara`'nın `resmi_gazete_tarihi_start`/`_end` filtresiyle mevzuat tarafından yaklaş. `resmi_gazete_getir` YALNIZ fihristten dönen `resmi_gazete:` kimliğini kabul eder — kimliği elle kurma, gün-geneli `pdf_url`'yi ona verme (o alan insanın açıp okuması içindir). **İlan bölümü varsayılan olarak KAPALIDIR**: icra/tebligat/ihale ilanları için `include_ilan: true` ver — o zaman her ilan kurum adıyla ayrı `document_id` ile döner. Alınamayan kategori olursa `ilan_hatalari` alanı söyler; o alan doluyken "bugün ilan yok" DEME. Bugünün fihristi kalıcı olarak cache'lenmez: mükerrer sayı gün içinde sonradan yayımlanabilir, bu yüzden aynı gün tekrar sorman anlamlıdır.
*   **Mülga Kanunlar**: Varsayılan olarak aramalar yürürlükteki kanunları hedefler. Tarihsel senaryoları araştırıyorsan, `mevzuat_tur_list`'e açıkça `["MULGA"]` geç. **Yürürlükten kaldırma önceki içtihatları otomatik olarak geçersiz kılmaz** — eski kanun döneminde gerçekleşmiş olaylara ilişkin uyuşmazlıklar çoğu zaman *geçici maddeler* aracılığıyla hâlâ o kanuna tabidir.

## 4. Görüş İçeren Strateji Sezgileri

*   **Bilindiğinde `mevzuat_no`'yu Tercih Et**: Kullanıcı "Türk Ticaret Kanunu", "TTK" veya "KVKK" soruyorsa, resmî Kanun numarasını (ör. 6102, 6698) bul ve `mevzuat_ara(mevzuat_no="6102")` kullan. Bu, başlıkla aramaktan sonsuz kat daha kesindir.
*   **Genişten Başla, Sonra Daralt**: Önce temel Kanun'u güvenceye al. Çerçeveyi anlamak için ilgili *Madde*'yi oku, sonra tam usulü belirleyen özel *Yönetmelik* veya *Tebliğ*'i ara.
*   **Bağlam İçin Outline'ları Kullan**: Devasa kanunlarda (Borçlar Kanunu - 6098 TBK gibi) körlemesine aramak kaotik sonuç verir. Önce outline'ı getir, ilgili *Bölüm*'ü belirle ve o özel *Madde*'leri getir.
*   **`mevzuat_icinde_ara`'yı Acımasızca Kullan**: 50.000 kelimelik bir kanunu getirip sayfalanmış parçaları okumak yerine, hedef anahtar kelimelerinden bahseden 3 maddeyi anında yalıtmak için bu aracı kullan.
*   **Daireyi Oku, Otoriteyi Tart (`birimAdi`)**: `ictihat_ara` bir `birimAdi` daire filtresi sunar ve daire, kararın içtihadî ağırlığını belirler. Genel Kurul kararları tek-daire kararlarını geçer: **HGK** (Hukuk Genel Kurulu) ve **CGK** (Ceza Genel Kurulu) bir tek Daire'den (`H1`–`H23` hukuk, `C1`–`C23` ceza; Danıştay `D1`–`D17`) çok daha fazla otorite taşır ve **İçtihadı Birleştirme (İBK)** doğrudan bağlayıcıdır. İçtihatlar çatıştığında, üst kurulu tercih et. İlgili daireyi öğrendiğinde onu hedeflemek için `birimAdi`'yi kullan (ör. bir Yargıtay kira uyuşmazlığı → kiraya bakan mevcut daire).
*   **Güncelliği Doğrula**: Bir içtihat bulduktan sonra, modern olaylara uygulamadan önce her zaman atıf yapılan maddenin güncel metnini, değişiklik notlarını, yürürlük tarihlerini ve *geçici maddeleri* kontrol et. Kontrol edilmemiş bir içtihada güvenmek felaket bir hatadır. *Lex mitior* (sonraki daha lehe kanunu uygulamak) bir **ceza hukuku** ilkesidir (TCK 5237 m.7); özel ve idari işlerde varsayılan **geriye yürümezlik** ve *kazanılmış hakların* korunmasıdır — ceza kuralını ceza-dışı alanlara taşıma.

## 5. Uçtan Uca Örnek Senaryolar

Aşağıdaki örnekler, gerçekçi Türk hukuku araştırması için tam tool-çağrısı dizilerini gösterir.

### Örnek 1: Yazılım İhracatı için KDV İstisnası Kuralları
**Senaryo**: "Bir teknoparkta geliştirilen yazılımın ihracatı için özel KDV istisna koşulları nelerdir?"

**Strateji**: Teknoparktan yazılım-ihracı istisnası İKİ kanunun birlikte çalışmasıyla yönetilir — KDV Kanunu 3065 (genel KDV çerçevesi) ve Teknoloji Geliştirme Bölgeleri Kanunu 4691 (teknoparka özel istisna). İkisini zincirle, sonra uygulayıcı Tebliğ'i bul.

1. **KDV Kanunu 3065'i bul** (genel KDV çerçevesi).
```json
// call: mevzuat_ara
{
  "mevzuat_no": "3065",
  "mevzuat_tur_list": ["KANUN"]
}
```
*Sonuç: `mevzuat_id: "mevzuatgov:kanun:5:3065"` döner. Kimliği ASLA kendin kurma — `tertip` (buradaki `5`) numaradan türetilemez, yalnız aramadan gelir.*

2. **Teknoloji Geliştirme Bölgeleri Kanunu 4691'i bul** (teknoparka özel kanun).
```json
// call: mevzuat_ara
{
  "mevzuat_no": "4691",
  "mevzuat_tur_list": ["KANUN"]
}
```
*Sonuç: `mevzuat_id: "mevzuatgov:kanun:5:4691"` döner. Teknopark istisnaları için birincil yönetici kaynak budur.*

3. **4691 içinde yazılım-ihracı istisna hükmünü ara**. Yerel Boole sözdizimi — büyük harf operatörler zorunlu.
```json
// call: mevzuat_icinde_ara
{
  "mevzuat_id": "mevzuatgov:kanun:5:4691",
  "query": "yazılım AND (ihracat OR \"hizmet ihracı\") AND istisna",
  "page": 1,
  "page_size": 5
}
```
*Sonuç: 4691 içindeki ilgili madde(ler)i döner. Her isabet `madde_id` + `madde_no` taşır — `madde_id` mevzuat kimliğinin madde ekli hâlidir (`mevzuatgov:kanun:5:4691:m3` gibi) ve doğrudan `mevzuat_getir`'e verilebilir.*

4. **KDV Kanunu 3065'in outline'ını getir** ve karşılık gelen ihracat-istisnası maddesini bul (Madde 11 civarı).
```json
// call: mevzuat_getir
{
  "id": "mevzuatgov:kanun:5:3065",
  "id_type": "outline"
}
```
*Sonuç: Madde 11'i bul — girdiler `{ "madde_id": "mevzuatgov:kanun:5:3065:m11", "madde_no": 11, "kind": "normal", "title": "Mal ve hizmet ihracatı:", "bolum": "BİRİNCİ BÖLÜM" }` gibi görünür. `kind` `normal`/`gecici`/`ek` olabilir — GEÇİCİ ve EK maddeler ayrı numara dizisi kullanır, bu yüzden onlarda `madde_no` yerine outline'daki `madde_id`'yi kullan.*

*Kısayol: madde numarasını zaten biliyorsan outline'ı atla — `mevzuat_getir({"id":"mevzuatgov:kanun:5:3065","id_type":"madde","madde_no":11})` tek çağrıda çözer (normal numaralı maddeler için; EK/GEÇİCİ maddelerde önce outline al).*

5. **Yakın okuma için KDV Kanunu 3065 Madde 11'i getir**.
```json
// call: mevzuat_getir
{
  "id": "mevzuatgov:kanun:5:3065:m11",
  "id_type": "madde"
}
```
*Sonuç: Yanıt `resolved_madde_id: "mevzuatgov:kanun:5:3065:m11"` ve maddenin markdown metnini taşır — atıfta bu kimliği kullan.*

6. **Uygulayıcı kuralları için Tebliğ'lerde ara**. Operatör yok — 2-5 anahtar kelime yaz. Alan-özel Türkçe terimleri karıştır: *teknoloji geliştirme bölgesi*, *hizmet ihracı*, *yazılım*, *istisna*.
```json
// call: mevzuat_ara
{
  "phrase": "+\"teknoloji geliştirme bölgesi\" +yazılım +istisna",
  "mevzuat_tur_list": ["TEBLIGLER"]
}
```
*Sonuç: "Katma Değer Vergisi Genel Uygulama Tebliği" ve ilgili usul tebliğlerini bulur. Belirli uygulama detayları için `mevzuat_icinde_ara` ile içeri gir.*

### Örnek 2: Türk Borçlar Kanunu (TBK) Uyarınca Kiracı Hakları ve Tahliye
**Senaryo**: "Bir kiraya veren, kendisi taşınmak istediğinde konut kiracısını hangi koşullarda tahliye edebilir? Bana kanunu ve yakın tarihli bir Yargıtay kararını ver."

**Strateji**: TBK'yı (No. 6098) bul, kira bölümü için outline'ı kontrol et, tahliye maddesini bul, sonra içtihat için Yargıtay kararlarını ara.

1. **TBK'yı bul**.
```json
// call: mevzuat_ara
{
  "mevzuat_no": "6098"
}
```
*Sonuç: `mevzuat_id: "mevzuatgov:kanun:5:6098"` döner.*

2. **Kira Sözleşmesi bölümünün yapısını anlamak için outline'ı getir**.
```json
// call: mevzuat_getir
{
  "id": "mevzuatgov:kanun:5:6098",
  "id_type": "outline"
}
```
*Sonuç: Outline "Kira Sözleşmesi"nin 299 ilâ 356. maddeler arasında olduğunu gösterir. Gereksinim sebebiyle tahliye Madde 350'dir.*

3. **Madde 350'yi getir**. Numarayı outline'dan (ya da `mevzuat_icinde_ara` isabetinin `madde_no`'sundan) okudun; mevzuat kimliği + `madde_no` tek çağrıda çözer:
```json
// call: mevzuat_getir
{
  "id": "mevzuatgov:kanun:5:6098",
  "id_type": "madde",
  "madde_no": 350
}
```
*Sonuç: `resolved_madde_id: "mevzuatgov:kanun:5:6098:m350"` + madde metni. Aynı kimliği doğrudan `id` olarak da verebilirsin.*

4. **"İhtiyaç"ın ne kadar sıkı yorumlandığını görmek için Yargıtay kararlarını ara**. Büyük harf Boole operatörleri kullan (bu aracın Solr örneği bunları destekler). **Kritik**: Türk hukuki üslubu *nedeniyle* / *sebebiyle* / *gereksinim* arasında değişir — ilgili içtihatları kaçırmamak için hepsini OR'la.
```json
// call: ictihat_ara
{
  "phrase": "(\"ihtiyaç sebebiyle tahliye\" OR \"ihtiyaç nedeniyle tahliye\" OR gereksinim) AND samimi AND zorunlu",
  "court_types": ["YARGITAYKARARI"],
  "birimAdi": "ALL"
}
```
*Sonuç: İhtiyacın "samimi" ve "zorunlu" olması gerektiğini vurgulayan yakın tarihli kararları döner. "YG-2023-12345" gibi bir documentId verir.*

5. **Mahkeme kararı metnini oku**.
```json
// call: ictihat_getir
{
  "documentId": "YG-2023-12345"
}
```

### Örnek 3: Yapısız Belgeler ve PDF İşleme (Cumhurbaşkanlığı Genelgeleri)
**Senaryo**: "Aile / nüfus politikası hakkında yakın tarihli Cumhurbaşkanlığı Genelgeleri'ni (CB_GENELGE) bul ve temel talimatlarını belirle."

**Strateji**: `CB_GENELGE` belgeleri resmî madde yapısı olmadan PDF olarak gelir. Sunucu getirmede otomatik OCR uygular. `mevzuat_icinde_ara` maddesiz türlerde tam belge kolunu (`source: "mevzuatgov_full"`, tek tam-metin eşleşmesi) kullanır.

1. **Cumhurbaşkanlığı Genelgeleri'nde ara**. Operatör yok: kısa bir öbek yaz, önce tam öbek denenir. Genelgeler PDF olduğu için maddeye bölünmez — tam metni getirip `mevzuat_icinde_ara` ile tara.
```json
// call: mevzuat_ara
{
  "phrase": "aile",
  "mevzuat_tur_list": ["CB_GENELGE"]
}
```
*Sonuç: Eşleşen genelgeleri döner (ör. "Aile ve Nüfus On Yılı" hakkında bir 2026 Genelgesi). Gerçek `mevzuat_id`'yi yanıttan oku. Bu PDF'ler için `has_outline` false olacaktır.*

2. **Genelge içinde ara**. İlk getirmede arka uç OCR tetiklenir (~2-3 sn). Tam belge kolunu doğrulamak için yanıtın `source` alanını incele.
```json
// call: mevzuat_icinde_ara
{
  "mevzuat_id": "<MEVZUAT_ID_FROM_STEP_1>",
  "query": "aile AND nüfus",
  "page": 1,
  "page_size": 3
}
```
*Sonuç: `{ source: "mevzuatgov_full", total_matches: 1, results: [{ match_count, snippet }] }` — tüm PDF tek birim olduğundan tek belge-seviyesi eşleşme (`madde_id` yok).*

3. **Snippet'in sağladığından daha geniş bağlam gerekiyorsa tam metni getir**.
```json
// call: mevzuat_getir
{
  "id": "<MEVZUAT_ID_FROM_STEP_1>",
  "id_type": "mevzuat"
}
```

### Örnek 4: Mülga Kanun ile Güncel Kanunu İzleme
**Senaryo**: "Eski Ceza Muhakemeleri Usulü Kanunu'nda (1412 sayılı), yeni Kanun (5271) ile değiştirilmeden önce istinaf usulü nasıl düzenlenmişti?"

**Strateji**: Mülga veritabanında 1412'yi, yürürlükteki veritabanında 5271'i ara. İlgili usul maddelerini karşılaştır. Eski kodlar Osmanlıca terminoloji kullanır — *müruru zaman* (zamanaşımı, 1980 öncesi metinlerde çoğu zaman iki kelime), *istinaf*, *temyiz* — bu yüzden varyant yazımları OR'la.

1. **Eski mülga Ceza Muhakemeleri Usulü Kanunu'nu bul**.
```json
// call: mevzuat_ara
{
  "mevzuat_no": "1412",
  "mevzuat_tur_list": ["MULGA"]
}
```
*Sonuç: `mevzuat_id: "mevzuatgov:mulga_kanun:3:1412"` döner. Tertibin `3` olduğuna dikkat et — yürürlükteki kanunların çoğu `5`'tir; tertibi asla tahmin etme, aramadan oku.*

2. **Mülga metinde ilgili usul maddelerini bul**. Slicer'ın madde gövdelerinde güvenilir şekilde bulacağı somut terimler kullan.
```json
// call: mevzuat_icinde_ara
{
  "mevzuat_id": "mevzuatgov:mulga_kanun:3:1412",
  "query": "temyiz AND ceza"
}
```
*Sonuç: `source: "mevzuatgov_madde"`, madde-seviyesi eşleşmeler. Eski koddaki temyiz-usulü maddelerini belirlemek için snippet'leri oku.*

3. **Modern CMK 5271 ile karşılaştır**.
```json
// call: mevzuat_ara
{
  "mevzuat_no": "5271"
}
// Ardından:
// call: mevzuat_icinde_ara
{
  "mevzuat_id": "<MEVZUAT_ID_OF_5271>",
  "query": "(istinaf OR temyiz) AND ceza"
}
```
*Sonuç: Modern CMK istinaf katmanını getirir (2016 sonrası reform). İki dönemin eşleşen maddelerini karşılaştırarak iki-kademeli temyiz modelinin doğrudan temyizin yerini nasıl aldığını gör. Eski metinler Osmanlıca yazımlar da kullanabilir (ör. `müruru zaman` iki kelime) — esasa (usul-dışı) ilişkin konularda terminoloji köprüsü gerektiğinde bunları OR alternatifi olarak ekle.*

### Örnek 5: Bir Değişiklikten Sonra İçtihat Hâlâ Geçerli mi?
**Senaryo**: "Eski Türk Ceza Kanunu'nu (TCK 765) uygulayan 2005-öncesi bir Yargıtay kararı buldum. TCK 5237 yürürlükteyken hâlâ geçerli mi?"

**Strateji**: Eski içtihadı bul, atıf yaptığı kanunu belirle, o kanunun MULGA'da olup olmadığını ve yerine gelenin önceki fiiller için eski-kanun uygulanabilirliğini koruyan *geçici maddeler* içerip içermediğini kontrol et.

1. **Mülga TCK 765'e atıf yapan 2005-öncesi bir Yargıtay içtihadı bul**.
```json
// call: ictihat_ara
{
  "phrase": "\"765 sayılı\"",
  "court_types": ["YARGITAYKARARI"],
  "kararTarihiStart": "2004-01-01",
  "kararTarihiEnd": "2004-12-31"
}
```
*Sonuç: Eski TCK'ya atıf yapan Yargıtay kararları. İlgili birinin `documentId`'sini not al.*

2. **Mevzuat veritabanında TCK 765'in durumunu kontrol et**.
```json
// call: mevzuat_ara
{
  "mevzuat_no": "765",
  "mevzuat_tur_list": ["MULGA"]
}
```
*Sonuç: TCK 765 MULGA listesindedir. 2005-öncesi içtihat **otomatik olarak geçersiz değildir**: 1 Haziran 2005'ten önce işlenen suçlar, sanık lehineyse hâlâ TCK 765 uyarınca yargılanabilir (lex mitior — bkz. TCK 5237 Madde 7). Güncel uygulanabilirlik hakkında akıl yürütmeden önce geçişi yeni kodun Madde 7'si ve geçici maddeler üzerinden doğrula.*

3. **TCK 5237'yi getir ve Madde 7'yi kontrol et** (zamansal uygulamayı düzenler).
```json
// call: mevzuat_ara
{
  "mevzuat_no": "5237"
}
// sonra: Madde 7'yi ve Geçici Madde girdilerini bulmak için id_type="outline" ile mevzuat_getir
```
*Sonuç: TCK 5237 Madde 7 lex mitior'u kodlar; Haziran 2005 öncesi suçlarda eski/yeni yaptırımın hafif olanı uygulanır. Yargıtay içtihadı, eski rejim dönemindeki olaylar için geçerli kalır — bu kuralı kontrol etmeden asla "geçersiz" ilan etme.*

### Örnek 6: Gelişmiş Mahkemeler-Arası Arama
**Senaryo**: "İş yerinde 'mobbing' tanımı konusunda Bölge Adliye Mahkemeleri (İstinaf), Yüksek Mahkeme'den (Yargıtay) nasıl farklılaşıyor?"

**Strateji**: `ictihat_ara`'ya karşı iki özdeş Solr araması yap, `court_types`'ı değiştirerek güncel istinaf eğilimlerini yerleşik yüksek-mahkeme doktrini ile karşılaştır.

1. **Yargıtay kararlarını ara**. Genişten başla — AND yığılması (mobbing AND "psikolojik taciz" AND ispat) geri çağırımı sıfıra düşürebilir. `mobbing AND ispat` zaten ispat uyuşmazlıklarına filtreler.
```json
// call: ictihat_ara
{
  "phrase": "mobbing AND ispat",
  "court_types": ["YARGITAYKARARI"]
}
```

2. **İstinaf (Bölge Adliye) kararlarını ara**. `ISTINAFHUKUK`'un varsayılan `court_types`'ta OLMADIĞINI unutma — açıkça geçmelisin. Elmayla-elma karşılaştırması için aynı sorguyu kullan.
```json
// call: ictihat_ara
{
  "phrase": "mobbing AND ispat",
  "court_types": ["ISTINAFHUKUK"]
}
```

3. **HER İKİ sonuç kümesinden seçilen kararların gerçek metnini getir**. `ictihat_ara` yalnız metadata döner — arama sonuçlarında `markdown_content` yoktur. Okumak istediğin her `documentId` için `ictihat_getir` çağırmalısın.
```json
// call: ictihat_getir
{
  "documentId": "<ID_FROM_YARGITAY_RESULT>"
}
// sonra tekrar: <ID_FROM_ISTINAF_RESULT>
```
*Sonuç: Getirilen Markdown metinlerini karşılaştırarak bölge istinaf eğilimleri ile yerleşik yüksek-mahkeme doktrini arasındaki ayrışmaları belirle. Yargıtay'ın tekdüze daha katı ya da İstinaf'ın tekdüze daha yumuşak olduğunu varsayma; esasa ilişkin ispat standartları daireye ve olay örgüsüne göre değişir.*

### Örnek 7: İdari İşlemin İptali (Danıştay Zinciri)
**Senaryo**: "Tütün Ürünleri Yönetmeliği'ndeki yakın tarihli ruhsat şartı *Danıştay*'da dava konusu oldu mu? Hangi gerekçelerle?"

**Strateji**: İdare hukuku uyuşmazlıkları ayrı bir hattı izler — *Kanun* → *Yönetmelik / Tebliğ* → *Danıştay* (iptal davası). Türk hukuk sorularının çoğu buradadır (vergi, düzenleme, ihale, memuriyet); hat, özel-hukuk iş akışlarından işlevsel olarak farklıdır. Varsayılan `court_types` `DANISTAYKARAR`'ı içerdiğinden bu kısım otomatiktir ama yine de doğru yasama kaynağını zincirlemen gerekir. Yetki uyarısı: yalnız **ülke çapında** düzenlemeler ilk derecede doğrudan Danıştay'da dava edilir (Danıştay Kanunu m.24); bölgesel/yerel bir düzenlemenin iptali İdare Mahkemesi'nde başlar — bu yüzden bir Danıştay isabetinin yokluğu dava olmadığı anlamına gelmez.

1. **Yetki veren Kanun'u bul** (Tütün düzenlemesi: 4733 sayılı Kanun — Tütün Ürünleri Piyasası).
```json
// call: mevzuat_ara
{
  "mevzuat_no": "4733",
  "mevzuat_tur_list": ["KANUN"]
}
```

2. **İlgili Yönetmelik'i bul** (gerçekte dava edilen ikincil düzenleme).
```json
// call: mevzuat_ara
{
  "mevzuat_adi": "tütün mamulleri ve alkollü içkiler",
  "mevzuat_tur_list": ["YONETMELIK", "KKY"]
}
```
*Sonuç: Aday Yönetmelik(ler)i belirle; ruhsata atıf yapanın `mevzuat_id`'sini not al.*

3. **Yönetmelik'te belirli ruhsat hükmünü ara**.
```json
// call: mevzuat_icinde_ara
{
  "mevzuat_id": "<MEVZUAT_ID_YONETMELIK>",
  "query": "ruhsat AND (satış OR perakende) AND başvuru"
}
```

4. **Bu Yönetmelik alanına iptal davaları için Danıştay kararlarını ara**. Solr Boole kullan (burada büyük harf OK).
```json
// call: ictihat_ara
{
  "phrase": "tütün AND ruhsat AND (iptal OR \"yetki aşımı\" OR \"hukuka aykırılık\")",
  "court_types": ["DANISTAYKARAR"]
}
```
*Sonuç: En ilgili `documentId` değerlerini seç; bu tür davalara genellikle Danıştay 10. veya 13. Daire bakar (gerekirse `birimAdi` ile daralt, ör. `D10` veya `D13`).*

5. **Seçilen kararı getir**.
```json
// call: ictihat_getir
{
  "documentId": "<ID_FROM_DANISTAY_RESULT>"
}
```
*Sonuç: Karar metni iptal gerekçelerini ortaya koyar — tipik olarak *yetki aşımı*, üst Kanun'la çatışma veya anayasal hak ihlali. 1. Adım'ın Kanun'una geri çapraz-referans vererek Yönetmelik'in yasal dayanağını doğrula.*

### Örnek 8: Snippet Odaklı Triyaj (Kota-Tasarrufu İş Akışı)
**Senaryo**: "*Kamulaştırmasız el atma* tazminatı konusunda en güçlü yakın tarihli Yargıtay kararlarını bul — ama yalnız en ilgili bir-iki tanesini tam oku."

**Strateji**: `include_snippets: true` ile alâka-sıralı bir arama çalıştır, dönen snippet'lerde triyaj yap ve belge getirmelerini YALNIZ kazananlara harca. Snippet getirmeleri kotasızdır; tam-belge getirmeleri değildir.

1. **Snippet'ler açık ara**. Her iki kavramı da `+` ile zorunlu işaretle (boşluk onları OR'lardı).
```json
// call: ictihat_ara
{
  "phrase": "+\"kamulaştırmasız el atma\" +tazminat",
  "court_types": ["YARGITAYKARARI"],
  "include_snippets": true,
  "page_size": 10
}
```
*Sonuç: Alâka-sıralı (`phrase` varsa varsayılan). Önde gelen sonuçlar `snippet` önizlemeleri taşır — cache'li kararlar her zaman taşır, ayrıca 5 taneye kadar cache-siz HTML isabeti kotasız getirilir; PDF kararları atlanır ve her bozulma `snippet_note` ile raporlanır, asla hata olarak değil.*

2. **Snippet'lerde triyaj yap**. `snippet` alanlarını oku ve terimleri yalnızca geçerken anan sonuçları ele. Snippet'leri gerçekten tazminat sorusuyla ilgilenen 1–2 `documentId`'yi seç.

3. **Yalnız kazananları getir**.
```json
// call: ictihat_getir
{
  "documentId": "<BEST_ID_FROM_TRIAGE>"
}
```
*Sonuç: Belge kotasını 10 yerine 2 kararda harcadın. Üst isabetleri sıralamak önemli olduğunda bunu varsayılan desenin yap.*


### Örnek 9: Anayasa Mahkemesi — Mülkiyet Hakkı İhlali (Bireysel Başvuru)
**Senaryo**: "Uzun süren kamulaştırma davasının yol açtığı mülkiyet-hakkı ihlaline dair yakın tarihli bir AYM bireysel-başvuru kararı bul ve oku."

**Strateji**: AYM kararları Bedesten'de değil, `aym_ictihat_ara` arkasında yaşar. Bireysel başvuru külliyatını düz anahtar kelimelerle ara, sonra kararı genel belge aracıyla oku.

```json
// call: aym_ictihat_ara
{
  "decision_type": "bireysel_basvuru",
  "query": "mülkiyet hakkı kamulaştırma",
  "decision_date_start": "2023-01-01",
  "results_per_page": 10
}
```
Her isabet özenli bir `konu_ozeti`, karar veren `birim`, sonuç (`sonuc`) ve kullanıma hazır bir `document_id` taşır:
```json
// call: ictihat_getir
{ "documentId": "anayasa:e12c57f4-74ef-9031-16ad-efbf7f62d23c" }
```
Öne çıkan AYM kararları uzundur; yanıt `is_paginated: true` taşıyorsa, `current_page == total_pages` olana kadar `page_number: 2, 3…` ile çağırmaya devam et. Atıflardan gelen eski-stil referanslar (`/ND/2024/202`, `/BB/2021/30620`) da doğrudan `documentId` olarak çalışır. Norm denetimi (bir kanunun anayasaya uygunluğu) için `decision_type: "norm_denetimi"` kullan ve E. numarası verildiğinde `esas_no` ile hedefle.

### Örnek 10: Kurum Kararları — Özelge, Dış-Arama Kurumu ve İki-Kademeli Bülten
**Senaryo**: "Gayrimenkul değer artışı kazancı istisnası hakkında bir GİB özelgesi bul; ayrıca açık rıza olmadan veri işlemeden dolayı verilen bir KVKK idari para cezası kararı ve yanıltıcı indirim reklamına ilişkin bir Reklam Kurulu kararı istiyorum."

**Strateji**: Kurum kararları `kurum_karari_ara` (arama) + `kurum_karari_getir` (getirme) ile yürür ve `kurum` parametresi ile hangi kurumun sorgulandığını belirler. İki mimari var: **doğrudan-API kurumları** (gib·btk·rekabet·uyusmazlik·kik·sayistay·kdk) yapılandırılmış kurum-özel filtreler kabul eder; **dış-arama kurumları** (bddk·kvkk·sigorta·reklam) Tavily web araması kullanır — yalnız `keywords`, tarih filtresi yok, tek sayfa, ve kelimeler üçüncü-tarafa gider (kişi-tanımlayıcı bilgi YAZMA). `sigorta` ve `reklam` için arama bir *dergi sayısı* / *bülten* döndürür; içinde arama ayrı iki-kademeli araçlarla yapılır.

1. **GİB özelgesini ara** (doğrudan-API kurumu; kurum-özel filtreler kullanılabilir).
```json
// call: kurum_karari_ara
{
  "kurum": "gib",
  "keywords": "gayrimenkul değer artışı kazancı istisna",
  "tarih_baslangic": "2023-01-01"
}
```
*Sonuç: Slim girdiler, her biri `gib:<id>` biçiminde bir `document_id` taşır. Kuruma ait olmayan bir filtre (ör. gib'e `karar_turu`) kotadan önce `invalid_params` döner.*

2. **Özelgenin tam metnini getir**.
```json
// call: kurum_karari_getir
{ "document_id": "gib:12345" }
```
*Sonuç: Markdown metin, süresiz cache'lenir. 40.000 karakteri aşarsa `page_number: 2, 3…` ile gez.*

3. **KVKK kararını ara** (dış-arama kurumu; YALNIZ `keywords`, kelimeler Tavily'ye gider).
```json
// call: kurum_karari_ara
{
  "kurum": "kvkk",
  "keywords": "açık rıza olmadan veri işleme idari para cezası"
}
```
*Sonuç: Tek sıralı sayfa (`page` > 1 boştur); `document_id` `kvkk:<...>` biçiminde döner. Sunucuda arama anahtarı yoksa `not_configured` döner — o zaman kullanıcıya dış aramanın yapılandırılmadığını bildir. ⚠️ Bu sorguya asla müvekkil adı veya kişi-tanımlayıcı ayrıntı ekleme.*
```json
// call: kurum_karari_getir
{ "document_id": "kvkk:NzAyOC8yMDIwLTM1OQ" }
```

4. **Reklam Kurulu bültenini ara (iki-kademeli)**. Bir sonuç tüm bir toplantı bültenidir; `document_id` = `reklam:<toplantı no>`.
```json
// call: kurum_karari_ara
{
  "kurum": "reklam",
  "keywords": "yanıltıcı fiyat indirimi"
}
```
*Sonuç: `reklam:336` gibi bir `document_id`. Tüm bülteni okumak için `kurum_karari_getir({"document_id":"reklam:336"})`; ama belirli bir kararı bulmak için bülten İÇİNDE ara:*
```json
// call: reklam_bulten_icinde_ara
{
  "bulten_no": 336,
  "keywords": "indirim"
}
```
*Sonuç: Eşleşen kararlar; her biri `dosya_no`, `sikayet_edilen` (şikayet edilen firma), kategori ve alıntı taşır. Bülten yalnız bir kez indirilip metne çevrilir (cache'lenir), sonraki içinde-aramalar yeniden getirmez. Sigorta Tahkim için aynı desen `sigorta_dergi_icinde_ara({"dergi_no": <n>, "keywords": "..."})` ile çalışır; `<n>`'yi `kurum: "sigorta"` aramasından al.*

### Örnek 11: Belirli Bir Gün Ne Yayımlandı? (Resmî Gazete → konsolide metin)
**Senaryo**: "6 Ağustos 2026 tarihli Resmî Gazete'de vergiyle ilgili ne çıktı, tam metnini ver."

**Strateji**: Resmî Gazete gün bazlıdır: önce o günün fihristini al, ilgili maddeyi başlığından seç, metnini getir. Bir mevzuat değişikliği söz konusuysa RG metni yalnızca **değişiklik metnidir** — yürürlükteki konsolide metin için `mevzuat_ara`/`mevzuat_getir`'e geç.

1. **Günün fihristini al**.
```json
// call: resmi_gazete_fihrist
{
  "tarih": "2026-08-06"
}
```
*Sonuç: `{ sayi, sections: [{ bolum: "Yürütme ve İdare Bölümü", items: [{ baslik, document_id }] }, …], pdf_url }`. Kimlikler `resmi_gazete:20260806/3.htm` biçimindedir — başlıklardan ilgili olanı seç ve `document_id`'yi YANITTAN oku, kurma. O gün mükerrer varsa `mukerrer` listesinde görünür; içeriği için ayrı bir çağrıda `mukerrer_no` geç.*

2. **Seçtiğin maddenin tam metnini getir**.
```json
// call: resmi_gazete_getir
{
  "document_id": "<FİHRİSTTEN_GELEN_DOCUMENT_ID>"
}
```
*Sonuç: Maddenin Markdown metni (HTML kaynaklıysa doğrudan çevrilir, PDF kaynaklıysa OCR'lanır — ilk getirme birkaç saniye sürebilir).*

3. **Bir kanunu/yönetmeliği değiştiriyorsa yürürlükteki konsolide metne geç**. RG'deki metin yalnız değişiklik hükmüdür; "şu an yürürlükteki hâli ne" sorusunu yanıtlamaz.
```json
// call: mevzuat_ara
{
  "mevzuat_no": "<DEĞİŞTİRİLEN_KANUNUN_NUMARASI>",
  "mevzuat_tur_list": ["KANUN"]
}
// Ardından mevzuat_getir ile ilgili maddeyi oku (id_type: "madde", madde_no: …)
```
*Uyarı: `mevzuat_ara`'nın `resmi_gazete_tarihi_start`/`_end` filtresi **yayım** tarihine bakar, yürürlük tarihine değil — değişikliğin ne zaman uygulanacağını her zaman kanunun `Yürürlük` maddesinden doğrula.*

## 6. Kavram Araması — YALNIZCA `semantik_ictihat_ara` Araç Listende Varsa

Bazı hesaplar ek olarak `semantik_ictihat_ara` sunar. **tools/list'inde YOKSA bu bölümü tamamen atla** — bu kılavuzdaki her şey onsuz çalışır.

*   **Ne yapar**: doğal-dil bir sorguyu gömer ve kavramsal olarak en benzer mahkeme kararlarını döner — bir hukuki FİKİR için içtihat gerektiğinde ve tam ifade bilinmiyor veya değişkense faydalı (anahtar kelime araması başka türlü söylenişleri kaçırır).
*   **Ne alırsın**: her isabet doğrudan `ictihat_getir` ile kullanılabilir bir `documentId` artı `related_quotes` (alâkaya göre sıralı eşleşen pasajlar) ve daire/dosya-numarası metadata'sı taşır.
*   **Külliyat düzenli güncellenir** — güncel kararları da kapsar. Yine de birebir ifade, esas/karar numarası veya tarih aralığı gerektiren aramalarda `ictihat_ara` (canlı indeks) daha isabetlidir; kavramla bulduğun kararı oradan doğrula.
*   **Soğuk başlangıç**: boşluktan sonraki ilk sorgu ~20 saniye sürebilir (gömme modelinin ısınması). Sonraki sorgular hızlıdır.
*   **İş akışı**: semantik sorgu → `related_quotes` terminolojisini topla → atıflanabilir kararlar için o terimlerle `ictihat_ara`'yı yeniden çalıştır.

## Son Öğütler

Otonom bir ajan olarak en büyük avantajın, aramaları hızlıca paralelleştirme ve belirli parçaları okuma yeteneğindir.
1. **`mevzuat_icinde_ara` kullanabiliyorken 100 sayfalık bir PDF'i asla okuma**.
2. **Kanun numaralarını asla uydurma**. Emin değilsen `mevzuat_adi` ile ara.
3. **Türk hukukunun ağır kodifiye olduğunu unutma**. Yanıt genellikle geniş bir *Kanun* ile son derece özel bir *Tebliğ*'in, bir *Yargıtay* kararıyla yorumlanan kesişimindedir. İşin bu üç noktayı birleştirmektir.
4. **Kapsamlı çok-kollu araştırma için paralelleştir**. Subagent ya da paralel görev başlatabiliyorsan ve soru birden çok kaynak veya mahkeme kapsıyorsa, orkestrasyon oyun planı için `agentic_legal_deep_research` çağır (ayrıştır → paralel kollar → atıflı sentez).
