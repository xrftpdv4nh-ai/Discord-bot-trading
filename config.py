import os

# Discord Bot Token (محطوط في Railway Variables)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin IDs (حط ID حسابك هنا)
ADMIN_IDS = [
    802148738939748373
]

# Trading Settings
MIN_BET = 5000
MAX_BET = 100000

BASE_WIN_RATE = 0.55
COOLDOWN_SECONDS = 60
BIG_TRADE_AMOUNT = 50000


# ================== Deposit / Wallet Settings ==================

# الرول اللي يقدر يقبل ويرفض
ADMIN_ROLE_ID = 1292973462091989155

# الروم اللي بيروحله طلب الإيداع (قبول / رفض)
ADMIN_ACTION_CHANNEL_ID = 1293008901142351952

# روم اللوج
LOG_CHANNEL_ID = 1293146723417587763

# صاحب حساب ProBot
PROBOT_OWNER_ID = 802148738939748373

# ================== Payment Numbers ==================

VODAFONE_NUMBER = "01009137618"
INSTAPAY_NUMBER = "01124808116"

# ================== Deposit Data ==================
DATA_FILE = "data/deposits.json"

PROBOT_ID = 802148738939748373
