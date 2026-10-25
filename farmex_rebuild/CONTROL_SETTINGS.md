# Kontrol ayarlarının kaynak üreticisi

`control_settings.py`, `004576ec` fonksiyonunun `004581b9..004584af`
aralığını modeller: 191 talimat, 15 panel alanı ve 16 sayısal yazım.
Tam fonksiyon veya canlı oyun sertifikası değildir.

| Alan | Context ofseti | Kaynak davranışı |
|---|---|---|
| Zone değişince durdur / Town isteğinde durdur | BD / BE | Getter AL |
| NP / Coin kontrolü | BF / C0 | Getter AL |
| Coin eşiği | C8 ve CC | Parser EDX:EAX, tam 64 bit; fallback 0 |
| Seviye kontrolü / hedef seviye | D0 / D4 | AL / alt DWORD; fallback 54 |
| Saat kontrolü / saat / dakika | D8 / DC / E0 | AL / alt DWORD / alt DWORD; fallback 0 / 0 |
| Party sayısı eşiği | E4 | Alt DWORD; fallback 5 |
| Party azsa durdur / alarm | E8 / E9 | Getter AL |
| Priest yoksa durdur / alarm | EA / EB | Getter AL |

Sayı metinleri ilgili checkbox kapalı olsa da okunur ve dönüştürülür.
Kaynak parserının normal dönüşü veya catch landing yolu ayrı gözlem ister;
hatalı metinden otomatik olarak fallback sonucu çıkarılmaz. Coin dışındaki
sayılarda üst DWORD saklanmaz. Parserın dış dönüşü gelmeden yazım yapılmaz;
temizlik dönüşündeki bekleme ise kabul edilmiş yazımları geri almaz.

`ControlSettingsTrial`, bu 15 gerçek alanın kendi profil değerlerinden sabit
bir snapshot alır. Örnek doldurma açıkça sentetik signed decimal64 politikası
kullanır; kaynak RTL'nin tüm metin/locale kurallarını taklit ettiği iddia edilmez.
Bu aşamada yeni EnginePage düğmesi veya compiler girişi eklenmedi.

`replay_control_settings_consumer`, yalnız tamamlanmış ve tam yazım sırası
doğrulanmış yerel ayar planını mevcut NP/coin/seviye/saat/party kararlarına
verir. Gerçek oyun, ayar üretiminden sonra alanları yeniden değiştirebilir;
bu köprü yerel sabit snapshot denemesidir. BD/BE alanlarının sonraki çalışma
tüketicisi bu köprüde uygulanmaz. Stop, Town, alarm ve process sonlandırma
çağrıları yalnız plan olarak kalır; hiçbirini yürütmez.

12 yeni test; toplam 3834 Python testi geçti. Coin eşiğinin negatif üst DWORD'u,
pozitif üst DWORD'u, kaynak fallbackleri, öncelikli NP çıkışı, party alarmı,
bağımsız parser/dış dönüş/temizlik sınırları ve snapshot geçerliliği sınandı.
Arayüz değişmedi; bu aşamada tam UI testi tekrarlanmadı.
