# Desempate simulado da última vaga

`JevReferenceTieBreak` é um adapter privado de teste para pedir uma opinião de
semelhança entre candidatas que o chamador já comprovou estarem empatadas na
última vaga. Ele não calcula a nota, não comprova o empate, não altera a lista,
não publica resultados e não está ligado a nenhuma activity ou rota. Aceita
somente `httpx.MockTransport` com flag explícita e guarda fornecida pelo chamador;
não realiza rede real nem autoriza gastos. Sua entrada de nomes e tipos é
transitória e mantida em memória, sem persistência ou logs pelo adapter.

Os identificadores privados não entram na requisição ao modelo. A resposta é
limitada a uma das opções numeradas enviadas ou `uncertain`; formato inválido,
probabilidades inconsistentes, falha ou cancelamento após a reserva deixam o
resultado incerto e notificam a guarda. Falta de evidência em qualquer candidata
leva a abstenção sem consulta. Para abstenção do Jev, o titular definiu como
desempate a ordem de retorno do Google. O adapter continua retornando abstenção:
o fallback ainda depende de provar a ordem de origem e a autorização do efeito.
Texto externo é dado não confiável, separado da instrução; isso não prova, por si
só, resistência completa a injeção de prompt ou fidelidade da opinião do modelo.

Antes de qualquer uso fora de testes ainda faltam: contrato e guarda duráveis
vinculando operação, candidatas empatadas, requisição, credencial e orçamento;
proveniência e validação da elegibilidade e nota; recuperação de efeitos e custo
incertos; persistência autenticada da ordem e da conclusão estruturada de
semelhança para recuperação sem nova consulta; integração transacional com a
lista publicável; validação de custos e testes sem conteúdo de cliente. Sem esses
gates não deve ser habilitado nem exposto como uma busca real.

O vínculo puro `tiebreak_request_mac` usa HMAC-SHA256 versionado para o pedido
HTTP exato, incluindo headers, corpo, modelo e credencial efetiva, e vincula
organização, negócio, ator, busca, efeito, piloto, efeitos anteriores, lote,
versão do contexto, MAC do lote, IDs ordenados das candidatas empatadas e valor
reservado. O resultado não revela a entrada. Ele não valida se esses IDs
correspondem aos dados do corpo ou se houve empate: o futuro chamador confiável
deverá provar ambas as relações antes do efeito. A rotação de chave e a reserva
transacional continuam pendentes; este HMAC não as implementa.


`JevReferenceSimilarityLevels` prepara uma única consulta simulada com duas
respostas explícitas por candidata: correspondência e grau de semelhança
`high`, `medium`, `low` ou `unknown`. O grau é solicitado ao modelo, nunca
derivado da confiança. A projeção `sanitize_leveled_observations` exclui grau
`unknown` antes de calcular a nota, inclusive para uma correspondência
classificada como `match`. Nenhum dos dois componentes está ligado à execução
real; o draft 0099 e a adaptação do pipeline precisam ser coordenados.
