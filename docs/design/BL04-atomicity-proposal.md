# BL04.2 — proposta de controle transacional para geração visual

Estado: **proposta para revisão; não aplicada**. A reserva com fence existente
não autoriza uma chamada real. Esta proposta descreve o objetivo e o alcance de
uma possível alteração de permissões; não constitui migração pronta nem prova
de que seja a única alternativa.

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
