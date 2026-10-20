# Decisões de arquitetura

> HISTÓRICO v0.1: ADR-003 e ADR-004 substituídas pela decisão Temporal do
> [SDD atual v0.2](v0-architecture.md). Não implementar dois orquestradores.
> As decisões e responsabilidades atuais estão nos documentos `v0-*`.

Status: propostas para o bootstrap; validar versões e provedores antes da produção.
Contexto completo: [SDD](SDD.md).

## ADR-001 — Monólito modular, processos separados

**Decisão:** um backend Python modular, empacotado para API, dispatcher, scheduler e
workers independentes. Escalar execução por grupo de trabalho.

**Motivo:** domínio ainda em descoberta e equipe inicial pequena. Separar deployments
permite aumentar renderização sem aumentar servidores HTTP, sem impor comunicação
distribuída entre todos os módulos de negócio.

**Alternativa:** microserviços desde o início. Aumentam contratos, deploys, observabilidade
e consistência distribuída antes de existir evidência da divisão correta de domínio.

**Revisão:** extrair módulo quando equipes, perfil de carga ou ciclo de releases
exigirem independência e houver contrato estável. Não extrair só por número de clientes.

## ADR-002 — FastAPI e PostgreSQL

**Decisão:** FastAPI/Pydantic, SQLAlchemy/Alembic e PostgreSQL. Processamento longo
assíncrono por filas; HTTP retorna identidade da operação.

**Motivo:** integrações e domínio transacional combinam com Python e banco relacional.
PostgreSQL concentra integridade, idempotência, franquias, aprovações e estado durável.
Utilizar async em endpoints não transforma CPU/render em trabalho não bloqueante.

**Alternativas:** Django pode ser adequado se admin e CRUD dominarem o projeto;
MongoDB não é necessário para guardar JSON de modelos, que pode usar JSONB com schema
de aplicação. Não trocar integridade relacional por flexibilidade indiscriminada.

**Custo:** RLS, índices, pools e limites precisam ser testados. Assíncrono no acesso
ao banco é escolha por processo; workers podem usar sessões síncronas bem delimitadas.

## ADR-003 — Celery com RabbitMQ; Redis temporário

**Decisão:** Celery executa tarefas; RabbitMQ é broker; Redis serve cache e rate limits.
PostgreSQL guarda resultados de domínio e andamento. Celery result backend não é
obrigatório quando não há uso de canvas/chords; evitar dependência desse backend.

**Motivo:** separar memória descartável do transporte de trabalho, usar confirmações
e filas replicadas, manter tarefas pesadas em pools distintos.

**Alternativas:** Celery + Redis é viável e pode escalar, mas exige entender visibility
timeout, redelivery e persistência. A escolha de RabbitMQ é sobre operação/semântica,
não uma afirmação de que Redis não escala. SQS é alternativa gerenciada se a cloud
for AWS; exige ajustar limites e comportamento do transporte escolhido.

**Custo:** mais um serviço para operar. Em desenvolvimento RabbitMQ single-node é
suficiente; em produção HA real exige cluster e teste de falha, não só reinício automático.

**Validação:** confirmar publisher confirms, roteamento, quorum queues e configurações
de prefetch/acks nas versões fixadas. Usar IDs de eventos e etapas para deduplicar.
Documentação: [Celery tasks](https://docs.celeryq.dev/en/stable/userguide/tasks.html),
[Redis transport](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html),
[RabbitMQ confirms](https://www.rabbitmq.com/docs/confirms).

## ADR-004 — Workflow persistido no banco

**Decisão:** estado explícito de runs/steps, scheduler com leases, inbox/outbox e
reconciliador. Celery transporta execução; não é a memória do processo de negócio.

**Motivo:** aprovação humana, callback e agendamento podem levar dias. Tasks não
devem ficar bloqueadas esperando pessoa ou fornecedor.

**Alternativa:** Temporal é candidato para workflows duráveis mais complexos. Pode
substituir a orquestração quando se provar vantajoso; não operar dois orquestradores
com autoridade sobre a mesma execução. A implementação atual deve encapsular o runner.

**Custo:** leases, fencing, retry e reconciliação exigem implementação e testes sérios.
Uma chain Celery sozinha não cobre interrupções humanas nem recuperação financeira.

## ADR-005 — S3 e composição determinística

**Decisão:** arquivos em object storage; metadados no banco. FFmpeg/ffprobe em sandbox,
templates e manifesto de cenas versionado. Tipografia/preços renderizados de forma
determinística. URLs de download são temporárias e adequadas ao TTL de cada integração.

**Motivo:** arquivos não precisam atravessar broker ou API web; renders são reproduzíveis
a partir de versão, manifesto e assets. Bibliotecas de composição podem ser adicionadas
se templates precisarem de motion design mais sofisticado.

**Alternativas:** Remotion exige runtime Node/Chromium e é opção para layouts animados;
MoviePy pode ajudar em protótipos, com benchmark de uso de memória. Não decidir apenas
pela familiaridade sem medir render representativo.

**Custo:** lifecycle, egress, download por provedor e scratch disk afetam bastante o COGS.

## ADR-006 — APIs de IA substituíveis, identidade rastreável

**Decisão:** usar APIs externas inicialmente, com adapters, orçamento e proveniência.
Avatar e voz são entidades vinculadas ao consentimento e fornecedor.

**Motivo:** não há necessidade inicial de treinar modelo ou manter GPU para comprovar
o produto. A qualidade percebida e custo por entrega importam mais que variedade de SDKs.

**Alternativa:** modelos próprios exigem equipe, infraestrutura, licença compatível e
benchmark. Avaliar depois com volume, qualidade e margem medidos.

**Custo:** limites externos restringem escala; planejar contratos, concorrência e
capacidade. Failover de avatar não é transparente, pois identidade pode não ser portável.

## ADR-007 — WhatsApp principal, web complementar

**Decisão:** cliente conversa no número da plataforma. Web mínima existe para OAuth,
identidade/consentimento, configurações e revisão específica de plataformas.

**Motivo:** simplicidade no cotidiano, sem prometer que toda etapa regulada por APIs
pode acontecer exclusivamente por áudio. A conta do Instagram continua pertencendo
ao cliente; nunca solicitar senha de rede social para integrar.

**Custo:** link e autenticação precisam ser fáceis, seguros e testados com público pouco
familiarizado com tecnologia. O produto deve guiar e oferecer suporte na conexão inicial.

## ADR-008 — Aprovação por versão e por destino

**Decisão:** aprovar snapshot imutável com mídia, legenda, conta e janela de envio.
Publicação tem estado separado por destino. Revisões invalidam autorização anterior
para os novos materiais.

**Motivo:** evitar publicação de preço/arquivo diferente do aprovado e respeitar
controles específicos de cada rede. Tratar cancelamento concorrente explicitamente.

**Alternativa:** autorização genérica para o calendário inteiro pode ser uma funcionalidade
posterior em redes que permitirem, com limites e experiência próprios.

## ADR-009 — Escala por medições, custos por operação

**Decisão:** infraestrutura como código, deployments independentes, limites de admissão,
observabilidade, ledger e testes de falha desde o primeiro fluxo. Tamanho inicial
modesto, serviços com HA em produção e crescimento orientado por carga medida.

**Motivo:** comprar capacidade para 200 mil clientes no primeiro dia não comprova
escalabilidade. Controlar gasto e recuperar efeitos externos evita crescimento de prejuízo.

**Custo:** produção confiável tem custo fixo relevante. Definir orçamento antes do deploy;
desenvolvimento local single-node não deve ser confundido com topologia de produção.
