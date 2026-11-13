# ASR real, avaliação sonora e orçamento novo — 12/11/2026

> **Escopo histórico — esclarecido em 13/11/2026.** Estados, versões selecionadas,
> orçamentos e ordens de parada abaixo descrevem a entrega desta data; não são
> automaticamente instruções para uma rodada nova. Contratos capturados continuam
> preservados. Consulte a [orientação vigente](motion-orientacao-vigente-2026-11-13.md)
> para diferenças entre geração nova/evolução, estado operacional e próximo roteiro.

O titular pediu fechar o ASR real e a avaliação dos arquivos sonoros, conferir
novamente a entrada e apresentar orçamento novo. Preparação v7 substitui v5/v6
para revisão, sem gerar plano, código, assets ou render. Peças anteriores continuam
somente como evidência de avaliação do produto, fora do contexto desta geração.

## Implementação e fronteira da preparação

- Modelo faster-whisper-small já disponível localmente; nenhum download ou API
  de transcrição. Bundle SHA-256
  `c176c33677afdaf71e808d4f365291928c28eadbd8e138204c68933569c26e9c`.
  Somente as configurações ASR do `.env` ignorado foram atualizadas: modo local,
  modelo/hash, português, dois threads e timeout de 180 s. Demais configurações
  preservadas. Nenhum contêiner reiniciado para propagar esse ambiente.
- `motion_supervised_prepare` chama o mesmo `MotionSpeechRecognition` e adapter
  `LocalMotionSpeech` do runtime. Claim e recibo privados, criação exclusiva,
  permissões 0600 e identidade `uuid5(operation_id, "speech:0")` registram cada
  reconhecimento novo; não há reutilização de transcrição arquivada. Trata-se de
  inspeção com journal local, sem admissão no banco ou execução pelo Temporal.
  O caminho normal continua usando os efeitos duráveis existentes.
- Novo contrato `motion-sound-analysis-v1` é capturado para pedidos novos no modo
  de qualidade independente. O loader decodifica fonte com áudio e candidatos
  localmente depois da transação SQL, com bytes/hash/tipo verificados, comandos
  limitados e PCM mono 16 kHz de até 60 s. Não mistura ou renderiza peça.
- Análise registra duração decodificada, RMS/pico de amostra, instante do pico,
  amostras no limiar de escala cheia e intervalos de energia. Não infere escuta,
  semântica, LUFS, true peak ou inteligibilidade. Plano limita cortes à menor
  duração entre contêiner e PCM, validando identidade da análise. Checkpoint
  compara contrato e análise na retomada. Snapshots históricos não ganham
  contrato novo silenciosamente.
- Evidência opcional `kind=audio` exige ID/hash do arquivo e vinculação aos bytes
  reais no builder, inclusive presença de áudio na fonte. Mudança de arquivo
  bloqueia envio. Relato humano não vira escuta do servidor, requisito criativo
  ou aprovação de mistura. Pedidos sem o campo mantêm serialização anterior.

## Resultado e avaliação humana

ASR novo da fonte atual: 30 palavras, alinhamento por palavra, provenance
`local_asr_unreviewed`. Uma palavra tem confiança 0,559, abaixo de 0,6; guardas
existentes impedem seu uso como âncora sem revisão. Texto e tempos não foram
revisados pelo titular. Transcrição privada em `ASR-REVISAO.md`; conteúdo de
cliente não foi copiado para fixtures ou documentação versionada.

Escuta do titular recebida nesta sessão:

- Fonte: **“Voz clara; sem sons de café audíveis”**.
- Candidatos servir café e contato da xícara: **“Os dois”**, em resposta sobre
  adequação para considerar no planejamento. Não exige usar ambos.

Os três relatos foram vinculados a SHA-256 na entrada efetiva. A fonte v7 tem os
mesmos bytes da fonte v5 apresentada para escuta. Essa avaliação fecha a adequação
dos arquivos isolados para planejar. Eventos, trechos, ganhos, sincronismo e
inteligibilidade da mistura ainda precisam de plano/revisão e prévia autorizada.
O catálogo estático e a análise mantêm sua origem sem escuta do sistema; a
avaliação humana específica está separada em `preparation_evidence`.

| Arquivo | Duração PCM | RMS dBFS | Pico de amostra dBFS | Instante do pico |
| --- | ---: | ---: | ---: | ---: |
| Fonte | 11.177 ms | −14,560 | −3,650 | 10.841 ms |
| Servir café | 5.053 ms | −36,782 | −8,190 | 3.596 ms |
| Contato da xícara | 5.074 ms | −48,751 | −13,240 | 3.025 ms |

