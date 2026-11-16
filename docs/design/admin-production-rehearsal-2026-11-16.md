# Ensaio produtivo pelo front administrativo — 16/11/2026

## 16/11/2026 — respostas, ajustes e teto pela UI

Esta entrada substitui as limitações de continuidade e orçamento das entradas
anteriores. O teto obrigatório é informado na UI por ensaio. Ajustes e respostas
usam o saldo do teto original, sem renová-lo. O teto global é opcional: zero em
`creation_lab_budget_usd_micros` significa ausência desse limite adicional, e não
execução desabilitada. A habilitação técnica independente é
`creation_lab_execution_enabled`, falsa por padrão. A identidade administrativa
exclusiva, consentimentos, reservas antes de efeitos e o limite por ensaio continuam
obrigatórios. Não altera planos, saldos ou quotas comerciais.

- Perguntas de intenção/editorial suspendem a criação e aparecem na UI; aprovar
  um checkpoint com perguntas é recusado. Responder prepara uma continuação no
  mesmo histórico, conservando pedido original, anexos e seleção do acervo.
- “Preparar ajuste” existe na revisão e na peça concluída. Cada tentativa tem
  identidade própria, referência à anterior e ao ensaio raiz; não reaproveita a
  identidade de uma chamada paga. Há uma única continuação por tentativa, no
  máximo dez tentativas e 4 mil caracteres para o pedido composto. Uma chamada
  não resolvida impede continuação. O operador revisa e inicia a nova tentativa
  pela UI; enviar feedback isolado continua sem autorizar geração.
- Peças de tentativas do mesmo ensaio podem ser comparadas na UI. Downloads e
  feedback usam a tentativa proprietária. Cada tentativa conserva seu trace,
  custos e pacote exportável; só o trace expira sete dias depois do seu término.
- Catálogo deixa de ser obrigatório para imagens. Sem correspondência, um pedido
  de criação identificado pode usar fatos vigentes e marca confirmada, com regras
  factuais/CTA compartilhadas. Não cria um item fictício nem transforma texto do
  modelo em fato. O laboratório apresenta essa base para confirmação; informações
  essenciais pendentes viram perguntas. No produto, o briefing institucional é
  recapturado antes de efeitos e respeita a validade dos fatos.
- A jornada produtiva WhatsApp passa a vincular respostas a uma pergunta citada e
  `Pedir ajustes: ...` com observação à entrega anterior. O material recebido
  continua sendo a identidade durável do workflow; ligação, autorização e auditoria
  são persistidas. Pedido composto e proveniência são compartilhados pelas etapas
  de briefing, editorial e geração visual. Uma mensagem nova sem referência não
  é presumida como resposta. O comando sem observação registra a decisão existente,
  sem inventar um ajuste. A entrega de candidatas continua simulada: isto não
  conclui a integração externa do WhatsApp nem a publicação real.

Migrações aditivas 0128 e 0129 aplicadas somente ao banco local de desenvolvimento.
O runtime `app.entrypoints.creation_lab` usa Temporal e o relay existente filtrado
para eventos do laboratório, em fila exclusiva. `make creation-lab` inicia esse
serviço persistente; os pedidos são feitos pela UI. Configuração local preparada
com credenciais existentes e imagem do renderizador já instalada. Worker exclusivo
iniciado após leitura confirmar zero execuções/etapas aprovadas pendentes; nenhum
consumidor antigo foi reiniciado por esta alteração. Flags produtivas não são
habilitadas pelo adaptador administrativo.

Revisão de código e formatação Ruff/Prettier realizadas. **Não executados testes,
CI, typecheck, build, QA em browser ou geração paga**, conforme pedido do titular.
A validação ponta a ponta será feita por ele pela UI. Não há alegação de qualidade
estética validada. Limites semanais por formato e melhorias dos motions permanecem
na etapa posterior combinada.

## 16/11/2026 — integração da execução privada do laboratório

Implementada a ligação da UI às etapas produtivas: início idempotente, fila via
outbox/Temporal, confirmação de catálogo, checkpoints, cancelamento, peças privadas,
comparação/feedback e pacote de execução. Migrações aditivas 0125–0127 aplicadas
somente ao banco local de desenvolvimento. Esta entrada substitui o estado de
integração pendente das entradas anteriores, sem declarar validação operacional.

Decisão confirmada nesta continuação: para posts/stories, o modelo sugere o produto
ou serviço a partir da mensagem e o administrador confirma antes da geração.
O fluxo reutiliza candidatos/snapshot de catálogo, Jev, provedor editorial, regras
factuais/CTA, skills, prompt de peça completa e provedor visual do produto. Não
seleciona automaticamente um item por coincidência textual. Ambiguidade/dúvidas
interrompem a tentativa com trace disponível; revisão do pedido inicia outro ensaio.
No acompanhado há revisão editorial adicional; no automático ela avança após as
validações. A confirmação do catálogo continua obrigatória nos dois modos.

