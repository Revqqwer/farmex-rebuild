# Kendi child'ımıza PE görüntüsü aktarma

Sonraki worker kontrolü: image'a ek olarak bağımsız3772bayt worker kodu ve25336bayt bağlam taşındı; entry artık ayrılan kod allocation'ından çalıştı. Başlangıç/fixture IPC/ayrı detach ve uyumsuz referansı entry öncesi reddetme kontrolleri geçti. Ayrıntı: [COPIED_WORKER.md](COPIED_WORKER.md). Aşağıdaki ilk transfer biçiminin resident-worker bağımlılığı bu yeni kendi-fixture biçiminde kaldırılmıştır; oyun uyumluluğu hâlâ açık.

17 Ekim 2026. Önceki askıda başlangıç kontrolünde DLL child'a gömülüydü ve child kendi kopyasını hazırlıyordu. Yeni `-TransferImage` biçiminde parent, sabit kendi DLL görüntüsünün başlık ve bölümlerini yalnız kendi yarattığı hash-pinned child'a aktarır. Child bu **aktarılmış allocation'ı** doğrulayıp relocation/import/entry hazırlığını yapar. Oyun hedeflenmedi.

## Gerçek çalışma sonucu

Parent own-child içinde `0x20000000` adresinde `0x5000` baytlık RW allocation oluşturdu. Tercih edilen DLL tabanı `0x10000000` olduğundan bu farklı tabanda çalışmadır. Dört WriteProcessMemory çağrısının tam byte sayısı kontrol edildi:

| Parça | Hedef RVA | Dosya offseti | Kopyalanan bayt |
|---|---|---|---|
| Headers | 0 | 0 | 512 |
| .text | 1000 | 200 | 7168 |
| .data | 3000 | 1e00 | 2560 |
| .reloc | 4000 | 2800 | 512 |

RVA/offsetler hexadecimal, boyutlar decimal'dir. Toplam10752bayt, dört ayrı başarılı kopyadır; image allocation boyutu20480bayttır.

Child, gelen pointer için tek başına ayrılmış tam `0x5000` boyutlu committed/MEM_PRIVATE/RW bölgesini denetler. Derlemede sabitlenmiş kendi DLL'inden sıfır boşlukları da kapsayan beklenen tam bellek görüntüsünü üretir ve gelen görüntüyle karşılaştırır. Bu olumlu örnekte tam görüntü karşılaştırması geçti. Ardından116relocation ve43import çözümlemesi kontrol edildi; bunlar exact pinned DLL'e ait sayılardır.

Başlangıç sonrasında parent'ın own-child sayfa metadata ölçümü: headers READONLY2, text EXECUTE_READ20, data READWRITE4. Maskeler hexadecimal'dir. Başlangıç allocation'ı RW idi; source Loader'ın bütün görüntüyü başlangıçta RWX ayırması aynen kopyalanmadı.

Ana main gövdesi hazır işareti vermeden önce child fixture çerçevesi FILE_MAP_READ ile alındı. Header/payload ABI, boyutlar, producer/payload PID, profile1, source FIXTURE, sequence2, hata alanlarının0olması,24bayt self-read ve HP250/500/MP100/300kontrol edildi. ResumeThread önceki suspend1döndürdü; main hazır işareti geldi, child kendi DLL/allocation'ını kapattı ve exit0ile bitti. Parent exit0ve haritanın kaybolması doğrulandı.

## Üç ayrı kontrol

