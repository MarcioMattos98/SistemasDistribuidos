import turtle
import rpyc

HOST = 'localhost' 
PORTA = 18861
username = input("Digite seu nome de jogador: ")

try:
    print(f"\nConectando ao servidor em {HOST}:{PORTA}...")
    proxy = rpyc.connect(HOST, PORTA)
    meu_id, meus_dados = proxy.root.registrar_jogador(username)
    print(f"Conectado com sucesso! ID: {meu_id} | Cor: {meus_dados['color']}\n")
except Exception as e:
    print(f"\n[ERRO] Não foi possível conectar ao servidor: {e}")
    exit()

wn = turtle.Screen()
wn.title(f"Jogo Distribuído - Jogador: {username} (ID: {meu_id})")
wn.bgcolor("green")
wn.setup(width=800, height=600)
wn.tracer(0)

largura_tela = wn.window_width()
altura_tela = wn.window_height()

meu_jogador = turtle.Turtle()
meu_jogador.speed(0)
meu_jogador.shape("circle")
meu_jogador.color(meus_dados['color'])
meu_jogador.penup()
meu_jogador.direction = "stop"

outros_jogadores = {}
ultima_posicao = (0, 0)

# Funções de Movimento
def go_up(): meu_jogador.direction = "up"
def go_down(): meu_jogador.direction = "down"
def go_left(): meu_jogador.direction = "left"
def go_right(): meu_jogador.direction = "right"

def move():
    global ultima_posicao
    limite_y, limite_x = altura_tela / 2, largura_tela / 2
    offset_bola = 15

    if meu_jogador.direction == "up" and meu_jogador.ycor() < limite_y - offset_bola:
        meu_jogador.sety(meu_jogador.ycor() + 5)
    if meu_jogador.direction == "down" and meu_jogador.ycor() > -limite_y - offset_bola:
        meu_jogador.sety(meu_jogador.ycor() - 5)
    if meu_jogador.direction == "left" and meu_jogador.xcor() > -limite_x - offset_bola:
        meu_jogador.setx(meu_jogador.xcor() - 5)
    if meu_jogador.direction == "right" and meu_jogador.xcor() < limite_x - offset_bola:
        meu_jogador.setx(meu_jogador.xcor() + 5)
    
    posicao_atual = (meu_jogador.xcor(), meu_jogador.ycor())
    if posicao_atual != ultima_posicao:
        proxy.root.atualizar_movimento(meu_id, posicao_atual[0], posicao_atual[1])
        ultima_posicao = posicao_atual

def on_close():
    try:
        proxy.root.desconectar_jogador(meu_id)
    except EOFError:
        print("Conexão com o servidor já estava fechada.")
    finally:
        wn.bye()

# Controles
wn.listen()
wn.onkeypress(go_up, "w")
wn.onkeypress(go_down, "s")
wn.onkeypress(go_left, "a")
wn.onkeypress(go_right, "d")
turtle.getcanvas().winfo_toplevel().protocol("WM_DELETE_WINDOW", on_close)


def game_loop():
    move()


    estado_jogo = proxy.root.obter_estado_jogo()
    
    for id_jogador, dados in estado_jogo:
        if id_jogador == meu_id:
            continue

        if id_jogador not in outros_jogadores:
            novo_jogador = turtle.Turtle()
            novo_jogador.speed(0)
            novo_jogador.shape("circle")
            novo_jogador.color(dados['color'])
            novo_jogador.penup()
            outros_jogadores[id_jogador] = novo_jogador 
            print(f"Novo jogador detectado: {dados['username']} (ID: {id_jogador})")


        outros_jogadores[id_jogador].goto(dados['x'], dados['y'])
    
    wn.update() 
    
    wn.ontimer(game_loop, 50) 


game_loop()
wn.mainloop()