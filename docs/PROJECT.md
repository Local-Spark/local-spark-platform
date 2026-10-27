# Meu Braço Direito — contexto vigente

Atualizado em **27/10/2026**. Este documento resume o produto, o estado local e
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
| WhatsApp e materiais | Inbox assinada/criptografada, vínculo, consentimentos, correlação, processamento, retenção/exclusão e transcrição opcional | Meta real não homologada; conversa automática ainda é limitada. SMS verificado não equivale a vínculo WhatsApp. |
| Contexto e texto | Fatos/preferências versionados, propostas e roteiros, adapter OpenAI, reservas/tokens e projeção administrativa limitada | Não há agente geral, pesquisa automática de concorrentes, skills executáveis por cliente nem geração visual integrada. |
| Kits BL01/BL02 | Vitrine fictícia de cafeteria, seleção por negócio, edição guiada de cores/fontes/logo/textos/composição, prévia, rascunho, confirmação e histórico | Kit `public_demo` somente para teste; direitos e qualidade comercial pendentes. F03 congela a versão; F04 ainda não a aplica à mídia. |
| Conteúdos F04/F06 | Prévias técnicas estáticas/vídeo, candidata, decisão explícita e publicação falsa com validação de versão/hash | Renderers Pillow/FFmpeg não são receitas aprovadas. Ajuste ainda não regenera automaticamente; envio de candidata e publicação reais pendentes. |
| Acervo BL03 | Cadastro manual versionado de produtos/serviços/promoções e fotos privadas de item/espaço, com cópia consentida de foto WhatsApp, implementados localmente | Importação automática de cardápio é BL03.3 posterior; o acervo alimenta briefing e roteiro experimentais em desenvolvimento/teste, sem geração visual integrada. |
| Produção BL04/BL05 | Worker local pode interpretar com Jev mediante autorização TypeSafe e orçamento; briefing privado consulta acervo, com revalidação e resposta simulada | Desligado por padrão, somente desenvolvimento/teste; precisa avaliação PT-BR, atendimento de esclarecimentos, imagem integrada e jornada completa. Prévia com briefing permanece bloqueada. |
| Infraestrutura F08 | Compose, CI e workflow de deploy preparado | AWS/staging, backup/restore, observabilidade operacional e capacidade não provisionados/homologados. |

Os ensaios em [evals](evals/) não são features do produto nem aceites comerciais.
A consulta a um perfil público não concede direitos sobre material ou aprovação
da titular. Custos de poucas chamadas isoladas não comprovam custo mensal.

## Experiência aprovada na web

| Área do cliente | Finalidade |
| --- | --- |
| Início | Resumo e orientações com estados reais do perfil, sem página estática de passos. |
| WhatsApp | Situação do canal, telefone/SMS, vínculo e consentimentos; histórico temporário de envios como consulta secundária. |
| Sobre meu negócio | Fatos/preferências, autorização de IA e acervo opcional de Produtos e serviços e Meu espaço. |
| Conteúdos | Acompanhar propostas/prévias e decisões disponíveis; alternativa à aprovação pelo WhatsApp. A simulação é identificada. |
| Kits visuais | Explorar, escolher e editar a direção visual aplicada ao negócio. |
| Plano e acesso | Assinatura, patrocínio e situação de acesso. |

Organização e negócio ativos são compartilhados entre as telas, com seleção em
memória; autorização permanece na API/RLS. `/app/content` é a rota vigente;
`/app/ideas` redireciona para ela e `/app/guide` para Início. `/app/phone` continua
como rota utilitária, acessível pela configuração WhatsApp.

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
pergunta curta ou conceito identificado. Material temporário só vira acervo
permanente com aceite específico.

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
o proprietário aprovou cadastro manual e fotos, agora implementados localmente. Jev é o primeiro candidato à interpretação local; um ensaio real com 30 mensagens fictícias de desenvolvimento apresentou um erro, e é insuficiente para homologação. Motion continua candidato, sem integração.

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
- A conversa WhatsApp reconhece intenções delimitadas por regras; o worker local pode chamar Jev para classificar texto e candidatos do acervo, com consentimento e reserva próprios. Não é um chat geral nem envio real homologado.
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