Reels reutilizam MotionOrchestrator e as etapas de preparação, planejamento,
implementação, storyboard, render, crítica e correção. Adaptadores mudam admissão,
fontes privadas, financiamento e persistência; preservam o bloqueio de alterações
visuais pendentes. Não personificam o proprietário nem
escrevem peças/quota do cliente. Checkpoints obrigatórios do produto permanecem
obrigatórios, inclusive no modo automático. Entrada: um vídeo MP4 e até quatro
imagens complementares PNG/JPEG somadas à seleção do acervo. Imagens privadas são
normalizadas pelo preparador compartilhado, com proveniência de upload; nomes de
arquivos não se tornam fatos comerciais. Áudio separado/múltiplos vídeos não são
inferidos como direção de edição e geram impedimento explícito.

Trace guarda entradas/saídas disponíveis e deltas reais dos adapters Responses de
motion/editorial. SSE reconecta por cursor; expiração normal de token permite
renovação sem repetir geração. Jev e Images apresentam espera/resposta terminal,
sem digitação simulada. Parciais não autorizam uso do resultado. Frames de storyboard
ficam no trace cifrado, evitando objetos de diagnóstico órfãos no armazenamento.
O trace é apagado sete dias após término; peças, anexos, textos/legendas, feedback,
auditoria e compromissos de custo permanecem. ZIP inclui o disponível no cursor,
com expiração explícita, sem credenciais; limites de tamanho recusam em vez de
truncar silenciosamente. Consulta/download revalidam acesso e integridade.

Claims, tokens de execução e identidade da etapa impedem repetir efeitos pagos e
impedem uma falha atrasada de finalizar uma etapa mais nova. Cancelar impede novas
etapas; chamadas já submetidas podem terminar/custar e mantêm reserva quando o
resultado é incerto. Compromissos administrativos são separados da franquia do
cliente; estimativa não é fatura confirmada. Teto global padrão zero, sem reset
semanal implícito. Tarifas/reserva editoriais novas também começam em zero.

Validação realizada: leitura/revisão do código, formatação Ruff/Prettier e aplicação
das migrações locais. Por orientação do titular, **não** foram executados testes,
CI, typecheck, build, QA em browser ou geração paga. Não há evidência de sucesso
ponta a ponta nem de melhoria estética. Ativação depende de configuração explícita
de fornecedores, orçamento/tarifas, armazenamento/renderizador e worker/relay
atualizados; consumidores anteriormente pausados não foram reiniciados. Limites
semanais por formato e melhorias de qualidade dos motions continuam para a etapa
seguinte, conforme decisão do titular.

## 16/11/2026 — execução administrativa ainda em integração

Infraestrutura adicionada para compromisso de orçamento, efeitos privados,
trace cifrado e versões/feedback (migrações 0123/0124). Retenção confirmada:
apagar somente o trace sete dias após término; anexos, peças, auditoria e custos
permanecem. Há workflow Temporal de limpeza; consumidores locais seguem pausados.
Teto administrativo padrão zero, sem autorização implícita de geração paga.

Etapas produtivas de motion estão sendo preparadas para reutilização com leitura
e persistência privadas. Corrigida e formatada a extração dos leitores de materiais.
Ainda faltam admissão administrativa ligada à geração, retomada das aprovações e
jornada completa de imagens/vídeos pela UI. O adaptador de motion recusa execução
até essa ligação existir. Exportação atual é de rascunho, não da execução completa.
O laboratório ainda não valida o meio inteiro do fluxo produtivo. Sem testes,
build ou geração paga nesta continuação, conforme orientação do titular.

Estado vigente: integração de execução adicionada; ativação/configuração e validação ponta a ponta ainda não realizadas.
Entrevista respondida; retenção do trace confirmada em 7 dias. Este documento não habilita fornecedores, concede acesso
em runtime, autoriza gasto ou publica conteúdo. Branch de trabalho: dev.

## Objetivo e decisões confirmadas

Substituir a preparação manual e os scripts específicos de cada rodada por uma
jornada permanente no front existente, executável pelo próprio titular/admin.
A entrada simula o envio de mensagem e mídia pelo WhatsApp enquanto a integração
não está completa; a produção usa os serviços reais do produto. O canal simulado
deve ser identificado, sem fabricar recebimento ou entrega real pelo WhatsApp.

- Cliente não tem acesso à área de testes, seus endpoints, eventos SSE, traces
  ou downloads. O contexto único do cliente pertence apenas à jornada normal
  do produto; não implica disponibilizar o laboratório ao cliente.
- O perfil admin deve poder escolher qualquer negócio da base para testar
  negócios diferentes pelo fluxo produtivo. A identidade administrativa real e
  o negócio alvo ficam registrados; não fingir que o admin é o proprietário.
- Mensagem natural e vídeo/material iniciam a jornada; o contexto, kit e acervo
  pertencem ao negócio ativo ou selecionado.
- Progresso exato do que está acontecendo, em tempo real, via SSE no front.
- Trace completo do fluxo: o que foi preparado, enviado ao modelo, retornado,
  validado, renderizado, revisado e decidido; incluir falhas e continuações.
- O usuário deve conseguir repetir os ensaios e avaliar resultados sem solicitar
  a criação de arquivos executáveis ou scripts fixos a cada rodada.
- Resultado, histórico de versões e feedback devem permanecer associados à
  execução. A melhora pretendida é operacional; esta tela não comprova por si
  só melhoria artística nem reduz automaticamente a latência do modelo/render.

