# Meu Braço Direito — contexto vigente

Atualizado em **28/10/2026**. Este documento resume o produto, o estado local e
as decisões aceitas. O [SDD](SDD.md) define os contratos; a
[trilha BL](phases/BL-brand-library.md) e o [índice de fases](phases/README.md)
definem a sequência. Registros cronológicos anteriores foram preservados
integralmente no [histórico da consolidação](history/2026-10-27-pre-consolidation/index.md).
Uma entrega técnica local não equivale a uma capacidade comercial homologada.

## Produto e resultado esperado

Pequenos negócios enviam texto, foto, áudio ou vídeo pelo WhatsApp; o sistema
usa contexto confirmado, kit visual e material autorizado para produzir conteúdo
útil, pedir aprovação simples, publicar nos canais habilitados e acompanhar
resultados observáveis. Também deve propor conteúdo quando o cliente não enviar
material novo, dentro da cadência aceita e da franquia. A rotina não exige saber
usar editor, escrever prompt ou conhecer modelos de IA.

**Decisão de produto posterior:** os materiais enviados pelo cliente devem ser
preservados para compor o contexto do seu negócio. O histórico de envios do
WhatsApp não oferece exclusão de texto, foto, áudio ou vídeo; se não gostar de
uma peça, o cliente pode enviar outro material. O acervo em Sobre meu negócio é diferente: o cliente pode remover
fotos desatualizadas, como as de uma loja que mudou de aparência. Guardar material e construir uma memória ou skill utilizável são
etapas diferentes: a incorporação automática ao contexto ainda precisa ser
implementada. A [proposta de preservação](design/BL04-whatsapp-durable-materials.md)
detalha a mudança e sua implantação coordenada. Prazo após encerramento da conta, descarte técnico e outras ações
de gestão de dados não foram definidos por essa decisão.

**Decisão de produto atual:** IA é parte do serviço contratado. A contratação
apresenta uma explicação e termos únicos; não pedir que o cliente habilite
OpenAI, TypeSafe, imagem ou transcrição separadamente. Contas já criadas verão
os termos atualizados uma única vez antes de usar o serviço. A API registra um
único aceite explícito e versionado por negócio. Ele é a
autorização contratual para texto, imagem, interpretação e transcrição; os
controles individuais saem da web. Registros antigos são preservados, sem
reativação ou reescrita. Configuração de fornecedores, plano e orçamento
continuam sendo controles internos. A validação completa mais uma rodada de
regressões atingiu 100% de linhas/branches no backend; a web passou 360 testes,
cobertura integral, build e três jornadas Chromium. Evidências no
[CHANGELOG](CHANGELOG.md). A integração visual real segue na BL04.2. Ver
[uso de IA como parte do serviço](design/ai-as-core-service.md).

O proprietário definiu **uma conta e organização por negócio**, com cobrança e
aceite próprios. A cobrança atual é por organização e pode ser reaproveitada;
o código local da API bloqueia outro negócio e a migration correspondente foi
aplicada ao banco de desenvolvimento. O
[desenho atualizado](design/one-business-per-organization.md) registra como
garantir a regra e a situação dos dados locais. Os dois negócios de teste
duplicados foram removidos com autorização e backup; a sequência de migrations
foi aplicada localmente após revisão e aprovação do proprietário.
O reaproveitamento da tabela existente `0056` para o aceite por negócio foi
aprovado; o aceite único usa essa tabela, com POST autenticado, versão/hash e auditoria.
A contratação exige o aceite antes de criar checkout. Contas existentes aceitam
uma vez em Plano e acesso; o registro não confirma pagamento nem liga provedores.

Na versão inicial, cada negócio poderá vincular **um número de WhatsApp ativo**
para conversar com a plataforma. Este é o número do cliente autorizado, distinto
do número oficial do Meu Braço Direito. Aceitar mais de um número por negócio é
uma evolução futura; como vincular pessoas, compartilhar histórico e distribuir
mensagens será decidido nessa etapa. A limitação não restringe o número de contas
proprietárias na web nem resolve a pendência entre proprietários descrita abaixo.

