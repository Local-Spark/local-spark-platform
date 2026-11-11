# Café Pausa — interação entre mensagem e elementos

Estado: recuperação encerrada; **MP4 com ajuste técnico local entregue**.
O pedido automático permaneceu failed por crítica inválida, após render com
recorte indevido. A variante local não equivale a sucesso automático do produto.
Teto acumulado US$ 3, com recuperação explicitamente autorizada; reservas US$ 2,90,
uso estimado US$ 0,758614, sem imagens pagas ou chamadas adicionais.

## Resultado da primeira tentativa

Pedido `655c8044-a0c3-5486-b851-ff5eed690d74` terminou em
`failed/MOTION_AI_OUTPUT_LIMIT`. Uma geração recebida, nenhum render ou crítica.
Uso informado: 24.945 tokens de entrada, 23.118 de saída (11.394 de raciocínio).
Estimativa conservadora US$ **0,293543**, reserva retida US$ **1,40**; não é fatura.
Worker dedicado encerrado e arquivo temporário de ambiente removido.

Pedido e resposta declaram `max_output_tokens=64000`, mas o provedor devolveu
`status=incomplete`, `reason=max_output_tokens` com a contagem acima. O motivo
exato da divergência não foi estabelecido. JSON de 41.276 caracteres termina
no meio de `scene_init`; não aceitar, completar manualmente ou executar essa
saída como se fosse composição válida. Guarda do produto funcionou como previsto.
Evidências locais: `generate-request-actual.json`,
`generate-provider-response-incomplete.json`, `result.json` e efeito durável.

## Recuperação autorizada pelo titular

Mesmo modelo, direção, elementos, áudio, referências e limites; briefing solicita
reutilização de funções/desenhos e remoção de repetição/comentários longos para
favorecer saída completa. Não reduzir as interações para conseguir um vídeo simples.
Não há evidência de que isso elimine a interrupção observada.

[Briefing de recuperação](brief-cafe-pausa-interacao-recuperacao-2026-11-10.txt) e
[pacote pelo montador do produto](../../.local/exports/motion-cafe-pausa-interacao-recuperacao-20261110.zip)
preparados offline. O titular autorizou explicitamente uma nova tentativa
e crítica dentro do mesmo teto acumulado de US$ 3. Identidade nova e guarda
sem reenvio automático. Reservar US$ 0,75 para
geração e US$ 0,75 para crítica, somados ao US$ 1,40 já retido = US$ 2,90, dentro
do teto acumulado de US$ 3 desta rodada. O corpo real continua sujeito à contagem
e ao teto por chamada antes de envio; não liberar a reserva da falha para abrir espaço.

## Entrada

- Mesma fonte/voz/kit, 11,2 s, 720×1280/30 fps, modelo `gpt-6.1-sol`, high,
  geração até 64.000 tokens, crítica até 8.000, `storyboard=false`.
- Skill v4, direção fornecida em três momentos, repertório business-reel-v1
  com seis referências e seis quadros da gravação. Fatos/recursos existentes.
- [Direção](direcao-cafe-pausa-interacao-2026-11-10.json) e
  [briefing](brief-cafe-pausa-interacao-2026-11-10.txt).
- Texto na tela é a base de tempo desta coreografia. Não há transcrição alinhada
  e nenhum sincronismo vocal é alegado. Elementos figurativos são código original.
- [Pacote integral](../../.local/exports/motion-cafe-pausa-interacao-20261110.zip)
  produzido pelo mesmo montador offline, sem rede/credenciais/render.

Comparar a nova candidata com a versão tipográfica de
`reel-refactor-comparison-20261110/v0.mp4` e com os desenhos históricos de
`reel-storyboard-composition-20261109/v0.mp4`. Preservar ambos os arquivos.

## Critérios e limites

Reconhecer visualmente o vínculo tempo→percurso, café→preenchimento e pausa→repouso;
ver interação real de elementos e continuidade entre os momentos, não somente
entradas de ícones e palavras. Conferir desenho adulto, leitura, partes da xícara,
recorte do líquido, seta com origem/destino, ação da gravação, voz e kit preservados.
O parecer automático deve se basear em quadros e declarar ações não amostradas.

Uma peça não isola causalmente cada mudança nem comprova qualidade universal.
O próximo pedido é uma nova criação, não alteração do código do resultado anterior.
Comparação humana define se o acabamento atende; `adequate` não é esse aceite.

