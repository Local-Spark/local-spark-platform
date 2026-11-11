# Executor isolado de motion HTML

`runner.cjs` preserva o caminho criativo HTML + `scene_init` + áudio dos ensaios.
O JavaScript gerado executa apenas no Chromium. O módulo Node controla arquivos,
browser e FFmpeg; não importa código de `scripts/evals` e não recebe credenciais.
Fatos, direitos, briefing e qualidade criativa pertencem aos serviços de produção
e à revisão da peça. O executor não apresenta essa validação como concluída.

O adapter `app/adapters/motion_html_renderer.py` recebe `RenderBundle` imutável,
confere os hashes dos assets e cria um contêiner por identidade de operação.
Os IDs públicos são `assets/<nome>`; o plano de áudio usa esses mesmos IDs.
Uma faixa pode apontar para o MP4 original com áudio, sem passar pelo WAV mono
de 16 kHz usado pela transcrição. O mixer preserva offsets, trims e ganhos, sem
normalizar ou definir `-ar`/`-ac`; o mix final é codificado em AAC a 192 kbit/s,
portanto não promete identidade binária do áudio original.
O trim pode terminar depois do fim da fonte, preservando a semântica dos ensaios:
`atrim` encerra no EOF e `amix` acompanha a faixa mais longa, sem `apad` ou criação
de fala/silêncio. O diagnóstico registra a duração disponível, o trim solicitado
e as faixas que terminam antes dele; início no EOF ou posterior é inválido.

## Recursos de movimento versionados

`movement-v1.js` é código browser-only, entregue pelo worker como prefixo de
`scene.js` **somente** quando o snapshot inclui `movement_runtime`. O adapter
confere SHA-256 antes de empacotar; o limite de cena e seu hash incluem o prefixo.
O runner existente continua avaliando a cena exclusivamente no Chromium. Não há
novo pacote externo, CDN, permissão, relógio de animação ou processo de execução.

`window.MotionV1.timeline(tracks)` compila tracks `{id, initial, beats}` ligadas
por ID ao DOM. Cada beat `{start_ms,end_ms,to,curve}` herda o estado final anterior.
`timeline.seek(ms)` recalcula desde o estado inicial, permitindo salto, repetição
e retorno. `stagger(tracks,step_ms)` desloca beats por índice e não altera inputs.
`progress(ms,start_ms,end_ms,curve)` permite dirigir outros grafismos por tempo.
A API completa enviada ao modelo está em `app/services/motion_movement.py`.

Estados numéricos: `x/y` (px), `scaleX/scaleY`, `rotate` (graus), `opacity`,
`clipTop/clipRight/clipBottom/clipLeft` (%) e `radius` (px). O runtime controla
integralmente transform/opacity/clip-path/border-radius; use wrappers para layout
ou outros transforms. Segmente texto no HTML conforme a direção. Curvas nomeadas
são cúbicas; Bézier resolve o eixo do tempo; mola usa resposta analítica normalizada
na duração. Valores de opacidade/máscara são limitados, preservando overshoot
espacial. CSS animations/transitions não devem competir com o seek.

Não é um compilador do plano textual nem prova de qualidade. As cores/fontes,
conteúdo e relações narrativas continuam na direção do negócio. Uma biblioteca
publicada deve ser imutável; versões futuras exigem fonte/versionamento próprios.
Sem a capacidade no snapshot, cenas históricas conservam seus bytes originais.
O Dockerfile do worker já copia estes assets; nesta entrega não houve deploy.

## Limites e saída

- Imagem por digest/ID, aquisição automática desabilitada, UID/GID 65532,
  capabilities removidas, `no-new-privileges`, rede `none`, filesystem somente
  leitura e apenas o pacote de entrada montado, também somente leitura.
- Perfil seccomp explícito, IPC privado, limites de memória, CPU, processos,
  arquivos, tempo e tmpfs. O socket Docker não entra no contêiner.
- Browser com sandbox habilitada, CSP, bloqueio de WebSocket/WebRTC/Workers,
  assets por lista permitida e rejeição de erros ou pedidos externos.
  A origem interna fixa `https://motion-fixture.invalid` conserva URLs absolutas
  das composições qualificadas; isso não libera hosts externos nem altera HTML.
- HTML é servido como `text/html; charset=utf-8`, preservando os bytes e hashes
  recebidos. Isso evita corrupção de acentos quando a composição omite `<meta
  charset>`, sem depender de uma correção paga pelo modelo.
- stdout contém um cabeçalho JSON limitado seguido dos bytes exatos de MP4 e
  PNGs. Não há extração de tar nem diretório gravável do host montado na execução.
  O adapter confere tamanhos, hashes, geometria, tempos e vínculo ao input.
  `--log-driver=none` impede que o daemon persista esse protocolo binário como
  logs; o worker recebe a saída diretamente pelo attach.
