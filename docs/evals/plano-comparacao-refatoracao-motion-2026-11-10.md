# Comparação após a refatoração de motion

Estado: **execução concluída** após autorização nova de US$ 5 pelo titular.
Uma geração, um render e uma crítica válida, sem refações ou imagens pagas.
O resultado está disponível para comparação humana; não há aprovação criativa final.

## Resultado entregue

- [Comparação A/B](../../.local/evals/reel-refactor-comparison-20261110/comparison.html),
  com reprodução conjunta e alternância de áudio.
- [Nova candidata MP4](../../.local/evals/reel-refactor-comparison-20261110/v0.mp4).
- [Parecer automático](../../.local/evals/reel-refactor-comparison-20261110/v0-review.json)
  e [registro da execução](../../.local/evals/reel-refactor-comparison-20261110/result.json).

Pedido `af516483-1146-5c77-a6d6-03e0020d2be4`, peça
`a4ac4fde-4706-5272-a9ce-2edacd8227f6`, estado `completed`, sem publicação.
Fluxo API → outbox → Temporal → worker dedicado → serviços de geração/render/crítica,
com uma versão e nenhuma correção manual do código gerado. Worker encerrado.
Execução do workflow: aproximadamente 376 s, além da preparação local.

| Chamada | Entrada | Saída | Estimativa US$ |
| --- | ---: | ---: | ---: |
| Geração | 22.796 tokens | 10.626 tokens | 0,163250 |
| Crítica | 47.062 tokens | 4.110 tokens | 0,158755 |
| Total | | | **0,322005** |

Estimativa conservadora do uso, não fatura. Reservas de US$ 2,80 permanecem
distintas do custo estimado; não usar saldo para novas tentativas.

MP4: H.264, 720×1280, 30 fps, 336 quadros, 11,2 s, 1.474.125 bytes.
SHA-256 `cb849d6c97daede56f842a4750e4e0c5bf277ef79f99b88602148191825f5e47`.
Áudio AAC de 11,176 s; comparação após decodificação mono/16 kHz, sem ajuste de
offset, deu correlação 0,999988 e razão RMS 0,999636 com a fonte. Indica preservação
do sinal; não é escuta humana ou transcrição. Dados em `technical-inspection.json`.

Crítica `adequate`, sem issues e com quatro verificações criativas `met`.
O parecer terminou em 4.110 tokens de saída, abaixo dos 8.000 disponíveis, sem
truncamento nesta execução. Áudio ficou `uncertain`, coerente com ausência de
escuta. A crítica analisou a candidata e suas amostras, não o MP4 anterior:
`preferred=undetermined`. Não apresentar esse parecer como vitória em A/B.

Inspeção local de quadros mostra tipografia em destaque, gravação maior e planos
gráficos em lugar da jarra/xícara desenhadas. A aparência é mais sóbria, mas esse
juízo visual não demonstra equivalência às referências nem fluidez integral.
O titular deve comparar os vídeos completos; 14 de 17 eventos não entraram na
seleção temporal da crítica. A comparação mede o conjunto das mudanças e da direção.

## Fidelidade da entrada e verificações

Skill v3, direção fornecida, seis referências e seis quadros da fonte confirmados.
Entrada realmente enviada preservada em `generate-request-actual.json` e resposta
em `generate-provider-response.json`; equivalente para `review`. O payload real
da geração tem 2.613.372 bytes: os PNGs da fonte produzidos pelo worker Linux têm
codificação diferente dos da preparação macOS, mas os seis quadros têm pixels RGB,
dimensões e tempos idênticos. O restante do payload é igual. As seis referências
visuais permaneceram byte a byte iguais. O contador/teto do produto usou a entrada
real do worker. Evidências em `actual-call-verification.json` e
`source-frame-differences.json`; não confundir hash de PNG com mudança visual.

Sem alteração de código de produção, migração, limpeza do banco ou CI longo.
Checagem sintética do renderer, hashes do worker/insumos, validações do produto,
FFprobe, inspeção de quadros e comparação de áudio foram suficientes para esta
rodada. Arquivo temporário de ambiente do worker removido após seu encerramento.

Pendência: avaliação humana do acabamento. Nenhum novo efeito está autorizado
automaticamente pelo saldo restante.

