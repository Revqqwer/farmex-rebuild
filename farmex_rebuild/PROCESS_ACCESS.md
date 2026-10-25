# Canlı okuyucunun handle erişim tanısı

18 Ekim19:44UTC: Kullanıcının yeni onayı ve Windows UAC sonrası tek seferlik
HP/MP testi yönetici olarak tamamlandı. PID14788 ve kayıtlı disk hash'i eşleşti.
VM_READ isteği handle döndürdü, fakat verilen erişim maskesi0idi. Üretim
okuyucusu validate_vm_read_handle_access aşamasında durdu; HP/MP alanları boş,
bellek okuması0bayt. Yönetici çalıştırma tek başına erişimi çözmedi; hakkı
kaldıran bileşen kanıtlanmadı. Oyun yazımı/eylemi/koruma değişimi0.
Kanıt: outputs/FarmexBot_host_HPMP_admin_14788_once.json; hash ve invariant
kontrolü: outputs/FarmexBot_admin_HPMP_sonuc_dogrulamasi.json.
Canlı uyumluluk doğrulanmadı. Test tek seferliktir, yeniden başlatılmadı.

18Ekim güncellemesi: Varsayılan sandbox4süreç/0game, aynı normal kullanıcı
host scope275süreç/PID14788 gördü. Pencere sağlayıcısı da oyun pencerelerini
buldu; boş default liste oyun kapanışı kanıtı değildir. Host HP/MP denemesi
disk kimliği sonrası OpenProcess(VM_READ)hata5 ile durdu;bytes0,maskNone.
Observer medium/nonadmin,game high/admin metadata'sı ayrıca ölçüldü.
Bu sonuç önceki admin0maske kayıtlarıyla karıştırılmamalı. Ayrıntı:
[PROCESS_DISCOVERY.md](PROCESS_DISCOVERY.md). Yeni tek-shot admin test onay sonrası tamamlandı; güncel sonuç yukarıdadır. Aşağısı tarihseldir.

## 16 Ekim14:48UTC — PID19216 yeniden doğrulaması

Kullanıcının önceden onayladığı salt metadata tanısı, PID19216ile aynı beklenen oyun yolu/hash kapıları altında yönetici olarak tamamlandı. VM_READ0x10isteği handle açtı; NtQueryObject56bayt kaydındaki verilen maske0idi. QUERY_LIMITED0x1000, QUERY_INFORMATION0x1400aldı. Root-slot11289c0sayfası committed/MEM_IMAGE, allocation base400000ve protect0x40olarak gözlendi. Önceki PID20832ölçümündeki0x4ile fark, farklı süreç/ölçüm zamanlarına aittir; VirtualProtect veya başka belirli bir bileşenin bu değişime neden olduğu kanıtlanmadı.

VM_READ hakkı gözlenmediği için HP/MP değer testi yeniden çalıştırılmadı. Sayfa metadata'sının sorgulanabilmesi ve sayfanın read/write/execute koruması dış handle'a okuma hakkı vermez. Oyun değer okuması/yazımı, koruma değişimi, ayrıcalık değişimi, modül yükleme ve oyun eylemi0dır. Hakkı kaldıran bileşen ve gerçek HP/MP hâlâ bilinmiyor.

Bu PID'de CRT dosya yolunun0x321a0000tabanındaki eşlemesi10:39UTC'de gözlenmişti.14:48UTCerişim tanısı o eşlemeyi yeniden sorgulamadı; eski kayıt güncel modül snapshot'ı veya kod kimliği olarak sunulmaz. Kanıt: `FarmexBot_canli_erisim_maskesi_bot_panel_19216_once.json`; karşılaştırma/hashler: `FarmexBot_panel_oturumu_erisim_karsilastirma.json`. Önceki PID'lere ait hata nedenleri bu sonuçla geriye dönük kesinleştirilmez.

`process_access.py`, zaten açılmış handle için NtQueryObject/ObjectBasicInformation ile verilen erişim maskesini sorgular. Süreç açmaz, bellek değeri okumaz, handle kapatmaz veya ayrıcalık değiştirmez. API yoksa, hata verirse veya dönen kayıt boyutu beklenmedikse sonuç bilinmeyen (`None`) kalır. Gözlenen sıfır maske bilinmeyen değildir.

