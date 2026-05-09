from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager, closing
from pydantic import BaseModel
from typing import Optional
import json
import httpx
import asyncio
import sqlite3
import os
import datetime
import calendar
import imaplib
import email
import email.header
import icalendar
import recurring_ical_events
import hashlib
import unicodedata
import html
import re
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "dashboard.db")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
STATIC_DIR = os.path.join(BASE_DIR, "static")

DEFAULT_CONFIG = {
    "clock": {"font": "Pretendard", "color": "#00ff88", "separator": "colon", "notation": "24h"},
    "weather": {"city": "Pohang", "font": "Pretendard", "color": "#ffffff", "api_key": ""},
    "notifications": {"colors": {"CHZZK": "#00ff88", "YOUTUBE": "#ff0000", "GMAIL": "#ea4335", "SYSTEM": "#aaaaaa"}},
    "gmail": {"email": "", "app_password": ""},
    "calendar": {"ical_url": "", "keywords": {}}
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        user_config = json.load(f)
    
    needs_save = False
    for k, v in DEFAULT_CONFIG.items():
        if k not in user_config:
            user_config[k] = v; needs_save = True
        elif isinstance(v, dict):
            for sub_k, sub_v in v.items():
                if sub_k not in user_config[k]:
                    user_config[k][sub_k] = sub_v; needs_save = True
    if needs_save: save_config(user_config)
    return user_config

def save_config(config_data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=4)

def decode_mime_words(s):
    if not s: return ""
    decoded_words = email.header.decode_header(s)
    result = []
    for word, encoding in decoded_words:
        if isinstance(word, bytes): result.append(word.decode(encoding or 'utf-8', errors='ignore'))
        else: result.append(word)
    return "".join(result)

def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS notifications 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, border_color TEXT, bg_color TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS channels (channel_id TEXT PRIMARY KEY, name TEXT)''')
        
        try: c.execute("ALTER TABLE channels ADD COLUMN platform TEXT DEFAULT 'CHZZK'")
        except sqlite3.OperationalError: pass
        conn.commit()


async def poll_chzzk():
    last_live_status = {}
    while True:
        try:
            with closing(sqlite3.connect(DB_PATH)) as conn:
                c = conn.cursor()
                c.execute("SELECT channel_id, name FROM channels WHERE platform='CHZZK' OR platform IS NULL")
                channels = c.fetchall()
                async with httpx.AsyncClient() as client:
                    for channel_id, name in channels:
                        url = f"https://api.chzzk.naver.com/polling/v2/channels/{channel_id}/live-status"
                        response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                        if response.status_code == 200:
                            data = response.json()
                            current_status = data["content"]["status"]
                            if last_live_status.get(channel_id) != "OPEN" and current_status == "OPEN":
                                live_title = data["content"].get("liveTitle", "제목 없음")
                                msg = f"🟢 <b>{name}</b> 방송 시작: {live_title}"
                                c.execute("SELECT 1 FROM notifications WHERE message = ? AND source = 'CHZZK' LIMIT 1", (msg,))
                                if not c.fetchone():
                                    c.execute("INSERT INTO notifications (source, message) VALUES (?, ?)", ("CHZZK", msg))
                                    conn.commit()
                            last_live_status[channel_id] = current_status
        except: pass
        await asyncio.sleep(60)

async def poll_youtube():
    while True:
        try:
            with closing(sqlite3.connect(DB_PATH)) as conn:
                c = conn.cursor()
                c.execute("SELECT channel_id, name FROM channels WHERE platform='YOUTUBE'")
                channels = c.fetchall()
                async with httpx.AsyncClient() as client:
                    for channel_id, name in channels:
                        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
                        res = await client.get(url)
                        if res.status_code == 200:
                            root = ET.fromstring(res.text)
                            ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
                            entry = root.find('atom:entry', ns)
                            if entry is not None:
                                video_id = entry.find('yt:videoId', ns).text
                                title = entry.find('atom:title', ns).text
                                
                                c.execute("SELECT 1 FROM notifications WHERE source = 'YOUTUBE' AND message LIKE ? LIMIT 1", (f"%{video_id}%",))
                                if not c.fetchone():
                                    msg = f"🔴 <b>{name}</b> 새 영상 업로드!<br><a href='https://youtu.be/{video_id}' target='_blank'>{title}</a><span style='display:none;'>{video_id}</span>"
                                    c.execute("INSERT INTO notifications (source, message) VALUES (?, ?)", ("YOUTUBE", msg))
                                    conn.commit()
        except Exception as e: print(f"[YouTube Error] {e}")
        await asyncio.sleep(300)

def _check_imap(user, pwd):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, pwd)
        mail.select("inbox")
        status, messages = mail.search(None, '(UNSEEN)')
        if status == "OK" and messages[0]:
            msg_ids = messages[0].split()[-5:]
            with closing(sqlite3.connect(DB_PATH)) as conn:
                c = conn.cursor()
                for msg_id in reversed(msg_ids):
                    res, msg_data = mail.fetch(msg_id, '(RFC822)')
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject = decode_mime_words(msg.get("Subject", ""))
                            sender = decode_mime_words(msg.get("From", "발신자 미상")).split('<')[0].strip()
                            snippet = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain":
                                        snippet = part.get_payload(decode=True).decode('utf-8', errors='ignore'); break
                            else: snippet = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                            
                            snippet = html.escape(snippet.replace('\n', ' ').strip()[:60])
                            full_msg = f"📩 <b>{html.escape(sender)}</b>: {html.escape(subject)}<br><span style='font-size:0.85rem; color:#888;'>{snippet}</span>"
                            c.execute("SELECT 1 FROM notifications WHERE message = ? AND source = 'GMAIL' LIMIT 1", (full_msg,))
                            if not c.fetchone():
                                c.execute("INSERT INTO notifications (source, message) VALUES (?, ?)", ("GMAIL", full_msg))
                                conn.commit()
        mail.logout()
    except: pass

async def poll_gmail():
    while True:
        cfg = load_config()
        u, p = cfg["gmail"]["email"], cfg["gmail"]["app_password"]
        if u and p: await asyncio.to_thread(_check_imap, u, p)
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    asyncio.create_task(poll_chzzk())
    asyncio.create_task(poll_youtube())
    asyncio.create_task(poll_gmail())
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/api/config")
async def get_config_api(): return load_config()

@app.post("/api/config")
async def update_config_api(new_config: dict): save_config(new_config); return {"status": "success"}

@app.get("/")
async def read_index(): 
    return FileResponse(os.path.join(STATIC_DIR, 'index.html'))

@app.get("/api/notifications")
async def get_notifications():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        c = conn.cursor()
        c.execute("SELECT source, message, timestamp, border_color, bg_color FROM notifications ORDER BY id DESC LIMIT 15")
        return [{"source": r[0], "message": r[1], "timestamp": r[2], "border_color": r[3], "bg_color": r[4]} for r in c.fetchall()]

@app.get("/api/channels")
async def get_channels():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        c = conn.cursor()
        c.execute("SELECT channel_id, name, platform FROM channels")
        return [{"channel_id": r[0], "name": r[1], "platform": r[2] or "CHZZK"} for r in c.fetchall()]

@app.post("/api/channels")
async def add_channel_api(data: dict):
    channel_id = data.get("channel_id", "").strip()
    name = data.get("name", "").strip()
    platform = data.get("platform", "CHZZK").upper()

    if not channel_id or not name:
        return {"status": "error", "message": "입력값이 부족합니다."}

    if platform == "YOUTUBE" and not channel_id.startswith("UC"):
        url = channel_id
        if not url.startswith("http"):
            if not url.startswith("@"): url = f"@{url}"
            url = f"https://www.youtube.com/{url}"
        
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(url, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                
                match = re.search(r'title="RSS" href=".*?channel_id=(UC[\w-]+)"', res.text)
                
                if not match: 
                    match = re.search(r'<meta itemprop="identifier" content="(UC[\w-]+)">', res.text)
                
                if match: 
                    channel_id = match.group(1)
                else: 
                    return {"status": "error", "message": "채널 ID를 찾을 수 없습니다. 주소나 핸들을 확인해주세요."}
            except:
                return {"status": "error", "message": "유튜브 서버에 접근할 수 없습니다."}

    with closing(sqlite3.connect(DB_PATH)) as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO channels (channel_id, name, platform) VALUES (?, ?, ?)", (channel_id, name, platform))
        conn.commit()

    async def send_welcome_notification():
        try:
            msg = ""
            async with httpx.AsyncClient() as client:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                
                if platform == "YOUTUBE":
                    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
                    res = await client.get(rss_url, headers=headers)
                    if res.status_code == 200:
                        root = ET.fromstring(res.text)
                        ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
                        entry = root.find('atom:entry', ns)
                        if entry is not None:
                            video_id = entry.find('yt:videoId', ns).text
                            title = entry.find('atom:title', ns).text
                            msg = f"✅ <b>{name}</b> 채널 감시 시작!<br><span style='font-size:0.8rem; color:#888;'>최근 영상:</span> <a href='https://youtu.be/{video_id}' target='_blank'>{title}</a><span style='display:none;'>{video_id}</span>"
                        else:
                            msg = f"✅ <b>{name}</b> 채널 감시 시작! (업로드된 영상 없음)"
                
                elif platform == "CHZZK":
                    api_url = f"https://api.chzzk.naver.com/polling/v2/channels/{channel_id}/live-status"
                    res = await client.get(api_url, headers=headers)
                    if res.status_code == 200:
                        content = res.json().get("content", {})
                        if content.get("status") == "OPEN":
                            live_title = content.get("liveTitle", "제목 없음")
                            msg = f"✅ <b>{name}</b> 채널 감시 시작!<br><span style='font-size:0.8rem; color:#00ff88;'>● 현재 방송 중:</span> {live_title}"
                        else:
                            msg = f"✅ <b>{name}</b> 채널 감시 시작! (현재 오프라인)"

            if msg:
                with closing(sqlite3.connect(DB_PATH)) as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO notifications (source, message) VALUES (?, ?)", (platform, msg))
                    conn.commit()
        except Exception as e:
            print(f"[Welcome Notification Error] {e}")

    asyncio.create_task(send_welcome_notification())
    return {"status": "success", "resolved_id": channel_id}

@app.delete("/api/channels/{channel_id}")
async def delete_channel_api(channel_id: str):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        conn.commit()
    return {"status": "success"}

@app.get("/api/weather")
async def get_weather():
    cfg = load_config()
    city, key = cfg["weather"]["city"], cfg["weather"]["api_key"]
    if not key: return {"temp": 0, "description": "API 키 설정 필요", "icon": "01d", "city": city}
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}&units=metric"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url); data = res.json()
            return {"temp": round(data["main"]["temp"], 1), "description": data["weather"][0].get("main", "알 수 없음"), "icon": data["weather"][0]["icon"], "city": data.get("name", city)}
        except: return {"temp": 0, "description": "날씨 로드 실패", "icon": "01d", "city": city}

def safe_match(keyword, target):
    k = unicodedata.normalize('NFC', str(keyword)).replace(" ", "").lower()
    t = unicodedata.normalize('NFC', str(target)).replace(" ", "").lower()
    return k and (k in t)

@app.get("/api/calendar")
async def get_calendar_events():
    cfg = load_config(); ical_url = cfg.get("calendar", {}).get("ical_url"); kw_map = cfg.get("calendar", {}).get("keywords", {})
    now = datetime.datetime.now()
    if not ical_url: return {"events": [], "current_month": now.month, "current_year": now.year}
    try:
        start_dt = datetime.date(now.year, now.month, 1); end_dt = start_dt + datetime.timedelta(days=45) 
        async with httpx.AsyncClient() as client:
            res = await client.get(ical_url); cal = icalendar.Calendar.from_ical(res.read())
            events = recurring_ical_events.of(cal).between(start_dt, end_dt)
            frontend_events = []
            for ev in events:
                summary = str(ev.get("SUMMARY", "제목 없음"))
                dtstart = ev.get("DTSTART").dt
                date_str = dtstart.isoformat() if hasattr(dtstart, 'isoformat') else str(dtstart)
                color_id, matched = "1", False
                for kw, cid in kw_map.items():
                    if safe_match(kw, summary): color_id, matched = str(cid), True; break
                if not matched: color_id = str((int(hashlib.md5(summary.encode('utf-8')).hexdigest(), 16) % 11) + 1)
                frontend_events.append({"summary": summary, "start": {"dateTime": date_str}, "colorId": color_id})
            return {"events": frontend_events, "current_month": now.month, "current_year": now.year}
    except Exception as e: return {"events": [], "current_month": now.month, "current_year": now.year, "error": str(e)}

class WebhookData(BaseModel): source: str; message: str; border_color: Optional[str] = None; bg_color: Optional[str] = None     
@app.post("/api/notify")
async def receive_notification(data: WebhookData):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO notifications (source, message, border_color, bg_color) VALUES (?, ?, ?, ?)", (data.source, data.message, data.border_color, data.bg_color))
        conn.commit()
    return {"status": "success"}