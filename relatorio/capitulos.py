"""Texto do relatório. R = factos calculados na instância base; D = CSV das experiências."""
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOMES = {"bfs": "BFS", "dfs": "DFS", "ids": "IDS", "ucs": "UCS", "gulosa": "Gulosa", "astar": "A*",
         "idastar": "IDA*+TT", "idastar_simples": "IDA* simples"}
NIVEL = {"pequena": "pequenas", "media": "médias", "grande": "grandes", "base": "base"}


def f(x, casas=1):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    if isinstance(x, float) and x.is_integer() and casas == 0:
        return f"{int(x):,}".replace(",", " ")
    if isinstance(x, (int,)) or (isinstance(x, float) and abs(x) >= 1000):
        return f"{x:,.0f}".replace(",", " ")
    return f"{x:.{casas}f}".replace(".", ",")


def pct(a, b):
    return f"{100 * a / b:.1f}".replace(".", ",") + " %"


# ======================================================================= estatísticas
def estat(D):
    """Números agregados usados no resumo, discussão e conclusões."""
    df = D.get("resultados.csv")
    E = {}
    if df is None:
        return E
    df = df.copy()
    df["ok"] = df.estado == "ok"
    df["config"] = df.algoritmo + df.heuristica.map(lambda h: "" if h == "—" else "-" + h)
    E["df"] = df
    E["n_inst"] = {n: df[df.nivel == n].instancia.nunique() for n in ("pequena", "media", "grande")}
    E["execucoes"] = len(df)
    E["falhas"] = int((~df.ok).sum())
    res = {}
    for (nivel, crit, cfg), g in df.groupby(["nivel", "criterio", "config"]):
        res[(nivel, crit, cfg)] = (int(g.ok.sum()), len(g), g.loc[g.ok, "expandidos"].mean(),
                                   g.loc[g.ok, "tempo_s"].mean())
    E["res"] = res

    def comum(nivel, crit, a, b):
        """razão média de expandidos a/b nas instâncias resolvidas por ambos"""
        s = df[(df.nivel == nivel) & (df.criterio == crit)]
        A = s[(s.config == a) & s.ok].set_index("instancia").expandidos
        B = s[(s.config == b) & s.ok].set_index("instancia").expandidos
        i = A.index.intersection(B.index)
        return (A[i] / B[i]).mean() if len(i) else float("nan"), len(i)
    E["comum"] = comum
    return E


# ======================================================================= resumo
def resumo(R, D):
    E = estat(D)
    m, p = R["movimentos"], R["ponderado"]
    base = (f"Este relatório formula como problema de busca o P6, “Engarrafamento na Baixa”, uma "
            f"generalização do puzzle Rush Hour em que o chapa X tem de sair de um parque congestionado "
            f"pela saída à direita, com tabuleiros M×M até 8×8, obstáculos fixos e dois critérios de "
            f"optimização: número de movimentos e custo ponderado (comprimento × casas). O estado é um "
            f"tuplo imutável com a posição de cada veículo. Implementámos de raiz BFS, DFS, IDS, Custo "
            f"Uniforme, Gulosa, A* e IDA* com tabela de transposição sobre uma interface genérica, quatro "
            f"heurísticas (h1–h4) e um gerador de instâncias por busca para trás com a semente 202606. "
            f"Na instância base, com {m['estados']} estados alcançáveis, o óptimo é de {m['optimo']} "
            f"movimentos e custo ponderado {p['optimo']}, e os dois critérios coincidem; o gerador "
            f"encontrou uma instância em que nenhuma solução de mínimo de movimentos é óptima no custo "
            f"ponderado. Provámos que a dica h2 não é admissível em movimentos (contra-exemplo com h2 = 4 "
            f"e h* = 3), mas é admissível no custo ponderado. ")
    if E:
        r_a, n_a = E["comum"]("media", "ponderado", "astar-h4", "ucs")
        r_t, n_t = E["comum"]("media", "movimentos", "idastar-h4", "idastar_simples-h4")
        base += (f"Nas instâncias médias, o A* com h4 expandiu em média {pct(1 - r_a, 1)} menos nós do que "
                 f"o UCS no custo ponderado, e a tabela de transposição reduziu os nós do IDA* em "
                 f"{pct(1 - r_t, 1)}. ")
    base += ("Concluímos que, para este problema, o A* com uma heurística consistente derivada de um "
             "problema relaxado é a melhor escolha e que BFS/DFS/IDS só são viáveis em instâncias pequenas.")
    return base


# ======================================================================= capítulos
def escrever(w, R, D, GRAF):
    E = estat(D)
    introducao(w, R)
    revisao(w)
    formulacao(w, R)
    heuristicas(w, R, D)
    implementacao(w, R, D, GRAF)
    experiencias(w, R, D, E, GRAF)
    conclusoes(w, R, D, E)
    referencias(w)
    anexos(w)


def introducao(w, R):
    w.h1("INTRODUÇÃO")
    w.h2("Contextualização do problema")
    w.p("Na Baixa de Maputo, os parques de estacionamento junto aos terminais de chapas enchem-se nas "
        "horas de ponta. Quando um chapa precisa de sair, é frequente ter de pedir a vários condutores que "
        "desloquem os seus veículos, numa ordem que nem sempre é evidente: mover primeiro o veículo errado "
        "pode bloquear a saída ainda mais. O problema atribuído ao Grupo 06 (P6) modela esta situação como "
        "uma generalização do puzzle ~Rush Hour~: num parque representado por uma grelha, cada veículo "
        "ocupa duas casas (carros) ou três (camiões), só se desloca na sua orientação e não pode atravessar "
        "outros veículos nem obstáculos fixos, como um carro da polícia estacionado. O objectivo é tirar o "
        "chapa X pela saída à direita da linha 3.")
    w.p("O problema é difícil porque o número de configurações cresce exponencialmente com o número de "
        "veículos e o ~Rush Hour~ generalizado é PSPACE-completo (Flake & Baum, 2002). Resolver bem significa "
        "encontrar a sequência com o menor número de movimentos (menos pedidos aos condutores) ou com o "
        "menor esforço total, se mover um camião custar mais do que mover um carro. Estes dois critérios "
        "nem sempre levam à mesma solução, e o grupo mostra-o experimentalmente.")
    w.h2("Objectivos")
    w.h3("Objectivo geral")
    w.p("Modelar o problema P6 como problema de busca no espaço de estados e comparar, teórica e "
        "experimentalmente, sete estratégias de busca na sua resolução.")
    w.h3("Objectivos específicos")
    w.lista(["Formular o problema (estado, acções, transição, custo e objectivo) com uma representação "
             "compacta, imutável e ~hashable~, para os dois critérios de optimização;",
             "Implementar de raiz BFS, DFS, IDS, Custo Uniforme, Gulosa, A* e IDA* com tabela de "
             "transposição sobre uma interface genérica;",
             "Propor heurísticas, provar (ou refutar) a sua admissibilidade e consistência e verificá-las "
             "automaticamente em todos os estados de instâncias pequenas;",
             "Construir um gerador reprodutível (semente 202606) de puzzles com solução óptima certificada;",
             "Comparar os algoritmos em três níveis de instâncias e interpretar os resultados à luz da teoria."],
            numerada=True)
    w.h2("Metodologia de trabalho do grupo")
    w.p("O grupo organizou o trabalho num sprint de seis dias (9 a 14 de Novembro de 2026), com um quadro "
        "de 35 tarefas (S01–S35) e um responsável por tarefa, documentado em "
        "`outputs/Grupo_06_Sprint_Scrum_6_Dias.pdf` e `outputs/Grupo_06_Quadro_Sprint.xlsx`. O código está "
        "num repositório Git partilhado (`Alexandros-o-megas/Projecto-IAI`), com um ramo por tarefa "
        "(por exemplo `feature/lino/S02-S03-S09-S10`) integrado na `main` por ~pull request~ após revisão "
        "de outro membro. Primeiro fechou-se o contrato do domínio (`CONTRATO_DOMINIO.md`: convenção de "
        "saída, o que conta como movimento e custos), depois a interface comum e só então as buscas, "
        "heurísticas, gerador e experiências. A contribuição de cada membro está no Anexo B.")
    w.h2("Estrutura do relatório")
    w.p("O Capítulo 2 resume a teoria de busca usada. O Capítulo 3 formula o P6 como problema de busca. O "
        "Capítulo 4 define as heurísticas, com as provas de admissibilidade e consistência. O Capítulo 5 "
        "descreve a implementação, o gerador e os testes. O Capítulo 6 apresenta o desenho experimental, "
        "os resultados e a resposta à pergunta de análise. O Capítulo 7 conclui. Os anexos contêm a "
        "declaração de uso de IA, as contribuições e excertos de código.")


