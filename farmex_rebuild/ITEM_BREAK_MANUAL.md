# Manuel item kırma ve diğer modların kapsamı

23 Ekim 2026. `item_break_manual.py`, Button5Click004b38a4 ve manuel
00471134 normal yolunu mevcut NPC/istek çocuklarıyla modeller. Yeni REA
analizleri105-talimat manuel gövde ve14-talimat Gem callback'iyle eşleşir.
Eski/güncel ikililerde manuel105, button12, producer65 ve altı callback84
olmak üzere532 disk kaydı doğrulanır.

Manuel düğme context569a20 ile00471134 çağırır; callback'te561f55 gate'i
yoktur. Yerel ClickFrame yine açık callback-entry ve handler normal dönüşü
ister. Gerçek bir VCL tıklaması veya native handler yürütülmez.

Manuel yordam önce tipli NPC çocuğunu ve ayrı parent normal dönüşünü
tüketir. NPC AL0 ise yalnız “NPC Yakininda Olmalisiniz !” notice/temizleme
bölümüne gider. Bu yolda bot stop çağrısı yoktur. NPC başarılıysa taze+c
mode DWORD'u okunur; NPC çocuğunun önceki mode gözleminden türetilmez.
Sıfır olmayan modlar başka manuel işlem yapmadan normal sona gider.

Mode0 için Abyss Gem string/lookup/AL sonucu ve geçici temizliği ayrı
gözlemlerdir. AL0 ise “Cantanizda Abbys Gem Yok !” notice/temizleme bölümü
gerekir. Yine bot stop yoktur. AL sıfır değilse mevcut tipli istek çocuğu
ve004ca9b0 parent normal dönüşü gerekir. Başarılı kendi kuyruk modeli normalde
hedef hazırlığı ve iki kırma kaydı üretir; her enqueue gate'i bağımsızdır.

Bu manuel çağıran otomatik çalışma baytlarını, otomatik enable kutusunu,
envanter doluluğunu veya hız/cooldown yordamını okumaz. Clock zaman store'u
da yoktur. İç enqueue çocuklarının tick gözlemleri ayrı kalır; “manuelde
hiç tick kullanılmaz” sonucu çıkarılmadı. Eksik çocuk/normal dönüşü önden
verilen sonraki alanlarla atlatılamaz; yerel kuyruk tekrar çağrıda çoğalmaz.

Gem/Box/Narki tasarım seçicilerinde Enabled=false var. Dört radio callback'i
de561f55 açıksa aynı470cc4 üreticisini çağırır. Üretici yalnız rdAbbys AL
sonucunu kontrol eder ve seçiliyse mode+c DWORD'unu0 yapar. Diğer radio
adları için1/2/3 eşlemesi bu üreticide bulunmaz; seçili değilse önceki+c
değerine yeni store yoktur. Model diğer modları Abyss olarak uygulamaz.

Üç diğer radio ve beş gelişmiş checkbox için ilgili published-field
kayıtları iki ikilide de doğrulanır. Keşfedilmiş assembly envanterinde bu
sekiz offsetin açık alan displacement başvuruları taranır; sonuç ayrı kapsam
raporundadır. Her sürümdeki altı sayısal literal eşleşmesi ayrıca korunur:
bunlar EBP'ye göre stack word store'larıdır, form alanı erişimi değildir.
Beş checkbox tasarımda GroupBox20 yüksekliğinin altında kalan
Top değerlerine sahiptir ve event tanımları yoktur. Bunlar tasarım/sınırlı
statik bulgulardır: runtime property değişiklikleri, RTTI/dolaylı alan erişimi,
keşfedilmemiş kod ve gerçek oturum davranışı dışlanmış değildir.

12 yeni test; toplam3941 test geçti. UI375 bağlı/148 bağlanmamış olarak
değişmedi. Gerçek lookup/select/string/notice/queue etkileri, diğer modların
tam çalışma yolu, gönderim/sunucu sonucu ve canlı oyun bağlantısı açık kalır.
