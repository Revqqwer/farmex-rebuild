# Str, SW ve Wolf doğrudan kayıt üretimi

20 Ekim 2026. `direct_chat_packets.py` artık önceki TP/Priest ortak/Cure/Disease yollarına ek olarak `004d36ac` Str, `004e08e0` SW ve `004e103c` Wolf yardımcılarının normal kayıt üretimini modeller.

| Yardımcı | Relative | Kayıt uzunlukları | İkinci gecikme | Hedef davranışı |
|---|---:|---|---:|---|
| Str | 4 | 48 / 26 | 1500 | DWORD sıfır kontrolü ve DWORD kopyası |
| SW | 10 | 48 / 38 | 1500 | WORD kopyası; sıfırda da üretim |
| Wolf | 30 | 48 / 38 | 1700 | Hedef argümanı yok; template FFFFFFFF korunur |

Str sıfır kontrolü class ve actor getter'larından sonra gelir. Üst16bit dolu, alt16bit sıfır hedef Str'de atlanmaz. SW üst16bit'i kayda kopyalamaz. Wolf getter'ları X/Y/Z sırasıyla çağırır, fakat iki kayda da X/Z/Y sırasıyla offset14/18/22 yazar. İlk Wolf template'inde offset42 değeri 11hex'tir. Ham EAX bitleri dönüştürülmeden korunur; bu sabitlere doğrulanmamış protokol anlamları verilmez.

Ortak `DirectChatPacketFrame`, tüketilmiş getter değerlerini, bağımsız enqueue gate/tick gözlemlerini ve ilk oluşturulmuş kaydı korur. İkinci enqueue veya normal dönüş eksikken yeniden adımlama kayıt çoğaltmaz. Enqueue normal dönüşü ve dış return span ayrı gözlemlerdir.

`work/audit_direct_chat_remaining.py`, korunmuş eski ve güncel PE dosyalarında toplam590 talimat kaydını doğrular; altı template'i, 22 memcpy argüman dizisini ve her yardımcıdaki iki kuyruk çağrısının uzunluk/gecikmesini kontrol eder. Import ve frame-setup adresleri rol kimliğine göre normalize edildiğinde gövdeler eşleşir. Kaynak rapor `outputs/FarmexBot_dogrudan_chat_kalan_kaniti.json`. Bu korunmuş Ghidra/PE kanıtıdır; yeni REA Evidence değildir.

Altı yeni test Str guard/kopya genişliğini, SW sıfır hedefini, Wolf argüman/koordinat/template/gecikmesini, tüketilmiş getter değerlerini ve geç enqueue devamında tek kayıt oluşmasını sınar. Tam test sonucu `DIRECT_CHAT_REMAINING_VALIDATION.json` içinde tutulur.

Bu çalışma bağımsız, sınırlı byte dizileri ve yerel kuyruk üretir. Doğrudan tüketicilerin bu alt modele bağlanması henüz tamamlanmadı. Orijinal native kod, gerçek bellek yazımı veya ağ gönderimi çalıştırılmadı; helper EAX, skill başarısı ve canlı uyumluluk doğrulanmadı. UI ve native C değişmedi; UI yeniden test edilmedi. Önceki `DIRECT_CHAT_PACKETS.md` önceki dört yardımcı aşamasının tarihsel kaydıdır.
