# BL04.2 — coordenação transacional antes da geração visual real

Atualizado em **29/10/2026**. Estado: **admissão simulada implementada no recorte
descrito abaixo; guarda real não implementada**. O [SDD BL04](../phases/BL04-context-and-ai-production.md)
define a fase; o [registro de decisões](../DECISIONS.md) define produto e dúvidas.

## Problema ainda vigente

O preparo e a revalidação de contexto, kit, acervo e contrato usam a sessão owner.
A admissão simulada agora revalida essas fontes e o plano sob locks antes de
gravar o run durável. A reserva financeira, intenção e fence usam a sessão
correlator. A reserva e o fence são atômicos entre si; os dois commits continuam
separados e não demonstram uma guarda integral de submissão paga. O run bloqueia
as mudanças já coordenadas; escritores ainda não cobertos podem deixar janelas
concorrentes. Fence protege o commit de um worker vencido; sozinho não impede gasto.

`VisualEffectGuard` é somente um protocolo do orquestrador isolado. Ainda falta
uma implementação que demonstre admissão e recuperação completas antes do envio.
O workflow visual separado também não está ligado ao dispatcher/worker. Configurar
chave, modo ou budget não fecha essas lacunas e não libera chamada real.

## Regras atuais de produto

- Um negócio por tenant, assegurado pela 0057; cobrança e acesso continuam no tenant.
- Um aceite contratual versionado cobre texto, imagem, interpretação e transcrição.
  Não criar retirada por fornecedor; registros e APIs antigos são compatibilidade.
- Mudanças de kit, foto do acervo ou contexto aguardam criações já admitidas;
  cancelam fila não iniciada e bloqueiam novos inícios até serem aplicadas.
  Prévias concluídas permanecem revisáveis com indicação de criação anterior à mudança;
  direitos e aprovação específica continuam sendo exigidos para publicar.
- Materiais WhatsApp associados não expiram e sua exclusão pelo histórico é recusada,
  em todos os tipos (0058). Troca de número não interrompe o processamento;
  entrega simulada usa o número ativo novo.
- Se o plano vencer durante a criação já iniciada, terminar e permitir revisão
  privada da prévia; bloquear novas criações e publicação até renovar. As prévias
  devem permanecer sem expiração automática enquanto a conta estiver ativa.
  O recorte atual aplica a continuidade à criação `visual_fake` admitida com
  prova durável; o renderer local legado não recebe a mesma exceção de conclusão.
  Concluídas e proveniência já são conservadas sem purge por prazo. Aprovação,
  validade factual e URL assinada mantêm prazos independentes.

Se o autor perder acesso, somente staff poderá resolver a pendência, com ação
restrita, registrada e auditada; outro proprietário não assume sua autoria. Esse
fluxo ainda precisa de implementação. Outro owner já é impedido de substituir ou
descartar o comando do autor. O proprietário adiou a implementação de suporte em
29/10, para evolução de gestão de acesso/suporte. Não bloqueia o fechamento do
recorte simulado; até sua entrega, a exceção permanece bloqueada. A proposta
de novas permissões fica como referência futura, sem aprovação. Retenção após encerramento fica para a fase
própria, sem exclusão automática nesta etapa. Não interpretar vencimento do plano
como encerramento da conta ou como autorização de acesso para owner revogado.

## Recorte implementado com provedor simulado

`VisualAdmissionChecks` integra `VisualConsentGate.admit` no renderer fake:

1. A transação owner bloqueia a proposta antes do advisory visual existente e,
   depois, o advisory comercial. Não adquire a proposta após o visual.
2. Valida usuário ativo, membership/negócio, plano atual, aceite aplicável e o
   fingerprint capturado de proposta, fontes, kit e briefing. Só então grava o
   run e a auditoria. A revogação de patrocínio usa o mesmo lock comercial.
3. Após o commit owner, o preparo de bytes/storage ocorre sem locks. A reserva
   correlator continua vinculando fence, tentativa e ledger em sua transação,
   com orçamento por tenant e agregado aplicável já existentes. Não foram
   criadas tabelas, roles ou concessões de leitura adicionais nesta fatia.
4. Um run existente não autoriza nova execução. Falha entre commits, lease vencida
   ou resultado incerto conservam a evidência e bloqueiam repetição; não se presume
   rollback conjunto nem conclusão do efeito externo. Tentativas visuais iniciadas
   sem resultado resolvido não são apagadas pelo purge.

A exceção financeira consulta o run/fence efetivo durante execução e o resultado
concluído na revisão. Vencimento não é bloqueio financeiro explícito, revogação
de patrocínio ou perda de usuário/membership. Novas criações/publicação continuam
exigindo plano. Prévias concluídas, propostas/roteiros e snapshots referenciados
são preservados, sem prolongar aprovação ou tornar fato vencido atual.

