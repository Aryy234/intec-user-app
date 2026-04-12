import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.users import router as users_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Crear aplicación FastAPI con metadata OpenAPI
app = FastAPI(
    title="INTEC User Management API",
    description=(
        "## API para la gestión de usuarios institucionales INTEC\n\n"
        "Esta API permite crear usuarios en **Microsoft 365** de forma automática "
        "a partir de los datos personales del estudiante/empleado.\n\n"
        "### Lógica de generación de credenciales\n\n"
        "| Campo | Formato | Ejemplo |\n"
        "|-------|---------|---------|\n"
        "| **Correo** | `(1ra letra nombre)(apellido)@intec.edu.ec` | `aelizalde@intec.edu.ec` |\n"
        "| **Contraseña** | `(1ra letra Mayús)(apellido)(últimos 4 cédula)@i` | `Aelizalde4290@i` |\n\n"
        "### Funcionalidades\n\n"
        "- 📋 **Pre-visualización** de credenciales antes de crear\n"
        "- 👤 **Creación** de usuarios en Microsoft 365\n"
        "- 🔄 **Deduplicación** automática de correos (variantes numéricas)\n"
        "- ✅ **Validación** de datos de entrada\n"
    ),
    version="1.0.0",
    contact={
        "name": "INTEC IT Department",
        "email": "soporte@intec.edu.ec",
    },
    license_info={
        "name": "Uso Interno",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configurar CORS para permitir el frontend Vue.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternativo
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(users_router)


@app.get("/", include_in_schema=False)
async def root():
    """Redirige a la documentación Swagger."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/docs")
