# Plano de implementação

> HISTÓRICO v0.1: substituído pelo [plano atual da v0](v0-delivery.md).
> Usar Temporal em vez de Celery/RabbitMQ. Planejamento proativo, avatar e cenas
> geradas fazem parte da v0 completa, conforme a nova matriz de receitas.

Referência: [SDD](SDD.md) e [ADRs](architecture-decisions.md).
Os itens abaixo são backlog proposto. Não foram implementados ou executados.

## 1. Organização sugerida do novo backend

```text
content-platform/
  pyproject.toml
  uv.lock
  .env.example
  compose.yaml
  Dockerfile
  src/content_platform/
    api/                 # app FastAPI, dependencies, HTTP e webhooks
    modules/
      identity/
      tenancy/
      businesses/
      conversations/
      media/
      content/
      avatars/
      workflows/
      publishing/
      analytics/
      billing/
      notifications/
      support/
    adapters/            # WhatsApp, redes, IA, storage e pagamentos
    workers/             # tasks finas chamando serviços de aplicação
    scheduler/           # claims, vencimentos e reconciliação
    shared/              # DB, auth, eventos, telemetry e erros
  migrations/
  tests/
    unit/
    integration/
    contracts/
    failure_recovery/
    load/
  infra/
  docs/
```

Dentro dos módulos, separar domínio, serviços de aplicação e persistência quando
essa separação ajudar. Evitar dezenas de pastas vazias e abstrações sem consumidor.
Testes de integração usam PostgreSQL/broker reais, não SQLite como substituto de RLS
ou locks. Adapters fake têm comportamento de erro/timeout, não só caminho feliz.

## 2. Instalar e configurar

| Ambiente | Ferramentas/serviços |
| --- | --- |
| Máquina de desenvolvimento | Git, Docker/Compose, Python em versão suportada fixada, uv, FFmpeg/ffprobe se rodar renderer fora do container |
| Backend | FastAPI, Uvicorn, Pydantic Settings, SQLAlchemy, driver PostgreSQL, Alembic, Celery, Kombu, cliente Redis, HTTPX e cliente S3 |
| Qualidade | pytest, cobertura, Ruff, type checker, verificação de dependências e segredos |
| Desenvolvimento local | PostgreSQL, RabbitMQ, Redis, object storage S3 local e stub de provedores |
| Observabilidade | OpenTelemetry, collector e destino de logs/métricas/traces conforme cloud |
| CI | Lint, tipos, testes de integração, contratos, migrações e build/scan das imagens |
| Produção | Containers gerenciados, banco/broker/cache gerenciados, buckets, secret manager, TLS, DNS e IaC |

Fixar versões compatíveis no bootstrap e gerar lockfile; não usar `latest` nas imagens.
Não instalar Kubernetes, Kafka, banco vetorial, modelos locais ou GPUs por precaução.
Selecionar ferramentas adicionais apenas quando houver requisito/benchmark.

Compose futuro deve incluir `api`, `dispatcher`, `scheduler`, workers por fila,
`postgres`, `rabbitmq`, `redis` e storage local. Mock deve ser modo padrão; integrações
pagas só são ligadas por configuração explícita. Um healthcheck não implica API pronta
para gerar mídia. Não incluir credenciais reais nos arquivos versionados.

## 3. Spikes técnicos antes de fechar os planos

### SPIKE-01 — WhatsApp oficial

Provar recebimento de foto, vídeo, áudio e texto; validação da assinatura; download;
duplicação de webhook; envio de prévia; ações de aprovação e templates necessários.
Não depender de bibliotecas de sessão WhatsApp Web para o núcleo do produto.

**Aceite:** uma solicitação completa roda em conta de teste e reinício não perde evento.
Registrar permissões, limites e custos vigentes. Não estimar custo de mensageria
somente pela quantidade de conversas; modelar mensagens/categorias efetivamente usadas.

