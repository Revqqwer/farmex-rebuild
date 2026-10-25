# Seçim wrapper'ları için izole x86 yürütüm

`native/relog_selection_fixture.c`, dört kaynak wrapper'ın302byte gövdesini
kendi x86 sürecinde çalıştırır. Gövdeler iki sabitlenmiş sürümde aynıdır;
102talimat*2=204byte kaydı doğrulanır.302byte içindeki26operand relocation'ı
yalnız fixture'ın kendi global slotlarına ve kendi reader fonksiyonuna yönelir.
Diğer instruction byte'ları korunur. Tüm mutlak memory operandları bilinen
fixture slot listesiyle sınırlıdır. Kod sayfaları RW hazırlanır, RX olarak mühürlenir.

Target PID, yabancı handle, oyun/DLL modülü veya kullanıcı girdisi kabul edilmez.
Header'daki özgün adresler çalıştırılmadan önce bütünüyle fixture adreslerine
taşınır. Kendi reader'ı yalnız fixture dizileri/root değişkenini kabul eder;
45dc44'ün gerçek VirtualProtect/bellek davranışı çalıştırılmaz. Doğrudan pointer
zincirleri de yalnız kendi dizilerimize gider. Receiver'lar da kendi kod sayfalarıdır.

| Pozitif sözleşme | Test bulgusu |
|---|---|
|İlk seçim|Kendi RET8 alıcısı; ECXobject, ilk stack argümanı item, ikincisi10000000hex. İndeks0/3/FFFFFFFF ve stride4/8 denendi.|
|İkinci seçim|Kendi RET4 alıcısı; tek hamDWORD argümanı0/FFFFFFFF, ECXobject.|
|Onay|Kendi RET8 alıcısı; item/1 argümanları. Paylaşılan ve son guarded okumada değişen root denendi.|
|İlerletme|Kendi RET8 alıcısı; doğrudan item/1. İki farklı item ve vtable offset'i denendi.|
|Dönüş|Tüm10senaryoda stack/EBP dengesi, seedEBX/ESI/EDI ve EAXCAFEBABE doğrulandı. ReceiverEBX/EBP'yi değiştirir; advance receiverEDI'yi de değiştirir. ESI bütün receiver'larda korunur.|

Receiver girişinde stack farkları ilk36, ikinci24, onay32, ilerletme28byte'tır.
Caller argümanlı iki wrapper için kendi argümanını4byte temizler. Çift/single
receiver'lar kendi8/4byte argümanlarını temizler. Yanlış cleanup sözleşmesi veya
yanlış pointer çalıştırılmadı; bu testlerden gerçek oyunun callee ABI'si çıkarılmaz.

Yeni Python üretim modeli/UI değişikliği yok. Son3637testlik tam Python sonucu
tarihsel olarak yeniden kullanılır; tekrar çalıştırılmış sayılmaz. Fixture
sonuçları ayrıca mevcut saf modelin fiziksel PUSH/context kayıtlarıyla karşılaştırılır.
Derleme ve yürütüm araç sandbox'ı dışında yapıldı; Windows UAC/RunAs/privilege
değişikliği istenmedi. Host sürecinin elevation durumu ölçülmedi.

Bu **yalnız kendi süreç/reader/receiver sözleşmesi altında native yürütüm**
kanıtıdır. Oyun hedefi, gerçek45dc44, native helper exception/ABI, hook kurulumu,
seçimin oyuna teslimi, tam fonksiyon ve canlı uyumluluk sertifikası değildir.
Derlenmiş EXE kaynak paketine konmaz; kaynak/header/build script saklanır.