def revisao(w):
    w.h1("REVISÃO TEÓRICA")
    w.h2("Problemas de busca e espaço de estados")
    w.p("Um problema de busca é definido por um conjunto de estados S, um estado inicial s0, uma função "
        "ACÇÕES(s) com as acções aplicáveis em s, um modelo de transição RESULTADO(s, a), um custo de "
        "acção c(s, a, s′) > 0 e um teste de objectivo (Russell & Norvig, 2021, cap. 3). Uma solução é uma "
        "sequência de acções de s0 até um estado objectivo, e é óptima se tiver o menor custo de caminho "
        "g. Os estados e as transições formam um grafo (o espaço de estados); a busca constrói uma árvore "
        "de nós, em que cada nó guarda o estado, o pai, a acção, g e a profundidade. A ~busca em árvore~ "
        "pode gerar o mesmo estado muitas vezes; a ~busca em grafo~ guarda um conjunto de estados "
        "alcançados ou fechados para o evitar, à custa de memória. As estratégias comparam-se pela "
        "completude (encontra uma solução se existir), optimalidade (encontra a de menor custo) e "
        "complexidade em tempo e espaço, expressas em função do factor de ramificação b, da profundidade "
        "d da solução mais rasa, da profundidade máxima m e do custo óptimo C*.")
    w.h2("Estratégias de busca não informada")
    w.p("A **BFS** expande por níveis com uma fila FIFO; com teste de objectivo na geração encontra a "
        "solução com menos acções, que só é óptima quando todos os custos são iguais. A **DFS** expande "
        "o nó mais profundo (pilha LIFO); usa pouca memória, mas não é completa sem controlo de ciclos e "
        "não é óptima. O **IDS** repete DFS com limite 0, 1, 2, …, juntando a memória linear da DFS à "
        "completude e optimalidade (custos unitários) da BFS, à custa de re-expandir os níveis "
        "superiores. A **Custo Uniforme (UCS)** expande o nó de menor g com uma fila de prioridade e é "
        "óptima para custos positivos (Dijkstra, 1959).")
    w.tabela("Propriedades das estratégias de busca",
             ["Algoritmo", "Completo?", "Óptimo?", "Tempo", "Espaço"],
             [["BFS", "Sim (b finito)", "Só com custos iguais", "O(b^d)", "O(b^d)"],
              ["DFS", "Não (sim em grafo finito com controlo de ciclos e limite ≥ d)", "Não", "O(b^m)", "O(bm)"],
              ["IDS", "Sim", "Só com custos iguais", "O(b^d)", "O(bd)"],
              ["UCS", "Sim (custos ≥ ε > 0)", "Sim", "O(b^(1+⌊C*/ε⌋))", "O(b^(1+⌊C*/ε⌋))"],
              ["Gulosa", "Em grafo finito sim; em árvore não", "Não", "O(b^m)", "O(b^m)"],
              ["A*", "Sim", "Sim (h admissível; consistente em grafo)", "Exponencial no erro de h", "O(b^d)"],
              ["IDA* (+TT)", "Sim", "Sim (h admissível)", "O(b^d) por iteração; nº de iterações = valores f distintos",
               "O(bd) (+ tabela)"]],
             larguras=[2.3, 4.2, 3.4, 3.2, 2.8])
    w.h2("Estratégias de busca informada e heurísticas")
    w.p("A busca informada usa uma função heurística h(n), que estima o custo de n até ao objectivo. A "
        "**Gulosa** expande o nó de menor h: é rápida mas não óptima. O **A*** expande o nó de menor "
        "f(n) = g(n) + h(n) (Hart, Nilsson & Raphael, 1968). Uma heurística é **admissível** se "
        "h(n) ≤ h*(n) para todo n, em que h* é o custo óptimo real; é **consistente** se "
        "h(n) ≤ c(n, a, n′) + h(n′) para toda a transição e h(objectivo) = 0. Consistência implica "
        "admissibilidade e garante que o A* em grafo nunca precisa de reabrir nós fechados. Se "
        "h1(n) ≤ h2(n) para todo n, h2 **domina** h1 e o A* com h2 nunca expande mais nós (salvo "
        "desempates). A qualidade mede-se pelo **factor de ramificação efectivo b***, que satisfaz "
        "N + 1 = 1 + b* + (b*)² + … + (b*)^d para N nós expandidos e solução de profundidade d. Boas "
        "heurísticas obtêm-se como custo exacto de um **problema relaxado** (com menos restrições) ou de "
        "bases de dados de padrões (Culberson & Schaeffer, 1998).")
    w.h2("Algoritmo avançado atribuído")
    w.p("O **IDA*** (Korf, 1985) é o equivalente do IDS para busca informada: faz DFS em que um nó é "
        "cortado quando f = g + h excede um limite; o limite inicial é h(s0) e, em cada nova iteração, "
        "passa a ser o menor f que excedeu o limite anterior. Com h admissível, a primeira solução "
        "encontrada é óptima, e a memória é linear na profundidade, ao contrário do A*, que guarda todos "
        "os nós gerados. O preço é re-expandir os mesmos nós em cada iteração e, sobretudo, não detectar "
        "transposições: no ~Rush Hour~, o mesmo estado é alcançado por muitas ordens de movimentos "
        "diferentes, e o IDA* simples explora cada uma delas.")
    w.p("A **tabela de transposição** (TT) (Reinefeld & Marsland, 1994) guarda, durante uma iteração, o "
        "menor g com que cada estado foi visitado. Se um estado reaparece com g′ ≥ g guardado, a subárvore "
        "pode ser podada: na primeira visita foi explorada com folga (limite − g) maior ou igual, logo não "
        "contém nenhuma solução dentro do limite que a segunda visita pudesse encontrar, e os valores f "
        "que excederam o limite já foram registados para o limite seguinte. A tabela é limpa no início de "
        "cada iteração (com um limite maior, uma subárvore cortada antes pode ter agora uma solução). O "
        "pseudocódigo implementado é:")
    w.codigo("""limite ← h(s0)
repetir:
    TT ← {}                                   # limpa em cada iteração
    (sol, novo) ← DFS(raiz, limite)
    se sol: devolver sol      senão se novo = ∞: devolver falha
    limite ← novo                              # menor f > limite

DFS(n, limite):
    f ← g(n) + h(n);  se f > limite: devolver (nada, f)
    se objectivo(n): devolver (n, f)
    se TT[n.estado] ≤ g(n): devolver (nada, ∞) # transposição já explorada
    TT[n.estado] ← g(n)
    para cada filho n′ fora do caminho actual, por ordem de f crescente:
        (sol, t) ← DFS(n′, limite);  se sol: devolver sol;  mínimo ← min(mínimo, t)
    devolver (nada, mínimo)""")
    w.p("O IDA* é indicado quando a memória é o recurso limitante, os custos tomam poucos valores "
        "distintos (cada valor distinto de f obriga a uma iteração) e a heurística é boa. Com custos "
        "variados (como o custo ponderado) o número de iterações aumenta, o que é visível nos resultados.")
    w.h2("Abordagens alternativas e trabalhos relacionados")
    w.p("O ~Rush Hour~ clássico (6×6) foi resolvido de forma exaustiva: Collette, Raskin & Servais (2006) "
        "enumeraram todas as configurações e identificaram os puzzles mais difíceis (93 movimentos no "
        "critério de movimentos de um veículo de várias casas), usando BFS para trás a partir dos "
        "objectivos, a mesma ideia do nosso gerador. Em geral, o problema é PSPACE-completo (Flake & Baum, "
        "2002), pelo que não se espera um algoritmo polinomial. Alternativas à busca no espaço de estados "
        "são a formulação como planeamento clássico (PDDL) resolvida por planeadores com heurísticas "
        "independentes do domínio, a satisfação de restrições/SAT com horizonte limitado e as "
        "metaheurísticas (algoritmos genéticos, ~simulated annealing~), que encontram soluções mas sem "
        "garantia de optimalidade. Para tabuleiros até 8×8, a busca heurística óptima (A*/IDA*) é a "
        "escolha adequada: os espaços alcançáveis são da ordem de 10³ a 10⁶ estados e precisamos de "
        "soluções óptimas para os dois critérios.")


