"""Secções 6.3, 6.4 e Capítulo 7, escritos a partir dos números reais (CSV)."""
import math

from capitulos import f, pct


def _res(E, nivel, crit, cfg):
    return E["res"].get((nivel, crit, cfg), (0, 0, float("nan"), float("nan")))


def _resolvidas(E, nivel, crit, cfg):
    ok, n, _, _ = _res(E, nivel, crit, cfg)
    return f"{ok}/{n}" if n else "—"


def escrever(w, R, D, E):
    m, p = R["movimentos"], R["ponderado"]
    w.h2("Análise e discussão")
    if not E:
        w.p("(Sem resultados: correr `python experiencias.py`.)")
        return
    df = E["df"]
    comum = E["comum"]
    tem_grande = E["n_inst"].get("grande", 0) > 0

    # --- completude e limites das não informadas
    w.p("**Completude e limites das buscas não informadas.** Nas instâncias pequenas todos os algoritmos "
        "terminam, como o enunciado exige. Nas médias (óptimo de 15 a 38 movimentos), DFS e IDS falham "
        f"por tempo em todas (DFS {_resolvidas(E, 'media', 'movimentos', 'dfs')}, IDS "
        f"{_resolvidas(E, 'media', 'movimentos', 'ids')}), embora as componentes tenham só 4 000–33 000 "
        "estados. A teoria explica-o: são buscas em árvore com controlo de ciclos apenas no caminho, e "
        "no ~Rush Hour~ o mesmo estado é alcançado por um número exponencial de ordens de movimentos "
        "(transposições), pelo que exploram O(b^d) nós e não O(|S|). Nas pequenas o IDS já expande em "
        f"média {f(_res(E, 'pequena', 'movimentos', 'ids')[2], 0)} nós, contra "
        f"{f(_res(E, 'pequena', 'movimentos', 'bfs')[2], 0)} da BFS, e na base (d = 8, b ≈ "
        f"{f(R['ramificacao'])}) excede 60 s. A BFS e o UCS, sendo buscas em grafo, resolvem todas as "
        "médias em poucos segundos, porque o número de estados distintos é pequeno.")
    if tem_grande:
        w.p(f"Nas instâncias grandes (componentes de 290 000 a 780 000 estados, óptimo de 15 a 36 "
            f"movimentos), a BFS resolveu {_resolvidas(E, 'grande', 'movimentos', 'bfs')} e o UCS "
            f"{_resolvidas(E, 'grande', 'ponderado', 'ucs')} no ponderado, contra "
            f"{_resolvidas(E, 'grande', 'ponderado', 'astar-h4')} do A* com h4 e "
            f"{_resolvidas(E, 'grande', 'ponderado', 'gulosa-h2')} da Gulosa (h2), enquanto DFS, IDS, IDA* simples "
            "e IDA*+TT não resolveram nenhuma. **Ao contrário do previsto no enunciado (“só as informadas "
            "terminam”), a BFS e o UCS ainda terminaram em todas as grandes**, com médias de "
            f"{f(_res(E, 'grande', 'movimentos', 'bfs')[3], 1)} s e "
            f"{f(_res(E, 'grande', 'ponderado', 'ucs')[3], 1)} s (máximo de 56 s no UCS). A razão é que só "
            "expandem os estados mais próximos do início do que a solução (em média "
            f"{f(_res(E, 'grande', 'movimentos', 'bfs')[2], 0)} na BFS), uma fracção pequena da componente. "
            "Para os fazer falhar seriam precisas componentes de vários milhões de estados, que o nosso "
            "gerador não consegue certificar por enumeração (Secção 7.2). Mesmo assim, a vantagem das "
            "informadas mantém-se: no ponderado, o A* com h4 expande "
            f"{pct(E['comum']('grande', 'ponderado', 'astar-h4', 'ucs')[0], 1)} dos nós do UCS e usa menos "
            "memória, e a Gulosa resolve em cerca de um terço do tempo, embora com custos até 27 % acima "
            "do óptimo.")

    # --- optimalidade
    bfs_p = _res(E, "media", "ponderado", "bfs")
    w.p("**Optimalidade.** UCS, A* (h0, h1, h3, h4) e IDA*+TT devolveram sempre o custo óptimo (Custo/óptimo "
        "= 1,000), confirmando a teoria (h1, h3 e h4 são consistentes). O A* com h2 foi óptimo em todas as "
        "instâncias menos uma: na `grande_05` (critério movimentos) devolveu uma solução de 31 movimentos, "
        "quando o óptimo é 30. É a confirmação experimental de que h2 não é admissível em movimentos "
        "(Secção 4.2): a sobrestimação fez o A* fechar o objectivo antes de expandir o caminho óptimo. No "
        "ponderado, onde provámos h2 ≤ h4 ≤ h*, o A* com h2 foi sempre óptimo. A BFS "
        "é óptima em movimentos, mas no critério ponderado o custo médio foi "
        f"{f(df[(df.nivel == 'pequena') & (df.criterio == 'ponderado') & (df.config == 'bfs') & df.ok].custo.sum() / max(1, df[(df.nivel == 'pequena') & (df.criterio == 'ponderado') & (df.config == 'ucs') & df.ok].custo.sum()), 3)} "
        "vezes o óptimo nas pequenas: minimiza acções e não custo. A DFS devolve soluções muito piores "
        f"(até {f(_res(E, 'pequena', 'movimentos', 'dfs')[2] and df[(df.nivel == 'pequena') & (df.criterio == 'movimentos') & (df.config == 'dfs') & df.ok].custo.max(), 0)} movimentos "
        "para óptimos de 6 a 8), porque segue o primeiro ramo até ao limite de 50. A Gulosa resolve "
        "depressa com poucos nós, mas sem óptimo (até ≈ 10 % acima nas médias, Figura 5).")

    # --- heurísticas
    r_h1, _ = comum("media", "movimentos", "astar-h1", "astar-h0")
    r_h4p, n4 = comum("media", "ponderado", "astar-h4", "ucs")
    r_h3p, _ = comum("media", "ponderado", "astar-h3", "ucs")
    w.p("**Heurísticas.** No critério movimentos, o A* com h1 expande em média "
        f"{pct(1 - r_h1, 1)} menos nós do que com h0 (UCS) nas médias, e h2/h3/h4 melhoram um pouco mais "
        "(Tabela 3). Os ganhos são modestos porque o ~Rush Hour~ tem poucos estados por nível de "
        "profundidade: muitos estados têm o mesmo f, e o que domina é o número de estados com f < C*. No "
        f"critério ponderado, h1–h3 quase não ajudam (A* h3 expande {pct(r_h3p, 1)} dos nós do UCS), "
        "porque contam acções (≈ 1 por veículo) enquanto o custo de cada acção vale 2 a 15. A h4 mede o "
        f"custo mínimo em casas × comprimento e expande {pct(r_h4p, 1)} dos nós do UCS nas médias "
        f"({n4} instâncias), e ainda menos nas pequenas e grandes. Isto confirma a regra de que uma "
        "heurística deve estar na mesma escala da função de custo.")

    # --- IDA*
    r_tt, n_tt = comum("pequena", "movimentos", "idastar-h4", "idastar_simples-h4")
    r_ttp, _ = comum("pequena", "ponderado", "idastar-h4", "idastar_simples-h4")
    mem_a = _res(E, "media", "movimentos", "astar-h4")
    w.p("**IDA* e tabela de transposição.** A tabela de transposição reduziu os nós expandidos do IDA* "
        f"para {pct(r_tt, 1)} (movimentos) e {pct(r_ttp, 1)} (ponderado) dos do IDA* simples nas "
        f"pequenas (Figura 6, exigência específica 3), e o IDA* simples não resolveu nenhuma média, "
        f"enquanto o IDA*+TT resolveu {_resolvidas(E, 'media', 'movimentos', 'idastar-h4')} em movimentos. "
        "Mesmo assim, o IDA* expande mais nós do que o A*: repete as iterações (uma por valor distinto "
        "de f) e a tabela é limpa em cada uma. No critério ponderado o número de iterações aumenta "
        "(f toma muitos valores), e por isso resolve menos instâncias "
        f"({_resolvidas(E, 'media', 'ponderado', 'idastar-h4')} médias). A vantagem do IDA* é a "
        f"memória: nas médias usou em média {f(_res(E, 'media', 'movimentos', 'idastar-h4')[2] and df[(df.nivel == 'media') & (df.criterio == 'movimentos') & (df.config == 'idastar-h4') & df.ok].memoria_mb.mean(), 2)} MB, "
        f"contra {f(df[(df.nivel == 'media') & (df.criterio == 'movimentos') & (df.config == 'astar-h4') & df.ok].memoria_mb.mean(), 2)} MB do A*, "
        "apesar de também guardar a tabela de uma iteração.")
    w.p("**Recomendação.** Para este problema recomendamos o A* em grafo com h4 (igual a h3 em movimentos): "
        "é óptimo nos dois critérios, é o que resolve mais instâncias e expande menos nós entre os "
        "algoritmos óptimos. O IDA*+TT só se justifica se a memória for o limite (tabuleiros 8×8 muito "
        "abertos) e com o critério movimentos. A BFS chega para minimizar movimentos em instâncias até "
        "dezenas de milhares de estados. A Gulosa é útil quando basta uma solução rápida, sem garantia de "
        "óptimo.")
    w.p("**Os dois critérios** (exigência específica 1). Na base, os óptimos coincidem: 8 movimentos e "
        f"custo 40, e a solução de mínimo de movimentos ({R['sol_mov']}) também tem custo ponderado "
        f"{R['div_base'][1]}. Coincidem porque a solução óptima move cada veículo uma única vez, pelo "
        "deslocamento mínimo necessário, e na base não há forma de poupar casas acrescentando "
        "movimentos. Com o gerador encontrámos instâncias em que os critérios diferem de facto. Para não "
        "depender de desempates, calculámos sobre o grafo completo o menor custo ponderado entre TODAS as "
        "soluções de mínimo de movimentos (`heuristicas.divergencia`):")
    div = D.get("divergencia_criterios.csv")
    if div is not None:
        linhas = [[r.instancia, r.min_movimentos, r.melhor_ponderado_com_min_movimentos, r.optimo_ponderado,
                   r.movimentos_do_optimo_ponderado] for r in div[div.diferem].itertuples()]
        w.tabela("Instâncias em que os dois critérios de optimização divergem",
                 ["Instância", "Mín. movimentos", "Melhor custo ponderado com mín. movimentos",
                  "Óptimo ponderado", "Movimentos do óptimo ponderado"], linhas, tamanho=8.5)
        w.p(f"Em {len(linhas)} das {len(div)} instâncias analisadas (base, pequenas e médias), nenhuma "
            "solução com o número mínimo de movimentos é óptima no custo ponderado: por exemplo, na "
            "`pequena_02` o mínimo são 7 movimentos, mas o melhor dessas soluções custa 24, enquanto o "
            "óptimo ponderado, 21, precisa de 8 movimentos (mover um carro em vez de um camião, ou "
            "deslocar um veículo menos casas com um movimento extra). Assim, a BFS (óptima em movimentos) "
            "deixa de ser óptima no custo ponderado, como se vê na coluna Custo/óptimo da BFS nas tabelas "
            "do critério ponderado.")

    w.h2("Resposta à pergunta de análise")
    w.p("~Qual é o número de estados alcançáveis na instância base, e que fracção deles o A* com h2 "
        "expande?~")
    a2m, a2p = m["astar-h2"], p["astar-h2"]
    w.p(f"Uma BFS exaustiva a partir de s0 (função `espaco_alcancavel`) encontra **{m['estados']} estados "
        f"alcançáveis** na base (4 deles objectivos e {f(m['transicoes'])} transições), num limite teórico "
        f"de 160 000 configurações sem colisões. O A* com h2 expande **{a2m.expandidos} nós no critério "
        f"movimentos, isto é, {pct(a2m.expandidos, m['estados'])} dos estados alcançáveis**, contra "
        f"{m['astar-h1'].expandidos} ({pct(m['astar-h1'].expandidos, m['estados'])}) com h1, "
        f"{m['astar-h4'].expandidos} ({pct(m['astar-h4'].expandidos, m['estados'])}) com h3/h4 e "
        f"{m['ucs-None'].expandidos} ({pct(m['ucs-None'].expandidos, m['estados'])}) com h0/UCS. "
        f"No critério ponderado, o A* com h2 expande {a2p.expandidos} nós "
        f"({pct(a2p.expandidos, p['estados'])}): h2 conta veículos e é demasiado pequena face a custos "
        f"de 2 a 9 por acção, enquanto h4 reduz para {p['astar-h4'].expandidos} "
        f"({pct(p['astar-h4'].expandidos, p['estados'])}). Os valores são verificados pelos testes "
        "(`test_hstar_base`) e reproduzem-se com `python experiencias.py` (`outputs/analise_base.txt`). "
        f"Em ambos os casos o custo encontrado é o óptimo ({m['optimo']} movimentos; custo {p['optimo']}).")
    w.p("A fracção é alta porque o espaço da base é pequeno e muito ligado: a solução óptima exige "
        "mover 7 dos 8 veículos, logo grande parte dos estados tem f ≤ C*. A h2 expande menos do que "
        "h3/h4 em movimentos porque é, em média, maior, mas o preço é a perda da garantia de optimalidade "
        "(contra-exemplo da Secção 4.2).")


