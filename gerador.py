"""Gerador de instâncias reproduzíveis do P6 (semente do Grupo 06 Laboral: 202606).

Método ("busca para trás a partir de estados objectivo"):
1. sortear uma configuração em que X já está no objectivo (encostado à borda
   direita da linha de saída), com carros (2), camiões (3) e obstáculos fixos
   (carros da polícia, '#');
2. explorar por BFS toda a componente de estados alcançáveis a partir desse
   objectivo (as acções são reversíveis, logo é a mesma componente que leva ao
   objectivo);
3. calcular, por BFS multi-origem a partir de TODOS os objectivos da
   componente, a distância óptima (em nº de movimentos) de cada estado;
4. escolher como estado inicial o estado mais distante; aceitar o puzzle só se
   essa distância (certificada, é exacta) for >= min_mov (15 por omissão).

Níveis: a pequena aceita o estado mais distante que DFS e IDS ainda resolvem
dentro de um orçamento fixo de nós (ver NIVEIS); média e grande exigem óptimo
>= 15 movimentos e distinguem-se pelo tamanho da componente (nº de estados
alcançáveis), que determina se BFS/UCS terminam dentro do limite.
"""
import argparse
import json
import random
from collections import deque
from pathlib import Path

from dominio import RushHour, Veiculo

SEMENTE = 202606
PASTA = Path(__file__).parent / "instancias"

# min_mov: óptimo mínimo exigido (movimentos). Para "pequena" o enunciado exige
# que TODOS os algoritmos terminem; com DFS/IDS de controlo de ciclos só no
# caminho isso é impossível com 15 movimentos (b^d nós; ver relatório, 6.1),
# por isso a pequena aceita o estado mais difícil que DFS e IDS ainda resolvem
# dentro do orçamento ORCAMENTO_NOS (determinístico, independente da máquina).
NIVEIS = {
    "pequena": dict(tamanhos=(5, 6), veiculos=(6, 12), obstaculos=(0, 2), limite=3_000,
                    min_mov=6, min_estados=0, max_estados=3_000),
    "media":   dict(tamanhos=(6, 7), veiculos=(9, 14), obstaculos=(0, 2), limite=40_000,
                    min_mov=15, min_estados=3_000, max_estados=40_000),
    "grande":  dict(tamanhos=(7, 8), veiculos=(10, 22), obstaculos=(0, 3), limite=800_000,
                    min_mov=15, min_estados=250_000, max_estados=800_000, por_indice=True),
}
ORCAMENTO_NOS = 300_000


def configuracao_objectivo(rng, n, n_veiculos, n_obst):
    """Configuração aleatória válida com X na posição objectivo."""
    r = rng.randrange(1, n - 1) if n > 6 else 2
    ocup = {(r, n - 2), (r, n - 1)}
    veiculos = [Veiculo("X", "H", 2, r)]
    posicoes = [n - 2]
    obst = []
    tent = 0
    while len(obst) < n_obst and tent < 200:
        tent += 1
        c = (rng.randrange(n), rng.randrange(n))
        if c in ocup or c[0] == r:          # nunca na linha de saída (puzzle impossível)
            continue
        ocup.add(c)
        obst.append(c)
    letras = iter("ABCDEFGHIJKLMNOPQRSTUVWYZ")
    tent = 0
    while len(veiculos) - 1 < n_veiculos and tent < 500:
        tent += 1
        L = 3 if rng.random() < 0.3 else 2
        ori = rng.choice("HV")
        fixa = rng.randrange(n)
        if ori == "H" and fixa == r:        # horizontal na linha de X: só à esquerda, inútil
            continue
        pos = rng.randrange(n - L + 1)
        casas = [(fixa, pos + k) if ori == "H" else (pos + k, fixa) for k in range(L)]
        if any(c in ocup for c in casas):
            continue
        ocup.update(casas)
        veiculos.append(Veiculo(next(letras), ori, L, fixa))
        posicoes.append(pos)
    return RushHour(n, veiculos, posicoes, obst, r)


def distancias(p, limite):
    """Componente do estado inicial de p (que é um objectivo) e distância em
    movimentos de cada estado ao objectivo mais próximo. None se exceder limite.
    Duas passagens (sem guardar listas de vizinhos) para poupar memória."""
    # 1) enumerar a componente (accoes_todas: também se sai dos objectivos)
    componente = {p.estado_inicial()}
    fila = deque(componente)
    while fila:
        s = fila.popleft()
        for a in p.accoes_todas(s):
            s2 = p.aplicar(s, a)
            if s2 not in componente:
                componente.add(s2)
                fila.append(s2)
                if len(componente) > limite:
                    return None
    # 2) BFS multi-origem a partir de todos os objectivos da componente
    dist = {s: 0 for s in componente if p.e_objectivo(s)}
    del componente
    fila = deque(dist)
    while fila:
        s = fila.popleft()
        for a in p.accoes_todas(s):
            s2 = p.aplicar(s, a)
            if s2 not in dist:
                dist[s2] = dist[s] + 1
                fila.append(s2)
    return dist


