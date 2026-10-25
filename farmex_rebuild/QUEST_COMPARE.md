# Görev sıralaması ve karşılaştırma kapsamı

Kaynak `LwZoneQuestsCompare` (`004b4940`), ilk satırın
`SubItems.Strings[0]` metnini alıp `StrToInt` çağırır; ardından aynı işlemi
ikinci satır için yapar. Sonuç alanına ilk DWORD'dan ikinci DWORD'un farkını
yazar. Görev adı ve başlık bu karşılaştırmaya girmez. Satır üretimindeki
ilk alt alan minimum seviyedir.

`QuestCompareFrame` bu sıra ile normal dönüşleri ayrı izler. Sonuç yazımı
ikinci ve ilk Unicode temizlemelerinden önce gerçekleşir. Temizleme veya
epilog eksikse yazılmış sonuç korunur; callback tamamlanmış sayılmaz.
Ham DWORD farkı işaret veya -1/0/1 değerine indirgenmez. Açık seçimle
`rtl_integer32` modeli kullanılabilir; hatalı sayı native istisna yolu
çözülmemiş olarak kalır, sıfır sonucuna çevrilmez.

İki Richard sürümünün PE importları son çağrıyı VCL
`TCustomListView.AlphaSort`, sayısal dönüşümü RTL `StrToInt` olarak doğrular.
`plan_quest_alpha_sort`, daha önce saklanan VCL kanıtındaki ortak
HandleAllocated/GetHandle/SendMessageW akışını yeniden kullanır.
Gerçek pencereye mesaj göndermez. BOOL dönüşü gerçek sıralama kanıtı değildir.

Bağımsız sürüm için `sort_quest_rows_owned` kullanılabilir. Üreticinin
0..255 minimum-seviye alanında sayısal artan sıraya koyar; eşit seviyelerde
giriş sırasını korumak **kendi sürümümüzün açık politikasıdır**. Native
eşitlik sırası doğrulanmamıştır. Bu alan dışında taşmalı DWORD farkı Python
sayı sırasıyla değiştirilmez; işlem eksik sonuç verir. Girdiler değiştirilmez.

Bu kod henüz Yenile olayına bağlı değildir ve `QuestListFrame`'in
`sort_pending` sonucunu native tamamlanma sertifikasına dönüştürmez.
Yenile başlangıcı, tam tarama orkestrasyonu, son temizlemeler ve UI bağlantısı
hâlâ tamamlanmalıdır. Yeni GUI/native/oyun çalışması yapılmadı.

Kanıtlar proje kökünde `outputs/FarmexBot_gorev_karsilastirma_kaniti.json` ve
`outputs/FarmexBot_gorev_karsilastirma_test_sonucu.json` dosyalarındadır.
İki PE sürümünde toplam 1632 instruction kaydı karşılaştırıldı; bu sayı
yeniden kontrol edilen Yenile gövdesini de içerir, yeni çözülen fonksiyon
sayısı değildir.
