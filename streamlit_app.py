import streamlit as st
import time
import random
import copy

# ─────────────────────────────────────────────
# PARÂMETROS GERAIS
# ─────────────────────────────────────────────
PREVIEW_ROWS = 4
GAME_ROWS    = 20
INNER_W      = 20  # largura útil entre <!  !>
LINHA_VAZIA  = "<!" + " ." * 10 + " !>"
EMPTY_CELL = " ."
BLOCK_CELL = "[]" # Usar string consistente para blocos

BASE_SLEEP   = 0.05      # intervalo base do loop (usado para calcular velocidade)
LEVEL_STEP   = 30        # segundos para subir de nível
SPEED_STEP   = 0.005     # quanto reduz o sleep a cada nível
MIN_SLEEP    = 0.02      # limite inferior
DROP_MOD     = 4         # A peça desce a cada X "ticks" lógicos

def linha_texto(txt: str) -> str:
    return "<!" + txt.center(INNER_W) + " !>"

# ─────────────────────────────────────────────
# PEÇAS
# ─────────────────────────────────────────────
peca_I = [[BLOCK_CELL], [BLOCK_CELL], [BLOCK_CELL], [BLOCK_CELL]]
peca_O = [[BLOCK_CELL, BLOCK_CELL], [BLOCK_CELL, BLOCK_CELL]]
peca_T = [['.', BLOCK_CELL, '.'], [BLOCK_CELL, BLOCK_CELL, BLOCK_CELL]]
peca_L = [[BLOCK_CELL, '.'], [BLOCK_CELL, '.'], [BLOCK_CELL, BLOCK_CELL]]
peca_J = [['.', BLOCK_CELL], ['.', BLOCK_CELL], [BLOCK_CELL, BLOCK_CELL]]
peca_S = [['.', BLOCK_CELL, BLOCK_CELL], [BLOCK_CELL, BLOCK_CELL, '.']]
peca_Z = [[BLOCK_CELL, BLOCK_CELL, '.'], ['.', BLOCK_CELL, BLOCK_CELL]]
TODAS  = [peca_I, peca_O, peca_T, peca_L, peca_J, peca_S, peca_Z]

rotacionar = lambda p: [list(reversed(c)) for c in zip(*p)]

