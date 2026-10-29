# Meu Braço Direito — contexto vigente

Atualizado em **29/10/2026**, após a primeira imagem real pelo caminho do produto
na parte 3: Café do Cedro, com fontes autorizadas, teto de US$ 1 e sem publicação.
A próxima fatia é BL04.3, qualidade e custo por peça aceita. Decisões de produto e pendências ficam em
[DECISIONS](DECISIONS.md); contratos no [SDD](SDD.md); sequência no
[índice de fases](phases/README.md) e na [trilha BL](phases/BL-brand-library.md).
As versões anteriores foram [preservadas integralmente](history/2026-10-28-pre-documentation-reconciliation/index.md).
Uma entrega local não equivale a uma capacidade comercial homologada.

## Produto

Pequenos negócios enviam texto, foto, áudio ou vídeo pelo WhatsApp. A plataforma
usa os fatos confirmados, o kit e os materiais do próprio negócio para preparar
conteúdo, pedir aprovação específica, publicar nos canais habilitados e mostrar
resultados observáveis. Também deverá propor conteúdo sem envio novo, dentro de
uma cadência aceita e da franquia; essa proatividade ainda não está implementada.
O cliente não precisa escrever prompt ou operar um editor.

A web complementa identidade, contratação, canal, fatos, acervo, kits e revisão.
A vitrine pública usa exemplos fictícios já produzidos; uma visita não chama IA
nem conecta contas sociais. A escolha do kit não aprova publicação.

Uma conta de cliente e uma organização por negócio, com cobrança e aceite
próprios. O runtime garante no máximo um negócio por organização; memberships e
seleção legadas são preservadas. Staff é independente de cadastro de negócio.
Um número WhatsApp de cliente ativo por negócio na primeira versão.

## Decisões atuais sobre IA, materiais e prévias

- **Aceite único entregue localmente (C01):** em Plano e acesso, antes do
  checkout, o cliente concorda uma vez com IA para interpretação, texto, imagem
  e transcrição. Contas existentes recebem o mesmo passo. Não há permissões por
  fornecedor em WhatsApp ou Informações e preferências. Credenciais, plano,
  orçamento e versões são controles internos. Aceitar não confirma pagamento.
- **Envios WhatsApp preservados (C04/C05):** materiais associados ficam sem
  expiração automática; histórico e API não oferecem sua exclusão. A troca de
  número não interrompe material já associado; a entrega simulada usa o novo
  vínculo. Envio real de candidata ainda falta. Eventos técnicos não atribuídos
  e uploads órfãos têm limpeza separada.
- **Acervo:** fotos desatualizadas de item/espaço podem ser removidas. A cópia
  explícita de uma foto do WhatsApp cria outro objeto; preservar o envio não
  cria uma ficha de produto, fato confirmado, memória pesquisável ou skill.
- **Mudanças durante criação (C06/C07):** aguardar processos iniciados, cancelar
  a fila que não começou e impedir novos inícios até aplicar a mudança de kit,
  foto ou contexto. A prévia anterior continua para revisão, identificada como
  anterior à alteração. Os caminhos `visual_fake` e `visual_ai` compartilham
  essa coordenação dos escritores atuais.
- **Continuidade e preservação (C08/C09):** a criação `visual_fake` ou `visual_ai` já admitida
  tem prova durável para concluir após o vencimento financeiro e permitir revisão
  privada. Bloqueio financeiro explícito e revogação de patrocínio continuam
  distintos do vencimento. Novas criações e publicação exigem plano vigente.
  Prévias concluídas e sua proveniência saem da limpeza automática por prazo;
  tentativas visuais iniciadas sem resultado resolvido também são conservadas.
- **Autor sem acesso (C10), implementação de suporte adiada em 29/10:** outro
  owner não pode substituir nem descartar sua alteração pendente. Essa proteção
  permanece; a recuperação staff fica para evolução de gestão de acesso/suporte.
  A exceção continua bloqueada e não impede fechar a fatia simulada validada.

