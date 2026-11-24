# Video-reel v1 — Fatia A (VR1–VR3)

## 23/11/2026 — reforço de orientação VR3, sem alteração do gate

Novas capturas usam `instagram-reel-video-v15` e, no staging padrão, o
`business-video-reel-v2` (revisão do v1). Pins de skill, manifesto e conteúdo
foram adicionados; v14/v1 permanecem carregáveis para replay. Repertório
explicitamente selecionado continua respeitado. As regras transmitidas exigem
que cada texto cubra a cena: primeiro beat enter em scene.start_ms, último
exit em scene.end_ms, continuidade, nenhum hold opacity=0 e invisibilidade
somente via enter/exit. CTA final com hold estável visível ≥1500ms entre ambos.
Exemplo canônico pinado no repertório é validado pelo gate existente.

`VIDEO_REEL_CONTRACT`, validate_video_reel e DOM guard permanecem intactos;
não há mudança nos bytes/replay photo polish v1–v6. Testes sintéticos reproduzem
a topologia de pausa/tempo/cta do run `853327f8…`, isolada e conjuntamente,
sem usar conteúdo do cliente nem alegar seus tempos intermediários exatos.
Validação: 118 unitários aprovados; 100% de linhas e branches nos serviços
motion_skills, motion_repertoire e motion_video_reel (174 statements/78 branches),
sem exclusões novas. Três integrações aprovadas em PostgreSQL dedicado `_test`,
roles restritas e fornecedores simulados. Ruff/formato do recorte e mypy desses
três serviços passaram (cache temporário limpo). Os 175 assets existentes,
contrato, validador e DOM guard foram comparados com o índice inicial: bytes
intactos. A suíte adicional contexto/photo teve 52 aprovados e 18 falhas;
as mesmas 18 falhas foram reproduzidas em checkout isolado do índice anterior.
`make ci` executado, bloqueado nos 66 lints preexistentes. CI integral e
cobertura global 100% continuam pendentes; não houve correções fora do escopo.

Sem VR4–VR6/Fatia B, chamada paga, captura, reload, MP4 ou aceite E2E.
Próximo passo depende de autorização para nova captura e revisão do titular.

O diagnóstico e os pins abaixo documentam o estado anterior ao reforço.

Data: 23/11/2026. Implementação autorizada após rejeição de `versao-1 (13).mp4`
(`04973908e995f43a5842df2cecdedfde43b10e6542eb4d16091a057898e8974e`).
Não é aceite audiovisual. Run `0a24112c…` e entrada `dd3f0265…` não foram alterados.

## Contratos e escopo

Novas capturas HTML de vídeo recebem `motion-video-reel-v1` e a skill
`instagram-reel-video-v14`; o repertório padrão do planejamento staged passa a
`business-video-reel-v1`. Os três são versionados; skill, manifesto, conteúdo do
repertório e guarda `motion_video/video-reel-v1.js` têm hashes fixos. Repertórios
selecionados explicitamente continuam identificados, mas não dispensam VR1–VR3.
Recaptura conserva contrato/skill/repertório capturados; snapshots sem contrato
novo não ganham suas regras. Plano compacto e plano completo transportam
`video_layout`; o schema do provedor omite esse campo e sua definição nos
contratos históricos e photo. Dumps históricos sem campo continuam idênticos.
Nenhum arquivo/pin de polish photo v1–v6 foi editado. Comparação confirmou
140 arquivos históricos de skills/repertórios/photo idênticos byte a byte com HEAD.

O briefing continua soft: pausa aconchegante, frases curtas, cores/identidade do
kit e convite sem urgência, oferta ou hard-sell inventados. As referências das
41 peças e Maestros orientam acabamento, sem anexar conteúdo de terceiros.

## Gates

- **VR1:** cada cena vincula seu `video_element_id` a `assets/source.mp4` em
  `video_layout.mode=cover`. DOM exige um único VIDEO carregado, fonte correta,
  object-fit cover e cobertura 9:16 do primeiro ao último seek. Confere geometria,
  opacidade e ancestrais, clipping/máscaras, blur, cantos recortados e transforms
  que distorcem ou revelam bordas. Cartaz, janela e letterbox são recusados.
