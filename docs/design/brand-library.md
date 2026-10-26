# Biblioteca de identidade visual e formatos

Data: 26/10/2026. Estado: **decisão de produto para validação**; a web já tem um
simulador estático inicial, mas catálogo, escolha pelo cliente e renderização
por receita ainda não estão implementados. Complementa o [plano criativo](creative-production-quality.md) e
o [eval de contexto](../evals/visual-context-eval-v1.md).

## Problema e decisão

O cadastro atual guarda apenas uma cor. Isso não permite inferir uma identidade
visual, e um template universal produz peças repetitivas e fracas. A plataforma
deve oferecer uma **biblioteca de kits de campanhas prontos para demonstração**,
criados e avaliados uma única vez pela equipe. Cada kit já inclui amostras de
feed, story, reels e, quando suportado, outros formatos. O dono pode comparar
esses kits **dentro da nossa plataforma** e escolher o que representa melhor
seu negócio. Nesta escolha, nenhuma peça precisa conter o nome, logo, foto,
cor, produto ou preço do cliente. Um exemplo de cafeteria pode usar a marca
fictícia “Meu Braço Direito”. A personalização vem **depois da escolha** e as
peças reais continuam sujeitas à aprovação individual pelo WhatsApp.

Inspiramo-nos no conceito de [Brand Kit do Canva](https://www.canva.com/en_in/help/brand-kit/)
e de [templates da marca](https://www.canva.com/en_in/help/using-brand-templates/):
ativos e regras aprovados alimentam vários formatos. As artes e os padrões do
produto serão próprios, sem copiar templates, marcas ou publicações alheias.

## Três camadas distintas

1. **Kit de demonstração da biblioteca:** pacote próprio, pré-produzido e
   versionado por segmento/estética. Inclui direção fotográfica (luz, cenário,
   enquadramento e tratamento), composição, fontes com licença, paleta,
   fotos/vídeos de demonstração com direitos, dez publicações exemplares,
   stories e reels, legendas fictícias e exemplos de conversa. Inclui também
   **arquivos-fonte/receitas editáveis** por formato e campos permitidos para
   produto, imagem, fato, preço, nome, CTA e logo; JPEG/MP4 de demonstração
   sozinhos não bastam para produzir novas peças do cliente.
   Todos veem os mesmos arquivos pré-gerados; abrir o catálogo não chama IA.
2. **Kit aplicado ao negócio:** escolha do `kit_id/version` e, depois, nome,
   logo, cores e referências reais opcionais do cliente. A seleção mantém a
   direção visual do pacote; ajustes simples geram versão própria do negócio.
   Uma sugestão automática não se torna identidade aprovada sem o aceite dele.
3. **Receitas de conteúdo:** padrões reutilizáveis para produto, oferta,
   bastidor, depoimento consentido e dica. Cada receita declara formato (feed,
   story, capa de reel, carrossel ou vídeo), fontes necessárias, zonas seguras,
   limites de texto, CTA e rotas de produção. O kit define a aparência dessas
   receitas. Exemplos do catálogo têm qualidade de peça publicável, mas o texto
   e a marca fictícios não são publicados como se fossem do cliente.

## Experiência simples de escolha

1. Usar o segmento já informado no cadastro para filtrar o catálogo. Mostrar
   até três kits sugeridos, com opção de explorar os demais. **Não pedir fotos,
   logo ou paleta para abrir a vitrine.** Quem já tem marca pode escolher um kit
   compatível ou iniciar pela importação da própria identidade.
2. Ao abrir um kit, carregar os arquivos **já cadastrados no nosso catálogo
   interno**: dez exemplos de posts numa grade, stories, reels reproduzíveis,
   legenda e exemplos da origem pelo WhatsApp ou pela rotina proativa. Os
   exemplos são feitos uma vez com marca e materiais fictícios/licenciados.
3. O dono alterna entre kits e entre simuladores de Instagram, Facebook e
   TikTok **dentro da nossa web**. Não abre a conta pessoal dele nem conecta as
   redes nessa etapa. Cada kit deve exibir todos os formatos que ele promete e
   indicar quais dependem do plano ou de integração ainda não disponível.
4. Ao escolher, o cliente confirma a direção visual. Depois pode ajustar cor,
   fonte licenciada, peso da foto e importar logo/fotos próprias; isso cria um
   kit aplicado ao negócio. A web atualiza três prévias representativas
   (feed, story e capa vertical) pelas receitas editáveis, sem regenerar a
   biblioteca por IA a cada clique. Pode comparar com o padrão e voltar a ele.
   Edição posterior cria nova versão e não altera peças aprovadas.
5. WhatsApp pode enviar link direto ao catálogo e receber a escolha por resposta
   curta; a web oferece a comparação completa. Escolher kit não autoriza postar.

### Simulação da presença futura

Esta é uma **experiência da nossa plataforma**, acessível após o contexto inicial
e antes de conectar Instagram/Facebook/TikTok. O simulador Instagram mostra a
estrutura familiar de perfil, grade de dez posições, stories separados e reels;
as abas Facebook/TikTok exibem como **as mesmas amostras genéricas** se
apresentariam nesses canais. Todas as imagens/vídeos/legendas vêm de arquivos
pré-gerados do catálogo, via armazenamento/CDN. Não abrir, alterar ou ler a
conta pessoal do cliente. A UI rotula “Exemplo do kit · marca fictícia · ainda
não publicado” e não inventa seguidores, curtidas, comentários ou resultados.

Cada posição abre o arquivo demonstrativo completo e mostra objetivo, formato,
legenda/CTA fictícios e “o que seria enviado pelo WhatsApp”. O cliente alterna
entre kits e percebe o conjunto, sem gerar novas peças. Sempre que possível,
usar as mesmas pautas fictícias nos kits comparados para evidenciar a diferença
de estilo. A biblioteca completa mostra disponibilidade por plano e plataforma.

Dois cenários obrigatórios na demonstração:

| Origem | Exemplo de entrada | Exemplo de saída simulada |
| --- | --- | --- |
| WhatsApp fictício | “Hoje o croissant do café de exemplo está R$ 18” + foto licenciada | Story e post **pré-produzidos** do kit, mostrando o resultado possível e a confirmação de preço que o sistema pediria no uso real. |
| Dia sem mensagem | Nenhuma entrada nova para o café fictício | Post/dica **pré-produzido** do kit, mostrando como o planejador agiria com acervo e fatos vigentes; no uso real, pediria material caso faltasse. |

As dez posições e os outros formatos são produzidos **uma vez por versão do
kit**, revisados editorial/visualmente e armazenados como ativos estáticos do
catálogo. O custo de IA ocorre na criação/revisão dessa biblioteca, amortizado
pelos clientes que a consultarem; cada abertura é leitura de mídia/cache, não
dez ou trinta gerações. Reel demonstrativo só é reproduzível se o vídeo completo
estiver no pacote. A prova de qualidade do catálogo exige abrir os arquivos
reais em celular; uma grade bonita não pode esconder peça ampliada ruim.

Os formatos, cortes e requisitos específicos de cada canal ficam em adapters
versionados, pois mudam. A experiência pode demonstrar Facebook/TikTok antes
de haver conexão, mas só oferece publicação real quando a integração e a
receita daquele canal estiverem homologadas. A escolha do kit nunca implica
acesso à conta nem autorização para publicar.

No começo, recomendações por segmento são hipóteses editoriais curadas. Só usar
desempenho agregado como sinal de preferência depois de haver métricas comparáveis,
permissão e amostra suficiente. Concorrentes podem inspirar **formatos**, nunca
fornecer template copiado nem afirmar que uma estética causou vendas.

## Produção e custo

- **Criação do catálogo pela equipe:** design/IA produzem os kits exemplares por
  segmento; revisão humana valida conteúdo, legibilidade, direitos e qualidade
  de todos os formatos. Guardar `kit_id/version` e arquivos finais. Esse é um
  custo de produto por versão, não um gasto de geração por visitante.
- **Navegação/seleção:** servir arquivos pré-gerados por armazenamento/CDN;
  custo variável é hospedagem/tráfego. Abrir dez posts de três kits não executa
  trinta inferências. IA pode ajudar a recomendar kits com base no segmento,
  mas a recomendação não precisa gerar imagens.
- **Produção personalizada posterior:** só após selecionar o kit e receber
  material/contexto reais, a plataforma planeja e produz posts do negócio.
  Aqui sim há custo variável de IA, composição, mensageria e revisão, contado
  no plano mensal. O exemplo fictício do catálogo não vira postagem real com
  simples troca de nome quando fonte/fato/produto não correspondem. O pipeline
  usa as regras e fontes editáveis do kit para novas pautas, em vez de copiar o
  JPEG/MP4 exemplar e apenas sobrepor a marca do cliente.
- **Kit como referência criativa:** F03/F04 resolvem `kit_id/version` no backend
  e montam um briefing com tokens de marca, receita/formato, limites de texto,
  composição, estilo fotográfico, fato/CTA vigentes e material do cliente.
  Quando IA visual for necessária, enviar **no máximo uma imagem de referência
  do kit, da mesma receita/formato**, além do material original do cliente
  quando houver. Nunca enviar as dez peças da vitrine. Referência com marca
  fictícia deve ter o texto/logo removido ou mascarado para evitar cópia na
  saída; nome e logo reais entram como dados exatos e são validados no arquivo.
  O modelo não conhece um `kit_id` por si só: a plataforma traduz o kit em
  instruções e referências.
- Arte pronta recebida: preservar o original. Foto própria boa + preço/CTA
  exatos + receita aprovada: testar composição local de qualidade profissional.
  Essa rota economiza chamadas de imagem e preserva o produto real, mas só entra
  no piloto se passar pelo mesmo gate de qualidade da rota por IA.
- Quando o material pede nova cena, tratamento criativo ou a composição local
  falha na revisão: gerar/editar com IA visual, ancorar no material autorizado e
  aplicar texto/logo exatos por composição quando necessário. Vídeo real usa
  seleção de trechos, áudio e legendas; vídeo generativo/avatar têm orçamento e
  consentimento próprios.
- O roteador decide por **receita + qualidade da fonte + preferência do dono +
  fidelidade factual + custo restante**. Não substituir uma geração ruim por um
  template genérico de modo silencioso. Registrar rota, versões, tentativas e
  gasto total; medir custo **por peça aceita** e COGS mensal, com meta de
  R$ 50/cliente/mês para o plano de R$ 99.

A biblioteca reduz variância e retrabalho, mas não cria fotos reais boas nem
garante variedade sozinha. Cada direção precisa de composições alternativas,
alternância de formatos e memória de publicações recentes. Não gerar tudo em IA
nem supor que um editor local tem a mesma qualidade sem comparação cega.

**Hipótese de economia na produção:** referências consistentes podem reduzir
erro, ajustes e chamadas repetidas. Não garantem chamada individual mais barata:
imagens de entrada e saída consomem tokens; a
[documentação oficial da OpenAI](https://developers.openai.com/api/docs/guides/image-generation)
orienta medir `usage` por configuração e informa que o cache de entrada de
imagem para GPT Image 2/2.5 se aplica à ferramenta de geração na Responses API,
não à Images API direta. A decisão por provedor/rota compara **custo total por
peça aprovada**, incluindo entradas, saídas, falhas, OCR e revisões. O kit
compacto + uma referência pode ganhar do prompt sem kit. Isso é hipótese de
teste, não economia demonstrada.

## Contratos para implementar em fatias

- **F03 — contexto e escolha:** `brand_kit` por negócio e versão, estado
  `suggested/approved/retired`, proprietário/horário de aprovação, ativos com
  hash/direitos, regras, `style_pack_id` e `style_pack_version`; nenhuma sugestão
  pendente entra em produção automática. Snapshot editorial inclui versão do
  kit e referências autorizadas. F03 usa segmento/preferências apenas para
  **filtrar/recomendar kits já existentes** e registra o `kit_id/version`
  escolhido. As dez pautas da demonstração pertencem ao catálogo, não são
  criadas por F03 com fatos do visitante.
- **Catálogo interno — curadoria/versionamento:** `catalog_kit` com segmento,
  estilo, status, direitos, formatos, versão e disponibilidade por plano;
  `catalog_sample` com posição, canal, receita, imagem/vídeo/legenda final,
  miniatura, roteiro da conversa fictícia e autoria; `catalog_recipe_source`
  guarda arte-fonte editável, tokens visuais, slots tipados e regras de formato.
  Pacote só fica público depois de revisão; versão publicada é imutável e
  cacheável. A produção posterior fixa a versão do pacote escolhido.
- **F04.1b/F04.2b — receitas e roteamento:** `recipe_id/version`, formatos
  suportados, entradas exigidas, limites, alternativas visuais e renderer
  `preserve/compose/ai_edit/ai_generate`. Chave idempotente da prévia inclui
  versão do kit, receita, fonte, fato e briefing. Guardar rota e custo de cada
  tentativa **somente na produção real**. A primeira fatia de catálogo pode
  conter três nichos iniciais e um kit completo por nicho, mesmo que o pipeline personalizado
  comece validando apenas foto/story. Indicar formatos ainda não habilitados no
  produto, sem prometer publicação automática neles. Resolver **zero ou uma**
  referência visual do kit por receita, guardar hashes e impedir que nome,
  logo ou produto fictícios do exemplo apareçam na saída personalizada.
- **Área web — simulador de catálogo:** carregar `catalog_kit/version` e seus
  ativos estáticos, exibir visualizações por canal e comparar kits sem
  `brand_preview_session` ou geração individual. Persistir somente seleção e
  eventual preferência do negócio. Link pode ser enviado pelo WhatsApp; nenhuma
  rede precisa estar conectada.
- **F06 — aprovação:** prévia, legenda e destino continuam aprovados por hash.
  Mudança de kit ou receita gera nova candidata, sem transferir aprovação.
- **F07 — aprendizado:** registrar escolha do kit, motivo de ajuste/rejeição,
  aceitação das peças e custo por aceita; desempenho da rede fica separado de
  atribuição de vendas.

## Eval antes de ampliar a biblioteca

**Eval do catálogo:** três kits iniciais (cafeteria, manicure e personal), com
dez posts exemplares e os formatos anunciados em cada pacote. Medir tempo até
escolha, adequação ao nicho, qualidade das peças ampliadas, coerência entre formatos e se o
cliente entende que a marca/fotos são fictícias. Medir custo de **produção do
catálogo por versão** e tráfego por visita, sem imputar dez gerações ao cliente.

**Eval de produção real, separado:** com foto autorizada, fato vigente e kit
escolhido, comparar **(a)** prompt sem kit, **(b)** manifesto compacto do kit,
**(c)** manifesto + uma referência visual relevante, **(d)** composição local
pela receita. Fixar mesmo produto, texto e formato, sem comparar prompts
diferentes como se fosse ganho do kit. Registrar fidelidade do produto, texto/
logo corretos, aderência à direção, taxa de aceitação sem ajuste, número de
tentativas, latência, tokens e custo por peça aceita. Uma ótima vitrine não
valida sozinha a produção personalizada. Sem qualidade >= gate F04 com material
consentido, corrigir a receita antes de comercializar novos formatos.
