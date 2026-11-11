# Evolução da qualidade de motion a partir das referências

**Decisão mais recente — corrigir antes do teste externo.**
O titular pediu documentar a execução em etapas: (1) contrato/contexto sem
contradições; (2) repertório e referências efetivamente enviados; (3) direção
visual distinta da construção; (4) orientações e exemplos de construção/movimento;
(5) crítica alinhada ao alvo e aos limites; (6) exportação do payload completo.
Plano: `docs/design/refatoracao-contexto-motion-2026-11-10.md`.
Implementação ainda não iniciada. Primeiro concluir os ajustes; depois entregar
prompt, anexos e manifesto para teste manual em ChatGPT, Grok ou outro modelo.
Parar antes de chamadas pagas, geração de assets ou render da peça. Não preparar
um prompt paralelo como se fosse a entrada exata do produto. Aguardar resultado
externo para decidir prova integrada. Infraestrutura existente e kit preservados.


## Ponto 4 — prova integrada com aprovação dos quadros

**10/11 — vídeo renderizado; melhora parcial, qualidade desejada não atingida.**
Após a recuperação dos quadros (migração 0115), o titular aprovou a versão exata.
A API registrou o aceite e o Temporal montou o MP4 reutilizando composição e
materiais. Comparativo: `.local/evals/reel-storyboard-composition-20261109/comparison.html`.
O titular reconheceu mais elementos visuais, mas considerou o desenho infantil e
o resultado ainda distante do acabamento profissional das referências. Esse
feedback não é aprovação criativa final. Pediu analisar dois novos vídeos como
referência de acabamento. Esclareceu que edição de bruto para YouTube é outra
ideia, fora do escopo atual: manter a gravação do cliente e explorar muito mais
a composição/movimento ao redor dela na postagem do negócio. Cortes do bruto
não são pré-requisito para esta melhoria.

A única crítica prevista veio truncada no limite de 8.000 tokens, sem parecer
válido. Pedido encerrado como `failed/MOTION_AI_OUTPUT_LIMIT`, MP4 e recibos
preservados. Corrigida a identidade de falha da continuação para não colidir com
a falha anterior em audit/outbox; migração aditiva 0116 aplicada no dev, sem
limpeza. Nenhuma repetição de IA, render ou correção automática nessa recuperação.

Acumulado da prova: quatro chamadas textuais, estimativa US$ 0,775244 e reservas
US$ 3,40 retidas; nenhuma imagem gerada paga. Estimativa não equivale à fatura.
Qualquer nova chamada exige plano/autorização próprios; não reutilizar o saldo
como autorização automática. 69 testes unitários direcionados (1,55 s) e três
testes SQL em banco `_test` (7,52 s) passaram, com Ruff aprovado. Sem CI completo.
Ponto 4 não qualificado; etapa 5 não iniciada. Resultado detalhado em
`docs/evals/resultado-video-composicao-2026-11-10.md`.

**Análise posterior das referências:** download e inspeção dos dois vídeos de Lucas
Leite concluídos por amostragem visual. Auditoria da chamada confirmou seis quadros
da fonte, nenhuma referência visual de acabamento, skill resumida e três fichas
antigas com restrições incompatíveis com o executor HTML. Modelo `gpt-6.1-sol`,
esforço alto, geração completa; não há benchmark que atribua a causa ao modelo.
A direção da prova também induziu os desenhos de jarra/xícara. Corrigir contexto
e testar uma cena exigente é o próximo recorte proposto, ainda não implementado.
Detalhes: `docs/evals/analise-acabamento-motion-2026-11-10.md`. Nenhuma nova chamada paga.

**Histórico — reformulação da composição autorizada, antes do vídeo.**
O titular gostou das xícaras desenhadas e autorizou reformular a composição.
Isso não aprova a galeria anterior para animação. A nova direção alterna gesto
real, transformação ilustrada e convite à pausa, com foco, escala e organização
distintos; preserva desenhos figurativos, kit, fonte integral, áudio e aprovação
humana dos quadros. Esse roteiro é específico da prova Café Pausa.

Orientação geral de geração/crítica ajustada para avaliar evolução da composição,
sem impor variedade arbitrária: acrescentar desenhos a um layout repetido não
demonstra elaboração por si só. Repetição com função narrativa continua válida.
Vinte testes direcionados passaram em 1,09 s; Ruff/format aprovados. Worker
reconstruído; renderer, runtime, hashes históricos e banco não foram alterados.

Novo payload preparado para o produto, dentro da autorização original: até
US$ 3,70 restantes + US$ 1,70 retidos = US$ 5,40. Duas chamadas textuais/contagens,
até duas ilustrações opcionais, sem correção automática; parar nos quadros.
Plano: `docs/evals/plano-reformulacao-composicao-2026-11-09.md`.
Pendente: nova galeria real, aceite humano e vídeo/crítica. Etapa 5 não iniciada.

**Histórico da retomada anterior — três quadros após correção técnica local.**
Retomada autorizada executou uma geração completa, validada pelo contrato. O modelo
criou três cenas com desenhos SVG próprios; não solicitou ilustrações pagas.
O render integrado falhou (`MOTION_RENDER_EXECUTION_FAILED`): elementos estáticos
receberam tracks com `beats:[]`, mas a biblioteca exige ao menos um intervalo.

Diagnóstico local preservou o original e acrescentou somente holds idênticos ao
estado inicial dessas tracks. O mesmo renderer isolado capturou três PNGs reais,
sem nova IA, MP4 ou alteração/reabertura do pedido encerrado. Galeria aberta para
o titular: `.local/evals/reel-storyboard-resume-20261109/diagnostic-gallery.html`.
É uma captura após correção técnica, **não** uma galeria aprovada/persistida pelo
fluxo integrado. O titular depois solicitou reformular essa direção antes do vídeo. Movimento/áudio não
foram avaliados; a composição ainda repete vídeo à esquerda e desenho à direita.

Instruções da biblioteca agora explicitam 1–12 beats por track e hold para elementos
estáticos. Runtime e hashes dos snapshots permanecem intactos; não adicionamos
recuperação automática ou nova geração. Cinco testes direcionados passaram em
0,68 s, Ruff aprovado; captura real passou pelo sandbox/protocolo 2. Sem CI completo.

