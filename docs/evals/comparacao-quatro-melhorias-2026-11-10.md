# Comparação das quatro melhorias — três tentativas sem MP4

O titular autorizou preparar/iniciar uma nova comparação Café Pausa e respondeu
à entrevista autorizando teto exclusivo de US$ 4. Os orçamentos anteriores não
foram reutilizados. Reservas máximas US$ 3,30: composição 1,40, uma imagem 0,50 e
crítica 1,40. Sem refações, tentativas extras ou publicação. Pedido admitido pela
API e despachado no Temporal; tentativa falhou sem MP4. A primeira admissão recebeu
401 pela sessão expirada do usuário sintético: nenhuma chamada paga ocorreu ali.
Uma sessão exclusiva desse fixture foi aberta pelo serviço de autenticação, com
auditoria e logout ao terminar a admissão; contas/sessões reais não foram alteradas.

Mesma gravação/voz/kit, moldura e aproximação, fundo narrativo, alternância com
motion pleno, xícara conceitual fotográfica em camadas 2.5D e ações ligadas à fala.
A direção anterior foi adaptada: texto editorial sobre tempo não é tratado como
fala. Focos propostos: Sinta/cheiro, pausa, café e Pausa final. A imagem é conceitual,
não produto documental nem geometria 3D; depende de geração autorizada.

## Qualificação da transcrição

Instalado o extra opcional speech no venv local, sem reconstruir Docker. Modelo
público Systran/faster-whisper-small, revisão
536b0662742c02347bc0e980a01041f333bce120, provisionado separadamente. Bundle SHA-256
c176c33677afdaf71e808d4f365291928c28eadbd8e138204c68933569c26e9c.
A inferência local sobre a gravação existente levou 6,41 s e retornou 30 palavras.
Origem local_asr_unreviewed; não há validação humana nem garantia de exatidão.
Esta prévia não substitui o efeito durável da operação Temporal futura.

Duas incompatibilidades reais foram corrigidas antes de qualquer gasto: o bundle
precisa incluir vocabulary.txt/json além de pesos/tokenizer/config; o hash agora
inclui esse vocabulário. O faster-whisper 1.2.1 tenta passar metadata_errors ao
PyAV 19, que não aceita esse argumento. Agora reutilizamos diretamente o PCM mono
16 kHz já extraído pelo produto, com leitura limitada a 60 s e conversão float32;
não há segunda decodificação nem interpolação de tempos. WAV de pipe pode declarar
comprimento indeterminado: o limite se aplica aos bytes efetivamente lidos.

43 testes dirigidos passaram em 1,10 s, com 100% de linhas/ramos no worker de
transcrição. Ruff e Mypy aprovados. Testes de fundação usam PCM sintético e não
exigem NumPy/ASR opcionais; a inferência acima é qualificação separada. Sem CI global.

## Entrada e próximos passos

Pasta local: `.local/evals/reel-four-improvements-20261110/`. Brief, direção,
transcrição, plano de custo e relatório de preparação disponíveis. O pacote
`input-package/` foi gerado pelo montador do produto, com payload de 2.045.096 bytes,
seis quadros da fonte e seis imagens de referência. SHA-256 do payload:
ff34e96fa3e4c337677690ced228ba3935d6e8c43bc3dfbbcd13d7bc518d6dc4.
Tempos da prévia alimentam esse pacote, mantendo proveniência automática. A imagem
da xícara ainda não existe; a composição só pede sua geração e reserva espaço.

Preparação consultou Temporal e admissão sem criar pedido. Após autorização,
pedido 9a54464b-2eb3-5ad8-81c0-fd022eb47060 admitido; execução encerrada com falha. Configuração específica de
comparação, fila exclusiva e worker no host; cinco contêineres com parada mantida
por autorização anterior continuam parados. Nenhum volume removido. Executor verificado com quadro sintético 64×64, sem IA. Conferir após execução o MP4, áudio,
tratamento da gravação, objeto, fundo e sincronismo perceptível junto da versão
anterior. A qualidade visual permanece por qualificar.

## Resultado da tentativa autorizada

