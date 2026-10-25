# Merchant Tarama — sonuç sütunları

`merchant_result_rows.py`, değişmez yerel kayıtları mevcut filtre modelinden geçirip kaynak `004b9294` sırasıyla satıra çevirir. Caption satıcıdır; subitems sırası item adı, adet, fiyat, `PM`, `GİT`, X ve Y'dir. Son iki sütun tasarımda gizlidir. Kaynak PM/GİT hücrelerinin metin olarak eklenmesi, tıklama eylemlerinin uygulandığı anlamına gelmez.

Miktar kaynağı filtre planındaki +0x20/+0x24 seçimidir. `0041da08` yardımcısının UTF16 `%lu` biçimi işaretsiz DWORD kullanır. X/Y, `00407360` yardımcısında `%i` ile işaretli 32 bit sayıya dönüşür. Böylece 0xffffffff adet için `4294967295`, koordinat için `-1` olur.

Fiyat +0x14 alanından sıfır genişletilmiş DWORD olarak `0046063c` yardımcısına verilir. Bu normal sayısal yolda decimal metin sağdan üçlü noktalı gruplara ayrılır: `1000` → `1.000`, `4294967295` → `4.294.967.295`. Yerel formatlayıcı bu girdi alanını uygular; genel signed64 metin, native helper istisnası veya managed lifetime eşliği iddia etmez.

Filtre eksik gözlemde durursa tamamlanan satır öneki korunur. Normal bitişte bile sonuç `rows_prepared_sort_pending` olarak kalır: native AlphaSort yerine Python sıralaması eklenmedi. Yerel display metinleri açık Unicode girdileridir; orijinal ANSI→Unicode dönüşümü ve heap davranışı bununla doğrulanmaz.

7 yeni test dahil toplam 4107 test geçti (`work/merchant_result_rows_full_tests.log`). İki Richard sürümünde append/fiyat/adet/koordinat/validasyon yardımcılarının 1978 talimat kaydı baytlarla doğrulandı; format literal ve import kimlikleri ayrıca denetlendi. Rapor: `FarmexBot_merchant_sonuc_sutun_kaniti.json`. Bu aşamada yeni başarılı REA analizi yok; mevcut Ghidra çıktısı kullanıldı. Panel kodu bu aşamada değiştirilmedi.

Sıradaki kaynaklar bulundu: `LwMerchantScanCompare` callback'i `004b94d4` yardımcısına gider. Sütun 0 `CompareText`, sütun 1 `AnsiCompareText` kullanır. Sütun 2 `StrToInt` sonuçlarını DWORD çıkarma ile, sütun 3 ise `00460fa4` fiyat metni ayrıştırıcısının EAX sonuçlarını çıkararak karşılaştırır. Bu işlem normal matematiksel karşılaştırma değildir; taşma ve parse hataları çözülmeden native sıralama eşliği varsayılmamalıdır. Fiyat ayrıştırıcısının 169 talimatlık gövdesi ve compare yardımcısının 243 talimatlık gövdesi sonraki incelemenin hedefidir.

Gerçek sonuç listesi panel bağı, native sıralama, hücre tıklama davranışları ve kaynak olay/heap hata yolları tamamlanmadı. Son doğrulanmış dağıtım paketi korunmuştur; bu API değişiklikleri henüz yeni bir doğrulanmış GUI paketi oluşturmaz.
