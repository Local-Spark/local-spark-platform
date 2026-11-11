# Ensaio exploratório de motion intenso — 06/11/2026

Rodada concluída: [MP4 intenso, comparação e evidências](ensaio-motion-intenso-2026-11-06.md).
Uma chamada, estimativa US$ 0,3086025, código renderizado como recebido.
Avaliação criativa final permanece com o titular; abaixo, o plano preservado.

## Pedido e objetivo

O titular percebeu melhora na rodada `276486`, gostou da peça e ainda prefere
o v2 mínimo. Destacou a inversão de tema — verde/letras claras para fundo
claro/letras verdes — como contraste agradável. Pediu uma versão mais robusta,
**“exagerada”**, para explorar o repertório de motion graphics.

É uma variante experimental do mesmo caso, não estilo universal ou definição
automática para todas as peças comerciais. V2 continua piso, sem copiar seu
layout/roteiro. Revisão humana permanece somente no MP4 final.

## Direção preparada

- Três momentos fortes, com intensidade alternada com pausas de leitura.
- Temas verde e creme com cores do texto invertidas; transições por máscara
  preservando contraste, sem deixar fundo/letras com cores iguais no meio.
- Janela viva, com mudanças amplas de proporção, posição, foco e escala;
  enquadramento retrato sustentado e transições geométricas contínuas.
- Forma/ponto com presença e consequência: antecipação, compressão, percurso,
  contato, abertura/reorganização e metamorfose, além de tipografia por máscaras.
- Explorar ao menos um mecanismo adicional do `showreel` já fornecido:
  padrões de arcos em ondas (`cap5`), letras que mudam de linha (`cap6`),
  `faisca` ou maior desenvolvimento da morfose. Reusar código pertinente em
  composição própria, mantendo uma linguagem coerente e o material legível.

Mesmo vídeo, voz integral, kit, fontes, 720×1280, 30 fps e 11.180 ms nominais.
A interpretação Jev e transcrição permanecem caches históricos identificados.
Não há nova pesquisa, asset pago, imagem, TTS, música ou vídeo generativo.
Skill própria Reel e fontes MIT selecionadas na rodada anterior continuam
incluídas. São os mesmos oito quadros do material/v2; nenhuma mídia da galeria
será enviada. As funções adicionais já estão no código original preservado.

## Pedido e orçamento

Arquivos privados:
`.local/evals/motion-intense-round-2026-11-06/proposal/`.
`instructions.md`, `input.md`, `request.json`, `manifest.json` e
`cafe-reel-intense.json` permitem revisar o pedido. O `prepare.py` é offline,
não lê credenciais e não transmite dados.

SHA-256 do pedido:
`b7de85fc1507409bbf8eac1b91bf8f108f85ede528f6787bc013a477072b8124`.
Corpo de 2.076.774 bytes e 122.365 caracteres textuais; bytes/caracteres não
determinam tokens nem cobrança. Preflight offline do cenário passou.

Plano: **uma chamada `gpt-6.1-sol/high`**, serviço padrão, até 32.000 tokens de
saída, depois render local. Estimativa **US$ 0,30–0,70**, reserva e teto
operacional **US$ 0,75 adicionais**, sem refação automática. Referência de
tarifa consultada nesta sessão: entrada US$ 2/M, cache-write US$ 2,50/M e saída
US$ 10/M; raciocínio já compõe a saída. O CLI usa custo conservador de entrada.
Estimativa não é fatura. [Preços oficiais](https://developers.openai.com/api/docs/pricing?latest-pricing-expanded=true).

**Autorizado pelo titular:** uma chamada e envio deste pacote, até US$ 0,75
adicionais, sem refação automática. Operação iniciada:
`b14bc09d-4131-4018-b666-1f9d0fff8651`; autorização em
`.local/evals/motion-intense-round-2026-11-06/authorization.json`.
Não reaproveitar orçamentos anteriores. A autorização inclui envio do pacote a
`api.openai.com/v1/responses`. O teto controla iniciar a chamada, não limita a
cobrança por uma chamada já iniciada. Identidade e reserva duráveis antes da
rede; falha incerta ou resposta rejeitada não autorizam refação automática.

## Execução e demonstração

```sh
make motion-eval EXECUTE=1 BUDGET_USD=0.75 MOTION_CASE=.local/evals/motion-intense-round-2026-11-06/proposal/cafe-reel-intense.json
```

Essa variante é selecionada explicitamente, sem alterar o cenário padrão
moderado do comando. O mesmo renderer executa a composição recebida, sem
novas dependências/infraestrutura. O relatório compara **versão intensa**,
**v2 mínimo** e **biblioteca — última versão**, com MP4s locais, downloads,
inputs/outputs, código, custo e trace congelados. Preservar qualquer falha ou
intervenção; não apresentar alterações manuais como resposta intocada.

Depois da geração, conferir mudanças reais de tema, leitura, geometria,
uso dos mecanismos, primeiro/último quadro, áudio e fidelidade do render.
Intensidade não demonstra automaticamente melhor qualidade. A avaliação é
da peça final pelo titular; não fixar nota automática como aceite.
Não há alteração do pipeline de produto ou necessidade de banco/Temporal
para este ensaio. Testes do CLI/renderer existentes continuam válidos para o
contrato; CI integral não foi repetido apenas para preparar esta variante.
