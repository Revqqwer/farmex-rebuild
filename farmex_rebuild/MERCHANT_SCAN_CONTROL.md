# Tarama ayarları ve başlat/durdur

`merchant_scan_control.py`, kaynak `004b8f2c` ve `004be6dc` davranışlarının tek çağrılık, değişmez yerel durum izdüşümüdür. Gerçek native yardımcılar çalıştırılmaz; her çağrı için bağımsız normal dönüş gözlemi gerekir. Eksik gözlem, önceki tamamlanan yerel adımları geri almaz. Bu API henüz panel, tarama zamanlayıcısı veya yanıt sağlayıcısına bağlı değildir.

Ayar okuyucu önce combo indeksini işaretli DWORD olarak sıfırdan büyük olup olmamasına göre 0/1'e çevirir. SELL, BUY, kaydet ve rota getter'larında yalnız AL saklanır; bu byte'lar boolean'a normalize edilmez. Dört checkbox callback'i kapalı initialization gate altında okuyucuyu çağırmaz. Combo OnChange'in aynı okuyucuyu çağırdığı varsayılmaz.

Başlatma sırası: +78 ve +58 vektörleri, rota vektörü, rota indeksi, sonuç kayıtları ve liste temizliği; ardından başlat/durdur/tek tarama düğmeleri 0/1/0 olur. Taze SELL AL=0 ve BUY AL=1 olduğunda combo Buying yapılır ve başarılı setter dönüşünden sonra önbellek modu güncellenir. Rota kullanılacak mı kararı önbellekteki rota byte'ına bağlıdır. Başlatma +0f bekleyen-yanıt byte'ını sıfırlamaz.

Rota satır sayısı her döngüde yeniden gözlenir ve işaretli karşılaştırılır. X/Y metinleri için ayrı StrToInt ve cleanup dönüşleri gerekir. Size/capacity karşılaştırması işaretsizdir. Hızlı eklemede kopyalama dönüşü ve yeni end EAX ayrı tutulur; büyütmede end iterator yardımcısı ve ekleme ayrı dönüşlerdir. Aktif bayrağı bütün rota işlemlerinden sonra yazılır. Boş rota kendiliğinden hata sayılmaz; sonraki worker'ın sınır davranışı ayrı kapsamdadır.

Durdurma önce aktif ve bekleyen-yanıt bayraklarını sıfırlar, düğmeleri 1/0/1 yapar ve tamamlandı parametresine göre durumu yazar. Vektörleri veya rota indeksini temizlemez. Status setter sonrası cleanup eksikse yeni yerel metin korunur.

Eksik native helper dönüşünde helper'ın içindeki kısmi bellek değişiklikleri bilinmez; model bunların olmadığına dair iddia taşımaz. Yeniden giriş/resume veya kaynak SEH/lifetime eşliği sağlanmaz. Metin→sayı dönüşümünde Python parser'ı kullanılmaz; yakalanmış native EAX gerekir.

İlk bağımsız API aşamasında 16 yeni senaryo ve toplam 4288 test geçti. İki Richard sürümündeki 1130 instruction kaydı dosya byte'larıyla karşılaştırıldı; seçili dallar, iterator alanları, StrToInt importları ve durum literal'leri ayrıca sabitlendi. Sonraki yerel UI yaşam döngüsüyle birlikte toplam 4296 test ve tam GUI kontrolü geçti; API artık bu sürümün paketine dahil. Önceki 4272 paket yedeği ayrı korunur. Güncel kapsam MERCHANT_SCAN_RUNTIME_VALIDATION.json içindedir. Bu sayılar tam fonksiyon veya canlı uyumluluk sertifikası değildir.
