# Recuperação motion — implementação R1–R5

Data: 11/11/2026. Pedido do titular: implementar as cinco fatias do
[plano de recuperação](../design/plano-recuperacao-e-evolucao-motion-2026-11-11.md).
R1–R4 implementadas tecnicamente; R5 tem preparação reproduzível pelo montador
real, mas a execução e o aceite visual continuam pendentes. Não há nova peça
nem comprovação de melhora artística nesta entrega. A etapa 7 original permanece
aberta. A autorização antiga de US$ 6,75 não foi reutilizada.

## Entregas e estado

| Fatia | Entrega verificável | Limite do resultado |
| --- | --- | --- |
| R1 — referências e recursos | Base principal identificada no banco existente, MP4/composição vinculados, xícara original localizada e validada; inventário de referências/acervo | Confirma disponibilidade, não aplicação criativa |
| R2 — base no produto | Contrato opcional `MotionRequest.evolution`, captura por tenant/negócio/versão/hash, quadros e composição no payload real de plano/implementação/revisão | Ativa nas solicitações com vínculo explícito; não altera pedidos históricos nem elege automaticamente uma base |
| R3 — direção sem perdas silenciosas | Matriz das 18 funções/elementos da base; direção e brief revistos; validação antes de construir | Declaração de função não prova que o código gerado a executará bem |
| R4 — cobertura e seleção | Política temporal v3 para pedidos de evolução; galeria inclui base; crítica comparativa e bloqueio de seleção inferior/equivalente/inconclusiva | Quadros não certificam fluidez nem áudio; avaliação do modelo não substitui o titular |
| R5 — rodada controlada | Script usa captura/preparação/montador reais; pacote verificável, proposta nova de reserva, pipeline e bloqueios explícitos | Não executada: CI integral, admissão, orçamento novo e decisões humanas pendentes |

## R1 — fatos fechados

A base principal é “Nova — quatro melhorias”, render 0 da solicitação
`f9a58258-0c49-576f-ac3f-d9cf315495ab`, com peça persistida e estado `completed`.
SHA-256 do MP4: `187b611018d2b24c27edb99f07a4a21aecd5599e7333a64ad1b227147df0c451`.
A versão desenhada continua referência complementar de ação, identificada no
plano; não substitui o comparador principal nem entra como segundo comparador
automático desta rodada.

A imagem original foi encontrada entre recibos de upload recebidos da própria
base: 1.185.671 bytes, SHA-256
`30f06f55bba05c83de815b9ac38592d3b6e6d0368d1ab801134c9a5dc93e560b`.
Reutilização explícita como `assets/reused-30f06f55bba05c83.png`, sem gerar imagem.
Continua identificada como arte conceitual, não fotografia real do negócio.
A imagem da tentativa reprovada também existe, mas não é a selecionada.

Consultas restritas ao negócio encontraram zero referências próprias ativas,
zero sugestões selecionadas e nenhuma foto no acervo. O montador confirmou
`reference_context=[]`. Portanto, não havia nesses grupos um material elegível
omitido nesta entrada; isso não desativa suas capacidades no produto.
A leitura direta de `learning_heads` não foi permitida ao papel restrito e não
foi elevada; não se afirma inventário global dos aprendizados. O contexto
selecionado pelo serviço existente foi inspecionado.

A preparação efetiva conserva skill `instagram-reel-v13`, repertório
`business-reel-v2`, cinco imagens de acabamento, seis quadros da gravação, kit,
voz original, runtimes e ASR arquivado identificado como não revisado.
As adaptações de motion-sources continuam no repertório/bibliotecas existentes;
não há carregamento indiscriminado de repositórios ou skills externas.

## R2 e R3 — proteção adicionada

A base histórica tem canal próprio (`historical_baseline` e quadros `baseline`),
separado de `current`/`previous`, que continuam protegendo a correção da mesma
rodada. O montador envia direção/plano da base, hash e matriz; não executa seu
HTML/JS antigo nem expõe chaves privadas de armazenamento no payload.
Fonte, áudio e kit são conferidos. Imagem e vídeo são lidos fora das transações
SQL e conferidos por tamanho/hash; recibos de material precisam pertencer ao
mesmo tenant/negócio/solicitação. Nenhuma tabela, migração ou serviço foi criado.

A matriz exige contabilizar todos os elementos da base e apontar destinos reais
na direção nova. Preservar exige manter identidade; substituir exige declarar
destino, função e resultado esperado. Essa possibilidade evita congelar uma
receita gráfica. A validação também é aplicada ao plano antes dos efeitos de
construção. Sem vínculo/matriz válida, o fluxo para.

Artefatos do caso:

- `direcao-cafe-pausa-recuperacao-2026-11-11.json`: restaura relações de ligação,
  prepara a revelação do objeto e conserva sua participação no retorno da gravação.
- `evolucao-cafe-pausa-recuperacao-2026-11-11.json`: matriz de 18 elementos,
  base explícita e reutilização da xícara original.
