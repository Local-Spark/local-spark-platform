# WhatsApp — histórico de vínculo: proposta técnica para revisão

**Situação posterior:** esta proposta é apenas uma hipótese, não uma estrutura
aprovada nem um pré-requisito definido pelo produto. O proprietário determinou
que o processamento continua durante a troca e que a prévia e a aprovação vão
para o novo número ativo. Avaliar primeiro como cumprir isso com os dados já
existentes; não exigir que o cliente aguarde nem implementar esta tabela por
suposição. A entrega real da prévia por WhatsApp ainda não existe.

**Estado:** desenho; nenhuma tabela, migration, política, permissão ou código foi alterado. Mantém-se a decisão de **um número ativo por negócio**. O registro histórico é evidência de origem; não é outro número ativo nem uma autorização para mandar mensagens ao número antigo.

## Fatos do código atual

- `whatsapp_channel_links` tem chave primária `(tenant_id,business_id)` e índice único de `sender_hash` quando ativo. `WhatsAppLinkService.confirm()` sobrescreve `actor_id`, `sender_hash`, `proof_event_id` e `linked_at` ao confirmar outro vínculo. Não há timestamp do fim do vínculo anterior.
- `whatsapp_inbox` recebe o webhook sem tenant. `route_once()` associa uma mensagem de `quarantined` à linha do vínculo ativo de mesmo remetente se `received_at >= linked_at`, gravando tenant, negócio, remetente e instante em `whatsapp_material_events`.
- `WhatsappMaterialProcessor._eligible`, transcrição, `editorial_briefings`, `content_activities` e `content_deliveries` consultam o vínculo atual; a troca pode impedir processamento ou reuso de material antigo mesmo que os dados continuem gravados.
- `content_deliveries` obtém o destino do payload da mensagem original. Alterar somente os JOINs para consultar histórico poderia permitir envio ao número anterior; origem e destino exigem validações distintas.
- Alteram vínculo os caminhos `WhatsAppLinkService.confirm` e `disconnect`, `PhoneVerificationService.update_phone` e `WhatsAppMaterialsService.revoke_consent` (legado). Eles usam transações do banco, mas não foi demonstrado que compartilhem hoje uma ordem única de locks com recebimento e correlação.

## Opção recomendada para revisão: tabela de períodos, vínculo ativo permanece

Continuar usando `whatsapp_channel_links` como registro do vínculo corrente. Manter o índice de remetente ativo e a unicidade atual por negócio. Acrescentar, **somente após revisão**, uma tabela candidata `whatsapp_channel_link_periods` contendo:

| Campo | Propósito proposto |
| --- | --- |
| `id uuid` | Identidade estável de um período de vínculo. |
| `tenant_id`, `business_id` | Dono do vínculo; FK composta ao negócio. |
| `actor_id` | Ator que comprovou o vínculo na época, referência à conta existente. |
| `sender_hash char(64)` | Identificador do remetente; não guardar telefone em texto adicional. |
| `proof_event_id uuid` | Referência lógica à prova já usada pela confirmação; não presumir FK física a inbox, porque ela pode ser limpa. |
| `started_at timestamptz` | Início registrado do período. |
| `ended_at timestamptz NULL` | Fechamento do período; NULL indica período ainda aberto. |

Não incluir conteúdo de mensagens, novos provedores ou histórico de contatos de clientes finais. Verificar antes da migration se a FK correta é a de `business_profiles` ou `businesses` e como remoção de conta/negócio deve afetar os períodos; não definir exclusão em cascata sem decisão revisada.

**Invariantes propostos:**

1. Período não vazio: `ended_at IS NULL OR ended_at >= started_at`. Definir se igualdade é possível e qual convenção de precisão em testes.
2. Índice único parcial de período aberto por `(tenant_id,business_id)` e outro por `sender_hash` aberto, alinhados ao vínculo atual. A abertura e o fechamento devem ser atômicos com a alteração do vínculo atual; dois índices em tabelas diferentes, por si sós, não garantem consistência entre as tabelas.
3. Não associar automaticamente se mais de um período puder corresponder ao mesmo remetente e instante. Decidir uma restrição contra sobreposição de períodos encerrados **antes** de implantar: uma exclusion constraint pode exigir extensão `btree_gist`; outra abordagem exige serialização comprovada por remetente e revisão de todas as escritas. Nenhuma extensão é presumida aprovada.
4. Dados do período não devem ser reatribuídos para outro tenant/negócio após criação. A eventual atualização deve limitar-se ao encerramento e ser auditável; avaliar coluna de encerramento/registro próprio sem retirar as garantias existentes de auditoria.
5. Manter a chave de deduplicação de cada envio conforme o desenho de retenção durável. Um período não resolve sozinho reentrega duplicada nem arquivos que a Meta nunca entregou.

