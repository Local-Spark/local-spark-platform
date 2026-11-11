# V0 de conteúdo com motion — formatos e casos da etapa 0

Registro inicial de 05/11/2026 para iniciar as fatias do [plano](plano-v0-imagens-video-motion-2026-11-05.md), com atualização de estado em 09/11 abaixo. Os casos originais são especificações de ensaio, não novas execuções; aquele registro não realizou chamadas pagas.

As entrevistas confirmaram uma gravação do cliente por pedido de edição, com
até 60 segundos de entrada, 50 MiB por arquivo e até 60 segundos de saída.
Excesso pede versão menor, sem cortar automaticamente. Reel/story são 9:16;
carrossel tem 3–5 páginas em 4:5 vertical, 5–8 segundos por MP4; a IA escolhe
os valores nessa faixa. Ajustar uma página
preserva as demais; mudanças nelas exigem confirmação antes de aplicar, além da
nova revisão da sequência. O estilo é escolhido a cada pedido, preservando o
kit. A prioridade revisada é concluir geração, prévia, ajustes, aprovação da
peça e download dos formatos abaixo. Viabilidade e integração de postagem no
Instagram ficam para a fase posterior; conta Meta e publicação real não são
critérios de conclusão da geração. Essas regras ainda precisam de implementação
e validação; aprovação da peça não autoriza postagem futura.

## Matriz vigente — 09/11/2026

A sequência vigente é concluir a qualificação do Reel (etapa 4 do
[roteiro de trabalho](execucao-ate-etapa-7-2026-11-07.md)) antes de implementar
os demais formatos (etapa 5). Esta atualização registra leitura do código e
contratos, sem executar novas APIs ou implementar a etapa 5.

| Formato | Estado atual e reuso | Lacuna para a próxima fatia |
| --- | --- | --- |
| Imagem feed | Geração `full_piece_v1`, contexto/kit/skills, provider, ledger e Temporal já existem. O novo `content_pieces` importa a imagem concluída para revisão por versão sem postagem. | Crítica automática, edição condicional da peça anterior e comparação ainda não estão ligadas. Inspecionar o JPEG final armazenado, depois da conversão do PNG do provider. |
| Imagem story | O mesmo caminho visual já tem perfil/skill de story e evidência histórica de geração com referências. | Aplicar o ciclo qualificado de imagem com critérios próprios de proporção, área segura e leitura; o ensaio anterior não conclui a integração revisada. |
| Reel de vídeo enviado | Etapa 3 concluída no recorte 1c/legibilidade e Giz/refinamento guiado. Serviços HTML/`scene_init`, Temporal, versões e interface têm qualificação local concluída: quatro replays, prova integrada com modelo fake e CI 5.353/100%. | Ativação comercial, wiring de deploy, limite de entrada/imagens para orçamento e avaliação criativa do gerador pago ainda pendentes. Configuração permanece limitada a material sintético; não há nova API paga ou ativação para clientes reais. |
| Story de vídeo enviado | Mídia, render e revisão do Reel são pontos de reuso; contratos experimentais e skill de story já existem. | O pedido de produção novo aceita somente `reel`. Exige perfil/briefing e qualificação próprios antes de habilitar story em vídeo. |
| Carrossel com motion | `MotionDirection` valida 3–5 páginas/5–8 s, e `content_pieces` já preserva conjuntos ordenados e decisões exatas. | Faltam produção HTML por página, estado/recuperação de falha parcial, coerência da sequência e execução de ajuste seletivo. Metadados `page_positions` não executam esse ajuste. |

O [desenho da próxima fatia](ciclo-revisao-imagens-2026-11-09.md) coloca a inspeção
do JPEG final antes da entrega e registra as lacunas de finalização durável.
A menor fatia proposta é qualificar uma imagem feed já gerada: crítica,
uma edição condicional limitada, comparação e nova versão privada preservando
a original. Depois, validar story no mesmo ciclo. Reutilizar
`VisualBrandFinishService`, provider de imagem, guards, `VisualCostLedger` e
Temporal existentes, com evidência e critérios próprios de imagem; não tratar
imagem como vídeo para reutilizar a rubrica de motion.

O endpoint de edição usado hoje quando há referências não é um ciclo de
correção: `PreviewRequest` recusa `parent_preview_id` nos modos visuais, e
`finish` revalida contexto sem inspecionar pixels. Corrigir isso requer vínculo
durável com versão/hash/achado e operações próprias, não apenas retirar a
validação. O provider admite até cinco referências; fonte/item/espaço, logo e
exemplo do kit já podem ocupar essa capacidade. A versão anterior precisa de
seleção explícita de referências. Testes locais não autorizam nova chamada paga.

