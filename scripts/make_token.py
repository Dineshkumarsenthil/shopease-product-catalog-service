import sys
import time

import jwt

from app.core.config import settings

role = sys.argv[1]
user_id = sys.argv[2] if len(sys.argv) > 2 else "1"
payload = {"sub": user_id, "role": role, "exp": int(time.time()) + 3600}
print(jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm))