# BL04.2 — proposta para excluir foto WhatsApp sem perder a prévia concluída

Estado: **proposta para revisão, não implementada**. Restringe-se à exclusão
voluntária de uma foto recebida pelo WhatsApp. Não autoriza envio real de imagens
à IA, não altera as FKs existentes e não representa o comportamento atual.

## Resultado esperado

Se o proprietário pedir a exclusão enquanto uma geração já admitida usa a foto,
registrar o pedido, cancelar logicamente a fila anterior e impedir novos inícios.
A foto permanece disponível exclusivamente para a tentativa já admitida; após
o resultado conhecido, processar a exclusão e manter a prévia resultante para
revisão até seu prazo original ou o prazo adicional definido abaixo. A tela deve
identificá-la como anterior à exclusão. Se não houver geração admitida, a
exclusão prossegue imediatamente.
Uma falha ou resultado desconhecido não prova que o fornecedor terminou: manter
o pedido pendente e exigir reconciliação, sem reenvio automático.

O pedido de excluir a origem não equivale à autorização de publicar a prévia.
A publicação a partir dessa exceção continua bloqueada; outros consentimentos e
acesso ao negócio continuam sendo aplicados. Decisão de 28/10/2026: se o prazo
de retenção vencer durante uma geração já iniciada que usa a foto, manter a
origem privada até a conclusão conhecida e excluí-la em seguida. Resultado
incerto permanece em verificação; não interpretar uma lease vencida como prova
de que a geração terminou. A prévia concluída deverá permanecer para revisão
mesmo após a exclusão da origem. Este controle ainda não está implementado.

## Por que a exceção atual não basta

- `WhatsAppMaterialsService.delete_material` marca a origem para remoção e
  exclui propostas vinculadas. A remoção física do asset também causa cascata
  para propostas e briefings, preservando as FKs atuais.
- `media_previews` e a prova de `0050` podem sobreviver, mas `list`, `file_key`,
  `_validate_visual` e a tela de Conteúdos exigem a proposta e a origem ativas.
- `whatsapp_retention` pode apagar inbox, evento, arquivo e asset durante uma
  geração; `media_retention` pode recolher a prévia quando a proposta/origem
  desaparece. Os workers de retenção usam a role correlator, que não lê os runs
  owner-scoped. Conferir apenas `state='rendering'` ou o prazo da lease não
  demonstra que uma tentativa iniciada terminou.
- O worker de prévias não pode emitir uma prova se o objeto, evento ou proposta
  já tiverem sido apagados. Uma exceção genérica para `MATERIAL_NOT_FOUND`
  ampliaria acesso indevidamente e não deve ser utilizada.

## Controle mínimo proposto, ainda sujeito a revisão de permissões

Uma migração aditiva posterior a `0050`, sem `SECURITY DEFINER`, sem retirar
FKs e sem conceder novos direitos sobre tabelas existentes, poderia criar:

1. `visual_whatsapp_source_holds`: somente identificadores `tenant_id`,
   `business_id`, `preview_id`, `operation_id` e `source_asset_id`, com
   unicidade por tentativa e FKs restritivas para run, prévia e asset. Sem
   nome, texto, telefone, objeto ou conteúdo. O app owner teria SELECT/INSERT/
   DELETE sujeito à política do tenant e membership; o correlator teria apenas
   SELECT das colunas de identificação necessárias para reter seus lotes.
   A policy de leitura global do correlator seria limitada a esta tabela
   nova, necessária ao job multitenant, e precisa de revisão explícita. Não
   conceder a ele acesso aos runs owner-scoped nem payloads da fila.
2. Um recibo específico `visual_deleted_whatsapp_review_receipts`, ou extensão
   aditiva equivalente da prova existente, vinculado por FK à prévia e à
   operação durável de exclusão. Deve conter tenant, negócio, proprietário,
   preview, fence, hash do resultado, prova do consentimento visual original,
   identificador da origem e somente os metadados necessários para verificar
   que a autorização de processamento e o vínculo continuam válidos. Dados
   como hash do remetente, caso necessários, ficam privados e nunca são
   devolvidos pela API. Não copiar foto, transcrição, texto ou título do post.

As constraints de integridade são defesa adicional, não barreira suficiente:
uma FK pode impedir `DELETE` SQL, mas não desfaz um `store.delete()` que tenha
ocorrido antes. A sincronização descrita abaixo é obrigatória.

## Ordem transacional proposta

1. A admissão usa o lock advisory atual do negócio, valida owner, consentimento,
   fence e origem, incluindo expiração e ausência de exclusão/lease reivindicada.
   Na mesma transação, insere o hold das fontes WhatsApp usadas. Se a retenção
   já tiver iniciado a remoção, bloquear a admissão; lease vencida, sozinha, não
   prova que a remoção externa parou. Não manter lock durante rede ou storage.
2. A exclusão voluntária usa operação determinística/idempotente e o mesmo lock.
   Com hold em andamento, enfileira `whatsapp_material_delete` na fila de `0050`
   e retorna estado pendente. Sem hold, executa o caminho normal. A fila bloqueia
   novas admissões; pedidos repetidos não produzem exclusão duplicada.
3. Os jobs de retenção descobrem candidatos sem row lock e processam por negócio
   em ordem determinística: adquirir primeiro o mesmo lock advisory, reconsultar
   o hold e a validade, e somente então reivindicar uma lease. Um hold impede
   apagar asset, objeto, evento e inbox associados. A autorização da claim tem
   de continuar válida até o efeito externo; queda, reclaims e exclusão externa
   com resultado desconhecido exigem protocolo próprio, não simples timeout.
   `purge_expired_raw`, `claim_expired_assets`, `finish_purge` e suas rotas de
   retries precisam ser incluídos; SQL com lotes mistos exige limites e testes
   de deadlock/contenção. Não se deve segurar o lock durante `store.delete`.
