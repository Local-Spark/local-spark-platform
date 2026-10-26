# BL — Biblioteca visual, vitrine e produção por kit

Data: 26/10/2026. Estado: **UI exploratória BL01 em andamento; catálogo e kit final pendentes**.
Esta trilha cruza F01 (área cliente), F03 (escolha/contexto), F04 (mídia) e F06
(aprovação). Ela muda a ordem dessas entregas, sem substituir a arquitetura,
autenticação, RLS, Temporal ou os contratos de publicação já existentes.

## Decisão central

A equipe produz kits demonstrativos completos **uma vez por versão**, com marca
fictícia, dez posts, stories, reels, exemplos de conversa WhatsApp e de dia sem
nova mensagem. A web os mostra em simuladores de Instagram/Facebook/TikTok
internos; visitar a vitrine não gera imagem, não consulta contas sociais e não
precisa de dados visuais do cliente. Cada kit contém também receitas editáveis,
direção fotográfica, paleta, tipografia, regras de corte/texto e direitos.

Após escolher, o cliente pode adaptar o kit ao negócio. F03/F04 montam novas
peças com fatos e materiais reais, usando o manifesto compacto do kit e, se a
rota de IA visual precisar, **no máximo uma imagem de referência do kit para o
formato/receita escolhido**, além do material do próprio cliente. O texto e a
marca fictícios do exemplo não entram na saída. Cada publicação real continua
precisando de aprovação individual. O contrato detalhado está na
[biblioteca de identidade visual](../design/brand-library.md).

## Ordem de entrega e aceite

### BL01 — Kit piloto e contrato do catálogo

- **Escopo:** escolher um segmento inicial (cafeteria fictícia), definir
  manifest/validator, versionamento, licenças, formatos, receitas-fonte e
  armazenamento dos exemplos. Produzir **um kit de qualidade comercial** com
  dez posts, pelo menos um story e um reel demonstrativo completo, usando só
  materiais próprios/licenciados. O catálogo pode começar como JSON validado
  no repositório e mídia em armazenamento de objetos; publicação de nova versão
  promove um conjunto imutável. Não criar CMS antes da primeira curadoria.
- **UI em paralelo (BL01-UI):** abrir uma vitrine no app desde o primeiro kit,
  com abas internas Instagram/Facebook/TikTok e mídia demonstrativa estática.
  Ela pode começar com pautas e capas identificadas como protótipo; não oferece
  escolha nem afirma que vídeo/catálogo estão concluídos. A implementação do kit
  final substitui esses exemplos sem refazer a navegação.
- **Aceite:** qualquer exemplo abre inteiro no celular, o reel é reproduzível,
  nenhuma fonte/direito fica sem registro e a receita editável consegue gerar
  uma nova peça. Layout universal atual não vale como kit piloto.
- **Status:** exploração web inicial entregue com três fotos fictícias e pautas
  ilustrativas. Manifesto, mídia final, reel reproduzível, receitas, direitos e
  kit completo ainda pendentes.

### BL02 — Prova de reaplicação e economia

- **Escopo:** com o kit BL01 fixado, produzir pelo **pipeline real** uma nova
  foto/story para um negócio fictício distinto, usando foto própria/licenciada e
  fato válido. Comparar quatro rotas no mesmo caso: sem kit, manifesto do kit,
  manifesto + uma referência do mesmo formato e composição local pela receita.
  A IA pode criar/tratar a cena; texto, preço e logo exatos podem ser compostos
  deterministicamente. Guardar modelo, parâmetros, tokens, tentativas,
  latência, resultado e custo completo.
- **Aceite:** amostras cegas no celular; nenhuma marca/produto inventado; preço
  e CTA literais; ao menos uma rota aprovada por dono de material consentido
  antes de declarar qualidade comercial. O ganho de custo só existe se o
  **custo por peça aceita** cair, incluindo falhas e revisões. Até lá, resultado
  sintético é técnico, não validação comercial.
- **Status:** não implementada. O eval visual atual é de uma peça isolada, não
  prova reaplicação do kit.

### BL03 — Completar e ampliar a vitrine web

- **Escopo:** expandir para **três kits iniciais em nichos distintos**:
  cafeteria/alimentação, profissional com agenda (manicure) e personal trainer.
  Cada kit exige fotos, pautas e formatos próprios do nicho: para manicure,
  resultado autorizado do atendimento e disponibilidade de horários; para
  personal, rotina/serviço sem promessas de resultado físico. Conectar o catálogo
  responsivo na `local-spark-web`. O visitante
  explora grade de dez posts, abre legenda/arte, percorre stories, reproduz reels
  e alterna entre simuladores de Instagram/Facebook/TikTok **dentro do produto**.
  Mostrar disponibilidade por plano e canal; a marca fictícia, ausência de
  publicação e capacidades ainda não homologadas ficam claras.
