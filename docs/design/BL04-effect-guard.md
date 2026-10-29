# BL04.2 — guarda concreta antes da integração do provedor

Estado em **29/10/2026**: parte 1 implementada com imagens sintéticas, sem
habilitar chamadas pagas, modo real persistido ou novos grants. Produto em
[DECISIONS](../DECISIONS.md); sequência em
[BL04](../phases/BL04-context-and-ai-production.md).

## Fronteiras e identidade

`DatabaseVisualEffectGuard` implementa o contrato do orquestrador existente.
`GuardedVisualSubmissionClaims` renova a prova owner antes da claim correlator.
A operação financeira é `uuid5(..., visual-preview:<preview>)`; operação do
pedido, tenant, negócio, ator, proposta, candidata, fingerprint e fence também
precisam corresponder à prévia persistida. Header não concede acesso.

As sessões owner e correlator têm commits separados. A barreira entre elas é o
run durável: escritores coordenados aguardam sua conclusão e não mudam as fontes
de uma chamada admitida. Nenhuma sessão recebe credenciais da outra; não há locks
entre sessões ou durante provider/storage/renderização.

## Ordem de autorização

1. **Admitir:** conferir a prévia correlator; em owner, adquirir proposta → visual
   → comercial, validar fontes, aceite, membership e plano vigente e gravar
   run/auditoria. Replay não inicia outra execução.
2. **Reservar:** revalidar prova owner do run/fence e fontes; em correlator,
   adquirir prévia → ledger tenant → agregado OpenAI e gravar tentativa/reserva.
   Prazos são revalidados após esperas. Reserva existente ou confirmação perdida
   não autoriza nova submissão.
3. **Iniciar o efeito:** renovar prova owner com a data real original do run;
   em correlator, adquirir prévia → comercial → ledger tenant e conferir
   usuário/membership, lease, prazo factual e bloqueios financeiros. A regra de
   texto/fato/CTA é a mesma do preparo (`authorize_visual_copy`); a prova leva
   o menor prazo de proposta, fato/preço e transição de promoção. Esse limite é
   comparado ao relógio real após os locks, sem consultar fontes pela role errada.
   O CAS `submitted`
   → `uncertain`, com evento durável, é a única claim. Seu commit confirmado é
   o início durável; revogação posterior não desfaz uma chamada que já pode ter
   começado. Não há retry da mesma submissão.
4. **Disponibilizar a prévia privada:** após resposta/acabamento, renovar prova
   owner; em correlator, adquirir prévia → comercial e revalidar identidade,
   acesso, fence/prazos e tentativa reclamada. Só então gravar chave, hash,
   dimensões do formato e auditoria. O upload ocorre fora da transação.
5. **Concluir:** o orquestrador informa explicitamente se o efeito terminou.
   A prévia falhada se torna terminal sob lock correlator, ou há prova do
   resultado concluído. Após o commit, owner conclui o run e aplica mudanças.
   Sem resultado conhecido, tentativa/reserva existente, inclusive não vinculada,
   conserva run/hold. Sem tentativa, provar ausência sob prévia → ledger antes
   de abortar. Confirmação perdida não prova rollback.

Resposta tardia conhecida pode encerrar o run original após substituição do fence:
a prévia substituta é encerrada antes de liberar fontes. Resultado tardio não
vence fence novo nem autoriza outra cobrança. Commit de arquivo incerto conserva
objeto/run; não apagar objeto possivelmente referenciado. Custo desconhecido
continua reservado mesmo quando a criação já terminou: resposta/tokens não são
fatura e não liberam dinheiro por inferência.

## Escritores e fontes atuais

| Recurso | Coordenação/invariante verificado |
| --- | --- |
| Contexto, catálogo, confirmação de kit e fotos | Gate visual/comandos duráveis: aguardam admitidas, bloqueiam novas e invalidam fila anterior. |
| Edição/revisão de roteiro | Proposta → visual. Comando conserva documento/versão/revisão atuais; aplicação após commit de finish em nova transação nessa ordem. Dispatcher de outros comandos para antes de roteiro, sem adquirir proposta sob visual. |
| Cobrança/patrocínio | Writers de acesso financeiro usam advisory comercial; `BillingProcessor.save` participa antes de mudar status, prazo ou bloqueio. Revogação usa relógio real após o lock. |
| Usuário/membership | Revalidados na prova owner, claim e commit. Não há writer runtime nem grant de atualização de active/papel de cliente. Futuras mutações precisam respeitar o início durável. |
| Material WhatsApp processado | Original/atribuição preservados, inserção idempotente; fluxo atual não reescreve fonte processada/transcrição concluída. |
| Telefone/canal | Destino atual separado da origem atribuída. Troca/revalidação ou relink por outro owner não muda identidade da fonte (C05); leitura usa asset/event do negócio + owner ativo/aceite, entrega usa novo vínculo verificado. |
| Logo/briefing preparados | Logo ready imutável, seleção só pela confirmação do kit; upload pendente não é fonte. Snapshot de briefing preparado não é reescrito. |
| Nome, timezone e cor básica | Sem writer runtime além do cadastro atual; identidade visual da criação vem do kit confirmado. |

O roteiro é criado pela IA a partir do WhatsApp/contexto. Editor manual é
ferramenta interna DEV: aguarda alteração de outro recurso já pendente/falhada e
conserva formulário para retry, evitando comando inválido após a primeira mudança.
Não foi criado editor na jornada do cliente nem entregue ajuste automático por
WhatsApp (BL05). `pending_change` é extensão opcional dos contratos do laboratório;
a interface não apresenta sucesso antes da aplicação.

C08 permite concluir/revisar criação admitida após vencimento; bloqueio explícito,
revogação de patrocínio e perda de identidade são distintos. O scope
`admitted_visual_run` envolve o orquestrador e é restaurado ao sair. C07/C09
preservam arte anterior, versão/prova e revisão privada; aprovação/publicação
continuam exigindo suas verificações vigentes.

## Rollout e sequência delimitada

Retirar canal mutável do fingerprint altera o algoritmo. Drenar fila/criações
admitidas com fingerprints antigos antes de carregar o novo worker. Não misturar
código antigo/novo na mesma criação. Concluídas antigas continuam revisáveis pela
prova durável existente, sem reescrever hashes.

**Parte 2:** modo real distinto na persistência/API, dispatcher/worker/runner e
esta guarda/claims em testes ponta a ponta, preservando históricos Temporal.
Nesta parte 1 a guarda aceita somente simulação em desenvolvimento/teste; adapter
real não foi ligado à aplicação.

**Parte 3:** chamada real controlada pelo produto, com credenciais, fontes e teto
de gasto explícitos. BL04.3 mede qualidade/custo por peça aceita após a conexão.
C10, limpeza física de PUT incerto, varredura fora do redispatch e suporte seguem
em evoluções próprias. Exceções sem prova de resolução permanecem bloqueadas;
não ampliar permissões nem repetir possível efeito pago para contorná-las.
