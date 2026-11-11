# Etapa visual 4 — transcrição automática e movimento ligado à fala

Atualização de qualificação: dependências/modelo provisionados no host para a
comparação; 30 palavras reconhecidas em 6,41 s. Vocabulário incluído no bundle e
PCM extraído reutilizado diretamente para compatibilidade com PyAV 19.
43 testes dirigidos adicionais passaram. Detalhes e limites em
`docs/evals/comparacao-quatro-melhorias-2026-11-10.md`. As seções abaixo registram
a entrega inicial anterior a essa execução real; configuração geral segue opt-in.

Data: 10/11/2026. Titular autorizou implementar obtenção automática dos tempos
para Reels de até 60 s, preparando a base para futuros cortes de vídeos longos.
Implementação concluída; parar antes da comparação. Nenhum áudio do cliente foi
transcrito nesta fatia, nem modelo instalado/baixado, imagem gerada ou peça renderizada.

## Repertório dos Maestros da IA e decisão

O ZIP completo `clipador-viral.zip` contém `tools/transcribe.py`, com
mlx-whisper/faster-whisper e word_timestamps, e `tools/realign.py`, para reavaliar
palavras contra o áudio cortado. A skill shorts-repurpose distingue transcrição,
correção, fronteiras e escuta. Esses arquivos não estavam entre os trechos de
repertório previamente incorporados ao produto. Consulta local preservada em
[manifesto](../../.local/research/motion-speech-20261110/manifest.json), com hashes,
sem executar o pipeline externo ou importar suas regras de marca, CTA ou publicação.

O Maestro Video Generator usa também Gemini para legendas e `vad_align.py` para
redistribuir texto proporcionalmente nas regiões detectadas de fala. Essa
redistribuição não mede cada palavra. Adotamos a abordagem de ASR por palavra do
Clipador em código próprio, sem importar interpolação de fronteiras como precisão
comprovada. O realinhamento de áudio após cortes fica para a feature de cortes.

