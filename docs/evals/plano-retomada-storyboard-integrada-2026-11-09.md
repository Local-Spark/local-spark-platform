# Retomada proposta — quadros reais do Café Pausa

Estado: retomada executada; geração válida, render integrado falhou.
Três quadros locais após ajuste técnico estão disponíveis; decisão visual pendente.

## Falha preservada

A primeira tentativa do ponto 4 encerrou com `MOTION_AI_OUTPUT_LIMIT`:
resposta `incomplete`, motivo `max_output_tokens`, limite solicitado 32.000.
Uso reportado: 11.583 tokens de entrada e 21.252 de saída, incluindo 7.052 de
raciocínio. Não inferir que houve consumo de exatamente 32.000 tokens: o motivo
foi informado pelo provedor. Estimativa pelo uso: **US$ 0,241478**; reserva de
**US$ 0,85** retida, sem confundir estimativa com valor faturado.

O JSON foi cortado dentro do último campo descritivo. Inspeção estritamente local
mostrou também IDs repetidos entre cenas e momentos dos quadros expressos como
deslocamentos relativos. Nenhum reparo manual foi promovido para o produto.
Não houve imagem gerada, quadro real capturado, MP4, crítica ou repetição paga.
O worker dedicado foi parado; fontes, resposta original, efeitos e ledger preservados.

## Ajuste implementado

Instruções e descrições do schema agora explicitam identidade global dos elementos
com prefixo por cena e `keyframe_ms` absoluto desde o início da peça, com exemplo
numérico. Saída deve ser compacta e descrições concisas, preservando elaboração
visual. Validações existentes continuam estritas; não aceitamos JSON truncado.

Retomada propõe geração com 64.000 tokens de saída e crítica com 8.000, mesmo
modelo, fonte, kit e briefing. Contagem do payload e teto de custo continuam
obrigatórios antes de reservar/chamar. Limite maior não comprova sucesso futuro.
Não haverá correção automática nesta retomada.

105 testes direcionados passaram em 1,71 s; Ruff/format aprovados. Worker local
reconstruído apenas com os dois arquivos alterados. Renderer permanece o já
verificado nesta rodada; não repetimos render sintético nem CI completo.

## Limites propostos, dentro da autorização total anterior

- Até duas chamadas textuais: geração e crítica, com duas contagens.
- Até duas ilustrações opcionais, uma chamada por imagem, sem regeneração.
- Até **US$ 3,70** em novas reservas nesta retomada: US$ 1,70 textuais e US$ 2,00 imagens.
- Somando US$ 0,85 já retido: **US$ 4,55**, dentro dos US$ 5,40 autorizados.
- Teto global: US$ 11,35, incluindo US$ 7,65 anteriores já retidos.
- Imagens usam os mesmos parâmetros e regras do plano original; reserva é admissão
  local, não teto de fatura imposto pela Images API. Uso desconhecido/excedido para.
- Falha interrompe sem nova tentativa. Aceite humano exato da galeria antes do MP4.
- Mesmos dados fictícios enviados à OpenAI conforme plano original; sem novos
  materiais de terceiros ou conteúdo de cliente real.

A autorização específica foi obtida porque o plano original exigia parar após falha
e limitava a geração a 32.000 tokens. O orçamento total não aumentou.

Preparação local em `.local/evals/reel-storyboard-resume-20261109/`.
Payload inicial: 1.779.230 bytes, SHA-256
`2523c060938a20e1870780ff837722a2bbdcbed063992989586868f8f6b465e1`.

## Resultado da retomada

Uma chamada retornou `completed`, composição válida, 11.770 tokens de entrada e
15.070 de saída. Estimativa US$ 0,180125; reserva US$ 0,85 retida. Nenhuma imagem
foi solicitada. Total das duas tentativas: estimativa US$ 0,421603 e US$ 1,70 retidos.
Nenhuma crítica paga ou nova tentativa automática. Worker dedicado foi parado.

O render falhou com `MOTION_RENDER_EXECUTION_FAILED`. Código do modelo incluiu
tracks estáticas com `beats:[]`; runtime exige 1–12 beats. A instrução fornecida
não explicitava o mínimo; foi esclarecida, incluindo alternativa de hold idêntico.
Não alteramos o runtime nem trocamos os bytes vinculados aos pedidos antigos.

Diagnóstico corrigiu somente essas tracks na cópia local, com hold linear de
0 a 11.200 ms e `to=initial`. Original e correção estão preservados por hash em
`diagnostic-render.json`. Composição, desenhos, textos, kit, tempos e fonte não
foram redesenhados. Captura real pelo mesmo sandbox gerou três PNGs 720 × 1280,
protocolo 2, sem MP4, sem rede do browser e sem IA adicional.

[Galeria local após correção técnica](../../.local/evals/reel-storyboard-resume-20261109/diagnostic-gallery.html).
O pedido do produto continua encerrado com falha: esses arquivos não substituem
seu resultado nem um aceite persistido. Não há aprovação humana registrada.

Inspeção visual do agente: jarra, xícara, fio de líquido e vapor se relacionam à
mensagem, mas as três cenas repetem vídeo à esquerda e desenho à direita. Ainda
não demonstra o nível de elaboração das referências. Titular recebeu entrevista
para decidir entre reformular composição ou avaliar movimento dessa direção.

Validação da instrução: cinco testes direcionados em 0,68 s e Ruff aprovados.
Sem CI completo, suíte de banco ou testes amplos adicionais. Resta fechar direção,
resolver a continuidade integrada preservando efeitos/custos e avaliar vídeo com
som; nenhuma expansão de formatos iniciada.

## Decisão posterior do titular

O titular gostou das xícaras desenhadas e autorizou reformular a composição antes
do vídeo. Não houve aprovação da galeria para animação. Próxima execução registrada
no [plano de reformulação](plano-reformulacao-composicao-2026-11-09.md).
