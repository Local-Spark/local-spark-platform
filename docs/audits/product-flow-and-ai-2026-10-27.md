# Auditoria de produto, código e IA — 27/10/2026

Estado: navegação e limpezas P1–P15 aprovadas e implementadas localmente, com
verificação concluída. Melhorias futuras dependem de suas fases e decisões próprias. Esta auditoria antecede BL03 e não autoriza
remoções em lote.

## Método e limites

Foram inspecionados rotas, componentes, serviços, workers, migrações e SDDs
dos dois repositórios. A busca de chamadas distingue código executado, código
restrito a desenvolvimento e estruturas sem consumidor no projeto. Não houve
consulta a mensagens ou arquivos privados de clientes. A ausência de chamadas
no código não equivale a medição de uso por clientes em produção.

A configuração local consultada sem mostrar segredos usa
`editorial_ai_mode=openai`, `editorial_ai_model=gpt-5-mini` e
`audio_transcription_mode=disabled`. Nenhuma chamada paga foi feita para esta
auditoria.

## Decisões aprovadas

| Ponto | Aprovação do proprietário do produto | Escopo autorizado |
| --- | --- | --- |
| 1 | WhatsApp com histórico secundário | Renomear “WhatsApp e materiais” para “WhatsApp”; transformar a listagem em “Histórico de envios”, preservando consulta, download, exclusão, retenção e processamento. |
| 2 | Conteúdos e laboratório separado | `/app/content` acompanha propostas/prévias/decisões; `/app/ideas` redireciona; controles manuais de geração, roteiro e renderer ficam em `/app/editorial-lab` somente DEV. |
| 3 | Remover Primeiros passos estático | Remover menu/GuidePage, redirecionar rota antiga e concentrar orientações na página inicial usando estados reais disponíveis, sem completude fictícia. |
| 4 | Consentimento de IA em Sobre meu negócio | Mover o controle de autorizar/retirar IA, preservando o registro e a API existentes. |
| 5 | Negócio ativo compartilhado | Remover seleção e consultas de negócios duplicadas; manter organização/negócio ativo coerentes entre navegação, kits, conteúdo, contexto, telefone e plano. |
| 6 | Telefone como etapa do WhatsApp | Retirar item permanente do menu; continuar correção e verificação SMS no fluxo da conexão, com a rota utilitária e serviços preservados. |
| 7 | Resumo chamado Início | Renomear o overview “Meu negócio” para “Início”; “Sobre meu negócio” mantém configuração e futuro acervo. |
| 8 | Retirar frequência semanal manual da UI | Ocultar “Publicações por semana (0–7)” até a cadência por formato/plano; preservar valor histórico ao editar outras preferências. |
| 9 | Retirar outbox financeira sem consumidor | Migração nova preserva eventos faltantes em `billing_audit` antes de remover `billing_outbox` e sua gravação; manter `billing_jobs`, Stripe e reconciliação. |
| 10 | Retirar helper legado de identidade | Remover `actor_for_subject()` e teste exclusivo; preservar `Identity`, usuários e IDs existentes. |
| 11 | Retirar comando de seed aposentado | Remover `scripts/seed_development.py`, que só encerrava com orientação; usar `scripts/seed_operator.py`. |
| 12 | Retirar declaração Keycloak sem serviço | Remover apenas a declaração do volume no Compose; não apagar volumes ou dados Docker. |
| 13 | Consolidar documentação vigente | PROJECT/SDD/README passam a distinguir estado real e sequência BL; preservar versões integrais anteriores em histórico, specs de fases e evals. |
| 14 | Retirar novos recibos assíncronos de CRUD | Parar emissões `business.created`/`brand_kit.changed` e retirar relay da inicialização automática; manter auditoria transacional, tabelas/handlers e comando legado para compatibilidade. |
| 15 | Avatar após o primeiro piloto | Manter F05 e contratos de identidade/consentimento; retirar avatar dos critérios do primeiro piloto, que valida imagens e vídeos com material real antes. |

As aprovações 1–8 não autorizam apagar tabelas de ingestão, propostas, roteiros,
previews, consentimento, telefone, cobranças ou histórico de auditoria.
P9 autoriza exclusivamente a outbox financeira, com preservação da auditoria.
A migração 0038 foi verificada em banco `_test`; não foi aplicada à base de
desenvolvimento com dados do usuário nesta revisão. Eventos ausentes são copiados
antes do DROP e conflito de tenant interrompe a operação. Executáveis antigos
devem ser atualizados junto da migração, pois ainda tentam gravar a tabela antiga.
P14 mantém compatibilidade com históricos da fundação: retirar emissão nova e
startup do relay não autoriza apagar `outbox_events`, `processed_events` ou
handlers usados por replay. Não há remoção do Temporal ou dos processos úteis.