Artefatos privados desta rodada: `.local/evals/reel-refactor-comparison-20261110/`.
`paid-plan.json` e `approval.json` vinculam escopo, teto novo e hash do plano.
Reserva de US$ 1,40 por chamada, máximo de duas chamadas (US$ 2,80 reserváveis).
Tarifa conferida na [página oficial](https://developers.openai.com/api/docs/models/gpt-6.1-sol):
US$ 2/M entrada, US$ 2,50/M escrita de cache e US$ 10/M saída; cálculo conservador
usa US$ 2,50/M para toda a entrada, com limite de contexto existente.
O serviço conta a entrada e verifica o limite antes de cada envio.

Para entregar diretamente o MP4 solicitado, o novo pedido usa `storyboard=false`,
opção existente. Isso não registra aprovação criativa de quadros nem da peça.
Worker dedicado reconstruído com o código atual; renderer existente preservado,
com hashes de runner, áudio e MotionV1 iguais aos arquivos atuais.

## Comparação proposta

- A: último Café Pausa, `.local/evals/reel-storyboard-composition-20261109/v0.mp4`,
  SHA-256 `a52bf391ffd3d6a8b5d1c7970073f9903e19f7839958ed0fae84d276acb4c57f`.
  É a peça avaliada como parcialmente melhor, mas infantil, e não o baseline mais antigo.
- B: nova candidata com a mesma gravação integral, voz, kit, duração de 11,2 s,
  saída 720×1280/30 fps e configuração histórica `gpt-6.1-sol`, high, até
  64.000 tokens na geração. Usar os serviços e montador atuais do produto.
- Direção: “abrir espaço para uma pausa”, em dois momentos, conforme
  `direcao-cafe-pausa-2026-11-10.json` e `brief-cafe-pausa-2026-11-10.txt`.
  Skill v3, repertório business-reel-v1 com seis referências visuais,
  contrato criativo v5 e crítica motion-review-v2.
- Escopo proposto: uma geração de composição, render local e uma crítica
  automática de até 8.000 tokens; nenhuma refação, retry ou imagem paga.
  Respeitar a aprovação de quadros caso o pedido use storyboard.
- Entrega: MP4 novo, comparação A/B, entradas/respostas e parâmetros registrados,
  custo/uso com distinção entre reserva e estimativa, e crítica ligada às evidências.

Avaliar hierarquia e tipografia, composição em camadas, continuidade, função e
acabamento do movimento, legibilidade, fidelidade ao kit e preservação da gravação
e áudio. O parecer automático não substitui a avaliação do titular.

Esta comparação mede o conjunto das mudanças, incluindo a nova direção visual.
Não isola o efeito de cada etapa nem prova qualidade geral com uma única amostra.
O resultado do Grok é um braço externo adicional, com modelo e interação distintos.

## Preparação verificada

Último MP4 e ZIP conferidos por hash. ZIP original permanece com 39 arquivos e
SHA-256 `45229038492e0e6842dac633397e6558e0ff679245291da5b8a313a218a5c3be`.
Os arquivos listados no manifesto da pasta exportada estão presentes e íntegros.
O verificador estrito recusa essa pasta por três extras: `.DS_Store`,
`execution/.DS_Store` e `execution.zip`. Não foram apagados nem incorporados
como entradas do modelo. Para uma nova operação, montar uma entrada própria.

A árvore contém mudanças staged anteriores; foram preservadas. Nenhum script
histórico de execução foi chamado e nenhum orçamento anterior foi reaproveitado.

## Sequência aplicada na execução

1. Teto novo e tarifa conferidos. Validar contagem/limite por chamada no serviço;
   não tratar a reserva como custo final ou usar o restante para outras tentativas.
2. Conferir executor e serviços locais. A documentação registra worker antigo
   parado; preparar imagem com o código atual antes de uma prova integrada.
3. Criar identidades novas e capturar contexto atual pelos controles existentes,
   com Python/API, Temporal, auditoria/outbox e ledger. Conferir payload e hashes
   antes da chamada; não repetir operações incertas nem limpar o banco.
4. Executar somente o escopo e teto autorizados. Preservar falhas e saídas para
   inspeção, sem corrigir manualmente o código gerado e apresentar como geração bruta.

As etapas acima foram executadas nesta rodada. A conclusão de ganho de qualidade
continua dependente da comparação humana; o resultado técnico está registrado acima.