Para carrossel permanecem 4:5, 3–5 MP4s de 5–8 s, ordem imutável e aprovação da
sequência completa. Ajustar uma página preserva os hashes das demais; expansão
do alcance precisa de confirmação prévia. O compilador declarativo experimental
não substitui automaticamente o caminho HTML escolhido para preservar a
composição criativa. Ver o [contrato de revisão](revisao-peca-sem-postagem-2026-11-05.md)
e o [desenho da integração atual](integracao-reel-2026-11-09.md).

## Matriz histórica — 05/11/2026

O quadro e os casos abaixo conservam o ponto de partida daquela data; os
estados vigentes são os da matriz de 09/11 acima.

| Formato | Evidência e estado atual | Próxima lacuna |
| --- | --- | --- |
| Imagem feed | Uma prévia real privada foi concluída pelo worker e consultada pela API no [ensaio BL04.2](../evals/bl042-first-product-image-2026-10-29.md); publicação permaneceu simulada. | Concluir avaliação de fidelidade, legibilidade e custo por peça aceita, sem tomar o resultado histórico como homologação. |
| Imagem story | O caminho visual local contempla `story`; o [ensaio direto BL04.3](../evals/bl043-reference-quality-2026-11-04.md) produziu comparação com e sem referências. | Validar qualidade e jornada integrada; o ensaio isolado não prova entrega de produto. |
| Reel de vídeo enviado | O [ensaio de referência](../evals/ensaio-motion-referencia-2026-11-05.md) tem MP4 e trace; o titular preferiu v2. Jev retornou esclarecimento, e a direção/render foram experimentais. | Interpretar pedido e material, selecionar trechos e integrar edição, revisão e recuperação. V2 é referência de qualidade, não estilo universal. |
| Story de vídeo enviado | O renderer antigo e a reprodução web de uma prévia de vídeo não demonstram edição criativa de story. | Definir e testar direção, área segura, som opcional e entrega de vídeo vertical. |
| Carrossel com motion | O ensaio direto criou três MP4s independentes, sem comprovar publicação ou loop. A web atual mostra uma prévia por proposta. | Modelar coleção ordenada, estados por página, falhas parciais, revisão e download; verificar compatibilidade de publicação separadamente. |

Hoje propostas podem estar pendentes, em preparação, concluídas, rejeitadas, com orçamento excedido ou incertas; prévias individuais podem estar pendentes, renderizando, concluídas ou falhas. Revisão e entrega existentes referem-se a uma prévia. Eles não definem ainda os estados duráveis de uma coleção de páginas, de uma edição audiovisual ou de seus materiais. O contrato e a recuperação desses estados pertencem às próximas fatias, com identidade de operação, auditoria e isolamento já exigidos pelo projeto.

Em todos os formatos, geração integrada, revisão/ajustes, aprovação da peça por
versão e download final continuam pendentes e são critérios de conclusão desta
entrega. Um ensaio isolado não comprova esse fluxo. Postagem será tratada depois.

## Casos para ensaios separados

Entradas comuns: negócio de cafeteria fictício e kit `cafe-pausas` versão 1, com contexto, padrões parciais e instruções registrados nos arquivos `context.json` do [trace anterior](../../.local/evals/motion-referencia-2026-11-05/real-v1/TRACE.md). Não há fatos comerciais confirmados nesses casos; não inventar preço, oferta, horário ou destino. O material abaixo simula envio, não seleção pelo cliente. Padrões são parciais, não prova de que as referências foram integralmente conferidas. Para cada nova execução, registrar versão e hash dos insumos e skills efetivamente usados; Jev e direção devem ser identificados como reais ou simulados.

