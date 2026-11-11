# Resultado do refinamento criativo do Giz — 09/11/2026

O ensaio real terminou `completed_human_pending`, com original e v1 preservados.
Foram duas chamadas HTTP 200, sem reenvio, operação incerta ou reparo visual
manual. A crítica comparativa preferiu v1, retornou `adequate`, marcou os três
requisitos `met`, seis critérios `pass` e áudio `uncertain`, sem achados.
Em resposta à entrevista sobre motion/narrativa, o titular afirmou **“B ficou
melhor.”** O QA e a validação técnica do CI foram concluídos. Com a melhora de
legibilidade reconhecida no 1c, **a etapa 3 está concluída no recorte provado**.
A preferência por B não constitui aceite isolado de todos os critérios ou do
áudio, nem generaliza qualidade/custo para outros pedidos. Integração do Reel
(4) e demais formatos (5) são os próximos trabalhos já autorizados, ainda não
concluídos.

[Comparação privada A/B](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/report.html) ·
[Original](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/giz/v0/render.mp4) ·
[Refinamento v1](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/giz/v1/render.mp4).

Run: `1c758136-7530-43d8-96b7-39e4b0e44888`. O
[plano](plano-refinamento-motion-giz-2026-11-08.md) conserva hipótese, preparo,
qualificação, pedidos e autorização. O titular autorizou até duas chamadas e
US$ 1,25 em 09/11, em decisão específica do Giz, sem transferir outros tetos.

## Feedback humano recebido e alcance da conclusão

Resposta exata: **“B ficou melhor.”** Entrevista
`call_3e1d59720b1b4daabd16fcb8cfd27982`, item 0, sobre a comparação de motion/
narrativa A/B. O [registro privado](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/human-feedback.json)
foi acrescentado em arquivo exclusivo/somente leitura e tem SHA-256
`cdfabf43a8b4378eddb4cb1cdcde9dee55a31941a3f51bdd834338d3ee47f924`.
Ele vincula A/v0, B/v1, relatório e summary aos hashes conferidos. Vídeos,
crítica, relatório e summary não foram alterados; o status automático
`completed_human_pending` continua como registro do momento anterior ao feedback.

A conclusão da etapa 3 combina duas evidências delimitadas: reparação de
legibilidade do 1c e refinamento criativo do Giz reconhecidos pelo titular.
O Giz recebeu feedback e referência novos; não prova que a autocrítica teria
encontrado um erro no pedido original. Não foi dada aprovação separada de
áudio, de cada critério, de publicação, de todo formato ou de economia geral.
A preferência humana autoriza cumprir a sequência de implementação já
combinada, sem ampliar orçamentos ou representar integração concluída.

## O que foi comparado

O baseline é o Giz `15adf19d-6edb-4073-9857-bd11684e4162`, do lote de diversidade.
Ele já possuía desenho, escrita, apagamentos e movimento; não foi demonstrada
violação inequívoca de seu briefing original. A revisão recebeu o feedback
humano posterior e seis quadros de Intensa como contexto adicional declarado.
V2 não foi enviada visualmente ao modelo. Portanto, o experimento mede
**refinamento guiado por feedback e referência nova**, não descoberta autônoma
de um defeito do pedido inicial. Não houve crítica paga inicial redundante.

| Requisito do briefing atualizado | Evidência observada e limite |
| --- | --- |
| `theme_change` | Área editorial verde → creme → verde, mantendo rodapé verde, gravação e paleta. A crítica identifica distinção entre pergunta, momento sensorial e convite. |
| `window_transformation` | Janela retangular transforma-se em arco e retorna ao retângulo elevado. Máscara interpolada entre 2,582–3,182 s e 8,053–8,753 s; quadros mostram estados intermediários. |
| `narrative_role` | Escrita, traços e apagamentos do Giz acompanham pergunta → sensações → convite. A crítica identifica função editorial das transformações, sem certificar o ritmo do vídeo completo. |

As inspeções locais observaram leiteira, fio de leite e xícara reconhecíveis.
O arco recorta um pouco mais a extremidade da mão superior/esquerda; não foi
observado corte da ação principal nas amostras. Essa observação não certifica
cada instante do vídeo nem substitui a avaliação do titular.

