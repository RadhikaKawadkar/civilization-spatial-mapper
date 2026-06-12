"""
================================================================
  CIVILIZATION SPATIAL INTELLIGENCE MAPPER
  FastAPI Backend — backend/main.py

  Endpoints:
    GET  /                          health check
    GET  /run                       execute C++ engine, stream output
    GET  /api/civilizations         all civilizations
    GET  /api/nearest?lat=&lon=     KD-Tree nearest neighbor
    GET  /api/range                 KD-Tree range query
    GET  /api/cluster?eps=&min=     DBSCAN clustering
    GET  /api/compare?a=&b=         compare two civilizations
    GET  /api/rtree?lat=&lon=       R-Tree region lookup
    GET  /api/stats                 tree statistics

  RUN:
    cd backend
    uvicorn main:app --reload --port 8080
================================================================
"""

import os
import math
import subprocess
import httpx
import random
import time
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, HTMLResponse
from pydantic import BaseModel
from models import Civilization, ClusterResult
from kdtree import KDTree
from rtree_index import RTreeIndex
from clustering import dbscan
from database import init_db, create_user, get_user_by_email, get_user_by_id, add_custom_civilization, get_custom_civilizations, update_user_password, get_civilizations_by_user, get_all_civilizations, delete_custom_civilization, delete_builtin_civilization
import hashlib
import secrets

load_dotenv()

# ── Gmail SMTP Configuration ─────────────────────────────────────
GMAIL_SENDER       = os.environ.get("GMAIL_SENDER", "").strip()
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
GMAIL_DISPLAY_NAME = os.environ.get("GMAIL_DISPLAY_NAME", "Civilization Spatial Mapper").strip()

# ── In-Memory OTP Store { email: {otp, expires_at} } ────────────
otp_store: dict = {}
OTP_EXPIRY_SECONDS = 600  # 10 minutes


