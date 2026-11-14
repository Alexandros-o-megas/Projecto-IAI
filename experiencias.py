"""Bateria de experiências do P6: corre os algoritmos sobre as instâncias,
regista métricas em CSV e gera os gráficos e tabelas usados no relatório.

Uso:
    python experiencias.py                 # tudo (bateria + análises + gráficos)
    python experiencias.py --so-graficos   # refaz só gráficos/resumos a partir do CSV
    python experiencias.py --workers 2 --tempo 60

Cada execução (instância × algoritmo × heurística × critério) corre num processo
novo com limite de memória de 2 GB (RLIMIT_AS) e limite de 60 s (prazo
verificado dentro do algoritmo, com um limite rígido de segurança no processo
pai). Execuções que excedem os limites ficam registadas como
"falhou (tempo)" / "falhou (memória)", não são omitidas.
A memória de pico é medida com tracemalloc (só a memória alocada pelo Python;
o tempo inclui o custo do tracemalloc, igual para todos os algoritmos).
"""
import argparse
import csv
import json
import math
import os
import platform
import resource
import sys
import time
import tracemalloc
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturoTempo
from multiprocessing import get_context
from pathlib import Path

from buscas import executar
from dominio import RushHour, carregar_base
from heuristicas import b_efectivo, divergencia, h_estrela, verificar

RAIZ = Path(__file__).parent
INST = RAIZ / "instancias"
OUT = RAIZ / "outputs"
GRAF = OUT / "graficos"
LIMITE_MEMORIA = 2 * 1024 ** 3
NIVEIS = ("pequena", "media", "grande")

# (algoritmo, heurística) corridos para cada instância e critério
CONFIGURACOES = [
    ("bfs", None), ("dfs", None), ("ids", None), ("ucs", None),
    ("gulosa", "h1"), ("gulosa", "h2"),
    ("astar", "h0"), ("astar", "h1"), ("astar", "h2"), ("astar", "h3"), ("astar", "h4"),
    ("idastar_simples", "h4"), ("idastar", "h4"),
]
OPTIMOS = {"ucs", "astar", "idastar", "idastar_simples"}  # garantem óptimo (h admissível)
CAMPOS = ["nivel", "instancia", "tamanho", "veiculos", "obstaculos", "optimo_mov_gerador",
          "criterio", "algoritmo", "heuristica", "estado", "custo", "comprimento",
          "expandidos", "gerados", "fronteira_max", "reexpandidos", "iteracoes",
          "podas_tabela", "tempo_s", "memoria_mb"]


def _limitar_memoria():
    try:
        resource.setrlimit(resource.RLIMIT_AS, (LIMITE_MEMORIA, LIMITE_MEMORIA))
    except (ValueError, OSError):
        pass
    sys.setrecursionlimit(20000)


def correr_um(ficheiro, criterio, alg, heur, tempo):
    """Executa uma configuração e devolve uma linha do CSV (corre no processo filho)."""
    p = RushHour.de_json(ficheiro, criterio)
    linha = {"criterio": criterio, "algoritmo": alg, "heuristica": heur or "—"}
    tracemalloc.start()
    t0 = time.perf_counter()
    try:
        r = executar(alg, p, heur, tempo_max=tempo)
        estado = {"ok": "ok", "tempo": "falhou (tempo)"}.get(r.estado, r.estado)
    except MemoryError:
        r, estado = None, "falhou (memória)"
    except RecursionError:
        r, estado = None, "falhou (recursão)"
    dt = time.perf_counter() - t0
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    linha.update(estado=estado, tempo_s=round(dt, 4), memoria_mb=round(pico / 2 ** 20, 3))
    if r is not None:
        linha.update(custo=r.custo, comprimento=r.comprimento, expandidos=r.expandidos,
                     gerados=r.gerados, fronteira_max=r.fronteira_max,
                     reexpandidos=r.reexpandidos, iteracoes=r.iteracoes,
                     podas_tabela=r.extra.get("podas_tabela", ""))
    return linha