Workflow encerrou em 512,66 s, MOTION_AI_OUTPUT_LIMIT, zero versões. A resposta
reporta status incomplete/reason max_output_tokens, mas max_output_tokens=64000
na solicitação e resposta, input_tokens=34928 e output_tokens=25722, dos quais
15020 de reasoning. O JSON da composição tem 36245 caracteres e termina dentro
da string scene_init, sem fechamento. Não se trata de erro de renderização: a
composição não chegou completa. A contagem divergente não permite concluir por
que o provedor interrompeu a saída; não atribuir o resultado à qualidade do modelo.

Uma chamada paga, estimativa registrada US$ 0,34454; reserva US$ 1,40 mantida, sem
liberação manual. Imagem e crítica não acionadas. ASR efetivamente executado e
registrado como efeito durável com 30 palavras e custo zero. Worker exclusivo no
host encerrado; os cinco serviços previamente parados não foram reiniciados.
Executor passou em verificação sintética 64×64, mas não há nova peça comparável.

Evidências locais: result.json, workflow-result.json, failure-analysis.json,
incomplete-composition.txt e efeitos privados na pasta da rodada. Não executar
a composição truncada nem apresentá-la como resultado visual.

Recuperação preparada separadamente em
`.local/evals/reel-four-improvements-recovery-20261110/`: mesma direção, referências,
fonte, kit, transcrição e quatro melhorias; instrução adicional de reutilização
de funções/helpers e código compacto, sem relaxar contratos. Proposta de uma nova
composição, uma imagem e crítica: reservas US$ 0,75 + 0,50 + 0,75 = US$ 2,00; com
US$ 1,40 já retidos, acumulado máximo US$ 3,40 dentro do teto de US$ 4. Orçamento
acumulado conferido sem liberar reservas anteriores. O titular autorizou explicitamente a tentativa extra dentro dos US$ 4.
Recuperação executada pelo mesmo fluxo API/Temporal e encerrada com a mesma
falha; nenhuma nova tentativa autorizada. Resultado abaixo.

## Resultado da recuperação autorizada

Pedido a36e4d8f-2391-520e-bb50-07e7cb33d1fa: workflow terminou em 364,07 s,
MOTION_AI_OUTPUT_LIMIT, zero versões. Foi solicitada composição com instrução
adicional de funções/helpers e menos repetição, mantendo fonte, kit, referências,
direção e quatro melhorias. A mudança não resolveu a interrupção.

O provedor retornou status incomplete/reason max_output_tokens e JSON com 36.927
caracteres, cortado dentro de scene_init, durante a preparação do vídeo/imagem.
Solicitação e retorno indicam max_output_tokens=64000; usage registra 35.075 de
entrada, 19.856 de saída (8.804 reasoning), total 54.931. Na primeira tentativa
foram 34.928 de entrada e 25.722 de saída. Os corpos recebidos têm 216.240 e
325.612 bytes, respectivamente, abaixo do limite local de 4 MiB; scene_init admite
1 MiB. Nenhuma evidência de truncamento pelo limite de bytes local. A causa do
limite reportado pelo provedor permanece indeterminada; não afirmar esgotamento
numérico de 64.000 tokens nem atribuir falha à qualidade criativa do modelo.

Estimativa da recuperação US$ 0,286248; acumulado US$ 0,630788. Reservas somadas
US$ 2,15 (1,40 + 0,75) permanecem, sem liberação manual; não equivalem à fatura.
Imagem e crítica não foram acionadas em nenhuma das tentativas. ASR local com
efeito durável funcionou nas duas; não houve novo render ou avaliação visual.
Worker exclusivo encerrou normalmente; nenhum dos cinco serviços parados foi
reiniciado. Sem mudanças de produção ou nova bateria de testes nesta execução;
validações anteriores do worker/PCM permanecem registradas acima.

Evidências na pasta de recuperação: result.json, cumulative-result.json,
workflow-result.json, failure-analysis.json, incomplete-composition.txt,
request-body.json e input-package/. Aprovação específica em approval.json privado.
Nenhuma terceira tentativa autorizada. Antes de gastar novamente: investigar a
interrupção reportada e preparar uma redução verificável da duplicação plano/código
e do código de carregamento/seek, preservando contratos e recursos visuais. A
orientação textual de concisão sozinha foi insuficiente. Não remendar silenciosamente
a resposta incompleta para apresentá-la como geração bem-sucedida do produto.