## Sequência confirmada pelo titular

1. Implementar primeiro o teste pela UI administrativa, com seleção de negócio,
   execução pelo produto e observabilidade descritas neste documento. Validar a
   jornada com fixtures e testes de integração antes do ensaio pago.
2. Com o fluxo disponível e validado, solicitar a geração de uma peça por essa
   interface, com credenciais e orçamento explicitamente configurados/autorizados.
3. Inspecionar o resultado e seu trace; identificar e implementar melhorias de
   qualidade de motion progressivamente, comparando as versões e preservando
   evidências. Melhorias artísticas não são pré-requisito para entregar a UI.

Esta sequência substitui a proposta anterior de avançar melhorias de motion em
paralelo. Corrigir falhas necessárias ao funcionamento da jornada continua parte
da implementação da UI. O cliente não pode executar este tipo de teste; seleção
entre negócios e execução do laboratório pertencem exclusivamente ao perfil admin
do titular solicitante. Usar os serviços produtivos não concede acesso ao cliente
nem coloca o ensaio no histórico comercial normal.

## Jornada proposta para detalhamento

Admin abre a área de testes, busca um negócio e confirma visualmente o contexto.
Somente o perfil admin autorizado acessa essa jornada. A conversa recebe
mensagem e mídia selecionada do acervo ou enviada pelo usuário. Preparação e
admissão ocorrem no backend; IDs, payloads e configurações técnicas não precisam
ser montados pelo operador. O backend aplica orçamento e permissões explícitos.

A conversa apresenta respostas, pedidos de decisão e a peça produzida no formato escolhido. Um painel
mostra a execução e permite abrir cada etapa/chamada, materiais, entradas, saídas,
uso/custo disponível e erros. Comparação entre versões e feedback referenciado
por instante, quando houver vídeo, ajudam a revisão. Os modos automático e
acompanhado e o acesso exclusivo do titular seguem as decisões da entrevista.

## Progresso e trace: contrato técnico proposto

1. Etapas reais: recebido, preparação de contexto/materiais, transcrição,
   planejamento, espera de aprovação quando aplicável, construção, storyboard,
   render, crítica, correção/replanejamento, conclusão ou falha. A sequência deve
   refletir o caminho executado, inclusive etapas omitidas e atividades paralelas.
2. Eventos duráveis com identidade, execução, negócio, etapa, tentativa, sequência
   e horários. Correlacionar operações, efeitos, chamadas e artefatos. Eventos de
   estado acompanham transações/auditoria/outbox; Temporal permanece o executor.
3. SSE projeta eventos persistidos; não inicia geração. Reconexão retoma por cursor
   (`Last-Event-ID` ou equivalente), com deduplicação, ordenação documentada e
   recuperação por snapshot caso o cursor não esteja mais disponível. Fechar a
   página não cancela a execução nem reenviará chamadas pagas.
4. Mostrar início/fim, tempo decorrido, espera, falha e causa observável. Percentual
   só quando houver medida concreta, como quadros renderizados/total. Uma chamada
   sem progresso interno observável aparece como aguardando resposta, sem inventar
   porcentagem ou expor raciocínio interno do modelo.
5. Trace registra instruções/contexto efetivamente enviados, versões de templates,
   modelo e parâmetros, mensagens, ferramentas usadas quando houver, resposta
   recebida, validações e decisão resultante. Distinguir preparado, envio iniciado,
   resposta recebida e resultado incerto. Não inferir envio a partir do payload.
6. Texto/JSON acessível no detalhe; mídia/código/MP4 como artefatos privados ligados
   por IDs/hashes e acesso autenticado. Não colocar vídeos/base64 completos em
   cada evento SSE. O painel permite recuperar o conteúdo autorizado referenciado.
7. Trace completo significa evidência observável da aplicação e do provedor, sem
   chaves, tokens de autenticação ou raciocínio privado do modelo. Conteúdo de
   cliente fica em armazenamento privado/trace protegido, nunca em stdout/logs
   genéricos. Logs continuam com eventos estáveis e campos permitidos.
8. Permissão administrativa explícita para seleção, execução e inspeção de trace,
   com auditoria e RLS; o seletor ou header não concede acesso. Essa capacidade
   amplia o escopo administrativo atual e precisa ser implementada, sem presumir
   que os endpoints de owner já aceitam staff. SSE e leitura de artefatos revalidam
   acesso; revogação deve interromper exposição. Não usar credenciais na URL.
9. Custos distinguem teto, reserva, estimativa, uso observado e fatura. Novas
   execuções exigem credenciais/budgets configurados; reconexão ou duplo clique
   não pode criar uma segunda cobrança. Orçamento administrativo separado da
   franquia do cliente; exportação confirmada e retenção do trace de 7 dias.

## Base existente e trabalho necessário

Na dev, `app/api/v1/motion_requests.py` já oferece criação/listagem/status,
checkpoints e decisões, além de leitura/galeria/decisão de storyboard. Isso é base
para a jornada, não comprovação de suporte administrativo ou SSE de ponta a ponta.
`editorial-conversation/simulate` é um ensaio limitado a ofertas/disponibilidade;
não conduz hoje essa conversa completa de reels.

