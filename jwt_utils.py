import jwt
from jwt import InvalidTokenError, ExpiredSignatureError

# Секретный ключ (должен быть защищён)
SECRET_KEY = "your-secret-key"

def verify_jwt(token: str):
    """
    Проверяет JWT-токен.

    :param token: JWT-токен в виде строки.
    :return: Декодированные данные, если токен валиден.
    :raises: ValueError, если токен невалиден или истёк.
    """
    try:
        # Расшифровываем и проверяем токен
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded_token
    except ExpiredSignatureError:
        raise ValueError("JWT-токен истёк")
    except InvalidTokenError:
        raise ValueError("JWT-токен невалиден")
