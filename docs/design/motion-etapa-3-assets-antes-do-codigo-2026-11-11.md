# Motion — etapa 3: materiais antes do código

> **Escopo histórico — esclarecido em 13/11/2026.** Estados, versões selecionadas,
> orçamentos e ordens de parada abaixo descrevem a entrega desta data; não são
> automaticamente instruções para uma rodada nova. Contratos capturados continuam
> preservados. Consulte a [orientação vigente](motion-orientacao-vigente-2026-11-13.md)
> para diferenças entre geração nova/evolução, estado operacional e próximo roteiro.

Data: 11/11/2026. Esta entrega altera a ordem técnica das novas capturas com
direção fornecida. Não executa geração de imagens, chamada paga ou renderização.
A qualidade visual continua sem validação; uma imagem plana não é um modelo 3D.

## Decisão e comportamento

O contrato `provided-direction-output-v4` mantém as etapas de plano e
implementação, mas resolve as ilustrações declaradas depois da validação do plano
e antes da implementação. Também verifica imagens autorizadas já disponíveis.
Cada imagem do plano deve possuir bytes PNG válidos, hash compatível e preview
determinístico, com largura, altura e presença de transparência declaradas. O
montador real anexa os pixels do preview e as limitações da imagem à entrada da
implementação. Se imagem, preview, hash ou política falhar, a chamada dependente
não acontece. São mantidos os limites de materiais e os efeitos, reservas,
recibos e upload existentes; não existe segunda geração no caminho posterior.

O servidor conserva plano, direção e áudio, associa a implementação ao SHA-256
do plano e rejeita alterações. O schema v4 permite declarar
`requires_plan_revision` com motivo, sem código executável; o fluxo encerra com
`MOTION_PLAN_REVISION_REQUIRED`, preserva recibo/custo e não repete chamada. Uma
revisão precisa de novo plano/hash e autorização própria: não há endpoint de
retomada parcial ou nova chamada automática nesta fatia. A v3 permanece com sua
ordem anterior e os contratos v1/v2 também são preservados. Requisições sem
direção fornecida mantêm seu fluxo anterior; esta evolução aplica-se ao v4.

O exportador offline usa a mesma validação de materiais e o mesmo builder da
API. Para uma implementação com ilustração declarada, exige PNGs resolvidos e
seus hashes explícitos; não gera nem busca arquivos. A política de ilustração,
quando necessária para a simulação offline, é fornecida explicitamente e nunca
autoriza despesa. Sem política nova, a entrada preparada não carrega orçamento
antigo. Os testes usam imagens sintéticas e transporte local sem rede.

## Evidência e limites da comparação

O pacote de planejamento v4 foi preparado pelo montador do produto em
`.local/exports/motion-qualidade-etapa3-entrega-20261111/`, sem rede ou render.
Preserva fonte, kit, áudio e transcrição da base; não contém um plano novo nem
pixels de objeto futuros. O briefing revisado da etapa 1 ainda descreve a xícara
como representação provisória por código; não afirmar que os pixels da xícara
anterior chegaram à implementação. A prova de implementação com preview usa
fixture sintética, não o conteúdo do cliente.
O manifesto tem SHA-256
`d0bd02cc68a9fe707be46023ce0838c35d3e4ce689293c6a6fa0825031c00fad`;
os pacotes preliminares da etapa 3 foram superados por este.

O recibo histórico registra `assets/illustration-xicara-realista.png`, 1.185.671
bytes, SHA-256 `30f06f55bba05c83de815b9ac38592d3b6e6d0368d1ab801134c9a5dc93e560b`,
proveniência `generated_illustration`. Nenhum arquivo com esses bytes foi
encontrado na busca local em `.local`; o armazenamento privado não foi consultado.
Conferir a disponibilidade, direitos e adequação do material original antes de
decidir seu reúso na comparação; não substituir pelo preview antigo e chamá-lo
de original. Nenhum orçamento anterior foi reutilizado.

## Verificação e trabalho restante

Testes locais cobrem ordem plano → imagem → implementação, identidade e pixels
do preview no payload, plano imutável, falha de imagem sem chamada dependente,
ausência de segunda geração, custo/recibo preservados em pedido de revisão,
exportação e incompatibilidade v4. O transporte é simulado; não é prova real de
provedor. Também foi corrigida a recuperação do storyboard v2 introduzido na
etapa 2 para reconstruir as janelas e os identificadores de upload capturados;
recuperação v1 permanece compatível.

Passaram 280 testes Python dirigidos e outros 159 de contexto, revisão, storyboard
e plano (grupos com possível sobreposição), além de Ruff e Mypy em dez módulos; CI integral e
cobertura global não foram executados. Nenhum banco ou serviço foi modificado; os cinco serviços
anteriormente interrompidos não foram iniciados, mas seu estado não foi consultado.
Validação visual, storyboard real e comparação autorizada são futuros. A etapa 4
depende de OK do titular; aceite de implementação não autoriza gasto ou render.