- **Aceite:** mesma mídia do catálogo para todos, sem chamada de IA ou banco de
  cliente ao alternar kits; navegação por teclado e celular, loading/erro de
  mídia e fallback; usuário entende o que escolhe sem conectar rede social.
  Cada nicho passa por revisão própria de qualidade, direitos e aplicabilidade
  antes de aparecer como opção selecionável. Medir custo de curadoria por versão
  e tráfego/CDN por visita.
- **Status:** casca navegável antecipada em BL01; mídias finais, três kits,
  carregamento do catálogo e reprodução de vídeo ainda pendentes.

### BL04 — Escolha versionada por negócio

- **Escopo:** API do proprietário registra `kit_id/version` escolhido e ajustes
  opcionais de cor, fonte, foto, logo e tom. A web mostra prévias rápidas de
  feed, story e capa vertical usando receitas/tokens aprovados; não faz dez
  chamadas de IA para cada ajuste. A seleção é idempotente, auditada,
  protegida por tenant/RLS e não transfere aprovação de peças antigas. Na web,
  aceitar kit é uma ação clara após a comparação; o cliente pode mudar depois.
  F03 passa a incluir kit aprovado no snapshot/briefing de novas propostas.
- **Aceite:** outro tenant não lê/altera a seleção; replay e concorrência
  preservam uma versão vigente; mídia/receita antigas mantêm provenance;
  confirmar o kit nunca é tratado como autorização para publicar. O cliente
  consegue voltar ao padrão, comparar antes/depois e concluir sem fornecer logo
  ou fotos; cada alteração aprovada gera nova versão aplicada ao negócio.
- **Status:** não implementada.

### BL05 — Jornada de conteúdo e piloto controlado

- **Escopo:** F03 e F04 usam o kit selecionado para mensagens recebidas e dias
  sem nova entrada. F04.3/F06 entregam candidata, ajuste e aprovação via
  WhatsApp simulado; publicação simulada mantém hash/versão exatos. Homologação
  Meta real, custo mensal, suporte, direitos e segurança são gates posteriores
  do piloto/produção. Outros segmentos e formatos só entram após os próprios
  gates de qualidade e margem.
- **Aceite:** um negócio consentido reconhece a direção que escolheu nas peças
  reais, aprova ou pede alteração pelo WhatsApp, e o sistema mostra custo total
  por peça aceita, frequência e erros sem operação manual oculta. A Meta
  restrita não impede testes locais, mas impede a promessa de canal real.
- **Status:** contratos locais F02/F04.3/F06 já existem; aplicação do kit e
  teste comercial ponta a ponta ainda não.

## Fronteiras entre repositórios

| Local | Responsabilidade |
| --- | --- |
| `local-spark-platform` | Schema/validador do catálogo, publicação de versões, índice público/cacheável, seleção autenticada, snapshot por negócio, roteamento e medição de geração. |
| `local-spark-web` | Vitrine e simuladores internos, comparação, detalhes dos exemplos, seleção/edição do kit e estados acessíveis. |
| Armazenamento de objetos + CDN | Exemplos públicos e versionados do catálogo. Mídia real de clientes continua privada e separada por tenant. |

Não criar terceiro serviço de workflow ou repositório para o catálogo inicial.
Uma versão de kit publicada é imutável; revogação de direitos despublica o ativo
e impede novas seleções/gerações dependentes dele. O custo de curadoria do kit é
amortizado; o COGS do plano inclui apenas custos atribuíveis à operação e a
parcela amortizada quando fizer a análise de margem.

## O que mudou na sequência

Antes, o próximo marco era tentar melhorar uma peça do renderer universal e
ampliar o pipeline de geração visual. Agora, **a UI de BL01 acompanha o kit
piloto**, para avaliar a experiência desde o início. BL02 precede ampliar o
catálogo para três kits e automatizar a produção comercial: primeiro provar que
um kit bonito gera nova peça com a mesma qualidade. BL03 completa a vitrine e
BL04 torna os kits escolhíveis.
F03/F04/F06 já implementadas continuam úteis, mas as receitas visuais atuais
seguem como baseline técnico e não são promovidas ao piloto por essa mudança.