- **VR2:** `brand_element_id` aponta IMG `assets/logo.png` do inventário autorizado;
  ausência de logo exige material, sem fallback para label/identidade inventada.
  Overlay visível, dentro do quadro, no máximo 25% da largura e 12% da altura.
  Verificação de empilhamento recusa logo atrás da gravação. Textos e painéis não
  declarados são recusados; nome fixo como hero não substitui o kit.
- **VR3:** todos os textos da cena são vinculados à gravação, com enter/transform/
  exit e continuidade de estados. V1 usa estados JSON `{x,y,opacity}` e curvas
  lineares; transform desloca ao menos 4px. DOM confronta a interpolação real em
  cada seek, inclusive reverso; não basta descrever movimento ou executar endpoints.
  CTA final precisa de hold estável/visível ≥1500ms, além de entrada e saída.

O perfil inicial de legibilidade exige fonte ≥28px em 720px, texto claro e scrim
preto local (.75–.8), sem blur/sombra. Texto entre 12–78% da altura, margens laterais
4%, scrim <90% da largura/<25% da altura e padding ≤16px; área agregada ≤35% do
quadro. Esses limites são decisões conservadoras da v1, não garantia de qualidade
perceptual. Evitam rodapé de slide e placas dominantes. Fonte/copy e composição
continuam condicionadas ao material e kit; se inviáveis, revisar o plano/material,
sem afrouxar silenciosamente os gates.

A guarda não corrige o código nem altera mídia/áudio. Storyboard e render aplicam
a mesma guarda pinada e registram hash do `scene_init` executado na identidade do
efeito existente. Erros interrompem antes de aceitar/uploadar o resultado. O plano
é validado antes da implementação, e novamente antes do renderer. Não há novos
workflows, efeitos de rede ou operações sem identidade durável.

## Validação e limites

34 testes do contrato: 100% de linhas e branches no serviço novo (65 statements,
34 branches), sem exclusões. O recorte com storyboard soma 73 testes aprovados.
A suíte unitária motion terminou com 1725 aprovados e 20 falhas preexistentes
confirmadas abaixo. Prova Chromium usa WebM sintético em memória, rede
interceptada e logo sintético; 91 instantes de frame e seeks reversos/fronteiras,
mais rejeições adversariais de layout/legibilidade/execução. Não cria MP4.
284 testes Node existentes passaram. Três integrações em PostgreSQL dedicado
`_test`, com roles restritas e fornecedores/renderer simulados, provaram captura
imutável/idempotente, auditoria/outbox, admissão antes do render e guarda no bundle.
Ruff do recorte e mypy do serviço novo passaram.

`make ci` foi executado: bloqueado nos 66 lints preexistentes. Mypy de context/AI
continua com os quatro erros preexistentes documentados. Comparação com checkout
HEAD isolado confirmou as 20 falhas existentes de fixtures de contexto/áudio;
não foram mascaradas com exclusões. CI integral e cobertura global 100% pendentes.

## Fora da fatia e próximo gate

Temporal, HTML/Chromium/FFmpeg, uma gravação por pedido e tetos 60s/50MiB mantidos.
Não implementar VR4 (EDL), VR5 (motion de crop/transições) ou VR6 (música/mix).
Sem TTS/avatar/Remotion, chamada paga, captura do cliente, reload de worker,
reenvio do run, publicação ou reabertura do photo-reel Café congelado.

Captura com worker antigo (`versao-1 (14)`) não valida a Fatia A. Run `853327f8…`
com contrato ativo falhou em tipografia cinética (holds fantasmas) — ver
[kinetic-text-gate](motion-video-reel-v1-kinetic-text-gate-2026-11-23.md) antes de
nova captura. Após o reforço de skill/repertório, o titular autoriza **uma captura**
e revisa VR1–VR3 no MP4. Música/EDL/transições ficam fora. Fatia B só com novo pedido.