A admissão visual verifica proposta, fontes, usuário/membership, aceite e plano
sob locks na ordem proposta → visual → comercial, antes de gravar o run. A reserva
financeira continua em outra transação/role: falha ou confirmação perdida mantém
o run bloqueante e não libera repetição. A recuperação local pode encerrar uma
tentativa obsoleta/falhada somente após tornar a prévia terminal e comprovar,
sob locks correlator, ausência de tentativa e de reserva, inclusive não vinculada.
O commit confirmado precede a conclusão owner; confirmação perdida permite repetir
somente a reconciliação. Uma duplicata viva não derruba a criação original.
`DatabaseVisualEffectGuard` agora reúne admissão, fontes, reserva, claim única e
commit privado com prova owner e revalidação correlator. Roteiro aguarda runs em
transação separada proposta → visual; writers financeiros participam do comercial.
Troca de telefone não muda a identidade de fonte já atribuída. O protocolo dos
escritores atuais está no [desenho da guarda](design/BL04-effect-guard.md).
O modo persistido `visual_ai` agora liga essa guarda ao adapter OpenAI por um
runner e workflow próprios; os testes usam transporte HTTP simulado. A ativação
continua desligada por padrão. A parte 3 executou uma chamada real de imagem com
Jev, guarda, kit/logo e prévia privada, sob autorização delimitada; ver
[evidência](evals/bl042-first-product-image-2026-10-29.md).
C08 cobre `visual_fake` e `visual_ai`; o
renderer local legado ainda não recebe a mesma exceção de conclusão. `expires_at`
continua delimitando criação/aprovação, sem apagar uma prévia concluída. URL
assinada, validade factual e prazo de aprovação permanecem separados da preservação.
Revisão histórica não depende de manter a execução visual habilitada.

O prazo de exclusão após encerramento da conta foi explicitamente adiado para
essa fase; não implementar exclusão automática nesta etapa (P03). Vencimento do
plano não equivale a encerrar conta nem a perder membership.

## Estado implementado e limites

| Área | Existe localmente | Falta demonstrar ou entregar |
| --- | --- | --- |
| Fundação e identidade | FastAPI, PostgreSQL/RLS, auth própria, sessões, recuperação, e-mail HTML, onboarding, MFA/convites de staff | Homologação de operação e segurança em staging/produção. |
| Contratação | Stripe sandbox, webhook/jobs/reconciliação, patrocínio e aceite único versionado por negócio | Contratos comerciais definitivos, franquias e cenários externos restantes. Cadastro e retorno de checkout não ativam plano. |
| WhatsApp | Inbox assinada/cifrada, vínculo, correlação, processamento, transcrição configurável e preservação de materiais | Meta oficial, envio real de candidata e conversa completa ainda não homologados. |
| Contexto e texto | Fatos/preferências versionados, propostas/roteiros, adapter editorial, reservas/tokens e projeção administrativa restrita | Qualidade comercial, conversa com memória, pesquisa ampla e skills executáveis. |
| BL01/BL02 | Vitrine fictícia de cafeteria, escolha/edição de kit e logo privado; kit/logo aplicados à primeira imagem real controlada | Kit `public_demo` não tem liberação comercial; fidelidade precisa de revisão. |
| BL03.1/BL03.2 | Catálogo/fotos privadas e uso seletivo de fontes na primeira imagem real controlada | Importação de cardápio é BL03.3 futura; qualidade/fidelidade do contexto aplicado ainda requer avaliação. |
| BL04 | Caminho `visual_ai`, Jev, guarda e adapter exercitados com uma imagem real de feed e prévia privada preservada | BL04.3: revisão de post/story, fidelidade e custo por peça aceita. Uma chamada não comprova qualidade, fatura ou margem. |
| F04/F06 | Prévias técnicas estáticas/vídeo, candidata, revisão e publicação simulada com versão/hash | Ajuste não regenera automaticamente; candidata WhatsApp e Instagram reais pendentes. |
| F08 | Compose, CI e workflow manual de deploy preparados | AWS/staging, recuperação coordenada, observabilidade operacional e capacidade não homologadas. |

