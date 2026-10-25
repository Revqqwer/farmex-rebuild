# Oyun göndericisinin operand zinciri ve kuyruk bağı

19 Ekim 2026. `native_sender.py`, Richard'ın `00464918` wrapper'ını gerçek çağrı yapmadan modeller. Aynı yordamın eski/güncel16talimatı, kuyruk çağrı aralığı ve güncel constructor store/caller aralıkları toplam **66 talimat kaydıyla** disk baytlarından doğrulandı. Kaynak Ghidra/PE karşılaştırmasıdır; REA aracı çıktısı veya canlı yürütme değildir.

Kaynak sırası şöyledir: `553e84` globalinden slot adresini al, slotun DWORD değerini doğrudan okuyup ECX yap, uzunluğu sonra tampon pointer'ını stack'e push et, taze `553e90` globalini oku ve dolaylı çağrı planla. Kaynakta null-slot erken dönüşü yoktur; eksik doğrudan okuma modelde sıfır veya başarıya çevrilmez.

Wrapper `PUSHAD/PUSHFD` ve `POPFD/POPAD` kullanır. Çağrı normal döndüğünde caller register'ları, EAX dahil, ve flags geri yüklenir. Hedefin dönüş EAX'i bu wrapper tarafından gönderim başarısı olarak dışarı aktarılmaz. Hedefin iki argüman için8bayt stack temizliği yapması beklenir; bunun gerçek hedef ABI'siyle uyuştuğu doğrulanmadı. Native hedef normal dönüşü ile wrapper normal dönüşü de ayrı gözlemlerdir; ikisi server ACK değildir.

| Güncel kaynak profili | Context slot adayı | Send target adayı |
|---|---:|---:|
| US (`004fd640`) | `0x1128a94` | `0x70b360` |
| Steam (`004e4398`) | `0x11eaa84` | `0x6241a0` |

Bu literal'ler constructor'a `553e3c` gönderilen çağrılardan ve `+48/+54` store'larından elde edildi. Eski US `0x7032e0` adayı güncel tablo değeri değildir. `SOURCE_SENDER_DEFAULTS` yalnız açıkça etiketlenmiş kaynak sabitleridir; plan eksik gözlemi bunlarla otomatik tamamlamaz. Runtime sonradan bu global'leri değiştirebilir.

Sonraki analiz, profilin EXE klasöründeki `steam_api.dll` için kaynak FileExists sonucuyla seçildiğini doğruladı. Bağımsız detector-tail/startup alan projeksiyonu ve iki taze mode okumasının ayrıntıları [SOURCE_PROFILE_SELECTION.md](SOURCE_PROFILE_SELECTION.md) içindedir; gerçek canlı seçim veya global değer ölçümü değildir.

Korunmuş ca69cece…952a9 US oyun dosyasında iki context slotu da sanal aralık içindedir fakat dosya baytları yoktur. Sıfır bağlam çıkarılamaz. Güncel US target için diskte32bayt bulunur; bu baytların varlığı ve section'ın executable işareti gerçek çağrılabilir kod/ABI kanıtı değildir. Steam literal'lerinin aynı US disk geometrisine düşmesi bir Steam dosyasını doğrulamaz. Önceki bad-instruction analizi eski US adayıyla ilgili tarihsel kayıttır; yeni adrese taşınmış sayılmaz.

`SenderObservation` pointer, immutable payload snapshot'ı, iki sıralı global okuması, doğrudan context okuması ve native-normal dönüşü ayrı taşır. `plan_source_sender` hiçbir bellek okumaz, hedefi çağırmaz veya gönderim yapmaz. Bound payload karşılaştırması bağımsız kuyruğa ait bir provenance kontrolüdür; kaynakta böyle bir byte karşılaştırması yoktur ve gerçek native tamponun sahipliğini ispatlamaz.

`QueueSample.sender_inputs` verilirse yalnız due ve connected dalda bu plan değerlendirilir. Yerel kaydın byte snapshot'ı/operandı/hedef dönüşü eksikse eski `sender_returned=True` değeri kaydın kaldırılmasına yetmez. Child plan tamamlandıktan sonra `sender_returned` ayrıca wrapper normal dönüşü için gerekir. Henüz due olmayan kayıt, bilinmeyen bağlantı ve disconnected-drop dalı gönderici operandlarını tüketmez. Her kayıt bağımsız context/target gözlemleri kullanır.

Legacy `sender_inputs=None` fixture yolu uyumluluk için durur. Mevcut Eylem Kuyruğu UI'si bu yolu kullanır; ayrıntılı gönderici operandlarını henüz UI'den toplamaz. Modelin `complete` sonucu yalnız gözlemlerle tanımlanan dar planın tamamlandığını gösterir; native yürütme/ABI/gerçek ağ veya canlı üyelik sertifikası değildir.

**11 yeni testle toplam2668 birim testi geçti (6.717s).** Sıralı eksik/yanlış okumalar, null-slot gözlem boşluğu, raw DWORD sınırları, payload uyuşmazlığı, ulaşılmayan binding, ayrı child/parent dönüşleri ve kayıt başına bağımsız context/target sınandı. UI ve native C kodu değişmedi; bu tur UI/native fixture tekrar çalıştırılmadı. Son tam UI2657aşamasında geçti.

Canlı bağlantı hâlâ runtime slot/context/target gözlemlerine, doğrulanmış hedef ABI'sine ve gerçek oturumda bağımsız karşılaştırmaya ihtiyaç duyar. Önceki yönetici HP/MP testi okuma hakkı alamamıştı; bu çalışma o engeli kaldırmadı ve yeni yönetici testi başlatmadı.
