# Ensaio visual com IA: croissant de demonstração

Data: 26/10/2026. Status: **conceito visual privado e uma edição da API direta
medida; qualidade comercial e custo mensal ainda não validados**. Não é peça da
Priscila Silveira nem publicação autorizada. A fonte foi
a [foto CC0 de Petr Kratochvil no Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Croissant-newspaper-and-tea.jpg),
SHA-256 `519772437eca1f7d2383edeebf80dc4beaf3d5e3039910cee5b975643de182ed`.
Não foi usado qualquer material da cafeteria real.

## Execução e resultado

- O renderer atual gerou `current-template-baseline.jpg` com a foto CC0 e texto
  demonstrativo. O resultado continua com o painel grande e CTA genérico.
- A ferramenta de imagem disponível na sessão editou a fonte para criar
  `ai-photo-concept.png`: croissant em cenário fictício de café, foto vertical,
  fundo verde/madeira e espaço para título. Em segunda edição, produziu
  `ai-post-concept.png` com a cópia exata “Uma pausa para saborear.” e “Café e
  croissant.”, sem preço ou marca de cliente. As duas saídas e a entrada ficam
  apenas em `.local/evals/ai-visual-2026-10-26/` (fora do Git). A ferramenta
  integrada não expôs identificador do modelo, `usage` nem cobrança por chamada.
- A composição final dá ao produto mais destaque e tem melhor hierarquia que o
  baseline. O texto da amostra é legível e correto. A IA recriou pixels do
  croissant e introduziu mesa/ambiente/xícara que não constavam no original:
  isto demonstra **capacidade visual**, não fidelidade de produto/local real.
  Somente proprietário com originais autorizados pode aceitar a peça para uso.

## Tentativa de medir a API direta

Foi feita **uma** chamada de edição na conta configurada em `.env`, modelo
`gpt-image-2.5-flare`, `quality=high`, `size=1024x1280`, `n=1`, com a foto CC0.
Resposta HTTP `429`, `insufficient_quota`, `credit_balance_exhausted` em 1,27 s.
Nenhuma imagem veio da API direta; portanto não há `usage` nem custo faturado
medido. Não repetimos chamadas naquele momento. O saldo da conta/projeto
associado à chave precisou ser corrigido antes do benchmark de custo real. Créditos da ferramenta
integrada ou de ChatGPT/Codex não equivalem a créditos dessa API.

Após o usuário adicionar créditos, repetimos **uma** chamada com a mesma foto
CC0 e configuração (`gpt-image-2.5-flare`, `high`, 1024×1280, JPEG). A API
retornou a edição `ai-edited-croissant.jpg` em 19,56 s, com `usage` de 1.080
tokens de imagem de entrada, 189 de texto e 1.510 de imagem de saída. Pelas
[tarifas oficiais Standard do modelo](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare),
o custo calculado desta **única chamada** é
`(1080×8 + 189×5 + 1510×30)/1.000.000 = US$ 0,054885`, aproximadamente
R$ 0,30 usando a PTAX de referência citada abaixo, antes de impostos e spread.
Arquivo, prompt e metadados completos permanecem em `.local/evals/ai-visual-2026-10-26/`.
A saída é visualmente mais atraente que o template, mas recria o croissant e o
cenário; ela não prova fidelidade ao produto ou ao local de um cliente. Também
não inclui texto final, logo, revisão, mensagens, publicação ou vídeo.

## Preço de referência, separado da medição

Os [preços publicados pela Runway](https://docs.dev.runwayml.com/guides/pricing/)
para `gpt_image_2_5_flare`/`sunburst` em **1K, 4:5, high**, são 8 créditos por
imagem + 1 crédito por referência, a US$ 0,01/crédito: **US$ 0,09 por edição**;
duas edições seriam **US$ 0,18** nessa rota. À
[PTAX de venda de 26/10/2026, R$ 5,5007/US$](https://ptax.bcb.gov.br/ptax_internet/consultarTodasAsMoedas.do?method=consultaTodasMoedas),
isso equivale aproximadamente a **R$ 0,50** e **R$ 0,99**, antes de impostos,
spread, retries e outras etapas. É uma configuração *comparável* de outro
fornecedor, **não** o preço ou modelo identificável das imagens geradas pela
ferramenta integrada e não representa a fatura da OpenAI. Na API direta da
OpenAI, GPT Image 2.5 é cobrado por tokens de imagem/texto efetivamente usados;
a medição de uma chamada com `usage` está acima. Ver
[tarifas oficiais](https://developers.openai.com/api/docs/pricing) e
[guia de custos](https://developers.openai.com/api/docs/guides/image-generation).

Para uma operação de produção, uma edição visual paga e tipografia exata em
compositor local podem custar menos do que duas edições pagas; isso requer
comparar **qualidade e custo por peça aceita**, incluindo imagens rejeitadas e
retrabalho. O ensaio não mede vídeo, avatar, WhatsApp, infraestrutura nem o
custo mensal total do plano de R$ 99. Próximo teste: fonte original autorizada,
edição que não invente o local/produto, revisão do dono e medição integral de
uma peça aceita.
