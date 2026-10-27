# BL04.2 — proposta de controle transacional para geração visual

Estado: **proposta para revisão; não aplicada**. A reserva com fence existente
não autoriza uma chamada real. Esta proposta descreve o objetivo e o alcance de
uma possível alteração de permissões; não constitui migração pronta nem prova
de que seja a única alternativa.

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

Após o commit, a chamada é considerada em trânsito. O produto decidiu que uma
retirada solicitada enquanto a tentativa já está em andamento aguarda sua
conclusão e permite visualizar a prévia terminada; bloqueia novas admissões.
Alterações de outras fontes ou direitos continuam exigindo revalidação. O gate
que coordena essa retirada existe no fluxo simulado e ainda precisa ser ligado
e validado no provedor real; não elimina a necessidade de coordenar outras
fontes com a reserva. Resposta perdida ou timeout não deve levar a reenvio
automático; o custo fica reservado até conciliação. O teto global do ensaio
sintético é um controle separado, também pendente antes de chamadas pagas.

## Riscos e verificação antes de aplicar

Alterar roles, grants e políticas amplia a superfície de segurança do banco.
Bloqueios de várias fontes podem causar contenção ou deadlocks se a ordem e os
escritores não forem revisados. Antes de usar o provedor real, detalhar tabelas
e privilégios mínimos e testar isolamento entre tenants, revogação e nova
concessão, mudança e exclusão de fotos, vencimento, fence, rollback, replay,
concorrência pelo orçamento, timeout, resposta tardia e limpeza de arquivos.
Nenhuma permissão adicional foi aplicada por este documento.
