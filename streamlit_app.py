import streamlit as st
import time
import random
import copy

# ... (todo o código anterior permanece o mesmo até a seção de renderização) ...

# ─────────────────────────────────────────────
# PARÂMETROS GERAIS
# ─────────────────────────────────────────────
PREVIEW_ROWS = 4
GAME_ROWS    = 20
INNER_W      = 20
LINHA_VAZIA  = "<!" + " ." * 10 + " !>"
EMPTY_CELL = " ."
BLOCK_CELL = "[]"

BASE_SLEEP   = 0.05
LEVEL_STEP   = 30
SPEED_STEP   = 0.005
MIN_SLEEP    = 0.02
DROP_MOD     = 4
PYTHON_GAME_LOOP_INTERVAL = 0.03 # Intervalo do loop principal Python (aprox. 33 FPS)

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
    preview = [[EMPTY_CELL for _ in range(INNER_W // 2)] for _ in range(PREVIEW_ROWS)]
    jogo    = [[EMPTY_CELL for _ in range(INNER_W // 2)] for _ in range(GAME_ROWS)]
    return {"preview": preview, "game": jogo}

def formatar_tabuleiro_para_exibicao(tab_data_game_area, proxima_peca_preview=None, score=0, level=0, msg_extra=None, player_id=None, current_peca_info=None):
    linhas_finais = []
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
    if player_id is None:
        linhas_finais.append(linha_texto(f"SCORE: {score:05}"))
        linhas_finais.append(linha_texto(f"NÍVEL: {level}"))
    if msg_extra:
        linhas_finais.append(linha_texto(msg_extra))
    return "\n".join(linhas_finais)

def piece_to_preview_lines(peca_data):
    linhas = []
    for row in peca_data:
        linha_str = ""
        for cell in row:
            linha_str += BLOCK_CELL if cell == BLOCK_CELL else "  "
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
                if not (0 <= tab_c < (INNER_W // 2)): return True
                if tab_r >= GAME_ROWS: return True
                if tab_r < 0: continue
                if tab_game_data[tab_r][tab_c] == BLOCK_CELL: return True
    return False

def colisao_topo_game_over(tab_game_data, peca, x_peca, y_peca_display_inicial):
    for r_idx_peca, linha_p in enumerate(peca):
        for c_idx_peca, bloco in enumerate(linha_p):
            if bloco == BLOCK_CELL:
                tab_r = y_peca_display_inicial - r_idx_peca
                tab_c = x_peca + c_idx_peca
                if 0 <= tab_r < GAME_ROWS and 0 <= tab_c < (INNER_W // 2):
                    if tab_game_data[tab_r][tab_c] == BLOCK_CELL: return True
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
    for r in range(GAME_ROWS -1, -1, -1):
        linha = tab_game_data[r]
        if EMPTY_CELL in linha:
            linhas_a_manter.append(linha)
        else:
            linhas_limpas += 1
    novas_linhas_topo = [[EMPTY_CELL for _ in range(INNER_W // 2)] for _ in range(linhas_limpas)]
    novo_tab_game_data = novas_linhas_topo + list(reversed(linhas_a_manter))
    while len(novo_tab_game_data) < GAME_ROWS:
        novo_tab_game_data.insert(0, [EMPTY_CELL for _ in range(INNER_W // 2)])
    return novo_tab_game_data[:GAME_ROWS], linhas_limpas


# ─────────────────────────────────────────────
# INICIALIZAÇÃO DO JOGO E ESTADO
# ─────────────────────────────────────────────
def inicializar_estado_sessao():
    if "screen" not in st.session_state:
        st.session_state.screen = "menu"
    if 'last_keyboard_input' not in st.session_state:
        st.session_state.last_keyboard_input = {}

def _spawn_nova_peca(gs_dict_ou_prefixo, is_2p_player_num=None):
    if is_2p_player_num:
        gs = st.session_state[f'{gs_dict_ou_prefixo}{is_2p_player_num}']
    else:
        gs = st.session_state[gs_dict_ou_prefixo]
    gs['peca_atual'] = gs['proxima_peca']
    gs['proxima_peca'] = random.choice(TODAS)
    gs['y_display'] = altura_peca(gs['peca_atual']) -1
    gs['x'] = (INNER_W // 4) - largura_peca(gs['peca_atual']) // 2
    gs['last_drop_time'] = time.time()
    if colisao_topo_game_over(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display']):
        if is_2p_player_num:
            gs['alive'] = False
            p1_alive = st.session_state.game_2p_p1.get('alive', False)
            p2_alive = st.session_state.game_2p_p2.get('alive', False)
            if not p1_alive and not p2_alive:
                st.session_state.game_2p_common['game_over_global'] = True
                st.balloons()
        else:
            gs['game_over'] = True
            st.balloons()
        return False
    return True

def inicializar_jogo_1p():
    st.session_state.game_1p = {
        "tab_data": criar_tabuleiro_data()["game"], "proxima_peca": random.choice(TODAS),
        "score": 0, "level": 1, "start_time": time.time(), "paused": False,
        "game_over": False, "last_rot_time": 0,
    }
    _spawn_nova_peca('game_1p')
    st.session_state.last_keyboard_input = {}


def inicializar_jogo_2p():
    st.session_state.game_2p_common = {
        "level": 1, "start_time": time.time(), "paused": False, "game_over_global": False,
    }
    for i in range(1, 3):
        st.session_state[f'game_2p_p{i}'] = {
            "tab_data": criar_tabuleiro_data()["game"], "proxima_peca": random.choice(TODAS),
            "score": 0, "alive": True, "last_rot_time": 0,
        }
        _spawn_nova_peca('game_2p_p', i)
    st.session_state.last_keyboard_input = {}

# ─────────────────────────────────────────────
# LÓGICA DO JOGO (SINGLE PLAYER)
# ─────────────────────────────────────────────
def logica_jogo_1p_tick():
    gs = st.session_state.game_1p
    if gs['game_over'] or gs['paused']: return
    elapsed_time = time.time() - gs['start_time']
    gs['level'] = 1 + int(elapsed_time // LEVEL_STEP)
    game_speed_interval = max(MIN_SLEEP, BASE_SLEEP - (gs['level']-1)*SPEED_STEP) * DROP_MOD
    force_drop = st.session_state.pop("force_drop_1p", False) # Esta flag não é mais usada diretamente pelo input do teclado
    
    # A ação 'down' do teclado agora causa uma descida imediata em handle_input_1p.
    # Esta seção lida com a queda natural.
    if time.time() - gs.get('last_drop_time', gs['start_time']) > game_speed_interval :
        if gs.get('peca_atual') and not colisao(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display'] + 1):
            gs['y_display'] += 1
            gs['last_drop_time'] = time.time()
        elif gs.get('peca_atual'): # Se há peça e colidiu ao tentar descer naturalmente
            gs['tab_data'] = fixar_peca_no_tabuleiro(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display'])
            gs['tab_data'], linhas_limpas = limpar_linhas_completas(gs['tab_data'])
            gs['score'] += (linhas_limpas ** 2) * 100 if linhas_limpas > 0 else 0
            if not _spawn_nova_peca('game_1p'): return

def handle_input_1p(action): 
    gs = st.session_state.game_1p
    if gs['game_over'] or gs['paused'] or not gs.get('peca_atual'): return

    current_time = time.time()
    moved_or_rotated = False
    collided_after_action = False

    if action == "left":
        if not colisao(gs['tab_data'], gs['peca_atual'], gs['x'] - 1, gs['y_display']):
            gs['x'] -= 1
            moved_or_rotated = True
    elif action == "right":
        if not colisao(gs['tab_data'], gs['peca_atual'], gs['x'] + 1, gs['y_display']):
            gs['x'] += 1
            moved_or_rotated = True
    elif action == "down":
         if not colisao(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display'] + 1):
            gs['y_display'] += 1
            moved_or_rotated = True # Consideramos como uma ação que pode precisar resetar o drop time
         else: # Colidiu ao tentar descer
            collided_after_action = True
    elif action == "rotate":
        if current_time - gs.get('last_rot_time', 0) > 0.2: 
            peca_rotacionada = rotacionar(gs['peca_atual'])
            new_x = gs['x']
            if new_x + largura_peca(peca_rotacionada) > (INNER_W // 2):
                new_x = (INNER_W // 2) - largura_peca(peca_rotacionada)
            if new_x < 0: new_x = 0
            if not colisao(gs['tab_data'], peca_rotacionada, new_x, gs['y_display']):
                gs['peca_atual'] = peca_rotacionada
                gs['x'] = new_x
                gs['last_rot_time'] = current_time
                moved_or_rotated = True
    
    if moved_or_rotated:
        gs['last_drop_time'] = time.time() # Reseta o tempo da queda natural após uma ação
        # Se a ação foi 'down' e colidiu, precisa fixar a peça.
        if action == "down" and colisao(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display'] + 1): # Verifica colisão após o 'down'
             collided_after_action = True


    if collided_after_action: # Se uma ação de 'down' resultou em colisão imediata
        gs['tab_data'] = fixar_peca_no_tabuleiro(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display'])
        gs['tab_data'], linhas_limpas = limpar_linhas_completas(gs['tab_data'])
        gs['score'] += (linhas_limpas ** 2) * 100 if linhas_limpas > 0 else 0
        _spawn_nova_peca('game_1p') # Não precisa verificar retorno aqui, logica_jogo_tick fará


# ─────────────────────────────────────────────
# LÓGICA DO JOGO (MULTIPLAYER)
# ─────────────────────────────────────────────
def logica_jogo_2p_tick_player(player_idx):
    common_gs = st.session_state.game_2p_common
    player_gs = st.session_state[f'game_2p_p{player_idx}']
    if common_gs['game_over_global'] or common_gs['paused'] or not player_gs['alive'] or not player_gs.get('peca_atual'): return
    
    elapsed_time = time.time() - common_gs['start_time']
    common_gs['level'] = 1 + int(elapsed_time // LEVEL_STEP)
    game_speed_interval = max(MIN_SLEEP, BASE_SLEEP - (common_gs['level']-1)*SPEED_STEP) * DROP_MOD
    
    if time.time() - player_gs.get('last_drop_time', common_gs['start_time']) > game_speed_interval:
        if player_gs.get('peca_atual') and not colisao(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'], player_gs['y_display'] + 1):
            player_gs['y_display'] += 1
            player_gs['last_drop_time'] = time.time()
        elif player_gs.get('peca_atual'):
            player_gs['tab_data'] = fixar_peca_no_tabuleiro(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'], player_gs['y_display'])
            player_gs['tab_data'], linhas_limpas = limpar_linhas_completas(player_gs['tab_data'])
            player_gs['score'] += (linhas_limpas ** 2) * 100 if linhas_limpas > 0 else 0
            if not _spawn_nova_peca('game_2p_p', player_idx): return

def handle_input_2p(player_idx, action):
    common_gs = st.session_state.game_2p_common
    player_gs = st.session_state[f'game_2p_p{player_idx}']
    if common_gs['game_over_global'] or common_gs['paused'] or not player_gs['alive'] or not player_gs.get('peca_atual'): return

    current_time = time.time()
    moved_or_rotated = False
    collided_after_action = False

    if action == "left":
        if not colisao(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'] - 1, player_gs['y_display']):
            player_gs['x'] -= 1
            moved_or_rotated = True
    elif action == "right":
        if not colisao(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'] + 1, player_gs['y_display']):
            player_gs['x'] += 1
            moved_or_rotated = True
    elif action == "down":
        if not colisao(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'], player_gs['y_display'] + 1):
            player_gs['y_display'] += 1
            moved_or_rotated = True
        else:
            collided_after_action = True
    elif action == "rotate":
        if current_time - player_gs.get('last_rot_time', 0) > 0.2:
            peca_rotacionada = rotacionar(player_gs['peca_atual'])
            new_x = player_gs['x']
            if new_x + largura_peca(peca_rotacionada) > (INNER_W // 2):
                new_x = (INNER_W // 2) - largura_peca(peca_rotacionada)
            if new_x < 0: new_x = 0
            if not colisao(player_gs['tab_data'], peca_rotacionada, new_x, player_gs['y_display']):
                player_gs['peca_atual'] = peca_rotacionada
                player_gs['x'] = new_x
                player_gs['last_rot_time'] = current_time
                moved_or_rotated = True
    
    if moved_or_rotated:
        player_gs['last_drop_time'] = time.time()
        if action == "down" and colisao(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'], player_gs['y_display'] + 1):
            collided_after_action = True

    if collided_after_action:
        player_gs['tab_data'] = fixar_peca_no_tabuleiro(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'], player_gs['y_display'])
        player_gs['tab_data'], linhas_limpas = limpar_linhas_completas(player_gs['tab_data'])
        player_gs['score'] += (linhas_limpas ** 2) * 100 if linhas_limpas > 0 else 0
        _spawn_nova_peca('game_2p_p', player_idx)


# ─────────────────────────────────────────────
# COMPONENTE DE TECLADO HTML/JS
# ─────────────────────────────────────────────
KEYBOARD_COMPONENT_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Streamlit Keyboard Input</title>
  <style> body {{ margin: 0; padding: 0; }} #info {{ display: none; }} </style>
</head>
<body>
  <div id="info">Keyboard listener active</div>
  <script>
    const pressedKeys = new Set();
    const P1_KEYS = ['arrowup', 'arrowdown', 'arrowleft', 'arrowright'];
    const P2_KEYS = ['w', 'a', 's', 'd']; // Mantendo minúsculas como no JS
    const ALL_RELEVANT_KEYS = [...P1_KEYS, ...P2_KEYS];

    function getActionState() {
        const p1_actions = [];
        const p2_actions = [];

        // Player 1 - Setas
        if (pressedKeys.has('arrowleft')) p1_actions.push("left");
        if (pressedKeys.has('arrowright')) p1_actions.push("right");
        if (pressedKeys.has('arrowup')) p1_actions.push("rotate");
        if (pressedKeys.has('arrowdown')) p1_actions.push("down");

        // Player 2 - ASDW (JS usa 'a', 's', 'd', 'w' minúsculas)
        if (pressedKeys.has('a')) p2_actions.push("left");
        if (pressedKeys.has('d')) p2_actions.push("right");
        if (pressedKeys.has('w')) p2_actions.push("rotate");
        if (pressedKeys.has('s')) p2_actions.push("down");
        
        const component_value = {};
        if (p1_actions.length > 0) component_value.p1 = p1_actions;
        if (p2_actions.length > 0) component_value.p2 = p2_actions;
        
        Streamlit.setComponentValue(Object.keys(component_value).length > 0 ? component_value : null);
    }

    document.addEventListener('keydown', (event) => {
        const key = event.key.toLowerCase(); // Sempre usar minúsculas para consistência
        if (ALL_RELEVANT_KEYS.includes(key)) {
            event.preventDefault(); 
            if (!pressedKeys.has(key)) { 
                pressedKeys.add(key);
                getActionState(); 
            }
        }
    });

    document.addEventListener('keyup', (event) => {
        const key = event.key.toLowerCase(); // Sempre usar minúsculas
        if (ALL_RELEVANT_KEYS.includes(key)) {
            event.preventDefault();
            pressedKeys.delete(key);
            getActionState(); 
        }
    });

    window.addEventListener('load', () => {
      Streamlit.setFrameHeight(1); 
      getActionState(); 
    });
  </script>
</body>
</html>
"""

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
    if st.button("🚀 Jogar 1 Player", key="menu_1p_btn", use_container_width=True): # Adicionado _btn para evitar conflito com key do componente
        inicializar_jogo_1p()
        st.session_state.screen = "game_1p"
        st.rerun()
    if st.button("🧑‍🤝‍🧑 Jogar 2 Players", key="menu_2p_btn", use_container_width=True):
        inicializar_jogo_2p()
        st.session_state.screen = "game_2p"
        st.rerun()
    if st.button("📜 Comandos", key="menu_cmd_btn", use_container_width=True):
        st.session_state.screen = "commands"
        st.rerun()
    if st.button("🚪 Sair", key="menu_quit_btn", use_container_width=True):
        st.session_state.screen = "quit"
        st.rerun()

def render_commands():
    st.header("📜 Comandos")
    st.markdown(f"""
    ### Controles Gerais:
    - Utilize os botões na tela ou o teclado para interagir.
    - `Pausar/Retomar (Botão)`: Pausa ou continua o jogo.
    - `Sair para Menu (Botão)`: Encerra a partida atual e retorna ao menu.

    ### Jogador 1 (Modo 1P ou Jogador 1 no Modo 2P):
    - **Teclado:**
        - `Seta para Esquerda`: Mover peça para esquerda.
        - `Seta para Direita`: Mover peça para direita.
        - `Seta para Cima`: Rotacionar a peça atual.
        - `Seta para Baixo`: Acelerar a queda da peça atual.
    - **Botões na Tela:** Funcionalidade correspondente.

    ### Jogador 2 (Apenas no Modo 2P):
    - **Teclado:**
        - `A`: Mover peça para esquerda.
        - `D`: Mover peça para direita.
        - `W`: Rotacionar a peça atual.
        - `S`: Acelerar a queda da peça atual.
    - **Botões na Tela:** Funcionalidade correspondente.
    
    ### Gameplay:
    - **Níveis**: A dificuldade aumenta a cada {LEVEL_STEP} segundos.
    - **Pontuação**: Complete linhas para ganhar pontos!
    """)
    if st.button("⬅️ Voltar ao Menu", key="cmd_back_btn"):
        st.session_state.screen = "menu"
        st.rerun()

def render_game_1p():
    gs = st.session_state.game_1p
    
    # Correção: Removido o argumento 'key' da chamada html
    keyboard_actions = st.components.v1.html(KEYBOARD_COMPONENT_HTML, height=0) 

    if not gs['game_over'] and not gs['paused'] and keyboard_actions:
        if isinstance(keyboard_actions, dict):
            p1_key_actions = keyboard_actions.get("p1", [])
            
            if "left" in p1_key_actions: handle_input_1p("left")
            elif "right" in p1_key_actions: handle_input_1p("right")
            
            if "rotate" in p1_key_actions: handle_input_1p("rotate")
            if "down" in p1_key_actions: handle_input_1p("down")

    if not gs['game_over'] and not gs['paused']:
        logica_jogo_1p_tick()

    display_message = None
    if gs['game_over']: display_message = "GAME OVER"
    elif gs['paused']: display_message = "PAUSADO"
    
    current_peca_info_1p = None
    if not gs['game_over'] and gs.get('peca_atual'): 
        current_peca_info_1p = {"peca_atual": gs['peca_atual'], "x": gs['x'], "y_display": gs['y_display']}

    tab_str = formatar_tabuleiro_para_exibicao(
        gs['tab_data'], gs['proxima_peca'], gs['score'], gs['level'],
        display_message, player_id=None, current_peca_info=current_peca_info_1p
    )
    game_placeholder = st.empty()
    game_placeholder.code(tab_str, language="text")

    if gs['game_over']:
        st.error("FIM DE JOGO!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Novo Jogo (1P)", key="govr_new_1p_btn", use_container_width=True): inicializar_jogo_1p(); st.rerun()
        with col2:
            if st.button("⬅️ Voltar ao Menu", key="govr_menu_1p_btn", use_container_width=True): st.session_state.screen = "menu"; st.rerun()
        return

    cols = st.columns(4)
    # Removido st.rerun() dos botões para centralizar no loop principal
    if cols[0].button("⬅️", key="btn_p1_left_ui", use_container_width=True, disabled=gs['paused']): handle_input_1p("left")
    if cols[1].button("➡️", key="btn_p1_right_ui", use_container_width=True, disabled=gs['paused']): handle_input_1p("right")
    if cols[2].button("🔄", key="btn_p1_rotate_ui", use_container_width=True, disabled=gs['paused']): handle_input_1p("rotate")
    if cols[3].button("⬇️", key="btn_p1_down_ui", use_container_width=True, disabled=gs['paused']): handle_input_1p("down")

    col_opts1, col_opts2 = st.columns(2)
    if col_opts1.button("❚❚ Pausar/Retomar" if not gs['paused'] else "▶️ Pausar/Retomar", key="pause_1p_btn", use_container_width=True):
        gs['paused'] = not gs['paused']
        if not gs['paused']: gs['last_drop_time'] = time.time()
        st.session_state.last_keyboard_input = {} 
    
    if col_opts2.button("🚪 Sair para Menu", key="quit_1p_btn", use_container_width=True):
        st.session_state.screen = "menu"; st.rerun() # Sair para o menu deve ser imediato

    if not gs['game_over'] and not gs['paused']:
        time.sleep(PYTHON_GAME_LOOP_INTERVAL)
        st.rerun()


def render_game_2p():
    common_gs = st.session_state.game_2p_common
    p1_gs = st.session_state.game_2p_p1
    p2_gs = st.session_state.game_2p_p2

    # Correção: Removido o argumento 'key' da chamada html
    keyboard_actions = st.components.v1.html(KEYBOARD_COMPONENT_HTML, height=0)

    if not common_gs['game_over_global'] and not common_gs['paused'] and keyboard_actions:
        if isinstance(keyboard_actions, dict):
            if p1_gs['alive']:
                p1_key_actions = keyboard_actions.get("p1", [])
                if "left" in p1_key_actions: handle_input_2p(1, "left")
                elif "right" in p1_key_actions: handle_input_2p(1, "right")
                if "rotate" in p1_key_actions: handle_input_2p(1, "rotate")
                if "down" in p1_key_actions: handle_input_2p(1, "down")
            
            if p2_gs['alive']:
                p2_key_actions = keyboard_actions.get("p2", [])
                if "left" in p2_key_actions: handle_input_2p(2, "left")
                elif "right" in p2_key_actions: handle_input_2p(2, "right")
                if "rotate" in p2_key_actions: handle_input_2p(2, "rotate")
                if "down" in p2_key_actions: handle_input_2p(2, "down")

    if not common_gs['game_over_global'] and not common_gs['paused']:
        if p1_gs['alive']: logica_jogo_2p_tick_player(1)
        if p2_gs['alive']: logica_jogo_2p_tick_player(2)
    
    st.subheader(f"Nível Comum: {common_gs['level']}")
    if common_gs['paused']: st.warning("JOGO PAUSADO")
    if common_gs['game_over_global']: st.error("FIM DE JOGO PARA AMBOS!")

    game_area_placeholder = st.empty()
    with game_area_placeholder.container():
        col_p1, col_score, col_p2 = st.columns([2,1,2])
        with col_p1: # ... (UI P1 com botões)
            st.markdown("<h4 style='text-align: center;'>Jogador 1 (Setas)</h4>", unsafe_allow_html=True)
            msg1 = None; current_peca_info_p1 = None
            if not p1_gs['alive']: msg1 = "ELIMINADO!"
            elif common_gs['paused']: msg1 = "PAUSADO"
            elif p1_gs.get('peca_atual'): current_peca_info_p1 = {"peca_atual": p1_gs['peca_atual'], "x": p1_gs['x'], "y_display": p1_gs['y_display']}
            tab_str_p1 = formatar_tabuleiro_para_exibicao(p1_gs['tab_data'], p1_gs['proxima_peca'], player_id=1, msg_extra=msg1, current_peca_info=current_peca_info_p1)
            st.code(tab_str_p1, language="text")
            if p1_gs['alive'] and not common_gs['game_over_global']:
                btn_cols_p1 = st.columns(4)
                if btn_cols_p1[0].button("⬅️ P1", key="btn_2p_p1_left_ui", use_container_width=True, disabled=common_gs['paused']): handle_input_2p(1, "left")
                if btn_cols_p1[1].button("➡️ P1", key="btn_2p_p1_right_ui", use_container_width=True, disabled=common_gs['paused']): handle_input_2p(1, "right")
                if btn_cols_p1[2].button("🔄 P1", key="btn_2p_p1_rotate_ui", use_container_width=True, disabled=common_gs['paused']): handle_input_2p(1, "rotate")
                if btn_cols_p1[3].button("⬇️ P1", key="btn_2p_p1_down_ui", use_container_width=True, disabled=common_gs['paused']): handle_input_2p(1, "down")
        
        with col_score: # ... (UI Placar e botões Pause/Sair)
            st.markdown("<h4 style='text-align: center;'>Placar</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 1.2em; text-align: center;'>P1: {p1_gs['score']:05}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 1.2em; text-align: center;'>P2: {p2_gs['score']:05}</p>", unsafe_allow_html=True)
            st.markdown("---")
            if st.button("❚❚ Pausar" if not common_gs['paused'] else "▶️ Retomar", key="pause_2p_btn", use_container_width=True):
                common_gs['paused'] = not common_gs['paused']
                if not common_gs['paused']:
                    if p1_gs['alive']: p1_gs['last_drop_time'] = time.time()
                    if p2_gs['alive']: p2_gs['last_drop_time'] = time.time()
                st.session_state.last_keyboard_input = {}
            if st.button("🚪 Sair Menu", key="quit_2p_btn", use_container_width=True): st.session_state.screen = "menu"; st.rerun()

        with col_p2: # ... (UI P2 com botões)
            st.markdown("<h4 style='text-align: center;'>Jogador 2 (ASDW)</h4>", unsafe_allow_html=True)
            msg2 = None; current_peca_info_p2 = None
            if not p2_gs['alive']: msg2 = "ELIMINADO!"
            elif common_gs['paused']: msg2 = "PAUSADO"
            elif p2_gs.get('peca_atual'): current_peca_info_p2 = {"peca_atual": p2_gs['peca_atual'], "x": p2_gs['x'], "y_display": p2_gs['y_display']}
            tab_str_p2 = formatar_tabuleiro_para_exibicao(p2_gs['tab_data'], p2_gs['proxima_peca'], player_id=2, msg_extra=msg2, current_peca_info=current_peca_info_p2)
            st.code(tab_str_p2, language="text")
            if p2_gs['alive'] and not common_gs['game_over_global']:
                btn_cols_p2 = st.columns(4)
                if btn_cols_p2[0].button("⬅️ P2", key="btn_2p_p2_left_ui", use_container_width=True, disabled=common_gs['paused']): handle_input_2p(2, "left")
                if btn_cols_p2[1].button("➡️ P2", key="btn_2p_p2_right_ui", use_container_width=True, disabled=common_gs['paused']): handle_input_2p(2, "right")
                if btn_cols_p2[2].button("🔄 P2", key="btn_2p_p2_rotate_ui", use_container_width=True, disabled=common_gs['paused']): handle_input_2p(2, "rotate")
                if btn_cols_p2[3].button("⬇️ P2", key="btn_2p_p2_down_ui", use_container_width=True, disabled=common_gs['paused']): handle_input_2p(2, "down")

    if common_gs['game_over_global']: 
        winner_msg = "Empate!"
        if p1_gs['score'] > p2_gs['score']: winner_msg = "Jogador 1 Vence!"
        elif p2_gs['score'] > p1_gs['score']: winner_msg = "Jogador 2 Vence!"
        st.subheader(winner_msg)
        col_gm_opts1, col_gm_opts2 = st.columns(2)
        if col_gm_opts1.button("🔄 Novo Jogo (2P)", key="govr_new_2p_btn", use_container_width=True): inicializar_jogo_2p(); st.rerun()
        if col_gm_opts2.button("⬅️ Voltar ao Menu", key="govr_menu_2p_btn", use_container_width=True): st.session_state.screen = "menu"; st.rerun()
        return

    if not common_gs['game_over_global'] and not common_gs['paused']:
        if p1_gs['alive'] or p2_gs['alive']:
            time.sleep(PYTHON_GAME_LOOP_INTERVAL)
            st.rerun()


# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
def main():
    st.set_page_config(layout="wide", page_title="Streamlit Tetris - Custom Input v2")
    inicializar_estado_sessao()

    if st.session_state.screen == "menu": render_menu()
    elif st.session_state.screen == "commands": render_commands()
    elif st.session_state.screen == "game_1p": render_game_1p()
    elif st.session_state.screen == "game_2p": render_game_2p()
    elif st.session_state.screen == "quit": 
        st.title("👋 Obrigado por jogar!")
        st.balloons()
        if st.button("⬅️ Voltar ao Menu Principal", key="quit_to_menu_btn"):
            st.session_state.screen = "menu"
            st.rerun()

if __name__ == "__main__":
    main()