O front React está no repositório separado `local-spark-web`. A implementação
precisa inspecionar suas instruções e telas antes de definir componentes/rotas.
Ainda falta mapear eventos/traces existentes por etapa, autorização administrativa,
preparação reutilizável no backend, transporte SSE, histórico/artefatos, experiência
de conversa e feedback. Não criar outro runner nem regras de produção no front.

## Decisões da entrevista — confirmadas em 16/11/2026

1. **Escopo:** todos os tipos de criação já desenvolvidos, incluindo posts,
   stories e reels/motion conforme capacidades efetivamente existentes. Inventariar
   os caminhos disponíveis antes da implementação; não anunciar formatos futuros.
2. **Modos:** automático e acompanhado, selecionáveis por execução. O acompanhado
   usa checkpoints pertinentes a cada formato; automático respeita os limites e
   decisões obrigatórias do produto. Não confundir geração com publicação.
3. **Destino:** área de ensaios separada do histórico normal do negócio, usando
   contexto e pipeline produtivos, com proveniência de teste preservada.
4. **Acesso administrativo:** somente o perfil do titular solicitante poderá
   selecionar qualquer negócio, executar ensaios e inspecionar seu trace nesta
   área. Ser admin genericamente não concede essa permissão. Resolver a identidade
   pelo cadastro autenticado, sem fixar e-mail ou segredo no código. A regra de
   contexto único do usuário do negócio não concede acesso ao laboratório admin.
5. **Orçamento:** orçamento administrativo com teto por execução; ensaios não
   consomem franquia comercial do cliente. Valores e credenciais são configuração
   explícita posterior; esta decisão não autoriza uma chamada paga agora.
6. **Streaming:** mostrar também texto parcial enquanto o modelo responde, via
   SSE, quando o provedor permitir. Integrar suporte nos adapters necessários;
   identificar trechos como parciais até o recebimento/validação terminal. Sem
   suporte, mostrar a espera real e a resposta completa ao terminar, sem simular
   digitação. Queda do stream não autoriza reenviar a geração ou repetir cobrança.
7. **Retenção/exportação:** trace completo terá prazo de retenção e botão para
   baixar o pacote da execução. Prazo confirmado: 7 dias. O pacote deve reunir
   entradas/saídas disponíveis, eventos, versões, custos e manifesto de artefatos,
   com acesso privado e sem credenciais; indicar conteúdo indisponível/expirado.

### Retenção confirmada

Trace completo retido por **7 dias**. Convenção técnica proposta: contar a partir
do encerramento terminal da execução; execução ativa não expira. Mostrar na UI
`Trace disponível até <data e hora>`, no fuso do usuário. Download disponível
durante esse prazo; baixar não renova a retenção. Pacotes temporários exportados
não devem manter cópia de servidor além do vencimento do trace.

Após o prazo, remover o conteúdo de diagnóstico sujeito à política e apresentar
`Trace expirado`, desabilitando sua exportação. A execução continua identificável
pelos metadados mínimos permitidos. A retenção de auditoria, ledger, materiais e
entregas do negócio segue suas próprias regras; não apagar esses dados ao expirar
o trace. A implementação deve definir campos e armazenamento abrangidos pela
limpeza, incluindo eventos com texto parcial e cópias de payloads, sem apagar
artefatos necessários a execuções ainda ativas.

## Organização proposta da UI administrativa

Este é o desenho funcional da tela, ainda não implementado nem conferido contra
os componentes do repositório web. A posição exata no menu e os componentes visuais
serão ajustados à navegação existente; os comportamentos abaixo orientam a entrega.

### Entrada e contexto

Entrada `Testes de criação` na área administrativa, visível somente ao perfil do
titular autorizado. Não aparece no menu ou na jornada de clientes. A tela abre com
busca de negócios/clientes e identificação suficiente para distinguir homônimos.
Após escolher, cabeçalho persistente mostra negócio, cliente/contexto selecionado
e o aviso `Ensaio administrativo — não envia WhatsApp nem publica`.

Trocar de negócio abre o histórico correspondente; não transfere mensagens, anexos
ou rascunhos entre negócios. Execução em andamento permanece vinculada ao negócio
original e continua no servidor. Links diretos sempre revalidam permissão.

### Composição da tela

- **Histórico de ensaios:** execuções do negócio selecionado, com formato, data,
  status e identificação; botão `Novo teste`. Histórico separado das criações
  normais do cliente. Abrir um ensaio recupera a conversa e o estado persistido.
- **Conversa central:** mensagem natural, seleção de material do acervo/upload,
  respostas do produto, pedidos de decisão e prévia da peça. Formatos disponíveis
  correspondem aos já implementados; a UI não promete capacidades futuras.
- **Painel de execução:** timeline das etapas, etapa ativa, duração, espera/erro,
  uso/custo e acesso ao trace. Em viewport menor, conversa, execução e trace podem
  ser abas, preservando o mesmo estado e o contexto do negócio.

Antes de iniciar: escolher modo `Automático` ou `Acompanhado`, conferir materiais
anexados, teto da execução e saldo administrativo disponível. Botão `Executar teste`
cria uma única operação; cliques repetidos/reconexão não duplicam execução. Falta
de configuração ou material aparece como impedimento acionável antes do envio.

