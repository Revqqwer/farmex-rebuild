# Item kırma çağrı sırası ve bekleme

23 Ekim 2026. `item_break_cycle.py`, Richard ana döngüsünün
`00471294..00471353` normal bölümünü (54 talimat) ve bekleme yardımcısının
`004710d7..00471131` bölümünü (29 talimat) bağımsız gözlem/plan API'sine taşır.
Giriş bayrağı bu sınırlı bölümlere ulaşıldığını belirtir; native ABI/SEH
ve gerçek yardımcılar çalıştırılmaz.

Ana döngü önce561f60, sonra yapılandırma+0 baytını kontrol eder. Ardından
561f6c baytını **iki kez** okur. İlk okuma sıfır değilse envanter/item
kontrolünü00470f6c çağırır; normal dönüşü ikinci baytın değerini kanıtlamaz.
İlk okuma0, ikinci okuma1 de geçerli bir gözlem dizisidir ve NPC yoluna gider.
İkinci okuma0 ise NPC ve bekleme çağrıları atlanır.

NPC yardımcısı00470d98 sonucunun yalnız AL baytı kullanılır. AL0 durumunda
0040ae0c(561f34,0) çağrı planından sonra ayrı bilgi metni/temizleme normal
bölümü gerekir. AL sıfır değilse tipli bekleme çocuğu ve ardından onun parent
normal dönüşü gerekir. Parent dönüş bayrağı eksik çocuğu atlatamaz.
Envanter kontrolü ve NPC yardımcısının iç davranışları bu aşamada opaktır.

Bekleme yardımcısı yapılandırma+c DWORD'u sıfır değilse diğer alanları okumaz.
Sıfırsa ilk GetTickCount normal dönüşü, EAX, zaman553d50 düşük DWORD'u,
553d54 yüksek DWORD'u ve taze hız+4 değerini sırasıyla tüketir:

```
elapsed = signed64(zero_extend(tick) - stored_qword)
threshold = signed32(low32(speed * 1000))
due = elapsed >= threshold
```

Karşılaştırma eşitliğinde işlem yolu açıktır. Zaman sayacı DWORD taşması
burada otomatik pozitif fark haline getirilmez. Hız çarpımı32 bitte taşar;
0xffffffff hız değeri için threshold−1000, 0x80000000 için0 olur. Bunlar
kaynak aritmetiğinin sonuçlarıdır; yeni bir hız doğrulama politikası değildir.

Süre dolunca004ca9b0(561ef8) normal dönüşü istenir. Daha sonra ikinci
GetTickCount ayrıca okunur ve yalnız bu dönüşten sonra553d50=ikinci_tick,
553d54=0 store planı çıkar. İlk tick ikinci tick yerine kullanılamaz.
Action yardımcısının normal dönüşü sunucu başarısı değildir: kaynak yardımcı
seçili NPC0 olduğunda erken dönebilir; çağıran yine zamanı günceller.

Çerçeveler yalnız ulaşılan verileri saklar. Bekleyen action/NPC/notice
dönüşünden sonra önceki kapılar ve zaman hesabı yeni örnekle değişmez.
Çağrı/store sonuçları kendi yerel planlarıdır; oyuna uygulanmaz.

İki Richard sürümünde ana64, clock33, action50 ve GetTickCount thunk1
kaydı ile ana dağıtıcıdaki5-talimatlık mode5/context569a20 çağrı bölümü
disk baytlarıyla doğrulanır: toplam306 kayıt. İki yeni REA analizi ana ve
clock gövdeleriyle eşleşir. Action gövdesinin bayt doğrulaması onun yeniden
uygulandığı veya sunucu sonuçlarının çözüldüğü anlamına gelmez.

Bu aşamada panel değişmez. Önceki ayar üreticisi bağımsız taze okumalara
otomatik bağlanmaz. NPC uzaklık/nesne seçimi, envanter kontrolünün içi,
diğer kırma modları, istek serileştirme, native çalıştırma ve gerçek oyun
uyumluluğu açık iş olarak kalır.
