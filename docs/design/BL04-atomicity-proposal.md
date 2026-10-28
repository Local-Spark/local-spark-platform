# BL04.2 — proposta de controle transacional para geração visual

**Decisão posterior do proprietário:** o material enviado deve ser preservado
para contexto do negócio, e a foto recebida não deve ser excluída apenas por
insatisfação com uma peça. A exceção de sete dias discutida abaixo dependia da
expiração automática da foto e deixa de ser premissa da jornada desejada. As
seções anteriores ficam como histórico e diagnóstico do código atual, que
ainda implementa expiração e exclusão. A política de prévias, o descarte técnico
e dados após encerramento da conta não foram definidos por essa decisão.

Estado: **desenvolvimento com mocks aprovado; coordenação real não aplicada**.
O proprietário aprovou testar a opção sem novas tabelas ou grants. A reserva
com fence existente não autoriza uma chamada real, e a proposta anterior de
alterar permissões não foi aprovada nem aplicada. A revisão automática rejeitou
a extração proposta da barreira enquanto a coordenação ainda não estava
suficientemente demonstrada; não repetir nem contornar essa rejeição.

Em 28/10/2026, o proprietário alterou a regra: pedidos de mudança de fonte ou
retirada aguardam as criações já iniciadas, cancelam a fila ainda não iniciada e
impedem novos inícios até sua aplicação. Isso substitui a alteração imediata de
kit/foto descrita anteriormente e exige reavaliar as alternativas abaixo; elas
são hipóteses históricas, não a única solução ou requisito de grants amplos.

## Problema

O worker que reserva valores usa a role do correlator. O briefing, kit, acervo
e consentimento são protegidos por políticas diferentes para o proprietário.
Consultá-los em uma sessão e reservar em outra deixa uma janela em que as
fontes ou a autorização podem mudar antes do registro da tentativa. Um fence
impede que um worker antigo conclua a prévia, mas, isoladamente, não evita
chamada paga com fontes desatualizadas.

## Alteração candidata

Na mesma transação curta e em ordem fixa: validar tenant e proprietário ativo;
proteger contra alterações concorrentes a associação, plano, consentimentos,
vínculo e material WhatsApp, proposta e briefing, versões atuais de contexto,
catálogo e kit e as fotos/logo efetivamente selecionadas; revalidar fontes;
validar fence; registrar a intenção e reservar o valor; confirmar o commit.
As consultas devem ser restritas ao tenant, negócio e ator autorizados, sem
acesso geral a dados de outros clientes.

Uma possibilidade é uma função fixa `SECURITY DEFINER` com `search_path` fixo,
sem SQL dinâmico, de uma role sem login e sem `BYPASSRLS`, com políticas
específicas para as leituras bloqueantes necessárias. Ela exigiria permissões
adicionais nas tabelas relevantes; o escopo exato de cada privilégio e a
alternativa de encapsular também a reserva precisam de revisão. O login do app
não receberia essa role. Não se pretende manter transação aberta durante a
chamada externa. Ausência de linha, expiração e inserções concorrentes exigem
tratamento explícito.

O levantamento inicial dos recursos inclui `memberships`, `business_profiles`,
`billing_accounts`, `billing_sponsorships`, `visual_ai_consents`,
`editorial_ai_consents`, `intent_jev_consents`, `whatsapp_processing_consents`,
`whatsapp_channel_links`, `whatsapp_material_events`, `whatsapp_material_assets`,
`editorial_proposals`, `editorial_briefings`, `business_context_heads`,
`business_catalog_heads`, `business_offerings`, `business_offering_promotions`,
`business_collection_photos`, `business_brand_kit_heads` e
`business_brand_kit_logos`, além da própria `media_previews`. Isso é um
levantamento para análise, não uma lista aprovada de grants: verificar também
versões imutáveis, registros ausentes e todos os escritores antes de definir o
conjunto mínimo. As tabelas `visual_cost_reservations` e `visual_ai_attempts`
armazenam reserva e intenção.