def _send_gmail_sync(to_email: str, subject: str, html_body: str) -> bool:
    """
    Send an HTML email via Gmail SMTP (TLS on port 587).
    Uses the GMAIL_SENDER and GMAIL_APP_PASSWORD from .env.
    This is a synchronous function; call it via asyncio.to_thread.
    """
    if not GMAIL_APP_PASSWORD or GMAIL_APP_PASSWORD == "YOUR_16_CHAR_APP_PASSWORD_HERE":
        print("[EMAIL] Gmail App Password not configured in backend/.env — skipping email")
        print(f"[EMAIL] Would have sent '{subject}' to {to_email}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{GMAIL_DISPLAY_NAME} <{GMAIL_SENDER}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, to_email, msg.as_string())

        print(f"[EMAIL] [OK] Sent to {to_email}: {subject}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("[EMAIL] [ERROR] Gmail auth failed — check GMAIL_APP_PASSWORD in backend/.env")
        return False
    except Exception as e:
        print(f"[EMAIL] [ERROR] Error sending email: {e}")
        return False


async def send_gmail(to_email: str, subject: str, html_body: str) -> bool:
    """Async wrapper — runs the blocking SMTP call in a thread."""
    return await asyncio.to_thread(_send_gmail_sync, to_email, subject, html_body)


def build_otp_email(name: str, otp: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
    <body style="margin:0;padding:0;background:#050d1a;font-family:'Segoe UI',sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#050d1a;min-height:100vh;">
        <tr><td align="center" style="padding:40px 20px;">
          <table width="520" cellpadding="0" cellspacing="0" style="background:linear-gradient(135deg,#0a1628,#0d1f3c);border:1px solid rgba(201,168,76,0.3);border-radius:16px;overflow:hidden;">
            <!-- Header -->
            <tr>
              <td style="background:linear-gradient(135deg,#0d1f3c,#162040);padding:32px 40px;text-align:center;border-bottom:1px solid rgba(201,168,76,0.2);">
                <div style="font-size:2rem;margin-bottom:8px;">🏛️</div>
                <h1 style="margin:0;font-family:'Georgia',serif;font-size:1.4rem;color:#c9a84c;letter-spacing:0.08em;">CIVILIZATION SPATIAL MAPPER</h1>
                <p style="margin:6px 0 0;color:#7a8ba0;font-size:0.8rem;letter-spacing:0.15em;text-transform:uppercase;">Password Reset</p>
              </td>
            </tr>
            <!-- Body -->
            <tr>
              <td style="padding:36px 40px;">
                <p style="color:#c8d6e5;font-size:1rem;margin:0 0 12px;">Hello <strong style="color:#c9a84c;">{name}</strong>,</p>
                <p style="color:#7a8ba0;font-size:0.9rem;margin:0 0 28px;line-height:1.6;">We received a request to reset your password. Use the one-time passcode below. It expires in <strong style="color:#c9a84c;">10 minutes</strong>.</p>
                <!-- OTP Box -->
                <div style="background:rgba(201,168,76,0.08);border:2px solid #c9a84c;border-radius:12px;padding:28px;text-align:center;margin:0 0 28px;">
                  <p style="margin:0 0 8px;color:#7a8ba0;font-size:0.75rem;letter-spacing:0.2em;text-transform:uppercase;">Your OTP Code</p>
                  <div style="font-size:2.8rem;font-weight:700;letter-spacing:0.35em;color:#c9a84c;font-family:'Courier New',monospace;">{otp}</div>
                </div>
                <p style="color:#7a8ba0;font-size:0.82rem;margin:0;line-height:1.6;">If you did not request this, you can safely ignore this email. Your password will remain unchanged.</p>
              </td>
            </tr>
            <!-- Footer -->
            <tr>
              <td style="background:rgba(0,0,0,0.3);padding:20px 40px;text-align:center;border-top:1px solid rgba(255,255,255,0.05);">
                <p style="margin:0;color:#3a4a5a;font-size:0.75rem;">Civilization Spatial Intelligence Mapper &bull; civilizationspatialmapper@gmail.com</p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """


def build_civilization_added_email(user_name: str, civ_name: str, region: str, resource: float, knowledge: float, military: float) -> str:
    score = round((resource + knowledge + military) / 3, 2)
    score_color = "#c9a84c" if score >= 85 else "#4ade80" if score >= 77 else "#f4a261"
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
    <body style="margin:0;padding:0;background:#050d1a;font-family:'Segoe UI',sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#050d1a;min-height:100vh;">
        <tr><td align="center" style="padding:40px 20px;">
          <table width="520" cellpadding="0" cellspacing="0" style="background:linear-gradient(135deg,#0a1628,#0d1f3c);border:1px solid rgba(201,168,76,0.3);border-radius:16px;overflow:hidden;">
            <!-- Header -->
            <tr>
              <td style="background:linear-gradient(135deg,#0d1f3c,#162040);padding:32px 40px;text-align:center;border-bottom:1px solid rgba(201,168,76,0.2);">
                <div style="font-size:2rem;margin-bottom:8px;">🏛️</div>
                <h1 style="margin:0;font-family:'Georgia',serif;font-size:1.4rem;color:#c9a84c;letter-spacing:0.08em;">CIVILIZATION SPATIAL MAPPER</h1>
                <p style="margin:6px 0 0;color:#7a8ba0;font-size:0.8rem;letter-spacing:0.15em;text-transform:uppercase;">New Civilization Added</p>
              </td>
            </tr>
            <!-- Body -->
            <tr>
              <td style="padding:36px 40px;">
                <p style="color:#c8d6e5;font-size:1rem;margin:0 0 12px;">Hello <strong style="color:#c9a84c;">{user_name}</strong>,</p>
                <p style="color:#7a8ba0;font-size:0.9rem;margin:0 0 24px;line-height:1.6;">You have successfully added a new civilization to the Spatial Intelligence Mapper!</p>
                <!-- Civilization Card -->
                <div style="background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.25);border-radius:12px;padding:24px;margin:0 0 24px;">
                  <h2 style="margin:0 0 4px;font-family:'Georgia',serif;font-size:1.3rem;color:#c9a84c;">{civ_name}</h2>
                  <p style="margin:0 0 20px;color:#7a8ba0;font-size:0.82rem;letter-spacing:0.1em;text-transform:uppercase;">{region}</p>
                  <!-- Metrics -->
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="padding:6px 0;">
                        <p style="margin:0 0 4px;color:#7a8ba0;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;">Resource Density</p>
                        <div style="background:rgba(255,255,255,0.06);border-radius:4px;height:8px;overflow:hidden;">
                          <div style="background:#c9a84c;height:8px;width:{resource}%;border-radius:4px;"></div>
                        </div>
                        <p style="margin:2px 0 0;color:#c9a84c;font-size:0.8rem;font-weight:700;">{resource}</p>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:6px 0;">
                        <p style="margin:0 0 4px;color:#7a8ba0;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;">Knowledge Density</p>
                        <div style="background:rgba(255,255,255,0.06);border-radius:4px;height:8px;overflow:hidden;">
                          <div style="background:#00b4d8;height:8px;width:{knowledge}%;border-radius:4px;"></div>
                        </div>
                        <p style="margin:2px 0 0;color:#00b4d8;font-size:0.8rem;font-weight:700;">{knowledge}</p>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:6px 0;">
                        <p style="margin:0 0 4px;color:#7a8ba0;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;">Military Strength</p>
                        <div style="background:rgba(255,255,255,0.06);border-radius:4px;height:8px;overflow:hidden;">
                          <div style="background:#f87171;height:8px;width:{military}%;border-radius:4px;"></div>
                        </div>
                        <p style="margin:2px 0 0;color:#f87171;font-size:0.8rem;font-weight:700;">{military}</p>
                      </td>
                    </tr>
                  </table>
                  <!-- Score -->
                  <div style="margin-top:16px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.06);text-align:center;">
                    <p style="margin:0;color:#7a8ba0;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;">Spatial Score</p>
                    <p style="margin:4px 0 0;font-size:2rem;font-weight:700;color:{score_color};">{score}</p>
                  </div>
                </div>
                <p style="color:#7a8ba0;font-size:0.82rem;margin:0;line-height:1.6;">This civilization is now live on the spatial map and indexed in the KD-Tree.</p>
              </td>
            </tr>
            <!-- Footer -->
            <tr>
              <td style="background:rgba(0,0,0,0.3);padding:20px 40px;text-align:center;border-top:1px solid rgba(255,255,255,0.05);">
                <p style="margin:0;color:#3a4a5a;font-size:0.75rem;">Civilization Spatial Intelligence Mapper &bull; civilizationspatialmapper@gmail.com</p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """


# ── App setup ──────────────────────────────────────────────────
app = FastAPI(
    title="Civilization Spatial Intelligence Mapper",
    description="KD-Tree + R-Tree spatial queries over historical civilizations",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CPP_EXE      = Path(__file__).parent.parent / "mapper.exe"
FRONTEND_HTML = Path(__file__).parent.parent / "civilization_mapper_frontend.html"

init_db()

all_civs: list[Civilization] = []

# ── Load built-in civilizations from the database ──────────────
for row in get_all_civilizations():
    c = Civilization(
        name=row["name"], lat=row["latitude"], lon=row["longitude"],
        start=row.get("start_year") or 0, end=row.get("end_year") or 0,
        region=row.get("region") or "Unknown",
        resource=row.get("resource_density") or 50.0,
        knowledge=row.get("knowledge_density") or 50.0,
        military=row.get("military_strength") or 50.0,
    )
    all_civs.append(c)

# ── Load custom civilizations added by users ───────────────────
custom_rows = get_custom_civilizations()
for row in custom_rows:
    # Avoid duplicating if a custom civ has same name as a built-in
    if not any(c.name == row["name"] for c in all_civs):
        c = Civilization(
            name=row["name"], lat=row["lat"], lon=row["lon"],
            start=row.get("start_year") or 0, end=row.get("end_year") or 0,
            region=row.get("region") or "Unknown",
            resource=row.get("resource_density") or 50.0,
            knowledge=row.get("knowledge_density") or 50.0,
            military=row.get("military_strength") or 50.0,
            added_by_name=row.get("added_by_name")
        )
        all_civs.append(c)

kd_tree = KDTree()
kd_tree.build(all_civs)

r_tree = RTreeIndex()
r_tree.add_default_regions()

print(f"[OK] Loaded {len(all_civs)} civilizations (built-in + custom)")
print(f"[OK] KD-Tree built: {kd_tree.node_count} nodes")
print(f"[OK] R-Tree built:  {len(r_tree.regions)} regions")


# ── Routes ─────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    """
    Serve the frontend HTML so users open http://localhost:8080
    instead of a file:// URL (which browsers block for security).
    """
    if FRONTEND_HTML.exists():
        return HTMLResponse(content=FRONTEND_HTML.read_text(encoding="utf-8"))
    return HTMLResponse(
        content="<h2>Frontend not found. Make sure civilization_mapper_frontend.html is in the project root.</h2>",
        status_code=404,
    )


@app.get("/health")
def health():
    return {
        "status": "running",
        "project": "Civilization Spatial Intelligence Mapper",
        "backend": "FastAPI + Python KD-Tree",
        "endpoints": [
            "/run", "/api/civilizations", "/api/nearest",
            "/api/range", "/api/cluster", "/api/compare",
            "/api/rtree", "/api/stats",
        ],
    }


@app.get("/run", response_class=PlainTextResponse)
def run_cpp_engine():
    """
    Execute the compiled C++ spatial engine and return its stdout.
    Sends a scripted input sequence so the binary runs non-interactively.
    """
    if not CPP_EXE.exists():
        raise HTTPException(
            status_code=404,
            detail=f"C++ executable not found at {CPP_EXE}. Build with: make",
        )
    try:
        # Feed: nearest query (lat=20, lon=78) then exit
        scripted_input = "1\n20\n78\n5\n"
        result = subprocess.run(
            [str(CPP_EXE)],
            input=scripted_input,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout or ""
        if result.returncode != 0 and result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        return output or "[C++ engine produced no output]"
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="C++ engine timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/register")
def register(req: RegisterRequest):
    user_id = create_user(req.name, req.email, req.password)
    if not user_id:
        raise HTTPException(status_code=400, detail="Email already registered")
    return {"message": "User created", "user_id": user_id, "name": req.name}

@app.post("/api/login")
def login(req: LoginRequest):
    user = get_user_by_email(req.email)
    if not user or user["password_hash"] != hashlib.sha256(req.password.encode()).hexdigest():
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"message": "Login successful", "token": user["id"], "name": user["name"]}

# ── Forgot Password — OTP Flow ──────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: str

@app.post("/api/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    """Step 1: Generate OTP and email it to the user."""
    user = get_user_by_email(req.email)
    if not user:
        # Return success anyway to avoid email enumeration
        return {"message": "If that email is registered, an OTP has been sent."}
    
    otp = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    otp_store[req.email] = {
        "otp": otp,
        "expires_at": time.time() + OTP_EXPIRY_SECONDS,
        "verified": False,
    }
    
    html = build_otp_email(user["name"], otp)
    await send_gmail(
        to_email=req.email,
        subject="Your Password Reset OTP — Civilization Spatial Mapper",
        html_body=html,
    )
    print(f"[OTP] Generated for {req.email}: {otp}")  # dev log
    return {"message": "If that email is registered, an OTP has been sent."}


class VerifyOTPRequest(BaseModel):
    email: str
    otp: str

@app.post("/api/verify-otp")
def verify_otp(req: VerifyOTPRequest):
    """Step 2: Validate the OTP. Returns verified=True if valid."""
    entry = otp_store.get(req.email)
    if not entry:
        raise HTTPException(status_code=400, detail="No OTP request found for this email. Please request a new one.")
    if time.time() > entry["expires_at"]:
        otp_store.pop(req.email, None)
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
    if entry["otp"] != req.otp.strip():
        raise HTTPException(status_code=400, detail="Invalid OTP. Please check and try again.")
    
    # Mark as verified (allows password reset)
    otp_store[req.email]["verified"] = True
    return {"message": "OTP verified successfully.", "verified": True}


class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str
    otp: str

@app.post("/api/reset-password")
def reset_password(req: ResetPasswordRequest):
    """Step 3: Reset password — requires a verified OTP."""
    entry = otp_store.get(req.email)
    if not entry:
        raise HTTPException(status_code=400, detail="No verified OTP found. Please start the reset process again.")
    if time.time() > entry["expires_at"]:
        otp_store.pop(req.email, None)
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
    if not entry.get("verified"):
        raise HTTPException(status_code=400, detail="OTP not verified. Please verify your OTP first.")
    if entry["otp"] != req.otp.strip():
        raise HTTPException(status_code=400, detail="OTP mismatch. Please start the reset process again.")
    
    user = get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=404, detail="Email address not found")
    
    success = update_user_password(user["id"], req.new_password)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset password")
    
    # Clean up OTP
    otp_store.pop(req.email, None)
    return {"message": "Password reset successfully"}

class ChangePasswordRequest(BaseModel):
    token: int
    old_password: str
    new_password: str

@app.post("/api/change-password")
def change_password(req: ChangePasswordRequest):
    user = get_user_by_id(req.token)
    if not user or user["password_hash"] != hashlib.sha256(req.old_password.encode()).hexdigest():
        raise HTTPException(status_code=401, detail="Invalid current password")
    
    success = update_user_password(user["id"], req.new_password)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password")
    return {"message": "Password updated successfully"}

@app.get("/api/user-civilizations")
def get_user_civilizations(token: int = Query(...)):
    user = get_user_by_id(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_civs = get_civilizations_by_user(token)
    return user_civs

class CivilizationRequest(BaseModel):
    name: str
    lat: float
    lon: float
    region: str
    resource: float
    knowledge: float
    military: float
    token: int

@app.post("/api/civilizations")
async def post_civilization(req: CivilizationRequest):
    user = get_user_by_id(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    civ_id = add_custom_civilization(
        req.name, req.lat, req.lon, req.region,
        req.resource, req.knowledge, req.military, user["id"]
    )
    if not civ_id:
        raise HTTPException(status_code=400, detail="Civilization name already exists")
    
    c = Civilization(
        name=req.name, lat=req.lat, lon=req.lon,
        region=req.region, resource=req.resource, knowledge=req.knowledge,
        military=req.military, added_by_name=user["name"]
    )
    all_civs.append(c)
    kd_tree.build(all_civs)

    # Send confirmation email to user
    user_email = user.get("email", "")
    if user_email:
        html = build_civilization_added_email(
            user_name=user["name"],
            civ_name=req.name,
            region=req.region,
            resource=req.resource,
            knowledge=req.knowledge,
            military=req.military,
        )
        await send_gmail(
            to_email=user_email,
            subject=f"Civilization Added — {req.name} 🏛️",
            html_body=html,
        )

    return {"message": "Civilization added", "civilization": c.to_dict()}

@app.get("/api/civilizations")
def get_civilizations():
    return [c.to_dict() for c in all_civs]


class DeleteCivilizationRequest(BaseModel):
    token: int

@app.delete("/api/civilizations/{civ_name}")
def delete_civilization(civ_name: str, req: DeleteCivilizationRequest):
    """Delete a civilization (built-in or custom)."""
    global all_civs

    user = get_user_by_id(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    target = next((c for c in all_civs if c.name == civ_name), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Civilization '{civ_name}' not found")

    if target.added_by_name:
        # Custom civilization ownership check
        deleted = delete_custom_civilization(civ_name, user["id"])
        if not deleted:
            raise HTTPException(
                status_code=403,
                detail="You can only delete civilizations you added yourself"
            )
    else:
        # Built-in civilization
        deleted = delete_builtin_civilization(civ_name)
        if not deleted:
            raise HTTPException(
                status_code=500,
                detail="Error deleting built-in civilization from database"
            )

    # Remove from in-memory list and rebuild KD-Tree
    all_civs = [c for c in all_civs if c.name != civ_name]
    kd_tree.build(all_civs)

    return {"message": f"'{civ_name}' deleted successfully", "total": len(all_civs)}


@app.get("/api/nearest")
def nearest(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    result = kd_tree.nearest(lat, lon)
    if result is None:
        raise HTTPException(status_code=404, detail="No civilizations loaded")
    civ, dist = result
    return {
        "query": {"lat": lat, "lon": lon},
        "nearest": civ.to_dict(),
        "distance_km": round(dist * 111, 2),
        "algorithm": "KD-Tree O(log n) with branch pruning",
    }


@app.get("/api/range")
def range_query(
    latMin: float = Query(..., ge=-90,  le=90),
    latMax: float = Query(..., ge=-90,  le=90),
    lonMin: float = Query(..., ge=-180, le=180),
    lonMax: float = Query(..., ge=-180, le=180),
):
    if latMin > latMax or lonMin > lonMax:
        raise HTTPException(status_code=400, detail="Min values must be <= Max values")
    results = kd_tree.range_query(latMin, latMax, lonMin, lonMax)
    return {
        "query": {"latMin": latMin, "latMax": latMax, "lonMin": lonMin, "lonMax": lonMax},
        "count": len(results),
        "results": [c.to_dict() for c in results],
        "algorithm": "KD-Tree O(log n + k) spatial pruning",
    }


@app.get("/api/cluster")
def cluster(
    eps: float = Query(default=15.0, gt=0, description="Epsilon radius in degrees (~111 km/degree)"),
    min_pts: int = Query(default=2, ge=1, description="Minimum points to form a cluster"),
):
    """
    DBSCAN clustering using the KD-Tree range search as the epsilon-neighborhood query.
    Returns cluster assignments for every civilization.
    """
    clusters: list[ClusterResult] = dbscan(all_civs, kd_tree, eps, min_pts)
    grouped: dict[int, list] = {}
    for cr in clusters:
        grouped.setdefault(cr.cluster_id, []).append(cr.to_dict())

    return {
        "params": {"eps_degrees": eps, "eps_km": round(eps * 111, 1), "min_pts": min_pts},
        "total_civilizations": len(all_civs),
        "num_clusters": len([k for k in grouped if k != -1]),
        "noise_points": len(grouped.get(-1, [])),
        "clusters": grouped,
    }


@app.get("/api/compare")
def compare(
    a: str = Query(..., description="Name of civilization A"),
    b: str = Query(..., description="Name of civilization B"),
):
    civ_a = next((c for c in all_civs if c.name == a), None)
    civ_b = next((c for c in all_civs if c.name == b), None)
    if not civ_a:
        raise HTTPException(status_code=404, detail=f"Not found: {a}")
    if not civ_b:
        raise HTTPException(status_code=404, detail=f"Not found: {b}")

    dist = math.sqrt(
        (civ_a.latitude - civ_b.latitude) ** 2 +
        (civ_a.longitude - civ_b.longitude) ** 2
    ) * 111

    winner = civ_a.name if civ_a.spatial_score() >= civ_b.spatial_score() else civ_b.name
    return {
        "civilization_a": civ_a.to_dict(),
        "civilization_b": civ_b.to_dict(),
        "score_a": civ_a.spatial_score(),
        "score_b": civ_b.spatial_score(),
        "distance_km": round(dist, 2),
        "winner": winner,
    }


@app.get("/api/rtree")
def rtree_lookup(
    lat: float = Query(..., ge=-90,  le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    regions = r_tree.query_point(lat, lon)
    return {
        "query": {"lat": lat, "lon": lon},
        "regions": regions,
        "count": len(regions),
        "algorithm": "R-Tree bounding box overlap O(log n)",
    }


@app.get("/api/stats")
def stats():
    n = len(all_civs)
    log_n = math.ceil(math.log2(n)) if n > 0 else 0
    return {
        "total_civilizations": n,
        "kdtree_nodes": kd_tree.node_count,
        "rtree_regions": len(r_tree.regions),
        "linear_ops": n,
        "kdtree_ops": log_n,
        "speedup": n // log_n if log_n > 0 else 1,
    }


# ── Chat endpoint (OpenAI primary · Gemini fallback) ───────────

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

class ChatResponse(BaseModel):
    reply: str
    ok: bool = True
    model: str | None = None
    provider: str | None = None   # "openai" | "gemini" | "offline"
    error: str | None = None


CHAT_SYSTEM = """You are the Spatial Intelligence Assistant for the "Civilization Spatial Intelligence Mapper" project.

PROJECT CONTEXT:
- A spatial data system indexing historical civilizations by latitude, longitude, and time
- KD-Tree backend: nearest neighbor O(log n), range search O(log n+k), built in Python/C++
- FastAPI Python backend exposing: /api/civilizations, /api/nearest, /api/range, /api/cluster, /api/compare, /api/rtree, /api/stats
- DBSCAN clustering built on top of KD-Tree range search (no external libraries)
- Leaflet.js frontend with CARTO Dark tiles, live map click queries
- Dataset: 59 civilizations — 47 Indian dynasties (Indus Valley through Sikh Empire) + 12 global civilizations
- R-Tree: 8 named bounding-box regions (South Asia, Mediterranean, Middle East, East Asia, Mesoamerica, North Africa, Central Asia, South America)

You are a general-purpose AI assistant. Answer ANY question — about this project, history, geography, programming, algorithms, or any other topic. Give specific technical answers for project questions. Be concise, friendly, and technically accurate.
Do not use excessive markdown headers in your responses."""


def _build_live_context() -> str:
    """Build a complete live-data context containing all civilizations currently in the database."""
    try:
        civ_list = []
        for c in all_civs:
            start_fmt = f"{abs(c.start_year)} BCE" if c.start_year < 0 else f"{c.start_year} CE"
            end_fmt = f"{abs(c.end_year)} BCE" if c.end_year < 0 else f"{c.end_year} CE"
            added_by = f" (Added by: {c.added_by_name})" if c.added_by_name else ""
            civ_list.append(
                f"- Name: {c.name}{added_by} | Lat: {c.latitude}, Lon: {c.longitude} | Period: {start_fmt} to {end_fmt} | "
                f"Region: {c.region} | Resource Density: {c.resource_density}, Knowledge Density: {c.knowledge_density}, "
                f"Military Strength: {c.military_strength} | Spatial Score: {c.spatial_score()}"
            )
        civs_str = "\n".join(civ_list)
        return (
            f"There are currently {len(all_civs)} civilizations in the database:\n"
            f"{civs_str}\n\n"
            f"KD-Tree nodes: {kd_tree.node_count}. R-Tree regions: {len(r_tree.regions)}."
        )
    except Exception as e:
        return f"Live dataset loaded with {len(all_civs)} civilizations. Error loading details: {e}"


async def _call_openai(message: str, history: list[ChatMessage], system: str) -> str:
    """Call OpenAI Chat Completions API asynchronously."""
    from openai import AsyncOpenAI
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model   = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"

    client = AsyncOpenAI(api_key=api_key)
    messages = [{"role": "system", "content": system}]
    for m in history:
        messages.append({"role": "user" if m.role == "user" else "assistant", "content": m.content})
    messages.append({"role": "user", "content": message})

    resp = await client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=700,
        temperature=0.7,
    )
    return resp.choices[0].message.content or "No response from OpenAI."


async def _call_gemini(message: str, history: list[ChatMessage], system: str) -> str:
    """Call Gemini generateContent API asynchronously."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model   = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash").strip() or "gemini-1.5-flash"

    gemini_messages = []
    for m in history:
        role = "user" if m.role == "user" else "model"
        gemini_messages.append({"role": role, "parts": [{"text": m.content}]})
    gemini_messages.append({"role": "user", "parts": [{"text": message}]})

    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": gemini_messages,
        "generationConfig": {"maxOutputTokens": 700}
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
    resp.raise_for_status()
    data = resp.json()
    if "candidates" in data and data["candidates"]:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    return "No response from Gemini."


@app.post("/api/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    """
    AI chat proxy — tries providers in order:
      1. OpenAI   (if OPENAI_API_KEY is set)
      2. Gemini   (if GEMINI_API_KEY is set)
      3. Friendly error message
    """
    if not req.message or not req.message.strip():
        return ChatResponse(reply="Please type a message.", ok=False, error="empty_message")

    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    openai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    gemini_model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash").strip() or "gemini-1.5-flash"

    system = CHAT_SYSTEM + "\n\nLIVE CONTEXT:\n" + _build_live_context()

    # ── 1. Try OpenAI ──────────────────────────────────────────
    if openai_key and openai_key != "YOUR_OPENAI_API_KEY_HERE":
        try:
            reply = await _call_openai(req.message, req.history, system)
            return ChatResponse(reply=reply, ok=True, model=openai_model, provider="openai")
        except Exception as e:
            print(f"[CHAT] OpenAI failed: {e}. Trying Gemini...")

    # ── 2. Try Gemini ──────────────────────────────────────────
    if gemini_key and gemini_key != "YOUR_GEMINI_API_KEY_HERE":
        try:
            reply = await _call_gemini(req.message, req.history, system)
            return ChatResponse(reply=reply, ok=True, model=gemini_model, provider="gemini")
        except Exception as e:
            print(f"[CHAT] Gemini failed: {e}")
            return ChatResponse(
                reply="AI service is temporarily unavailable. Please try again in a moment.",
                ok=False, model=gemini_model, provider="gemini", error=str(e)[:200]
            )

    # ── 3. Neither key configured ──────────────────────────────
    return ChatResponse(
        reply=(
            "🤖 **AI chat is not configured yet.**\n\n"
            "Add your OpenAI API key to `backend/.env`:\n"
            "```\nOPENAI_API_KEY=sk-...\n```\n"
            "Then restart the backend. You can get a key at **platform.openai.com/api-keys**."
        ),
        ok=False,
        provider="offline",
        error="no_api_key",
    )


CHAT_SYSTEM = """You are the Spatial Intelligence Assistant for the "Civilization Spatial Intelligence Mapper" project.

PROJECT CONTEXT:
- A spatial data system indexing historical civilizations by latitude, longitude, and time
- C++ core: KD-Tree (insertion, nearest neighbor O(log n), range search O(log n+k)), R-Tree (bounding box regions)
- FastAPI Python backend exposing: /run, /api/civilizations, /api/nearest, /api/range, /api/cluster, /api/compare, /api/rtree, /api/stats
- DBSCAN clustering built on top of KD-Tree range search (no external libraries)
- Leaflet.js frontend with CARTO Dark tiles, live map click queries
- Dataset: 47 Indian civilizations from final_dataset.csv

You are a general-purpose AI assistant. You can answer ANY question — about this project, history, geography, programming, algorithms, data structures, or any other topic. When questions relate to the project, give specific technical answers. For general questions, answer helpfully and thoroughly.

Be concise, friendly, and technically accurate."""

