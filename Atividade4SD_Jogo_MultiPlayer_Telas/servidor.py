import rpyc
import random
import time
import threading
from rpyc.utils.server import ThreadedServer

PORTA = 18861
JOGADORES_POR_PARTIDA = 3 # Baseado no seu diagrama

class ServicoMatchmaking(rpyc.Service):
    # Dicionários e listas compartilhadas por todas as conexões
    jogadores = {}      # {id_jogador: {'username': ..., 'estado': ..., 'partida_id': ...}}
    fila_de_espera = [] # [id_jogador, ...]
    partidas = {}       # {partida_id: {'jogadores': {id_jogador: {'aceitou': ...}}, 'estado': ...}}
    
    proximo_id_jogador = 0
    proximo_id_partida = 0

    def on_connect(self, conn):
        print("Nova conexão de cliente recebida.")

    def exposed_registrar_jogador(self, username):
        """Registra um jogador no sistema, dá um ID e o coloca no estado 'OCIOSO'."""
        meu_id = ServicoMatchmaking.proximo_id_jogador
        ServicoMatchmaking.jogadores[meu_id] = {
            'username': username,
            'estado': 'OCIOSO', # OCIOSO, NA_FILA, CONFIRMANDO_PARTIDA, EM_PARTIDA
            'partida_id': None,
            'dados_jogo': { # Dados que serão usados QUANDO o jogo começar
                'x': random.randint(-350, 350), 'y': random.randint(-250, 250), 
                'color': random.choice(["red", "blue", "yellow", "orange", "purple", "white"])
            }
        }
        ServicoMatchmaking.proximo_id_jogador += 1
        print(f"Jogador '{username}' (ID: {meu_id}) entrou no sistema.")
        return meu_id

    def exposed_buscar_partida(self, id_jogador):
        """Move o jogador do estado 'OCIOSO' para 'NA_FILA'."""
        if id_jogador not in ServicoMatchmaking.fila_de_espera:
            ServicoMatchmaking.jogadores[id_jogador]['estado'] = 'NA_FILA'
            ServicoMatchmaking.fila_de_espera.append(id_jogador)
            print(f"Jogador {id_jogador} entrou na fila. Jogadores na fila: {len(ServicoMatchmaking.fila_de_espera)}")
        return True

    def exposed_aceitar_partida(self, id_jogador):
        """Registra que um jogador aceitou a partida encontrada."""
        partida_id = ServicoMatchmaking.jogadores[id_jogador].get('partida_id')
        if partida_id is not None and partida_id in ServicoMatchmaking.partidas:
            partida = ServicoMatchmaking.partidas[partida_id]
            if id_jogador in partida['jogadores']:
                partida['jogadores'][id_jogador]['aceitou'] = True
                print(f"Jogador {id_jogador} aceitou a partida {partida_id}")
        return True

    def exposed_obter_status(self, id_jogador):
        """Função PRINCIPAL do cliente: pergunta 'O que eu devo fazer/ver agora?'"""
        if id_jogador not in ServicoMatchmaking.jogadores:
            return {'estado': 'DESCONECTADO'}
        
        jogador = ServicoMatchmaking.jogadores[id_jogador]
        estado_atual = jogador['estado']
        
        # Se estiver confirmando, envia o status da confirmação
        if estado_atual == 'CONFIRMANDO_PARTIDA':
            partida_id = jogador['partida_id']
            partida = ServicoMatchmaking.partidas[partida_id]
            jogadores_na_partida = partida['jogadores']
            aceites = sum(1 for p in jogadores_na_partida.values() if p['aceitou'])
            return {'estado': 'CONFIRMANDO_PARTIDA', 'total_jogadores': len(jogadores_na_partida), 'jogadores_aceitos': aceites}
        
        # Se estiver em jogo, envia o estado da partida
        if estado_atual == 'EM_PARTIDA':
            partida_id = jogador['partida_id']
            partida = ServicoMatchmaking.partidas[partida_id]
            # Envia os dados do jogo SÓ dos jogadores desta partida
            estado_do_jogo = {pid: ServicoMatchmaking.jogadores[pid]['dados_jogo'] for pid in partida['jogadores']}
            return {'estado': 'EM_PARTIDA', 'estado_jogo': list(estado_do_jogo.items())}
        
        # Caso contrário, envia o estado simples ('OCIOSO' ou 'NA_FILA')
        return {'estado': estado_atual}

    def exposed_atualizar_movimento(self, id_jogador, x, y):
        """Recebe a nova posição de um jogador e atualiza no servidor."""
        if id_jogador in ServicoMatchmaking.jogadores:
            ServicoMatchmaking.jogadores[id_jogador]['dados_jogo']['x'] = x
            ServicoMatchmaking.jogadores[id_jogador]['dados_jogo']['y'] = y
        return "OK"

