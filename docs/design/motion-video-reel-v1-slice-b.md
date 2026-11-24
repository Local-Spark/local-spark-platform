# Video-reel v1 — Fatia B (VR4–VR5; VR6 se biblioteca permitir)

## 24/11/2026 — correção do padding final da EDL (v2)

Run `e5cbf795-c5a7-5506-a275-e184fa7470d3` falhou com
`MOTION_VIDEO_EDL_INVALID`: saída 11200ms, fonte medida 11176ms; cena final
6780–11200ms com in/out 6780–11176ms. A diferença de 24ms é arredondamento
para frame de saída, não corte de fala. O runtime já limitava o seek ao fim
real da fonte, mas o gate do plano v1 exigia durações exatamente iguais.

Novas capturas usam `motion-video-edit-v2`, `instagram-reel-video-v21` e
`business-video-reel-v4`. Somente a última cena pode terminar 1–34ms antes
na fonte, com source_out_ms exatamente igual a source.duration_ms medido pelo
servidor. Sem tolerância em cenas internas, fonte sem duração, fim inventado,
speed ramp ou alteração do áudio. V1/v20/v3 e guarda JS mantêm bytes/pins;
replay v1 continua com o gate original. VR1–VR3, scrim, texto puro, visibilidade
e photo polish permanecem intactos. VR6 continua indisponível.

Validação sintética: 154 testes, 100% linhas/branches nos cinco serviços
medidos (277 statements/122 branches), sem exclusões. Casos de 1/24/34ms,
fonte silenciosa/com áudio, replay v1 e rejeições de cortes internos/fins
não verificados/35ms cobertos. Ruff e mypy do recorte passaram. Mais 32 testes
de wiring/staging e 12
integrações em PostgreSQL dedicado `_test` passaram, com roles restritas e
fornecedores simulados. `make ci` segue nos 66 lints preexistentes. Todos os
193 assets presentes no índice antes desta correção continuam byte a byte iguais.
Revalidação somente em memória do plano capturado: v1 rejeita, v2 passa os
gates de vídeo A+B; isso não é aceite audiovisual.
Run e snapshots do cliente não foram alterados; sem chamada paga, reenvio,
render ou novo MP4. Aceite audiovisual permanece pendente. Worker local
reiniciado com zero runs
ativos: PID 97278 → 3169, carregando v2/v21/v4. Imagem do renderer mantida,
pois a guarda JS não mudou. Pollers workflow/activity do PID 3169 confirmados.
Nenhum snapshot antigo foi promovido.

### Pins da correção

| Artefato | SHA-256 |
| --- | --- |
| `instagram-reel-video-v21` | `db94aa9c5815be52208b08fe4145643e1d0a8c33b8bde193afe168c266e2fd43` |
| `business-video-reel-v4 manifest` | `90e590529195128ba77dcdfeea03354d67dbd1928ac341b7933d0a53974be7cb` |
| `business-video-reel-v4 capture` | `8996cd7126f88ed42e79ad3dd7ea4795a3269baaca3d2ec3c282f27ac0d8a6a8` |

## 24/11/2026 — Fatia B: EDL e crop declarados, VR6 indisponível

Implementada extensão pinada `motion-video-edit-v1`, skill
`instagram-reel-video-v20` e repertório `business-video-reel-v3` para novas
capturas. O contrato/guarda VR1–VR3 e scene-visibility-v1 permanecem intactos;
replay sem extensão B não recebe EDL nem regras novas. Photo-reel Café e bytes
polish photo v1–v6 continuam congelados.

B exige pelo menos duas cenas contíguas com funções editoriais distintas,
in/out explícitos na fonte, intenção de crop e corte perceptível entre cenas.
Cada segmento tem pan/scale linear declarado; play-through com só troca de
texto falha. A guarda confere tempo real da fonte e matriz de crop em todo seek,
inclusive reverso, além da guarda A de cover, logo, texto puro e scrim estável.
Não libera grafismos ou assets extras. Storyboard e render compartilham a
mesma montagem; hash do código executado permanece na identidade durável.

Escopo conservador de fala: com áudio original, EDL usa intervalos contíguos
da fonte e cortes de reenquadramento; não elimina palavras nem remixa a faixa.
Sem áudio, permite remonte temporal. Duração final igual à original nesta
versão. Trims/remonte temporal com fala e duração reduzida são trabalho futuro,
não promessa desta entrega. VR6 tem estado capturado
`unavailable / edl_music_mix_not_qualified`: sem música/SFX novos ou provedor.
O mixer existente preserva uma única faixa original e não foi estendido nesta
fatia; biblioteca existente não equivale a mix qualificado para EDL.

