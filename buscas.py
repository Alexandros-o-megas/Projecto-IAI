"""Sete estratégias de busca genéricas (mais IDA* simples para comparação).

Os algoritmos usam apenas a interface de `problema.Problema`:
estado_inicial(), accoes(s), resultado(s, a), custo(s, a, s2), e_objectivo(s)
e heuristica(s, nome). Não conhecem veículos nem grelhas.

Convenções de contagem (iguais em todos os algoritmos):
- expandidos: nós cujos sucessores foram gerados;
- gerados: nós criados como sucessores (a raiz conta como 1 gerado);
- fronteira_max: maior tamanho da fronteira (pilha de recursão no caso do
  DFS/IDS/IDA*, isto é, profundidade máxima + 1);
- reexpandidos: expansões de estados que já tinham sido expandidos antes
  (IDS e IDA* entre iterações; A* quando reabre um nó fechado).
"""
import heapq
import itertools
import time
from collections import deque
from dataclasses import dataclass, field

from problema import No, caminho


class TempoEsgotado(Exception):
    pass


@dataclass
class Resultado:
    algoritmo: str
    estado: str = "sem solução"     # ok | sem solução | limite | tempo
    no: No | None = None
    expandidos: int = 0
    gerados: int = 0
    fronteira_max: int = 0
    reexpandidos: int = 0
    iteracoes: int = 0
    extra: dict = field(default_factory=dict)

    @property
    def custo(self):
        return self.no.g if self.no else None

    @property
    def comprimento(self):
        return self.no.profundidade if self.no else None

    def accoes(self):
        return [n.accao for n in caminho(self.no)[1:]] if self.no else []

    def estados(self):
        return [n.estado for n in caminho(self.no)] if self.no else []


class LimiteNos(Exception):
    pass


class _Relogio:
    """Verifica o prazo de 256 em 256 chamadas (perf_counter é barato mas não grátis)
    e, opcionalmente, um orçamento determinístico de nós (usado pelo gerador)."""

    def __init__(self, tempo_max, max_nos=None):
        self.prazo = None if tempo_max is None else time.perf_counter() + tempo_max
        self.max_nos = max_nos
        self.n = 0

    def verificar(self):
        self.n += 1
        if self.max_nos is not None and self.n > self.max_nos:
            raise LimiteNos
        if self.prazo is not None and self.n & 255 == 0 and time.perf_counter() > self.prazo:
            raise TempoEsgotado


def _filho(problema, no, a):
    s2 = problema.resultado(no.estado, a)
    return No(s2, no, a, no.g + problema.custo(no.estado, a, s2), no.profundidade + 1)


def _executar(r, funcao):
    try:
        funcao()
    except TempoEsgotado:
        r.estado, r.no = "tempo", None
    except LimiteNos:
        r.estado, r.no = "limite", None
    return r


# ---------------------------------------------------------------- BFS
def bfs(problema, tempo_max=None, max_nos=None, **_):
    """Busca em largura em grafo, com teste de objectivo na geração.
    Óptima em nº de acções; não é óptima quando os custos variam."""
    r = Resultado("BFS")
    rel = _Relogio(tempo_max, max_nos)

    def correr():
        raiz = No(problema.estado_inicial())
        r.gerados = 1
        if problema.e_objectivo(raiz.estado):
            r.estado, r.no = "ok", raiz
            return
        fronteira = deque([raiz])
        alcancados = {raiz.estado}
        r.fronteira_max = 1
        while fronteira:
            rel.verificar()
            no = fronteira.popleft()
            r.expandidos += 1
            for a in problema.accoes(no.estado):
                filho = _filho(problema, no, a)
                r.gerados += 1
                if filho.estado in alcancados:
                    continue
                if problema.e_objectivo(filho.estado):   # teste na geração
                    r.estado, r.no = "ok", filho
                    return
                alcancados.add(filho.estado)
                fronteira.append(filho)
            r.fronteira_max = max(r.fronteira_max, len(fronteira))
    return _executar(r, correr)


