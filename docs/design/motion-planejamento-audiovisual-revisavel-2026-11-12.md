# Preparação audiovisual revisável a partir da mensagem do cliente

> **Escopo histórico — esclarecido em 13/11/2026.** Estados, versões selecionadas,
> orçamentos e ordens de parada abaixo descrevem a entrega desta data; não são
> automaticamente instruções para uma rodada nova. Contratos capturados continuam
> preservados. Consulte a [orientação vigente](motion-orientacao-vigente-2026-11-13.md)
> para diferenças entre geração nova/evolução, estado operacional e próximo roteiro.

**Correção posterior do titular:** peças dos ensaios devem apoiar a avaliação do
produto, sem entrar como referência obrigatória para criar outra peça. O piso
independente e a preparação v5 substituem o uso da base descrito nesta entrega:
[decisão e implementação](motion-piso-qualidade-independente-2026-11-12.md).
V4 e os registros abaixo permanecem históricos; não submeter esse pacote.

12/11/2026. Continuação do contrato de qualidade e das fases 1–3. HEAD inicial
`096b95e`, working tree limpo; os commits posteriores a `30c6575` foram conferidos.
Entrega técnica e pacote privado de preparação. **Nenhuma chamada paga, plano ou
código novo de modelo, render de peça, migração ou aprovação artística.**

## Fronteira corrigida

`MotionRequest.propose_direction=true` permite o percurso acompanhado sem
`scene_direction` fornecida. Exige preparação, checkpoints e storyboard habilitado
como portão futuro. `instruction` deve coincidir com a mensagem preservada. Decisões
operacionais ficam separadas, com origem explícita; não são fala técnica do cliente.
O schema rejeita mistura com direção, eventos sonoros ou ducking pré-fixados.

O novo contrato `proposed-audiovisual-output-v1`, com criativo `reel-creative-v8` e
preparação v2, solicita **interpretação da mensagem e proposta de direção no plano**.
Não se afirma que essa interpretação já ocorreu: o pacote não foi enviado. Esse
percurso passa pela API/serviços de motion; não implementa a conversa WhatsApp nem
um novo chat. Preservar a mensagem deixou de ser a única mudança na entrada:
o modelo recebe schema próprio com direção proposta, plano temporal e decisões
sonoras/funcionais, antes de qualquer código.

`MotionContext.capture` recupera negócio autenticado, kit confirmado, fatos
vigentes, referências do negócio e materiais elegíveis. Sem seleção explícita de
fotos no modo proposto, disponibiliza até quatro fotos prontas/ativas/autorizadas,
ordenadas por ID, com RLS e escopo de negócio. É uma janela determinística de
candidatos, não busca semântica de todo o acervo. Leitura dos bytes e decodificação
ocorrem depois de sair da transação. A fonte e a voz permanecem nos controles
existentes; isso não depende de o cliente escrever instruções técnicas.

O retorno completo fica no checkpoint `plan`. Após aprovação do conteúdo/hash
exatos, o código deve preservar integralmente direção, plano, áudio, ilustrações
e `audiovisual`. O servidor reinjeta esses campos, exige o hash do plano e compara
o resultado. Materiais continuam resolvidos antes da implementação; inviabilidade
exige `requires_plan_revision`, sem código/replanejamento automático.
O checkpoint seguinte continua `awaiting_render`, anterior ao storyboard.

As reservas de capacidade nas funções de construção agora consideram apenas a
próxima chamada nos pedidos com checkpoints. A implementação inclui eventual
reserva de imagem habilitada. Isso não configura tarifa, não autoriza gasto,
não cria saldo e não altera os gates gerais de admissão. Pedidos sem checkpoints
mantêm a exigência anterior de três/duas reservas para a sequência automática.

## Piso funcional sem congelar a composição

