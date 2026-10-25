# Merchant item metadata üretici bağı

`merchant_item_metadata.py`, yeni lookup planlarını mevcut `item_name.py` captured-byte modeliyle birleştirir. Sonuç `MerchantItemMetadata` girdisine, oradan ham yanıt/record/filtre/sütun zincirine gider. Aynı isim yardımcısı yeniden uygulanmadı.

Ulaşılan aşamalar: temel lookup planı ve normal dönüş/EAX; base+4 resolver gözlemi; extension lookup planı ve normal dönüş/EAX; extension+0x4c ad kategorisi; extension DWORD ID; mevcut isim helper modeli; açık yerel byte→Unicode decoder; taze extension+0x4c record kategorisi. Son normalize isim byte'ları hâlâ ayrı opsiyonel girdidir; arama gerektirirse mevcut filtre modeli bunları ister.

İsim yardımcısı ayrıca extension+0x44 kategorisini okur. Bu değer ad son ekini seçen +0x4c veya daha sonraki record kategorisiyle eşitlenmez. Önceden sağlanan lookup/extension pointer'ları sıfır değilse isim yardımcısına doğrudan bağlanır. Sıfırsa mevcut isim modeli kendi taze lookup yolunu korur; önceki sonuç veya isim alanı uydurulmaz.

Captured ANSI byte sonucu henüz yoksa boş isim sayılmaz. Byte sonucu hazır ama yerel decoder yoksa veya dönüşüm başarısızsa metadata tamamlanmaz; byte öneki kaybolmaz. Decoder açıkça kullanıcının/kendi uygulamamızın yerel dönüşüm politikasıdır. Mevcut `WindowsNameCodec` somut kod sayfasıyla kullanılabilir; oyun runtime'ının aynı kod sayfasını/RTL politikasını kullandığı kanıtlanmış değildir.

`project_merchant_scan_with_lookups` her dolu slotun gerçek raw item ID'sini bu üreticiye verir. Bilinmeyen actor durumunda item üreticileri tüketilmez. Bir sonraki item gözlemi eksikse önceki tamamlanan record öneki korunur. Kaynaktaki interleaved native event sırası, native helper dönüş makbuzları, otomatik resume veya GUI işlemi bu sabit değer zinciriyle kanıtlanmaz. Tekrar oynatmayı idempotent yapan gizli bir mekanizma yoktur.

9 yeni test, toplam 4159 test geçti (`work/merchant_item_metadata_full_tests.log`). Ham yanıt→lookup planları→isim bytes→yerel decode→kategori/son ek→filtre→sütun zinciri ve eksik aşamalar sınandı. İki Richard sürümünde 4898 talimat kaydı ve caller/helper operandları doğrulandı (`FarmexBot_merchant_item_metadata_bagi_kaniti.json`). Yeni başarılı REA analizi yok; mevcut Ghidra ihracatı kullanıldı.

Bu, native lookup'un gerçekten çalıştığı anlamına gelmez. Çağrı dönüşleri, runtime global/table değerleri, actor metadata, gerçek kod sayfası ve normalize metin üretimi, native istisna/lifetime, gerçek panel/sıralama/hücre eylemleri ve dispatcher parse/finish dönüşleri açıktır. Dağıtım ZIP'i değiştirilmedi.