# ---------------------------------------------------------------- DFS / IDS
def _dfs_limitado(problema, limite, r, rel, expandidos_antes=None):
    """DFS recursiva com controlo de ciclos no caminho actual.
    Devolve (nó objectivo | None, cortado?)."""
    no_caminho = set()

    def rec(no):
        rel.verificar()
        if problema.e_objectivo(no.estado):
            return no, False
        if no.profundidade >= limite:
            return None, True
        r.expandidos += 1
        if expandidos_antes is not None:
            if no.estado in expandidos_antes:
                r.reexpandidos += 1
            else:
                expandidos_antes.add(no.estado)
        no_caminho.add(no.estado)
        r.fronteira_max = max(r.fronteira_max, len(no_caminho) + 1)
        cortado = False
        for a in problema.accoes(no.estado):
            filho = _filho(problema, no, a)
            r.gerados += 1
            if filho.estado in no_caminho:     # ciclo no caminho
                continue
            achado, c = rec(filho)
            if achado:
                return achado, False
            cortado = cortado or c
        no_caminho.discard(no.estado)
        return None, cortado

    r.gerados += 1
    return rec(No(problema.estado_inicial()))


def dfs(problema, tempo_max=None, limite=50, max_nos=None, **_):
    """Busca em profundidade com controlo de ciclos no caminho e limite configurável."""
    r = Resultado("DFS")
    rel = _Relogio(tempo_max, max_nos)

    def correr():
        no, cortado = _dfs_limitado(problema, limite, r, rel)
        if no:
            r.estado, r.no = "ok", no
        else:
            r.estado = "limite" if cortado else "sem solução"
        r.extra["limite"] = limite
    return _executar(r, correr)


def ids(problema, tempo_max=None, limite_max=100, max_nos=None, **_):
    """Aprofundamento iterativo; conta os nós re-expandidos entre iterações."""
    r = Resultado("IDS")
    rel = _Relogio(tempo_max, max_nos)
    vistos = set()

    def correr():
        for limite in range(limite_max + 1):
            r.iteracoes += 1
            no, cortado = _dfs_limitado(problema, limite, r, rel, vistos)
            if no:
                r.estado, r.no = "ok", no
                return
            if not cortado:
                r.estado = "sem solução"
                return
        r.estado = "limite"
    return _executar(r, correr)


# ---------------------------------------------------------------- melhor-primeiro
def _melhor_primeiro(problema, nome, prioridade, tempo_max, reabrir, max_nos=None):
    """Busca em grafo com fila de prioridade (heapq).
    Entradas obsoletas (g pior do que o melhor conhecido) são descartadas ao sair."""
    r = Resultado(nome)
    rel = _Relogio(tempo_max, max_nos)

    def correr():
        raiz = No(problema.estado_inicial())
        r.gerados = 1
        desempate = itertools.count()
        fronteira = [(prioridade(raiz), next(desempate), raiz)]
        melhor_g = {raiz.estado: 0}
        fechados = set()
        r.fronteira_max = 1
        while fronteira:
            rel.verificar()
            _, _, no = heapq.heappop(fronteira)
            if no.g > melhor_g[no.estado]:
                continue                                  # entrada obsoleta
            if no.estado in fechados:
                if not reabrir:
                    continue
                r.reexpandidos += 1
            if problema.e_objectivo(no.estado):           # teste na expansão
                r.estado, r.no = "ok", no
                return
            fechados.add(no.estado)
            r.expandidos += 1
            for a in problema.accoes(no.estado):
                filho = _filho(problema, no, a)
                r.gerados += 1
                antigo = melhor_g.get(filho.estado)
                if antigo is not None and (filho.g >= antigo or not reabrir and filho.estado in fechados):
                    continue
                melhor_g[filho.estado] = filho.g
                heapq.heappush(fronteira, (prioridade(filho), next(desempate), filho))
            r.fronteira_max = max(r.fronteira_max, len(fronteira))
    return _executar(r, correr)


def ucs(problema, tempo_max=None, max_nos=None, **_):
    """Custo uniforme: prioridade g(n)."""
    return _melhor_primeiro(problema, "UCS", lambda n: n.g, tempo_max, reabrir=False, max_nos=max_nos)


def gulosa(problema, heuristica="h1", tempo_max=None, max_nos=None, **_):
    """Gulosa pela melhor escolha: prioridade h(n)."""
    def prioridade(n):
        return problema.heuristica(n.estado, heuristica)
    r = _melhor_primeiro(problema, "Gulosa", prioridade, tempo_max, reabrir=False, max_nos=max_nos)
    r.extra["heuristica"] = heuristica
    return r


