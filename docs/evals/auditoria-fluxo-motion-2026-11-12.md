# Auditoria do fluxo motion — conferência por etapa

**Atualização posterior:** as lacunas descritas abaixo pertencem à execução
histórica. Em 12/11 foram implementadas as
[fases 1–3 de preparação/revisão](../design/motion-preparacao-e-revisao-fases-1-3-2026-11-12.md),
incluindo duas pausas opt-in e inspeção da chamada/retorno reais. Isso não reexecuta
nem requalifica a peça auditada. A distinção entre cobertura, trace e qualidade,
e a proposta OpenCode, estão em
[inspeção do produto](../design/opencode-e-inspecao-do-produto-2026-11-12.md).

## Rastreamento técnico completo — complemento de 12/11/2026

Este complemento responde à solicitação de rastrear frase de entrada, chamadas,
retornos e lacunas de todo o processo. Trata da rodada de recuperação de 11/11,
pedido 2d6bc06c-d12e-5cac-afc8-66667f872dae, e da prévia posterior. Estados vêm
dos recibos arquivados, não de consulta atual ao banco. Nada foi gerado novamente.

### 0. De onde veio a mensagem que simula o cliente

**Esta rodada não partiu de uma mensagem natural de cliente interpretada pelo
produto.** O assistente preparou brief, direção e vínculo de evolução. O script
local run_round.py carregou o pacote e enviou seu JSON diretamente à API de
motion. Na configuração desta rodada, intent_ai_mode, editorial_ai_mode,
descoberta de referências e webhook Meta estavam desabilitados. Isso não prova
remoção dessas capacidades; significa que não participaram deste percurso.

A mensagem efetiva, no campo instruction de request-body.json, era:

> Evolua a base histórica indicada, preservando abertura, voz original integral,
> texto, kit e a mesma imagem conceitual da xícara. A mudança está nas passagens:
> gravação abre o espaço para cenário/objeto, apoio e percurso preparam a
> revelação, e xícara permanece visível enquanto cede espaço ao retorno da
> gravação. Evite cartela de espera sem ação e intervalo vazio no retorno. Use a
> direção e a matriz de preservação; não redesenhe toda a peça. A moldura da
> abertura é escolha desta comparação, não regra para outros Reels. Não gerar
> nova imagem nem acrescentar música. O material reutilizado é ilustração
> conceitual, não fotografia documental do produto.

**Lacuna:** a tradução do pedido em direção foi feita pelo assistente; esta prova
não qualificou “cliente fala → sistema entende → monta esse briefing”.
Fonte: docs/evals/brief-cafe-pausa-recuperacao-2026-11-11.txt e script da rodada.

### 1. API: o que chamamos e recebemos

Chamada: POST /api/v1/organizations/{tenant_id}/businesses/{business_id}/motion-requests.
O harness usa httpx.ASGITransport e sessão autenticada, executando a rota FastAPI
real em processo. Não é acesso via interface/WhatsApp nem chamada manual ao modelo.

Entrada: MotionRequest com operation_id, instruction, source_asset_id,
format="reel", storyboard=true, repertoire_id="business-reel-v2", scene_direction
e evolution (base histórica, preservações e imagem reutilizada). A gravação já
estava armazenada; o POST recebe seu ID. Não houve novo upload nessa etapa.

Código: app/api/v1/motion_requests.py::request_motion →
MotionRequestService.create → MotionContext.capture. Verifica qualificação,
acesso, consentimento e configuração; captura fonte elegível, kit, contexto,
referências selecionadas, base e versões dos contratos. Persiste snapshot
cifrado/fingerprint em motion_requests, vínculos de assets, auditoria/outbox.
Idempotência usa operation_id; corpo diferente na mesma operação é conflito.

Retorno real: HTTP 202, state="queued", piece_id=null, failure_code=null,
id=2d6bc06c-d12e-5cac-afc8-66667f872dae,
operation_id=fe846b46-45a2-4fbe-8e6e-acd6e1e88051.
Artefatos: request-body.json, request.json e snapshot.json na pasta da rodada.

**Lacuna:** snapshot íntegro não valida qualidade da direção nem seleciona todo
acervo automaticamente. A captura mantém as escolhas já feitas.

