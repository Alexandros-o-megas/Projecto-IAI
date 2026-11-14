"""Heurísticas: admissibilidade (h <= h*) em TODOS os estados alcançáveis,
consistência em todas as transições, dominância e b*."""
import math

import pytest

from dominio import RushHour, Veiculo, carregar_base
from heuristicas import b_efectivo, h_estrela, verificar

ADMISSIVEIS = ["h1", "h3", "h4"]


@pytest.fixture(scope="module", params=["movimentos", "ponderado"])
def base_hstar(request):
    p = carregar_base(request.param)
    hstar, arestas = h_estrela(p)
    return p, hstar, arestas


def test_hstar_base(base_hstar):
    p, hstar, _ = base_hstar
    assert len(hstar) == 1079
    assert hstar[p.estado_inicial()] == (8 if p.criterio == "movimentos" else 40)


@pytest.mark.parametrize("nome", ADMISSIVEIS + ["h2"])
def test_admissivel_e_consistente_na_base(base_hstar, nome):
    p, hstar, arestas = base_hstar
    v = verificar(p, nome, hstar, arestas)
    assert v["estados"] == 1079
    assert v["admissivel"], v["exemplo_adm"]
    if nome in ADMISSIVEIS:
        assert v["consistente"], v["exemplo_cons"]


def test_heuristicas_nulas_no_objectivo(base_hstar):
    p, hstar, _ = base_hstar
    for s in hstar:
        if p.e_objectivo(s):
            assert all(p.heuristica(s, h) == 0 for h in ["h0", "h1", "h2", "h3", "h4"])


def test_dominancia(base_hstar):
    p, hstar, _ = base_hstar
    for s in hstar:
        h1, h3, h4 = (p.heuristica(s, h) for h in ("h1", "h3", "h4"))
        assert h1 <= h3 <= h4
        assert p.heuristica(s, "h2") >= h1


def test_h1_conta_veiculos_e_nao_casas():
    p = carregar_base()
    assert p.heuristica(p.estado_inicial(), "h1") == 2          # Q e O
    assert p.heuristica(p.estado_inicial(), "h3") == 3


def test_h4_ponderado_na_base():
    # X anda 3 casas (2*3=6); Q (L=3) sai com 2 casas para baixo (6); O (L=3) com 3 para baixo (9)
    p = carregar_base("ponderado")
    assert p.heuristica(p.estado_inicial(), "h4") == 6 + 6 + 9


def test_estado_impossivel_tem_h_infinito():
    # camião horizontal à frente de X na linha de saída: nunca sai da linha
    p = RushHour(6, [Veiculo("X", "H", 2, 2), Veiculo("T", "H", 3, 2)], (0, 3), linha_saida=2)
    assert all(math.isinf(p.heuristica(p.estado_inicial(), h)) for h in ["h1", "h2", "h3", "h4"])


def test_h2_nao_e_admissivel():
    """Contra-exemplo encontrado pela verificação exaustiva (ver relatório, 4.2)."""
    from tests.contra_exemplo_h2 import instancia
    p, estado, h2, hstar = instancia()
    assert p.heuristica(estado, "h2") == h2 > hstar
    hs, _ = h_estrela(RushHour(p.tamanho, p.veiculos, estado, sorted(p.obstaculos), p.linha_saida,
                               p.criterio))
    assert hs[estado] == hstar


def test_b_efectivo():
    assert b_efectivo(3, 1) == pytest.approx(3)
    assert b_efectivo(14, 3) == pytest.approx(2, abs=1e-6)      # 2+4+8 = 14
    assert b_efectivo(52, 5) == pytest.approx(1.92, abs=0.01)


def test_h2_admissivel_no_ponderado_porque_h2_nao_excede_h4(base_hstar):
    """No custo ponderado h2 <= h4 <= h*: cada bloqueador b com deslocamento mínimo m_b
    tem no máximo m_b bloqueadores de 2.º nível e 1 + m_b <= L_b * m_b (L_b >= 2)."""
    p, hstar, _ = base_hstar
    if p.criterio != "ponderado":
        pytest.skip("só no critério ponderado")
    for s in hstar:
        assert p.heuristica(s, "h2") <= p.heuristica(s, "h4")
    from tests.contra_exemplo_h2 import instancia
    q, s, _, _ = instancia("ponderado")
    assert q.heuristica(s, "h2") <= h_estrela(q)[0][s]
