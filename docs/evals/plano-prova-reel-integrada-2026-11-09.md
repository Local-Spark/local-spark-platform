# Prova integrada com IA real — 09/11/2026

> Registro histórico da primeira rodada. A [nova comparação integrada](plano-comparacao-criativa-integrada-2026-11-09.md#resultado-da-execução-autorizada) concluiu crítica e download em outra operação, preservando a falha e as versões desta rodada.

Estado: rodada encerrada com falha de persistência antes da crítica final; ponto 3 não concluído.
Nenhuma chamada à OpenAI, inclusive contagem, foi realizada durante o preparo.

O titular autorizou usar o banco **dev** existente e, em entrevista separada,
aplicar as migrações 0112/0113. Elas foram aplicadas sem limpar/recriar dados.
Os registros da demonstração pertencem a um tenant e negócio fictícios novos.
Uma fila exclusiva usa o worker normal do produto em contêiner; API/auth,
outbox, Temporal, renderer e armazenamento continuam sendo os componentes reais.

## Peça e envio

Caso fictício **Café Pausa**, com a gravação de preparo de café já usada nos
ensaios. Preservar gravação inteira e áudio; criar abertura tipográfica,
progressão e fechamento com movimento funcional, sem inventar fatos ou fala.
O envio inclui briefing/kit fictícios, quadros da gravação e, nas revisões,
composição HTML/JavaScript e quadros renderizados. A contagem usa esses mesmos
conteúdos antes da geração; o arquivo MP4 não é enviado ao modelo.

Modelo `gpt-6.1-sol`, reasoning `high`, processamento Standard. Até 16.000
tokens de saída para geração/correção e 8.000 para cada crítica.

## Limites autorizados

- Até quatro chamadas de geração/crítica e quatro consultas de contagem.
- Uma geração e uma crítica; uma correção e crítica final somente se necessárias.
- Reserva de **US$ 0,85 por chamada**, até **US$ 3,40 em novas reservas**.
- A guarda soma entrada contada e saída máxima antes de autorizar cada geração.
  Tarifas conservadoras configuradas: US$ 2,50/MTok de entrada, US$ 10/MTok de saída.
- Sem repetição automática após falha/resultado incerto; preservar evidências e
  reservas. Não transferir autorização dos ensaios anteriores.
- Reserva não é gasto realizado: uso estimado será registrado; fatura não será inventada.

## Preparo concluído

Imagem `motion-worker` construída a partir do Dockerfile do produto. A checagem
real dentro do worker produziu MP4 de 1.939 bytes e dois quadros com o renderer
isolado, sem banco/IA: sandbox, montagem compartilhada e saída validadas pelo
adapter existente. Nenhum CI completo foi executado.

O pedido foi admitido pela API real via ASGI/auth no banco dev. No preparo,
permaneceu enfileirado sem consumidor até a autorização do orçamento.
O pacote inicial foi construído localmente, com hashes preservados.
[Plano exato e identificadores](../../.local/evals/reel-integrated-openai-proof-20261109/paid-plan.json).

Após execução: preservar vídeo(s), críticas, custos e estado final; apresentar
relatório visual. Aprovação humana e publicação não serão fabricadas. Se o
gerador/crítico falhar, relatar a falha concreta sem chamar a prova de concluída.

## Ambiente de execução confirmado

O Temporal dev falhou ao despachar, com zero efeitos pagos. Um reinício
recuperou consultas simples, mas o serviço continuou excedendo prazos enquanto
processava histórico antigo. O titular autorizou usar a instância local já
ativa em `localhost:49805`; o banco continua sendo o dev. O workflow anterior
não foi encontrado e o pedido seguia `queued`, sem efeitos, antes da troca.
A identidade durável do pedido foi preservada, sem repetição de geração paga.
O Temporal dev foi devolvido ao estado parado original, sem remover histórico.

A troca e as autorizações estão preservadas no pacote local. A falha do
Temporal dev não será tratada como resolvida por esta prova.

## Defeito encontrado durante a prova

A primeira crítica identificou acentos/símbolos corrompidos e acionou a única
correção autorizada. O runner servia bytes UTF-8 como `text/html` sem declarar
charset. O código foi ajustado para `text/html; charset=utf-8`, sem modificar
HTML ou hashes. A prova paga continua usando seu digest original, preservando
a comparação e a identidade dos efeitos.

Os 71 testes direcionados do runner passaram em 1,17 s. A imagem corrigida foi
construída sem rede, reutilizando dependências locais:
`sha256:fa18127583b7d2e66cee3c49900179b52a81e9298913293a164cd9ef3aef8c25`.
Uma checagem real mínima exige no navegador `document.characterSet === 'UTF-8'`
e texto exato `Café Pausa — Faça uma pausa →`, sem meta charset no HTML.
A imagem anterior falhou; a nova passou e produziu dois quadros legíveis.
O primeiro harness esperava código de erro específico para a asserção; o runner
reporta exceções do JavaScript como falha genérica. Corrigido o registro da prova,
foi executada somente a imagem nova, sem repetir a tentativa antiga.
[Resultado](../../.local/evals/reel-integrated-openai-proof-20261109/utf8-check.json).
Isso elimina essa causa técnica de refação; não comprova que toda revisão seja
necessária nem substitui avaliação humana de movimento e áudio.

## Resultado da rodada

[Comparativo com som e download das duas versões](../../.local/evals/reel-integrated-openai-proof-20261109/report.html).
[Estado e efeitos](../../.local/evals/reel-integrated-openai-proof-20261109/result.json).

| Efeito pago | Uso estimado (US$) |
| --- | ---: |
| Geração | 0,109813 |
| Crítica da primeira versão | 0,114005 |
| Correção | 0,188703 |
| Total conhecido | **0,412521** |

Três reservas de US$ 0,85: **US$ 2,55** de US$ 3,40 autorizados. Elas permanecem
retidas como `uncertain` até conciliação de fatura; estimativa não foi transformada
em valor faturado. As três chamadas tiveram contagem e teto completos registrados.
A quarta contagem precedeu o claim que falhou, conforme ordem do código; seu
valor não sobreviveu ao rollback, e não foi inventado no relatório.

V0: 1.688.683 bytes. V1: 1.680.603 bytes. Ambas 720×1280, 30 fps, 336 quadros,
11,2 s, áudio original reencodado. O JavaScript é idêntico; V1 acrescenta meta
UTF-8 e entidades HTML para os caracteres. Inspeção do quadro de fechamento
confirma a correção visual dos acentos e seta; não é aprovação de movimento/áudio.
A segunda renderização levou aproximadamente 581 s, contra 115 s da primeira,
no ambiente local sob carga; não atribuir essa diferença a mudança de animação.

A falha ocorreu no INSERT de `motion_effects` antes da quarta submissão:
PostgreSQL `statement_timeout` de 10 s, SQLSTATE 57014. Leituras posteriores de
pacotes grandes também excederam esse prazo. A exportação local somente leitura
usou `SET LOCAL statement_timeout = '60s'`; isso não muda configuração global,
não reabre o pedido e não é correção do fluxo do produto.

As duas versões estão no armazenamento privado e foram recuperadas com hash
conferido. Pedido `failed`, `piece_id=null`: **não houve crítica final, seleção
concluída, peça na coleção nem prova de download assinado no produto nesta rodada**.
O relatório permite comparar os arquivos locais recuperados. A guarda não fez
nova chamada após falha nem liberou a peça sem concluir a revisão.

O worker exclusivo foi parado. PostgreSQL/storage dev permanecem disponíveis;
Temporal dev está no estado parado original, e a instância alternativa existente
foi preservada. Não houve CI completo, limpeza de dados ou alteração global de
prazos. Próximo trabalho necessário: corrigir a persistência dos pacotes grandes,
validar esse recorte e preparar uma retomada explícita antes de novas APIs pagas.
A etapa 5 continua posterior; esta rodada não fecha os três pontos do Reel.

## Implementação posterior à rodada — persistência

O item 1 de correção foi implementado sem reabrir este pedido ou executar IA:
pacotes grandes de entrada/quadros passam ao armazenamento privado cifrado,
com manifesto pequeno no SQL e upload durável verificado. No pacote salvo da
correção deste caso, o campo SQL caiu de 42.205.388 para 716 bytes com roundtrip
exato. 81 testes direcionados passaram em 1,42 s; Ruff/mypy aprovados. O código
não foi implantado no worker nem submetido a nova prova SQL/IA nesta fatia.
[Contrato e validação](../design/integracao-reel-2026-11-09.md).
O estado falho acima continua sendo o resultado desta rodada histórica.
O titular também considerou o motion fraco; critérios criativos são o item 2,
a iniciar por comando separado. Corrigir acentos não aprova a direção criativa.

## Implementação posterior — direção criativa (item 2)

O contrato criativo foi implementado para novos pedidos: quatro avaliações
estruturadas, vinculadas ao briefing e a quadros enviados, com evidências temporais
para progressão, função do motion e desenvolvimento visual. Calibrações são
textuais; nenhum vídeo de referência foi enviado nem houve nova API paga.
98 testes direcionados passaram em 1,50 s; a qualidade da geração/crítica real
continua a ser hipótese do item 3. Esta rodada histórica não foi reavaliada.
[Direção, critérios e limites](../design/integracao-reel-2026-11-09.md).
