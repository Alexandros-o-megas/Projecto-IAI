"""TUI (Text-based User Interface) com ANSI Art para o P6 — Engarrafamento na Baixa.

Lança a interface gráfica em terminal:
    python tui.py

Modos directos (passados ao motor existente em main.py):
    python tui.py --instancia base --alg astar --h h4
    python tui.py --gerar media --semente 202606 --alg idastar --h h4

A TUI é uma camada puramente visual sobre os módulos originais (dominio, buscas,
heuristicas, gerador, main) — não altera nenhum desses ficheiros.
"""
import os
import sys
import time
import threading
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# Compatibilidade Windows – activa cores ANSI no terminal do Windows
# ──────────────────────────────────────────────────────────────────────────────
if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    os.system("")   # força o modo ANSI no conhost/Windows Terminal

# ──────────────────────────────────────────────────────────────────────────────
# Paleta ANSI
# ──────────────────────────────────────────────────────────────────────────────
R  = "\033[0m"          # reset
BOLD = "\033[1m"
DIM  = "\033[2m"

# Cores de texto
BLACK   = "\033[30m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[37m"
GRAY    = "\033[90m"

# Cores claras
LRED    = "\033[91m"
LGREEN  = "\033[92m"
LYELLOW = "\033[93m"
LBLUE   = "\033[94m"
LMAG    = "\033[95m"
LCYAN   = "\033[96m"
LWHITE  = "\033[97m"

# Fundos
BG_BLACK  = "\033[40m"
BG_RED    = "\033[41m"
BG_GREEN  = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE   = "\033[44m"
BG_MAG    = "\033[45m"
BG_CYAN   = "\033[46m"
BG_WHITE  = "\033[47m"
BG_GRAY   = "\033[100m"

# Paleta de veículos (cicla sobre estes)
PALETA_VEI = [
    "\033[32m",   # verde
    "\033[34m",   # azul
    "\033[35m",   # magenta
    "\033[36m",   # ciano
    "\033[91m",   # vermelho claro
    "\033[92m",   # verde claro
    "\033[93m",   # amarelo claro
    "\033[94m",   # azul claro
    "\033[95m",   # magenta claro
    "\033[96m",   # ciano claro
    "\033[33m",   # amarelo
    "\033[32;1m", # verde bold
]

LIMPAR = "\033[2J\033[H"

# ──────────────────────────────────────────────────────────────────────────────
# Arte ANSI — cabeçalho do programa
# ──────────────────────────────────────────────────────────────────────────────
LOGO = f"""{CYAN}{BOLD}
  ██████╗ ██╗   ██╗███████╗██╗  ██╗    ██╗  ██╗ ██████╗ ██╗   ██╗██████╗
  ██╔══██╗██║   ██║██╔════╝██║  ██║    ██║  ██║██╔═══██╗██║   ██║██╔══██╗
  ██████╔╝██║   ██║███████╗███████║    ███████║██║   ██║██║   ██║██████╔╝
  ██╔══██╗██║   ██║╚════██║██╔══██║    ██╔══██║██║   ██║██║   ██║██╔══██╗
  ██║  ██║╚██████╔╝███████║██║  ██║    ██║  ██║╚██████╔╝╚██████╔╝██║  ██║
  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝{R}
{YELLOW}  ╔══════════════════════════════════════════════════════════════════════╗
  ║   {LWHITE}P6 — Engarrafamento na Baixa  ·  Rush Hour Generalizado{YELLOW}            ║
  ║   {GRAY}Inteligência Artificial e Introdução — Grupo 06{YELLOW}                      ║
  ╚══════════════════════════════════════════════════════════════════════╝{R}
"""

SEPARADOR = f"{CYAN}  {'═' * 70}{R}"

# ──────────────────────────────────────────────────────────────────────────────
# Utilitários de terminal
# ──────────────────────────────────────────────────────────────────────────────

def cls():
    print(LIMPAR, end="")


def linha(texto="", cor=""):
    print(f"  {cor}{texto}{R}")


