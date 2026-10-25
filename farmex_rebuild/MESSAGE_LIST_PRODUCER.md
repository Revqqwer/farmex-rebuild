# Sıralı mesaj listesinin derlenmesi

23 Ekim 2026. `message_list_producer.py`, Richard0045c488'in post-prologue
normal yolunu captured helper/alan girdileriyle modeller. Yeni REA208-talimat
gövdeyle eşleşir. Eski/güncel iki sürümde producer208, fast-append36,
size16 ve capacity16 olmak üzere552 disk kaydı doğrulanır. Tam native
VCL/string/vector/SEH davranışı sertifikalanmış değildir.

Kaynak önce end iterator, begin iterator ve range erase yardımcılarını
sırayla çağırır. Üç ayrı normal dönüşten sonra kendi projection listesi
temizlenmiş sayılır. Bu gerçek heap'te erase etkisinin gözlendiği anlamına
gelmez. UI boşken de clear yolu vardır. Satır sayısı her tur yeniden
okunur ve signed EAX>index koşulu kullanılır; ilk sayı sabit snapshot'a
çevrilmez. Satır checkbox durumu bu üreticide ayrı filtre olarak okunmaz.

| Kayıt alanı | Kaynak UI alanı | İşlem |
|---|---|---|
| +0 kanal | Satır Caption | Captured Unicode→ANSI bytes |
| +4 mesaj | SubItem0 | Captured Unicode→ANSI bytes |
| +8 delay DWORD | SubItem1 | Typed integer(default10), low32×1000 |

Unicode getter, ANSI dönüşümü, captured bytes ve Unicode cleanup ayrı
sınırlardır. Model kod sayfasını tahmin etmez. Kendi immutable byte dizileri
NUL dahil korunur; native string eşitliği/serializer'ın NUL davranışı burada
belirlenmiş değildir. Sayı dönüşümü mevcut SourceIntegerFrame'i kullanır;
metinden parse veya catch seçimi uydurulmaz. Kaynaktaki PUSH0xa fallback10'dur,
UI'deki başlangıç bekleme değeri değildir. Negatif/büyük sayı düşükDWORD'u
alınıp32 bitte1000 ile çarpılır; yeni sınırlandırma eklenmez.

Geçici iki kayıt string'i oluşturulup atanır; ardından size ve capacity
yardımcılarının ayrı ham EAX sonuçları unsigned karşılaştırılır. size<capacity
ise taze end ve normal fast-append çağrısından sonra caller context+14'e
EAX store planı çıkar. Fast helper'ın normal kuyruğu end+12*count döndürür;
bu caller count1 verir. İsteğe bağlı EAX capture bununla çelişirse reddedilir.
Diğer dal end iterator/grow-insert normal dönüşlerini ister; caller'da yeni
bir end store'u yoktur. Growth yardımcısının iç heap/stores etkileri opaktır.

Rows çıktısı helper'a geçirilmiş kendi kayıt projection'larıdır; native
kuyruğun gerçek içeriğinin kanıtı değildir. Kayıt kabulü/store planından sonra
dört ayrı cleanup gerekir: kayıt mesajı, kayıt kanalı, ilk mesaj, ilk kanal.
Beklerken önceki kendi prefix korunur ve tekrar advance kayıtları çoğaltmaz.
Bir sonraki tur yeni UI count gözlemi gerekir. Own row_budget kaynak limiti
değildir; daha fazla satır varsa incomplete kalır ve extend_budget ile büyütülür.

12 yeni test; toplam3985 test geçti. UI değişmedi (378 bağlı/145 bağlanmamış).
Bu üretici henüz gerçek panel listesinden çalışan UI trial'ına bağlanmadı.
Captured kayıtların gerçek native adres/handle'larına yazılması, toggle,
serializer, gönderim/sunucu sonucu ve canlı oyun bağlantısı açık kalır.