def instancias(niveis=NIVEIS):
    lista = [("base", INST / "base.json")] if "pequena" in niveis else []
    for nivel in niveis:
        lista += [(nivel, f) for f in sorted(INST.glob(f"{nivel}_*.json"))]
    return lista


def meta(ficheiro):
    dados = json.loads(Path(ficheiro).read_text(encoding="utf-8"))
    return {"instancia": Path(ficheiro).stem, "tamanho": dados["tamanho"],
            "veiculos": len(dados["veiculos"]), "obstaculos": len(dados.get("obstaculos", [])),
            "optimo_mov_gerador": dados.get("meta", {}).get("optimo_movimentos", "")}


def bateria(niveis, workers, tempo, saida, anexar=False):
    tarefas = []
    for nivel, f in instancias(niveis):
        for criterio in ("movimentos", "ponderado"):
            for alg, heur in CONFIGURACOES:
                tarefas.append((nivel, f, criterio, alg, heur))
    print(f"{len(tarefas)} execuções, {workers} processo(s), limite {tempo}s / 2 GB")
    ctx = get_context("forkserver")
    linhas = []
    with ProcessPoolExecutor(workers, mp_context=ctx, initializer=_limitar_memoria,
                             max_tasks_per_child=1) as pool:
        futuros = [(t, pool.submit(correr_um, str(t[1]), t[2], t[3], t[4], tempo)) for t in tarefas]
        for i, ((nivel, f, criterio, alg, heur), fut) in enumerate(futuros, 1):
            try:
                linha = fut.result(timeout=tempo * 3 + 60)
            except FuturoTempo:
                linha = {"criterio": criterio, "algoritmo": alg, "heuristica": heur or "—",
                         "estado": "falhou (tempo)", "tempo_s": tempo}
            except Exception as e:   # processo morto (p.ex. memória)
                linha = {"criterio": criterio, "algoritmo": alg, "heuristica": heur or "—",
                         "estado": f"falhou ({type(e).__name__})"}
            linha.update(nivel=nivel, **meta(f))
            linhas.append(linha)
            print(f"[{i}/{len(tarefas)}] {linha['instancia']} {criterio} {alg} {heur or ''} "
                  f"-> {linha['estado']} custo={linha.get('custo')} exp={linha.get('expandidos')} "
                  f"t={linha.get('tempo_s')}", flush=True)
    if anexar and Path(saida).exists():
        with open(saida, encoding="utf-8") as fh:
            antigas = [l for l in csv.DictReader(fh)
                       if l["nivel"] not in niveis and not (l["nivel"] == "base" and "pequena" in niveis)]
        linhas = antigas + linhas
    with open(saida, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, CAMPOS)
        w.writeheader()
        for linha in linhas:
            w.writerow({k: linha.get(k, "") for k in CAMPOS})
    return saida