- Aktarılan görüntü yolu: parent `693eda60…7d33cc`, child `ba8190e2…eb7929`; bütün sekiz aşama geçti. Kanıt: `FarmexBot_aktarilan_PE_693eda60_testi.json`.
- Ortak hazırlayıcı değiştiği için gömülü-DLL yolu ayrı klasörde yeniden derlendi: parent `4e2b2346…68d88`, child `3ba7e1d3…b2dea`; sıfır parent image-write ile aynı başlangıç/IPC/resume/cleanup regresyonu geçti. Kanıt: `FarmexBot_askida_baslangic_4e2b2346_testi.json`.
- Hedef dosya kimliği negatif kontrolü: parent'ın ayrı kopyasının yanında kendi child dosyasının DOS işareti bozuldu. Parent bunu birinci aşamada reddetti; child PID0kaldı, süreç oluşturulmadı. Bu beklenen ret testi geçti. Kanıt: `FarmexBot_PE_hedef_kimlik_kapisi_693eda60_testi.json`. Bu test child'ın bellek görüntüsü karşılaştırmasına fault injection yapmaz; o ayrı bir ret dalıdır.

Eski başarılı `4f8b69cd` kontrol kaydı üzerine yazılmadı. Native zincir kontrolleri Python birim testi sayısına eklenmez. Son1719birim/UI sonuçları önceki kapsamdır; native-only değişiklikte tekrar çalıştırılmadı.

## REA yaklaşımıyla kaynak bağı

`work/audit_loader_pe_transfer.py`, orijinal Loader SHA256 `97d946ddec5df814e0042384b78b711c029f136aa6c43701910fd21cef5a0775` içindeki `0041e710` gövdesinin127talimat kaydını byte olarak doğruladı. Statik API bağları OpenProcess1, VirtualAllocEx2, WriteProcessMemory4site ve CreateRemoteThread1site içerir. Kaynak, image SizeOfImage/SizeOfHeaders alanlarını ve section RVA/raw-size/raw-offset düzenini kullanır. Kendi testimizde headers+üç section toplamı ayrıca gerçek10752bayt/four-copy sonucu ile karşılaştırıldı.

Bu, Ghidra exact-byte kanıtı ve ayrı kendi runtime kontrolüdür; REA Evidence veya özgün programda canlı API izi değildir. Kaynak kaydı `FarmexBot_PE_aktarim_kod_kaniti.json` dosyasındadır. Kaynaktaki dört statik WriteProcessMemory site'ı dört toplam runtime çağrı demek değildir: section site'ı döngüdedir, ayrıca worker metadata/code kopyaları vardır.

## Kalan fark

Bu kontrolün bootstrap yordamı kendi child EXE'mizde önceden bulunan export'tur. Orijinal Loader ise worker bağlamını ve worker kodunu uzak allocation'a da kopyalar. O worker-code taşıma yolu ve gerçek oyunda çalışacak bağımsız başlangıç entry'si bu testte tamamlanmış değildir. Child içinde gömülü DLL, aktarılan görüntüyü doğrulamak için referans olarak kalır; transfer biçimi onu yürütülecek görüntü olarak yeniden kopyalamaz.

Parent yine yalnız kendisinin CreateProcess ile oluşturduğu sabit sibling handle'ını kullanır. CLI mevcut PID, program yolu veya DLL payload'ı kabul etmez. Child dosyası SHA256ile doğrulanır ve yazmaya kapalı handle ile tutulur. Başarısızlık cleanup/termination yolu yalnız bu kendi child'ına ve kendi job'ına aittir. DLL SHA256kapısı `4510845e33931b26da0381adfa12e414c4ef72d9c0206728952f6ecfe1903c3a` olarak korunur.

Bu deneyde own-child memory write/allocation ve bir remote thread vardır; Game üzerinde bunlar0dır. Gerçek oyunda hakların verildiği, oyunun başlangıç/TLS/loader aşamalarının aynı olduğu, hedef adres/ABI, HP/MP veya özellik sonuçları doğrulanmadı. Yönetici başlatma iptalinden sonra yeni UAC isteği yapılmadı.

Derleme `native/build_suspended_bootstrap_fixture.ps1 -TransferImage` ile ayrı OutputDirectory'ye yapılır. `work/verify_suspended_bootstrap.py --transferred` ve `--embedded-refresh` ilgili kendi build'lerini, `work/verify_bootstrap_hash_gate.py` ayrı negatif kopyayı sınar. Generated header'lar ve programlar kaynak ZIP'ine girmez.
