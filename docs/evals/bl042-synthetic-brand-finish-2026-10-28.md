# BL04.2 — ensaio sintético de imagem e acabamento (28/10/2026)

Este ensaio é **isolado** e não usa o worker ou dados de clientes. A autorização
adicional foi de até US$ 1; o runner `evaluate_bl042_guarded_v2.py` reservou
integralmente esse valor para uma única tentativa, em ledger independente do
ensaio anterior. Ele não reenvia após falha ou resultado desconhecido. A reserva
local não é um limite de faturamento imposto pelo fornecedor.

Foi usada uma foto CC0 de croissant e um kit/logo fictícios, com hashes fixos.
O modelo `gpt-image-2.5-flare-2026-09-08` gerou uma cena sem texto, em 1024×1280
e qualidade medium. Em seguida, o acabamento experimental aplicou os textos,
preço e logo fictícios do kit. O cenário criado não representa o interior de
um estabelecimento real, e a peça não está aprovada para publicação.

- Cena original local: `.local/evals/bl042-guarded-synthetic-v2/scene.png`.
- Prévia final local: `.local/evals/bl042-guarded-synthetic-v2/feed.png`.
- Uso retornado: 127 tokens de texto de entrada, 1.080 tokens de imagem de
  entrada e 378 tokens de imagem de saída.
- Estimativa por essas quantidades e [tarifas oficiais standard](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare):
  **US$ 0,020615**. Não é a fatura final nem custo por peça aceita ou por mês;
  não inclui texto, WhatsApp, infraestrutura, retrabalho ou impostos.
- Ledger permanece em `completed_unreconciled`, com US$ 1 reservado por
  segurança. Não houve reenvio automático nem nova chamada neste ensaio.

As imagens são geradas localmente no diretório ignorado pelo Git. A qualidade e
fidelidade devem ser avaliadas com materiais autorizados e titulares reais na
BL04.3. Este teste não conclui a integração da BL04.2 ao produto.
