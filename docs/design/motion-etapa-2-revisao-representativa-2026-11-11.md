# Motion — etapa 2: revisão e prévias representativas

Data: 11/11/2026. Implementação técnica da seleção e do storyboard; nenhuma
peça foi produzida, revisada por modelo ou aprovada nesta etapa. A decisão humana
do storyboard continua após a construção do código, antes do MP4 final.

## Seleção e limites

Novas capturas usam `motion-temporal-v2`; snapshots v1 continuam com a política
original. O limite permanece em três janelas e vinte quadros. A política reserva
janelas para passagens entre cenas e uma ação, escolhendo entre beats existentes;
prioriza imagens, vínculo à fala e proximidade do centro, sem inferir qual ação é
criativamente a mais importante. Passagens usam o intervalo de sobreposição das
cenas e uma margem anterior. As amostras são deduplicadas. Em peças com mais
passagens do que vagas, a seleção informa quantas foram omitidas e quais cenas
ficaram sem janela. Sequências com menos de três quadros ou com quadros faltantes
são incompletas. Pass temporal é rejeitado quando faltam passagens ou cenas; a
crítica pode declarar incerteza, sem inventar problema para disparar correção.
Mesmo em janelas completas, os quadros não comprovam continuidade entre eles,
sincronismo de fala ou som. Eventos não selecionados continuam omitidos.

O storyboard existente inclui quadros em ordem cronológica das janelas escolhidas
e, no espaço restante, os quadros principais das cenas. A galeria informa eventos,
passagens e quadros principais omitidos, sequências incompletas e cenas sem janela.
A prévia e a decisão continuam vinculadas ao hash do payload com composição,
direção, plano, código, quadros, materiais e bibliotecas; ao retomar, a direção,
os bytes dos materiais e hashes das bibliotecas são conferidos novamente. As
imagens do storyboard são capturas estáticas, não clipes nem escuta de áudio.
Sem tabelas, serviços, runners ou efeitos pagos novos.

## Reprodução da seleção Café Pausa

Usada somente a composição preservada
`.local/evals/motion-staged-retry-20261111/v0-composition.json`, SHA-256
`90251261fbf5c9e86f70fcde578438fa698a2ac66ac88067a57c4770ab5231d2`.
Seu MP4 anterior tem SHA-256
`187b611018d2b24c27edb99f07a4a21aecd5599e7333a64ad1b227147df0c451`.
A política anterior escolheu três dos 49 eventos, todos próximos de 1,9 s. A nova
política escolhe três de 49, agora distribuídos:

| Janela planejada | Intervalo (ms) | Quadros esperados no MP4 (ms) |
| --- | --- | --- |
| Passagem para `cafe` | 3580–4220 | 3533, 3567, 3867, 4200, 4233 |
| Entrada de `cafe-xicara` | 6780–7420 | 6733, 6767, 7067, 7400, 7433 |
| Passagem para `pausa` | 8340–9060 | 8300, 8333, 8667, 9033, 9067 |

Com cinco amostras globais deduplicadas, o pedido totaliza 20 quadros; 46 eventos
continuam omitidos. Isto reproduz **a seleção a partir do plano**, não uma nova
extração ou crítica. As amostras novas não foram renderizadas nem decodificadas e
o resultado não prova que o crítico identificará os problemas. Os instantes
conhecidos de 3967 e 8767 ms não coincidem exatamente com as novas amostras; devem
continuar disponíveis como evidências históricas e ser avaliados em prévia futura.

Observações anteriores, preservadas em
`.local/evals/motion-staged-retry-20261111/manual-inspection.json` e `transitions/`:
em 3967 ms, recorte de papel e resíduo de moldura; em 5600 ms, espaço vazio antes
da xícara; em 8767 ms, filete e sobreposição na volta da gravação. O quadro de
5600 ms já está em `v0-frames/` e consta no índice `v0-frame-index.json`. São
observações para revisão, não diagnósticos criados pelo novo seletor ou correções.

## Verificação e pendências

Passaram 247 testes Python dirigidos, além de Ruff e Mypy em sete módulos. Fixtures
locais verificam distribuição, limite de quadros, peças curtas, omissão
de passagens em peças longas, associação ao payload real da crítica e rejeição de
pass sem cobertura. Testes do storyboard usam renderer e storage simulados para
verificar identidade de cada quadro, galeria, portão e rejeição de alterações na
direção, composição ou material aprovado. Não houve banco, rede, nova geração,
asset, MP4 ou render. A prova de imagens futuras reais, o movimento entre quadros
e o ganho criativo dependem da comparação autorizada posteriormente. CI integral
e cobertura global não foram executados. Os cinco serviços não foram iniciados
ou alterados; seu estado não foi consultado nesta etapa e a consulta anterior ao
socket havia sido bloqueada.

Etapa 3 depende de OK do titular. A comparação futura exige autorização e orçamento
próprios; o aceite de storyboard não autoriza gasto nem substitui aceite visual.
