# v0 — Idempotência, concorrência, atomicidade e observabilidade

Data: 20/10/2026. Contrato obrigatório de implementação, complementar à
[resiliência](v0-reliability.md). Não representa código ou testes já executados.

## 1. Garantias e fronteiras

- Eventos e activities podem chegar/executar mais de uma vez e fora de ordem.
- Repetição da mesma operação lógica deve preservar o resultado e não duplicar
  débito, reserva, aprovação, agendamento ou transição no domínio.
- Banco garante integridade por constraints e transações; locks são locais ao recurso.
- Não existe transação ACID única entre PostgreSQL, Temporal, S3 e APIs externas.
- Temporal permite retomada; não transforma API externa em efeito exactly-once.
- Lock local ou distribuído não substitui a chave idempotente da operação externa.
- Logs de diagnóstico não substituem estado persistente, ledger ou auditoria.

Garantias são expressas em invariantes testáveis, não em “usar lock em tudo”.

## 2. Identidades e deduplicação por camada

| Camada | Chave e escopo | Repetição |
| --- | --- | --- |
| Envelope de webhook | Provider, conta receptora, event ID estável quando disponível | Não processar envelope validado novamente |
| Evento normalizado | Provider, conta e chave semântica do subevento | Preservar eventos distintos de um mesmo envelope |
| Mensagem recebida | Canal/conta receptora e message ID | Uma mensagem de domínio |
| Comando HTTP | Tenant, ator/escopo autorizado, método/rota, Idempotency-Key | Mesmo resultado lógico e operation_id |
| Evento interno | Event ID persistido na outbox | Mesmo consumidor não repete efeito |
| Comando ao workflow | Workflow ID e command_id | Deduplicação da mensagem e no domínio |
| Operação externa | Tenant, operation_key, fingerprint e conta provedora | Reusar resultado/consultar status |
| Render | Versão, manifesto, hashes de assets, perfil e engine | Reaproveitar arquivo íntegro |
| Publicação | Versão aprovada e conta de destino | Uma intenção de publicação |
| Reserva/consumo/compensação | Operação, tipo de lançamento e unidade | Um lançamento lógico por finalidade |

Não usar só message ID para deduplicar recibos: `sent`, `delivered`, `read` e erros
podem se referir à mesma mensagem. A chave do subevento inclui seu tipo/identidade
e campos semânticos do contrato. Webhooks sem event ID exigem regra por adapter,
com fingerprint canônico dos campos estáveis; hash do JSON bruto não é solução geral.

Checksums de arquivo ajudam a reutilizar mídia, mas duas solicitações deliberadas
com a mesma foto não são necessariamente o mesmo pedido. Nova revisão, nova postagem
intencional ou comando alterado recebe identidade própria e aprovação correspondente.

`Idempotency-Key` tem request hash canônico versionado. Mesma chave com payload
diferente gera 409; não sobrescreve resultado. Retries não devem gerar chave nova.
Reautenticar/autorizar antes de devolver resposta idempotente já salva para evitar
vazamento após revogação de acesso. DTO retornado respeita dados/estado atuais da sessão.

Retenção é por tipo: janela HTTP cobre retries contratados; tombstones de operações
pagas/publicações duram além do horizonte de redelivery e conciliação. Purga/partição
não pode reabilitar evento antigo. No banco particionado, projetar registro de dedupe
separado ou chave compatível com as constraints de particionamento; não presumir
unique global entre partições temporais.

## 3. Transação atômica de domínio

Cada comando executa uma transação curta com:

1. Autorização e contexto do tenant na transação.
2. Inserção/claim idempotente, usando constraint única como árbitro.
3. Validação e alteração de estado com versão/precondições.
4. Reserva ou lançamento financeiro, quando necessário.
5. Auditoria obrigatória e evento de outbox.
6. Resultado idempotente da operação e commit.

Não usar “SELECT para ver se existe → INSERT” sem proteção de unicidade, pois dois
processos podem observar ausência simultaneamente. Usar `INSERT ... ON CONFLICT`
com tratamento do resultado. Em READ COMMITTED uma inserção concorrente pode
exigir nova leitura após o conflito; distinguir resultado concluído e em andamento.
Se comando já foi recebido mas não terminou, devolver operation_id pendente, não
sucesso fictício nem executar de novo.

Erros de domínio não deixam uma inbox marcada como concluída sem seus efeitos. Se
parte do trabalho é assíncrona, inbox registra recebimento e a transação de processamento
registra conclusão com as mudanças correspondentes. Lease não equivale a conclusão.

Não manter transação/row lock aberto durante transcrição, render, espera humana,
chamada HTTP ou sleep. Persistir a intenção, commit, executar IO e gravar resultado
em outra transação idempotente. Falha entre efeito externo e gravação continua
possível e usa o estado `UNKNOWN` definido na política de resiliência.

## 4. Estratégia de concorrência por recurso

