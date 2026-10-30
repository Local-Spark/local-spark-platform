# Três negócios fictícios — comparação visual com e sem skill

Em 29/10/2026, com autorização para teto de **US$ 10**, três cenários com
pedidos de WhatsApp e fotos de referência produziram seis prévias reais. O teto
conservador considerou **US$ 6,615 em holds anteriores** e reservou mais
**US$ 3,15** neste ensaio; total de holds US$ 9,765. Hold não é fatura e não
limita outras operações da conta.

## Resultado

| Negócio e pedido fictício | Sem skill | Com skill | Resultado observado |
| --- | --- | --- | --- |
| Café do Cedro: post de croissant por R$ 18 | [Prévia](../../.local/evals/three-business-ab-20261029/revisao/cafe-feed-sem-skill.jpg) | [Prévia](../../.local/evals/three-business-ab-20261029/revisao/cafe-feed-com-skill.jpg) | As duas mostram croissant, mas não incluem o preço pedido. |
| Dog em Casa: story de cachorro-quente por R$ 19,90 | [Prévia](../../.local/evals/three-business-ab-20261029/revisao/delivery-story-sem-skill.jpg) | [Prévia](../../.local/evals/three-business-ab-20261029/revisao/delivery-story-com-skill.jpg) | As duas mostram lanche semelhante à referência, sem o preço pedido. |
| Estúdio da Luma: story de alongamento acrílico decorado por R$ 95 | [Prévia](../../.local/evals/three-business-ab-20261029/revisao/manicure-story-sem-skill.jpg) | [Prévia](../../.local/evals/three-business-ab-20261029/revisao/manicure-story-com-skill.jpg) | As duas mostram unhas decoradas, sem o preço pedido; recortes e detalhes mudam. |

Todas as peças usam o nome do item e o CTA genérico “Fale com o negócio”. A
ausência do preço confirmado é falha material contra os três pedidos: elas não
cumprem integralmente a intenção, independentemente da aparência. O baseline
insere o fato do catálogo em primeiro lugar e seleciona o primeiro fato para a
cena; a skill experimental influencia o prompt da imagem, não a escolha de copy
ou CTA. A correção exige integração editorial e verificação factual, sem inventar
ou liberar preço vencido.

Uma peça por grupo não demonstra melhora consistente nem separa efeito da skill
da variação aleatória do gerador. A inspeção nesta sessão não substitui revisão
do usuário ou titular no celular. As fotos são referências CC0 ilustrativas,
não demonstram fidelidade de produtos ou serviços de negócios reais.

## Fontes e percurso

- Três contas/negócios fictícios isolados com catálogo, fato de preço vigente e
  kits individuais configurados como overrides do kit demonstrativo; sem logos
  próprios. Cada mensagem tinha caption e imagem.
- Fontes: [croissant CC0](https://commons.wikimedia.org/wiki/File:Croissant-newspaper-and-tea.jpg),
  [hot dog CC0](https://commons.wikimedia.org/wiki/File:Hot_Dog_1.JPG) e
  [unhas CC0](https://commons.wikimedia.org/wiki/File:Acrylic_Nails.jpg). As
  cópias são normalizadas/sem metadados e usadas como fontes ilustrativas.
- Jev real interpretou cada pedido; o adapter OpenAI real criou as seis cenas.
  O fluxo usou serviços do produto, PostgreSQL `_test` separado, Temporal,
  admissão/claim/ledger e acabamento. Nenhum banco da aplicação foi migrado ou
  limpo. Não houve publicação ou dados de cliente.
- A origem WhatsApp foi inserida **já processada** como evento/asset sintético;
  não há prova de webhook ou entrega oficial Meta. A primeira candidata segue o
  workflow; a segunda prévia com skill foi solicitada internamente, não escolhida
  automaticamente pelo WhatsApp. A foto no acervo é cópia em objeto separado dos
  mesmos bytes recebidos: prova as duas identidades, não retrieval entre fotos
  diferentes. Storage local é adapter de teste privado, não S3 de produção.
- Cada par usa o mesmo contexto, fonte, kit, modelo, tamanho e acabamento. A skill
  pinada é aplicada somente como orientação visual do prompt, com guardas
  comuns; não gera roteiro, legenda ou CTA. Não houve pesquisa de concorrentes.

## Uso, reservas e validação

| Caso | Jev estimado | Imagens estimadas sem/com skill | Total estimado |
| --- | ---: | ---: | ---: |
| Café | US$ 0,000032424 | US$ 0,029605 / US$ 0,034330 | US$ 0,063967424 |
| Delivery | US$ 0,000032760 | US$ 0,031205 / US$ 0,035135 | US$ 0,066372760 |
| Unhas | US$ 0,000032886 | US$ 0,028655 / US$ 0,032585 | US$ 0,061272886 |

Estimativa total **US$ 0,19161307**, a partir de uso retornado e tarifas
configuradas/documentadas; não é fatura nem inclui infraestrutura, mensageria,
suporte ou custo por peça aceita. Imagem usou `gpt-image-2.5-flare-2026-09-08`,
medium; interpretação usou `jev-1.14.0`. Os seis valores do ledger de domínio
permanecem incertos para faturamento; respostas não provam custo final. O efeito
textual anterior segue incerto e não foi reenviado.

O percurso de teste e o executor real foram exercitados com transportes mock
em PostgreSQL `_test`/Temporal antes do efeito; nove operações mock concluíram.
`make ci`: **1.920 testes**, 100% linhas e branches, Ruff/formatação e mypy em
152 módulos. As nove operações reais tiveram resposta e seis hashes de prévia
foram verificados, sem reenvio. O conjunto é pequeno, em dados fictícios, e não
homologa qualidade comercial, Meta nem conclusão da BL04.3.

As fotos, cenários, prompts de imagem, IDs, hashes, uso e arquivos completos
estão em `.local/evals/three-business-ab-20261029/`; credenciais não entram no
relatório. O ledger, banco dedicado e objetos privados ficam preservados.