`motion-evolution-v1` continua legível e vinculante como antes. A nova seleção v2
usa funções, IDs da base e instantes de evidência, sem IDs-alvo impostos. Cenas,
objetos, molduras, textos, cenário e transições podem mudar. A aquisição da base
continua exigindo versão real, mesmo negócio/fonte, hash, kit e bytes coerentes.
Não se promoveu a prévia de avaliação a versão normal ou aprovada.

O plano declara, para cada função, alvos próprios, preservação da função ou troca
de representação, justificativa, verificação e limitações. Falta de cobertura,
alvo inexistente, base adulterada ou instante de evidência ausente são rejeitados.
Os vínculos comprovam rastreabilidade da intenção, não equivalência artística.
A revisão humana precisa julgar justificativas e comparar o resultado depois.

No caso preparado há seis funções: integração da gravação, ação sensorial,
coerência espacial, continuidade da atenção, leitura/ritmo e identidade/convite.
Elas agrupam capacidades da base; não impõem seus 18 elementos ou três cenas.
A quantidade de funções/elementos não é uma métrica de ganho.

## Som disponível ao planejamento e ao executor

`public-cc0-v1` contém dois arquivos reais locais, obtidos com a autorização desta
rodada: previews MP3 HQ de [Maajora](https://freesound.org/people/Maajora/sounds/432775/)
e [TheHiraHira](https://freesound.org/people/TheHiraHira/sounds/460242/). As páginas
declaram CC0 e permitem uso comercial; a [CC0](https://creativecommons.org/publicdomain/zero/1.0/)
e a [FAQ](https://freesound.org/help/faq/) foram conferidas. São derivados públicos
do provedor, não os originais oferecidos por login. Autores, URLs de origem/download,
licença/data/evidência, formato, bytes/hash, duração medida, canais e limitações
estão no manifesto fixado por hash. [Proveniência e limites](../../app/assets/motion_sounds/README.md).

A obtenção pública foi feita pelo operador nesta implementação, e os arquivos
passaram a integrar o catálogo versionado do produto. O runtime não pesquisa nem
baixa som da internet. O modelo recebe metadados, não escuta os arquivos; pode
selecionar candidatos e trechos ou explicar a omissão de cada um.

Todo evento exige cena, elemento, intervalo de ação não estática, propósito,
hash do candidato, trecho, posição, volume e fades. Tempo incompatível, som não
contabilizado, identidade duplicada ou bytes alterados falham antes de executar.
O servidor compila a seleção para `motion-audio-v2`; preserva a faixa original,
sem mudar ordem, trecho, posição, ganho ou aplicar fade/compressão a ela.
A retomada dos checkpoints e do storyboard recupera a mesma mixagem.

Não foi fabricada a declaração `not_duplicate_of_source` usada na seleção manual
legada. Adequação, duplicação com o áudio original e inteligibilidade ficam
explicitamente pendentes em todos os eventos propostos. Não houve escuta da fonte,
dos candidatos ou de uma mistura. Não criar cena para usar som disponível nem
aplicar um efeito por palavra. Ducking/mixer/medição existentes foram preservados;
não foi criada geração ElevenLabs, síntese sonora ou música nesta etapa.

## Referências e capacidades efetivas

`business-reel-v4` mantém os três exemplos adaptados e avisos de licença do v3,
com **zero prints selecionados**. Os oito arquivos rejeitados, versões e provas
históricas continuam intactos. Fonte, base comparativa e preview de material
continuam anexados. Nenhum print arbitrário foi acrescentado para substituí-los.
Pacote vazio de referências é válido; anexos inesperados/adulterados continuam
rejeitados. Uma seleção visual futura ainda precisa justificar necessidade da
cena, mecanismo observado, evidência, adaptação, limites e verificação. Quadro
apoia composição; movimento precisa de evidência temporal pertinente. Nesta
rodada não existe evidência temporal nova selecionada de referência externa.

| Recurso consultado | Integrado e executado pelo produto | Apenas instrução/exemplo enviado ou disponível na origem |
| --- | --- | --- |
| `meu-braco-direito-skills`, HEAD `3199f78` | Loader versionado das skills locais; Reel HTML usa `instagram-reel-v13` | Original Reel: 22 linhas, igual à v1 local. V13: 713 linhas, adaptação da plataforma; o repositório não executa um agente neste fluxo. |
| `meu-braco-direito-motion-sources`, HEAD `180ded2` | Seleções/adaptações locais versionadas nos estilos/repertórios | Snapshots e estilos de origem não são importados/executados integralmente. |
| `claude-video` instalada | Métodos selecionados adaptados nos contratos e exemplos locais | Galeria, perícia própria, GSAP/HyperFrames, síntese `trilha.py` e General MIDI permanecem na origem; o fluxo completo da skill não foi acionado. |
| Extratos Maestro | Biblioteca local de elementos e contratos de imagem já integrados, quando habilitados | `layered-evidence.js` chega como exemplo de código. Busca de b-roll/Pexels/Pixabay/Coverr e agentes completos não são executados. |
| Extratos Finalizador | Exemplo adaptado testado com as bibliotecas atuais | `route-action.js` é texto/código anexado; os 70 estilos, motor, QA e Resolve não foram incorporados em bloco. |
| Repertório v4 | Loader/pins e exemplos chegam ao builder | Os três exemplos precisam ser incluídos/adaptados pelo código gerado; não são funções instaladas automaticamente no executor. |
| Som | Arquivos CC0 locais verificados, seleção estruturada no plano e compilação/mixer existentes | ElevenLabs já documentado em Maestros (04:43–05:24); síntese já existe em exemplos de claude-video. Nenhuma dessas gerações foi integrada/acionada aqui. |

Consultados os dois repositórios, skill instalada e extratos referenciados no
[estudo de elementos](../evals/pesquisa-elementos-motion-2026-11-09.md) e na
[análise Maestros](../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md).
Nenhum arquivo desses repositórios de origem foi alterado. Copiar instrução não
é integrar capacidade, e presença no payload não comprova aplicação ou qualidade.

## Pacote real para revisão

Pasta privada: `.local/evals/motion-supervised-20261112/preparation-v4/`, com ZIP
adjacente, permissão restrita e manifesto verificado. V3 anterior permanece como
histórico de montagem; `draft-input` original continua superado e não deve ser enviado.

- Mensagem: “Faça um Reel com esse vídeo para divulgar minha cafeteria.”
- `request.json`, `snapshot.json` e `context.json`: pedido operacional, captura
  RLS atual e contexto entregue ao builder. Não houve admissão de pedido novo.
- `generation-request.json`: bytes da chamada proposta montados por
  `OpenAIMotionProvider.build_request`, com transporte offline que rejeita rede.
  Hash: `0b7fabcaad4748d53a9e911d026d0a4666511b42cd5bc72035c78017074e74cf`.
- `PROMPT-INTEGRAL.md`, schema e `input/order.json`: entrada legível e associação
  dos anexos. 15 quadros da fonte, 20 da base registrada, um preview, zero prints
  externos e dois sons locais disponíveis, ainda não selecionados no plano.
- Fonte/kit/voz preservados. Kit `cafe-pausas` v1; skill `instagram-reel-v13`;
  acervo elegível sem fotos neste negócio; fatos confirmados/referências do negócio
  vazios nesta captura. Há uma ilustração conceitual reutilizada disponível como opção.
- ASR histórico da mesma fonte/hash, explicitamente não revisado; sem nova
  transcrição/escuta. Preservação da voz não foi atribuída ao texto do cliente.
  Essa reutilização pertence à preparação offline. A admissão futura precisa
  conferir/configurar o ASR local existente; se produzir outros cues/contexto,
  reconstruir e revisar a entrada antes da chamada paga, sem declarar igualdade
  com este pacote por pressuposição.
- Base registrada: hash `187b611018d2b24c27edb99f07a4a21aecd5599e7333a64ad1b227147df0c451`.
  A última prévia favorável `e4bfabe68500189d6cd147f440f8ef4f2bccabd6e3001dff08cebf9e7e5d47f0`
  permanece evidência histórica não registrada; seu hash/status estão na preparação,
  sem fabricar versão/aprovação ou afirmar que seus pixels são a base enviada.
- Manifesto: `a1b6cf668027a436b3222a456c6f82cb10b7723dd15228299c3b4a4cd245d7da`.
  `status.json` aponta para esta preparação; `intake-v2.json` permanece intacto.
  Reconstrução pelo builder atual semanticamente igual, com anexos e ordem do
  schema preservados. A leitura de `context.json` ordena chaves: não se declara
  igualdade binária dessa reconstrução com o wire original preservado/hashado.
  Prova privada: `preparation-v4-verification.json`.

O comando novo `python -m scripts.evals.motion_supervised_prepare` lê a identidade,
pedido e ASR privados, exige o nome do banco existente, captura contexto/mídia e
exporta sem chamar modelo/renderer. `--model` é proposta explícita apenas para o
payload offline. O runtime encontrado está **disabled**, sem tarifas/reservas;
dev continua na revisão **0117**, `_test` na **0118**. Isso não habilita execução.

## Validação e limites operacionais

- Suíte motion/exportadores: **1.584 passaram, dois skipped**; verificação final
  dirigida: **47 passaram**, incluindo recusa de evidência funcional ausente.
  Grupos se sobrepõem, não devem ser somados.
- Integrações motion/checkpoints: **55 passaram**; uma falhou porque o endereço
  padrão `127.0.0.1:7233` estava indisponível. Repetida somente essa prova na
  instância de CI já ativa em `127.0.0.1:49805`: **passou**. Incluem fonte original
  preservada, descoberta RLS de materiais, plano/código duráveis, recusa de plano
  ou som adulterados e zero renderer nos checkpoints solicitados.
  As **quatro integrações novas** foram conferidas novamente com o contrato final
  e passaram; esse grupo é parte das 55, não um total adicional.
- Dois módulos novos de produção, schema audiovisual e biblioteca sonora:
  **100% de linhas e branches** (121 statements/36 branches). Isso não é a
  cobertura integral exigida pelo projeto nem prova artística.
- Ruff lint global e Mypy em **332 módulos** aprovados. `make ci`, com cache local
  autorizado, parou na formatação preexistente de **14 arquivos**; não se incluiu
  reformatação em massa. CI/cobertura integral continuam pendentes, sem exclusão
  de módulos de produção. `git diff --check` e verificação do pacote aprovados.
- Somente o banco `_test` existente e logins restritos nas integrações; fixtures
  dedicadas. Sem testes de migração, banco novo, migração reaplicada ou alteração
  em dev. Consulta de negócio da preparação foi apenas de leitura com RLS.
- Cinco contêineres indicados permanecem `exited`; nenhum foi iniciado. Nenhum
  serviço/tabela/dependência nova. Temporal existente mantém execução e identidades.

## Próximo gate

Revisar esta entrada e definir orçamento novo. Antes de admitir uma execução,
configurar explicitamente modelo/tarifas/budgets e resolver a revisão de banco com
a autorização correspondente; não usar teto antigo nem migrar implicitamente.
Não submeter o rascunho original ou uma versão histórica desta preparação.

Só depois gerar o plano, parar em `awaiting_plan` e revisar por cena: fala/cues,
gravação e gesto protegido, objeto, fundo/apoio/luz, texto exato, passagem e som,
com tempos, função, materiais, justificativas e limites. O esquema permite
outra composição; a revisão precisa avaliar se ela mantém ou evolui as funções.
Após aprovação específica desse plano/hash, gerar o código e conferir fidelidade
nos campos preservados e no que o código declara executar. **Parar em
`awaiting_render`; não aprovar nem capturar storyboard.** Qualidade visual,
movimento contínuo e som exigirão prévia/escuta posteriormente autorizadas.
