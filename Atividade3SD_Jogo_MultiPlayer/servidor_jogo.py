# servidor_jogo.py
import rpyc
import random
from rpyc.utils.server import ThreadedServer

class ServicoJogo(rpyc.Service):
    def __init__(self):
        self.jogadores = {}
        self.proximo_id = 0 # Este contador funciona se o servidor não for reiniciado
        self.cores_disponiveis = ["red", "blue", "yellow", "orange", "purple", "white", "cyan"]
        print("Servidor de Jogo iniciado.")

    def on_disconnect(self, conn):
        print("Um cliente se desconectou.")

    def exposed_conectar(self):
        meu_id = self.proximo_id
        cor = random.choice(self.cores_disponiveis)
        estado_inicial = {'x': 0, 'y': 0, 'color': cor}
        self.jogadores[meu_id] = estado_inicial
        self.proximo_id += 1 # O ID é incrementado para o próximo jogador
        print(f"Jogador {meu_id} conectado com a cor {cor}.")
        return meu_id, cor

    def exposed_atualizar_posicao(self, player_id, x, y):
        if player_id in self.jogadores:
            self.jogadores[player_id]['x'] = x
            self.jogadores[player_id]['y'] = y
        return "OK"

    def exposed_obter_estado_jogo(self):
        return list(self.jogadores.items())

if __name__ == "__main__":
    t = ThreadedServer(ServicoJogo, port=18861)
    t.start()