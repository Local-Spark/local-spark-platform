# BL04 — ensaio visual sintético vertical, 27/10/2026

Estado: ensaio isolado com chamada real; **não é integração do fluxo do produto nem aceite comercial**. O usuário autorizou até US$ 1 no total para testes de imagem com dados fictícios; esta execução usou uma chamada. A evidência é uma amostra única, sem aprovação de titular ou cálculo de custo mensal.

## Caso e execução

O negócio Café do Cedro e o logo são fictícios; o produto usa uma fotografia CC0 da fixture `visual-context-cafe-v1.json`, não uma foto documental de cliente. A partir do briefing de `scripts/evaluate_visual_context.py`, trocou-se o pedido de feed por uma arte vertical para story; foram enviadas só a fotografia do produto e o logo fictício, separadas. A chamada usou o novo adapter isolado `OpenAIVisualProvider` com `gpt-image-2.5-flare-2026-09-08`, qualidade `medium`, JPEG e 1024 × 1792. Essa proporção é próxima, mas não idêntica, a 9:16; uma receita de story precisa verificar formato e áreas seguras.

O arquivo privado local é `.local/evals/bl04-synthetic-story-v1/story.jpg`; o relatório local é `attempt.json`, com uso, identificadores e SHA-256. A pasta `.local` não integra o repositório. A execução guardou o intento antes da chamada, sem repetição automática; é ensaio local, **não** usa o ledger multi-tenant nem substitui o controle do produto.

## Resultado e limites

- Uma chamada concluída, **13,72 s**, 469 tokens de texto e 1.574 de imagem na entrada, 323 tokens de imagem na saída. Custo **estimado** pelos preços fixados no ensaio: **US$ 0,024627**; consultar fatura para cobrança efetiva. Não inclui operação, armazenagem, texto, revisões, mensageria ou infraestrutura.
- Inspeção visual inicial do desenvolvedor: o produto é reconhecível e o preço `R$ 18` aparece correto; a cena e composição foram geradas a partir da fotografia de referência e não demonstram um ambiente real.
- O logotipo foi redesenhado em vez de fielmente preservado; a chamada para ação aparece com ponto final adicional em relação ao literal solicitado. O texto na faixa inferior e as áreas seguras também precisam de avaliação real em celular. Esses achados impedem afirmar fidelidade literal; aplicação determinística do logo/texto ou validação/revisão devem ser comparadas.
- A amostra não demonstra estabilidade, qualidade para outros segmentos, direitos sobre mídia real, fidelidade ao estabelecimento nem aprovação do cliente. A hipótese de R$ 50 de custo total mensal continua aberta. Nenhuma peça foi publicada.

Comparação futura exige outro conjunto com fontes consentidas, prévia de feed e story, razões de recusa, custo por peça aceita incluindo tentativas e revisão pelo titular; caminhos pagos de clientes requerem consentimentos e ledger integrados antes da chamada.
