import os

# ===================== BOT =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ===================== MONGODB =====================
# حط رابط مونجو في متغير بيئة باسم MONGO_URL
MONGO_URL = os.getenv("MONGO_URL")

# اسم قاعدة البيانات (تقدر تغيره لو حابب)
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
ADMIN_ACTION_CHANNEL_ID = 1293008901142351952
LOG_CHANNEL_ID = 1293146723417587763
ROLE_LOG_CHANNEL_ID = 1293146723417587763

# ===================== PAYMENTS =====================
VODAFONE_NUMBER = "01009137618"
INSTAPAY_NUMBER = "01124808116"

# ===================== PROBOT =====================
PROBOT_ID = 802148738939748373
PROBOT_OWNER_ID = 802148738939748373
PROBOT_FEE_RATE = 0.053  # 5.3%

# ===================== TRADING SETTINGS =====================
MIN_BET = 5000
MAX_BET = 100000
BASE_WIN_RATE = 0.55
COOLDOWN_SECONDS = 60
BIG_TRADE_AMOUNT = 50000

# ===================== DATA FILES =====================
DATA_FILE = "data/deposits.json"
