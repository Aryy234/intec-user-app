import logging

from fastapi import APIRouter, HTTPException, Depends

from config import Settings, get_settings
from models.schemas import (
    UserCreateRequest,
    UserCreateResponse,
    UserPreviewResponse,
    ErrorResponse,
    HealthResponse,
)
from services.credential_generator import (
    generate_email,
    generate_password,
    generate_mail_nickname,
    generate_display_name,
)
from services.microsoft_graph import MicrosoftGraphService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Usuarios"])


def get_graph_service(settings: Settings = Depends(get_settings)):
    """Dependency injection para el servicio de Microsoft Graph."""
    return MicrosoftGraphService(settings)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Verifica que el servicio esté funcionando correctamente.",
)
async def health_check():
    """Endpoint de salud del servicio."""
    return HealthResponse(
        status="healthy",
        service="INTEC User Management API",
        version="1.0.0",
    )


@router.post(
    "/users/preview",
    response_model=UserPreviewResponse,
    summary="Pre-visualizar credenciales",
    description=(
        "Genera y muestra el correo electrónico y contraseña que se crearían "
        "para el usuario, **sin crear la cuenta** en Microsoft 365. "
        "Útil para verificar los datos antes de confirmar."
    ),
)
async def preview_user(
    user_data: UserCreateRequest,
    settings: Settings = Depends(get_settings),
):
    """Pre-visualiza las credenciales sin crear el usuario."""
    email = generate_email(user_data.nombre, user_data.apellido, settings.DOMAIN)
    password = generate_password(
        user_data.nombre, user_data.apellido, user_data.cedula
    )

    return UserPreviewResponse(
        nombre=user_data.nombre,
        apellido=user_data.apellido,
        cedula=user_data.cedula,
        email=email,
        password=password,
    )


@router.post(
    "/users",
    response_model=UserCreateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Datos de entrada inválidos"},
        409: {"model": ErrorResponse, "description": "El usuario ya existe"},
        500: {
            "model": ErrorResponse,
            "description": "Error al crear usuario en Microsoft 365",
        },
    },
    summary="Crear usuario en Microsoft 365",
    description=(
        "Crea un nuevo usuario en Microsoft 365 con las credenciales generadas "
        "automáticamente a partir del nombre, apellido y cédula. "
        "Si el correo ya existe, se intentará con variantes numéricas."
    ),
)
async def create_user(
    user_data: UserCreateRequest,
    settings: Settings = Depends(get_settings),
    graph_service: MicrosoftGraphService = Depends(get_graph_service),
):
    """Crea un usuario en Microsoft 365."""
    try:
        # Generar credenciales
        base_nickname = generate_mail_nickname(user_data.nombre, user_data.apellido)
        password = generate_password(
            user_data.nombre, user_data.apellido, user_data.cedula
        )
        display_name = generate_display_name(user_data.nombre, user_data.apellido)

        # Buscar un email disponible (maneja duplicados automáticamente)
        email, final_nickname = await graph_service.find_available_email(
            base_nickname, settings.DOMAIN
        )

        # Crear el usuario en Microsoft 365
        result = await graph_service.create_user(
            display_name=display_name,
            mail_nickname=final_nickname,
            user_principal_name=email,
            password=password,
            nombre=user_data.nombre,
            apellido=user_data.apellido,
        )

        return UserCreateResponse(
            nombre=user_data.nombre,
            apellido=user_data.apellido,
            cedula=user_data.cedula,
            email=email,
            password=password,
            microsoft_id=result["id"],
            message=f"Usuario {email} creado exitosamente en Microsoft 365.",
        )

    except Exception as e:
        logger.error(f"Error creando usuario: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear el usuario en Microsoft 365: {str(e)}",
        )
