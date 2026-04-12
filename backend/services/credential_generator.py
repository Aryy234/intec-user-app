import unicodedata
import re


def normalize_text(text: str) -> str:
    """
    Normaliza texto: quita tildes, caracteres especiales y convierte a minúsculas.

    Ejemplos:
        "María" -> "maria"
        "José" -> "jose"
        "Pérez" -> "perez"
        "O'Brien" -> "obrien"
    """
    # Descomponer caracteres unicode (ej: é -> e + ́)
    normalized = unicodedata.normalize("NFD", text)
    # Eliminar marcas diacríticas (tildes, diéresis, etc.)
    without_accents = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    # Eliminar caracteres no alfanuméricos
    clean = re.sub(r"[^a-zA-Z]", "", without_accents)
    return clean.lower()


def get_first_name(nombre: str) -> str:
    """
    Extrae el primer nombre de un nombre compuesto.

    Ejemplos:
        "María José" -> "María"
        "Ariel" -> "Ariel"
        "Juan Carlos" -> "Juan"
    """
    return nombre.strip().split()[0]


def get_first_apellido(apellido: str) -> str:
    """
    Extrae el primer apellido de un apellido compuesto.

    Ejemplos:
        "Pérez López" -> "Pérez"
        "Elizalde" -> "Elizalde"
    """
    return apellido.strip().split()[0]


def generate_email(nombre: str, apellido: str, domain: str) -> str:
    """
    Genera el correo electrónico institucional.

    Formato: (primera letra del primer nombre)(primer apellido)@dominio
    Todo en minúsculas, sin tildes ni caracteres especiales.

    Ejemplos:
        ("Ariel", "Elizalde", "intec.edu.ec") -> "aelizalde@intec.edu.ec"
        ("María José", "Pérez López", "intec.edu.ec") -> "mperez@intec.edu.ec"
    """
    first_name = get_first_name(nombre)
    first_apellido = get_first_apellido(apellido)

    first_letter = normalize_text(first_name)[0]
    apellido_clean = normalize_text(first_apellido)

    return f"{first_letter}{apellido_clean}@{domain}"


def generate_mail_nickname(nombre: str, apellido: str) -> str:
    """
    Genera el mailNickname (alias sin dominio).

    Ejemplos:
        ("Ariel", "Elizalde") -> "aelizalde"
    """
    first_name = get_first_name(nombre)
    first_apellido = get_first_apellido(apellido)

    first_letter = normalize_text(first_name)[0]
    apellido_clean = normalize_text(first_apellido)

    return f"{first_letter}{apellido_clean}"


def generate_password(nombre: str, apellido: str, cedula: str) -> str:
    """
    Genera la contraseña del usuario.

    Formato: Intec.(últimos 4 dígitos de cédula)!(inicial nombre mayúscula)(inicial apellido mayúscula)
    Este formato evita que la contraseña contenga el nombre de usuario (UPN),
    lo cual Microsoft 365 rechaza con error PasswordShouldNotContainUpn.

    Ejemplos:
        ("Ariel", "Elizalde", "1751754290") -> "Intec.4290!AE"
        ("María", "Pérez", "0912345678") -> "Intec.5678!MP"
        ("Nataly", "Rodriguez", "1234567890") -> "Intec.7890!NR"
    """
    first_name = get_first_name(nombre)
    first_apellido = get_first_apellido(apellido)

    initial_nombre = normalize_text(first_name)[0].upper()
    initial_apellido = normalize_text(first_apellido)[0].upper()
    last_four = cedula[-4:]

    return f"Intec.{last_four}!{initial_nombre}{initial_apellido}"


def generate_display_name(nombre: str, apellido: str) -> str:
    """
    Genera el nombre para mostrar.

    Ejemplos:
        ("Ariel", "Elizalde") -> "Ariel Elizalde"
        ("María José", "Pérez López") -> "María José Pérez López"
    """
    return f"{nombre.strip()} {apellido.strip()}"