Após a admissão e confirmação do início de uma criação, pedidos de alteração
do kit, foto ou contexto e retirada visual devem ficar pendentes até seu término;
nenhuma nova criação deve ser admitida enquanto existir pedido pendente, e as
que aguardam na fila devem ser canceladas. Não manter transação ou lock aberto
durante a chamada: a pendência e seus efeitos precisam ser duráveis. Uma resposta
perdida ou timeout não prova conclusão; não reenviar automaticamente e manter o
pedido em verificação até haver solução segura. A prévia que conclui enquanto
se aguarda a retirada de autorização permanece disponível. A prévia concluída
antes da alteração de uma fonte também permanece disponível para revisão,
identificada como criada antes da mudança; publicação exige direitos e aprovação.
O gate de retirada existe apenas no
fluxo simulado; a espera por mudança de fonte ainda não está implementada.
Direitos, expiração, acesso e demais eventos fora de uma solicitação de mudança
seguem exigindo verificações apropriadas; a decisão não autoriza uso sem direito.

## Alternativa a avaliar: locks cooperativos, sem novas permissões

Uma alternativa arquitetural é usar locks advisory transacionais em operações
que alteram as fontes e na decisão de iniciar a geração. O lock não concede
permissão de leitura ou escrita: cada operação continua sujeita às roles e ao
RLS existentes. A revisão automática rejeitou a migração anterior que criava
roles e grants amplos; esta alternativa não a aplica nem a contorna. **Ainda é
um desenho, não uma implementação validada nem autorização para ligar o
provedor real.**

O portão de consentimento visual já coordena sua própria retirada no fluxo
simulado. Uma coordenação mais ampla só funciona se **todos** os escritores das
demais fontes obedecerem ao mesmo protocolo, incluindo:

- Atualizações de catálogo, preços, promoções, fotos e direitos do acervo;
  configuração e exclusão de logo; kit e fatos do negócio.
- Mudanças e revisão de roteiro, consentimentos editorial/Jev/WhatsApp e visual,
  vínculo do canal, telefone, material recebido e transcrição.
- Alterações de associação/owner, assinatura e patrocínio, inclusive jobs de
  cobrança; escritores futuros e processos administrativos precisam aderir.
- Workers de retenção, descarte, upload e exclusão, não apenas endpoints web.

Os caminhos `whatsapp_retention.purge_expired_raw` e
`whatsapp_routing.route_once` removem eventos em lotes de múltiplos tenants.
Precisam identificar as chaves envolvidas e adquirir locks em ordem estável
antes de alterar registros, ou ser redesenhados em lotes menores por tenant.
Não basta adicionar lock a alguns endpoints. Remoção de objetos continua fora
da transação: o estado/direito deve ser marcado e verificado antes do I/O;
não manter lock enquanto se espera storage ou qualquer fornecedor.

O plano, a assinatura e a associação pertencem ao tenant e nem sempre têm
`business_id`. Uma hipótese é usar uma guarda compartilhada por tenant e
exclusiva por negócio para operações específicas, e guarda exclusiva por tenant
para alterações que atingem todos os negócios. A geração, a retirada e os
escritores precisam seguir uma única ordem definida: por exemplo, tenant,
negócio e depois as linhas e locks já existentes. Locks múltiplos de lote devem
ser ordenados antes da aquisição. O desenho concreto precisa verificar essa
ordem em todos os caminhos para evitar deadlocks; não há presunção de que os
locks existentes já sigam essa hierarquia.

Como as roles atuais não compartilham uma transação, uma hipótese de execução é:

1. Na sessão owner, adquirir a guarda e validar proprietário, consentimentos,
   fontes e fingerprint; não carregar bytes nem chamar fornecedor sob lock.
2. Enquanto a guarda curta permanece, a sessão correlator valida o fence e
   registra intenção e reserva em sua própria transação.
3. Somente após ambos os commits confirmados e os demais gates concluídos, a
   operação externa pode iniciar. Se a transação correlator confirmar e a owner
   falhar ou o processo cair entre commits, **não enviar**: preservar a tentativa
   como órfã ou incerta para reconciliação, sem presumir custo zero nem repetir.
   Essas transições duráveis e sua recuperação ainda precisam ser projetadas e
   testadas. Duas transações não são atomicamente equivalentes a uma.
