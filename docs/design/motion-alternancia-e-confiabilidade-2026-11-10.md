# Alternância narrativa e confiabilidade do Reel — 10/11/2026

O titular gostou mais da peça com interações, mas identificou a gravação sempre
visível como limite de composição. Autorizou duas fatias: permitir alternância
entre registro real e motion, corrigir recorte/crítica, e entregar comparação.
A geração da comparação tem autorização própria de até US$ 3, uma geração,
render e crítica, sem tentativas extras ou imagens pagas.

## Direção e compatibilidade

Novas capturas usam `instagram-reel-v6`, `html-motion-executor-v2` e contrato
criativo v6 (direção proposta) ou v7 (fornecida). Preservar duração, ordem e áudio
não exige uma janela de vídeo permanente. A direção escolhe por função narrativa:
gravação dominante, integrada ou coberta por composição gráfica inteira. Não há
percentual fixo, seleção automática de takes, alteração da fala ou edição longa.
O mesmo nó de vídeo recebe seek absoluto mesmo oculto; retorna no instante corrente.
Ações necessárias como evidência de um fato permanecem observáveis. Cobertura
planejada não deve ser confundida com recorte acidental. Texto editorial não
substitui transcrição alinhada, ainda ausente desta integração.

Capturas anteriores preservam executor, skill, contrato criativo, revisão e runtime.
Os contratos criativos v4/v5 e bytes de skills v1–v5 permanecem disponíveis. Nenhuma
migração, serviço, tabela, runner ou mudança dos controles financeiros.

## Causa do recorte corrigida no runtime

`movement-v1.js` escrevia `clip-path:inset(0)` em toda track, mesmo só para mover
um wrapper. Esse valor recorta descendentes transladados para fora da caixa do pai.
`movement-v2.js` só controla clip-path quando initial ou algum estado to declara
explicitamente clipTop/Right/Bottom/Left. Tracks sem esses campos preservam CSS
existente; não criam máscara. Até zero explícito significa máscara intencional.
Máscaras de líquido/texto continuam funcionando. API global continua MotionV1;
version passa a motion-movement-v2. Não se remove clipping globalmente.

O montador captura versão/hash. Renderer e exportador selecionam os bytes pelo hash,
sem promover composições antigas. A biblioteca business-reel-v1 permanece imutável;
o loader aceita também a combinação explicitamente testada com o runtime v2.
O nome `execution/libraries/movement-v1.js` do export continua como alias compatível;
a versão real dos bytes é a do contrato/manifesto, não a desse nome de arquivo.

## Crítica com vínculo explícito

Novas capturas usam `motion-review-v3`/`LinkedMotionReview`. Cada creative_check
tem issue_indices, índices base zero dos problemas que sustentam not_met. O serviço
inclui a evidência real desses problemas no check antes de aplicar as validações
existentes. Não tenta deduzir por texto se duas observações descrevem o mesmo defeito.

Links duplicados, inexistentes, de outro critério, com quadro inexistente ou de
source/previous são rejeitados. Met/uncertain não podem ligar problemas. Para
needs_revision, cada not_met liga problema major/blocking acionável. Mínimos de
quadros e sequências temporais permanecem; o vínculo não cria evidência temporal.
A crítica v2 antiga continua exigindo IDs exatamente compartilhados. Não há retry,
conversão de parecer inválido em aprovação nem reescrita de evidência histórica.

## Verificação

393 testes Python dirigidos passaram em 6,63 s; cobertura 100% linhas/ramos nos
serviços movement, review, creative, repertoire e schema review_wire. Dois casos
adicionais de compatibilidade foram exercitados na execução de 47 testes de
contexto/skills. 25 testes Node exercitam runtimes v1/v2, exemplos e repertório.
Ruff e Mypy dos dez módulos afetados passaram. Sem CI global ou testes SQL.

Dois quadros sintéticos no Chromium isolado reproduziram o recorte na v1 e sua
eliminação na v2, preservando a máscara explícita nas duas. Artefato privado:
`.local/evals/reel-alternancia-20261110/browser-clipping-check.json`. Checagem curta
do executor também passou. Isso prova o mecanismo, não o acabamento da peça.

Resultado real e limites em
[plano da comparação](../evals/plano-motion-alternancia-2026-11-10.md).

## Feedback adicional após o despacho — skill v7

O titular observou fundo constantemente clean/inativo e vídeo com tamanho fixo,
apenas reposicionado para acomodar a xícara. Novos pedidos passam a usar skill v7:
coordenação do quadro inteiro, função narrativa do fundo, variação pertinente de
moldura, escala, máscara, entrada/saída e enquadramento da gravação. Não exige
saturação, textura, agitação ou todos os efeitos em toda marca. Kit, ação legível,
leitura e limites dos materiais prevalecem. Crítica usa checks/evidências existentes.

A rodada já despachada permanece na v6; não foi alterada nem reenviada. V7 é um
ajuste de orientação posterior, **ainda sem prova visual paga**, e não muda runtime
ou schema novamente. 66 testes de contexto/skills/exportação e dois exemplos Node
passaram após o ajuste, incluindo recaptura v6. Não atribuir à saída da primeira tentativa
a realização de instruções que não estavam em sua entrada.


## Limite da prova real

A primeira geração (v6) foi completa, mas falhou por dois beats sobrepostos; a
recuperação autorizada (v7) veio incompleta. Não chegaram à crítica real. Os
consertos implementados não autorizam declarar geração automática qualificada.
A comparação local usa apenas o código completo da primeira resposta, com dois
intervalos descritivos do plano reunidos, sem alterar HTML/JS. A recuperação
parcial permanece sem execução. Custos e artefatos no plano do ensaio.

A comparação local também não concluiu MP4: limite de captura integral e timeout
do navegador na captura por trechos. Apenas três estados estáticos estão disponíveis;
não qualificam continuidade nem áudio. Investigar captura e cancelamento sem
relaxar isolamento/limites. O ensaio registra o encerramento e os artefatos parciais.
