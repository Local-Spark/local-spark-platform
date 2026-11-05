# Ensaio direto de vídeo e carrossel com motion — 04/11/2026

O titular rejeitou as primeiras prévias por terem pouco movimento e pediu um
ensaio seguindo o [procedimento rápido](../design/ensaios-rapidos-qualidade.md),
com cortes, transições, efeitos, música, locução e legendas dinâmicas. Esta
rodada usa o caso fictício de cafeteria e executa as etapas em processo local,
sem preparar banco, Temporal, fila, API ou frontend para a avaliação.

**Estado:** pedidos, interpretações Jev reais e planos de direção foram
recebidos; as peças foram montadas e aguardam revisão. Não há evidência de
publicação ou aprovação pelo titular. Uma avaliação visual e auditiva é
necessária para aferir a qualidade dos resultados.

## Entradas e etapas efetivamente executadas

| Etapa | Vídeo | Carrossel |
| --- | --- | --- |
| Mensagem simulada | “Gravei um pouco da preparação do café. Faça um reel com cortes, transições, motion graphics e legendas para convidar as pessoas para uma pausa.” | “Crie um carrossel animado para apresentar nosso croissant, com motion graphics e uma sequência convidativa.” |
| Interpretação | Jev real `jev-1.14.0`: pedido de conteúdo, decisão `clarify`, formato não selecionado. | Jev real `jev-1.14.0`: pedido de conteúdo, decisão `clarify`, formato não selecionado. |
| Direção | `gpt-5-mini`, recebendo seis quadros amostrados da gravação, kit, skill, referências e pedido. | `gpt-5-mini`, recebendo três imagens do kit, skill, referências e pedido. |
| Saída do modelo | Plano para reel de 15 segundos, com cenas, textos, legendas e indicações de áudio; retornou também um segundo render não solicitado. | Plano com três páginas de aproximadamente quatro segundos cada, com composição, movimento, legendas e áudio. |

O Jev atual só oferece seleção de `photo` e `story`; seus guardas tratam
explicitamente vídeo e carrossel como indisponíveis. Assim, as duas respostas
`clarify` são o resultado real dessa etapa, e não uma autorização automática de
produção. Para prosseguir com a experiência, a direção audiovisual foi uma
**adaptação experimental**, executada separadamente. Ela parte da configuração
do builder editorial de imagem, mas substitui seu prompt e formato de saída por
um contrato de cenas, keyframes, legendas e áudio. Não representa um adapter de
vídeo integrado nem comprova o comportamento do produto completo.

O modelo de direção recebeu os seis quadros de 0, 3, 6, 9, 12 e 15 segundos;
ele não recebeu o vídeo completo nem ouviu seu áudio. Os arquivos de pedido
registram o prompt e os hashes dos quadros, em vez de armazenar imagens em
base64 no relatório. O áudio original foi excluído; a locução sintética proposta
é uma criação de demonstração e não é fala da pessoa retratada. Os planos de
tempo das legendas exigem conferência contra a locução efetivamente produzida.

## Fontes e referências

- Negócio fictício da rodada BL04.3 e kit demonstrativo `cafe-pausas` v1,
  com cores verde, creme e caramelo e fontes DejaVu. Imagens do carrossel são
  acervo de demonstração gerado para o kit; não são registros de um negócio real.
