"""Heurísticas do P6 (Rush Hour generalizado) e ferramentas para as estudar.

Notação: r = linha de saída, x = coluna esquerda de X, n = tamanho do tabuleiro.
O objectivo é x = n - 2. As casas "à frente de X" são (r, x+2), ..., (r, n-1).

h0  zero (A* passa a ser UCS).
h1  nº de veículos distintos à frente de X (dica do enunciado).
h2  h1 + nº de veículos distintos que impedem cada bloqueador directo de sair
    da linha r pelo lado mais curto (dica do enunciado; NÃO é admissível,
    ver relatório e tests/test_heuristicas.py).
h3  h1 + 1 se X ainda não está no objectivo (o último movimento de X é uma
    acção distinta da dos bloqueadores). Admissível e consistente no critério
    "movimentos"; domina h1.
h4  relaxação "cada veículo sozinho no tabuleiro": custo mínimo de X percorrer
    a distância que falta mais, para cada bloqueador directo, o custo mínimo de
    o tirar da linha r ignorando os outros veículos (mas não os obstáculos).
    Em "movimentos" coincide com h3; em "ponderado" vale 2·d + Σ L·deslocamento
    mínimo. Admissível e consistente nos dois critérios.

Estados sem solução detectáveis de imediato (obstáculo ou veículo horizontal
à frente de X, ou bloqueador vertical que não consegue sair da linha) devolvem
infinito em h1–h4, o que mantém a admissibilidade (h* = ∞).
"""
import heapq
import math
from collections import deque

INF = math.inf


def _grelha(p, s):
    """Grelha como dicionário (linha, coluna) -> id ('#' para obstáculo)."""
    g = {o: "#" for o in p.obstaculos}
    for v, pos in zip(p.veiculos, s):
        for k in range(v.comprimento):
            g[(v.fixa, pos + k) if v.orientacao == "H" else (pos + k, v.fixa)] = v.id
    return g


def bloqueadores(p, s, g=None):
    """Lista ordenada de ids que ocupam casas à frente de X; None se impossível."""
    g = _grelha(p, s) if g is None else g
    x = s[p.indice("X")]
    r = p.linha_saida
    vistos = []
    for c in range(x + 2, p.tamanho):
        ocupante = g.get((r, c))
        if ocupante is None or ocupante in vistos:
            continue
        if ocupante == "#":
            return None
        v = p.veiculos[p.indice(ocupante)]
        if v.orientacao == "H":  # nunca sai da linha de X
            return None
        vistos.append(ocupante)
    return vistos


def saidas(p, s, vid):
    """Para um bloqueador vertical, devolve [(deslocamento, casas_atravessadas)]
    das direcções possíveis para libertar a linha r, ignorando outros veículos."""
    v = p.veiculos[p.indice(vid)]
    pos = s[p.indice(vid)]
    r, col, L, n = p.linha_saida, v.fixa, v.comprimento, p.tamanho
    opcoes = []
    # para cima: a casa de baixo do veículo fica em r-1 => novo topo = r - L
    topo = r - L
    if topo >= 0:
        casas = [(lin, col) for lin in range(topo, pos)]
        if not any(c in p.obstaculos for c in casas):
            opcoes.append((topo - pos, casas))
    # para baixo: novo topo = r + 1
    topo = r + 1
    if topo + L <= n:
        casas = [(lin, col) for lin in range(pos + L, topo + L)]
        if not any(c in p.obstaculos for c in casas):
            opcoes.append((topo - pos, casas))
    return opcoes


def h0(p, s):
    return 0


def h1(p, s):
    b = bloqueadores(p, s)
    return INF if b is None else len(b)


def h2(p, s):
    g = _grelha(p, s)
    b = bloqueadores(p, s, g)
    if b is None:
        return INF
    segundo = set()
    for vid in b:
        opcoes = saidas(p, s, vid)
        if not opcoes:
            return INF
        _, casas = min(opcoes, key=lambda o: abs(o[0]))
        for c in casas:
            ocupante = g.get(c)
            if ocupante is not None and ocupante not in b and ocupante != "#":
                segundo.add(ocupante)
    return len(b) + len(segundo)


def h3(p, s):
    b = bloqueadores(p, s)
    if b is None:
        return INF
    return len(b) + (0 if p.e_objectivo(s) else 1)


def h4(p, s):
    b = bloqueadores(p, s)
    if b is None:
        return INF
    d = p.tamanho - 2 - s[p.indice("X")]
    ponderado = p.criterio == "ponderado"
    total = (2 * d if ponderado else (1 if d > 0 else 0))
    for vid in b:
        opcoes = saidas(p, s, vid)
        if not opcoes:
            return INF
        L = p.veiculos[p.indice(vid)].comprimento
        total += min(L * abs(k) for k, _ in opcoes) if ponderado else 1
    return total


HEURISTICAS = {"h0": h0, "h1": h1, "h2": h2, "h3": h3, "h4": h4}