def cabecalho(titulo):
    print()
    print(SEPARADOR)
    print(f"  {CYAN}{BOLD}  {titulo}{R}")
    print(SEPARADOR)
    print()


def pausa(msg="Pressione Enter para continuar…"):
    input(f"\n  {DIM}{msg}{R}")


def erro(msg):
    print(f"\n  {LRED}{BOLD}✖  Erro: {R}{LRED}{msg}{R}\n")


def sucesso(msg):
    print(f"\n  {LGREEN}{BOLD}✔  {msg}{R}\n")


def info(msg):
    print(f"  {LCYAN}ℹ  {msg}{R}")


def aviso(msg):
    print(f"  {LYELLOW}⚠  {msg}{R}")


# ──────────────────────────────────────────────────────────────────────────────
# Spinner de espera animado
# ──────────────────────────────────────────────────────────────────────────────

class Spinner:
    _FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, msg="A calcular"):
        self._msg = msg
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        i = 0
        while not self._stop.is_set():
            frame = self._FRAMES[i % len(self._FRAMES)]
            print(f"\r  {CYAN}{frame}{R}  {self._msg}…", end="", flush=True)
            time.sleep(0.1)
            i += 1

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *_):
        self._stop.set()
        self._thread.join()
        print("\r" + " " * 60 + "\r", end="", flush=True)


# ──────────────────────────────────────────────────────────────────────────────
# Renderização do tabuleiro com ANSI Art
# ──────────────────────────────────────────────────────────────────────────────

def _mapa_cores(p):
    """Devolve {id_veiculo: codigo_cor_ansi}."""
    cores = {}
    outros = [v.id for v in p.veiculos if v.id != "X"]
    for i, vid in enumerate(outros):
        cores[vid] = PALETA_VEI[i % len(PALETA_VEI)]
    return cores


def desenhar_tabuleiro(p, s, movido=None, titulo=None, mostrar_legenda=True):
    """Devolve string com o tabuleiro ANSI Art completo (bordas, cores, legenda)."""
    cores = _mapa_cores(p)
    grelha = p.grelha(s)
    n = p.tamanho

    # ── largura interna: cada célula ocupa 2 chars + separadores
    cel_w = 2
    largura = n * (cel_w + 1) + 1       # ex: 6×3 + 1 = 19

    linhas_out = []

    # título opcional
    if titulo:
        linhas_out.append(f"  {BOLD}{LCYAN}{titulo}{R}")
        linhas_out.append("")

    # borda superior
    topo = f"  {CYAN}╔{'═' * (largura)}╗{R}"
    linhas_out.append(topo)

    for r, linha_grelha in enumerate(grelha):
        partes = [f"  {CYAN}║{R}"]
        for x in linha_grelha:
            if x == ".":
                celula = f"{DIM}··{R}"
            elif x == "#":
                celula = f"{BG_GRAY}{BOLD} # {R}"[:-len(R)] + f"{R}"
                celula = f"{GRAY}{BOLD} #{R}"
            elif x == "X":
                celula = f"{BG_RED}{LWHITE}{BOLD}XX{R}"
            elif x == movido:
                celula = f"{BG_YELLOW}{BLACK}{BOLD}{x}{x}{R}"
            else:
                L = p.veiculos[p.indice(x)].comprimento
                cor = cores[x]
                b = BOLD if L == 3 else ""
                celula = f"{cor}{b}{x}{x}{R}"
            partes.append(f" {celula}")
        partes.append(f" {CYAN}║{R}")

        # marcador de saída
        saida = ""
        if r == p.linha_saida:
            saida = f"  {LGREEN}{BOLD}⟶ saída{R}"

        linhas_out.append("".join(partes) + saida)

        # separador entre linhas (excepto a última)
        if r < n - 1:
            sep = f"  {CYAN}╠{'═' * (largura)}╣{R}"
            # separadores mais suaves entre linhas intermédias
            sep = f"  {CYAN}║{GRAY}{'─' * largura}{CYAN}║{R}"
            linhas_out.append(sep)

    # borda inferior
    base = f"  {CYAN}╚{'═' * (largura)}╝{R}"
    linhas_out.append(base)

    # legenda de veículos
    if mostrar_legenda:
        linhas_out.append("")
        legenda = []
        for vid, cor in cores.items():
            L = p.veiculos[p.indice(vid)].comprimento
            b = BOLD if L == 3 else ""
            tag = "camião" if L == 3 else "carro "
            legenda.append(f"{cor}{b}{vid}{R}={tag}")
        # X em destaque
        legenda_x = f"{BG_RED}{LWHITE}{BOLD}X{R}=alvo "
        linhas_out.append("  " + legenda_x + "  ".join(legenda))

    return "\n".join(linhas_out)


