# BL02 — Reaplicação técnica do kit de cafeteria

Data: 26/10/2026. Resultado: **ensaio sintético concluído; qualidade comercial e
economia por peça aceita não demonstradas**.

O caso usa `Café do Cedro`, negócio fictício distinto da marca do kit
`cafe-pausas/v1`. A entrada é a foto de croissant
[CC0](https://commons.wikimedia.org/wiki/File:Croissant-newspaper-and-tea.jpg)
do fixture existente; `R$ 18` e o CTA são fatos fictícios válidos apenas para o
ensaio. Nenhum material de cliente ou da Priscila Silveira foi enviado à API.
O programa `scripts/evaluate_brand_kit_transfer.py` executa dry-run por padrão;
`--live` requer chave local já configurada e reserva no máximo três chamadas,
com teto de US$ 0,30. Os arquivos privados do ensaio estão em
`.local/evals/brand-kit-transfer/20261026T230433457783Z/`; não são publicação.

As quatro rotas usam a mesma foto, produto, formato 4:5 e texto. As três rotas
IA usam `gpt-image-2.5-flare`, qualidade `medium`, tamanho `1024x1280`, uma
tentativa cada. A única variação é: briefing base; briefing base + paleta e
composição do manifesto; o mesmo briefing + **uma** foto de referência 4:5
do kit. A quarta rota aplica a receita local à foto original. Depois da foto,
o mesmo compositor escreve `Croissant de manteiga`, `R$ 18` e
`Peça informações pelo WhatsApp` em todas as saídas. Isso garante texto literal
e impede que erro de tipografia da IA contamine a comparação fotográfica.

| Rota | Entrada de referência extra | Tokens de imagem de entrada | Tempo | Custo de API Standard calculado |
| --- | ---: | ---: | ---: | ---: |
| Sem kit | 0 | 1.080 | 10,92 s | US$ 0,020605 |
| Manifesto | 0 | 1.080 | 10,46 s | US$ 0,020870 |
| Manifesto + referência | 1 | 2.542 | 10,89 s | US$ 0,032836 |
| Composição local | 0 | 0 | 0,05 s | US$ 0 de API; infraestrutura não medida |

Total das três chamadas: **US$ 0,074311**, calculado do `usage` pelas
[tarifas Standard oficiais](https://developers.openai.com/api/docs/pricing).
Não é valor final da fatura nem custo operacional completo. A
[documentação oficial de geração de imagem](https://developers.openai.com/api/docs/guides/image-generation)
orienta medir o uso por configuração e informa que a Images API direta não
aplica cache de entrada de imagem. A referência elevou o custo nesta amostra;
não gerou benefício visual evidente na inspeção inicial. O manifesto, sem
referência, aproximou a cena da paleta verde do kit por US$ 0,000265 a mais
que o briefing base. Todas as imagens IA recriaram parte do cenário/produto;
nenhuma pode ser apresentada como foto fiel de um produto real. A composição
local preservou a foto original, mas teve apresentação menos alinhada ao kit.

**Limite adicional identificado na vitrine:** o briefing deste ensaio pede uma
“cafeteria fictícia” e, portanto, só avalia direção de estilo em um caso
sintético. Para cafeteria física real, esse fundo poderia representar outro
estabelecimento e a rota seria reprovada. A próxima avaliação precisa separar
foto do espaço de foto do produto/delivery, exigir preservação da fonte e
testar texto sem foto como arte gráfica ou pedido de material. O resultado
histórico deste ensaio não valida essas rotas.

O relatório guarda modelo, qualidade, tamanho, tokens, request IDs, hashes,
latência, tentativas, arquivos de saída, hash da foto de origem e hash do
manifesto. `manifest-at-eval.json` preserva exatamente o pacote usado. Após o
ensaio, BL01 recebeu um segundo story; essa adição mudou o hash do manifesto,
mas não a receita/paleta/foto de referência usadas na avaliação. A ordem de
revisão cega, notas em celular, aceite do titular e custos de revisão ainda
precisam ser coletados. **Não há denominador de peças aceitas**, portanto não
há conclusão de economia nem escolha final de rota.

Próximo gate: mostrar as quatro saídas em ordem embaralhada em celular para
revisores sem saber a rota; aferir produto, legibilidade, aderência ao kit e
vontade de publicar. Depois, repetir com fotos e fatos de um comerciante que
autorize o uso e peça as revisões reais. Só então calcular custo de todas as
tentativas dividido pelas peças aceitas e decidir se a referência visual vale
seu custo adicional.
