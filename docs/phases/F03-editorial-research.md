# F03 — Pesquisa, temas e planejamento proativo

Status: Em implementação; F03.1, F03.2a e partes de F03.2c entregues localmente. F03.3 tem roteiro e revisão local, ainda sem benchmark comercial.
Dependências: F01, F02.

Entrega local F03.3: roteiro estruturado de até três cenas a partir do
material e dos fatos confirmados, conforme a sequência no [índice das fases](README.md). F03.2a já
produz uma ideia inicial, mas F03.2b decidiu não ativá-la comercialmente após
encontrar linguagem não fundamentada nos fatos confirmados. F03.2c cobre parte
do diagnóstico administrativo, sem completar o percurso inteiro. F03.3 deve
melhorar e avaliar a ideia e gerar cenas, fala/texto, CTA, fonte de cada fato e
validade, com versão e revisão pelo proprietário; ainda não renderiza ou publica.
Testes usam a entrada F02 com webhooks assinados e mídia sintética, mesmo com a
Meta indisponível. Um mock não dispensa smoke real antes da operação comercial.

Aceite da F03.3: uma foto com legenda e uma mensagem de preço confirmada, vindas
de webhook sintético assinado e vinculadas ao mesmo negócio, chegam à biblioteca;
o proprietário solicita um roteiro que cita somente fatos vigentes e os materiais
autorizados. A UI mostra cenas e fontes para edição/aprovação. Material sem fato
confirmado pede informação em vez de publicar uma afirmação. Replay, concorrência,
revogação de consentimento e conteúdo de outro tenant não criam roteiro válido.
Nenhuma peça é renderizada ou publicada nesta entrega.

Implementação local F03.3: o modelo escolhe formato e ordem das cenas em JSON
estrito; o serviço monta texto da cena factual exclusivamente de fatos vigentes do
snapshot fixado. Uma foto ou vídeo autorizado pode aparecer como cena de material;
áudio e texto entram como referência, sem fingir que são imagem. Cada cena expõe
IDs de fatos e material, e a UI permite ao proprietário aceitar o roteiro ou pedir
ajustes com uma observação. A decisão é única, idempotente por operação, serializada
por bloqueio de linha, auditada e isolada por tenant. Aceitar o roteiro não é
autorizar produção ou publicação. A ausência de fato confirmado continua bloqueando
o pedido antes da chamada paga; fatos vencidos são excluídos do contexto.

Gaps: edição direta de cenas e ciclo automático de nova versão após pedido de
ajustes ainda não existem; o proprietário pode alterar fatos e solicitar novo
roteiro. Não há leitura visual da imagem, avaliação humana em lote nem benchmark
PT-BR que libere qualidade comercial. O teste Meta externo aguarda WABA liberada.
F04 deve usar esta estrutura para renderizar peça de foto/cartão com legenda e
prévia; vídeo e avatar são incrementos posteriores. A passagem de F03.3 para F04
não equivale a ativar geração automática para clientes reais.

### F03.3b — Edição e avaliação comercial do roteiro (planejada antes do piloto)

- Permitir corrigir cenas, texto na tela, fala e CTA na web; pedidos de ajuste
  recebidos pelo WhatsApp, quando o fluxo F06 existir, usam o mesmo versionamento.
  Preservar a origem dos materiais, IDs de fatos, validade, contexto e autor da
  alteração em cada versão. Revalidar
  afirmações comerciais após qualquer edição; texto livre editado não transforma
  hipótese em fato confirmado.
- Cada revisão recebe ID/hash próprios. Aceite de versão anterior não migra para
  a nova, e aprovação de uma peça renderizada nunca migra para outra versão.
  Concorrência, replay e pedido de ajuste durante render/agendamento deixam uma
  única versão elegível; as demais não podem seguir para publicação.
- Ampliar o conjunto PT-BR com negócios e materiais consentidos, incluindo
  preço vencido, promoção ambígua, foto sem descrição e alegação inventada.
  Comparar baseline e modelos em revisão humana, correções, abstenção, latência e
  custo por roteiro aprovado; declarar critérios de aprovação antes da avaliação.
  A ativação comercial exige evidência de qualidade e segurança factual, não só
  testes automatizados ou aceite técnico da API.

