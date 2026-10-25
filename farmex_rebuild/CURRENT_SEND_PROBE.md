# Güncel oyun gönderim adayının sınırlı disk incelemesi

20 Ekim 2026. Gerçek bağlantı boşluğu yeniden kontrol edildi: `ReadOnlyGameProvider.submit()` hâlâ `unavailable` döndürür; `native_sender.py` yalnız operand planıdır. Önceki modeller ve testler gerçek gönderim adaptörü oluşturmaz.

17:24:44 UTC host süreç metadata sorgusu275 süreçte Knight/Farmex/Loader adıyla eşleşme bulmadı. Sonuç yalnız o an ve isim kapsamı içindir. 17:27:05 UTC kurulu `C:\NTTGame\KnightOnlineEn\KnightOnLine.exe` dosyasının7008392 bayt ve SHA256 `ca69cecebdefd82b409ca8cf041655da53cb97113b068a086c5f7a6ef7e952a9` olduğu görüldü; korunmuş güncel kopyayla aynı. Bu, yüklü bir runtime'ın kimliğini veya adreslerin doğruluğunu kanıtlamaz.

REA MCP araçları bu oturumda listelenmedi. Mevcut Ghidra12.1.4 ve JDK21 ile **ayrı yeni statik proje** oluşturuldu; genel auto-analysis kapalı tutuldu. İlk başlatma varsayılan AppData profil dizinine yazamadığı için durdu. Java/profil yolları yalnız komut ortamında mevcut çalışma alanına yönlendirilince import ve post-script tamamlandı. Orijinal oyun çalıştırılmadı, eski analiz projesi değiştirilmedi. Çıktı yeni REA Evidence değil, ayrı Ghidra/PE kanıtıdır.

| Aday | Kapsam | Çözülen doğrusal kayıt / bayt | Durma nedeni |
|---|---|---|---|
| 0070b360 | Güncel US initializer literal'i | 24 / 67 | Talimat sınırı |
| 006241a0 | Steam literal'inin aynı US diskindeki geometrisi | 14 / 40 | Terminal doğrusal talimat |

US penceresinde `0070b367` adresinde ESP'yi bellek operandıyla AND eden komut, `0070b391` adresinde EAX/ESP değişimi ve `0070b396` adresinde görüntü dışında `0f2471b8` operandına far-call çözümü bulunur. Toplam38 kayıt bağımsız PE dosya eşlemesiyle bayt bayt doğrulandı. Dallar takip edilmedi; bunların runtime'da yürüdüğü veya tek bir gerçek fonksiyona ait olduğu kanıtlanmadı. Steam dosyası analiz edilmedi.

Kaynak wrapper'ın beklediği8 bayt callee stack temizliği bu incelemeyle doğrulanmadı. Disk çözümünün olağandışı görünmesi packing, encryption, yanlış profil veya farklı runtime byte'ları için tek başına neden kanıtı değildir. Eski7032e0 adayındaki tarihsel bad-instruction sonucu yeni70b360 adresine aktarılmadı; yeni aday ayrıca incelendi.

Canlı bağlantı için açık kalanlar: runtime slot/context/target değerleri ve byte'ları; gerçek giriş ve stack convention; önceki VM_READ hakkı reddinin nedeni; gerçek oyun/sunucu sonucu. 18 Ekim yönetici tek-seferlik HP/MP testinde handle hakları0 ve okunan byte0'dı. Bu tur yeniden yönetici testi veya başka yükleme yapılmadı.

Kaynaklar: `outputs/Ghidra_guncel_oyun_gonderim_probe.json`, `outputs/FarmexBot_guncel_gonderim_probe_degerlendirmesi.json`, `outputs/FarmexBot_canli_onkontrol_20261020_1724.json`. Üreticiler `work/ghidra_scripts/ProbeCurrentSendTarget.java` ve `work/assess_current_send_probe.py`; başlatma log'u `work/current_send_probe_headless.log`.

Runtime Python/UI/native C değiştirilmedi; yeni birim testi veya tam test koşusu yapılmadı. Son tam koşu2916 testtir; bu incelemenin ABI/canlı doğrulaması değildir. Statik inceleme ve kimlik sonuçları `CURRENT_SEND_PROBE_VALIDATION.json` dosyasında tutulur.
