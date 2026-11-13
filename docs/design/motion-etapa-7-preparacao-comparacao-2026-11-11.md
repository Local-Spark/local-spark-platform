# Etapa 7 — preparação da comparação controlada

> **Escopo histórico — esclarecido em 13/11/2026.** Estados, versões selecionadas,
> orçamentos e ordens de parada abaixo descrevem a entrega desta data; não são
> automaticamente instruções para uma rodada nova. Contratos capturados continuam
> preservados. Consulte a [orientação vigente](motion-orientacao-vigente-2026-11-13.md)
> para diferenças entre geração nova/evolução, estado operacional e próximo roteiro.

**Atualização posterior:** titular autorizou a proposta com reserva nova máxima
US$ 6,75 e aprovação do storyboard antes do MP4. Executor qualificado; plano,
uma imagem, implementação e storyboard de 18 quadros concluídos via API/Temporal.
Reserva US$ 3,00; estimativa US$ 0,372465 sem confirmação de fatura. Galeria aguarda
decisão, sem MP4 novo, crítica ou correção; qualidade visual pendente. A preparação
abaixo é o registro anterior à autorização; execução, ressalvas e recibos em
`../evals/comparacao-qualidade-motion-etapa7-2026-11-11.md`.

Data: 11/11/2026. Preparação concluída; execução e aceite criativo pendentes.
O contrato vigente tem sete etapas. Não existe etapa 8 definida ou autorizada.

## Estado e proposta criativa

Etapas 1–6 estavam no índice do Git, sem alterações fora dele; último commit
`4adb596`, sem commit posterior identificado. Nada foi sobrescrito ou colocado
no índice nesta etapa. As provas técnicas anteriores permanecem válidas nos seus
limites; CI integral e qualidade visual não foram demonstrados por elas.

O titular escolheu manter somente a gravação original nesta rodada. Para a xícara,
pediu nossa proposta: conservar a aparência conceitual fotográfica apreciada na
base, trabalhando preparação, revelação, assentamento e repouso coordenados com
fundo/texto/sombra. Não simular faces ou rotação 3D com um recorte. A proposta está
em `docs/evals/direcao-cafe-pausa-comparacao-etapa7-2026-11-11.json` e no brief
adjacente; a direção provisória anterior foi preservada. A proposta ainda não é
aceite criativo nem permissão para gerar imagem.

A xícara anterior tem recibo e SHA-256
`30f06f55bba05c83de815b9ac38592d3b6e6d0368d1ab801134c9a5dc93e560b`, com 1.185.671
bytes. Nova busca local por PNGs do tamanho/hash não encontrou o original. O
armazenamento privado não foi consultado. O fluxo atual de captura não seleciona
diretamente uma ilustração gerada em pedido anterior; não se introduziu um desvio
manual para forçar esse reúso. A proposta prevê até uma imagem nova, explicitando
essa diferença, somente após autorização. A etapa 3 assegura pixels e preview
resolvidos antes da implementação; não há imagem futura disfarçada de pronta.

## Pacote verificável

Script: `scripts/evals/motion_comparison_prepare.py`, usando os builders reais
`capture_motion_guidance` e `OpenAIMotionProvider.build_request`, pelo exportador
existente. Não lê credenciais, consulta banco, chama provedor ou despacha workflow.
O pacote serve à futura execução por API/Temporal e dev existentes; não é uma
solução por prompt manual externo.

Pacote vigente: `.local/exports/motion-qualidade-etapa7-proposta-20261111/`, com ZIP
adjacente. SHA-256 do manifesto:
`518cb8be6a6666ffaf6c5868df7fb606e56e7355db6261b9a00b77c814674e57`.
O pacote `motion-qualidade-etapa7-preparacao-20261111` anterior é preliminar e
contém a direção provisória em código; não é a proposta vigente.

Inclui payload exato do planejamento, prompt legível, contexto, direção, kit,
schemas, contratos, bibliotecas, fontes/licenças, gravação, seis quadros da fonte,
cinco referências e hashes. Inclui cópia intacta de `v0.mp4` como base, sem nova
codificação. `pipeline.json` marca materiais, implementação, storyboard, render,
crítica e eventual correção como dependentes de respostas futuras. Schemas dessas
chamadas não são apresentados como prompts já executados. `rubric.json` registra
as seis dimensões como não avaliadas; parecer humano permanece nulo.