## O que continua necessário

- `whatsapp_material_events/assets` são recibos temporários de entrada,
  idempotência, processamento, transcrição e retenção. Alimentam F03/F04/F06.
  O acervo BL03 será memória durável, autorizada e estruturada, com promoção
  explícita de material para esse acervo.
- `editorial_proposals`, versões e prévias são usados também pelo workflow
  WhatsApp automático. Tirar o editor da jornada do cliente não elimina esse
  domínio.
- A aprovação da peça final permanece explícita. A revisão intermediária do
  roteiro no caminho manual é um contrato separado que exige avaliação antes
  de retirar endpoints/colunas.
- Pillow/FFmpeg ainda fazem processamento e prévias técnicas. A baixa qualidade
  do template não justifica remover preservação, corte, validação ou extração
  de áudio.

## Propostas ainda sem autorização

| Candidato | Evidência | Recomendação e condição |
| --- | --- | --- |
| Cadência futura | Campo manual retirado após ponto 8; a preferência histórica continua persistida. | Entregar ritmo recomendado dentro da franquia F03/F07; não converter o campo legado em agendamento implícito. |
| Fatos livres de produto/serviço/preço | Contexto atual e confirmação WhatsApp usam fatos; BL03 criará catálogo estruturado. | Definir ligação/conversão progressiva para evitar dois preços contraditórios; manter fatos gerais e proveniência. |
| Aprovação intermediária do roteiro | Render manual exige roteiro aceito; candidata automática usa outro contrato. | Concentrar experiência normal na peça final; revisar separadamente endpoints/colunas ao substituir o caminho manual. |
| `business_profiles.brand_color` | Paleta do kit é a direção futura, mas renderer atual ainda lê a coluna. | Migrar leitura para kit em BL04 e só então avaliar a remoção do campo/coluna. |
| Renderers v4 | São adapters atuais efetivamente chamados; não há uma pilha runtime de v1–v3 abandonados. | Isolar como baseline de laboratório; retirar somente após receita substituta passar nos gates de BL04. |
| `businesses.row_version` | Coluna da fundação sem leitura/escrita no runtime inspecionado; o negócio ainda não tem edição geral implementada. | Decidir junto do contrato futuro de edição se será versão de concorrência real ou coluna removível; não atribuir proteção atual a um contador que nunca muda. |

Migrações Alembic antigas devem permanecer. Remoção aprovada de tabela ou coluna
será feita por uma revisão nova, após avaliar leitura/escrita, dados e
compatibilidade. `billing_outbox` era escrita sem consumidor e sua remoção foi aprovada no ponto 9;
as tabelas gerais de outbox/recibos têm consumidor e não estão autorizadas para remoção.

## Avaliação da IA atual

A implementação atual tem três limitações relevantes para produto e custo:

1. `editorial_conversation.classify()` usa regex para preço de hoje e
   disponibilidade de horário. Pedidos livres fora desses padrões não são
   interpretados por LLM. Isso é capacidade ainda faltante, não código morto.
2. `OpenAIEditorialProvider.propose()` faz uma chamada Responses com JSON
   Schema e `tools=[]`. Não há hoje loop de ferramentas para consultar
   acervo/pesquisa ou execução de skills por negócio.
3. `EditorialProposalService._ground()` substitui título e ângulo criativos
   por baseline; `_script()` monta frases fixas a partir do primeiro fato.
   Portanto, trocar fornecedor não corrige sozinho a falta de variedade.
   A melhoria proposta é preservar fatos exatos e permitir criatividade nos
   campos adequados, com fontes e eval, sem retirar as guardas comerciais.

O ledger atual mede tokens/reservas/resultado incerto. O admin ainda devolve
`estimated_cost_minor=None`; o custo completo por peça aceita e por cliente
não está comprovado.

## Cowork, APIs e arquitetura — parecer preliminar

