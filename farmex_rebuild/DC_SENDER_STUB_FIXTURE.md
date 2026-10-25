# DC gönderici şablonunun kendi x86 sürecimizde sınanması

`native/dc_sender_stub_fixture.c`, kaynakta523360 adresindeki26byte şablonun komut biçimini kendi x86 sürecimizde sınar. Şablonun dört operandı yalnız **kendi** context-slot, byte tamponu ve sahte alıcı adreslerimizle doldurulur. Başka bir PID seçilmez; oyun/modül/DLL yüklenmez; OpenProcess, uzak bellek veya uzak thread çağrısı yoktur. Kendi code sayfaları RW olarak hazırlanıp çalıştırılmadan önce RX yapılır.

İki sahte alıcı ECX'i, stack'teki iki argümanı ve giriş ESP'sini kaydeder. Sonra genel register'ları değiştirip carry'yi açıkça set/clear eder ve **RET8** ile döner. Bu alıcı sözleşmesi bizim testimizin açık koşuludur; gerçek oyunun alıcısının da RET8 kullandığı doğrulanmış değildir.

Altı native vaka geçti: bir byte, zero context/zero byte,38byte tampon, sıfır uzunluk, değişen slot değeri ve carry'yi temizleyen farklı alıcı. Bunlar oyun protokolünün geçerli paketleri olarak yorumlanmaz; yalnız kendi argüman aktarımımızı sınar.

Gözlenen sonuçlar:

- Alıcı ECX değeri, kendi slot'umuzun güncel DWORD değeriyle eşleşti; iki stack argümanı kendi tampon pointer'ı ve uzunluğuydu.
- İki argümanı RET8 ile temizleyen alıcı altında çağrı öncesi/sonrası ESP ve EBP aynı kaldı. Alıcı girişindeki ESP, dış ölçümden48byte aşağıdaydı: iki CALL dönüş adresi, PUSHAD32 ve iki argüman8.
- Sahte alıcı register'ları değiştirdiği halde genel register'lar şablon dönüşünde geri yüklendi. EAX, alıcının ürettiği değer değil çağrı öncesi değerdi; bunu sender başarı sonucu sayamayız.
- Carry, alıcının bıraktığı değerde döndü. Şablonda PUSHFD/POPFD yoktur; PUSHAD/POPAD flags'i korumaz. Bu yolun flags davranışı başka gönderici/wrapper modellerine otomatik eşitlenmemelidir.

Yanlış stack temizleme sözleşmeli alıcı çalıştırılmadı. İki PUSH sonrası dengeli dönüş için callee temizliği gerektiği, kaynak biçimi ve pozitif RET8 vakalarından yapılan çıkarımdır. Gerçek sender adresinin veya context'in geçerli olduğunu göstermez. Sıfır context/uzunluk vakaları da yalnız izole şablona aittir; orijinal helper'ın allocation veya oyun nesnesi kapılarını doğrulamaz.

TCC x86 compiler hash'i sabitlendi. Native fixture exe importları kendi VirtualAlloc/Protect/Free ve instruction-cache API'lerini içerir; yasaklanan foreign-process erişim/thread API'lerini içermediği ayrıca kontrol edildi. Derleme ve çalıştırma araç sandbox'ı dışındaki host bağlamında yapıldı; Windows UAC başlatılmadı veya oyun erişimi yapılmadı; host token yönetici durumu bu testte ölçülmedi. CLI argümanlarıyla hedef PID/alıcı verilmez.

Denetim `work/audit_dc_sender_stub_fixture.py`; kanıt `outputs/FarmexBot_DC_gonderici_sablon_own_native_kaniti.json`. Eski/güncel Richard gövdelerinde76+43instruction toplam238 kayıt, şablonun26byte'ı ve iki mevcut REA çıktısı doğrulandı. Native executable ve run log hash'leri de kaydedildi. Dağıtım ZIP'i kendi C/PowerShell kaynaklarını içerir; native test çıktısı exe'sini veya vendor binary'lerini içermez.

Önceki Python uygulaması değişmediği için3474test sonucu tarihsel olarak yeniden kullanılır; Python/UI testleri bu aşamada tekrar koşulmadı. Yeni doğrulama altı gerçek own-native vakadır. Oyun ABI'si, remote transfer/thread/wait/failure davranışı, actual sender profile/SEH ve canlı uyumluluk açık kalır. `owned_native_execution_verified=True`, oyun/native uyumluluk bayraklarıFalse olarak ayrı tutulur.
