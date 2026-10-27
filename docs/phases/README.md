# Fases de implementação

Atualizado em 27/10/2026. Este índice distingue **o que existe no ambiente
local**, **a próxima fase** e os gates para piloto/produção. A v0 completa
continua distribuída entre F00–F08; a trilha [BL](BL-brand-library.md) define
a ordem de produto para aplicar um kit visual e o acervo do negócio a uma
peça nova.

## Estado atual

- F00/F01: fundação, identidade, onboarding, cobrança sandbox, área do cliente
  e admin mínimo locais. Homologação externa e staging continuam pendentes.
- F02: webhook, vínculo do remetente, recibos de texto/foto/áudio/vídeo,
  biblioteca e respostas limitadas locais. A conta Meta restrita impede
  homologação de envio/recebimento reais.
- F03: fatos/preferências, ideia e roteiro versionado com edição local.
  Pesquisa ampla, qualidade comercial e sugestão proativa ainda pendem.
- F04/F06: prévias estáticas/vídeo locais e candidata/aprovação/publicação
  **simuladas**. F03 já congela o kit confirmado em novas propostas; F04 ainda
  não o aplica à mídia, nem usa acervo estruturado ou IA visual integrada.
- BL01: um kit fictício de cafeteria e simuladores públicos/cliente locais.
  Ver a vitrine não é escolher ou editar o kit.
- BL02: seleção e edição guiada do kit na área autenticada, logo privado,
  prévias ampliáveis, rascunho/confirmado e histórico por negócio locais.

## Próximas entregas em ordem

| Ordem | Fase | Entrega demonstrável | Estado |
| --- | --- | --- | --- |
| 1 | [BL01](BL-brand-library.md#bl01--kit-piloto-e-vitrine-local) | Kit piloto de cafeteria, dez posts, stories, reel e vitrine. | Técnica local pronta; revisão comercial/direitos pendente. |
| 2 | [BL02](BL-brand-library.md#bl02--escolher-e-editar-o-kit-piloto-para-um-negócio) | Dono seleciona o kit e ajusta cores, fontes, logo, textos e composição guiada de feed/story/capa vertical; vê e confirma prévias versionadas. | Implementada localmente; gate comercial do kit segue pendente. |
| 3 | [BL03](BL-brand-library.md#bl03--acervo-progressivo-em-sobre-meu-negócio) | Dentro de “Sobre meu negócio”, cadastrar opcionalmente produtos/serviços e fotos reais do espaço; dado privado, confirmado e versionado. | **Próxima fase de implementação.** |
| 4 | [BL04](BL-brand-library.md#bl04--recuperar-contexto-e-produzir-uma-peça-nova) | Áudio/texto livre resolve o item e fontes automaticamente; IA visual/receita gera nova peça com kit aplicado; medir fidelidade, aceite e custo completo. | Planejada; ensaio sintético isolado não encerra o gate. |
| 5 | [BL05](BL-brand-library.md#bl05--jornada-completa-local-ajuste-e-proatividade-mínima) | WhatsApp simulado e proposta sem mensagem percorrem prévia, ajuste, aprovação e publicação falsa com as mesmas regras. | Contratos F02/F04/F06 parciais já existem; integração pendente. |
| 6 | [BL06](BL-brand-library.md#bl06--ampliar-a-biblioteca-e-servir-o-catálogo-em-escala) | Kits de manicure e personal, catálogo público versionado em objetos/CDN e revisões por nicho. | Planejada após prova de reaplicação. |

BL02 e BL03 podem avançar com a Meta restrita. BL04 testa localmente com
mocks e, para fechar qualidade comercial, precisa de avaliação de titular
com material consentido. BL05 exercita integração e falhas locais; uso real
depende da homologação F02/F06. A expansão BL06 não precisa atrasar o primeiro
piloto de cafeteria, mas não deve anteceder uma peça personalizada aprovada.

## Fases transversais até produção

| Fase | Escopo | Estado/gate |
| --- | --- | --- |
| [F00](F00-foundation.md) | Fundação, Postgres/RLS, Temporal e observabilidade base | Concluída localmente. |
| [F01](F01-identity-onboarding.md) | Identidade, onboarding, admin e cobrança mínima | Código local; staging/homologação externa pendentes. |
| [F02](F02-whatsapp-ingestion.md) | WhatsApp, materiais e confirmação | Local/mock; Meta real pendente. |
| [F03](F03-editorial-research.md) | Contexto, pauta, roteiro, cadência proativa e pesquisa | Parte local; BL02–BL05 integram contexto/kit e proatividade mínima. Pesquisa ampla fica depois. |
| [F04](F04-media-recipes.md) | Receita visual, IA de imagem/vídeo, prévia e ajuste | Renderer local é baseline técnico; BL04 fecha primeira receita aprovada. |
| [F05](F05-avatar-generative-video.md) | Avatar, voz e cenas geradas | Opcional/posterior, com consentimento e orçamento próprios. |
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
- [SDD geral](../SDD.md) e [contexto vivo](../PROJECT.md):
  contratos e decisões correntes.

**Numeração histórica:** entradas até 26/10 chamavam a prova de reaplicação
de BL02, a expansão de BL03, a escolha de BL04 e o acervo de BL04.5.
A [trilha BL vigente](BL-brand-library.md#numeração-substituída) renumerou
esses marcos para seguir a dependência real. Changelogs antigos permanecem
registros do momento em que foram escritos.