- Evidências vêm da **decodificação do MP4 final**, com PTS conferidos via FFprobe.
  São 20 quadros uniformes por padrão, até 64 pedidos explícitos e 32 MiB agregados.
  Com `motion-temporal-v1`, o serviço envia até 20 tempos dirigidos a eventos
  (três janelas mais contexto), mantendo o teto por versão. O executor apenas
  extrai os quadros; cobertura, crítica e orçamento pertencem aos serviços.
  Pedidos de tempo são mapeados ao quadro imediatamente anterior; `ms` é o PTS
  arredondado, e `pts_seconds` conserva o valor de seis casas retornado pelo FFprobe.

O adapter remove somente o ID retornado por seu próprio `docker create`, mesmo em
falha ou cancelamento. Ele nunca remove por nome uma tentativa preexistente.
O serviço/Temporal mantém a identidade durável, estados e regras de retomada.

A qualificação real anterior usou worker Python no host. A configuração para
worker em contêiner foi implementada em `docker-compose.motion.yml` e no target
`motion-worker`, com CLI/socket explícitos e diretório temporário compartilhado
no mesmo caminho. O adapter aceita `scratch_directory`; somente a subpasta
`input` de cada tentativa é montada, em leitura, no renderer. O socket jamais
é montado no renderer. O ponto 3 executou build e verificação real dentro do
worker; a prova paga gerou duas versões e parou na persistência da crítica final.
A correção posterior de UTF-8 passou por uma checagem real mínima. Instruções no
[guia do worker](../../../docker/motion-worker/README.md).

## Perfil seccomp

Derivado do [perfil Playwright 1.64.1](https://github.com/microsoft/playwright/blob/v1.64.1/utils/docker/seccomp_profile.json),
com licença preservada em `LICENSE.playwright-seccomp`. Mantém a criação de user
namespaces necessária ao Chromium e permite `chroot` dentro da sandbox; o
namespace externo continua sem capabilities. `clone3` retorna ENOSYS para o
fallback de libc. `io_uring`, `ptrace` e `socketcall` são negados; `socket` limita
as famílias a UNIX/INET/INET6, bloqueando também ALG e VSOCK. Não há `SYS_ADMIN`,
modo privilegiado ou `--no-sandbox`.

A configuração do browser segue o princípio de usuário dedicado e filtro
seccomp descrito pelo [Playwright](https://playwright.dev/docs/docker). A política
explícita evita depender da configuração padrão do daemon, conforme o mecanismo
do [Docker](https://docs.docker.com/engine/security/seccomp/). O runner exige
`Seccomp=2` e procura evidência do filtro adicional aplicado ao processo Chromium.
Se não conseguir comprovar a sandbox, a execução falha.

## Imagem Linux

`docker/motion-renderer/Dockerfile` usa base Node 24.18.0/Bookworm ARM64 por digest;
`dependencies.lock.json` registra os arquivos adquiridos. O contexto de build
contém apenas dependências conferidas e estes arquivos do renderer. Os `.deb`
são verificados por SHA-256 e instalados sem rede; Playwright 1.64.1, browser
156.0.8078.4/revisão 1248 e FFmpeg/FFprobe 5.1.9 são fixados no pacote.

A aquisição e os logs de qualificação locais ficam em `.local/motion-linux-*`.
O build local não confirma arquitetura de deploy, distribuição de fontes de
terceiros ou backup independente. Esses limites continuam no registro de
dependências Linux; nenhum deploy foi realizado nesta fatia.

## Protocolo 2: quadros principais

Config `version=2` reutiliza HTML, scene_init, assets e sandbox, mas busca apenas
`sample_frames` e devolve PNGs com `evidence_source=browser_keyframes`, vídeo vazio
com SHA do conteúdo vazio e cabeçalho version 2. Não codifica MP4 nem inspeciona/mixa
áudio. Fonts e imagens são aguardadas após seek. Protocolo 1 continua devolvendo
MP4 e quadros decodificados do vídeo. O adaptador recusa respostas de outro protocolo.
Imagem do container precisa ser reconstruída e ter novo digest antes da ativação.


### Movimento v2 — 10/11/2026

Na rodada v2, novas capturas passaram a usar movement-v2.js, com API global MotionV1 compatível. Tracks sem
clipTop/Right/Bottom/Left explícitos não escrevem clip-path nem recortam filhos.
CSS existente é preservado. Uma máscara explicitamente declarada continua ativa,
inclusive inset(0). Renderer resolve bytes exatos por hash; movement-v1.js permanece
imutável para pedidos antigos. Regressões Node e dois quadros sintéticos no
Chromium conferem contêineres transladados e máscaras intencionais.


### Movimento v3 — tratamento da gravação

Novas capturas usam movement-v3.js. Uma track sem radius em initial/to preserva
o border-radius CSS da moldura; declaração explícita (inclusive zero) assume
o controle do raio e continua determinística em seeks repetidos/inversos.
O comportamento de clip-path da v2 permanece. V1/v2 são imutáveis e resolvidas
por hash; não migrar automaticamente peças antigas. Repertório testado nas três
versões. Runtime é enviado pelo adaptador; nenhum motor/serviço novo foi criado.
