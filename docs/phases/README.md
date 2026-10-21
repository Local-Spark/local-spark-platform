# Fases de implementação

Cada fase é integrada em features menores, com testes e SDD atualizados.
A v0 completa reúne F00–F08; concluir F00 não conclui o produto.

| Fase | Escopo | Status |
| --- | --- | --- |
| [F00](F00-foundation.md) | Fundação executável | Concluída localmente |
| [F01](F01-identity-onboarding.md) | Identidade, onboarding, admin mínimo e base React | Em implementação |
| [F02](F02-whatsapp-ingestion.md) | WhatsApp e biblioteca de materiais | Planejada |
| [F03](F03-editorial-research.md) | Pesquisa, temas e planejamento proativo | Planejada |
| [F04](F04-media-recipes.md) | Artes, carrosséis e edição de vídeo | Planejada |
| [F05](F05-avatar-generative-video.md) | Avatar, voz e cenas geradas | Planejada |
| [F06](F06-instagram-publishing.md) | Aprovação, agenda e Instagram | Planejada |
| [F07](F07-billing-reports.md) | Franquias, assinatura e relatórios | Contratação mínima na F01.5; restante pendente |
| [F08](F08-production-scale.md) | Operação, segurança e escala | Planejada |

F01 é integrada com a base web e o admin mínimo; telas essenciais do cliente entram
junto. Área completa acompanha F02–F07. Contratação/ativação mínima antecipa F07
na fatia F01.5; métricas reais entram quando existirem suas fontes.

Decisão transversal de F02–F07: [contexto versionado do negócio, adapters por
capacidade e ledger anterior ao primeiro gasto pago](../design/business-context-and-generation.md).