# ──────────────────────────────────────────────────────────────────────────────
# Exibição de resultado passo a passo (TUI)
# ──────────────────────────────────────────────────────────────────────────────

def mostrar_resultado(p, r, passo_a_passo=True, pausa_seg=0.0, animar=False):
    from main import NOMES
    heur_str = f"({r.extra['heuristica']})" if "heuristica" in r.extra else ""
    alg_nome = NOMES.get(r.algoritmo, r.algoritmo)

    cabecalho(f"{alg_nome} {heur_str}  —  critério: {p.criterio}")

    if r.estado != "ok":
        aviso(f"Sem solução: {LRED}{r.estado}{R}")
    else:
        estados, accoes = r.estados(), r.accoes()
        sentido = {
            ("H",  1): f"{LGREEN}direita →{R}",
            ("H", -1): f"{LYELLOW}esquerda ←{R}",
            ("V",  1): f"{LRED}baixo ↓{R}",
            ("V", -1): f"{LCYAN}cima ↑{R}",
        }
        total = 0

        if passo_a_passo:
            # estado inicial
            if animar:
                cls()
            print(desenhar_tabuleiro(p, estados[0], titulo="Estado inicial"))
            print()

            for i, (a, s) in enumerate(zip(accoes, estados[1:]), 1):
                if pausa_seg:
                    time.sleep(pausa_seg)
                if animar:
                    cls()
                v = p.veiculos[p.indice(a.veiculo)]
                total += p.custo_accao(a)
                dir_str = sentido[(v.orientacao, 1 if a.deslocamento > 0 else -1)]
                cores = _mapa_cores(p)
                cor_v = cores.get(a.veiculo, LWHITE)
                L = v.comprimento
                b = BOLD if L == 3 else ""

                titulo_passo = (
                    f"Passo {BOLD}{i}/{len(accoes)}{R}  ·  "
                    f"mover {cor_v}{b}{a.veiculo}{R} "
                    f"{abs(a.deslocamento)} casa(s) para {dir_str}  "
                    f"{DIM}(custo {p.custo_accao(a)}, acumulado {total}){R}"
                )
                print(desenhar_tabuleiro(p, s, movido=a.veiculo, titulo=titulo_passo))
                print()

            if p.e_objectivo(estados[-1]):
                print(f"  {LGREEN}{BOLD}★  O chapa X chegou à saída! Puzzle resolvido!  ★{R}")

        # linha de solução compacta
        seq = " ".join(
            f"{BOLD}{a.veiculo}{R}{GRAY}{a.deslocamento:+d}{R}" for a in accoes
        )
        print(f"\n  {LCYAN}{BOLD}Solução:{R}  {seq}\n")

    # ── métricas
    _mostrar_metricas(r)