# ─────────────────────────────────────────────
# FUNÇÕES DO TABULEIRO
# ─────────────────────────────────────────────
def criar_tabuleiro_data():
    # Retorna a estrutura de dados, não as strings formatadas diretamente
    # Cada célula será EMPTY_CELL ou BLOCK_CELL
    # A renderização cuidará do "<! ... !>"
    preview = [[EMPTY_CELL for _ in range(INNER_W // 2)] for _ in range(PREVIEW_ROWS)]
    jogo    = [[EMPTY_CELL for _ in range(INNER_W // 2)] for _ in range(GAME_ROWS)]
    return {"preview": preview, "game": jogo}

def formatar_tabuleiro_para_exibicao(tab_data, proxima_peca_preview=None, score=0, level=0, msg_extra=None, player_id=None):
    linhas_finais = []

    # Preview Area
    linhas_finais.append(linha_texto("PRÓXIMA PEÇA"))
    preview_display = [[' ' for _ in range(INNER_W)] for _ in range(PREVIEW_ROWS -1)]
    if proxima_peca_preview:
        peca_render = piece_to_preview_lines(proxima_peca_preview)
        for r_idx, r_val in enumerate(peca_render):
            if r_idx < PREVIEW_ROWS - 1:
                # Centralizar a peça no preview
                start_col = (INNER_W - len(r_val)) // 2
                for c_idx, c_val in enumerate(r_val):
                    if start_col + c_idx < INNER_W:
                        preview_display[r_idx][start_col + c_idx] = c_val
    
    for r in preview_display:
        linhas_finais.append(linha_texto("".join(r)))
    for _ in range(PREVIEW_ROWS - 1 - len(preview_display)): # Preencher se a peça for pequena
         linhas_finais.append(LINHA_VAZIA)


    # Game Area
    tab_render = copy.deepcopy(tab_data["game"]) # Começa com o tabuleiro fixo

    # Desenhar peça atual se houver
    peca_atual = None
    peca_x, peca_y = 0, 0

    if player_id is None: # Single player
        if 'game_1p' in st.session_state and st.session_state.game_1p.get('peca_atual'):
            peca_atual = st.session_state.game_1p['peca_atual']
            peca_x = st.session_state.game_1p['x']
            peca_y = st.session_state.game_1p['y_display'] # y relativo ao topo da area de jogo
    else: # Multiplayer
        if f'game_2p_p{player_id}' in st.session_state and st.session_state[f'game_2p_p{player_id}'].get('alive') and st.session_state[f'game_2p_p{player_id}'].get('peca_atual'):
            peca_atual = st.session_state[f'game_2p_p{player_id}']['peca_atual']
            peca_x = st.session_state[f'game_2p_p{player_id}']['x']
            peca_y = st.session_state[f'game_2p_p{player_id}']['y_display']


    if peca_atual:
        for r_idx, linha_peca in enumerate(peca_atual):
            for c_idx, bloco in enumerate(linha_peca):
                if bloco == BLOCK_CELL:
                    abs_r = peca_y - r_idx # y é a base da peça, r_idx sobe
                    abs_c = peca_x + c_idx
                    if 0 <= abs_r < GAME_ROWS and 0 <= abs_c < (INNER_W // 2):
                        tab_render[abs_r][abs_c] = BLOCK_CELL
    
    for linha_jogo in tab_render:
        linhas_finais.append("<!" + "".join(c for c in linha_jogo) + " !>")

    # Rodapé e Info
    linhas_finais.append("<!=-=-=-=-=-=-=-=-=-=-=!>")
    linhas_finais.append("\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/")
    if player_id is None: # Single player score/level
        linhas_finais.append(linha_texto(f"SCORE: {score:05}"))
        linhas_finais.append(linha_texto(f"NÍVEL: {level}"))
    
    if msg_extra:
        linhas_finais.append(linha_texto(msg_extra))

    return "\n".join(linhas_finais)


def piece_to_preview_lines(peca_data):
    # Converte a estrutura de dados da peça para linhas de texto para o preview
    linhas = []
    for row in peca_data:
        linha_str = ""
        for cell in row:
            linha_str += BLOCK_CELL if cell == BLOCK_CELL else "  " # Dois espaços para '.'
        linhas.append(linha_str.rstrip())
    
    # Normaliza a largura para centralização
    larg_max = max((len(s) for s in linhas), default=0)
    return [l.ljust(larg_max) for l in linhas]


def largura_peca(p): return len(p[0]) if p and len(p) > 0 else 0
def altura_peca(p): return len(p) if p else 0


def colisao(tab_game_data, peca, x_peca, y_peca_display):
    # y_peca_display é a linha da base da peça, 0 é o topo do tabuleiro do jogo
    # x_peca é a coluna do canto esquerdo da peça, 0 é a esquerda
    for r_idx_peca, linha_p in enumerate(peca):
        for c_idx_peca, bloco in enumerate(linha_p):
            if bloco == BLOCK_CELL:
                # Coordenadas no tabuleiro de jogo
                tab_r = y_peca_display - r_idx_peca  # y_peca_display é a base, r_idx_peca sobe
                tab_c = x_peca + c_idx_peca

                # Checar limites do tabuleiro
                if not (0 <= tab_c < (INNER_W // 2)): # Fora horizontalmente
                    return True 
                if not (0 <= tab_r < GAME_ROWS): # Fora verticalmente (abaixo do fundo)
                    if tab_r >= GAME_ROWS: # Colisão com o fundo
                        return True
                    # Se for acima do topo, não é colisão ainda (peça entrando)
                    continue 

                # Checar colisão com blocos existentes no tabuleiro
                if tab_game_data[tab_r][tab_c] == BLOCK_CELL:
                    return True
    return False

def colisao_topo_game_over(tab_game_data, peca, x_peca, y_peca_display):
    # Verifica se a peça, ao ser colocada na posição inicial, já colide (Game Over)
    # Usado quando uma nova peça é gerada.
    # y_peca_display aqui é a posição inicial da peça (topo do jogo)
    for r_idx_peca, linha_p in enumerate(peca):
        for c_idx_peca, bloco in enumerate(linha_p):
            if bloco == BLOCK_CELL:
                tab_r = y_peca_display - r_idx_peca 
                tab_c = x_peca + c_idx_peca
                # Só consideramos blocos da peça que estão dentro da área visível do jogo
                if 0 <= tab_r < GAME_ROWS and 0 <= tab_c < (INNER_W // 2):
                    if tab_game_data[tab_r][tab_c] == BLOCK_CELL:
                        return True # Colisão no topo ao spawnar
    return False


def fixar_peca_no_tabuleiro(tab_game_data, peca, x_peca, y_peca_display):
    # y_peca_display é a linha da base da peça
    for r_idx_peca, linha_p in enumerate(peca):
        for c_idx_peca, bloco in enumerate(linha_p):
            if bloco == BLOCK_CELL:
                tab_r = y_peca_display - r_idx_peca
                tab_c = x_peca + c_idx_peca
                if 0 <= tab_r < GAME_ROWS and 0 <= tab_c < (INNER_W // 2):
                    tab_game_data[tab_r][tab_c] = BLOCK_CELL
    return tab_game_data # Retorna o tabuleiro modificado

def limpar_linhas_completas(tab_game_data):
    linhas_a_manter = []
    linhas_limpas = 0
    for r in range(GAME_ROWS -1, -1, -1): # De baixo para cima
        linha = tab_game_data[r]
        if EMPTY_CELL in linha:
            linhas_a_manter.append(linha)
        else:
            linhas_limpas += 1
    
    novas_linhas_topo = [[EMPTY_CELL for _ in range(INNER_W // 2)] for _ in range(linhas_limpas)]
    novo_tab_game_data = novas_linhas_topo + list(reversed(linhas_a_manter)) # Inverter pois construímos de baixo pra cima
    
    # Garantir que tem GAME_ROWS
    while len(novo_tab_game_data) < GAME_ROWS:
        novo_tab_game_data.insert(0, [EMPTY_CELL for _ in range(INNER_W // 2)])
    
    return novo_tab_game_data[:GAME_ROWS], linhas_limpas


# ─────────────────────────────────────────────
# INICIALIZAÇÃO DO JOGO E ESTADO
# ─────────────────────────────────────────────
def inicializar_estado_sessao():
    if "screen" not in st.session_state:
        st.session_state.screen = "menu"
    if "last_action_time" not in st.session_state: # Para debounce de rotação
        st.session_state.last_action_time = 0

def inicializar_jogo_1p():
    st.session_state.game_1p = {
        "tab_data": criar_tabuleiro_data()["game"],
        "peca_atual": random.choice(TODAS),
        "proxima_peca": random.choice(TODAS),
        "x": (INNER_W // 2) // 2 - largura_peca(random.choice(TODAS)) // 2, # Posição x da peça (coluna)
        "y_display": altura_peca(random.choice(TODAS)) -1, # Posição y da base da peça (linha, 0 no topo)
        "score": 0,
        "level": 1,
        "start_time": time.time(),
        "last_drop_time": time.time(),
        "paused": False,
        "game_over": False,
        "last_rot_time": 0,
        "tick_counter": 0 # Para a lógica de descida baseada em DROP_MOD
    }
    # Ajustar y inicial para que a peça comece no topo
    st.session_state.game_1p['peca_atual'] = random.choice(TODAS) # Garante que a peça é escolhida antes de calcular altura
    st.session_state.game_1p['y_display'] = altura_peca(st.session_state.game_1p['peca_atual']) - 1
    st.session_state.game_1p['x'] = (INNER_W // 2) // 2 - largura_peca(st.session_state.game_1p['peca_atual']) // 2

    if colisao_topo_game_over(st.session_state.game_1p['tab_data'], st.session_state.game_1p['peca_atual'], st.session_state.game_1p['x'], st.session_state.game_1p['y_display']):
        st.session_state.game_1p['game_over'] = True


def inicializar_jogo_2p():
    st.session_state.game_2p_common = {
        "level": 1,
        "start_time": time.time(),
        "last_drop_time": time.time(), # Comum para ambos? Ou individual? Vamos individual.
        "paused": False,
        "game_over_global": False, # Quando ambos perdem
        "tick_counter": 0
    }
    for i in range(1, 3): # Player 1 e Player 2
        peca_inicial = random.choice(TODAS)
        st.session_state[f'game_2p_p{i}'] = {
            "tab_data": criar_tabuleiro_data()["game"],
            "peca_atual": peca_inicial,
            "proxima_peca": random.choice(TODAS),
            "x": (INNER_W // 2) // 2 - largura_peca(peca_inicial) // 2,
            "y_display": altura_peca(peca_inicial) -1,
            "score": 0,
            "alive": True,
            "last_rot_time": 0,
            "last_drop_time": time.time()
        }
        if colisao_topo_game_over(st.session_state[f'game_2p_p{i}']['tab_data'], 
                                  st.session_state[f'game_2p_p{i}']['peca_atual'], 
                                  st.session_state[f'game_2p_p{i}']['x'], 
                                  st.session_state[f'game_2p_p{i}']['y_display']):
            st.session_state[f'game_2p_p{i}']['alive'] = False


# ─────────────────────────────────────────────
# LÓGICA DO JOGO (SINGLE PLAYER)
# ─────────────────────────────────────────────
def logica_jogo_1p_tick():
    gs = st.session_state.game_1p
    if gs['game_over'] or gs['paused']:
        return

    # Atualizar nível
    elapsed_time = time.time() - gs['start_time']
    gs['level'] = 1 + int(elapsed_time // LEVEL_STEP)
    
    # Lógica de descida da peça
    gs['tick_counter'] +=1
    
    # Intervalo de "tick" do jogo original (sleep_t) ajustado pelo nível
    # A peça desce a cada DROP_MOD ticks.
    # Intervalo de descida = (BASE_SLEEP - (level-1)*SPEED_STEP) * DROP_MOD
    # Mas no Streamlit, vamos checar o tempo real.
    game_speed_interval = max(MIN_SLEEP, BASE_SLEEP - (gs['level']-1)*SPEED_STEP) * DROP_MOD

    # Tenta descer a peça se o tempo passou ou se foi forçado (ex: tecla 'baixo')
    force_drop = st.session_state.get("force_drop_1p", False)
    if force_drop: # Limpa o flag
        st.session_state.force_drop_1p = False

    if force_drop or (time.time() - gs['last_drop_time'] > game_speed_interval) :
        if not colisao(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display'] + 1):
            gs['y_display'] += 1
            gs['last_drop_time'] = time.time() # Resetar tempo apenas se moveu
        else:
            # Colidiu, fixar peça
            gs['tab_data'] = fixar_peca_no_tabuleiro(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display'])
            gs['tab_data'], linhas_limpas = limpar_linhas_completas(gs['tab_data'])
            gs['score'] += (linhas_limpas ** 2) * 10 # Pontuação simples

            # Nova peça
            gs['peca_atual'] = gs['proxima_peca']
            gs['proxima_peca'] = random.choice(TODAS)
            gs['y_display'] = altura_peca(gs['peca_atual']) -1
            gs['x'] = (INNER_W // 2) // 2 - largura_peca(gs['peca_atual']) // 2
            
            if colisao_topo_game_over(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display']):
                gs['game_over'] = True
                st.balloons()
        # Mesmo que não tenha movido por colisão, resetamos o tempo para o próximo ciclo de tentativa
        gs['last_drop_time'] = time.time()


def handle_input_1p(action):
    gs = st.session_state.game_1p
    if gs['game_over'] or gs['paused']:
        return

    current_time = time.time()

    if action == "left":
        if gs['x'] > 0 and not colisao(gs['tab_data'], gs['peca_atual'], gs['x'] - 1, gs['y_display']):
            gs['x'] -= 1
    elif action == "right":
        if gs['x'] + largura_peca(gs['peca_atual']) < (INNER_W // 2) and not colisao(gs['tab_data'], gs['peca_atual'], gs['x'] + 1, gs['y_display']):
            gs['x'] += 1
    elif action == "down":
        # Força uma tentativa de descida no próximo tick lógico
        st.session_state.force_drop_1p = True 
    elif action == "rotate":
        if current_time - gs.get('last_rot_time', 0) > 0.2: # Debounce rotação
            peca_rotacionada = rotacionar(gs['peca_atual'])
            # Checar se a rotação é válida (dentro das bordas e sem colisão)
            valid_rotation = True
            if gs['x'] + largura_peca(peca_rotacionada) > (INNER_W // 2): # Fora da borda direita
                valid_rotation = False
            if valid_rotation and colisao(gs['tab_data'], peca_rotacionada, gs['x'], gs['y_display']):
                valid_rotation = False
            
            if valid_rotation:
                gs['peca_atual'] = peca_rotacionada
                gs['last_rot_time'] = current_time
    
    # Após qualquer ação, processar um tick do jogo (que pode incluir a descida)
    logica_jogo_1p_tick()


# ─────────────────────────────────────────────
# LÓGICA DO JOGO (MULTIPLAYER)
# ─────────────────────────────────────────────
def logica_jogo_2p_tick_player(player_idx):
    common_gs = st.session_state.game_2p_common
    player_gs = st.session_state[f'game_2p_p{player_idx}']

    if common_gs['game_over_global'] or common_gs['paused'] or not player_gs['alive']:
        return

    # Atualizar nível (comum)
    elapsed_time = time.time() - common_gs['start_time']
    common_gs['level'] = 1 + int(elapsed_time // LEVEL_STEP)
    
    game_speed_interval = max(MIN_SLEEP, BASE_SLEEP - (common_gs['level']-1)*SPEED_STEP) * DROP_MOD
    
    force_drop = st.session_state.get(f"force_drop_p{player_idx}", False)
    if force_drop:
        st.session_state[f"force_drop_p{player_idx}"] = False

    if force_drop or (time.time() - player_gs['last_drop_time'] > game_speed_interval):
        if not colisao(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'], player_gs['y_display'] + 1):
            player_gs['y_display'] += 1
        else:
            player_gs['tab_data'] = fixar_peca_no_tabuleiro(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'], player_gs['y_display'])
            player_gs['tab_data'], linhas_limpas = limpar_linhas_completas(player_gs['tab_data'])
            player_gs['score'] += (linhas_limpas ** 2) * 10

            player_gs['peca_atual'] = player_gs['proxima_peca']
            player_gs['proxima_peca'] = random.choice(TODAS)
            player_gs['y_display'] = altura_peca(player_gs['peca_atual']) -1
            player_gs['x'] = (INNER_W // 2) // 2 - largura_peca(player_gs['peca_atual']) // 2
            
            if colisao_topo_game_over(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'], player_gs['y_display']):
                player_gs['alive'] = False
                # Verificar se todos os jogadores morreram
                if not st.session_state.game_2p_p1['alive'] and not st.session_state.game_2p_p2['alive']:
                    common_gs['game_over_global'] = True
                    st.balloons()
        player_gs['last_drop_time'] = time.time()


def handle_input_2p(player_idx, action):
    common_gs = st.session_state.game_2p_common
    player_gs = st.session_state[f'game_2p_p{player_idx}']

    if common_gs['game_over_global'] or common_gs['paused'] or not player_gs['alive']:
        return

    current_time = time.time()

    if action == "left":
        if player_gs['x'] > 0 and not colisao(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'] - 1, player_gs['y_display']):
            player_gs['x'] -= 1
    elif action == "right":
        if player_gs['x'] + largura_peca(player_gs['peca_atual']) < (INNER_W // 2) and not colisao(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'] + 1, player_gs['y_display']):
            player_gs['x'] += 1
    elif action == "down":
        st.session_state[f"force_drop_p{player_idx}"] = True
    elif action == "rotate":
        if current_time - player_gs.get('last_rot_time', 0) > 0.2:
            peca_rotacionada = rotacionar(player_gs['peca_atual'])
            valid_rotation = True
            if player_gs['x'] + largura_peca(peca_rotacionada) > (INNER_W // 2):
                valid_rotation = False
            if valid_rotation and colisao(player_gs['tab_data'], peca_rotacionada, player_gs['x'], player_gs['y_display']):
                valid_rotation = False
            
            if valid_rotation:
                player_gs['peca_atual'] = peca_rotacionada
                player_gs['last_rot_time'] = current_time
    
    logica_jogo_2p_tick_player(player_idx)


# ─────────────────────────────────────────────
# RENDERIZAÇÃO E TELAS (STREAMLIT)
# ─────────────────────────────────────────────
def render_menu():
    st.title("TETRIS com Streamlit")
    st.subheader("Desenvolvido por: Gustavo de Almeida Leite")
    st.caption("Matrícula: 202504002")
    st.caption("BIA UFG - 2025 | IP - PROF. LEO")

    if st.button("Jogar 1 Player", key="menu_1p", use_container_width=True):
        inicializar_jogo_1p()
        st.session_state.screen = "game_1p"
        st.rerun()
    if st.button("Jogar 2 Players", key="menu_2p", use_container_width=True):
        inicializar_jogo_2p()
        st.session_state.screen = "game_2p"
        st.rerun()
    if st.button("Comandos", key="menu_cmd", use_container_width=True):
        st.session_state.screen = "commands"
        st.rerun()
    if st.button("Sair", key="menu_quit", use_container_width=True):
        st.session_state.screen = "quit"
        st.rerun()

def render_commands():
    st.header("Comandos")
    st.markdown("""
    - **Player 1 (Modo 1P ou Player 1 no Modo 2P):**
        - `Botão Esquerda`: Mover para esquerda
        - `Botão Direita`: Mover para direita
        - `Botão Girar`: Rotacionar peça
        - `Botão Descer`: Acelerar queda da peça
    - **Player 2 (Modo 2P):**
        - Controles similares, mas em sua própria seção.
    - **Geral:**
        - `P`: Pausar / Retomar o jogo
        - `Q` ou `Voltar ao Menu`: Sair da partida atual
        - Níveis aumentam a cada 30 segundos de jogo.
    """)
    if st.button("Voltar ao Menu", key="cmd_back"):
        st.session_state.screen = "menu"
        st.rerun()

def render_game_1p():
    gs = st.session_state.game_1p
    
    # Lógica de tick do jogo acontece aqui, antes de renderizar e processar input do frame atual
    if not gs['game_over'] and not gs['paused']:
         logica_jogo_1p_tick()


    display_message = None
    if gs['game_over']:
        display_message = "GAME OVER"
    elif gs['paused']:
        display_message = "PAUSADO"

    tab_str = formatar_tabuleiro_para_exibicao(
        {"game": gs['tab_data']}, 
        gs['proxima_peca'], 
        gs['score'], 
        gs['level'],
        display_message
    )
    st.code(tab_str, language="text")

    if gs['game_over']:
        st.error("FIM DE JOGO!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Novo Jogo (1P)", key="gameover_new_1p", use_container_width=True):
                inicializar_jogo_1p()
                st.rerun()
        with col2:
            if st.button("Voltar ao Menu", key="gameover_menu_1p", use_container_width=True):
                st.session_state.screen = "menu"
                st.rerun()
        return

    # Controles
    cols = st.columns(4)
    if cols[0].button("⬅️ Esquerda", key="p1_left", use_container_width=True, disabled=gs['paused']):
        handle_input_1p("left")
        st.rerun()
    if cols[1].button("➡️ Direita", key="p1_right", use_container_width=True, disabled=gs['paused']):
        handle_input_1p("right")
        st.rerun()
    if cols[2].button("🔄 Girar", key="p1_rotate", use_container_width=True, disabled=gs['paused']):
        handle_input_1p("rotate")
        st.rerun()
    if cols[3].button("⬇️ Descer", key="p1_down", use_container_width=True, disabled=gs['paused']):
        handle_input_1p("down") # Vai forçar um tick com descida
        st.rerun()

    # Pausa e Sair
    col_opts1, col_opts2 = st.columns(2)
    if col_opts1.button("Pausar/Retomar (P)", key="pause_1p", use_container_width=True):
        gs['paused'] = not gs['paused']
        if not gs['paused']: # Se retomou, resetar o last_drop_time para evitar pulo grande
            gs['last_drop_time'] = time.time()
        st.rerun()
    
    if col_opts2.button("Sair para Menu (Q)", key="quit_1p", use_container_width=True):
        st.session_state.screen = "menu"
        st.rerun()

def render_game_2p():
    common_gs = st.session_state.game_2p_common
    p1_gs = st.session_state.game_2p_p1
    p2_gs = st.session_state.game_2p_p2

    # Lógica de tick para ambos os jogadores
    if not common_gs['game_over_global'] and not common_gs['paused']:
        logica_jogo_2p_tick_player(1)
        logica_jogo_2p_tick_player(2)
    
    # Placar central
    st.subheader(f"Nível: {common_gs['level']}")
    if common_gs['paused']: st.warning("JOGO PAUSADO")
    if common_gs['game_over_global']: st.error("FIM DE JOGO PARA AMBOS!")

    col_p1, col_score, col_p2 = st.columns([2,1,2])

    with col_p1:
        st.markdown("<h4 style='text-align: center;'>Jogador 1</h4>", unsafe_allow_html=True)
        msg1 = None
        if not p1_gs['alive']: msg1 = "ELIMINADO!"
        elif common_gs['paused']: msg1 = "PAUSADO"
        
        tab_str_p1 = formatar_tabuleiro_para_exibicao(
            {"game": p1_gs['tab_data']}, p1_gs['proxima_peca'], player_id=1, msg_extra=msg1
        )
        st.code(tab_str_p1, language="text")
        
        if p1_gs['alive'] and not common_gs['game_over_global']:
            btn_cols_p1 = st.columns(4)
            if btn_cols_p1[0].button("⬅️ P1", key="p1_left_2p", use_container_width=True, disabled=common_gs['paused']):
                handle_input_2p(1, "left"); st.rerun()
            if btn_cols_p1[1].button("➡️ P1", key="p1_right_2p", use_container_width=True, disabled=common_gs['paused']):
                handle_input_2p(1, "right"); st.rerun()
            if btn_cols_p1[2].button("🔄 P1", key="p1_rotate_2p", use_container_width=True, disabled=common_gs['paused']):
                handle_input_2p(1, "rotate"); st.rerun()
            if btn_cols_p1[3].button("⬇️ P1", key="p1_down_2p", use_container_width=True, disabled=common_gs['paused']):
                handle_input_2p(1, "down"); st.rerun()
    
    with col_score:
        st.markdown("<h4 style='text-align: center;'>Placar</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 1.2em; text-align: center;'>P1: {p1_gs['score']:05}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 1.2em; text-align: center;'>P2: {p2_gs['score']:05}</p>", unsafe_allow_html=True)

    with col_p2:
        st.markdown("<h4 style='text-align: center;'>Jogador 2</h4>", unsafe_allow_html=True)
        msg2 = None
        if not p2_gs['alive']: msg2 = "ELIMINADO!"
        elif common_gs['paused']: msg2 = "PAUSADO"

        tab_str_p2 = formatar_tabuleiro_para_exibicao(
            {"game": p2_gs['tab_data']}, p2_gs['proxima_peca'], player_id=2, msg_extra=msg2
        )
        st.code(tab_str_p2, language="text")

        if p2_gs['alive'] and not common_gs['game_over_global']:
            btn_cols_p2 = st.columns(4)
            if btn_cols_p2[0].button("⬅️ P2", key="p2_left_2p", use_container_width=True, disabled=common_gs['paused']):
                handle_input_2p(2, "left"); st.rerun()
            if btn_cols_p2[1].button("➡️ P2", key="p2_right_2p", use_container_width=True, disabled=common_gs['paused']):
                handle_input_2p(2, "right"); st.rerun()
            if btn_cols_p2[2].button("🔄 P2", key="p2_rotate_2p", use_container_width=True, disabled=common_gs['paused']):
                handle_input_2p(2, "rotate"); st.rerun()
            if btn_cols_p2[3].button("⬇️ P2", key="p2_down_2p", use_container_width=True, disabled=common_gs['paused']):
                handle_input_2p(2, "down"); st.rerun()

    if common_gs['game_over_global']:
        st.error("FIM DE JOGO PARA AMBOS!")
        winner_msg = "Empate!"
        if p1_gs['score'] > p2_gs['score']: winner_msg = "Jogador 1 Vence!"
        elif p2_gs['score'] > p1_gs['score']: winner_msg = "Jogador 2 Vence!"
        st.subheader(winner_msg)

        col_gm_opts1, col_gm_opts2 = st.columns(2)
        if col_gm_opts1.button("Novo Jogo (2P)", key="gameover_new_2p", use_container_width=True):
            inicializar_jogo_2p()
            st.rerun()
        if col_gm_opts2.button("Voltar ao Menu", key="gameover_menu_2p", use_container_width=True):
            st.session_state.screen = "menu"
            st.rerun()
        return

    # Pausa e Sair (comum)
    col_gopts1, col_gopts2 = st.columns(2)
    if col_gopts1.button("Pausar/Retomar Jogo (P)", key="pause_2p", use_container_width=True):
        common_gs['paused'] = not common_gs['paused']
        if not common_gs['paused']: # Se retomou, resetar tempos de queda
            p1_gs['last_drop_time'] = time.time()
            p2_gs['last_drop_time'] = time.time()
        st.rerun()
    
    if col_gopts2.button("Sair para Menu (Q)", key="quit_2p", use_container_width=True):
        st.session_state.screen = "menu"
        st.rerun()


# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
def main():
    st.set_page_config(layout="wide", page_title="Streamlit Tetris")
    inicializar_estado_sessao()

    if st.session_state.screen == "menu":
        render_menu()
    elif st.session_state.screen == "commands":
        render_commands()
    elif st.session_state.screen == "game_1p":
        render_game_1p()
    elif st.session_state.screen == "game_2p":
        render_game_2p()
    elif st.session_state.screen == "quit":
        st.title("Obrigado por jogar!")
        st.balloons()
        if st.button("Voltar ao Menu Principal", key="quit_to_menu"):
            st.session_state.screen = "menu"
            st.rerun()

if __name__ == "__main__":
    main()
