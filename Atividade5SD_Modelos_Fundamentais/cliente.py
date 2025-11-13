import socket
import ssl
import hashlib
import time


HOST_SERVIDOR = 'servidor-app' 
PORTA_SERVIDOR = 5000
SEGREDO = "segredo_comp"


context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE 

def get_token():
    """ Gera o token de segurança correto """
    return hashlib.sha256(SEGREDO.encode()).hexdigest()

def measure_time(func):
    """ Um "decorador" para medir o tempo de execução de qualquer teste """
    def wrapper(*args, **kwargs):
        print("\n" + "="*30)
        start_time = time.time()
        
        func(*args, **kwargs) 
        
        end_time = time.time()
        duration = (end_time - start_time) * 1000 
        print(f"--- Tempo total do teste: {duration:.2f} ms ---")
        print("="*30 + "\n")
    return wrapper

def connect_to_server():
    """ Função central para criar e conectar o socket SSL """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssock = context.wrap_socket(sock, server_hostname=HOST_SERVIDOR)
        ssock.connect((HOST_SERVIDOR, PORTA_SERVIDOR))
        return ssock
    except ConnectionRefusedError:
        print("[Cliente] ERRO: Servidor recusou a conexão.")
    except Exception as e:
        print(f"[Cliente] ERRO ao conectar: {e}")
    return None



@measure_time
def run_test_baseline():
    """ Teste 1: Interação Simples (Partes 1 & 3) """
    print("Executando: Teste de Interação Padrão (com TLS e Token)")
    ssock = connect_to_server()
    if not ssock: return

    msg = "Olá servidor!"
    pacote = f"{msg}|{get_token()}"
    
    ssock.send(pacote.encode())
    resposta = ssock.recv(1024).decode()
    print(f"[Cliente] Resposta do Servidor: {resposta}")
    ssock.close()

@measure_time
def run_test_timeout():
    """ Teste 2: Falha de Timeout (Parte 2) """
    print("Executando: Teste de Falha de Timeout (Limite de 3s)")
    ssock = connect_to_server()
    if not ssock: return
    

    ssock.settimeout(3.0) 

    msg = "TEST_TIMEOUT" 
    pacote = f"{msg}|{get_token()}"
    
    try:
        ssock.send(pacote.encode())
        resposta = ssock.recv(1024).decode()
        print(f"[Cliente] Resposta do Servidor: {resposta}")
    except socket.timeout:
        print("[Cliente] SUCESSO DO TESTE: Timeout de 3s atingido!")
    except Exception as e:
        print(f"[Cliente] Erro inesperado: {e}")
    finally:
        ssock.close()

@measure_time
def run_test_bizantine():
    """ Teste 3: Falha Bizantina (Desafio) """
    print("Executando: Teste de Falha Bizantina (Token Inválido)")
    ssock = connect_to_server()
    if not ssock: return

    msg = "Olá, sou um impostor"
    token_falso = "token_falso_bizantino_12345"
    pacote = f"{msg}|{token_falso}"
    
    ssock.send(pacote.encode())
    resposta = ssock.recv(1024).decode()
    print(f"[Cliente] Resposta do Servidor: {resposta}")
    if "Acesso negado" in resposta:
        print("[Cliente] SUCESSO DO TESTE: Servidor detectou a falha bizantina.")
    ssock.close()

@measure_time
def run_test_retry():
    """ Teste 4: Lógica de Retry (Parte 2) """
    print("Executando: Teste de Lógica de Retry (Falha de Conexão)")
    host_falso = "servidor-que-nao-existe"
    
    for i in range(3):
        try:
            print(f"[Cliente] Tentando conectar em '{host_falso}'... ({i+1}/3)")
            sock_falso = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_falso.settimeout(1.0)
            sock_falso.connect((host_falso, PORTA_SERVIDOR))
        except Exception as e:
            print(f"[Cliente] Falha esperada: {e}")
            time.sleep(1)
    print("[Cliente] SUCESSO DO TESTE: Loop de retry concluído.")


def main_menu():
    while True:
        print("\n--- PAINEL DE CONTROLE - SISTEMAS DISTRIBUÍDOS ---")
        print("Escolha um teste para executar:")
        print("1. Teste Padrão (Interação, Token, TLS e Medição de Tempo)")
        print("2. Teste de Timeout (Falha de Tempo)")
        print("3. Teste Bizantino (Falha de Segurança)")
        print("4. Teste de Retry (Falha de Conexão)")
        print("5. Sair")
        
        choice = input("Opção: ")
        
        if choice == '1':
            run_test_baseline()
        elif choice == '2':
            run_test_timeout()
        elif choice == '3':
            run_test_bizantine()
        elif choice == '4':
            run_test_retry()
        elif choice == '5':
            print("Encerrando...")
            break
        else:
            print("Opção inválida, tente novamente.")

if __name__ == "__main__":
    print("Aguardando o servidor Docker ficar pronto (5s)...")
    time.sleep(5) 
    main_menu()