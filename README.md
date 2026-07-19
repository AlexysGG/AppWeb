# AppWeb — Generador de Pagarés (Producto 2)

Aplicación web para automatizar la generación de pagarés conforme a la
**Ley General de Títulos y Operaciones de Crédito (LGTOC, arts. 170-174)**,
desarrollada para un despacho de abogados mexicano. Permite a abogados
autorizados capturar la información del pagaré, generar el documento en
PDF, enviarlo a firma electrónica y consultar el historial para fines
de auditoría.

Stack: **Python 3.12 + Django 5 + Django REST Framework**, base de
datos SQLite (dev), autenticación JWT.

## Arquitectura

```
config/            settings, urls, wsgi/asgi
apps/
  accounts/         usuarios, roles (RBAC), login/JWT
  pagares/          modelos Cliente/Pagaré, API REST propia, servicio de PDF
  firmas/           cliente del Web Service de terceros (firma electrónica) + webhook
  audit/            bitácora de auditoría (modelo + middleware)
```

Patrón aplicado: **Service Layer** (`apps/pagares/services/pdf_service.py`
separa la generación de PDF de las vistas) + **Repository implícito**
vía el ORM de Django + **Adapter** (`apps/firmas/client.py` encapsula al
proveedor externo de firma electrónica, desacoplando su SDK/API del
resto del sistema).

## 1. Mecanismos de seguridad

- Autenticación **JWT** (access/refresh, rotación y blacklist) vía
  `djangorestframework-simplejwt`.
- **RBAC**: roles `ADMIN` / `ABOGADO` con permisos a nivel de objeto
  (`apps/accounts/permissions.py`) — un abogado solo ve sus propios
  pagarés; solo abogados verificados por el despacho pueden operar.
- **Throttling** (`DEFAULT_THROTTLE_RATES`): mitiga fuerza bruta en
  login (5/min) y abuso de la API.
- Contraseñas con **hash PBKDF2** + validadores de robustez (longitud
  mínima, no numéricas, no comunes).
- **CSRF** activo en todas las vistas basadas en sesión/admin.
- Endurecimiento HTTPS/cookies automático en producción (`DEBUG=False`):
  `SECURE_SSL_REDIRECT`, `HSTS`, cookies `Secure`/`HttpOnly`.
- **Integridad documental**: hash SHA-256 del PDF generado, almacenado
  junto al pagaré.
- **Autenticidad de webhooks**: el callback del proveedor de firma
  electrónica se valida con **HMAC-SHA256** (`X-Signature`) antes de
  procesarse.
- **Bitácora de auditoría** automática (middleware) + eventos
  explícitos (login, creación de pagaré, generación de PDF, envío a
  firma) con usuario, IP, ruta y timestamp.
- Variables sensibles fuera del código (`.env`, `python-decouple`).

## 2. Web Services de terceros

`apps/firmas/client.py` (`ClienteFirmaElectronica`) integra un
proveedor externo de firma electrónica (API REST tipo DocuSign/Mifiel)
para: enviar el PDF a firmar (`crear_solicitud`) y recibir la
confirmación vía webhook (`apps/firmas/views.py::WebhookFirmaView`).
Mientras no se cuenten con credenciales productivas, el cliente corre
en modo *sandbox local* (mismo contrato de datos) para que el flujo
sea 100% demostrable — basta con configurar `ESIGN_API_BASE_URL` /
`ESIGN_API_KEY` reales para apuntar al proveedor contratado.

## 3. Web Services propios (API REST)

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/api/auth/token/` | Login, emite JWT (throttled) |
| POST | `/api/auth/token/refresh/` | Refresca el access token |
| POST | `/api/auth/registro/` | Alta de abogado (requiere verificación posterior) |
| GET | `/api/auth/perfil/` | Perfil del usuario autenticado |
| GET/POST | `/api/clientes/` | CRUD de suscriptores |
| GET/POST | `/api/pagares/` | CRUD de pagarés |
| GET | `/api/pagares/{id}/pdf/` | Genera/descarga el PDF del pagaré |
| POST | `/api/pagares/{id}/solicitar-firma/` | Envía el pagaré al servicio de firma electrónica |
| POST | `/api/firmas/webhook/` | Recibe la confirmación de firma (verificado por HMAC) |

## Interfaz web (Bootstrap)

Además de la API REST, el proyecto incluye una interfaz web tradicional
(vistas Django + formularios, Bootstrap 5 vía CDN) pensada para que los
abogados del despacho no necesiten Postman/curl:

| Ruta | Descripción |
|---|---|
| `/accounts/login/` | Login (formulario) |
| `/pagares/` | Listado de pagarés (con badges de estatus) |
| `/pagares/nuevo/` | Formulario para crear un pagaré |
| `/pagares/<id>/` | Detalle: ver/generar PDF, enviar a firma electrónica |
| `/clientes/` | Listado de clientes (suscriptores) |
| `/clientes/nuevo/` | Alta de cliente |

Estas vistas reutilizan exactamente los mismos servicios que la API
(`generar_pdf_pagare`, `ClienteFirmaElectronica`) y respetan las mismas
reglas de alcance por usuario (un abogado solo ve sus propios registros,
salvo que sea administrador).

## 4. Repositorio

Repo: https://github.com/AlexysGG/AppWeb

## Instalación local

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # ajustar SECRET_KEY, etc.
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Flujo de prueba rápido

```bash
# 1. Login
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"abogado1","password":"..."}'

# 2. Crear cliente (suscriptor)
curl -X POST http://127.0.0.1:8000/api/clientes/ \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"nombre":"Juan Pérez","direccion":"Calle 1, Puebla"}'

# 3. Crear pagaré, descargar PDF y enviar a firma
#    ver tabla de endpoints arriba
```

## Metodología

Desarrollo iterativo por *sprints* funcionales (autenticación → modelo
de datos → generación de PDF → integración con firma electrónica →
auditoría/endurecimiento de seguridad), reflejado en el historial de
commits del repositorio.
