# Projecto IA I — Grupo 06 (Laboral)

**P6 — “Engarrafamento na Baixa” (Rush Hour generalizado)**, com IDA* e tabela de transposição como algoritmo avançado.
Membros: Falaque, Dalton; Nhabinde, Alex; Nhabomba, Lino; Quive, Alexandre; Ricardo.
Semente do grupo: **202606**.

## Instalação

Requer Python 3.10 ou superior.

```sh
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Execução

```sh
python main.py                                            # menu interactivo
python main.py --alg astar --h h4 --criterio ponderado    # A* na instância base, passo a passo
python main.py --alg astar --h h4 --pausa 1 --animar      # animação: 1 s por passo, a cores
python main.py --instancia instancias/media_04.json --alg idastar --h h4 --sem-passos
python main.py --gerar pequena --alg bfs                  # gera uma instância com a semente e resolve-a

python -m pytest -q                                       # testes
python gerador.py --nivel todos                           # regenera instancias/{pequena,media,grande}_NN.json
python experiencias.py --workers 2                        # bateria completa (cerca de 2 h), CSV e gráficos
python experiencias.py --so-graficos                      # refaz resumos e gráficos a partir do CSV
python relatorio/gerar_relatorio.py                       # relatório .docx a partir dos resultados
```

Algoritmos (`--alg`): `bfs`, `dfs`, `ids`, `ucs`, `gulosa`, `astar`, `idastar` (com tabela de transposição) e `idastar_simples`.
Heurísticas (`--h`): `h0` (zero), `h1` (veículos a bloquear X), `h2` (h1 + bloqueadores dos bloqueadores), `h3` (h1 + movimento final de X) e `h4` (relaxação com cada veículo sozinho).
Visualização: o X aparece a vermelho, o veículo que acabou de mexer a amarelo, os camiões em negrito e os obstáculos `#` a cinzento. `--pausa S` espera S segundos entre passos; `--animar` limpa o ecrã a cada passo; `--sem-cor` desliga as cores.
Critérios (`--criterio`): `movimentos` (cada movimento custa 1) e `ponderado` (comprimento × casas).

## Estrutura

```text
problema.py         # classe abstracta Problema, No e caminho()
dominio.py          # RushHour(Problema): estado, acções, transição, custos e objectivo
buscas.py           # BFS, DFS, IDS, UCS, Gulosa, A*, IDA* (+ tabela de transposição)
heuristicas.py      # h0–h4, h* exacto, verificação de admissibilidade/consistência, b*
gerador.py          # instâncias por busca para trás a partir de objectivos (semente 202606)
experiencias.py     # bateria (60 s / 2 GB por execução), CSV, resumos e gráficos
main.py             # menu e demonstração
instancias/         # base.json + 10 pequenas, 10 médias e 10 grandes
tests/              # testes pytest
relatorio/          # template oficial e gerador do relatório
outputs/            # resultados.csv, resumo_*.csv, heuristicas.csv, gráficos, relatório
```

## Convenções (ver `CONTRATO_DOMINIO.md`)

- Coordenadas começam em zero. O estado é um tuplo com a posição de cada veículo, pela ordem do JSON: a coluna esquerda nos horizontais e a linha de cima nos verticais.
- Um movimento desloca um veículo k ≥ 1 casas livres. O objectivo é a casa direita de X atingir a borda direita da linha de saída.
- Instância base: 1079 estados alcançáveis. Óptimo de 8 movimentos ou custo ponderado 40; os dois critérios coincidem.

## Resultados principais

Ver `outputs/analise_base.txt`, `outputs/resumo_<nivel>_<criterio>.csv`, `outputs/heuristicas.csv`, `outputs/divergencia_criterios.csv`, `outputs/verificacao_heuristicas.csv` e `outputs/graficos/`.

## Colaboração

Seguir `CONTRIBUTING.md`: um ramo por tarefa e Pull Request para `main` após revisão.
