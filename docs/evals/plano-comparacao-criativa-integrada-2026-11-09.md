# Nova comparação criativa integrada — 09/11/2026

Estado: execução técnica concluída; avaliação humana indica melhora parcial, abaixo do nível criativo esperado.
Nenhuma chamada à OpenAI, inclusive contagem, foi feita durante o preparo.

## Comparação e hipótese

A: Café Pausa da rodada anterior, versão com acentos corrigidos, cujo motion foi
considerado fraco pelo titular. B: nova geração com a mesma gravação, kit, briefing,
modelo e limites de saída, usando as correções implementadas e o contrato
`reel-creative-v1`. C só existirá se a crítica de B apontar falha maior acionável.

A/B mede a nova geração com direção/validação criativa atualizada; não isola ganho
de autocrítica nem elimina a variabilidade do modelo. Se houver C, B/C registra a
correção condicional. Todos os vídeos ficam preservados. Não se presume ganho.
O modelo revisa as versões novas; a comparação visual com A cabe ao titular.
Calibrações de Intensa/Dog/Luma/Giz B são textuais, sem envio de novos quadros dessas
referências ou introdução de suas mídias na composição.

Gravação de preparo de café com 11,2 s finais, preservando sequência e áudio.
SHA de origem: `dd3f0265a4b2d94206188f46c094dc0177663e1a529b9ad2e0718a1dfad78a34`.
O briefing continua pedindo abertura tipográfica, progressão narrativa, fechamento
e movimento que ajude a contar a história, sem inventar fatos comerciais.

## Preparo concreto

- Nova operação/tenant fictício no banco dev existente autorizado. Sem migração,
  limpeza ou reabertura do pedido anterior. API real via ASGI/auth retornou 202.
- Temporal local `localhost:49805`, já autorizado e saudável; fila própria. O
  Temporal dev problemático permanece parado, sem alteração de seu histórico.
- Worker construído com o target do produto e código atual:
  `sha256:d714cb11d80e32cafd5b84a17d7791b5f5fafb0e4c36f70497f11e82ba896f3c`.
  Importação e hashes de nove módulos verificados em contêiner sem rede.
- Renderer com UTF-8 já verificado:
  `sha256:fa18127583b7d2e66cee3c49900179b52a81e9298913293a164cd9ef3aef8c25`.
- Pacote inicial construído, com seis quadros da fonte e hash preservado.
  Executor de coleta adaptado às referências cifradas, fazendo IO do storage
  fora de transações SQL e mantendo o prazo normal de 10 s do banco.
- Relatório preparado para mostrar A/B/C, quatro checks criativos, critérios
  técnicos, custos, limites e download. Nenhum CI ou nova suíte prolongada.

[Plano exato](../../.local/evals/reel-integrated-creative-proof-20261109/paid-plan.json),
[preparo](../../.local/evals/reel-integrated-creative-proof-20261109/preparation.json),
[worker](../../.local/evals/reel-integrated-creative-proof-20261109/worker-ready.json).

## Orçamento autorizado

Modelo `gpt-6.1-sol`, reasoning `high`, Standard. Até **quatro chamadas ao modelo**
e **quatro contagens de entrada**: geração e crítica; uma correção e crítica final
somente se justificadas. Máximo 16.000 tokens de saída na geração/correção e
8.000 nas críticas. A guarda conta a entrada completa antes da reserva/geração.

**Até US$ 3,40 em novas reservas**, US$ 0,85 por chamada. A rodada anterior mantém
US$ 2,55 retidos até conciliação: o teto agregado desta execução será US$ 5,95,
sendo US$ 3,40 novos e US$ 2,55 já comprometidos. Isso não libera reservas antigas
nem transforma estimativas em faturamento. O limite do novo pedido/tenant é US$ 3,40.

Envio à OpenAI: contexto/kit fictícios, quadros da fonte/peça, composição HTML/JS
e calibrações textuais. MP4/áudio não são enviados. Falha ou resultado incerto
interrompe sem repetição automática, novo modelo ou orçamento transferido.

## Encerramento esperado e limites

Produzir e avaliar a peça com as regras novas; persistir referências pequenas;
concluir a coleção privada e verificar download assinado por SHA. Preservar
críticas, quatro checks criativos, versões e custo estimado separado das reservas.
Apresentar comparação com som para decisão humana sobre motion/narrativa e
possíveis regressões em leitura, enquadramento, mensagem e áudio.

Aprovação de checks pelo modelo não é aceite criativo humano. Quadros não provam
movimento inteiro, fluidez, ritmo, sincronismo ou escuta. Se não melhorar ou se a
integração falhar, registrar a limitação sem declarar conclusão. Nada será
publicado ou cobrado de cliente. Encerrar somente o worker próprio ao terminar.