Os ensaios em [evals](evals/) são evidências datadas, não features ou aceites
comerciais. As imagens reais de IA de 27/10 e 28/10 foram geradas em ensaios
isolados, fora do worker do cliente. Não comprovam fidelidade, margem ou custo
mensal. Consultar perfil público não concede direitos sobre o material observado.
A [execução de 29/10](evals/bl042-first-product-image-2026-10-29.md) percorreu o
worker do produto e exportou o JPEG pela API autenticada e S3 privado. Meta de
entrada/prova de canal foram sintéticas e a entrega da candidata permaneceu
simulada; isso ainda não comprova conversa WhatsApp completa ou homologação.

## Jornada web vigente

| Área | Finalidade |
| --- | --- |
| Início | Resumo e orientações com estados reais do negócio. |
| Plano e acesso | Aceite único do serviço, assinatura, patrocínio e situação financeira. |
| WhatsApp | Telefone/SMS, vínculo e histórico preservado de envios como consulta secundária. |
| Sobre meu negócio | Informações e preferências, Produtos e serviços e Meu espaço. |
| Conteúdos | Acompanhar propostas/prévias e decisões disponíveis; simulações identificadas. |
| Kits visuais | Explorar, escolher e editar a direção visual. |

Organização/negócio ativos são compartilhados em memória; a autorização é
verificada na API/RLS. `/app/content` é a rota vigente; `/app/ideas` redireciona
para ela e `/app/guide` para Início. `/app/phone` é utilitária do WhatsApp.
`/app/editorial-lab` mantém os controles técnicos só no build DEV. O valor
histórico `posts_per_week` é preservado, sem campo manual de frequência.

## Próxima entrega e sequência

1. **BL04.3:** revisar o feed produzido e completar o conjunto post/story pelo
   produto, com titular e fontes
   consentidas, medir fidelidade, texto, legibilidade, rejeições e custo por
   peça aceita, incluindo refações. Novas chamadas exigem autorização própria;
   a autorização delimitada de US$ 1 não ativa uso recorrente.
2. **BL05:** fechar WhatsApp como jornada principal de mensagem → prévia → ajuste
   → aprovação → publicação simulada, incluindo iniciativa sem mensagem e pausa.
3. **Piloto:** homologar Meta/Instagram, aplicar franquias F07 e operar staging,
   observabilidade e recuperação F08. A Meta pendente não impede testes locais.
4. **Expansão:** BL03.3 importa cardápio como rascunho; BL06 amplia kits/nichos e
   catálogo/CDN. Pesquisa ampla, avatar/voz e multicanal seguem fases próprias.

Foto e story são os formatos iniciais; vídeo e suas franquias/preço permanecem
para definição posterior. R$ 99/mês e teto total de R$ 50/cliente/mês orientam
medição, sem margem comprovada. Avatar/voz sintética ficam após o primeiro
piloto. HyperFrames/Remotion e outros estudos são candidatos, não integrações.
A aquisição por vídeos longos dos três sócios segue estratégia comercial; a
meta de 200 mil clientes orienta capacidade gradual, sem comprovação atual.

`visual_ai` exige `VISUAL_AI_MODE=openai`, `VISUAL_AI_EXECUTION_ENABLED=true`,
reserva positiva por tentativa, tetos mensal por tenant e agregado suficientes,
chaves de provedor/criptografia e enforcement do aceite único C01. Os nomes de
variáveis usam o prefixo `MEU_BRACO_DIREITO_`; o padrão é flag desligada e reserva
zero. A API usa apenas o pool owner; o worker exige seu pool correlator restrito.
O dispatcher usa ID estável por prévia e lease de 12 minutos, sem redispatch do
efeito visual incerto. A resolução automática do item exige a configuração Jev
existente, com credencial/orçamento próprios; correspondência lexical não a substitui.

## Arquitetura, validação e continuidade

Backend Python modular, FastAPI, PostgreSQL compartilhado/RLS, Temporal e S3;
React em `local-spark-web`. API, dispatchers e workers escalam separadamente.
Redis não é dependência ativa; não adicionar outro runner para os processos de
Temporal. Sem rede sob row lock e sem IO em workflows determinísticos.

