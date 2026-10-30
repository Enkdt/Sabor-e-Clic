from zxcvbn import zxcvbn
import re

def check_email(email: str):
    """Verifica o formato do email"""
    email_format = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}"
    return isinstance(email, str) and bool(re.fullmatch(email_format, email))

def check_pwd_strength(pwd: str,usr_imp):
    """Verifica a força da senha, retorna bool"""
    if not pwd or len(pwd) < 8:
        return False
    return zxcvbn(pwd,user_inputs=(usr_imp or []))['score'] >=3

def check_json(data):
    """Verifica se o dado está formatado em json"""
    return isinstance(data, dict)