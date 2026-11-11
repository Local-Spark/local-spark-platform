# Motion 1c — peças rejeitadas por regressão criativa

## Avaliação do titular — 06/11/2026

O titular rejeitou Reel, story e carrossel: o Reel concentrou vídeo no centro,
legenda em faixa verde e troca de títulos, o story ficou simples demais e o
carrossel foi percebido como estático. Considerou forte regressão em relação
ao Reel v2 anterior e pediu explicação do caminho. Decodificação, cobertura,
schema e render bem-sucedidos não constituem qualidade criativa. Nenhuma nova
chamada paga foi autorizada. [Registro privado da avaliação](../../.local/evals/motion-v0-rodada-1c-2026-11-05/creative-review-user-rejected.json).

A revisão dos inputs confirmou que o campo `references` efetivamente enviado
estava vazio e que a direção concreta do Reel v2 não foi fornecida. As fichas
tinham menções resumidas a ele, sem sua sequência de composição. O prompt antigo
exigia movimento expressivo, transformações de composição, tipografia cinética
e momentos distintos; essa exigência perdeu força na migração para o contrato
parametrizado. Reel/carrossel escolheram `editorial-janela-v1`; story escolheu
`clareza-neutra-v1`. O carrossel prescreveu textos fixos e apenas 2–3% de escala
na foto. Isso já estava na direção, antes da montagem. A perícia comparativa
continua; melhorias de parsing não corrigem essa regressão criativa.

06/11/2026. Ensaio direto com material fictício; sem banco, workflow ou jornada
completa para avaliar criatividade. A autorização cobre sete operações do
[plano 1c](plano-motion-v0-rodada-1c-2026-11-05.md). As sete chamadas ocorreram:
três interpretações Jev, uma transcrição e três direções. Nenhuma foi repetida.
As direções completaram no provedor, mas todas foram rejeitadas pelo contrato
local. A montagem usa derivados técnicos identificados; não houve refação paga.

Atualização de 06/11: após o bloqueio descrito abaixo, o titular autorizou
explicitamente retomar somente story e carrossel. O registro separado
`round/user-resume-approval.json` vincula essa decisão ao grant, à revisão
técnica e aos dois IDs, preservando o teto. A execução foi retomada.

O story também recebeu resposta completa, mas falhou na validação local.
Sua montagem usa uma cópia derivada, com sete correções documentadas e sem
nova chamada. A continuação para o último ID passou pela revisão técnica das
duas rejeições e pela revisão automática, informada da nova falha do story.
Nenhuma aprovação criativa foi presumida. Rodada paga encerrada.

## Mensagens simuladas e etapas

| Caso | Mensagem |
| --- | --- |
| Reel | Enviei este vídeo da preparação do café. Faça um reel com cortes, transições, motion graphics e legendas para convidar as pessoas para uma pausa. |
| Story | Enviei este vídeo sem fala da preparação do café. Faça um story para convidar as pessoas para uma pausa. |
| Carrossel | Enviei uma foto do croissant. Crie um carrossel animado a partir dela, com motion graphics e uma sequência convidativa. |

Jev reconheceu os três formatos, sem escolher item inexistente entre candidatos
vazios. A transcrição do Reel corresponde às palavras do roteiro sintético
documentado; só pontuação e capitalização diferem. A saída foi mantida, com
comparação explícita e sem alegação de alinhamento temporal por palavra.

A direção recebeu kit, três fichas próprias, pedido, seis quadros efetivamente
anexados e transcrição revisada. Escolheu `editorial-janela-v1`, justificando a
janela para destacar a preparação e separar títulos/legendas. Não recebeu o vídeo
integral nem referências estruturadas; observações e hipóteses constam da saída.

O modelo retornou `completed`, `gpt-6.1-sol`, tier `default`; a validação local
rejeitou nove segmentos sem interpolação declarada e o rótulo da faixa de voz.
A resposta original e o estado `rejected` permanecem intactos.

## Peça e intervenções locais

- [Página local de revisão dos vídeos e da referência anterior](../../.local/evals/motion-v0-rodada-1c-2026-11-05/review.html).
- [Reel com legibilidade ajustada — MP4](../../.local/evals/motion-v0-rodada-1c-2026-11-05/local-adaptation/reel-legibility-v2/render/page-1.mp4).
- [Quadros da peça](../../.local/evals/motion-v0-rodada-1c-2026-11-05/local-adaptation/reel-legibility-v2/review/contact.png).
- [Primeira montagem, com texto pequeno demais](../../.local/evals/motion-v0-rodada-1c-2026-11-05/local-adaptation/reel/render/page-1.mp4).

