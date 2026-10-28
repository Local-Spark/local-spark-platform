# Cadência, planos e recomendações explicáveis

Atualizado em 27/10/2026. Estado: decisão de produto; franquias, preços finais e
recomendador ainda **não implementados**. Complementa [BL01–BL06](../phases/BL-brand-library.md),
[F03](../phases/F03-editorial-research.md) e [F07](../phases/F07-billing-reports.md).

## Quem decide a quantidade

O **plano contratado determina o teto**, por mês e por tipo de peça (foto/feed,
story, carrossel, vídeo/reel) e canais habilitados. A **plataforma propõe a
cadência** dentro desse teto, usando objetivo, funcionamento do negócio, agenda,
fatos confirmados, material disponível, capacidade do plano e sinais de
desempenho quando existirem. O **cliente aceita ou ajusta para baixo** sem saber
termos técnicos de marketing; pode pausar. Para exceder o limite, a web mostra
um plano compatível e pede aceite explícito da mudança de preço. A IA não
assina um plano, publica, cobra nem amplia frequência sozinha.

O preço de cada faixa só será fechado após BL04 medir **custo por peça aceita**
por formato, incluindo geração, reprocesso, revisão, armazenamento, mensagens,
publicação e suporte. O plano de entrada de R$ 99 deve preservar a meta de
custo total de até R$ 50/mês por cliente; se a medição não couber, reduzir
franquia/formatos ou mudar preço antes de prometer a frequência. Vídeo e avatar
têm custos diferentes de uma foto, portanto não equivalem automaticamente a
“um post”.

Na UI, apresentar “até N publicações por mês” e a composição por formato, sem
exigir que o cliente entenda créditos. No backend, `plan_entitlements` registra
quantidade por formato, canais, revisões incluídas e teto de gasto. Uma peça
final aprovada conta uma vez na franquia criativa; variações por canal e envio
têm limites separados quando causarem custo. Retentativas idempotentes não
contam duas vezes. Falha da plataforma não vira publicação entregue, embora seu
custo apareça no ledger interno. Orçamento interno e reservas impedem que muitas
tentativas de IA consumam margem sem alertar a operação. Cancelamento,
expiração, replay e troca de plano precisam de regras e testes na F07.

## Jornada “próximo, próximo, concluir”

1. **Seu negócio:** aproveitar segmento, localização, serviço/produto, agenda e
   informações já confirmadas; pedir só o dado que bloqueia uma proposta útil.
2. **Seu estilo:** recomendar um kit curado do nicho, abrir simulações de feed,
   story e vídeo; aceitar ou escolher outro. Cores, fontes, logo, textos e
   composição por formato são ajustes guiados e opcionais em BL02.
3. **Seu ritmo:** mostrar uma programação inicial em linguagem comum, por
   exemplo “duas publicações por semana”, quais formatos entram, quanto do plano
   ela usa, por que foi sugerida e quando será reavaliada. O cliente aceita,
   reduz ou pausa. Fuso, dias fechados, horários de atendimento e antecedência
   de ofertas/horários vagos são considerados.

Em **Sobre meu negócio**, BL03 oferece acervo opcional e progressivo de
produtos, serviços e fotos do ambiente. O cliente pode concluir a escolha do
kit e pedir conteúdo sem cadastrar um cardápio completo. Em BL04, o pedido por
texto ou áudio recupera automaticamente os itens pertinentes; o cliente não
precisa escolhê-los a cada mensagem.

“Concluir” confirma kit aplicado e preferência de cadência; **não** aprova peças
futuras nem autoriza publicação silenciosa. Cada candidata ainda vai para
revisão/aceite conforme F06. O WhatsApp permite corrigir dados e ajustar ritmo
depois, sem reabrir o onboarding inteiro.

## Recomendação com evidência, sem falsa certeza

A primeira sugestão é uma **hipótese operacional**, não “o melhor horário do
algoritmo”. Deve incluir: ação proposta, objetivo, evidências disponíveis,
limites do plano, grau de confiança, o que será medido e data de revisão. Sem
histórico confiável, priorizar horário em que o negócio pode receber contatos,
validade da oferta, material existente e regularidade sustentável. Não inventar
percentuais de melhora ou prometer faturamento.

