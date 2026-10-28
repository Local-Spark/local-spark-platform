# Sequência de entrega até produção e evolução do escopo

Atualizado em 28/10/2026. Complementa o [índice](../phases/README.md) e a
[trilha BL](../phases/BL-brand-library.md). F00–F08 representam áreas técnicas;
BL01–BL06 ordenam o produto. As duas numerações não são projetos concorrentes.
“Concluído localmente” não significa homologação, qualidade ou operação comercial.

## Base disponível

Identidade/auth própria, onboarding, admin, convites/MFA, cobrança sandbox,
ingestão e tratamento de WhatsApp, fatos/preferências, propostas/roteiros,
prévias técnicas e revisão/publicação falsas. BL01 entrega vitrine fictícia;
BL02 entrega escolha e edição guiada do kit. A auditoria P1–P15 simplificou a
jornada sem apagar os domínios necessários. Nenhuma dessas entregas demonstra
sozinha uma publicação final com qualidade comercial.

## Ponto de retomada em 28/10

BL03.1/BL03.2 estão implementadas localmente. BL04.1 já oferece retrieval/Jev
opcionais no worker dev/test, desligados por padrão e sob aceite único. BL04.2
prepara fontes e prévia fake com kit, mas guarda/dispatcher/worker visuais reais
seguem desconectados. A próxima fatia implementa [C08/C09/C10](../DECISIONS.md)
e coordenação de fontes/acesso/orçamento: concluir/revisar após plano vencido,
preservar prévias enquanto conta ativa e recuperação restrita/auditada por staff.
Depois conectar real, validar BL04.3 e seguir BL05. Materiais WhatsApp associados
já são duráveis (0058); isso não implementa retenção de prévias nem memória geral.

## Ordem até o primeiro piloto comercial

| Ordem | Fase | Entrega e condição de saída |
| --- | --- | --- |
| 1 — local | BL03.1 + BL03.2 | Acervo privado e opcional em Sobre meu negócio: produtos, serviços, promoções, fotos dos itens/local, versão, revisão e aproveitamento consentido de imagem WhatsApp. Sem IA paga no cadastro. |
| 2 | Início BL04 / F03 | Corrigir o contrato criativo para aproveitar título/ângulo/roteiro gerados sem perder validação de fatos; interpretação de pedido livre e recuperação seletiva do contexto/kit/acervo. Comparar decisões/modelos com casos PT-BR. |
| 3 | BL04 / F04 | Integrar geração/edição visual ao produto, provar post/story novos com kit e material reais; medir fidelidade, legibilidade, taxa de aceite e custo por peça aceita. Cada formato passa por gate próprio; vídeo com material real e animação entram por receitas validadas, não por associação com um kit. |
| 4 | BL05 / F03 mínimo | Jornada completa com WhatsApp simulado: mensagem/áudio/foto/vídeo → proposta → prévia → ajuste → aprovação → publicação falsa; iniciativa em dia sem mensagem, cadência simples por formato dentro do plano e pausa. |
| 5 | Homologação F02 + F06 | WhatsApp/Instagram oficiais: conta/app/permissões, vínculo, envio de prévia, respostas, aprovação/agenda/publicação, reauth, reconciliação e coleta autorizada de métricas. Código e mocks avançam antes da liberação Meta. |
| 6 | F07 mínimo | Converter custo medido em planos/franquias por formato, revisões e canais; orçamento/reservas/ledger monetário, cobrança e relatório básico honesto. Receita Stripe mínima já existe. |
| 7 | F08 mínimo | AWS/staging, HTTPS/segredos, CI/CD, storage privado, observabilidade, alertas, suporte, backup/restore e ensaios de falha/carga da primeira coorte. Capacidade cresce por medição. |
| 8 | Piloto comercial acompanhado | Negócio autorizado avalia peças reais; fluxo oficial e limites funcionam; medir aceitação, custo completo, trabalho de suporte e sinais de interesse. Liberar somente formatos/receitas que passaram nos gates. |

Custos monetários básicos e budgets entram **antes** de liberar novas chamadas
pagas na BL04; F07 consolida o produto comercial depois da medição. F08 prepara
staging e infraestrutura em paralelo quando necessário. Esta ordem não exige
esperar cada departamento terminar para começar todo o seguinte, nem coloca
homologação Meta como bloqueio do trabalho local BL03–BL05.

O alvo do plano de entrada permanece R$ 99/mês com custo total máximo pretendido
de R$ 50/cliente/mês, sujeito a comprovação. Qualidade não é substituída por
cobertura de testes. O piloto não exige avatar do cliente (decisão P15).

## Evolução até o escopo ampliado do produto

