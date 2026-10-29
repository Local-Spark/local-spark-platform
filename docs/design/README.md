# Desenhos e decisões do Meu Braço Direito

Índice reconciliado em **29/10/2026**. A leitura para continuar o desenvolvimento
começa pelo [PROJECT](../PROJECT.md), [SDD vigente](../SDD.md),
[decisões aceitas e pendentes](../DECISIONS.md) e
[SDD da fase ativa BL04](../phases/BL04-context-and-ai-production.md).
Esses documentos prevalecem sobre propostas e desenhos versionados desta pasta.
O [índice de fases](../phases/README.md) distingue entrega local, etapa futura e
homologação externa. Um desenho ou ensaio não comprova capacidade entregue.

## Contratos atuais e próxima fatia

| Tema | Documento | Estado e finalidade |
| --- | --- | --- |
| Aceite de IA | [IA como parte do serviço](ai-as-core-service.md) | Aceite único implementado em Plano e acesso; tabelas antigas preservadas como histórico. |
| Conta e cobrança | [Uma organização por negócio](one-business-per-organization.md), [cobrança](billing.md) | Unicidade 0057 e cobrança por tenant; sandbox local não homologa produção. |
| WhatsApp | [Materiais duráveis](BL04-whatsapp-durable-materials.md) | 0058 aplicada localmente; todos os tipos associados preservados, sem exclusão pelo histórico; troca de número coberta no processamento e entrega simulada. |
| Coordenação BL04.2 | [Atomicidade](BL04-atomicity-proposal.md), [integração segura](BL04-integration-safety.md) | Próximo trabalho: fechar coordenação de fontes/acesso/contrato/orçamento com mocks antes de ligar IA visual real. |
| Execução visual | [Temporal](BL04-visual-temporal-execution.md), [quarentena](BL04-quarantine-rollout.md) | Workflow isolado testado, ainda desconectado; limpeza física/reconciliação pendentes. |
| Identidade visual | [Biblioteca](brand-library.md) | Kit demonstrativo e editor locais; acabamento ligado ao modo simulado; direitos/qualidade comerciais pendentes. |
| Contexto | [Contexto e geração](business-context-and-generation.md) | Fatos/preferências e acervo versionados; retrieval e Jev opcionais no worker local, sem memória geral. |
| Qualidade | [Gate criativo](creative-production-quality.md) | BL04.3 precisa medir fidelidade e custo por peça aceita, incluindo refações. |
| Sequência | [Roadmap](delivery-roadmap-2026-10-27.md), [cadência](editorial-planning-and-evidence.md) | BL04 → BL05 → homologação, franquias e operação; sem promessa de quantidade antes de medir. |
| Identidade/autorização | [Auth própria](native-auth.md), [tenancy](v0-tenancy.md) | API/RLS, membership e papéis restritos. |
| Consistência | [Transações e logs](v0-consistency-observability.md), [resiliência](v0-reliability.md) | Invariantes de implementação; exemplos futuros identificados separadamente. |

Prévias geradas devem ser preservadas sem expiração automática enquanto a conta
estiver ativa. Se o plano vencer durante uma criação já iniciada, ela termina e
sua prévia privada continua revisável; novas criações e publicação aguardam
renovação. O recorte simulado já aplica C08 à criação `visual_fake` admitida e
C09 às concluídas/proveniência; a coordenação completa ainda falta. A migration
0058 preserva a origem WhatsApp e não é a implementação dessas regras de prévias.
Somente staff poderá recuperar pendência cujo autor perdeu acesso, com ação
restrita e auditada; o proprietário adiou sua implementação em 29/10 para evolução
de gestão de acesso/suporte. A exceção permanece bloqueada e não impede fechar a
fatia simulada validada. A política após
encerramento fica para a fase própria, sem exclusão automática nesta etapa. Ver
[registro de decisões](../DECISIONS.md).

## Arquitetura e evolução

Runtime atual: FastAPI, PostgreSQL com RLS, Temporal e armazenamento privado
compatível com S3; web React/TypeScript em repositório separado. Redis é candidato
futuro, sem dependência ativa. Temporal é o único coordenador dos workflows;
Celery, RabbitMQ e o runner próprio dos rascunhos anteriores foram superados.

- [Arquitetura e limites atuais](v0-architecture.md).
- [Integrações: estado local, homologação e candidatos](v0-integrations.md).
- [Entrega, infraestrutura e gates](v0-delivery.md).
- [Inteligência local e pesquisa futura](v0-intelligence.md).
- [Vídeo real e voz](video-real-and-voice.md) e
  [pesquisa datada de ferramentas](video-tool-candidates-2026-10-27.md): vídeo não
  integra automaticamente a oferta inicial; avatar/voz ficam depois do piloto.

## Propostas superadas e evidências

Os caminhos abaixo mantêm referência ao desenho original preservado, sem
transformá-lo em backlog obrigatório:

- [SDD v0.1](SDD.md), [ADRs v0.1](architecture-decisions.md) e
  [plano v0.1](implementation-plan.md): histórico, sem autoridade sobre runtime.
- [Leitura adicional de usage](BL04-editorial-usage-access-proposal.md): grant
  rejeitado, sem implementação; não reintroduzir toggles individuais.
- [Holds de retenção](BL04-tenant-retention-claim-protocol.md) e
  [exclusão de foto WhatsApp](BL04-whatsapp-deletion-review-proposal.md): premissas
  superadas por materiais duráveis; não aplicar a exceção antiga de sete dias.
- [Histórico de vínculo](BL04-whatsapp-link-history-review.md): hipótese para
  análise de mensagens ainda não atribuídas, não requisito para os materiais já associados.
- [Cobrança multinegócio](review-billing-and-agreement-per-business.md): substituída
  por uma organização por negócio.
- [Revisão local 0050–0057](local-migrations-0050-0057-review.md): evidência datada,
  anterior à 0058 e ao aceite único entregue.

Os [snapshots anteriores à reconciliação](../history/2026-10-28-pre-documentation-reconciliation/index.md)
conservam integralmente as análises e rejeições. Evals datados continuam como
resultados de uma execução, sem autorização contínua de gasto ou publicação.

Versão anterior integral: [snapshot de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/README.md).
