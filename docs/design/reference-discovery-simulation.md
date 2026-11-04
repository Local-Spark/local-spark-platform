# Descoberta de referências: infraestrutura de simulação

**Decisão de produto de 03/11:** o fake permite uma pesquisa por raio no prazo
comum de seis meses, inclusive para outro raio após a confirmação; detalhes em
[DECISIONS](../DECISIONS.md).

Fatia local e **não habilitada ao cliente**. `reference_discovery_mode=fake` só
é admitido em desenvolvimento/teste e fica desligado por padrão. Não consulta
Google, Apify, Instagram ou modelos, nem mede qualidade. A API privada do owner
registra a versão de contexto, a categoria e a preferência de pesquisa.

A transação grava o pedido, auditoria e `reference.search_requested` na outbox;
replay devolve a operação original. O relay e o worker encaminham o pedido a
uma activity Temporal local. Ela confere o evento e compara categoria e alcance
atuais com o snapshot. A conclusão `simulated` ou `stale`, auditoria e recibo
processado são gravados atomicamente. A simulação produz três fixtures anônimas
por operação concluída, identificadas como `fake`, isoladas por tenant e não
utilizadas no briefing. Fixtures com o mesmo identificador canônico no mesmo
ciclo representam o mesmo exemplo observado em raios distintos; não representam
perfis ou negócios reais, nem provam a deduplicação de negócios reais.

Uma fixture adicional representa candidato inadequado e é descartada por
semelhança predefinida antes da fórmula experimental escolhida para testes;
as três restantes incluem um caso pontuado com menos de dez avaliações. As
avaliações e a semelhança são fictícias: não há consulta ou análise pelo Jev.
A lista simulada omite negócios sem média ou sem avaliações disponíveis e ordena
os demais pela pontuação integral decrescente; empates usam a identidade da
fixture como desempate técnico. Isso não demonstra recomendação de negócio real.
A conclusão da pesquisa fake grava por candidata a nota integral e as versões
da fórmula e fixture; a resposta usa esse snapshot e arredonda a duas casas
apenas para apresentação. Mudanças posteriores da fórmula ou fixture não mudam
a nota registrada. A migração 0073 recusa atualizar um banco que contenha
candidatas sem nota comprovada e recusa downgrade que apagaria snapshots;
não inventa histórico nem remove dados. Estrelas e contagem não são persistidas.
O snapshot protege a nota, não representa ainda uma lista real versionada de
até dez nem executa a reconfirmação de referências fora da lista nova.