4. Após a resposta, revalidar fontes e direitos e aplicar a regra acordada de
   retirada pendente. A expiração pelo relógio pode ocorrer mesmo com locks;
   verificá-la na admissão e novamente na disponibilização.

`Database.transaction` atualmente define `lock_timeout` de 3 segundos e
`statement_timeout` de 10 segundos. Muitos locks de tenants num batch, ou um
lock compartilhado por negócios do mesmo tenant, podem gerar contenção e
timeouts; é necessário limitar lotes, medir o impacto e fazer somente retries
transacionais seguros que ainda não tenham produzido efeitos externos. Como
ninguém deve esperar o fornecedor segurando lock, estender timeouts não resolve
o protocolo de efeitos incertos.

Antes de qualquer ativação: inventariar e revisar todas as escritas, versões
imutáveis e inserções de linhas ausentes; provar que as alterações passam pelas
roles atuais; testar em concorrência consentimento/reconcessão, troca e exclusão
de fotos, expiração, kit, associação, plano e retenção, incluindo lotes de
tenants diferentes, reversão, fence, crash entre commits, resposta tardia e
estouro de orçamento. Medir contenção e comprovar que nenhuma exceção, rota
antiga ou job pula a guarda. Se não for possível demonstrar esses requisitos, o
provedor real permanece desligado. Uma eventual proposta concreta pode exigir
revisão específica; este texto não concede aprovação para alterar segurança.

## Riscos e verificação antes de aplicar

Alterar roles, grants e políticas amplia a superfície de segurança do banco.
Bloqueios de várias fontes podem causar contenção ou deadlocks se a ordem e os
escritores não forem revisados. Antes de usar o provedor real, detalhar tabelas
e privilégios mínimos e testar isolamento entre tenants, revogação e nova
concessão, mudança e exclusão de fotos, vencimento, fence, rollback, replay,
concorrência pelo orçamento, timeout, resposta tardia e limpeza de arquivos.
Nenhuma permissão adicional foi aplicada por este documento.

## Avaliação do protocolo cooperativo em 27/10/2026

Foi prototipada uma alternativa com travas curtas por negócio e tenant, sem
novas permissões de banco. Testes isolados demonstraram a exclusão mútua, mas
isso não demonstrou a cobertura de todos os escritores nem a recuperação após
falhas entre transações de roles diferentes. Os processos em lote também
precisam de limites de espera e avaliação de contenção. A recuperação de uma
retirada de consentimento quando o proprietário perde acesso permanece aberta.
As alterações experimentais nesses processos foram retiradas: o protótipo não
é uma proteção ativa nem autoriza envio de imagens ao provedor real. Antes de
ativar a geração, implementar e testar a solução completa com falhas, concorrência
e as permissões existentes.

## Proposta para revisão após a decisão de um negócio por organização

**Desenvolvimento com mocks aprovado em 28/10/2026; não autoriza chamadas reais.**
O proprietário aprovou desenvolver e testar coordenação usando travas e ledger
existentes, sem criar tabelas ou ampliar grants. A retenção de fotos WhatsApp
continua dependente de solução técnica revisada; a proteção completa ainda não
foi demonstrada. Como existe no máximo um negócio por organização, a guarda de execução pode ser organizada por
`tenant_id` sem consultar outro negócio. Isso reduz a complexidade de seleção,
mas não torna atômicos o aceite, os dados, a reserva e a chamada externa.

Uma opção a revisar, sem criar grants ou tabelas, é reutilizar a trava curta de
organização existente em `billing.lock_commercial_change` e a trava de negócio
de `VisualConsentGate._lock`. A hipótese de adquirir primeiro a trava comercial
e depois a visual **não é segura e não deve ser implementada**: o worker
`EditorialProposalService.run` atualmente adquire a trava visual antes da
comercial. Uma prova sintética com roles app e correlator na base `_test`
reproduziu a espera circular entre as duas ordens, sem escritas nem provedores.
No mesmo ensaio, duas sessões usando a ordem visual → comercial foram
serializadas sem timeout. Isso não demonstra que essa ordem seja segura para
todos os demais caminhos; a hierarquia completa ainda precisa ser revisada e
testada.

