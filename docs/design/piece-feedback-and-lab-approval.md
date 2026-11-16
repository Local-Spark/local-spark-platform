# Feedback de peças aprovadas e testes em Conteúdos

Implementado localmente em 16/11/2026; validação manual da jornada pendente.

## Decisões confirmadas

O cliente escreve livremente o que gostou e o que prefere diferente. Esse texto é
referência interpretável de gosto, não preferência fixa nem confirmação de um fato
comercial. Não há conversão automática em regra, nem pedido de confirmação de uma
regra derivada. O pedido atual prevalece.

Aprovação de teste é explícita por botão. Só as versões aprovadas aparecem em
Conteúdos para o administrador autorizado do laboratório. Feedback desses testes
permanece separado e nunca alimenta o histórico criativo real.

## Jornada do cliente

Após aprovar a versão exata em Conteúdos, o cliente vê um formulário opcional de
feedback. O comentário não altera o aceite, não bloqueia publicação e não gera
outra peça. Cada comentário é vinculado à peça/versão aprovada. Históricos de peças
simuladas não são elegíveis. Aprovação continua separada da publicação.

Sobre meu negócio → Preferências de conteúdo mostra os comentários como referências
de gosto, sem substituí-los por regras rígidas. É possível retirar um comentário
do contexto; o registro permanece para auditoria. Uma correção pode ser feita
retirando o comentário anterior e enviando outro na peça aprovada.

Até doze comentários ativos mais recentes alimentam o contexto criativo. Quando
existe, o briefing/legenda da versão é preservado junto à referência, permitindo
interpretar elogios sobre composição. Contextos antigos podem não conter briefing;
o modelo não deve presumir posições, aparência ou ritmo ausentes. A interpretação
ocorre na geração normal, sem chamada paga adicional para classificar feedback.
Isso não é treinamento/fine-tuning nem garante melhora visual por si só.

Snapshots do fluxo comum de imagens e motion incluem essas referências, sujeitas à
revalidação do contexto antes dos efeitos. O editorial legado também recebe as
referências na preparação do pedido. Comentários não fornecem fatos comerciais.

## WhatsApp

A aprovação registra um convite opcional quando existe vínculo ativo do cliente.
A resposta textual citando esse convite é encaminhada ao serviço de feedback com
identidade durável do evento de entrada, não ao gerador de ajustes. A correlação
confere ator, negócio, tenant, vínculo ativo, destinatário e prazo de sete dias.
Convites aparecem na lista de mensagens simuladas do espaço.

O transporte segue simulado, com `fake-feedback/...`; não há comprovação de envio
ou recebimento real pela Meta. Nesta fatia, feedback aceita texto até 2.000
caracteres. Áudio/anexos retornam feedback_text_required e texto acima do limite
retorna feedback_text_too_long, sem gasto ou geração. Não foi implementada
transcrição paga de feedback nem envio real de uma mensagem de erro.

## Jornada administrativa

Na prévia concluída há Aprovar peça de teste. O aceite confere versão e hash e
registra auditoria/outbox. Peças aprovadas ficam em uma seção própria de Conteúdos
marcada Teste, com prévia e download privado. Clientes não recebem essa listagem.
Nenhum teste é copiado para content_pieces nem ganha autorização para publicação.
`selected` continua significando escolha do produto, não aprovação humana.

## Persistência e autorização

Migração aditiva 0132: feedback por versão, convite de feedback por versão/ator,
aprovação privada de teste e contexto criativo opcional na versão produtiva.
RLS forçada e roles restritos. Comentários/contexto permanecem criptografados.
Feedback usa acesso de proprietário do negócio; laboratório exige identidade
configurada e conta administrativa ativa. Mutações são idempotentes e transacionais
com auditoria/outbox. Não há rede enquanto os registros estão bloqueados.

## Validação e limites

Migração aplicada à base local habitual, sem limpeza ou aprovação automática.
Leituras autenticadas confirmaram as novas listagens vazias nos três negócios e a
preservação da peça existente, ainda não aprovada. Sintaxe Python, Ruff, Prettier e
diff revisados. Regressões unitárias adicionadas, não executadas por orientação do
usuário. Sem suíte, banco de testes, build, typecheck, browser ou geração paga.

Pendente: validação manual das duas jornadas, provas de integração/RLS e concorrência
no banco dedicado de testes quando autorizadas e integração real de transporte.
Não há alegação de CI/cobertura integral ou validação end-to-end.
