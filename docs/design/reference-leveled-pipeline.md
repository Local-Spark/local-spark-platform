# Pipeline simulado com evidência de semelhança

Esta fatia usa somente transportes fictícios. O produtor pede classificação e
grau ao Jev em uma única resposta; `unknown` não é convertido em grau baixo e
não chega ao cálculo de nota. A origem ordenada é autenticada novamente em
memória pelo MAC v3 e o lote sanitizado é conferido antes da transação que grava
simultaneamente as conclusões estruturadas e a lista filtrada. A projeção não
contém nomes, estrelas, quantidades, endereços, coordenadas ou respostas brutas.

As migrations 0098 e 0099 mantêm os novos writers e recoveries sem GRANT de
runtime. A 0099 bloqueia novos commits pelo caminho anterior e mantém somente o
replay autenticado de lotes já existentes. Os testes que verificam internamente
o comportamento anterior concedem acesso apenas no banco de teste e revogam o
grant ao final. A leitura restrita devolve somente campos sanitizados e marca
explicitamente que origem da resposta e ordem do Google ainda não foram
comprovadas; não autoriza fallback, publicação, novo efeito ou provedor real.

O gate para excluir a própria loja continua pendente: o produtor fake não tem
contrato que prove nome/endereço/versão da loja. Não se deve tratar o endereço
usado como origem de pesquisa ou o ID de geocodificação como prova da ficha.
Também faltam activity confiável, prova da associação entre as respostas e o
lote, exclusão da própria loja antes do ranking e integração segura do custo.

Validação em banco descartável `_test`: a bateria do pipeline e snapshot com
Nearby/MAC v3 passou 15/15; a bateria de compatibilidade passou 35/36 na
primeira execução. Um caso falhou na preparação da reserva Google simulada com
`PLACES_BUDGET_UNAVAILABLE`; passou no rerun isolado e na sequência de quatro
casos instrumentada. O mesmo sintoma foi observado em outro teste, sem causa
identificada. A intermitência não está resolvida e não se deve apresentá-la como
CI estável. Não foram chamadas APIs externas nem migrado banco de desenvolvimento.