def formulacao(w, R):
    m = R["movimentos"]
    w.h1("FORMULAÇÃO DO PROBLEMA DE BUSCA")
    w.h2("Descrição do problema e pressupostos")
    w.p("O parque é uma grelha n×n (2 ≤ n ≤ 8; base 6×6) com uma saída na borda direita da linha de "
        "saída r (na base, a linha 3, índice 2 a contar de zero). Cada veículo tem identificador, "
        "orientação (H ou V), comprimento 2 ou 3 e linha (H) ou coluna (V) fixa. Os obstáculos (veículos "
        "da polícia) ocupam casas fixas. Pressupostos, registados em `CONTRATO_DOMINIO.md`:")
    w.lista(["coordenadas a contar de zero; X é horizontal, tem 2 casas e está na linha de saída;",
             "**o objectivo é X tocar a borda direita** (a sua casa direita na última coluna); a saída "
             "física não é uma acção adicional, porque custaria o mesmo em todas as soluções;",
             "**um movimento** desloca um único veículo k ≥ 1 casas livres na sua orientação; todas as "
             "casas atravessadas têm de estar livres (não há saltos);",
             "os estados objectivo são terminais (não têm acções);",
             "os obstáculos são imóveis e nunca estão à frente de X na linha de saída em instâncias geradas "
             "(isso tornaria o puzzle impossível);",
             "dois critérios: **movimentos** (cada acção custa 1) e **ponderado** (L × k, em que L é o "
             "comprimento do veículo: os camiões gastam mais)."])
    w.p("Os dados são os do enunciado (instância base) ou gerados pelo `gerador.py` com a semente do "
        "grupo, 2026 × 100 + 6 = 202606; não foram usados dados externos.")
    w.h2("Representação do estado")
    w.p("Separa-se o que muda do que é fixo. A parte fixa (tamanho, linha de saída, obstáculos e, para cada "
        "veículo, `Veiculo(id, orientacao, comprimento, fixa)` como `dataclass(frozen=True)`) fica no "
        "objecto `RushHour`. O **estado** é apenas um `tuple` de inteiros, com uma posição por veículo, "
        "pela ordem do JSON: a coluna mais à esquerda nos horizontais e a linha de cima nos verticais.")
    w.p("A representação é **suficiente**: como a orientação, o comprimento e a linha/coluna fixa não "
        "mudam, a posição de referência determina todas as casas ocupadas por cada veículo, e a grelha "
        "pode ser reconstruída (`grelha(s)`). É **mínima**: guardar a grelha (n² caracteres) ou as casas "
        "ocupadas seria redundante, e cada veículo só tem um grau de liberdade. Como é um tuplo de "
        "inteiros, é imutável e ~hashable~ e pode ser usado directamente em `set`/`dict` (fechados, "
        "tabela de transposição) com custo O(nº de veículos).")
    w.h2("Estado inicial")
    w.p(f"Na instância base, a ordem dos veículos é A, B, C, O, P, Q, R, X e o estado inicial é "
        f"s0 = {R['s0']}:")
    w.codigo(R["grelha"], 10)
    w.h2("Acções e modelo de transição")
    w.p("Há um único tipo de acção, `Accao(veiculo, deslocamento)`, com deslocamento inteiro k ≠ 0 "
        "(positivo: direita/baixo; negativo: esquerda/cima). `accoes(s)` gera, para cada veículo e cada "
        "sentido, todos os k até à primeira casa ocupada ou à borda.")
    w.tabela("Acções do problema", ["Acção", "Parâmetros", "Pré-condições", "Efeito no estado", "Custo"],
             [["Mover veículo", "v (id), k ∈ ℤ \\ {0}",
               "s não é objectivo; 0 ≤ pos(v)+k ≤ n−L(v); todas as |k| casas atravessadas na linha/coluna "
               "de v estão livres (sem veículos nem obstáculos)",
               "s′ = s com pos(v) ← pos(v) + k; restantes posições iguais",
               "movimentos: 1; ponderado: L(v)·|k|"]],
             larguras=[2.2, 2.4, 5.2, 4, 2.6])
    w.p(f"Na base, s0 tem 11 acções aplicáveis (A+1, A+2, A+3, C−1, C−2, C−3, O+1, Q±1, R±1); B, P e X "
        f"estão presos. O factor de ramificação médio observado em todos os estados alcançáveis da base é "
        f"{f(R['ramificacao'])} acções por estado. As acções são **reversíveis** (mover v por −k "
        f"desfaz a acção, com o mesmo custo), o que o gerador e o cálculo de h* aproveitam.")
    w.h2("Função de custo")
    w.p("c(s, a, s′) = 1 no critério **movimentos** e c(s, a, s′) = L(v)·|k| no critério **ponderado** "
        "(unidades: casas × comprimento, um “esforço” de manobra). Os custos são positivos, mas no "
        "critério ponderado variam entre 2 (carro, 1 casa) e 3·(n−3) (camião a atravessar o tabuleiro). "
        "Consequências: a BFS minimiza o número de acções e só é óptima no primeiro critério; a DFS não é "
        "óptima em nenhum. No critério ponderado são necessários UCS, A* ou IDA*. Como o conjunto de "
        "acções é o mesmo nos dois critérios e só a função de custo muda, a comparação é justa: "
        "“movimento” significa sempre deslocar um veículo qualquer número de casas.")
    w.h2("Teste de objectivo")
    w.p("Em linguagem matemática: objectivo(s) ⇔ pos_X(s) + 2 = n (a casa direita de X está na coluna "
        "n − 1 da linha r). Em Python: `s[self._indices[\"X\"]] + 2 == self.tamanho`. Há **vários estados "
        f"objectivo** (qualquer configuração dos outros veículos compatível com X na saída); na base, "
        f"{m['objectivos']} dos estados alcançáveis são objectivos.")
    w.h2("Dimensão do espaço de estados")
    w.p("Ignorando colisões, um veículo de comprimento L tem n − L + 1 posições, logo |S| ≤ "
        "∏ᵢ (n − Lᵢ + 1). Na base (4 carros com 5 posições e 4 camiões com 4 posições) o limite é "
        f"5⁴ · 4⁴ = 160 000. Por BFS exaustiva medimos **{m['estados']} estados alcançáveis** "
        f"({pct(m['estados'], 160000)} do limite), com {m['transicoes']} transições. Num tabuleiro 8×8 "
        "com 15 veículos o limite ultrapassa 10¹², e as instâncias grandes geradas têm componentes de "
        "centenas de milhares de estados. Assim, BFS e UCS (que guardam todos os estados alcançados) "
        "só são viáveis até 10⁵–10⁶ estados, e DFS/IDS (busca em árvore, O(b^d) com b ≈ 5 a 11) só com "
        "soluções curtas (d ≲ 8); para as instâncias grandes são precisas heurísticas (Capítulo 6).")