Zero amostras no limiar de escala cheia nesses PCM; isso não certifica ausência
de distorção. MP3s têm duração decodificada inferior ao contêiner (5.093/5.120 ms).
Intervalos de energia estão na entrada; candidatos contêm silêncio e níveis
diferentes, exigindo escolha justificada de trecho/ganho, sem normalização
automática para um pico comum. Faixa original e seu contrato permanecem intactos.

## Entrada conferida

Pacote privado `.local/evals/motion-supervised-20261112/preparation-v7/`, operação
`3427c666-53eb-5e94-bbe9-8e1a7942ece9`. Payload SHA-256
`6be0608f467776acfe1efcf97bfe9e88afc94d6ddbaaa40ff1e5dda613c2b158`.

Contexto/kit/fatos/materiais recuperados com escopo autenticado do negócio
existente; mensagem de cliente continua simulada. São 15 quadros da fonte, zero
da peça anterior, zero referências externas ou imagens recuperadas de render,
dois candidatos sonoros e três relatos humanos de escuta. Critérios do produto,
repertório v4 sem os oito prints e bibliotecas mantidos. Nenhum evento selecionado.

Manifesto/bytes/imagens verificados; builder atual reproduz semanticamente o
payload e preserva ordem do schema de saída. Recibo ASR bruto reproduz exatamente
o timing/transcrição normalizados, com fonte/política/identidade conferidos.
`MOTION_QUALITY_SPEECH_REQUIRED` de v5 foi resolvido nesta preparação. Isso
comprova integridade e prontidão para revisão, não qualidade artística.

`PREPARACAO-ATUAL.md`, `intake-v4.json`, `status.json`,
`preparation-v7-verification.json`, `AVALIACAO-SONORA.md` e
`ORCAMENTO-NOVO.md` apontam para a rodada atual. Pacotes anteriores e versões dos
relatórios antes da escuta foram preservados.

## Orçamento proposto, ainda não autorizado

| Etapa | Chamadas máximas | Reserva |
| --- | ---: | ---: |
| Plano | 1 | US$ 1,25 |
| Código, após aprovação específica do plano exato | 1 | US$ 1,25 |
| Total da rodada | 2 | **US$ 2,50** |

GPT-6.1 Sol, esforço high, Standard/default, até 54.000 tokens de saída por
chamada. [Tarifa oficial do modelo](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
conferida em 12/11/2026: US$ 2/M entrada, US$ 2,50/M escrita de cache e US$ 10/M
saída. Política qualificada existente usa conservadoramente US$ 2,50/M para toda
entrada e bloqueia acima de 272.000 tokens. Nesse limite, entrada mais saída
custam no máximo US$ 1,22 por chamada; proposta arredonda reserva para US$ 1,25.

É teto operacional, não estimativa de fatura nem autorização. Não houve contagem
remota de tokens; após autorização, o guard existente conta o payload completo
de cada etapa, incluindo imagens, e bloqueia limites excedidos. Sem Fast,
regional, contexto longo, cache 12 h, retries/correção, crítica, geração de
assets, ASR pago, storyboard, render ou publicação. ASR e medições desta preparação
tiveram custo zero de API. Orçamento antigo não foi reutilizado.

## Validação e trabalho restante

- 1.646 testes motion/exportadores passaram; dois skipped. Quatro integrações
  passaram no `_test` existente com logins restritos, sem migração. Grupo dirigido
  final de 128 passou; grupos sobrepostos, sem somar contagens.
- `motion_sound_analysis.py` e `motion_sound_library.py`: 100% de linhas e
  branches (142 statements/58 branches). Ruff lint global e Mypy de 334 módulos
  aprovados. Sem exclusão de produção para elevar cobertura.
- `make ci` tentado, ainda bloqueado por 13 arquivos preexistentes de formatação;
  seus conteúdos foram preservados. CI/cobertura global não qualificados.
- Dev continua `0117_motion_recapture_events`; dedicado `_test` já estava 0118.
  Sem migração, novo banco/serviço/dependência, admissão ou chamadas pagas. Geração
  disabled, execução desabilitada e orçamento zero. Cinco contêineres restritos
  confirmados `exited`.

Próximo gate: titular revisar entrada/orçamento; fechar CI e configuração de
execução antes de gerar. Eventual migração 0118 do dev exige autorização separada,
não concedida nesta tarefa ou pela mera apresentação de orçamento. Depois:
plano → revisão por cena/aprovação exata → código → parar em `awaiting_render`,
antes de qualquer storyboard/render. Escuta da mistura e qualidade artística
permanecem para etapa posterior autorizada; não há v0 completa declarada.
