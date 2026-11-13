# Kitap Hafıza Merkezi V2.0 - Uygulama ve kabul planı

Durum: Kısmi geliştirme. Üretim otomasyonu ve telefon bildirimleri henüz kurulmadı.

## Zamanlama (Europe/Istanbul)
- 09:00: İstek listesinden önce üç kitap; eksikse popüler havuzundan. Yalnızca doğrulanmış iki özet hazırsa yayımla. İsimleri içeren bildirim.
- 12:00: Katalogdaki bütün kitaplarda 6 ve 20 paragraf versiyonlarını doğrula. Sadece eksikleri yeniden hazırla.
- 21:00: Aynı kuralla üç yeni kitap, doğrulama ve bildirim.
- Her kitap benzersiz kimlik ile takip edilmeli; aynı gün aynı kitap tekrar seçilmemeli.
- İşler sunucu tarafında zamanlanmalı; tarayıcının açık kalmasına bağlı olmamalı. GitHub Pages statik barındırma tek başına sunucu zamanlayıcısı değildir.
- İşlerin başarı/hata kaydı, tekrar deneme, alarm ve içerik yayımlama işlemlerinin atomikliği zorunlu.
- Kullanıcıya ait istek listesi ve okuma verileri şu an tarayıcı localStorage alanında tutuluyor. Sunucu işleri bu listeyi kendiliğinden göremez. Güvenli kimlik doğrulamalı eşitleme olmadan kullanıcı isteklerine göre otomatik seçim mümkün değildir.
- iOS web push için HTTPS, ana ekrana eklenmiş web uygulaması, izin ve push altyapısı gereklidir. Bildirim gönderildi demek için teslim doğrulaması gerekir.
- 6 ve 20 paragraflık versiyonlar doğrulanmalı; eksik içerik hazır gibi gösterilmemeli.
- Dinleme: kullanıcı başlatır; biten kitap dinlendi işaretlenir, sonraki hazır kitap denenir; durdurma devamı keser. iOS otomatik oynatma kısıtları gerçek cihazda test edilmeli.
- Yedekleme: kod değişikliğinden önce GitHub sürüm yedeği; kullanıcı localStorage kayıtları için ayrıca kullanıcı yedeği ve geri yükleme testi. GitHub kod yedeği kullanıcı verisinin yedeği değildir.

## Kabul testleri
1. Her saat diliminde tam üç yeni, tekrar etmeyen ve iki özeti doğrulanmış kitap.
2. İstek listesi boş değilken öncelik isteklerde; yayımlananlar isteklerden kaldırılır.
3. 40 başlangıç kitabı dahil her kitapta iki ayrı özet, 6 ve 20 paragraf.
4. İçerik eksikse hata durumu, tekrar deneme ve başarısızlığı gizlememe.
5. iPhone'da yeni kitap adlarıyla push bildirimi.
6. Üç ardışık kitabın sesli geçişi, durdurma ve kaldığı yerden devam.
7. Veri dışa aktarma, içe aktarma ve önceki sürümden veri kaybı olmaması.
