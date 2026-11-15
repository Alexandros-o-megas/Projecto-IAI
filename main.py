"""Menu do P6 — Engarrafamento na Baixa (Rush Hour generalizado), Grupo 06.

Modo interactivo:   python main.py
Modo directo:       python main.py --instancia base --alg astar --h h4 --criterio ponderado
                    python main.py --instancia instancias/media_03.json --alg idastar --h h4
                    python main.py --gerar grande --semente 202606 --alg astar --h h3
"""
import argparse
import sys
from pathlib import Path

from buscas import ALGORITMOS, INFORMADOS, executar
from dominio import RushHour, carregar_base

RAIZ = Path(__file__).parent
NOMES = {
    "bfs": "Busca em Largura (BFS)",
    "dfs": "Busca em Profundidade (DFS)",
    "ids": "Aprofundamento Iterativo (IDS)",
    "ucs": "Custo Uniforme (UCS)",
    "gulosa": "Gulosa pela melhor escolha",
    "astar": "A*",
    "idastar": "IDA* com tabela de transposição (algoritmo avançado)",
    "idastar_simples": "IDA* simples (sem tabela)",
}
HEURS = {"h0": "zero", "h1": "veículos a bloquear X", "h2": "h1 + bloqueadores dos bloqueadores",
         "h3": "h1 + movimento final de X", "h4": "relaxação: cada veículo sozinho (custo mínimo)"}


def carregar(instancia, criterio):
    if instancia in (None, "", "base"):
        return carregar_base(criterio)
    return RushHour.de_json(instancia, criterio)


def gerar(nivel, semente, criterio):
    from gerador import gerar as gerar_puzzles
    print(f"A gerar uma instância '{nivel}' com semente {semente}…")
    q, d, _ = gerar_puzzles(nivel, 1, semente)[0]
    print(f"Óptimo certificado: {d} movimentos.")
    return q.com_criterio(criterio)


# ---------------------------------------------------------------- cores (ANSI)
COR = {"ativo": sys.stdout.isatty()}
PALETA = [31, 32, 33, 34, 35, 36, 91, 92, 93, 94, 95, 96]


def c(texto, codigo):
    return f"\033[{codigo}m{texto}\033[0m" if COR["ativo"] else texto


def desenhar_cor(p, s, movido=None):
    """Tabuleiro com cores: X a vermelho e fundo, veículo movido em destaque,
    camiões em negrito, obstáculos (#) a cinzento, saída assinalada."""
    if not COR["ativo"]:
        return p.desenhar(s)
    cores = {}
    outros = [v.id for v in p.veiculos if v.id != "X"]
    for i, vid in enumerate(outros):
        cores[vid] = str(PALETA[i % len(PALETA)])
    linhas = []
    for r, linha in enumerate(p.grelha(s)):
        casas = []
        for x in linha:
            if x == ".":
                casas.append(c("·", "2"))
            elif x == "#":
                casas.append(c("#", "90;1"))
            elif x == "X":
                casas.append(c("X", "97;41;1"))
            elif x == movido:
                casas.append(c(x, "30;43;1"))      # destaque amarelo: veículo que acabou de mexer
            else:
                L = p.veiculos[p.indice(x)].comprimento
                casas.append(c(x, cores[x] + (";1" if L == 3 else "")))
        texto = " ".join(casas)
        if r == p.linha_saida:
            texto += c("  ⟶ saída", "92;1")
        linhas.append(texto)
    return "\n".join(linhas)


def mostrar(p, r, passo_a_passo=True, pausa=0.0, limpar=False):
    import time
    print(c(f"\n=== {NOMES.get(r.algoritmo, r.algoritmo)} "
            f"{'(' + r.extra['heuristica'] + ')' if 'heuristica' in r.extra else ''} — critério {p.criterio} ===",
            "1;36"))
    if r.estado != "ok":
        print(c(f"Sem solução: {r.estado}", "1;31"))
    else:
        estados, accoes = r.estados(), r.accoes()
        if passo_a_passo:
            sentido = {("H", 1): "direita →", ("H", -1): "esquerda ←", ("V", 1): "baixo ↓", ("V", -1): "cima ↑"}
            total = 0
            if limpar and COR["ativo"]:
                print("\033[2J\033[H", end="")
            print(c("\nEstado inicial:", "1"))
            print(desenhar_cor(p, estados[0]))
            for i, (a, s) in enumerate(zip(accoes, estados[1:]), 1):
                if pausa:
                    time.sleep(pausa)
                if limpar and COR["ativo"]:
                    print("\033[2J\033[H", end="")
                v = p.veiculos[p.indice(a.veiculo)]
                total += p.custo_accao(a)
                print(f"\n{c(f'Passo {i}/{len(accoes)}', '1')}: mover {c(a.veiculo, '30;43;1')} "
                      f"{abs(a.deslocamento)} casa(s) para {sentido[(v.orientacao, 1 if a.deslocamento > 0 else -1)]} "
                      f"(custo {p.custo_accao(a)}, acumulado {total})")
                print(desenhar_cor(p, s, a.veiculo))
            if p.e_objectivo(estados[-1]):
                print(c("\nO chapa X chegou à saída!", "1;32"))
        print(c("\nSolução:", "1"), " ".join(f"{a.veiculo}{a.deslocamento:+d}" for a in accoes))
    print("\nMétricas:")
    for nome, valor in [("estado", r.estado), ("custo da solução", r.custo),
                        ("comprimento (movimentos)", r.comprimento), ("nós expandidos", r.expandidos),
                        ("nós gerados", r.gerados), ("fronteira máxima", r.fronteira_max),
                        ("nós re-expandidos", r.reexpandidos), ("iterações", r.iteracoes or "—"),
                        ("tempo (s)", f"{r.extra.get('tempo', 0):.4f}"),
                        ("memória de pico (MB)", f"{r.extra.get('memoria', 0):.3f}")]:
        print(f"  {nome:26s} {valor}")
    if "podas_tabela" in r.extra and r.algoritmo == "IDA*+TT":
        print(f"  {'podas pela tabela':26s} {r.extra['podas_tabela']}")


