# Item kırma istek hazırlığı ve yerel döngü bağı

23 Ekim 2026. `item_break_requests.py` Richard004ca9b0 normal gövdesini
mevcut hedef hazırlama ve kuyruk modellerine bağlar. Yeni REA50-talimat
gövdesiyle karşılaştırılır. Eski/güncel iki ikilide action50, hedef30,
enqueue85 ve clock33 olmak üzere396 disk kaydı tekrar doğrulanır.

Seçili NPC00462630 ile iki kez okunur. İlk EAX0 ise şablonlar ve ikinci
getter atlanır. İlk sonuç sıfır değilse sabit6/19-byte şablonlar kopyalanır;
ardından ikinci taze EAX hedef hazırlama yardımcısına geçirilir. İki sonuç
eşit varsayılmaz. İkinci0 sonucu için kaynakta yeni erken çıkış yoktur.

Mevcut EventPacketFrame('target_prepare') ikinci NPC kimliğini10-byte
şablonun2..5 alanına little-endian olarak yerleştirir. Ayrı child ve parent
normal dönüşlerinden sonra iki sabit kayıt EventEnqueueFrame'e gider:

| Sıra | Byte sayısı | Delay DWORD | Payload |
|---|---:|---:|---|
| Hedef hazırlığı | 10 | 0 | 2001 + ikinciNPC32 + ffffffff |
| Kırma kaydı | 6 | 200 | 640725100000 |
| Moira betik kaydı | 19 | 250 | 55000f31363034375f4d6f6972612e6c7561ff |

Son betik kaydının ff son byte'ı korunur; yalnız görünür Lua adını almak
19-byte kaynak şablonunu eksiltir. Sabit iki şablona NPC ID eklenmez.
Üç enqueue çağrısının connection gate ve tick gözlemleri bağımsızdır.
Gate0 normal dönüşünde kayıt eklenmez ve tick gerekmez; sonraki çağrı
yine ilerleyebilir. Yerel kuyruğa commit ile enqueue normal dönüşü ayrıdır.
Bekleyen dönüşten sonra tekrar advance çağrısı kayıtları çoğaltmaz.

`ItemBreakRequestCycleFrame` önceki envanter, NPC ve clock modellerini tipli
istek çocuğuyla birleştirir. Raw clock action-return bayrağı kabul edilmez.
İstek çocuğu tamamlandıktan sonra ayrıca004ca9b0 parent normal dönüşü
gerekir. Ancak bundan sonra ikinci GetTickCount ve zaman store'ları açılır.
İlk NPC0 nedeniyle hiç kayıt üretilmese de helper normal dönerse clock
yine zamanı yeniler. Bu, sunucunun işlem kabul ettiği anlamına gelmez.

Bu yalnız kendi kuyruk durumumuzdur: native heap, memcpy, gönderim, hook,
oyun girdisi veya sunucu işlemi yürütülmez. Template byte doğrulaması ve
kayıt hazırlığı, teslim/sunucu yanıtı/üretilen item kanıtı değildir.

13 yeni test; toplam3929 test geçti. UI375 bağlı/148 bağlanmamış olarak
değişmedi. NPC/slot/managed helper etkileri, canlı kuyruk ve gerçek oyun
bağlantısı henüz doğrulanmış değil. Diğer item kırma modları tamamlanmadı.
