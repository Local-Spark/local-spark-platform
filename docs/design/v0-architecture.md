# Arquitetura do produto — runtime e evolução

Reconciliado em **28/10/2026**. Subordinado ao [SDD vigente](../SDD.md) e ao
[registro de decisões](../DECISIONS.md). O desenho v0.2 anterior está preservado
como contexto histórico; suas capacidades futuras não são funcionalidades entregues.

## Runtime atual

| Fronteira | Estado |
| --- | --- |
| API/domínio | FastAPI/Python modular em `app/core`, `app/api/v1`, `app/schemas` e `app/services`; regras de negócio nos serviços. |
| Banco | PostgreSQL, tabelas compartilhadas, RLS e logins runtime restritos; tenant deriva de identidade/membership, sem autoridade apenas pelo header. |
| Identidade | Auth própria, sessões/refresh, recuperação, convites/MFA de staff; sem Keycloak/Cognito/OIDC para clientes. |
| Execução | Temporal com SDK Python; API, dispatchers e workers separados. Nenhum IO dentro de workflow determinístico. |
| Arquivos | Storage privado compatível com S3, hashes/versões e URLs temporárias autorizadas. Arquivos do kit demo ainda são públicos no build web. |
| Mídia | Pillow/FFmpeg para prévias técnicas; acabamento do kit no modo `visual_fake`. Não são receitas comerciais homologadas. |
| IA | Texto/transcrição com adapters e gates; Jev/retrieval opcional no worker local dev/test. IA visual real isolada e desconectada. |
| Web | React/TypeScript em `local-spark-web`, configuração, plano, acervo, kit e revisão; token de acesso em memória/refresh HttpOnly. |
| Operação | Compose e CI/workflow de deploy preparados; AWS/staging/recuperação ainda não homologados. Redis sem dependência ativa. |

Temporal substitui Celery, RabbitMQ e o runner próprio dos rascunhos v0.1.
PostgreSQL conserva domínio, auditoria e ledger; Temporal conserva execução,
sem ser arquivo permanente de auditoria. Redis/CDN/infraestrutura por células
são evoluções dependentes de necessidade e medição, sem requisito de runtime local.

## Produto e fronteiras de autorização

Cada organização de cliente tem um negócio (0057), cobrança por tenant e um
aceite contratual explícito para interpretação, texto, imagem e transcrição.
A web não oferece permissões por fornecedor. Direitos sobre materiais, owner
ativo, orçamento e aprovação da peça continuam separados do contrato.

Materiais associados ao WhatsApp são duráveis (0058) e não são excluíveis pelo
histórico. O acervo é outro recurso e permite remover fotos desatualizadas.
Um número WhatsApp ativo atende cada negócio; troca não interrompe material já
atribuído, e entrega simulada segue para o número novo verificado.

O percurso desejado é pedido/contexto → briefing → prévia → revisão/ajuste →
aprovação específica → publicação → resultados observáveis. Existem fatias
locais de cada domínio, sem jornada real completa. Ajuste ainda não regenera
automaticamente; proatividade e pesquisa ampla permanecem futuras. O primeiro
plano contempla foto/story sem quantidade comercial fechada; vídeo/avatar não
entram automaticamente. Avatar/voz ficam após o primeiro piloto.

## Consistência e próxima entrega

Toda operação assíncrona tem identidade durável. Estado transacional inclui
auditoria e intenção/outbox com consumidor real; não emitir recibo assíncrono
sem efeito. Nenhuma chamada de rede/storage segura row lock. Snapshot fixa
fontes/versões; replay e fence impedem duplicação lógica e commit antigo,
sem prometer exactly-once com fornecedor externo.

A BL04.2 precisa fechar coordenação owner/correlator de fontes, acesso, contrato,
fence e orçamento antes de conectar o gerador real. A alternativa autorizada
para desenvolver com mocks usa travas/ledger existentes, sem novos grants.
Resultado incerto conserva prova e reserva, sem novo envio automático.

Mudanças de kit/fotos/contexto aguardam trabalhos admitidos, cancelam fila
não iniciada e bloqueiam novos inícios. Cobertura existe parcialmente no fake;
a [coordenação completa](BL04-atomicity-proposal.md) permanece pendente.
Prévias anteriores às mudanças ficam revisáveis com indicação, sem herdar
aprovação. Plano vencendo após início permite terminar/revisar; novas criações
e publicação aguardam renovação. A preservação de prévias enquanto conta ativa
e esses acessos ainda precisam de implementação coordenada.

Só staff poderá resolver pendência cujo autor perdeu acesso, com ação registrada
e auditada; outro owner não assume. O fluxo de recuperação staff ainda não existe,
e a regra não concede acesso geral a conteúdo privado. O encerramento da conta
fica para sua fase própria, sem exclusão automática introduzida nesta revisão.

## Piloto e escala

BL04.3 mede fidelidade, legibilidade, aceite do titular e custo por peça aceita,
incluindo refações. BL05 fecha jornada simulada, ajustes e proatividade mínima.
Homologação Meta oficial, franquias F07, staging/recuperação F08 e suporte são
condições do piloto. Escala até 200 mil clientes é objetivo: exige carga,
limites de fornecedores, orçamento, recuperação e coortes medidas.

Contratos complementares: [consistência](v0-consistency-observability.md),
[resiliência](v0-reliability.md), [tenancy](v0-tenancy.md),
[integrações](v0-integrations.md) e [entrega](v0-delivery.md).

Versão anterior integral: [snapshot de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/v0-architecture.md).
