# 🛡️ Telegram Defender Bot — Professional Guruh Moderatsiyasi va Pullik Reklamalarni Boshqarish Tizimi

**Defender Bot** — katta hajmdagi Telegram guruhlarida ruxsatsiz tijoriy reklamalarni avtomatik aniqlaydigan, guruhdan o‘chiradigan, qoidabuzarga rasmiy murojaat tartibini tushuntiradigan va administratorlar uchun to‘liq avtomatlashtirilgan pullik reklama xizmati (narx belgilash, to‘lov chekini qabul qilish, tekshirish va tasdiqlangandan so‘ng avtomatik e’lon qilish)ni taqdim etuvchi professional ishlab chiqarish darajasidagi tizimdir.

Ushbu loyiha **Python 3.12+**, **Aiogram 3.x**, **PostgreSQL**, **SQLAlchemy 2.x (asyncpg)**, **Alembic**, **Redis**, **Docker / Docker Compose** va zamonaviy xavfsizlik arxitekturasi asosida to‘liq ishlab chiqilgan. Barcha foydalanuvchi va ma’muriy xabarlar qat’iy **O‘zbek lotin alifbosi**da taqdim etiladi.

---

## 📋 MUNDARIJA

1. [Tizim talablari (Prerequisites)](#1-tizim-talablari-prerequisites)
2. [@BotFather orqali bot yaratish](#2-botfather-orqali-bot-yaratish)
3. [Bot tokenini sozlash](#3-bot-tokenini-sozlash)
4. [Guruh ID raqamini aniqlash va sozlash](#4-guruh-id-raqamini-aniqlash-va-sozlash)
5. [Botni guruhga administrator sifatida qo‘shish](#5-botni-guruhga-administrator-sifatida-qoshish)
6. [Xabarlarni ko‘rish va o‘chirish huquqlarini yoqish](#6-xabarlarni-korish-va-ochirish-huquqlarini-yoqish)
7. [Administrator Telegram ID raqamlarini sozlash](#7-administrator-telegram-id-raqamlarini-sozlash)
8. [To‘lov kartasi va karta egasini sozlash](#8-tolov-kartasi-va-karta-egasini-sozlash)
9. [Reklama e’lon qilinadigan nishon kanal/guruhni sozlash](#9-reklama-elon-qilinadigan-nishon-kanalguruhni-sozlash)
10. [Bog‘liqliklarni (Dependencies) o‘rnatish](#10-bogliqliklarni-dependencies-ornatish)
11. [PostgreSQL ma’lumotlar bazasini sozlash](#11-postgresql-malumotlar-bazasini-sozlash)
12. [Alembic migratsiyalarini ishga tushirish](#12-alembic-migratsiyalarini-ishga-tushirish)
13. [Botni ishga tushirish](#13-botni-ishga-tushirish)
14. [Avtomatlashtirilgan testlarni ishga tushirish (Pytest)](#14-avtomatlashtirilgan-testlarni-ishga-tushirish-pytest)
15. [Docker Compose orqali deploy qilish](#15-docker-compose-orqali-deploy-qilish)
16. [Avtomatik qayta ishga tushishni sozlash (Systemd & Docker)](#16-avtomatik-qayta-ishga-tushishni-sozlash-systemd--docker)
17. [Ma’lumotlar bazasini zaxiralash (Backup) va tiklash (Restore)](#17-malumotlar-bazasini-zaxiralash-backup-va-tiklash-restore)
18. [Loglarni kuzatish va xatoliklarni bartaraf etish (Troubleshooting)](#18-loglarni-kuzatish-va-xatoliklarni-bartaraf-etish-troubleshooting)
19. [Botni xavfsiz yangilash (Zero-downtime update)](#19-botni-xavfsiz-yangilash-zero-downtime-update)
20. [Oshkor bo‘lgan maxfiy kalitlarni almashtirish (Secret Rotation)](#20-oshkor-bolgan-maxfiy-kalitlarni-almashtirish-secret-rotation)
21. [Staging (sinov) muhitini sozlash](#21-staging-sinov-muhitini-sozlash)
22. [Production tayyorgarlik nazorat ro‘yxati (Checklist)](#22-production-tayyorgarlik-nazorat-royxati-checklist)

---

## 1. Tizim talablari (Prerequisites)

Loyihani serverda yoki mahalliy kompyuterda ishga tushirish uchun quyidagi dasturlar o‘rnatilgan bo‘lishi lozim:

- **Operatsion tizim:** Linux (Ubuntu 22.04 LTS / Debian 12 tavsiya etiladi) yoki Windows 10/11 / Windows Server.
- **Python:** 3.12 yoki undan yuqori barqaror versiya (`python --version`).
- **PostgreSQL:** 15 yoki 16 versiyalari (`psql --version`).
- **Redis (ixtiyoriy):** 7.x versiyasi (keshlash va taqsimlangan qulflar uchun).
- **Tesseract OCR (ixtiyoriy):** Rasmlardagi yozuvlarni aniqlash uchun (`tesseract-ocr`).
- **Docker & Docker Compose (ixtiyoriy, tavsiya etiladi):** Docker Engine 24+ va Compose v2+.
- **Git:** Repozitoriy kodini olish va yangilash uchun.

---

## 2. @BotFather orqali bot yaratish

1. Telegram ilovasida rasmiy **[@BotFather](https://t.me/BotFather)** botiga kiring va `/start` buyrug‘ini yuboring.
2. Yangi bot ochish uchun `/newbot` buyrug‘ini bering.
3. Bot uchun ko‘rinadigan nom kiriting (masalan: `Super Savdo Himoyachi`).
4. Bot uchun yagona `username` kiriting (u mantiqan `bot` bilan tugashi shart, masalan: `SuperSavdoDefenderBot`).
5. BotFather sizga maxfiy **API Token** beradi (masalan: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`). Ushbu tokenni hech kimga ko‘rsatmang!

---

## 3. Bot tokenini sozlash

Loyiha ildiz papkasidagi `.env.example` faylidan nusxa olib, `.env` faylini yarating:

```bash
cp .env.example .env
```

`.env` faylini ochib, olingan tokenni kiriting:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

> ⚠️ **DIQQAT:** `.env` fayli `.gitignore` ga kiritilgan. Uni hech qachon GitHub yoki ochiq repozitoriyalarga yuklamang!

---

## 4. Guruh ID raqamini aniqlash va sozlash

Bot faqat belgilangan guruhni nazorat qilishi uchun target guruh ID si ko‘rsatilishi lozim:

1. Botni guruhingizga qo‘shing.
2. Guruhga `@userinfobot` yoki `@RawDataBot` botini qo‘shib yoki xabarni unga forward qilib guruh ID sini oling. Guruh ID lari odatda `-100` prefiksi bilan boshlanadi (masalan: `-1001987654321`).
3. `.env` faylida quyidagi qatorni to‘ldiring:

```env
TARGET_GROUP_ID=-1001987654321
```

*Eslatma: Agar bu parametr bo‘sh qoldirilsa, bot o‘zi a’zo bo‘lgan barcha guruhlarda moderatsiyani amalga oshiradi.*

---

## 5. Botni guruhga administrator sifatida qo‘shish

1. Telegram guruh sozlamalariga kiring: **Guruh ma'lumotlari ➡️ Tahrirlash (Edit) ➡️ Administratorlar (Administrators)**.
2. **Administrator qo‘shish (Add Administrator)** tugmasini bosing.
3. Qidiruvdan botingiz nomini (`@SuperSavdoDefenderBot`) topib tanlang.
4. Administratorlikka tayinlashni tasdiqlang.

---

## 6. Xabarlarni ko‘rish va o‘chirish huquqlarini yoqish

Telegram cheklovlari va maxfiylik siyosati tufayli bot xabarlarni ko‘rishi va o‘chira olishi uchun quyidagi ikki muhim talab bajarilishi shart:

### A) @BotFather da Privacy Mode ni o‘chirish:
1. `@BotFather` botiga kiring.
2. `/mybots` ➡️ O‘z botingizni tanlang ➡️ **Bot Settings** ➡️ **Group Privacy** ➡️ **Turn off** (Disabled) qiling.
3. Bu botga guruhdagi barcha xabarlarni tahlil qilish uchun ko‘rish imkonini beradi.

### B) Guruhda zarur administratorlik huquqlarini berish:
Botga quyidagi huquqlar faol holatda bo‘lishi lozim:
- ✅ **Xabarlarni o‘chirish (Delete messages)** — Ruxsatsiz reklamalarni zudlik bilan o‘chirish uchun.
- ✅ **Foydalanuvchilarni cheklash (Restrict members)** — Zarur hollarda jazolash uchun.
- ✅ **Havola orqali taklif qilish (Invite users via link)** — Xizmat taklif havolalarini taqdim etish uchun.
- ✅ **Xabarlarni qadash (Pin messages)** — Rasmiy e’lonlarni qadash uchun.

---

## 7. Administrator Telegram ID raqamlarini sozlash

Bot ma’murlarining shaxsiy Telegram ID raqamlarini `@userinfobot` orqali bilib oling va `.env` fayliga kiriting:

```env
# Asosiy egasi (Owner)
OWNER_ID=123456789

# Qo'shimcha administratorlar (vergul bilan ajratiladi)
ADMINS=123456789,987654321

# Bog'lanish uchun username
ADMIN_USERNAME=bosh_admin
```

---

## 8. To‘lov kartasi va karta egasini sozlash

Reklama beruvchiga narx belgilanganda avtomatik yuboriladigan to‘lov rekvizitlarini `.env` faylida sozlang:

```env
AD_PAYMENT_CARD=8600 1234 5678 9012
AD_CARDHOLDER_NAME=ALISHER USMONOV
AD_PRICE=150000
MIN_AD_PRICE=1000
MAX_AD_PRICE=100000000
```

Ushbu parametrlar Telegram ichidagi `/admin` panelida interaktiv ravishda ham istalgan vaqt o‘zgartirilishi mumkin.

---

## 9. Reklama e’lon qilinadigan nishon kanal/guruhni sozlash

Agar tasdiqlangan reklamalarni original guruhning o‘ziga emas, balki alohida rasmiy kanal yoki guruhga chop etmoqchi bo‘lsangiz:

```env
AD_PUBLISH_CHANNEL_ID=-1002223334445
```

Agar bo‘sh qoldirilsa, tasdiqlangan reklama qaysi guruhdan o‘chirilgan bo‘lsa, aynan o‘sha guruhga `#reklama #hamkorlik` rasmiy xeshtegi bilan e’lon qilinadi.

---

## 10. Bog‘liqliklarni (Dependencies) o‘rnatish

Tizimda virtual muhit (virtual environment) yarating va kutubxonalarni o‘rnating:

```bash
# Virtual muhit yaratish
python -m venv venv

# Virtual muhitni faollashtirish (Linux / macOS)
source venv/bin/activate

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Pip yangilash va kutubxonalarni o'rnatish
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 11. PostgreSQL ma’lumotlar bazasini sozlash

1. PostgreSQL serverida ma’lumotlar bazasi va foydalanuvchi yarating:

```sql
CREATE USER defender_user WITH PASSWORD 'KuchliParol123!';
CREATE DATABASE defender_bot OWNER defender_user;
GRANT ALL PRIVILEGES ON DATABASE defender_bot TO defender_user;
```

2. `.env` fayliga ulanish manzilini yozing:

```env
DATABASE_URL=postgresql+asyncpg://defender_user:KuchliParol123!@localhost:5432/defender_bot
```

---

## 12. Alembic migratsiyalarini ishga tushirish

Ma’lumotlar bazasi jadvallarini eng so‘nggi versiyaga keltirish uchun Alembic migratsiyasini bajaring:

```bash
alembic upgrade head
```

Bu `users`, `groups`, `advertisements`, `orders`, `payments`, `warnings`, `settings`, `audit_logs` va boshqa barcha jadvallarni to‘liq yaratadi.

---

## 13. Botni ishga tushirish

Barcha sozlamalar kiritilgach, botni ishga tushiring:

```bash
python -m app.main
```

Konsolda quyidagi ma’lumot aks etadi:
```
2026-10-17 10:00:00 | INFO | Initialized database engine
2026-10-17 10:00:01 | INFO | Bot started | @SuperSavdoDefenderBot (ID: 1234567890)
2026-10-17 10:00:01 | INFO | Web Admin Panel available at: http://localhost:8000
```

---

## 14. Avtomatlashtirilgan testlarni ishga tushirish (Pytest)

Loyiha biznes logikasi, e’lonlar tahlili, to‘lovlar tasdiqlanishi va xavfsizlik holatlarini to‘liq qamrab oluvchi avtomatlashtirilgan testlarga ega:

```bash
pytest -v
```

Barcha 50 dan ortiq testlar 100% muvaffaqiyatli o‘tishi shart:
```
============================= 53 passed in 15.71s =============================
```

---

## 15. Docker Compose orqali deploy qilish

Docker Compose orqali tizimni birgina buyruq bilan PostgreSQL, Redis, Bot Worker va Web Admin paneli bilan birga ishga tushirishingiz mumkin:

```bash
# 1. Konteynerlarni qurish va fonda ishga tushirish
docker compose up -d --build

# 2. Konteynerlar holatini tekshirish
docker compose ps

# 3. Loglarni real vaqtda kuzatish
docker compose logs -f bot
```

---

## 16. Avtomatik qayta ishga tushishni sozlash (Systemd & Docker)

### A) Docker orqali:
`docker-compose.yml` faylida barcha servislar uchun `restart: unless-stopped` parametri yoqilgan. Server o‘chib yonsa ham, tizim avtomatik tiklanadi.

### B) Linux Systemd Servisi orqali (Docker ishlatilmaganda):
`/etc/systemd/system/defender-bot.service` faylini yarating:

```ini
[Unit]
Description=Telegram Defender Bot Service
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/defender_bot
EnvironmentFile=/home/ubuntu/defender_bot/.env
ExecStart=/home/ubuntu/defender_bot/venv/bin/python -m app.main
Restart=always
RestartSec=5
StandardOutput=append:/home/ubuntu/defender_bot/logs/bot_stdout.log
StandardError=append:/home/ubuntu/defender_bot/logs/bot_stderr.log

[Install]
WantedBy=multi-user.target
```

Servisni yoqing va ishga tushiring:
```bash
sudo systemctl daemon-reload
sudo systemctl enable defender-bot
sudo systemctl start defender-bot
sudo systemctl status defender-bot
```

---

## 17. Ma’lumotlar bazasini zaxiralash (Backup) va tiklash (Restore)

### Zaxira nusxa olish (Backup):
```bash
# Mahalliy PostgreSQL uchun:
pg_dump -U defender_user -h localhost defender_bot > backup_$(date +%Y%m%d_%H%M%S).sql

# Docker ichidagi PostgreSQL uchun:
docker exec -t defender_bot_postgres pg_dump -U postgres defender_bot > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Zaxiradan tiklash (Restore):
```bash
# Mahalliy PostgreSQL uchun:
psql -U defender_user -h localhost -d defender_bot < backup_file.sql

# Docker ichidagi PostgreSQL uchun:
cat backup_file.sql | docker exec -i defender_bot_postgres psql -U postgres -d defender_bot
```

---

## 18. Loglarni kuzatish va xatoliklarni bartaraf etish (Troubleshooting)

Log fayllar `logs/` papkasida avtomatik aylanuvchi (rotating) shaklda saqlanadi:

```bash
# Oxirgi loglarni kuzatish:
tail -f logs/bot.log

# Xatoliklarni qidirish:
grep "ERROR" logs/bot.log
```

### Keng tarqalgan holatlar:
1. **TelegramBadRequest: Not enough rights to delete message**
   - *Sabab:* Botga guruhda «Xabarlarni o‘chirish» huquqi berilmagan.
   - *Yechim:* Guruh administratorlari bo‘limidan bot huquqlarini tekshiring.
2. **TelegramForbiddenError: bot was blocked by the user**
   - *Sabab:* Foydalanuvchi botga avval `/start` bosmagan yoki botni bloklagan.
   - *Yechim:* Bot guruhda rasmiy ogohlantirish qoldiradi, bot bu xatolikda to‘xtab qolmaydi.
3. **Address already in use (Port 8000)**
   - *Sabab:* Web Admin panel porti boshqa jarayon tomonidan band qilingan.
   - *Yechim:* `.env` faylida `WEB_ADMIN_PORT=8080` qilib o‘zgartiring.

---

## 19. Botni xavfsiz yangilash (Zero-downtime update)

Yangi versiyani xavfsiz o‘rnatish tartibi:

```bash
# 1. Yangi kodni yuklab olish
git pull origin main

# 2. Yangi bog'liqliklarni yangilash
pip install -r requirements.txt

# 3. Ma'lumotlar bazasi migratsiyasini qo'llash
alembic upgrade head

# 4. Testlarni tekshirish
pytest -v

# 5. Servisni qayta yuklash
sudo systemctl restart defender-bot
# Yoki Docker da:
docker compose up -d --build
```

---

## 20. Oshkor bo‘lgan maxfiy kalitlarni almashtirish (Secret Rotation)

Agar `BOT_TOKEN` yoki ma’lumotlar bazasi paroli tasodifan ochiqlanib qolsa:

1. **Bot Tokenni yangilash:**
   - `@BotFather` ga kiring ➡️ `/mybots` ➡️ Botni tanlang ➡️ **API Token** ➡️ **Revoke current token**.
   - Yangi tokenni `.env` fayliga yozing va botni qayta ishga tushiring.
2. **Baza parolini yangilash:**
   - `ALTER USER defender_user WITH PASSWORD 'YangiKuchliParol';`
   - `.env` da `DATABASE_URL` dagi parolni yangilang.
3. **Web Admin Secret Key:**
   - `.env` dagi `WEB_ADMIN_SECRET_KEY` qiymatini yangi tasodifiy satrga almashtiring.

---

## 21. Staging (sinov) muhitini sozlash

Haqiqiy faol guruhga ulashdan oldin alohida staging sinov muhitini ochish qat’iy tavsiya etiladi:
- Yangi test boti oching (masalan: `@DefenderStagingBot`).
- Alohida sinov Telegram guruhi ochib, botni unga qo‘shing.
- `.env.staging` faylida alohida `DATABASE_URL=.../defender_staging` yarating.
- Stagingda barcha to‘lov cheki yuborish va e’lon qilish jarayonlarini to‘liq sinab ko‘ring.

---

## 22. Production tayyorgarlik nazorat ro‘yxati (Checklist)

- [x] `@BotFather` da Privacy Mode «Disabled» qilingan.
- [x] Bot guruhga «Xabarlarni o‘chirish» huquqi bilan administrator qilingan.
- [x] `OWNER_ID` va `ADMINS` to‘g‘ri kiritilgan.
- [x] To‘lov karta raqami va karta egasi to‘g‘ri ko‘rsatilgan.
- [x] `.env` faylida kuchli parollar o‘rnatilgan va git repozitoriyasiga qo‘shilmagan.
- [x] PostgreSQL bazasida barcha Alembic migratsiyalari muvaffaqiyatli o‘tgan (`alembic upgrade head`).
- [x] Pytest testlari 100% muvaffaqiyatli yakunlangan (`60 passed`).
- [x] Tizim loglari `logs/bot.log` ga yozilmoqda.
- [x] Server avtomatik qayta ishga tushish mexanizmi (Docker yoki Systemd) sozlangan.

---

## 23. Dinamik Mahsulot Anketalari va Savol-Javob Tizimi (Dynamic Questionnaire Engine)

Botda har bir mahsulot turi uchun maxsus dinamik savol-javob tizimi joriy etilgan:

### 1. Asosiy Bo‘limlar:
- **🏠 Uy va ko‘chmas mulk:** Novostroyka, Ikkilamchi xonadon, Hovli uy, Yer uchastkasi, Tijorat binosi, Ijara uylar.
- **🛋 Mebel:** Divan va yumshoq mebel, Yotoqxona, Shkaf, Oshxona, Stol-stul, Ofis, Bolalar mebeli, Buyurtma asosida mebel tayyorlash.
- **🪟 Jalyuzi va pardalar:** Vertikal, Gorizontal, Rulon, Zebra, Rim, Klassik, Tyul, Karniz, Tikish va montaj xizmatlari.
- **📱 Boshqa mahsulotlar va texnikalar:** Smartfonlar, Kompyuterlar, Televizorlar, Maishiy texnika, Isitish/sovitish uskunalari, Qurilish mollari, Asboblar, Avto ehtiyot qismlari, Kiyim-kechak va Xizmatlar.

### 2. Navigatsiya va Tahrirlash Imkoniyatlari:
- **⬅️ Orqaga:** Oldingi savolga qaytish (boshqa kiritilgan javoblarni saqlagan holda).
- **⏭ O‘tkazib yuborish:** Ixtiyoriy savollarni o‘tkazib yuborish.
- **❌ Bekor qilish:** Istalgan vaqtda jarayonni bekor qilish.
- **👀 Yakuniy Preview:** Barcha savollar tugagach, guruhga chiqadigan e’lonning to‘liq matni va yuklangan rasmlar foydalanuvchiga ko‘rsatiladi.
- **✏️ Ma’lumotlarni tahrirlash:** E’lon yuborilishidan oldin istalgan maydonni tanlab qayta tahrirlash mumkin.

### 3. Ma’muriy Narx Belgilash va To‘lov Jarayoni:
- Foydalanuvchi `/start` bosganda darhol karta yoki to‘lov talab qilinmaydi.
- Ma’lumotlar to‘liq yig‘ilib, foydalanuvchi tasdiqlagachgina adminga `AWAITING_PRICE` holatida yuboriladi.
- Admin narx belgilagandan so‘ng foydalanuvchiga shaxsiy xabar orqali to‘lov rekvizitlari yuboriladi.
- Foydalanuvchi to‘lov chekini (rasm yoki PDF) yuboradi (`RECEIPT_SUBMITTED`).
- Admin chekni tasdiqlagach (`PAYMENT_APPROVED`), reklama avtomatik ravishda belgilangan guruhga `#reklama` tegi bilan chop etiladi va status `PUBLISHED` ga o‘zgaradi.
- Bot qayta ishga tushganda (restart) barcha to‘xtab qolgan ishlar va ma’lumotlar avtomatik tiklanadi.

