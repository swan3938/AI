import os
keys = ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_ENCRYPT_KEY", "FEISHU_VERIFICATION_TOKEN"]
print({k: bool(os.getenv(k)) for k in keys})
