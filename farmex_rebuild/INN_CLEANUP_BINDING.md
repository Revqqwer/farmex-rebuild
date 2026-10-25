# Inn depo kapanış bağı — 19 Ekim 2026

`storage_workers.py`, ulaşılan 00470a94 kapanış bölümünde `merchant_bank_count.py` sonucunu ve yeni `source_inn_cleanup.py` okuma planını kullanabilir. Bu API bağıdır; arayüzde canlı depo kontrolü veya gerçek aktarım eklenmedi.

Kaynak sırası korunur:

1. Global mod 4 ise own durumda 569870 baytı 1 yapılır.
2. Bağlam+14 değeri sıfırsa 0046ff6c sayacı çağrılır. Bağlı sayaç ayrı normal dönüş onayı ve tamamlanmış 192 slot ister. Eksik slot kesin toplam sayılmaz. Aynı ulaşılan çağrıda ham helper sonucu veya eski slot taramasıyla karıştırılamaz.
3. Sayaç sonucu own bağlam+14 alanına yazılır. Sonraki okuma eksik kalırsa bu önceki yazım korunur. Kayıtlı değer sıfır değilse sonraki girişte sayaç atlanır; sıfırsa yeniden hesaplanır.
4. 553e80 globalinden root, taze 5540bc ofsetinden context ve taze 5541fc ofsetinden durum baytı okunmasının operandları planlanır. Her adres DWORD'a sarılır. Null veya açık koruma başarısızlığı sıfır üretebilir; eksik gözlem üretmez.
5. BYTE okuyucusunun EAX üst bitleri korunabilir; caller yalnız AL'yi sıfırlanmış ECX'e alıp azaltır. Bu nedenle yalnız tam 1 kapatma çağrısı üretir. Bağlı yolda ayrı `cleanup_close_returned=True` gözlemi olmadan own aktif/bekleyen baytları temizlenmez.

`StorageResult.bank_count_plans` ve `cleanup_plans` tanıyı taşır. NPC frame aktarımı own alanları korur. Sayaç ve okuyucu girdileri yalnız ulaşılan dalda tüketilir; VIP ve devam eden Inn slot işlemleri bunları okumaz. Önceki ham helper/scan fixture yolu ayrı kalır.

16 yeni test; eksik dönüş, eksik slot, sıfır sayacın tekrar çağrılması, ara yazımların korunması, cached sayacın atlanması, exact-1, EAX üst bitleri, taşma, null ve bilinmeyen okuma ayrımını kapsar. Son tam doğrulama **2509 test, 7.180 saniye**. Tamamı bağımsız yerel testtir.

İki korunmuş ikilide kapanış bölümü ve ortak okuyucuların **172 talimat kaydı** disk baytlarıyla doğrulandı. VirtualProtect import adresi iki sürümde farklıdır; export kimliği ayrı doğrulandı. Bu kapsam önceki denetimlerle örtüşür ve yeni benzersiz talimat sayısı olarak toplanmaz. Kanıt Ghidra/disk denetimidir; REA Evidence değildir.

Gerçek koruma çağrısı, bellek okuması, native helper dönüşü, kapatma/aktarım etkileri, eşzamanlılık ve canlı uyumluluk doğrulanmadı. `finished_plan` yalnız own plan sonucudur. Tam 00470a94 veya tüm depo özelliği tamamlanmış sayılmaz.