Se o cliente trocar o número enquanto um material já enviado está sendo
processado, o processamento continua para o mesmo negócio. Quando a troca
estiver concluída, a prévia e o pedido de aprovação devem seguir para o número
ativo novo, sem pedir que o cliente espere o processamento terminar para trocar.
O processamento e a entrega simulada usam essa regra em testes locais; o envio
real de prévia e aprovação via WhatsApp ainda não está implementado.

Para vídeo, priorizar a hipótese de orientação de gravação e material real do
negócio: cliente pode solicitar roteiro ou recebê-lo como sugestão consentida.
Original, edição leve e motion são receitas futuras a validar. Vídeo e sua
franquia não integram automaticamente a oferta inicial. Voz sintética é opcional
e posterior ao primeiro piloto; ver [plano de vídeo real](design/video-real-and-voice.md).
O [estudo dos projetos de vídeo e voz](design/video-tool-candidates-2026-10-27.md)
propõe uma POC futura de HyperFrames, com Remotion como alternativa; nenhum foi
integrado ou teve custo e qualidade comprovados no produto. Superpowers é
candidato a apoio de desenvolvimento, não dependência da aplicação.

A web complementa configuração, consentimentos, acervo, kits e revisão. O cliente
pode ver uma vitrine pública com posts, stories e reel fictícios em simuladores
de Instagram, Facebook e TikTok dentro da nossa plataforma. São arquivos
pré-produzidos uma vez, sem geração paga a cada visitante e sem acesso às contas
sociais do visitante. Escolher um kit não aprova nenhuma publicação.

Aquisição por vídeos longos de entretenimento dos três sócios permanece uma
estratégia comercial. R$ 99/mês é hipótese do plano de entrada; o teto de desenho
é R$ 50 de custo mensal total por cliente. Franquias e margem ainda precisam de
medição. A meta de 200 mil clientes orienta evolução de capacidade, não comprova
escala atual. Alcance e engajamento não comprovam faturamento nem causalidade.

## O que existe e o que ainda falta

| Área | Implementado localmente | Limite atual |
| --- | --- | --- |
| Fundação e identidade | FastAPI, PostgreSQL/RLS, auth própria, sessões, recuperação, e-mail HTML, onboarding, operador com MFA e convites | Staging, operação e segurança de produção ainda precisam de homologação. |
| Cobrança | Stripe Checkout sandbox, webhook assinado, jobs, reconciliação, assinatura de teste e patrocínio separados, painel de oportunidades | Franquias comerciais, custos completos e homologação de produção pendentes. Cadastro não ativa plano. |
| WhatsApp e materiais | Inbox assinada/criptografada, vínculo, correlação, processamento e transcrição; envios associados são preservados sem prazo e não podem ser excluídos pelo histórico | Migration 0058 aplicada localmente; Meta real e uso automático como memória não estão homologados. |
| Contexto e texto | Fatos/preferências versionados, propostas e roteiros, adapter OpenAI, reservas/tokens e projeção administrativa limitada | Não há agente geral, pesquisa automática de concorrentes, skills executáveis por cliente nem geração visual integrada. |
| Kits BL01/BL02 | Vitrine fictícia de cafeteria, seleção por negócio, edição guiada de cores/fontes/logo/textos/composição, prévia, rascunho, confirmação e histórico | Kit `public_demo` somente para teste; direitos e qualidade comercial pendentes. A prévia simulada aplica o kit; a produção real ainda não. |
| Conteúdos F04/F06 | Prévias técnicas estáticas/vídeo, candidata, decisão explícita e publicação falsa com validação de versão/hash | Renderers Pillow/FFmpeg não são receitas aprovadas. Ajuste ainda não regenera automaticamente; envio de candidata e publicação reais pendentes. |
| Acervo BL03 | Cadastro manual versionado de produtos/serviços/promoções e fotos privadas de item/espaço, com cópia consentida de foto WhatsApp, implementados localmente | Importação automática de cardápio é BL03.3 posterior; o acervo alimenta briefing e roteiro experimentais em desenvolvimento/teste, sem geração visual integrada. |
| Produção BL04/BL05 | Worker local pode interpretar com Jev sob o aceite único do serviço e orçamento; briefing privado consulta acervo. A BL04.2 prepara referências e pedido visual e exercita uma prévia simulada privada com reserva e revisão. | Desligado por padrão, somente desenvolvimento/teste; geração real segue bloqueada até fechar atomicidade, orçamento global e tratamento de incerteza. Ainda precisa avaliar qualidade e completar a jornada. |
| Infraestrutura F08 | Compose, CI e workflow de deploy preparado | AWS/staging, backup/restore, observabilidade operacional e capacidade não provisionados/homologados. |