- `brief-cafe-pausa-recuperacao-2026-11-11.txt`: hipótese delimitada de passagem,
  preservando abertura, gravação, kit e somente voz original.

Esses arquivos são específicos da comparação Café Pausa. Não tornam bordas,
vapor, xícaras, efeitos por palavra ou número de elementos obrigatórios em
outras peças. A direção revista ainda precisa ser julgada em uma candidata real.

## R4 — evidências e condição de conclusão

A amostragem v3 acompanha entradas/saídas conectadas através da passagem real.
Na composição reprovada, a janela da primeira passagem passa de 3.580–3.780 ms
para 3.380–4.500 ms; a do retorno, de 8.740–8.940 ms para 8.320–9.340 ms.
Isso inclui trechos que o recorte antigo deixava de fora. O limite continua em
20 quadros e três janelas; snapshots v1/v2 mantêm sua interpretação.

Os 15 quadros arquivados da base eram insuficientes para esta comparação.
Foram decodificados 20 quadros do MP4 existente segundo a política v3, sem
executar composição nem renderizar outra peça. A galeria do produto pode mostrar
esses quadros junto aos da candidata e informa os limites da inspeção estática.

A crítica precisa identificar o hash da base e comparar sentido/ação, gravação,
espaço, ritmo e identidade, citando evidência efetivamente enviada de ambos os
lados. Resultado regredido, incerto, apenas recuperado ou parcialmente melhorado
não conclui o pedido como evolução. O critério do plano exige melhora nas quatro
dimensões criativas e nenhuma regressão de identidade. A correção delimitada
existente conserva sua própria proteção entre candidatas; a base histórica não
ocupa o lugar da candidata anterior. Sem candidata elegível, o pedido falha pelo
controle existente de revisão obrigatória; não há promoção de referência.

## R5 — preparação real, sem execução paga

`scripts/evals/motion_recovery_prepare.py` lê o contexto pelo serviço do produto,
resolve os materiais e monta a entrada pelo provider real, com transporte de
exportação sem chamadas ao modelo. Não usa um prompt manual como substituto.
O ASR arquivado é conferido contra a fonte e continua não revisado; a admissão
real deverá conferir disponibilidade, políticas e timing novamente.

Pacote final local: `.local/exports/motion-recovery-20261111-v2/` e ZIP adjacente.
Manifesto SHA-256:
`8a6d853b9ad8433f112e46ad3f924f89fab3dbbc2196fe5c731bc7573cb0c155`.
Contém payload exato de planejamento, contratos futuros, 20 quadros da base,
seis da fonte, cinco referências, imagem reutilizada, bibliotecas e relatório.
As entradas de implementação/crítica dependem de respostas futuras e não foram
inventadas. A primeira exportação foi preservada; a revisão recebeu novo destino.

Reserva nova **proposta, não autorizada**: até US$ 6,25, com três chamadas iniciais
(plano, implementação e crítica) e até duas adicionais (uma correção delimitada
e sua crítica); zero imagens novas. É teto de reservas pela política configurada,
não previsão de custo nem consulta atual de preços. Nada foi reservado no ledger.
A execução continua por API/outbox/Temporal e exige aprovação do storyboard antes
do MP4. A tentativa reprovada permanece intocada, sem aprovação retroativa.

## Verificação e pendências

- 1.114 testes dirigidos passaram; dois ficaram skipped. Incluem 19 novos testes
  sintéticos de vínculo, integridade, matriz, payload, crítica, seleção, amostragem
  e decodificação. Nenhum conteúdo de cliente virou fixture de fundação.
- Ruff passou nos 20 arquivos Python desta recuperação; Mypy passou nos 325
  módulos de produção. Corrigida apenas a anotação de retorno de `motion_styles`
  identificada pelo Mypy, sem alteração de comportamento.
- `make ci` foi tentado e parou na formatação preexistente. Após formatar os dois
  arquivos também tocados nesta recuperação, restam 17 arquivos de outras
  alterações já presentes. CI integral, integração destrutiva em `_test` e
  cobertura de 100% não foram comprovadas; não declarar pronto para merge.
- Preparação real e inventário leram o dev existente com papéis restritos;
  nenhuma limpeza, migração ou banco temporário. Sem chamada paga, novo asset
  gerado, novo MP4 ou alteração do estado da tentativa anterior.
- Os cinco serviços foram conferidos como `exited`. Índice Git preservado; os
  14 arquivos de assets existentes registrados na abertura permaneceram iguais.

Recibos locais em `.local/evals/motion-recovery-20261111/`: `inventory.json`,
`preparation-result.json`, `sampling-check.json`, `verification.json` e
`work-start.json`. Não contêm autorização de execução. Antes de R5 executada:
resolver CI/qualificação do ambiente, conferir admissão, obter reserva nova,
avaliar storyboard comparativo e só então autorizar MP4/revisão. A entrega técnica
reduz caminhos conhecidos de regressão; ainda não prova uma peça melhor.
