# Continuação motion 1c — chamadas encerradas no teto global

Preparada em 05/11/2026 e conferida na retomada de 06/11/2026.
**As sete chamadas autorizadas foram executadas e encerradas em 06/11/2026,
sem refação paga e mantendo o teto global de US$ 1,60.** Houve autorização
específica do titular para retomar as duas operações restantes após a rejeição
do Reel; as revisões técnicas e a revisão automática foram registradas antes
de prosseguir. Não restam operações pagas não iniciadas nesta rodada.
Ver [resultado e intervenções locais](ensaio-motion-v0-rodada-1c-2026-11-06.md).
A [rodada 1b](ensaio-motion-v0-rodada-1b-2026-11-05.md) foi interrompida após
uma resposta Jev recebida/rejeitada. A reserva de US$ 0,01 e a estimativa de
US$ 0,000035 permanecem registradas; seu ledger não foi alterado ou reiniciado.

O ledger da 1c contém **14 eventos para sete operações únicas**. As três
interpretações Jev e a transcrição foram aceitas localmente. As três direções
retornaram `completed` pelo provedor, mas foram **rejeitadas pela validação
local**. Isso não é falha de transporte nem aprovação da peça. As respostas
originais permanecem intactas; correções e renders locais são derivações
identificadas separadamente, sem substituir o resultado original.

O [fechamento](../../.local/evals/motion-v0-rodada-1c-2026-11-05/round/round-closed.json)
e a [conferência de custos das sete chamadas](../../.local/evals/motion-v0-rodada-1c-2026-11-05/round/cost-review-after-seven-calls.json)
registram **US$ 0,263038 estimados na 1c**, mais US$ 0,000035 da 1b:
**US$ 0,263073 no total**, sem confirmação de fatura. A estimativa é conservadora:
todos os tokens de entrada de direção, inclusive leituras de cache, usam a
tarifa de escrita curta; raciocínio já está incluído nos tokens de saída.
As reservas permanecem integralmente em **US$ 1,55**, sem devolução. Saldo no teto
não autoriza outra chamada. O [inventário de fechamento](../../.local/evals/motion-v0-rodada-1c-2026-11-05/round-closeout-inventory.json)
preserva hashes dos registros, sem alterar inventários ou custos anteriores.

## O que muda

O adapter corrigido deixa de perguntar qual item selecionar quando não recebe
candidatos selecionáveis. Intenção e formato continuam sendo avaliados pelo
Jev com os limiares existentes. Isso não confirma fatos ou prontidão da peça,
nem altera a resposta anterior. Foram criadas novas identidades para sete
operações; os IDs simulados também são separados dos reais.

Mantêm-se os três casos, mensagens, mídia fictícia, kit, catálogo automático,
contrato v2, modelos, configuração standard/cache e limites do
[plano 1b](plano-motion-v0-rodada-1b-2026-11-05.md). A preparação inclui cópias e
hashes dos códigos usados; o executor verifica o hash do adapter Jev, e o
preflight confere as demais fontes. As provas sintéticas do renderer foram
preservadas, sem repeti-las ou apresentá-las como novas peças criativas.

A entrada de direção distingue as capacidades do compilador visual do produto
das do protótipo privado usado neste ensaio. Neste último, há mixagem ou silêncio
explícito, até duas faixas, velocidade 1:1 e ganho não positivo. O trace preserva
as duas descrições. Somente a afirmação de ausência de mixer das fichas recebe
esse esclarecimento de escopo; continuam vigentes as restrições de velocidade,
código, direitos, isolamento e revisão da fala. Fichas, hashes e anexos não mudam.

## Plano autorizado e executado

| Etapa | Executadas | Reserva preservada |
| --- | ---: | ---: |
| Jev, uma interpretação nova para cada caso | 3 | US$ 0,03 |
| Transcrição do Reel | 1 | US$ 0,01 |
| Direção de Reel, story e carrossel | 3 | US$ 1,50 |
| **Novas operações** | **7** | **US$ 1,54** |

- Estimativa original de planejamento: **US$ 1,00–1,50**, com as hipóteses e
  incertezas de tokens de imagem do plano 1b; não é fatura ou valor garantido.
- Reserva anterior mantida: **US$ 0,01**.
- Comprometimento total ao encerrar: **US$ 1,55**.
- **Teto global permanece US$ 1,60.** O executor 1c aplica limite próprio de
  **US$ 1,59**, descontando conservadoramente a reserva anterior.

A continuação inclui repetir a interpretação do Reel com pedido corrigido;
portanto foram oito chamadas somadas à tentativa da 1b, sendo sete na 1c.
Não incluiu refação automática. Resposta incerta/rejeitada ou gasto
incompatível interrompe a execução, conservando operação e reserva. O teto
limita o início das chamadas; não limita a cobrança do fornecedor por uma
chamada já iniciada.