- Vídeo ilustrativo [Latte Coffee making, de Stevenndori289](https://commons.wikimedia.org/wiki/File:Latte_Coffee_making.webm),
  SHA-256 `e08e6c32cec59e6d5117a94aa726e9c959f67183b39efb2476973778c408ae26`,
  17,7 s, licenciado sob [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
  A gravação foi editada e não representa a cafeteria fictícia; contém pessoa e
  marca de terceiros. Observar atribuição, alterações e condições da licença ao
  compartilhar a versão adaptada.
- Skills próprias `instagram-reel` e `instagram-carrossel-motion`, com seus
  hashes e texto registrados nos respectivos inputs; ainda não estão integradas
  ao seletor de produção.
- Contexto inclui nove padrões gerais da referência manual com análise parcial
  e uma referência indisponível, sem padrões. Os nove padrões ainda não foram
  conferidos contra as publicações originais; não houve nova coleta ou cópia de
  posts. O ensaio não inclui controle sem referências e não mede seu efeito.

O plano do carrossel introduziu alegações não confirmadas como croissant
“quentinho” e “café fresco”, apesar das instruções para usar fatos confirmados.
Esses textos foram removidos da montagem; a saída original e as adaptações foram
preservadas. O modelo também retornou um render adicional não solicitado no
caso de vídeo, que não foi usado.

## Rastreabilidade

Os materiais privados estão em `.local/evals/motion-valid-2026-11-04/real-v1/`.
Em cada diretório `video` e `carrossel`, `context.json` registra insumos;
`jev-request.json`, `jev-response.json` e `jev-decision.json` registram o Jev;
`direction-request.json`, `direction-response.json` e `direction-plan.json`
registram a chamada e o plano de direção. `ledger.jsonl` contém identidade,
hash, reserva e resultado de cada chamada. Os arquivos são privados e não devem
conter credenciais ou URLs assinadas.

Para o vídeo, `render-adaptacoes.md` registra as alterações necessárias ao
executar o plano, inclusive conversão de tempos, escolha de trechos, ajuste de
legibilidade, locução sintética e ausência de reverb/ducking. A sincronização
das palavras foi estimada a partir da duração das frases, não obtida por
reconhecimento forçado; exige verificação auditiva. A trilha identificada nas
adaptações é [Jazz Piano, Serolillo](https://commons.wikimedia.org/wiki/File:Jazz_Piano.ogg),
sob [CC BY 2.5](https://creativecommons.org/licenses/by/2.5/). Efeitos de chiado
e clique foram produzidos localmente, sem aproveitar o áudio original.

As peças disponíveis para revisão são:

- [Reel de 15 segundos](../../.local/evals/motion-valid-2026-11-04/real-v1/video/reel-motion-v1.mp4), com cortes, transições, locução sintética, trilha, efeitos e legendas animadas.
- Carrossel com três MP4s e PNGs: [página 1](../../.local/evals/motion-valid-2026-11-04/render/carrossel/pagina-1.mp4), [página 2](../../.local/evals/motion-valid-2026-11-04/render/carrossel/pagina-2.mp4) e [página 3](../../.local/evals/motion-valid-2026-11-04/render/carrossel/pagina-3.mp4); os PNGs estão na mesma pasta. As [adaptações do carrossel](../../.local/evals/motion-valid-2026-11-04/render/carrossel/ADAPTACOES.md) incluem a retirada das alegações não confirmadas e ajustes dos tempos.

Todos os MP4s têm vídeo H.264 e áudio AAC; foram decodificados e seus quadros
inspecionados. O áudio foi medido como não silencioso, mas não foi feita revisão
auditiva perceptiva; palavras das legendas do Reel usam tempos estimados dentro
das frases e as do carrossel acompanham trechos medidos, não alinhamento por
palavra. A gravação de origem tem apenas 360 × 640 e foi ampliada. A direção
produzida pelo modelo é simples e ainda não demonstra motion graphics
sofisticado. A emenda dos loops e aceitação da proporção pelo Instagram não
foram verificadas.

## Orçamento e limites

O titular autorizou até **US$ 0,50 em reservas**, aceitando que a cobrança real
possa superar a reserva. O ledger preserva quatro operações concluídas:

| Operação | Reserva USD | Custo estimado USD |
| --- | ---: | ---: |
| Jev — vídeo | 0,010000 | 0,000030 |
| Direção — vídeo | 0,150000 | 0,010267 |
| Jev — carrossel | 0,010000 | 0,000030 |
| Direção — carrossel | 0,150000 | 0,008744 |
| **Total** | **0,320000** | **0,019071** |

A estimativa usa o consumo informado pelas respostas e tarifas consultadas,
incluindo arredondamento no ledger; não é fatura nem inclui infraestrutura,
operação e trabalho. As reservas limitam novas admissões do ensaio, sem impor
um teto absoluto à cobrança do fornecedor. Não houve retentativa automática;
uma chamada incerta mantém sua reserva e não deve ser reenviada. Custo por
peça aceita depende da revisão do titular e de despesas efetivamente apuradas.

Não foi feita transcrição de fala real, e o experimento não comprova geração de
vídeo integrada, edição automática do produto, uso no Instagram, loop em todas
as plataformas ou publicação. A qualidade e a sincronização devem ser revistas
com o titular antes de decidir próximos ajustes.
