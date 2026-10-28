# BL04.2 — Preservação dos materiais do WhatsApp: proposta para revisão

**Estado:** a retenção de materiais associados foi implementada e a migration
0058 foi aplicada à base local. A entrega real de prévias pelo WhatsApp e o
uso automático de memória continuam pendentes. As opções abaixo são registros
do desenho e de limitações, não uma autorização para ativar provedores. O cliente
decidiu preservar os materiais enviados pelo WhatsApp como contexto do negócio,
retirar a opção de excluir fotos desse histórico e manter a remoção de fotos
no acervo, para substituir imagens desatualizadas. Guardar os arquivos não cria
automaticamente memória pesquisável ou skills; isso requer implementação própria.

**Decisão posterior:** se o cliente trocar de número enquanto processamos um
material já enviado, a criação continua para o mesmo negócio. Após a troca, a
prévia e o pedido de aprovação devem ir para o número ativo novo. O cliente não
precisa esperar o processamento para trocar o número. A implementação e a
validação dessa jornada estão pendentes.

## Mudança proposta

1. Reutilizar `whatsapp_material_assets` para os materiais já recebidos e seus
   objetos privados e `whatsapp_material_events` para a ligação ao negócio e
   processamento, sem criar uma nova tabela de acervo. Não classificar
   automaticamente uma mensagem ou foto como produto ou fato confirmado.
2. Preparar uma migração nova, sujeita a revisão, que preserve registros
   existentes e permita ausência de expiração em `expires_at` dos assets e dos
   eventos de material. Rever os defaults e a criação dos registros para que
   novos envios associados ao negócio também não recebam esses prazos. Não
   eliminar colunas históricas, reescrever migrations antigas ou supor que um
   objeto já apagado possa ser recuperado.
3. Ajustar, como uma alteração coordenada, a roteirização, processamento,
   histórico, download, transcrição, briefing, seleção de referências,
   propostas e prévias para aceitar materiais sem data de expiração. As
   verificações existentes de tenant, negócio e permissões permanecem. O
   prazo próprio de aprovação ou de prévias não é alterado por esta decisão.
4. Deixar de purgar o material recebido e seu evento devido a 7 ou 30 dias.
   Manter a limpeza de uploads incompletos e objetos órfãos, sem confundi-los com
   uma mídia aceita e salva; manter separados callbacks de status e registros
   estritamente técnicos. A regra de armazenamento após encerramento da conta
   não foi decidida.
5. A interface já não oferece **Excluir** para fotos no histórico do WhatsApp
   e mantém a remoção no acervo. O backend também recusa pedidos de exclusão
   de fotos por API, sem apagar propostas vinculadas. O tratamento da ação de exclusão atualmente
   disponível para texto, áudio e vídeo não deve ser ampliado nem presumido
   apenas por essa definição sobre o botão de fotos.

## Inbox e idempotência: ponto técnico a fechar antes de migrar

A inbox atual guarda a chave única que deduplica callbacks; ao expirar após sete
dias, um reenvio tardio pode virar um novo evento. O evento de material também
expira em sete dias, mesmo quando pendente ou falho. Só desativar o worker de
limpeza, ou apenas trocar o prazo do asset, deixa filtros, joins e a
idempotência incorretos.

A opção inicial a avaliar, sem tabela nova ou ampliação de grants, é manter na
inbox os **registros de mensagem** já vinculados a materiais, enquanto existirem
seus materiais/eventos, preservando a chave de deduplicação. Não tratar todos os
registros `linked` como material: também existem callbacks de status com esse
estado. A limpeza dos status pode permanecer técnica e separada.

É necessário fechar a preservação das mensagens válidas ainda em `quarantined`
quando o correlator está atrasado, inclusive a concorrência com alteração do
vínculo do número. Hoje a mensagem chega sem negócio e o vínculo atual é
sobrescrito ao trocar número; uma mensagem anterior ainda não processada pode
perder a associação. A solução precisa ser revisada antes da implantação. A limpeza atual ocorre também no recebimento pela role Meta,
e não apenas no dispatcher; não se deve dar à role Meta leitura ampla de
negócios ou eventos para resolver isso. Avaliar centralizar a limpeza em
componente que já tenha permissões adequadas, mantendo separada a quarentena de
mensagens ainda não associadas a negócio. Conferir políticas RLS reais e testar
as roles antes de escolher SQL; se a solução exigir novos grants ou outra
estrutura, voltar para revisão. Não presumir que um payload em quarentena já
represente um arquivo baixado.

## Evidências do rascunho de retenção