O backend escolhido é faster-whisper local, CPU/int8. A documentação primária
confirma [word_timestamps e CPU](https://github.com/SYSTRAN/faster-whisper) e o
[código do backend](https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py)
expõe confiança por palavra e arquivos locais. O adaptador exige tokenizer local
para evitar o fallback remoto desse backend. Não foi criada outra API paga.
A consulta à [documentação OpenAI](https://developers.openai.com/api/docs/guides/speech-to-text)
precedeu a inspeção completa dos ZIPs; não foi implementada integração nova com
Whisper API. A skill OpenAI Docs foi usada somente para essa verificação.

## Integração no produto

O Temporal continua executando o workflow existente. Antes da geração, o
orquestrador chama MotionSpeechRecognition quando a política local foi capturada.
A execução tem UUID estável `speech:0`, claim no efeito existente `generate` com
purpose `local_speech_recognition`, resultado criptografado e custo externo zero.
Não usa reserva de API paga, novo runner, serviço externo ou tabela. Claim já
existente impede repetição automática; falha/timeout não inventa fala nem repete
inferencia silenciosamente. Não há IO sob lock SQL.

O adapter extrai o áudio pelo inspetor existente, sem cortar ou acelerar. Um
subprocesso curto executa faster-whisper com word_timestamps, CPU/int8, duas
threads por padrão, um worker e timeout de 180 s. Saída limitada a 256 KiB/300
palavras. O processo usa ambiente offline, sem credenciais herdadas, timers de
animação ou download de modelo. A limpeza/timeout reutiliza o executor de
subprocessos já testado do renderer; erros são apresentados com código estável.

Pesos, tokenizer e configuração precisam estar no worker. O bundle é verificado
por hash antes da inferência, incluindo os arquivos .bin/.json, com limite de
512 MiB de arquivos (não é limite de RAM). Threads/timeout limitam trabalho;
latência e memória reais ainda precisam da qualificação no ambiente escolhido.
Configuração fica desabilitada por padrão; instanciar o runner não carrega pesos.

Resultado bruto é persistido antes da validação semântica. O contexto recebe
speech_result/transcript com origem `local_asr_unreviewed`, palavras, tempos e
confiança. Isso não é revisão humana nem garantia de tempo exato. Confiança abaixo
de 0,6 não pode ancorar ação; se todas as palavras forem incertas, o fluxo pede
revisão antes de pagar pela composição. A confiança é indicador do ASR, não prova
calibrada de precisão. Sem palavras reconhecidas, mantém-se o áudio e não se
inventa fala; resultado vazio não comprova silêncio real. Sem faixa de áudio,
registra no_audio_track sem invocar o reconhecedor.

Correção reutiliza o resultado. O storyboard já persiste o contexto completo e o
restaura no retorno da aprovação, sem nova transcrição. Snapshots anteriores sem
política permanecem sem ASR mesmo se a configuração atual for habilitada.

## Tempos revisados e validação do motion

MotionRequest.speech_timing também aceita correção humana explícita:
`motion-speech-v1`, source_sha256, provenance=owner_reviewed, alignment segment/word,
cues com ID/texto/início/fim em ms e focus_cue_ids. O caller não pode declarar
resultado automático pelo campo revisado. Um novo pedido pode corrigir palavras
e tempos mantendo os bytes originais do vídeo; a UI de revisão ainda é futura.

A captura confere hash. O loader verifica áudio, duração real e bytes. O schema
rejeita tempos vazios/invertidos/sobrepostos, IDs repetidos e focos inexistentes.
Não se redistribui texto para corrigir timestamps inválidos; tais resultados falham.

MotionBeat.speech_cue_id liga movimento e palavra/trecho. Cada foco humano exige
uma ação não hold; em ASR sem focos humanos, o modelo escolhe ao menos uma palavra
relevante e ação ligada. Onset deve coincidir com o cue, tolerância de 34 ms para
arredondamento a 30 fps. Não há segundo relógio. Antecipação pode ocorrer num beat
anterior sem vínculo; leitura e repouso podem durar além da palavra. Segmentos
não são divididos em tempos de palavras inventados.

O builder recusa geração com ASR pendente ou transcript divergente. Geração,
crítica e correção recebem o mesmo resultado. Sampler prioriza até três eventos
ligados, preservando teto de 20 quadros e distribuição global básica. Um vínculo
válido não prova que o código realizou ação perceptível. A skill v11 orienta
significado, interação e checks existentes; quadros não certificam áudio/fluidez.
Moldura, fundo, recorte realista e alternância das etapas anteriores preservados.
Skills anteriores imutáveis; campos opcionais ausentes mantêm serialização antiga.

## Ativação para a comparação futura

Não executado nesta etapa. No ambiente do worker, instalar as dependências
opcionais com `uv sync --frozen --extra speech`, ou construir o target motion-worker
com `--build-arg MOTION_SPEECH=1`. O build padrão continua sem os pacotes de ASR.
Provisionar separadamente um modelo CTranslate2 compatível e montar seu diretório
somente para leitura; não há download automático dentro de um pedido.

Calcular o digest com bundle_hash de app.adapters.motion_local_speech_worker
(passando Path do diretório). Configurar:

- MEU_BRACO_DIREITO_MOTION_SPEECH_MODE=local
- MEU_BRACO_DIREITO_MOTION_SPEECH_MODEL_DIRECTORY: caminho absoluto no worker
- MEU_BRACO_DIREITO_MOTION_SPEECH_MODEL_SHA256: digest do bundle completo
- MEU_BRACO_DIREITO_MOTION_SPEECH_LANGUAGE=pt
- MEU_BRACO_DIREITO_MOTION_SPEECH_THREADS=2
- MEU_BRACO_DIREITO_MOTION_SPEECH_TIMEOUT_SECONDS=180

Os valores aparecem em .env.example; nenhum ambiente existente foi habilitado.
A resolução do uv.lock consultou metadados públicos, sem instalar pacotes/modelos.
O pacote Python é opcional, travado no lock; imagens Docker não foram reconstruídas.

O exportador offline aceita `--speech-timing CAMINHO.json` para tempos humanos
revisados. Usa o mesmo speech_context, incorpora prompt/contexto/JSON e rejeita
fonte incompatível. Não executa ASR nem habilita geração de imagens. Não foi criado
pacote de comparação com tempos fictícios de Café Pausa.

Antes da nova peça: habilitar/provisionar o worker escolhido, obter a transcrição
real, conferir as palavras importantes e adequar a direção ao que é dito, incluindo
a xícara/fundo/moldura. Definir escopo e orçamento próprios para composição/imagem/
crítica; nenhuma autorização anterior é reutilizada. Escuta da comparação ainda
é necessária. Vídeos brutos de 30 minutos, seleção e execução de cortes não estão
implementados nesta fatia; exigirão ingestão longa, segmentos e mapa fonte→corte.

## Verificação

346 testes Python dirigidos passaram em 8,66 s, incluindo falas sintéticas,
silêncio, ruído/baixa confiança, metadados/tempos inválidos, hash de modelo/fonte,
subprocesso offline/limite/limpeza, claim/replay, captura e recaptura, geração,
crítica/correção, integração do orquestrador, storyboard e exportação.
100% de linhas/ramos nos sete módulos medidos: schema/serviços de fala, adapters
locais e loader de skills. Não é cobertura global. Inclui wiring local sem carregar o modelo.
Mypy de 16 módulos e Ruff passaram; uv.lock conferido offline; 11 testes Node dos exemplos/movement-v3
passaram. Sem CI global, SQL, inferência real ou acionamento do Docker.

Implementação pronta para a prova controlada; qualidade/precisão reais ainda não
qualificadas. Aguardar OK do titular para iniciar a comparação com nova peça.