### 2. Outbox e Temporal

dispatch_once → _start_workflow → MotionProductionWorkflow →
activity run_motion_production → MotionActivities.run → MotionOrchestrator.run.
A activity tem maximum_attempts=1. O evento carrega identidades; mídia/prompts
não são colocados integralmente no histórico do workflow.

MotionRequestService.begin verifica evento/admissão/fonte corrente e reivindica
a execução. O orquestrador abre o snapshot e prepara inputs. O caminho normal
neste modo deveria retornar awaiting_storyboard; a execução terminou em falha.

**Lacuna:** plano, materiais e implementação estão encadeados dentro da mesma
activity; não há espera humana entre plano e código nesse fluxo.

### 3. Mídia, repertório e base: preparação local

MotionInputLoader.prepare(snapshot) lê arquivos via MaterialStore, confere hashes,
inspeciona mídia, carrega fontes/runtime/repertório, prepara amostras com FFmpeg
e incorpora a base/material reutilizado. Retorna PreparedMotionInput com contexto,
assets, source_frames, asset_previews, reference_images, baseline_frames e áudio.

Nesta rodada: fonte 360×640 com 11.176 ms; saída 720×1280/30 fps/11.200 ms.
Quatro assets de execução: MP4, duas fontes e PNG da xícara. Evidência visual:
seis quadros da fonte, vinte da base, cinco referências e um preview da xícara.
Áudio preparado: assets/source.mp4, offset 0, trim 0–11176, volume 1; sem SFX extra.

**Lacuna:** vídeo completo está no executor, mas a chamada visual do modelo
recebe apenas amostras. Seis quadros uniformes podem omitir gestos/preparações.

### 4. Reconhecimento da fala: chamada local, não Responses

MotionSpeechRecognition.prepare registra o efeito speech:0 e chama
LocalMotionSpeech.transcribe. FFmpeg extrai PCM mono 16 kHz; subprocesso
app.adapters.motion_local_speech_worker usa faster_whisper local, CPU/int8,
word_timestamps=True, temperature=0, sem download remoto.

Retorno real: engine 1.2.1, idioma pt, trinta palavras com início/fim/confiança.
Exemplo: Feche, 0,00–0,38 s, confiança 0,9310. recognized_timing converte para
MotionSpeechTiming com IDs word-1 etc. e milissegundos. speech_context acrescenta
texto/cues/regras. Proveniência: local_asr_unreviewed.

Transcrição retornada: “Feche os olhos por um segundo. Sinta o cheiro. É hora de
uma pausa. Venha experimentar o momento só seu, café, calma e carinho. Pausa na
nossa cafeteria. Te esperamos.” Não é transcrição certificada por escuta humana.

**Lacuna:** palavras/timestamps não descrevem prosódia, ambiente nem eventos
sonoros. A próxima chamada não recebe o áudio para ouvir.

### 5. Primeira chamada generativa: plano

construct_motion_with_assets → _construct_motion cria MotionModelRequest sem
construction_plan. MotionEffects.model → OpenAIMotionProvider.build_request →
POST https://api.openai.com/v1/responses/input_tokens → validação de custo →
efeito/reserva duráveis → POST https://api.openai.com/v1/responses.
IO ocorre fora de locks de transação. O modelo não executa ferramentas nessa
chamada; o código do produto controla a sequência.

Parâmetros: model=gpt-6.1-sol, reasoning.effort=high, max_output_tokens=54000,
store=false. Payload contém instructions, JSON Schema de saída e uma mensagem
input com blocos de texto e imagens. Não inclui toda a conversa com o titular.

| Campo do texto estruturado | Conteúdo/regra |
| --- | --- |
| authorized_context.request | Brief, direção preparada e parâmetros de evolução |
| skill, kit, preferences, confirmed_facts | Skill v13, identidade, contexto; fatos confirmados vazios na captura |
| creative_contract | Direção, visibilidade, movimento, elementos e política temporal |
| generation_contract | Plano/código separados; representação compacta dos beats |
| executor_contract | Capacidades e limites do renderer |
| review_contract, correction_contract | Regras futuras; presença não executa crítica |
| repertoire, styles | Seleção de acabamento e exemplos |
| transcript, speech_result | Texto/cues do ASR com ressalvas |
| authorized_audio, available_materials, source, output | Material, áudio permitido e perfil |
| historical_baseline | Composição histórica sem HTML/JS e obrigações de comparação |
| assets | IDs, tipos e hashes; vídeo/fontes são arquivos do executor |
| construction_stage | plan |
| current_composition, previous_composition, critique | null; base histórica está no campo próprio |