Cowork já oferece tarefas agendadas e acesso a skills/conectores. A documentação
atual descreve execução remota, com exceções para tarefas que dependem de recursos
locais. É uma ferramenta útil para curadoria e operação da equipe.
[Agendamentos Cowork](https://support.claude.com/en/articles/13854387-schedule-recurring-tasks-in-claude-cowork).

Para integrar um agente no SaaS, há alternativas reais por API:
[Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview)
e [OpenAI Agents API](https://developers.openai.com/api/docs/guides/agents-api/overview).
Ambas oferecem harness gerenciado; adotá-las deve ser comparado com chamadas
diretas/SDK usando tarefas reais. Não assumir que uma assinatura de interface
ou um scheduler substitui autorização, RLS, franquia, aprovação de peça e
estados financeiros do produto.

Recomendação ainda não implementada: manter Temporal responsável pelo processo
durável e prazos de negócio; usar chamadas diretas/um loop curto de ferramentas
dentro de atividades para interpretar e gerar; avaliar harness gerenciado para
pesquisa/curadoria multietapas quando houver ganho medido. Não há evidência
atual para trocar toda a arquitetura ou manter um agente autônomo permanente
por cliente.

Skills devem empacotar procedimentos/receitas reutilizáveis da plataforma;
dados e preferências do cliente ficam no contexto versionado e são recuperados
sob autorização. A documentação de
[Skills da Anthropic](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
explica carregamento progressivo. Isso não equivale a treinar o modelo nem
garante economia sem medição.

## Modelos e teste de qualidade/custo propostos

O modelo local `gpt-5-mini` aparece como deprecated na
[documentação oficial](https://developers.openai.com/api/docs/models/gpt-5-mini).
A seleção deve ser reavaliada antes de produção; nenhuma configuração foi
alterada por esta auditoria.

Candidatos para benchmark, não vencedores aprovados:

- Interpretação curta, extração e roteamento: [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)
  e [Claude Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview).
- Direção criativa/roteiro e análise visual: [GPT-6.1 Terra](https://developers.openai.com/api/docs/models/gpt-6.1-terra)
  e Claude Sonnet 5.5; escalar para modelos mais caros somente em falhas
  demonstradas pelo eval.
- Áudio de WhatsApp: o adapter usa `gpt-transcribe`, mas está desativado na
  configuração local consultada. O [modelo atual](https://developers.openai.com/api/docs/models/gpt-transcribe)
  e seu custo devem entrar no benchmark; tornar a seleção configurável.
- Imagem/vídeo/avatar são capacidades próprias. Os modelos Claude atuais têm
  texto/imagem de entrada e texto de saída; podem dirigir ferramentas, mas
  a geração de mídia ainda precisa de motor específico.
  [Modelos Claude](https://platform.claude.com/docs/en/models/overview),
  [geração de imagem OpenAI](https://developers.openai.com/api/docs/guides/image-generation).

Comparar custo por tarefa concluída e peça aceita: input/output/reasoning,
ferramentas, execução, revisões, falhas, armazenamento, mensagens e operação.
A tarifa textual publicada de Luna e Haiku para prompts curtos começa em
US$ 0,10/1M de entrada e US$ 0,50/1M de saída; diferentes tokenizadores,
raciocínio e retentativas podem mudar o resultado real.
[Preço Luna](https://developers.openai.com/api/docs/models/gpt-6-luna),
[preços Claude](https://platform.claude.com/docs/en/about-claude/pricing).

Harnesses têm custos além dos tokens: Managed Agents cobra runtime enquanto
a sessão está rodando, e a Agents API cobra ferramentas/containers aplicáveis.
Não fazer promessa de margem apenas com preço por token.
[Managed Agents — preço](https://platform.claude.com/docs/en/about-claude/pricing#claude-managed-agents-pricing),
[Agents API — preço](https://developers.openai.com/api/docs/guides/agents-api/overview#pricing).

O benchmark proposto usa os mesmos casos PT-BR sintéticos ou consentidos,
contexto/kit e fatos para cada candidato; mede intenção correta, perguntas necessárias, invenções de fatos,
qualidade criativa, fidelidade do produto/local, latência e custo por aceite.
O teto de R$ 50/cliente/mês para o plano de R$ 99 continua meta a comprovar.
Nenhuma troca de modelo, contratação, chamada paga ou alteração do contrato
criativo foi autorizada automaticamente por este parecer.


## Ordem recomendada para corrigir IA e custo

Esta avaliação não implementa nem autoriza automaticamente uma troca de provedor.
A prioridade é corrigir o aproveitamento do modelo e medir o resultado antes de
adotar outra infraestrutura de agentes.

| Entrega | Melhoria proposta | Efeito esperado e verificação |
| --- | --- | --- |
| BL03 | Acervo opcional em Sobre meu negócio e contrato de leitura por tenant/negócio, com fonte, direitos, validade e versão. | Contexto correto e seletivo; evitar produto/local/preço inventado sem tornar catálogo obrigatório por pedido. |
| Início BL04 | Corrigir contrato criativo: manter fatos/valores exatos em campos verificáveis e permitir título, ângulo e roteiro criativos fundamentados. | Parar de pagar pela geração textual e substituí-la por frases fixas; eval negativo continua bloqueando fatos inventados e tópicos proibidos. |
| BL04.1 | Interpretação semântica curta com saída estruturada e poucas ferramentas autorizadas de consulta ao contexto/acervo. | Pedidos livres passam a ser entendidos; perguntar apenas por informação necessária. Não abrir chat genérico nem acesso entre tenants. |
| BL04.2 | Adapter real de imagem/edição, kit aplicado, mídia real autorizada e validação antes do aceite. | Entregar uma peça nova fiel, comparar com composição por receita e medir rejeições/revisões. O teste isolado de imagem ainda não é essa integração. |
| Antes de liberar chamadas pagas da BL04 | Custos monetários por tentativa/operação, tarifas versionadas, resultado incerto e teto de orçamento. | Comparar custo por peça aceita e projetar custo mensal incluindo falhas, sem tratar tokens como custo total. |
| BL04, antes de escolher modelo | Benchmark PT-BR das mesmas intenções/briefings com candidatos OpenAI e Claude; comparar chamada direta/loop curto e harness quando pertinente. | Escolher pela qualidade, fidelidade, latência e custo observado; documentação de preço não determina o vencedor. |
| BL05 | Agenda durável dentro da cadência/plano aceitos, pausa e proatividade usando somente fontes vigentes. | Proposta em dia sem mensagem, sem confundir polling técnico com agendamento editorial. |
| BL06/F07 | Curadoria por nicho, pesquisa com fontes autorizadas e franquias com margem medida. | Ampliar o catálogo depois da prova de qualidade e calibrar planos ao custo completo. |

O procedimento reutilizável da plataforma pode ser uma skill versionada. O
perfil/kit/acervo de cada negócio é dado privado, e não exige um agente sempre
ligado ou fine-tuning por cliente. Começar com prompt/contexto compactos e
recuperação seletiva; usar caching e ferramentas somente quando houver economia
medida. Harness gerenciado pode ajudar em pesquisa longa, mas sua adoção deve
ter orçamento, prazo, ferramentas limitadas e responsabilidades de estado claras
para não duplicar orquestração e custos do Temporal.

Comandos inequívocos de confirmação, pausa e revogação continuam determinísticos,
com autorização e efeitos fora do modelo. A camada semântica atende pedidos livres
e ambiguidades, com limite de chamadas; não é necessário invocar um agente longo
para cada mensagem. Ao ativar outro fornecedor, revisar o contrato e a autorização
de envio de dados: a interface atual menciona especificamente a OpenAI. O
benchmark não autoriza encaminhar mensagens reais a outro provedor silenciosamente.

## Verificação final e estado de uso

- Backend: `make ci` passou com Ruff, formatação, mypy e **722 testes**;
  **100% de linhas e ramos**, sem exclusões novas de produção.
- Web: **257 testes** e **100% de linhas, statements, funções e ramos**;
  build/typecheck, Prettier e quatro jornadas Chromium passaram (WhatsApp,
  Conteúdos, laboratório e continuidade do negócio ativo entre telas/celular).
  O build de produção não disponibiliza o editor manual DEV.
- Migração 0038: cópia de lacunas, histórico/auditoria existente, isolamento,
  conflito de tenant e rollback verificados somente na base dedicada `_test`.
  A base de desenvolvimento do usuário ainda precisa do upgrade para 0038 ao
  adotar o código novo; coordenar atualização da API/processo de cobrança.
- Novas mutações de negócio/kit não emitem os recibos legados; testes continuam
  exercitando seus handlers e relay com fixtures históricas explícitas.
- Sem commit/push/deploy, geração paga, troca de modelo ou remoção adicional de
  tabela. BL03 não foi iniciada. Nenhuma aprovação individual P1–P15 ficou pendente.

O gate passou com aviso já existente de depreciação Starlette/httpx. O build web
avisou sobre o bundle principal acima de 500 kB minificado; divisão adicional de
rotas pode ser avaliada na etapa de desempenho, sem ocultar esses avisos ou mudar
os gates nesta revisão.
