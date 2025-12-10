import os
import uuid
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from .core.auth import create_access_token
from .core.scheduler import start_scheduler
from .core.logging import logger
from .models import init_db, write_log
from .services.cleaning import preview_csv, preview_xlsx, read_all, read_all_stream
from .services.aggregation import compute_overview, compute_monthly, compute_subject

app = FastAPI(title="Bluewow Activation")

origins = []
allowed = os.getenv("ALLOWED_ORIGIN")
if allowed:
    origins = [allowed]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

init_db()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

STATE = {"activation_path": None, "activated_rows": []}

def recompute():
    rows = []
    if STATE["activation_path"]:
        try:
            rows = read_all(STATE["activation_path"])
        except Exception:
            rows = []
    STATE["activated_rows"] = rows
    write_log("update_run", "recompute")

start_scheduler(recompute)

# 静态站点：将前端构建产物挂载到根路径，统一域名
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/web", StaticFiles(directory=STATIC_DIR, html=True), name="static")

@app.get("/")
def root():
    return RedirectResponse("/ui")

@app.get("/healthz")
def healthz():
    return {"ok": True}

# 无前端 Agent：一次性上传文件并返回处理结果与CSV（base64）
import base64

def _csv_string(headers, rows):
    out = ",".join(headers) + "\n"
    for r in rows:
        vals = []
        for h in headers:
            v = r.get(h)
            if v is None:
                v = ""
            v = str(v).replace("\n", " ").replace(",", " ")
            vals.append(v)
        out += ",".join(vals) + "\n"
    return out

@app.post("/api/bluewow/agent/process")
async def agent_process(file: UploadFile = File(...)):
    rows = []
    file.file.seek(0)
    rows = read_all_stream(file.file, file.filename)
    overview = compute_overview(rows, None)
    monthly = compute_monthly(rows)
    subject_overall = compute_subject(rows, True)
    # CSV payloads
    monthly_rows = [{"month": m["month"], "activated": m["activated"]} for m in monthly]
    monthly_csv = _csv_string(["month", "activated"], monthly_rows)
    subject_csv = _csv_string(["subject", "count", "rate"], subject_overall)
    activated_csv = _csv_string(["employee_id", "first_login_at", "subject", "platform", "company", "name"], rows)
    return {
        "overview": overview,
        "monthly": monthly,
        "subject_overall": subject_overall,
        "files": {
            "monthly_csv": {"filename": "monthly.csv", "base64": base64.b64encode(monthly_csv.encode()).decode()},
            "subject_overall_csv": {"filename": "subject_overall.csv", "base64": base64.b64encode(subject_csv.encode()).decode()},
            "activated_csv": {"filename": "activated.csv", "base64": base64.b64encode(activated_csv.encode()).decode()},
        },
    }

def require_admin(token: Optional[str] = None):
    return True

# 单表上传：仅上传激活/登录名单

@app.post("/api/bluewow/upload/activation")
async def upload_activation(file: UploadFile = File(...)):
    key = f"activation_{uuid.uuid4().hex}_{file.filename}"
    path = os.path.join(UPLOAD_DIR, key)
    with open(path, "wb") as f:
        f.write(await file.read())
    STATE["activation_path"] = path
    write_log("upload", key)
    preview = []
    ext = (file.filename or "").lower()
    with open(path, "rb") as f:
        try:
            if ext.endswith(".xlsx") or ext.endswith(".xls"):
                preview = preview_xlsx(f)
            else:
                preview = preview_csv(f)
        except Exception:
            preview = []
    return {"stored": key, "preview": preview}

@app.post("/api/bluewow/process")
def process():
    rows = []
    if STATE["activation_path"]:
        try:
            rows = read_all(STATE["activation_path"])
        except Exception:
            rows = []
    overview = compute_overview(rows, None)
    monthly = compute_monthly(rows)
    subject_overall = compute_subject(rows, True)
    write_log("process", "run")
    return {"overview": overview, "monthly": monthly, "subject_overall": subject_overall}

@app.get("/api/bluewow/metrics/overview")
def metrics_overview():
    rows = STATE["activated_rows"]
    overview = compute_overview(rows, None)
    return overview

@app.get("/api/bluewow/metrics/monthly")
def metrics_monthly():
    rows = STATE["activated_rows"]
    return compute_monthly(rows)

@app.get("/api/bluewow/metrics/by-subject")
def metrics_subject(scope: Optional[str] = "overall"):
    rows = STATE["activated_rows"]
    return compute_subject(rows, scope == "overall")

@app.get("/api/bluewow/unactivated")
def unactivated():
    return {"available": False, "reason": "未接入花名册，无法计算未激活"}

@app.get("/api/bluewow/feishu/unactivated/list")
def unactivated_list(subject: Optional[str] = None):
    return {"available": False}

@app.get("/api/bluewow/raw")
def raw(month: Optional[str] = None, subject: Optional[str] = None):
    rows = STATE["activated_rows"]
    out = []
    for r in rows:
        ok = True
        if month:
            ts = r.get("first_login_at")
            if not ts or not ts.startswith(month):
                ok = False
        if ok and subject:
            s = r.get("subject")
            if s != subject:
                ok = False
        if ok:
            out.append(r)
    return out