| Recurso | Controle principal | Razão |
| --- | --- | --- |
| Webhook duplicado | UNIQUE + transação | Serializa apenas a mesma identidade lógica |
| Revisão/aprovação/cancelamento | UPDATE condicional com row_version | Detecta alteração concorrente sem lock longo |
| Última unidade da franquia | UPDATE condicional ou row lock curto na conta de quota | Impede saldo insuficiente em disputa |
| Criação de publicação | UNIQUE da intenção + estado aprovado | Dois consumidores não criam duas intenções |
| Relay/outbox e manutenção | SKIP LOCKED + lease e fencing | Distribui trabalho elegível entre réplicas |
| Conversa/material agrupado | Versão/claim por conversa ou solicitação | Não formar dois briefings para os mesmos itens |
| Concorrência de API terceira | Semáforo/lease distribuído em Redis | Limita capacidade, não decide estado de negócio |
| Compensação | Chave própria única + versão do recurso | Repetição não estorna/libera duas vezes |

Nenhum lock global para 200 mil clientes. Contenção é limitada ao agregado relevante.
Múltiplas contas de orçamento são bloqueadas em ordem estável. Limites globais de
provedor usam coordenação e quotas por coorte, evitando atualizar uma linha global
do banco em toda chamada sem avaliar o gargalo e a reserva agregada.

### Exemplo de compare-and-swap

SQL ilustrativo de transição, não migration pronta:

```sql
UPDATE publications
SET state = 'PREPARING', row_version = row_version + 1
WHERE tenant_id = :tenant_id
  AND id = :publication_id
  AND state = 'SCHEDULED'
  AND row_version = :expected_version
RETURNING id, row_version;
```

Zero linhas significa conflito, estado alterado, recurso inacessível ou comando já
aplicado; distinguir esses casos em leitura autorizada. Não ignorar o resultado nem
assumir que zero linhas é permissão para disparar a chamada externa.

O claim de publicação e o cancelamento competem pelas mesmas precondições. A etapa
de envio revalida aprovação/consentimento e persiste intenção. Após início do HTTP
há corrida inevitável com cancelamento: resultado é reconciliado e informado.

### Reserva financeira concorrente

Transação cria reserva única e reduz `available_units` condicionalmente a saldo
suficiente. Se não houver saldo, rollback da criação da reserva. Se reserva já
existir, retornar seu resultado, sem reduzir novamente. Consumo e liberação usam
lançamentos únicos por operação e transições válidas da reserva.

Não validar saldo só com valor lido anteriormente. Modelar invariantes de múltiplas
linhas com locks explícitos na conta pai ou SERIALIZABLE quando necessário, com teste
de write skew. `CHECK` de uma linha sozinho não protege soma de lançamentos em várias linhas.

## 5. Leases, fencing e workers atrasados

Claim persistido contém `owner_id`, `lease_expires_at` e `fencing_token` monotônico.
Aquisição e incremento são atômicos; renovação exige mesma posse, token e lease válido.
Nova posse incrementa token. Commit de resultado exige token atual e precondições.
Usar relógio do banco para decisões de lease no banco, evitando relógios locais divergentes.

Exemplo: worker A recebe token 41 e pausa. Lease expira; B recebe 42. A retorna:
gravação com 41 é recusada. Heartbeat e TTL reduzem risco, mas não impedem sozinhos
que A envie HTTP atrasado. API externa precisa de idempotência, referência correlacionável
ou tratamento explícito de ambiguidade. Fencing local não cancela efeito remoto.

Redis lock, se usado, tem token de posse, TTL, renovação e liberação compare-and-delete;
não liberar lock alheio só porque a chave existe. `asyncio.Lock` protege apenas um
processo e nunca é mecanismo de exclusão entre containers. Advisory lock, se realmente
necessário, prefere escopo transacional e chave bem definida; cuidado com locks de
sessão em pool de conexões. O caminho inicial prioriza constraints e row/CAS locks.

## 6. Isolamento, deadlocks e ordenação

READ COMMITTED como padrão, com constraints, updates condicionais e locks curtos.
SERIALIZABLE apenas em invariantes que precisarem dessa garantia; testar custo e
retry. Para SQLSTATE `40001` ou `40P01`, reiniciar a transação inteira com backoff
e tentativas limitadas; nunca repetir cegamente apenas a última instrução.

Definir `lock_timeout`, `statement_timeout` e timeout da aplicação por operação,
além de controlar conexões. Detectar deadlocks, espera de lock e transações longas.
Retentativa da transação não pode repetir IO pago, pois IO não pertence à transação.

Timestamp não é ordenação total de eventos. UUID também não prova ordem causal.
Usar versão do agregado e sequence do provedor quando seu contrato garantir isso.
Callback tardio não regride estado por um simples ranking de enums; validar a tabela
de transições e o mesmo ID de operação/versão. Resultado externo pode exigir correção
auditada de projeção, não apagar evidência anterior. Pai e workflows filhos têm
ownership explícito de cada transição, sem vários escritores irrestritos.

