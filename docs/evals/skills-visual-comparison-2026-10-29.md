# Ensaio visual com e sem skill — 29/10/2026

O proprietário autorizou até **US$ 5 no total** para comparar duas imagens reais
com e sem skill, usando fontes fictícias ou de uso autorizado, sem publicação.
O ensaio concluiu duas direções textuais e duas imagens de feed; é laboratório
isolado, não execução do worker, API, Temporal ou guarda multi-tenant do produto.
O resultado é uma peça por grupo, não demonstra ganho consistente ou aceitação.

## Insumos e método

- Negócio fictício Café do Cedro, pedido de feed para croissant de manteiga por
  R$ 18 e CTA WhatsApp; preço e contexto são apenas fatos do fixture.
- Mesma [fotografia CC0](assets/croissant-cc0.jpg), kit e logo sintético,
  cópia, CTA, proporção 1024×1280 e acabamento `render_brand_overlay` em ambos.
  A fotografia é de banco de imagens, não do produto real de uma cafeteria.
- Mesmo `gpt-5-mini` e contrato para duas direções de enquadramento, luz e
  fundo; apenas o segundo pedido acrescenta o conteúdo integral da skill de
  feed. As direções foram incluídas nos prompts das imagens. Mesmo adapter
  `OpenAIVisualProvider`, `gpt-image-2.5-flare-2026-09-08`, edição da mesma foto,
  qualidade medium e PNG; o texto e o logo foram aplicados depois igualmente.
- O teste isola influência da orientação da skill **na cena**; texto, legenda,
  CTA, layout do acabamento, fidelidade de cliente e jornada não foram comparados.
  Não houve pesquisa externa ou uso de concorrentes.

As direções foram inspecionadas antes das imagens. Ambas propuseram prato; a
direção com skill também propôs guardanapo e composição quadrada. Essas sugestões
conflitavam com restrições comuns de não adicionar objetos e usar 4:5. Os prompts
conservaram as direções integrais como propostas e repetiram as restrições, sem
regenerar ou reescrever as respostas. O resultado visual contém prato em ambos e
o que parece ser tecido no canto da imagem com skill: o modelo não demonstrou
obedecer integralmente à restrição de objetos. A saída final tem as dimensões 4:5
nos dois casos. Essa divergência deve ser considerada na avaliação.

## Arquivos e observações

- Sem skill: `.local/evals/visual-skill-ab-20261029/control_image-final.png`,
  SHA-256 `c8d6ca566b09100bf1e9b2277530e9f70ce3814c093bb26821c013ddcf0f7623`.
- Com skill: `.local/evals/visual-skill-ab-20261029/skill_image-final.png`,
  SHA-256 `eff8101170481e4d83edb8963f29eb1b3320b06ac997369a5988cb27454d9365`.

Na inspeção inicial, a segunda peça mostra o croissant maior e mais próximo do
centro; ambas preservam o texto fixo visível. O logo no canto superior direito
está pequeno dentro de um bloco claro e o topo das peças tem espaço vazio amplo;
isso precisa de revisão humana, especialmente no celular. Não declarar que uma
é melhor em caráter geral: a geração é estocástica e não há revisão de titular.

O diretório local ignorado pelo Git preserva cenas, arquivos finais, respostas e
uso no ledger, os pedidos textuais em `text-requests.json`, prompts visuais em
`image-requests.json`, a revisão em `revisao-direcoes.md`, o runner e testes
usados, além da cópia da skill. O ledger fixa o pedido por hash antes do efeito.

## Custos e validação

Quatro operações concluídas: texto sem skill 252/458 tokens entrada/saída;
texto com skill 1.105/489; imagem sem skill 1.503/378; imagem com skill
1.506/378. Pelas tarifas standard dos modelos na data do ensaio, a estimativa
de uso é **US$ 0,04643825** no total: US$ 0,000979 e US$ 0,00125425 em texto;
US$ 0,022095 e US$ 0,022110 em imagem. Fontes: [tarifas do modelo de texto](https://developers.openai.com/api/docs/models/gpt-5-mini)
e [tarifas do modelo de imagem](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare).
É estimativa, não fatura nem custo por peça aceita; não inclui infraestrutura,
suporte ou mensageria. O ledger conserva quatro holds de US$ 1,25, total US$ 5,
sem liquidação automática; esse controle não limita a fatura externa.

Dry run e 15 testes mock passaram; os quatro efeitos reais tiveram retorno
completo, sem reenvio automático. A tentativa anterior de texto permanece
incerta em ledger separado, sem reenvio e sem custo conhecido. Não houve
publicação ou dados de cliente. Revisão por titular, teste pelo produto e
medição de rejeição/refação/custo por aceita continuam pendentes.
