# DC, kalkma ve Town yardımcılarının bağımsız modelleri

Sonraki UI bağı: ayrıntılı yardımcı seçeneğiyle bu modeller Chat Komutları denemesinde kullanılabilir. 2772 test ve tam gizli UI geçti. Aşağıdaki UI bağlantısı bulunmadığına ilişkin notlar ilk aşamanın kapsamını anlatır. [Güncel ayrıntılı deneme](COMMAND_HELPERS_UI.md).

20 Ekim 2026. `command_helpers.py`, chat komutlarının üç yardımcısını ayırır. Kaynak çağrılarının gerçek oyun etkileri ayrıca doğrulanmalıdır; bu modül Win32 API, thread veya kod parçası yürütmez.

| Kaynak yardımcı | Bağımsız veri/işlem modeli |
|---|---|
| `004c7e0c` — DC komutu | `00` tek bayt; length1/delay0 ile own kuyruğa |
| `004c8d48` — kalkma komutu | `12 01` iki bayt; length2/delay0 ile own kuyruğa |
| `00465678` → `00465ca4` — Town | Sabit `/Town` string'inden80bayt kayıt ve22bayt kod şablonu projeksiyonu |

DC/kalkma çerçevesi bağlantı gate'ini bir kez tüketir. Gate nonzero olup tick eksikse sonraki adım gate'i değiştirmez. Gate0 bilinen enqueue-atlamasıdır; başarılı iletim sayılmaz. Tamamlanan aynı frame yeni kayıt eklemez. Paketlere aktör, isim veya başka tahmini alan eklenmez. Üst helper normal dönüşü yerel enqueue sonucundan ayrıdır.

Town bir ağ paketi olarak kuyruğa eklenmez. Kaynak `VirtualAlloc` ile0x50bayt alan ister; bu alanı sıfırlar, `/Town` beş baytını başa koyar, `+0x10` konumuna uzunluk BYTE5, `+0x14` konumuna tür BYTE0f kopyalar. Model bunları kendi bytearray'inde kurar. String-lifetime ve bütün kopya/cleanup normal dönüşleri ayrı receipt'lerdir.

Kaynak22bayt şablonun `+3` alanına `553e80` globalinin DWORD değerini, `+8` alanına kayıt pointer'ını, `+14` alanına `553eec` globalinin DWORD değerini koyar. Şablon PUSHAD, `MOV ECX,[root-slot]`, kayıt pointer'ını push, dolaylı çağrı, POPAD ve RET biçimindedir. PUSHFD/POPFD içerdiği varsayılmaz. Root-slot operandı, daha sonra thread'in okuyacağı root DWORD'u değildir; bu ikinci canlı değer burada bilinmez.

`00464740` kaynakta kod alanı ayırma/kopyalama, **aynı süreçte CreateThread**, handle nonzero ise sonsuz wait, CloseHandle ve VirtualFree içerir. Bu raporda onun dönüşü opaque bir sınır olarak tutulur. CreateThread0döndüğünde de yardımcı normal dönebilir; normal dönüş, Town callback'inin çalışması veya oyunun komutu kabul etmesi değildir. Model thread oluşturmuyor ve şablonu çalıştırmıyor.

Kaynak kayıt allocation sonucuna memset öncesi null kontrolü koymaz. Bağımsız modelde0allocation `unchecked_null_allocation` boşluğunda durur; bu kaynakta bulunan güvenli bir erken dönüş gibi sunulmaz. Arbitrar metin taşmaları modellenmez; kapsam yalnız sabit `/Town` beş baytıdır.

`TownFrame` tüketilmiş allocation/global/normal-return öneklerini korur. Sonraki helper boşluğu geldiğinde kaynak pointer veya root yeniden gözlemlenmiş gibi değiştirilmez. Tamamlanmış bir Town planı yanlış record literal'i, farklı şablon opcode'u veya uyuşmayan buffer pointer'ıyla etiketlenemez.

`ChatCommandsObservation.action_executions` isteğe bağlı typed child plan bağlar. Ulaşılan DC/kalkma/Town action'ında kind eşleşir ve child tamamlanmamışsa `action:<key>` normal dönüşü bunu bypass edemez. Child hazır olduğunda üst helper normal dönüşü yine ayrıca gerekir. `ChatCommandsFrame` geç gelen tamamlanmış child ile önceki karşılaştırma önekini tekrar istemeden devam eder. Ulaşılmayan farklı kind değerlendirilmez. Mevcut UI raw normal-return fixture yolunu korur; detaylı child binding henüz UI JSON alanı değildir.

**Eski/güncel iki ikilide toplam426talimat kaydı**, payload literal'leri, Town string/şablonu ve Win32/CRT import kimlikleri dosya baytlarıyla doğrulandı. Frame setup/string-lifetime alt yordamları opaque kaldı; bütün gövde eşdeğerliği sertifikası verilmedi. Bu Ghidra/PE audit'idir, REA aracı çıktısı değildir.

**12 yeni testle toplam2729 birim testi geçti (6.949s).** Exact seed, gate/tick/tekrar kayıt, Town80bayt/22bayt patch'leri, her normal-return boşluğu, null allocation, global sıra, tüketilmiş önek ve chat child/parent kapıları sınandı. UI/native C değişmedi; son tam UI2717aşamasında geçti. Gerçek memory/thread/target ABI/ağ teslimi ve canlı uyumluluk doğrulanmadı.