Preservação verificada: fonte, metadados, kit, áudio autorizado, transcrição,
perfil 720×1280/30 fps/11,2 s, modelo `gpt-6.1-sol` e teto de 54.000 tokens de
construção. A crítica mantém limite de 8.000. A fonte tem hash
`dd3f0265a4b2d94206188f46c094dc0177663e1a529b9ad2e0718a1dfad78a34`; a base tem hash
`187b611018d2b24c27edb99f07a4a21aecd5599e7333a64ad1b227147df0c451`.

Diferenças declaradas: brief/direção revisados, skill v13, repertório v2, cinco
referências em vez das seis antigas, contratos atuais de materiais/revisão/correção,
storyboard como decisão humana antes do MP4 e no máximo uma correção condicional.
O áudio complementar foi omitido por escolha do titular; não haverá A/B de trilha.
O ASR arquivado é automático não revisado. Uma nova execução deve registrar e
comparar seu resultado real, sem promover os tempos antigos a revisão humana.
A comparação mede o conjunto das mudanças; não isola causalmente cada melhoria.

## Nova proposta de reserva — não autorizada

| Trabalho | Quantidade máxima | Reserva proposta US$ |
| --- | ---: | ---: |
| Planejamento | 1 | 1,25 |
| Imagem conceitual | 1 | 0,50 |
| Implementação após os pixels | 1 | 1,25 |
| Crítica da candidata | 1 | 1,25 |
| Correção delimitada, se autorizada e justificável | 1 | 1,25 |
| Crítica da correção que passou no verificador local | 1 | 1,25 |
| Total inicial | | 4,25 |
| Total incluindo correção condicional | | 6,75 |

É uma proposta nova, sem reaproveitar aprovações, ledger ou reservas históricas.
Foi calculada pela política de admissão existente: entrada até 272.000 tokens,
rates locais de 2,50/10,00 por milhão de tokens de entrada/saída, máximo de US$ 1,22
por construção no teto. Não houve contagem remota nem atualização independente
da tabela do fornecedor; não é estimativa de fatura. Antes de cada envio, o
preflight real deve verificar tokens, tarifas configuradas, limites e saldos;
falha interrompe sem aumentar orçamento nem repetir automaticamente.

ASR local quando necessário, storyboard, render completo de até duas candidatas
e verificação de regressão usam a infraestrutura existente. Não são novas chamadas
pagas de modelo. O storyboard requer decisão do titular antes do MP4. Uma correção
não regenera a imagem. Nenhuma ação desta preparação consome a reserva proposta.

## Executor e verificações

Reconstruída imagem isolada com os arquivos das etapas 5–6, dependências locais
e build sem rede/pull. Nenhuma mudança em configurações ativas ou serviços.
Digest: `sha256:59c6229282fc8ba5cbf52c84321a260e8e5a94f37e373025ce0ca9ede733e449`,
linux/arm64. Entrada/hash do build e ID em `.local/motion-stage7-executor-20261111/`.
A consulta confirmou a imagem local; não se executou o renderer nem um fixture
em contêiner. Build não equivale a qualificação: o pacote mantém
`executor_qualified=false` e `execution_ready=false`.

Passaram 24 testes dirigidos do exportador/preparação, Ruff e Mypy do módulo novo.
Testes verificam payload idêntico ao builder, hashes, ausência de campos privados,
dependências futuras não inventadas, reservas, mudanças indevidas da base e
distinção entre imagem construída e executor qualificado. Não houve CI integral,
migração, banco temporário ou teste destrutivo. Docker foi consultado e a imagem
construída, sem iniciar/reconfigurar os serviços previamente interrompidos.

## Pendências e próximo aceite

Faltam autorização específica da proposta e orçamento novo, qualificação curta do
executor, admissão fresca pelo produto, plano/materiais/código reais, decisão sobre
storyboard, MP4, crítica, eventual correção e comparação lado a lado com parecer
humano. Não existe candidata, escuta ou melhora visual comprovada. O contrato
exige esse aceite para concluir a etapa 7; não declarar etapa concluída só porque
o pacote ficou pronto. Nenhuma etapa 8 será iniciada.
