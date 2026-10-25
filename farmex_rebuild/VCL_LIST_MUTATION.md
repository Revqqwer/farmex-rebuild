# VCL liste mutasyon gövdeleri ve caller bağı

18 Ekim2026. Korunmuş `vcl260_84ea9ebbdc4570cb.bpl` export tablosundaki
sekiz metot Ghidra ile statik çözüldü: Clear, ClearSelection, DeleteSelected,
GetCount, GetItemIndex, GetSelCount, GetSelected, SetItemIndex.190 talimat
kaydı8192baytlık address-bound carrier ve orijinal PE baytlarıyla eşleşti.
Kaynak SHA25684ea9ebb…f83cc6. Üreticiler `work/prepare_list_mutation_scope.py`,
`work/run_list_mutation_scope.ps1`, `work/audit_vcl_list_mutation.py`;
rapor `outputs/FarmexBot_VCL_liste_mutasyon_kod_kaniti.json`.
Bu Ghidra/disk kanıtıdır; REA Evidence veya runtime execution değildir.

## Clear ve DeleteSelected

Clear50d3d9c4, kontrol+2b0 Items nesnesinin virtual48 metodunu çağırır.
Gerçek private Items implementasyonu ve etkileri bu küçük gövdeden çıkmaz.

DeleteSelected50d3db40, kontrol+2a0 BYTE0ise tek seçim yoluna gider.
Virtual130 ItemIndex **iki kez** çağrılır. İlk DWORD FFFFFFFF ise dönüş;
diğer tüm değerlerde ikinci taze DWORD doğrudan Items virtual4c Delete
parametresidir. İkinci değerin FFFFFFFF olması yeniden denetlenmez. Getter
değerleri birleştirilmez ve geçersiz indeks kendi sessiz no-op politikamıza
dönüştürülmez. Native Delete hata/dönüş/etkisi bağımsız gözlemdir.

MultiSelect BYTE nonzero ise Items.Count bir kez okunur; low32 DEC sonucu
signed negatifse dönüş olur. Aksi halde son indeksten0a kadar GetSelected
çağrılır; normal dönen AL nonzero ise aynı indeks silinir. İndeks ters
ilerlediği için önceki silmelerin etkisiyle yeniden hesaplanmaz. Count80000000
decrement sonrası7fffffff olur; model bu büyük döngüyü tamamlandı saymaz,
explicit own iteration budget veya gözlem prefix'i sonunda eksik bırakır.
GetSelected'ın pencere mesajı/istisna iç davranışları bu modelde uygulanmaz.

`vcl_list_mutation.py` normal helper dönüşlerini ve mutation sonrası Unicode
satırlarını ayrı ister. Seçim getter/count değerleri entry liste uzunluğundan
üretilmez; native satır silme etkileri Python tuple silme olarak varsayılmaz.
Eksik gözlemde state girişte, prospective bilinen prefix'te kalır; native
rollback değildir. Delete indices çağrı istekleridir, native başarı kaydı değildir.

`source_name_mutation.py` optional typed alt planın action/entry kimliğini
denetler, raw post-state override'ını reddeder; complete alt plandan sonra da
parent virtual dönüş receipt'i ister. Ardından kaynak gibi46c3b8 refresh gelir.
Own panel halen tek seçim/stable UTF16 politikasını kullanır; bu metotların
oyunda çalıştırıldığı veya aynı BPL'nin yüklü olduğu kanıtlanmış değildir.
DFM'de MultiSelect alanının olmaması güncel runtime BYTE değerini kanıtlamaz.

On yeni test: iki taze indeks/ikinci-1, ilk-1 erken dönüş, ters çoklu seçim,
BYTE nonzero, signed DEC wrap, eksik prefix/budget, eksik mutation etkisi,
normal dönüşler ve parent identity/override denetimleri. UI değişmedi.
Native window/game/IO etkileri0, canlı uyumluluk henüz doğrulanmadı.
