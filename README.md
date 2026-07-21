# Sıfır Maliyetli Otomatik Blog Sistemi (GitHub → WordPress)

Bu sistem her gün otomatik olarak:
1. Google Gemini API (ücretsiz katman) ile bir blog yazısı üretir,
2. WordPress sitenize REST API üzerinden otomatik olarak yayınlar,
3. (opsiyonel) Pexels'ten ücretsiz bir öne çıkan görsel ekler.

Tamamı ücretsiz katmanlarla çalışır: GitHub Actions (public repo'da sınırsız dakika),
Google Gemini API free tier (günde 1 yazı için fazlasıyla yeterli), Pexels API (ücretsiz).

## 1) WordPress tarafında yapılacaklar

- Siteniz **HTTPS** üzerinden yayında olmalı (Application Passwords özelliği HTTP'de varsayılan olarak kapalıdır).
- WordPress yönetim panelinde: **Kullanıcılar → Profil → Uygulama Parolaları (Application Passwords)**
  bölümünden yeni bir uygulama parolası oluşturun (ör. isim: "github-otomasyon"). Size gösterilen
  parolayı bir daha göremezsiniz, kaydedin.
- REST API'nin açık olduğunu kontrol edin: tarayıcıdan
  `https://siteniz.com/wp-json/wp/v2/posts` adresine gidin, JSON verisi dönmeli
  (bazı güvenlik eklentileri veya bazı ucuz paylaşımlı hosting'ler REST API'yi kapatabiliyor).

## 2) Ücretsiz API anahtarlarını alın

- **Gemini API key:** https://aistudio.google.com/apikey adresinden kredi kartı gerekmeden alınır.
- **(Opsiyonel) Pexels API key:** https://www.pexels.com/api/ adresinden ücretsiz alınır.
  İstemiyorsanız bu adımı atlayabilirsiniz, script görselsiz devam eder.

## 3) Bu klasörü GitHub reponuza yükleyin

Bu klasördeki tüm dosyaları (`.github` klasörü dahil) yeni bir GitHub reposunun köküne
yükleyin (public repo Actions dakikaları tamamen ücretsizdir; private repo da ayda 2000
dakikaya kadar ücretsizdir, günde 1 yazı için bu limit sorun olmaz).

## 4) Secrets (gizli anahtarları) tanımlayın

Repo → **Settings → Secrets and variables → Actions → New repository secret** yolundan şunları ekleyin:

| Secret adı         | Açıklama                                              |
|---------------------|--------------------------------------------------------|
| `GEMINI_API_KEY`    | Adım 2'de aldığınız Gemini API anahtarı                |
| `WP_URL`            | Sitenizin adresi, örn: `https://siteniz.com`           |
| `WP_USERNAME`       | WordPress kullanıcı adınız                             |
| `WP_APP_PASSWORD`   | Adım 1'de oluşturduğunuz uygulama parolası (boşluklu haliyle) |
| `PEXELS_API_KEY`    | (Opsiyonel) Pexels API anahtarınız                     |

## 5) Konu listenizi düzenleyin

`topics.txt` dosyasındaki örnek konuları silip kendi niş alanınıza uygun konularla değiştirin.
Script her gün listedeki bir sonraki konuya geçer, liste bitince başa döner. Konu ilerlemesi
`state.json` dosyasında tutulur ve her çalıştırmadan sonra otomatik commit'lenir.

## 6) Test edin

Repo → **Actions** sekmesi → "Günlük Blog Yazısı" iş akışını seçin → **Run workflow**
butonuyla elle bir kez çalıştırıp WordPress sitenizde yazının göründüğünü doğrulayın.

## Bilinmesi gerekenler

- **Zamanlama:** Workflow her gün 07:00 UTC'de (10:00 Türkiye saati) çalışacak şekilde
  ayarlı (`.github/workflows/daily-post.yml` içindeki `cron` satırından değiştirebilirsiniz).
  GitHub'ın yoğunluğuna göre tetikleme birkaç dakika-birkaç saat gecikebilir, dakika hassasiyeti
  garanti edilmez.
- **60 gün kuralı:** GitHub, hiç commit almayan repolardaki zamanlanmış workflow'ları 60 gün
  sonra otomatik durdurur. Bu script her çalıştığında `state.json`'ı commit'lediği için bu
  sorunu kendiliğinden çözer.
- **İçerik kalitesi:** Üretilen yazıları özellikle ilk günlerde WordPress'te "taslak" (draft)
  olarak bırakıp elle kontrol etmek isterseniz, `generate_and_post.py` içindeki
  `"status": "publish"` satırını `"status": "draft"` olarak değiştirin.
- **Maliyet:** Gemini API'nin ücretsiz katmanında günlük istek kotası var; günde 1 yazı bu
  kotayı katbekat aşmıyor. Yine de Google'ın ücretsiz katman şartlarını (girdi/çıktılarınızın
  model eğitiminde kullanılabilmesi gibi) kontrol etmenizi öneririm.