Na proposta, antes da submissão, a sessão
owner revalida acesso e impressão digital das fontes e registra a admissão
durável; enquanto segura a guarda curta, a sessão correlator reserva a tentativa
e o orçamento pelo fence existente. A chamada ao provedor só ocorre depois da
confirmação dos commits. Preparação de bytes, armazenamento e rede permanecem
fora dos locks. O identificador do negócio e suas fontes vêm de dados validados
do servidor, nunca de uma chave de objeto arbitrária enviada pelo cliente.

A coordenação precisa cobrir todos os caminhos, não somente os formulários:

- `editorial_context`, `business_catalog`, `brand_kits` e `business_collection`
  já usam a guarda visual em parte das alterações e implementam espera para
  alguns tipos; revisar gravações de logo, conclusão de upload, reconciliação,
  versões e alterações ainda não cobertas antes de confiar nessa proteção.
- `editorial_proposals` altera e revisa roteiros em caminhos que não usam a
  mesma guarda. `whatsapp_materials.delete_material` pode excluir propostas;
  `whatsapp_retention` e `whatsapp_routing` apagam materiais/eventos em lotes.
  Esses caminhos precisam preservar o processamento já iniciado e impedir novos
  usos conforme a decisão do proprietário, sem segurar locks durante I/O.
- `phone_verification`, `whatsapp_link`, `audio_transcription`, alterações de
  membership/usuário e mudanças de conta/patrocínio em `billing` e
  `billing_processor` também podem mudar as condições verificadas. A regra de
  acesso ou cobrança durante um processo já iniciado ainda precisa ser
  confirmada; não presumir que uma solicitação de exclusão de foto autoriza o
  uso após perda de acesso.
- As rotinas de retenção e roteamento operam com a role correlator em lotes de
  tenants. Essa role não tem acesso ao estado owner de `visual_consent_runs`;
  locks isolados não demonstram como adiar exclusões até uma criação terminar.
  Resolver essa fronteira com as permissões vigentes, sem ampliar grants, ou
  apresentar uma alternativa de segurança separada para revisão. O término de
  uma operação também não deve depender de um owner que já perdeu acesso.

O ledger existente distingue reserva `submitted` e claim `uncertain`, e faz o
claim antes do envio. Isso ajuda a evitar segunda cobrança, mas duas transações
não são uma só: se houver crash ou confirmação perdida entre a reserva e o
commit owner, preservar a tentativa e conciliar por estado durável antes de
qualquer liberação ou repetição. A recuperação, os timeouts, a ordem entre a
guarda comercial, a visual, o preview e o lock financeiro, e a contenção para
lotes ainda precisam ser definidos e testados; não tratar timeout como prova de
que o provedor não recebeu o pedido.

Além da inversão confirmada entre as travas visual e comercial, o worker
editorial adquire a linha de proposta antes da trava visual; o briefing e a
criação da proposta usam uma trava de origem antes da visual; a transcrição
usa a visual antes da sua trava de orçamento. Alterações precisam considerar
essas sequências e os locks de preview e financeiro, não apenas duas travas.

Uma segunda prova em `_test`, usando uma proposta sintética e as roles atuais
do app e do correlator, reproduziu espera circular entre linha de proposta →
visual e visual → linha de proposta. No mesmo cenário, as duas transações
seguindo visual → linha serializaram. Os registros sintéticos foram removidos;
nenhum provedor foi chamado. O resultado cobre somente essas duas ordens e não
comprova segurança do fluxo completo nem implementa proteção no runtime.

Antes de ativar o fluxo real, demonstrar em `_test`, sem chamadas pagas:
isolamento RLS entre contas, todas as mudanças concorrentes relevantes,
retenção/exclusão da origem, prévia mantida após mudança pendente, queda entre
commits, duplicação do dispatch, resposta incerta e limite de gasto. O teste
sintético do orquestrador com guard e provedor simulados prova o encaixe de
componentes, **não** o protocolo de concorrência. Caso a alternativa não cubra
as fronteiras de role e recuperação com as permissões vigentes, apresentar uma
proposta diferente para revisão, sem reintroduzir o grant rejeitado.