Os ensaios em [evals](evals/) não são features do produto nem aceites comerciais.
A [amostra sintética BL04.2](evals/bl042-guarded-synthetic-feed-2026-10-27.md)
é uma chamada real isolada, com estimativa de custo; não usa o worker do cliente
nem comprova fidelidade, margem ou prontidão comercial.
A [amostra sintética de 28/10](evals/bl042-synthetic-brand-finish-2026-10-28.md)
testa uma cena real de IA com acabamento de kit; também é um ensaio isolado.
Decisão de 28/10: ao solicitar alteração de kit, foto ou contexto durante uma
criação, a mudança deve aguardar os processos já iniciados. A fila ainda não
iniciada deve ser cancelada e novas criações bloqueadas enquanto houver mudança
pendente. A prévia concluída antes da alteração permanece disponível para revisão
e é identificada como criada antes da mudança; sua publicação depende dos direitos
e do fluxo de aprovação aplicáveis.
O modo simulado cobre parcialmente contexto editorial, catálogo de produtos e
serviços, confirmação de kit e inclusão/alteração/exclusão de fotos do acervo; outros escritores de fontes, limpeza
física automática e casos com proprietários diferentes permanecem pendentes.
O provedor real ainda não está conectado. Testes antigos exercitaram a regra
anterior, de alteração imediata e descarte.
O workflow Temporal separado para geração real já tem prazos e uma única
tentativa testados, mas ainda não está conectado ao dispatcher ou ao provedor.
No acervo, o autor pode descartar um upload incerto após vencer a reserva e
liberar o negócio; o objeto fica privado em quarentena, sem limpeza física
automática. A atualização exige drenagem e avaliação de órfãos legados; outro
owner ainda não recupera uma pendência cujo autor perdeu acesso.
A migration 0058 aplicada localmente e o código preservam materiais associados sem prazo
automático; excluem a ação de exclusão do histórico para todos os tipos e mantêm
a limpeza técnica de eventos não atribuídos e uploads órfãos. A implantação local
ocorreu após pausa e backup; objetos já apagados não podem ser recuperados.
A política geral de retenção das prévias não foi definida por essa mudança.
O ledger também possui teto mensal agregado para reservas OpenAI, separado do
teto por tenant; não limita despesas fora do próprio ledger e não ativa o worker.
A consulta a um perfil público não concede direitos sobre material ou aprovação
da titular. Custos de poucas chamadas isoladas não comprovam custo mensal.

## Experiência aprovada na web

| Área do cliente | Finalidade |
| --- | --- |
| Início | Resumo e orientações com estados reais do perfil, sem página estática de passos. |
| WhatsApp | Situação do canal, telefone/SMS e vínculo; histórico preservado de envios como consulta secundária. |
| Sobre meu negócio | Fatos/preferências e acervo opcional de Produtos e serviços e Meu espaço. |
| Conteúdos | Acompanhar propostas/prévias e decisões disponíveis; alternativa à aprovação pelo WhatsApp. A simulação é identificada. |
| Kits visuais | Explorar, escolher e editar a direção visual aplicada ao negócio. |
| Plano e acesso | Aceite único do serviço, assinatura, patrocínio e situação de acesso. |

Organização e negócio ativos são compartilhados entre as telas, com seleção em
memória; autorização permanece na API/RLS. `/app/content` é a rota vigente;
`/app/ideas` redireciona para ela e `/app/guide` para Início. `/app/phone` continua
como rota utilitária, acessível pela configuração WhatsApp.

