"""Figura da arquitectura do programa (módulos e dependências)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


def desenhar(saida):
    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.9)
    ax.axis("off")
    caixas = {
        "main.py\nmenu, visualização ASCII": (3.6, 5.3, "#dbe9f6"),
        "experiencias.py\nbateria, CSV, gráficos": (7.1, 5.3, "#dbe9f6"),
        "gerador.py\nsemente 202606": (0.2, 5.3, "#dbe9f6"),
        "buscas.py\nBFS DFS IDS UCS\nGulosa A* IDA*(+TT)": (1.2, 2.9, "#fde2c8"),
        "heuristicas.py\nh0–h4, h*, b*": (6.2, 2.9, "#e2f0d9"),
        "problema.py\nProblema (abstracta)\nNo, caminho()": (1.2, 0.5, "#eeeeee"),
        "dominio.py\nRushHour(Problema)\nVeiculo, Accao": (6.2, 0.5, "#e2f0d9"),
    }
    pos = {}
    for texto, (x, y, cor) in caixas.items():
        w, h = 2.7, 0.95
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", fc=cor, ec="#333"))
        ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=9)
        pos[texto.split("\n")[0]] = (x + w / 2, y + h / 2, w, h)

    def seta(a, b, rot=""):
        xa, ya, wa, ha = pos[a]
        xb, yb, wb, hb = pos[b]
        if ya == yb:   # mesma linha: ligar pelos lados
            xa2, xb2 = (xa - wa / 2, xb + wb / 2) if xa > xb else (xa + wa / 2, xb - wb / 2)
            ax.annotate("", (xb2, yb), (xa2, ya), arrowprops=dict(arrowstyle="->", color="#333"))
            ax.text((xa2 + xb2) / 2, ya + .08, rot, fontsize=7.5, color="#555", ha="center")
            return
        ya2 = ya - ha / 2 if ya > yb else ya + ha / 2 if ya < yb else ya
        yb2 = yb + hb / 2 if ya > yb else yb - hb / 2 if ya < yb else yb
        ax.annotate("", (xb, yb2), (xa, ya2), arrowprops=dict(arrowstyle="->", color="#333"))
        if rot:
            ax.text((xa + xb) / 2 + .05, (ya2 + yb2) / 2, rot, fontsize=7.5, color="#555")

    seta("main.py", "buscas.py", "executar()")
    seta("main.py", "dominio.py")
    seta("experiencias.py", "buscas.py")
    seta("experiencias.py", "heuristicas.py", "h*, b*")
    seta("gerador.py", "dominio.py")
    seta("buscas.py", "problema.py", "só a interface")
    seta("dominio.py", "problema.py", "herda")
    seta("dominio.py", "heuristicas.py", "heuristica(s, nome)")
    ax.text(5, 6.65, "Os algoritmos só conhecem a interface Problema; o domínio P6 está isolado em dominio.py",
            ha="center", fontsize=9, style="italic")
    fig.tight_layout()
    fig.savefig(saida, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    desenhar("outputs/graficos/arquitectura.png")