Um rascunho parcial foi preparado fora do repositório. Em PostgreSQL descartável,
passou por testes de texto, foto, áudio e vídeo com 40 dias simulados, deduplicação
e isolamento; também preservou registros sintéticos na transição 0057 → 0058 e
recusou uma foto com exclusão pendente. Ele não foi aplicado: ainda faltam cobrir
mudança de número, quarentena e implantação coordenada. Não recupera arquivos que
já tenham sido fisicamente apagados. O rascunho de retenção foi exercitado em
95 testes direcionados com PostgreSQL descartável e roles restritas; a reversão
da migration foi experimentada separadamente sem apagar os dados de origem. A
integração com troca de número e o CI completo ainda não foram validados.

## Troca de número — solução técnica ainda em análise

A troca hoje sobrescreve o vínculo anterior. Mesmo quando um material foi
salvo, algumas consultas usam apenas o vínculo atual; além disso, uma mensagem
recebida pouco antes da troca pode ainda não estar associada ao negócio. A
preservação precisa abranger os dois casos, sem habilitar dois números ativos.

Uma hipótese técnica ainda não aprovada é manter o vínculo atual e guardar os
intervalos dos vínculos anteriores ([proposta detalhada](BL04-whatsapp-link-history-review.md)),
para comprovar a origem de cada envio e recuperar o contexto depois de trocar
o número. Não presumir que essa estrutura seja necessária; avaliar primeiro
o uso seguro das informações já vinculadas ao negócio. Confirmação, desvinculação e alteração do
telefone precisariam atualizar o histórico de forma consistente. A solução deve
impedir associação ambígua se um número passar a outro negócio e limitar os
acessos por tenant e papel; o desenho de tabelas, políticas e privilégios ainda
precisa ser detalhado e revisado. O histórico que já foi sobrescrito não pode
ser reconstruído com segurança apenas a partir do vínculo atual.

A alternativa antes considerada de fazer o cliente esperar pela associação ou
pelo processamento para trocar o número não integra a jornada definida.
Recuperar conteúdo histórico e escolher o número para enviar uma resposta são
operações diferentes: a prévia e o pedido de aprovação devem usar o número ativo
novo após a troca, e não o número antigo apenas porque aparece no histórico.

## Ordem segura de implementação e implantação

- Preparar a migration e as alterações de aplicação como um conjunto, com
  avaliação de consultas e das permissões atuais; não executá-las na base local
  antes da revisão necessária. Testar em banco separado.
- Antes de atualizar um ambiente com dados, verificar o inventário de assets,
  eventos, pedidos de exclusão e uploads pendentes; fazer backup verificável.
  Decidir como tratar registros com exclusão já em andamento, sem ressuscitar
  arquivos comprovadamente apagados.
- Planejar a transição de **todos** os processos que podem apagar ou depender de
  prazo: API que recebe webhook, correlator, dispatcher/retention e workers.
  Código antigo não entende `NULL` em vários pontos. Não executar a migração
  enquanto qualquer processo antigo puder apagar registros ou ler esses valores.
  O plano de pausa da entrada deve permitir retentativa do provedor sem acusar
  recebimento de mensagens que não foram salvas; validar no ambiente de teste.
- Aplicar migration e código compatíveis e retomar serviços de forma controlada,
  verificando ingestão, processamento, histórico e ausência de descarte. Ter um
  plano de reversão que considere mensagens recebidas após a atualização: voltar
  o código ou restaurar backup cegamente pode perder dados mais recentes.

## Verificação necessária

Em banco e armazenamento de teste, sem cobranças reais:

- Receber texto, imagem, áudio e vídeo; simular passagem além de sete e 30 dias;
  executar as rotinas de limpeza e confirmar consulta, arquivo, transcrição e
  uso em briefing quando aplicável.
- Simular mensagem pendente, falha transitória, worker parado e reenvio da mesma
  mensagem depois de sete dias; confirmar processamento recuperável e uma só
  cópia por negócio.
- Verificar isolamento entre negócios, roles existentes e acessos diretos à API;
  testar concorrência entre limpeza, ingestão e processamento.
- Confirmar que histórico não oferece nem executa exclusão de fotos e que a
  remoção de fotos do acervo continua funcionando; não confundir as duas cópias.
- Verificar que upload órfão é limpo sem apagar um objeto efetivamente salvo e
  que os prazos próprios de propostas e prévias permanecem como estavam.

A preservação só pode ser garantida depois que o sistema receber e salvar a
mídia. Se o download falhar e a mídia de origem deixar de estar disponível,
precisamos registrar o erro e permitir recuperação quando possível; a proposta
não promete recuperar arquivos que nunca chegaram ao nosso armazenamento.