No fluxo visual simulado, solicitar a retirada de autorização impede novas
admissões, cancela logicamente a fila não iniciada e aguarda apenas trabalhos
admitidos. A prévia que termina durante a pendência continua visível; sua
aprovação/publicação após a retirada está bloqueada. O dispatcher atualiza
fisicamente as filas canceladas quando as encontra. Conclusão incerta exige
verificação; ainda não há reconciliação automática. O mesmo comportamento ainda
precisa ser integrado ao provedor real.

Gerar ideia manualmente, aceitar/editar roteiro e operar ajustes técnicos do
renderer ficam em `/app/editorial-lab`, disponível somente no build de
desenvolvimento. As APIs, propostas, roteiros e versões permanecem: também
sustentam a jornada automática. A frequência semanal manual sai da interface;
`posts_per_week` histórico é preservado até recomendação por formato e plano.

## Próximas entregas, em ordem

| Fase | Resultado esperado | Estado |
| --- | --- | --- |
| [BL02](phases/BL-brand-library.md#bl02--escolher-e-editar-o-kit-piloto-para-um-negócio) | Escolha e edição guiada do primeiro kit por negócio | Implementada localmente; manter gates comerciais. |
| [BL03](phases/BL-brand-library.md#bl03--acervo-progressivo-em-sobre-meu-negócio) | Acervo privado, opcional e progressivo em Sobre meu negócio: produtos/serviços, fotos dos itens e do espaço | **Cadastro manual e fotos implementados localmente; BL03.3 é posterior.** |
| [BL04](phases/BL-brand-library.md#bl04--recuperar-contexto-e-produzir-uma-peça-nova) | Pedido livre recupera fontes automaticamente; nova peça aplica kit com IA visual/receita e mede fidelidade, qualidade e custo por peça aceita | **Em implementação local; sem gate de qualidade concluído.** |
| [BL05](phases/BL-brand-library.md#bl05--jornada-completa-local-ajuste-e-proatividade-mínima) | WhatsApp simulado percorre criação, ajuste, aprovação/publicação falsa e proposta em dia sem mensagem | Planejada; reutiliza as fatias F02–F06 existentes. |
| [BL06](phases/BL-brand-library.md#bl06--ampliar-a-biblioteca-e-servir-o-catálogo-em-escala) | Kits de manicure/personal e catálogo público em objetos/CDN | Após provar reaplicação do primeiro kit. |

O acervo é contexto recuperado automaticamente, sem seleção obrigatória de item
por pedido. “Crie uma imagem de um croissant” deve resolver o produto, as fotos e
os fatos pertinentes do mesmo negócio. Para mostrar o café real, a edição deve
partir de foto real do espaço e preservar o produto; fonte insuficiente exige
pergunta curta ou conceito identificado. Os envios deverão ser preservados
automaticamente como contexto, sem classificá-los como produtos ou fatos
confirmados. A cópia de foto ao acervo ainda é manual; a preservação do envio
não equivale à criação automática de uma ficha de produto ou de uma skill.

Antes do piloto comercial: fechar BL03–BL05 para as receitas prometidas, obter
avaliação consentida de qualidade, medir custo por peça aceita e franquia F07,
homologar WhatsApp/Instagram oficiais e operar staging/recuperação F08. Avatar e
voz permanecem no produto, **após o primeiro piloto comercial**, quando imagens
e vídeos com material real, qualidade e custo já tiverem sido validados (P15).
Exigem consentimento e orçamento próprios. Pesquisa ampla e novos nichos vêm depois da primeira peça personalizada aprovada.

A [sequência até produção e expansão](design/delivery-roadmap-2026-10-27.md)
reúne BL03–BL06, homologação Meta, franquias, AWS, piloto, pesquisa, avatar e
multicanal. Importar fotos de cardápio/tabela de serviços está previsto como
BL03.3: preencher fichas automaticamente como rascunho e conferir ambiguidades;
o proprietário aprovou cadastro manual e fotos, agora implementados localmente. Jev é o primeiro candidato à interpretação local; a [comparação sintética com OpenAI](evals/intent-comparison-2026-10-27.md) identificou erros e saídas incompletas, sem homologar produção ou conversa real. Motion continua candidato, sem integração.

## Decisões técnicas e limites de IA

- Backend Python modular; FastAPI, PostgreSQL com tabelas compartilhadas/RLS,
  Temporal e armazenamento compatível com S3. Web React em repositório separado.
  API, dispatchers e workers escalam separadamente. Redis é opção prevista, não
  dependência ativa; não há Celery, Make ou n8n no runtime.
- Temporal coordena processos duráveis de integração/geração. CRUD simples usa
  transação e auditoria; não precisa iniciar workflow apenas para emitir recibo.
- Auth própria: Argon2id, JWT de acesso em memória na web, refresh HttpOnly,
  sessão revogável, Origin/CSRF e MFA obrigatório para staff. Permissão de
  operador é distinta de owner e não exige cadastrar negócio.
- O adapter editorial atual usa OpenAI Responses com saída estruturada, sem
  tools; `gpt-5-mini` é o default de configuração, sem escolha comercial final
  de modelo. O adapter de áudio referencia `gpt-transcribe`. Não houve aprovação
  nesta revisão para trocar fornecedor, modelo ou adicionar plataforma agente.
- A conversa WhatsApp reconhece intenções delimitadas por regras; o worker local pode chamar Jev para classificar texto e candidatos do acervo, sob o aceite único e com reserva própria. Não é um chat geral nem envio real homologado.
- Reservas e tokens são dados de consumo, não custo monetário completo. Faltam
  tarifa versionada e visão de gastos de todas as tentativas; o admin não recebe
  material/prompt privado irrestrito. Memória versionada não treina o modelo
  automaticamente nem garante economia de tokens.

## Limpeza aprovada e preservação

A [auditoria de 27/10](audits/product-flow-and-ai-2026-10-27.md) registra as
aprovações ponto a ponto. A revisão preserva domínio editorial, materiais e
históricos; não autoriza remoções gerais por aparente falta de uso.

- P1–P8 simplificam navegação e fluxo, sem remover APIs/tabelas editoriais.
- P9 retira `billing_outbox` pela migração nova `0038`, preservando eventos
  faltantes em `billing_audit`. Jobs, Stripe e reconciliação permanecem.
- P10–P12 retiram `actor_for_subject`, o seed aposentado e a declaração sem
  serviço do volume Keycloak. Usar `scripts/seed_operator.py`; contas/IDs/MFA e
  volumes existentes são preservados.
- P13 separa estado vigente dos registros antigos nos três documentos de
  entrada, mantendo snapshots integrais e specs/evals detalhados.
- P14 encerra novos eventos-recibo `business.created`/`brand_kit.changed` e tira
  o relay genérico da inicialização automática. Auditoria transacional e
  snapshots de kit continuam. Tabelas, handlers e relay manual são mantidos
  temporariamente para compatibilidade com históricos; Temporal continua nos
  processos com efeitos reais. A retirada não apaga volumes ou eventos antigos.
- P15 mantém avatar/voz como F05 posterior ao primeiro piloto comercial, sem
  implementar nem encerrar essa fase nesta revisão.

## QA local e cenários fictícios

O [guia dos três negócios fictícios](evals/manual-qa-negocios-ficticios.md) define loja de cachorro-quente, delivery e manicure, passos manuais disponíveis e gates futuros. Os negócios e imagens ainda não foram provisionados. OpenCode é candidato para QA, não integração operacional aprovada.

## Continuidade e fontes de verdade

Produto adotado: **Meu Braço Direito**. Diretórios/remotos permanecem
`local-spark-platform` e `local-spark-web`; configuração usa `MEU_BRACO_DIREITO_`
e bancos `meu_braco_direito_platform`/`meu_braco_direito_platform_test`.
A [renomeação](product-rename.md) preserva identidades e explica compatibilidade.
O repositório de infraestrutura é planejado, não provisionado.

Atualizar este contexto, o [SDD](SDD.md), o SDD da fase e o
[CHANGELOG](CHANGELOG.md) em cada entrega. Manter resultados datados no changelog
e nos evals; não acumular estados antigos no texto vigente. Em conflito, o estado
atual e a fase ativa prevalecem sobre rascunhos históricos em `design/`.
Configuração local e comandos estão no [README](../README.md); critérios de
qualidade e operação ficam no [SDD](SDD.md) e em [operações](operations.md).
