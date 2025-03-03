# DockeGram

DockeGram, Docker konteynerlarını doğrudan Telegram mesajları üzerinden yönetmenizi sağlayan bir Telegram botudur. DockeGram ile konteynerları başlatabilir, durdurabilir, yeniden başlatabilir, logları görüntüleyebilir ve konteyner durumunu izleyebilirsiniz, tüm bunları Telegram uygulamanızdan yapabilirsiniz.

## Özellikler

- Docker konteynerlarını başlatma, durdurma ve yeniden başlatma
- Konteyner loglarını görüntüleme
- Tüm konteynerları mevcut durumlarıyla listeleme
- Belirli konteynerların varlığını kontrol etme
- Beklenmeyen durumlar için otomatik konteyner durum izleme ve uyarı gönderme
- Erişimi yalnızca yetkili kullanıcılarla sınırlandırmak için kullanıcı kimlik doğrulama

## Ön Gereksinimler

- Ana makinede Docker kurulu olmalı
- Telegram Bot Token (BotFather'dan alınır)
- Yetkili kullanıcıların Telegram Kullanıcı ID'leri

### Telegram Bot Oluşturma

1. Telegram'ı açın ve `@BotFather` araması yapın
2. BotFather ile bir sohbet başlatın ve `/newbot` komutunu gönderin
3. Botunuzu oluşturmak için talimatları izleyin
4. Oluşturulduktan sonra, BotFather size bir token verecektir. Bu token'ı daha sonra kullanmak üzere saklayın.

### Telegram Kullanıcı ID'nizi Alma

1. Telegram'da `@userinfobot`'a bir mesaj gönderin
2. Bot size Kullanıcı ID'nizi ve diğer bilgileri içeren bir yanıt verecektir

## Kurulum ve Kullanım

<details open>
  <summary><h3>Yöntem 1: Docker Compose Kullanımı</h3></summary> 

1. Aşağıdaki içerikle bir `docker-compose.yml` dosyası oluşturun:

```yaml
version: '3.9'

services:
  dockergram:
    image: gdagtekin/dockegram:latest
    container_name: dockegram
    restart: unless-stopped
    environment:
      - TELEGRAM_BOT_TOKEN=BOT_TOKEN
      - ALLOWED_USER_IDS=KULLANICI_ID
      - ENABLE_MONITORING=True
      - MONITORING_INTERVAL=300
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

2. `BOT_TOKEN` ve `KULLANICI_ID` değerlerini kendi değerlerinizle değiştirin
3. `docker-compose.yml` dosyasının bulunduğu dizinde aşağıdaki komutu çalıştırın:

```bash
docker compose up -d
```

</details>

<details>
  <summary><h3>Yöntem 2: Docker Run Kullanımı</h3></summary> 

```bash
docker run -d \
  --name dockegram \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN=BOT_TOKEN \
  -e ALLOWED_USER_IDS=KULLANICI_ID \
  -e ENABLE_MONITORING=True \
  -e MONITORING_INTERVAL=300 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  gdagtekin/dockegram:latest
```

`BOT_TOKEN` yerine BotFather'dan aldığınız token'ı ve `KULLANICI_ID` yerine Telegram Kullanıcı ID'nizi yazın. Birden fazla kullanıcıya izin vermek istiyorsanız, ID'leri virgülle ayırın (örn. `123456789,987654321`).


Logları kontrol edebilirsiniz

```bash
docker logs -f dockegram
```

</details>

<details>
  <summary><h3>Yöntem 3: Kaynak Koddan Derleme</h3></summary> 

1. Repoyu klonlayın:

```bash
git clone https://github.com/kullanıcıadınız/dockegram.git
cd dockegram
```

2. Docker imajını oluşturun:

```bash
docker build -t dockegram .
```

3. Konteyneri çalıştırın:

```bash
docker run -d \
  --name dockegram \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN=BOT_TOKEN \
  -e ALLOWED_USER_IDS=KULLANICI_ID \
  -e ENABLE_MONITORING=True \
  -e MONITORING_INTERVAL=300 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  dockegram
```

Logları kontrol edebilirsiniz

```bash
docker logs -f dockegram
```

</details>

## Yapılandırma Seçenekleri

Dockegram'ı aşağıdaki çevre değişkenleri ile yapılandırabilirsiniz:

| Değişken | Açıklama | Varsayılan |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot token'ınız | Gerekli |
| `ALLOWED_USER_IDS` | Yetkili Telegram Kullanıcı ID'lerinin virgülle ayrılmış listesi | Gerekli |
| `ENABLE_MONITORING` | Otomatik konteyner izlemeyi etkinleştir | False |
| `MONITORING_INTERVAL` | İzleme kontrol aralığı (saniye cinsinden) | 300 |

## Bot Komutları

Dockegram iki komut formatını destekler:

### Doğrudan Komut Formatı (Önerilen)

- `/start_konteyner_adı` - Bir konteyneri başlatır
- `/stop_konteyner_adı` - Bir konteyneri durdurur
- `/restart_konteyner_adı` - Bir konteyneri yeniden başlatır
- `/logs_konteyner_adı` - Bir konteynerden son 10 logu gösterir

### Geleneksel Format (Ayrıca Desteklenir)

- `/start konteyner_adı` - Bir konteyneri başlatır
- `/stop konteyner_adı` - Bir konteyneri durdurur
- `/restart konteyner_adı` - Bir konteyneri yeniden başlatır
- `/logs konteyner_adı` - Bir konteynerden son 10 logu gösterir
- `/check konteyner_adı` - Bir konteynerin var olup olmadığını kontrol eder

### Diğer Komutlar

- `/list` - Tüm konteynerları tıklanabilir komut bağlantıları ile listeler
- `/help` - Yardım mesajını gösterir
- `/info` - Bot ortamı hakkında bilgi gösterir

## Kullanım Örnekleri

- "nginx" adlı bir konteyneri başlatmak için: `/start_nginx` veya `/start nginx`
- Bir konteyneri durdurmak için: `/stop_nginx` veya `/stop nginx`
- Konteyner loglarını görüntülemek için: `/logs_nginx` veya `/logs nginx`
- Tüm konteynerları listelemek için: `/list`

## İzleme Özelliği

`ENABLE_MONITORING` değeri `True` olarak ayarlandığında, Dockegram periyodik olarak tüm konteynerların durumunu kontrol eder. Bir konteyner beklenmedik şekilde durursa (bot aracılığıyla manuel olarak durdurulmamışsa), Dockegram tüm yetkili kullanıcılara bir uyarı mesajı gönderir.

## Güvenlik Hususları

- Bot yalnızca `ALLOWED_USER_IDS` listesindeki kullanıcılardan gelen komutlara izin verir
- Docker soketi konteynere bağlanır, bu da bota Docker ortamınız üzerinde tam kontrol sağlar
- Erişimi yalnızca tam Docker kontrolüne güvendiğiniz kullanıcılara verin

## Lisans

AGPLv3 Lisansı altında dağıtılmaktadır. Daha fazla bilgi için [`LICENSE.md`](https://github.com/gdagtekin/dockegram/blob/master/LICENSE) dosyasına bakabilirsiniz.

## Katkı Sağlayanlar

Gökhan Dağtekin tarafından geliştirilmiştir.