def _to_csv(headers, rows):
    yield ",".join(headers) + "\n"
    for r in rows:
        line = []
        for h in headers:
            v = r.get(h)
            if v is None:
                v = ""
            v = str(v).replace("\n", " ").replace(",", " ")
            line.append(v)
        yield ",".join(line) + "\n"

@app.get("/api/bluewow/download/monthly.csv")
def download_monthly():
    data = compute_monthly(STATE["activated_rows"])
    headers = ["month", "activated"]
    rows = [{"month": d["month"], "activated": d["activated"]} for d in data]
    return StreamingResponse(_to_csv(headers, rows), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=monthly.csv"})

@app.get("/api/bluewow/download/subject_overall.csv")
def download_subject_overall():
    data = compute_subject(STATE["activated_rows"], True)
    headers = ["subject", "count", "rate"]
    return StreamingResponse(_to_csv(headers, data), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=subject_overall.csv"})

@app.get("/api/bluewow/download/activated.csv")
def download_activated():
    rows = STATE["activated_rows"]
    headers = ["employee_id", "first_login_at", "subject", "platform", "company", "name"]
    return StreamingResponse(_to_csv(headers, rows), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=activated.csv"})

@app.get("/api/bluewow/feishu/auth/login")
def feishu_login():
    return RedirectResponse("/")

@app.get("/api/bluewow/feishu/auth/callback")
def feishu_callback(code: Optional[str] = None):
    token = create_access_token("feishu_user", "admin")
    return {"token": token}

@app.get("/api/bluewow/feishu/event")
def feishu_event_get():
    return {"ok": True}

@app.post("/api/bluewow/feishu/event")
async def feishu_event(payload: dict):
    t = payload.get("type")
    if t == "url_verification":
        return JSONResponse({"challenge": payload.get("challenge")})
    write_log("feishu_event", t or "unknown")
    return {"ok": True}

@app.get("/ui")
def ui():
    html = """
    <!doctype html>
    <html lang=zh>
    <meta charset=utf-8>
    <meta name=viewport content="width=device-width,initial-scale=1">
    <title>Bluewow 上传与报告</title>
    <style>
      body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial;max-width:960px;margin:24px auto;padding:0 16px}
      .row{display:flex;gap:12px;align-items:center;margin:12px 0}
      .card{border:1px solid #eee;border-radius:8px;padding:12px;margin:12px 0}
      button{padding:8px 12px}
      table{border-collapse:collapse;width:100%}
      th,td{border:1px solid #ddd;padding:6px}
    </style>
    <div class=row>
      <input type=file id=f accept=.csv,.xlsx>
      <button id=go>生成报告</button>
    </div>
    <div class=card>
      <div id=overview></div>
      <div class=row>
        <button id=d1>下载月度CSV</button>
        <button id=d2>下载主体总体CSV</button>
        <button id=d3>下载激活明细CSV</button>
      </div>
    </div>
    <div class=card>
      <h3>月度激活</h3>
      <table id=monthly></table>
    </div>
    <div class=card>
      <h3>主体总体</h3>
      <table id=subject></table>
    </div>
    <script>
    const el = (s)=>document.querySelector(s)
    const tfill = (table, cols, rows)=>{
      table.innerHTML = "";
      const thead = document.createElement("thead");
      const trh = document.createElement("tr");
      cols.forEach(c=>{const th=document.createElement("th");th.textContent=c;trh.appendChild(th)});
      thead.appendChild(trh); table.appendChild(thead);
      const tb=document.createElement("tbody");
      rows.forEach(r=>{const tr=document.createElement("tr");cols.forEach(c=>{const td=document.createElement("td");td.textContent=(r[c]??"");tr.appendChild(td)});tb.appendChild(tr)});
      table.appendChild(tb);
    }
    const downloadB64 = (name,b64)=>{const bin=atob(b64);const buf=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)buf[i]=bin.charCodeAt(i);const blob=new Blob([buf]);const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=name;a.click();URL.revokeObjectURL(a.href)}
    el('#go').onclick = async ()=>{
      const f = el('#f').files[0]; if(!f){alert('请选择文件');return}
      const fd = new FormData(); fd.append('file', f);
      const resp = await fetch('/api/bluewow/agent/process',{method:'POST',body:fd});
      const data = await resp.json();
      el('#overview').textContent = `总激活人数: ${data.overview.activated}`;
      tfill(el('#monthly'), ['month','activated'], (data.monthly||[]));
      tfill(el('#subject'), ['subject','count','rate'], (data.subject_overall||[]));
      el('#d1').onclick = ()=>downloadB64(data.files.monthly_csv.filename, data.files.monthly_csv.base64);
      el('#d2').onclick = ()=>downloadB64(data.files.subject_overall_csv.filename, data.files.subject_overall_csv.base64);
      el('#d3').onclick = ()=>downloadB64(data.files.activated_csv.filename, data.files.activated_csv.base64);
    }
    </script>
    </html>
    """
    return HTMLResponse(content=html)