Depois de conectar uma conta com permissão, usar métricas **do próprio negócio**
para comparar formatos/horários em períodos e públicos compatíveis: alcance,
interações relevantes, cliques/contatos observáveis, custo e aprovação das
peças. Mostrar amostra e período; quando não houver dado suficiente, dizer
“ainda estamos testando”. Alterar um fator de cada vez quando viável, registrar
hipótese/resultado e permitir rejeição do cliente. Maior engajamento não prova
mais vendas; faturamento depende de fonte própria e consentida.

Contrato sugerido: `cadence_recommendation` versiona objetivo, conjunto de
regras/modelo, fontes com data/escopo, opções, justificativa, confiança,
capacidade do plano, custo estimado, decisão do dono e revisão agendada.
`editorial_schedule` guarda fuso, dias/horários preferidos, frequência,
formatos e pausa. Mudanças são auditadas e serializadas por negócio; eventos
de agenda são idempotentes. Uma recomendação nunca altera a assinatura.

## Biblioteca crescente de referências

Separar **referência de desempenho** de **mídia que podemos publicar**. A
biblioteca publicável contém só kits/receitas que criamos ou licenciamos.
Observar concorrentes pode informar um padrão abstrato (“vídeo curto mostrando
resultado de manicure”, “carrossel com disponibilidade da agenda”), mas não
autoriza copiar foto, vídeo, legenda, marca, rosto, voz ou layout identificável.

Cada referência guarda nicho, região quando pertinente, canal, formato, tema,
gancho, CTA, data, URL/fonte, permissão de uso, métricas públicas disponíveis,
denominador conhecido ou ausente, limitações e revisão humana. Sem acesso
permitido ou contexto suficiente, o sinal fica `unknown` e não vira afirmação
de que “funciona”. A equipe pode curar exemplos públicos manualmente; conectores
automáticos só entram após validar termos, permissões e campos de cada API.
Dados de resultados dos **nossos clientes** só alimentam aprendizado entre
negócios em agregado com base legal/consentimento apropriados, mínimo de amostra
e sem expor conteúdo, preços, conversas ou desempenho individual de outro
tenant. O cliente pode discordar de uma referência sugerida.

Há uma restrição de acesso relevante: a documentação oficial do
[TikTok Research API](https://developers.tiktok.com/docs/en/research-api-faq)
exclui usuários comerciais desse programa; ele não é nossa fonte planejada de
concorrentes. A [coleção oficial da Meta para Instagram](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api)
descreve contas profissionais, publicação e insights, mas qualquer leitura de
terceiros depende das permissões/capacidades efetivamente aprovadas para o
nosso app. A disponibilidade deve ser testada no adapter antes de prometer
análise automática por raio.

## Sequência

- **BL01–BL02:** kit demonstrativo local, escolha versionada e edição guiada
  por formato. Recomendações iniciais de kit são curadoria, sem alegação
  estatística.
- **BL03:** acervo privado e opcional em **Sobre meu negócio**, com produtos,
  serviços e fotos do ambiente, sem bloquear pedidos livres.
- **BL04:** F03 recupera contexto do pedido livre e F04 gera uma nova peça com
  kit e acervo pertinentes; medir fidelidade, aceitação e custo por peça aceita
  antes de fechar as franquias F07.
- **BL05 + F03 mínimo + F07 mínimo:** jornada local pelo WhatsApp simulado,
  proatividade, aprovação e ajustes; cadência simples dentro do plano,
  justificativa honesta, pausa e enforcement da franquia.
- **BL06:** ampliar para três kits de nichos distintos e publicar o catálogo
  público em objeto/CDN, com gate próprio de qualidade e direitos por kit.
- **Piloto:** medir custos, aceitação e sinais do próprio negócio; testar
  ajustes de horário/formato sem prometer ganho causal.
- **F03 pesquisa avançada:** curar referências por nicho/região e integrar
  somente fontes permitidas; ampliar a biblioteca com padrões auditáveis,
  depois de validar ganho sobre o baseline sem concorrentes.
