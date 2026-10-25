# Chat isteği ile ortak pending alanlarının bağı

20 Ekim 2026. Gelen opcode10 chat çağrısı `004d83c0` adresinde `0x569220` tabanını `00455ec0` işleyicisine geçirir. Dokuz eşleşen skill isteği orijinal context argümanını her yazım için yeniden yükler. Adres bağı şöyledir:

| Alan | Üretici offset'i | Tüketici adresi | Genişlik |
|---|---|---|---|
| Bekleyen istek | +180hex | 005693a0 | BYTE |
| İstek türü | +184hex | 005693a4 | DWORD |
| Gönderen | +188hex | 005693a8 | DWORD |

`work/audit_chat_pending_identity.py` iki kaynak PE sürümünde dokuz yedi-talimatlık store bloğunu, yedi-talimatlık seçilmiş caller aralığını ve üç tüketicide79 doğrudan alan referansını doğrular: toplam298 talimat kaydı. Sender, parsed local DWORD'dan alınır; üreticide WORD'a kırpılmaz. İncelenen doğrudan pending store'larının hepsi BYTE0 temizliğidir. Kaynak `outputs/FarmexBot_chat_pending_kimlik_kaniti.json`; korunmuş Ghidra/PE kanıtıdır, yeni REA Evidence değildir. Dolaylı/alias yazıcılar veya bütün dispatcher reachability'si bu aralıklarla dışlanmaz.

`chat_pending_binding.PendingConsumerFrame`, tamamlanmış **yeni** üretici isteğini açıkça seçilmiş aynı sınıfın tüketici frame'ine bağlar. Mesaj context tabanı kaynakta doğrulanmış569220 olmalıdır; sınıf çağrısının actor context'i ayrı argümandır. Kind ve sender alanları tek, sabit yerel pending görünümünden sağlanır. Çelişen açık alanlar reddedilir. Kısmi WORD register yüklemelerinin üst bitleri türetilmez; tam push gözlemi ayrıca gerekir.

Bu sabit görünüm bağımsız yerel modelin açık sözleşmesidir. Kaynakta taze global okumaların araya giren başka bir thread yüzünden değişmeyeceği kanıtlanmış değildir. Gerçek kaynak eşzamanlılığı varsayılarak bu model canlı çalıştırılmış sayılmaz.

Eksik producer sonucu consumer'ı başlatmaz. Producer yeni istek oluşturmamışsa sonuç `no_new_request` olur; bu önceki bekleyen isteğin olmadığı veya işlendiği anlamına gelmez. Runtime lock, sınıf gate'leri, dış helper normal dönüşleri ve alt generic/direct sonuçlar bağımsız gözlem olarak kalır. Consumer store planları yalnız prospective sonuçlardır; bu adaptör ortak belleğe veya mesajlar arasında kalıcı pending state'e commit yapmaz.

Sekiz yeni test dokuz üretici isteğinden doğrudan tüketiciye kind/sender aktarımını, yanlış context/sınıf/store'ları, çelişen sabit alanları, eksik üreticiyi, yeni istek yokken tüketmeme davranışını ve geç üst normal dönüşünde kayıt korumasını sınar. Tam koşu `CHAT_PENDING_BINDING_VALIDATION.json` içinde kaydedilir.

UI/native C değişmedi; UI yeniden test edilmedi. Mesajlar arası pending state, kilit timer'ı, native callback, gerçek ağ teslimi, server sonucu ve canlı uyumluluk açık kalır.