Validação: 591 testes aprovados e duas falhas de áudio preexistentes,
reproduzidas em checkout isolado de HEAD; 100% linhas/branches nos oito módulos
Python medidos (696 statements/302 branches), sem exclusões novas. 295 testes
Node aprovados, 100% linhas/branches/funções nos seis módulos medidos. Dez
integrações em PostgreSQL dedicado `_test`, roles restritas e fornecedores
simulados passaram. Três provas Chromium sintéticas passaram (B, A e
scene-visibility), sem MP4. Ruff/formato do recorte e mypy de sete módulos
passaram. `make ci` continua bloqueado nos mesmos 66 lints preexistentes;
CI integral/cobertura global permanecem pendentes.

Pins e limites detalhados abaixo.
Sem chamada paga, captura do cliente, deploy/reload ou novo MP4. Não há aceite
E2E: depende de execução posteriormente autorizada e revisão do titular.

### Decisões de implementação

- Geração automática usa `proposed-video-output-v2`, removendo a proibição
  histórica de EDL; v1 continua disponível para replay. O clamp da fonte aceita
  no máximo 34ms de padding final, pois a preparação arredonda ao frame de saída.
- Campo opcional `video_layout.edit` em plano completo/compacto, omitido nos
  dumps históricos. Schema do provedor só inclui `VideoEdit/VideoCrop` com B;
  A/photo continuam com o schema anterior.
- `source_in_ms/source_out_ms`, `purpose` (hook/detail/invitation), `intent`,
  `transition=cut`, `crop_from/crop_to={scale,x,y}`. Escala 1–1,35; x/y em fração
  do canvas, limitados por `(scale-1)/2` para não revelar bordas. Interpolação
  linear; cada segmento varia escala ≥0,03 ou translação ≥0,02. Cada corte
  muda escala ≥0,06 ou translação ≥0,04. Esses limites são decisões versionadas,
  não certificação perceptual ou semântica da intenção descrita.
- Um único VIDEO com ID da cena ativa, dimensões do canvas, origem central,
  object-fit cover. Helper do repertório executa crop e aguarda seeked; guarda
  confere, sem reparar o código. Erro seguro `MOTION_VIDEO_EDIT_NOT_EXECUTED`
  atravessa runner/adapter sem stack ou conteúdo do cliente.
- Com áudio, apenas cortes de reenquadramento: in/out iguais ao intervalo da
  cena. Sem áudio, in/out podem mudar de posição dentro da duração original.
  Isso preserva fala sem supor alinhamento de palavras a partir de frames.
  Reenquadramento precisa respeitar região essencial; gate não entende rostos,
  mãos ou produto e não substitui revisão visual.
- Cortes secos são a transição qualificada; dissolves/grafismos/acervo extra
  continuam fora desta implementação mínima. A escolha atende VR5 por crop
  intencional e corte, sem abrir a permissão de overlays da guarda A.
- VR6 explicitamente indisponível. Não foi feita seleção/download/compra de
  trilha, geração musical, TTS, avatar ou troca de renderer. Mix com biblioteca
  e duck sob fala fica pendente de qualificação separada.

### Pins novos

| Artefato | SHA-256 |
| --- | --- |
| `edit-v1.js` | `a6d462ce99d33c3279e92b8e041bbc39d6c11bc645d700a1b7ae19ed4fa006af` |
| `instagram-reel-video-v20` | `cb90bb39cdf8bee28d4ebc1d71a5d91ef11011c9476f8a08e24464b8af08fb1b` |
| `business-video-reel-v3 manifest` | `59a8e97dd2f1b1c87aeee2f2e0ab8bf728eb95a17bd23522f690801558f063b6` |
| `business-video-reel-v3 capture` | `71090518340ac61222c40c2b1f4a0f5a8721304e95e7f43e90d5f9ce893be057` |

### Validação desta implementação

Após fechar os pins, 141 testes focalizados passaram com 100% linhas/branches
nos cinco serviços medidos (269 statements/120 branches). A última revisão
da geometria passou nos quatro testes Node da guarda (100% linhas/branches/
funções) e na prova Chromium com pai deslocado, mantendo os gates A ativos.

