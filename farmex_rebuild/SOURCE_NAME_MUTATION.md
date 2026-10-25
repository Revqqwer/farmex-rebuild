# İsim listesi temizleme/silme caller'ları

Güncelleme: optional typed VCL alt planı, ayrı action/entry kimliği ve raw
post-state conflict denetimiyle bağlandı. Metot gövdelerinin190 talimatlık
disk kanıtı ve sınırları [VCL_LIST_MUTATION.md](VCL_LIST_MUTATION.md) içinde.

18 Ekim 2026. `source_name_mutation.py`, beyaz Clear 00423cac,
kara Clear 00423cd8, beyaz DeleteSelected 00423d04 ve kara DeleteSelected
00423d30 normal çağrı akışlarını gözlemlerle modeller. Her fonksiyon16
talimattır; iki sürümde128 kayıt, mevcut1444 kayıtlık liste üretici
denetiminin alt kümesidir. Yeni fonksiyon çözümleme sayısı olarak eklenmez.
`work/audit_source_name_lists.py`, kontrol alanları3d4/3f0, sanal çağrı
slotları13c/148,5690f8 context ve46c3b8 refresh sırasını diskle doğrular.
Kurulu VCL diskindeki slot/export kimlikleri ayrı runtime envanterindedir.
Bu yerel disk/Ghidra kanıtıdır; REA Evidence veya canlı çağrı kanıtı değildir.

Caller seviyesinde boş liste/seçim kontrolü veya değişiklik testi yoktur.
Sanal metot normal döndüğünde refresh koşulsuz çağrılır. Sanal dönüş,
private runtime sınıfının hangi satırları değiştirdiğini tek başına kanıtlamaz:
`rows_after_mutation` ayrıca verilir. Özellikle DeleteSelected'ın yalnız tek
satır sildiği varsayılmaz; bu, kendi panelimizin seçim politikasından ayrıdır.

Optional typed refresh eksikse ilerleme durur. Complete refresh verilse bile
ayrı normal dönüş receipt'i gerekir. Refresh'in taze getter örnekleri post
mutation satırlarına zorla eşitlenmez. Geç eksiklikte `state` giriş durumunu,
`prospective` bilinen yerel sonucu korur; bu native rollback iddiası değildir.
Oyun belleği, pencere veya dosya IO yapılmaz; native_execution_verified False.

Sekiz odaklı test dört kontrol/slot eşleşmesini, no-op sonrası refresh'i,
eksik sanal dönüş/post-state/refresh, bağımsız dönüş receipt'i ve taze getter
ayrımını sınar. Gerçek VCL mutasyon etkileri ve oyun dispatch'i açıktır.
