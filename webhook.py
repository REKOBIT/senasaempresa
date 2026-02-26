"""
WEBHOOK: SENASA EMPRESA - Gravity Forms -> Google Sheets -> Email

Columnas del Google Sheet (en este orden exacto):
A: NOMBRE
B: EMAIL
C: TELEFONO
D: FECHA
E: CAMPANA
F: SEDE
G: PISO
H: carril piso 4 xola
I: carril piso 3 troncoso
J: carril piso 7 xola
K: PRODUCTO
L: QUE PASO?
M: HORA
N: imagen
O: carril naucalpan

Logica condicional:
  SEDE = Xola -> Piso Xola
      Piso 4  -> Carril Maquina P.4
      Piso 7  -> Carril Maquina P.7
  SEDE = Troncoso  -> Carril Maquina P.3
  SEDE = Naucalpan -> Carril Maquina Naucalpan
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webhook")

app = FastAPI(title="Webhook SENASA EMPRESA", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_field(raw_data, field_id, default=""):
    """Busca un campo de Gravity Forms por su ID."""
    possible_keys = ["input_" + str(field_id), str(field_id), field_id]
    for key in possible_keys:
        if key in raw_data:
            val = raw_data[key]
            if isinstance(val, str):
                return val.strip()
            return str(val).strip()
    for key in raw_data:
        if key.lower().replace("input_", "") == str(field_id):
            return str(raw_data[key]).strip()
    return default


def normalize_gravity_form(raw_data):
    """Extrae todos los campos usando los IDs de Gravity Forms."""

    nombre = get_field(raw_data, "1")
    email = get_field(raw_data, "3")
    telefono = get_field(raw_data, "4")
    fecha = get_field(raw_data, "5")
    campana = get_field(raw_data, "6")
    sede = get_field(raw_data, "7")
    piso_xola = get_field(raw_data, "18")
    descripcion = get_field(raw_data, "19")
    producto = get_field(raw_data, "10")

    # Hora compuesta
    hora_h = get_field(raw_data, "14.1")
    hora_m = get_field(raw_data, "14.2")
    hora_ap = get_field(raw_data, "14.3")
    hora = ""
    if hora_h:
        hora = hora_h + ":" + (hora_m or "00") + " " + hora_ap
        hora = hora.strip()
    if not hora:
        hora = get_field(raw_data, "14")

    # Carriles
    carril_p4 = get_field(raw_data, "12")
    carril_p3 = get_field(raw_data, "13")
    carril_p7 = get_field(raw_data, "11")
    carril_naucalpan = get_field(raw_data, "20")

    # Fotos
    fotos = get_field(raw_data, "16")

    # Limpiar placeholders
    placeholders = [
        "Seleccionar un piso", "Seleccionar",
        "Indique que paso con su producto",
        "Seleccione Producto", "Seleccione producto",
        "Seleccione carril",
    ]
    if piso_xola in placeholders:
        piso_xola = ""
    if descripcion in placeholders:
        descripcion = ""
    if producto in placeholders:
        producto = ""
    if sede == "Seleccionar":
        sede = ""
    if carril_p4 in placeholders:
        carril_p4 = ""
    if carril_p3 in placeholders:
        carril_p3 = ""
    if carril_p7 in placeholders:
        carril_p7 = ""
    if carril_naucalpan in placeholders:
        carril_naucalpan = ""

    # Limpiar carriles segun logica condicional
    if sede == "Xola":
        carril_naucalpan = ""
        carril_p3 = ""
        if piso_xola == "Piso 4":
            carril_p7 = ""
        elif piso_xola == "Piso 7":
            carril_p4 = ""
        else:
            carril_p4 = ""
            carril_p7 = ""
    elif sede == "Troncoso":
        piso_xola = ""
        carril_p4 = ""
        carril_p7 = ""
        carril_naucalpan = ""
    elif sede == "Naucalpan":
        piso_xola = ""
        carril_p3 = ""
        carril_p4 = ""
        carril_p7 = ""

    return {
        "nombre": nombre,
        "email": email,
        "telefono": telefono,
        "fecha": fecha,
        "campana": campana,
        "sede": sede,
        "piso_xola": piso_xola,
        "carril_p4": carril_p4,
        "carril_p3": carril_p3,
        "carril_p7": carril_p7,
        "producto": producto,
        "descripcion": descripcion,
        "hora": hora,
        "fotos": fotos,
        "carril_naucalpan": carril_naucalpan,
    }


# --- Google Sheets ---
def get_google_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_file(
        settings.GOOGLE_CREDENTIALS_FILE, scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(settings.GOOGLE_SHEET_ID).sheet1


def write_to_sheet(data):
    """
    Escribe en Google Sheets en el orden EXACTO de las columnas:
    A: NOMBRE
    B: EMAIL
    C: TELEFONO
    D: FECHA
    E: CAMPANA
    F: SEDE
    G: PISO
    H: carril piso 4 xola
    I: carril piso 3 troncoso
    J: carril piso 7 xola
    K: PRODUCTO
    L: QUE PASO?
    M: HORA
    N: imagen
    O: carril naucalpan
    """
    try:
        sheet = get_google_sheet()
        row = [
            data["nombre"],
            data["email"],
            data["telefono"],
            data["fecha"],
            data["campana"],
            data["sede"],
            data["piso_xola"],
            data["carril_p4"],
            data["carril_p3"],
            data["carril_p7"],
            data["producto"],
            data["descripcion"],
            data["hora"],
            data["fotos"],
            data["carril_naucalpan"],
        ]
        sheet.append_row(row)
        logger.info("Sheet OK: " + data["nombre"] + " | " + data["sede"])
        return True
    except Exception as e:
        logger.error("Error Google Sheets: " + str(e))
        return False


# --- Email ---
def send_notification(data):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Reporte: " + data["nombre"] + " | " + data["sede"] + " | " + (data["producto"] or "sin producto")
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = settings.EMAIL_NOTIFY_TO

        carril = data["carril_p4"] or data["carril_p3"] or data["carril_p7"] or data["carril_naucalpan"] or "-"
        carril_label = "Carril"
        if data["carril_p4"]:
            carril_label = "Carril Maquina P.4"
        elif data["carril_p3"]:
            carril_label = "Carril Maquina P.3"
        elif data["carril_p7"]:
            carril_label = "Carril Maquina P.7"
        elif data["carril_naucalpan"]:
            carril_label = "Carril Maquina Naucalpan"

        fotos_html = ""
        if data["fotos"]:
            fotos_html = '<h3 style="color:#34495e;margin-top:20px">Fotos</h3><p><a href="' + data["fotos"] + '" style="color:#3498db">Ver foto adjunta</a></p>'

        html = (
            '<html><body style="font-family:Arial,sans-serif;padding:20px;background:#f5f5f5">'
            '<div style="max-width:600px;margin:0 auto;background:white;border-radius:12px;padding:30px;box-shadow:0 2px 10px rgba(0,0,0,0.1)">'
            '<h2 style="color:#2c3e50;margin-top:0">Nuevo reporte - SENASA EMPRESA</h2>'
            '<hr style="border:none;border-top:1px solid #eee">'
            '<h3 style="color:#34495e;margin-top:20px">Datos del usuario</h3>'
            '<table style="width:100%;border-collapse:collapse">'
            '<tr><td style="padding:8px 0;color:#7f8c8d;width:160px">Nombre</td><td style="padding:8px 0;font-weight:bold">' + data["nombre"] + '</td></tr>'
            '<tr><td style="padding:8px 0;color:#7f8c8d">Email</td><td style="padding:8px 0"><a href="mailto:' + data["email"] + '">' + data["email"] + '</a></td></tr>'
            '<tr><td style="padding:8px 0;color:#7f8c8d">Telefono</td><td style="padding:8px 0">' + (data["telefono"] or "-") + '</td></tr>'
            '<tr><td style="padding:8px 0;color:#7f8c8d">Fecha</td><td style="padding:8px 0">' + data["fecha"] + '</td></tr>'
            '<tr><td style="padding:8px 0;color:#7f8c8d">Hora</td><td style="padding:8px 0">' + (data["hora"] or "-") + '</td></tr>'
            '<tr><td style="padding:8px 0;color:#7f8c8d">Campana</td><td style="padding:8px 0">' + (data["campana"] or "-") + '</td></tr>'
            '</table>'
            '<h3 style="color:#34495e;margin-top:20px">Ubicacion</h3>'
            '<table style="width:100%;border-collapse:collapse">'
            '<tr><td style="padding:8px 0;color:#7f8c8d;width:160px">Sede</td><td style="padding:8px 0;font-weight:bold">' + data["sede"] + '</td></tr>'
            '<tr><td style="padding:8px 0;color:#7f8c8d">Piso</td><td style="padding:8px 0">' + (data["piso_xola"] or "-") + '</td></tr>'
            '<tr><td style="padding:8px 0;color:#7f8c8d">' + carril_label + '</td><td style="padding:8px 0;font-weight:bold;font-size:18px">' + carril + '</td></tr>'
            '</table>'
            '<h3 style="color:#34495e;margin-top:20px">Detalle</h3>'
            '<table style="width:100%;border-collapse:collapse">'
            '<tr><td style="padding:8px 0;color:#7f8c8d;width:160px">Que paso?</td><td style="padding:8px 0">' + (data["descripcion"] or "-") + '</td></tr>'
            '<tr><td style="padding:8px 0;color:#7f8c8d">Producto</td><td style="padding:8px 0;font-weight:bold">' + (data["producto"] or "-") + '</td></tr>'
            '</table>'
            + fotos_html +
            '<hr style="border:none;border-top:1px solid #eee;margin-top:20px">'
            '<p style="color:#bdc3c7;font-size:11px;margin-bottom:0">' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' - Webhook SENASA EMPRESA</p>'
            '</div></body></html>'
        )
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Email OK: " + settings.EMAIL_NOTIFY_TO)
        return True
    except Exception as e:
        logger.error("Error email: " + str(e))
        return False


# === ENDPOINTS ===

@app.get("/")
def root():
    return {"status": "ok", "message": "Webhook SENASA EMPRESA activo", "version": "3.0"}


@app.get("/formulario")
def formulario():
    return FileResponse("formulario.html", media_type="text/html")


@app.post("/webhook")
async def webhook(request: Request):
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            raw_data = await request.json()
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form = await request.form()
            raw_data = dict(form)
        else:
            body = await request.body()
            raw_data = json.loads(body)
    except Exception as e:
        logger.error("Error leyendo datos: " + str(e))
        raise HTTPException(status_code=400, detail="No se pudieron leer los datos")

    logger.info("Recibido: " + json.dumps(raw_data, default=str, ensure_ascii=False)[:500])

    data = normalize_gravity_form(raw_data)
    logger.info("Normalizado: " + str(data))

    if not data["nombre"]:
        raise HTTPException(status_code=400, detail="Nombre es obligatorio")
    if not data["email"]:
        raise HTTPException(status_code=400, detail="Email es obligatorio")

    sheet_ok = write_to_sheet(data)
    email_ok = send_notification(data)

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Reporte de " + data["nombre"] + " registrado",
            "google_sheets": "ok" if sheet_ok else "error",
            "email": "ok" if email_ok else "error",
        },
    )


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0 - SENASA EMPRESA",
    }
