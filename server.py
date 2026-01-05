from fastapi import FastAPI, Request, HTTPException
from jose import jwt
from datetime import datetime, timedelta
import hashlib, requests

app = FastAPI()

BOT_TOKEN = "8476333752:AAF9uvZ6j7K_kt9hF-1mM5vBK4eN74p1PRk"
GROUP_ID = -1003624792891
WEB_SECRET = "SOLVIX0_ULTRA_SECRET"

def is_member(uid):
    r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember",
        params={"chat_id": GROUP_ID, "user_id": uid})
    return r.status_code==200 and r.json()["result"]["status"] in ["member","administrator","creator"]

@app.post("/tg-login")
async def tg_login(req: Request):
    uid = (await req.json()).get("uid")
    if not uid or not is_member(uid):
        raise HTTPException(403)

    dev = hashlib.sha256(f"{uid}|{req.client.host}".encode()).hexdigest()
    token = jwt.encode({
        "u": uid,
        "d": dev,
        "exp": datetime.utcnow()+timedelta(hours=72)
    }, WEB_SECRET, algorithm="HS256")

    return {"token": token}

@app.post("/auth/verify")
async def verify(req: Request):
    token = req.headers.get("Authorization","").replace("Bearer ","")
    try:
        jwt.decode(token, WEB_SECRET, algorithms=["HS256"])
        return {"ok": True}
    except:
        raise HTTPException(401)