Fontes: [locks PostgreSQL](https://www.postgresql.org/docs/current/explicit-locking.html),
[isolamento de transações](https://www.postgresql.org/docs/current/transaction-iso.html).

## 7. Logs estruturados e correlação

JSON para stdout e coleta centralizada; envelope estável alinhado a OpenTelemetry.
Convenção proposta de atributos da aplicação, não nomes obrigatórios do padrão:

```json
{
  "timestamp": "2026-10-20T15:00:00.000Z",
  "severity": "WARN",
  "service": "local-spark-io-worker",
  "environment": "staging",
  "release": "git-sha",
  "event": "external_operation.outcome_unknown",
  "trace_id": "otel-trace-id",
  "span_id": "otel-span-id",
  "correlation_id": "request-chain-id",
  "causation_id": "origin-command-id",
  "tenant_id": "tenant-uuid",
  "business_id": "business-uuid",
  "event_id": "event-uuid",
  "operation_id": "operation-uuid",
  "workflow_id": "workflow-logical-id",
  "run_id": "temporal-run-id",
  "activity_id": "activity-id",
  "attempt": 1,
  "provider": "heygen",
  "duration_ms": 60000,
  "error_code": "EXTERNAL_OUTCOME_UNKNOWN",
  "resolution": "reconcile_before_resubmit"
}
```

Campos opcionais variam por etapa. Log não carrega chave de idempotência secreta,
telefone/email, transcrição, prompt bruto, imagem, token, URL assinada ou resposta
integral do fornecedor. Redaction por allowlist no boundary e teste de vazamento.
ID de correlação recebido do cliente é validado e não serve como autorização.

Propagar trace context em HTTP/outbox/activities de forma controlada. Espera longa
ou workflow durando dias usa spans de execução e links de causalidade; não manter
um span HTTP aberto durante toda a jornada. Em replay, usar logger compatível com
Temporal para não duplicar logs de workflow; tentativas reais de activity têm logs
distintos com attempt/run_id.

`INFO`: transições confirmadas e entrega; `WARN`: recuperação/limite/conflito esperado
com agregação apropriada; `ERROR`: falha não resolvida ou intervenção necessária.
Não logar cada evento duplicado em ERROR. Diferenciar “intenção registrada” de
“efeito confirmado”; um log anterior ao commit não prova sucesso.

Logs têm retenção, RBAC, redaction e orçamento. Sampling de debug/traces não remove
ledger/auditoria obrigatórios; eventos de segurança e mudanças críticas têm política
própria. Não colocar tenant_id/workflow_id como labels ilimitados de métricas.
Auditoria registra ator, motivo, comando e versão na transação de domínio, com acesso
restrito e exportação protegida. Não depende exclusivamente de entrega de stdout.

Fonte: [OpenTelemetry Logs Data Model](https://opentelemetry.io/docs/specs/otel/logs/data-model/).

## 8. Critérios de aceite de concorrência

| Cenário | Invariante exigida |
| --- | --- |
| Cem entregas paralelas do mesmo evento | Uma mensagem/efeito lógico e outbox correspondente |
| Dois eventos diferentes da mesma mensagem | Recibos/estados distintos não são perdidos por dedupe incorreto |
| Duas requisições com mesma chave e payload diferente | Uma operação e conflito explícito, sem sobrescrita |
| Vários workers disputam última unidade | Saldo não negativo; apenas reservas cobertas |
| Revisão concorre com aprovação | Nenhuma versão diferente herda aprovação |
| Cancelamento concorre com claim de envio | Resultado consistente e efeitos iniciados reconciliados |
| Lease expirado e worker antigo retorna | Commit antigo recusado pelo fencing |
| Crash entre commit e sinal ao Temporal | Outbox entrega comando depois, sem perder nem duplicar efeito |
| Crash após efeito externo e antes de gravar ID | UNKNOWN/reconciliação, sem retry pago cego |
| Callback duplicado, tardio ou fora de ordem | Transição válida, sem regressão arbitrária ou novo débito |
| Deadlock/serialization failure forçado | Retry da transação inteira com limite e sem IO duplicado |
| Perda de Redis e retomada | Estado/ledger preservados; admissão externa reconstruída com segurança |
| Purga de partição e evento antigo redelivered | Tombstone/janela contratada impede novo efeito indevido |
| Reuso de conexão entre tenants | Contexto RLS não vaza; recurso de outro tenant não é acessível |
| Logs de erro contêm token/URL de mídia de fixture | Redaction impede segredo no destino de logs |

Executar contra PostgreSQL real e processos concorrentes, com barreiras determinísticas
para forçar interleavings. Incluir testes de propriedade da máquina de estados e
contabilidade quando agregarem valor. Replay de workflow e teste unitário isolado
não substituem integração transacional, crash tests ou validação do adapter externo.