| Ordem | Entrega | Resultado |
| --- | --- | --- |
| 9 | BL03.3 — Importação assistida do acervo | Foto(s) de cardápio/tabela de serviços gera(m) fichas automaticamente, com evidência por campo, preços/variações e revisão das ambiguidades. Entrega própria após o acervo manual; reaproveita a capacidade multimodal/ledger validada na BL04, sem bloquear a primeira peça. |
| 10 | BL06 | Kits de manicure e personal com qualidade/direitos próprios; catálogo público versionado em objetos/CDN, separado das fotos privadas. |
| 11 | F03 — Pesquisa e otimização avançadas | Referências por nicho/região, concorrentes com fontes permitidas, comparação de formatos/horários e aprendizado/evals versionados. Recomendações ganham evidência do próprio cliente; não copiar conteúdo nem inventar dados privados da concorrência. |
| 12 | F05 | Avatar e voz do próprio cliente, receitas híbridas e cenas generativas, após consentimento, benchmark PT-BR, fidelidade e custo/franquia próprios. |
| 13 | Extensões F06/F07 | Facebook/TikTok e outros canais elegíveis, com adapters/permissões/formatos e relatórios próprios; otimização recorrente dentro da capacidade paga. |
| 14 | Evolução F08 | Escala por coortes até a meta de 200 mil clientes, HA/recuperação, controle de custos, suporte e capacidade de fornecedores comprovados. |

O produto continua sendo operado e melhorado após a conclusão desse escopo.
Não prometer datas ou percentuais de prontidão sem medir gates e dependências.

**Evolução futura sem fase definida:** permitir mais de um número WhatsApp ativo
por negócio. Na versão inicial, manter um número ativo; a forma de vincular cada
pessoa, compartilhar histórico e direcionar mensagens será definida antes dessa
evolução. Isso é independente da quantidade de proprietários com conta web e não
encerra a pendência de operações entre proprietários diferentes.

O [plano de vídeo real e voz](video-real-and-voice.md) detalha roteiro sob pedido
ou proativo, gravação de mãos/produto/ambiente, preservação do original, edição
leve e motion. A entrega de voz sintética continua F05 após o piloto (P15), com
pesquisa isolada possível antes. Foto e story são a oferta inicial decidida; vídeo
e suas franquias/preço permanecem em definição.

## Foto ou vídeo: contrato já especificado

O plano define formatos/quantidades habilitados; a plataforma recomenda a peça
pela intenção, objetivo, validade, kit, material existente e orçamento. Por
exemplo: preço válido com foto real pode sugerir post/story; um clipe mostrando
preparo/resultado pode sugerir reel; uma vaga de agenda pode pedir story curto.
São hipóteses, não uma regra universal de que vídeo sempre vende mais.

BL04 seleciona uma receita elegível para cada pedido; BL05 agenda a cadência
aceita. F06/F07 fornecem métricas reais do próprio negócio; F03 avançada compara
referências permitidas de concorrentes e reavalia a recomendação. Ausência de
material, quota ou evidência resulta em pergunta/alternativa, não invenção. Cada
peça continua exigindo aprovação específica.

Contrato detalhado: [cadência e evidência](editorial-planning-and-evidence.md) e
[inteligência/pesquisa](v0-intelligence.md). Esses recomendadores/pesquisa ainda
não foram implementados só porque seus SDDs existem.

## JEV e Motion: candidatos dentro dessas etapas

Jev já pode interpretar pedidos e selecionar candidatos no worker local dev/test,
opcional e desligado por padrão; qualidade/conversa/comercial seguem em avaliação
PT-BR. Ordenação mais ampla e seleção de receitas permanecem candidatas. O fornecedor descreve
saídas tipadas e confiança; geração criativa continua em outro modelo. Permissão,
quota e aprovação permanecem regras do domínio. [Documentação TypeSafe](https://docs.typesafe.ai/introduction).
A seleção de versão e preço deve ser revisada no benchmark; o estudo de 27/10
registrou a release 1.14 e o preço de US$ 0,042/1M tokens de entrada, com saída gratuita.
[Modelos oficiais](https://docs.typesafe.ai/models).

Claude Motion é candidato para curadoria/teste de animações de ofertas, textos
e fotos na F04/BL04, disponível em beta Team/Enterprise com exportação MP4.
O guia descreve animação por código, sem filmagem generativa realista. Uma
integração automática no SaaS exige contrato API/execução e custo verificados;
o recurso da interface não prova disponibilidade de endpoint público.
[Guia oficial](https://support.claude.com/en/articles/17454997-get-started-with-claude-motion).

Proposta de engenharia para animações: receitas curadas, versionadas e
reutilizáveis, parâmetros de kit/texto/mídia e render isolado. Medir qualidade e
custo frente às alternativas. Não executar código arbitrário do modelo no worker
principal nem contratar outra ferramenta antes desse teste. BL03 não integra
Jev/Motion, não instala seus SDKs e não chama APIs pagas.

Versão anterior à reconciliação: [snapshot integral de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/delivery-roadmap-2026-10-27.md).
