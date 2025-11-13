import socket
import ssl
import hashlib
import time
import threading


SEGREDO = "segredo_comp"
token_esperado = hashlib.sha256(SEGREDO.encode()).hexdigest()
HOST = '0.0.0.0' 
PORTA = 5000

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

def handle_client(conn, addr):
    """ Cuida de uma conexão de cliente em uma thread separada """
    print(f"[Servidor] Conectado por {addr}")
    try:
        # 1. Recebe os dados
        data = conn.recv(1024).decode()
        
        # 2. Processa a mensagem e o token
        try:
            msg, token_recebido = data.split('|')
        except ValueError:
            print("[Servidor] Erro: Mensagem mal formatada.")
            conn.send("Erro: Formato inválido.".encode())
            conn.close()
            return

        print(f"[Servidor] Mensagem recebida: '{msg}'")

        # 3. Verifica a Segurança (Parte 3)
        if token_recebido != token_esperado:
            print("[Servidor] FALHA BIZANTINA! Token inválido.")
            conn.send("Acesso negado (Token inválido).".encode())
            conn.close()
            return

        # 4. Lógica de Negócios (Reage aos testes)
        resposta = "Autenticação bem-sucedida!"

        if "TEST_TIMEOUT" in msg:
            print("[Servidor] Simulação de timeout iniciada (5s)...")
            time.sleep(5)
            resposta = "Resposta (após 5s)."
    

        # Responde
        conn.send(resposta.encode())

    except ssl.SSLError as e:
        print(f"[Servidor] Erro de SSL: {e}")
    except Exception as e:
        print(f"[Servidor] Erro: {e}")
    finally:
        print(f"[Servidor] Conexão com {addr} fechada.")
        conn.close()

def start_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORTA))
    sock.listen(5)
    print(f"[Servidor] Servidor TLS aguardando conexão na porta {PORTA}...")


    ssock = context.wrap_socket(sock, server_side=True)


    while True:
        try:
            conn, addr = ssock.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()
        except Exception as e:
            print(f"[Servidor] Erro ao aceitar conexão: {e}")

if __name__ == "__main__":
    start_server()