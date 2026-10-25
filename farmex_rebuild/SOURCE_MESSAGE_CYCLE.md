# Sıralı mesaj döngüsü: kaynak operand modeli

23 Ekim 2026. `source_message_cycle.py`, Richard0045cce8 normal karar/operand
akışını ve0046f1b8'in yalnız46f1bb..46f1cf kapı bölümünü modeller. Herhangi
bir mesaj göndermez, oyun belleği okumaz ve ağ veya kuyruk gönderimi yapmaz.
0045c1f8 kanal/metin yardımcısı yalnız opak normal dönüş sınırıdır.

İlk liste sayısı için context+10 begin önce sıfır testiyle okunur. Sıfır
değilse +14 end ve **yeniden** +10 begin okunur.32 bit çıkarma sonucu
signed32 olarak12'ye bölünür; bölüm sıfıra doğru kesilir. Sıfır bölüm hemen
çıkış yapar. Negatif, sıfır olmayan bölüm de kaynak TEST/JZ kapısını geçer;
model buna kendi güvenli kapasite/list-validity kuralını eklemez.

İlk GetTickCount, +28 düşük damga ve +2c yüksek damga ayrı girdilerdir.
Elapsed signed64(zero_extend(tick)-storedQWORD) olur. Bekleme için indeks+24
ve begin+10 taze okunur; delay DWORD'u begin+12*index+8 adresindendir.
Kaynak delay'i signed32 genişletir. Eşitlikte helper yolu açıktır; DWORD
sayaç taşması otomatik pozitif elapsed farkına dönüştürülmez.

Helper çağrısı için iki satır alanı ayrı indeks/begin okumalarıyla alınır.
Fiziksel PUSH sırası field4, field0, context'tir. Bu alanları sırf çağıran
koddan kesin kanal/metin içeriği olarak etiketlemiyoruz; managed-string ve
kanal eşlemesi yardımcının ayrı işidir. Ham adresler hesaplanır ama bu model
tarafından dereference edilmez. Kaynakta önceden bounds/modulo kontrolü yoktur.

Helper normal döndükten sonra ayrı ikinci GetTickCount gerekir. Önce damga
low=tick/high=0 store planı, sonra **taze** index INC okuması/store'u çıkar.
Tail'da liste sayısı tekrar begin-test/end/subtract-begin okumalarıyla hesaplanır
ve bir kez daha taze index ile karşılaştırılır. Yalnız exact32-bit eşitliğinde
index0 store'u vardır; >= veya modulo yoktur. Bekleme dalında bile tail
karşılaştırması yapılır. İlk/tail sayısı veya aradaki indeksler aynı varsayılmaz.

Çerçeve yalnız ulaşılan operand/dönüşleri saklar. Bekleyen helper/clock
dönüşünden sonra önceki zaman/row argümanları yeni örnekle değişmez. Yerel
store planı gerçek bellek yazımı değildir. Signed count, wrapped adres,
negatif delay veya bozuk indeksin native güvenilirliği sertifikalanmaz.

Bounded callback context569910'un+20 alanına denk gelen569930 baytını okur.
Sıfırsa çocuk atlanır; diğer baytlarda tamamlanmış tipli döngü çocuğundan
sonra ayrıca parent normal dönüşü gerekir. Callback'in kalan gövdesi ve
çalışma zamanındaki zamanlayıcı/merchant mod ilişkisi bu kapsam dışındadır.

Eski/güncel iki ikilide84+5+1 kayıt doğrulanır: toplam180 disk kaydı.
Mevcut REA84-talimat gövdeyle eşleşir.12 yeni test; toplam3962 test geçti.
UI değişmedi;378 bağlı/145 bağlanmamış girdi kaldı. Liste derleyicisi,
başlat/durdur UI davranışı, kanal helper'ı, gerçek gönderim ve canlı uyumluluk
açık kalır. Önceki genel MessageSequence denemesi bu kaynak modelin yerine geçmez.