def heuristicas(w, R, D):
    hi = R["h_inicial"]
    w.h1("HEURÍSTICAS")
    w.h2("Definição das heurísticas")
    w.p("Seja r a linha de saída, x a coluna esquerda de X e d_X = n − 2 − x a distância que X ainda tem "
        "de percorrer. B(s) é o conjunto de veículos distintos que ocupam casas (r, c) com c ≥ x + 2 "
        "(à frente de X). Para um bloqueador vertical b de comprimento L_b, m_b é o menor deslocamento que "
        "o tira da linha r para cima ou para baixo, ignorando os outros veículos mas respeitando as bordas "
        "e os obstáculos da sua coluna. Se um obstáculo ou um veículo horizontal estiver à frente de X, ou "
        "um bloqueador não puder sair da linha, o estado não tem solução e todas as heurísticas valem ∞.")
    w.lista([f"**h1(s) = |B(s)|**, o nº de veículos que bloqueiam X (dica do enunciado). Relaxação: cada "
             f"bloqueador sai com uma acção. Na base, h1(s0) = {hi['h1']} (Q e O).",
             f"**h2(s) = h1(s) + |B₂(s)|**, em que B₂ são os veículos distintos, fora de B, que ocupam as "
             f"casas que cada bloqueador atravessa ao sair pelo lado mais curto (dica do enunciado). "
             f"h2(s0) = {hi['h2']}.",
             f"**h3(s) = h1(s) + [d_X > 0]**: acrescenta o movimento do próprio X, que é uma acção "
             f"distinta das dos bloqueadores. h3(s0) = {hi['h3']}.",
             f"**h4(s)**, a relaxação “cada veículo sozinho no tabuleiro”: o custo óptimo do problema em "
             f"que os veículos não se bloqueiam uns aos outros. No critério ponderado, "
             f"h4(s) = 2·d_X + Σ_(b∈B) L_b·m_b; em movimentos, h4 = h3. Na base, h4(s0) = 2·3 + 3·2 + 3·3 = "
             f"{R['h4_pond']} no ponderado (óptimo 40)."])
    w.p("h1 e h2 são as dicas do enunciado; h3 e h4 são as heurísticas propostas pelo grupo, que as "
        "melhoram: h3 domina h1 em movimentos, h4 domina h1 e h3 no ponderado, e ambas são consistentes "
        "nos dois critérios, ao contrário de h2.")
    w.h2("Prova de admissibilidade")
    w.p("**Lema.** Em qualquer solução a partir de s, cada b ∈ B(s) é movido pelo menos uma vez e o seu "
        "deslocamento total é ≥ m_b; X percorre pelo menos d_X casas. ~Prova:~ X só se move na linha r e "
        "não salta veículos, logo para chegar a x = n − 2 tem de ocupar sucessivamente todas as casas "
        "(r, x+2), …, (r, n−1). No momento em que X entra na casa ocupada inicialmente por b, b já não "
        "está na linha r; como b é vertical, isso exige deslocá-lo pelo menos m_b casas (os obstáculos "
        "não se movem, por isso um lado bloqueado por um obstáculo nunca fica livre). □")
    w.p("**h1.** Cada acção move um só veículo e custa ≥ 1, logo uma solução tem ≥ |B(s)| acções e "
        "h1 ≤ h* (no ponderado cada acção custa ≥ 2, folga ainda maior). **h3.** Se d_X > 0, X move-se "
        "pelo menos uma vez, e essa acção é distinta das acções dos |B| bloqueadores: h3 ≤ h*. **h4.** No "
        "ponderado, o custo de uma solução é a soma, por veículo, de L·Σ|k|. Pelo lema, a parcela de X é "
        "≥ 2·d_X e a de cada b ∈ B é ≥ L_b·m_b; as parcelas são de veículos diferentes, logo somam-se: "
        "h4 ≤ h*. Os estados com h = ∞ não têm solução (h* = ∞).")
    w.p("**h2 não é admissível no critério movimentos.** Contra-exemplo (5×5, linha de saída 3), "
        "verificado em `tests/contra_exemplo_h2.py`:")
    w.codigo(""". . . C C
. . . . A
X X B . A   → saída
. . B . .
. E E . .""", 10)
    w.p("B = {B, A}, logo h1 = 2. Pelo lado mais curto, B desce 1 casa (E bloqueia) e A sobe 1 casa "
        "(C bloqueia), logo h2 = 4. Mas B−2, A+2, X+3 resolve em 3 movimentos: h* = 3 < h2 = 4. O erro "
        "da dica é assumir que o bloqueador sai pelo lado mais curto, quando o lado mais longo pode "
        "estar livre. **h2 é admissível no critério ponderado:** o caminho mais curto de b tem m_b casas, "
        "logo no máximo m_b bloqueadores de 2.º nível; como L_b ≥ 2 e m_b ≥ 1, 1 + m_b ≤ L_b·m_b; somando "
        "sobre b ∈ B, h2 ≤ Σ L_b·m_b ≤ h4 ≤ h*. Isto responde à exigência específica 2 do P6.")
    w.h2("Prova de consistência")
    w.p("Uma acção move um só veículo v por k casas. (i) Se v = X, as casas para onde X avança estavam "
        "livres e as que liberta não ficam à sua frente, logo B não muda; d_X varia exactamente k: h1 "
        "não muda, [d_X > 0] diminui no máximo 1 ≤ c, e 2·d_X diminui no máximo 2|k| = c. (ii) Se v ≠ X, "
        "só a parcela de v muda: h1 e h3 diminuem no máximo 1 ≤ c (v sai de B); em h4, m_v é a distância "
        "a uma posição livre da linha r, que varia no máximo |k| quando v se desloca |k| casas, logo a "
        "parcela L_v·m_v diminui no máximo L_v|k| = c (se v entra em B, h aumenta, o que não viola a "
        "condição). Em todos os casos h(s) ≤ c(s, a, s′) + h(s′), e h = 0 nos objectivos (B = ∅, "
        "d_X = 0): **h1, h3 e h4 são consistentes nos dois critérios**. **h2 não é consistente em "
        "movimentos** (inadmissível implica inconsistente); por isso o A* implementado reabre nós "
        "fechados quando encontra um g melhor, mantendo a correcção com qualquer heurística.")
    w.h2("Verificação empírica e dominância")
    v = D.get("verificacao_heuristicas.csv")
    texto = ("O teste automático (`heuristicas.verificar`, chamado nos testes `pytest` e em "
             "`experiencias.py`) enumera todos os estados alcançáveis, calcula h* exacto por Dijkstra no "
             "grafo invertido a partir de todos os objectivos e verifica h(s) ≤ h*(s) em todos os estados "
             "e h(s) ≤ c + h(s′) em todas as transições. ")
    if v is not None:
        n_est = int(v.drop_duplicates(["instancia", "criterio"]).estados.sum())
        n_tr = int(v.drop_duplicates(["instancia", "criterio"]).transicoes.sum())
        res = {}
        for (h, c), g in v.groupby(["heuristica", "criterio"]):
            res[(h, c)] = (int(g.violacoes_adm.sum()), int(g.violacoes_cons.sum()))
        texto += (f"Na base e nas 10 instâncias pequenas foram verificados, em cada critério, {f(n_est // 2)} "
                  f"estados e {f(n_tr // 2)} transições: h1, h3 e h4 não violam a admissibilidade "
                  f"nem a consistência; h2 tem {res[('h2', 'movimentos')][0]} violações de "
                  f"admissibilidade e {res[('h2', 'movimentos')][1]} de consistência em movimentos, e "
                  f"{res[('h2', 'ponderado')][0]} de admissibilidade e {res[('h2', 'ponderado')][1]} de "
                  f"consistência no ponderado. A inadmissibilidade de h2 é rara (não aparece nestas instâncias, só no "
                  f"contra-exemplo construído), mas a inconsistência é frequente. ")
    texto += ("A dominância h1 ≤ h3 ≤ h4 verifica-se em todos os estados (teste `test_dominancia`). A "
              "Tabela 3 compara as heurísticas no A* (nós expandidos e b*) em instâncias representativas.")
    w.p(texto)
    t = D.get("heuristicas.csv")
    linhas = []
    if t is not None:
        for crit in ("movimentos", "ponderado"):
            sel = t[t.criterio == crit].copy()
            ordem = ["base"] + [f"pequena_{i:02d}" for i in (1, 2, 5)] + [f"media_{i:02d}" for i in (1, 4, 6)] + \
                    [f"grande_{i:02d}" for i in (1, 2)]
            for inst in ordem:
                r = sel[sel.instancia == inst]
                if r.empty:
                    continue
                r = r.iloc[0]
                linhas.append([f"{inst} ({crit[:3]}.)", f(r.get("d"), 0)] +
                              [f(r.get(f"exp_{h}"), 0) for h in ("h0", "h1", "h2", "h3", "h4")] +
                              [f(r.get(f"b_{h}"), 2) for h in ("h1", "h4")])
    w.tabela("Comparação das heurísticas no A*",
             ["Instância", "d", "Exp. h0", "Exp. h1", "Exp. h2", "Exp. h3", "Exp. h4", "b* h1", "b* h4"],
             linhas, tamanho=8)
    w.p("d é o nº de movimentos da solução encontrada pelo A*; b* calcula-se com N = nós expandidos. "
        "“—” indica que a execução excedeu 60 s. No critério movimentos, h2 expande menos nós do que h3/h4 "
        "porque é maior (e por vezes sobrestima); só não perde a optimalidade nas instâncias geradas porque "
        "as sobrestimações são raras. h3 e h4 coincidem em movimentos. No critério ponderado, h4 é a mais "
        "informada e a única que reduz claramente o b*.")


