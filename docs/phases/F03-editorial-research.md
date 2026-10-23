# F03 — Pesquisa, temas e planejamento proativo

Status: Em implementação; F03.1 e a primeira fatia da F03.2 entregues localmente em 23/10/2026.
Dependências: F01, F02.

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

## F03.2b — Avaliação e ativação controlada (pendente)

Criar conjunto de avaliação PT-BR com materiais consentidos/sintéticos de
segmentos distintos e casos de abstention; comparar baseline e modelo em acerto,
fatos inventados, utilidade, latência e custo. Validar credencial/modelo em
sandbox, observar limites por tenant e só então habilitar coortes. Integração
Jev permanece experimental até contrato/API, benchmark e disponibilidade serem
verificados. Pesquisa por raio e planejamento proativo serão fatias posteriores.
O assistente de conversa editorial no WhatsApp segue o contrato da
[F02](F02-whatsapp-ingestion.md); sua classificação/extração deve entrar no
mesmo conjunto de eval antes de ativar respostas automáticas.

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
