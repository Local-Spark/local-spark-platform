# Snapshots de skills de motion

As três versões v1 abaixo reproduzem os bytes do working tree de
`../meu-braco-direito-skills/skills/` em 05/11/2026. O repositório próprio tinha
`main` no commit `5ff6306`, mas as três skills eram arquivos novos com mudanças
no índice e no working tree; o commit não identifica seu conteúdo. O hash de
cada arquivo abaixo identifica a versão efetivamente incorporada. Os IDs `v1`
são versões locais deste snapshot, não versões declaradas pela fonte.

| Formato | Fonte relativa ao repositório próprio | Snapshot | SHA-256 |
| --- | --- | --- | --- |
| Reel | `skills/instagram-reel/SKILL.md` | `instagram-reel-v1.md` | `4ed6a1307437b492cf423612855645752fda331e206920abfcf155c198271ec7` |
| Story em vídeo | `skills/instagram-story-video/SKILL.md` | `instagram-story-video-v1.md` | `083981e2de27c68588878aaba430a92a68b9ee9eefc8ac74446d8484c39b5713` |
| Carrossel com motion | `skills/instagram-carrossel-motion/SKILL.md` | `instagram-carrossel-motion-v1.md` | `b91757da20a4a415fe4116a15aec84b90e27c98c99182fa29cb195cfed4af0de` |

São instruções de direção, não renderizadores nem prova de integração ou
qualidade. O loader só aceita os IDs, formatos e hashes registrados e não
habilita a execução no produto. Mudanças futuras exigem nova versão e hash;
não alterar silenciosamente snapshots referenciados por uma operação.

## Adaptação para o executor HTML

`instagram-reel-v2.md` é uma adaptação local da orientação de Reel para a
integração HTML que preserva integralmente a gravação e sua voz. Não altera a
v1 usada por pedidos históricos e pelo fluxo de direção declarativa. SHA-256:
`4401257fd8a4e73352ed55aa5985a9a636612a84f1efb5ce3d315661bc8edcab`.


## Construção visual e movimento — etapa 4

Na etapa 4, novos pedidos HTML passaram a usar `instagram-reel-v3.md`, orientação local versionada com
hierarquia tipográfica, máscaras com folga para glifos, profundidade por camadas,
ação com resultado, coordenação de atenção, leitura e continuidade. A direção
fornecida continua sendo a entrada; as instruções não autorizam sua substituição.
SHA-256: `40c7fbd49864507ba6b76c945af456fc159694e2611f829af6abb78865345661`.

Inclui dois exemplos JavaScript originais completos, transmitidos dentro da skill:
`makeCompositionPassage` usa o MotionV1 existente para passagem entre focos com
vídeo contínuo; `makeReadingReveal` expõe tempos finais após stagger e mantém o
estado de leitura. São helpers adaptáveis, não cenas prontas, novas APIs instaladas
nem peças renderizadas. CSS/layout/kit e seek assíncrono da fonte pertencem à
implementação da peça. Não executar esses exemplos como um render isolado.

O mapa de uso liga esses mecanismos ao repertório selecionado na etapa 2, sem
copiar identidade ou exigir percurso, órbita, neon, desenho ou quantidade de cenas.
A skill não inclui as imagens: elas continuam separadas no pacote opcional.

Naquela entrega, captura HTML nova resolvia v3; recaptura carrega o ID/hash já registrado.
O fluxo declarativo mantém v1. Arquivos v1/v2 e runtimes não foram alterados.
O texto integral tem 13.321 bytes UTF-8 e segue dentro de `authorized_context.skill`
no mesmo payload contado/limitado; esse tamanho não é contagem de tokens nem custo.

Verificação local, sem navegador ou mídia:

```sh
.venv/bin/pytest -q app/tests/unit/test_motion_skills.py app/tests/unit/test_motion_context_requests.py
node --test app/tests/node/motion_construction.test.cjs app/tests/node/motion_repertoire.test.cjs
```

