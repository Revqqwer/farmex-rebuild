# Merchant Tarama — yerel sonuç filtresi

`merchant_result_filter.py`, kaynak `004bad1c` içindeki filtre kararlarının değişmez yerel kayıtlar üzerindeki normal değer modelidir. Gerçek tarama, arayüz liste yenilemesi veya native olay yürütümü değildir. Mevcut `merchant_scan.py` ve `merchant_scan_collection.py` modellerinin sonuçlarını otomatik olarak tamamlanmış bir tabloya dönüştürdüğü iddia edilmez.

Satış/alış seçiminde başlangıç değeri sıfırdır; yalnız tam `Buying Merchant` metni bir değerini seçer. Kategori tam metin karşılaştırmalarında Magic=1, Rare=2, Craft=3, Unique=4, Upgrade=5, Rebirth=11 ve Rebirth Unique=12 kullanılır. Eşleşmeyen metin, `Tümü` dahil, kaynak -1 filtresini korur. Bu davranış seçim sıra numaralarıyla değiştirilmedi.

Kayıt yönü +0x0c, kategori +0x1c alanından gelir. Arama, eşleşen kayıtta **font rengi** sıfırken ve signed 32-bit Unicode uzunluğu pozitifken uygulanır. Önceki “font style” adı, pinned VCL SetColor/GetStyle alan kanıtıyla düzeltildi; ayrıntı MERCHANT_SEARCH_FIELD.md dosyasındadır. İkinci metin okumasının dönüştürülmüş byte dizisi ayrı girdidir; ilk uzunluk pozitifken ikinci dizinin boş olması mümkündür. Kaynak CString hazırlığı sebebiyle ilk NUL sonrasını aramaya dahil etmeyiz. Byte araması case-sensitive'dir; uppercase/locale/kod sayfası dönüşümü model tarafından tahmin edilmez. Kaynakta arama metni Unicode `AnsiUpperCase`, kayıt adı ise ANSI `AnsiUpperCase` zincirinden gelir; eşdeğer yerel dönüşüm henüz doğrulanmadı.

Kategori sıfır ve unsigned +0x24 değeri birden büyükse miktar +0x24'ten, diğer durumlarda +0x20'den seçilir. Bu, para veya metin formatlama yardımcısının çözülmüş olduğu anlamına gelmez. Normal bitişte kaynak context+0x10 değerini 3 yapıp AlphaSort çağırır. Yerel plan yalnız bu istekleri bildirir; Python sıralamasını native sıralama yerine kullanmaz.

Eksik arama girdisi tamamlanmış kayıt önekini korur ve eksik aşamayı bildirir; final sıralama isteği üretmez. API'ye verilen kayıt ve kontrol görüntüleri sabittir. Kaynaktaki taze okumalar, vector değişimi, helper istisnaları ve managed lifetime kapsam dışıdır. Üç OnChange callback'inin 0x561f55 başlangıç kapısı bu API'nin dışında kalır.

Doğrulama: 9 yeni test, toplam 4100 test geçti (`work/merchant_result_filter_full_tests.log`). İki Richard sürümünde 3274 talimat kaydı, kategori literalleri/kodları, gate/amount/find karşılaştırmaları ve Clear/AlphaSort importları diskten doğrulandı (`FarmexBot_merchant_filtre_giris_kaniti.json`). Tam talimat bayt kapsamı, tam davranış çözümü değildir. Bu aşamada yeni başarılı REA analizi yoktur; mevcut Ghidra ihracatı kullanılmıştır.

Bu belgedeki4100-test aşamasından sonra sütun/fiyat modelleri, sonlu native comparator/sıra karşılaştırması ve gerçek yerel sonuç tablosu bağı eklendi. Güncel kapsam MERCHANT_WINDOWS_SORT.md ve MERCHANT_SEARCH_FIELD.md içindedir. Native arama dönüşümü, tam hata/eşzamanlılık yolları, PM/GİT, tarama runtime'ı ve canlı eşlik açık kalır.
