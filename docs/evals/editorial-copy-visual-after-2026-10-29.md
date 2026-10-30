# Comparação visual após a geração editorial — 29/10/2026

O proprietário autorizou seis novas imagens com teto cumulativo de US$ 15 e
pediu um ensaio concentrado em qualidade, sem executar a jornada completa.
Os mesmos três negócios, pedidos, fotos fictícias CC0, kits e preços do
[ensaio anterior](three-business-visual-ab-2026-10-29.md) foram usados.

## Peças e respostas

| Caso | Pedido fictício | Sem skill | Com skill | Arte, legenda e CTA gerados |
| --- | --- | --- | --- | --- |
| Café do Cedro, feed | Faça um post para o feed com esta foto do nosso croissant. O preço é R$ 18. | [Imagem](../../.local/evals/three-business-editorial-real-20261029/revisao/cafe-feed-sem-skill.png) | [Imagem](../../.local/evals/three-business-editorial-real-20261029/revisao/cafe-feed-com-skill.png) | Arte e legenda: “apresente Croissant por R$ 18,00”. CTA: “aproveite Croissant por R$ 18,00”. |
| Dog em Casa, story | Crie um story usando esta foto do nosso cachorro-quente para divulgar o delivery. O preço é R$ 19,90. | [Imagem](../../.local/evals/three-business-editorial-real-20261029/revisao/delivery-story-sem-skill.png) | [Imagem](../../.local/evals/three-business-editorial-real-20261029/revisao/delivery-story-com-skill.png) | Arte: “apresente Cachorro-quente por R$ 19,90”. Legenda: “Cachorro-quente por R$ 19,90”. CTA: “mande mensagem whatsapp”. |
| Estúdio da Luma, story | Faça um story com esta foto para apresentar o alongamento acrílico decorado. O preço é R$ 95. | [Imagem](../../.local/evals/three-business-editorial-real-20261029/revisao/manicure-story-sem-skill.png) | [Imagem](../../.local/evals/three-business-editorial-real-20261029/revisao/manicure-story-com-skill.png) | Arte: “Alongamento acrílico decorado”. Legenda: “Alongamento acrílico decorado por R$ 95,00”. CTA: “mande mensagem”. |

As duas artes de café e as duas de delivery mostram o preço; as duas de
manicure não mostram o preço, embora ele apareça na legenda. No ensaio anterior
nenhuma das seis imagens o exibia. As saídas de café e delivery usam “apresente”
como texto voltado ao público, soando como instrução interna. A CTA do café
repete o preço; as demais são pouco específicas. A guarda lexical aprovou as
três propostas, mas isso não demonstra qualidade comercial. A lista limitada de
vocabulário e a instrução para usá-la são uma possível causa da redação
artificial, não uma causa comprovada. A inclusão do preço na própria arte ainda
não é garantida.

As duas versões de cada negócio compartilham a **mesma proposta editorial**;
apenas o prompt da cena visual recebe ou não a skill. Comparar os pares não
mede a influência da skill na legenda ou CTA. Os enquadramentos e decorações
variam, mas uma imagem por braço não demonstra melhora geral nem separa efeito
da skill da variação aleatória. O antes/depois também muda o caminho e a copy;
não demonstra causalidade. As fotos do acervo e WhatsApp são cópias dos mesmos
bytes, não um teste de seleção entre fotos distintas.

## Procedimento e gastos

Três chamadas editoriais `gpt-5-mini` e seis chamadas de imagem
`gpt-image-2.5-flare-2026-09-08` foram concluídas; não houve Jev ou publicação.
O executor isolado alimentou diretamente o adapter editorial, a validação lexical,
o adapter de imagem e o acabamento do produto. Os prompts visuais reproduzem a
composição do produto, mas são montados no executor. Não foram executados banco,
Temporal, admissão, `_inputs`, seleção de fatos, revalidação do catálogo ou
WhatsApp real. O input fornecia um único fato de preço por caso; portanto, este
ensaio não prova que o produto escolheria esse fato entre outros disponíveis.

O ledger soma US$ 9,765 em reservas anteriores e US$ 3,30 nesta rodada,
totalizando **US$ 13,065** sob teto cumulativo de US$ 15. As reservas não são
fatura e permanecem preservadas. O uso estimado pelas tarifas já documentadas é
**US$ 0,19736825** nesta rodada, não custo faturado nem custo por peça aceita.
Nove operações terminaram; nenhuma foi repetida. Os inputs, saídas, prompts,
hashes, ledger e respostas sintéticas estão em
`.local/evals/three-business-editorial-real-20261029/`. O acabamento devolveu PNG;
as cópias com extensão `.png` mantêm os bytes originais para facilitar a abertura.
Três testes mock do executor passaram; o CI **não foi executado**, conforme pedido.