def resolver(p, alg, heur, tempo, limite_dfs, passo_a_passo=True, pausa=0.0, limpar=False):
    import time
    import tracemalloc
    sys.setrecursionlimit(20000)
    tracemalloc.start()
    t0 = time.perf_counter()
    r = executar(alg, p, heur, tempo_max=tempo, limite=limite_dfs)
    r.extra["tempo"] = time.perf_counter() - t0
    r.extra["memoria"] = tracemalloc.get_traced_memory()[1] / 2 ** 20
    tracemalloc.stop()
    mostrar(p, r, passo_a_passo, pausa, limpar)
    return r


def escolher(titulo, opcoes, omissao):
    print(f"\n{titulo}")
    chaves = list(opcoes)
    for i, k in enumerate(chaves, 1):
        print(f"  {i}. {k} — {opcoes[k]}")
    x = input(f"Escolha [{chaves.index(omissao) + 1}]: ").strip()
    if not x:
        return omissao
    if x.isdigit() and 1 <= int(x) <= len(chaves):
        return chaves[int(x) - 1]
    return x if x in opcoes else omissao


def menu():
    print("P6 — Engarrafamento na Baixa (Rush Hour generalizado) — Grupo 06")
    criterio = "movimentos"
    p = carregar_base(criterio)
    while True:
        print(c("\nInstância actual:", "1"))
        print(desenhar_cor(p, p.estado_inicial()))
        print(f"Critério: {p.criterio}")
        op = escolher("Menu", {"resolver": "escolher algoritmo, heurística e limites e resolver",
                               "ficheiro": "carregar instância de ficheiro JSON",
                               "gerar": "gerar instância (semente e nível)",
                               "base": "voltar à instância base",
                               "criterio": "mudar critério (movimentos / ponderado)",
                               "sair": "terminar"}, "resolver")
        try:
            if op == "sair":
                return
            if op == "ficheiro":
                lista = sorted((RAIZ / "instancias").glob("*.json"))
                for i, f in enumerate(lista, 1):
                    print(f"  {i}. {f.name}")
                x = input("Número ou caminho: ").strip()
                f = lista[int(x) - 1] if x.isdigit() else Path(x)
                p = RushHour.de_json(f, p.criterio)
            elif op == "gerar":
                nivel = escolher("Nível", {"pequena": "", "media": "", "grande": ""}, "pequena")
                semente = int(input("Semente [202606]: ").strip() or 202606)
                p = gerar(nivel, semente, p.criterio)
            elif op == "base":
                p = carregar_base(p.criterio)
            elif op == "criterio":
                p = p.com_criterio("ponderado" if p.criterio == "movimentos" else "movimentos")
            elif op == "resolver":
                alg = escolher("Algoritmo", NOMES, "astar")
                heur = escolher("Heurística", HEURS, "h4") if alg in INFORMADOS else None
                tempo = float(input("Limite de tempo em segundos [60]: ").strip() or 60)
                limite = 50
                if alg == "dfs":
                    limite = int(input("Limite de profundidade do DFS [50]: ").strip() or 50)
                passo = input("Mostrar passo a passo? [S/n]: ").strip().lower() != "n"
                pausa = float(input("Pausa entre passos em segundos [1]: ").strip() or 1) if passo else 0
                resolver(p, alg, heur, tempo, limite, passo, pausa, limpar=pausa > 0)
        except (ValueError, OSError, IndexError, KeyError) as e:
            print("Erro:", e)


def main():
    ap = argparse.ArgumentParser(description="P6 — Rush Hour generalizado (Grupo 06)")
    ap.add_argument("--instancia", help="'base' ou caminho para JSON")
    ap.add_argument("--gerar", choices=["pequena", "media", "grande"])
    ap.add_argument("--semente", type=int, default=202606)
    ap.add_argument("--alg", choices=list(ALGORITMOS))
    ap.add_argument("--h", default="h4", choices=list(HEURS))
    ap.add_argument("--criterio", default="movimentos", choices=["movimentos", "ponderado"])
    ap.add_argument("--tempo", type=float, default=60)
    ap.add_argument("--limite-dfs", type=int, default=50)
    ap.add_argument("--sem-passos", action="store_true", help="mostrar só a solução e as métricas")
    ap.add_argument("--pausa", type=float, default=0.0,
                    help="segundos entre passos (animação), p.ex. --pausa 1")
    ap.add_argument("--animar", action="store_true", help="limpar o ecrã a cada passo (usar com --pausa)")
    ap.add_argument("--sem-cor", action="store_true", help="desligar as cores ANSI")
    a = ap.parse_args()
    if a.sem_cor:
        COR["ativo"] = False
    if a.alg is None:
        menu()
        return
    p = gerar(a.gerar, a.semente, a.criterio) if a.gerar else carregar(a.instancia, a.criterio)
    resolver(p, a.alg, a.h if a.alg in INFORMADOS else None, a.tempo, a.limite_dfs, not a.sem_passos,
             a.pausa, a.animar)


if __name__ == "__main__":
    main()