Seleção de modelo da F03.3 (24/10/2026): o padrão local `gpt-5-mini` permanece
configurável para compatibilidade, mas [está marcado como deprecated na documentação
oficial](https://developers.openai.com/api/docs/models/gpt-5-mini). Antes de escolher
um novo padrão, comparar ao menos o baseline sem IA, `gpt-6-luna` e `gpt-6.1-sol`
com o mesmo conjunto PT-BR de mensagens e roteiros, incluindo afirmação inventada,
abstenção, utilidade, revisão humana, latência, tokens totais e custo por roteiro
aprovado. A [documentação atual de modelos](https://developers.openai.com/api/docs/models)
classifica Luna para volume sensível a custo e Sol para equilíbrio entre capacidade
e custo; isso é ponto de partida, não evidência de qualidade neste produto. O
modelo vencedor deve ter versão fixada após os testes; nenhuma troca automática
por novidade ou preço por token isolado. Revalidar preços, API e disponibilidade
antes de ativar cada fornecedor em produção.

## Objetivo

Pesquisar referências permitidas e produzir ideias/roteiros úteis mesmo sem material novo no dia.

## F03.1 — Contexto confirmado e versionado (entregue localmente)

O proprietário registra até 20 fatos por negócio, com tipo, declaração, origem
informada e validade. Preços, horários e ofertas exigem validade; fatos vencidos
continuam no histórico, mas uma proposta futura não poderá usá-los como atuais.
Preferências de objetivo, tom, frequência semanal e assuntos a evitar ficam em
campo separado. Hipóteses são uma categoria distinta e permanecem vazias nesta
fatia: texto vindo do WhatsApp, transcrição ou pesquisa não vira fato confirmado.

`GET/PUT /api/v1/organizations/{tenant_id}/businesses/{business_id}/editorial-context`
consulta e substitui o snapshot. O PUT exige `expected_version` e `operation_id`;
o banco faz compare-and-swap, registra cada versão imutável e audita no mesmo
commit. Repetir a mesma operação devolve a versão original; mesmo ID com outro
conteúdo e edição baseada em versão antiga retornam 409. Histórico limitado a 20
versões recentes, leitura por versão e restauração explícita estão na mesma API.
A restauração cria nova versão; não apaga o histórico. RLS e autorização de owner
protegem os dois registros por tenant/negócio. A web oferece edição, correção e
restauração, com conflito de versão visível.

Não há chamada paga nem inferência nesta fatia. F03.2 consumirá um snapshot
fixado, separará propostas e fatos e só então integrará um provedor de texto com
consentimento, orçamento e eval. Pesquisa de referências, raio e agendamento
proativo também continuam pendentes. A WABA Meta restrita não bloqueia a edição
manual do contexto, mas impede homologar ingestão real.

Validação local: 417 testes backend com 100% de linhas/ramos, Ruff e mypy;
concorrência, replay, autorização e isolamento em PostgreSQL real. Migration 0021
revertida/reaplicada no `_test` e aplicada ao desenvolvimento após backup
verificado. Web: 158 testes com 100% nos quatro critérios, build, formatação e
jornada Chromium de salvar/restaurar.

## F03.2a — Sugestão editorial revisável (entregue localmente)

O proprietário solicita uma ideia por negócio a partir de um material preparado
do WhatsApp ou dos fatos confirmados. A API grava o pedido com `operation_id`,
versão fixa do contexto e fonte opcional. Um dispatcher com lease/fencing usa ID
determinístico no Temporal; a activity executa uma vez. O mesmo pedido devolve o
mesmo resultado e a concorrência não duplica uma chamada paga. A lista do dono
mostra estado, data, versão, formato, ângulo, fatos referidos, hipóteses e perguntas.
Não existe aprovação nem publicação nesta fatia.
O conteúdo legível nesta fatia é texto de mensagem, legenda de mídia ou áudio
transcrito; imagem/vídeo sem texto não é analisado. A interface só oferece
materiais com texto disponível.

Sem provedor configurado, `baseline-v1` monta uma sugestão local simples, sem
enviar conteúdo externo. Com `MEU_BRACO_DIREITO_EDITORIAL_AI_MODE=openai`, o worker
usa a Responses API com JSON Schema estrito, `store=false`, sem ferramentas, modelo
configurável (padrão `gpt-5-mini`) e resposta limitada. O dono deve aceitar um
consentimento separado para texto/contexto; recepção de material e transcrição
de áudio não autorizam esse envio. A ativação exige chave e limite diário de
reserva de pelo menos 30 mil tokens. Antes da chamada, uma transação com lock por
tenant reserva teto conservador no ledger; o retorno registra tokens observados.
Submissão incerta não é repetida automaticamente. Revogação de consentimento ou
plano, fonte excluída e fatos vencidos impedem usar o resultado. Pedir exclusão
do material remove no mesmo commit todas as sugestões derivadas dele. Ideias
expiram em 30 dias, quando o reconciliador apaga os registros.
O contrato de `text.format` e `store=false` segue a
[documentação oficial de Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
e o [guia da Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses).

O modelo recebe apenas o snapshot confirmado ainda válido e o texto selecionado;
material é tratado como dado não confiável. IDs de fatos, números não apoiados e
assuntos a evitar passam por guardas determinísticas. Isso não prova que toda
afirmação em linguagem natural é verdadeira: a ideia é um rascunho para revisão.
Hipóteses permanecem separadas e não alteram `BusinessContext`. Não há uso de
Jev, busca externa, classificação de intenção persistida ou disparo automático
por novo WhatsApp. A WABA de teste bloqueada segue impedindo o smoke Meta real.

Validação: 442 testes backend com 100% de linhas/ramos, Ruff/mypy, migration 0022
revertida/reaplicada no `_test` e aplicada no desenvolvimento após backup
verificado. PostgreSQL com papéis restritos, RLS, replay, concorrência,
orçamento e falhas incertas; testes de contrato do provedor sem chamada paga
real. Web: 167 testes/100% em quatro critérios, typecheck, build, formatação e
jornada Chromium de `/app/ideas` com API simulada. Workers reconstruídos e
em execução; reiniciar API em debug para ler a rota nova. O teste real do
provedor e avaliação PT-BR por coorte continuam
pendentes antes de qualquer ativação comercial. Preço/token em moeda e COGS real
dependem de tarifas vigentes e serão medidos na F03.2b, sem supor custo fixo.

## F03.2b — Avaliação técnica concluída; ativação comercial bloqueada

Atualização de 23/10: material sem nenhum fato vigente confirmado agora produz
`EDITORIAL_FACTS_REQUIRED` no worker, sem reserva/cobrança do provedor. A web
bloqueia a criação nesses casos e orienta o dono a confirmar um fato no contexto.
O runner `--live` não chama o provedor nos dois casos sintéticos sem fatos.
Isso elimina a inferência observada nesses dois cenários, mas não demonstra
ausência de afirmações inventadas quando há fatos: a revisão humana continua
necessária. O gate comercial segue fechado até avaliação por coorte consentida,
comparação de modelos com preço vigente e smoke em staging.

Nova rodada sintética `gpt-5-mini` em 23/10: 3/3 chamadas elegíveis retornaram
JSON válido e passaram os guardas automáticos; 2/2 materiais sem fato exigiram
confirmação sem chamada. Foram 821 tokens de entrada e 1.335 de saída. Revisão
manual dos três rascunhos encontrou linguagem promocional e contexto não
confirmado, como “promoção”, “horário de pico” e “ambiente acolhedor”. Logo,
**decisão desta avaliação: não ativar o provedor para clientes**. O fluxo pode
ser testado com material sintético, mas o critério de segurança semântica não
foi atingido. Próxima iteração da F03.2b deve mudar o contrato do rascunho para
separar afirmações factuais de sugestões hipotéticas verificáveis, ampliar o
conjunto de casos e passar por revisão humana antes de qualquer coorte.

Correção local seguinte: o título e o ângulo entregue ao proprietário agora são
montados deterministicamente a partir do primeiro fato vigente confirmado. O
modelo só escolhe formato e fornece hipóteses/perguntas marcadas para revisão;
suas afirmações livres em título/ângulo não são persistidas como sugestão. A
validação exige ao menos um ID de fato válido citado pelo modelo. Essa guarda
remove o risco identificado da superfície factual, mas reduz a diversidade do
texto. **Não interpretar como aprovação comercial**: utilidade, hipóteses,
revisão humana e testes em staging ainda precisam de critérios de aceite.
Na rodada após a guarda, 3/3 propostas elegíveis passaram pelos guardas e
2/2 casos sem fatos foram bloqueados sem chamada; 821 tokens de entrada e
1.466 de saída. Os três ângulos efetivamente entregues continham somente o
fato confirmado usado como fonte, mesmo quando o texto bruto do modelo trouxe
adjetivos ou ofertas não confirmadas.
O fechamento desta fatia é um **no-go de ativação**: credencial, contrato,
orçamento, ledger, abstinência e isolamento foram exercitados; qualidade
semântica e utilidade ainda não justificam coorte comercial. A avaliação
consentida por coorte e o staging são gates do piloto, não liberação implícita.

Criar conjunto de avaliação PT-BR com materiais consentidos/sintéticos de
segmentos distintos e casos de abstention; comparar baseline e modelo em acerto,
fatos inventados, utilidade, latência e custo. Validar credencial/modelo em
sandbox, observar limites por tenant e só então habilitar coortes. Integração
Jev permanece experimental até contrato/API, benchmark e disponibilidade serem
verificados. Pesquisa por raio e planejamento proativo serão fatias posteriores.
O assistente de conversa editorial no WhatsApp segue o contrato da
[F02](F02-whatsapp-ingestion.md); sua classificação/extração deve entrar no
mesmo conjunto de eval antes de ativar respostas automáticas.

Primeiro smoke de 23/10/2026 com dados **sintéticos**, sem conteúdo de cliente:
a credencial respondeu, mas o limite anterior de 800 tokens foi consumido pelo
raciocínio sem saída visível. O adapter agora usa esforço `low`, limite 1200 e
JSON Schema com tamanhos compatíveis com `ProposalDraft`. O conjunto versionado
`docs/evals/editorial-ptbr-v1.json` cobre manicure, preço confirmado, preço e
agenda sem confirmação, e instrução maliciosa em material. Execute
`uv run python -m scripts.evaluate_editorial` para baseline sem custo ou acrescente
`--live` para no máximo cinco chamadas pagas sintéticas. O relatório completo fica
em `.local/evals/`, fora do Git; nenhum conteúdo de cliente é incluído.

Na última rodada, 5/5 respostas foram estruturadas e 5/5 passaram pelos guardas
automáticos de IDs, números e assunto evitado. Foram 1.276 tokens de entrada e
1.945 de saída, cerca de US$ 0,0042 para a rodada às tarifas publicadas do
[`gpt-5-mini`](https://developers.openai.com/api/docs/models/gpt-5-mini) em
23/10/2026 (sem incluir chamadas diagnósticas). Latência observada
entre 3,2 e 9,8 segundos. Esses guardas não medem verdade semântica: uma sugestão
para agenda sem fato confirmado insinuou tipo de atendimento não informado.
Comparação pontual com o mesmo conjunto e prompt usando
[`gpt-5.4-mini`](https://developers.openai.com/api/docs/models/gpt-5.4-mini):
5/5 saídas estruturadas, 4/5 nos guardas (preço sem confirmação foi recusado),
1.276 tokens de entrada, 1.509 de saída, cerca de US$ 0,0077 na tarifa publicada,
latência entre 3,1 e 4,8 segundos. A amostra é pequena e nenhum modelo está
escolhido para produção.
Portanto **não liberar coorte comercial**. Antes: ampliar eval PT-BR e revisão
humana, endurecer abstention para material sem fato confirmado, comparar outros
modelos atuais (a documentação do `gpt-5-mini` o marca como deprecated), registrar preço
vigente e fazer smoke via serviço/ledger/Temporal em ambiente isolado. O worker
local já recebeu `EDITORIAL_AI_MODE=openai` pela configuração do ambiente; no
fechamento havia zero consentimentos ativos, zero pedidos em andamento e zero
propostas OpenAI persistidas. Esta avaliação chamou o adapter diretamente com
dados sintéticos; não houve uso de dados reais.
Validação do código: `make ci` passou com 442 testes, 100% de linhas/ramos,
Ruff e mypy. O runner é uma ferramenta sintética explícita; não é um gate de
qualidade suficiente para liberar clientes.

## F03.2c — Aprendizado por negócio e diagnóstico operacional (planejado antes do piloto)

Primeira fatia implementada em 23/10: endpoint de leitura
`GET /api/v1/admin/editorial-operations?tenant_id=…&limit=…` para staff, com
auditoria e função SQL de projeção restrita, lista até 100 pedidos recentes.
RLS continua bloqueando leitura cruzada direta das tabelas. Projeta IDs, estado,
erro estável, versão do contexto/modelo, tokens reservados/observados e datas.
`estimated_cost_minor=null` significa que ainda não existe tarifa versionada
nem custo monetário confiável. Não retorna texto do material, prompt ou rascunho.
O painel web `/admin/editorial-operations` mostra 25 registros recentes e filtro
por organização. É apenas o trecho de geração de ideias; timeline unificada,
tentativas por etapa, agregações além da quota editorial, feedback por negócio e acesso restrito
ao conteúdo permanecem nesta fase antes do piloto pago.
Validação local: `make ci` passou com 443 testes e 100% de cobertura de linhas e
ramos; migration 0023 reversível no banco exclusivo `_test`, base de
desenvolvimento migrada após backup verificado. Web: 170 testes e 100% nos
quatro critérios, typecheck/build e Chromium em viewport mobile.

Segunda fatia em 23/10: novos eventos `editorial.proposal_*` usam o ID interno
único do pedido como chave de auditoria, associado ao `operation_id` externo
na projeção. Isso evita misturar dois negócios que reutilizem o mesmo ID externo;
reentregas da mesma transição não criam outro marco. O claim registra `dispatching` na mesma
transação que muda o estado. A migration 0024 expõe função SQL `SECURITY DEFINER`
restrita a staff para consultar somente ação e data de eventos de um pedido.
`GET /api/v1/admin/editorial-operations/{proposal_id}/events` audita a leitura;
o painel mostra essas etapas sob demanda. Pedidos anteriores à mudança podem
ter histórico incompleto: a API não reconstrói eventos nem apresenta tempos
inferidos. A visão ainda cobre somente geração editorial; correlação com
webhook, transcrição, publicação, custos monetários, alertas externos e feedback seguem
pendentes nesta fase.
Validação da segunda fatia: `make ci` com 443 testes e 100% de linhas/ramos;
migration 0024 revertida/reaplicada no banco `_test` e aplicada à base local
após backup. Teste de integração cobre dois negócios com mesmo `operation_id`
externo sem cruzamento de etapas e revogação de staff.

Terceira fatia em 23/10: migration 0025 adiciona a projeção
`admin_editorial_usage_today` restrita a staff, limitada a 100 organizações e
indexada por data. `GET /api/v1/admin/editorial-usage` audita a leitura, aceita
filtro por organização e retorna reservas, tokens observados, quantidade de
chamadas com medição completa, pendentes e incertas no dia UTC. O limite atual
de tokens configura os estados normal, aviso em 80%, esgotado em 100% e sem
configuração. A soma observada pode ser parcial e não equivale a custo; a API
mantém `estimated_cost_minor=null`. A consulta não retorna conteúdo privado.
O painel exibe alertas de quota por organização. Não há ainda custo em moeda,
alerta automatizado fora do painel, paginação além dos 25 maiores consumidores,
nem composição de todas as etapas do WhatsApp à publicação.
Validação: `make ci` com 444 testes, 100% de linhas/ramos, Ruff e mypy;
migration 0025 aplicada no banco `_test` e na base local após backup.

Materiais WhatsApp conservam a retenção da F02 (inbox/fila curta, asset preparado
com prazo inicial de 30 dias); a plataforma não guarda a conversa inteira para
sempre nem usa toda mensagem automaticamente como dataset. O `BusinessContext`
versionado guarda fatos confirmados e preferências explícitas por negócio; sinais
de correção, aprovação/rejeição e desempenho podem virar hipóteses separadas,
revisáveis e expiráveis. Chamar isso de personalização/contexto, não de treino ou
"skill" executável por tenant. A cada geração, recuperar somente fatos atuais,
preferências e materiais relevantes com orçamento de tokens; persistir histórico
sozinho não reduz tokens. Medir tokens e qualidade antes de introduzir resumo,
cache por tenant ou modelo treinado. Evals globais começam com casos sintéticos;
amostras reais exigem finalidade, direitos, controle de acesso, retenção e
autorização específicos. Não misturar conteúdo privado entre negócios.

Antes de piloto pago, criar uma visão administrativa por `operation_id` que una
webhook, correlação, material, transcrição, classificação, pedido, workflow,
activity, chamada de modelo, validações, revisão e publicação. Cada etapa mostra
estado, início/fim, tentativas, erro estável, versão do contexto/modelo/prompt,
tokens reservados/observados, custo estimado/real quando conhecido e IDs de
proveedor; incerteza e custo desconhecido devem ser explícitos. Agregar gasto por
tenant, fase, fornecedor e período com alertas de orçamento. Logs e traces usam
IDs e metadados permitidos, nunca prompt, resposta integral, telefone ou mídia.
Para diagnosticar uma sugestão errada, o admin pode abrir o material e rascunho
persistidos por caminho **separado**, com papel de suporte específico, motivo,
escopo, expiração e leitura auditada; ocultar por padrão, proibir busca global
por conteúdo e respeitar exclusão/retenção. O cliente vê seu próprio histórico
e pode corrigir o contexto. Console mínimo entra nesta F03.2c; F08 amplia SLO,
tracing distribuído e operação em escala. Estado atual: auditoria, ledger e IDs
existem em partes do backend; a UI admin cobre apenas a geração de ideias, e o
percurso unificado ainda não existe.

## Features e contratos

- Contexto de fatos, objetivo e materiais autorizados; ideias com fontes e validade.
- Raio configurável, candidatos a concorrente/referência e correção pelo comerciante.
- Google Places/Tavily respeitam permissões e retenção; dados privados não viram cache compartilhado.
- Roteiro e plano de cenas estruturados; preferências de frequência, gasto e mensagens.
- DecisionProvider com baseline; Jev em shadow/eval PT-BR antes de ativar.
- `BusinessContext` compacto e versionado por tenant/negócio: fatos confirmados
  com origem/validade, preferências explícitas e padrões hipotéticos separados.
  Snapshot fixado em cada proposta/roteiro; dono pode inspecionar, corrigir e
  restaurar versões. Atualizações concorrentes usam CAS, evento único e auditoria.
- Montar apenas contexto necessário e fontes autorizadas; registrar tokens/custo
  reais e comparar qualidade/custo com baseline antes de alegar economia. Entrada
  externa não é instrução confiável para o agente.
- Implantar reserva atômica de quota/COGS antes de qualquer pesquisa ou chamada de
  modelo paga nesta fase, inclusive propostas proativas sem material do dia.

## Critérios de aceite e testes

- Fontes ausentes/expiradas não viram fatos ou métricas inventadas.
- Sem dados novos, sugestão contextual; silêncio nunca autoriza publicação.
- Teste de orçamento de pesquisa e admissão por coorte, sem cron simultâneo de 200 mil.
- Medição de custo, acerto, abstention e fallback de modelos.
- Aprovação posterior de uma peça não confirma fatos comerciais usados nela;
  preço/promoção/horário vencidos ou não confirmados bloqueiam a sugestão factual.

## Limites e decisões pendentes

- Fonte pública não dá acesso a métricas privadas da concorrência.
- Não compartilhar ou treinar com conteúdo sem direitos compatíveis.

## Integração e manutenção

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.

## Interfaces e transparência

Propostas e referências aparecem no WhatsApp e, quando disponível, na área do
cliente. Admin vê estado operacional e consumo, não segredos. Fonte, data, fatos
e limites de gasto acompanham sugestões. Entrega depende dos SDDs web admin/cliente.
