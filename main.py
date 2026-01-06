from fastapi import FastAPI, Request, HTTPException, Header
from jose import jwt, JWTError
from datetime import datetime, timedelta
import hashlib
import requests

app = FastAPI()

# ضع هذه القيم في Environment Variables على Railway (مهم جداً للأمان)
BOT_TOKEN = "8476333752:AAF9uvZ6j7K_kt9hF-1mM5vBK4eN74p1PRk"  # غيّر هذا إلى env var
GROUP_ID = -1003624792891                                        # غيّر هذا إلى env var
WEB_SECRET = "SOLVIX0_ULTRA_SECRET_PLEASE_CHANGE_THIS"           # غيّر هذا إلى سر قوي وطويل!

def is_member(user_id: int) -> bool:
    """التحقق من عضوية المستخدم في المجموعة"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
        response = requests.get(url, params={"chat_id": GROUP_ID, "user_id": user_id}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            status = data.get("result", {}).get("status")
            return status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"خطأ في التحقق من العضوية: {e}")
    return False

@app.get("/")
def home():
    return {"message": "Solvix0 Auth Server جاهز ويعمل ✅"}

@app.post("/tg-login")
async def tg_login(request: Request):
    """
    Endpoint لتسجيل الدخول عبر Telegram
    يتوقع JSON مثل: {"uid": 123456789}
    """
    try:
        body = await request.json()
        uid = body.get("uid")
        
        if not uid:
            raise HTTPException(status_code=400, detail="uid مطلوب")
        
        uid = int(uid)

        # التحقق من العضوية في المجموعة
        if not is_member(uid):
            raise HTTPException(status_code=403, detail="غير مسموح: يجب أن تكون عضواً في المجموعة")

        # توليد معرف الجهاز بناءً على IP + user_id
        client_ip = request.client.host
        device_id = hashlib.sha256(f"{uid}|{client_ip}".encode()).hexdigest()

        # إنشاء JWT صالح لـ 72 ساعة
        payload = {
            "u": uid,
            "d": device_id,
            "exp": datetime.utcnow() + timedelta(hours=72)
        }
        token = jwt.encode(payload, WEB_SECRET, algorithm="HS256")

        return {"token": token}

    except ValueError:
        raise HTTPException(status_code=400, detail="uid غير صالح")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="خطأ داخلي")

@app.post("/auth/verify")
async def verify_token(authorization: str = Header(None)):
    """
    التحقق من صحة التوكن
    يتوقع Header: Authorization: Bearer <token>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="توكن مفقود أو غير صالح")

    token = authorization.replace("Bearer ", "")

    try:
        jwt.decode(token, WEB_SECRET, algorithms=["HS256"])
        return {"ok": True}
    except JWTError:
        raise HTTPException(status_code=401, detail="توكن غير صالح أو منتهي الصلاحية")