## Evidências de mudanças ainda não coordenadas

Em 28/10, duas provas diagnósticas temporárias foram executadas somente em
`_test`, sem chamadas externas e sem alterar o runtime:

- Com um registro visual em `in_flight`, `edit_script` atualizou o roteiro da
  versão 1 para 2 sem criar uma mudança pendente. Uma prévia sintética do modo
  `local` deixou de aparecer na listagem porque ela ainda exigia a versão
  anterior. Essa prova **não** executou IA ou uma prévia `visual_fake`; o filtro
  de versão identificado em `MediaPreviewService.list` é compartilhado.
- Com uma operação visual em `in_flight`, a exclusão explícita do material
  WhatsApp marcou a origem para remoção e apagou a proposta imediatamente. A
  chave estrangeira também apagou seu histórico de versões de roteiro, enquanto
  a linha de prévia permaneceu. A leitura da prévia exige proposta e origem
  válidas, por isso uma coordenação que apenas adie a exclusão ainda não prova
  que a prévia será revisável após ela.

As provas mostram comportamentos atuais que devem ser corrigidos, não definem
o contrato desejado. Preservar revisão após edição ou remoção exige demonstrar
proveniência, permissão de leitura e o comportamento da retenção sem enfraquecer
as barreiras existentes. A solução e a disponibilidade da prévia anterior
seguem pendentes; não habilitar geração real por causa dessas evidências.

## Retenção da foto WhatsApp e prévia por sete dias — opções para revisão

**Pesquisa não implementada:** o proprietário aprovou testar a coordenação com
travas e ledger existentes, sem criar tabelas ou ampliar permissões. A solução
específica de retenção e qualquer nova coluna, policy ou grant permanecem para
revisão separada; nenhuma opção abaixo habilita IA real por si só.

Ocorrem efeitos em vários pontos: `whatsapp_routing` e `whatsapp_retention`
podem remover o evento; a retenção pode apagar o objeto e o asset fora da
transação; excluir o asset remove proposta e briefing por cascata; e
`media_retention` pode apagar a prévia ao vencer seu lease. A listagem e o
arquivo da prévia exigem origem e proposta existentes. Portanto, apenas adiar
o DELETE do asset não preserva a revisão depois que a origem for excluída.

**Opção A — usar somente evidências e permissões atuais.** O correlator lê
`media_previews`, inclusive `source_asset_id`, `state` e `updated_at`, além do
ledger. Isso permite detectar algumas prévias em renderização e calcular um
prazo lógico `updated_at + 7 dias` após `completed`, sem atualizar
`expires_at`. Entretanto, `rendering` não comprova admissão; uma lease vencida
ou uma reserva `uncertain` não prova que o fornecedor terminou; e `updated_at`
é um campo genérico, não uma prova imutável da conclusão ou do motivo da
retenção. `visual_change_completed_previews` só é gravada para certas mudanças
pendentes e simulações, não informa o vencimento da origem e não é legível pelo
correlator. Após apagar o asset não é possível reconstruir com esses dados se
ambos os prazos venceram durante a geração. Reter toda prévia concluída por
sete dias ou reutilizar `error_code` como marcador ampliaria ou alteraria o
contrato e não foi aprovado. Não há implementação segura demonstrada com esta
opção; não transferir a credencial de app ao dispatcher para contornar a
separação de roles ou a rejeição automática anterior.

**Opção B — prova explícita e acesso mínimo, sujeita a nova aprovação.** Como
hipótese, reaproveitar `visual_change_completed_previews` com metadados
específicos que distingam o vencimento das demais mudanças e registrem o prazo
revisável; registros antigos sem essa prova não recebem a exceção por suposição.
Avaliar uma permissão de **somente leitura e somente colunas necessárias** para
o correlator nas evidências visuais, com policy e teste RLS por tenant, além de
qualquer ajuste mínimo de schema necessário. Isso seria uma mudança nova e não
aprovada: detalhar grants, policies e dependências antes de pedir revisão. Não
é o grant de leitura de `editorial_ai_usage` à API rejeitado anteriormente e
não autoriza reintroduzi-lo ou contorná-lo.

