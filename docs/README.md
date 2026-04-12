# 📘 INTEC User Management API — Documentación Técnica

Sistema de gestión de usuarios institucionales para **INTEC** que automatiza la creación de cuentas en **Microsoft 365** a partir de datos personales (Nombre, Apellido y Cédula).

---

## 📑 Índice

1. [Descripción General](#descripción-general)
2. [Arquitectura del Proyecto](#arquitectura-del-proyecto)
3. [Estructura de Archivos](#estructura-de-archivos)
4. [Configuración de Azure](#configuración-de-azure)
5. [Lógica de Generación de Credenciales](#lógica-de-generación-de-credenciales)
6. [Endpoints de la API](#endpoints-de-la-api)
7. [Instalación y Ejecución](#instalación-y-ejecución)
8. [Uso con Swagger UI](#uso-con-swagger-ui)
9. [Manejo de Errores](#manejo-de-errores)
10. [Consideraciones de Seguridad](#consideraciones-de-seguridad)

---

## Descripción General

### ¿Qué hace esta aplicación?

1. El usuario ingresa **Nombre**, **Apellido** y **Cédula** a través de la API
2. El sistema genera automáticamente un **correo electrónico** y una **contraseña** institucional
3. Se crea la cuenta del usuario en **Microsoft 365** mediante la **Microsoft Graph API**
4. Se retornan las credenciales generadas al solicitante

### Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|-----------|---------|
| **Backend** | Python + FastAPI | Python 3.10+ / FastAPI 0.115+ |
| **Microsoft SDK** | msgraph-sdk + azure-identity | msgraph-sdk 1.5+ |
| **Documentación API** | Swagger UI (OpenAPI 3.0) | Integrado en FastAPI |
| **Frontend** (futuro) | Vue.js + Vite | Pendiente |

---

## Arquitectura del Proyecto

```
┌─────────────────────────────────────────────────────────────────┐
│                        Cliente / Swagger UI                      │
│                     http://localhost:8000/docs                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP Request (JSON)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (:8000)                       │
│                                                                  │
│  ┌──────────────┐   ┌─────────────────────┐   ┌──────────────┐ │
│  │  routers/    │──▶│  services/           │──▶│  Microsoft   │ │
│  │  users.py    │   │  credential_gen.py   │   │  Graph API   │ │
│  │              │   │  microsoft_graph.py  │   │  (Azure AD)  │ │
│  └──────────────┘   └─────────────────────┘   └──────────────┘ │
│         │                                                        │
│  ┌──────────────┐   ┌─────────────────────┐                     │
│  │  models/     │   │  config.py          │                     │
│  │  schemas.py  │   │  (.env)             │                     │
│  └──────────────┘   └─────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de datos

```
Solicitud POST /api/users
        │
        ▼
┌─── Validación Pydantic (schemas.py) ───┐
│  - nombre: mín 2 chars                 │
│  - apellido: mín 2 chars               │
│  - cedula: 10-13 dígitos               │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌─── Generación de credenciales ─────────┐
│  credential_generator.py               │
│  - Email: aelizalde@intec.edu.ec       │
│  - Password: Intec.4290!AE             │
│  - Display Name: Ariel Elizalde        │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌─── Verificación de duplicados ─────────┐
│  microsoft_graph.py                    │
│  - ¿Existe aelizalde@intec.edu.ec?    │
│  - Si existe: intenta aelizalde1@...  │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌─── Creación en Microsoft 365 ──────────┐
│  Microsoft Graph API                   │
│  POST /v1.0/users                      │
│  - accountEnabled: true                │
│  - usageLocation: EC                   │
│  - forceChangePassword: false          │
└────────────────┬───────────────────────┘
                 │
                 ▼
        Respuesta JSON con credenciales
```

---

## Estructura de Archivos

```
intec-user-app/
├── backend/
│   ├── .env                              # Variables de entorno (SECRETO - no subir a Git)
│   ├── .env.example                      # Plantilla de variables (sin datos reales)
│   ├── .gitignore                        # Archivos excluidos de Git
│   ├── requirements.txt                  # Dependencias Python
│   ├── main.py                           # Punto de entrada de la aplicación FastAPI
│   ├── config.py                         # Configuración y carga de variables de entorno
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                    # Modelos Pydantic (request/response)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── credential_generator.py       # Lógica de generación de email y password
│   │   └── microsoft_graph.py            # Cliente de Microsoft Graph API
│   └── routers/
│       ├── __init__.py
│       └── users.py                      # Endpoints REST de usuarios
├── frontend/                             # (Futuro) Vue.js + Vite
└── docs/
    └── README.md                         # Esta documentación
```

### Descripción de cada archivo

#### `main.py` — Punto de entrada

- Crea la instancia de **FastAPI** con metadata para OpenAPI (título, descripción, versión)
- Configura **CORS** para permitir requests del frontend Vue.js (`localhost:5173`)
- Incluye el router de usuarios
- Redirige la ruta raíz `/` a la documentación Swagger `/docs`
- Configura el **logging** del sistema

#### `config.py` — Configuración

- Define la clase `Settings` usando `pydantic-settings`
- Carga automáticamente las variables del archivo `.env`:
  - `AZURE_CLIENT_ID` — ID de la aplicación registrada en Azure
  - `AZURE_TENANT_ID` — ID del directorio/tenant de Azure
  - `AZURE_CLIENT_SECRET` — Secreto de la aplicación
  - `DOMAIN` — Dominio del correo (por defecto: `intec.edu.ec`)
- Usa `@lru_cache()` para crear un **singleton** cacheado (solo se lee `.env` una vez)

#### `models/schemas.py` — Modelos de datos

Define los modelos Pydantic para validación y documentación OpenAPI:

| Modelo | Uso | Campos principales |
|--------|-----|-------------------|
| `UserCreateRequest` | Body de entrada | `nombre`, `apellido`, `cedula` (con validaciones) |
| `UserPreviewResponse` | Respuesta del preview | `email`, `password` generados |
| `UserCreateResponse` | Respuesta de creación | `email`, `password`, `microsoft_id` |
| `ErrorResponse` | Errores | `detail` con mensaje de error |
| `HealthResponse` | Health check | `status`, `service`, `version` |

Validaciones aplicadas:
- `nombre`: mínimo 2, máximo 50 caracteres
- `apellido`: mínimo 2, máximo 50 caracteres
- `cedula`: solo dígitos, entre 10 y 13 caracteres (regex: `^\d{10,13}$`)

#### `services/credential_generator.py` — Generador de credenciales

Funciones puras (sin side effects) para generar credenciales:

| Función | Descripción | Ejemplo |
|---------|-------------|---------|
| `normalize_text(text)` | Quita tildes y caracteres especiales | `"María"` → `"maria"` |
| `get_first_name(nombre)` | Extrae el primer nombre | `"María José"` → `"María"` |
| `get_first_apellido(apellido)` | Extrae el primer apellido | `"Pérez López"` → `"Pérez"` |
| `generate_email(nombre, apellido, domain)` | Genera el correo institucional | `"aelizalde@intec.edu.ec"` |
| `generate_mail_nickname(nombre, apellido)` | Genera el alias sin dominio | `"aelizalde"` |
| `generate_password(nombre, apellido, cedula)` | Genera la contraseña | `"Intec.4290!AE"` |
| `generate_display_name(nombre, apellido)` | Genera el nombre para mostrar | `"Ariel Elizalde"` |

#### `services/microsoft_graph.py` — Cliente Microsoft Graph

Clase `MicrosoftGraphService` que encapsula todas las interacciones con Azure AD:

| Método | Descripción |
|--------|-------------|
| `__init__(settings)` | Inicializa las credenciales Azure y el cliente Graph |
| `check_user_exists(upn)` | Verifica si un UPN ya existe en Azure AD |
| `create_user(...)` | Crea un usuario nuevo vía Microsoft Graph API |
| `find_available_email(nickname, domain)` | Busca un email disponible (intenta variantes numéricas si hay duplicado) |
| `close()` | Cierra la conexión del credential |

Propiedades del usuario creado en Microsoft 365:
- `accountEnabled`: `true` — La cuenta se activa inmediatamente
- `displayName`: Nombre completo (ej: "Ariel Elizalde")
- `givenName`: Primer nombre
- `surname`: Apellido
- `mailNickname`: Alias (ej: "aelizalde")
- `userPrincipalName`: Email/UPN (ej: "aelizalde@intec.edu.ec")
- `usageLocation`: `"EC"` (Ecuador)
- `passwordProfile.password`: Contraseña generada
- `passwordProfile.forceChangePasswordNextSignIn`: `false` — **No** obliga a cambiar la contraseña

#### `routers/users.py` — Endpoints

Define los 3 endpoints de la API (ver sección [Endpoints](#endpoints-de-la-api)).

---

## Configuración de Azure

### Requisitos previos en [portal.azure.com](https://portal.azure.com)

#### 1. Registro de aplicación

La aplicación ya está registrada con los siguientes valores:

| Parámetro | Valor |
|-----------|-------|
| **ID de aplicación (client)** | `57dd329d-a2b7-4ebd-baf7-c90086db1bde` |
| **ID de directorio (tenant)** | `39370498-2204-4ace-bc5e-31686bcb682b` |
| **Secreto de cliente** | Almacenado en `.env` (no compartir) |

#### 2. Permisos de API requeridos

Ruta: **Microsoft Entra ID** → **App registrations** → Tu app → **API permissions**

| Permiso | Tipo | Estado requerido |
|---------|------|-----------------|
| `User.Read` | Delegada | ✅ Concedido |
| `User.ReadWrite.All` | **Aplicación** | ✅ Concedido (con admin consent) |

> ⚠️ **Importante**: El permiso `User.ReadWrite.All` debe ser de tipo **Aplicación** (no Delegada) y debe tener **consentimiento de administrador** otorgado.

#### 3. Flujo de autenticación

Se utiliza el flujo **Client Credentials** (sin usuario interactivo):

```
Backend FastAPI                    Azure AD                    Microsoft Graph
      │                              │                              │
      │── ClientSecretCredential ──▶│                              │
      │   (tenant_id, client_id,     │                              │
      │    client_secret)            │                              │
      │                              │                              │
      │◀── Access Token ────────────│                              │
      │                              │                              │
      │── POST /v1.0/users ─────────────────────────────────────▶│
      │   Authorization: Bearer {token}                            │
      │                              │                              │
      │◀── 201 Created ─────────────────────────────────────────│
      │   { id, displayName, ... }   │                              │
```

#### 4. Dominio personalizado

El dominio `intec.edu.ec` debe estar **verificado** en el tenant:
- Ruta: **Microsoft Entra ID** → **Custom domain names**
- El dominio debe aparecer con estado **Verificado** ✅

---

## Lógica de Generación de Credenciales

### Correo electrónico

**Formato**: `(primera letra del primer nombre)(primer apellido)@intec.edu.ec`

```
Entrada:  Nombre = "Ariel", Apellido = "Elizalde"
Proceso:  primera_letra("Ariel") = "a"
          normalizar("Elizalde") = "elizalde"
Salida:   "aelizalde@intec.edu.ec"
```

**Casos especiales**:

| Entrada | Resultado |
|---------|-----------|
| `"María José"`, `"Pérez López"` | `mperez@intec.edu.ec` |
| `"José"`, `"García"` | `jgarcia@intec.edu.ec` |
| `"Andrés"`, `"O'Brien"` | `aobrien@intec.edu.ec` |

**Deduplicación**: Si `aelizalde@intec.edu.ec` ya existe, se intenta `aelizalde1@intec.edu.ec`, `aelizalde2@intec.edu.ec`, etc. (hasta 10 intentos).

### Contraseña

**Formato**: `Intec.(últimos 4 dígitos de cédula)!(inicial nombre mayúscula)(inicial apellido mayúscula)`

```
Entrada:  Nombre = "Ariel", Apellido = "Elizalde", Cédula = "1751754290"
Proceso:  inicial_nombre = "A"
          inicial_apellido = "E"
          últimos_4 = "4290"
Salida:   "Intec.4290!AE"
```

| Entrada | Contraseña |
|---------|-----------|
| `"Ariel"`, `"Elizalde"`, `"1751754290"` | `Intec.4290!AE` |
| `"Nataly"`, `"Rodriguez"`, `"1234567890"` | `Intec.7890!NR` |
| `"María"`, `"Pérez"`, `"0912345678"` | `Intec.5678!MP` |

> **¿Por qué este formato?** Microsoft 365 rechaza contraseñas que contengan el nombre de usuario (UPN). El formato anterior (`Aelizalde4290@i`) contenía `elizalde`, que es parte del UPN `aelizalde@intec.edu.ec`. Este nuevo formato evita ese conflicto.

**Características de seguridad de la contraseña**:
- ✅ Mayúsculas (`I`, `A`, `E`)
- ✅ Minúsculas (`ntec`)
- ✅ Dígitos (`4290`)
- ✅ Caracteres especiales (`.`, `!`)
- ✅ No contiene el nombre de usuario
- ✅ No se fuerza cambio en el primer inicio de sesión

---

## Endpoints de la API

### `GET /api/health` — Health Check

Verifica que el servicio esté funcionando.

**Request:**
```bash
curl http://localhost:8000/api/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "service": "INTEC User Management API",
  "version": "1.0.0"
}
```

---

### `POST /api/users/preview` — Pre-visualizar credenciales

Genera y muestra el correo y contraseña **sin crear** la cuenta en Microsoft 365.

**Request:**
```bash
curl -X POST http://localhost:8000/api/users/preview \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Ariel", "apellido": "Elizalde", "cedula": "1751754290"}'
```

**Response (200):**
```json
{
  "nombre": "Ariel",
  "apellido": "Elizalde",
  "cedula": "1751754290",
  "email": "aelizalde@intec.edu.ec",
  "password": "Intec.4290!AE"
}
```

---

### `POST /api/users` — Crear usuario en Microsoft 365

Crea la cuenta del usuario en Microsoft 365 con las credenciales generadas.

**Request:**
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Ariel", "apellido": "Elizalde", "cedula": "1751754290"}'
```

**Response (200):**
```json
{
  "nombre": "Ariel",
  "apellido": "Elizalde",
  "cedula": "1751754290",
  "email": "aelizalde@intec.edu.ec",
  "password": "Intec.4290!AE",
  "microsoft_id": "59ab877d-400c-4922-b25b-002fd2ec5513",
  "message": "Usuario aelizalde@intec.edu.ec creado exitosamente en Microsoft 365."
}
```

**Posibles errores:**

| Código | Descripción |
|--------|-------------|
| `422` | Datos de entrada inválidos (validación Pydantic) |
| `500` | Error al crear usuario en Microsoft 365 (permisos, conexión, etc.) |

---

## Instalación y Ejecución

### Requisitos

- Python 3.10 o superior
- Acceso a internet (para comunicarse con Microsoft Graph)
- Aplicación registrada en Azure con los permisos configurados

### Pasos

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd intec-user-app/backend

# 2. Crear entorno virtual
python3 -m venv venv

# 3. Activar entorno virtual
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Configurar variables de entorno
cp .env.example .env
# Editar .env con los valores reales de Azure

# 6. Ejecutar el servidor
uvicorn main:app --reload --port 8000
```

### Verificar que funciona

```bash
# Health check
curl http://localhost:8000/api/health

# Abrir Swagger UI en el navegador
# http://localhost:8000/docs
```

---

## Uso con Swagger UI

La documentación interactiva está disponible en:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Cómo probar un endpoint

1. Abrir `http://localhost:8000/docs` en el navegador
2. Hacer click en el endpoint que deseas probar (ej: `POST /api/users/preview`)
3. Click en **"Try it out"**
4. Modificar el JSON del body con los datos deseados
5. Click en **"Execute"**
6. Revisar la respuesta en la sección **"Response body"**

---

## Manejo de Errores

### Errores comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `Request_BadRequest` / `PasswordShouldNotContainUpn` | La contraseña contiene el username | Ya resuelto con el nuevo formato `Intec.XXXX!XX` |
| `Authorization_RequestDenied` | Faltan permisos en Azure | Agregar `User.ReadWrite.All` (Application) y otorgar admin consent |
| `Request_BadRequest` / `InvalidDomainName` | Dominio no verificado en el tenant | Verificar `intec.edu.ec` en Custom domain names |
| `Connection Error` | Sin acceso a internet o Azure inaccesible | Verificar conectividad |
| `422 Validation Error` | Datos de entrada no cumplen las reglas | Verificar formato (cédula solo dígitos, 10-13 chars) |

### Logs

El sistema registra logs con el formato:
```
2026-04-12 09:30:35 - services.microsoft_graph - INFO - Creando usuario: aelizalde@intec.edu.ec
2026-04-12 09:30:36 - services.microsoft_graph - INFO - Usuario creado exitosamente: aelizalde@intec.edu.ec (ID: 59ab877d-...)
```

---

## Consideraciones de Seguridad

### Secretos

- El archivo `.env` contiene el **secreto de cliente** de Azure. **Nunca** debe subirse a un repositorio Git.
- El `.gitignore` ya está configurado para excluir `.env`.
- En producción, usar variables de entorno del sistema o Azure Key Vault.

### Contraseñas generadas

- Las contraseñas se retornan en texto plano en la respuesta de la API. En producción, considerar:
  - Enviar las credenciales por email seguro al usuario
  - Mostrarlas solo una vez en la interfaz
  - Implementar HTTPS obligatorio

### Permisos de la API

- `User.ReadWrite.All` es un permiso de alto privilegio. Solo debe otorgarse a aplicaciones previamente revisadas y autorizadas.
- Considerar implementar autenticación en la propia API (API Key, JWT, etc.) para restringir quién puede crear usuarios.

### CORS

- Actualmente el CORS permite requests desde `localhost:5173` y `localhost:3000`. En producción, limitar al dominio específico del frontend.

---

## Dependencias del proyecto

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `fastapi[standard]` | ≥0.115.0 | Framework web con Swagger UI integrado |
| `uvicorn[standard]` | ≥0.30.0 | Servidor ASGI para ejecutar FastAPI |
| `python-dotenv` | ≥1.0.0 | Carga de variables desde `.env` |
| `pydantic` | ≥2.0.0 | Validación de datos y serialización |
| `pydantic-settings` | ≥2.0.0 | Carga de configuración tipada |
| `msgraph-sdk` | ≥1.5.0 | SDK oficial de Microsoft Graph para Python |
| `azure-identity` | ≥1.17.0 | Autenticación con Azure AD (Client Credentials) |