### Execução e decisões

Após o envio, a conversa conserva a mensagem original e mostra respostas/eventos
reais. O painel recebe SSE com etapas pertinentes ao formato. Texto parcial do
modelo aparece no detalhe da chamada, identificado como parcial; não é apresentado
como resposta final válida ou peça aprovada antes da validação.

No modo acompanhado, decisões aplicáveis aparecem como cards com prévia e ações
`Aprovar e continuar` e `Solicitar ajuste`, vinculadas à versão exata. A interface
deve explicar quando o ajuste inicia nova tentativa e seu impacto no orçamento;
conectar os serviços necessários sem fingir que todos os tipos de ajuste já são
suportados. No automático, o produto segue os gates existentes, parando diante
de decisão obrigatória ou impossibilidade de continuar.

Estados visíveis incluem fila/preparação, executando, aguardando decisão,
concluído, falhou e resultado incerto quando aplicável. Desconexão do SSE mostra
`Reconectando` sem rotular o job como falho. Não incluir botão genérico de repetir
uma chamada incerta. Recuperações seguem as condições dos serviços existentes.

### Inspeção do trace

Selecionar uma etapa abre suas chamadas e eventos correlacionados. O detalhe
oferece entrada efetivamente enviada, saída parcial/final recebida, parâmetros e
modelo, referências de materiais, validações, tempos, custos disponíveis e erros.
Conteúdo preparado ainda não enviado fica explicitamente identificado. Exibir
JSON/código expansível e prévias autorizadas, sem obrigar a ler payloads para operar.

Cabeçalho do trace mostra a expiração e `Baixar execução`. O pacote é gerado pelo
produto, não por script local, e inclui manifesto do que foi exportado. Ações de
consulta/download têm autorização no servidor e auditoria conforme o contrato.

### Resultado e próxima tentativa

A conversa exibe imagem ou player conforme o formato, avaliações, versões e custo
observado. Ações propostas: visualizar/baixar a peça, comparar versões e registrar
feedback; para vídeo, permitir associar o comentário a um instante. Uma revisão
mantém vínculo com a execução/versão anterior e aplica as regras de orçamento e
continuação. `Novo teste` cria outra execução identificada, sem apagar a anterior.

Não há ação de enviar WhatsApp ou publicar nesta área. Conclusão técnica, crítica
automática e avaliação humana aparecem separadas. Após expirar o trace, a tela
informa a indisponibilidade do diagnóstico, sem afirmar que a peça ou o ledger
foram apagados.

## Critérios de aceite e validação futura

- Somente o perfil admin do titular acessa o laboratório e seleciona negócios.
  Clientes e outros admins não acessam a UI, endpoints, SSE, traces ou downloads,
  mesmo conhecendo IDs/URLs. Negócios não misturam contexto, artefatos ou orçamento.
- Ambos os modos cobrem os formatos já desenvolvidos; execuções ficam na área
  separada, consomem orçamento administrativo e preservam a franquia do cliente.
- Outro admin não recebe o acesso exclusivo do titular. Texto parcial e resposta
  final permanecem distinguíveis; download respeita acesso e retenção configurada.
- Mensagem/mídia percorrem os serviços produtivos com proveniência de simulação.
- Progresso observado corresponde a eventos reais; desconectar/reconectar conserva
  histórico e não duplica efeitos. Falha de rede é distinta de falha da execução.
- Cada chamada pode ser inspecionada com entrada/saída disponíveis e vínculos às
  evidências, sem segredos. Sessão revogada e usuário sem permissão não leem trace.
- Resultado, críticas, versões, decisões e custos ficam acessíveis sem scripts
  novos por rodada; estados incertos e limites de retomada continuam explícitos.
- Testes locais de jornada usam fixtures; ensaio real é separado, com orçamento.
  Integrações usam banco dedicado `_test` e runtime restrito. Implementação exige
  testes de isolamento, SSE/reconexão, idempotência e jornada web, além de `make ci`.

Validação desta alteração: revisão documental e `git diff --check`. Sem alteração
de produção/front, migração, chamada paga ou execução de CI; requisitos e dúvidas
não devem ser apresentados como capacidades já entregues.

## Implementação iniciada — 16/11/2026

Respostas adicionais confirmadas pelo titular:
- Permitir ensaios sem plano comercial ativo, apenas no laboratório com orçamento
  administrativo. Aceite de IA e permissões sobre os materiais continuam exigidos.
- Anexos novos ficam privados no laboratório, sem inclusão no acervo do cliente.

Inspeção: o front existente tem AdminGate, AppLayout e busca de organizações;
`/app/editorial-lab` é uma tela de desenvolvimento no contexto do cliente, não
serve como autorização para o novo laboratório. A API de motion exige owner,
plano ativo e contexto qualificado; ainda precisa de escopo administrativo explícito
para executar sem personificar o cliente. O adapter motion acumula a resposta HTTP
antes de interpretar o JSON; `client.stream` sozinho não entrega deltas ao front.