Anexos: cinco referências, um preview da xícara, seis quadros da gravação e vinte
da base. reference_context do negócio estava vazio na captura; isso é distinto
do repertório Maestros presente. Não houve busca nova de referência.

Retorno real HTTP 200: concept, source_usage, audio, illustrations=[] e
motion_plan. Sem HTML, vídeo ou nova direção. Conceito literal:

> Preservar a abertura e evoluir apenas as passagens: a gravação entrega seu
> espaço ao cenário, percurso e superfície preparam a chegada da mesma xícara,
> e o objeto cede espaço ao vídeo corrente sem desaparecer.

| Cena retornada | Intervalo | Mensagem | Elementos |
| --- | --- | --- | --- |
| tempo | 0–4220 ms | Sinta o cheiro. | 5 |
| cafe | 3680–9060 ms | Uma pausa. Café, calma e carinho. | 6 |
| pausa | 8440–11200 ms | Te esperamos. Café Pausa — Saiba mais. | 7 |

A sobreposição temporal serve às passagens. O plano detalha estados, curvas,
ações e relações. decode_construction_plan expande o formato compacto e reinsere
a direção fornecida. plan.json é saída normalizada, não o JSON literal do modelo.

Uso registrado: 55.211 tokens de entrada/10.986 de saída; estimativa US$ 0,247888.
Entrada integral: planning-input.json e planning-input/PROMPT-INTEGRAL.md.
Saída literal extraída: .local/evals/motion-stage-audit-20261112/plan-model-output.json.

**Lacuna:** validação estrutural e fidelidade não avaliam suficiência artística
da direção. O resultado ecoa o escopo restrito; não houve revisão humana do plano
antes da chamada seguinte.

### 6. Materiais antes da implementação

validate_declarations verifica assets/plano e a igualdade do áudio original.
MotionIllustrations.prepare trata a lista de ilustrações, vazia nesta rodada.
A imagem antiga já estava carregada: nenhuma imagem nova foi gerada.
prepare_implementation_materials confere PNG/hash/dimensões/transparência,
prepara preview até 512×512 e acrescenta implementation_materials ao contexto.

**Lacuna:** valida disponibilidade/identidade, não adequação artística; não cria
geometria 3D a partir de PNG nem seleciona SFX por significado.

### 7. Segunda chamada generativa: implementação

Repete contagem de tokens, reserva e Responses. Entrada contém contexto, assets
e evidências, agora com validated_plan, plan_sha256, implementation_materials e
construction_stage="implementation". O produto reenvia explicitamente o plano;
não depende de memória de chat. O contrato permite requires_plan_revision se
a implementação exigir mudança de plano.

Retorno real HTTP 200: plan_sha256, status="implemented", html, scene_init,
revision_reason. HTML com 7.537 caracteres; JS com 9.089. O adapter confere hash/
status e incorpora o plano preservado em HTMLMotionComposition. O serviço confere
igualdade dos metadados. composition.json é a composição normalizada.

Uso: 63.607 tokens de entrada/16.120 de saída; estimativa US$ 0,320218.
Entrada: implementation-input.json. Saída literal extraída:
.local/evals/motion-stage-audit-20261112/implementation-model-output.json.

**Lacuna:** implemented não é parecer de qualidade. Não ocorreu crítica de
movimento/som entre plano e código; a fidelidade também preserva concepção fraca.

### 8. Storyboard: render realizado, persistência falhou

MotionStoryboards.capture seleciona momentos v3 e monta RenderBundle: HTML, JS,
assets, áudio, hashes das bibliotecas e frames_only=true. IsolatedMotionRenderer
executa Node/Chromium/Playwright em contêiner sem rede; window.seek(ms) posiciona
composição e gravação antes das capturas.

