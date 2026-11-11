# Reel orientado pela biblioteca — 06/11/2026

Rodada concluída após autorização: [MP4, comparação e evidências](ensaio-motion-biblioteca-2026-11-06.md).
Uma chamada, estimativa conservadora US$ 0,28714, sem ajuste manual da cena.
Qualidade criativa aguarda avaliação final; as seções abaixo preservam o plano.

## Decisão e objetivo

O titular esclareceu que o Reel v2 é **o mínimo aceito**, não uma composição a
copiar. Espera uma evolução própria apoiada nos bons exemplos da biblioteca
instalada. A peça anterior não foi considerada ruim, mas não entregou o salto
esperado. A avaliação continua somente no MP4 final; cards e frames não exigem
aprovações intermediárias neste ensaio rápido.

O relatório pedido é o mesmo modelo da [rodada anterior](../../.local/evals/motion-runs/53054ac7-8968-44a1-99bb-4e3763135269/report.html).
Ele agora aceita comparações adicionais: nova peça, **V2 — mínimo aceito** e
**Rodada anterior — 53054**, com players, downloads, custo e trace.

## Ajustes preparados

- Triagem local das 21 fichas/códigos e amostras dos 21 vídeos da galeria;
  três candidatas examinadas com grades de 6 fps. Isso é inspeção amostrada,
  não assistência/audição em tempo real. [Seleção e limites](../../.local/evals/motion-library-round-2026-11-06/library-review/REVIEW.md).
- Exemplos selecionados: `showreel` (ponto que muda de papel e morfose de
  formas), `app-de-motion` (câmera/interpolação de posição e escala) e
  `diagrama-azul-marinho` (percurso e chegada que provoca ação). São fontes
  concretas de código; a IA escolhe uma linguagem coerente e funções adequadas,
  sem obrigação de colar três estilos ou copiar as cenas dos exemplos.
- Skill própria **`instagram-reel-v1`**, resolvida pelo loader real, SHA-256
  `4ed6a1307437b492cf423612855645752fda331e206920abfcf155c198271ec7`.
  Bytes iguais ao working tree do repositório próprio de skills. Entram sua
  direção narrativa, materiais, áudio, fatos e entrega; o transporte técnico
  permanece o wrapper executável do ensaio. A entrega textual vai em `concept`.
- Prompt novo sem reutilizar a direção/cards anteriores ou copiar o código
  da composição v2. O v2 entra como piso visual e critérios, com dois quadros.
  Material, kit, voz e outros seis quadros são os mesmos do benchmark. Jev e
  transcrição são reaproveitados e identificados; não há chamadas novas dessas
  etapas. Modelo recebe imagens/texto, não assiste/ouve os filmes completos.
- Critérios: composição e narrativa próprias; janela de vídeo com estados
  retrato/paisagem sustentados e transformação contínua; curvas e assentamento;
  ponto/linha/forma com consequência na transição; alternância entre intensidade
  e leitura. Não reduzir “calma” a falta de expressão. Isso não obriga copiar
  o v2 nem impõe seu estilo a outros negócios.
- Report estendido mantendo casos antigos compatíveis. As comparações também
  são verificadas e congeladas antes da rede. 27 testes offline, Ruff e mypy
  estrito passaram; preflight do cenário Make passou. Nenhuma API nesta preparação.

## Fontes e preservação

21 arquivos originais dessa seleção, incluindo duas licenças MIT, foram copiados
sem alteração para
`../meu-braco-direito-motion-sources/snapshots/claude-video-library-selection-2026-11-06/`,
com manifesto, origem e hashes conferidos após a cópia. README e arquivos
existentes preservados; sem commit/push. Não é espelho completo ou backup remoto.

O payload envia código, fichas e análise própria; **não envia vídeos/quadros da
galeria**, fontes ou áudios dos exemplos. As grades da galeria ficam como análise
local privada até revisão individual de seus direitos. Não foram incorporadas
dependências CDN/GSAP ou materiais de terceiros ao runtime; o modelo adapta
funções com os avisos MIT e usa apenas os assets autorizados do caso. Os exemplos
selecionados são cenas desenhadas; integrá-los ao vídeo real continua sendo
trabalho criativo/técnico da nova composição, não capacidade já demonstrada
pelas três peças originais.

## Pedido concreto e orçamento

Preparação privada:
`.local/evals/motion-library-round-2026-11-06/proposal/`.
`instructions.md`, `input.md`, `request.json`, `manifest.json` e
`cafe-reel-library.json` são inspecionáveis. O `prepare.py` é offline e não lê
credenciais. Pedido SHA-256:
`3705e75ae9550f4fa98598ebc9872f2d07752ba849f7878a9350fc91d123a020`.
São 115.811 caracteres de texto, oito imagens e 2.071.600 bytes de corpo;
bytes/caracteres não determinam tokens nem cobrança.

Plano proposto: **uma chamada `gpt-6.1-sol/high`**, até 32.000 tokens de saída,
serviço padrão, depois render local. Estimativa **US$ 0,25–0,65**, reserva e
teto operacional **US$ 0,75 adicionais**, sem refação automática. Tarifas de
referência já consultadas nesta sessão: entrada US$ 2/M, cache-write US$ 2,50/M,
saída US$ 10/M. A estimativa do CLI usa a taxa conservadora de cache-write para
toda entrada; raciocínio já compõe tokens de saída. Não é fatura.
[Preços oficiais](https://developers.openai.com/api/docs/pricing?latest-pricing-expanded=true).

**Autorizado pelo titular:** uma chamada e envio deste pacote, até US$ 0,75
adicionais. A operação `276486e3-f312-4c5c-aaa6-4975536b9fb3` foi iniciada;
registro privado em `.local/evals/motion-library-round-2026-11-06/authorization.json`.
O orçamento anterior não é reaproveitado. A autorização inclui transmitir este
pacote específico a `api.openai.com/v1/responses`. O teto limita iniciar a chamada,
não a cobrança por uma chamada já enviada. Sem novas chamadas Jev, transcrição,
imagem, TTS, música ou vídeo generativo. Identidade/reserva novas antes da rede;
resultado incerto mantém os registros e bloqueia retry.

## Execução após autorização

```sh
make motion-eval EXECUTE=1 BUDGET_USD=0.75
```

O cenário padrão do Make agora aponta para esta proposta. A rodada anterior
permanece acessível passando seu caminho em `MOTION_CASE`; pedidos/outputs
históricos não foram alterados. O render segue Canvas/DOM/WAAPI no Chromium
com sua sandbox normal e FFmpeg, sem instalação por pedido. Não há troca de
motor, banco/Temporal ou integração de WhatsApp/Meta neste ensaio.

Depois da geração: conferir se a resposta foi executada fielmente, verificar
vídeo/áudio e função real dos componentes usados, e entregar MP4 e relatório
comparativo. Notas automáticas ou mera decodificação não demonstram que a nova
peça superou o piso. A validação final é humana. CI integral da aplicação não
foi repetido nesta preparação; testes pertinentes do CLI foram executados.
