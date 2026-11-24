# Video-reel v1 — runtime de visibilidade por cena

## 24/11/2026 — runtime de visibilidade por cena, além da orientação

Implementado `motion-video-scene-visibility-v1`, com código/hash pinados no
snapshot de novas capturas vídeo. O executor aplica display:block no scrim da
cena ativa e display:none nos demais, antes e depois do seek do modelo. Assim,
o texto ativo é mensurável e o código gerado não deixa scrims de outras cenas
sobrepostos. O runtime resolve todos os text_element_ids e exige pais exclusivos;
DOM ausente/duplicado, pais compartilhados ou conteúdo extra falham com
MOTION_VIDEO_SCENE_SCOPE_INVALID. Não oculta nós desconhecidos nem modifica
beats, opacidade, fonte, posição, vídeo, logo ou o plano.

Storyboard e render usam o mesmo serviço de montagem: implementação → escopo
de cena → guarda vídeo v1 intacta. O hash do scene_init executado continua na
identidade durável do efeito. Contrato ausente preserva bytes de execução antigos;
previous não ganha o runtime retroativamente. Photo não recebe esse contrato.
Skill v19 e repertório v2 permanecem pinados sem mudança de bytes. Não é mais
uma tentativa de resolver esta falha apenas por prompt.

Validação: 451 testes Python, 291 Node e oito integrações em PostgreSQL `_test`
com roles restritas/fornecedores simulados. 100% linhas/branches nos seis módulos
Python medidos (551 statements/238 branches), incluindo o novo serviço; 100%
linhas/branches/funções no novo JS e nos quatro módulos Node do renderer. O
Makefile inclui o runtime novo na cobertura, sem exclusões. Chromium reproduz
o problema em duas cenas, cobre 337 instantes e seeks reversos/fronteiras,
e mantém rejeições de BR, grafismo desconhecido e pai não exclusivo. Prova local
adicional com o código capturado do run `3e690872…`, mídia sintética e runtime
pinado: 345 seeks passaram, sem MP4. Isso não é aceite audiovisual.

Ruff/formato do recorte passaram. Mypy aponta somente a chamada preexistente sem
tipo a feedback_context em motion_context; CI integral/cobertura global seguem
pendentes. make ci continua bloqueado nos 66 lints preexistentes.
Imagem local derivada do digest anterior foi construída copiando só runner.cjs,
sem credenciais, conteúdo do cliente, novas dependências ou download de base.
Hash interno e código específico de scope foram verificados em contêiner sem
rede. Aplicada no lab após verificar zero runs queued/running: pin local atualizado
para sha256:b4d0352f0403cfe5f1d2e4e387136f78afadf137a7e1dac19f8cfa92c498344b;
worker dedicado reiniciado (PID 68650), com pollers workflow/activity confirmados.
Imagem anterior preservada; nenhum run submetido ou repetido.
Sem chamada paga, reenvio do run, alteração de snapshots ou Fatia B/VR4–VR6.

## Evidência

Run `3e690872-259f-52f2-ad0d-4f630d812de7` capturou v19/v2, mas deixou três
scrims no documento: dois da cena1 e um da cena2. Os textos estavam transparentes
fora de sua cena, mas seus pais ainda eram considerados presentes pela guarda,
e interferiam em elementFromPoint. A reprodução local recusou 0ms por
UNPLANNED_OVERLAY e 33ms por READABLE_ACTION_OVERLAY_REQUIRED. Ocultar apenas
os pais de textos inativos em memória fez os 337 instantes passarem. O runtime
implementa esse controle de forma versionada e verifica propriedade exclusiva
dos pais antes de ocultá-los; não é um sanitizador arbitrário de HTML.

## Contrato e compatibilidade

`video_scene_visibility_contract` entra apenas em novas capturas com contrato
vídeo. O descriptor inclui regras e hash; bytes alterados ou descriptor sem
video_reel_contract correto interrompem montagem. O runtime é instalado após
o scene_init do modelo e antes da guarda. Precisa de todos os nós de texto no
DOM, cada um em seu pai exclusivo; não cria, reparenta ou remove nós. O display
do pai é propriedade explícita do runtime; o modelo mantém o resto do layout.
No limite compartilhado de cenas, ativa a cena seguinte; em duration_ms, mantém
a última cena. Resolve propriedade antes/depois do await; um erro do modelo
continua propagando. Conteúdo não declarado permanece visível para a guarda.

O novo código de erro foi acrescentado às whitelists do runner e do adapter.
Não altera as regras photo nem o guard vídeo. O runtime também não oculta logos
ou vídeos inativos; a implementação ainda deve cumprir um VIDEO por seek e logo
correto conforme o contrato já existente. Sem promoção de snapshots anteriores.

## Imagem e aplicação local

- Imagem anterior preservada: `sha256:33f0703c51d90bf69f30c359e8eb71fa68a98b10b568265966c3c8d5025c080a`.
- Nova imagem: `sha256:b4d0352f0403cfe5f1d2e4e387136f78afadf137a7e1dac19f8cfa92c498344b`.
- Runner SHA-256: `c6f981c8f51220182603746a8440dc6a4f396b278808d64f8ae42bfd7b74b3bc`.
- Runtime SHA-256: `81549f12024416a65410dc86bbadd7d43ba477ff2b158c3e29c664088add95f4`.

A imagem é derivada localmente da anterior, com somente o runner atualizado.
O runtime de cena é anexado pelo serviço ao bundle; não requer dependência nova
na imagem. O smoke leu o hash interno e verificou failureCode para o novo código.
Aplicação concluída em 24/11/2026: zero runs queued/running antes da troca,
.env local com novo digest e worker dedicado PID 68650 confirmado nas duas filas.
Nenhum workflow de geração foi submetido. Snapshots existentes permanecem intactos.