A [crítica final](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/giz/v1/critique.json)
associa cada requisito a evidências de A/B e referências. Fatos, marca,
legibilidade, composição, motion e técnica receberam `pass`; áudio permaneceu
`uncertain`. `adequate` significa ausência de outro defeito acionável nas
evidências avaliadas, não aprovação criativa global. A preferência automática
por v1 era provisória; o feedback posterior confirmou a preferência comparativa
por B. A aprovação de publicação e a qualificação da integração continuam sendo
etapas distintas.

## Inspeções e integridade

A [inspeção de código](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/inspection-code.json)
conferiu HTML byte a byte igual ao baseline, dois avisos MIT, fontes, seis
assets admitidos, créditos, textos hero/CTA, sete legendas, paleta e plano de
áudio. A alteração está no inicializador visual; não houve nova mídia, inclusão
de pixels das referências ou reparo manual. Isso é inspeção concreta do código
recebido, não garantia geral de invariância textual pelo schema HTML/JS livre.

A [inspeção do artefato](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/inspection-artifact.json)
conferiu amostras A/B, estados intermediários, convite e créditos. A impressão
de corte no rodapé foi investigada com pares e comparação de pixels; não foi
confirmada como regressão. A análise não é OCR nem prova perceptual. Código e
artefato foram inspecionados antes da segunda chamada; as aprovações locais
admitiam render/comparação, sem substituir aceite criativo humano.

- Original SHA-256: `230921ac23f714dcaa90c2d16b65dfbf5246d1c8d6b601d5af56695e52e58eb6`.
- V1 bruta SHA-256: `868c1ce885f2d45ee780acb545b3b4640b5ad1488f7b7e26afcb3fb921eab079`.
- V1 final SHA-256: `9c2bb1708aea9dfc708ad98c2c44372d7bca5b18c2269d9fd9652910cf26c32e`.

A [proveniência](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/giz/v1/render-provenance.json)
distingue MP4 bruto/trace e final. O final copia o AAC do baseline sem recodificar
vídeo. A [prova de áudio](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/giz/v1/audio-preservation.json)
confirma 176 pacotes AAC, tempos e PCM idênticos. Não houve escuta; identidade
técnica não qualifica a mixagem, sincronização percebida ou qualidade da voz.

O MP4 final tem 720×1280, 30 fps, 336 quadros e 11,2 s; decodificação passou.
Os 20 ms além dos 11,18 s nominais já existiam no arredondamento do baseline.
O trace não registrou requisições negadas, e os assets foram conferidos.

## Custos e tempos

| Operação | Identidade | Resultado | Estimativa de API | Tempo |
| --- | --- | --- | --- | --- |
| Refinamento | `f14f52de-131f-4068-8a12-506e7ae5aa8b` | HTTP 200; composição validada, inspecionada e renderizada | US$ 0,3844100 | 312,398 s |
| Comparação | `daa3ed0a-0844-40f6-9037-2330456cc1f8` | HTTP 200; crítica válida, preferência provisória por v1 | US$ 0,2638475 | 79,164 s |

Estimativa incremental: **US$ 0,6482575**. Histórico da geração original Giz:
US$ 0,2203975. Subtotal de APIs: **US$ 0,8686550**, sem fatura, COGS completo
ou custo por peça aceita. A operação Papel incerta do lote histórico não foi
repetida, reconciliada nem incorporada como custo conhecido deste caso.

Reservas nominais: US$ 1,00 (US$ 0,75 + US$ 0,25). O uso estimado da comparação
excedeu sua reserva em US$ 0,0138475; comprometimento registrado de
US$ 1,0138475, ainda dentro do teto autorizado de US$ 1,25. Não há operações
incertas nesta execução. Reserva, comprometimento e estimativa de uso são
medidas diferentes.

APIs: 391,562 s. Render e extração de evidências: 92,310 s.
**Subtotal medido: 483,872 s**, excluindo qualificação, preparação, inspeções,
intervalos, trabalho humano e infraestrutura. Não é tempo total da tarefa,
SLA de produto ou custo faturado. Fontes: [summary](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/summary.json)
e [ledger](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/ledger.jsonl).

