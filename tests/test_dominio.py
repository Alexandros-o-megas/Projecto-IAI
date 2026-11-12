import pytest
from dominio import Accao, RushHour, Veiculo, carregar_base
from problema import No, caminho


def test_base():
    p = carregar_base()
    assert ["".join(l) for l in p.grelha(p.estado_inicial())] == [
        "AA...O", "P..Q.O", "PXXQ.O", "P..Q..", "B...CC", "B.RRR."]
    assert hash(p.estado_inicial())


@pytest.mark.parametrize("k", [1, 2, 3])
def test_movimento_e_imutabilidade(k):
    p = carregar_base()
    s = p.estado_inicial()
    a = Accao("A", k)
    novo = p.resultado(s, a)
    assert novo[0] == k and s[0] == 0
    assert p.custo(s, a, novo) == 1
    ponderado = carregar_base("ponderado")
    assert ponderado.custo(s, a, novo) == 2*k


@pytest.mark.parametrize("a", [Accao("A", 4), Accao("A", -1), Accao("A", 0),
                               Accao("X", 1), Accao("X", 4), Accao("Z", 1)])
def test_movimentos_ilegais(a):
    p = carregar_base()
    with pytest.raises(ValueError):
        p.resultado(p.estado_inicial(), a)


def test_saida():
    p = RushHour(4, [Veiculo("X", "H", 2, 1)], (0,), linha_saida=1)
    s = p.resultado((0,), Accao("X", 2))
    assert p.e_objectivo(s)
    assert p.accoes(s) == []
    assert p.heuristica(s, "h0") == 0


def test_obstaculo():
    p = RushHour(4, [Veiculo("X", "H", 2, 1)], (0,), [(1, 2)], 1)
    assert p.accoes((0,)) == []


def test_colisao():
    with pytest.raises(ValueError):
        RushHour(4, [Veiculo("X", "H", 2, 1)], (0,), [(1, 1)], 1)


def test_oito():
    p = RushHour(8, [Veiculo("X", "H", 2, 0)], (0,), linha_saida=0)
    assert len(p.accoes((0,))) == 6


def test_caminho():
    raiz = No((0,))
    filho = No((1,), raiz, Accao("X", 1), 1, 1)
    assert caminho(filho) == [raiz, filho]
    assert caminho(None) == []