No desenho futuro, o cliente escolheu não receber sugestões sem avaliação.
O [Nearby Search](https://developers.google.com/maps/documentation/places/web-service/nearby-search)
ordena por popularidade por padrão e aceita no máximo 20 resultados, mas não
afirma que todos tenham média e contagem nem que sua ordem coincida com a
fórmula própria. Campos de valor padrão podem ser
[omitidos mesmo quando solicitados](https://developers.google.com/maps/documentation/places/web-service/choose-fields#field-path-considerations).
Dados ausentes não comprovam que o estabelecimento nunca foi avaliado, mas não
permitem calcular essa pontuação. Filtragem e seleção podem retornar menos de
dez negócios; o teste fake não faz chamadas nem comprova uso permitido da fonte.

A operação fake admite exclusivamente os raios 5, 20 e 50 km. Dentro do ciclo,
cada raio pode ter uma pesquisa pendente ou concluída; requisições repetidas com
a mesma identidade são idempotentes. Um resultado `stale`, incluindo falha
comprovada da simulação ou simulação desativada, libera o raio. A compensação
após falhas locais é processada pelo Temporal; não implementa política de
repetição de efeitos externos pagos ou incertos.

A confirmação aceita de uma a três fixtures distintas, incluindo as do ciclo atual
e referências que continuem selecionadas de ciclos anteriores. Após uma busca
que inicie ciclo novo, a confirmação inicia o prazo comum de seis meses de
calendário. Raios ainda não pesquisados continuam
disponíveis nesse prazo; um raio já pesquisado não é liberado por alteração de
endereço ou segmento. A troca por outras fixtures disponíveis, inclusive de
raios diferentes, não reinicia o prazo; indicações manuais são independentes e
não contam nesse limite. Após o vencimento, uma nova pesquisa abre outro ciclo;
a seleção anterior continua marcada até outra confirmação. A confirmação grava
auditoria e outbox na mesma transação; seu consumidor Temporal registra o recibo
durável. O modelo real de candidato, aceite e uso no briefing ainda não existe.

O worker fake exige conexão correlator para reconciliar autor revogado. O
correlator possui policies RLS específicas por tenant e ator do evento e grants
limitados para comprovar o evento, liberar pedido fake pendente e registrar o
recibo e a auditoria. Confirmações já gravadas são reconhecidas sem alterar o
prazo. Desativar o modo fake antes do processamento impede a criação de fixtures.

Endereço manual é recusado enquanto não houver geocodificação e confirmação de
ponto; localização confirmada de dispositivo pode alimentar a simulação. Busca
nacional é recusada na API fake; dados de preferência legados são preservados.
Latitude e longitude não são enviadas no payload do outbox. A API de simulação
retorna estado, modo `fake`, datas e fixtures anônimas em endpoint separado.
Trabalhos iniciados não são automaticamente reagendados por mudança de contexto.

Esta fatia não implementa pesquisa real, busca automática, botão ao cliente,
confirmação de endereço, integração de orçamento com fornecedores, acervo compartilhado,
comparação por reputação ou deduplicação de negócios reais. Os eventos anteriores
`reference.created` e `reference.removed` continuam pendentes até existir um
consumidor real para verificação de perfis. Os mecanismos fake não demonstram a
conformidade ou a segurança de efeitos pagos na integração futura.

Os efeitos fictícios orçados são independentes da conclusão da busca simulada.
Conectá-los exige coordenação durável, estado para orçamento recusado ou retorno
incerto e tratamento de revogação e replay; a conclusão atual não demonstra
que esses efeitos ocorreram.

Validação local: 48 testes funcionais de serviço, API, concorrência, RLS, replay,
expiração, troca e preservação de seleção, compensação de falha, revogação e
Temporal real local; cobertura combinada isolada de linhas e ramos em 100% nos
nove módulos novos da simulação. Nenhuma chamada paga pela simulação. As migrations
0065–0069 foram aplicadas somente ao banco dedicado `_test`. CI não foi executado
a pedido do titular; a cobertura global não foi verificada.

## Efeitos e reservas fictícios

A simulação privada dispõe de intenções e eventos consumidos pelo Temporal para
três fixtures fechadas que representam Google, Apify e Jev, sem acesso externo.
O HMAC vincula a intenção aos seus parâmetros fictícios; a chave configurada deve
permanecer a mesma até drenar todas as intenções pendentes. Se ela estiver ausente
ou diferente, a tentativa não inicia novo efeito. Uma tentativa anterior pode já
ter reservado orçamento: o hold é mantido, e o processamento só pode prosseguir
depois de restaurar a chave. Versionamento e rotação de chaves estão pendentes
antes de uso durável real.

A política de custos é global e versionada, só aceita UTC nesta etapa e inicia sem
versão ativa. Ela conserva reservas incertas entre meses; uma repetição do mesmo
claim reconhece a reserva admitida mesmo se o acesso for revogado durante a
espera. Após a revogação não se admite etapa nova, mas a etapa já iniciada pode
ser concluída. Sem evidência verificável, o worker não pode liquidar a reserva
nem declarar custo zero. A reserva é um limite conservador de exposição, não
garantia da fatura; cobranças externas podem pertencer a outro mês ou superar a
estimativa, inclusive valores de plataforma fora do limite de um actor do Apify.

## Preparação da integração Places

O teto de até US$ 5 autorizado para o primeiro teste controlado é compartilhado
entre fornecedores e não ativa por si só uma política financeira. Antes de uma
chamada real, a reserva precisa vincular por identidade e hash todos os
parâmetros efetivos e o custo estimado correspondente, e o teto do ensaio precisa
valer mesmo atravessando meses. O guardião isolado atual de Places recebe só a
identidade da operação; ainda não comprova vínculo com todos os parâmetros.

Um replay concorrente não deve encerrar a tentativa original enquanto seu
executor aguarda resposta. A futura integração precisa de executor com identidade
e fence duráveis, estado incerto para tentativa órfã e testes de concorrência e
queda, sem repetição automática de uma chamada potencialmente cobrada. Inputs
transitórios do Google, incluindo estrelas e contagem, não devem ser gravados em
argumentos ou resultados do Temporal, eventos, logs ou ledger; cálculo e
sanitização precisam ocorrer antes da saída da fronteira de efeito. Esses
controles permanecem pendentes: o fluxo fake não os comprova para HTTP real.