Recorte Python: serviços `motion_video_edit`, `motion_video_reel`,
`motion_video_scene_visibility`, `motion_video_requests`, `motion_skills`,
`motion_repertoire`, `motion_generation` e adapter `motion_html_renderer`.
A execução ampliada inclui duas falhas de testes de áudio preexistentes; não
foram excluídas nem mascaradas para obter cobertura. Os 18 testes de contexto
que falham por mocks de `feedback_context` também foram reproduzidos em HEAD.
Mypy do adapter AI encontra os mesmos três erros de HEAD em streaming; mypy
dos sete módulos focalizados passou. Não se afirma CI global verde.

Chromium executou 181 posições da EDL/crop, mais fronteiras, seeks reversos,
remonte temporal silencioso e recusas por crop omitido, tempo errado, BR e
grafismo não planejado. A guarda adicional também confronta o retângulo real
com o crop declarado, para impedir deslocamentos ocultos em pais. Os testes
A e scene-visibility existentes passaram sequencialmente; em paralelo houve
timeouts, sem afrouxar os limites das guardas. Fontes são WebM sintéticos
indexados com HTTP Range, além de logo/textos sintéticos, sem conteúdo do cliente.

Replay A: o código final montado com scene-visibility e guarda A mantém SHA-256
`974bf6592d40af8b84e91c08f5cd8d5455306fb513596e018354c14fa5ce9f11`,
medido também no checkout isolado anterior. Novas capturas recebem B; não se
editou snapshot, run ou acervo do titular.
Snapshots A e photo não foram atualizados. Comparação dos 185 assets históricos
com HEAD: 184 intactos, incluindo todas as skills anteriores, repertórios,
guardas A/scene-visibility e polish photo; só runner.cjs mudou, para transportar
o novo código de erro. O deployment atual continua com o código anterior até
uma aplicação operacional separada. Não se declarou aceite audiovisual.

## 24/11/2026 — autorização após rejeição criativa do primeiro MP4 Fatia A

Titular rejeitou `versao-1 (15).mp4`
(`f446d636d8ad24388c00603478f34153698ed195dc0ad2aa81962cda008550e9`),
run `86990c48-457f-51e8-b3f8-dc9d078ac3c4`. Review automática `adequate`;
revisão humana: peça fraca. Gravação integral full-bleed + três textos com
scrim preto + logo; sem EDL, sem motion no vídeo, sem grafismos planejados,
sem uso de outros materiais do acervo, sem trilha/SFX. Skill v19 / repertório
v2 / scene-visibility-v1 / guarda Fatia A cumpridos — **gate ≠ qualidade**.

Ordem vigente desde
[gaps](motion-ensaio-cafe-aurora-video-reel-v1-gaps-2026-11-23.md): Fatia A
(VR1–VR3) → uma captura → Fatia B. Fatia A está **tecnicamente** no ar e não
deve ser desfeita. Fatia B é a fatia autorizada agora para subir a qualidade.

## Escopo autorizado

Preservar Temporal, HTML/Chromium/FFmpeg, uma gravação ≤60s/50MiB, briefing
soft (pausa aconchegante, sem hard-sell), photo-reel Café congelado, pins e
replay Fatia A (cover, logo kit, tipografia cinética, texto puro, scrim
estável, scene-visibility, diagnóstico do renderer).

| ID | Objetivo | Critério mínimo |
| --- | --- | --- |
| **VR4** | EDL / remonte com função | ≥2 segmentos com papel distinto (ex.: gancho → preparo/detalhe → convite). Cortes ou dissolves curtos entre segmentos; não um único play-through da fonte com textos trocados. Respeitar fala quando houver (não cortar no meio da palavra sem regra). |
| **VR5** | Motion e grafismo com intenção | Pelo menos um de: (a) pan/scale/crop intencional da gravação ainda em cover 9:16; (b) grafismos **declarados no plano** e permitidos por guarda versionada (linhas/formas mínimas alinhadas ao tom soft); (c) transição perceptível entre segmentos. Rejeitar plano em que só a mídia-fonte “se move sozinha” e a UI/texto fazem todo o trabalho. Materiais do inventário/acervo autorizado (fotos do kit/anexos) podem entrar como apoio se estiverem no pedido — não inventar assets. |
| **VR6** | Mix (condicional) | Reutilizar biblioteca já existente (`motion_music` / sound library / photo-music), com duck sob narração quando houver fala. Se não houver trilha elegível: estado explícito de indisponível — não inventar música nem compra nova sem autorização. SFX só da biblioteca licenciada, sobrios. Se a extensão de áudio bloquear a fatia visual, entregar VR4–VR5 primeiro e documentar VR6 pendente; não atrasar B só por áudio. |

## O que mudar (direção técnica)

