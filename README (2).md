# CITY BUILDER 3D MVP

## 1. Papka tuzilishi

Fayllarni quyidagicha joylashtiring:

```text
city-builder/
  app.py
  requirements.txt
  .env
  templates/index.html
  static/app.js
  static/style.css
```

## 2. O'rnatish

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Brauzerda `http://localhost:5000` oching.

## 3. MongoDB

MongoDB Atlas cluster yarating, database user va Network Access sozlang. `.env` faylida:

```env
MONGO_URI=mongodb+srv://USER:PASSWORD@CLUSTER.mongodb.net/?retryWrites=true&w=majority
BOT_TOKEN=TelegramBotFather bergan bot token
DEV_MODE=true
```

Local testda `DEV_MODE=true` bo'lsa, Telegram initData bo'lmasa Developer user ishlatiladi. Production’da albatta `DEV_MODE=false` qiling.

## 4. Telegram Mini App

BotFather’da Web App URL sifatida Render URL’ini qo‘ying. URL HTTPS bo‘lishi kerak. `BOT_TOKEN` aynan Mini App ochiladigan bot tokeni bo‘lsin.

## 5. Render

Repository root’iga fayllarni joylang. Render’da Web Service tanlang:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

Environment Variables:

```text
BOT_TOKEN=...
MONGO_URI=...
MONGO_DB=city_builder
DEV_MODE=false
```

## 6. MVP boshqaruvi

- Sichqoncha yoki touch bilan kamera aylantiriladi.
- BUILD bosiladi.
- Bino tanlanadi.
- Terrain ustidagi bo'sh joy bosiladi.
- Server coin, level va collision tekshiradi.
- COLLECT passiv income’ni server vaqti orqali hisoblaydi.
- UPGRADE oxirgi qurilgan binoni upgrade qiladi.

Ushbu MVP 3D procedural low-poly mesh ishlatadi: modellar emoji yoki 2D rasm emas. Keyingi bosqichda procedural obyektlarni GLB assetlar bilan almashtirish mumkin.
