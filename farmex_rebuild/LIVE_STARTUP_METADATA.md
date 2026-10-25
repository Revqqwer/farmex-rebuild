# 23 Ekim başlangıç testi

Kullanıcının tek seferlik onayıyla yeni PID16468, sabit hash'li
KnightOnLine.exe'den CREATE_SUSPENDED ile oluşturuldu. Yönetici gözlemci,
devam ettirmeden önce ve yaklaşık1 saniye sonra istenen1fffff/10 handle
haklarını metadata olarak kaydetti. ResumeThread önceki askı sayısı1 döndürdü.

Ancak oyun **“Please execute Knight Online via the Launcher!-(NullParam)”**
uyarısı verdi. Sürecin devam ettirilmesi geçerli oyun oturumuna ulaşmak
anlamına gelmedi. Bu hak sonuçları korumalı oyun oturumunda okunabilir bellek,
geçerli adresler, HP/MP veya çalışan bot bağlantısı kanıtı değildir.

Aynı PID'nin daha sonraki normal-host sorgusunda VM_READ isteği hata5 verdi;
gözlemci yetkisi değiştiğinden yalnız zamanlamaya dayalı bir neden çıkarılmadı.
Kullanıcı isteğiyle normal Launcher ayrıca açıldı. Kullanıcının sunucuya giriş
bildiriminden sonraki metadata kontrolünde PID6524 ve dosya kimliği eşleşti;
normal-host VM_READ yine hata5 verdi. Güncel hash için kayıtlı/doğrulanmış
adres profili yoktur. Bu oturum için yeni yönetici veya bellek testi yapılmadı.

Bütün bu adımlarda oyun belleği okuma/yazma0, DLL işlemi0, uzak thread0,
oyun girdisi0. Başlangıç claim'i tüketildi ve korundu; test tekrarlanmadı.

Ham kanıtlar üst outputs klasöründedir:

- FarmexBot_baslangic_haklari_20261023_052614_023805.json
- FarmexBot_canli_metadata_20261023_052644_072491.json
- FarmexBot_canli_metadata_20261023_053043_276110.json
- FarmexBot_baslangic_metadata_sonuc_kaniti.json

Doğrulayıcı work/audit_early_game_metadata_result.py başlangıç kontrol
noktasını orijinal Loader'ın144 assembly kaydıyla tekrar karşılaştırır.
CreateProcessA/flags4 kaynakta kanıtlıdır; deneyin CreateProcessW/sabit komut
satırı orijinal dinamik parametrelerin eşdeğeri sayılmaz.
