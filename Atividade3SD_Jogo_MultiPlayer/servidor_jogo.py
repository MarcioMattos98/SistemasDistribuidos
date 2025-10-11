# servidor_jogo.py
import rpyc
import random
from rpyc.utils.server import ThreadedServer

PORTA = 18861

class ServicoJogo(rpyc.Service):
    jogadores = {}
    proximo_id = 0
    
    cores = ["carmesim", "azul-claro", "rosa", "dourado", "vermelho", "marrom", 
             "azul", "amarelo", "laranja", "roxo", "branco", "ciano"]

    def on_connect(self, conn):
        print(f"Nova conexão recebida. Total de jogadores agora: {len(self.jogadores)}")

    def on_disconnect(self, conn):
        print("A conexão de um cliente foi perdida.")

    def exposed_registrar_jogador(self, username):
        meu_id = ServicoJogo.proximo_id 
        
        dados_jogador = {
            'x': 0, 'y': 0,
            'color': random.choice(ServicoJogo.cores),
            'username': username
        }
        
        ServicoJogo.jogadores[meu_id] = dados_jogador 
        ServicoJogo.proximo_id += 1
        
        print(f"Jogador registrado: {username} (ID: {meu_id}) - Total: {len(ServicoJogo.jogadores)}")
        return meu_id, dados_jogador

    def exposed_obter_estado_jogo(self):
        return list(ServicoJogo.jogadores.items())

    def exposed_atualizar_movimento(self, id, x, y):
        if id in ServicoJogo.jogadores:
            ServicoJogo.jogadores[id]['x'] = x
            ServicoJogo.jogadores[id]['y'] = y
        return "OK"
    
    def exposed_desconectar_jogador(self, id):
        if id in ServicoJogo.jogadores:
            username = ServicoJogo.jogadores[id]['username']
            del ServicoJogo.jogadores[id]
            print(f"Jogador desconectado: {username} (ID: {id}) - Total: {len(ServicoJogo.jogadores)}")
        return "OK"

if __name__ == "__main__":
    print(f"Servidor de Jogo iniciado na porta {PORTA}. Aguardando jogadores...")
    t = ThreadedServer(ServicoJogo, port=PORTA)
    t.start()