Primeira implementação: configuração opcional `creation_lab_actor_id`, negada por
padrão; serviço de autorização exige identidade exata e staff ainda ativo.
`GET /api/v1/admin/creation-lab/access` e `/businesses` oferecem descoberta
administrativa com auditoria, paginação e busca literal; usam a transação e o
papel restrito existentes. Não concedem execução nem acesso aos materiais.
Nenhum e-mail foi fixado no código; identificação da conta autorizada solicitada.

Validação atual: sete testes unitários/HTTP passaram, 100% linhas/branches nos
dois módulos novos; Ruff e mypy (343 módulos) passaram. Teste PostgreSQL de
isolamento/revogação passou com papel restrito e banco `_test`, depois de iniciar
o PostgreSQL existente. Nenhuma migration aplicada. CI integral em andamento.

Em 16/11 o titular iniciou Docker Desktop e autorizou explicitamente pausar os dez
consumidores antigos dos projetos meu-braco-direito-platform/local-spark-platform.
A pausa foi aplicada após revisão automática inicialmente rejeitar a ação ampla.
PostgreSQL/Temporal locais iniciados; consumidores permanecem parados. Instâncias
isoladas de CI preexistentes também foram iniciadas para verificar alternativa de
validação sem interferência, sem alteração de seus bancos.

A conta indicada foi conferida em leitura: ativa, ainda não staff. Após autorização
explícita do titular, recebeu staff ativo com registro em platform_audit, mantendo
senha/MFA. Configuração exclusiva vinculada ao UUID no `.env` local ignorado pelo
Git; e-mail/UUID pessoais não fixados no código. Login existente exige MFA para
staff, incluindo recusa de sessão anterior sem MFA.

Front: `/admin/creation-lab`, entrada condicional à autorização da API e seleção
real de negócios, busca/paginação, troca de contexto, erros e revogação. Não há
botão de geração nesta fatia; a UI informa execução ainda indisponível. A página
fica sob AdminGate, sem depender só dele para a autorização exclusiva.
Validação web: tipos e 528 testes passaram, 100% nas quatro métricas; QA Chromium
e build em andamento. Esses testes não comprovam geração produtiva pelo laboratório.

Restam persistência de ensaios/eventos, autorização/RLS do escopo produtivo,
orçamento administrativo, materiais privados, preparação reutilizável, execução
por formato, SSE/deltas, retenção/exportação e UI completa. A base de acesso e
seleção não equivale ao laboratório pronto. Sem chamada paga ou publicação.

### Continuação após dispensa de testes pelo titular

O titular solicitou não corrigir nem executar testes nesta etapa. O CI anterior
foi interrompido após falhas de geocodificação no banco de teste antigo: ausência
de `reference_cost_reservations.policy_id`. Não houve correção desse banco nem
nova execução de testes após a instrução. As validações de acesso/seleção descritas
acima precedem as alterações a seguir e não qualificam a árvore atual.

Implementados rascunhos privados, com mensagem cifrada, formato/modo e teto
proposto; gravação idempotente por operação, histórico por negócio e evento durável
na mesma transação da auditoria. Guardas de identidade exclusiva e staff ativo
continuam aplicadas; guardar rascunho não reserva verba nem inicia geração.
Migração aditiva `0119_creation_lab_drafts` aplicada somente ao banco local de
desenvolvimento conferido em 0118: duas tabelas novas com RLS, nenhum dado
comercial removido. Banco de testes não foi migrado para esta fatia.

Front recebe editor/histórico de rascunhos e acompanhamento SSE autenticado, com
cursor, reconexão e remoção dos eventos exibidos após revogação. Backend revalida
sessão e acesso durante o stream, sem manter sessão SQL/locks enquanto aguarda.
O evento disponível nesta fatia é `draft.created`; não é trace de geração nem
streaming do modelo. Retenção de sete dias, download de pacote, anexos privados,
orçamento administrativo com reserva e execução produtiva ainda não conectados.
Nenhuma chamada paga, geração, publicação ou deploy. Somente formatação aplicada;
não declarar lint/tipos/cobertura/build aprovados para esta continuação.


## Esclarecimentos do titular — planejamento, modos e limites semanais

Laboratório é a área exclusiva do titular para ensaios. Acompanhado e automático
são modos **dentro** dessa área. No acompanhado, o operador revisa o planejamento
antes da geração e os checkpoints pertinentes; no automático, não há pausas
opcionais, mas controles obrigatórios de consentimento, direitos e orçamento
permanecem. Não são produtos ou áreas diferentes.

O planejamento anterior à geração abrange **todos os formatos**, inclusive vídeos:
objetivo/assunto, texto ou roteiro e direção visual. A mensagem natural e o contexto
do negócio alimentam essa preparação. O termo interno “proposta editorial” não
deve exigir que o usuário conheça entidades ou monte IDs manualmente. O fluxo de
motion já possui planejamento criativo; integrá-lo à mesma experiência, sem criar
uma segunda etapa equivalente apenas para repetir o planejamento.