4. Cada geração com resposta conhecida conclui sua prévia e registra prova de
   conclusão sob o gate. O último `finish` cria o recibo específico para as
   prévias cujo `source_asset_id` é o da operação de exclusão, antes de marcar
   a origem e apagar propostas; em seguida aplica a exclusão, registra auditoria
   e remove o hold correspondente. Tudo isso confirma em transação owner curta;
   a exclusão física fica com a retenção após o commit. Uma queda desfaz o
   conjunto; não alternar `app.actor_id` da sessão para outro usuário.
5. `media_retention` precisa distinguir recibo válido de uma proposta/origem
   desaparecida: proteger apenas essa prévia comprovada até o prazo de revisão aprovado,
   com prioridade para uma solicitação explícita de excluir a própria prévia.
   Ao mesmo tempo, garantir limpeza do objeto privado correto. O caminho atual
   deriva a chave de `render_key`; antes de ativar, conferir a compatibilidade
   com a chave de simulação contendo `attempt-{fence}` e testar falhas de storage.

A finalização por um owner diferente do autor do pedido ainda tem limitação RLS
conhecida e deve ficar fail-closed com estado visível; não contornar a rejeição
automática anterior com troca de identidade em outra transação. Uma eventual
identidade de serviço para execução delegada exige desenho e revisão separados.

## Contrato de revisão isolado

Um endpoint privado de arquivo revisável pode retornar apenas `id`,
`created_at`, `expires_at`, `width`, `height` e `created_before_change=true`.
A UI pode exibir “Prévia anterior à exclusão” com botão de visualização, mesmo
sem uma proposta. Não reconstruir proposta, título ou texto de origem. O link
privado exige prova específica, resultado concluído, hash/fence iguais, owner
ativo, tenant e negócio corretos, acesso por plano quando aplicável, TTL e
consentimentos/vínculo exigidos pela jornada. A verificação visual pós-retirada
deve respeitar a regra já aprovada apenas para o run admitido; nova concessão
não valida provas antigas automaticamente. Nenhuma dessas leituras concede
aprovação, nova geração ou publicação.

Essa leitura deve ser separada de `MediaPreviewService.file_key()`, que também
é usado por entrega e publicação. A exceção de revisão não pode tornar uma
prévia elegível a esses fluxos. O comprovante deve ligar tenant, negócio, owner
ativo, operação, run, fence, hash da prévia e concessão original, verificando
o prazo aprovado. Sua emissão deve ocorrer na transação de finalização após
comprovar a prévia concluída e antes de liberar o hold ou aplicar a exclusão.
Não retornar a origem nem reconstruir seus dados. Políticas e permissões para
essa prova continuam sujeitas a revisão e testes com as roles reais.

## Testes necessários antes de habilitar

- Corridas `admit` × claim de retenção, `delete` × múltiplos runs, falha ao
  preparar/gerar, cancelamento de fila, `finish` × purge, TTL, replay e fences.
- Queda após claim, após exclusão do objeto e entre commit de prévia e `finish`;
  resultado externo incerto mantém hold, sem duplicação nem conclusão fictícia.
- Dois tenants, acesso por viewer/owner revogado/segundo owner, consentimento
  retirado e reativado, canal desvinculado, plano inativo e hashes adulterados.
- Comprovar que FKs e retenção do original permanecem intactas, que o arquivo
  excluído não fica em consultas de materiais e que o artefato aprovado para
  revisão seja eliminado ao final de seu TTL; o endpoint não retorna a origem.
- Exercício com roles reais no banco `_test`, jobs concorrentes multitenant e
  armazenamento falso; testes da UI em tela pequena e não incluir chamadas pagas.

## Decisões e lacunas adicionais — 28/10/2026

O prazo de retenção da origem, se vencer durante uma geração já iniciada,
aguarda o resultado conhecido; então a origem deve ser eliminada. Resultado
externo incerto permanece em verificação. A prévia comprovadamente concluída
continua revisável mesmo após a exclusão da origem; se a retenção da foto e o prazo dela
vencer durante a geração, deve permanecer disponível por sete dias após a
conclusão. Essa prova só autoriza a revisão, não uma nova geração ou publicação.
Quando o prazo original da prévia não vencer durante a geração, ele permanece
inalterado. Os sete dias devem ser contados a partir do instante persistido de
conclusão, não do início da geração nem de uma leitura posterior.

A retirada dos consentimentos de WhatsApp e de IA de texto também deve aguardar
a conclusão da geração admitida, bloqueando novas operações e cancelando as que
ainda não começaram. A dependência da autorização específica de transcrição
de áudio precisa ser avaliada separadamente; sua inclusão não foi decidida.

**Ainda não implementado:** os serviços atuais revogam imediatamente esses
consentimentos, e seus consumidores consultam o estado diretamente em recepção,
processamento, transcrição, respostas, propostas e entregas. Simplesmente adiar
o registro de revogação permitiria novas operações indevidas. A implementação
deve coordenar todos esses caminhos, estado pendente nas APIs e na interface,
prova limitada ao run admitido e aplicação após a última execução, com testes
de concorrência e isolamento entre negócios. A retenção da fonte e a revisão
independente dela também permanecem pendentes; não há hold conectado ao runtime.