def implementacao(w, R, D, GRAF):
    w.h1("IMPLEMENTAÇÃO")
    w.h2("Arquitectura do código")
    w.p("O código segue a estrutura mínima do enunciado (Figura 1). `problema.py` define a classe "
        "abstracta `Problema` (estado_inicial, accoes, resultado, custo, e_objectivo, heuristica), o nó "
        "`No(estado, pai, accao, g, profundidade)` e `caminho(no)`. `dominio.py` contém `RushHour`, "
        "subclasse de `Problema`. `buscas.py` contém os algoritmos, que **só usam a interface**: trocar "
        "de problema não obriga a alterar nenhum algoritmo (os testes usam também tabuleiros 4×4 e 5×5 "
        "sem mudar `buscas.py`). `heuristicas.py` define h0–h4 e as ferramentas de análise (h* exacto, "
        "verificação, b*, divergência entre critérios). `gerador.py`, `experiencias.py` e `main.py` usam "
        "estes módulos.")
    w.figura(GRAF / "arquitectura.png", "Arquitectura do programa", 15)
    w.h2("Estruturas de dados")
    w.lista(["**Fronteira:** `collections.deque` na BFS (FIFO, O(1) nas duas pontas); `heapq` no UCS, "
             "Gulosa e A*, com entradas (prioridade, contador, nó): o contador desempata em ordem de "
             "inserção e evita comparar nós; recursão (pilha implícita) na DFS, IDS e IDA*.",
             "**Alcançados/fechados:** `set` de estados (tuplos) para teste de pertença em O(1) médio; "
             "`dict` `melhor_g` estado → menor g na fila de prioridade.",
             "**Entradas obsoletas:** em vez de actualizar a prioridade dentro do ~heap~ (O(n)), insere-se "
             "uma nova entrada quando se encontra um g melhor e, ao retirar, descarta-se a entrada cujo g "
             "é maior do que `melhor_g[estado]` (descarte preguiçoso, O(log n) por operação).",
             "**Controlo de ciclos no caminho** (DFS, IDS, IDA*): `set` com os estados do caminho actual, "
             "actualizado ao entrar e sair da recursão: O(1) por teste e memória O(d).",
             "**Tabela de transposição:** `dict` estado → menor g na iteração actual, limpo em cada iteração.",
             "**Reconstrução do caminho:** cada nó guarda o pai; `caminho(no)` segue os pais até à raiz "
             "(O(d)), sem copiar caminhos em cada nó.",
             "**Domínio:** `resultado()` só verifica as casas atravessadas, com uma ~cache~ da ocupação do "
             "último estado (os algoritmos aplicam várias acções seguidas ao mesmo estado). Medimos uma "
             "redução de cerca de 5× no tempo por nó face à versão inicial, que regenerava todas as acções "
             "para validar cada uma."])
    w.h2("Algoritmos implementados")
    w.p("Todos os algoritmos devolvem um `Resultado` com o nó final, o estado da execução (ok, sem "
        "solução, limite, tempo) e as mesmas métricas: nós expandidos (nós cujos sucessores foram "
        "gerados), gerados (sucessores criados, mais a raiz), fronteira máxima e re-expandidos. O prazo "
        "de 60 s é verificado dentro do ciclo principal (de 256 em 256 expansões). Decisões:")
    w.lista(["**BFS:** busca em grafo com teste de objectivo **na geração**, o que poupa um nível inteiro "
             "de expansões; o `set` de alcançados inclui a fronteira.",
             "**DFS:** recursiva, com controlo de ciclos no caminho actual e limite de profundidade "
             "configurável (por omissão 50); devolve “limite” se cortou ramos e “sem solução” se esgotou "
             "a árvore sem cortes.",
             "**IDS:** DFS limitada com limite 0, 1, 2, …; conta como re-expansão cada expansão de um estado "
             "já expandido numa iteração anterior; pára com “sem solução” quando uma iteração termina sem "
             "cortes.",
             "**UCS / Gulosa / A*:** um único `_melhor_primeiro` parametrizado pela prioridade (g, h ou "
             "g + h) e com teste de objectivo **na expansão** (necessário para a optimalidade). O A* desempata "
             "f igual pelo maior g (mais perto do objectivo) e reabre nós fechados se encontrar g menor, o "
             "que só acontece com h2.",
             "**IDA* (+TT):** recursivo, filhos ordenados por f crescente, controlo de ciclos no caminho e, "
             "na variante com tabela, poda por transposição; `idastar_simples` é a mesma função sem tabela, "
             "para medir a redução de nós (exigência específica 3)."])
    w.p("Excerto do A* (o código completo está no repositório e no Anexo C):")
    w.codigo('''while fronteira:
    _, _, no = heapq.heappop(fronteira)
    if no.g > melhor_g[no.estado]:
        continue                                  # entrada obsoleta
    if no.estado in fechados:
        if not reabrir: continue
        r.reexpandidos += 1                       # só com h inconsistente
    if problema.e_objectivo(no.estado):           # teste na expansão
        return no
    fechados.add(no.estado); r.expandidos += 1
    for a in problema.accoes(no.estado):
        filho = _filho(problema, no, a); r.gerados += 1
        antigo = melhor_g.get(filho.estado)
        if antigo is not None and filho.g >= antigo: continue
        melhor_g[filho.estado] = filho.g
        heapq.heappush(fronteira, (prioridade(filho), next(desempate), filho))''')
    w.h2("Gerador de instâncias")
    w.p("O `gerador.py` cria puzzles por **busca para trás a partir de estados objectivo**: (1) sorteia, "
        "com `random.Random(\"202606-<nível>\")`, um tamanho, carros, camiões e obstáculos numa "
        "configuração em que X já está no objectivo; (2) enumera por BFS toda a componente de estados "
        "alcançáveis a partir dela (as acções são reversíveis, logo são exactamente os estados que "
        "chegam a esse objectivo); (3) calcula, por BFS multi-origem a partir de **todos** os objectivos "
        "da componente, a distância óptima em movimentos de cada estado; (4) escolhe como estado inicial "
        "um dos estados mais distantes. A distância é exacta (BFS), por isso o gerador **certifica** o "
        "óptimo e não apenas o número de passos do passeio para trás. Instâncias repetidas são rejeitadas, "
        "e cada JSON guarda a semente, o nível, o óptimo certificado e o tamanho da componente.")
    w.p("Níveis: **média** e **grande** só aceitam puzzles com óptimo ≥ 15 movimentos (regra 2 do P6), e "
        "distinguem-se pelo tamanho da componente (3 000–40 000 estados nas médias, em tabuleiros 6×6/7×7; "
        "250 000–800 000 nas grandes, em 7×7/8×8). Na **pequena** o enunciado exige que todos os algoritmos "
        "terminem. Verificámos que isso é incompatível com o mínimo de 15 movimentos: DFS e IDS fazem "
        "busca em árvore com controlo de ciclos só no caminho, e com b ≈ 5–11 e d = 15 a árvore tem "
        "10¹⁰–10¹⁵ nós (em puzzles com apenas 553 estados alcançáveis e d = 15, o IDS excedeu os 60 s com "
        "mais de um milhão de expansões). Por isso, a pequena aceita o estado mais distante (óptimo ≥ 6) "
        "que DFS e IDS ainda resolvem dentro de um orçamento **determinístico** de 300 000 nós; a decisão "
        "fica documentada no código e não relaxa a regra dos 15 movimentos nos outros níveis. Também "
        "suporta M×M até 8×8 e obstáculos (exigência 1). Comando: `python gerador.py --nivel todos`.")
    w.h2("Testes automáticos")
    w.p(f"A pasta `tests/` contém testes `pytest` em quatro ficheiros. Resultado da execução final: "
        f"**{D['testes']}**.")
    w.lista(["`test_dominio.py` (Lino): instância base, movimentos e imutabilidade, movimentos ilegais, saída, "
             "obstáculos, colisões, tabuleiro 8×8, `caminho()`;",
             "`test_buscas.py`: **sucessores de um estado conhecido** (as 11 acções de s0); óptimos da base "
             "(8 e 40) com UCS, A* h0/h1/h3/h4 e IDA*; **A* e UCS devolvem o mesmo custo** em instâncias "
             "geradas; BFS óptima em movimentos; **instância sem solução** em todos os algoritmos; limite da "
             "DFS; re-expansões do IDS; a TT reduz nós; Gulosa válida; limite de tempo; divergência dos "
             "critérios; cada solução é revalidada reaplicando as acções;",
             "`test_heuristicas.py`: **admissibilidade e consistência em todos os estados** da base "
             "(1079 estados, dois critérios); h = 0 nos objectivos; dominância; valores conhecidos de h1/h4; "
             "estados impossíveis com h = ∞; o contra-exemplo de h2; h2 ≤ h4 no ponderado; b*;",
             "`test_gerador.py`: reprodutibilidade com a semente, óptimo certificado igual ao da BFS após "
             "gravar e reler o JSON e o mínimo de movimentos de todas as instâncias gravadas."])
    w.h2("Interface e instruções de execução")
    w.p("Instalação: `python -m pip install -r requirements.txt` (Python ≥ 3.10). O `main.py` tem um menu "
        "de texto (instância base, ficheiro JSON ou gerada com semente e nível; critério; algoritmo; "
        "heurística; limite de tempo e de profundidade) e mostra a solução passo a passo em ASCII e as "
        "métricas. Para demonstração aceita também argumentos:")
    w.codigo("""python main.py                                   # menu interactivo
python main.py --alg astar --h h4 --criterio ponderado
python main.py --instancia instancias/media_04.json --alg idastar --h h4 --sem-passos
python gerador.py --nivel todos                  # regenera as 30 instâncias
python experiencias.py --workers 2               # bateria completa, CSV e gráficos
python -m pytest -q                              # testes""")
    w.p("Excerto da execução `python main.py --alg astar --h h4 --criterio ponderado` (últimos passos):")
    import subprocess
    import sys as _s
    saida = subprocess.run([_s.executable, "main.py", "--alg", "astar", "--h", "h4", "--criterio", "ponderado"],
                           cwd=RAIZ, capture_output=True, text=True).stdout.strip().splitlines()
    w.codigo("\n".join(saida[-28:]), 8)


