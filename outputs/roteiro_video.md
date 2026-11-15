# Guião do vídeo — Grupo 06, P6 “Engarrafamento na Baixa”

O vídeo substitui a defesa. Duração alvo de 12 a 15 min, em MP4. **Cada membro fala na sua parte.**
Gravar o ecrã (OBS Studio ou `ffmpeg -f x11grab`) com o terminal em letra grande. Antes de gravar: `source .venv/bin/activate`.

| # | Tempo | Quem | O que mostrar e dizer |
|---|-------|------|------------------------|
| 1 | 0:00–1:00 | Ricardo | Apresentação do grupo, do problema P6 e do algoritmo avançado (IDA* com tabela de transposição). Mostrar a estrutura do repositório (`ls`, `README.md`). |
| 2 | 1:00–3:00 | Lino | Formulação: o estado é um tuplo de posições (`dominio.py`, `para_dict`, `grelha`). Acções `Accao(veiculo, deslocamento)`, custos (movimentos / ponderado), teste de objectivo. Correr `python -m pytest -q tests/test_dominio.py`. Mostrar a base: 1079 estados alcançáveis. |
| 3 | 3:00–5:00 | Dalton | Buscas não informadas (`buscas.py`): BFS com teste na geração, DFS com controlo de ciclos e limite, IDS com re-expansões, UCS com `heapq` e entradas obsoletas. Demonstração: `python main.py --alg bfs` (passo a passo) e `python main.py --alg ids --tempo 10`, que excede o tempo na base: explicar porquê (b ≈ 11, d = 8). |
| 4 | 5:00–7:30 | Alex | Heurísticas (`heuristicas.py`): h1–h4, prova de admissibilidade de h4 e o contra-exemplo de h2 (`tests/contra_exemplo_h2.py`, h2 = 4 > h* = 3). Correr `python -m pytest -q tests/test_heuristicas.py`. Demonstração animada: `python main.py --alg astar --h h4 --criterio ponderado --pausa 1 --animar`. Comparar com `--alg ucs` (mesmo custo, 40; menos nós). |
| 5 | 7:30–10:00 | Alexandre | IDA* e tabela de transposição (`idastar` em `buscas.py`): explicar a poda `visto <= g` e a limpeza por iteração. Demonstração numa instância grande: `python main.py --instancia instancias/grande_01.json --alg idastar --h h4 --sem-passos` e o mesmo com `--alg idastar_simples` (mais nós). Gerador: `python main.py --gerar pequena --alg astar --h h3`. |
| 6 | 10:00–13:00 | Ricardo | Experiências: `outputs/resumo_*.csv` e os gráficos em `outputs/graficos/` (nós vs. tamanho, tempo vs. tamanho, custo vs. óptimo, IDA* vs. IDA*+TT). Resposta à pergunta de análise: 1079 estados; fracção expandida pelo A* com h2 (`outputs/analise_base.txt`). A instância `pequena_02`, em que os critérios divergem. |
| 7 | 13:00–14:00 | Todos | Conclusões, limitações e declaração de uso de IA (Anexo A do relatório). |

Valores a dizer na demonstração (instância base): óptimo de **8 movimentos** e **custo ponderado 40**; os dois critérios coincidem. Ver `outputs/analise_base.txt` para os nós expandidos.

Entrega no Vula: relatório PDF, vídeo MP4 (ou link do Google Drive com acesso para os docentes) e link do repositório ou o ZIP `IA_PROJECTO_GRUPO_06_LAB.zip` criado por `scripts/empacotar.sh`.
