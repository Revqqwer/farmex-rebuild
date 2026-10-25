# Satış açılışını bekleme: aşama 5

18 Ekim 2026: `merchant_sell_open_wait.py`, `00421c2c..00421eb3`
aralığındaki caller sırasını verilen gözlemler üzerinde modeller.
`work/audit_sell_open_wait.py` iki sürümde toplam 318 talimat kaydının
baytlarını ve çağrı/import kimliklerini doğruladı. Rapor:
`outputs/FarmexBot_satis_acilis_bekleme_kod_kaniti.json`.
Bu Ghidra tabanlı statik doğrulamadır; REA Evidence veya native yürütme değildir.
Diğer auditlerle örtüşen talimatlar benzersiz toplam olarak toplanmaz.

Pending BYTE sıfır değilse açık DWORD tick gerekir. Tick sıfır genişletilir;
QWORD açılış damgasından çıkarılan fark signed64 olarak 10000 ile karşılaştırılır.
DWORD saat sarması unsigned32 elapsed hesabına dönüştürülmez; negatif fark bekler.
Timeout dalı ayrı stop-helper ve mesaj/cleanup normal dönüşlerini gerektirir.
Model bu yardımcıların iç etkilerini uygulamaz. Runner'ın `open_timeout`
ile durması kendi politikasıdır.

Pending sıfırsa saat okunmaz. Setup gate +58 yalnız nonzero ise temizlenir;
status BYTE +90 her zaman temizlenir. Ardından dört bağımsız normal dönüş gerekir:

1. `00421d11..00421d5d`: durum metni hazırlama.
2. `00421d60..00421dbc`: durum gösterimi.
3. `00421dbf..00421e33`: birikmiş QWORD +98, selector 3.
4. `00421e36..00421eaa`: net QWORD +a0, selector 5.

Son iki değer yalnız ilgili aşamaya erişilince istenir. Kaynaktaki high DWORD
önce, low DWORD sonra okuma sırası kaydedilir. Display planı ham QWORD ve selector
içerir; gerçek biçimlenmiş metin veya VCL çağrısı üretildiği iddia edilmez.
Dört dönüş tamamlanınca phase +4 alanı 6 olur. Önceki yazılar eksik gözlemde
prospective state içindedir; accepted state tamamlanmadan ilerlemez.

Bir frame bir caller invocation'ıdır. Normal bekleme sonucu tamamlanmıştır;
sonraki tick veya değişmiş pending için yeni frame oluşturulur. Bilinen örnekler
aynı frame'de değiştirilemez; tamamlanan span ve okumalar tekrarlanmaz.

`MerchantSnapshot.sell_open_wait_execution` bağı, pending ve açılış damgasının
runner ile eşleşmesini ister; eksik span eski ready bayrağıyla atlanamaz.
Sonraki aşama için runner'ın kendi zaman kaydı, o aşamanın source-clock eşdeğerliği
anlamına gelmez. Workbench bu yeni gözlemler için kontrol sunmaz; API kapsamıdır.

14 yeni test dahil tam Python çalıştırmasında **1893 test geçti** (7.176 saniye).
Birleşik model profil/liste/maliyet/session/slot/opening/verilen yanıt zincirinden,
dört açık span dönüşü ve taze 100/97 toplamlarıyla aşama 6 sınırına ilerler.
Bu yanıtlar ve dönüşler test girdileridir; yakalanmış sunucu ACK'sı değildir.
Sonraki [SELL_MONITOR.md](SELL_MONITOR.md) çalışması aşama 6'nın yerel izleme
ve yeniden açma kararını ekler. Native UI/stop/heap etkileri ve canlı uyumluluk doğrulanmadı.
Bu çalışma oyun belleği okumaz/yazmaz, oyun çağrısı veya paket gönderimi yapmaz.
