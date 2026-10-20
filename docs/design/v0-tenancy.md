# v0 — Estratégia de multi-tenancy

Data: 20/10/2026. Decisão proposta: banco e tabelas compartilhados, com isolamento
por `tenant_id`, autorização de aplicação e RLS. Evolução possível por células/shards
ou banco dedicado, sem criar um schema por cliente como padrão.

## 1. O que representa um tenant

Tenant é a organização/conta contratante. Negócio é uma unidade pertencente a ela.
Usuário pode participar de mais de uma organização, com membership e papel próprios.
Uma agência pode administrar clientes distintos por memberships, sem misturar todos
num tenant apenas para simplificar o acesso. A concessão de acesso gratuito usa a
mesma estrutura, com entitlement e prazo, não um caminho menos seguro.

```text
Tenant / organização
  ├── Assinatura, franquias e membros
  ├── Negócio A
  │     ├── Conversas e materiais
  │     ├── Avatar e consentimentos
  │     └── Contas sociais, conteúdo e publicações
  └── Negócio B, se permitido pelo plano
```

## 2. Alternativas consideradas

| Opção | Vantagem | Impacto para este produto |
| --- | --- | --- |
| Tabelas compartilhadas e tenant_id | Uma estrutura de migração, pool e operação | Exige isolamento explícito em todos os caminhos |
| Schema por tenant | Namespace separado e possível customização | Multiplica objetos e trabalho de migração; não isola CPU/IO nem backup físico |
| Banco por tenant | Fronteira de acesso/administração própria | Multiplica bancos, pools, migrações e custo operacional |
| Instância dedicada | Isolamento de recursos mais forte | Reservar para contrato/necessidade específicos |

Exemplo aritmético, não limite PostgreSQL: 200 mil tenants e 40 tabelas por schema
produziriam oito milhões de tabelas, antes de índices e outros objetos. Para
microempresas usando essencialmente o mesmo produto, essa multiplicação não traz
benefício proporcional. Schema não é unidade independente de recursos físicos.

Começar com estrutura compartilhada não significa comprometer-se com uma única
instância para sempre. Capacidade é medida por dados, operações e perfil de uso,
não apenas quantidade de cadastros. Células podem hospedar grupos de tenants com
mesmo modelo de dados, reduzindo blast radius e distribuindo carga.

## 3. Isolamento obrigatório

1. Tabelas privadas possuem `tenant_id NOT NULL`; recursos de unidade também têm business_id.
2. FKs compostas incluem tenant para impedir relacionamento cruzado.
3. Constraints/índices de negócio respeitam escopo do tenant; consultar com filtros explícitos.
4. RLS habilitada com leitura e escrita protegidas. Role runtime não é superuser,
   dona das tabelas ou BYPASSRLS; avaliar FORCE RLS também para defesa adicional.
5. Tenant deriva de identidade/membership validados, não do JSON, header ou mensagem.
6. Contexto transacional via SET LOCAL ou set_config local; nunca usar configuração
   de sessão persistente num pool. Ausência de contexto deve falhar de modo fechado.
7. Cada activity abre transação e reestabelece contexto validado. Argumento tenant_id
   de evento não dispensa conferir vínculo do recurso e origem do comando.
8. SQL parametrizado, roles sem DDL e privilégio mínimo. RLS é defesa adicional,
   não proteção completa contra comprometimento do processo ou SQL injection.

Tabelas de identidade global e pesquisa compartilhável têm política própria e
permissões restritas; não recebem exceção genérica para facilitar código. Jobs globais
enumeram IDs por interface restrita e executam trabalho dentro do tenant correto.
Suporte tem acesso temporário/autorizado/auditado; não role de superuser no console.

O PostgreSQL permite políticas por linha, mas roles privilegiadas e normalmente
donos podem ignorá-las; TRUNCATE também não é coberto por RLS. Por isso roles e
privilégios fazem parte da garantia. Fonte: [RLS oficial](https://www.postgresql.org/docs/current/ddl-rowsecurity.html).

## 4. Tenant em toda a jornada

- S3: prefixo não é autorização. Downloads/uploads verificam membership, recurso e
  tenant antes de gerar URL temporária; workers usam permissões mínimas.
- Redis: chave privada contém tenant e versão do recurso. Cache compartilhado apenas
  para dados autorizados para reuso e sem informação privada.
- Temporal: workflow/command/operação identificam tenant, mas namespace não é criado
  por cliente como padrão. UI de operação não é exposta diretamente aos assinantes.
- APIs externas: tokens/IDs de conta são vinculados ao tenant e nunca selecionados
  só por parâmetro livre do cliente.
- Observabilidade: tenant é correlação em logs com acesso controlado; não label
  ilimitado de métricas nem justificativa para expor conteúdo entre clientes.
- Cotas: limites por tenant e por provedor evitam que um usuário intenso monopolize
  slots de render, orçamento ou publicação. RLS não resolve noisy neighbor.

## 5. Evolução de capacidade

Preparar abstração de localização do tenant; não desenvolver sharding completo antes
de medir necessidade. Quando ativado, diretório `tenant → cell/database` é mantido no
control plane, com roteamento server-side, cache versionado e migração coordenada.

Mover tenant exige plano de pausa/coordenação de escritores, cópia consistente,
tratamento de inbox/outbox/ledger, mudança atômica de rota, invalidação de cache e
reconciliação de workflows em andamento. Não usar dois bancos como escritores sem
protocolo. Banco dedicado é extensão dessa fronteira, não schema improvisado.

Backups/PITR do banco compartilhado restauram o conjunto. Recuperação de um tenant
exige restore isolado e extração controlada, incluindo relacionamentos, arquivos e
reconciliação de efeitos externos. Exclusão/exportação por tenant devem existir
desde a v0; isolamento lógico não torna essas operações automáticas.

## 6. Aceite

Testar acesso cruzado em API, jobs, OAuth, cache, URLs S3, pesquisa privada e suporte;
reuso de conexão entre dois tenants; inserção com tenant divergente; FK cruzada;
contexto ausente; roles e migração que criem tabela privada sem RLS. Executar com
role real da aplicação, não com a credencial administrativa usada para preparar teste.

Fonte de organização de namespaces: [schemas PostgreSQL](https://www.postgresql.org/docs/current/ddl-schemas.html).
