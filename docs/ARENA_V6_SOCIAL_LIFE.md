# BOOK CENTER ARENA V6.0 — Sosyal Yaşam
Durum: geliştirme dalında tasarım ve güvenli entegrasyon sözleşmesi. Canlıya alınmadı.

## Amaç
Kitap modüllerini bozmadan 10 sanal karakterin sosyal akış, profil, mesajlaşma, ilişki, günlük hikâye ve Arena ligini aynı mobil ekranda sunmak.

## Ekran
- Üst özet: benim lig sıram, 10 karakter, son etkinlik zamanı, sunucu durumu.
- Sekmeler: Akış, Karakterler, Mesajlar, Lig, Yönetim.
- Akış: karakter adı, avatar, zaman, kitap referansı, olay türü, metin; kronolojik, sayfalı.
- Karakter profili: düzenlenebilir ad ve başlangıç kişiliği, hedefler, geçmiş, ilişkiler, okunan kitaplar, etkinlikler.
- Mesajlar: kullanıcı-bot ve bot-bot diyalogları ayrı; simülasyon içeriği açıkça işaretli.
- Lig: kullanıcı ve botlar aynı tabloda; gerçek kullanıcı puanları ile simülasyon puanları ayrı alanlarda.
- Yönetim: başlat/durdur, olay kaydı, çalışma modu ve sunucu sağlığı.

## Veri ve güvenlik
- Mevcut kitap kataloğu, özetler, okuma geçmişi, puanlar, yerel depolama anahtarları ve otomasyonlar değiştirilmeyecek.
- Yeni veriler ayrı arena_v6 isim alanında tutulacak. Versiyonlu şema ve idempotent olay kimliği kullanılacak.
- Botlar insan gibi tanıtılmayacak; tüm bot içerikleri simülasyon olarak etiketlenecek.
- Uygulama kapalıyken sunucuda gerçek çalışma yalnızca çalışan zamanlayıcı/worker ve kalıcı veritabanı doğrulanırsa gösterilecek. Aksi durumda geçmişe dönük simülasyon açıkça belirtilecek.
- Gizli anahtarlar istemciye, GitHub deposuna veya günlüklere yazılmayacak.

## Kabul testleri
1. Mevcut kitap okuma, Keşfet, Kitaplığım, istek, yedek ve özet ekranları regresyon testinden geçer.
2. 10 botun kimliği uygulama kapanıp açılınca korunur.
3. Akış olayları tekrar açılışta çiftlenmez ve zaman sırasıyla gösterilir.
4. Lig kullanıcı ve bot puanlarını doğru ve ayrı kaynaklardan gösterir.
5. Mesajlar bot kimliğine doğru bağlanır; yetkisiz kullanıcı başka kullanıcının mesajlarını göremez.
6. Sunucu kapalıysa 'canlı' ibaresi gösterilmez.
7. iPhone PWA ve Android mobil görünümde taşma/donma olmaz.

## Entegrasyon sırası
1. Mevcut dağıtım dalı, Arena ekranının gerçek dosya yolları, API uçları ve otomasyon bağımlılıklarını saptama.
2. Sosyal akış + karakter profili arayüzü ve izole veri modeli.
3. Mesajlar ve lig entegrasyonu.
4. Kalıcı sunucu olay motoru, izleme, test ve kontrollü yayın.
