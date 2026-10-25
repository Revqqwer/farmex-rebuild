# PID22908 tek seferlik erişim metadata sonucu

23 Ekim 2026, 04:15:54 UTC. Kullanıcı yalnız bu test için yönetici başlatmasını
onayladı; izin kullanıldı. Sürecin başlangıç FILETIME'ı, tam yolu, boyutu ve
`ecc420d7c0274ef198c8d174007f51eb954507d25b7226a7082d3ad44493706e`
dosya hash'i eşleşti. Yönetici token'ı doğrulandı.

Normal oturumda VM_READ handle açılması hata5 verdi. Yönetici testinde
OpenProcess başarılı oldu; fakat NtQueryObject sonucundaki GrantedAccess **0**
olarak kaydedildi. VM_READ biti (0x10) bulunmuyor. Query-limited handle'ın
GrantedAccess değeri 4096 olarak kaydedildi. Açılan handle, okuma yetkisinin
kazanıldığını göstermez. Bu test ReadProcessMemory çağırmadı.

Bellek okunan byte:0; yazma:0; oyun işlemi:0. Koruma mekanizmasının nedeni
tespit edilmiş sayılmaz. Güncel oyun hash'i için doğrulanmış adres profili de
bulunmuyor. Bu sonuç canlı HP/MP veya bot uyumluluğunu kanıtlamaz.

Ham kanıt üst outputs klasöründe
`FarmexBot_admin_erisim_metadata_22908_once.json`; kaynak test
`work/elevated_access_metadata_22908_once.py`. Tek seferlik claim ve rapor korunur;
aynı izinle tekrar başlatılmaz.
