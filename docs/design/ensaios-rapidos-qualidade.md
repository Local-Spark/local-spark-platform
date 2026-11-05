# Ensaios rápidos de qualidade de conteúdo

## Decisão do titular — 04/11/2026

Para comparar rapidamente a qualidade criativa de peças, usar um **ensaio
isolado das etapas**, semelhante ao executado na
[BL04.3](../evals/bl043-reference-quality-2026-11-04.md#resultado-do-ensaio-direto--04112026).
O objetivo é mostrar os resultados ao titular cedo, com as entradas e saídas
necessárias para explicar de onde vieram, sem preparar um ambiente completo.
**Não criar outro banco nem montar Temporal, filas, workers, API ou frontend
apenas para esse tipo de ensaio.** Usar o contexto e os recursos já disponíveis
no ambiente local, sob autorização e sem alterar dados alheios. Se os dados já
estiverem disponíveis, carregá-los diretamente ou lê-los pelo serviço existente
com a role e o escopo corretos; preservar o histórico e evitar consultas pagas de
descoberta apenas para repetir a avaliação.

Esta decisão trata de **avaliação criativa isolada**. Não é permissão para
substituir Temporal no runtime, contornar controles de produto ou declarar uma
integração testada. Quando o pedido for testar banco, fluxo real, integração ou
CI, usar os mecanismos e testes correspondentes: PostgreSQL dedicado terminado
em `_test`, logins restritos e serviços locais. Nunca limpar ou migrar o banco de
um projeto existente para testar.

## Procedimento

1. **Definir o caso e fontes.** Usar pedido fictício simulando a mensagem de
   WhatsApp e identificar o negócio, formato, fatos confirmados, acervo com
   direitos, kit/versão, skill/hash e referências selecionadas. Registrar
   origem e cobertura dos padrões já derivados; não arquivar posts, legendas ou
   imagens de terceiros. Se comparar dois braços, manter os demais inputs e
   configurações iguais e declarar exatamente qual variável muda: por exemplo,
   referências vazias versus referências e seus padrões, ou somente padrões.
2. **Planejar gasto antes de rede.** Verificar credenciais existentes sem
   imprimi-las; dimensionar número de chamadas, modelos, tarifas/estimativas,
   reservas e possíveis refações. Respeitar autorização e teto específicos do
   ensaio. Tetos anteriores, inclusive os US$ 2 de 04/11, não são renovados
   automaticamente; se o pedido atual ainda não autorizar gasto, apresentar o
   plano e obter autorização antes das chamadas pagas.
3. **Rodar etapas diretamente.** Usar os adapters e builders reais pertinentes
   em processo local de avaliação. Registrar mensagem e entrada/saída Jev;
   quando Jev for simulado, identificá-lo expressamente. Construir e registrar o
   input editorial com contexto, kit, skill, acervo e referências; guardar a
   resposta e verificar texto e fatos. Preparar e registrar o input visual,
   incluindo hashes dos arquivos autorizados, e gerar as imagens finais. Cada
   braço deve ter sua própria resposta editorial quando se pretende medir o
   efeito editorial e visual das referências.
4. **Conservar identidade e orçamento.** Antes de cada chamada paga, gravar
   identidade única, hash do pedido e reserva em ledger durável do próprio ensaio,
   com teto cumulativo que some todos os provedores e etapas. Não manter locks
   durante rede. Registrar respostas, uso, tempo e custo informado ou estimado;
   nunca registrar credenciais ou URLs assinadas. Quando o resultado for incerto,
   preservar operação e reserva e parar; não reenviar nem zerar ledger. Uma
   resposta comprovadamente recebida e rejeitada pode ser conciliada com evidência
   e uma nova tentativa distinta, dentro da autorização, preservando o histórico.
5. **Mostrar e aprender.** Guardar imagens, textos e arquivos privados em
   `.local/evals/` com acesso restrito e preparar visualização lado a lado, com
   links para entradas/saídas relevantes. Registrar em `docs/evals/` os casos,
   versões, modelo/configuração, preferências ou rejeições do titular, limitações,
   todas as tentativas, reservas e custos. Diferenciar estimativa, valor informado
   e fatura; custo por peça aceita só existe quando há aceite e despesas apuráveis.
   Avisar ao concluir o ensaio e pedir revisão humana, sem chamar uma preferência
   visual de aprovação de publicação.

Os arquivos locais de 04/11 são referências de método: a
[comparação](../../.local/evals/bl043-rapid/real/comparacao.html), as entradas e
saídas no mesmo diretório, o executor `runner.py`, o ledger e a continuação
`continue_once.py`. A pasta `.local` é privada e ignorada pelo Git: pode não
existir em outro checkout. Os executores e ledgers **têm identidade e paths
específicos daquela rodada**; não reexecutá-los nem reutilizar suas reservas,
resultados ou autorização para um novo ensaio. Preparar uma execução com
identidade própria e validação mínima de seu caso, sem criar um segundo sistema.

## Resultado e limites do exemplo de 04/11

Duas mensagens produziram duas interpretações Jev reais, editoriais por braço e
quatro peças: feed/story com e sem referências. O titular preferiu as duas
versões com referências. A primeira resposta editorial do feed com referências
foi rejeitada, preservada e conciliada como recebida, e outra tentativa usou uma
orientação adicional; por isso aquele par não isola perfeitamente o efeito das
referências. A legenda do story com referências continha uma instrução interna,
que precisa ser corrigida. A análise original das referências é parcial e não
foi visualmente conferida. Reservas: US$ 1,52; estimativa: US$ 0,216691, não
fatura. O valor não é custo por peça aceita nem autorização para outro teste.