def certificar(p, criterio="movimentos", tempo_max=120):
    """Custo óptimo exacto por A* com h3/h4 (admissíveis)."""
    from buscas import astar
    q = p.com_criterio(criterio)
    r = astar(q, "h3" if criterio == "movimentos" else "h4", tempo_max=tempo_max)
    return (r.custo if r.estado == "ok" else None), r


def _resolvem_todos(q):
    """DFS e IDS (os mais frágeis) terminam dentro do orçamento de nós?"""
    from buscas import dfs, ids
    return all(f(q, max_nos=ORCAMENTO_NOS).estado == "ok" for f in (dfs, ids))


def _escolher_exacto(rng, p, cfg, nivel):
    dist = distancias(p, cfg["limite"])
    if not dist or not cfg["min_estados"] <= len(dist) <= cfg["max_estados"]:
        return None
    novo = lambda s: RushHour(p.tamanho, p.veiculos, s, sorted(p.obstaculos), p.linha_saida)
    por_d = {}
    for s, d in dist.items():
        por_d.setdefault(d, []).append(s)
    for d in sorted(por_d, reverse=True):
        if d < cfg["min_mov"]:
            return None
        candidatos = sorted(por_d[d])
        if nivel != "pequena":
            return novo(rng.choice(candidatos)), d, len(dist)
        for s in rng.sample(candidatos, min(3, len(candidatos))):
            q = novo(s)
            if _resolvem_todos(q):
                return q, d, len(dist)
    return None


def _procurar(rng, cfg, nivel, vistos, verbose, rotulo):
    tentativas = 0
    while True:
        tentativas += 1
        n = rng.choice(cfg["tamanhos"])
        p = configuracao_objectivo(rng, n, rng.randint(*cfg["veiculos"]), rng.randint(*cfg["obstaculos"]))
        escolha = _escolher_exacto(rng, p, cfg, nivel)
        if escolha is None:
            continue
        q, d, n_estados = escolha
        chave = (q.tamanho, q.veiculos, q.estado_inicial(), q.obstaculos)
        if chave in vistos:
            continue
        vistos.add(chave)
        if verbose:
            print(f"{nivel} #{rotulo}: {q.tamanho}x{q.tamanho}, {len(q.veiculos)} veículos, "
                  f"{len(q.obstaculos)} obstáculos, óptimo {d} mov., componente {n_estados} estados "
                  f"(tentativa {tentativas})", flush=True)
        return q, d, n_estados


def gerar(nivel, quantidade, semente=SEMENTE, min_mov=None, verbose=False, indices=None):
    """Gera `quantidade` puzzles. Nos níveis com por_indice=True (grande), a
    instância i usa a sua própria sequência Random("<semente>-<nível>-<i>"),
    o que permite gerar índices em paralelo sem perder a reprodutibilidade."""
    cfg = dict(NIVEIS[nivel])
    if min_mov is not None:
        cfg["min_mov"] = min_mov
    vistos = set()
    if cfg.get("por_indice"):
        indices = indices or range(1, quantidade + 1)
        return [_procurar(random.Random(f"{semente}-{nivel}-{i}"), cfg, nivel, vistos, verbose, i)
                for i in indices]
    rng = random.Random(f"{semente}-{nivel}")
    return [_procurar(rng, cfg, nivel, vistos, verbose, k + 1) for k in range(quantidade)]


def gravar(nivel, puzzles, semente=SEMENTE, pasta=PASTA, indices=None):
    pasta.mkdir(exist_ok=True)
    caminhos = []
    for i, (q, d, n_estados) in zip(indices or range(1, len(puzzles) + 1), puzzles):
        f = pasta / f"{nivel}_{i:02d}.json"
        meta = {"nivel": nivel, "semente": semente, "optimo_movimentos": d,
                "estados_componente": n_estados}
        f.write_text(json.dumps(q.para_dict(meta=meta), ensure_ascii=False, indent=1), encoding="utf-8")
        caminhos.append(f)
    return caminhos


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--nivel", default="todos", choices=["todos", *NIVEIS])
    ap.add_argument("--quantidade", type=int, default=10)
    ap.add_argument("--semente", type=int, default=SEMENTE)
    ap.add_argument("--min-mov", type=int, default=None, help="sobrepõe o mínimo do nível")
    ap.add_argument("--indices", type=int, nargs="*", help="só estes índices (níveis por índice, p.ex. grande)")
    a = ap.parse_args()
    for nivel in (NIVEIS if a.nivel == "todos" else [a.nivel]):
        indices = a.indices if NIVEIS[nivel].get("por_indice") else None
        puzzles = gerar(nivel, a.quantidade, a.semente, a.min_mov, verbose=True, indices=indices)
        gravar(nivel, puzzles, a.semente, indices=indices)


if __name__ == "__main__":
    main()
