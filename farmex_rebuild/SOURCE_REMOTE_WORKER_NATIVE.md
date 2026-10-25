# Özgün işçinin kendi askıda çocuğumuza aktarılması

23 Ekim 2026. Önceki [yerel DLL deneyi](SOURCE_LOADER_BRIDGE_NATIVE.md)
aynı süreç içinde çalışıyordu. Bu yeni deney, parent'ın yalnız kendisinin
oluşturduğu hash-pinned x86 child'a görüntü, özgün işçi ve bağlam aktarmasını sınar.
Mevcut PID/program yolu veya çalışma anında DLL/payload girdisi kabul edilmez.

Kendi DLL hash'i `4510845e33931b26da0381adfa12e414c4ef72d9c0206728952f6ecfe1903c3a`.
Parent sibling dosyasını hash/boyut/image-base/export RVA'larıyla sabitler ve
yazmaya kapalı handle ile tutar. CREATE_SUSPENDED ile yalnız bu sibling'i
oluşturur; own-job sınırı ve hata temizliği de yalnız bu child'a aittir.

| Aktarım | Child allocation | Bayt | Yazım |
|---|---|---:|---:|
| Kendi DLL başlığı + üç section | 20000000 | 10752 | 4 |
| Özgün Loader0041e558 işçisi | 21000000, RX | 431 | 1 |
| Altı DWORD kaynak bağlamı | 22000000, RW | 24 | 1 |

431 byte kaynakla aynıdır; operand veya başka byte değiştirilmez. Child'ın
kendi preflight export'u, kodu ve tam5000hex görüntüyü sıfır aralıkları dâhil
karşılaştırır. Bağlamın sabit adresleri, kendi süreç metadata'sı ve LoadLibraryA /
GetProcAddress adresleri child içinde yeniden doğrulanır. Önceden yüklenmiş iki
dependency'nin sistem dizininde olduğu da kontrol edilir. Hash-pinned child
pin üreticisi bu iki yardımcı export'u ayrıca zorunlu tutar.

Olumlu akışta üç thread kendi child'ında sırasıyla preflight, ayrılan allocation'daki
özgün işçi ve kendi fixture-yayın helper'ını çalıştırır. Özgün işçi normal exit1
döndürür. Son helper116 relocation hedefi ve43 IAT adresini doğrular; DLL attach'i
tekrar çağırmaz. Header R, text RX ve data RW korunmasına geçer, yalnız kendi
sentetik arena'sını yayımlar. Üretim game export'u own-hostta WRONG_PROCESS ve
sıfır okuma verir. Parent FILE_MAP_READ ile84-byte fixture çerçevesini doğrular:
HP250/500, MP100/300, producer PID, ABI, sequence2 ve native okuma24 byte.

Bu yayın kontrolü yapılırken own application-main event'i hâlâ işaretlenmemiştir.
Kod/bağlam allocation'ları parent tarafından bırakılır. ResumeThread önceki sayıyı1
döndürür; child-main event'i sonra işaretlenir. Bırakma event'i, DLL detach/temizliği,
child exit0 ve paylaşım haritasının yokluğu doğrulanır. Bu, bütün Windows
loader/TLS başlangıcının veya koruma bileşenlerinin hiç çalışmadığını göstermez.

| Deney | Beklenen sonuç |
|---|---|
| Özgün işçi olumlu zinciri | Stage8, worker exit1, publish/child exit0 |
| Aktarılan başlığın bir byte'ı yanlış | Preflight66; özgün işçi başlamaz |
| Bağlamdaki LoadLibrary adresi yanlış | Preflight62; özgün işçi başlamaz |
| Eski resident hazırlayıcı/transfer regresyonu | Stage8, child exit0 |

İki negatif durumda yalnız kendi yeni child'ı sonlandırılır; ana thread
devam ettirilmez. Bu beklenen retler test başarısızlığı gibi sayılmaz.
Ek offline kontrolde, source helper export'ları olmayan baseline child için
`prepare_bootstrap_child.py --source-worker` çıktı üretmeden reddeder.

Native pin üreticisinin Python dosyası değişti; pozitif/baseline build'ler ve
eksik-helper ret kontrolüyle sınandı. Uygulamanın diğer Python dosyaları önceki
manifestle aynıdır. 3860 Python testi ve son1037-kontrol UI sonucu kendi
kapsamlarında korunur; bu native denemeler o sayılara eklenmez.

Orijinal dış Loader0041e710 kodu burada çalıştırılmadı; aktarımı yapan parent
kendi denetimli yeniden yazımımızdır. Orijinal431-byte işçi gerçekten kendi
child'ında çalıştı. Oyun seçimi, oyun üzerinde okuma/yazma/thread/modül işlemi,
oyun başlangıcındaki haklar, güncel adres uyumu ve canlı bot özellikleri0/kanıtsızdır.
Kendi child'ımıza verilen haklar güncel oyuna verilecek hakların kanıtı değildir.
