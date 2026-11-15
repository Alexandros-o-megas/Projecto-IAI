"""Algoritmos de busca: optimalidade, coerência entre algoritmos e casos limite."""
import sys

import pytest

from buscas import ALGORITMOS, executar
from dominio import RushHour, Veiculo, carregar_base

sys.setrecursionlimit(10000)
OPTIMOS = [("ucs", None), ("astar", "h0"), ("astar", "h1"), ("astar", "h3"), ("astar", "h4"),
           ("idastar", "h4"), ("idastar_simples", "h3")]


def valida(p, r):
    """Reaplica as acções a partir do estado inicial e confirma custo e objectivo."""
    s, custo = p.estado_inicial(), 0
    for a in r.accoes():
        s2 = p.resultado(s, a)
        custo += p.custo(s, a, s2)
        s = s2
    assert p.e_objectivo(s)
    assert custo == r.custo
    assert len(r.accoes()) == r.comprimento


@pytest.mark.parametrize("criterio,optimo", [("movimentos", 8), ("ponderado", 40)])
@pytest.mark.parametrize("alg,h", OPTIMOS)
def test_optimos_na_base(criterio, optimo, alg, h):
    if alg == "idastar_simples" and criterio == "ponderado":
        pytest.skip("IDA* sem tabela excede 60 s no ponderado (custos finos => muitas iterações)")
    p = carregar_base(criterio)
    r = executar(alg, p, h, tempo_max=60)
    assert r.estado == "ok"
    assert r.custo == optimo
    valida(p, r)


def test_bfs_optimo_em_movimentos_e_os_dois_optimos_coincidem_na_base():
    pm, pp = carregar_base("movimentos"), carregar_base("ponderado")
    r = executar("bfs", pm)
    assert r.comprimento == 8
    assert sum(pp.custo_accao(a) for a in r.accoes()) == executar("ucs", pp).custo == 40


def test_astar_igual_ucs_em_custo_em_instancias_geradas():
    from pathlib import Path
    for f in sorted(Path("instancias").glob("pequena_0[1-3].json")):
        for criterio in ("movimentos", "ponderado"):
            p = RushHour.de_json(f, criterio)
            assert executar("astar", p, "h4").custo == executar("ucs", p).custo


def test_sucessores_do_estado_inicial():
    p = carregar_base()
    accoes = {(a.veiculo, a.deslocamento) for a in p.accoes(p.estado_inicial())}
    # B, P e X estão presos; O só desce 1 (C por baixo); Q sobe ou desce 1
    assert accoes == {("A", 1), ("A", 2), ("A", 3), ("C", -1), ("C", -2), ("C", -3),
                      ("O", 1), ("Q", -1), ("Q", 1), ("R", -1), ("R", 1)}


def sem_solucao():
    # obstáculo fixo (polícia) na linha de saída à frente de X
    return RushHour(4, [Veiculo("X", "H", 2, 1), Veiculo("A", "V", 2, 0)], (0, 2),
                    [(1, 3)], linha_saida=1)


@pytest.mark.parametrize("alg", list(ALGORITMOS))
def test_instancia_sem_solucao(alg):
    r = executar(alg, sem_solucao(), "h4")
    assert r.estado == "sem solução"
    assert r.no is None


def test_dfs_respeita_limite_de_profundidade():
    p = carregar_base()
    r = executar("dfs", p, limite=5)
    assert r.estado == "limite" and r.fronteira_max <= 6
    r = executar("dfs", p, limite=30)
    assert r.estado == "ok" and r.comprimento <= 30
    valida(p, r)


def test_ids_conta_reexpansoes_e_e_optimo_em_movimentos():
    p = RushHour(6, [Veiculo("X", "H", 2, 2), Veiculo("A", "V", 3, 4), Veiculo("B", "H", 2, 5)],
                 (0, 2, 3), linha_saida=2)
    r = executar("ids", p)
    assert r.estado == "ok" and r.comprimento == executar("bfs", p).comprimento
    assert r.reexpandidos > 0 and r.iteracoes == r.comprimento + 1


def test_tabela_de_transposicao_reduz_nos():
    p = carregar_base()
    simples = executar("idastar_simples", p, "h2")
    tt = executar("idastar", p, "h2")
    assert simples.custo == tt.custo == 8
    assert tt.expandidos < simples.expandidos
    assert tt.extra["podas_tabela"] > 0


def test_gulosa_nao_garante_optimo_mas_resolve():
    p = carregar_base()
    r = executar("gulosa", p, "h1")
    assert r.estado == "ok" and r.custo >= 8
    valida(p, r)


def test_limite_de_tempo():
    r = executar("ids", carregar_base(), tempo_max=0.2)
    assert r.estado == "tempo"


def test_criterios_divergem_na_instancia_gerada_pequena_02():
    """Nenhuma solução de mínimo de movimentos (7) é óptima no custo ponderado (21, com 8 mov.)."""
    from heuristicas import divergencia
    p = RushHour.de_json("instancias/pequena_02.json")
    assert divergencia(p) == (7, 24, 21, 8)
    assert divergencia(carregar_base()) == (8, 40, 40, 8)
    pp = p.com_criterio("ponderado")
    assert executar("bfs", pp).custo > executar("ucs", pp).custo == 21
