from imports import *

try:
    id_pattern = re.compile(r"^.\d+$")

    # Bot Information
    API_ID = int(os.environ.get("API_ID", "15479023"))
    API_HASH = os.environ.get("API_HASH", "f8f6cf547822449c29fc60dae3b31dd4")
    SESSION_STRING = os.environ.get("SESSION_STRING", "BQDsMO8AmFb6JbgFyK7jiJtXcx3AFBuboExTZHINbxsl8_YzR0HaeAI5_BnsfUv_vN-vrB8NvarvyBvTRb80QQsTUuCahomUwfyd4lYuGyiQ3olZsxvJ-jKg_5XvfMN6DalcD2zNuWGf-FvvTeH_-t8QMcAPXpDxyt97bYsBIBtQAoTDpHu5bqf0h6XphvYAnYPBWLluo6VASKQJ2FsxPQfV0pEflImcLKiakUFNzA5Sn0AX6ZzRbP9gmGvKJg5L4aOD7SmYwaDhm6N7xR4p8jtpx4zszlxriOQB_lCjywawyWw-_O01f0roGKph7TGLkSEr_uJ0asKkJAyIQ3yDiJ751R51JwAAAABaJgrVAA")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8459663050:AAHlICH3sLKfmoBkM5IzzApJOkhzJohQqcU")
    BOT_USERNAME = os.environ.get("BOT_USERNAME", "XclusiveMembershipBot") # without @

    # Database Information
    DB_URI = os.environ.get("DB_URI", "mongodb+srv://KM-Membership:KM-Membership123@km-membership.8xbdxy0.mongodb.net/?retryWrites=true&w=majority&appName=KM-Membership")
    DB_NAME = os.environ.get("DB_NAME", "membership")

    # Moderator Information
    ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in os.environ.get("ADMINS", "1512442581").split()]

    # Channel Information
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1002937162790"))

    # This Is Force Subscribe Channel, also known as Auth Channel 
    auth_channel = os.environ.get("AUTH_CHANNEL", "-1002829948273") # give your force subscribe channel id here else leave it blank
    AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else None
except Exception as e:
    print("⚠️ Error loading config.py:", e)
    traceback.print_exc()