### SPIKE-02 — Avatar e voz do dono

Usar adultos voluntários com autorização explícita; testar segmentos diferentes,
preços, nomes, sotaques e uma receita híbrida com imagens reais do negócio.
Medir semelhança, naturalidade, erros de fala, latência p50/p95, falhas, revisões,
custo por segundo e exigências de captura/consentimento do fornecedor.

**Aceite:** evidência comparativa de pelo menos dois caminhos viáveis (fornecedores
ou técnicas), escolha justificada e custo por entrega contabilizado. Segunda opção
pode ser tecnicamente inferior e não vira failover automático sem consentimento.
Não assumir que assinatura pessoal do site inclui API para revenda ou multi-tenancy.

### SPIKE-03 — Publicação e métricas Instagram

Escolher caminho OAuth; publicar imagem e Reel em conta profissional de teste;
consultar processamento, erro, token expirado e insights disponíveis. Validar Stories
se elegível e documentar exigências de app review para contas externas à equipe.

**Aceite:** link de publicação real, consentimento/conta identificados e relatório
com dados reais disponíveis. Distinguir teste com papel no app de acesso de produção.

### SPIKE-04 — Viabilidade econômica e render

Montar corpus autorizado de materiais representativos. Medir render de arte/vídeo,
storage, tráfego, APIs e custo de revisão. Modelar uso mediano e usuários intensivos.

**Aceite:** proposta de franquias e orçamento por formato baseada em medições,
sem promessa de vídeo/avatar ilimitado a R$ 99.

## 4. Entregas ordenadas

### E0 — Fundação executável

- Bootstrap, configuração tipada, containers e ambiente local reproduzível.
- Modelo de tenant/business/member, autenticação e contexto transacional de tenant.
- Migração inicial, CI e logs correlacionados sem dados sensíveis.
- Inbox/outbox, dispatcher, runner de steps, leases e scheduler com adapters fake.
- Object storage privado e health/readiness.

**Aceite:** ambiente sobe do zero; evento persistido é retomado após queda de
worker/broker; teste de isolamento passa em API, DB e worker. RLS usa role sem bypass.

### E1 — Primeiro fluxo completo com materiais reais

- WhatsApp recebe e agrupa material; orienta envio e confirma fatos.
- Receita de arte e Reel simples, transcrição, identidade visual e legendas.
- Prévia, aprovação/correção por versão, agendamento e cancelamento.
- Instagram publica, reconcilia estado e devolve link confirmado.
- Painel operacional mínimo para erro, replay seguro e suporte.

**Aceite:** cliente consegue chegar do áudio/foto à publicação sem operar editor;
versão revisada não usa aprovação antiga; timeout ambíguo não dispara reenvio cego.
Medir o tempo e os pontos em que suporte foi necessário.

### E2 — Identidade do cliente e controle financeiro

- Cadastro de avatar/voz, evidência de consentimento e revogação.
- Receita híbrida e vídeo com avatar aprovados pelo cliente.
- Ledger/reservas/franquias; assinatura, cancelamento e concessão de seis meses.
- Bloqueios por limite de uso/custo e reconciliação de operações externas.

**Aceite:** gasto rastreável até cada versão; concorrência não ultrapassa saldo;
revogação impede trabalhos pendentes; término promocional não cria cobrança sozinho.
O spike de avatar começa antes, mesmo que sua entrega integrada esteja nesta etapa.

### E3 — Rotina que sustenta uso recorrente

- Preferências de frequência, sugestões contextuais e biblioteca de materiais.
- Reaproveitamento com validade, autorização e prevenção de repetição excessiva.
- Coleta incremental de insights e relatório semanal no WhatsApp.
- Relatório identifica dados indisponíveis e fontes de contatos/vendas confirmadas.
- Fluxos de reconexão de conta e atendimento assistido.

**Aceite:** uma semana de operação exige esforço pequeno e observado do cliente;
nenhuma promoção vencida é reaproveitada; métricas exibidas são reproduzíveis.

