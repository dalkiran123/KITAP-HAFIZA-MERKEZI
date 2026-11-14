# Çok kullanıcılı prototip: güvenli dağıtım kontrol listesi

**Durum:** Bu kod bir prototiptir. GitHub Pages üzerindeki mevcut Kitap Hafıza Merkezi'nin yerine geçmez. Gerçek telefonlardan eşitleme veya canlı sunucu henüz doğrulanmadı.

## Dağıtım için zorunlu önkoşullar

1. Ayrı, erişimi sınırlandırılmış bir test alan adı ve HTTPS/TLS sertifikası hazırlayın. TLS sonlandırmasını güvenilir reverse proxy üzerinde yapın.
2. Reverse proxy, `Host` değerini tek bir kanonik alan adıyla sınırlandırmalı; istemciden gelen `X-Forwarded-Host`, `X-Forwarded-Proto` ve `X-Forwarded-For` değerlerini doğrudan geçirmemeli. Uygulamanın `REMOTE_ADDR` değeri güvenilir bir kaynaktan gelmeli.
3. `BOOK_PUBLIC_ORIGIN=https://books.example.com` değerini **gerçek test alan adıyla** ayarlayın. `BOOK_DB_PATH` için kalıcı ve yedeklenen SQLite dosya yolu kullanın. Örnek alan adı gerçek bir servis değildir.
4. Sunucunun veritabanına yalnızca gerekli dosya izinleriyle erişmesini sağlayın. SQLite veritabanını web kök dizininde sunmayın.
5. Kalıcı oturumlar, CSRF koruması, başarısız giriş sınırı ve kullanıcı ayrımını HTTPS üzerinden iki ayrı cihazla test edin. Aynı kitap üzerinde eşzamanlı düzenleme için HTTP 409 davranışını doğrulayın.
6. Kullanıcı kayıtlarını taşımadan önce iPhone'daki V3 JSON yedeğini ayrı yerde saklayın; içe aktarma henüz yalnızca hazırlık aşamasında. Mevcut GitHub Pages `main` dalına dokunmayın.

## Yerel çalıştırma (yalnızca geliştirme)

`multiuser` dizininde `python -m unittest discover -v -p 'test_*.py'` komutuyla testleri çalıştırın. Yerel HTTP üzerinde `Secure` oturum çerezleri tarayıcıda çalışmayabilir. Bu, gerçek telefon testi için HTTPS gerekliliğini ortadan kaldırmaz.

## Açık riskler

- Canlı HTTPS barındırması ve gerçek cihaz doğrulaması yok.
- Giriş sınırlandırması SQLite üzerinde paylaşımlı; çoklu sunucu dağıtımı ve proxy IP yapılandırması ayrıca değerlendirilmelidir.
- Kullanıcı veri yedeğinin geri yüklenmesi ve canlı uygulama entegrasyonu tamamlanmadı.
- Güvenlik testi başarısı, üretime hazır olma onayı değildir.
