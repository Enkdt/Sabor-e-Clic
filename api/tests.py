#Envia a porra do email, vou ver como fazer os outros tests funcionarem
import sys
from app import app
from utils import generateToken, sendAuthEmail

def main():
    if len(sys.argv) != 2:
        print("Tem que ser: python3 tests.py <email>")
        return 1

    recipient = sys.argv[1]
    with app.app_context():
        token = generateToken(recipient, "validation", 30)
        sendAuthEmail(recipient, token)

    print(f"Email enviado para {recipient}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