Autorização: entrevista `call_6ee5147d4e0641d1a1d98805c09b21d1`, resposta
“Autorizar até US$ 3,40 para esta rodada”. O pacote local vincula a autorização
ao SHA do plano; não reutiliza autorização de rodada anterior.


## Resultado da execução autorizada

Pedido `c5e7641c-eb2d-5da0-8f41-df76751fdcf5` terminou `completed`,
`simulated=false`, com peça `6d7b1834-5bc9-587c-b3a1-00825c095fa8`.
Geração, renderer isolado, crítica e persistência passaram pelo worker do produto
no dev e Temporal local autorizado. Nenhuma migração, limpeza ou suíte CI nesta
rodada. Worker próprio confirmado `exited`; baseline preservado por hash.

[Comparativo A/B com som](../../.local/evals/reel-integrated-creative-proof-20261109/report.html),
[vídeo B](../../.local/evals/reel-integrated-creative-proof-20261109/selected.mp4),
[resultado](../../.local/evals/reel-integrated-creative-proof-20261109/result.json),
[verificações](../../.local/evals/reel-integrated-creative-proof-20261109/verification.json).

A crítica retornou `adequate`, os quatro requisitos criativos `met`, sem issues.
Não houve correção: B é a geração inicial nova, não uma versão corrigida de A.
A peça alterna abertura tipográfica, observação do preparo e convite final;
barras de pausa se transformam em linhas e seta. A linguagem permanece editorial.
Quadros amostrados foram inspecionados. A avaliação humana posterior reconheceu
melhora parcial, sem atingir o nível esperado; detalhes abaixo. Não há aprovação
comercial ou publicação. A resposta não certifica áudio ou ausência de regressões.

Foram **duas chamadas ao modelo e duas contagens**, sem retry:

| Etapa | Duração do efeito | Uso estimado (US$) | Entrada cifrada no SQL |
| --- | ---: | ---: | ---: |
| Geração | 244,286 s | 0,133373 | 716 bytes |
| Render | 310,299 s | — | 18.660 bytes |
| Crítica | 70,681 s | 0,132783 | 716 bytes |

Workflow: **667,63 s**. Uso total estimado **US$ 0,266156**, sujeito à fatura;
reservas novas **US$ 1,70**, abaixo dos US$ 3,40 autorizados. Somadas às reservas
anteriores de US$ 2,55, ficam US$ 4,25 retidos; nenhuma conciliação presumida.
Limites calculados antes das chamadas: US$ 0,179703 e US$ 0,170493, ambos abaixo
da reserva individual de US$ 0,85. Evidências grandes ficaram cifradas no storage,
com referências pequenas no SQL, sem aumentar seu prazo de 10 s.

Leitura autenticada da peça e emissão do link assinado retornaram 200; download
real também 200. MP4 com 1.657.707 bytes, SHA-256
`82c11f885ce4879fc6e6b28621d142d9bdd5d2c6987c942f2b63809a2ae6536e`,
conferido contra a versão selecionada. Saída de 11,2 s, 720×1280 e 30 fps.
A prova demonstra o caminho técnico com IA real, não desempenho comercial,
jornada completa de WhatsApp ou qualificação dos demais formatos.


## Avaliação humana recebida

Resposta à entrevista `call_973da592f9264e0a94166f80c95f2db5`:

> ficou legal, mas ainda está muita aquem aos motions graphics que vejo na internet que sao virais. é bem longe dos exemplos de bibliotecas de motions que temos. mas ficou um pouco melhor.

Conclusão: pequena melhora percebida em B, insuficiente para o objetivo criativo.
A execução técnica permanece concluída. Não interpretar a preferência parcial
como aprovação comercial, de publicação ou confirmação de áudio/enquadramento.
O julgamento original do modelo fica preservado para comparar com o humano.

Diagnóstico com base no contrato e na crítica registrados: os quatro checks
verificaram progressão e função gráfica, mas aceitaram uma composição abaixo do
patamar esperado. O próprio crítico declarou não ter recebido imagens das
referências nem versão anterior; as calibrações eram somente textuais. Assim,
`adequate` nesta prova não demonstra proximidade do acabamento das bibliotecas.
A causa exata da distância criativa ainda exige comparação com uma referência
concreta; não se conclui que aumentar efeitos ou chamadas resolverá o problema.

Próximo trabalho proposto: selecionar referência existente com o titular, explicitar
ritmo, tipografia, transições e transformações que definem o acabamento desejado,
e usar esse alvo tanto na direção quanto na avaliação. Referências visuais e
evidências temporais precisam de tratamento e orçamento próprios; nenhum novo
ensaio pago ou mudança de código foi executado ao registrar este feedback.
