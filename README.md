# 🔗 Webhook: WordPress → Google Sheets → Email

## Qué hace

Alguien llena tu formulario en WordPress → Se guarda en Google Sheets → Te llega un correo de notificación.

## Archivos del proyecto

```
automation_system/
├── webhook.py          ← El webhook (código principal)
├── config.py           ← Lee las variables del .env
├── requirements.txt    ← Dependencias de Python
├── .env.example        ← Plantilla de configuración (copiar a .env)
├── credentials.json    ← (TÚ LO AGREGAS) Credenciales de Google
├── Dockerfile          ← Para desplegar con Docker
└── docker-compose.yml  ← Para desplegar en Coolify
```

## Paso a paso

### 1. Configurar Google Sheets API

1. Ve a https://console.cloud.google.com
2. Crea un proyecto nuevo
3. Busca y habilita: **Google Sheets API** y **Google Drive API**
4. Ve a Credenciales → Crear credenciales → **Cuenta de servicio**
5. Dentro de la cuenta, ve a Claves → Agregar clave → **JSON**
6. Se descarga un archivo → renómbralo a `credentials.json` y ponlo en esta carpeta
7. Crea un Google Sheet nuevo
8. Comparte el Sheet con el email de la cuenta de servicio (termina en `@...iam.gserviceaccount.com`)
9. En la primera fila del Sheet pon: `Fecha | Nombre | Email | Teléfono | Mensaje | Origen`
10. Copia el ID del Sheet (está en la URL: `docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit`)

### 2. Configurar Email

1. Ve a https://myaccount.google.com/apppasswords
2. Genera una contraseña de aplicación para "Correo"
3. Guarda esa contraseña

### 3. Crear tu .env

Copia el ejemplo y edítalo con tus datos:

```bash
cp .env.example .env
```

### 4. Probar en tu máquina

```bash
pip install -r requirements.txt
uvicorn webhook:app --reload
```

Abre http://localhost:8000 → Debe decir "Webhook activo 🚀"

Prueba con curl:

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Test","email":"test@mail.com","telefono":"5551234567","mensaje":"Prueba"}'
```

### 5. Desplegar en Coolify

Sube el proyecto a un repo de GitHub y en Coolify:
- Nuevo recurso → Docker Compose
- Apunta a tu repo
- Agrega las variables del .env en la configuración
- Sube el `credentials.json` como volumen
- Despliega

Tu webhook quedará en: `https://tu-dominio.com/webhook`

### 6. Conectar con WordPress

#### Contact Form 7
1. Instala plugin **"CF7 to Webhook"**
2. Edita tu formulario → pestaña Webhook
3. URL: `https://tu-dominio.com/webhook`

#### Elementor Forms
1. Edita el formulario
2. Actions After Submit → agrega **Webhook**
3. URL: `https://tu-dominio.com/webhook`

#### WPForms
1. Instala addon **Webhooks** o usa **Uncanny Automator**
2. URL: `https://tu-dominio.com/webhook`

#### Gravity Forms
1. Instala **Webhooks Add-On**
2. Settings → Webhooks
3. URL: `https://tu-dominio.com/webhook`