def tabela_nivel(w, D, nivel, criterio):
    t = D["resumos"].get(f"{nivel}_{criterio}")
    if t is None:
        return
    linhas = []
    for _, r in t.iterrows():
        alg, _, h = r.config.partition("-")
        falhas = r.falhas if isinstance(r.falhas, str) else ""
        linhas.append([NOMES.get(alg, alg), h or "—", r.resolvidas + (" *" if falhas else ""),
                       f(r.custo_medio, 1), f(r.custo_optimo, 3), f(r.expandidos, 0), f(r.gerados, 0),
                       f(r.fronteira_max, 0), f(r.tempo_s, 3), f(r.memoria_mb, 2)])
    w.tabela(f"Resultados médios por algoritmo — instâncias {NIVEL[nivel]}, critério {criterio}",
             ["Algoritmo", "Heur.", "Resolvidas", "Custo médio", "Custo / óptimo", "Nós expandidos",
              "Nós gerados", "Fronteira máx.", "Tempo (s)", "Memória (MB)"], linhas, tamanho=7.5)


def experiencias(w, R, D, E, GRAF):
    amb = D["ambiente"]
    w.h1("EXPERIÊNCIAS E RESULTADOS")
    w.h2("Desenho experimental")
    n = E.get("n_inst", {})
    w.p(f"Máquina: {amb.get('processador', '?')}, {amb.get('cpus', '?')} CPUs lógicos, "
        f"{f(amb.get('ram_gb'), 1)} GB de RAM, {amb.get('sistema', '?')}, Python {amb.get('python', '?')}. "
        f"Semente 202606. Instâncias: a base mais {n.get('pequena', 0)} pequenas, {n.get('media', 0)} médias "
        f"e {n.get('grande', 0)} grandes, geradas pelo `gerador.py` (Secção 5.4). Para cada instância e "
        f"cada critério (movimentos e ponderado) correram 13 configurações: BFS, DFS (limite 50), IDS, UCS, "
        f"Gulosa (h1, h2), A* (h0, h1, h2, h3, h4), IDA* simples (h4) e IDA*+TT (h4), num total de "
        f"{E.get('execucoes', 0)} execuções. Cada execução corre num processo novo, com limite de memória "
        f"de 2 GB (`RLIMIT_AS`) e de 60 s (prazo verificado dentro do algoritmo); as que excedem os limites "
        f"aparecem como “falhou (tempo)” ou “falhou (memória)”. Mede-se o tempo com `time.perf_counter` e "
        f"a memória de pico com `tracemalloc` (o tempo inclui a sobrecarga do tracemalloc, igual para "
        f"todos). As contagens de nós são determinísticas, por isso basta uma repetição; o tempo de uma "
        f"execução isolada tem variação de alguns %, e o desvio-padrão entre instâncias está nos CSV "
        f"(`outputs/resumo_*.csv`). O óptimo de referência de cada instância é o menor custo obtido por UCS, "
        f"A* ou IDA* (todos óptimos com h admissível) e coincide com o óptimo certificado pelo gerador.")
    w.h2("Resultados")
    w.p("As Tabelas 4 a 9 resumem os resultados por nível e critério. As médias de custo, nós, tempo e "
        "memória usam só as execuções resolvidas; “Resolvidas” indica quantas de 10 terminaram, e o "
        "asterisco assinala falhas (motivo nos CSV). As Figuras 2 a 6 mostram a evolução com a dimensão "
        "da instância, medida pela profundidade óptima d (nº de movimentos da solução óptima).")
    for nivel in ("pequena", "media", "grande"):
        for criterio in ("movimentos", "ponderado"):
            tabela_nivel(w, D, nivel, criterio)
    for nome, leg in [("expandidos_vs_tamanho_movimentos", "Nós expandidos em função do tamanho da instância (escala logarítmica), critério movimentos"),
                      ("expandidos_vs_tamanho_ponderado", "Nós expandidos em função do tamanho da instância (escala logarítmica), critério ponderado"),
                      ("tempo_vs_tamanho_ponderado", "Tempo de execução em função do tamanho da instância (escala logarítmica), critério ponderado"),
                      ("custo_vs_optimo_ponderado", "Custo obtido em função do custo óptimo, critério ponderado"),
                      ("idastar_tt_vs_simples", "Nós expandidos pelo IDA* simples e pelo IDA* com tabela de transposição")]:
        if (GRAF / f"{nome}.png").exists():
            w.figura(GRAF / f"{nome}.png", leg, 14)
    import discussao
    discussao.escrever(w, R, D, E)


