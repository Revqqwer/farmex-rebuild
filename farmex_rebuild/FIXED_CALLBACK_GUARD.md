# Sabit-skill callback koruma dalı — 19 Ekim 2026

Transformation yardımcılarının çağrı taraması, 0046f33c içinde farklı bir doğrudan skill kullanımını gösterdi. `fixed_callback_guard.py` bunun yalnız 561f7c baytı sıfır olan dalını modeller. Bu bulgu periyodik Transformation işçisi olarak adlandırılmadı; kullanıcının gördüğü hangi özelliğe ait olduğu henüz bağlanmadı.

561ede baytı sıfırsa yordam EAX0 döner. Aksi durumda GetTickCount ile 553d3c DWORD farkı düşük 32 bitte hesaplanır ve unsigned olarak 5000 ile karşılaştırılır. Tam5000 geçer; saat taşması veya geriye gidiş kaynak DWORD davranışıyla korunur. Bu yol diğer yordamların signed QWORD saat modeliyle birleştirilmez.

Sabit skill0x7a3dc için 00464268 normal dönüşü ve raw EAX ayrı gözlemlerdir. AL sıfırsa EAX0 erken dönüşü vardır; +2000 fallback yoktur. AL nonzero ise doğrudan 004c8388 kayıt üreticisine girilir. `DirectSkillFrame` mevcut actor/copy/yerel kuyruk modelini seçici çağrısı eklemeden kullanır.

Cast dönüşünden sonra ikinci GetTickCount ayrıca istenir. Önce 553d3c bu değerle güncellenir, ardından yalnız AL1 yazılır. Bu yüzden örneğin tick12345678 için EAX12345601'dir. Post-cast tick bilinmiyorsa dönüş AL'si tahmin edilmez; önceden oluşturulmuş own kuyruk kaydı tutulur ve tekrar eklenmez.

Mevcut callback kuyruk kapılarına bu model bağlandı. Koruma AL1 döndüğünde aynı callback'te kuyruk tüketicisi atlanır; yeni kayıt korunur. Sonraki callback'te bekleme koşulu AL0 üretebilir. Tüketiciye geçmeden önce source00458c70 iş yardımcısının normal dönüşü **ve sonrasındaki açık kuyruk durumu** gerekir. Yardımcının kayıtları değiştirmediği varsayılmaz. Outer skip veya guard bypass yolları child gözlemlerini tüketmez. Ulaşılan bağlı guard ile ayrıca raw AL verilmesi reddedilir.

14 yeni test dahil **2600 yerel test, 6.836 saniye** geçti. Beş saniye sınırı/taşma, AL üst bitleri, direct-entry/fallback ayrımı, post-tick boşluğu, kayıt tekrarı, callback skip→sonraki drain sırası, helper dönüşü/post-state ayrımı ve unmodeled dalın sıfıra çevrilmemesi sınandı. Kuyruk yalnız `native_send_plan` tanısı üretir; sender çağrılmaz ve ACK varsayılmaz.

İki korunmuş ikilide guard başlık/dal bölümü ve caller guard→work→consumer sırasının 86 talimat kaydı, iki GetTickCount import kimliğiyle doğrulandı. Serializer için önceki Transformation denetimi ayrı kaynak kanıtıdır. Kapsamlar örtüşebilir; yeni tam-fonksiyon sertifikası değildir. Ghidra/disk/import kanıtıdır, REA Evidence değildir.

561f7c nonzero dalı, diğer callback blokları, gerçek skill/actor/kopya/kuyruk/clock/sender etkileri ve canlı oyun uyumluluğu açıktır. UI değişmedi ve bu tur UI regresyonu tekrarlanmadı. Bütün callback veya otomatik Transformation tamamlanmış sayılmaz.
