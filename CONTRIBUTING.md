# Como contribuir

## Antes de começar

1. Actualize `main`: `git switch main` e `git pull`.
2. Crie um ramo com o seu nome e o ID do quadro: `git switch -c feature/alex/S17-astar`.
3. Mantenha o trabalho ligado a uma tarefa do quadro. Se surgir trabalho novo, registe-o e combine responsável e prazo no daily.

## Durante o trabalho

- Faça commits pequenos, com mensagens claras, por exemplo `feat: implementar BFS` ou `test: validar bloqueio intermédio`.
- Não inclua ambientes virtuais, cache, ficheiros temporários, credenciais ou resultados experimentais inventados.
- Preserve a interface acordada para estado, acções, custos e objectivo. Fale com o grupo antes de a alterar.
- Actualize README, testes e documentação quando a alteração modificar a forma de executar ou interpretar resultados.
- Cada membro deve usar o seu próprio nome e email Git para que o histórico identifique correctamente as contribuições.

## Integrar

1. Actualize o seu ramo com `main` e resolva conflitos localmente.
2. Execute os testes e a demonstração relevantes à tarefa.
3. Abra um Pull Request para `main`, descrevendo mudança, evidência e tarefa do quadro.
4. Peça revisão a pelo menos um colega que não tenha feito a alteração.
5. Integre apenas após aprovação e actualize o quadro.

## Ramo principal

`main` deve permanecer executável. Não fazer push directo para `main`; usar Pull Requests. Escolher uma pessoa para gerir a integração em cada dia e rodar essa responsabilidade quando possível.