def conclusoes(w, R, D, E):
    import discussao
    discussao.conclusoes(w, R, D, E)


def referencias(w):
    w.h1("REFERÊNCIAS BIBLIOGRÁFICAS")
    refs = [
        "Collette, S., Raskin, J.-F., & Servais, F. (2006). On the symbolic computation of the hardest "
        "configurations of the Rush Hour game. In ~Computers and Games~ (Lecture Notes in Computer Science, "
        "Vol. 4630, pp. 220–233). Springer.",
        "Culberson, J. C., & Schaeffer, J. (1998). Pattern databases. ~Computational Intelligence, 14~(3), "
        "318–334.",
        "Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. ~Numerische Mathematik, "
        "1~(1), 269–271.",
        "Flake, G. W., & Baum, E. B. (2002). Rush Hour is PSPACE-complete, or “Why you should generously "
        "tip parking lot attendants”. ~Theoretical Computer Science, 270~(1–2), 895–911.",
        "Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). A formal basis for the heuristic determination "
        "of minimum cost paths. ~IEEE Transactions on Systems Science and Cybernetics, 4~(2), 100–107.",
        "Korf, R. E. (1985). Depth-first iterative-deepening: An optimal admissible tree search. "
        "~Artificial Intelligence, 27~(1), 97–109.",
        "Reinefeld, A., & Marsland, T. A. (1994). Enhanced iterative-deepening search. ~IEEE Transactions "
        "on Pattern Analysis and Machine Intelligence, 16~(7), 701–710.",
        "Russell, S., & Norvig, P. (2021). ~Artificial Intelligence: A Modern Approach~ (4.ª ed.). Pearson.",
        "Universidade Eduardo Mondlane, Faculdade de Engenharia. (2026). ~Projecto Prático 2026 — "
        "Resolução de Problemas de Busca em Python~ (enunciado de Inteligência Artificial I).",
    ]
    for r in refs:
        par = w.p(r)
        from docx.shared import Cm
        par.paragraph_format.left_indent = Cm(1)
        par.paragraph_format.first_line_indent = Cm(-1)