# --------------------------------------------------------------------- análises
def analise_base():
    """Pergunta de análise do P6 e factos da instância base."""
    linhas = []
    for criterio in ("movimentos", "ponderado"):
        p = carregar_base(criterio)
        hstar, arestas = h_estrela(p)
        s0 = p.estado_inicial()
        linhas.append(f"[{criterio}] estados alcançáveis: {len(hstar)}; "
                      f"objectivos alcançáveis: {sum(p.e_objectivo(s) for s in hstar)}; "
                      f"transições: {sum(len(v) for v in arestas.values())}; "
                      f"custo óptimo: {hstar[s0]}")
        for alg, h in [("bfs", None), ("ucs", None), ("astar", "h0"), ("astar", "h1"),
                       ("astar", "h2"), ("astar", "h3"), ("astar", "h4"),
                       ("idastar_simples", "h2"), ("idastar", "h2"),
                       ("idastar_simples", "h4"), ("idastar", "h4")]:
            r = executar(alg, p, h, tempo_max=60)
            frac = f"{100 * r.expandidos / len(hstar):.1f}%"
            linhas.append(f"  {alg:16s} {h or '—':3s} estado={r.estado:10s} custo={r.custo} "
                          f"movimentos={r.comprimento} expandidos={r.expandidos} ({frac} dos estados) "
                          f"gerados={r.gerados}")
    pm, pp = carregar_base("movimentos"), carregar_base("ponderado")
    rb = executar("bfs", pm)
    custo_pond_bfs = sum(pp.custo_accao(a) for a in rb.accoes())
    ru = executar("ucs", pp)
    linhas.append(f"Solução BFS (mín. movimentos={rb.comprimento}) tem custo ponderado {custo_pond_bfs}; "
                  f"óptimo ponderado (UCS) = {ru.custo} com {ru.comprimento} movimentos -> "
                  f"{'coincidem' if custo_pond_bfs == ru.custo else 'diferem'}.")
    linhas.append("Solução óptima (movimentos): " + " ".join(f"{a.veiculo}{a.deslocamento:+d}" for a in rb.accoes()))
    linhas.append("Solução óptima (ponderado):  " + " ".join(f"{a.veiculo}{a.deslocamento:+d}" for a in ru.accoes()))
    texto = "\n".join(linhas)
    (OUT / "analise_base.txt").write_text(texto + "\n", encoding="utf-8")
    print(texto)