def _mostrar_metricas(r):
    """Tabela de métricas formatada com bordas ANSI."""
    cabecalho("Métricas de desempenho")
    campos = [
        ("Estado",              r.estado),
        ("Custo da solução",    r.custo),
        ("Comprimento (movimentos)", r.comprimento),
        ("Nós expandidos",      r.expandidos),
        ("Nós gerados",         r.gerados),
        ("Fronteira máxima",    r.fronteira_max),
        ("Nós re-expandidos",   r.reexpandidos),
        ("Iterações",           r.iteracoes or "—"),
        ("Tempo (s)",           f"{r.extra.get('tempo', 0):.4f}"),
        ("Memória de pico (MB)", f"{r.extra.get('memoria', 0):.3f}"),
    ]
    if "podas_tabela" in r.extra and "TT" in r.algoritmo:
        campos.append(("Podas pela tabela", r.extra["podas_tabela"]))

    col1 = 32
    print(f"  {CYAN}╔{'═' * col1}╦{'═' * 20}╗{R}")
    print(f"  {CYAN}║{BOLD}{'Campo':^{col1}}{R}{CYAN}║{BOLD}{'Valor':^20}{R}{CYAN}║{R}")
    print(f"  {CYAN}╠{'═' * col1}╬{'═' * 20}╣{R}")
    for nome, valor in campos:
        cor_v = LGREEN if r.estado == "ok" and nome == "Estado" else LWHITE
        print(f"  {CYAN}║{R} {LCYAN}{nome:<{col1-1}}{R}{CYAN}║{R} {cor_v}{str(valor):<19}{R}{CYAN}║{R}")
    print(f"  {CYAN}╚{'═' * col1}╩{'═' * 20}╝{R}")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Menus TUI
# ──────────────────────────────────────────────────────────────────────────────

def _menu_escolher(titulo, opcoes: dict, omissao: str):
    """Menu numerado com destaque ANSI. Devolve a chave escolhida."""
    print(f"\n  {BOLD}{LCYAN}{titulo}{R}")
    print(f"  {CYAN}{'─' * 60}{R}")
    chaves = list(opcoes)
    for i, k in enumerate(chaves, 1):
        marcador = f"{LGREEN}▶{R}" if k == omissao else f"{GRAY}·{R}"
        idx_cor = LGREEN if k == omissao else LCYAN
        desc = opcoes[k]
        print(f"  {marcador} {idx_cor}{i:>2}.{R} {BOLD}{k:<18}{R} {DIM}{desc}{R}")
    print(f"  {CYAN}{'─' * 60}{R}")
    omissao_num = chaves.index(omissao) + 1
    try:
        raw = input(f"  {LYELLOW}Escolha [{omissao_num}]:{R} ").strip()
    except (EOFError, KeyboardInterrupt):
        return omissao
    if not raw:
        return omissao
    if raw.isdigit() and 1 <= int(raw) <= len(chaves):
        return chaves[int(raw) - 1]
    return raw if raw in opcoes else omissao