## Continuação local após pedido do titular

Titular pediu continuar para obter a comparação ao retornar. Implementado e
verificado contrato compacto v2; detalhes em
`docs/design/motion-contrato-compacto-2026-11-10.md`. Nova entrada preparada em
`.local/evals/reel-four-improvements-compact-20261110/`, sem chamada paga.
Entrevista pendente para ampliar uma tentativa dentro do mesmo teto US$ 4;
reservas acumuladas propostas US$ 3,95. Nenhuma nova peça produzida ainda.

## Atualização — 11/11/2026

O titular autorizou explicitamente mais uma tentativa de composição, imagem e
crítica dentro do mesmo teto acumulado US$ 4. Execução do contrato compacto v2
iniciada; verificação durável das duas tentativas anteriores mantém reservas e
limita o acumulado proposto a US$ 3,95. Sem tentativa adicional além desta.
Execução encerrada com falha; resultado abaixo.


## Resultado do contrato compacto em 11/11/2026

Pedido 3f6f955e-6d62-50ea-b4f6-eeaea0ff86a3 admitido via API e executado no Temporal.
A checagem consultou efeitos anteriores no banco e confirmou reserva máxima
acumulada US$ 3,95 antes da admissão. Modelo e schema enviados: gpt-6.1-sol e
CompactProvidedDirectionOutput. Não houve troca silenciosa de modelo.

Workflow encerrou em 562,74 s com MOTION_AI_OUTPUT_LIMIT. Retorno incomplete /
max_output_tokens; 54.000 tokens de saída solicitados e retornados na configuração,
35.340 de entrada e 27.924 de saída reportados (18.425 reasoning), total 63.264.
JSON de 30.988 caracteres, cortado dentro de scene_init durante atualização do
percurso gráfico. Corpo HTTP completo e parseável de 383.298 bytes, abaixo do
limite local de 4 MiB. A resposta do provedor é que marca composição incompleta.
A compactação efetivamente foi enviada e reduziu a representação medida offline,
mas não solucionou a interrupção nem qualificou qualquer ganho visual. Causa do
limite reportado permanece indeterminada; não afirmar que se consumiram 54.000
tokens de saída nem atribuir o problema à qualidade criativa do modelo.

Estimativa desta tentativa US$ 0,367590; acumulado das três US$ 0,998378. Reservas
US$ 2,80 preservadas (1,40 + 0,75 + 0,65), sem liberação manual. Nenhuma imagem,
renderização da peça ou crítica foi acionada. A transcrição local foi registrada
como efeito durável, custo zero. Imagem do renderer confirmada disponível; cinco
serviços permaneciam parados na inspeção e não foram reiniciados. Worker exclusivo
encerrou ao concluir o workflow. Sem alteração de código de produção ou nova
bateria de testes nesta execução; verificações anteriores do contrato mantidas.

Pasta `.local/evals/reel-four-improvements-compact-20261110/`: result.json,
cumulative-result.json (três tentativas), cumulative-preflight.json,
failure-analysis.json, workflow-result.json e incomplete-composition.txt.
Não há MP4 novo para comparar. Não há quarta tentativa autorizada. Antes de
outro gasto: usar estes metadados para investigar o limite reportado e preparar
uma solução verificável de geração que não dependa de repetir a mesma saída
monolítica. Não remendar a resposta e apresentá-la como sucesso do produto.

## Análise posterior

**Análise das interrupções concluída, sem chamada paga adicional.** Retornos
reproduzidos offline no parser: corte em scene_init vem marcado pela API; limites
locais de bytes, orçamento e falta de anexos não explicam a falha registrada.
Identificados saída indivisível, ordenação alfabética do schema colocando código
após plano e reasoning=high fixo. A causa raiz do limite reportado continua sem
comprovação: uso abaixo do teto e dos limites públicos do modelo. Compactação de
20,87% não era prova de conclusão. Próximos passos documentados, não implementados.
Relatório: `docs/evals/diagnostico-interrupcao-motion-2026-11-11.md`.

