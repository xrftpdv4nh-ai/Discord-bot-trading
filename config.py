import os

# Discord Bot Token (محطوط في Railway Variables)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin IDs (حط ID حسابك هنا)
ADMIN_IDS = [
    123456789012345678
]

# Trading Settings
MIN_BET = 5000
MAX_BET = 100000

BASE_WIN_RATE = 0.55
COOLDOWN_SECONDS = 60
BIG_TRADE_AMOUNT = 50000