## QA real do relatório e apresentação ao titular

O [QA de navegador](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/report-qa-2026-11-09T12-18-27-787Z-79549e/qa.json)
passou: 390/1440 px, modos cego/identificado, oito reproduções mutadas completas
de 11,2 s e sete links por vista com resposta HEAD 200. Não houve overflow,
erro JavaScript/console/HTTP ou requisição externa. Três leituras locais de
mídia canceladas com `ERR_ABORTED` foram registradas separadamente; todos os
players chegaram ao fim. Os 248 arquivos conferidos antes/depois conservaram
seus hashes, e 12 screenshots documentam as vistas.

QA SHA-256: `1d6d7f33acfca8a9d9619eeec451683dd8f875b04655f7507281b00e982747d3`.
Relatório SHA-256: `753721817bfd70de7f8f70e83f19ee9aa1991b35ff7fd2a2668531a2b34c63ec`.
A primeira tentativa de QA falhou com `EPERM` antes de abrir o navegador e foi
preservada. A execução local seguinte passou com o mesmo script. Não houve
nova API ou alteração das peças por esse QA.

As vistas de B a 390 px e do modo cego a 1440 px foram inspecionadas; o relatório
foi aberto no navegador local e a entrevista enviada com link explícito.
A resposta posterior “B ficou melhor.” está registrada acima. Reprodução
mutada comprova funcionamento da apresentação/decodificação; a preferência
criativa vem da resposta humana, sem presumir escuta ou aceite de áudio.

## Limites e próximo gate

Quadros amostrados e código não comprovam o movimento completo. Os tempos
são buscas solicitadas, não PTS medidos. As referências da Intensa são quadros
históricos anteriores ao encode, úteis para orientar características, sem
provar equivalência temporal. O novo contrato separa presença de movimento do
atendimento aos três requisitos; uma avaliação favorável não o calibra para
todos os estilos, negócios ou formatos.

O QA passou e o titular confirmou preferência por B na entrevista de motion/
narrativa. A etapa 3 está encerrada nesse recorte, junto com a evidência de
legibilidade do 1c. Isso não permite inferir uma verificação humana isolada de
cada critério, escuta/mixagem aprovada, benefício geral da revisão automática
ou retorno financeiro geral. Cada entrega integrada exigirá sua qualificação.

A [validação técnica final](../../.local/ci-20261108/ci-final-result.json)
foi concluída: `make ci` exit 0, 5.043 testes aprovados e dois pulados por falta
de FFmpeg/FFprobe no PATH. Os mesmos dois testes reais de MP4 passaram
separadamente em 4,97 s após ajuste somente do PATH privado para FFmpeg 9.0/
FFprobe 4.4.8. Não houve alteração de produção ou dos testes para essa execução.
Cobertura da aplicação: 17.229/17.229 linhas e 4.726/4.726 branches, 100%.

Também passaram 363 testes Python motion, três Node de áudio, 62 Node do
renderer (100% linhas/branches/funções), Ruff/formatação e mypy de 272 módulos
app mais oito scripts. Os 735 arquivos app/migrations e 29 arquivos do
laboratório ficaram iguais aos snapshots. Os recortes anteriores não devem
ser somados a esses resultados. Logs sem credenciais e falhas anteriores em
recibo/token foram preservados como histórico.

Foram 69 amostras de relógio sem sinal de repouso: diferença total de −0,048 s
em 1.114,6 s. A disponibilidade do Mac não bloqueia mais esta execução concluída.
O PostgreSQL descartável usou `fsync`, `synchronous_commit` e `full_page_writes`
desligados apenas no CI. Isso não qualifica durabilidade sob perda de energia
ou recuperação de falha do servidor; requisitos de produção permanecem próprios.

QA, validação técnica e preferência humana registrados. Prosseguir com a
implementação já autorizada do Reel (4) e depois demais formatos (5), em fatias
qualificadas; a integração ainda não está concluída. Intensa,
Dog e Luma permanecem referências já avaliadas. A confirmação de legibilidade
do 1c e seus custos continuam separados deste refinamento.
