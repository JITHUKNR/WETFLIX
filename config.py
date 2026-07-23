import os

# ബോട്ടിന്റെ ടോക്കണും മറ്റ് വിവരങ്ങളും ഇവിടെ സുരക്ഷിതമായി സൂക്ഷിക്കുന്നു
BOT_TOKEN = os.environ.get("BOT_TOKEN", "നിങ്ങളുടെ_ടോക്കൺ")
MONGO_URI = os.environ.get("MONGO_URI", "നിങ്ങളുടെ_മൊംഗോ_ലിങ്ക്")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456789)) # താങ്കളുടെ ഐഡി
PORT = int(os.environ.get("PORT", 5000))
