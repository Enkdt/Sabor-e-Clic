#Envia a lindeza do email, vou ver como fazer os outros tests funcionarem
import sys
from app import app
from utils import sendAuthEmail

def main():
    if len(sys.argv) != 2:
        print("Sintaxe: python3 tests.py <email>")
        return 1
    recipient = sys.argv[1]
    with app.app_context():
        sendAuthEmail(recipient)
    print("Email de verificação enviado")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