Retorno: vinte quadros e diagnósticos, sem MP4. O serviço registrou o recibo e
iniciou uploads. A versão executada colidia identidades de uploads de amostras
na mesma cena: MOTION_EFFECT_ALREADY_CLAIMED. Pedido failed; sem storyboard
persistido ou piece_id. A correção atual do helper não altera esse fato histórico.

Recaptura posterior, sem modelo, falhou em MOTION_RECAPTURE_PIXELS_CHANGED.
Diagnóstico: 19/20 hashes iguais, diferença em 2.800 ms não localizada visualmente.

**Impacto:** aprovação → produção → crítica normais não foram atingidas.

### 9. Caminho do MP4 entregue: avaliação separada

Após autorização do titular, render_preview.py conferiu composição recebida,
assets/áudio e criou operação Temporal de avaliação. Usa workflow/activity
existentes com runner Preview, que chama o renderer diretamente; não chama
MotionOrchestrator.produce nem promove o pedido falho para aprovado/concluído.

O renderer executa window.seek a 30 fps; FFmpeg codifica H.264/AAC e verifica
a saída. Retorno: MP4 720×1280, 11,2 s, 336 quadros, 1.242.383 bytes, vinte
amostras e diagnósticos; apenas áudio original. SHA-256:
e4bfabe68500189d6cd147f440f8ef4f2bccabd6e3001dff08cebf9e7e5d47f0.
Sem novo código, imagem ou chamada paga.

**Impacto:** é o arquivo apreciado pelo titular, mas não demonstra conclusão
normal do fluxo de produção e revisão persistido.

### 10. Caminho implementado que não foi executado nessa rodada

Após storyboard persistido aprovado, /storyboard/decisions emite
motion.storyboard_approved; novo workflow chama resume → produce.
produce renderiza, pede crítica ao modelo, valida revisão e seleciona candidata.
Se houver problema corrigível, escopo e orçamento, chama correção, renderiza,
compara regiões protegidas e pede nova crítica. Só candidata elegível permite
complete. Nesta rodada: zero chamadas de crítica/correção e nenhum complete normal.

Não atribuir à prévia entregue um ciclo de crítica que não ocorreu. Crítica de
imagens/métricas também não equivale a escuta da peça.

### Evidências, limites e próximos pontos de decisão

| Fronteira | Lacuna verificada | Impacto |
| --- | --- | --- |
| Cliente → pedido | Brief/direção do assistente e entrada direta por API | Entendimento natural não qualificado nesta rodada |
| Mídia → modelo | Amostras e ASR, sem percepção contínua/escuta | Informação temporal/sensorial limitada |
| Referências → modelo | Seleção de trajetória | Trechos pertinentes de luz/câmera ausentes das imagens |
| Direção → plano | Direção fixa reinserida pelo servidor | Concepção restrita pode ser executada fielmente |
| Plano → código | Avanço automático | Falta revisão intermediária antes do próximo gasto |
| Código → storyboard | Upload/recaptura falhos | Aprovação persistida não atingida |
| Prévia → conclusão | Runner de avaliação sem crítica/seleção normais | Qualidade do fluxo completo ainda não demonstrada |

Foram duas chamadas generativas e duas contagens remotas de tokens. ASR/render
locais. Estimativa somada US$ 0,568106; reservas US$ 2,50 incertas no registro,
sem fatura confirmada. Nenhuma dessas chamadas foi repetida nesta auditoria.

Validação: respostas literais extraídas dos recibos, campos confrontados com
saídas normalizadas e dois hashes dos payloads originais conferidos. Recibos
normalizados reordenam chaves: o hash de wire foi calculado dos payloads originais,
não da sua reserialização ordenada. Evidência:
.local/evals/motion-stage-audit-20261112/technical-chain-evidence.json.

Somente análise/documentação e extração local de evidências; sem código de
produção alterado, acesso a banco, serviços iniciados ou nova validação criativa.
Persistência, CI e revisão audiovisual permanecem pendentes.

---

Data: 12/11/2026. O titular pede acompanhar a geração e comparar, ao final de
cada etapa, pedido, entrada efetiva, saída, lacunas e impacto na próxima etapa.
Essa prioridade antecede a hipótese de aprimorar uma janela de 4–5 segundos.
O trabalho mantém a arquitetura e as capacidades já implementadas.

