# Projecto IA I - Grupo 06

Implementação do problema P6, “Engarrafamento na Baixa” (Rush Hour generalizado), para o Projecto Prático de Inteligência Artificial I 2026.

## Preparar o ambiente

- Python 3.10 ou superior.
- Para executar testes: `python -m pip install -r requirements.txt`.
- Clonar o repositório partilhado e criar um ramo para cada tarefa.

```powershell
git clone <URL_DO_REPOSITORIO>
cd projecto-ia-grupo06
git switch -c feature/nome/tarefa
```

## Estrutura

```text
dominio.py          # representação e regras do P6
problema.py         # interface Problema, No e caminho
buscas.py           # BFS, DFS, IDS, UCS, Gulosa, A* e IDA*
heuristicas.py      # heurísticas, provas e apoio
gerador.py          # instâncias reproduzíveis (semente do Grupo 06: 202606)
experiencias.py     # experiências, métricas, CSV e gráficos
main.py             # menu e demonstração
instancias/         # puzzles JSON
tests/              # testes pytest
outputs/            # relatório, resultados e gráficos da entrega
```

## Colaboração

Seguir `CONTRIBUTING.md` e o sprint em `outputs/Grupo_06_Sprint_Scrum_6_Dias.pdf`. Actualizar o quadro `outputs/Grupo_06_Quadro_Sprint.xlsx` no daily. Cada pessoa trabalha num ramo próprio; integrar alterações na `main` após revisão de outro membro. Não fazer push directamente para `main`.

## Enunciado e critérios

O problema é P6. A especificação oficial define os sete algoritmos, o IDA* com tabela de transposição, as duas funções de custo, heurísticas, gerador, experiências e entregáveis. Antes de implementar, acordar em equipa as convenções de saída do chapa e o que conta como um movimento, e registar essa decisão.

## Estado

Este repositório contém o esqueleto de colaboração e os materiais de planeamento. As pastas de implementação estão inicialmente vazias; preencher cada componente em ramos separados e integrar progressivamente.
