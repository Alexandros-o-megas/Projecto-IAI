"""Gera o relatório (template oficial) com os resultados reais das experiências.

    python relatorio/gerar_relatorio.py   ->  outputs/Relatorio_Grupo06_P6.docx

Os números são calculados aqui (instância base) ou lidos dos CSV produzidos por
experiencias.py; nada é escrito à mão. Converter para PDF com
    libreoffice --headless --convert-to pdf --outdir outputs outputs/Relatorio_Grupo06_P6.docx
(no Word/LibreOffice: actualizar os índices antes de exportar o PDF final).
"""
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
from docx import Document

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from buscas import executar  # noqa: E402
from docx_util import Escritor, remover, substituir  # noqa: E402
from dominio import carregar_base  # noqa: E402
from heuristicas import b_efectivo, divergencia, h_estrela  # noqa: E402
import capitulos  # noqa: E402

OUT = RAIZ / "outputs"
GRAF = OUT / "graficos"
MEMBROS = ["Falaque, Dalton", "Nhabinde, Alex", "Nhabomba, Lino", "Quive, Alexandre", "Ricardo"]
DATA = "Maputo, 18 de Novembro de 2026"


def factos_base():
    R = {}
    for criterio in ("movimentos", "ponderado"):
        p = carregar_base(criterio)
        hs, ar = h_estrela(p)
        R[criterio] = {"estados": len(hs), "transicoes": sum(len(v) for v in ar.values()),
                       "objectivos": sum(p.e_objectivo(s) for s in hs),
                       "optimo": hs[p.estado_inicial()]}
        for alg, h in [("bfs", None), ("ucs", None), ("astar", "h0"), ("astar", "h1"), ("astar", "h2"),
                       ("astar", "h3"), ("astar", "h4"), ("gulosa", "h1"), ("gulosa", "h2"),
                       ("idastar_simples", "h2"), ("idastar", "h2"), ("idastar", "h4"), ("dfs", None)]:
            r = executar(alg, p, h, tempo_max=60)
            R[criterio][f"{alg}-{h}"] = r
    p = carregar_base()
    R["h_inicial"] = {h: p.heuristica(p.estado_inicial(), h) for h in ("h1", "h2", "h3")}
    R["h4_pond"] = carregar_base("ponderado").heuristica(p.estado_inicial(), "h4")
    R["div_base"] = divergencia(p)
    R["ramificacao"] = R["movimentos"]["transicoes"] / R["movimentos"]["estados"]
    R["sol_mov"] = " ".join(f"{a.veiculo}{a.deslocamento:+d}" for a in R["movimentos"]["bfs-None"].accoes())
    R["sol_pond"] = " ".join(f"{a.veiculo}{a.deslocamento:+d}" for a in R["ponderado"]["ucs-None"].accoes())
    R["grelha"] = p.desenhar(p.estado_inicial())
    R["s0"] = p.estado_inicial()
    R["b_ida"] = {k: R["movimentos"][k] for k in ("idastar_simples-h2", "idastar-h2")}
    return R


def ler_csv(nome):
    f = OUT / nome
    return pd.read_csv(f) if f.exists() else None


def testes():
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=RAIZ,
                       capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1].split(" in ")[0]


def capa(doc):
    corpo = list(doc.element.body.iterchildren())
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    for el in corpo[:40]:
        if el.tag.endswith("}p"):
            par = Paragraph(el, doc)
            if "<Pn" in par.text:
                substituir(par, "P6 — “Engarrafamento na Baixa” (Rush Hour generalizado)")
            elif "<GRUPO" in par.text:
                substituir(par, "GRUPO 06 — Laboral")
            elif "Maputo, <dia>" in par.text:
                substituir(par, DATA)
        elif el.tag.endswith("}tbl"):
            t = Table(el, doc)
            for i, linha in enumerate(list(t.rows[1:])):
                if i < len(MEMBROS):
                    substituir(linha.cells[0].paragraphs[0], MEMBROS[i])
                else:
                    remover(linha._tr)   # 6.ª linha vazia (o grupo tem 5 membros)


