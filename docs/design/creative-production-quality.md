# Plano de qualidade criativa — imagem, story, vídeo e avatar

Origem em 26/10/2026; reconciliado em 28/10/2026. Estado: **preparo visual e
acabamento do kit implementados no modo simulado; integração real e gate comercial
BL04.3 pendentes**. O [SDD BL04](../phases/BL04-context-and-ai-production.md) e
as [decisões atuais](../DECISIONS.md) prevalecem sobre diagnósticos datados.
Responsáveis: F03 (entender/planejar), F04 (produzir/revisar), F05 (avatar),
F06 (aprovar/publicar), F07 (franquia/custo). Referência de avaliação:
`../evals/priscila-public-reference-2026-10-26.md`.

**Refinamento posterior de produto:** a
[biblioteca de identidade visual e receitas](brand-library.md) define a escolha
do cliente quando não possui kit. IA visual continua candidata prioritária onde
traz ganho de qualidade, mas a rota de composição local com foto real e layout
aprovado precisa ser comparada no mesmo caso. Nenhuma das duas rotas é liberada
comercialmente por antecipação; custo por peça aceita e avaliação do dono
decidem. A expressão “rota principal” abaixo descreve a hipótese anterior ao
benchmark, não uma escolha irrevogável de renderer.
Depois da escolha, o kit versionado fornece manifesto/receita e **no máximo uma
imagem de referência do kit** relevante à geração personalizada; a galeria demonstrativa
inteira não é enviada a cada chamada. Ver o
[eval específico de custo e aderência](brand-library.md#eval-antes-de-ampliar-a-biblioteca).

## Baseline técnico diagnosticado em 26/10/2026

- `app/adapters/editorial_ai.py` chama IA para **texto estruturado**; a proposta
  contém título, ângulo, IDs de fatos e três tipos genéricos de cena. Não contém
  descrição visual validada da foto, identidade visual completa ou seleção de
  momentos do vídeo. Foto/vídeo sem legenda não são interpretados visualmente.
- `app/adapters/static_preview.py` desenha a mesma composição com Pillow:
  cabeçalho do negócio, foto dentro de caixa, painel grande com `CONFIRA`, fato
  e `Saiba mais`. `app/adapters/video_preview.py` monta cenas e cortes temporais
  com Pillow/FFmpeg. O vídeo fica sem áudio e sem legenda de fala sincronizada.
  São provas técnicas do pipeline, **não** imagens ou vídeos gerados por IA visual.
- A amostra interna da cafeteria encontrou texto/logo duplicados numa arte já
  pronta e produto pequeno num frame bruto. Cor HEX, nome e texto factual não
  formam um sistema de marca nem uma direção de arte. Os artefatos vistos não
  passam por avaliação da proprietária.

**Decisão de produto: usar a rota visual que passar no gate por receita.** O
sistema junta objetivo, contexto vigente, kit aprovado, referências autorizadas,
foto/clipe enviado, texto factual e CTA num briefing. Para cada receita, compara
gerar/editar com IA visual e compor localmente com direção de arte aprovada,
seleciona a rota validada e confere o arquivo antes de oferecer revisão e
aprovação. A IA pode produzir a composição quando entregar fidelidade e
qualidade suficientes; a composição local pode preservar melhor uma foto real e
texto exato. `preserve` é obrigatório para arte já pronta. Pillow, FFmpeg,
PhotoCraft e FilmCraft são motores de execução possíveis, não direção criativa
por si sós. O template universal atual não é uma receita comercial aprovada.

**Estado atual:** a geração visual real continua **desconectada do produto**.
O preparo de referências, pedido/ledger e acabamento de kit já existem no modo
simulado; adapter/orquestrador real e workflow isolados têm testes, sem guarda
real registrada/ligada ao dispatcher. Pillow/FFmpeg seguem como baseline técnico.
No ensaio de 26/10, fora do pipeline de cliente, a primeira
chamada paga falhou por falta de saldo, e uma nova chamada após recarga gerou
imagem por US$ 0,054885. A existência de WhatsApp,
Temporal, prévias privadas e aprovação simulada não significa geração visual
por IA ponta a ponta.

## Impacto da mudança na implementação existente

- **Reaproveitar:** autenticação, tenants, cobrança, recepção/armazenamento de
  materiais, fatos confirmados, roteiro versionado, Temporal, idempotência,
  prévias privadas, aprovação por versão e a estrutura de publicação. Esses
  contratos continuam necessários com qualquer provedor criativo.
- **Completar a seleção de receita:** a prévia local mantém seus renderers e
  a BL04.2 já separa preparação/pedido/acabamento fake. A integração real precisa
  ligar receita/provedor, saída, briefing e proveniência/custo da tentativa,
  preservando revalidação, fencing, idempotência e limpeza. Ajuste da peça deve
  gerar nova versão com aprovação própria; a regeneração automática ainda falta.
- **Completar e integrar:** inspeção visual da fonte, briefing/kit e referências
  existentes; guarda real do adapter Images API, orçamento/ledger e liquidação
  por tenant/tentativa; checagem factual/visual e avaliação humana. Vídeo com áudio/legenda e geração
  por IA ficam em gates separados. O template atual permanece apenas como
  baseline técnico, sem exigir migração dos dados centrais dos clientes.

O teste da API mede custo e capacidade de **uma edição de foto**, não custo de
peça aprovada. A transformação recriou o croissant; fidelidade do produto real,
tipografia, revisões, rejeições e vídeo ainda precisam de medição.

O [eval de contexto completo](../evals/visual-context-eval-v1.md) acrescenta
fixture fictício com todos os campos atuais relevantes e kit/catálogo/concorrência
propostos, mock de ferramentas de leitura e três chamadas comparáveis da mesma
foto CC0. Flare/medium custou US$ 0,026272 contra US$ 0,060232 de Flare/high
e Sunburst/high; foi visualmente promissor nesta amostra, mas as saídas falharam
em texto literal e não provam fidelidade comercial. O ensaio sintético de
[28/10](../evals/bl042-synthetic-brand-finish-2026-10-28.md) já exercitou cena de IA
com acabamento exato, fora do worker. A comparação por receita com a peça completa
da IA, mesma rubrica e custo por aceita continua pendente de gate comercial.

O cliente não deve precisar saber qual modelo foi escolhido, criar prompts,
montar cenas ou abrir um editor. Há **dois inícios equivalentes** para o mesmo
percurso: uma mensagem/mídia recebida e uma sugestão programada pelo sistema
quando não chegou material novo. A segunda usa o kit, acervo autorizado e fatos
vigentes, escolhe um tema não repetido e pede material/confirmação se faltarem
elementos para uma boa peça. Cadência e pausa são escolhas do cliente; peça
proativa segue o mesmo gate de qualidade, orçamento e aprovação explícita.

O objetivo de negócio é gerar interesse útil: visitas ao perfil, clique para
contato, mensagens recebidas, agendamentos/pedidos que puderem ser atribuídos e
feedback do comerciante. Otimizar apenas curtidas/visualizações pode levar a
conteúdo chamativo sem clientes. Métricas de rede não provam aumento de vendas;
o relatório distingue observado de declarado e não promete causalidade.

Prévias geradas devem ser preservadas enquanto a conta estiver ativa. Plano
vencendo depois do início permite concluir e revisar, mas bloqueia novas criações
e publicação até renovação. Recuperação do autor sem acesso será restrita a staff,
com ação auditada. Esses contratos ainda precisam de implementação coordenada.

## Contrato do percurso criativo

**Fidelidade da cena é um gate, não só preferência de estilo.** O briefing
classifica se a peça pretende retratar `real_venue`, `real_product`,
`generic_concept` ou `authorized_archive`. Para `real_venue`, exigir foto/vídeo
do próprio local e conservar elementos reconhecíveis; IA não inventa salão,
fachada ou equipe. Para `real_product`, partir da foto autorizada do item e
comparar saída com o original para detectar troca de ingrediente, porção,
embalagem ou aparência. Em delivery, um fundo neutro pode mudar, mas o alimento
e a embalagem permanecem fiéis. Texto/áudio sem mídia pode render arte gráfica
ou conceito explicitamente ilustrativo; se o pedido exigir foto do prato ou
local reais, perguntar pelo material. As duas opções precisam de revisão e
aprovação antes de publicação. A decisão, hash do original e instruções de
edição acompanham cada tentativa; resultado sem fonte ou fidelidade suficiente
é bloqueado, não reclassificado silenciosamente como foto real.

1. **Entender a fonte** (F02/F03): classificar `raw_photo`, `finished_art`,
   `raw_video`, `voice`, `text_only`; extrair metadados, OCR, transcrição e
   amostras de frames quando autorizado. Detectar produto/serviço e área de
   interesse com confiança; dúvida produz pergunta curta pelo WhatsApp. Arte
   pronta vai a `preserve` e nunca recebe título/logo repetidos automaticamente.
2. **Montar kit de marca progressivo** (F03): referências originais autorizadas,
   logo, paleta secundária, fontes/licenças, estilos aceitos/rejeitados, tom,
   enquadramento preferido e proibições. Onboarding continua curto; o dono pode
   confirmar escolhas propostas pelo sistema em vez de preencher um formulário
   extenso. Fatos comerciais confirmados/validade ficam separados do estilo.
3. **Criar briefing versionado** (F03.3b): objetivo, público, mensagem principal,
   gancho, fonte visual, tipo de peça, duração/proporção, cena a cena, textos
   exatos derivados de fatos, CTA, direitos, risco de alegação e teto de custo.
   Guardar IDs/hashes das fontes e versão do kit. A IA propõe opções; um
   validador impede preço, oferta, produto ou resultado sem origem confirmada.
4. **Escolher rota** (F04): para nova foto/story/carrossel, usar a receita e o kit
   aprovados, a mídia real e a evidência de qualidade/custo para escolher entre
   composição local e geração/edição por IA. Arte já finalizada é preservada;
   clipe real pode pedir edição em vez de cena nova; vídeo generativo/identidade
   exigem orçamento e direitos próprios. A escolha usa pedido do cliente,
   qualidade esperada, material, direitos e teto remanescente. As três direções
   são apresentadas uma vez na escolha do kit; uma peça individual segue o
   limite de propostas/revisões da receita e do plano.
5. **Produzir e verificar** (F04/F05): o modelo visual recebe briefing estruturado
   com referências versionadas, dimensões, cópia exata e restrições. A peça pode
   sair completa da IA. Se preço/texto/logo vierem incorretos, bloquear a saída;
   corrigir por uma revisão limitada ou por composição exata sem degradar o
   visual. Não substituir silenciosamente a peça por template genérico.
   Revisão automática verifica OCR, produto visível, ausência de repetição,
   corte, contraste, áreas seguras, proporção, áudio, legenda, fonte, direitos,
   contexto vigente e orçamento. Visão de IA ajuda a sinalizar problemas, mas
   não substitui revisão humana do piloto. Falha vira nova versão privada ou
   pergunta; nunca publicação automática silenciosa.
6. **Aprovar e aprender** (F06/F07): peça, legenda, destino e horário aprovados
   por hash. Registrar motivo de aceitação/ajuste/rejeição, custo de todas as
   tentativas e receita utilizada. Sinais viram hipótese de preferência, nunca
   fato comercial; comparar alcance apenas quando a plataforma fornecer dados.

Exemplos do que o cliente pode pedir pelo WhatsApp:

- “Faz um story com a foto do croissant e coloca R$ 20 hoje”: confirmar que
  produto, preço e validade são fatos do negócio; usar foto e kit de marca no
  modelo de imagem para gerar o story com texto/CTA; conferir por OCR e visão;
  enviar prévia para aprovar. Se o preço não estiver confirmado, perguntar antes.
- “Transforma esta foto em um vídeo curto”: encaminhar para imagem→vídeo
  generativo se a franquia/direitos permitirem; caso contrário, oferecer motion
  da foto como formato distinto, sem fingir que os dois são equivalentes.
- “Esse post já está pronto; só publica”: preservar pixels da arte, verificar
  direitos e legenda/horário e pedir aprovação da versão final; não gerar outro.
- “Cria um vídeo comigo falando”: fluxo F05 de consentimento específico de
  identidade/voz; não inferir autorização de uma foto ou de um áudio comum.

## Formatos e promessa honesta

| Formato | Receita inicial a avaliar | Quando usar IA visual | Principal critério de qualidade |
| --- | --- | --- | --- |
| Foto do feed | IA recebe briefing e foto real, gera a peça completa ou edição; arte já pronta é preservada | Comparar IA e composição aprovada, com fonte real ancorando o produto | Pessoa reconhece o produto e a marca; texto não repete a fonte |
| Story | IA compõe em 9:16 com uma ideia e CTA; foto/clipe real ancora o assunto | Comparar IA e composição aprovada, com limite de área e texto | Leitura rápida em celular e objeto dominante |
| Carrossel | IA cria direção e slides com funções distintas; validador mantém coerência e fatos | Candidata para capa/apoios após gate próprio | Narrativa útil sem slides genéricos repetidos |
| Reel com vídeo real | Seleção semântica de momentos, corte, áudio original útil, legenda sincronizada e ritmo | Melhoria de imagem/áudio ou cena adicional com benefício medido | Parece o negócio real, tem começo/meio/fim e fala coerente |
| Motion de foto | IA planeja visual/ritmo; foto real recebe movimento, recortes e tipografia animada | Visual/cena de apoio quando necessário; render de movimento pode ser local | Declarado como motion; não fingir gravação real |
| Cena inteiramente gerada | Só quando o objetivo admite ilustração e o dono aceita isso | Modelo de vídeo/imagem com identidade controlada | Não representar produto, pessoa ou local sintéticos como reais |
| Avatar do dono | Vídeo curto consentido com rosto e voz, separado por identidade/tenant | Provedor especializado após benchmark F05 | Semelhança, sincronização e PT-BR aprovados pelo dono |

Animação de texto/foto é edição; vídeo generativo cria novos frames e tem custo,
risco factual e controle diferentes. Não oferecer “vídeo diário com avatar” no
plano de R$ 99 até medir viabilidade. Quando não houver material suficiente,
oferecer ideia/roteiro e orientação de captação; não preencher a ausência com
foto sintética de um prato ou atendimento como se fosse o negócio real.

## Provedores, execução e experimento

- Os ensaios de 26–28/10 compararam candidatos de imagem e acabamento com dados
  fictícios/CC0 fora do percurso de cliente. Resultados/preços daquelas execuções
  estão nos evals datados; não há modelo comercial vencedor nem autorização
  recorrente para novo gasto. A avaliação integrada deve fixar fonte, instruções,
  tamanho/qualidade e teto, comparando saída completa e acabamento exato pela
  mesma rubrica de fidelidade, texto/logo e custo por peça aceita.
- Texto comercial e logo podem ser camadas controladas quando a geração por IA
  alterar grafia ou identidade. Renderizar em workers isolados; PhotoCraft,
  Pillow/SVG, FFmpeg ou FilmCraft podem executar receitas aprovadas. Para vídeo
  generativo, fazer spike separado de qualidade e custo; preço por segundo não
  inclui retrabalho e não justifica incluí-lo por padrão. Provedor de avatar
  exige consentimento específico, comparação PT-BR e processo de revogação.
- Um lote local com mídia sintética testa segurança e integração. Avaliação
  **comercial** requer originais e permissão do negócio. Fotos públicas da
  cafeteria servem apenas como referência privada; não serão usadas em chamadas
  pagas, treinamento, publicação ou amostra comercial sem autorização.

Fontes técnicas a revalidar no spike:
[edição de imagens OpenAI](https://developers.openai.com/api/reference/resources/images/methods/edit),
[guia GPT Image](https://developers.openai.com/api/docs/guides/image-generation),
[preços OpenAI](https://developers.openai.com/api/docs/pricing),
[preços Runway](https://docs.dev.runwayml.com/guides/pricing/).

## Economia do plano de R$ 99

Meta **total**: COGS + impostos + aquisição amortizada + atendimento atribuído
`<= R$ 50/cliente/mês`; margem restante não é lucro líquido demonstrado. A
divisão preliminar R$ 30 tecnologia/cobrança/mensageria e R$ 20 demais custos
é apenas envelope para medir, não valor observado. Calcular custo por **peça
aceita**: soma de inspeção, LLM, imagens/vídeos gerados (inclusive descartados),
render, storage/tráfego, WhatsApp, retries e suporte / peças aprovadas. Registrar
taxa de rejeição, chamadas por peça e p95 além da média.

Antes de cada chamada paga: reserva atômica por operação/tenant e custo máximo,
limite de tentativas, reconciliação de status incerto, liquidação pelo valor
faturado e alerta quando a margem estiver ameaçada. Quota mensal deve ser por
formato e custo ponderado, não só número de posts; o mesmo teto não comporta
promessa de publicações ilimitadas, vídeos generativos diários e avatares. A
franquia do plano básico, adicionais e preço dos planos superiores serão
definidos com custo medido e taxa de aceite, antes de oferta comercial.

## Ordem concreta de implementação e gates

| Ordem | Entrega | Gate observável |
| --- | --- | --- |
| 1 — F03.3b/F04.1b | Inspeção de mídia, `preserve/raw`, kit de marca e briefing; adapter de geração/edição visual por IA integrado ao worker e à prévia existente; comparar saída completa da IA com acabamento exato quando necessário | Mesmo original autorizado, prévias da **API do produto** no celular, escolha e motivo do dono, OCR/produto/fato corretos, custo por aceita |
| 2 — F04.2b | Corte semântico de clipe real, áudio/legenda sincronizados e motion de foto com narrativa | Revisão do dono em celular; nenhuma fala cortada/mudada; custo e tempo de exportação medidos |
| 3 — F04.3/F06 | Entregar a receita aprovada via WhatsApp, ajuste versionado e publicação fake; Meta real depois | Aprovação apenas da versão final; nenhum material cru ou reprovado publicado |
| 4 — F04 expansão | Carrossel e outras receitas por segmento | Repetir gate de formato, fatos, direitos e custo; não copiar layout universal |
| 5 — F05 | Avatar/cena generativa opcional, com plano próprio se necessário | Consentimento, identidade/voz, custo por aceita e revogação comprovados |

Plano futuro de laboratório (vídeo somente após gate/escopo próprio): um negócio
consentido, 10–20 originais de foto/clipe e
briefings reais, três saídas que ele publicaria (feed, story, reel), duas rotas
comparáveis por fonte e registro de todos os descartes. Depois aplicar os gates
amostrais atuais F03/F04 (20 peças, quatro segmentos; >=90% de nota 4/5 de
legibilidade/visibilidade; >=80% aceitas sem ajuste; zero erro crítico). Sem
originais autorizados, execução do produto e avaliação comercial permanecem
pendentes; testes sintéticos não fecham o marco.

Versão anterior à reconciliação: [snapshot integral de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/creative-production-quality.md).
