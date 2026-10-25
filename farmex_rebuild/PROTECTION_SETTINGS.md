# Ortak Koruma ayar üreticisi

`protection_settings.py`,0046b928 yordamının607 instruction'lık gövdesindeki normal ayar kontrol/veri akışını modeller. Önceki19 instruction'lık TP alt bölümünden daha geniştir:50 form üyesi kaynakta görülen sırayla ele alınır. Arayüzdeki checkbox, metin, rota ve işlem seçimi alanları AntiCR, karşı ırk, bildirim, PM ve TP gruplarına aittir.

Giriş ve prologue normal dönüşü açık gözlemlerdir. VCL getter'ları çağrılmadan native nesne kimliği varsayılmaz; ham EAX/AL sonuçları alınır. BYTE alanlarına yalnızAL yazılır; AL2 gibi nonzero baytlar bool1'e daraltılmaz. Hiçbir oyun belleği okunmaz veya değiştirilmez.

## İşlem radio'larının önceliği

| Grup | Kaynak öncelik sırası ve yazılan değer | Hiçbiri işaretli değilse |
|---|---|---|
|AntiCR,context+10|DC→5,rota→0,town→1,slotta kal→2|Yeni store yok|
|Karşı ırk,context+34|rota→0,DC→1,town→2|Yeni store yok|
|Bildirim,context+44|DC→0,oyunu kapat→4,town→1,rota→2,Genie→3|Yeni store yok|
|PM,context+84|town→0,rota→1,DC→3,oyunu kapat→4|Yeni store yok|
|TP,context+B4|Stop radio nonzero→1;else→2|Kaynak2 yazar|

İlk dört grupta eksik seçim, önceki değerin0 olduğu anlamına gelmez. Model o offset'i `unchanged_enum_offsets` içinde bildirir; kaynağın yazmadığı bir varsayılan üretmez. İlk eşleşmeden sonraki getter'lar tüketilmez. TP'nin else kuralı farklıdır ve aynı şekilde genellenmez.

## Sayı ve metin alanları

| Alan | Form üyesi | Context hedefi |0045ef80 fallback DWORD|
|---|---:|---:|---:|
|AntiCR mesafe/metin değeri|74C|0C|80|
|Genie kapatma bekleme değeri|788|1C|60|
|Karşı ırk mesafesi|7DC|2C|50|
|Bildirim Genie süresi|7BC|4C|30|

Bu üreticide dört alana da helper'ın EAX düşükDWORD sonucu yazılır;1000 çarpımı veya signed-negative reddi eklenmez. Gerçek StrToInt64 sözdizimi emüle edilmez. Mevcut `SourceIntegerFrame`, normal parser sonucu veya açıkça gözlemlenmiş catch-landing yolundan default sonucunu üretir. İç modelin tamamlanması ve dış0045ef80 normal dönüşü ayrıdır. Parent alanı ancak ikisi de sağlanınca yazılmış sayılır; sonrasındaki parent Unicode temporary cleanup'ı beklenirken bu store korunur.

Rota alanları760→+24,7F0→+3C,7B0→+54 ve80C→+88'dir. Kaynak Unicode Text getter, ANSI dönüşüm, string assignment, ANSI cleanup ve Unicode cleanup sırasını korur. Model string atamasını `(hedef,captured_bytes)` biçiminde **mantıksal projeksiyon** olarak tutar. Bu, C++ string nesnesine ham bytes yazıldığı veya codepage/nesne yerleşiminin çözüldüğü anlamına gelmez. Unicode metinden byte'lar kendiliğinden tahmin edilmez.

## Sıra ve kısmi ilerleme

Kaynak enable kutularıFalse olsa bile grupların diğer ayarlarını okur. Model de bütün bir grubu enableFalse diye atlamaz. Normal dönüş veya gözlem eksikse yalnız ulaşılan alan beklenir. Önceden tüketilen getter/metin/byte sonuçları sabittir; henüz okunmayan alanlar sonraki ilerletmeden gelebilir. Sayı veya string assignment'ından sonraki cleanup eksikse önceden üretilen store/atama geri alınmaz. Tamamlanmış aynı invocation ikinci kez üretilmez.

Bütün ayar işlemleri tamamlandığında model0046c18f FS/register/stack sonlandırma sınırına ulaşır. Bu sonuç bütün607 instruction'ın native yürütülmesi veya helper/SEH/istisna/ABI doğrulaması değildir. `whole_producer_verified`, `string_identity_verified`, `native_execution_verified` ve `live_compatibility_verified` False kalır. Sayı modeli ve VCL/string yardımcıları gerçek oyunda çağrılmadı.

12 yeni test; dört farklı fallback, no-radio/no-store, öncelik ve kesintili enum değerleri, rawAL,64 bit parser sonucunun düşükDWORD'u, iç/dış parser dönüş ayrımı, store-before-cleanup, string assignment öneki, değişmez input ve giriş kapılarını denetler.

İki sabit Richard görüntüsünde607 ayar instruction'ı ve48 integer helper instruction'ı, toplam1310 kayıt byte doğrulandı.50 form üyesinin tam kaynak sırası ve scalar hedefleri ayrıca eşleştirildi. İki mevcut REA çıktısı kullanıldı; yeni çağrı yapılmadı. Bu kapsamlar diğer aşamalarla örtüşür ve yeni benzersiz analiz yüzdesi değildir. Sınırlı fonksiyon sayısı145 olarak kaldı; aynı fonksiyonun kapsamı genişledi.

API henüz ortak50 alanın tamamıyla arayüz denemesine bağlanmadı; mevcut TP/Genie alt modelleri ayrı kapsamlarını korur. Çalışma tüketicilerinin eylemleri ve canlı uyumluluk ayrıca çözülmelidir. Kanıt: `outputs/FarmexBot_koruma_ortak_ayar_kaniti.json`; denetim: `work/audit_protection_settings.py`.
