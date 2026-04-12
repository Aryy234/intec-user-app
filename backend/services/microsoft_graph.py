import logging

from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.user import User
from msgraph.generated.models.password_profile import PasswordProfile

from config import Settings

logger = logging.getLogger(__name__)


class MicrosoftGraphService:
    """Servicio para interactuar con Microsoft Graph API."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._credential = ClientSecretCredential(
            tenant_id=settings.AZURE_TENANT_ID,
            client_id=settings.AZURE_CLIENT_ID,
            client_secret=settings.AZURE_CLIENT_SECRET,
        )
        self._client = GraphServiceClient(
            credentials=self._credential,
            scopes=["https://graph.microsoft.com/.default"],
        )

    async def check_user_exists(self, user_principal_name: str) -> bool:
        """
        Verifica si un usuario con el UPN dado ya existe en Azure AD.

        Args:
            user_principal_name: El email/UPN a verificar (ej: aelizalde@intec.edu.ec)

        Returns:
            True si el usuario existe, False en caso contrario.
        """
        try:
            user = await self._client.users.by_user_id(user_principal_name).get()
            return user is not None
        except Exception:
            # Si hay un error 404 o similar, el usuario no existe
            return False

    async def create_user(
        self,
        display_name: str,
        mail_nickname: str,
        user_principal_name: str,
        password: str,
        nombre: str = "",
        apellido: str = "",
    ) -> dict:
        """
        Crea un nuevo usuario en Microsoft 365 vía Graph API.

        Args:
            display_name: Nombre completo (ej: "Ariel Elizalde")
            mail_nickname: Alias sin dominio (ej: "aelizalde")
            user_principal_name: Email/UPN completo (ej: "aelizalde@intec.edu.ec")
            password: Contraseña inicial
            nombre: Primer nombre (para givenName)
            apellido: Apellido (para surname)

        Returns:
            Diccionario con los datos del usuario creado incluyendo su ID.

        Raises:
            Exception: Si falla la creación del usuario en Microsoft 365.
        """
        request_body = User(
            account_enabled=True,
            display_name=display_name,
            mail_nickname=mail_nickname,
            user_principal_name=user_principal_name,
            given_name=nombre.strip(),
            surname=apellido.strip(),
            usage_location="EC",
            password_profile=PasswordProfile(
                force_change_password_next_sign_in=False,
                password=password,
            ),
        )

        try:
            logger.info(f"Creando usuario: {user_principal_name}")
            new_user = await self._client.users.post(request_body)

            logger.info(
                f"Usuario creado exitosamente: {user_principal_name} (ID: {new_user.id})"
            )

            return {
                "id": new_user.id,
                "displayName": new_user.display_name,
                "userPrincipalName": new_user.user_principal_name,
                "mail": new_user.mail,
            }
        except Exception as e:
            logger.error(f"Error al crear usuario {user_principal_name}: {str(e)}")
            raise

    async def find_available_email(
        self, base_nickname: str, domain: str, max_attempts: int = 10
    ) -> tuple[str, str]:
        """
        Encuentra un email disponible, probando variantes numéricas si es necesario.

        Args:
            base_nickname: Alias base (ej: "aelizalde")
            domain: Dominio del email (ej: "intec.edu.ec")
            max_attempts: Número máximo de variantes a probar.

        Returns:
            Tupla (email_disponible, nickname_disponible)

        Raises:
            Exception: Si no se encuentra un email disponible después de max_attempts.
        """
        # Intentar con el email base primero
        email = f"{base_nickname}@{domain}"
        if not await self.check_user_exists(email):
            return email, base_nickname

        # Probar variantes numéricas
        for i in range(1, max_attempts + 1):
            variant_nickname = f"{base_nickname}{i}"
            variant_email = f"{variant_nickname}@{domain}"
            if not await self.check_user_exists(variant_email):
                logger.info(
                    f"Email base {base_nickname}@{domain} ocupado. "
                    f"Usando variante: {variant_email}"
                )
                return variant_email, variant_nickname

        raise Exception(
            f"No se encontró un email disponible para {base_nickname}@{domain} "
            f"después de {max_attempts} intentos."
        )

    async def close(self):
        """Cierra la conexión del credential."""
        await self._credential.close()