def _menu_ficheiros(raiz):
    """Lista JSON em instancias/ e deixa o utilizador escolher."""
    lista = sorted((raiz / "instancias").glob("*.json"))
    print(f"\n  {LCYAN}Instâncias disponíveis:{R}")
    print(f"  {CYAN}{'─' * 50}{R}")
    for i, f in enumerate(lista, 1):
        print(f"  {GRAY}{i:>3}.{R}  {LWHITE}{f.name}{R}")
    print(f"  {CYAN}{'─' * 50}{R}")
    try:
        raw = input(f"  {LYELLOW}Número ou caminho:{R} ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    if not raw:
        return None
    try:
        return lista[int(raw) - 1] if raw.isdigit() else Path(raw)
    except (IndexError, ValueError):
        return None


def _pedir(prompt, omissao, tipo=str):
    try:
        raw = input(f"  {LYELLOW}{prompt} [{omissao}]:{R} ").strip()
    except (EOFError, KeyboardInterrupt):
        return omissao
    if not raw:
        return tipo(omissao)
    try:
        return tipo(raw)
    except ValueError:
        return omissao


# ──────────────────────────────────────────────────────────────────────────────
# Ecrã de boas-vindas e estado actual
# ──────────────────────────────────────────────────────────────────────────────

def _ecrã_principal(p):
    cls()
    print(LOGO)
    print(f"  {BOLD}Instância actual:{R}  "
          f"{LCYAN}{p.tamanho}×{p.tamanho}{R}  "
          f"{DIM}·{R}  {len(p.veiculos)} veículos  "
          f"{DIM}·{R}  critério: {LYELLOW}{p.criterio}{R}\n")
    print(desenhar_tabuleiro(p, p.estado_inicial()))
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Menu principal
# ──────────────────────────────────────────────────────────────────────────────

NOMES_ALG = {
    "bfs":           "Busca em Largura (BFS)",
    "dfs":           "Busca em Profundidade (DFS)",
    "ids":           "Aprofundamento Iterativo (IDS)",
    "ucs":           "Custo Uniforme (UCS)",
    "gulosa":        "Gulosa pela melhor escolha",
    "astar":         "A*",
    "idastar":       "IDA* com tabela de transposição (avançado)",
    "idastar_simples": "IDA* simples (sem tabela)",
}
HEURS = {
    "h0": "zero — equivalente a UCS",
    "h1": "nº de veículos à frente de X",
    "h2": "h1 + bloqueadores dos bloqueadores (NÃO admissível)",
    "h3": "h1 + movimento final de X",
    "h4": "relaxação: cada veículo sozinho (custo mínimo)",
}


def menu_tui():
    from buscas import ALGORITMOS, INFORMADOS, executar
    from dominio import RushHour, carregar_base

    RAIZ = Path(__file__).parent
    criterio = "movimentos"
    p = carregar_base(criterio)

    while True:
        _ecrã_principal(p)

        op = _menu_escolher(
            "Menu principal",
            {
                "resolver": "escolher algoritmo, heurística e resolver",
                "ficheiro": "carregar instância de ficheiro JSON",
                "gerar":    "gerar instância aleatória (nível + semente)",
                "base":     "voltar à instância base do projecto",
                "criterio": "alternar critério  movimentos ↔ ponderado",
                "sair":     "terminar o programa",
            },
            "resolver",
        )

        try:
            if op == "sair":
                cls()
                print(f"\n{LOGO}")
                linha("Até à próxima! 👋", LCYAN + BOLD)
                print()
                return

            elif op == "ficheiro":
                f = _menu_ficheiros(RAIZ)
                if f is None:
                    aviso("Nenhuma instância seleccionada.")
                    pausa()
                else:
                    try:
                        p = RushHour.de_json(f, p.criterio)
                        sucesso(f"Carregada: {f.name}")
                        pausa()
                    except (OSError, ValueError, KeyError) as e:
                        erro(str(e))
                        pausa()

            elif op == "gerar":
                from gerador import gerar as gerar_puzzles
                nivel = _menu_escolher(
                    "Nível de dificuldade",
                    {"pequena": "tabuleiro 5-6×, óptimo ≥ 6 movimentos",
                     "media":   "tabuleiro 6-7×, óptimo ≥ 15 movimentos",
                     "grande":  "tabuleiro 7-8×, óptimo ≥ 15 movimentos"},
                    "pequena",
                )
                semente = _pedir("Semente", 202606, int)
                with Spinner(f"A gerar puzzle '{nivel}'"):
                    q, d, _ = gerar_puzzles(nivel, 1, semente)[0]
                p = q.com_criterio(p.criterio)
                sucesso(f"Puzzle '{nivel}' gerado  —  óptimo certificado: {BOLD}{d}{R}{LGREEN} movimentos")
                pausa()

            elif op == "base":
                p = carregar_base(p.criterio)
                sucesso("Instância base carregada.")
                pausa()

            elif op == "criterio":
                novo = "ponderado" if p.criterio == "movimentos" else "movimentos"
                p = p.com_criterio(novo)
                sucesso(f"Critério alterado para: {BOLD}{novo}{R}")
                pausa()

            elif op == "resolver":
                # ── escolha do algoritmo
                alg = _menu_escolher("Algoritmo de busca", NOMES_ALG, "astar")

                # ── heurística (só para algoritmos informados)
                heur = None
                if alg in INFORMADOS:
                    heur = _menu_escolher("Heurística", HEURS, "h4")

                # ── parâmetros
                tempo  = _pedir("Limite de tempo (segundos)", 60, float)
                limite = 50
                if alg == "dfs":
                    limite = _pedir("Limite de profundidade (DFS)", 50, int)

                passo_raw = input(f"  {LYELLOW}Mostrar passo a passo? [S/n]:{R} ").strip().lower()
                passo = passo_raw != "n"

                pausa_seg = 0.0
                animar    = False
                if passo:
                    pausa_seg = _pedir("Pausa entre passos (segundos)", 0.5, float)
                    animar    = pausa_seg > 0

                # ── resolução com spinner
                import tracemalloc, time as _time
                sys.setrecursionlimit(20000)
                tracemalloc.start()
                t0 = _time.perf_counter()
                with Spinner(f"A resolver com {NOMES_ALG.get(alg, alg)}"):
                    r = executar(alg, p, heur, tempo_max=tempo, limite=limite)
                r.extra["tempo"]   = _time.perf_counter() - t0
                r.extra["memoria"] = tracemalloc.get_traced_memory()[1] / 2 ** 20
                tracemalloc.stop()

                # ── apresentação
                cls()
                mostrar_resultado(p, r, passo, pausa_seg, animar)
                pausa()

        except (ValueError, OSError, IndexError, KeyError) as e:
            erro(str(e))
            pausa()
        except KeyboardInterrupt:
            pass   # Ctrl+C regressa ao menu sem sair


# ──────────────────────────────────────────────────────────────────────────────
# Ponto de entrada  — suporta os mesmos argumentos de main.py (modo directo)
# ──────────────────────────────────────────────────────────────────────────────

def main():
    import argparse
    from buscas import ALGORITMOS, INFORMADOS, executar
    from dominio import RushHour, carregar_base

    RAIZ = Path(__file__).parent

    ap = argparse.ArgumentParser(
        description="TUI ANSI Art — P6 Rush Hour generalizado (Grupo 06)"
    )
    ap.add_argument("--instancia", help="'base' ou caminho para JSON")
    ap.add_argument("--gerar", choices=["pequena", "media", "grande"])
    ap.add_argument("--semente",    type=int,   default=202606)
    ap.add_argument("--alg",        choices=list(ALGORITMOS))
    ap.add_argument("--h",          default="h4", choices=list(HEURS))
    ap.add_argument("--criterio",   default="movimentos",
                    choices=["movimentos", "ponderado"])
    ap.add_argument("--tempo",      type=float, default=60)
    ap.add_argument("--limite-dfs", type=int,   default=50)
    ap.add_argument("--sem-passos", action="store_true")
    ap.add_argument("--pausa",      type=float, default=0.0)
    ap.add_argument("--animar",     action="store_true")
    a = ap.parse_args()

    if a.alg is None:
        # modo interactivo
        try:
            menu_tui()
        except KeyboardInterrupt:
            cls()
            print(f"\n  {LCYAN}Até à próxima!{R}\n")
        return

    # ── modo directo (linha de comandos)
    cls()
    print(LOGO)
    criterio = a.criterio
    if a.gerar:
        from gerador import gerar as gerar_puzzles
        with Spinner(f"A gerar puzzle '{a.gerar}'"):
            q, d, _ = gerar_puzzles(a.gerar, 1, a.semente)[0]
        p = q.com_criterio(criterio)
        sucesso(f"Puzzle '{a.gerar}' gerado — óptimo {d} movimentos")
    elif a.instancia in (None, "", "base"):
        p = carregar_base(criterio)
    else:
        p = RushHour.de_json(a.instancia, criterio)

    heur = a.h if a.alg in INFORMADOS else None

    import tracemalloc, time as _time
    sys.setrecursionlimit(20000)
    tracemalloc.start()
    t0 = _time.perf_counter()
    with Spinner(f"A resolver com {NOMES_ALG.get(a.alg, a.alg)}"):
        r = executar(a.alg, p, heur, tempo_max=a.tempo, limite=a.limite_dfs)
    r.extra["tempo"]   = _time.perf_counter() - t0
    r.extra["memoria"] = tracemalloc.get_traced_memory()[1] / 2 ** 20
    tracemalloc.stop()

    mostrar_resultado(p, r, not a.sem_passos, a.pausa, a.animar)


if __name__ == "__main__":
    main()
