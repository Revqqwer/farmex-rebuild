# Kaynak004ca220 — PM isteği byte/kuyruk modeli

`PrivateChatRequestFrame`, ayrı kendi `QueueState` ve gözlemler üzerinde `35 01 <WORD length LE> <name bytes>` çıktısını hazırlar. Bu, `0x10` chat-text serializer'ı değildir. Kaynak null fresh name pointer için5479b5 empty literal kullanır; ilk argument değeri, by-value copy sonrasındaki fresh pointer yerine geçmez. Frame, string construction ve helper normal dönüşlerini açık gözlemler olarak ister.

WORD uzunluk, kopya kontrol DWORD'u, memcpy uzunluğu ve kopya sonrası index artışı ayrı okunur. Tutarlı string görüntüsü varsayımıyla birbirlerinden türetilmezler. Eksik data capture veya memcpy normal dönüşü byte uydurmaz. Tamamlanan helperlar ve kopyalanan byte'lar resume sırasında korunur. Enqueue'dan sonra cleanup eksikse tekrar aynı own kaydı eklenmez. Gate0 yolu tick gözlemi gerektirmeden kendi kuyruğunu değiştirmeyebilir; bu delivery/ACK kanıtı değildir.

Kaynak buffer başlangıcı EBP-0xb8, daha önce kullanılıp sonra ölü kalan pointer EBP-0x54, index EBP-0x50'dir. Modellenen ilk bölge100 byte, counter'a kadar104 byte'tır. Header4 byte olduğundan name kopyası100 byte'a kadar bu sınırın içinde kalır. Kopya counter alanına ulaşırsa açık `source_stack_alias_copy` eksikliği verilir. Index initialize edilmiş byte'ların ötesine çıkarsa `uninitialized_enqueue_tail` ile durur; sıfır dolgu eklenmez. Bu, kaynak buffer overflow yolunun güvenli bir yeniden yorumlanması veya native unwind çözümü değildir.

12 test wire byte'larını, null pointer, bağımsız uzunluk okumaları,100/104 sınırı, sıfır uzunluk copy, eksik capture/normal dönüş, kopya öneki, gate0 ve cleanup-resume tekilliğini kontrol eder. Bütün kayıtlar kendi belleğindeki kuyruktadır; Windows/game handle, socket, ağ gönderimi veya actual PM oluşmaz.

Ortak string/byte/WORD append ve004c7710 enqueue gövdeleri iki pinned sürümde kontrol edilmiştir. Ortak kanıt FarmexBot_merchant_hucre_PM_kaniti.json dosyasındadır. Source header/body bağları, pointer/heap ömrü ve SEH opaque normal-return gözlemleriyle sınırlıdır. Gerçek Merchant cell binding ve kaynak native/game runtime tamamlanmadı.