def conclusoes(w, R, D, E):
    m, p = R["movimentos"], R["ponderado"]
    w.h1("CONCLUSÕES")
    w.h2("Síntese")
    w.p("Retomando os objectivos específicos:")
    w.lista([f"**Formular o problema** — atingido. O estado é um tuplo imutável de posições (suficiente e "
             f"mínimo), as acções são deslocamentos de k casas e há dois custos (Capítulo 3). A base tem "
             f"{m['estados']} estados alcançáveis e óptimos de {m['optimo']} movimentos e custo {p['optimo']}.",
             "**Implementar os sete algoritmos** — atingido. BFS, DFS, IDS, UCS, Gulosa, A* e IDA* com tabela "
             "de transposição sobre uma interface genérica, verificados pelos testes automáticos "
             f"({D['testes']}).",
             "**Heurísticas e provas** — atingido. h1, h3 e h4 são admissíveis e consistentes (provas e "
             "verificação exaustiva); a dica h2 é inadmissível em movimentos (contra-exemplo h2 = 4 > h* = 3) "
             "e admissível no ponderado (h2 ≤ h4).",
             "**Gerador reprodutível** — atingido. 30 instâncias com a semente 202606 e óptimo certificado, "
             "≥ 15 movimentos nas médias e grandes, incluindo instâncias onde os dois critérios divergem.",
             "**Comparação experimental** — atingido. Os resultados confirmam a teoria: completude e "
             "optimalidade dos algoritmos óptimos, explosão de DFS/IDS em árvore, vantagem do A*+h4 e "
             "redução de nós do IDA* pela tabela de transposição."], numerada=True)
    w.h2("Limitações")
    w.lista(["Nas instâncias pequenas o mínimo de 15 movimentos foi substituído pelo maior óptimo que "
             "DFS e IDS resolvem (6 a 8 movimentos), porque as duas exigências são incompatíveis com "
             "DFS/IDS de controlo de ciclos só no caminho (Secção 5.4).",
             "Os tempos foram medidos com `tracemalloc` activo e com 2 a 3 execuções em paralelo, num "
             "portátil; os valores absolutos são indicativos, mas as contagens de nós são exactas e "
             "determinísticas.",
             "A implementação é em Python puro (≈ 10⁴ expansões/s); com o limite de 60 s, isso define a "
             "fronteira entre resolvido e falhou nas instâncias grandes.",
             "A h2 do enunciado não é admissível em movimentos; os resultados com h2 nesse critério não "
             "têm garantia de óptimo, e numa instância grande (grande_05) o resultado não foi óptimo.",
             "As instâncias grandes (290 000 a 780 000 estados) não chegaram para esgotar o tempo da BFS e do "
             "UCS (só DFS, IDS e IDA* falharam): o gerador certifica o óptimo enumerando toda a componente, "
             "o que limita as grandes a menos de 10⁶ estados com a memória disponível (cerca de 3 GB)."])
    w.h2("Trabalho futuro")
    w.lista(["Heurística por base de dados de padrões (pattern database) para o grupo de veículos à frente "
             "de X, que capture interacções entre bloqueadores, com prova de admissibilidade.",
             "Representação em bits (bitboards) e geração incremental de acções para multiplicar a "
             "velocidade por 10–50 e resolver componentes de milhões de estados.",
             "Busca bidireccional e IDA* com tabela de transposição persistente entre iterações (com "
             "limites guardados) para reduzir as re-expansões no critério ponderado."])
