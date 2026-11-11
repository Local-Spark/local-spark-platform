# Clipe musical pessoal — plano da rodada

## Execução autorizada

Titular autorizou as três chamadas/envio pessoal, até US$ 1,60 adicionais,
sem refação automática. `authorization.json` privado vincula fonte, plano,
proposta ASR e classes de dados. Transcrição recebida na operação
`6f4fdd0c-ff03-4dfe-b55c-efc5d396a760`, estimativa US$ 0,0047.
Quatro trechos semânticos foram conferidos/corrigidos com legendas incorporadas,
sem alterar a resposta original; tempos seguem aproximados do ASR, não alinhamento
auditivo comprovado. Letra/correções ficam somente em arquivos privados.
Demais etapas concluíram: peça de 46,5s e comparação disponíveis, total estimado
US$ 0,51148. Direção excessivamente conservadora recebeu revisão escrita antes
da composição; código final executado como recebido. Áudio original confirmado
idêntico; avaliação criativa do titular pendente.
[Resultado e verificações](ensaio-clipe-musical-pessoal-2026-11-06.md).

## Entrega e material

Titular pediu focar somente a edição do próprio vídeo: peça musical com formas,
motion e imagens/planos realistas ligados à letra e ao ritmo. Preservar canto e
execução. Entrega pretendida: MP4 vertical dos 46,5 s e página de comparação
original/editado com entradas, saídas, código, custo e trace. Avaliação criativa
somente no final, conforme escolha anterior; sem portões intermediários de cards.

Original fornecido: 7.493.056 bytes, H.264 480×848/30fps, AAC estéreo;
SHA-256 `ec4063b5405b7e2c8c7d1a664ee201e52ee8e9e349a275efdc0dd1b15f39e474`.
Cópia privada íntegra, AAC extraído sem recodificar, WAV mono 16kHz e 12 quadros
em `.local/evals/music-performance-2026-11-06/`. Original não é alterado.
Título “Chuva de Castigo” e legendas já incorporados à imagem foram observados;
não duplicar textos cegamente nem encobrir rosto/mãos/instrumento.

Dois apoios realistas licenciados preparados: chuva no vidro e recorte de
vitrola/disco. Usos específicos dependem da letra/timeline; não constituem nova
filmagem da pessoa. Fontes, licenças, recortes, hashes e limites de inspeção em
`support-media/provenance-selected.json`. Não usar originais excluídos.
Nenhuma geração paga de imagens/vídeos está incluída; Higgsfield e estudo Brabo
ficam fora desta rodada, como frentes adiadas pelo titular.

## Caminho real e limites

1. Uma transcrição com palavras/segmentos temporizados. Conferir com os textos
   incorporados e registrar incertezas do canto; tempos do reconhecedor não são
   prova de alinhamento perfeito. Não inventar versos ou completar a canção.
2. Uma direção criativa: narrativa, contraste de temas, movimentos/forma/câmera,
   uso dos apoios e entradas ligadas a palavras/momentos. A performance continua
   protagonista. Não criar identidade pública, nome artístico ou kit de marca
   sem base; paleta pode ser provisória desta peça.
3. Uma composição executável usando direção/timeline, skill própria Reel,
   referências/motores MIT reais e método da Intensa. Preservar o áudio original
   em montagem técnica separada; não adicionar Jazz Piano, TTS ou dublagem.
4. Render local com modo explícito de material pessoal, mux do AAC original,
   validação de vídeo/áudio/tempos e comparação. Registrar qualquer intervenção.

O CLI de fixtures não aceita esse material como sintético. Um renderer privado
separado usa `owner_media_evaluation`, consentimento local vinculado ao SHA
original e allowlist de assets por hash. Mantém Chromium sandbox normal, CSP,
rotas, ambiente limpo e bloqueios existentes. Pré-teste técnico com código local
confiável gerou 1s/30 quadros mudos, com seeks/decodificação e hash do original
preservados. Não é peça criativa, isolamento de SO comprovado, runner de produção
ou liberação genérica de clientes. Não houve API, banco, Temporal ou instalação.
Render integral de 1.395 quadros ainda não executado; teto privado é 1.600.

## Chamadas e orçamento propostos

| Etapa | Modelo | Chamadas | Reserva |
| --- | --- | ---: | ---: |
| Transcrição com tempos | whisper-1 | 1 | US$ 0,10 |
| Direção/storyboard | gpt-6.1-sol/high, até 16 mil tokens saída | 1 | US$ 0,75 |
| Composição HTML/JS | gpt-6.1-sol/high, até 32 mil tokens saída | 1 | US$ 0,75 |
| Total | | **3** | **US$ 1,60 adicionais** |

Estimativa total: **US$ 0,60–1,50**, não fatura. Transcrição isolada estimada
US$ 0,00465 a US$ 0,006/min; reserva permite arredondamentos/incertezas.
Whisper suporta tempos por palavra/segmento e está depreciado; uso pontual do
ensaio, não adoção como nova base do produto. [Guia oficial](https://developers.openai.com/api/docs/guides/speech-to-text),
[modelo/preço](https://developers.openai.com/api/docs/models/whisper-1).

Sem retry automático. Operação incerta preserva reserva e para a sequência.
Respostas recebidas e possíveis adaptações ficam separadas. Verba anterior não
é renovada nem reutilizada; teto controla início, não a cobrança de chamada
enviada. Só avaliar qualidade após MP4 real, sem usar CI como nota criativa.

Antes de rede, solicitar autorização para as três chamadas e para enviar à
OpenAI o áudio real voz/violão de 46,5s, 12 quadros pessoais, letra/tempos derivados,
quadros de apoio licenciados e código/documentação local/MIT/benchmark próprio.
Transcrição usa `/v1/audio/transcriptions`; demais `/v1/responses`, `store:false`.
Nenhuma mídia pessoal enviada na preparação. Não reaproveitar consentimento
anterior de fixtures para este caso real.

Plano privado: `proposal/plan.json`, SHA-256
`27b5a20ee38237264d0555c65e28c6fb3a107b604545a00b41c0928dcf47a4c9`.
Proposta ASR: `proposal/transcription-request.json`, SHA-256
`3649372e07425d09811418f8e6f5fcc255aba5a1fd85446c09cbbe4cf3426bb7`.
Pedidos das etapas dependentes serão congelados por hash antes de cada efeito,
dentro das mesmas classes de dados e limites autorizados.

Esta alteração prepara um ensaio pessoal; não conclui vídeo no produto,
story/carrossel, identidade de marca ou publicação.
