"""Contrato genérico para algoritmos de busca."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class Problema(ABC):
    @abstractmethod
    def estado_inicial(self): ...

    @abstractmethod
    def accoes(self, s): ...

    @abstractmethod
    def resultado(self, s, a): ...

    @abstractmethod
    def custo(self, s, a, s2): ...

    @abstractmethod
    def e_objectivo(self, s): ...

    @abstractmethod
    def heuristica(self, s, nome): ...


@dataclass
class No:
    estado: Any
    pai: "No | None" = None
    accao: Any = None
    g: float = 0
    profundidade: int = 0


def caminho(no):
    """Lista de nós da raiz ao destino, incluindo ambos."""
    nos = []
    while no is not None:
        nos.append(no)
        no = no.pai
    return list(reversed(nos))