Uso estimado da retomada: US$ 0,180125; somado à tentativa truncada, US$ 0,421603.
Reservas das duas tentativas: US$ 1,70 retidos para conciliação. Nenhuma imagem ou
crítica paga, nenhuma correção paga. Os limites autorizados não foram ampliados.
Plano/resultado: `docs/evals/plano-retomada-storyboard-integrada-2026-11-09.md`.
Pendente: decisão visual, tratamento da falha na integração e vídeo/crítica final.
Nenhuma equivalência às referências demonstrada; nenhuma etapa 5 iniciada.

**Histórico da conclusão do ponto 3 — quadros completos por cena e aprovação antes do MP4.**
Pedidos com `storyboard=true`, quando a capacidade estiver explicitamente habilitada,
produzem um PNG completo por cena com a composição e os assets reais da geração.
O modelo indica o momento representativo; o renderer captura somente esses momentos,
sem codificar vídeo/áudio. Não são todos os frames nem evidência de ritmo/mixagem.

Galeria HTML e metadados privados ficam disponíveis pela API autenticada. O aceite
vincula versão e hash do conjunto; reprovação registra feedback e encerra o pedido,
sem tentar outra chamada paga. A aprovação emite outbox e retoma pelo Temporal,
reutilizando composição e ilustrações, revalidando fontes, consentimento e orçamento.
Reentregas são bloqueadas por identidade durável. A revisão/aprovação final da peça
continua distinta da aprovação inicial de composição.

Validação: 295 testes Python direcionados em 3,70 s e 72 testes Node em 0,55 s;
mypy e Ruff aprovados. IO de banco/browser/provedor substituído nos testes locais;
regressão SQL de isolamento/aceite/reentrega adicionada, não executada. Sem CI
completo, chamadas pagas, reconstrução Docker, migração aplicada ou prova criativa.

**Pendências registradas ao concluir o ponto 3 (resolvidas na preparação do ponto 4):** aplicar `0114_motion_storyboards`, reconstruir
renderer com protocolo 2 e configurar seu novo digest; habilitar
`motion_storyboard_enabled` (default false) e enviar `storyboard=true`.
Pedidos antigos continuam no fluxo anterior. Naquela conclusão, o ponto 4 aguardava comando: prova real
com IA, apresentação dos quadros para o titular e avaliação do vídeo após aceite.
Não há uma nova peça real produzida nesta implementação nem orçamento reutilizado.

### O que o titular verá

Uma imagem completa de cada cena (até 12), usando HTML, texto, kit, componentes,
fotos e ilustrações do próprio pedido, no viewport 720 × 1280. Não é um placeholder
nem catálogo de ícones. Nos testes são pixels sintéticos; a prova paga futura usa a
peça gerada pela IA. O titular escolheu explicitamente ver/aprovar os quadros.

O modelo continua devolvendo direção, plano e código na mesma chamada. Esta etapa
interrompe **antes do render integral do vídeo**, não antes de o modelo escrever
qualquer código de movimento. `keyframe_ms` por cena identifica um momento com a
arte visível; tempos ausentes, fora da cena, desordenados ou coincidentes após
quantização a 30 fps são recusados antes de gerar ilustrações. O schema não prova
que todos os elementos estejam visualmente bem compostos; essa é a avaliação humana.

### Render e pausa durável

- `RenderBundle.frames_only=true` usa protocolo 2, sem fallback para MP4; imagens
  antigas rejeitam esse protocolo. Mantém container isolado, runtime/assets por
  hash, limites de bytes, CSP, bloqueio de rede e sandbox do Chromium. Captura PNG
  direto do browser nos momentos pedidos, aguardando fontes e imagens. Protocolo 1
  e evidência extraída do MP4 continuam intactos para o vídeo final.
- Evidência estática usa `browser_keyframes`, distinta de `decoded_mp4`; não é
  usada para afirmar qualidade temporal ou áudio. Não executa ffmpeg/ffprobe no
  modo de quadros, mas o vídeo de entrada pode ser decodificado pelo navegador.
- Render e uploads possuem efeitos duráveis próprios. Cada PNG é persistido e
  verificado por download/SHA. Composição, contexto, frames e referências das
  ilustrações ficam cifrados, com manifesto/hash e fingerprint da fonte.
- `motion_storyboards` tem RLS obrigatória, vínculo tenant/negócio/pedido e estados
  `awaiting_approval`, `approved`, `rejected`, `rendering`. Uma versão por pedido
  nesta fatia; não há reedição automática de quadros após reprovação.
- Pedido permanece `running` enquanto aguarda avaliação; a atividade Temporal
  inicial termina com `awaiting_storyboard`, sem ocupar worker ou efetuar polling.
  As proteções existentes de alteração/revogação durante operação continuam ativas.
- Aprovação e evento `motion.storyboard_approved` são transacionais com auditoria.
  Relay inicia a mesma classe de workflow Temporal com identidade distinta para a
  continuação. O serviço confere o evento real, titular e estado; muda para
  `rendering` antes de IO. Reentrega não toma posse nem repete efeitos pagos.
- Continuação valida contexto/acesso e restaura ilustrações privadas por hash.
  Não chama geração textual ou de imagem novamente. Render/crítica e correção
  condicional existentes seguem depois do aceite. Correções podem alterar o vídeo;
  a aprovação desta galeria não substitui a decisão final sobre a peça resultante.
- Reprovação registra feedback cifrado e encerra com `MOTION_STORYBOARD_REJECTED`,
  liberando mudanças pendentes. Uma nova tentativa depende de novo pedido e seu
  orçamento; este passo não implementa um editor nem revisão paga automática da arte.

### API e ativação

No endpoint existente de criação, enviar `storyboard: true` junto de operação,
instrução e material. Campo false é omitido e não muda a identidade de pedidos
históricos. `motion_storyboard_enabled` é false por padrão e impede entrada da
capacidade antes da configuração. Revalidação também impede retomada se desligada.

Sob `/api/v1/organizations/{tenant}/businesses/{business}/motion-requests/{request}`:

- `GET /storyboard`: estado, version_id, content_sha256, cenas/mensagens/tempos/SHA.
- `GET /storyboard/gallery`: HTML com os PNGs completos embutidos, escapando textos
  e sem código do modelo, URLs de storage ou scripts. Autenticação Bearer e
  `Cache-Control: no-store`; pode ser salvo pelo cliente autenticado para avaliação.
