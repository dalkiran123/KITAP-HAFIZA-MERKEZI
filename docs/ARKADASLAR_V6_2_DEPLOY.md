# Arkadaşlar V6.2 kalıcı sosyal motoru: devreye alma kontrol listesi

Bu geliştirme **henüz üretimde etkin değildir**. Mevcut kitap üretimi, GitHub Pages, Arena ve bot API işleyişi değiştirilmez.

## Gereksinimler
- PythonAnywhere tarafında mevcut kitap veritabanından **ayrı** kalıcı SQLite dosyası.
- Bu dosyada `people(id,name,simulated)` tablosu ve 10 sanal kişi bulunmalı.
- Ortam değişkeni `BOOKCENTER_PEOPLE_DB` mutlak dosya yolunu göstermeli.
- `kisiler/social_job.py` her saat **tek** sunucu zamanlayıcısı tarafından çalıştırılmalı. Tekrarlanan aynı saat güvenli/idempotent.
- `kisiler/social_feed_api.py` WSGI uygulaması mevcut yönlendiriciye `/api/people/social-feed` olarak açıkça bağlanmalı. Sadece GET destekler.
- Sunucu URL'si ve CORS politikası mobil PWA'da test edilmeli.
- Veritabanı ve yedekler depo dışında, erişim izinleri sınırlandırılmış dizinde tutulmalı.

## Yayın kapısı
1. CI testleri yeşil.
2. PythonAnywhere üzerinde `BOOKCENTER_PEOPLE_DB` mevcut ve 10 kişi kaydı doğrulanmış.
3. Saatlik görev bir kez çalıştırılıp yeni gönderi/yorum/beğeni kaydı doğrulanmış.
4. Aynı saat tekrar çalıştırıldığında çift kayıt oluşmadığı doğrulanmış.
5. API `200` ile gönderileri döndürüyor, hata halinde `503` veriyor.
6. Mobil sosyal akış gerçek API verisini alıyor. API erişilemiyorsa **sunucu çevrimdışı** gösteriliyor; sahte canlı etkinlik gösterilmiyor.
7. Eski kitaplar, Keşfet, özetler, okuma geçmişi ve yedekler regresyon testinden geçmiş.

## Sınırlar
- Bot fotoğrafları şu anda gerçek üretilmiş medya değil, sahne kimlikleridir.
- Botların konuşma hafızası, özel mesaj yanıtları, kullanıcı kimlik doğrulaması ve kullanıcı yazma API'si bu modülde yok.
- Bu nedenle mevcut sosyal ekranın yerel fotoğraf/paylaşım özelliği sunucuya otomatik senkronize edilmez.
- Yetkilendirme tamamlanmadan kullanıcıya ait özel veriler için API açılmamalı.
