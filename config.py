import os

# ===================== BOT =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ===================== MONGODB =====================
MONGO_URL = os.getenv("MONGO_URL")
MONGO_DB_NAME = "trono_trade"

# ===================== ADMINS =====================
ADMIN_IDS = [
    802148738939748373
]

# ===================== ROLES =====================
ADMIN_ROLE_ID = 1292973462091989155
SUPPORT_ROLE_ID = 1468746308780294266

# ===================== CHANNELS =====================
DEPOSIT_CHANNEL_ID = 1292971040489603156
TRADE_CHANNEL_ID = 1292970481976217732
LOG_CHANNEL_ID = 1293146723417587763
ROLE_LOG_CHANNEL_ID = 1293146723417587763

# ===================== PROBOT SETTINGS =====================
PROBOT_ID = 282859044593598464  # ID بروبوت الرسمي
PROBOT_RECEIVER_ID = 1035345058561540127  # الحساب اللي هيستلم الكريدت
PROBOT_FEE_RATE = 0.05  # 20% رسوم بروبوت
DEPOSIT_TIMEOUT = 5  # مدة انتظار التحويل بالدقائق

# ===================== TRADING SETTINGS =====================
MIN_BET = 5000
MAX_BET = 100000
BASE_WIN_RATE = 0.55
COOLDOWN_SECONDS = 60
BIG_TRADE_AMOUNT = 50000
