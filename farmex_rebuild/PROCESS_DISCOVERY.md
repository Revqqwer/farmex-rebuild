# Süreç görünürlüğü ve güncel canlı kontrol

18 Ekim2026. `game_provider.discover_game_processes`, Toolhelp süreç
listelemesinin normal bitişini hata/partial sonuçtan ayırır. Önceki
`find_game_processes` ilk/sonraki API false dönüşlerinin LastError değerini
incelemiyordu; hata da empty PID listesi sayılabiliyordu. Bugünkü ilk boş
sonucun gerçekten bu bug'dan geldiği ileri sürülmez; ayrı yeniden ölçüm
aşağıdadır.

Microsoft belgelerinde false dönüşte ERROR_NO_MORE_FILES normal bitişi
gösterir: [Process32FirstW](https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/nf-tlhelp32-process32firstw),
[Process32NextW](https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/nf-tlhelp32-process32nextw).
Kod her call öncesi LastError'ı temizler; false sonrası hemen yakalar.
Diğer hata veya hata kodu verilmemesi complete/absence sayılmaz. CloseHandle
sonradan hata değerini değiştirirse yakalanmış tanı korunur.

`ProcessDiscovery` PID tuple,scanned count,normal completion,API aşaması ve
raw hata kodunu taşır. Partial eşleşmeler tanıda tutulabilir ama eski list
interface'inden verilemez: `find_game_processes` `ProcessDiscoveryError`
fırlatır. ConnectionPage bu durumda provider.observe çağırmaz ve ayrı
listeleme hatası gösterir. Complete empty list de yalnız bu oturumdan
oyunun görülemediğini söyler; global oyun kapanışı kanıtı değildir.

## İki execution scope karşılaştırması

Aynı provider SHA253e6fbd...41c4 ve64bit Python, iki ölçümde de adminFalse:

| Scope | Taranan süreç | Knight PID |
|---|---:|---|
| Varsayılan sandbox |4|Yok|
| Sandbox dışında, normal kullanıcı|275|14788|

Desteklenen pencere sağlayıcısı da aynı oyun yoluna ait iki pencere döndürdü.
Panel snapshot'ı minimized hatası verdi; bu aşamada aktivasyon/input
yapılmadı. Dolayısıyla default terminalden oyunun kapalı olduğu sonucu
çıkmaz. Scope farkı bu ölçümlerde doğrulandı; bütün Windows envanterleri
veya belirli bir güvenlik bileşeni için genelleme yapılmaz.

Raporlar `outputs/FarmexBot_surec_gorunurlugu_{default,outside_sandbox}.json`,
`outputs/FarmexBot_host_oyun_pencere_yeniden_kontrol.json`; karşılaştırma/hash
kanıtı `outputs/FarmexBot_surec_gorunurlugu_karsilastirma.json` içinde.
Üreticiler `work/record_process_visibility.py` ve
`work/finalize_process_visibility.py`. Bunlar REA Evidence değildir.

## Güncel okuma sonucu

Host normal-user üretim reader PID14788 tam yol ve kayıtlı7008392byte/
ca69cece...952a9disk kimliğini doğruladı. Ardından OpenProcess(VM_READ)
**hata5** verdi; handle açılmadı, hiçbir oyun belleği okunmadı ve HP/MP alanı
üretilmedi. Granted-access maskesi bu ölçümde bilinmiyor (`None`); önceki
16Ekim admin ölçümlerindeki0maskeyle aynı gözlem sayılmaz.

Token metadata'sı observer medium2000/elevatedFalse,game high3000/
elevatedTrue gösterdi. Bu ölçüm yetki farkını kanıtlar; admin testinin
kesinlikle okuyacağını veya DACL/driver/koruma nedenini kanıtlamaz.
Oyun action,write,protection veya privilege değişimi yapılmadı.

Güncel PID/hash'e sabit tek-shot admin HP/MP helper'ı hazırlandı:
`work/elevated_host_vitals_14788_once.py`. Kendi kendini yükseltmez; PID,
hash veya elevation değişirse durur, exclusive claim ile tekrar çalışmaz.
Yalnız mevcut üretim HP/MP reader'ını kullanır. Yeni kullanıcı onayı ve
manuel Windows UAC sonrası çalıştırıldı; sonucu aşağıdadır.
Oyun zaten açık olduğundan önceki kullanıcı giriş talebi geri çekildi.

10yeni test dahil **2396 test geçti (7.802 saniye)**; discovery/provider/
native-provider odaklı33 test geçti. First/Next hata,partial PID,unknown
error0,normal terminator,invalid handle,close sonrası tanı ve UI'nın partial
snapshot'la okumaması sınandı. Tam gizli UI1037kontrol/11form/18sekme geçti.

Gerçek HP/MP,orijinal iç-süreç yöntemi,send ABI ve bütün feature parity
hâlâ açık. Dış okuyucu testi orijinal bot bağlantısının eşdeğeri sayılmaz.

## Onay sonrası yönetici testi

18 Ekim19:44UTC: Kullanıcının yeni onayı ve Windows UAC sonrası tek seferlik
HP/MP testi yönetici olarak tamamlandı. PID14788 ve kayıtlı disk hash'i eşleşti.
VM_READ isteği handle döndürdü, fakat verilen erişim maskesi0idi. Üretim
okuyucusu validate_vm_read_handle_access aşamasında durdu; HP/MP alanları boş,
bellek okuması0bayt. Yönetici çalıştırma tek başına erişimi çözmedi; hakkı
kaldıran bileşen kanıtlanmadı. Oyun yazımı/eylemi/koruma değişimi0.
Kanıt: outputs/FarmexBot_host_HPMP_admin_14788_once.json; hash ve invariant
kontrolü: outputs/FarmexBot_admin_HPMP_sonuc_dogrulamasi.json.
Canlı uyumluluk doğrulanmadı. Test tek seferliktir, yeniden başlatılmadı.