- `POST /storyboard/decisions`: operation_id da decisão, version_id,
  content_sha256 e `decision: approve|reject`, com feedback opcional.
  Versão/hash divergentes são rejeitados; mesma operação/conteúdo é idempotente.

A galeria é acessível pela API existente; não foi criado um novo portal/login ou
botão de aceite que dispense o cliente autenticado. Na prova conduzida pelo agente,
a galeria será apresentada ao titular e a decisão explícita dele será registrada
pela API. Não há aprovação inferida de silêncio ou de passagem do tempo.

Migração 0114 e nova imagem do renderer precisam ser aplicadas antes da ativação;
nenhum ambiente havia sido modificado no ponto 3. Orçamento e ativação do
ponto 4 estão registrados no estado vigente acima. Validação SQL adicionada para RLS, pausa, versão exata, outbox único e
retomada única em `_test`; não executada para evitar a suíte longa solicitada.


## Histórico do ponto 2 — criação/seleção e geração de elementos

**Ponto 2 implementado — componentes, acervo e ilustrações sob demanda.**
O fluxo do Reel reúne 16 componentes vetoriais, desenho original por código,
até quatro fotos autorizadas do acervo e até duas ilustrações geradas quando
necessárias. A mesma geração textual declara a arte e seus caminhos; o serviço
cria os PNGs antes do render, e a crítica recebe os pixels gerados. Kits, skills,
biblioteca de movimento, Temporal e histórico privado continuam preservados.

Ilustrações têm identidade por pedido/asset, reserva própria no ledger compartilhado,
registro de uso/proveniência e upload privado verificado. Correções reutilizam os
mesmos arquivos e não podem alterar a lista para disparar novas imagens. Despacho
repetido, falha incerta, custo desconhecido/excedido e falta de orçamento interrompem.
A reserva é limite de admissão local, não teto de faturamento imposto pela Images API.

Ativação explícita desabilitada por padrão: `motion_illustrations_enabled=false`,
reserva e orçamento de imagens zero. O orçamento de imagens é parte do orçamento
total do Reel; precisa deixar espaço para geração e crítica. Sem novas permissões,
migração ou chamadas pagas. Modelos e contratos históricos preservados; não há
ativação retroativa para pedidos capturados sem essa capacidade.

**Na conclusão do ponto 2, o próximo ponto era:** quadros principais com a arte
pronta antes do vídeo (ponto 3, implementado conforme registro acima). Prova visual com IA real e aceite criativo continuam posteriores;
esta implementação não demonstra que o acabamento já atingiu as referências.
Validação: testes direcionados com pixels sintéticos e transporte simulado; sem CI
completo, banco ou render integrado. Regressão SQL adicionada para execução no `_test`.
273 testes direcionados aprovados em 3,76 s; Ruff/format e mypy em 12 módulos aprovados.

### Contratos e execução

- `reel-creative-v4` inclui `motion-elements-v1`: 12 contornos do Maestro
  autorizado e quatro objetos próprios, partes animáveis, nós e conectores.
  `code` permite desenhos originais; `component` exige ID do catálogo;
  `authorized_asset` usa acervo e `generated_asset` identifica ilustração.
- `collection_photo_ids`: até quatro fotos distintas, ativas e prontas do
  tenant/negócio, com direitos confirmados, versão e SHA revalidados. Originais
  no render, miniaturas de até 512 × 512 no payload contado, sem chaves de storage.
- `illustration_generation`, quando configurada, entra no snapshot e fingerprint.
  `illustrations` na composição declara `asset_id`, `description` e `purpose`.
  A lista vazia não gera chamada nem reserva extra; é omitida no histórico.
  Identificadores usam `assets/illustration-<nome>.png`; a direção e o plano
  precisam usar esses assets. Caminhos inexistentes, duplicados ou sem uso no
  plano são recusados antes da cobrança. Áudio original é conferido antes de gerar.
- O modelo decide a necessidade dentro dos limites, sem outra chamada obrigatória
  de planejamento. Serviço constrói prompt com identidade do kit, descrição e
  função narrativa. Apenas arte ilustrativa; não substitui evidência real de
  produto/local/pessoa. Essa orientação semântica ainda depende de crítica humana
  e do modelo; a validação de schema não comprova o conteúdo da imagem.
- Adaptador existente `OpenAIVisualProvider` ganhou `background` opcional, omitido
  em requisições antigas. Esta fatia usa `gpt-image-2.5-flare-2026-09-08`, qualidade
  medium, 1024 × 1024, PNG transparente e uma saída por chamada. Não usa cromakey,
  rede dentro do renderer nem outro executor. Requisição sem referências visuais;
  acervo real já segue como arquivo, não como material a redesenhar.
- Cada imagem tem UUID derivado do pedido e asset, efeito `generate` com propósito
  `motion_illustration`, reserva e resultado cifrado com uso/modelo/request ID/SHA.
  Reutiliza as regras compartilhadas de `MotionEffects.reserve_submission`.
  Efeito `upload` separado registra o objeto privado, com verificação de download.
  Nenhum IO de provedor/storage acontece sob lock transacional.
- Antes do lote, verifica espaço para todas as imagens declaradas e a crítica.
  Cada chamada revalida pedido/consentimento/contexto e limites do ledger.
  Resultado sem uso, custo acima da reserva, PNG inválido/opaco/vazio, revogação ou
  falha de storage interrompem, sem fallback pago ou repetição. Falha do provedor
  conserva a reserva incerta; resultado conhecido registra uso antes do upload.
- Imagem e miniatura são anexadas ao `PreparedMotionInput`, com proveniência
  `generated_illustration`. Até seis miniaturas (quatro fotos + duas ilustrações)
  participam das contagens existentes da crítica/correção. Declarações permanecem
  imutáveis nas correções; layout e movimento podem mudar reutilizando os pixels.
- Reentrega do workflow não regenera: claim durável e execução existente continuam
  impedindo repetição. Não há retomada automática de uma imagem com resposta perdida.

### Orçamento e ativação