O titular apontou futuros limites semanais por negócio e formato (feed, story,
reel), para controlar custos diferentes de imagens e vídeos, e confirmou que essa
implementação fica para a **próxima etapa**, após o laboratório. Ainda não estão
definidos valores, semana/fuso de referência, relação com plano, nem consumo por
geração, publicação, tentativa, revisão ou falha. Na definição futura, distinguir
peças publicadas de gerações pagas: produzir ou refazer pode custar mesmo sem
publicar. Não converter automaticamente teto monetário em quota de postagem.
O laboratório continua com teto administrativo por execução, sem consumir franquia
do cliente. Nenhuma regra ou quota semanal foi implementada nesta continuação.

## Continuação implementada — anexos privados e exportação do rascunho

Migração aditiva `0120_creation_lab_attachments` aplicada ao banco local de
desenvolvimento, sem tocar bancos de teste ou remover dados comerciais. Tabela
privada vinculada à execução, FORCE RLS, identidade da operação, hash e metadados
cifrados. Direitos de uso explicitamente confirmados por upload. Até 8 arquivos,
100 MiB somados por rascunho; limites individuais herdados de `material_media`:
imagem 5 MiB, áudio 16 MiB e vídeo 50 MiB. O conteúdo passa pela inspeção existente.

Claim e evento duráveis são confirmados antes do PUT no armazenamento privado.
Nenhuma transação fica aberta durante IO. Repetir a operação devolve o estado
persistido e não reenvia; operação com outros bytes/metadados retorna conflito.
Falha ambígua fica `uncertain`; interrupção antes da confirmação pode deixar
`uploading`, sem presumir sucesso ou permitir repetição automática. Recuperação e
limpeza desses uploads ainda precisam de política implementada antes da entrega
completa. Os anexos não são inseridos nas tabelas do acervo do cliente.

Endpoints autenticados de lista, upload, download individual e `draft-package`.
Download confere tamanho/hash e revalida autorização após IO. Sem token ou URL
assinada exposta; respostas não armazenáveis em cache. ZIP montado em memória,
sem cópia persistida no servidor, inclui manifesto, mensagem, eventos até cursor
e anexos confirmados nesse cursor. Não inclui payload de modelo inexistente nem
apresenta orçamento proposto como reserva efetiva. Exportar não inicia geração.

A UI tem upload com confirmação de direitos, estados reais, downloads e eventos
SSE de anexos. Botão é “Baixar rascunho e anexos”: ainda não é o pacote completo
de execução previsto no contrato. O prazo de sete dias se refere ao trace após
encerramento; não há execução terminal nesta fatia nem job de expiração entregue.

Validação nesta continuação: leitura/revisão do código e formatação. **Nenhum teste,
build, typecheck ou chamada paga executado**, conforme pedido vigente do titular.
Armazenamento local iniciado; dez consumidores previamente pausados permanecem
parados. Restam geração pelo produto em todos os formatos, isolamento do contexto
administrativo no pipeline, orçamento separado, aprovações, seleção do acervo,
trace de modelo/deltas, peças/versões/feedback e retenção/limpeza de sete dias.


## Continuação implementada — leitura do contexto selecionado

`GET /api/v1/admin/creation-lab/runs/{run_id}/context` consulta o negócio do ensaio,
sem aceitar tenant/business alternativos do browser. O serviço valida o titular e
staff ativo, lê o ensaio sob RLS e define o escopo somente na transação. A função
SQL `creation_lab_read_scope` é SECURITY INVOKER, mantém FORCE RLS do ensaio e
confere negócio/tenant/ator e staff. Políticas novas são somente `FOR SELECT` nas
tabelas necessárias a kit, contexto, consentimento e consulta de fotos. Nenhuma
regra de owner foi relaxada, membership criada ou permissão de escrita ampliada.

Usa `BrandKitService._state`, `EditorialContextService._version/_present` e
`VisualConsentGate._state` para manter as mesmas projeções/regras. Fatos vencidos
são omitidos com base no fuso cadastrado do negócio. Fotos expõem somente metadados,
sem chave de storage, token ou URL; requerem estado ativo, direitos confirmados e
nenhuma exclusão em andamento. A listagem inicial é limitada a 50 e indica quando
há mais. A seleção efetiva de fotos para geração permanece pendente.

A UI mostra kit/versão, aceite, fatos e nomes de fotos. É consulta do estado atual,
não contexto congelado que já tenha sido enviado ao modelo. `generation_authorized`
permanece falso nesta fatia. Migração 0121 aplicada localmente; sem testes, build ou
chamadas pagas. A autorização administrativa para **executar** serviços produtivos,
com isolamento das escritas, ainda precisa ser implementada separadamente.


## 16/11/2026 — organização da UI e seleção privada do acervo

Laboratório reorganizado com seletor de negócios em cards, busca com campo visível,
cabeçalho compacto após seleção, histórico lateral e editor de pedido. CSS local
reutiliza cores/componentes existentes e prevê layout móvel, foco por teclado e
estados vazios/erro. Novo rascunho e reutilização explícita de pedido geram outra
identidade de operação; a reutilização não copia anexos nem seleção de fotos.

Seleção de até quatro fotos confirmadas do acervo agora é persistida somente no
laboratório, com versão/hash/título cifrados, autorização exclusiva/RLS, identidade
idempotente e evento SSE transacional. Migração aditiva 0122 aplicada ao banco local.
Não modifica o acervo. Material selecionado deve ser revalidado antes de geração.
ZIP captura mensagem, eventos, uploads e seleção em uma mesma leitura SQL; inclui
referências do acervo, não seus arquivos. Recusa exportação acima de 10 mil eventos
em vez de truncar silenciosamente. Sem testes/build/typecheck/QA visual nesta etapa,
conforme orientação do titular. Revisão do código e formatação apenas.