Em qualquer opção, é necessário coordenar início, exclusão e retenção com a
mesma ordem de travas, sem lock durante chamada externa; impedir admissão de
foto já expirada ou com exclusão iniciada; aguardar resultado desconhecido;
produzir e persistir prova de conclusão antes da remoção; e oferecer a prévia
para revisão com tenant, owner, fence e hash verificados, mesmo se origem e
proposta tiverem sido apagadas. Isso exige também adaptar a navegação que hoje
parte da proposta. A disponibilidade para revisão não autoriza publicação.
Casos legados, perda de acesso do owner, timeout/crash, lote entre tenants e
limpeza após sete dias ainda exigem desenho e testes; nenhuma opção está provada.

Por fim, a constraint da migration `0047_visual_preview_mode` admite apenas
`local` e `visual_fake`. Um modo persistido de geração real exige uma mudança
específica revisada; reaproveitar o rótulo `visual_fake` para IA real seria
incorreto. Essa constatação não aprova alteração de schema nem de permissões.

## Proposta detalhada de privilégio mínimo para retenção — revisão futura

**NÃO APROVADA E NÃO IMPLEMENTADA.** O escopo autorizado atualmente é testar
coordenação com mocks, sem novos grants. Esta seção é um desenho para revisão:
não comprova que a solução seja segura nem autoriza alterar schema, policies,
roles, runtime ou ativar o provedor real. A proposta não inclui acesso da API a
`editorial_ai_usage`, cujo grant foi rejeitado pela revisão automática.

### Evidência e prazo

Como hipótese sem nova tabela, acrescentar à prova existente
`visual_change_completed_previews` duas colunas anuláveis, ambas preenchidas
somente para o caso específico aprovado pelo cliente:

- `source_expired_at`: vencimento da foto WhatsApp capturado enquanto sua
  origem ainda existe; não armazena a foto, o texto nem a chave do objeto.
- `retention_review_until`: fim do prazo de revisão, igual ao instante
  persistido e verificável da conclusão mais sete dias. Para as demais provas,
  inclusive registros históricos, ambos seriam nulos.

A exceção só seria registrada quando **os dois prazos**, o da foto e o da
própria prévia, vencerem entre a admissão e a conclusão da geração. É preciso
definir e testar o instante autoritativo de conclusão: `updated_at` é genérico,
e `now()` no PostgreSQL representa o início da transação. A proposta depende de
uma prova transacional consistente com a conclusão, sem presumir que
`created_at` da prova ou uma lease expirada representa esse instante.
Validar a relação entre tenant, negócio, prévia, execução, fence e hash, e
exigir que ambas as novas colunas estejam preenchidas ou ambas nulas. Remoção
explícita e mudanças de kit/contexto têm regras próprias; não equipará-las
automaticamente ao vencimento simultâneo.

O prazo seria lógico: a leitura e o expurgo considerariam a prova válida sem
alterar `media_previews.expires_at`. O hash e os identificadores da prova podem
vincular a prévia ao resultado concluído sem preservar o conteúdo original. A
API precisaria disponibilizar para o proprietário uma prévia desvinculada da
origem e da proposta, validando escopo e integridade; a tela de Conteúdos hoje
parte da proposta e precisaria acompanhar essa mudança. Revisão não autoriza
publicação. A prova tem FK para a prévia: o expurgo não pode apagar a prévia,
nem a prova em cascata, antes do prazo aplicável.

### Acessos propostos, ainda sujeitos a revisão

Para o correlator, avaliar **somente SELECT por coluna** nas seguintes
evidências; estas listas são um teto inicial para investigação, não uma prova
de que todas as colunas sejam necessárias:

- `visual_consent_runs`: `tenant_id`, `business_id`, `preview_id`,
  `operation_id`, `actor_id`, `fence`, `state`, `created_at` e `finished_at`.