O teste Node extrai e executa os blocos JavaScript da própria skill com o runtime
real e DOM substituído, incluindo seeks diretos, repetidos e reversos, leitura,
ordem de revelação e preservação do nó de mídia. Isso não comprova enquadramento,
legibilidade ou acabamento renderizado. A crítica e a exportação integral ficam
nas etapas 5 e 6, mediante os próximos OKs do titular.

## Interação entre mensagem e elementos — retorno do titular

A rodada de interação usou `instagram-reel-v4.md`, SHA-256
`45c20abcfad7bcac5892f24eb435c4e0f216ff219872d98895b2e0bae906cda6`.
Texto integral: 18.230 bytes UTF-8. Mantém os dois exemplos executáveis da v3 e
acrescenta orientações de relação entre unidade de sentido, elemento, ação e
resultado; construção de objetos figurativos com acabamento adulto; e crítica
dessas interações pelos checks já existentes. Sem schema, runtime ou serviço novo.

O alvo depende do pedido. Não há obrigação global de xícaras, ícones, setas ou um
efeito por palavra. Ausência de transcrição não prova ausência de fala. A ação pode
usar texto editorial autorizado, sem ser apresentada como sincronizada à voz.
Transcrição alinhada continua indisponível na integração HTML atual; não foi
implementada nesta fatia. Recapturas preservam v1/v2/v3/v4 por ID/hash; não alterar
os bytes de snapshots antigos. O fluxo declarativo continua em v1.

Os testes acima cobrem o novo snapshot e preservação dos anteriores; o teste Node
executa os mesmos exemplos, preservados na v5. O retorno real do titular, a
direção e o resultado da próxima prova constam em
`docs/design/motion-interacao-mensagem-2026-11-10.md`.

## Ajustes após a prova — v5 histórica

Novas capturas HTML usam `instagram-reel-v5.md`, 19.670 bytes UTF-8, SHA-256
`c8c9e83de74053e3156c325bc7e599c1594977ede53e90d0552d6ca119e7345b`.
A v4 fica imutável para recapturas e para a prova já realizada. V5 acrescenta:

- cuidado com `clipPath: inset(0)` aplicado pelo MotionV1 mesmo em wrappers de
  transformação, que pode recortar descendentes deslocados; preservar máscaras
  intencionais e evitar/remover o recorte somente nos contêineres apropriados;
- orientação para compartilhar o mesmo ID de evidência atual entre falha criativa
  acionável e issue correspondente, conforme a validação já existente.

Não muda runtime nem relaxa guardas. Os testes usam a v5, mas as duas gerações
pagas desta rodada usaram v4; não houve prova real da v5. A correção CSS local
entregue é identificada separadamente, sem converter a falha automática em sucesso.

## Alternância narrativa — v6 histórica

Novas capturas usam `instagram-reel-v6.md`; hash registrado em motion_skills.py.
Permite gravação dominante, integrada ou cobertura gráfica completa conforme
função narrativa, com áudio contínuo e retorno no tempo absoluto. Incorpora
semântica de máscaras explícitas de movement-v2 e vínculos de crítica v3.
Skills v1–v5 intactas. Exemplos são mecanismos adaptáveis, não obrigação de manter
a janela sempre visível. Ver `docs/design/motion-alternancia-e-confiabilidade-2026-11-10.md`.

## Composição inteira ativa — v7 vigente

`instagram-reel-v7.md` orienta fundo, gravação, objetos e tipografia como partes
coordenadas, com função narrativa, variação de escala/moldura e leitura. Não impõe
fundo saturado ou animação permanente. Mantém runtime v2 e crítica v3. Hash no
registro motion_skills.py. A primeira geração de alternância usou v6 e falhou no plano; a recuperação
autorizada com v7 veio incompleta. Nenhum desses resultados qualifica geração
automática. A comparação local deriva somente da saída completa v6, preservada.


## Tratamento da gravação — etapa visual 1