`game_provider.py` önce mevcut yol/PE/hash-boyut kapılarını uygular. VM_READ handle açılınca yeni metadata kontrolünü yapar. Bilinen maske PROCESS_VM_READ içermiyorsa `validate_vm_read_handle_access` aşamasında durur; hiç ReadProcessMemory çağırmaz. Metadata bilinmiyorsa önceki salt okunur okuma/hata kontrolleri devam eder. Gözlenen maske, snapshot alanlarına veya bağımsız canlı doğrulamaya eşdeğer değildir.

Observation içindeki `granted_access` raw maskedir veya None'dır. Eksik hak nedeniyle kendi doğrulamasının durması, Windows'tan yeni bir hata5 alınmış gibi etiketlenmez; `error_code=0` ile ayrı aşama ve açıklama döner. Oyun belleği okunmadığı için bytes_read0 kalır.

`disk_identity_verified` yalnız dosya kimliği kayıtlı hash/boyut tablosunda bulunduğunda True olur. Hash hesaplanmış olması yeterli değildir. Bağlantı sayfasındaki sürüm eşleşme mesajı artık bu alanı kullanır. Gerçek canlı veri hâlâ ayrıca doğrulanmalıdır.

## 16 Ekim canlı metadata sonucu

Kullanıcının onayladığı yönetici tanısı, oyun yeniden başladığı için önce eski PID5100'ü reddetti; oyun handle'ı açılmadı. Sonraki tek seferlik tanı tek oyun sürecini tam dosya yolu ve mevcut disk hash'iyle doğruladı: PID20832, SHA256ca69cece…952a9. Observer elevatedTrue idi.

| İstenen erişim | Handle açıldı | Gözlenen verilen maske |
|---|---|---|
| QUERY_LIMITED_INFORMATION,1000 | Evet | 1000 |
| PROCESS_VM_READ,10 | Evet | 0 |
| QUERY_INFORMATION,400 | Evet | 1400 |

Maskeler hexadecimal'dir. Dolayısıyla güncel VM_READ isteğinde açılan handle okuma hakkı taşımıyor. Bu, yönetici yetkili dış okuyucunun yalnız OpenProcess başarısına güvenemeyeceğini doğrudan gösterir. Hakkın hangi bileşence kaldırıldığı belirlenmedi; anti-cheat/driver/DACL nedenlerinden biri kanıtlanmış gibi sunulmaz. Önceki PID5100 okuma hatasının nedeni bu yeni oturum ölçümüyle geriye dönük kesinleşmiş sayılmaz.

QUERY_INFORMATION handle'ıyla yalnız iki sayfanın metadata bilgisi alındı:400000 görüntü tabanı committed/image/read-only;11289c0 aday kök slotunun sayfası committed/image/read-write. İki alanın allocation base'i400000. Bu, aday kök slotunun bulunduğu sayfanın varlığını gösterir; root DWORD'u veya HP/MP okunmadı, alan anlamı doğrulanmadı. Oyun bellek değer okuması/yazımı, koruma değişimi, modül yükleme ve oyun eylemi sayıları0'dır.

Kanıtlar: FarmexBot_canli_erisim_maskesi_admin_yeni_oturum_once.json ve FarmexBot_okuma_metadata_oz_testi.json. Önceki iptal edilen Windows başlatması ve eski PID'yi reddeden tanı, başarılı bellek kontrolü olarak sayılmaz.

## Kendi süreç kontrolü

Yedi Win32 vaka geçti. Üretim query fonksiyonu kendi süreç handle'larında metadata yardımcısıyla aynı maskeleri döndürdü. Aynı ReadProcessMemory parametre biçimi kendi DWORD'umuzu okudu. Kendi testimizde okuma hakkı olmayan handle hata5, PAGE_NOACCESS alanı hata299 verdi. Bunlar bu makinede ölçülen kontrol sonuçlarıdır; tüm Windows hata nedenleri için evrensel sınıflandırma değildir.

API tanımları: [NtQueryObject ve GrantedAccess](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntqueryobject), [VirtualQueryEx erişim gereksinimi](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualqueryex), [sayfa metadata alanları](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-memory_basic_information). API'nin değişebileceği için üretimde metadata yokluğu erişim reddi sayılmaz.