`motion_illustrations_enabled`, `motion_illustration_reservation_usd_micros` e
`motion_illustration_budget_usd_micros` têm defaults false/0/0. O último é suborçamento
dentro de `motion_request_budget_usd_micros`, não verba adicional. Deve comportar ao
menos uma reserva; o total do Reel deve comportar esse suborçamento mais duas reservas
de modelo (geração/crítica). Limite de imagens é min(2, orçamento/reserva).
Correção continua condicional ao saldo, sem gerar outras imagens.

Estimativa pelo uso efetivo: US$ 5/M tokens de texto de entrada, US$ 8/M de imagem
quando reportados e US$ 30/M de saída, sem desconto de cache. **Reserva não é uma
prova de teto da fatura**: a Images API não oferece aqui um limite de tokens de
saída aplicado pelo cliente. O custo não foi estimado por tabela de outro modelo.
Excesso conhecido interrompe antes da próxima imagem e fica registrado no efeito;
ledger retém a reserva para conciliação. Uso desconhecido não libera verba.

Parâmetro de transparência e tarifas conferidos nas fontes oficiais em 09/11/2026:
[geração de imagens](https://developers.openai.com/api/docs/guides/image-generation)
e [GPT Image 2.5 Flare](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare).
Configuração está no overlay e exemplo do worker; nenhum `.env` foi ativado nesta
rodada. Execução paga futura requer plano/orçamento próprio e configuração explícita.

### Validação e limites

Testes locais cobrem criação → persistência privada → render/crítica/correção com
pixels sintéticos, chamadas HTTP simuladas, recusa de referências inválidas,
orçamento, falhas incertas e proibição de regeneração. Regressão SQL adicionada
para identidade/custo/proveniência/reentrega em banco dedicado `_test`, não executada.
Sem prova criativa, CI completo, migração, chamadas pagas ou publicação.

Seleção automática de catálogo inteiro, interface de escolha de fotos, busca de
mídia externa, variações/regeração de imagens, recorte de produtos reais e catálogo
completo do Finalizador não fazem parte desta fatia. Próximo ponto é conferir
quadros principais; expansão depende do que a composição e prova visual mostrarem.

## Histórico do ponto 1: direção visual por cena

Após a avaliação de que o motion continua muito simples, o titular autorizou
somente o primeiro ponto da nova sequência: direção criativa por cena. Não
confundir esta sequência com os quatro passos técnicos históricos abaixo.

Novos snapshots usam `reel-creative-v3`, com `scene-direction-v1`. A geração e
a correção devolvem `scene_direction` obrigatório junto de `motion_plan` e do
código, na mesma chamada contabilizada. A direção especifica, para cada cena:

- Base no briefing/fatos, representação visual, composição do quadro principal
  e ação narrativa que explica a mensagem.
- Ordem de atenção vinculada aos IDs dos elementos da própria cena.
- O que cada elemento representa, sua aparência/partes e construção por código
  ou uso de asset já autorizado. Grafismos originais não exigem biblioteca pronta.

O `motion_plan-v1` continua sendo a única fonte de tempos, estados, trajetórias,
relações e transições. A direção associa significado e arte a esses movimentos;
não duplica a timeline. A instrução pede planejar a arte antes de escrever o
código, mas esta fatia não cria uma etapa separada de storyboard/aprovação nem
prova a ordem interna de raciocínio do modelo.

`motion_plan.py` exige correspondência exata de cenas na ordem do plano, todos
os elementos uma única vez, focos distintos locais à cena e origem coerente com
o asset do elemento. Falha interrompe antes de reservar render, tanto na geração
quanto na correção. Novos contratos exigem direção não nula no schema de resposta.
Descrições vazias, versões desconhecidas e meios de geração indisponíveis são
recusados. O schema não comprova pertinência semântica, acabamento ou execução.

A direção acompanha a composição nas versões cifradas, no contexto da crítica
e nas correções. O contrato capturado continua no fingerprint e no payload
contabilizado. Sem chamada adicional obrigatória, retry ou aumento de limites;
o texto extra consome parte do orçamento já validado. `reel-creative-v2` continua
exigindo o plano, sem direção nova; v1/sem contrato preservam seus requisitos.
O campo nulo é omitido ao serializar composições antigas. Sem migração.

**Validação:** 201 testes direcionados em 5,18 s, Ruff/format e mypy aprovados.
Cobertura de 100% das 81 instruções e 36 branches dos três módulos medidos
(`motion_scene_direction`, `motion_plan`, `motion_creative`), não da aplicação
inteira. Regressão SQL adicionada para ausência de direção e reentrega sem nova
geração; não executada nesta rodada. Sem CI completo, banco, API paga, render
ou deploy. O fixture sintético continua identificado como prova técnica.

**Plano registrado ao concluir o ponto 1 (estado atual acima):**

2. Criação/seleção dos elementos e adaptação dos materiais existentes ao kit.
3. Quadros principais com a arte pronta para conferir composição antes de animar.
4. Animação/crítica representativas e nova prova visual pelo produto.

O titular informou que o conteúdo do Maestro está liberado para nosso uso.
Essa autorização foi registrada; a observação documental anterior sobre o ZIP
não bloqueia o trabalho autorizado. Nenhum código Maestro foi incorporado nesta
primeira fatia. Qualidade criativa continua não comprovada por esta implementação.

## Histórico da sequência de movimento e prova integrada

Estado: passos 1–3 implementados. Quarto passo concluiu o fluxo técnico real após
retomada autorizada; comparativo A/B disponível, avaliação humana recebida:
melhora parcial, ainda muito longe do alvo. Qualidade criativa não aceita.
A crítica cobriu três de 40 eventos sem sequências próximas das principais
transições: esse resultado não demonstra acabamento equivalente às referências.
[Resultado, custos e limites](../evals/plano-retomada-motion-temporal-2026-11-09.md).
O titular forneceu quatro Shorts adicionais como alvo de qualidade e processo.
Complementam o [Reel específico](../evals/referencia-reel-Db9axeiOotS-2026-11-09.md)
e a [análise do vídeo completo](../evals/referencia-motion-youtube-fqaEZqPzKZs-2026-11-09.md).
A avaliação do Café Pausa continua sendo melhora parcial, abaixo do nível esperado.

## Esclarecimento do titular: qualidade de movimento, identidade do negócio

As referências exemplificam acabamento de motion; não fornecem o kit visual das
peças do produto. Cores, fontes, logo e identidade vêm do kit confirmado do negócio.
Fotos, textos e fatos vêm dos materiais/contexto autorizados. O plano de movimento
pode aproveitar princípios de ritmo, trajetória, aceleração, continuidade,
transformação e coordenação, adaptados ao pedido. Não importar a estética de uma
referência como padrão nem penalizar uma peça por usar a identidade do cliente.

Os quadros de referência são evidência técnica identificada separadamente do kit
e dos assets de composição. A integração futura deve manter essa distinção no
snapshot, no payload, na crítica e na proveniência. Exemplos das bibliotecas não
são autorização para incorporar suas marcas ou mídias à peça do cliente.

## Primeiro passo entregue — 09/11/2026

- `app/schemas/motion_plan.py` define `motion-plan-v1`: cenas cobrem a duração;
  cada elemento descreve estados, propósito, relações, trajetória e beats com
  tempos absolutos. Curvas nomeadas, Bézier e mola têm parâmetros validados.
  As descrições de estado/trajetória ainda são direção textual; não constituem
  uma linguagem executável nem medição automática de posição no vídeo.
- `reel-creative-v2` exige esse plano em geração/correção, na mesma chamada.
  `concept` resume a ideia. A correção recebe o plano anterior e instrução de
  preservar identidades de elementos não alterados. Não há detector novo de
  mudanças locais; isso permanece orientação ao gerador.
- O serviço verifica duração, existência do estilo no snapshot e vínculos aos
  assets preparados antes do render. Texto/grafismo não referenciam arquivos;
  imagem/vídeo identificam material autorizado. O kit continua sendo a origem
  da identidade; o plano não é um validador automático de cores/fontes no HTML.
- Contexto, skill, biblioteca, orçamento, efeito durável e versões privadas
  existentes são reaproveitados. Schema e plano entram no payload contabilizado;
  não se acrescentam chamadas obrigatórias. O plano pode aumentar tokens, dentro
  dos limites existentes. Históricos v1/sem contrato permanecem compatíveis.
- A crítica atual continua aceitando os dois contratos e recebe o plano como
  intenção; a coleta de sequências e a avaliação temporal foram implementadas
  posteriormente no passo 3, conforme registro abaixo.
  Referências externas continuam fora dos assets e não são enviadas visualmente
  por esta mudança. Não se declara qualidade a partir do texto do plano.

A sequência local já analisada do Reel Db9axeiOotS, de **21,1 a 22,9 s, a cada
0,1 s**, fundamenta a necessidade de sobrepor transição de composição e entrada
escalonada de elementos. Ela não permite recuperar curvas exatas. Usamos relações,
tempos e estados explícitos para descrever esse tipo de coordenação, sem fixar
um preset de duração, importar cores/clarão ou alegar parâmetros medidos que não
foram obtidos. Ver [evidência original](../evals/referencia-reel-Db9axeiOotS-2026-11-09.md).

**Validação:** 155 testes direcionados passaram em 8,75 s; Ruff e mypy aprovados.
Incluem schema, payload sem rede, contexto preservado, ausência de repetição da
chamada, compatibilidade histórica e bloqueio anterior ao render de geração e
correção. Adicionada regressão SQL de falha durável/reentrega, não executada.
Sem CI completo, migração, render, API paga ou deploy nesta fatia.

O passo 2 foi implementado posteriormente, conforme registro abaixo. O contrato
não comprova que o HTML executa seu plano nem que atingiu as referências.

## Segundo passo entregue — 09/11/2026

`app/assets/motion_html_renderer/movement-v1.js` fornece `window.MotionV1`:

- Timeline com estados numéricos, IDs DOM alinhados aos IDs planejados, tempos
  absolutos e beats sem sobreposição por elemento. Cada beat herda o estado final
  anterior; intervalos preservam o estado e seek reverso recalcula tudo.
- Curvas linear, cúbicas de entrada/saída, Bézier com solução de x e mola com
  rigidez/amortecimento/massa. A mola é normalizada na duração do beat para
  alcançar o alvo continuamente; não é simulação incremental por frame.
- `stagger` desloca os beats de grupos com intervalo explícito. Tracks coordenadas
  permitem transições entre composições; spans no HTML permitem texto segmentado.
- Translation, escala, rotação, opacidade, raio e máscara inset. Composição,
  tipografia, cores e materiais continuam definidos pelo kit e pela direção.
  Elementos com layout/transforms próprios usam wrappers; não há template imposto.

`movement_runtime` no contrato criativo registra versão, hash e instruções da API,
chegando à geração/correção pela mesma chamada já contabilizada. O plano continua
sendo direção: o gerador deve traduzir estados/tempos em tracks. Não há compilação
automática das descrições textuais, verificador de uso efetivo dos helpers ou
comparação automática entre plano e movimento renderizado nesta etapa.

O orquestrador confere disponibilidade antes da geração paga, registra o hash no
efeito de render e passa-o ao adapter. O adapter verifica os bytes e inclui a
biblioteca antes da cena, mantendo execução exclusivamente no Chromium e o limite
de 1 MiB de `scene.js` completo. O hash da cena no pacote/diagnóstico cobre também
a biblioteca. Pedidos sem a capacidade permanecem autocontidos, sem prefixo novo;
versão/hash indisponível falha, sem substituição silenciosa. A distribuição do
worker já inclui `app/assets`; não exige mudar o protocolo nem reconstruir a imagem
do renderer. Nenhum worker foi reiniciado/deployado nesta fatia. Após publicar uma
versão da biblioteca, mantê-la imutável e criar nova versão para alterações futuras.

**Validação proporcional:** 266 testes Python passaram em 4,20 s, 8 Node em 0,51 s,
Ruff/mypy aprovados. Ajuste de compatibilidade confirmado por 30 testes em
1,98 s; recusa de cena vazia mesmo com prefixo confirmada em 5 testes (1,66 s). Regressões cobrem endpoints/curvas, avanço/retorno/repetição, holds,
coordenação, vínculo ao efeito/pacote e recusa antes de chamada paga quando o
runtime não corresponde ao snapshot. Sem CI completo ou testes de banco.

[Render sintético local e quadros](../../.local/evals/motion-movement-step2-20261109/report.html):
4 s, 120 quadros, 360×640, 30 fps, H.264 íntegro, sem áudio. Fixture manual em
`app/tests/fixtures/motion_movement_scene.cjs`, empacotada pelo adapter real e
reproduzida no Chromium com sandbox, CSP e roteamento bloqueado; frames do MP4
inspecionados. Sem dados de clientes ou IA paga. A sandbox da ferramenta bloqueou
a primeira abertura do navegador; a execução local autorizada fora dessa sandbox
concluiu o render, mantendo a sandbox do Chromium. Isso não é nova qualificação
do isolamento Linux/Temporal, nem peça gerada pelo produto, nem prova de ganho
criativo. A calibração criativa permanece pendente.

O passo 3 foi implementado posteriormente, conforme registro abaixo. Passo 4
continua sendo a comparação integrada com IA, mediante orçamento e avaliação
humana. Não expandimos formatos nesta fatia.

## Terceiro passo entregue — 09/11/2026

A capacidade `temporal_review` (`motion-temporal-v1`) é capturada no snapshot e no
fingerprint. O serviço `motion_temporal.py` seleciona até três eventos ao longo
da peça: beats, transições de cenas e holds de texto, inclusive intervalos de
permanência implícitos. Distribui a seleção no tempo; não usa áudio, detecção de
batidas ou preferências estéticas para escolher. Em peças complexas, muitos
movimentos permanecerão sem cobertura próxima, explicitados como omitidos.

O render recebe até 20 tempos: cinco pontos de contexto mais vizinhos, início,
meio, fim e posterior de cada evento selecionado. Converte tempos aos quadros de
30 fps, elimina duplicatas e respeita os limites da peça. Eventos muito curtos
podem ter menos de três quadros distintos e são insuficientes. Bordas truncadas
são identificadas. Não se aumenta o teto anterior de 20 imagens por versão; a
fonte mantém seus limites próprios. A contagem de entrada inclui o manifesto e
as imagens exatas; exceder a reserva interrompe, sem corte silencioso ou repetição.

A seleção solicitada integra o efeito durável do render. O manifesto, com IDs
por cena/elemento, janela, PTS arredondados, SHA-256, cobertura e omissões, acompanha
o pacote privado de evidências. O adapter e o validador reconstroem o manifesto
a partir do plano e dos quadros realmente disponíveis; diagnósticos ou texto do
modelo não podem inventar uma sequência ausente. O pacote existente continua
usando frames decodificados do MP4 final, com PTS conferidos pelo runner.

`MotionReview.temporal_checks` exige uma ocorrência de cada nome:

| Check | Critério associado | Foco da observação |
| --- | --- | --- |
| `continuity` | motion | Descontinuidades visíveis na sequência amostrada |
| `overlap` | composition | Oclusões e sobreposições indevidas |
| `reading_time` | legibility | Permanência e legibilidade observadas, sem regra universal de segundos |
| `coordination` | motion | Relações entre elementos e passagens de composição |

`pass` precisa cobrir todos os eventos selecionados; `fail` localiza eventos
completos. Cada evento conclusivo exige referências a pelo menos três tempos,
incluindo primeiro e último da janela. `uncertain` nunca vira issue temporal
acionável; `adequate` não pode ocultar check temporal falho/incerto. Correção
por check temporal falho liga índices de issues major/blocking, no critério
correto e com tempo/hash dentro da sequência citada. Issue genérica de motion
não contorna incerteza temporal: requer esse vínculo ou falha criativa narrativa
fundamentada pelas regras anteriores. Uma correção apenas estática continua
possível mediante sua evidência própria, sem alegar ganho temporal.

A preferência por current quando há anterior requer sequências completas citadas
das duas versões. Ausência de plano/sequência anterior impede afirmar essa
preferência; empate/incerteza preservam a anterior conforme o fluxo existente.
Planejamento, runtime, marca e materiais não são reescritos pelo crítico: a
correção recebe a mesma evidência e instruções para localizar cena/elemento e
preservar o que não precisa mudar. Referências/calibrações orientam funções e
acabamento, sem exigir a identidade visual alheia. **Não foram integrados novos
vídeos/quadros de referência externos:** a comparação visual com eles não pode
ser alegada. Esse fornecimento poderá ser definido para a prova, com orçamento.

**Validação:** 292 testes Python em 7,29 s, Ruff/mypy; ajuste final contra contorno
da incerteza confirmado em 41 testes (0,80 s). Testes sem rede cobrem cobertura,
eventos/quadros inventados, versões trocadas, imagem ausente, limites pequenos,
preferência A/B, correção sem vínculo e passagem da seleção/manifesto pelo
orquestrador. O fluxo simulado usa duas chamadas existentes (geração e crítica),
sem acrescentar chamadas. A regressão SQL histórica foi ajustada à capacidade
anterior; não executamos testes de banco ou CI completo.

[Sequências extraídas do MP4 sintético do passo 2](../../.local/evals/motion-temporal-step3-20261109/report.html):
16 PNGs decodificados, três janelas completas, 12 eventos omitidos registrados.
Tempos/hashes e imagem de inspeção preservados. Sem novo render, dados de clientes,
modelo pago, migração ou deploy. Não houve julgamento real de IA nesta fatia;
testes de contrato não demonstram sensibilidade do crítico nem melhoria estética.

**Próximo trabalho, somente após comando:** quarto passo, prova pelo fluxo do
produto com baseline, custo/tempo, crítica real e decisão humana. A política de
três janelas/20 imagens é uma primeira escolha conservadora de custo; sua eficácia
precisa ser medida nessa prova antes de alterar limites ou expandir formatos.

## Quarto passo executado — 09/11/2026

A primeira geração foi truncada em 16.000 tokens. A retomada explicitamente
autorizada usou teto de 32.000, produziu 18.102 e concluiu em 9 min 34 s pelo fluxo
real, com uma crítica, sem correção. Download privado validado por hash e worker
próprio encerrado. Total com falha: US$ 0,562636 estimado, US$ 2,55 reservado.

A/B está disponível no relatório vinculado acima. O modelo aprovou os checks,
mas as janelas selecionadas privilegiaram entrada de uma palavra, de um ponto
e hold do CTA. Faltaram sequências próximas das duas principais transições. O
parecer é limitado aos eventos observados; nenhuma equivalência criativa é
presumida. A crítica usou 7.924 de 8.000 tokens, outro limite operacional a medir.

A decisão humana foi recebida: melhorou, mas ainda está muito longe. O titular
identificou vídeo reposicionado, textos e poucas formas, sem variedade de
componentes figurativos, imagens e ícones relacionados à mensagem. A hipótese
de que possa atender um pequeno cliente não constitui aceite comercial. Não
houve confirmação específica de áudio, enquadramento ou ausência de regressões.

## Diagnóstico após avaliação humana — composição visual insuficiente

Reinspeção dos quadros de B e das sequências locais de `Lt1jJmG3l_k` e
`Db9axeiOotS`: B combina gravação, títulos e linhas; as referências também
mostram ilustrações, interfaces, listas com estados e exemplos visuais associados
ao conteúdo. Quadros comprovam essa diferença de repertório, não fluidez integral
ou sincronismo. O alvo envolve representação visual da mensagem, além de curvas.

Gargalos encontrados no código vigente:

- `motion_inputs.py` prepara vídeo, duas fontes e logo opcional. A integração
  não entrega uma seleção de fotos/ilustrações/ícones do acervo por cena; kit,
  skills e styles presentes no contexto não equivalem a esses materiais.
- `motion_creative.py` e as regras de geração enfatizam tipografia, gravação,
  enquadramento e transformações. Já proíbem reduzir motion elaborado a títulos
  e fades, mas faltam seleção de representações e componentes concretos por
  mensagem. Repetir essa proibição não demonstra solução.
- `MotionV1` executa movimentos de elementos; não fornece por si só o desenho
  de objetos, ilustrações ou componentes narrativos. O plano permite grafismos
  e imagens, sem que isso assegure sua presença ou pertinência no resultado.
- A entrada integrada mantém `transcript=None`. Ainda não há base para ilustrar
  palavras faladas no instante correto; essa capacidade requer alinhamento.
- A crítica aceitou a peça simples e amostrou eventos pouco representativos.
  Aprovação técnica/temporal não certifica o objetivo criativo do titular.

Recorte proposto após o feedback (primeiro ponto implementado acima):

1. Planejar por mensagem: significado, representação visual, material/componente,
   estados e passagem para a próxima cena. Preparar quadros-chave antes de gastar
   com render completo; usar uma cena exigente para investigar capacidade visual.
2. Conectar acervo e uma pequena biblioteca de componentes pertinentes (objetos
   vetoriais, recortes, cards, diagramas/listas) à composição e ao kit. Produzir
   somente assets ausentes necessários; geração paga exige plano próprio. Não
   impor quantidade de ícones nem inserir decoração sem função narrativa.
3. Animar relações e transformações desses componentes no executor existente,
   preservando identidade do negócio. Transcrição/alinhamento quando houver fala.
4. Criticar cenas e transições principais contra evidências das referências,
   separadas dos assets/kit, e repetir prova pelo produto após prévia visual.

Uma cena escrita manualmente pode investigar o limite do renderer, mas deve ser
identificada como tal: não comprova geração automática. Ainda não medimos o teto
criativo da stack nem garantimos equivalência às referências. Não há evidência
nesta prova de que trocar Python/API por outro ambiente resolva esses gargalos.
Kits, acervo, skills, biblioteca, Temporal, versões e orçamento são preservados.
Nenhum novo render, API paga, mudança de runtime ou expansão de formato nesta
revisão; validação documental por `git diff --check`.

## Fontes já disponíveis para o próximo recorte

A [pesquisa de arte/componentes](../evals/pesquisa-elementos-motion-2026-11-09.md)
confirmou que os pacotes fornecidos já contêm geração de objetos recortados,
busca de takes, captura de páginas, componentes desenhados e catálogo com 70
cenas. Essa descoberta evita tratar toda a biblioteca como trabalho do zero.
São candidatos à adaptação, não capacidades já qualificadas no produto; o
titular confirmou liberação do Maestro para nosso uso. Nenhum pacote foi
executado, nenhum asset pago gerado e nenhuma cena promovida automaticamente.

## Sequência concreta de implementação proposta

1. **Contrato de movimento e uso de referências — implementado acima.** Evoluir `motion_creative.py`,
   o schema de composição e o payload em `motion_ai.py`. Registrar por cena/elemento
   início, duração, estados, trajetória/curva, relação com outros elementos e
   propósito. Vincular a identidade visual ao kit existente. Analisar sequências
   mais densas de poucos trechos para fundamentar parâmetros; a amostragem de 1 s
   desta análise não mediu curvas exatas. Planejamento pode integrar a mesma chamada
   de geração, sem etapa paga obrigatória separada.
2. **Execução consistente do movimento — implementado acima.** Acrescentar somente os recursos necessários
   ao renderer atual para interpolação/curvas, entradas escalonadas, máscaras e
   transições coordenadas, todos calculados por `seek(ms)`. A geração passa a usar
   esses recursos com parâmetros explícitos, preservando liberdade de composição.
   Conferir render real de transições e leitura, sem confundir determinismo com
   qualidade. Uma biblioteca extensa não é pré-requisito: a primeira prévia pode
   ser mostrada após esta fatia, com a revisão existente e avaliação humana.
3. **Crítica do movimento realizado — implementada com os limites acima.** Evoluir coleta de evidências, `MotionReview`
   e `motion_review.py`: sequências antes/durante/depois dos eventos relevantes,
   avaliação fundamentada de descontinuidades, sobreposição indevida, tempo de
   leitura e coordenação. Comparação de referência sobre movimento/acabamento,
   sem exigir paleta ou fonte da referência. Preservar incerteza quando a evidência
   não bastar. Correção localizada somente com problema demonstrado e orçamento.
4. **Prova integrada e decisão.** Gerar pelo worker do produto, mantendo kit,
   briefing e materiais de um caso existente; preservar baseline e apresentar
   resultado, tempo e custo. A prova final verifica a combinação das mudanças e
   depende da avaliação do titular. Uma peça escrita manualmente fora do fluxo não
   comprova a melhoria do produto. Regressões dirigidas e verificações proporcionais;
   nenhum gasto autorizado nesta definição.

A demonstração inicial não exige concluir todas as capacidades futuras de edição.
Transcrição, cortes, recorte de pessoa, imagens geradas, 60 fps e migração de motor
não são pré-requisitos desta primeira melhoria de motion. O planejamento por
cenas e os recursos devem servir a diferentes kits, sem estabelecer um template
único ou uma intensidade universal.

## Evidências novas

[Vídeos completos e sequências locais](../../.local/evals/shorts-motion-references-20261109/report.html)
· [manifesto com hashes e metadados](../../.local/evals/shorts-motion-references-20261109/manifest.json).

| Referência | Duração | Observação e aplicação |
| --- | ---: | --- |
| [mleEn-qt17A](https://www.youtube.com/shorts/mleEn-qt17A) | 57,594 s | Alterna pessoa, interfaces e demonstrações gráficas. Relacionar material visual à mensagem e compor a passagem entre eles. |
| [cavLvkX4jMw](https://www.youtube.com/shorts/cavLvkX4jMw) | 37,474 s | Apresenta vídeo como código e modificações por instrução. Parametrização ajuda a revisar; não prova acabamento por si só. |
| [Lt1jJmG3l_k](https://www.youtube.com/shorts/Lt1jJmG3l_k) | 62,614 s | Mostra conceitos/quadros ilustrados, seleção de direção e animação com estilos próprios. A preparação da arte faz parte do resultado. |
| [Xk9AuuD1GKo](https://www.youtube.com/shorts/Xk9AuuD1GKo) | 107,514 s | Explica direção detalhada, animação como função do tempo, render quadro a quadro, ajustes e recomposição vertical. |

Método: download integral; 266 quadros inspecionados, a cada segundo, cobrindo
os quatro vídeos. Legendas automáticas em português obtidas e lidas no quarto.
Não houve escuta integral, medição de curvas, prova de sincronismo ou reprodução
independente dos resultados alegados. Cópias de análise 360×640; não avaliar
nitidez final por elas. Não assumir como verificadas as alegações de preços,
licenças, velocidade, viralidade ou autoria. Nada enviado a IA paga ou incorporado
aos assets do produto.

## O processo do último vídeo e o produto atual

| Orientação apresentada | Situação concreta |
| --- | --- |
| Executar programas para produzir o arquivo | Já existe: worker Python/Temporal, navegador isolado e FFmpeg. |
| Descrever a cena com direção específica | Passos 1–2: contrato temporal e API numérica implementados; correspondência entre plano e execução ainda depende do gerador e da avaliação do render. |
| Calcular o quadro pelo tempo, sem relógio ou sorteio | Já exigido no adapter: `window.seek(ms)` determinístico e idempotente. |
| Renderizar quadro a quadro | Já existe no runner: chamada a `seek(index*1000/30)`, captura e montagem do MP4. O vídeo sugere 60 fps; o produto usa 30. |
| Refinar por instruções | Crítica/correção condicionais já existem. Ajustes criativos localizados e jornada completa de feedback do cliente ainda precisam ser qualificados/integrados. |
| Recompor para vertical | A saída atual já é vertical. Adaptação futura entre formatos deve recalcular composição, sem depender de corte central. |

Aumentar fps não substitui composição, curvas ou conteúdo gráfico. Não há evidência
nesta análise para tornar 60 fps requisito ou para migrar o executor para Remotion.
Os vídeos apresentam alternativas de ferramentas; não autorizam instalá-las ou
contratar integrações. A execução determinística existente deve ser preservada.

## Próximas fatias propostas

### Direção visual e cenas verificáveis

Estender o planejamento para registrar mensagem, hierarquia, materiais, elementos,
estados de entrada/leitura/saída e continuidade entre cenas. Para cada movimento,
explicitar duração, trajetória, aceleração/desaceleração e função. Antecipação,
amortecimento, sobreposição de movimentos, profundidade e transformação de formas
são recursos possíveis, não uma lista obrigatória para toda marca.

Preparar quadros-chave de aparência antes do render completo, usando o mesmo código
quando possível, para detectar composição fraca cedo. Não impor uma aprovação manual
nova a cada pedido do cliente nem uma chamada paga separada para todo planejamento.

### Recursos gráficos e execução

Criar recursos reutilizáveis de texto segmentado, máscaras, revelação de traços,
cards, diagramas e transformações, com tempos e curvas explícitos e render verificável.
Usar materiais próprios do negócio. Acrescentar ilustrações/imagens geradas somente
quando necessárias à direção, com orçamento e proveniência específicos. O exemplo
ilustrado exige avaliar essa preparação de materiais; sobrepor títulos não a substitui.

Identidades de cena/elemento devem permitir correção localizada, preservando os
materiais e as cenas aprovadas quando não forem afetados. Isso é evolução proposta,
não capacidade concluída de edição parcial.

### Crítica comparativa e prova

Fornecer evidências visuais selecionadas da referência tanto à geração quanto à
crítica, distinguindo inspiração de cópia. Avaliar o resultado renderizado: qualidade
da composição, realização das transformações, continuidade, leitura e adequação da
intensidade. Amostrar mais densamente os eventos relevantes, respeitando orçamento.
Amostras continuam sem certificar áudio ou toda a fluidez; preservar revisão humana.

Primeira prova: mesmos materiais/briefing de um caso existente, baseline preservado,
comparação visível, custo total e correção apenas se justificada. Aprovação dos checks
pelo modelo não basta: Café Pausa B permanece como exemplo de atendimento técnico
com acabamento humano insuficiente. Não expandir formatos sob alegação de qualidade
concluída antes de demonstrar ganho suficiente nesse recorte.

Para vídeo falado, integrar transcrição/alinhamento e depois edição que preserve
sentido e voz. Para peças sem fala, eventos podem seguir tempos do roteiro. Cortes,
recorte de pessoa, imagens adicionais e som entram quando a direção exigir; não são
pré-requisitos universais nem podem ser presumidos prontos por existir o renderer.

## Validação da análise original, anterior aos passos 1–3

Relatório e manifesto local gerados; metadados reais dos quatro arquivos conferidos;
legendas automáticas do quarto lidas; código do adapter/runner consultado para mapear
capacidades existentes. `git diff --check` aprovado. Sem mudança de runtime, migração,
CI, chamada paga ou novo orçamento. O trabalho é definição concreta da próxima
implementação, não demonstração de equivalência criativa já atingida.
