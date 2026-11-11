# Rodada motion 1b — proposta para aprovação

## Autorização recebida — 05/11/2026

O titular autorizou explicitamente esta rodada com teto operacional de US$ 1,60,
sete chamadas e sem refação automática. A concessão privada foi registrada com
vínculo ao manifesto e à preparação técnica. O restante deste documento preserva
o plano apresentado antes da autorização; a execução e os custos serão registrados
separadamente, sem transformar estimativas em valores faturados.

Preparação concluída em 05/11/2026. **Nenhuma chamada paga foi realizada e não
há concessão de orçamento.** Esta proposta substitui, para a próxima execução,
o [rascunho anterior](plano-motion-v0-rodada-1-2026-11-05.md), que usava contrato
antigo e ficha fictícia. Os arquivos anteriores permanecem preservados.

## Casos e resultado pretendido

Três mensagens simuladas para cafeteria fictícia, sem fatos comerciais inventados:

1. Reel 9:16: editar o preparo de café com motion, cortes, áudio e legendas
   quando adequadas. Gravação ilustrativa de 11,18 s com voz sintética; fazer
   uma transcrição e conferir seu texto contra a origem documentada da fixture.
2. Story 9:16: editar a cópia sem faixa de áudio do mesmo preparo. A direção
   pode usar música/efeito apropriado, sem inventar fala.
3. Carrossel 4:5: foto de croissant enviada, com 3–5 páginas e MP4 de 5–8 s
   por página. A IA escolhe quantidade, duração e estilo dentro dos limites.

Usar builder, skills, catálogo de três fichas, contrato v2 e compilador próprios.
O modelo escolhe o estilo por pedido; não recebe uma seleção pronta. As fontes
disponíveis do kit são DejaVu Sans/Serif regulares, com IDs e hashes explícitos.
Reel/story recebem seis quadros identificados por tempo/hash; o modelo não recebe
o vídeo inteiro nem ouve seu áudio. Os padrões históricos de referências estão
preservados separadamente: não foram promovidos a snapshot válido sem sua
proveniência estruturada. Este ensaio não é comparação controlada com o v2.

## Plano de chamadas e orçamento

| Etapa | Máximo | Reserva por chamada | Total reservado |
| --- | ---: | ---: | ---: |
| Jev 1.14, uma interpretação por caso | 3 | US$ 0,01 | US$ 0,03 |
| `gpt-transcribe`, gravação do Reel | 1 | US$ 0,01 | US$ 0,01 |
| `gpt-6.1-sol`, uma direção por caso | 3 | US$ 0,50 | US$ 1,50 |
| **Total** | **7** | | **US$ 1,54** |

**Teto operacional proposto: US$ 1,60. Estimativa de planejamento: US$ 1,00–1,50.**
Não inclui refação. O teto controla o início das chamadas; não é limite imposto
ao fornecedor. Se uma resposta for incerta, rejeitada ou incompatível com a
reserva, interromper e conservar evidências/reserva, sem reenviar automaticamente.
Qualquer nova tentativa exigirá plano e autorização próprios.

A estimativa é conservadora e ainda não medida: cada direção tem cerca de
34–37 kB de JSON sem os bytes de imagem, além dos anexos, e até 24 mil tokens
de saída, incluindo raciocínio. Três saídas no limite representam US$ 0,72 na
tarifa standard. Uma aproximação conservadora de um token por byte para o texto
leva a cerca de US$ 0,28 de entrada adicional na tarifa de escrita de cache;
não é contagem pelo tokenizer do modelo. A faixa de planejamento inclui margem
para imagens, Jev e transcrição, mas a fórmula de tokens de imagem deste modelo
não ficou confirmada na documentação consultada. A primeira direção permitirá
conferir o uso retornado antes de prosseguir. Não prometer custo por peça aceita.

