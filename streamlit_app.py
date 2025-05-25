import streamlit as st
import time
import random
import copy
from st_keyup import st_keyup # Certifique-se de instalar: pip install st-keyup

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
DROP_MOD     = 4         # A peça desce a cada X "ticks" lógicos (usado no cálculo do game_speed_interval)

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
    # preview = [[EMPTY_CELL for _ in range(INNER_W // 2)] for _ in range(PREVIEW_ROWS)] # Não usado diretamente
    jogo    = [[EMPTY_CELL for _ in range(INNER_W // 2)] for _ in range(GAME_ROWS)]
    return {"preview": [], "game": jogo} # Preview data não é mais necessário aqui

def formatar_tabuleiro_para_exibicao(tab_data_game_area, proxima_peca_preview=None, score=0, level=0, msg_extra=None, player_id=None, current_peca_info=None):
    linhas_finais = []

    # Preview Area
    linhas_finais.append(linha_texto("PRÓXIMA PEÇA"))
    preview_altura_render = PREVIEW_ROWS -1
    preview_display_area = [[' ' for _ in range(INNER_W)] for _ in range(preview_altura_render)]

    if proxima_peca_preview:
        peca_render_linhas = piece_to_preview_lines(proxima_peca_preview)

        peca_alt = len(peca_render_linhas)
        peca_larg_str = max(len(l) for l in peca_render_linhas) if peca_render_linhas else 0

        start_row_preview = (preview_altura_render - peca_alt) // 2
        start_col_preview_str = (INNER_W - peca_larg_str) // 2

        for r_idx, linha_str_peca in enumerate(peca_render_linhas):
            if start_row_preview + r_idx < preview_altura_render:
                for c_idx_str, char_peca in enumerate(linha_str_peca):
                    if start_col_preview_str + c_idx_str < INNER_W:
                        preview_display_area[start_row_preview + r_idx][start_col_preview_str + c_idx_str] = char_peca

    for r_preview in preview_display_area:
        linhas_finais.append(linha_texto("".join(r_preview)))

    # Game Area
    tab_render = copy.deepcopy(tab_data_game_area)

    if current_peca_info and current_peca_info.get('peca_atual'):
        peca_atual = current_peca_info['peca_atual']
        peca_x = current_peca_info['x']
        peca_y_display = current_peca_info['y_display']

        for r_idx, linha_peca in enumerate(peca_atual):
            for c_idx, bloco in enumerate(linha_peca):
                if bloco == BLOCK_CELL:
                    abs_r = peca_y_display - r_idx
                    abs_c = peca_x + c_idx
                    if 0 <= abs_r < GAME_ROWS and 0 <= abs_c < (INNER_W // 2):
                        tab_render[abs_r][abs_c] = BLOCK_CELL

    for linha_jogo in tab_render:
        linhas_finais.append("<!" + "".join(c for c in linha_jogo) + " !>")

    linhas_finais.append("<!=-=-=-=-=-=-=-=-=-=-=!>")
    linhas_finais.append("\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/")
    if player_id is None: # Modo 1P
        linhas_finais.append(linha_texto(f"SCORE: {score:05}"))
        linhas_finais.append(linha_texto(f"NÍVEL: {level}"))
    # Para 2P, o score e nível são mostrados em outro lugar

    if msg_extra:
        linhas_finais.append(linha_texto(msg_extra))

    return "\n".join(linhas_finais)


def piece_to_preview_lines(peca_data):
    linhas = []
    for row in peca_data:
        linha_str = ""
        for cell in row:
            linha_str += BLOCK_CELL if cell == BLOCK_CELL else "  " # Dois espaços para .
        linhas.append(linha_str.rstrip())

    larg_max = max((len(s) for s in linhas), default=0)
    return [l.ljust(larg_max) for l in linhas]


def largura_peca(p): return len(p[0]) if p and len(p) > 0 else 0
def altura_peca(p): return len(p) if p else 0


def colisao(tab_game_data, peca, x_peca, y_peca_display):
    for r_idx_peca, linha_p in enumerate(peca):
        for c_idx_peca, bloco in enumerate(linha_p):
            if bloco == BLOCK_CELL:
                tab_r = y_peca_display - r_idx_peca
                tab_c = x_peca + c_idx_peca

                if not (0 <= tab_c < (INNER_W // 2)):
                    return True # Colisão lateral com as bordas do tabuleiro
                if tab_r >= GAME_ROWS: # Colisão com o fundo
                    return True
                if tab_r < 0: # Acima do topo, não é colisão para peça caindo (mas pode ser para rotação)
                    continue # Ou return True se for spawn/rotação

                if tab_game_data[tab_r][tab_c] == BLOCK_CELL: # Colisão com blocos existentes
                    return True
    return False

def colisao_topo_game_over(tab_game_data, peca, x_peca, y_peca_display_inicial):
    for r_idx_peca, linha_p in enumerate(peca):
        for c_idx_peca, bloco in enumerate(linha_p):
            if bloco == BLOCK_CELL:
                tab_r = y_peca_display_inicial - r_idx_peca
                tab_c = x_peca + c_idx_peca
                if 0 <= tab_r < GAME_ROWS and 0 <= tab_c < (INNER_W // 2): # Dentro dos limites
                    if tab_game_data[tab_r][tab_c] == BLOCK_CELL:
                        return True # Game Over se colidir ao spawnar
    return False


def fixar_peca_no_tabuleiro(tab_game_data, peca, x_peca, y_peca_display):
    for r_idx_peca, linha_p in enumerate(peca):
        for c_idx_peca, bloco in enumerate(linha_p):
            if bloco == BLOCK_CELL:
                tab_r = y_peca_display - r_idx_peca
                tab_c = x_peca + c_idx_peca
                if 0 <= tab_r < GAME_ROWS and 0 <= tab_c < (INNER_W // 2):
                    tab_game_data[tab_r][tab_c] = BLOCK_CELL
    return tab_game_data

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
    novo_tab_game_data = novas_linhas_topo + list(reversed(linhas_a_manter)) # Inverte para ordem correta

    while len(novo_tab_game_data) < GAME_ROWS:
        novo_tab_game_data.insert(0, [EMPTY_CELL for _ in range(INNER_W // 2)])

    return novo_tab_game_data[:GAME_ROWS], linhas_limpas


# ─────────────────────────────────────────────
# INICIALIZAÇÃO DO JOGO E ESTADO
# ─────────────────────────────────────────────
def inicializar_estado_sessao():
    if "screen" not in st.session_state:
        st.session_state.screen = "menu"
    # Para st_keyup, pode ser útil inicializar o valor da tecla
    if "last_key_pressed" not in st.session_state:
        st.session_state.last_key_pressed = None


def _spawn_nova_peca(gs_dict_ou_prefixo, is_2p_player_num=None):
    if is_2p_player_num:
        gs = st.session_state[f'{gs_dict_ou_prefixo}{is_2p_player_num}']
        # common_gs = st.session_state.game_2p_common # Não usado aqui diretamente
    else:
        gs = st.session_state[gs_dict_ou_prefixo]

    gs['peca_atual'] = gs['proxima_peca']
    gs['proxima_peca'] = random.choice(TODAS)
    gs['y_display'] = altura_peca(gs['peca_atual']) -1
    gs['x'] = (INNER_W // 4) - largura_peca(gs['peca_atual']) // 2 # INNER_W // 4 porque INNER_W é o dobro da largura do tabuleiro de jogo
    gs['last_drop_time'] = time.time()

    if colisao_topo_game_over(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display']):
        if is_2p_player_num:
            gs['alive'] = False
            p1_alive = st.session_state.game_2p_p1.get('alive', False)
            p2_alive = st.session_state.game_2p_p2.get('alive', False)
            if not p1_alive and not p2_alive:
                st.session_state.game_2p_common['game_over_global'] = True
                # st.balloons() # Mover para a lógica de renderização de fim de jogo
        else: # Modo 1P
            gs['game_over'] = True
            # st.balloons()
        return False
    return True

def inicializar_jogo_1p():
    st.session_state.game_1p = {
        "tab_data": criar_tabuleiro_data()["game"],
        "proxima_peca": random.choice(TODAS),
        "score": 0,
        "level": 1,
        "start_time": time.time(),
        "paused": False,
        "game_over": False,
        "last_rot_time": 0,
        # "peca_atual", "x", "y_display", "last_drop_time" serão definidos por _spawn_nova_peca
    }
    _spawn_nova_peca('game_1p')


def inicializar_jogo_2p():
    st.session_state.game_2p_common = {
        "level": 1,
        "start_time": time.time(),
        "paused": False,
        "game_over_global": False,
    }
    for i in range(1, 3):
        st.session_state[f'game_2p_p{i}'] = {
            "tab_data": criar_tabuleiro_data()["game"],
            "proxima_peca": random.choice(TODAS),
            "score": 0,
            "alive": True,
            "last_rot_time": 0,
        }
        _spawn_nova_peca('game_2p_p', i)


# ─────────────────────────────────────────────
# LÓGICA DO JOGO (SINGLE PLAYER)
# ─────────────────────────────────────────────
def logica_jogo_1p_tick():
    gs = st.session_state.game_1p
    if gs['game_over'] or gs['paused'] or not gs.get('peca_atual'): # Checar se peca_atual existe
        return

    elapsed_time = time.time() - gs['start_time']
    gs['level'] = 1 + int(elapsed_time // LEVEL_STEP)

    game_speed_interval = max(MIN_SLEEP, BASE_SLEEP - (gs['level']-1)*SPEED_STEP) * DROP_MOD

    force_drop = st.session_state.pop("force_drop_1p", False)

    if force_drop or (time.time() - gs.get('last_drop_time', gs['start_time']) > game_speed_interval) :
        if not colisao(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display'] + 1):
            gs['y_display'] += 1
            gs['last_drop_time'] = time.time()
        else:
            gs['tab_data'] = fixar_peca_no_tabuleiro(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display'])
            gs['tab_data'], linhas_limpas = limpar_linhas_completas(gs['tab_data'])
            gs['score'] += (linhas_limpas ** 2) * 10 if linhas_limpas > 0 else (10 * linhas_limpas) # Pontuação por linha

            if not _spawn_nova_peca('game_1p'):
                return # Game over

def handle_input_1p(action):
    gs = st.session_state.game_1p
    if gs['game_over'] or gs['paused'] or not gs.get('peca_atual'):
        return

    current_time = time.time()
    # moved = False # Não usado diretamente para o tick, mas para cooldown de rotação

    if action == "left":
        if not colisao(gs['tab_data'], gs['peca_atual'], gs['x'] - 1, gs['y_display']):
            gs['x'] -= 1
    elif action == "right":
        if not colisao(gs['tab_data'], gs['peca_atual'], gs['x'] + 1, gs['y_display']):
            gs['x'] += 1
    elif action == "down":
        st.session_state.force_drop_1p = True
    elif action == "rotate":
        if current_time - gs.get('last_rot_time', 0) > 0.2: # Cooldown para rotação
            peca_rotacionada = rotacionar(gs['peca_atual'])
            new_x = gs['x']
            # Lógica de ajuste de parede ("wall kick") simples
            if colisao(gs['tab_data'], peca_rotacionada, new_x, gs['y_display']):
                # Tenta deslocar 1 para a direita
                if not colisao(gs['tab_data'], peca_rotacionada, new_x + 1, gs['y_display']):
                    new_x += 1
                # Tenta deslocar 1 para a esquerda
                elif not colisao(gs['tab_data'], peca_rotacionada, new_x - 1, gs['y_display']):
                    new_x -= 1
                # Tenta deslocar 2 para a direita (para peças compridas como I)
                elif largura_peca(peca_rotacionada) > 2 and not colisao(gs['tab_data'], peca_rotacionada, new_x + 2, gs['y_display']):
                     new_x += 2
                # Tenta deslocar 2 para a esquerda
                elif largura_peca(peca_rotacionada) > 2 and not colisao(gs['tab_data'], peca_rotacionada, new_x - 2, gs['y_display']):
                     new_x -= 2


            if not colisao(gs['tab_data'], peca_rotacionada, new_x, gs['y_display']):
                gs['peca_atual'] = peca_rotacionada
                gs['x'] = new_x
                gs['last_rot_time'] = current_time

    # O tick principal é chamado no loop de renderização para manter a queda constante
    # Se uma ação de input forçar uma descida, o tick processará.


# ─────────────────────────────────────────────
# LÓGICA DO JOGO (MULTIPLAYER)
# ─────────────────────────────────────────────
def logica_jogo_2p_tick_player(player_idx):
    common_gs = st.session_state.game_2p_common
    player_gs = st.session_state[f'game_2p_p{player_idx}']

    if common_gs['game_over_global'] or common_gs['paused'] or not player_gs['alive'] or not player_gs.get('peca_atual'):
        return

    elapsed_time = time.time() - common_gs['start_time']
    common_gs['level'] = 1 + int(elapsed_time // LEVEL_STEP)

    game_speed_interval = max(MIN_SLEEP, BASE_SLEEP - (common_gs['level']-1)*SPEED_STEP) * DROP_MOD

    force_drop = st.session_state.pop(f"force_drop_p{player_idx}", False)

    if force_drop or (time.time() - player_gs.get('last_drop_time', common_gs['start_time']) > game_speed_interval):
        if not colisao(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'], player_gs['y_display'] + 1):
            player_gs['y_display'] += 1
            player_gs['last_drop_time'] = time.time()
        else:
            player_gs['tab_data'] = fixar_peca_no_tabuleiro(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'], player_gs['y_display'])
            player_gs['tab_data'], linhas_limpas = limpar_linhas_completas(player_gs['tab_data'])
            player_gs['score'] += (linhas_limpas ** 2) * 10 if linhas_limpas > 0 else (10 * linhas_limpas)

            if not _spawn_nova_peca('game_2p_p', player_idx):
                return # Jogador eliminado ou game over


def handle_input_2p(player_idx, action):
    common_gs = st.session_state.game_2p_common
    player_gs = st.session_state[f'game_2p_p{player_idx}']

    if common_gs['game_over_global'] or common_gs['paused'] or not player_gs['alive'] or not player_gs.get('peca_atual'):
        return

    current_time = time.time()
    # moved = False

    if action == "left":
        if not colisao(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'] - 1, player_gs['y_display']):
            player_gs['x'] -= 1
    elif action == "right":
        if not colisao(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'] + 1, player_gs['y_display']):
            player_gs['x'] += 1
    elif action == "down":
        st.session_state[f"force_drop_p{player_idx}"] = True
    elif action == "rotate":
        if current_time - player_gs.get('last_rot_time', 0) > 0.2:
            peca_rotacionada = rotacionar(player_gs['peca_atual'])
            new_x = player_gs['x']
            # Lógica de ajuste de parede ("wall kick") simples
            if colisao(player_gs['tab_data'], peca_rotacionada, new_x, player_gs['y_display']):
                if not colisao(player_gs['tab_data'], peca_rotacionada, new_x + 1, player_gs['y_display']):
                    new_x += 1
                elif not colisao(player_gs['tab_data'], peca_rotacionada, new_x - 1, player_gs['y_display']):
                    new_x -= 1
                elif largura_peca(peca_rotacionada) > 2 and not colisao(player_gs['tab_data'], peca_rotacionada, new_x + 2, player_gs['y_display']):
                     new_x += 2
                elif largura_peca(peca_rotacionada) > 2 and not colisao(player_gs['tab_data'], peca_rotacionada, new_x - 2, player_gs['y_display']):
                     new_x -= 2

            if not colisao(player_gs['tab_data'], peca_rotacionada, new_x, player_gs['y_display']):
                player_gs['peca_atual'] = peca_rotacionada
                player_gs['x'] = new_x
                player_gs['last_rot_time'] = current_time
    # O tick principal é chamado no loop de renderização


# ─────────────────────────────────────────────
# PROCESSAMENTO DE INPUT DO TECLADO
# ─────────────────────────────────────────────
def process_keyboard_input_1p():
    gs = st.session_state.game_1p
    if gs['game_over'] or gs['paused']:
        return

    # Usar um key único para st_keyup para a tela 1P
    # Debounce de 50ms pode ser um bom começo.
    # `key` interno do Streamlit para manter o estado do widget
    key_event = st_keyup(value="", debounce=50, key="keyboard_input_1p")

    action = None
    if key_event:
        if key_event == "ArrowLeft":
            action = "left"
        elif key_event == "ArrowRight":
            action = "right"
        elif key_event == "ArrowDown":
            action = "down"
        elif key_event == "ArrowUp":
            action = "rotate"
        # Teclas de controle do jogo (Pausar, Sair) podem ser adicionadas aqui também
        elif key_event.lower() == "p": # Pausar
            gs['paused'] = not gs['paused']
            if not gs['paused']:
                gs['last_drop_time'] = time.time()
            st.rerun() # Rerun para atualizar a UI do pause
            return # Evitar processar outra ação de movimento
        elif key_event.lower() == "q": # Sair
            st.session_state.screen = "menu"
            st.rerun()
            return

    if action:
        handle_input_1p(action)
        # Um st.rerun() aqui pode ser muito agressivo se st_keyup já causa um.
        # O loop principal de renderização já tem um st.rerun() para a animação.
        # Pode ser necessário um rerun se a resposta ao teclado parecer lenta.
        # st.rerun() # Descomente se necessário


def process_keyboard_input_2p():
    common_gs = st.session_state.game_2p_common
    if common_gs['game_over_global'] or common_gs['paused']:
        return

    key_event = st_keyup(value="", debounce=50, key="keyboard_input_2p")

    action_p1 = None
    action_p2 = None

    if key_event:
        # Player 1 (Setas)
        if key_event == "ArrowLeft": action_p1 = "left"
        elif key_event == "ArrowRight": action_p1 = "right"
        elif key_event == "ArrowDown": action_p1 = "down"
        elif key_event == "ArrowUp": action_p1 = "rotate"
        # Player 2 (ASDW)
        elif key_event.lower() == "a": action_p2 = "left"
        elif key_event.lower() == "d": action_p2 = "right"
        elif key_event.lower() == "s": action_p2 = "down"
        elif key_event.lower() == "w": action_p2 = "rotate"
        # Controles comuns
        elif key_event.lower() == "p": # Pausar
            common_gs['paused'] = not common_gs['paused']
            if not common_gs['paused']:
                if st.session_state.game_2p_p1['alive']: st.session_state.game_2p_p1['last_drop_time'] = time.time()
                if st.session_state.game_2p_p2['alive']: st.session_state.game_2p_p2['last_drop_time'] = time.time()
            st.rerun()
            return
        elif key_event.lower() == "q": # Sair
            st.session_state.screen = "menu"
            st.rerun()
            return

    if action_p1 and st.session_state.game_2p_p1['alive']:
        handle_input_2p(1, action_p1)
    if action_p2 and st.session_state.game_2p_p2['alive']:
        handle_input_2p(2, action_p2)

    # if action_p1 or action_p2:
    # st.rerun() # Descomente se necessário


# ─────────────────────────────────────────────
# RENDERIZAÇÃO E TELAS (STREAMLIT)
# ─────────────────────────────────────────────
def render_menu():
    st.title("TETRIS com Streamlit")
    st.markdown("---")
    st.subheader("Desenvolvido por: Gustavo de Almeida Leite")
    st.caption("Matrícula: 202504002")
    st.caption("BIA UFG - 2025 | IP - PROF. LEO")
    st.markdown("---")

    if st.button("🚀 Jogar 1 Player", key="menu_1p", use_container_width=True):
        inicializar_jogo_1p()
        st.session_state.screen = "game_1p"
        st.rerun()
    if st.button("🧑‍🤝‍🧑 Jogar 2 Players", key="menu_2p", use_container_width=True):
        inicializar_jogo_2p()
        st.session_state.screen = "game_2p"
        st.rerun()
    if st.button("📜 Comandos", key="menu_cmd", use_container_width=True):
        st.session_state.screen = "commands"
        st.rerun()
    if st.button("🚪 Sair", key="menu_quit", use_container_width=True):
        st.session_state.screen = "quit"
        st.rerun()

def render_commands():
    st.header("📜 Comandos")
    st.markdown("""
    ### Controles Gerais (Botões):
    - Utilize os botões na tela para interagir.

    ### Controles do Teclado:
    - **Player 1 (Modo 1P ou Jogador 1 no Modo 2P):**
        - `SETA PARA ESQUERDA`: Mover peça para esquerda.
        - `SETA PARA DIREITA`: Mover peça para direita.
        - `SETA PARA CIMA`: Rotacionar a peça atual.
        - `SETA PARA BAIXO`: Acelerar a queda da peça atual.
    - **Player 2 (Apenas no Modo 2P):**
        - `A`: Mover peça para esquerda.
        - `D`: Mover peça para direita.
        - `W`: Rotacionar a peça atual.
        - `S`: Acelerar a queda da peça atual.
    - **Ambos os Modos:**
        - `P`: Pausar / Retomar o jogo.
        - `Q`: Sair da partida atual e retornar ao menu principal.

    ### Gameplay:
    - **Níveis**: A dificuldade (velocidade de queda das peças) aumenta automaticamente a cada 30 segundos de jogo.
    - **Pontuação**: Complete linhas para ganhar pontos! Múltiplas linhas de uma vez valem mais.
    """)
    if st.button("⬅️ Voltar ao Menu", key="cmd_back"):
        st.session_state.screen = "menu"
        st.rerun()

def render_game_1p():
    gs = st.session_state.game_1p
    process_keyboard_input_1p() # Processa input do teclado primeiro

    if not gs['game_over'] and not gs['paused']:
        logica_jogo_1p_tick()

    display_message = None
    if gs['game_over']:
        display_message = "GAME OVER"
        if "played_balloons_1p" not in st.session_state or not st.session_state.played_balloons_1p:
            st.balloons()
            st.session_state.played_balloons_1p = True # Para exibir apenas uma vez
    elif gs['paused']:
        display_message = "PAUSADO"
    else:
        st.session_state.played_balloons_1p = False # Reseta se o jogo não acabou

    current_peca_info_1p = None
    if not gs['game_over'] and gs.get('peca_atual'):
        current_peca_info_1p = {
            "peca_atual": gs['peca_atual'],
            "x": gs['x'],
            "y_display": gs['y_display']
        }

    tab_str = formatar_tabuleiro_para_exibicao(
        gs['tab_data'],
        gs['proxima_peca'],
        gs['score'],
        gs['level'],
        display_message,
        player_id=None,
        current_peca_info=current_peca_info_1p
    )
    game_placeholder = st.empty()
    game_placeholder.code(tab_str, language="text")


    if gs['game_over']:
        st.error("FIM DE JOGO!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Novo Jogo (1P)", key="gameover_new_1p", use_container_width=True):
                inicializar_jogo_1p()
                st.session_state.played_balloons_1p = False
                st.rerun()
        with col2:
            if st.button("⬅️ Voltar ao Menu", key="gameover_menu_1p", use_container_width=True):
                st.session_state.screen = "menu"
                st.session_state.played_balloons_1p = False
                st.rerun()
        return

    # Controles via botões (opcional, já que temos teclado)
    cols = st.columns(4)
    if cols[0].button("⬅️", key="p1_left_btn", use_container_width=True, disabled=gs['paused']):
        handle_input_1p("left"); st.rerun()
    if cols[1].button("➡️", key="p1_right_btn", use_container_width=True, disabled=gs['paused']):
        handle_input_1p("right"); st.rerun()
    if cols[2].button("🔄", key="p1_rotate_btn", use_container_width=True, disabled=gs['paused']):
        handle_input_1p("rotate"); st.rerun()
    if cols[3].button("⬇️", key="p1_down_btn", use_container_width=True, disabled=gs['paused']):
        handle_input_1p("down"); st.rerun()

    col_opts1, col_opts2 = st.columns(2)
    pause_label = "▶️ Retomar (P)" if gs['paused'] else "❚❚ Pausar (P)"
    if col_opts1.button(pause_label, key="pause_1p_btn", use_container_width=True):
        gs['paused'] = not gs['paused']
        if not gs['paused']:
            gs['last_drop_time'] = time.time()
        st.rerun()

    if col_opts2.button("🚪 Sair Menu (Q)", key="quit_1p_btn", use_container_width=True):
        st.session_state.screen = "menu"
        st.rerun()

    if not gs['game_over'] and not gs['paused']:
        time.sleep(0.05) # Pequeno sleep para controlar a taxa de atualização da tela
        st.rerun()


def render_game_2p():
    common_gs = st.session_state.game_2p_common
    p1_gs = st.session_state.game_2p_p1
    p2_gs = st.session_state.game_2p_p2

    process_keyboard_input_2p() # Processa input do teclado

    if not common_gs['game_over_global'] and not common_gs['paused']:
        if p1_gs['alive']: logica_jogo_2p_tick_player(1)
        if p2_gs['alive']: logica_jogo_2p_tick_player(2)

    st.subheader(f"Nível Comum: {common_gs['level']}")
    if common_gs['paused']: st.warning("JOGO PAUSADO (Pressione 'P' para retomar)")
    if common_gs['game_over_global']:
        st.error("FIM DE JOGO PARA AMBOS!")
        if "played_balloons_2p" not in st.session_state or not st.session_state.played_balloons_2p:
            st.balloons()
            st.session_state.played_balloons_2p = True
    else:
        st.session_state.played_balloons_2p = False


    game_area_placeholder = st.empty()

    with game_area_placeholder.container():
        col_p1, col_score, col_p2 = st.columns([2,1,2]) # Ajuste a proporção conforme necessário

        with col_p1:
            st.markdown("<h4 style='text-align: center;'>Jogador 1 (Setas)</h4>", unsafe_allow_html=True)
            msg1 = None
            current_peca_info_p1 = None
            if not p1_gs['alive']: msg1 = "ELIMINADO!"
            elif common_gs['paused']: msg1 = "PAUSADO"
            elif p1_gs.get('peca_atual'):
                current_peca_info_p1 = {"peca_atual": p1_gs['peca_atual'], "x": p1_gs['x'], "y_display": p1_gs['y_display']}

            tab_str_p1 = formatar_tabuleiro_para_exibicao(
                p1_gs['tab_data'], p1_gs['proxima_peca'], player_id=1, msg_extra=msg1, current_peca_info=current_peca_info_p1
            )
            st.code(tab_str_p1, language="text")

            # Botões P1 (opcionais)
            if p1_gs['alive'] and not common_gs['game_over_global']:
                btn_cols_p1 = st.columns(4)
                if btn_cols_p1[0].button("⬅️", key="p1_left_2p_btn", use_container_width=True, disabled=common_gs['paused']):
                    handle_input_2p(1, "left"); st.rerun()
                if btn_cols_p1[1].button("➡️", key="p1_right_2p_btn", use_container_width=True, disabled=common_gs['paused']):
                    handle_input_2p(1, "right"); st.rerun()
                if btn_cols_p1[2].button("🔄", key="p1_rotate_2p_btn", use_container_width=True, disabled=common_gs['paused']):
                    handle_input_2p(1, "rotate"); st.rerun()
                if btn_cols_p1[3].button("⬇️", key="p1_down_2p_btn", use_container_width=True, disabled=common_gs['paused']):
                    handle_input_2p(1, "down"); st.rerun()

        with col_score:
            st.markdown("<h4 style='text-align: center;'>Placar</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 1.2em; text-align: center;'>P1: {p1_gs['score']:05}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 1.2em; text-align: center;'>P2: {p2_gs['score']:05}</p>", unsafe_allow_html=True)
            st.markdown("---")
            pause_label_2p = "▶️ Retomar (P)" if common_gs['paused'] else "❚❚ Pausar (P)"
            if st.button(pause_label_2p, key="pause_2p_btn", use_container_width=True):
                common_gs['paused'] = not common_gs['paused']
                if not common_gs['paused']:
                    if p1_gs['alive']: p1_gs['last_drop_time'] = time.time()
                    if p2_gs['alive']: p2_gs['last_drop_time'] = time.time()
                st.rerun()
            if st.button("🚪 Sair Menu (Q)", key="quit_2p_btn", use_container_width=True):
                st.session_state.screen = "menu"; st.rerun()


        with col_p2:
            st.markdown("<h4 style='text-align: center;'>Jogador 2 (ASDW)</h4>", unsafe_allow_html=True)
            msg2 = None
            current_peca_info_p2 = None
            if not p2_gs['alive']: msg2 = "ELIMINADO!"
            elif common_gs['paused']: msg2 = "PAUSADO"
            elif p2_gs.get('peca_atual'):
                current_peca_info_p2 = {"peca_atual": p2_gs['peca_atual'], "x": p2_gs['x'], "y_display": p2_gs['y_display']}

            tab_str_p2 = formatar_tabuleiro_para_exibicao(
                p2_gs['tab_data'], p2_gs['proxima_peca'], player_id=2, msg_extra=msg2, current_peca_info=current_peca_info_p2
            )
            st.code(tab_str_p2, language="text")

            # Botões P2 (opcionais)
            if p2_gs['alive'] and not common_gs['game_over_global']:
                btn_cols_p2 = st.columns(4)
                if btn_cols_p2[0].button("⬅️", key="p2_left_2p_btn", use_container_width=True, disabled=common_gs['paused']):
                    handle_input_2p(2, "left"); st.rerun()
                if btn_cols_p2[1].button("➡️", key="p2_right_2p_btn", use_container_width=True, disabled=common_gs['paused']):
                    handle_input_2p(2, "right"); st.rerun()
                if btn_cols_p2[2].button("🔄", key="p2_rotate_2p_btn", use_container_width=True, disabled=common_gs['paused']):
                    handle_input_2p(2, "rotate"); st.rerun()
                if btn_cols_p2[3].button("⬇️", key="p2_down_2p_btn", use_container_width=True, disabled=common_gs['paused']):
                    handle_input_2p(2, "down"); st.rerun()

    if common_gs['game_over_global']:
        winner_msg = "Empate!"
        if not p1_gs['alive'] and p2_gs['alive']: winner_msg = "Jogador 2 Vence!"
        elif p1_gs['alive'] and not p2_gs['alive']: winner_msg = "Jogador 1 Vence!"
        elif p1_gs['score'] > p2_gs['score']: winner_msg = "Jogador 1 Vence!"
        elif p2_gs['score'] > p1_gs['score']: winner_msg = "Jogador 2 Vence!"
        st.subheader(winner_msg)

        col_gm_opts1, col_gm_opts2 = st.columns(2)
        if col_gm_opts1.button("🔄 Novo Jogo (2P)", key="gameover_new_2p_btn", use_container_width=True):
            inicializar_jogo_2p()
            st.session_state.played_balloons_2p = False
            st.rerun()
        if col_gm_opts2.button("⬅️ Voltar ao Menu", key="gameover_menu_2p_btn", use_container_width=True):
            st.session_state.screen = "menu"
            st.session_state.played_balloons_2p = False
            st.rerun()
        return

    if not common_gs['game_over_global'] and not common_gs['paused']:
        if p1_gs['alive'] or p2_gs['alive']:
            time.sleep(0.05) # Pequeno sleep para controlar a taxa de atualização
            st.rerun()


# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
def main():
    st.set_page_config(layout="wide", page_title="Streamlit Tetris by Gustavo L.")
    inicializar_estado_sessao() # Garante que 'screen' e 'last_key_pressed' existam

    if st.session_state.screen == "menu":
        render_menu()
    elif st.session_state.screen == "commands":
        render_commands()
    elif st.session_state.screen == "game_1p":
        render_game_1p()
    elif st.session_state.screen == "game_2p":
        render_game_2p()
    elif st.session_state.screen == "quit":
        st.title("👋 Obrigado por jogar!")
        st.balloons()
        if st.button("⬅️ Voltar ao Menu Principal", key="quit_to_menu_btn"):
            st.session_state.screen = "menu"
            st.rerun()

if __name__ == "__main__":
    main()
