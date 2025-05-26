import streamlit as st
import time
import random
import copy
import json # Ainda útil se o componente JS enviar JSON, mas vamos simplificar

# ─────────────────────────────────────────────
# PARÂMETROS GERAIS (sem grandes alterações)
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
PYTHON_GAME_LOOP_INTERVAL = 0.030 # Intervalo para ~33 FPS

def linha_texto(txt: str) -> str:
    return "<!" + txt.center(INNER_W) + " !>"

# ─────────────────────────────────────────────
# PEÇAS (código original)
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
# FUNÇÕES DO TABULEIRO (código original)
# ─────────────────────────────────────────────
def criar_tabuleiro_data():
    preview = [[EMPTY_CELL for _ in range(INNER_W // 2)] for _ in range(PREVIEW_ROWS)]
    jogo    = [[EMPTY_CELL for _ in range(INNER_W // 2)] for _ in range(GAME_ROWS)]
    return {"preview": preview, "game": jogo}

def formatar_tabuleiro_para_exibicao(tab_data_game_area, proxima_peca_preview=None, score=0, level=0, msg_extra=None, player_id=None, current_peca_info=None):
    # ... (código original mantido) ...
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
    # ... (código original mantido) ...
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
    # ... (código original mantido) ...
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
    # ... (código original mantido) ...
    for r_idx_peca, linha_p in enumerate(peca):
        for c_idx_peca, bloco in enumerate(linha_p):
            if bloco == BLOCK_CELL:
                tab_r = y_peca_display_inicial - r_idx_peca
                tab_c = x_peca + c_idx_peca
                if 0 <= tab_r < GAME_ROWS and 0 <= tab_c < (INNER_W // 2):
                    if tab_game_data[tab_r][tab_c] == BLOCK_CELL: return True
    return False

def fixar_peca_no_tabuleiro(tab_game_data, peca, x_peca, y_peca_display):
    # ... (código original mantido) ...
    for r_idx_peca, linha_p in enumerate(peca):
        for c_idx_peca, bloco in enumerate(linha_p):
            if bloco == BLOCK_CELL:
                tab_r = y_peca_display - r_idx_peca
                tab_c = x_peca + c_idx_peca
                if 0 <= tab_r < GAME_ROWS and 0 <= tab_c < (INNER_W // 2):
                    tab_game_data[tab_r][tab_c] = BLOCK_CELL
    return tab_game_data

def limpar_linhas_completas(tab_game_data):
    # ... (código original mantido) ...
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
    # Estado para o componente de teclado customizado
    if "keyboard_state" not in st.session_state:
        st.session_state.keyboard_state = {"p1_actions": [], "p2_actions": [], "system_action": None, "system_key_just_pressed": {}}

def _spawn_nova_peca(gs_dict_ou_prefixo, is_2p_player_num=None):
    # ... (código original mantido) ...
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
                if st.session_state.screen != "menu": st.balloons()
        else:
            gs['game_over'] = True
            if st.session_state.screen != "menu": st.balloons()
        return False
    return True


def inicializar_jogo_1p():
    # ... (código original mantido) ...
    st.session_state.game_1p = {
        "tab_data": criar_tabuleiro_data()["game"], "proxima_peca": random.choice(TODAS),
        "score": 0, "level": 1, "start_time": time.time(), "paused": False,
        "game_over": False, "last_rot_time": 0,
    }
    _spawn_nova_peca('game_1p')
    st.session_state.keyboard_state = {"p1_actions": [], "p2_actions": [], "system_action": None, "system_key_just_pressed": {}}


def inicializar_jogo_2p():
    # ... (código original mantido) ...
    st.session_state.game_2p_common = {
        "level": 1, "start_time": time.time(), "paused": False, "game_over_global": False,
    }
    for i in range(1, 3):
        st.session_state[f'game_2p_p{i}'] = {
            "tab_data": criar_tabuleiro_data()["game"], "proxima_peca": random.choice(TODAS),
            "score": 0, "alive": True, "last_rot_time": 0,
        }
        _spawn_nova_peca('game_2p_p', i)
    st.session_state.keyboard_state = {"p1_actions": [], "p2_actions": [], "system_action": None, "system_key_just_pressed": {}}

# ─────────────────────────────────────────────
# LÓGICA DO JOGO E INPUT HANDLERS
# ─────────────────────────────────────────────
def logica_jogo_1p_tick():
    # ... (código original mantido) ...
    gs = st.session_state.game_1p
    if gs['game_over'] or gs['paused'] or not gs.get('peca_atual'): return

    elapsed_time = time.time() - gs['start_time']
    gs['level'] = 1 + int(elapsed_time // LEVEL_STEP)
    game_speed_interval = max(MIN_SLEEP, BASE_SLEEP - (gs['level']-1)*SPEED_STEP) * DROP_MOD
    
    if time.time() - gs.get('last_drop_time', gs['start_time']) > game_speed_interval :
        if not colisao(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display'] + 1):
            gs['y_display'] += 1
            gs['last_drop_time'] = time.time()
        else: 
            gs['tab_data'] = fixar_peca_no_tabuleiro(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display'])
            gs['tab_data'], linhas_limpas = limpar_linhas_completas(gs['tab_data'])
            gs['score'] += (linhas_limpas ** 2) * 100 if linhas_limpas > 0 else 0
            if not _spawn_nova_peca('game_1p'): return

def handle_input_1p(action): 
    # ... (código original mantido e funcional) ...
    gs = st.session_state.game_1p
    if gs['game_over'] or gs['paused'] or not gs.get('peca_atual'): return

    current_time = time.time()
    action_taken_this_call = False 

    if action == "left":
        if not colisao(gs['tab_data'], gs['peca_atual'], gs['x'] - 1, gs['y_display']):
            gs['x'] -= 1; action_taken_this_call = True
    elif action == "right":
        if not colisao(gs['tab_data'], gs['peca_atual'], gs['x'] + 1, gs['y_display']):
            gs['x'] += 1; action_taken_this_call = True
    elif action == "down":
         if not colisao(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display'] + 1):
            gs['y_display'] += 1; action_taken_this_call = True
         else: 
            gs['tab_data'] = fixar_peca_no_tabuleiro(gs['tab_data'], gs['peca_atual'], gs['x'], gs['y_display'])
            gs['tab_data'], linhas_limpas = limpar_linhas_completas(gs['tab_data'])
            gs['score'] += (linhas_limpas ** 2) * 100 if linhas_limpas > 0 else 0
            _spawn_nova_peca('game_1p')
            return 
    elif action == "rotate":
        if current_time - gs.get('last_rot_time', 0) > 0.2: 
            peca_rotacionada = rotacionar(gs['peca_atual'])
            new_x = gs['x']
            if new_x + largura_peca(peca_rotacionada) > (INNER_W // 2): new_x = (INNER_W // 2) - largura_peca(peca_rotacionada)
            if new_x < 0: new_x = 0
            if not colisao(gs['tab_data'], peca_rotacionada, new_x, gs['y_display']):
                gs['peca_atual'] = peca_rotacionada; gs['x'] = new_x
                gs['last_rot_time'] = current_time; action_taken_this_call = True
    
    if action_taken_this_call:
        gs['last_drop_time'] = time.time()


def logica_jogo_2p_tick_player(player_idx):
    # ... (código original mantido) ...
    common_gs = st.session_state.game_2p_common
    player_gs = st.session_state[f'game_2p_p{player_idx}']
    if common_gs['game_over_global'] or common_gs['paused'] or not player_gs['alive'] or not player_gs.get('peca_atual'): return
    
    elapsed_time = time.time() - common_gs['start_time']
    actual_level = 1 + int(elapsed_time // LEVEL_STEP)
    if common_gs['level'] != actual_level:
        common_gs['level'] = actual_level

    game_speed_interval = max(MIN_SLEEP, BASE_SLEEP - (common_gs['level']-1)*SPEED_STEP) * DROP_MOD
    
    if time.time() - player_gs.get('last_drop_time', common_gs['start_time']) > game_speed_interval:
        if not colisao(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'], player_gs['y_display'] + 1):
            player_gs['y_display'] += 1
            player_gs['last_drop_time'] = time.time()
        else:
            player_gs['tab_data'] = fixar_peca_no_tabuleiro(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'], player_gs['y_display'])
            player_gs['tab_data'], linhas_limpas = limpar_linhas_completas(player_gs['tab_data'])
            player_gs['score'] += (linhas_limpas ** 2) * 100 if linhas_limpas > 0 else 0
            if not _spawn_nova_peca('game_2p_p', player_idx): return

def handle_input_2p(player_idx, action):
    # ... (código original mantido e funcional) ...
    common_gs = st.session_state.game_2p_common
    player_gs = st.session_state[f'game_2p_p{player_idx}']
    if common_gs['game_over_global'] or common_gs['paused'] or not player_gs['alive'] or not player_gs.get('peca_atual'): return

    current_time = time.time()
    action_taken_this_call = False

    if action == "left":
        if not colisao(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'] - 1, player_gs['y_display']):
            player_gs['x'] -= 1; action_taken_this_call = True
    elif action == "right":
        if not colisao(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'] + 1, player_gs['y_display']):
            player_gs['x'] += 1; action_taken_this_call = True
    elif action == "down":
        if not colisao(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'], player_gs['y_display'] + 1):
            player_gs['y_display'] += 1; action_taken_this_call = True
        else:
            player_gs['tab_data'] = fixar_peca_no_tabuleiro(player_gs['tab_data'], player_gs['peca_atual'], player_gs['x'], player_gs['y_display'])
            player_gs['tab_data'], linhas_limpas = limpar_linhas_completas(player_gs['tab_data'])
            player_gs['score'] += (linhas_limpas ** 2) * 100 if linhas_limpas > 0 else 0
            _spawn_nova_peca('game_2p_p', player_idx)
            return
    elif action == "rotate":
        if current_time - player_gs.get('last_rot_time', 0) > 0.2:
            peca_rotacionada = rotacionar(player_gs['peca_atual'])
            new_x = player_gs['x']
            if new_x + largura_peca(peca_rotacionada) > (INNER_W // 2): new_x = (INNER_W // 2) - largura_peca(peca_rotacionada)
            if new_x < 0: new_x = 0
            if not colisao(player_gs['tab_data'], peca_rotacionada, new_x, player_gs['y_display']):
                player_gs['peca_atual'] = peca_rotacionada; player_gs['x'] = new_x
                player_gs['last_rot_time'] = current_time; action_taken_this_call = True
    
    if action_taken_this_call:
        player_gs['last_drop_time'] = time.time()

# ─────────────────────────────────────────────
# COMPONENTE DE TECLADO HTML/JS (Revisado)
# ─────────────────────────────────────────────
KEYBOARD_COMPONENT_HTML = """
<!DOCTYPE html>
<html><head><title>Keyboard Handler</title><style>body{margin:0;}</style></head>
<body>
<script>
const pressedGameKeys = new Set();
const P1_KEYS_MAP = { 'arrowleft': 'left', 'arrowright': 'right', 'arrowup': 'rotate', 'arrowdown': 'down' };
const P2_KEYS_MAP = { 'a': 'left', 'd': 'right', 'w': 'rotate', 's': 'down' };
const SYSTEM_KEYS_MAP = { 'p': 'toggle_pause', 'escape': 'quit_to_menu' };
const ALL_RELEVANT_RAW_KEYS = [...Object.keys(P1_KEYS_MAP), ...Object.keys(P2_KEYS_MAP), ...Object.keys(SYSTEM_KEYS_MAP)];

// Variaveis para debounce de teclas de sistema (P, Escape)
let systemKeyLastProcessed = { 'p': 0, 'escape': 0 };
const SYSTEM_KEY_DEBOUNCE_MS = 200; // 200ms debounce

function sendStateToStreamlit() {
    const state = { p1_actions: [], p2_actions: [], system_action: null };
    
    pressedGameKeys.forEach(key => {
        if (P1_KEYS_MAP[key]) {
            state.p1_actions.push(P1_KEYS_MAP[key]);
        } else if (P2_KEYS_MAP[key]) {
            state.p2_actions.push(P2_KEYS_MAP[key]);
        }
    });

    // Para teclas de sistema, processamos no keydown e aplicamos debounce
    // O envio aqui é mais para limpar o 'system_action' se a tecla foi solta,
    // mas a ação principal é no keydown.
    // A lógica de 'system_action' no keydown é mais importante.

    // Remove arrays vazios para limpar a saida
    if (state.p1_actions.length === 0) delete state.p1_actions;
    if (state.p2_actions.length === 0) delete state.p2_actions;
    
    Streamlit.setComponentValue(Object.keys(state).length > 0 ? state : null);
}

document.addEventListener('keydown', (event) => {
    const rawKey = event.key.toLowerCase();
    if (ALL_RELEVANT_RAW_KEYS.includes(rawKey)) {
        event.preventDefault();
        
        if (SYSTEM_KEYS_MAP[rawKey]) { // É uma tecla de sistema
            const now = Date.now();
            if (now - systemKeyLastProcessed[rawKey] > SYSTEM_KEY_DEBOUNCE_MS) {
                Streamlit.setComponentValue({ system_action: SYSTEM_KEYS_MAP[rawKey] });
                systemKeyLastProcessed[rawKey] = now;
            }
        } else { // É uma tecla de jogo
            if (!pressedGameKeys.has(rawKey)) {
                pressedGameKeys.add(rawKey);
                sendStateToStreamlit();
            }
        }
    }
});

document.addEventListener('keyup', (event) => {
    const rawKey = event.key.toLowerCase();
    if (ALL_RELEVANT_RAW_KEYS.includes(rawKey)) {
        event.preventDefault();
        if (SYSTEM_KEYS_MAP[rawKey]) {
            systemKeyLastProcessed[rawKey] = 0; // Reseta debounce ao soltar
            // Envia estado nulo para system_action para limpar
            // Mas é importante que o Python já tenha processado o keydown.
            // A melhor forma é o Python consumir a ação de sistema e resetá-la.
        } else {
             if (pressedGameKeys.has(rawKey)) {
                pressedGameKeys.delete(rawKey);
                sendStateToStreamlit();
            }
        }
    }
});

window.addEventListener('load', () => {
    Streamlit.setFrameHeight(0); // Componente invisivel
    sendStateToStreamlit(); // Envia estado inicial (vazio)
});
</script>
</body></html>
"""

# ─────────────────────────────────────────────
# RENDERIZAÇÃO E TELAS (STREAMLIT)
# ─────────────────────────────────────────────
def render_menu():
    # ... (código dos botões de menu mantido por enquanto) ...
    st.title("TETRIS com Streamlit")
    st.markdown("---")
    st.subheader("Desenvolvido por: Gustavo de Almeida Leite")
    st.caption("Matrícula: 202504002") 
    st.caption("BIA UFG - 2025 | IP - PROF. LEO") 
    st.markdown("---")
    
    if st.button("🚀 Jogar 1 Player", key="menu_1p_btn", use_container_width=True):
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

def render_commands():
    # ... (tela de comandos atualizada, botão de voltar mantido) ...
    st.header("📜 Comandos do Teclado")
    st.markdown(f"""
    ### Controles Gerais (Durante o Jogo):
    - `P`: Pausar / Retomar o jogo.
    - `Esc`: Sair da partida atual e retornar ao Menu Principal.

    ### Jogador 1 (Modo 1P ou Jogador 1 no Modo 2P):
    - `Seta para Esquerda`: Mover peça para esquerda.
    - `Seta para Direita`: Mover peça para direita.
    - `Seta para Cima`: Rotacionar a peça atual.
    - `Seta para Baixo`: Acelerar a queda da peça atual.

    ### Jogador 2 (Apenas no Modo 2P):
    - `A`: Mover peça para esquerda.
    - `D`: Mover peça para direita.
    - `W`: Rotacionar a peça atual.
    - `S`: Acelerar a queda da peça atual.
    
    ### Gameplay:
    - **Níveis**: A dificuldade (velocidade) aumenta a cada {LEVEL_STEP} segundos.
    - **Pontuação**: Complete linhas para ganhar pontos!
    """)
    if st.button("⬅️ Voltar ao Menu Principal", key="cmd_back_btn"):
        st.session_state.screen = "menu"
        st.rerun()

def process_keyboard_input_for_game(keyboard_state, game_state, player_prefix, input_handler_func, player_idx=None):
    """Processa as ações de jogo do teclado para um jogador."""
    if not game_state['game_over'] and not game_state['paused'] and keyboard_state:
        actions = keyboard_state.get(f"{player_prefix}_actions", [])
        
        # Lógica para tratar múltiplas ações (ex: esquerda + rotação)
        # Prioridade: Movimento lateral > Rotação > Descida (ou processar todas se o handler permitir)
        # Por simplicidade, processaremos todas as ações detectadas.
        # Os handlers individuais (handle_input_1p/2p) já têm debounce para rotação.
        
        # Para evitar processar 'left' e 'right' simultaneamente se o JS enviar ambos (improvável com Set)
        has_moved_lr = False
        if "left" in actions:
            if player_idx: input_handler_func(player_idx, "left")
            else: input_handler_func("left")
            has_moved_lr = True
        if "right" in actions and not has_moved_lr:
            if player_idx: input_handler_func(player_idx, "right")
            else: input_handler_func("right")

        if "rotate" in actions:
            if player_idx: input_handler_func(player_idx, "rotate")
            else: input_handler_func("rotate")
        if "down" in actions:
            if player_idx: input_handler_func(player_idx, "down")
            else: input_handler_func("down")

def render_game_1p():
    gs = st.session_state.game_1p
    
    # O componente HTML retorna um dicionário com o estado das teclas
    # ou None se nenhuma tecla de jogo estiver ativa.
    # Ações de sistema são enviadas com 'system_action'.
    raw_keyboard_data = st.components.v1.html(KEYBOARD_COMPONENT_HTML, height=0)

    # Priorizar ações de sistema
    if raw_keyboard_data and isinstance(raw_keyboard_data, dict) and "system_action" in raw_keyboard_data:
        system_action = raw_keyboard_data["system_action"]
        if system_action == "toggle_pause":
            gs['paused'] = not gs['paused']
            if not gs['paused']: gs['last_drop_time'] = time.time()
            # Limpar a ação de sistema para não reprocessar no próximo rerun
            st.session_state.keyboard_state["system_action"] = None 
            st.rerun(); return 
        elif system_action == "quit_to_menu":
            st.session_state.screen = "menu"
            st.rerun(); return
    
    # Atualiza o estado global do teclado com os dados recebidos (para teclas de jogo)
    if raw_keyboard_data and isinstance(raw_keyboard_data, dict):
        st.session_state.keyboard_state["p1_actions"] = raw_keyboard_data.get("p1_actions", [])
    elif raw_keyboard_data is None : # Nenhuma tecla de jogo ativa
         st.session_state.keyboard_state["p1_actions"] = []


    # Processar inputs de jogo
    process_keyboard_input_for_game(st.session_state.keyboard_state, gs, "p1", handle_input_1p)

    if not gs['game_over'] and not gs['paused']:
        logica_jogo_1p_tick()

    display_message = None
    if gs['game_over']: display_message = "FIM DE JOGO"
    elif gs['paused']: display_message = "PAUSADO (Pressione 'P')"
    
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
        st.markdown("Pressione `Esc` para voltar ao Menu.")
        if st.button("⬅️ Voltar ao Menu Principal", key="gameover_1p_back_menu_btn"): # Botão mantido
            st.session_state.screen = "menu"; st.rerun()
        return

    if not gs['game_over']:
        time.sleep(PYTHON_GAME_LOOP_INTERVAL)
        st.rerun()


def render_game_2p():
    common_gs = st.session_state.game_2p_common
    p1_gs = st.session_state.game_2p_p1
    p2_gs = st.session_state.game_2p_p2
    
    raw_keyboard_data = st.components.v1.html(KEYBOARD_COMPONENT_HTML, height=0)

    if raw_keyboard_data and isinstance(raw_keyboard_data, dict) and "system_action" in raw_keyboard_data:
        system_action = raw_keyboard_data["system_action"]
        if system_action == "toggle_pause":
            common_gs['paused'] = not common_gs['paused']
            if not common_gs['paused']:
                if p1_gs['alive']: p1_gs['last_drop_time'] = time.time()
                if p2_gs['alive']: p2_gs['last_drop_time'] = time.time()
            st.session_state.keyboard_state["system_action"] = None
            st.rerun(); return
        elif system_action == "quit_to_menu":
            st.session_state.screen = "menu"; st.rerun(); return
    
    if raw_keyboard_data and isinstance(raw_keyboard_data, dict):
        st.session_state.keyboard_state["p1_actions"] = raw_keyboard_data.get("p1_actions", [])
        st.session_state.keyboard_state["p2_actions"] = raw_keyboard_data.get("p2_actions", [])
    elif raw_keyboard_data is None:
        st.session_state.keyboard_state["p1_actions"] = []
        st.session_state.keyboard_state["p2_actions"] = []


    if p1_gs['alive']:
        process_keyboard_input_for_game(st.session_state.keyboard_state, p1_gs, "p1", handle_input_2p, player_idx=1)
    if p2_gs['alive']:
        process_keyboard_input_for_game(st.session_state.keyboard_state, p2_gs, "p2", handle_input_2p, player_idx=2)


    if not common_gs['game_over_global'] and not common_gs['paused']:
        if p1_gs['alive']: logica_jogo_2p_tick_player(1)
        if p2_gs['alive']: logica_jogo_2p_tick_player(2)
    
    st.subheader(f"Nível Comum: {common_gs['level']}")
    if common_gs['paused']: st.warning("JOGO PAUSADO (Pressione 'P' para retomar)")
    if common_gs['game_over_global']: st.error("FIM DE JOGO PARA AMBOS!")

    game_area_placeholder = st.empty() # ... (UI 2P como antes, sem botões de controle)
    with game_area_placeholder.container():
        col_p1, col_score_info, col_p2 = st.columns([2,1,2]) 
        with col_p1:
            st.markdown("<h4 style='text-align: center;'>Jogador 1 (Setas)</h4>", unsafe_allow_html=True)
            msg1 = None; current_peca_info_p1 = None
            if not p1_gs['alive']: msg1 = "ELIMINADO!"
            elif common_gs['paused']: msg1 = "PAUSADO"
            elif p1_gs.get('peca_atual'): current_peca_info_p1 = {"peca_atual": p1_gs['peca_atual'], "x": p1_gs['x'], "y_display": p1_gs['y_display']}
            tab_str_p1 = formatar_tabuleiro_para_exibicao(p1_gs['tab_data'], p1_gs['proxima_peca'], player_id=1, msg_extra=msg1, current_peca_info=current_peca_info_p1)
            st.code(tab_str_p1, language="text")
        
        with col_score_info:
            st.markdown("<h4 style='text-align: center;'>Placar</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 1.2em; text-align: center;'>P1: {p1_gs['score']:05}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style_list='font-size: 1.2em; text-align: center;'>P2: {p2_gs['score']:05}</p>", unsafe_allow_html=True) # Corrigido style_list para style
            st.markdown("---")
            st.caption("P: Pausar/Retomar")
            st.caption("Esc: Sair para Menu")

        with col_p2:
            st.markdown("<h4 style='text-align: center;'>Jogador 2 (ASDW)</h4>", unsafe_allow_html=True)
            msg2 = None; current_peca_info_p2 = None
            if not p2_gs['alive']: msg2 = "ELIMINADO!"
            elif common_gs['paused']: msg2 = "PAUSADO"
            elif p2_gs.get('peca_atual'): current_peca_info_p2 = {"peca_atual": p2_gs['peca_atual'], "x": p2_gs['x'], "y_display": p2_gs['y_display']}
            tab_str_p2 = formatar_tabuleiro_para_exibicao(p2_gs['tab_data'], p2_gs['proxima_peca'], player_id=2, msg_extra=msg2, current_peca_info=current_peca_info_p2)
            st.code(tab_str_p2, language="text")


    if common_gs['game_over_global']: 
        winner_msg = "Empate!" # ... (lógica de game over 2P com botão de voltar mantido)
        if p1_gs['score'] > p2_gs['score']: winner_msg = "Jogador 1 Vence!"
        elif p2_gs['score'] > p1_gs['score']: winner_msg = "Jogador 2 Vence!"
        st.subheader(winner_msg)
        st.markdown("Pressione `Esc` para voltar ao Menu.")
        if st.button("⬅️ Voltar ao Menu Principal", key="gameover_2p_back_menu_btn"):
            st.session_state.screen = "menu"; st.rerun()
        return

    if not common_gs['game_over_global']:
        time.sleep(PYTHON_GAME_LOOP_INTERVAL)
        st.rerun()

# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
def main():
    st.set_page_config(layout="wide", page_title="Streamlit Tetris - Custom Component")
    inicializar_estado_sessao()

    if st.session_state.screen == "menu": render_menu()
    elif st.session_state.screen == "commands": render_commands()
    elif st.session_state.screen == "game_1p": render_game_1p()
    elif st.session_state.screen == "game_2p": render_game_2p()
    elif st.session_state.screen == "quit": 
        st.title("👋 Obrigado por jogar!")
        st.balloons()
        if st.button("⬅️ Voltar ao Menu Principal", key="quit_to_menu_btn"):
            st.session_state.screen = "menu"; st.rerun()

if __name__ == "__main__":
    main()
