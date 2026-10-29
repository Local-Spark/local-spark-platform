# Fases de implementação

Atualizado em **29/10/2026**. Este índice distingue **o que existe no ambiente
local**, **a próxima fase** e os gates para piloto/produção. A v0 completa
continua distribuída entre F00–F08; a trilha [BL](BL-brand-library.md) define
a ordem de produto para aplicar um kit visual e o acervo do negócio a uma
peça nova.

## Estado atual

- F00/F01: fundação, identidade, onboarding, cobrança sandbox, área do cliente
  e admin mínimo locais. Homologação externa e staging continuam pendentes.
- F02: webhook, vínculo do remetente, recibos de texto/foto/áudio/vídeo,
  histórico preservado de envios associados e respostas limitadas locais.
  A restrição Meta observada no smoke impede afirmar homologação real.
- F03: fatos/preferências, ideia e roteiro versionado com edição local.
  Pesquisa ampla, qualidade comercial e sugestão proativa ainda pendem.
- F04/F06: prévias estáticas/vídeo locais e candidata/aprovação/publicação
  **simuladas**. F03 congela kit; BL04 recupera acervo no worker experimental e
  aplica kit à simulação. Geração visual real continua desconectada.
- BL01: um kit fictício de cafeteria e simuladores públicos/cliente locais.
  Ver a vitrine não é escolher ou editar o kit.
- BL02: seleção e edição guiada do kit na área autenticada, logo privado,
  prévias ampliáveis, rascunho/confirmado e histórico por negócio locais.
- BL03.1/BL03.2: catálogo manual e fotos privadas de item/espaço locais;
  BL03.3 importação de cardápio posterior.
- Contratação: um negócio por organização (`0057` aplicada), cobrança por
  organização e aceite único de IA antes do checkout. Sem check individual
  de transcrição, modelo ou fornecedor no WhatsApp/Sobre meu negócio.

## Próxima fatia e decisões aprovadas pendentes

A fase ativa é [BL04](BL04-context-and-ai-production.md). A parte 1 entrega a
guarda concreta de fontes, aceite, acesso, reserva/claim e resultado privado,
incluindo roteiro/cobrança e troca de telefone, com roles existentes e mocks.
A próxima fatia é a **parte 2**: modo real explícito na persistência/API e ligação
do workflow/runner ao dispatcher/worker, com percurso ponta a ponta simulado.
A **parte 3** faz a chamada real controlada com credenciais/fontes/budget explícitos.

A admissão `visual_fake` já revalida fontes, aceite e plano sob locks; depois de
admitida, a criação conclui e permite revisão privada após vencimento financeiro.
Novas criações/publicação esperam renovação. Concluídas e proveniência são
preservadas sem limpeza por prazo; a janela de aprovação continua independente.
O renderer local legado ainda tem limites próprios. Escritores atuais têm o
[protocolo documentado](../design/BL04-effect-guard.md); futuras capacidades de
acesso precisam participar dele antes de serem adicionadas.
Outro owner não assume pendência do autor original. A implementação da recuperação
staff C10 foi adiada pelo proprietário em 29/10, para evolução de gestão de acesso
e suporte; não bloqueia o fechamento do recorte simulado. A exceção permanece
bloqueada até a entrega futura. Retenção após encerramento
fica para essa fase, sem nova exclusão automática agora. Detalhes e lacunas em
[decisões](../DECISIONS.md).

## Próximas entregas em ordem

