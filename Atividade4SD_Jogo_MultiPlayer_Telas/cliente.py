import turtle
import rpyc

# --- ETAPA 1: Conexão e Registro ---
HOST = 'localhost' 
PORTA = 18861 
username = input("Digite seu nome de jogador: ")

try:
    proxy = rpyc.connect(HOST, PORTA)
    meu_id = proxy.root.registrar_jogador(username)
    print(f"Conectado ao servidor. Seu ID é: {meu_id}\n")
except Exception as e:
    print(f"\n[ERRO] Não foi possível conectar ao servidor: {e}")
    exit()

# --- ETAPA 2: Configuração da Tela e UI ---
wn = turtle.Screen()
wn.title(f"Jogo - {username} (ID: {meu_id})")
wn.bgcolor("grey20") # Fundo cinza do lobby
wn.setup(width=800, height=600)
wn.tracer(0)

ESTADO_ATUAL_CLIENTE = '' # Controla qual tela estamos mostrando
partida_iniciada = False

# --- Elementos da UI ---
ui_writer = turtle.Turtle()
ui_writer.hideturtle()
ui_writer.color("white")
ui_writer.penup()

botao_principal = turtle.Turtle()
botao_principal.shape("square")
botao_principal.shapesize(stretch_wid=2, stretch_len=10)
botao_principal.penup()

# --- ETAPA 3: Funções de Lógica e Desenho ---

def desenhar_botao(pos_y, cor, texto):
    botao_principal.goto(0, pos_y)
    botao_principal.color(cor)
    botao_principal.showturtle()
    ui_writer.goto(0, pos_y - 10)
    ui_writer.write(texto, align="center", font=("Arial", 16, "normal"))

def desenhar_tela_inicial():
    ui_writer.clear()
    ui_writer.goto(0, 100)
    ui_writer.write("Bem-vindo ao Jogo!", align="center", font=("Arial", 24, "bold"))
    desenhar_botao(-50, "green", "Buscar Partida")

def desenhar_tela_busca():
    botao_principal.hideturtle()
    ui_writer.clear()
    ui_writer.goto(0, 50)
    ui_writer.write("Procurando partida...", align="center", font=("Arial", 24, "bold"))

def desenhar_tela_aceitar(dados):
    ui_writer.clear()
    ui_writer.goto(0, 100)
    ui_writer.write("Partida Encontrada!", align="center", font=("Arial", 24, "bold"))
    ui_writer.goto(0, 50)
    status_texto = f"{dados['jogadores_aceitos']} / {dados['total_jogadores']} jogadores aceitaram"
    ui_writer.write(status_texto, align="center", font=("Arial", 20, "normal"))
    desenhar_botao(-50, "blue", "Aceitar")

def on_click_botao(x, y):
    global ESTADO_ATUAL_CLIENTE
    if ESTADO_ATUAL_CLIENTE == 'OCIOSO':
        proxy.root.buscar_partida(meu_id)
    elif ESTADO_ATUAL_CLIENTE == 'CONFIRMANDO_PARTIDA':
        proxy.root.aceitar_partida(meu_id)
        botao_principal.hideturtle() 
        ui_writer.clear() 

# --- Lógica do Jogo (quando a partida começa) ---
meu_jogador = turtle.Turtle()
meu_jogador.hideturtle()
outros_jogadores = {}
ultima_posicao = (0, 0)
largura_tela = wn.window_width()
altura_tela = wn.window_height()

def iniciar_partida_visual(estado_inicial):
    """Prepara a tela e os controles para o jogo real."""
    global ultima_posicao, partida_iniciada
    
    partida_iniciada = True
    botao_principal.hideturtle()
    ui_writer.clear()
    wn.bgcolor("green") # Fundo do jogo é verde

    dados_iniciais = dict(estado_inicial).get(meu_id)
    if not dados_iniciais: return

    meu_jogador.shape("circle")
    meu_jogador.color(dados_iniciais['color'])
    meu_jogador.penup()
    meu_jogador.goto(dados_iniciais['x'], dados_iniciais['y'])
    meu_jogador.direction = "stop"
    meu_jogador.showturtle()
    ultima_posicao = (meu_jogador.xcor(), meu_jogador.ycor())
    
    def go_up(): meu_jogador.direction = "up"
    def go_down(): meu_jogador.direction = "down"
    def go_left(): meu_jogador.direction = "left"
    def go_right(): meu_jogador.direction = "right"
    
    wn.listen()
    wn.onkeypress(go_up, "w")
    wn.onkeypress(go_down, "s")
    wn.onkeypress(go_left, "a")
    wn.onkeypress(go_right, "d")

def loop_do_jogo(estado_jogo):
    """Este é o loop de jogo que funciona (baseado no nosso código da Etapa 1)."""
    global ultima_posicao
    
    # 1. Movimentação e Limites da Tela
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
    
    # 2. Publica sua posição se ela mudou
    posicao_atual = (meu_jogador.xcor(), meu_jogador.ycor())
    if posicao_atual != ultima_posicao:
        proxy.root.atualizar_movimento(meu_id, posicao_atual[0], posicao_atual[1])
        ultima_posicao = posicao_atual

    # 3. Renderização dos outros jogadores
    ids_ativos = {id_jogador for id_jogador, dados in estado_jogo}
    for id_local in list(outros_jogadores.keys()):
        if id_local not in ids_ativos:
            outros_jogadores[id_local].hideturtle()
            del outros_jogadores[id_local]

    for id_jogador, dados in estado_jogo:
        if id_jogador == meu_id: continue
        if id_jogador not in outros_jogadores:
            novo_jogador = turtle.Turtle()
            novo_jogador.speed(0)
            novo_jogador.shape("circle")
            novo_jogador.color(dados['color'])
            novo_jogador.penup()
            outros_jogadores[id_jogador] = novo_jogador
        outros_jogadores[id_jogador].goto(dados['x'], dados['y'])

# --- ETAPA 4: O Loop Principal do Cliente (Máquina de Estados) ---

def loop_principal_cliente():
    global ESTADO_ATUAL_CLIENTE, partida_iniciada
    
    try:
        status = proxy.root.obter_status(meu_id)
        novo_estado = status['estado']
    except EOFError:
        print("Perda de conexão com o servidor. Fechando.")
        wn.bye()
        return

    # Se o servidor nos colocou em um novo estado, redesenha a tela
    if novo_estado != ESTADO_ATUAL_CLIENTE:
        ESTADO_ATUAL_CLIENTE = novo_estado
        if ESTADO_ATUAL_CLIENTE == 'OCIOSO':
            desenhar_tela_inicial()
        elif ESTADO_ATUAL_CLIENTE == 'NA_FILA':
            desenhar_tela_busca()
    
    # Estados que precisam de atualização constante
    if ESTADO_ATUAL_CLIENTE == 'CONFIRMANDO_PARTIDA':
        desenhar_tela_aceitar(status) # Atualiza a contagem de aceites
    
    elif ESTADO_ATUAL_CLIENTE == 'EM_PARTIDA':
        # Se o jogo não foi iniciado visualmente, inicie-o
        if not partida_iniciada:
            iniciar_partida_visual(status['estado_jogo'])
        
        # Roda o loop do jogo (movimentação e renderização)
        loop_do_jogo(status['estado_jogo'])
    
    wn.update()
    # No lobby, a verificação é lenta. No jogo, é rápida.
    intervalo = 50 if partida_iniciada else 500
    wn.ontimer(loop_principal_cliente, intervalo)

# --- INÍCIO ---
loop_principal_cliente() 
botao_principal.onclick(on_click_botao) 
wn.mainloop()