Uma cópia derivada recebeu dez correções documentadas: nove interpolações
`linear` entre estados idênticos, sem mudança visual, e a classificação
`recorded_voice` para a faixa integral cuja fala é conhecida e cuja preservação
foi explicitamente determinada pelo modelo. Nenhum texto, corte ou áudio mudou.

A primeira montagem revelou tipografia ilegível: `font_size` usa pontos-base
da altura, mas essa unidade só estava em comentário Python e não no schema
enviado. O modelo escolheu 32/46, produzindo aproximadamente 4/6 pixels.
Uma segunda variante recebeu **ajuste visual explícito do agente**, usando
esses números como hipótese de tamanho em pixels: legendas com 32 px e títulos
com aproximadamente 46 px. Não é normalização semanticamente neutra nem saída
intocada do provedor. Os sete ajustes estão registrados; texto, cortes e áudio
continuam iguais. Nenhuma chamada adicional produziu essa variante.

## Verificação e limites

O MP4 final tem 720 × 1280, H.264/AAC, 30 fps, 336 quadros e 11,2 s.
Decodificação integral passou. A duração lógica de 11.176 ms recebeu 24 ms no
fechamento em quadros. Inspeção dos quadros confirmou leitura dos títulos e
legendas sem cortes; a legenda mais longa ocupa três linhas. O início tem um
quadro sem o vídeo durante a entrada. A marca incidental da camiseta permanece.

Na primeira montagem, a correlação entre áudio de origem e saída, convertidos
para mono/16 kHz e comparados sem deslocamento, foi 0,991748. Isso é evidência
técnica, não escuta, alinhamento de palavras ou aprovação semântica. Não houve
escuta perceptiva nesta verificação. A variante de legibilidade preserva também
os bytes AAC extraídos, com hash idêntico ao da primeira montagem. O aceite
criativo do titular e a comparação com o Reel v2 preferido
continuam pendentes; esta peça não é homologação comercial nem autorização
de publicação.

## Trace e custo

- [Entradas por caso e snapshots](../../.local/evals/motion-v0-rodada-1c-2026-11-05/round/bundle/cases).
- [Pedidos, respostas, resultados e ledger](../../.local/evals/motion-v0-rodada-1c-2026-11-05/round/live).
- [Revisão da transcrição](../../.local/evals/motion-v0-rodada-1c-2026-11-05/round/transcription-comparison.json).
- [Dez correções técnicas](../../.local/evals/motion-v0-rodada-1c-2026-11-05/local-adaptation/reel/normalization-trace.json).
- [Sete ajustes visuais](../../.local/evals/motion-v0-rodada-1c-2026-11-05/local-adaptation/reel-legibility-v2/visual-adjustment-trace.json).
- [Custo por operação após sete chamadas](../../.local/evals/motion-v0-rodada-1c-2026-11-05/round/cost-review-after-seven-calls.json).

Estimativa conservadora das direções: Reel **US$ 0,105925** e story
**US$ 0,062325**, carrossel **US$ 0,093793**. Com Jev, transcrição e tentativa 1b anterior, estimativa global
**US$ 0,263073**, ainda sem conferência
em fatura. Tokens de raciocínio já integram a saída e não foram contados duas
vezes. Reservas conservadoras comprometidas: **US$ 1,55**, incluindo a reserva
anterior de US$ 0,01 e as reservas integrais das três direções rejeitadas. Nenhum reembolso
de reserva foi presumido.

## Story após retomada autorizada

- [Story — MP4](../../.local/evals/motion-v0-rodada-1c-2026-11-05/local-adaptation/story_video/render/page-1.mp4).
- [Quadros](../../.local/evals/motion-v0-rodada-1c-2026-11-05/local-adaptation/story_video/review/contact.png).
- [Correções técnicas](../../.local/evals/motion-v0-rodada-1c-2026-11-05/local-adaptation/story_video/normalization-trace.json).

O modelo escolheu `clareza-neutra-v1`, vídeo central, título e convite final,
com silêncio intencional. A gravação deste caso não tem áudio. A saída omitiu
duas interpolações entre estados iguais, terminou as animações de entrada antes
do fim das respectivas camadas e preencheu `omission_reason` embora não houvesse
fala a omitir. Os tempos eram relativos corretamente; faltava declarar a
permanência do estado final, já descrita pelo modelo.

