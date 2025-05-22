
# streamlit_app.py
# Tetris adaptado para Streamlit
import streamlit as st
import random

LARGURA = 10
ALTURA = 20

PECAS = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[0,1,0], [1,1,1]],
    "L": [[1,0], [1,0], [1,1]],
    "J": [[0,1], [0,1], [1,1]],
    "S": [[0,1,1], [1,1,0]],
    "Z": [[1,1,0], [0,1,1]]
}

if "tabuleiro" not in st.session_state:
    st.session_state.tabuleiro = [[0]*LARGURA for _ in range(ALTURA)]
    st.session_state.peca = random.choice(list(PECAS.values()))
    st.session_state.x = 3
    st.session_state.y = 0
    st.session_state.jogo_ativo = True
    st.session_state.score = 0

def desenhar_tabuleiro():
    linhas = ""
    for i in range(ALTURA):
        for j in range(LARGURA):
            if st.session_state.tabuleiro[i][j]:
                linhas += "🟥"
            elif esta_peca(i, j):
                linhas += "🟦"
            else:
                linhas += "⬛"
        linhas += "\n"
    return linhas

def esta_peca(i, j):
    p = st.session_state.peca
    for y, linha in enumerate(p):
        for x, val in enumerate(linha):
            if val:
                px = st.session_state.x + x
                py = st.session_state.y + y
                if px == j and py == i:
                    return True
    return False

def mover(dx, dy):
    st.session_state.x += dx
    st.session_state.y += dy

def fixar_peca():
    p = st.session_state.peca
    for y, linha in enumerate(p):
        for x, val in enumerate(linha):
            if val:
                px = st.session_state.x + x
                py = st.session_state.y + y
                if 0 <= px < LARGURA and 0 <= py < ALTURA:
                    st.session_state.tabuleiro[py][px] = 1
    limpar_linhas()
    nova_peca()

def limpar_linhas():
    nova = [linha for linha in st.session_state.tabuleiro if any(c == 0 for c in linha)]
    removidas = ALTURA - len(nova)
    st.session_state.score += removidas * 10
    st.session_state.tabuleiro = [[0]*LARGURA for _ in range(removidas)] + nova

def nova_peca():
    st.session_state.peca = random.choice(list(PECAS.values()))
    st.session_state.x = 3
    st.session_state.y = 0
    if colisao():
        st.session_state.jogo_ativo = False

def colisao():
    p = st.session_state.peca
    for y, linha in enumerate(p):
        for x, val in enumerate(linha):
            if val:
                px = st.session_state.x + x
                py = st.session_state.y + y
                if px < 0 or px >= LARGURA or py >= ALTURA:
                    return True
                if py >= 0 and st.session_state.tabuleiro[py][px]:
                    return True
    return False

st.title("🎮 Tetris com Streamlit")

if st.session_state.jogo_ativo:
    st.markdown(desenhar_tabuleiro())
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("⬅️"):
            st.session_state.x -= 1
    with col2:
        if st.button("⬇️"):
            st.session_state.y += 1
    with col3:
        if st.button("➡️"):
            st.session_state.x += 1
    with col4:
        if st.button("Fixar"):
            fixar_peca()
    st.markdown(f"**Pontos:** {st.session_state.score}")
else:
    st.markdown("### 💀 Game Over")
    if st.button("🔄 Recomeçar"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.experimental_rerun()
