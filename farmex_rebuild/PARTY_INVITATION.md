# Parti daveti karar modeli — 19 Ekim 2026

19 Ekim parti daveti UI: Gerçek panel flag/listesi, açık codepage, captured HEX ve ulaşılan JSON gözlemleri davranış denemesine bağlandı. Default boş veride bekler; sentetik Alice örneği ayrıdır; yanıt gönderilmez. **2619 test geçti (7.604 saniye)**; tam gizli UI1037kontrol/11form/18sekmede geçti. Canlı yakalama/üyelik açık. Ayrıntı: [PARTY_INVITATION_UI.md](PARTY_INVITATION_UI.md).

`party_invitation.py`, parti davet ayarlarını ve yakalanmış opcode2f/subtype2 girdisindeki karar sırasını bağımsız API olarak modeller. Arayüz motoruna veya gerçek ağa bağlanmadı; hiçbir oyuncuya davet, kabul veya ret gönderilmedi.

Panel üreticisinde otomatik kabul +1cc, “tümünü kabul et” seçiminin tersi +1cd, liste dışını reddet +1ce ve Party Bug Engelle +1cf baytlarına gider. Liste modu için yalnız all-radio okunur; diğer radyo doğrudan getter girdisi değildir. PartyList'in bütün caption satırları, checked durumuna bakılmadan işlenir.

Own derleyici açık Windows codepage ister ve kayıplı dönüşümü reddeder. Kaynak caption'ı ANSI'ye çevirip char* üzerinden std::string oluşturduğu için NUL sonrası kısım isimde kullanılmaz. İsimlerin sırası, tekrarları ve büyük/küçük harfleri korunur. Bu, gerçek VCL/vector/heap veya oyun codepage kanıtı değildir.

Karar sırası önce blocker baytı, sonra korumalı party-state EAX'ının düşük baytının tam1 olması ve otomatik kabul bayrağıdır. Bu erken çıkışlar davet alanlarını okumaz. Sonrasında WORD davetçi kimliği, WORD isim uzunluğu ve isim kopyası ayrı normal dönüşler ister. Own captured parser kısa paketlerde durur; kaynak native bellek taşması/fault davranışını emüle etmez.

İsim kopya yardımcısı da uzunluk kadar baytı kopyaladıktan sonra C-string oluşturur. Dolayısıyla paket içindeki NUL std::string ismini keser; length alanı kullanılarak gereken captured baytlar yine tam bulunmalıdır. Örneğin `Alice\0Bob`, normal C-string sözleşmesinde `Alice` ile karşılaştırılır.

İsim filtresi **tümünü kabul et modunda bile** çağrılır. Normal stable own vector modu exact byte eşitliği kullanır; ayrı normal dönüş gerekir. Alternatif raw filter EAX gözlemi bu own eşitlikle karıştırılamaz.

| Durum | Planlanan helper | Yordamın kaynak dönüşü |
|---|---|---|
| Tümünü kabul et veya listede eşleşme | Kabul | Party Bug baytı nonzero ise0, değilse1 |
| Liste dışı ve reddet etkin | Ret | 0 |
| Liste dışı ve reddet kapalı | Eylem yok | 1 |

Kabul/ret helper'ı ve son isim temizliği ayrı normal dönüşler ister. Bu0/1 sonuçları, gerçek parti üyeliği veya dış hook'un nihai paket uygulaması olarak yorumlanmaz. Action alanı yalnız istenen source çağrısıdır.

11 yeni test dahil **2611 yerel test, 6.583 saniye** geçti. Erken kapılar, liste/all modları, kabul/ret dönüşleri, case duyarlılığı, NUL, eksik paketler ve helper boşlukları sınandı. İki korunmuş ikilide1548talimat kaydı, form/method/import kimlikleri ve CRT char_traits.length→strlen wrapper baytları doğrulandı. Byte karşılaştırması önceki pinned CRT compare→memcmp denetimine bağlandı. Kapsamlar örtüşebilir; tam fonksiyon veya native runtime sertifikası değildir. Kanıt Ghidra/disk/form/import verisidir, REA Evidence değildir.

Kaynak isim kopyası length bayt ayırdıktan sonra terminatör yazıyor. Native allocator/fault/exception etkileri own bounded parser'ın kapsamı dışındadır. UI değişmedi ve bu tur UI testi tekrarlanmadı. Chat/PM daveti, dinamik party-list yenileme, gerçek kabul/ret ve canlı uyumluluk açıktır.

Ayrı incelemede nonzero callback guard dalının CAPTCHA yenileme metni taşıdığı saptandı. Bu yalnız pasif kanıt olarak kaydedildi; manuel/native sınırda AL bilinmeyen tutulur. CAPTCHA çözme, yenileme otomasyonu veya atlatma eklenmedi.