- `visual_change_completed_previews`: `tenant_id`, `business_id`, `actor_id`,
  `preview_id`, `operation_id`, `fence`, `sha256`, `source_expired_at` e
  `retention_review_until`.

Não incluir prompts, arquivos, chaves dos objetos ou escrita nessas tabelas.
Avaliar policies de SELECT por tenant nessas tabelas, com o tenant proveniente
do trabalho legitimamente reclamado e definido localmente à transação; manter
RLS obrigatória e verificar roles, heranças, `BYPASSRLS` e políticas efetivas em
cada ambiente. O correlator capaz de definir qualquer tenant não fica isolado
de um comprometimento apenas por essa variável: também é necessário provar a
vinculação do tenant ao trabalho. O acesso do owner à prova e seu `WITH CHECK`
também devem ser revisados para garantir autoria e integridade, sem pressupor
que a policy atual valide todos os campos de procedência.

Em `media_previews` já existe policy permissiva para o correlator com
`USING (true)`: policies permissivas aplicáveis se combinam por **OR**. Adicionar
outra policy restrita não reduziria esse acesso existente. Qualquer mudança
desse alcance exige revisão específica dos consumidores e não está aprovada
aqui. Não passar credenciais do app ao dispatcher nem reintroduzir o acesso
rejeitado ao ledger editorial como atalho.

### Caminhos concorrentes e recuperação

Os lotes de `whatsapp_retention` reclamam assets e apagam o objeto fora da
transação; `whatsapp_routing` também remove eventos vencidos;
`media_retention` expurga prévias, e a reconciliação editorial remove propostas
vencidas. A exclusão do asset pode eliminar proposta e briefing por cascata.
Já o expurgo do inbox bruto em `whatsapp_ingest` é independente: verificar sua
relevância para deduplicação e fontes já normalizadas, sem presumir que toda
linha bruta precise ser retida ou ampliar grants do ingest.

O desenho precisa impedir novas admissões após vencimento ou exclusão iniciada,
cancelar pedidos em fila e aguardar a execução admitida. Uma exclusão externa
já reclamada ou com resultado desconhecido não fica comprovadamente concluída
apenas porque sua lease venceu. O resultado desconhecido da IA também não deve
ser considerado concluído ou reenviado automaticamente. O ledger de custo em
`uncertain` não é prova de execução em andamento: pode continuar assim mesmo
após sucesso enquanto o custo é conciliado.

A prova deve ser persistida antes da remoção da origem; uma queda entre o
commit da prévia e o da prova exige impedir o expurgo e um caminho de
reconciliação autorizado, inclusive quando o proprietário perdeu acesso. Como
há transações e roles diferentes, atomicidade e recuperação ainda precisam ser
demonstradas. Não manter locks durante chamadas externas. A ordem global de
locks permanece em investigação: os diagnósticos anteriores já mostraram
deadlocks em ordens ingênuas. Lotes por tenant devem ser limitados e justos;
medir impacto de consultas e armazenamento adicional antes de assumir escala.

### Casos legados, decisões e testes necessários

Provas antigas sem os novos metadados não recebem sete dias por suposição.
Antes de qualquer migração, avaliar execuções antigas em andamento, como
interromper admissões e como recuperar registros incompletos sem descartar
dados ou inventar evidência. Permanecem decisões para revisão: mecanismo e
autoridade da reconciliação de falhas, efeito de perda do owner ou término do
plano sobre a revisão, e a política efetiva de expurgo após o prazo.

Validar com mocks e roles reais em base de teste: acesso por coluna e negação
de escrita, tenant ausente e cruzado, heranças e OR de policies; corridas entre
admissão, expiração, exclusão, geração, gravação de prova e expurgo; queda
entre commits e exclusão externa incerta; retries e fence; os limites exatos
dos dois vencimentos e dos sete dias; legado sem prova; preservação e acesso da
prévia após remoção da origem e proposta; e limpeza ao final do prazo. Testar
também negócios diferentes, proprietário sem acesso e concorrência dos lotes.
Esses cenários ainda não foram comprovados e não autorizam geração real.