| Ordem | Fase | Entrega demonstrável | Estado |
| --- | --- | --- | --- |
| 1 | [BL01](BL-brand-library.md#bl01--kit-piloto-e-vitrine-local) | Kit piloto de cafeteria, dez posts, stories, reel e vitrine. | Técnica local pronta; revisão comercial/direitos pendente. |
| 2 | [BL02](BL-brand-library.md#bl02--escolher-e-editar-o-kit-piloto-para-um-negócio) | Dono seleciona o kit e ajusta cores, fontes, logo, textos e composição guiada de feed/story/capa vertical; vê e confirma prévias versionadas. | Implementada localmente; gate comercial do kit segue pendente. |
| 3 | [BL03](BL-brand-library.md#bl03--acervo-progressivo-em-sobre-meu-negócio) | Dentro de “Sobre meu negócio”, cadastrar opcionalmente produtos/serviços e fotos reais do espaço; dado privado, confirmado e versionado. | **BL03.1/BL03.2 implementadas localmente; BL03.3 posterior.** |
| 4 | [BL04](BL-brand-library.md#bl04--recuperar-contexto-e-produzir-uma-peça-nova) | Áudio/texto livre resolve o item e fontes automaticamente; IA visual/receita gera nova peça com kit aplicado; medir fidelidade, aceite e custo completo. | **Em implementação local**; ensaio sintético isolado não encerra o gate. |
| 5 | [BL05](BL-brand-library.md#bl05--jornada-completa-local-ajuste-e-proatividade-mínima) | WhatsApp simulado e proposta sem mensagem percorrem prévia, ajuste, aprovação e publicação falsa com as mesmas regras. | Contratos F02/F04/F06 parciais já existem; integração pendente. |
| 6 | [BL06](BL-brand-library.md#bl06--ampliar-a-biblioteca-e-servir-o-catálogo-em-escala) | Kits de manicure e personal, catálogo público versionado em objetos/CDN e revisões por nicho. | Planejada após prova de reaplicação. |

BL02 e BL03 podem avançar com a Meta restrita. BL04 testa localmente com
mocks e, para fechar qualidade comercial, precisa de avaliação de titular
com material consentido. BL05 exercita integração e falhas locais; uso real
depende da homologação F02/F06. A expansão BL06 não precisa atrasar o primeiro
piloto de cafeteria, mas não deve anteceder uma peça personalizada aprovada.

O [roadmap completo até produção e expansão](../design/delivery-roadmap-2026-10-27.md)
organiza homologação Meta, custo/franquia, AWS e piloto depois da jornada local,
seguido de importação de cardápio, novos nichos, pesquisa, avatar e multicanal.
BL03 atual entrega cadastro manual/fotos; [BL03.3](BL03-business-collection.md#bl033--importação-automática-de-fotos-de-cardápio-planejada)
extrairá dados de fotos de cardápio/tabela de serviços e preencherá o acervo
automaticamente como rascunho para conferência. Não bloqueia a primeira peça.

## Fases transversais até produção

| Fase | Escopo | Estado/gate |
| --- | --- | --- |
| [F00](F00-foundation.md) | Fundação, Postgres/RLS, Temporal e observabilidade base | Concluída localmente. |
| [F01](F01-identity-onboarding.md) | Identidade, onboarding, admin e cobrança mínima | Código local; staging/homologação externa pendentes. |
| [F02](F02-whatsapp-ingestion.md) | WhatsApp, materiais e confirmação | Local/mock; Meta real pendente. |
| [F03](F03-editorial-research.md) | Contexto, pauta, roteiro, cadência proativa e pesquisa | Parte local; BL02–BL05 integram contexto/kit e proatividade mínima. Pesquisa ampla fica depois. |
| [F04](F04-media-recipes.md) | Receita visual, IA de imagem/vídeo, prévia e ajuste | Renderer local é baseline técnico; BL04 fecha primeira receita aprovada. |
| [F05](F05-avatar-generative-video.md) | Avatar, voz e cenas geradas | Avatar do cliente após o primeiro piloto comercial (P15), com consentimento, qualidade e orçamento próprios. |
| [F06](F06-instagram-publishing.md) | Aprovação, agenda, publicação e métricas Instagram | Fluxo falso local; Meta/Instagram reais pendentes. |
| [F07](F07-billing-reports.md) | Franquias, assinatura e relatórios honestos | Cobrança mínima F01.5 local; limite por formato e custo real antes do piloto pago. |
| [F08](F08-production-scale.md) | Deploy, segurança, suporte, recuperação e escala | Staging, backup/restore, capacidade e operação ainda pendentes. |

**Antes do primeiro piloto real:** completar BL02–BL05 para as receitas
prometidas; fechar qualidade e custo por peça aceita com um negócio consentido;
homologar WhatsApp e Instagram oficiais; aplicar franquia/orçamento F07 e
operar staging F08 com logs, alertas e recuperação. Aprovação de peça é
distinta de confirmação de preço ou escolha do kit. Não prometer frequência,
venda, alcance ou canal não comprovados.

**Depois do piloto:** BL06 amplia nichos; F03 acrescenta referências de
concorrentes com fontes permitidas e evidência de ganho; F05 acrescenta avatar
somente se qualidade, consentimento e margem sustentarem o formato. A meta de
200 mil clientes orienta capacidade gradual F08, não bloqueia a primeira
coorte.

## Documentos de decisão

- [Biblioteca e kits](../design/brand-library.md): amostras públicas, kit
  aplicado e acervo privado separados.
- [Contexto e geração](../design/business-context-and-generation.md):
  snapshots, adapters, ledger e dados confirmados.
- [Qualidade criativa](../design/creative-production-quality.md): gates
  por receita e comparação IA/composição.
- [Cadência e planos](../design/editorial-planning-and-evidence.md):
  franquia do plano, recomendação explicável e evidência.
- [Decisões vigentes e abertas](../DECISIONS.md): aceite, retenção, acesso,
  recuperação de pendências e escolhas ainda dependentes de evidência.
- [SDD geral](../SDD.md) e [contexto vivo](../PROJECT.md):
  contratos e decisões correntes.

**Numeração histórica:** entradas até 26/10 chamavam a prova de reaplicação
de BL02, a expansão de BL03, a escolha de BL04 e o acervo de BL04.5.
A [trilha BL vigente](BL-brand-library.md#numeração-substituída) renumerou
esses marcos para seguir a dependência real. Changelogs antigos permanecem
registros do momento em que foram escritos.

As [versões anteriores à reconciliação](../history/2026-10-28-pre-documentation-reconciliation/)
preservam evidências históricas; a síntese vigente acima não transforma antigas
permissões por fornecedor ou exclusão de envios em trabalho a retomar.