**Backfill:** copiar apenas o vínculo atualmente ativo e seus metadados conhecidos, dentro da migração e de modo auditável. Para vínculos já inativos ou sobrescritos não há hoje um `ended_at` confiável: não inferir períodos antigos ou associar mensagens ainda não correlacionadas com base em suposição. Os eventos já associados têm tenant/negócio gravados pelo correlator; se forem aceitos como prova de origem sem período histórico, isso deve passar por revisão de RLS, proveniência de escrita e autorização, não ser presumido neste documento.

## Transações e corridas a demonstrar

- Na confirmação bem-sucedida (`confirm`), criar/abrir o período ao mesmo tempo que a gravação do vínculo atual e a auditoria. Desfazer tudo no rollback, inclusive quando o remetente já estiver em outro negócio. Repetição da confirmação não cria período duplicado.
- Nos três caminhos que desativam vínculo (`disconnect`, alteração de telefone e revogação legada), encerrar o período na mesma transação em que o vínculo ativo é desativado e auditado. A substituição das autorizações legadas por um aceite único é um trabalho separado e não deve ser revertida por esta proposta.
- Correlacionar uma mensagem a um período apenas se sua origem e instante forem demonstravelmente compatíveis. A associação do inbox e a criação do evento devem ser atômicas e idempotentes. Manter seguro o caso de ambiguidade ou de mensagem ainda em quarentena.
- **Ordem temporal ainda não comprovada:** `received_at` e `linked_at` dependem de transações concorrentes. `now()` é o início da transação em PostgreSQL, não necessariamente a ordem de commit; uma comparação de timestamps sem coordenação pode associar incorretamente. Definir e testar serialização entre recebimento, troca e correlação por remetente e locks em ordem estável, sem segurar lock durante chamadas à Meta. Não basta acrescentar índices ou usar `clock_timestamp()` isoladamente.
- **Entrega tardia:** o instante em que nosso webhook recebe não necessariamente é o instante em que o cliente enviou a mensagem à Meta. Não é possível prometer associação correta apenas pelo timestamp local após a troca. Avaliar o timestamp assinado no payload, latência, limites e casos de reciclagem do número; se a origem não for demonstrável, preservar o evento para tratamento seguro em vez de atribuí-lo a outro negócio. O comportamento de recuperação ainda requer revisão; não inventar um novo fluxo ao cliente.

## Autorização e RLS — não aprovados ainda

As políticas existentes do app limitam `whatsapp_channel_links` ao tenant e a proprietário ativo; a role correlator já tem leitura desse vínculo para roteamento. Uma nova tabela não herda essas políticas nem grants. Antes de implementá-la:

- Definir leitura/escrita do app por tenant e proprietário ativo, com `WITH CHECK` e privilégios mínimos para abertura/encerramento, sem permitir reatribuição de identidade.
- Definir o acesso mínimo de correlação aos dados históricos de remetente para associação, considerando que a role correlator atua em múltiplos tenants. Não supor que RLS baseada apenas no contexto de usuário funcione na inbox pré-tenant, nem dar acesso amplo à role Meta como atalho.
- Revisar separadamente os pontos de leitura por workers, as permissões de tabelas envolvidas, e o comportamento atual de vínculo, plano e aceite. Não alterar `SECURITY DEFINER`, roles ou grants sem proposta e revisão. Aprovação anterior para testes com mocks não autoriza ampliação de permissões.
- Para usar material já atribuído como contexto, validar negócio, ator/membership atuais e contratação/condições aplicáveis, sem exigir que o número histórico continue ativo. Para responder via WhatsApp, validar o vínculo ativo e o destino no momento do envio; não reutilizar automaticamente o telefone extraído de um evento histórico. Essas são hipóteses de implementação que precisam de testes e revisão antes de substituir os gates existentes.

## Verificação e limites

Em PostgreSQL e storage isolados, sem Meta real: migração/backfill sem sobrescrever histórico desconhecido; duas trocas sequenciais; remetente reutilizado em outro negócio; mensagem recebida antes/depois de cada encerramento; correlação atrasada, simultânea à troca e replay; intervalo ambíguo; rollback; idempotência; leitura de material antigo no próprio tenant e negação em outro; assinatura/aceite e owner ativos; envio somente a destino permitido; comportamento de desconexão e correção de telefone; nenhum efeito pago. Verificar políticas RLS usando logins restritos, não apenas superusuário, e medir contenção dos locks.

A proposta não implica alteração ao prazo de prévias, contratação, política após encerramento de conta ou aquisição de clientes. Retenção durável dos envios e construção de memória utilizável pela IA continuam trabalhos distintos. A solução não está pronta para aplicar ou executar em produção.