O payload solicita explicitamente `service_tier=default` e cache implícito com
TTL mínimo de 30 minutos. O TTL não é prazo de exclusão. O executor conserva
modelo/tier retornados e interrompe se não corresponderem à configuração revista.
Para contexto até 272 mil tokens, o [modelo oficial](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
informa US$ 2/M de entrada, US$ 2,50/M de escrita de cache de 30 minutos e
US$ 10/M de saída; contextos maiores e outras modalidades têm tratamento próprio.
Configuração conforme [Responses](https://developers.openai.com/api/reference/resources/responses/methods/create)
e [cache](https://developers.openai.com/api/docs/guides/prompt-caching).
A transcrição está estimada a [US$ 0,0045/min](https://developers.openai.com/api/docs/models/gpt-transcribe);
Jev, a [US$ 0,042/M de entrada](https://help.typesafe.ai/articles/5187202169-how-much-does-jev-cost).
Conferir condições vigentes antes do efeito; estimativa não é fatura.

## Preparação e execução

O [diretório privado](../../.local/evals/motion-v0-rodada-1b-2026-11-05/)
preserva código do ensaio, bundle, prévias exatas, fontes, mocks e hashes. A rodada
tem ID `31ac0f47-d7b7-4b4f-85e0-d7e4ff0f2580`; IDs reais e simulados são distintos.
O manifesto atual tem SHA-256
`3f23d241e1632f5c0c0d9fb53c29f01320c03aee61d3cf01ba167f6469f14869`.
Não há `grant.json` nem chamadas reais. Presença das duas credenciais configuradas
foi conferida sem mostrar valores ou testar rede; elas não pertencem ao bundle.

O executor realiza uma operação por vez. Antes de rede, verifica a concessão e
o pedido, grava corpo/hash/reserva em ledger privado com lock/fsync e libera o
lock. Guarda resposta, uso e custo estimado separadamente de faturamento. Não
registra cabeçalhos de autenticação. Respostas parciais/incertas não são repetidas.
Jev que peça esclarecimento não é substituído por escolha forçada do formato.

A direção do Reel é montada depois da transcrição e da revisão técnica da fixture,
com hashes próprios para esse estágio. Isso não exige segunda autorização de
orçamento. O áudio normalizado já foi extraído duas vezes com hash idêntico;
não foi enviado ao transcritor. Texto revisado não comprova tempos por palavra.

Os testes locais do harness passaram: 33 testes com transportes simulados e
sete da ponte de render, sem rede. A compatibilidade do schema foi verificada
offline; sua aceitação remota é uma incerteza da primeira chamada autorizada.
A saída será validada, compilada e renderizada com código próprio; nenhum HTML
ou JavaScript gerado pelo modelo será executado.

## Renderer e limites da avaliação

O executor geral produziu e decodificou cinco MP4s sintéticos: Reel com duas
faixas, story sem áudio e três páginas 1080 × 1350. [Trace e arquivos](../../.local/evals/motion-v0-rodada-1b-2026-11-05/synthetic-render/)
confirmam dimensões, duração, frames distintos e bloqueios de rotas/CSP. A imagem
sintética do carrossel já contém texto embutido que se sobrepõe à camada de teste;
essa fixture prova execução, não composição criativa ou legibilidade aprovada.
Chromium usa sandbox, mas ainda não há isolamento de rede comprovado no SO nem
pacote de produção. O ensaio usa somente fontes fictícias conhecidas.

O executor admite até duas faixas 1:1, ganhos não positivos, cortes, fades e
camadas declarativas. Requisitos não suportados são recusados, sem descartá-los
silenciosamente. Semântica dos cortes, legendas, áudio, legibilidade e loops
exigem inspeção das peças; os testes sintéticos não substituem essa avaliação.
Não há banco, Temporal, API ou frontend montados para este ensaio criativo.

## Fontes e atribuição

- Foto: [Croissant Newspaper and Tea, Petr Kratochvil](https://www.publicdomainpictures.net/en/view-image.php?image=15461&picture=croissant-newspaper-and-tea),
  também identificada como [CC0 no Commons](https://commons.wikimedia.org/wiki/File:Croissant-newspaper-and-tea.jpg).
  Preservar os links de origem junto do resultado.
- Vídeo: [Latte Coffee making, Stevenndori289](https://commons.wikimedia.org/wiki/File:Latte_Coffee_making.webm),
  CC BY-SA 4.0. A fixture foi recortada, transcodificada e recebeu voz sintética
  que não pertence à pessoa filmada. Derivações compartilhadas devem preservar
  atribuição, indicação das mudanças e licença compatível.
- Música: [Jazz Piano, Serolillo](https://commons.wikimedia.org/wiki/File:Jazz_Piano.ogg),
  CC BY 2.5; a fixture é um trecho. Preservar crédito/licença e indicar mudanças.
  Efeito de clique é sintético; fontes DejaVu conservam os avisos do kit.

As páginas de origem foram conferidas nesta preparação. As mídias do ensaio não
serão incorporadas ao catálogo comercial nem ao pacote de dependências. Ao
apresentar as peças, incluir os créditos e distinguir fixture de material real.

Após autorização específica, executar os casos, mostrar entradas/saídas/peças e
trace e solicitar avaliação criativa. Isso não aprova publicação nem conclui a
jornada integrada da v0.