Na etapa visual 1, novas capturas passaram a usar `instagram-reel-v8.md`, SHA-256
`5050e1c0a4c523e28187eb393effde5f2e6be3e8a1ea0e502ed179a5d46c81fe`.
Acrescenta moldura, área externa, escala uniforme e estados de observação da
gravação, com `makeVideoFrameTreatment` executável e testado. A v7 permanece
registrada e inalterada. Novas capturas usam movement-v3; snapshots antigos
conservam os runtimes originais. Não é render nem prova de acabamento automático.


## Fundo narrativo — etapa visual 2

Novas capturas usam `instagram-reel-v9.md`, SHA-256
`49a0cb2b52b5870c3f2e3a020abc3501b7701ab3521bad709054b92c0e4678a8`.
Acrescenta estados de fundo ligados aos focos, contraste intermediário e repouso,
com `makeNarrativeBackdrop` executável/testado. Preserva o tratamento de vídeo da
v8 e o runtime movement-v3; v8 e versões anteriores permanecem imutáveis.
Exemplos chegam ao payload do produto; sua execução em testes não é prova visual
de um Reel gerado. Não libera geração de imagem, realismo 3D ou gasto adicional.

## Etapa visual 3 — recorte realista em camadas (10/11/2026)

Novas capturas usam `instagram-reel-v10.md`, SHA-256
`3ae3bb49051b9b0b42e9268eb75ebd5b7d80b8ce3bd41c994fb4c36480b47722`.
V1–v9 permanecem inalteradas; a referência a v9 acima registra a etapa 2.
A v10 preserva seus quatro exemplos e acrescenta makeCutoutObject para imagem e
sombra coordenadas, com origem/proveniência, material e limites de 2.5D explícitos.
Seleção de asset usa acervo ou fluxo de ilustração já existente, sem habilitar
capacidade/custo por carregar a skill. Exemplo é transmitido para construção em
scene_init e testado literalmente; não cria arquivos nem comprova acabamento.
Direção Café Pausa preparada depende de imagem ainda não gerada. Sem novo MP4.
Detalhes em `docs/design/motion-objeto-realista-2026-11-10.md`.

## Etapa visual 4 — fala alinhada (10/11/2026)

Novas capturas usam instagram-reel-v11.md (hash no loader), preservando v1–v10.
A v11 mantém os cinco exemplos de construção e liga ações ao sentido/tempos da
fala via speech_cue_id. Distingue owner_reviewed de local_asr_unreviewed, limita
alegações de precisão e mantém preservação do áudio. Contexto/validação/sampler
são implementados nos serviços; skill sozinha não transcreve. Backend local
opcional baseado na abordagem Clipador Viral; modelo não instalado/executado.
Ver docs/design/motion-fala-alinhada-2026-11-10.md para prova e ativação futura.


## Direção verificável — v12 (11/11/2026)

Novas capturas HTML usam `instagram-reel-v12.md`, SHA-256
`9924e20bf34c8ee4c1de5ff4fab6e33370bbb5f60b3c29c05187158e0d32b8ec`.
Momentos relevantes articulam intenção, preparação, acento, consequência e
passagem, nos campos e tempos existentes. Moldura é opcional; objeto realista,
fundo e alternância são escolhas da direção, não exigências cumulativas. As
receitas de xícara específicas foram removidas; exemplos executáveis continuam
como mecanismos opcionais. V1–v11 permanecem imutáveis para recapturas. Esta
instrução não constitui prova de execução ou de qualidade visual.

## Espaço e coreografia — v13 (11/11/2026)

Novas capturas HTML usam `instagram-reel-v13.md`, SHA-256
`6d5ae9e0478756b1ef006f3babf6591c6c0bbe243d8cc6aee4a2d8f5dd754822`.
O exemplo opcional `makeGroundedPassage` coordena fundo, wrapper da gravação,
objeto, sombra e texto com preparação, chegada, repouso e retorno. Os tempos e
estados das tracks são expostos para correspondência com o plano; o vídeo e o
áudio continuam sob o seek existente. O código é transmitido na skill, não é uma
biblioteca instalada nem uma receita para todos os negócios. V1–v12 permanecem
imutáveis. Testes com DOM sintético e o runtime v3 verificam seeks diretos,
reversos e preservação da gravação; não comprovam acabamento visual ou áudio.