### E4 — Redes e formatos adicionais

- Capabilities por rede/conta/formato, variantes de mídia e erros independentes.
- Facebook, TikTok e YouTube Shorts entram um por vez, após spikes próprios.
- TikTok inclui tela/UX exigidas, consentimento e auditoria; formato indisponível
  não aparece como publicação automática funcional.
- Carrosséis, mais templates e cenas geradas conforme custo/qualidade aprovados.

**Aceite:** falha parcial não repete sucesso de outra rede; preview e aprovação
correspondem à variante e conta enviadas. App reviews necessários concluídos.

### E5 — Homologação para crescimento

Preparar infraestrutura e observabilidade começa em E0; este marco comprova capacidade.

- Carga por etapa e cenário de pico; limites justos por tenant e provedor.
- Falha de nó/broker/banco, perda de callback, Redis indisponível e restore.
- Autoscaling, pool de conexões, configuração de fila e orçamento de storage/egress.
- Runbooks de fila acumulada, publicação UNKNOWN, token expirado e gasto inesperado.
- Relatório do limite medido com concorrência, hardware, mídia, fornecedor e custo.

**Aceite:** SLOs atingidos na carga declarada, gargalo identificado e plano do próximo
patamar. Não declarar suporte a 200 mil clientes baseado só em mock ou contagem de pods.

## 5. Primeiras issues implementáveis

| Ordem | Issue | Dependências | Resultado verificável |
| --- | --- | --- | --- |
| 1 | Bootstrap FastAPI e Compose | Nenhuma | API e dependências locais com readiness |
| 2 | Tenant, membership e business com RLS | 1 | Testes de acesso cruzado e pool passam |
| 3 | Inbox/outbox e dispatcher | 2 | Commit sem broker recupera depois |
| 4 | Workflow step e lease/fencing | 3 | Worker antigo não confirma etapa retomada |
| 5 | Webhook WhatsApp e ingestão | 3, SPIKE-01 | Assinatura, deduplicação e mídia privada |
| 6 | Briefing versionado e perguntas | 4, 5 | Fatos rastreáveis e ambiguidades pendentes |
| 7 | Renderer e preview | 6, SPIKE-04 | Arquivo reproduzível com preço correto |
| 8 | Aprovação e agendamento | 7 | Hash/versão/destino e cancelamento concorrente |
| 9 | Publisher Instagram e reconciliação | 8, SPIKE-03 | Post confirmado e timeout recuperável |
| 10 | Reserva de custo e provider job | 4 | Não duplica gasto em retry/timeout |
| 11 | Avatar autorizado e receita híbrida | 7, 10, SPIKE-02 | Vídeo do dono e revogação funcional |
| 12 | Assinatura, concessão e métricas | 9, 10 | Ciclo de uso completo e relatório real |

Planejar por critérios de aceite, sem prometer prazo em semanas antes de conhecer
app reviews, qualidade do avatar e disponibilidade dos responsáveis.

## 6. Portas de saída para piloto pago

1. Cadastro, conexão de rede e consentimento funcionam com pessoas fora da equipe.
2. Publicação, correção e pausa funcionam sem intervenção de engenheiro no caminho normal.
3. Recuperação de evento e proteção de saldo demonstradas em testes de falha.
4. Termos, cobrança, cancelamento e expiração promocional estão claros no produto.
5. Relatórios não inventam atribuição de vendas e mostram limitações de coleta.
6. Suporte consegue explicar e resolver falhas usando ferramentas auditadas.
7. Custo por cliente e por formato cabe na franquia proposta com margem definida.

Não provisionar serviços pagos, publicar conteúdo em contas reais ou gerar identidade
de terceiros apenas para cumprir a documentação: essas ações entram na implantação
e nos pilotos autorizados, com segredos no ambiente e limites de gasto configurados.