1. **Contrato / skill / repertório versionados** para video-reel Fatia B (novos
   pins). Snapshots Fatia A e photo permanecem reproduzíveis; não editar bytes
   de polish photo v1–v6 nem afrouxar silenciosamente a guarda v1 antiga.
2. **Plano:** modelar segmentos EDL (in/out na fonte, função, transição) e
   motion permitido no elemento de vídeo/crop; grafismos só com role/ids
   declarados e regras DOM novas — não reabrir `UNPLANNED_OVERLAY` para lixo
   decorativo livre.
3. **Guarda DOM / validate:** versionar (ex. video-reel-v2 ou extensão pinada)
   para aceitar o que B autoriza e continuar recusando cartaz/janela, label
   morto, texto com filhos, scrim fade indevido, overlays não planejados.
   Scene-visibility continua para textos/scrims por cena/segmento ativo.
4. **Orientação:** skill + repertório devem exigir progressão editorial e
   motion; exemplos canônicos que passem nos novos gates. Prompt sozinho não
   basta — a Fatia A mostrou isso.
5. **Testes** sintéticos (sem mídia do cliente): anti-padrões do run
   `86990c48…` (play-through único + só texto) devem falhar no plano/DOM;
   casos mínimos VR4/VR5 devem passar. Cobertura 100% no recorte; integrações
   `_test`. Docs PROJECT/SDD/BL04/CHANGELOG/DECISIONS na mesma mudança.

## Fora desta fatia

- Desfazer ou afrouxar VR1–VR3 / scene-visibility / texto puro para “ficar bonito”.
- Remotion, TTS, avatar, HeyGen, Meta publish.
- Reabrir polish photo-reel Café.
- Compra/download de música nova ou chamada paga sem autorização do titular.
- Declarar aceite E2E sem novo MP4 autorizado e revisão humana.

## Aceite audiovisual (após implementação)

Uma captura autorizada: full-bleed preservado; logo kit; tipografia legível;
progressão editorial perceptível (cortes/segmentos); motion ou grafismo
planejado alinhado ao tom soft; áudio com trilha/duck ou motivo explícito de
indisponibilidade. Revisão do titular — gates sozinhos não fecham o aceite.

## Prompt para o chat de implementação

```
Leia AGENTS.md e o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md,
docs/design/motion-ensaio-cafe-aurora-video-reel-v1-gaps-2026-11-23.md,
docs/design/motion-video-reel-v1-slice-a.md e
docs/design/motion-video-reel-v1-slice-b.md
(refs: docs/evals/analise-41-referencias-motion-2026-11-12.md,
docs/evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md;
photo-reel congelado).

Contexto: Fatia A (VR1–VR3 + scene-visibility + v19) está ativa e gerou MP4.
Titular rejeitou versao-1 (15).mp4 hash
f446d636d8ad24388c00603478f34153698ed195dc0ad2aa81962cda008550e9
(run 86990c48…): gravação integral + textos/scrim, sem EDL/motion/grafismo/
acervo/trilha. Review automática adequate ≠ aceite humano. Gate A não deve
ser desfeito; o teto criativo atual é o problema.

Briefing soft a preservar: reel aconchegante de pausa a partir da gravação,
frases curtas, identidade do kit, sem hard-sell.

Implemente a Fatia B do video-reel: VR4 e VR5 obrigatórios; VR6 somente
reutilizando biblioteca de áudio já existente (duck sob fala) ou estado
explícito de indisponível — sem música inventada nem compra nova.
NÃO afrouxar VR1–VR3 / texto puro / scrim estável / scene-visibility.
NÃO editar bytes/replay do polish photo v1–v6.
NÃO Remotion/TTS/avatar. NÃO reabrir photo-reel Café.
NÃO chamada paga / captura do cliente sem eu autorizar depois.

1) VR4: EDL com ≥2 segmentos com função; cortes/dissolves curtos; anti-padrão
   play-through único da fonte só com troca de texto deve falhar no gate.
2) VR5: motion intencional no crop/cover (pan/scale) e/ou grafismos mínimos
   DECLARADOS no plano com guarda versionada; transição perceptível entre
   segmentos; materiais do inventário autorizado podem apoiar — sem inventar.
3) Versionar contrato/skill/repertório/guarda; pins novos; snapshots A intactos.
4) Testes sintéticos + 100% cobertura no recorte; PROJECT/SDD/BL04/CHANGELOG/
   DECISIONS + slice-b na mesma mudança.
5) Se VR6 bloquear, entregue VR4–VR5 e documente VR6 pendente.

Não declare aceite E2E sem novo MP4 autorizado e minha revisão.
Não rode chamada paga sem eu autorizar.
```