As retomadas técnicas não repetiram Reel ou story. Elas permitiram somente
operações ainda não iniciadas do plano, com revisão explícita, hashes de resposta,
patches e derivados; preservaram cada rejeição e reserva. Os pedidos de story e
carrossel receberam esclarecimento de unidades e invariantes como sufixo de
instruções antes de serem enviados, mantendo os demais campos iguais. O carrossel
usou o mesmo pedido esclarecido já revisado. Não há nova tentativa ou continuidade
paga autorizada pelo fechamento.

O [vínculo de orçamento](../../.local/evals/motion-v0-rodada-1c-2026-11-05/budget-binding.json)
identifica hashes do ledger e da interrupção anteriores. A readiness técnica
vincula esse arquivo por hash, e o executor confere os registros anteriores e
a aritmética do teto antes de acessar credenciais e imediatamente antes da rede.
Mudança após reservar a nova operação conserva resultado incerto, sem envio.
A rodada antiga permanece encerrada; não usar
as seis operações antigas que não foram iniciadas para executar a continuação.

## Preparação verificável

- [Manifesto para revisão](../../.local/evals/motion-v0-rodada-1c-2026-11-05/prepared-for-review.json),
  com round ID `c517e08c-7615-4375-b158-e77f635a73b9`.
- [Manifesto das fontes de código](../../.local/evals/motion-v0-rodada-1c-2026-11-05/provenance/source-manifest.json).
- [Prontidão técnica e CI](../../.local/evals/motion-v0-rodada-1c-2026-11-05/round/technical-readiness.json)
  conferidos em 06/11/2026; o registro vincula pedidos, fontes, orçamento e log.
  Caches Python gerados por importação ficam fora do inventário de evidências;
  fontes e arquivos de entrada permanecem verificados. Isso não concede orçamento.
- Os três pedidos Jev enviados não contêm pergunta `offering` com candidatos
  vazios. A direção do Reel usou transcrição revisada da fixture, sem alinhamento
  por palavra, com hash do pedido final conferido antes da chamada.
- A preparação inicial passou em 53 testes locais; as extensões de retomada
  fecharam em **88 testes com mocks**, incluindo orçamento, adulteração, replay
  e preservação de rejeições/reservas. O [registro dos testes](../../.local/evals/motion-v0-rodada-1c-2026-11-05/technical-recovery-v2-tests.log)
  conserva a saída já retornada, sem declarar outra execução. O adapter passou em
  55 testes dirigidos com cobertura de 100%; o CI integral da correção passou:
  **5.044 testes Python e 62 Node**, sem pulados e com cobertura de 100%.
- A autorização específica foi registrada em `round/grant.json`, vinculada
  ao manifesto e à prontidão técnica. O ledger real registra a execução;
  autorização de chamadas não é aprovação da peça ou de publicação.
- [Ficha para avaliar as peças](../../.local/evals/motion-v0-rodada-1c-2026-11-05/creative-acceptance.md)
  preparada com critérios técnicos, criativos e comparação com o Reel v2.

Com o CI concluído, a continuação foi apresentada em entrevista e autorizada.
A concessão vinculada aos hashes permite somente as sete operações propostas.
Não há necessidade de repetir a pesquisa ou criar banco para o ensaio criativo.
O executor não mantém uma trava sobre o ledger anterior durante a chamada;
este controle local pressupõe que a rodada encerrada não seja modificada por
outro processo após a última conferência. Não é um ledger de produção.

## Trabalho restante após encerrar as chamadas

Conferir os patches e as peças derivadas, preservar seus manifests e avaliar
legibilidade, movimento, cortes, áudio e fidelidade das legendas com revisão
humana. As três rejeições locais não são apagadas por um render posterior.
Concluir a avaliação criativa dos formatos e a integração do produto continua
pendente; nenhuma peça foi aprovada para publicação por esta rodada. Nova
tentativa paga exige outro plano e autorização explícita.

As nove cópias de código usadas na rodada continuam íntegras. Após a última
chamada, concluída às 13:24:41 UTC de 06/11/2026, o agente principal aplicou
esclarecimentos descritivos em `app/schemas/motion.py` e
`app/services/motion_direction_input.py`. Por isso esses dois arquivos atuais
já diferem dos snapshots históricos; a auditoria registra a diferença, sem
reexecutar chamadas ou atribuir o código novo aos resultados anteriores.
Grant, readiness original, registros de retomada, requests e respostas conferem
com os hashes da execução. A validação da alteração posterior pertence à sua
própria fatia de CI.
