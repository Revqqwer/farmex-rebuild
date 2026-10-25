# Yerel oturum durum mesajı üreticisi

`session_status_wire.py`, 004f9f68 yordamının **004fa097 sonrası normal serileştirme aşamasını** kendi byte tamponunda üretir. Önceki oyun okuyucuları, mod/durum seçimi ve metin dönüştürme sonucu açık `SessionStatusPrepared` girdileridir. Üretici ağ bağlantısı açmaz ve oyun belleğine erişmez.

## Çözülen alan sırası

AA55 başlığı, kodlanmış uzunluk WORD'ü, sabit02 baytı, 5559b4 baytı, ad başlığı baytı ve serileştirilmiş ad gelir. Ardından hazırlanmış mod/durum baytları; 46209c,462670,46256c sonuçlarının AL kısmı; 64 bit tam sayı çarpma/bölme hesabından sonraki EAX sonucunun AL kısmı; 46258c DWORD sonucu; sıfır WORD; üç sıfır DWORD; 4625ac ve4625d8 DWORD sonuçları; 561f6f bayrağından üretilmiş0/1 ve55AA sonlandırıcısı yazılır. DWORD/WORD alanları little-endian'dır. Ad başlığı baytı ile gerçek metin byte sayısının eşitliği varsayılmaz.

Boş adla toplam uzunluk42 byte, N byte adla42+N'dir. Kaynak512 byte tamponu sıfırlar. Model512'yi aşan serileştirmeyi kesmez; taşma etkilerinin modellenmediğini bildirir.

Toplam yerel uzunluğun WORD kısmına çift uzunlukta0x3afc, tek uzunlukta0x1f40 eklenir ve başlığın2..3 byte konumlarına yazılır. Dönüşüm yardımcısının sayacı ayrıca global555db8 WORD'ünden okunur; model bu taze gözlemi zorunlu tutar. Yerel uzunlukla aynı olduğunu kendiliğinden varsaymaz. İki kaynak yardımcı arasında seçim ve sayaç okuması için tek, sabit gözlem desteklenir; bu okumalar arasında eşzamanlı değişiklikler henüz modellenmez.

004f94f8, yalnız4<=i<count-2 aralığındaki çift indisli baytlara0x6e, tek indislilere0x5e ekler. 004f9564 aynı aralıkta0x58/0x4a ekler. Bayt taşması korunur. Sayacın işaretli DWORD olarak negatif olduğu yardımcı çağrılarında döngü gövdesi çalışmaz. Başlık ve seçilen sayaçla belirlenen son iki bayt dönüşüme girmez; sayaç yerel uzunluktan farklıysa yerel mesaj sonlandırıcısı değişebilir.

## Kanıt ve sınırlar

`work/audit_session_status_wire.py`, iki sabit Richard görüntüsünde12 yordamın **3.630 instruction kaydını** disk baytlarıyla doğrular.10 yeni REA ve2 önceki REA çıktısı bunlarla eşleştirilir. Kurucu719, hata callback'i586 ve mesaj üreticisi339 instruction içerir. Bunların tamamının baytlarının doğrulanması, tamamının davranışının çözüldüğü anlamına gelmez.

Kurucu 004faf08'de +175c alanına17000, oradan +324 alanına port değeri; +32c alanına20000 bağlantı zaman aşımı yazılır. Metin kurma zinciri, gerçek sunucu adresi ve canlı nesne kimliği henüz doğrulanmadı. 004fab88 wrapper'ı 004fba2c hata yordamını çağırıp kaydedilmiş oyun callback'ine döner. Hata yordamında bot durdurma ve bildirim hazırlama yolları görülür; metin yardımcıları ve canlı etkiler açık kalır.

Yerel üretici, memcpy ve metin yardımcılarının normal tamamlandığı atomik bir aşamadır. Kaynak çağrılarının istisnalarını, SEH temizliğini, pointer aliasing'i, fonksiyon dönüş register'larını veya yeniden giriş davranışını kanıtlamaz. `complete=True` yalnız bu açık girdiler altındaki sınırlı byte üretiminin tamamlandığını belirtir; `full_builder_verified`, `native_execution_verified` ve `live_compatibility_verified` her zamanFalse kalır.

Yedi test; sabit çift/tek mesaj byte örneklerini, alan sırasını, düşük AL ve DWORD farkını, sarma davranışını, bağımsız global uzunluğu, tampon sınırını ve eksik giriş gözlemini denetler. Bunlar canlı ağ/protokol eşdeğerliği testi değildir. Ağ isteği ve oyun işlemi sayısı0'dır.

Tam denetim kaydı: `outputs/FarmexBot_oturum_mesaj_bicimi_kaniti.json`. Önceki soket akışı: [CALLBACK_SOCKET_ANALYSIS.md](CALLBACK_SOCKET_ANALYSIS.md).
