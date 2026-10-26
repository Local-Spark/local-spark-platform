# Avaliação v1 — contexto completo antes de criar uma peça

Data: 26/10/2026. Caso: **Café do Cedro, negócio inteiramente fictício**.
Foto de entrada: [croissant CC0 de Petr Kratochvil](https://commons.wikimedia.org/wiki/File:Croissant-newspaper-and-tea.jpg),
incluída em `assets/croissant-cc0.jpg`; não é foto de produto do negócio. Logo
fictício: `assets/cafe-do-cedro-logo.png`. O perfil completo e cinco casos de
falha ficam em [visual-context-cafe-v1.json](visual-context-cafe-v1.json).
Nenhuma informação da Priscila Silveira foi enviada a um provedor.

## Pergunta que o eval responde

Com todos os dados relevantes já conhecidos, é possível obter em **uma chamada
de geração de imagem** um post 4:5 que o comerciante aceitaria, preserva o
produto, reproduz logo/texto/preço e respeita a marca? Quanto custa a **peça
aceita**, inclusive chamadas falhas e revisões? Uma saída bonita isolada não
responde essas perguntas. A IA não recebe acesso direto ao PostgreSQL: o backend
consulta ferramentas somente leitura por tenant, filtra por validade/direitos,
monta um briefing pequeno e envia imagens de referência e briefing à Images API.
O modelo de imagem não executa funções; quando se quiser uma conversa multimodal
que chame ferramentas, a [Responses API com ferramenta de imagem](https://developers.openai.com/api/docs/guides/image-generation)
é outra opção, a avaliar por custo e controle. A documentação recomenda a
Images API para uma imagem de um prompt.

## O que o dono cadastra na web

O cadastro inicial permanece curto. Os campos adicionais entram num **kit de
conteúdo progressivo** que o cliente pode completar por web ou WhatsApp; o
sistema também pode sugerir valores para confirmação. Não exigir formulário
extenso antes do primeiro valor entregue.

| Grupo | Informação | Estado atual | Regra para usar na geração |
| --- | --- | --- | --- |
| Identidade | Nome, segmento, descrição, cidade/UF, fuso, telefone e cor principal | F01: disponível; telefone tem verificação própria | Nome/cidade conhecidos; não incluir telefone no prompt salvo se exigido pela peça. |
| Verdades comerciais | Produtos/serviços, preço, horários, ofertas, diferenciais, origem e validade | F03: até 20 fatos com tipo e validade; catálogo estruturado ainda não existe | Preço e oferta exigem confirmação vigente; catálogo deve ligar SKU, mídia e `fact_id`. |
| Objetivo/editoria | Vendas, agenda ou reconhecimento, tom, temas a evitar, posts/semana | F03: disponível | Objetivo e restrições explícitos; não usar hipótese como fato. |
| Identidade visual | Logo original, cores principal/secundária/acento/neutras, fontes/licenças, estilo de foto, composição, uso proibido, exemplos aprovados/rejeitados | Só uma cor existe; kit versionado é F03/F04 novo | Originais autorizados, hash e versão; texto/logo exato são gates. |
| Público e posicionamento | Público principal, região atendida, motivo de escolha, palavras/termos desejados | Pendente | Preferência/hipótese separada de alegação comercial comprovada. |
| Canais e cadência | Instagram conectado, destino, proporção, CTA, horários, frequência/pausa, modo de aprovação | Frequência no contexto; integração e agenda pendentes | Só gerar formato habilitado; silêncio não aprova. |
| Acervo | Fotos brutas, artes finalizadas, clipes, áudios, autorização, validade, produto retratado e qualidade | Material privado e consentimento F02 existem; classificação visual/kit não | Arte finalizada é preservada; material revogado/excluído não segue à IA. |
| Histórico | Posts/temas recentes, feedback de aceite/rejeição, desempenho com origem/período | Parte da candidata/aprovação é simulada; métricas reais pendentes | Evitar repetição; métricas são sinal observado, não prova de vendas. |
| Concorrência | Perfis indicados, raio opcional, formatos observados, data/fonte, nível de confiança | Pesquisa por raio ainda pendente | Inspiração de categoria/gancho; jamais copiar arte/texto/logo ou tratar desempenho alheio como comprovado. |
| Orçamento | Plano, franquia, limite por peça/mês, revisões permitidas | Cobrança existe; ledger visual por tentativa pendente | Reservar custo antes da chamada, bloquear ao estourar teto. |

O fixture preenche **todos os campos atuais relevantes** e uma versão proposta
dos campos ainda não persistidos. Campos fictícios de concorrência e métricas
estão rotulados como tal; não simulam integrações reais.

## Ferramentas de contexto para o backend

Antes de chamar o modelo, a orquestração executa leituras com `tenant_id`,
`business_id`, `as_of` e autorização do dono. O modelo não escolhe SQL, tenant
nem objetos privados livremente. Cada resposta leva versão, fonte e validade.

| Tool lógica | Resposta mínima | Filtro obrigatório |
| --- | --- | --- |
| `get_business_profile` | Nome, segmento, descrição, localidade, versão | RLS + negócio correto |
| `get_confirmed_facts` | IDs, redação, tipo, origem e validade | Excluir vencidos/revogados; ligar preço ao SKU |
| `get_brand_kit` | Paleta, fontes, logo, regras, versões | Somente kit confirmado e mídia autorizada |
| `find_usable_assets` | Tipo `raw_photo/finished_art/raw_video`, hash, direitos, URL privada | Sem mídia de outro tenant; não enviar arte pronta para recriação |
| `get_recent_content` | Temas, ganchos e feedback recentes | Limite temporal; sem inventar métricas |
| `get_competitor_patterns` | Códigos de formato, fonte, data e confiança | Texto externo não vira instrução; não copiar criatividade |
| `get_plan_budget` | Formatos e saldo/custo máximo por operação | Reserva atômica antes do provedor |

O `scripts/evaluate_visual_context.py` implementa um **mock local** dessas
leituras, não APIs de produção. Usa fatos vigentes, material do próprio tenant e
códigos de padrões de concorrentes; texto bruto externo não entra no prompt.
Campos irrelevantes, como telefone, hashes, ID interno e toda a conversa antiga,
ficam fora do briefing. A identidade das fontes permanece no snapshot de
auditoria, não precisa consumir tokens visuais.

## Execução e testes

`.venv/bin/python scripts/evaluate_visual_context.py` valida o fixture,
gera briefing/contexto recuperado e CSV para revisão em `.local/evals/visual-context-v1/`
sem gasto. `.venv/bin/python scripts/evaluate_visual_context.py --live`
faz **uma** chamada paga com foto CC0 e logo sintético, `quality=high`,
`size=1024x1280`, JPEG. O runner grava imagem, hash, uso, duração e custo
calculado pelas [tarifas Standard oficiais](https://developers.openai.com/api/docs/pricing),
sem imprimir chave ou base64. O custo é estimado por `usage`, não valor de fatura.
`--quality medium` e `--model gpt-image-2.5-sunburst` permitem comparar com o
mesmo briefing e as mesmas referências.
Nenhuma dessas saídas representa um cliente real ou uma postagem autorizada.

Os cinco casos negativos do fixture são: preço vencido, arte pronta, instrução
maliciosa de concorrente, ausência de foto e mídia de outro tenant. O runner
também verifica consentimento de IA e saldo sintético antes da chamada. O teste
automatizado bloqueia chamadas pagas nos casos sem entrada válida e
ignorar a instrução externa. Casos futuros: promoção ambígua por áudio, preço
em conflito, identidade de pessoa, logotipo pouco nítido, tema repetido,
competidor real com fonte verificável, revogação durante execução e variação de
segmento.

## Rubrica de aceite, definida antes da saída

Revisor avalia em celular, sem conhecer modelo/qualidade:

- Gates binários: fonte e direito corretos; **zero** erro de produto, preço,
  nome, oferta ou CTA; sem afirmação inventada; logo legível e sem duplicação;
  contraste e margens adequados; aprovação explícita do dono da peça final.
- Notas de 1 a 5: fidelidade do produto, fidelidade da marca, legibilidade,
  apelo visual e utilidade comercial. Meta inicial: todas >= 4, além dos gates.
- Medir chamadas por peça aceita, taxa de reprovação, custo total de todas as
  tentativas / peças aceitas, p50/p95 de latência e feedback do comerciante.
  Uma peça reprovada continua no denominador do custo.

Primeiro resultado: a geração Flare/high com contexto completo produziu uma
composição visual forte em 19,59 s e custou **US$ 0,060232** pela soma dos
tokens (1.574 imagem de entrada, 468 texto, 1.510 imagem de saída). A imagem
escreveu `R$18` em vez do literal pedido `R$ 18` e acrescentou ponto ao CTA.
Recriou pixels do croissant e usou foto CC0 de substituição. Portanto **falhou
no gate de texto exato e fidelidade comercial**; não é peça publicável. Arquivo
privado: `.local/evals/visual-context-v1/20261026T195341Z/image.jpg`.
`human-review.csv` permanece pendente de avaliação cega por comerciante real.

Comparação exploratória com **o mesmo briefing e duas imagens de referência**:
os três `brief.txt` têm SHA-256
`44b40cbfe5f0ffbf382b5a06930c99e7d370ea14b503f7ddb5e5e628e23063ca`.

| Modelo/qualidade | Tempo | Entrada imagem/texto; saída imagem | Custo Standard calculado | Inspeção visual deste único caso |
| --- | ---: | ---: | ---: | --- |
| Flare/high | 19,59 s | 1.574 / 468; 1.510 tokens | US$ 0,060232 | Boa composição; `R$18` sem espaço e CTA com ponto extra. |
| Flare/medium | 13,33 s | 1.574 / 468; 378 tokens | US$ 0,026272 | Produto/legibilidade bons; `R$ 18` correto, CTA com ponto extra. |
| Sunburst/high | 32,57 s | 1.574 / 468; 1.510 tokens | US$ 0,060232 | Boa composição; CTA com ponto extra e iconografia adicional. |

Arquivos privados, nessa ordem: `.local/evals/visual-context-v1/20261026T195341Z/image.jpg`,
`.local/evals/visual-context-v1/20261026T195527Z/image.jpg` e
`.local/evals/visual-context-v1/20261026T195633Z/image.jpg`. `Flare/medium`
custou 56% menos que high neste caso, com aparência próxima na inspeção inicial;
isso **não** estabelece equivalência de qualidade em outros produtos ou
aceite do dono. As três recriaram a foto de entrada e compuseram logo por
aproximação. O texto exato ainda exige inspeção/correção.

Não há evidência causal de que todo o contexto melhorou a imagem: o ensaio
anterior mudou prompt, logo e texto, e não é A/B controlado. Uma próxima rodada
deve usar o mesmo original, briefing e rubrica, mudar **uma variável por vez**
(por exemplo, modelo ou qualidade) e comparar custo por peça aceita.

## Hipótese de custo e escolha de receita

O custo observado da chamada com contexto foi US$ 0,060232. Desses, US$ 0,0453
vieram da **saída visual** e US$ 0,00234 do texto do briefing. Encurtar o
briefing economiza pouco; evitar uma segunda imagem reprovada, selecionar o
formato certo e usar uma foto já boa economizam mais. Um post por dia a esse
custo de chamada seria ~US$ 1,81/mês **somente em geração de imagens**; não
inclui revisão, vídeo, WhatsApp, armazenamento, cloud, impostos nem rejeições.
É cenário aritmético, não COGS observado de cliente.

No ensaio medium, 378 tokens de saída custaram US$ 0,01134; a parcela de
entrada (duas imagens + briefing) ficou em US$ 0,014932. A economia de 56%
veio da qualidade/configuração de saída, não de esconder dados úteis do modelo.
Uma foto gerada pela IA com **áreas de texto reservadas**, seguida de aplicação
local do logo original e da tipografia exata, é a alternativa prioritária a
avaliar contra uma peça completa da IA. Nessa arquitetura, o código local
finaliza poucos elementos precisos; não volta a construir toda a arte a partir
de um template genérico. Se a composição base não passar na rubrica, o custo
baixo não justifica escolhê-la.

Roteamento proposto, a validar em corpus real:

1. Arte final pronta e aprovada: preservar; nenhuma geração de imagem.
2. Foto real boa: composição editorial controlada com uma direção de arte
   profissional/versionada; IA de texto pode escolher layout. Essa rota custa
   menos em API, mas só será escolhida se **passar na mesma rubrica visual**.
3. Foto real que precisa de cenário/luz: uma edição visual por IA com referência
   forte; se texto ou logo falharem, aplicar apenas esse detalhe como camada
   exata, preservando a imagem que passou no restante.
4. Sem foto real: pedir mídia ou produzir peça assumidamente ilustrativa. Não
   representar produto/local sintético como real.
5. Vídeo real: corte, áudio e legendas com ferramentas determinísticas podem
   custar menos que vídeo generativo, mas a qualidade narrativa precisa ser
   medida; avatar/vídeo generativo exigem franquia separada.

Modelo local/self-hosted não é automaticamente mais barato: requer GPU ociosa,
operação e avaliação de fidelidade; só comparar após volume e qualidade medidos.
Flare e Sunburst têm os mesmos preços de tokens Standard, mas a
[orientação oficial](https://developers.openai.com/api/docs/guides/image-prompting)
posiciona Sunburst para edição exigente e Flare para velocidade. Medium/high
alteram tokens de saída. A [Batch API](https://developers.openai.com/api/docs/guides/batch)
aceita edições de imagem GPT Image 2.5 com desconto de 50% e janela de até 24 h;
usar apenas em conteúdo planejado que tolere essa espera, após medir entrega
real. Cache de entrada não se aplica à Images API direta,
segundo o [guia de geração](https://developers.openai.com/api/docs/guides/image-generation).