def verificacao_heuristicas(niveis=("pequena",)):
    """h(s) <= h*(s) em todos os estados e consistência em todas as transições."""
    linhas = []
    for nivel, f in instancias(niveis):
        for criterio in ("movimentos", "ponderado"):
            p = RushHour.de_json(f, criterio)
            try:
                hstar, arestas = h_estrela(p, limite=200_000)
            except MemoryError:
                continue
            for nome in ("h1", "h2", "h3", "h4"):
                v = verificar(p, nome, hstar, arestas)
                linhas.append({"instancia": f.stem, **{k: v[k] for k in (
                    "criterio", "heuristica", "estados", "transicoes", "admissivel",
                    "violacoes_adm", "consistente", "violacoes_cons")},
                    "contra_exemplo": json.dumps(v["exemplo_adm"]) if v["exemplo_adm"] else ""})
    with open(OUT / "verificacao_heuristicas.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    return linhas


def divergencias(niveis=("pequena", "media")):
    """Movimentos vs. custo ponderado: em que instâncias os óptimos diferem?"""
    linhas = []
    for nivel, f in instancias(niveis):
        d_mov, pond_de_min_mov, pond_opt, mov_de_pond = divergencia(RushHour.de_json(f))
        linhas.append({"instancia": f.stem, "min_movimentos": d_mov,
                       "melhor_ponderado_com_min_movimentos": pond_de_min_mov,
                       "optimo_ponderado": pond_opt, "movimentos_do_optimo_ponderado": mov_de_pond,
                       "diferem": pond_de_min_mov > pond_opt})
    with open(OUT / "divergencia_criterios.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    return linhas


# --------------------------------------------------------------------- resumos e gráficos
def carregar(saida):
    import pandas as pd
    df = pd.read_csv(saida)
    df["ok"] = df["estado"] == "ok"
    ref = (df[df.ok & df.algoritmo.isin(OPTIMOS)]
           .groupby(["instancia", "criterio"])["custo"].min().rename("optimo"))
    df = df.join(ref, on=["instancia", "criterio"])
    df["custo_rel"] = df["custo"] / df["optimo"]
    df["config"] = df.apply(lambda r: r.algoritmo + ("" if r.heuristica == "—" else f"-{r.heuristica}"), axis=1)
    # profundidade óptima d (nº de movimentos) para o eixo "tamanho"
    dmov = (df[df.ok & (df.criterio == "movimentos") & df.algoritmo.isin(["bfs", "ucs", "astar"])]
            .groupby("instancia")["comprimento"].min().rename("d"))
    return df.join(dmov, on="instancia")


def resumos(df):
    import pandas as pd
    for nivel in ("base",) + NIVEIS:
        sub = df[df.nivel == nivel]
        if sub.empty:
            continue
        for criterio in ("movimentos", "ponderado"):
            s = sub[sub.criterio == criterio]
            g = s.groupby("config", sort=False)
            tab = pd.DataFrame({
                "resolvidas": g["ok"].sum().astype(int).astype(str) + "/" + g.size().astype(str),
                "custo_medio": g.apply(lambda x: x.loc[x.ok, "custo"].mean()),
                "custo_optimo": g.apply(lambda x: x.loc[x.ok, "custo_rel"].mean()),
                "expandidos": g.apply(lambda x: x.loc[x.ok, "expandidos"].mean()),
                "gerados": g.apply(lambda x: x.loc[x.ok, "gerados"].mean()),
                "fronteira_max": g.apply(lambda x: x.loc[x.ok, "fronteira_max"].mean()),
                "tempo_s": g.apply(lambda x: x.loc[x.ok, "tempo_s"].mean()),
                "tempo_dp": g.apply(lambda x: x.loc[x.ok, "tempo_s"].std()),
                "memoria_mb": g.apply(lambda x: x.loc[x.ok, "memoria_mb"].mean()),
                "falhas": g.apply(lambda x: "; ".join(sorted(set(x.loc[~x.ok, "estado"])))),
            })
            tab.round(4).to_csv(OUT / f"resumo_{nivel}_{criterio}.csv")


def tabela_heuristicas(df):
    """Tabela 3: A* com h0..h4 — nós expandidos e factor de ramificação efectivo b*."""
    import pandas as pd
    a = df[(df.algoritmo == "astar") & df.ok]
    linhas = []
    for (inst, crit), g in a.groupby(["instancia", "criterio"]):
        linha = {"instancia": inst, "criterio": crit, "nivel": g.nivel.iloc[0]}
        for _, r in g.iterrows():
            d = int(r.comprimento)
            linha["d"] = d
            linha[f"exp_{r.heuristica}"] = int(r.expandidos)
            linha[f"b_{r.heuristica}"] = round(b_efectivo(int(r.expandidos), d), 3)
        linhas.append(linha)
    t = pd.DataFrame(linhas)
    t.to_csv(OUT / "heuristicas.csv", index=False)
    return t


def graficos(df):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    GRAF.mkdir(parents=True, exist_ok=True)
    seleccao = ["bfs", "dfs", "ids", "ucs", "gulosa-h2", "astar-h0", "astar-h2", "astar-h4",
                "idastar_simples-h4", "idastar-h4"]
    marcadores = dict(zip(seleccao, "osD^v<>Pp*X"))
    for criterio in ("movimentos", "ponderado"):
        s = df[(df.criterio == criterio) & df.ok & (df.nivel != "base")]
        for metrica, rotulo, nome, log in [
                ("expandidos", "Nós expandidos (escala log)", "expandidos_vs_tamanho", True),
                ("tempo_s", "Tempo (s, escala log)", "tempo_vs_tamanho", True)]:
            fig, ax = plt.subplots(figsize=(8, 5))
            for c in seleccao:
                pts = s[s.config == c].groupby("d")[metrica].mean()
                if len(pts):
                    ax.plot(pts.index, pts.values, marker=marcadores[c], label=c, alpha=.85)
            ax.set_yscale("log" if log else "linear")
            ax.set_xlabel("Tamanho da instância: profundidade óptima d (nº de movimentos)")
            ax.set_ylabel(rotulo)
            ax.set_title(f"{rotulo.split(' (')[0]} vs. tamanho — critério {criterio}")
            ax.grid(alpha=.3, which="both")
            ax.legend(fontsize=8, ncol=2)
            fig.tight_layout()
            fig.savefig(GRAF / f"{nome}_{criterio}.png", dpi=150)
            plt.close(fig)
        # custo obtido vs. custo óptimo
        fig, ax = plt.subplots(figsize=(6.5, 6))
        for c in ["bfs", "dfs", "gulosa-h1", "gulosa-h2", "astar-h4", "idastar-h4"]:
            pts = s[s.config == c]
            ax.scatter(pts.optimo, pts.custo, label=c, alpha=.7, s=22)
        lim = [0, max(s.custo.max(), s.optimo.max()) * 1.05]
        ax.plot(lim, lim, "k--", lw=1, label="custo = óptimo")
        ax.set_xlabel("Custo óptimo")
        ax.set_ylabel("Custo obtido")
        ax.set_yscale("log")
        ax.set_xscale("log")
        ax.set_title(f"Custo obtido vs. custo óptimo — critério {criterio}")
        ax.legend(fontsize=8)
        ax.grid(alpha=.3, which="both")
        fig.tight_layout()
        fig.savefig(GRAF / f"custo_vs_optimo_{criterio}.png", dpi=150)
        plt.close(fig)
    # IDA* simples vs. IDA* com tabela de transposição
    fig, ax = plt.subplots(figsize=(8, 5))
    for criterio, cor in (("movimentos", "tab:blue"), ("ponderado", "tab:orange")):
        s = df[(df.criterio == criterio) & (df.nivel != "base")]
        sim = s[s.config == "idastar_simples-h4"].set_index("instancia")
        tt = s[s.config == "idastar-h4"].set_index("instancia")
        comum = sim.index[sim.ok].intersection(tt.index[tt.ok])
        ax.scatter(sim.loc[comum, "expandidos"], tt.loc[comum, "expandidos"], color=cor,
                   label=f"{criterio} ({len(comum)} instâncias resolvidas por ambos)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    lims = ax.get_xlim()
    ax.plot(lims, lims, "k--", lw=1, label="igual")
    ax.set_xlabel("Nós expandidos — IDA* simples")
    ax.set_ylabel("Nós expandidos — IDA* + tabela de transposição")
    ax.set_title("Redução de nós com a tabela de transposição (h4)")
    ax.legend(fontsize=8)
    ax.grid(alpha=.3, which="both")
    fig.tight_layout()
    fig.savefig(GRAF / "idastar_tt_vs_simples.png", dpi=150)
    plt.close(fig)


def ambiente():
    info = {"python": platform.python_version(), "sistema": platform.platform(),
            "processador": platform.processor() or platform.machine(), "cpus": os.cpu_count()}
    try:
        for l in open("/proc/cpuinfo"):
            if l.startswith("model name"):
                info["processador"] = l.split(":", 1)[1].strip()
                break
        for l in open("/proc/meminfo"):
            if l.startswith("MemTotal"):
                info["ram_gb"] = round(int(l.split()[1]) / 2 ** 20, 1)
    except OSError:
        pass
    (OUT / "ambiente.json").write_text(json.dumps(info, indent=1, ensure_ascii=False), encoding="utf-8")
    return info


def main():
    ap = argparse.ArgumentParser(description="Experiências do P6")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--tempo", type=float, default=60)
    ap.add_argument("--niveis", nargs="*", default=list(NIVEIS))
    ap.add_argument("--so-graficos", action="store_true")
    ap.add_argument("--so-bateria", action="store_true", help="não refaz as análises da base/heurísticas")
    ap.add_argument("--anexar", action="store_true", help="substitui só os níveis pedidos no CSV existente")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    saida = OUT / "resultados.csv"
    if not a.so_graficos:
        print(ambiente())
        if not a.so_bateria:
            analise_base()
            verificacao_heuristicas()
            divergencias()
        bateria(a.niveis, a.workers, a.tempo, saida, a.anexar)
    df = carregar(saida)
    resumos(df)
    tabela_heuristicas(df)
    graficos(df)
    print("Resultados em", OUT)


if __name__ == "__main__":
    main()