A tarifa permanece a conferida na [página oficial](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
na rodada imediatamente anterior. O serviço usa contagem da entrada real, teto
conservador de US$ 2,50/M entrada e US$ 10/M saída, sem presumir desconto de cache.
Uso estimado, reserva e fatura serão registrados separadamente.

## Execução iniciada

Pedido `655c8044-a0c3-5486-b851-ff5eed690d74` admitido pela API e despachado pelo
outbox/Temporal. Worker dedicado com 356 arquivos atuais, sem credenciais na imagem.
Checagem sintética do renderizador aprovada antes da chamada. Entrada local tem
2.005.339 bytes, seis quadros de referência e seis da fonte. O worker conta e
preserva o corpo real antes do envio; PNGs da fonte podem mudar de codificação
entre macOS e Linux, conforme observado na rodada anterior.

Pasta privada: `.local/evals/reel-semantic-motion-20261110/`. Identidades, plano e
autorização próprios; nenhum replay de chamada anterior. Comparação preparada com
os dois MP4s históricos, sem sobrescrevê-los.

Recuperação em `.local/evals/reel-semantic-recovery-20261110/`, com plano/autorização
próprios. Pedido limitado a US$ 1,50 e reserva de US$ 0,75 por chamada. A preparação
confere que limites globais/do tenant permanecem dentro do teto da rodada original;
não renova US$ 3 nem libera a reserva de US$ 1,40 da tentativa incompleta.

Pedido de recuperação `96f1406b-a9af-53f2-9d63-4e38464aa7e4` admitido e
despachado via API/outbox/Temporal. Mesma imagem atualizada do worker, checagem
sintética no diretório novo aprovada. Reutiliza código do produto e cria operação
nova; a resposta parcial não foi reaproveitada como composição. Geração e crítica concluídas; resultado e limites abaixo.

## Resultado da recuperação

Pedido `96f1406b-a9af-53f2-9d63-4e38464aa7e4` terminou
`failed/MOTION_AI_RESPONSE_INVALID`, com uma versão renderizada e sem peça aprovada.
Geração: 25.053 tokens de entrada, 22.027 de saída; estimativa US$ 0,282903.
Crítica: resposta completa, 52.631 tokens de entrada e 5.059 de saída; estimativa
local conservadora US$ 0,182168. O ledger dessa crítica ficou sem valor estimado
porque a resposta foi rejeitada; `result.json` mantém `estimate_complete=false`.
O cálculo local não altera ledger nem constitui fatura.

A crítica identificou vídeo reduzido a faixa vertical. Seu schema compacto passou,
mas `brief_alignment=not_met` citou current-2/5/13 e a issue citou current-6;
faltou evidência atual compartilhada. Diagnóstico:
`MOTION_CREATIVE_CORRECTION_UNGROUNDED`. Parecer rejeitado permanece preservado,
sem aprovação, reescrita manual, relaxamento da guarda ou nova chamada paga.

O recorte vem do `clipPath: inset(0)` aplicado por MotionV1 a wrappers animados:
o deslocamento do filho fica limitado pelo contêiner ancestral, ainda que o
plano não peça máscara. É uma causa técnica observada, não hipótese sobre
capacidade do modelo. A orientação v5 explica esse cuidado e os IDs exatos da
crítica. A prova paga e os pacotes exportados continuam com v4; v5 sem prova real.

## Variante local para comparação

Correção CSS somente nos wrappers de transformação `tempo-video`, `cafe-video`,
`pausa-video` e `pausa-xicara`: `clip-path:none!important`. Máscaras intencionais
de texto/líquido, plano, desenhos, JavaScript, curvas, textos e áudio preservados.
Original automático e estado failed intactos. Operação local de render
`b4d963df-3d5f-4f99-a6b3-6582e4cf32a4` usa o renderer isolado existente diretamente;
não é uma versão aprovada pelo fluxo API/Temporal e não recebeu nova crítica paga.

Arquivos em `.local/evals/reel-semantic-recovery-20261110/`:

- `comparison.html`: abrir no navegador para reproduzir lado a lado; permite
  escolher versão tipográfica, desenhos históricos ou saída automática defeituosa.
- `local-repair.mp4`: candidata com ajuste técnico local, SHA-256
  `87533d1b0794f5d70c0fa5c71de2a73748f3f24227d0d67718e107b6440e876a`.
- `local-repair-composition.json`, `render_local_repair.py`,
  `local-repair-result.json`: composição, procedimento e diagnóstico local.
- `v0.mp4`, `v0-composition.json`: saída automática original, preservada.
- `review-output-invalid.json`, `review-validation-diagnostic.json`: parecer
  recebido e motivo de rejeição; não representam crítica válida da variante local.
- `technical-inspection-local-repair.json`, `local-repair-frames/`: metadados,
  comparação do sinal de áudio e 11 quadros extraídos do MP4.

MP4 H.264, 1.067.614 bytes, 720×1280, 30 fps, 336 quadros, 11,2 s. Áudio AAC
11,176 s. Comparação PCM mono/16 kHz com a fonte: correlação 0,99998847,
razão RMS 0,99963559; não equivale a escuta humana ou transcrição. Quadros
intermediários e finais inspecionados mostram vídeo inteiro após o ajuste,
percurso/seta, xícara preenchida e vapor ligado ao convite. Não comprovam
fluidez integral, acabamento aceito ou alinhamento com fala real.

Custo estimado acumulado pelo uso retornado: 0,293543 + 0,282903 + 0,182168 =
**US$ 0,758614**. Reservas retidas: 1,40 + 0,75 + 0,75 = **US$ 2,90**;
nenhuma liberação fictícia ou reaproveitamento do saldo. Worker dedicado encerrado
e arquivo temporário de ambiente removido. Render local não chama modelo.

Validação final: 100 testes Python, quatro Node, 100% linhas/ramos no loader,
Ruff e tipos direcionados; sem CI global nem teste SQL. Pendentes: avaliação humana
da proposta, prova automática futura da v5 e ingestão/alinhamento de fala quando
necessário ao pedido. Saldo não autoriza outras chamadas ou tentativas.