def anexos(w):
    w.h1("ANEXO A — DECLARAÇÃO DE USO DE FERRAMENTAS DE IA")
    w.p("O grupo usou assistentes de IA como apoio, conforme a secção 5.4 do enunciado. A tabela regista "
        "as ferramentas, para que foram usadas e o que o grupo verificou. **[A REVER PELO GRUPO antes da "
        "entrega: confirmar e completar com o uso de IA de cada membro.]**")
    w.tabela("Uso de ferramentas de IA",
             ["Ferramenta", "Para quê", "Pedido principal (resumo)", "O que o grupo verificou ou alterou",
              "Secção / ficheiro"],
             [["Assistente de IA (usado na preparação do domínio)", "Código e testes do domínio",
               "Implementar o contrato do domínio P6 (estado, acções, custos) e testes",
               "Convenções discutidas em grupo; testes executados", "dominio.py, problema.py, tests/test_dominio.py"],
              ["Claude Code (Anthropic, modelo Claude Opus)", "Código, depuração e revisão",
               "Implementar as buscas, heurísticas h1–h4 com provas, gerador com semente 202606, experiências, "
               "menu e testes, a partir do enunciado e do contrato do domínio",
               "Execução de todos os testes; verificação exaustiva h ≤ h*; conferência manual dos sucessores "
               "de s0 e do contra-exemplo de h2; nova execução das experiências",
               "buscas.py, heuristicas.py, gerador.py, experiencias.py, main.py, tests/"],
              ["Claude Code (Anthropic, modelo Claude Opus)", "Texto do relatório",
               "Redigir o relatório no template oficial com os números reais dos CSV",
               "Revisão do texto, das provas e das conclusões pelos membros", "Relatório (todos os capítulos)"]],
             tamanho=8)
    w.p("O grupo declara que compreende e consegue explicar todo o código e texto entregues, e que os "
        "resultados experimentais foram obtidos pela execução do código com a semente 202606 e são "
        "reproduzíveis com `python experiencias.py`.")
    w.p("Assinaturas: ______________________   ______________________   ______________________   "
        "______________________   ______________________")
    w.h1("ANEXO B — CONTRIBUIÇÃO DOS MEMBROS")
    w.p("Tarefas segundo o quadro do sprint (S01–S35). **[A CONFIRMAR PELO GRUPO: percentagens e "
        "tarefas efectivamente realizadas; o histórico Git é entregue com o projecto.]**")
    w.tabela("Contribuição individual",
             ["Membro (Apelido, Nome)", "Tarefas principais", "Ficheiros / secções", "Contribuição (%)", "Assinatura"],
             [["Falaque, Dalton", "S05, S11, S12, S18, S29: interface das buscas; BFS, UCS, DFS, IDS; garantias",
               "buscas.py; Cap. 2 e 6", "", ""],
              ["Nhabinde, Alex", "S06, S13, S17, S24, S30: heurísticas h1–h4, provas, Gulosa e A*; integração",
               "heuristicas.py, buscas.py; Cap. 4", "", ""],
              ["Nhabomba, Lino", "S02, S03, S09, S10, S16, S31: contrato, estado, domínio e testes do domínio",
               "dominio.py, problema.py, tests/test_dominio.py; Cap. 3", "", ""],
              ["Quive, Alexandre", "S07, S14, S19, S22, S23, S32: IDA* e tabela de transposição; gerador",
               "buscas.py (IDA*), gerador.py; Secções 2.4 e 5.4", "", ""],
              ["Ricardo", "S04, S08, S15, S20, S25, S27, S28, S33: repositório, métricas, menu, experiências, montagem",
               "main.py, experiencias.py; Cap. 5–6", "", ""]],
             tamanho=8)
    w.h1("ANEXO C — CÓDIGO-FONTE RELEVANTE")
    w.p("O código completo está no repositório (ficheiro ZIP entregue, com a pasta `.git`). Seguem os "
        "excertos centrais: a interface genérica e o IDA* com tabela de transposição.")
    w.codigo((RAIZ / "problema.py").read_text(encoding="utf-8"), 8)
    src = (RAIZ / "buscas.py").read_text(encoding="utf-8")
    a = src.index("def idastar(")
    b = src.index("def idastar_simples(")
    w.codigo(src[a:b], 7.5)
    src = (RAIZ / "heuristicas.py").read_text(encoding="utf-8")
    a = src.index("def h4(")
    b = src.index("HEURISTICAS = ")
    w.codigo(src[a:b], 8)