A derivação acrescenta as duas interpolações, mantém cada texto no estado final
até o término da camada e transfere a explicação do silêncio para o trace.
Reaplicar os sete ajustes à resposta original reproduziu exatamente o derivado.
Resposta e ledger continuam rejeitados. O MP4 tem 11 s, 330 quadros, 720 × 1280,
30 fps e nenhuma faixa de áudio; decodificação integral passou. Seis quadros
foram inspecionados: títulos legíveis, CTA próximo à borda inferior e marca
incidental na camiseta. Sobreposição da interface e qualidade completa do
movimento ainda não foram avaliadas; o titular não aprovou a peça.

## Retomada de story e carrossel

Os dois pedidos não enviados foram preparados com um sufixo de 649 caracteres
que explica unidades tipográficas, interpolação e papel da voz. Todos os outros
campos permanecem idênticos, incluindo modelo, schema, imagens, formatos, IDs e
limites. O [registro técnico](../../.local/evals/motion-v0-rodada-1c-2026-11-05/round/technical-recovery.json)
preserva a rejeição e todas as reservas; permite somente esses dois IDs, sem
repetir Reel. O registro técnico não concede nova autorização de usuário.

A revisão automática **bloqueou a execução de story antes do envio**, por
entender que a condição de parada após uma rejeição exige autorização explícita
para retomar. Não houve chamada ao provedor nem mudança no ledger por essa
tentativa de execução. Não será contornado o bloqueio por outro caminho.

Proposta apresentada e autorizada pelo titular: retomar **apesar da rejeição
anterior**, somente para uma direção de story e uma de carrossel, sem repetir
Reel e sem refações pagas. Estimativa adicional: **US$ 0,20–0,60**, baseada no
uso observado e limites de saída, com incerteza de tokens de imagem. Reserva
adicional: **US$ 1,00**; total comprometido planejado: **US$ 1,55**, dentro do
mesmo teto global **US$ 1,60**. O teto limita início de chamadas, não cobrança
do fornecedor por uma chamada já iniciada.

Após o story rejeitado, um registro técnico v2 vinculou as duas respostas e os
derivados revisados, permitindo somente o ID de carrossel ainda não iniciado,
com o mesmo request já preparado. A revisão automática permitiu essa execução
com o contexto da nova rejeição explicitamente informado. A extensão privada
passou em 88 testes mock; preservou prefixos do ledger, grant, reservas e
registros anteriores. Não constitui um mecanismo automático do produto.

O carrossel retornou três páginas de 6 s, em 4:5, com silêncio editorial e
estilo `editorial-janela-v1`. Seis easings entre estados iguais e três razões de
silêncio no campo reservado à omissão de fala causaram rejeição. Uma cópia
derivada usa nove correções técnicas rastreáveis; sua reprodução exata a partir
da resposta foi verificada. Os três MP4s foram renderizados em 1080 × 1350,
30 fps, sem faixa de áudio; decodificação integral passou.

- [Página 1](../../.local/evals/motion-v0-rodada-1c-2026-11-05/local-adaptation/carousel_motion/render/page-1.mp4),
  [página 2](../../.local/evals/motion-v0-rodada-1c-2026-11-05/local-adaptation/carousel_motion/render/page-2.mp4),
  [página 3](../../.local/evals/motion-v0-rodada-1c-2026-11-05/local-adaptation/carousel_motion/render/page-3.mp4).
- [Quadros das páginas](../../.local/evals/motion-v0-rodada-1c-2026-11-05/local-adaptation/carousel_motion/review/contact-pages.png).
- [Trace dos nove ajustes](../../.local/evals/motion-v0-rodada-1c-2026-11-05/local-adaptation/carousel_motion/normalization-trace.json).

As amostras mostram texto legível e a mesma foto em três enquadramentos. Motion
muito discreto: pequenas mudanças de escala da imagem e deslocamento do filete.
Início e fim semelhantes não comprovam continuidade perceptiva de loop. O CTA
“deslize” e a sobreposição de interface não foram validados num destino real;
publicação permanece fora desta entrega. Entrevista de qualidade enviada ao
titular com as peças, sem presumir aceite nem autorizar nova rodada paga.

Ainda faltam a revisão das peças e a integração no produto: admissão,
contexto/material, direção, renderer empacotado/isolado, Temporal, revisão,
ajustes e download. A correção das descrições do contrato deve entrar no produto
em fatia própria com os testes exigidos. Ela foi aplicada após todas as chamadas,
sem mudar versão ou validadores; CI em andamento. O ensaio privado preserva os
snapshots originais usados em cada chamada.