Há testes adicionados de captura real e fontes/transição comercial concorrentes
em PostgreSQL restrito, além de continuidade e retenção. `make ci` passou com
1.642 testes e 100% de linhas e branches; resultado no CHANGELOG. Esse recorte não fecha todos os
escritores, a recuperação staff ou a guarda concreta do orquestrador real.

## Escopo restante antes do provedor real

A opção autorizada para desenvolver/testar usa travas e ledger existentes,
sem criar tabelas ou ampliar grants. A prova completa ainda precisa demonstrar:

1. Identidade/tenant/negócio e owner ativo; contrato atual, estado da proposta e
   roteiro; versões de fatos, kit, catálogo, foto/logo e direitos efetivamente usados.
2. Admissão durável serializada com todos os escritores pertinentes, incluindo
   inserções/ausência de linha, mudança pendente e transições comerciais.
3. Reserva nova, orçamento por tenant e agregado aplicável, intenção durável e
   fence; nenhum replay de reserva autoriza uma nova chamada.
4. Commit confirmado antes de rede/storage/renderização. Crash entre sessões ou
   confirmação perdida conserva evidência e bloqueia reenvio até conciliação.
5. Finalização por operação/fence/hash, custo conhecido ou incerto, preservação da
   prévia e aplicação segura das mudanças pendentes. Nenhum timeout prova que um
   fornecedor terminou; lease vencida não autoriza gastar outra vez.

Preparar bytes, ler/escrever storage e chamar fornecedor sempre fora de locks e
transações. Verificação posterior não desfaz uma chamada já cobrada; o controle
precisa impedir admissão inválida antes dela.

## Cobertura parcial e escritores ainda a inventariar

O modo simulado já coordena alterações/restauração de contexto, catálogo,
confirmação de kit e inclusão/alteração/exclusão de fotos do acervo, com plano e
aceite revalidados na admissão. Não declarar cobertura de todos os escritores:
revisar logo, conclusão de upload, reconciliação, edição/revisão de roteiro,
demais transições comerciais, membership/usuário e processos
administrativos. Associar material e completar transcrição também podem alterar
fontes. Limpeza técnica de órfãos e quarentena continua tendo efeitos externos.

O autor pode descartar upload incerto após a reserva vencer, mantendo o objeto
privado em quarentena. Limpeza física automática e recuperação restrita por staff
ainda não estão implementadas; outro owner não é o caminho aprovado. Ver [rollout de quarentena](BL04-quarantine-rollout.md).
A preservação 0058 retira a antiga expiração/exclusão voluntária de materiais
associados da jornada; não é necessário implementar os holds antigos para isso.

## Ordem de locks e recuperação

O recorte de admissão usa proposta → visual → comercial, compatível com a ordem
do worker editorial. A reserva correlator segue preview → ledger por tenant →
linha do agregado quando aplicável. Essas transações não mantêm locks durante
storage/renderização. A prova dos pares testados não fecha a hierarquia global.

Diagnósticos sintéticos anteriores reproduziram espera circular nas ordens
comercial → visual versus visual → comercial, e proposta → visual versus visual
→ proposta. Uma ordem uniforme serializou esses pares isolados, **sem provar a
hierarquia global**. O worker editorial, briefing, transcrição, preview e ledger
possuem outras ordens que precisam ser inventariadas antes da integração real.

O caso de um tenant/negócio simplifica seleção e escopo, mas não elimina locks
financeiros, de origem/proposta ou as fronteiras RLS entre roles. Lotes precisam
ser limitados, ordenar chaves e medir contenção; estender timeout não corrige
inversões ou resultado externo incerto. Não passar credenciais de app ao
correlator nem trocar `actor_id` para aplicar pendência de outro usuário.

As propostas anteriores de novas roles, `SECURITY DEFINER` ou grants não foram
aprovadas; a proposta de leitura de usage foi rejeitada. São evidência histórica,
sem obrigação de implementação e sem autorização para contorná-las. Se a solução
com permissões existentes não fechar a fronteira, apresentar um desenho concreto
novo para revisão; este documento não o presume necessário.

## Evidência exigida antes de conectar o provedor

Em PostgreSQL `_test`, armazenamento falso e Temporal local, demonstrar RLS entre
tenants, ordem de locks completa, última reserva, fence/replay, mudanças simultâneas,
plano vencendo durante criação, revisão preservada, publicação bloqueada, upload
incerto, crash antes/depois dos commits e da possível submissão, resposta tardia,
custo desconhecido e recuperação sem segundo gasto. Mock injetado de guard prova
encaixe de componentes, sem comprovar esse protocolo de concorrência.

O ledger já tem teto mensal agregado OpenAI e por tenant, baseados em estimativas.
Não são limite de fatura, nem cobrem chamadas fora do ledger. O modo real também
exigirá schema/API próprios: hoje os modos persistidos são `local` e `visual_fake`.
Não rotular imagem real como simulação para evitar a mudança de contrato.

Versão anterior integral: [snapshot de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/BL04-atomicity-proposal.md).
