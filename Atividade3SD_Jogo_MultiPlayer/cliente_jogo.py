# cliente_jogo.py
import turtle
import time
import rpyc

# --- Conexão ---
conn = rpyc.connect('localhost', 18861)
servico_remoto = conn.root

meu_id, minha_cor = servico_remoto.conectar()
print(f"Conectado ao jogo! Meu ID é {meu_id} e minha cor é {minha_cor}")

# --- Configuração da Tela ---
wn = turtle.Screen()
wn.title(f"Move Game - Jogador {meu_id}")
wn.bgcolor("green")
wn.setup(width=800, height=600) # Definindo um tamanho fixo para facilitar
wn.tracer(0) 

# --- NOVO: Capturando as dimensões da tela ---
largura_tela = wn.window_width()
altura_tela = wn.window_height()

# --- Jogador Local ---
head = turtle.Turtle()
head.speed(0)
head.shape("circle")
head.color(minha_cor)
head.penup()
head.goto(0,0)
head.direction = "stop"

outros_jogadores = {}

# --- Funções de Movimento ---
def go_up():
    head.direction = "up"
def go_down():
    head.direction = "down"
def go_left():
    head.direction = "left"
def go_right():
    head.direction = "right"
def close():
    wn.bye()

# --- FUNÇÃO move() MODIFICADA ---
def move():
    # Coordenadas dos limites da tela (metade da altura/largura)
    limite_y = altura_tela / 2
    limite_x = largura_tela / 2
    
    # Offset para a borda da bolinha (para não passar metade pra fora)
    offset_bola = 15

    if head.direction == "up":
        # Só se move para cima se não tiver atingido a borda superior
        if head.ycor() < limite_y - offset_bola:
            y = head.ycor()
            head.sety(y + 5)
            
    if head.direction == "down":
        # Só se move para baixo se não tiver atingido a borda inferior
        if head.ycor() > -limite_y + offset_bola:
            y = head.ycor()
            head.sety(y - 5)

    if head.direction == "left":
        # Só se move para a esquerda se não tiver atingido a borda esquerda
        if head.xcor() > -limite_x + offset_bola:
            x = head.xcor()
            head.setx(x - 5)

    if head.direction == "right":
        # Só se move para a direita se não tiver atingido a borda direita
        if head.xcor() < limite_x - offset_bola:
            x = head.xcor()
            head.setx(x + 5)

# --- Controles do Teclado ---
wn.listen()
wn.onkeypress(go_up, "w")
wn.onkeypress(go_down, "s")
wn.onkeypress(go_left, "a")
wn.onkeypress(go_right, "d")
wn.onkeypress(close, "Escape")

# --- Loop de Jogo ---
def game_loop():
    wn.update()
    move()
    x_atual, y_atual = head.xcor(), head.ycor()
    servico_remoto.atualizar_posicao(meu_id, x_atual, y_atual)
    
    estado_jogo = servico_remoto.obter_estado_jogo()

    for player_id, estado in estado_jogo:
        if player_id == meu_id:
            continue

        if player_id not in outros_jogadores:
            novo_turtle = turtle.Turtle()
            novo_turtle.speed(0)
            novo_turtle.shape("circle")
            novo_turtle.color(estado['color'])
            novo_turtle.penup()
            outros_jogadores[player_id] = novo_turtle
            print(f"Novo jogador {player_id} entrou na partida!")

        outros_jogadores[player_id].goto(estado['x'], estado['y'])
    
    wn.ontimer(game_loop, 50)

# --- INÍCIO DO PROGRAMA ---
game_loop()
wn.mainloop()