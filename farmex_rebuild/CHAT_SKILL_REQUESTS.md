# PM/party mesajından bekleyen sınıf isteği

Sonraki Priest kapsamı: altı türün normal-yol modeli artık ortak consumer API’sine bağlıdır. Aşağıdaki Priest modelinin bulunmadığına ilişkin notlar önceki aşamanın kaydıdır. Native etkiler hâlâ açık. [Priest tüketicisi](PRIEST_CHAT_CONSUMER.md).

Sonraki tüketici kapsamı: Mage/Rogue adaylarının normal-yol modelleri artık mevcut; Priest ve bütün native etkiler açık. Aşağıdaki aday taraması ilk aşamanın kaydıdır. [Güncel tüketici modelleri](CHAT_SKILL_CONSUMERS.md).

20 Ekim 2026. `chat_skill_requests.py`, yalnız ulaşılan `004569d9..00457014` bölümünü modeller. Eski/güncel kaynakta **1844 talimat kaydı**, dokuz gerçek checkbox/metin çiftinin producer bağı ve **18 published form alanı** doğrulandı. Bu Ghidra/PE kanıtıdır; yeni REA Evidence veya canlı yürütme değildir.

Bu bölüm skill'i doğrudan kullanmaz. Eşleşme olduğunda context BYTE `180=1`, DWORD `184=istek türü`, DWORD `188=parsed sender DWORD` yazar. Model üç inert store projeksiyonunu `PendingChatSkillRequest` olarak döndürür; gerçek pending context'e yazmaz.

## Koşul ve öncelik

İlk taze kanal 2 değilse ikinci taze kanalın 3 olması gerekir. Aksi halde sonraki kaynak adresi `00457014` olur; kanal7 notice bölümü bu modelin dışında kalır. İçeri girildiğinde PM alarmı için kanal ayrıca tekrar okunur. Taze değer2 ve global `562281` BYTE'ı nonzero ise Default alarm aralığının normal dönüşü beklenir.

Alarm **runtime/pending kontrollerinden önce** gelir. Global `561f6c` sıfırsa veya context `180` zaten nonzero ise yeni pending istek üretilmez. Önceki istek kendi kendine temizlenmez veya üzerine yazılmaz.

Mage, Rogue, Priest sınıf probe aralıkları sırayla ve ayrı normal/düşük AL gözlemleriyle değerlendirilir. Bir probe true olduğunda o aile dalı seçilir; o ailenin checkbox'ı kapalı veya keyword'ü eşleşmiyor diye sonraki aileye geçilmez. Sabit bir seçilmiş sınıf varsayımıyla bu taze probe'lar birleştirilmez.

| Sıra | Kaynak kontrol/metin | Flag / command offset | İstek türü |
|---|---|---|---|
| Mage | chChatTP / txtChatTP | 18c / 190 | 1 |
| Rogue 1 | chChatSW / txtChatSW | 1b8 / 1c0 | 1 |
| Rogue 2 | chChatWolf / txtChatWolf | 1e8 / 1f0 | 2 |
| Priest 1 | chChatBuff / txtChatBuff | 218 / 220 | 1 |
| Priest 2 | chChatAC / txtChatAC | 248 / 250 | 2 |
| Priest 3 | chChatUnd / txtChatUnd | 278 / 280 | 3 |
| Priest 4 | chChatStr15 / txtChatStr15 | 2a8 / 2b0 | 4 |
| Priest 5 | chChatCure / txtChatCure | 2d8 / 2e0 | 5 |
| Priest 6 | chChatDisease / txtChatDisease | 308 / 310 | 6 |

Yalnız enabled checkbox'ın keyword'ü karşılaştırılır. Karşılaştırma tam byte/uzunluk eşitliğidir; harf farkı korunur. Rogue ve Priest'te ilk eşleşme kazanır; aynı keyword birden fazla request oluşturmaz. Bu, sekiz genel chat komutunun bağımsız if davranışından farklıdır.

Priest Buff açıkken, keyword karşılaştırılmadan önce `004645e4` dönüşü **signed DWORD olarak >=2** olmalıdır. `FFFFFFFF` veya `80000000` bu koşulu sağlamaz. Buff gate başarısızsa sıradaki AC isteği denenebilir. Mage/Rogue için bu ek gate yoktur.

Priest Text alanları formda basit ardışık checkbox+4 düzeninde değildir. AC flag slot'u `1118`, Text slot'u `1124`; Und flag slot'u `1120`, Text slot'u `111c` olarak kaynaktan doğrulandı. Derleyici kontrol adlarını bu gerçek bağlarla eşler.

## Bağımsız sözleşme ve açık işler

`compile_chat_skills(values,WindowsNameCodec(...))`, gerçek panel yollarından lossless ANSI/C-string keyword snapshot'ı üretir. Açık codepage gerekir. `ChatSkillFrame` bir çağrı boyunca tüketilmiş kanal, gate, aile probe ve normal karşılaştırma prefix'ini korur. Son karşılaştırma eksikse önceki aile tekrar seçilmez; tamamlanmış aynı frame tekrar request eklemez.

Bu API henüz deneme arayüzüne bağlı değildir. 18 yeni alan API-only olarak envanterde işaretlendi; UI/compiler271 ve envanter dışında251yol değişmedi. Typed gözlemler, gerçek VCL/string/native helper etkileri veya canlı oyun sonucu değildir. Handler'ın diğer fazları ve cleanup ayrı kalır.

Pending alanlarının absolute karşılıkları `5693a0`, `5693a4`, `5693a8` için bütün3226keşfedilmiş yordamda doğrudan referans taraması da yapıldı. **79 referans talimatının baytları doğrulandı**; adaylar `004994bc`, `004cee18`, `004da568`. Bunlar henüz çözülen skill tüketicileri değildir. İlgisiz context'lerde aynı `180/184` offset'lerinin bulunması tüketici kanıtı sayılmadı. Aliased veya dolaylı başka tüketiciler dışlanamaz.

İsteğin ne zaman tüketildiği, skill/mesafe/başarı kontrolleri, bekleyen bayrağın temizlenmesi ve native çağrı etkileri ayrı çalışmadır. Bu aşamada hiçbir skill çalıştırılmadı.

## Doğrulama

**12 yeni testle toplam 2808 test geçti (7.141 saniye).** Dokuz request türü, full sender DWORD, aile önceliği, ilk eşleşme, disabled compare atlaması, signed Buff sınırları, alarmın gate'lerden önce olması, pending koruması, taze kanallar, normal dönüş boşlukları ve kod sayfası/Text alan bağları sınandı. UI/native C değişmedi; UI yeniden test edilmedi.

Kaynak kanıtı `outputs/FarmexBot_chat_skill_istek_kaniti.json`; üretici `work/audit_chat_skill_requests.py`. Tüketici aday kaydı `outputs/FarmexBot_chat_skill_tuketici_adaylari.json`; üretici `work/find_chat_request_consumers.py`. Uygulama kaydı `CHAT_SKILL_REQUESTS_VALIDATION.json`.
