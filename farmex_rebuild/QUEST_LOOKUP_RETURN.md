# Görev arama yardımcısının normal dönüşü

Yeni kanıt: `FarmexBot_gorev_arama_donus_kaniti.json`. İki sabitlenmiş Richard
PE'sinde toplam 464 instruction kaydı gerçek disk byte'larıyla eşleşti.
Capstone ile komut sınırları bağımsız kontrol edildi; doğrudan normal akış
grafiğinde dönüşü zorunlu geçen komutlar hesaplandı. Orijinal kod çalıştırılmadı.

`004d642c` için mevcut iki disk görüntüsünde tek normal RET vardır. Tüm bu
RET yolları `004d6642 OR EAX,FFFFFFFF`, `004d6645 PUSH EAX` ve argument string
cleanup'ından sonraki `004d6658 POP EAX` üzerinden geçer. Geleneksel helper
çağrı/dönüş ve stack ABI'si korunduğunda normal dönüş değeri **FFFFFFFF**'tir.
Candidate indeksinin başarılı dönüşe atandığı bir dal bulunmaz.

`004d6618` üzerindeki son mode karşılaştırmasını bir başarı/başarısızlık
dallanması izlemez: sonraki SUB flags'i değiştirir. Eşleşme olsa da tarama
devam eder. İlk aralık karşılaştırması JG, sonraki karşılaştırma JLE'dir;
signed kapsayıcı sınırlar kullanılır. Üst sınır INT32_MAX ise DWORD sayaç
sarması normal sayaç çıkışı sağlamaz; koşulsuz sonlanma varsayılamaz.

Al ve Ver caller'ları dönüşün düşük WORD'ünü ilk altı byte isteğinin offset2
konumuna kopyalar. Yukarıdaki normal dönüş şartlarıyla bu alan **FFFF** olur.
Bu, gönderimin gerçekleştiğini veya sunucunun bu isteği kabul ettiğini göstermez.

## Mevcut kod ve sonraki iş

`quest_action.py` hâlâ lookup normal dönüşünü açık gözlem olarak ister.
Mevcut 12345678 vb. test girişleri dış gözlem aktarımını sınayan sentetik
fixture'lardır; bu iki disk görüntüsünün normal helper sonucuna kanıt değildir.
Native lookup sonucunun opak olduğu önceki not, artık normal dönüş açısından
bu kanıtla daraltılmıştır. İç helper etkileri ve tamamlanma gözlemleri hâlâ açıktır.

Sonucu sabit atayıp taramayı atlamak doğru değildir: metadata/string/read,
fresh faction/class okumaları, cleanup ve istisna etkileri ayrıca sürdürülmelidir.
Sonraki üretici bu sıra ve bitiş koşulları tamamlanmadan caller'a dönüş
uydurmamalıdır. Runtime patch/hook, farklı dosya sürümü, abnormal çıkış,
stack bozulması ve canlı oyun davranışı bu kanıtın kapsamında değildir.

Yeniden üretim: özgün yerel analiz çalışma alanında
`python work/audit_quest_lookup_return.py`. Bu çalışma alanındaki sabitlenmiş
iki PE ve retained assembly dökümleri gerekir; bu orijinal dosyalar GitHub
kaynak snapshot'ına dahil edilmez.
