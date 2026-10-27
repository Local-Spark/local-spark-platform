# BL04.2 — ensaio sintético isolado de feed

Data: 27/10/2026. Resultado: uma chamada real com dados fictícios; **não é
geração integrada ao produto nem aceite comercial**. Não foi enviada foto ou
informação de cliente. O café e seu logotipo são fictícios; a foto é uma
[referência CC0](https://commons.wikimedia.org/wiki/File:Croissant-newspaper-and-tea.jpg).

O runner `scripts/evaluate_bl042_guarded.py` valida por SHA o fixture, a foto e
o logo antes de construir o pedido. Não aceita caminhos, textos ou fontes
arbitrárias na CLI. Usa `gpt-image-2.5-flare-2026-09-08`, qualidade medium,
1024 × 1280, com uma chamada e sem retry. A intenção e os valores reservados
ficam em `.local/evals/bl042-guarded-synthetic/budget.sqlite3`; um lock e
transação SQLite impedem duas reservas concorrentes locais. As reservas não são
liberadas quando a chamada termina nem em caso de resultado incerto.

O orçamento autorizado foi de **até US$ 1 para testes de imagem fictícios**.
O ledger reserva **US$ 0,50 para histórico** e **US$ 0,50 para esta única
chamada**. Os gastos históricos encontrados somam pelo menos **US$ 0,300559 em
estimativas parciais**, incluindo os ensaios anteriores de contexto e kit; não
são fatura e a reserva histórica é uma margem conservadora. O valor reservado
para a nova chamada é outro limite interno estimado, **não um teto imposto pelo
provedor nem garantia de valor faturado**. O runner bloqueia outra chamada,
mesmo após sucesso, timeout ou reinício. O controle só cobre este runner, não
outros scripts ou uma conta inteira; não apagar/recriar o ledger para repetir.

## Resultado

- Arte privada: `.local/evals/bl042-guarded-synthetic/feed.jpg`; SHA-256
  `bf22ff0b2bfd871bf662419990cff6b5c6fb4db16732e617e2a5d77a3a084754`.
- Uma chamada concluída; uso relatado: **1.574 tokens de imagem e 468 de texto
  na entrada; 378 tokens de imagem na saída**.
- Estimativa calculada pelas [tarifas Standard da OpenAI](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare):
  **US$ 0,026272**. Não é a fatura e não inclui outras etapas, infraestrutura,
  rejeições ou revisões.
- A inspeção inicial mostra composição legível com produto em destaque e preço
  pedido. O logo foi redesenhado, o CTA recebeu um ponto adicional e o ambiente
  foi criado pela IA; o resultado não comprova fidelidade documental nem passa
  no gate de texto/logo literal.
- Os sete testes offline incluem bloqueio de fixture modificada, concorrência
  entre processos, replay, timeout e crash. Eles não fazem chamadas pagas.

Esta amostra não valida qualidade comercial nem custo por peça aceita. Um teste
com material real exige direitos e autorização do titular, controles completos
do pipeline e aprovação antes de qualquer publicação.
