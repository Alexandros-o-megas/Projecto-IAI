"""Rush Hour com vitória na borda direita e posições baseadas em zero."""
import json
from dataclasses import dataclass
from pathlib import Path
from problema import Problema


@dataclass(frozen=True)
class Veiculo:
    id: str
    orientacao: str
    comprimento: int
    fixa: int


@dataclass(frozen=True)
class Accao:
    veiculo: str
    deslocamento: int  # positivo: direita/baixo; negativo: esquerda/cima


def inteiro(valor):
    return type(valor) is int


class RushHour(Problema):
    def __init__(self, tamanho, veiculos, posicoes, obstaculos=(),
                 linha_saida=2, criterio="movimentos"):
        if not inteiro(tamanho) or not 2 <= tamanho <= 8:
            raise ValueError("Dimensão deve estar entre 2 e 8.")
        if criterio not in ("movimentos", "ponderado"):
            raise ValueError("Critério desconhecido.")
        if not inteiro(linha_saida) or not 0 <= linha_saida < tamanho:
            raise ValueError("Linha de saída inválida.")
        self.tamanho = tamanho
        self.veiculos = tuple(veiculos)
        self.criterio = criterio
        self.linha_saida = linha_saida
        ids = [v.id for v in self.veiculos]
        if any(not isinstance(i, str) or not i or i in (".", "#") for i in ids):
            raise ValueError("Identificador inválido.")
        if len(set(ids)) != len(ids) or "X" not in ids:
            raise ValueError("IDs devem ser únicos e incluir X.")
        self._indices = {v.id: i for i, v in enumerate(self.veiculos)}
        for v in self.veiculos:
            if (v.orientacao not in ("H", "V")
                    or not inteiro(v.comprimento) or v.comprimento not in (2, 3)
                    or not inteiro(v.fixa) or not 0 <= v.fixa < tamanho):
                raise ValueError("Metadados de veículo inválidos.")
        alvo = self.veiculos[self._indices["X"]]
        if alvo.orientacao != "H" or alvo.comprimento != 2 or alvo.fixa != linha_saida:
            raise ValueError("X deve ser horizontal, ter 2 casas e estar na saída.")
        celulas = tuple(tuple(o) for o in obstaculos)
        for o in celulas:
            if len(o) != 2 or any(not inteiro(n) or not 0 <= n < tamanho for n in o):
                raise ValueError("Obstáculo inválido.")
        if len(set(celulas)) != len(celulas):
            raise ValueError("Obstáculo repetido.")
        self.obstaculos = frozenset(celulas)
        self._inicial = tuple(posicoes)
        self.grelha(self._inicial)

    @classmethod
    def de_json(cls, ficheiro, criterio="movimentos"):
        with open(ficheiro, encoding="utf-8") as entrada:
            dados = json.load(entrada)
        veiculos = [Veiculo(v["id"], v["orientacao"], v["comprimento"], v["fixa"])
                    for v in dados["veiculos"]]
        return cls(dados["tamanho"], veiculos,
                   [v["posicao"] for v in dados["veiculos"]],
                   dados.get("obstaculos", ()), dados["linha_saida"], criterio)

    def estado_inicial(self):
        return self._inicial

    def grelha(self, s):
        if not isinstance(s, tuple) or len(s) != len(self.veiculos):
            raise ValueError("Estado deve ser uma tupla com uma posição por veículo.")
        grelha = [["." for _ in range(self.tamanho)] for _ in range(self.tamanho)]
        for linha, coluna in self.obstaculos:
            grelha[linha][coluna] = "#"
        for v, pos in zip(self.veiculos, s):
            if not inteiro(pos) or not 0 <= pos <= self.tamanho - v.comprimento:
                raise ValueError("Posição fora do tabuleiro.")
            for offset in range(v.comprimento):
                linha, coluna = (v.fixa, pos + offset) if v.orientacao == "H" else (pos + offset, v.fixa)
                if grelha[linha][coluna] != ".":
                    raise ValueError("Colisão entre veículos ou com obstáculo.")
                grelha[linha][coluna] = v.id
        return grelha

    def accoes(self, s):
        grelha = self.grelha(s)
        if self.e_objectivo(s):
            return []
        accoes = []
        for v, pos in zip(self.veiculos, s):
            for sentido in (-1, 1):
                distancia = 1
                while True:
                    frente = pos - distancia if sentido < 0 else pos + v.comprimento - 1 + distancia
                    if not 0 <= frente < self.tamanho:
                        break
                    linha, coluna = (v.fixa, frente) if v.orientacao == "H" else (frente, v.fixa)
                    if grelha[linha][coluna] != ".":
                        break
                    accoes.append(Accao(v.id, sentido * distancia))
                    distancia += 1
        return accoes

    def resultado(self, s, a):
        if not isinstance(a, Accao) or not inteiro(a.deslocamento) or a not in self.accoes(s):
            raise ValueError("Acção ilegal.")
        novo = list(s)
        novo[self._indices[a.veiculo]] += a.deslocamento
        return tuple(novo)

    def custo(self, s, a, s2):
        if self.resultado(s, a) != s2:
            raise ValueError("Estado sucessor incompatível.")
        if self.criterio == "movimentos":
            return 1
        return self.veiculos[self._indices[a.veiculo]].comprimento * abs(a.deslocamento)

    def e_objectivo(self, s):
        self.grelha(s)
        return s[self._indices["X"]] + 2 == self.tamanho

    def heuristica(self, s, nome="h0"):
        self.grelha(s)
        if nome == "h0":
            return 0
        raise NotImplementedError("h1/h2 dependem da implementação de Alex.")


def carregar_base(criterio="movimentos"):
    return RushHour.de_json(Path(__file__).parent / "instancias" / "base.json", criterio)
