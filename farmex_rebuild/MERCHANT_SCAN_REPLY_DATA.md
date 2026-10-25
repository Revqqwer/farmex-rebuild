# Merchant Tarama — yanıtın ham veri düzeni

`merchant_scan_reply_data.py`, `004bc650` yordamındaki byte alanları ve cursor ilerlemesini değişmez yerel veri üzerinde çözer. Paket yakalamaz, oyun okumaz, item/actor helper çağırmaz ve native parse dönüşünü başarılı saymaz. Mevcut `merchant_reply.py` dispatcher'ının ayrı `scan_parse_returned` ve `scan_finish_returned` gözlemleri korunur.

Kaynak ilk olarak unsigned uzunluk >=0x95 (149) kapısını kullanır. Bu kapıdan önce byte okunmaz. Subtype +1 değeri 0x23 ise alış yönü bir, başlangıç cursor'u üç; diğer değerlerde satış yönü sıfır, başlangıç cursor'u dörttür. WORD entity ID okunur. Opcode/status kontrolü kaynak dispatcher'dadır; raw decoder içine yeni bir opcode/status reddi eklenmedi.

Her yanıtta 12 slot işlenir. Slot başında DWORD item ID vardır. Sıfırsa alışta sekiz, satışta 12 ek byte okunmadan atlanır. Dolu slotta iki WORD ve DWORD fiyat okunur. Bu WORD'ler şimdilik `word_a` ve `word_b` olarak korunur; item metadata kararı olmadan anlamlarına yeni varsayım eklenmez.

Satış dolu slotunda ayrıca DWORD vardır. Sıfır değilse WORD uzunluk, o uzunlukta byte dizisi, DWORD, WORD ve BYTE ek alanlar tüketilir. Byte dizisi embedded NUL dahil aynen korunur. Native string oluşturma, olası buffer sınırı ve string yaşam döngüsü bu data modelinin kanıtı değildir.

Kaynak cursor helper'ları önce cursor'u artırıp eski adresteki veriye işaret eder. Yerel truncation bu sırayı kaydeder; tamamlanan slotlar ve kısmi alan öneki korunur. Eksik veri sıfırla doldurulmaz. Boş son slotun okunmayan kısmını atlamak cursor'u gerçek uzunluğun dışına taşıyabilir; decoder bunu fazladan bellek okuması saymaz. 149-byte kaynak kapısı satışın bütün slot okumalarını güvenli kılmaz.

10 yeni test ve toplam 4131 test geçti (`work/merchant_scan_reply_data_full_tests.log`). İki Richard sürümünde ana yordam ve cursor/string yardımcılarının 4394 talimat kaydı disk baytlarıyla denetlendi; raw branch ve çağrı operandları ayrıca kontrol edildi. Bu tam bayt kapsamı, 2068 talimatlık ana yordamın tamamının davranış modeline dönüştüğü anlamına gelmez. Yeni başarılı REA analizi yok; mevcut Ghidra çıktısı kullanıldı. Kanıt: `FarmexBot_merchant_yanit_veri_kaniti.json`.

Kalan bağ: kaynak actor lookup'u seller adı/koordinatları, item lookup ve item adı yardımcısı ise kategori/final ad metnini üretir. Bu çağrılar slot parsing, record append ve inline UI filtrelemeyle iç içedir. Yerel raw geçiş bunların native yürütüm sırasını veya başarılı sonuçlarını uydurmaz. Sonraki adım bu metadata üreticilerini çözüp mevcut filtre/sütun modellerine bağlamaktır; gerçek sonuç paneli ve native sıralama ayrıca açıktır.