# --------------------------------------------------------------------------
# Ferramentas de análise
# --------------------------------------------------------------------------

def espaco_alcancavel(p, limite=None):
    """BFS sobre todos os estados alcançáveis a partir do inicial.
    Devolve (estados, arestas) com arestas[s] = [(s2, custo)]."""
    inicial = p.estado_inicial()
    arestas = {inicial: []}
    fila = deque([inicial])
    while fila:
        s = fila.popleft()
        for a in p.accoes(s):
            s2 = p.resultado(s, a)
            arestas[s].append((s2, p.custo_accao(a)))
            if s2 not in arestas:
                arestas[s2] = []
                fila.append(s2)
                if limite is not None and len(arestas) > limite:
                    raise MemoryError("Espaço de estados maior do que o limite.")
    return list(arestas), arestas


def h_estrela(p, limite=None):
    """Custo óptimo h*(s) para todos os estados alcançáveis, por Dijkstra
    no grafo invertido a partir de todos os estados objectivo (força bruta exacta).
    Estados sem caminho para o objectivo ficam com infinito."""
    estados, arestas = espaco_alcancavel(p, limite)
    inverso = {s: [] for s in estados}
    for s, lista in arestas.items():
        for s2, c in lista:
            inverso[s2].append((s, c))
    dist = {s: INF for s in estados}
    fila = []
    for s in estados:
        if p.e_objectivo(s):
            dist[s] = 0
            fila.append((0, s))
    heapq.heapify(fila)
    while fila:
        d, s = heapq.heappop(fila)
        if d > dist[s]:
            continue
        for anterior, c in inverso[s]:
            if d + c < dist[anterior]:
                dist[anterior] = d + c
                heapq.heappush(fila, (d + c, anterior))
    return dist, arestas


def verificar(p, nome, hstar=None, arestas=None):
    """Verifica admissibilidade em todos os estados alcançáveis e consistência
    em todas as transições. Devolve dicionário com contagens e um contra-exemplo."""
    if hstar is None:
        hstar, arestas = h_estrela(p)
    viol_adm, viol_cons = [], []
    for s, hs in hstar.items():
        h = p.heuristica(s, nome)
        if h > hs:
            viol_adm.append((s, h, hs))
        for s2, c in arestas[s]:
            h2_ = p.heuristica(s2, nome)
            if h > c + h2_:
                viol_cons.append((s, s2, h, c, h2_))
    return {"heuristica": nome, "criterio": p.criterio, "estados": len(hstar),
            "transicoes": sum(len(v) for v in arestas.values()),
            "admissivel": not viol_adm, "violacoes_adm": len(viol_adm),
            "consistente": not viol_cons, "violacoes_cons": len(viol_cons),
            "exemplo_adm": min(viol_adm, key=lambda v: sum(v[0])) if viol_adm else None,
            "exemplo_cons": viol_cons[0] if viol_cons else None}


def b_efectivo(N, d, tol=1e-9):
    """Resolve N + 1 = 1 + b + b^2 + ... + b^d por bissecção (N = nós expandidos/gerados)."""
    if d <= 0 or N <= 0:
        return math.nan
    if N <= d:
        return 1.0 if N == d else math.nan

    def total(b):
        return d + 1 if abs(b - 1) < 1e-12 else (b ** (d + 1) - 1) / (b - 1)

    lo, hi = 1.0, float(N)
    while hi - lo > tol:
        meio = (lo + hi) / 2
        if total(meio) < N + 1:
            lo = meio
        else:
            hi = meio
    return (lo + hi) / 2


def divergencia(p):
    """Compara os dois critérios numa instância (sem depender de desempates):
    devolve (mín. movimentos, menor custo ponderado entre TODAS as soluções de
    mín. movimentos, custo ponderado óptimo, nº de movimentos dessa solução óptima).
    Se o 2.º valor > 3.º, nenhuma solução de mínimo de movimentos é óptima no ponderado."""
    pm, pp = p.com_criterio("movimentos"), p.com_criterio("ponderado")
    dm, arestas = h_estrela(pm)
    dp, arestas_p = h_estrela(pp)
    s0 = p.estado_inicial()
    # menor custo ponderado restringido ao DAG de caminhos mais curtos em movimentos
    memo = {}
    for s in sorted(dm, key=lambda e: dm[e]):
        if dm[s] == INF:
            continue
        if dm[s] == 0:
            memo[s] = 0
            continue
        memo[s] = min(c + memo[s2] for (s2, _), (_, c) in zip(arestas[s], arestas_p[s])
                      if dm[s2] == dm[s] - 1)
    # nº de movimentos da solução ponderada óptima com menos movimentos
    mov_p = {}
    for s in sorted(dp, key=lambda e: dp[e]):
        if dp[s] == INF:
            continue
        mov_p[s] = 0 if dp[s] == 0 else min(
            1 + mov_p[s2] for (s2, c) in arestas_p[s] if dp[s2] + c == dp[s])
    return dm[s0], memo[s0], dp[s0], mov_p[s0]