def pre_textuais(doc, R, D):
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    corpo = list(doc.element.body.iterchildren())
    for el in corpo[40:70]:
        if not el.tag.endswith("}p"):
            if el.tag.endswith("}tbl"):
                t = Table(el, doc)
                if t.rows[0].cells[0].text.strip() == "A*":
                    abrev = [("A*", "Algoritmo A estrela"),
                             ("b*", "Factor de ramificação efectivo"),
                             ("BFS", "Breadth-First Search — Busca em Largura"),
                             ("DFS", "Depth-First Search — Busca em Profundidade"),
                             ("g(n)", "Custo do caminho desde o estado inicial até ao nó n"),
                             ("h(n)", "Função heurística: estimativa do custo de n até ao objectivo"),
                             ("h*(n)", "Custo óptimo real de n até ao objectivo"),
                             ("IA I", "Inteligência Artificial I"),
                             ("IDA*", "Iterative Deepening A* — A* com aprofundamento iterativo"),
                             ("IDS", "Iterative Deepening Search — Aprofundamento Iterativo"),
                             ("TT", "Tabela de transposição"),
                             ("UCS", "Uniform-Cost Search — Busca de Custo Uniforme")]
                    linhas = list(t.rows)
                    while len(linhas) < len(abrev):
                        novo = __import__("copy").deepcopy(linhas[-1]._tr)
                        linhas[-1]._tr.addnext(novo)
                        linhas = list(t.rows)
                    for linha, (a, b) in zip(t.rows, abrev):
                        substituir(linha.cells[0].paragraphs[0], a)
                        substituir(linha.cells[1].paragraphs[0], b)
            continue
        par = Paragraph(el, doc)
        if par.text.startswith("<Entre 150"):
            substituir(par, capitulos.resumo(R, D))
        elif par.text.startswith("Palavras-chave"):
            substituir(par, "Palavras-chave: Inteligência Artificial; Busca no espaço de estados; A*; "
                            "Heurísticas admissíveis; Rush Hour; IDA*; Tabela de transposição; "
                            "Gerador de instâncias")
        elif par.text.startswith("<Todas as abreviaturas"):
            remover(el)


def main():
    doc = Document(RAIZ / "relatorio" / "template.docx")
    R = factos_base()
    D = {n: ler_csv(n) for n in ["resultados.csv", "heuristicas.csv", "verificacao_heuristicas.csv",
                                 "divergencia_criterios.csv"]}
    D["resumos"] = {f.stem.replace("resumo_", ""): pd.read_csv(f) for f in OUT.glob("resumo_*.csv")}
    D["ambiente"] = json.loads((OUT / "ambiente.json").read_text()) if (OUT / "ambiente.json").exists() else {}
    D["testes"] = testes()
    D["analise_base"] = (OUT / "analise_base.txt").read_text() if (OUT / "analise_base.txt").exists() else ""
    capa(doc)
    pre_textuais(doc, R, D)
    # remover o corpo do template (a partir de "INTRODUÇÃO") e reescrever
    corpo = list(doc.element.body.iterchildren())
    inicio = next(i for i, el in enumerate(corpo)
                  if el.tag.endswith("}p") and "INTRODUÇÃO" in "".join(el.itertext())
                  and "Heading" in (el.find(".//{*}pStyle").get(
                      "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val") if el.find(".//{*}pStyle") is not None else ""))
    for el in corpo[inicio:]:
        if not el.tag.endswith("}sectPr"):
            remover(el)
    w = Escritor(doc)
    capitulos.escrever(w, R, D, GRAF)
    saida = OUT / "Relatorio_Grupo06_P6.docx"
    doc.save(saida)
    print("Relatório gerado:", saida)


if __name__ == "__main__":
    main()