Negócios/kits usam auditoria transacional; relay, tabelas e handlers antigos
ficam só para compatibilidade, sem novos recibos de CRUD. Auth é própria;
access token em memória e refresh HttpOnly. Staff/MFA não equivale a owner.
Os modelos atuais são configuração, não escolha comercial definitiva. Contexto
versionado não treina automaticamente modelos e tokens não são COGS monetário.

Evidência anterior de aplicação: 1.583 testes backend e complemento de 24 testes
com sete casos novos; cobertura final de 100% de linhas/branches. Web: 360 testes,
100% nos quatro critérios, build e três jornadas Chromium. Evidências datadas
no [CHANGELOG](CHANGELOG.md). A parte 1 passou em `make ci`: **1.829 testes**,
**100% de linhas e branches** (9.284 statements e 2.550 branches), Ruff/formatação
e mypy (149 módulos). PostgreSQL `_test` restrito e Temporal locais cobrem admissão,
continuidade, preservação, autoria, recuperação entre commits e confirmações
perdidas, tentativa tardia, orçamento concorrente e fontes kit/logo. Não houve chamada
paga, novos grants ou homologação externa. A guarda concreta também cobre roteiro,
relink por outro owner, acesso financeiro e prazo factual após locks. Web:
**365 testes e 100% nos quatro critérios**, build/formatação e três jornadas
Chromium (laboratório pendente, conteúdo e aceite).

A parte 2 acrescenta testes da API até `VisualGenerationWorkflow`, runner,
adapter real com transporte HTTP simulado, acabamento e revisão privada, com
PostgreSQL/Temporal locais. `make ci` aprovado: **1.914 testes**, **100% de
linhas e branches** (9.394 statements, 2.582 branches), Ruff/formatação e mypy
(151 módulos). Web: **375 testes**, **100% nas quatro métricas**, build/formatação
e **quatro jornadas Chromium** na árvore final (conteúdo local/IA, laboratório e
aceite). As contagens anteriores são evidências da parte 1. A migration 0059 foi
aplicada somente ao `_test`, sem migrar o banco da aplicação, chamar fornecedor
pago ou alterar grants naquela entrega.

A parte 3 concluiu uma imagem real de feed com `gpt-image-2.5-flare-2026-09-08`,
Jev real e acabamento determinístico do kit/logo, preservando candidata pendente
e publicação nula. Estimativa por uso: **US$ 0,029701**, incluindo duas
interpretações Jev; não é fatura. A reserva visual de **US$ 0,99** continua
`uncertain`, com custo efetivo desconhecido, e o run terminou. A primeira entrada
resultou em story e o wrapper bloqueou antes do HTTP de imagem; prova de zero
submissões permitiu reconciliar a reserva antiga em zero, preservando tentativa
e auditoria. Uma nova origem esclarecida gerou o feed sob a mesma autorização;
não houve edição manual de roteiro nem aprovação/publicação. A migration 0059
agora também foi aplicada ao banco local da aplicação para essa execução.
Flags persistentes seguem desligadas, sem novos grants ou código de produção.
`make lint types` aprovado (151 módulos) e **94 testes unitários dirigidos**
aprovados; código de produção inalterado. O `make ci` acima é da parte 2 e não
foi repetido nesta execução operacional. Com geração `disabled`, flag desligada
e limites zero, owner listou/baixou o mesmo hash; acesso anônimo retornou 401.
Os processos temporariamente habilitados foram encerrados. Uma imagem isolada
não substitui as provas C08/C09 da suíte ou a revisão humana de BL04.3.

Diretórios/remotos continuam `local-spark-platform` e `local-spark-web`, com marca
Meu Braço Direito, prefixo `MEU_BRACO_DIREITO_` e bancos renomeados conforme
[registro](product-rename.md). Operação em [operations](operations.md).
Atualizar PROJECT, SDD, fase e CHANGELOG em cada entrega; decisões novas entram
em [DECISIONS](DECISIONS.md), sem recolocar perguntas já respondidas na fila.
