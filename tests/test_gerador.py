"""Gerador: reprodutível com a semente e óptimo certificado."""
import json
from pathlib import Path

from buscas import executar
from dominio import RushHour
from gerador import SEMENTE, gerar


def test_reprodutivel_com_a_semente():
    a = gerar("pequena", 2, SEMENTE)
    b = gerar("pequena", 2, SEMENTE)
    assert [(q.veiculos, q.estado_inicial()) for q, _, _ in a] == \
           [(q.veiculos, q.estado_inicial()) for q, _, _ in b]


def test_optimo_certificado_e_reaberto_do_json(tmp_path):
    q, d, _ = gerar("pequena", 1, SEMENTE)[0]
    f = tmp_path / "x.json"
    f.write_text(json.dumps(q.para_dict()), encoding="utf-8")
    p = RushHour.de_json(f)
    assert p.estado_inicial() == q.estado_inicial()
    assert executar("bfs", p).comprimento == d


def test_instancias_gravadas_cumprem_o_minimo():
    for f in sorted(Path("instancias").glob("*_*.json")):
        dados = json.loads(f.read_text(encoding="utf-8"))
        meta = dados["meta"]
        minimo = 15 if meta["nivel"] in ("media", "grande") else 6
        assert meta["optimo_movimentos"] >= minimo, f
        assert meta["semente"] == SEMENTE