Permanecem pendentes execução produtiva, aprovações, orçamento administrativo
efetivo, trace do modelo e retenção/limpeza de sete dias. Redesign não habilita
geração nem comprova qualidade de motion.

### Detalhes da seleção e próximos pontos de integração

`PUT /runs/{id}/collection` aceita identidade de operação e até quatro IDs distintos.
O serviço deriva tenant/business da execução, confere estado draft, direitos/estado
ativo da foto e serializa alterações no mesmo lock transacional dos eventos de
anexos. Repetir a mesma operação não sobrescreve escolhas posteriores; a UI consulta
o estado atual após o aceite. Reutilização da operação com outros IDs é conflito.

Escolhas ficam em tabela privada com snapshot cifrado, sem chave de storage enviada
ao front e sem escrita nas tabelas comerciais. Alteração posterior do acervo não
muda o snapshot registrado; o futuro executor precisa recapturar as versões/hashes
e rejeitar indisponibilidade ou mudança antes de qualquer efeito pago. Este passo
não é autorização de geração. A UI lista até 50 fotos e mantém visíveis seleções
anteriores fora da lista para permitir removê-las. Paginação completa e prévias de
fotos ainda devem ser incorporadas para acervos maiores.

A nova apresentação foi implementada a partir do screenshot do titular, sem afirmar
conferência visual em browser: testes, builds e QA continuam dispensados a pedido.

## Operação da UI após esta implementação

1. Entrar com a identidade administrativa exclusiva e abrir `/admin/creation-lab`.
2. Escolher negócio, escrever pedido, selecionar formato/modo/teto e salvar rascunho.
3. Anexar materiais privados e selecionar fotos do acervo; a lista tem paginação.
4. Para Reel, selecionar o vídeo MP4. Para feed/story, mencionar o produto/serviço
   ativo do catálogo; o modelo sugere a base e o operador confirma o conteúdo exato.
5. Iniciar a execução. Configuração/consentimento/orçamento ausente impede despacho.
   Aguardar fila, acompanhar eventos e texto parcial, revisar os checkpoints.
6. Aprovar autoriza a próxima etapa dentro do teto. Rejeitar encerra a tentativa.
   Para ajustes, registrar a observação e usar `Usar como novo pedido`; mensagem e
   opções são copiadas, materiais precisam ser selecionados novamente. Não há
   reenvio automático de chamadas incertas nem regeneração ao registrar feedback.
7. Abrir até duas versões, reproduzir vídeo/observar imagens, baixar peças ou pacote
   completo e registrar avaliação, com instante opcional para vídeo.

Configuração: além das credenciais/flags já existentes dos provedores, definir
`CREATION_LAB_ACTOR_ID`, `CREATION_LAB_BUDGET_USD_MICROS` e, para imagens,
`CREATION_LAB_EDITORIAL_RESERVATION_USD_MICROS`,
`CREATION_LAB_EDITORIAL_INPUT_USD_MICROS_PER_MILLION_TOKENS` e
`CREATION_LAB_EDITORIAL_OUTPUT_USD_MICROS_PER_MILLION_TOKENS` (prefixo de ambiente
`MEU_BRACO_DIREITO_`). Tarifas devem corresponder ao modelo editorial configurado;
não foram preenchidas com estimativas nesta implementação. O orçamento é cumulativo
administrativo, não uma quota semanal do cliente. API e worker devem receber a mesma
configuração. Worker e relay existentes executam o fluxo via Temporal; nenhuma
execução é disparada apenas por abrir a página ou salvar um rascunho.

O transporte de parciais foi implementado conforme os eventos documentados
`response.output_text.delta` e `response.completed` da
[Responses API](https://developers.openai.com/api/reference/resources/responses/streaming-events).
O fluxo produtivo sem observador mantém seu transporte anterior. Na modalidade
streaming, o recibo final conserva o objeto terminal da resposta, além dos deltas
persistidos; não representa uma cópia de todos os bytes do protocolo HTTP.

### Configuração local de custos nesta continuação

O teto por ensaio vem da UI; as reservas por chamada não ampliam esse teto.
Tarifas editoriais configuradas para o modelo já usado, GPT-5 mini: US$ 0,25 de
entrada e US$ 2 de saída por milhão de tokens, conforme a
[documentação do modelo](https://developers.openai.com/api/docs/models/gpt-5-mini).
Motion conserva GPT-6.1 Sol dos ensaios locais, com US$ 2/US$ 10 por milhão no
processamento padrão de contexto curto, conforme a
[documentação do modelo](https://developers.openai.com/api/docs/models/gpt-6.1-sol).
Reservas locais: US$ 0,05 editorial, US$ 1 imagem e US$ 0,85 por chamada de motion.
O uso observado/estimado não é uma fatura; cobranças não confirmadas conservam a
reserva. Nenhum modelo foi chamado para validar esta configuração.