def logica_matchmaking_juiz():
    """Esta é a 'thread do juiz'. Roda em segundo plano no servidor."""
    while True:
        # 1. Tenta criar novas partidas
        if len(ServicoMatchmaking.fila_de_espera) >= JOGADORES_POR_PARTIDA:
            jogadores_da_partida = ServicoMatchmaking.fila_de_espera[:JOGADORES_POR_PARTIDA]
            ServicoMatchmaking.fila_de_espera = ServicoMatchmaking.fila_de_espera[JOGADORES_POR_PARTIDA:]
            
            id_nova_partida = ServicoMatchmaking.proximo_id_partida
            ServicoMatchmaking.proximo_id_partida += 1
            
            ServicoMatchmaking.partidas[id_nova_partida] = {
                'jogadores': {pid: {'aceitou': False} for pid in jogadores_da_partida},
                'estado': 'CONFIRMANDO',
                'timestamp': time.time()
            }
            
            # Muda o estado de todos os jogadores para 'CONFIRMANDO'
            for pid in jogadores_da_partida:
                ServicoMatchmaking.jogadores[pid]['estado'] = 'CONFIRMANDO_PARTIDA'
                ServicoMatchmaking.jogadores[pid]['partida_id'] = id_nova_partida
            
            print(f"Partida {id_nova_partida} criada para {jogadores_da_partida}. Aguardando confirmação...")

        # 2. Gerencia partidas em confirmação (Time-out e Início)
        partidas_a_remover = []
        for pid, partida in ServicoMatchmaking.partidas.items():
            if partida['estado'] == 'CONFIRMANDO':
                agora = time.time()
                todos_aceitaram = all(p['aceitou'] for p in partida['jogadores'].values())
                
                # SUCESSO: Todos aceitaram
                if todos_aceitaram:
                    partida['estado'] = 'EM_ANDAMENTO'
                    # Muda o estado de todos os jogadores para 'EM_PARTIDA'
                    for id_jogador in partida['jogadores']:
                        ServicoMatchmaking.jogadores[id_jogador]['estado'] = 'EM_PARTIDA'
                    print(f"Partida {pid} iniciada!")
                
                # FALHA: Timeout de 10 segundos
                elif agora - partida['timestamp'] > 10: 
                    print(f"Partida {pid} expirou por timeout.")
                    for id_jogador in partida['jogadores']:
                        # Devolve para a fila quem aceitou
                        if partida['jogadores'][id_jogador]['aceitou']:
                            ServicoMatchmaking.jogadores[id_jogador]['estado'] = 'NA_FILA'
                            ServicoMatchmaking.fila_de_espera.append(id_jogador)
                        else: # Devolve para o menu quem não aceitou
                            ServicoMatchmaking.jogadores[id_jogador]['estado'] = 'OCIOSO'
                    partidas_a_remover.append(pid)

        # Limpa as partidas que expiraram
        for pid in partidas_a_remover:
            del ServicoMatchmaking.partidas[pid]

        time.sleep(1) # O "juiz" verifica o estado a cada 1 segundo

if __name__ == "__main__":
    print(f"Servidor de Matchmaking iniciado na porta {PORTA}.")
    # Inicia a thread do "juiz" em segundo plano
    thread_matchmaking = threading.Thread(target=logica_matchmaking_juiz, daemon=True)
    thread_matchmaking.start()
    
    t = ThreadedServer(ServicoMatchmaking, port=PORTA)
    t.start()