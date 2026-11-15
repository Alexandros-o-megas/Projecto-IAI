"""Contra-exemplo à admissibilidade de h2 (dica do enunciado) — critério movimentos.

    . . . C C
    . . . . A
    X X B . A   → saída
    . . B . .
    . E E . .

h1 = 2 (B e A bloqueiam X). Pelo lado mais curto, B sai para baixo (1 casa),
mas E está lá; A sai para cima (1 casa), mas C está lá. Logo h2 = 2 + 2 = 4.
Porém B pode subir 2 casas e A descer 2 casas (lados mais longos, livres):
B-2, A+2, X+3 resolve em 3 movimentos, logo h*(s) = 3 < h2(s) = 4.
"""
from dominio import RushHour, Veiculo


def instancia(criterio="movimentos"):
    veiculos = [Veiculo("X", "H", 2, 2), Veiculo("A", "V", 2, 4), Veiculo("B", "V", 2, 2),
                Veiculo("C", "H", 2, 0), Veiculo("E", "H", 2, 4)]
    estado = (0, 1, 2, 3, 1)
    p = RushHour(5, veiculos, estado, linha_saida=2, criterio=criterio)
    return p, estado, 4, 3
