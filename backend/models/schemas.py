from pydantic import BaseModel, Field


class UserCreateRequest(BaseModel):
    """Datos de entrada para crear un usuario."""

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Nombre del usuario",
        examples=["Ariel"],
    )
    apellido: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Apellido del usuario",
        examples=["Elizalde"],
    )
    cedula: str = Field(
        ...,
        min_length=10,
        max_length=13,
        pattern=r"^\d{10,13}$",
        description="Número de cédula (solo dígitos, 10-13 caracteres)",
        examples=["1751754290"],
    )


class UserPreviewResponse(BaseModel):
    """Pre-visualización de las credenciales que se generarán."""

    nombre: str = Field(..., description="Nombre ingresado")
    apellido: str = Field(..., description="Apellido ingresado")
    cedula: str = Field(..., description="Cédula ingresada")
    email: str = Field(..., description="Correo electrónico generado")
    password: str = Field(..., description="Contraseña generada")


class UserCreateResponse(BaseModel):
    """Respuesta después de crear el usuario en Microsoft 365."""

    nombre: str = Field(..., description="Nombre del usuario")
    apellido: str = Field(..., description="Apellido del usuario")
    cedula: str = Field(..., description="Cédula del usuario")
    email: str = Field(..., description="Correo electrónico asignado")
    password: str = Field(..., description="Contraseña asignada")
    microsoft_id: str = Field(..., description="ID del usuario en Microsoft 365")
    message: str = Field(..., description="Mensaje de confirmación")


class ErrorResponse(BaseModel):
    """Respuesta de error estándar."""

    detail: str = Field(..., description="Descripción del error")


class HealthResponse(BaseModel):
    """Respuesta del health check."""

    status: str = Field(..., description="Estado del servicio")
    service: str = Field(..., description="Nombre del servicio")
    version: str = Field(..., description="Versión de la API")
