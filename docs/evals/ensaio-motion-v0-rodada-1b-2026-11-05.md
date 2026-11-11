# Motion 1b — interrupção na interpretação Jev

Rodada autorizada em 05/11/2026: sete chamadas, teto operacional de US$ 1,60,
sem refação automática, conforme o [plano](plano-motion-v0-rodada-1b-2026-11-05.md).
A execução parou depois da primeira chamada. Não houve transcrição, direção
OpenAI ou geração de peças criativas nesta rodada.

## Mensagem, entrada e saída

Caso fictício Reel: “Enviei este vídeo da preparação do café. Faça um reel com
cortes, transições, motion graphics e legendas para convidar as pessoas para
uma pausa.” Jev recebeu essa mensagem, candidatos vazios e cinco formatos
elegíveis; não recebeu quadros ou vídeo nessa etapa.

O provedor respondeu HTTP 200 em cerca de 0,42 s, com modelo `jev-1.14.0`:

| Campo | Escolha | Confiança |
| --- | --- | ---: |
| Intenção | `content_request` | 1,00 |
| Formato | `reel` | 1,00 |
| Item | `none` | 0,46 |

A validação exigia confiança de pelo menos 0,50 também para item. Por isso,
o resultado exigiu esclarecimento e a operação foi preservada como resposta
recebida/rejeitada. As seis operações seguintes não foram iniciadas. A resposta
não foi reclassificada nem reenviada; a seleção correta de Reel, sozinha, não
constitui execução bem-sucedida de toda a etapa.

## Custo e evidência

Uso retornado: 828 tokens de entrada e 153 de saída. Pela tarifa proposta de
US$ 0,042/M de entrada e saída gratuita, a estimativa é **US$ 0,000034776**
(US$ 0,000035 arredondado para controle). Não é valor conferido em fatura.
A reserva de **US$ 0,01 permanece comprometida**; não foi liberada ou zerada.

- [Ledger privado](../../.local/evals/motion-v0-rodada-1b-2026-11-05/round/live/ledger.jsonl).
- [Pedido exato](../../.local/evals/motion-v0-rodada-1b-2026-11-05/round/live/505ac266-14c5-4432-bbc8-f8b77d4661c9/request.body).
- [Resposta recebida](../../.local/evals/motion-v0-rodada-1b-2026-11-05/round/live/505ac266-14c5-4432-bbc8-f8b77d4661c9/response.body).
- [Diagnóstico](../../.local/evals/motion-v0-rodada-1b-2026-11-05/round/live/505ac266-14c5-4432-bbc8-f8b77d4661c9/diagnosis.json)
  e [custo estimado](../../.local/evals/motion-v0-rodada-1b-2026-11-05/round/live/505ac266-14c5-4432-bbc8-f8b77d4661c9/cost-estimate.json).
- [Registro de interrupção](../../.local/evals/motion-v0-rodada-1b-2026-11-05/round/round-stopped.json).

O diagnóstico compara a resposta ao limiar original; não é replay integral
do adapter após sua alteração. Uma tentativa local de replay com o adapter já
alterado foi recusada pela diferença no hash do pedido, antes de gravar resultado
ou executar qualquer rede. Nada disso substitui a resposta original.

## Correção local e limites

O adapter passa a omitir a pergunta de item quando não recebe candidatos
selecionáveis. Mantém os limiares de intenção/formato e, quando há candidatos,
de seleção. A lista vazia significa ausência de candidatos recuperados; não
comprova catálogo vazio, ausência de produto no pedido ou suficiência de fatos.

O produto já define acervo opcional, mas o serviço de briefing ainda exige um
item resolvido para preparar sua jornada existente. Essa integração é uma fatia
posterior; a correção do adapter não habilita criação genérica no produto nem
dispensa validação de gravação, fatos, contexto e direitos.

Os 55 testes dirigidos passaram com cobertura integral do adapter. O primeiro
CI completo terminou com 5.043 testes aprovados e uma falha: o mock do ensaio
antigo de comparação acessava obrigatoriamente `questions.offering`, inclusive
em casos sem candidatos. O mock foi ajustado para responder somente às perguntas
enviadas, mantendo os mesmos casos, resultados esperados e cálculos de custo.
Os 73 testes conjuntos do adapter e da comparação passaram. Na retomada de
06/11/2026, conferido o CI final aprovado: **5.044 testes Python e 62 Node**,
sem pulados, cobertura de 100%, Ruff e mypy aprovados. O aviso de depreciação
do cliente HTTP de testes já existente não bloqueou a validação.
A nova requisição exige identidade/reserva e autorização próprias,
pois a rodada aprovada não permitia refação automática. É possível manter o
teto global de US$ 1,60, descontando conservadoramente a reserva de US$ 0,01
já comprometida. Nenhum orçamento futuro foi concedido por este registro.