## Entrega atual e limites

Primeira entrega: auditoria da entrada da rodada recuperada de 11/11, usando
artefatos da execução real. Não é uma nova geração nem uma nova admissão no banco.
Pedido e direção não foram editados. Nenhuma chamada paga, asset, render, acesso
a banco ou serviço iniciado. Orçamentos anteriores não autorizam a próxima rodada.

Foi executado `OpenAIMotionProvider.build_request` com o contexto arquivado,
materiais e amostras verificados, por `offline_provider` com transporte que rejeita
rede. A reconstrução é semanticamente igual ao payload executado. A ordem das
chaves do contexto exportado muda a serialização dos blocos de texto JSON; por
isso não se declara igualdade dos bytes reconstruídos. Separadamente, o hash do
payload original corresponde ao recibo arquivado do efeito executado:
`29c04a093a4ded536774e31f5186b1ba6da6ddd9154c6efee5ed119e7a8430c0`.

Evidência local: `.local/evals/motion-stage-audit-20261112/stage-1-evidence.json`.
Origem: `.local/evals/motion-recovery-run-20261111/`, especialmente
`request-body.json`, `snapshot.json`, `planning-input.json`, `planning-input/`
e recibo `effects/366177c7-a063-5342-bf3e-0f8ba7450c72.json`.

## Pontos de conferência do processo existente

| Ponto | O que comparar antes de continuar |
| --- | --- |
| Pedido e contexto | Intenção e requisitos vigentes → brief/direção preparados → entrada real: skill, kit, referências, fonte, transcrição, base e materiais |
| Direção e plano | O que foi solicitado → decisões espaciais, temporais e sonoras; substituições, restrições herdadas e hipóteses sem evidência |
| Materiais | O que o plano exige → arquivos disponíveis/resolvidos e previews; qualidade, origem e adequação, incluindo som; material reaproveitado já pode estar na primeira entrada |
| Implementação | Plano e materiais efetivamente enviados → código/ações produzidos; fidelidade não implica bom acabamento |
| Storyboard e audiovisual | Código → estados capturados → movimento e áudio; storyboard continua anterior ao MP4, PNG não aprova som/fluidez |
| Crítica, correção e seleção | Problema observado → correção delimitada → comparação com a base e resultado completo; manter evidência de regressões e limitações |

Em cada ponto: pedido, regras e sua origem/alcance, entrada efetiva, saída,
mantido/transformado/ausente, evidência, lacuna, impacto seguinte e recomendação.
Uma hipótese deve permanecer rotulada como hipótese. Ausência intencional,
não seleção, perda na transferência e limitação de representação são casos
diferentes; não tratar todos como bug. Validar com o titular antes de avançar
conforme o acompanhamento solicitado, sem repetir etapas já aceitas.

**Lacuna operacional confirmada:** `motion_construction._construct_motion`
encadeia plano validado → materiais → implementação dentro da mesma execução.
O `MotionOrchestrator.run` só retorna `awaiting_storyboard` depois da composição
e captura. Portanto, as divisões internas não oferecem hoje parada humana entre
plano e implementação. Antes da nova execução acompanhada, será necessário
habilitar interrupção/retomada durável nesse limite usando o fluxo existente,
sem perder recibos ou repetir chamadas. Esta auditoria não implementou essa
mudança nem demonstrou que novos serviços/tabelas sejam necessários. Exportador
offline serve para conferir entradas, não para contornar o fluxo do produto.

## Primeira conferência — pedido e contexto da rodada anterior

**Pedido de origem:** recuperar/evoluir as qualidades das peças indicadas pelo
titular, preservando gravação, voz e kit, com ações coordenadas e sem transformar
exemplos em regras universais. A rodada delimitou reutilização da imagem e áudio
original. Feedback posterior pede riqueza gráfica/sonora e investigação do fluxo;
ele não fazia parte da entrada histórica e ainda precisa de tradução para uma
nova entrada, sem alterar os recibos antigos.

