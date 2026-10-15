from db import get_db
from zxcvbn import zxcvbn
import re

def check_email(email: str):
    emailFormat = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}"
    return re.fullmatch(emailFormat,email)

def check_pwd_strength(pwd: str,usr_imp):
    if not pwd or len(pwd) < 8:
        return False
    return zxcvbn(pwd,user_inputs=(usr_imp or []))['score'] >=3

def norm_cpf(cpf:str) -> str:
    return re.sub(r"\D","" ,cpf);

#Retorna bool pra poder trocar o erro de acordo com a necessidade
def check_cpf(cpf:str) -> bool:
    cpf = norm_cpf(cpf)
    if not re.fullmatch(r"\d{11}",cpf):
        return False
    if cpf == cpf[0]*11:
        return False
    for i in (9,10):
        total = sum(map(lambda j:int(cpf[j])*((i+1)-j),range(i)))
        targ_digit = (total*10%11) % 10
        if targ_digit != int(cpf[i]): 
            return False
    return True

def check_json(data):
    return isinstance(data, dict)