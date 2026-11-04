# Arquitetura atual da jornada WhatsApp → conteúdo

Registro de análise em 30/10/2026, solicitado para discussão posterior. Ele
descreve o código local e separa o comportamento implementado dos próximos
gates. Recomendações abaixo não são autorização para refatorar, separar
repositórios ou alterar contratos da jornada.

## Repositórios e processos

- **Backend `local-spark-platform`:** API FastAPI, regras de negócio,
  persistência, adapters, definições de workflows e workers. Código organizado
  em `app/api/v1`, `app/schemas`, `app/services`, `app/adapters` e
  `app/workflows`; a regra de negócio pertence aos serviços.
- **Frontend `local-spark-web`:** telas de acesso, configuração, acervo, kits,
  acompanhamento e revisão. A API continua responsável pela autorização e
  aplicação das regras.
- **Skills `meu-braco-direito-skills`:** desenvolvimento de instruções e
  avaliações. O backend carrega cópias versionadas em `app/assets/visual_skills`,
  verificadas por hash; não consulta o repositório de skills a cada geração.

Um repositório backend não significa um único processo: API, correlator,
dispatchers e workers são executáveis separados. O [worker](../../app/entrypoints/worker.py)
registra workflows e activities no Temporal. O servidor Temporal é serviço
separado, responsável pelo histórico e execução dos workflows; PostgreSQL
mantém estados de domínio, operações e auditoria. Objetos de mídia usam
armazenamento S3 compatível. Detalhes de deploy dependem da configuração.

## Caminho atual da mensagem

```mermaid
flowchart LR
    M["Mensagem WhatsApp"] --> W["Webhook e registro"]
    W --> R["Correlação e despacho"]
    R --> WM["WhatsAppMaterialWorkflow"]
    WM --> CW["ContentCandidateWorkflow"]
    CW --> EP["Briefing e proposta"]
    EP --> VP["Prévia visual"]
    VP --> DEL["Entrega simulada"]
    DEL --> REV["Decisão por API"]
    REV --> PUB["Publicação simulada"]
```

1. O [webhook](../../app/api/v1/whatsapp.py) verifica a assinatura, extrai
   eventos e persiste antes da resposta. O correlator associa material a um
   negócio, e o dispatcher inicia o trabalho com identidade estável.
2. O [WhatsAppMaterialWorkflow](../../app/workflows/whatsapp_material.py)
   processa o material, tenta transcrever quando aplicável e inicia o workflow
   filho de candidata. Falhas posteriores não apagam o material já processado.
3. O [ContentCandidateWorkflow](../../app/workflows/content_candidate.py)
   solicita briefing e proposta, aguarda o resultado, solicita prévia, aguarda
   novamente e aciona a entrega. Dúvidas, bloqueios, prazos e estados de falha
   são tratados conforme o caminho disponível. O Jev participa quando habilitado
   e autorizado; seu papel atual é limitado à interpretação/seleção existente.
4. Proposta editorial e geração visual têm workflows e dispatchers próprios;
   sua coordenação com a candidata usa estados persistidos e temporizadores.
   A geração visual real depende de configuração, autorizações e orçamento;
   está desligada por padrão e restrita ao estágio de desenvolvimento/teste.
5. [ContentDeliveryService](../../app/services/content_deliveries.py) registra
   uma entrega **simulada** e uma decisão explícita. O contrato de aprovação
   da peça integral exige revisão visual vinculada ao hash da prévia. A web e
   a resposta do WhatsApp ainda não fornecem essa confirmação para a nova
   receita, e ajuste solicitado não regenera automaticamente.
6. A aprovação válida registra a decisão e pode acionar o dispatcher de
   publicação. O [workflow de publicação](../../app/workflows/content_publication.py)
   é separado e atualmente **simulado**; não publica no Instagram real.

A entrega real da candidata pelo WhatsApp, a conversa completa, a publicação
oficial, referências externas aceitas e o checklist de revisão nos canais de
cliente seguem pendentes ou não homologados. Testes diretos de qualidade de
imagem não comprovam que a jornada inteira foi executada.

## Orquestração e saga

Temporal fornece workflows duráveis, histórico, timers e políticas de tentativas;
as activities executam operações e IO. Estados, autorizações e resultados de
domínio ficam no PostgreSQL. Existem identidades estáveis, deduplicação,
auditoria, controles de concorrência e guardas de efeitos externos em partes do
percurso. A geração visual paga não repete cegamente uma tentativa cujo
resultado externo seja incerto. Nenhuma dessas proteções implica que todas as
etapas tenham exatamente a mesma estratégia de retry ou outbox.

O percurso **não é uma única saga clássica de ponta a ponta** aguardando a
aprovação e revertendo automaticamente todos os efeitos: há vários workflows e
despachos independentes. A preservação do material após falha é uma decisão de
continuidade, não rollback geral. Algumas operações externas não podem ser
desfeitas com rollback de banco e precisam de estado de incerteza e reconciliação.

Ponto de observabilidade: no workflow de material, a falha do workflow filho de
candidata pode ficar no histórico enquanto o pai retorna `processed`. Esse
resultado indica material processado; **não prova que a peça foi gerada ou
entregue**. É necessário avaliar uma visão de jornada correlacionada e seus
estados de espera/falha, sem expor conteúdo ou segredos em logs.

## Discussão futura: modularidade e divisão

Recomendação inicial para debate: manter o monólito modular e os repositórios
atuais enquanto a jornada e seus contratos são consolidados. Repositório,
processo, serviço, fila e banco são decisões diferentes; processos podem ser
operados separadamente sem criar outro repositório, e vários serviços podem
compartilhar um monorepo.

Antes de discutir divisão física, avaliar:

1. Fronteiras claras entre entrada/WhatsApp, interpretação, criação, revisão e
   publicação, preservando regras nos serviços e o Temporal como motor.
2. Estado e correlação de jornada suficientes para identificar a etapa atual,
   esperas, falhas, ação do cliente e resultado final; trace de provedores tem
   finalidade e controle de acesso próprios.
3. Garantias para efeitos pagos e publicação, recuperação de resultado incerto,
   teste de cenários de falha e observabilidade sem dados privados em logs.
4. Encerramento dos gates da jornada real — entrega, aprovação, ajustes e
   publicação — sem equiparar uma prévia a uma peça publicada.

Separar uma capacidade em serviço ou repositório pode vir a ser útil diante de
necessidade comprovada de escala, deploy, segurança ou equipes independentes.
Isso também acrescenta contratos de comunicação, versionamento, operação e
pontos de falha; nenhuma extração ou migração foi decidida nesta análise.
