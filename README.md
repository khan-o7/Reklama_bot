# 🛡️ Telegram Defender Bot — Professional Reklama va Spamga Qarshi Bot

**Defender Bot** — Telegram guruhlarida reklama, spam, tijoriy e'lonlar, ruxsat etilmagan havolalar va kanallarni real vaqt rejimida aniqlaydigan, o‘chiradigan, ogohlantirish beradigan, qoidabuzarlarni jazolaydigan (mute/ban) va administratorga to‘liq hisobot yuboradigan professional Telegram bot tizimi.

Ushbu loyiha **Python 3.12+**, **Aiogram 3.x**, **SQLAlchemy 2.x (asyncpg)**, **PostgreSQL**, **Alembic**, **FastAPI (Web Admin Panel)** va **Docker** asosida to‘liq production darajasida ishlab chiqilgan.

---

## 📋 MUNDARIJA

1. [Asosiy imkoniyatlar](#-asosiy-imkoniyatlar)
2. [Loyiha tuzilishi (Architecture)](#-loyiha-tuzilishi)
3. [Reklamani aniqlash algoritmi va Scoring](#-reklamani-aniqlash-algoritmi)
4. [Oq va Qora ro‘yxat (Whitelist & Blacklist)](#-oq-va-qora-royxat)
5. [Bosqichma-bosqich jazo choralari (Escalation)](#-bosqichma-bosqich-jazo-choralari)
6. [BotFather orqali botni sozlash (Privacy Mode va Huquqlar)](#-botfather-orqali-botni-sozlash)
7. [O‘rnatish va Ishga tushirish (Windows Server & Mahalliy)](#-windows-serverda-ornatish-va-ishga-tushirish)
8. [O‘rnatish va Ishga tushirish (Ubuntu VPS / Linux)](#-ubuntu-vps-da-ornatish-va-ishga-tushirish)
9. [Systemd Servis orqali ishga tushirish (Linux)](#-systemd-servis-sozlash-linux)
10. [Docker va Docker Compose orqali ishga tushirish](#-docker-orqali-ishga-tushirish)
11. [Web Admin Panel](#-web-admin-panel)
12. [Bot Buyruqlari (Commands)](#-bot-buyruqlari)
13. [Testlarni ishga tushirish (Pytest)](#-testlarni-ishga-tushirish)
14. [Muammolarni bartaraf etish (Troubleshooting)](#-troubleshooting)

---

## ✨ ASOSIY IMKONIYATLAR

- ⚡ **Real vaqt rejimidagi monitoring:** Guruhdagi barcha xabarlar (matn, rasm, video, hujjat, GIF/animatsiya, ovozli xabar) soniyalar ichida tekshiriladi.
- 🎯 **Multi-faktorli Scoring tizimi:** Faqatgina havolani ko‘rib xulosa qilmaydi; kalit so‘zlar, telefon raqamlar, tashqi kanallar, chegirmalar va havolalarni birgalikda tahlil qilib umumiy ball hisoblaydi.
- 🛡️ **Oq ro‘yxat (Whitelist):** Davlat saytlari (`gov.uz`, `my.gov.uz`), ta'lim portallari (`edu.uz`) kabi zarur saytlar avtomatik oq ro‘yxatga olingan va reklama sifatida belgilanmaydi.
- 🚫 **Qora ro‘yxat (Blacklist):** Taqiqlangan so‘zlar, bukmekerlik saytlari, spam domenlar yoki username'lar kiritilsa, bot ularni zudlik bilan 100 ball bilan o‘chiradi.
- 👨‍💼 **Original kontentni saqlab adminga yuborish:** Reklama guruhdan o‘chirilgach, uning asl holati (media, matn, caption, jo‘natuvchi ma’lumotlari, chat ID va aniqlash sabablari) bot administratorlariga yuboriladi.
- ⚠️ **Avtomatik ogohlantirish:** Qoidabuzarga guruhda ogohlantirish beriladi va uning ostida administrator profiliga eltuvchi **"👨‍💼 Adminga murojaat qilish"** inline tugmasi joylashtiriladi.
- ⏱️ **Ogohlantirishni avtomatik o‘chirish:** Guruhda ortiqcha xabarlar to‘planib qolmasligi uchun ogohlantirish belgilangan vaqtdan (masalan, 15 soniya) so‘ng o‘chiriladi.
- ⚖️ **Avtomatlashtirilgan jazo eskalatsiyasi:**
  - 1-marta: Ogohlantirish
  - 2-marta: 10 daqiqa MUTE
  - 3-marta: 1 soat MUTE
  - 4-marta: Guruhdan BAN
- 📊 **Web Dashboard:** Guruhlar, a’zolar, haftalik grafik, o‘chirilgan reklamalar statistikasi, sozlamalar va audit jurnali.

---

## 📁 LOYIHA TUZILISHI

```
Defender bot/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Bot va Web serverning asosiy kirish nuqtasi
│   ├── web_main.py              # Mustaqil FastAPI Web Admin kirish nuqtasi
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py          # Pydantic Settings (.env konfiguratsiyasi)
│   ├── database/
│   │   ├── __init__.py
│   │   ├── database.py          # Async SQLAlchemy 2.0 sessiya va ulanish
│   │   ├── models/              # Barcha jadvallar modellari
│   │   │   ├── user.py          # users jadvali
│   │   │   ├── group.py         # groups jadvali
│   │   │   ├── advertisement.py # advertisements jadvali
│   │   │   ├── warning.py       # warnings jadvali
│   │   │   ├── list_item.py     # blacklist & whitelist jadvallari
│   │   │   ├── setting.py       # settings jadvali
│   │   │   ├── audit_log.py     # audit_logs jadvali
│   │   │   └── admin_user.py    # admin_users jadvali
│   │   └── repositories/        # SQL ma'lumotlar ombori (CRUD)
│   ├── bot/
│   │   ├── loader.py            # Bot va Dispatcher yaratish
│   │   ├── handlers/
│   │   │   ├── start.py         # /start va /help
│   │   │   ├── admin.py         # /status, /stats, /whitelist, /blacklist, /mute, /ban, va h.k.
│   │   │   ├── moderation.py    # Guruh xabarlarini real vaqtda kuzatish
│   │   │   └── group_events.py  # Guruhga qo'shilish va huquqlarni tekshirish
│   │   ├── filters/             # Admin va chat turlari filtrlari
│   │   ├── keyboards/           # Inline tugmalar (ogohlantirish va admin menyu)
│   │   └── middlewares/         # Database, Rate Limiting va Error Handling
│   ├── services/
│   │   ├── advertisement_detector.py # Reklama aniqlash va scoring tizimi
│   │   ├── moderation_service.py     # Xabarni o'chirish, jazo va ogohlantirish berish
│   │   ├── notification_service.py   # Adminga alert yuborish
│   │   ├── cache_service.py          # Tezkor xotira keshi (0ms javob qaytarish)
│   │   └── statistics_service.py     # Statistika hisoblash
│   ├── utils/
│   │   ├── logger.py            # Console va aylanuvchi fayl logi (logs/bot.log)
│   │   ├── text_utils.py        # Matn tozalash, krill-lotin transliteratsiya
│   │   └── link_parser.py       # URL, Telegram havolalari va domen ajratish
│   └── web/                     # FastAPI Web Admin Panel
│       ├── app.py               # FastAPI factory
│       ├── auth.py              # Bcrypt va JWT cookie avtorizatsiya
│       ├── routes/              # View va API marshrutlari
│       └── templates/           # Jinja2 HTML andozalari (Tailwind CSS)
├── alembic/                     # Database migratsiyalari
├── tests/                       # Pytest unit testlar
├── .env.example                 # Sozlamalar namunasi
├── requirements.txt             # Kerakli kutubxonalar
├── Dockerfile                   # Docker konteyner qurish fayli
├── docker-compose.yml           # Bot + Postgres + Web Admin
├── alembic.ini                  # Alembic konfiguratsiyasi
└── README.md                    # Loyiha qo'llanmasi
```

---

## 🎯 REKLAMANI ANIQLASH ALGORITMI

Bot xabarni bir nechta parametr bo‘yicha tahlil qiladi va umumiy ball (score) hisoblaydi:

| Parametr / Sabab | Ball | Tavsif |
| :--- | :--- | :--- |
| **Tashqi havola (URL)** | **+40** | Xabarda URL yoki text_link bo‘lsa (oq ro‘yxatdagilardan tashqari) |
| **"reklama" so‘zi** | **+40** | Aniq reklama ekanligi ta'kidlangan xabarlar |
| **"sotiladi", "sotamiz"** | **+20** | Savdo va tijoriy e'lonlar |
| **"aksiya", "chegirma", "skidka"** | **+20** | Rag‘batlantiruvchi tijoriy takliflar |
| **"admin bilan bog‘laning"** | **+25** | Shaxsiy profilga yo‘naltirish |
| **"obuna bo‘ling", "kanalimizga"** | **+25** | Guruh/kanal auditoriyasini o‘g‘irlash |
| **Telefon raqam** | **+15** | O‘zbekiston va xalqaro telefon raqamlari |
| **Telegram username / mention** | **+20** | `@kanal` yoki tashqi profil chaqiruvlari |
| **"zakaz", "buyurtma", "dostavka"**| **+15** | Xizmat ko‘rsatish va buyurtma taklifi |
| **Qora ro‘yxatdagi element** | **100** | Qora ro‘yxatdagi so‘z/domen/username topilsa, darhol o‘chiriladi |

- **Chegara (Threshold):** Odatiy holatda **40 ball**. Agar xabar 40 yoki undan yuqori ball to‘plasa, u reklama deb hisoblanadi.
- **False Positive (Xato aniqlash) himoyasi:**
  - *"Telefonim buzilib qoldi"* — 40 balldan past, o‘chirilmaydi.
  - *"Bugun gov.uz saytidan ma'lumot oldim"* — havola oq ro‘yxatda, ball = 0, o‘chirilmaydi.
  - *"Bugun soat 18:00 da yig‘ilish bo‘ladi"* — tijoriy kontekst yo‘q, o‘chirilmaydi.

---

## 🛡️ OQ VA QORA RO‘YXAT

### Oq ro‘yxat (Whitelist)
Standart ruxsat etilgan domenlar:
- `gov.uz`
- `edu.uz`
- `customs.uz`
- `my.gov.uz`
- `lex.uz`
- `dtm.uz`

Admin yangi domen qo‘shishi yoki o‘chirishi mumkin:
```bash
/whitelist add myschool.uz
/whitelist del myschool.uz
```

### Qora ro‘yxat (Blacklist)
Taqiqlangan so‘z, domen yoki kanallarni qo‘shish:
```bash
/blacklist add word 1xbet
/blacklist add domain spamlink.org
/blacklist add username spambot_official
/blacklist del 1xbet
```

---

## ⚖️ BOSQICHMA-BOSQICH JAZO CHORALARI

Har bir foydalanuvchi bo‘yicha ogohlantirishlar soni database'da saqlanadi:
- **1-marta:** Guruhda ogohlantirish beriladi.
- **2-marta:** Ogohlantirish + **10 daqiqa MUTE** (yozish huquqidan mahrum qilish).
- **3-marta:** Ogohlantirish + **1 soat MUTE**.
- **4-marta:** Guruhdan to‘liq **BAN** (chetlatish).

*(Bu choralar `.env` yoki Web Admin panel orqali moslashtirilishi mumkin).*

---

## 🤖 BOTFATHER ORQALI BOTNI SOZLASH

### 1. Bot yaratish va Token olish
1. Telegramda [@BotFather](https://t.me/BotFather) botiga kiring.
2. `/newbot` buyrug‘ini bering.
3. Botga nom va username bering (masalan: `my_ad_defender_bot`).
4. BotFather sizga bergan **API Tokenni** nusxalab oling (masalan: `7123456789:ABC...`).

### 2. Privacy Mode sozlash (MUHIM!)
⚠️ **Telegram cheklovi:** Odatiy holatda botlar guruhdagi barcha xabarlarni ko‘ra olmaydi. Reklamani to‘g‘ri aniqlashi uchun Privacy Mode'ni o‘chirish shart:
1. [@BotFather](https://t.me/BotFather) ga `/mybots` deb yozing.
2. O‘z botingizni tanlang.
3. **Bot Settings** &rarr; **Group Privacy** bo‘limiga kiring.
4. **Turn off** tugmasini bosing (Natijada: *"Privacy mode is disabled"* bo‘lishi kerak).

### 3. Botni guruhga qo‘shish va Administrator qilish
1. Botni guruhingizga a’zo qilib qo‘shing.
2. Guruh sozlamalariga kirib, botni **Administrator** etib tayinlang.
3. Botga quyidagi huquqlarni bering:
   - ✅ **Delete Messages** (Xabarlarni o‘chirish) — *Majburiy*
   - ✅ **Ban Users** / **Restrict Members** (Foydalanuvchilarni cheklash/haydash) — *Majburiy*

---

## 💻 WINDOWS SERVERDA O‘RNATISH VA ISHGA TUSHIRISH

### 1. Python o‘rnatish
- [Python 3.12+](https://www.python.org/downloads/) rasmiy saytidan yuklab oling.
- O‘rnatish jarayonida **"Add python.exe to PATH"** katakchasini belgilang.

### 2. Loyihani yuklash va virtual environment yaratish
Windows Terminal yoki PowerShell orqali loyiha papkasiga o‘ting:
```powershell
cd "d:\10.PROYEKTLAR\Defender bot"

# Virtual muhit yaratish
python -m venv venv

# Virtual muhitni faollashtirish
.\venv\Scripts\activate
```

### 3. Kutubxonalarni o‘rnatish
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. .env faylini sozlash
`.env.example` faylidan nusxa olib `.env` yarating:
```powershell
copy .env.example .env
```
`.env` faylini Notepad yoki o‘zingiz yoqtirgan muharrirda oching va quyidagi o‘zgaruvchilarni to‘ldiring:
```env
BOT_TOKEN=7123456789:AAH...
OWNER_ID=123456789
ADMINS=123456789,987654321
ADMIN_USERNAME=sizning_admin_usernamingiz
DATABASE_URL=postgresql+asyncpg://postgres:parol@localhost:5432/defender_bot
```

### 5. PostgreSQL o‘rnatish va bazani yaratish
PostgreSQL o‘rnatilganidan so‘ng, `psql` yoki pgAdmin orqali baza oching:
```sql
CREATE DATABASE defender_bot;
```

### 6. Database Migratsiyalari (Alembic)
Jadvallarni PostgreSQL bazasida yaratish uchun:
```powershell
alembic upgrade head
```

### 7. Botni ishga tushirish
```powershell
python -m app.main
```
Konsolda quyidagi xabarni ko‘rasiz:
```
2026-10-04 18:45:21 | INFO    | Initializing Defender Bot and PostgreSQL Database...
2026-10-04 18:45:22 | INFO    | Database initialized successfully.
2026-10-04 18:45:22 | INFO    | Bot started | @my_defender_bot (ID: 7123456789)
2026-10-04 18:45:22 | INFO    | Web Admin Panel available at: http://localhost:8000
```

---

## 🐧 UBUNTU VPS DA O‘RNATISH VA ISHGA TUSHIRISH

### 1. Tizim paketlarini yangilash va o‘rnatish
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git postgresql postgresql-contrib
```

### 2. PostgreSQL bazasini sozlash
```bash
sudo -u postgres psql
```
PostgreSQL ichida:
```sql
CREATE DATABASE defender_bot;
CREATE USER botuser WITH PASSWORD 'KuchliParol123!';
GRANT ALL PRIVILEGES ON DATABASE defender_bot TO botuser;
ALTER DATABASE defender_bot OWNER TO botuser;
\q
```

### 3. Loyiha kodini joylashtirish va venv yaratish
```bash
cd /opt
sudo mkdir -p defender_bot
sudo chown -R $USER:$USER /opt/defender_bot
cd /opt/defender_bot

# Virtual muhit
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. .env sozlash
```bash
cp .env.example .env
nano .env
```
Bazaga ulanish:
```env
DATABASE_URL=postgresql+asyncpg://botuser:KuchliParol123!@localhost:5432/defender_bot
```

### 5. Migratsiya va ishga tushirish
```bash
alembic upgrade head
python3 -m app.main
```

---

## ⚙️ SYSTEMD SERVIS SOZLASH (LINUX)

Bot server qayta yuklanganda (reboot) avtomatik ishga tushishi va to‘xtab qolmasligi uchun `systemd` servis yarating:

```bash
sudo nano /etc/systemd/system/defender_bot.service
```

Quyidagi konfiguratsiyani kiriting:
```ini
[Unit]
Description=Telegram Ad Defender Bot Service
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/defender_bot
ExecStart=/opt/defender_bot/venv/bin/python3 -m app.main
Restart=always
RestartSec=5
EnvironmentFile=/opt/defender_bot/.env

[Install]
WantedBy=multi-user.target
```

Servisni faollashtiring va ishga tushiring:
```bash
sudo systemctl daemon-reload
sudo systemctl enable defender_bot
sudo systemctl start defender_bot

# Holatini tekshirish
sudo systemctl status defender_bot

# Loglarni jonli kuzatish
journalctl -u defender_bot -f
```

---

## 🐳 DOCKER ORQALI ISHGA TUSHIRISH

Loyiha to‘liq Docker va Docker Compose bilan ta'minlangan. PostgreSQL va Python muhiti alohida konteynerlarda avtomatik ko‘tariladi.

### 1. .env faylini tayyorlang
`.env` faylida token va admin ID laringizni to‘g‘rilang.

### 2. Konteynerlarni ishga tushirish
```bash
docker compose up -d --build
```

### 3. Ishini tekshirish
```bash
docker compose ps
docker compose logs -f bot
```

Bu holatda:
- `defender_bot_postgres`: PostgreSQL bazasi (ma'lumotlar `postgres_data` hajmida saqlanadi).
- `defender_bot_worker`: Telegram bot xabarlarni kuzatuvchi asosiy jarayon.
- `defender_bot_web_admin`: Web Admin boshqaruv paneli (`http://SERVER_IP:8000`).

---

## 🌐 WEB ADMIN PANEL

Loyiha bilan birga zamonaviy **FastAPI + Jinja2 + Tailwind CSS** asosidagi Web Admin Panel keladi:
- **Manzil:** `http://localhost:8000` (yoki serveringiz IP manzili: `http://SERVER_IP:8000`)
- **Standart login:** `admin`
- **Standart parol:** `admin12345` *(buni `.env` faylidagi `WEB_ADMIN_PASSWORD` orqali o‘zgartiring)*

### Web Paneldagi sahifalar:
1. **Dashboard:** Oxirgi 7 kunlik reklamalar grafigi (Chart.js), jami guruhlar, jami a’zolar, bugungi o‘chirilgan xabarlar, mute va ban qilinganlar soni.
2. **Guruhlar:** Bot ulangan guruhlar ro‘yxati va holati.
3. **Foydalanuvchilar:** A’zolar, ularning ogohlantirishlar soni va jazo holatlari.
4. **Reklamalar:** Barcha aniqlangan reklamalar, ularning balli, sabablari va xabar turi.
5. **Oq va Qora ro‘yxat:** Domen va so‘zlarni qo‘shish va o‘chirish.
6. **Sozlamalar:** Reklamani o‘chirish, mute/ban vaqtlarini interaktiv o‘zgartirish.
7. **Audit Loglar:** Xavfsizlik va ma'muriy hodisalar tarixi.

---

## 🕹️ BOT BUYRUQLARI

Faqat bot adminlari va guruh administratorlari ushbu buyruqlardan foydalana oladi. Oddiy a’zolar yozsa:
`❌ Sizda bu buyruqdan foydalanish huquqi yo‘q.` xabari qaytadi.

| Buyruq | Tavsif |
| :--- | :--- |
| `/start` | Botni ishga tushirish va asosiy boshqaruv menyusi |
| `/help` | Barcha buyruqlar bo‘yicha qo‘llanma |
| `/status` | Botning hozirgi holati, guruhlar soni, tekshirilgan xabarlar va baza holati |
| `/stats` | Bugungi, haftalik va oylik batafsil reklama statistikasi |
| `/settings` | Guruh yoki botning amaldagi sozlamalari |
| `/users` | Eng ko‘p reklama tarqatgan qoidabuzarlar ro‘yxati |
| `/whitelist` | Oq ro‘yxatdagi domenlarni ko‘rish, qo‘shish (`add`) yoki o‘chirish (`del`) |
| `/blacklist` | Qora ro‘yxatni ko‘rish, qo‘shish (`add`) yoki o‘chirish (`del`) |
| `/warnings` | Foydalanuvchining ogohlantirishlarini tekshirish (reply qilib) |
| `/mute [daqiqa]` | Qoidabuzarni belgilangan daqiqaga yozishdan cheklash (reply qilib) |
| `/unmute` | Foydalanuvchidan cheklovni yechish |
| `/ban` | Qoidabuzarni guruhdan butunlay chetlatish |
| `/unban` | Foydalanuvchini bandan chiqarish |
| `/logs` | Oxirgi audit hodisalari jurnali |

---

## 🧪 TESTLARNI ISHGA TUSHIRISH

Loyiha uchun to‘liq unit testlar to‘plami yozilgan. Ular URL aniqlash, so‘zlar, telefon raqamlar, oq ro‘yxat, qora ro‘yxat va noto‘g‘ri aniqlashlarning oldini olishni tekshiradi.

Testlarni ishga tushirish:
```powershell
pytest -v
```

---

## 🔧 TROUBLESHOOTING

1. **Bot guruhdagi xabarlarni ko‘rmayapti:**
   - [@BotFather](https://t.me/BotFather) orqali `Group Privacy` rejimini `Disabled` holatiga o‘tkazing.
   - Botni guruhdan chiqarib, qayta qo‘shing va Administrator huquqini bering.

2. **Bot xabarlarni o‘chira olmayapti:**
   - Botning guruhdagi administrator huquqlarida **Delete messages** yoqilganligini tekshiring.

3. **`TelegramRetryAfter` yoki Flood xatosi:**
   - Bot avtomatik ravishda `retry_after` soniyasini kutadi va qayta urinib ko‘radi. Tizimda bu xatolar xavfsiz ushlanadi.

4. **Web Admin panel ochilmayapti:**
   - Serverdagi xavfsizlik devorida (Firewall / UFW) 8000-port ochiqligini tekshiring: `sudo ufw allow 8000/tcp`.