def astar(problema, heuristica="h1", tempo_max=None, max_nos=None, **_):
    """A* em grafo: prioridade g + h; reabre nós fechados se encontrar g melhor
    (só acontece com heurísticas inconsistentes)."""
    cache = {}

    def prioridade(n):
        h = cache.get(n.estado)
        if h is None:
            h = cache[n.estado] = problema.heuristica(n.estado, heuristica)
        return (n.g + h, -n.g)       # desempate: maior g primeiro
    r = _melhor_primeiro(problema, "A*", prioridade, tempo_max, reabrir=True, max_nos=max_nos)
    r.extra["heuristica"] = heuristica
    return r


# ---------------------------------------------------------------- IDA*
def idastar(problema, heuristica="h1", tempo_max=None, tabela=True, max_iter=10_000, max_nos=None, **_):
    """IDA*: DFS com limite em f = g + h, que sobe para o menor f que o excedeu.

    Com `tabela=True` usa uma tabela de transposição estado -> menor g visto
    na iteração actual (limpa em cada iteração). Um estado reencontrado com
    g >= ao guardado é podado: a subárvore já foi explorada com pelo menos a
    mesma folga (limite - g), logo não pode conter uma solução nova dentro do
    limite. Sem tabela só há controlo de ciclos no caminho actual."""
    r = Resultado("IDA*+TT" if tabela else "IDA*")
    rel = _Relogio(tempo_max, max_nos)
    expandidos_antes = set()
    r.extra.update(heuristica=heuristica, podas_tabela=0)
    INF = float("inf")

    def h(s):
        return problema.heuristica(s, heuristica)

    def correr():
        raiz = No(problema.estado_inicial())
        r.gerados = 1
        limite = h(raiz.estado)
        no_caminho = set()
        tt = {}

        def rec(no, hn):
            rel.verificar()
            f = no.g + hn
            if f > limite:
                return None, f
            if problema.e_objectivo(no.estado):
                return no, f
            if tabela:
                visto = tt.get(no.estado)
                if visto is not None and visto <= no.g:
                    r.extra["podas_tabela"] += 1
                    return None, INF
                tt[no.estado] = no.g
            r.expandidos += 1
            if no.estado in expandidos_antes:
                r.reexpandidos += 1
            else:
                expandidos_antes.add(no.estado)
            no_caminho.add(no.estado)
            r.fronteira_max = max(r.fronteira_max, len(no_caminho) + 1)
            minimo = INF
            sucessores = []
            for a in problema.accoes(no.estado):
                filho = _filho(problema, no, a)
                r.gerados += 1
                if filho.estado in no_caminho:
                    continue
                sucessores.append((filho.g + h(filho.estado), filho))
            sucessores.sort(key=lambda t: t[0])       # ordenar filhos por f
            for fh, filho in sucessores:
                achado, novo = rec(filho, fh - filho.g)
                if achado:
                    return achado, novo
                minimo = min(minimo, novo)
            no_caminho.discard(no.estado)
            return None, minimo

        while r.iteracoes < max_iter:
            r.iteracoes += 1
            tt.clear()
            no_caminho.clear()
            achado, novo = rec(raiz, limite)
            if achado:
                r.estado, r.no = "ok", achado
                return
            if novo == INF:
                r.estado = "sem solução"
                return
            limite = novo
        r.estado = "limite"
    return _executar(r, correr)


def idastar_simples(problema, heuristica="h1", tempo_max=None, **kw):
    return idastar(problema, heuristica, tempo_max, tabela=False, **kw)


ALGORITMOS = {
    "bfs": bfs,
    "dfs": dfs,
    "ids": ids,
    "ucs": ucs,
    "gulosa": gulosa,
    "astar": astar,
    "idastar": idastar,                 # algoritmo avançado: IDA* com tabela de transposição
    "idastar_simples": idastar_simples,
}
INFORMADOS = {"gulosa", "astar", "idastar", "idastar_simples"}


def executar(nome, problema, heuristica=None, **kw):
    funcao = ALGORITMOS[nome]
    if nome in INFORMADOS:
        return funcao(problema, heuristica=heuristica or "h1", **kw)
    return funcao(problema, **kw)