1. **Reel com fala.** Mensagem: “Enviei este vídeo da preparação do café. Faça um reel com cortes, transições, motion graphics e legendas para convidar as pessoas para uma pausa.” Entrada local: `.local/evals/motion-referencia-2026-11-05/assets/video-enviado-simulado.mp4`, SHA-256 `dd3f0265a4b2d94206188f46c094dc0177663e1a529b9ad2e0718a1dfad78a34`. A fala foi sintetizada e não pertence à pessoa retratada. Esperado para uma próxima avaliação: direção e MP4 até 60 s, preservação de sentido da fala, conferência auditiva e legendas revisadas. O [trace anterior](../../.local/evals/motion-referencia-2026-11-05/real-v1/TRACE.md) registra erro de transcrição, correção e adaptações manuais; não prova cortes semânticos em fala humana.
2. **Story sem fala.** Mensagem: “Enviei este vídeo da preparação do café. Faça um story para convidar as pessoas para uma pausa.” Usar o mesmo vídeo do caso 1, com toda a faixa de áudio removida em uma cópia temporária: `ffmpeg -i .local/evals/motion-referencia-2026-11-05/assets/video-enviado-simulado.mp4 -map 0:v:0 -c:v copy -an /private/tmp/v0-story-sem-fala.mp4`. Registrar hash da cópia e confirmar ausência de áudio com `ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 /private/tmp/v0-story-sem-fala.mp4` (resultado vazio). No registro inicial os binários não estavam no PATH. A preparação posterior apontou executáveis locais e verificou a cópia silenciosa; ver [plano do ensaio](../evals/plano-motion-v0-rodada-1-2026-11-05.md). Isso não é dependência empacotada do produto. Esperado: direção e MP4 vertical até 60 s, sem inventar fala ou depender de legenda de fala; música ou efeitos somente se apropriados e com direitos. Esse caso ainda não foi executado.
3. **Carrossel.** Mensagem: “Enviei uma foto do croissant. Crie um carrossel animado a partir dela, com motion graphics e uma sequência convidativa.” Entrada: [`croissant-cc0.jpg`](../evals/assets/croissant-cc0.jpg), SHA-256 `519772437eca1f7d2383edeebf80dc4beaf3d5e3039910cee5b975643de182ed`. Esperado: sequência de três páginas para este caso, cada qual com MP4 próprio e ordem explícita; conferir legibilidade e emenda de cada loop. Não pressupor áudio contínuo entre páginas ou suporte da rede de destino. O ensaio anterior serve de comparação, não de prova de integração.
4. **Material ausente.** Mensagem: “Faça um reel da preparação do café”, sem anexos. Esperado: pedir a gravação necessária, sem escolher foto do acervo nem alegar que um vídeo foi produzido. Uma sugestão de captação pode ser apresentada como orientação, sem inventar fatos. Nenhuma renderização deve ser presumida; este caso ainda não foi executado.

Os arquivos em `.local` são privados e ignorados pelo Git: podem não existir em outro checkout. A origem do vídeo ilustrativo é de [Stevenndori289, CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:Latte_Coffee_making.webm); preservar atribuição e termos de obras derivadas. A voz sintética foi adicionada no ensaio; não confundir o vídeo público de origem com a entrada modificada. A trilha anterior é de [Serolillo, CC BY 2.5](https://commons.wikimedia.org/wiki/File:Jazz_Piano.ogg); uso futuro depende de conservar seus termos e atribuição. Recuperar as fontes e confirmar direitos antes de compartilhar ou empacotar; não presumir que um arquivo local em si concede novos direitos.

## Próximos passos

Além dos casos criativos, a futura integração deve testar os limites: uma entrada
de exatamente 60 segundos, uma acima do teto e um pedido com duas gravações;
carrosséis fora de 3–5 páginas ou com MP4 fora de 5–8 segundos; ajuste que preserva
as outras páginas e ajuste que aguarda confirmação para alterá-las; aprovação e
download do conjunto/versão corretos e recuperação de falhas da geração. Não
admitir automaticamente material excedente nem reinterpretar os limites como
autorização para cortar ou combinar entradas fora do contrato. Esses testes
ainda não foram executados.

1. Preservar e verificar as fontes, licenças e dependências adotadas; não redistribuir o que não tiver direitos demonstrados.
2. Fazer ensaios de vídeo e carrossel conforme o [procedimento rápido](ensaios-rapidos-qualidade.md): mensagem, entradas e saídas por etapa, peças e trace, com audição e inspeção do movimento. Não criar banco ou sistema completo só para a avaliação criativa.
3. Antes de novas chamadas pagas, apresentar plano, quantidade, modelos, estimativa e orçamento específico; usar identidade e ledger próprios. Os valores e autorização do ensaio anterior não se renovam.
4. Em fatias posteriores, implementar contratos e execução com testes de integração e CI próprios, incluindo banco `_test` e roles restritas. A avaliação isolada não substitui esses testes nem comprova publicação.
