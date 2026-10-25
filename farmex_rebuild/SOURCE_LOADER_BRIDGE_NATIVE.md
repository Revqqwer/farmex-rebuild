# Özgün işçi → kendi DLL'imiz → salt okunur IPC

23 Ekim 2026. Önceki [431-byte işçi testi](SOURCE_LOADER_WORKER_NATIVE.md)
kontrollü sentetik görüntü ve API sonuçları kullanıyordu. Bu yeni deney aynı
değiştirilmemiş işçiyi kendi gerçek DLL görüntümüzle çalıştırdı. DLL SHA256:
`4510845e33931b26da0381adfa12e414c4ef72d9c0206728952f6ecfe1903c3a`.
Orijinal FarmexBot DLL'i veya oyun çalıştırılmadı.

`build_local_bootstrap_fixture.ps1 -SourceWorker` ayrı kendi x86 hostunu üretir.
DLL build sırasında hash/boyut/PE yapısıyla sabitlenip gömülür; çalışma anında
DLL yolu, payload veya mevcut PID kabul edilmez. Context ve bütün hedefler
yalnız bu hostun kendi allocation'larıdır. Özgün işçi kodu RX sayfasına aynen
kopyalanır; kendi DLL görüntüsü hazırlıkta RWX, sonrasında bölüm bazında korunur.

DLL'nin bütün bölümleri ve 116 HIGHLOW girdisi önceden sınır denetiminden geçer.
İşçi bu düzeltmeleri gerçekten uygular; sonra her hedef beklenen değere eşit
olduğu için 116 yazım doğrulanır. İki dependency yalnız sistem dizininden yüklenir.
Bağlamdaki dar sarmalayıcılar gerçek LoadLibrary/GetProcAddress çağırır;
43 gerçek çözüm ve IAT yazımı ayrıca denetlenir. Bunlar sahte API dönüşleri değildir.

İşçi kendi DLL girişini çağırıp EAX1 döndü. Başlangıç iki kez çağrılmadı.
Kendi fixture export'u 24 byte'ı kendi sentetik arena'sından okudu. Üretim
`FarmexObserve` export'u kendi hostumuzda WRONG_PROCESS ve sıfır okuma döndürdü.
DLL, Windows loader modül listesine kayıtlı değildi; görüntü MEM_PRIVATE idi.

Ayrı64-bit `ReadOnlyNativeMap` okuyucu, kendi host PID/nonce/ABI/source-kind
kapılarından geçip84-byte paylaşım çerçevesini kabul etti: sequence2,
HP250/500, MP100/300, native okuma24 byte, kaynak **fixture**. Okuyucu kapandıktan
sonra kendi DLL detach/temizliği çalıştı; host exit0 ve paylaşım haritasının
artık bulunmadığı doğrulandı. Gerçek oyun belleği okunmadı.

Paylaşılan C dosyasına eklenen seçenek kapalıyken eski bağımsız hazırlayıcı yolu
da ayrı hostta aynı116/43, fixture verileri ve temiz kapanışla regresyonu geçti.
Python çalışma dosyaları değişmedi; önceki3860 test ve tam1037-kontrol UI sonucu
tekrarlanmadı. İki native zincir Python test sayısına eklenmedi.

Bu test yerel DLL hazırlama/başlangıç/IPC zincirini güçlendirir. Orijinal Loader'ın
uzak süreç aktarımı, oyunun askıda başlangıcındaki haklar, güncel hash/ofsetler,
gerçek HP/MP, thread/ABI bağlamı, özellik eylemleri ve canlı uyumluluk açık kalır.
Mevcut oyun erişim engeli bu deneyle kalkmaz; oyun üzerinde okuma/yazma0'dır.