**O que foi produzido pela preparação:** um brief e uma direção fixa de três
cenas. O brief pede preservar abertura e a mesma imagem, concentra a alteração
nas passagens e diz “não redesenhe toda a peça”. A direção detalha moldura e
representação da xícara. São escolhas da comparação, não normas gerais. A
igualdade entre pedido arquivado, snapshot e request enviado foi verificada;
a direção enviada coincide com o documento de recuperação. Não houve perda
desses campos na serialização até o modelo.

| Informação/recurso | O que realmente chegou | Lacuna e possível efeito no plano |
| --- | --- | --- |
| Skill e kit | `instagram-reel-v13`, kit confirmado, três fichas de estilo | Presentes; uso adequado ainda precisa ser verificado na saída. Presença não prova aplicação |
| Repertório | `business-reel-v2`, cinco imagens: Maestros em 80/84/88 s e Lucas em 3/5 s, com regras/exemplos | A seleção Maestros privilegia trajetória. Não fornece as imagens de luz/câmera identificadas como pertinentes na revisão anterior |
| Gravação | Seis PNGs em 0/2235/4470/6705/8940/11076 ms e metadados | Amostragem uniforme pode perder gesto/preparação/contato. MP4 completo está no executor, não na percepção do modelo |
| Voz | Transcrição e cues `local_asr_unreviewed`; áudio preservado para mixagem | O modelo desta chamada não ouve prosódia, sons ambientes ou líquido. Precisão de sincronia não é validada pela existência de timestamps |
| Base histórica | Composição em `historical_baseline` e vinte quadros | O vínculo antes ausente foi recuperado. Amostras não representam integralmente movimento/som; não confundir `previous_composition=null` com ausência da base histórica |
| Xícara | PNG reutilizado, hash verificado, um preview e um material disponível | A aparência realista está disponível; movimento volumétrico não é consequência automática de uma imagem. Adequação ao novo plano precisa ser decidida |
| Acervo selecionado | Zero fotos de coleção selecionadas além do material reutilizado | Não prova acervo vazio nem recurso desativado. Não foi feito inventário atual do acervo nesta auditoria |
| Referências do negócio | `selected=[]`, `learnings=[]`, `reference_context=[]` no snapshot e na entrada | Não há perda demonstrada nesse trajeto: já estavam vazios na captura. É outro canal, distinto do repertório Maestros presente |
| Complementos sonoros | Zero eventos; apenas fonte original | Escolha delimitada da rodada. Impede esperar efeitos novos dessa entrada; feedback posterior requer seleção e material próprios |
| Direção fornecida | Igual ao documento de recuperação e protegida por fidelidade | Hipóteses do assistente já fixadas limitam a exploração. Corrigir a direção antes de construir; não retirar a proteção para permitir mudanças silenciosas |

**Conclusão desta etapa:** não foi encontrado descarte genérico de skill, kit ou
repertório. Há redução de percepção (quadros sem vídeo/escuta), seleção limitada
de referências e direção prescritiva antes do plano. São mecanismos concretos
que podem limitar o resultado; ainda não atribuem causalidade exclusiva a cada
defeito visual. A transmissão íntegra de um contexto insuficiente continua
produzindo um contexto insuficiente.

**Antes da próxima geração:** revisar a tradução do feedback para o pedido;
conferir se as referências/amostras cobrem a ação e o acabamento pretendidos;
explicitar o que será ouvido/verificado fora da chamada visual; resolver o ponto
de parada entre plano e implementação. Apresentar entrada preparada e proposta
de orçamento nova antes da chamada paga. A prévia atual apreciada permanece
como referência de resultado, com sua pendência de persistência explícita.

## Estado e validação

- Conferência 1 entregue para revisão; não é aprovação do contexto da próxima peça.
- Reconstrução local sem rede: conteúdo estruturado e anexos iguais aos da
  entrada histórica; hashes dos quatro assets e 32 imagens conferidos; hash
  original compatível com recibo; pedido preservado até a entrada.
- Nenhum teste de runtime, CI integral ou novo aceite audiovisual declarado.
  Documentação conferida com `git diff --check`.
- Conferências seguintes não executadas nesta entrega; nova execução, orçamento,
  parada intermediária, persistência e validação visual/sonora permanecem pendentes.
