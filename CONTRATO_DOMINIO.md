# Contrato de domínio — S02, S03, S09 e S10

Implementação preparada com apoio de IA. Aprovação dos cinco membros e revisão por colega pendentes.

## Convenções propostas
Coordenadas começam em zero. X tem comprimento 2, orientação horizontal e fica na linha_saida. Vitória ocorre quando a extremidade direita de X atinge a borda direita. O movimento até à borda conta normalmente; não há movimento adicional de remoção. Estados objectivo são terminais.

Um movimento desloca um único veículo qualquer número inteiro positivo de casas livres, na sua orientação. Accao contém o ID e deslocamento com sinal (positivo direita/baixo). O custo é 1 em movimentos ou comprimento × valor absoluto do deslocamento em ponderado. Todas as casas atravessadas são verificadas. Obstáculos são imóveis.

Estado é tupla imutável, na ordem dos veículos do JSON. Horizontal guarda coluna esquerda; vertical guarda linha superior. Metadados ficam em Veiculo imutável. Na base, ordem A,B,C,O,P,Q,R,X e estado (0,4,4,0,1,1,2,1). Dimensão suportada entre 2 e 8. Grelhas devolvidas são reconstruídas e podem ser usadas na visualização.

## Interface
Problema declara estado_inicial(), accoes(s), resultado(s,a), custo(s,a,s2), e_objectivo(s), heuristica(s,nome).
resultado rejeita acções ilegais com ValueError. custo verifica a transição.
No guarda estado, pai, accao, g e profundidade. O algoritmo preenche esses campos.
caminho(no) retorna nós da raiz ao destino, incluindo raiz; acções correspondem a [n.accao for n in caminho(no)[1:]].
h0 retorna zero; h1/h2 aguardam Alex e lançam NotImplementedError.
carregar_base(criterio) e RushHour.de_json(ficheiro, criterio) carregam instâncias.
JSON contém tamanho, linha_saida, obstaculos (pares linha/coluna) e veiculos (id, orientacao H/V, comprimento 2/3, fixa, posicao).

## Dependências e estado
S02/S03 têm proposta e código preparados. O acordo colectivo depende dos colegas.
S09/S10 implementadas com testes próprios.
S16 depende de S15 do Ricardo e da revisão cruzada; permanece pendente.
S31 depende de S28 do Ricardo, incluindo resultados e contagem de estados; permanece pendente.
S01, S21, S26, S34 e S35 são colectivas e permanecem pendentes.
Integração, aprovação e commits identificados devem seguir CONTRIBUTING.md. Não foi criado commit em nome de Lino.
