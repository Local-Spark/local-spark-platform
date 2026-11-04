# Execução da aprendizagem de referências

Fatia de 04/11/2026: executor e Temporal usam as janelas canônicas da revisão
0108 e o ledger Jev da 0109. A ativação exige configuração explícita, permanece
desligada por padrão e independe de Google para permitir referências manuais.

O workflow transporta somente a identidade do negócio/janela, a data agendada e
estados estáveis. A primeira análise ocorre após o aceite e as próximas seguem
as janelas de seis meses. A coleta usa até 20 publicações; cada imagem acessível
de carrossel é considerada, sem limitar a quantidade de imagens a 20. A legenda
acompanha somente a primeira imagem acessível; sem imagem, usa apenas a legenda.

A decisão posterior ao piloto conserva somente autoria direta (`ownerUsername`
igual ao perfil selecionado). Não basta figurar em `coauthorProducers` ou
`taggedUsers`. Vídeos, inclusive Reels (`type=Video`, `productType=clips`), usam
somente capa (`displayUrl`) e legenda. Não são usados `videoUrl`, áudio,
transcrições, quadros adicionais ou arrays de imagens do vídeo. Um item Video
em carrossel contribui com sua capa explícita; arrays genéricos do carrossel misto
não são usados para presumir correspondência entre mídia e item. A interpretação
segue os campos documentados no [Instagram Scraper oficial](https://apify.com/apify/instagram-scraper).

Capas conservam análise parcial, pois não permitem concluir sobre o conteúdo
audiovisual. Uma capa inacessível permite aproveitar a legenda; ausência de ambas
deixa a publicação fora da análise. Resultados concluídos são imutáveis: mudar
o filtro não refaz a coleta nem altera a janela já agendada.

O executor grava o run Apify antes de consultar seu resultado. Uma resposta de
POST perdida conserva reserva e identidade; não inicia outro run. Recuperação
consulta o mesmo run e reaproveita análises concluídas por identidade opaca.
A âncora de legenda impede repetição mesmo se a imagem disponível mudar entre
execuções. Estados incertos não autorizam novo envio pago. O custo terminal Apify
é reconciliado antes das análises; ausência de recibo conserva a reserva.

Imagens, URLs, legendas e identificadores de publicações permanecem em memória.
Somente códigos próprios de padrões, contagens e cobertura são persistidos.
Falha de imagem ou resultado incerto de análise produz parcialidade explícita.
Falta de orçamento antes da coleta registra bloqueio e mantém a mesma janela;
falta de orçamento durante o Jev conserva o run e as amostras concluídas para
retomar em uma hora, sem iniciar outra coleta ou adiar tudo por seis meses.
A seleção e a versão da associação são revalidadas antes dos efeitos.

O nome opcional vem de `ownerFullName` no mesmo dataset de publicações, apenas
quando `ownerUsername` corresponde ao perfil solicitado e há um nome válido e
consistente. A fonte é o [Instagram Scraper oficial](https://apify.com/apify/instagram-scraper).
Não há chamada adicional para o nome nem uso de títulos retransmitidos do Maps.
Candidatos ainda não analisados continuam mostrando o @; referências escolhidas
analisadas podem mostrar o nome do perfil. Ausência, conflito ou dado inválido
preserva o @. Nome e resultado ficam vinculados à mesma versão da associação.

A validação final do recorte soma 237 unitários, com 100% de linhas e branches
nos seis módulos medidos. Quatro cenários PostgreSQL passaram: fluxo completo,
polling, pausa por orçamento com nova versão da política e evento preservado
com execução desligada. O nome opcional também foi persistido nesses testes.
Flags desligadas e uma configuração de chave restaurável pausam o workflow por
uma hora; históricos longos continuam em nova execução com a mesma identidade.
Contatos pendentes continuam consultando o run existente após essa renovação.
Uma coleta sem run recuperável encerra a tentativa como indisponível, preserva
seu custo incerto e agenda a janela seguinte, sem repetir o POST desconhecido.
Mypy estrito passou nos nove módulos verificados. O CI final passou em 4.734
testes/100%; o [piloto real](../evals/reference-feature-pilot-2026-11-04.md) confirmou
nove padrões no contexto de geração. A extensão de capas passou em 164 unitários
com cobertura integral do adapter e cinco integrações, além do CI integral.
Essa extensão usa fixtures sintéticas e não iniciou chamadas pagas.
