# BL04.2 — materiais WhatsApp duráveis e troca de número

Atualizado em **28/10/2026**. **Implementado localmente:** migration 0058 aplicada,
preservação dos materiais associados e continuidade após troca de número.
Complementa o [SDD](../SDD.md), [BL04](../phases/BL04-context-and-ai-production.md)
e as [decisões vigentes](../DECISIONS.md).

## Contrato atual

Texto, foto, áudio e vídeo já associados a um negócio são preservados sem prazo
automático. O histórico WhatsApp é consulta: não oferece exclusão desses envios,
e a API recusa essa exclusão para todos os tipos. A insatisfação com uma peça pode
ser resolvida enviando outro material. Direitos sobre conteúdo, aceite do serviço,
plano e aprovação de uma peça continuam tendo funções próprias.

O acervo estruturado em **Sobre meu negócio** é outro recurso: fotos desatualizadas
podem ser removidas. Copiar uma foto WhatsApp ao acervo é uma ação explícita com
direitos e origem; não classifica automaticamente mensagens como produtos, fatos
confirmados ou skills. Preservar mensagens não implementa memória pesquisável.

A 0058 aceita ausência de expiração em assets/eventos associados e ajusta seus
consumidores e limpeza. A deduplicação das mensagens associadas é preservada.
Limpeza de status, eventos descartados/não atribuídos e uploads órfãos continua
separada. O banco de desenvolvimento e a base `_test` receberam a migration;
isso não demonstra que outros ambientes tenham sido atualizados.

## Troca de número

Cada negócio tem **um número WhatsApp ativo**. O evento já associado conserva
seu tenant/negócio de origem e continua sendo processado após a troca ou durante
um intervalo sem vínculo ativo. A entrega simulada revalida o destinatário atual:
espera o novo vínculo verificado e envia para o número ativo novo, sem reutilizar
como destino o remetente do material original. Não exigir que o cliente espere
uma criação terminar para trocar o número.

Esse percurso está implementado e testado no processamento e na entrega falsa.
O envio real de prévia e aprovação pelo WhatsApp ainda precisa ser integrado e
homologado. Uma tabela histórica de períodos de vínculo não é requisito aprovado;
o [desenho anterior](BL04-whatsapp-link-history-review.md) permanece uma hipótese
para lacunas de correlação, sem autorizar schema ou grants novos.

## Limites e trabalho restante

- Mensagens ainda não atribuídas, quarentena e callbacks tardios exigem análise
  própria: não presumir associação retrospectiva ao negócio apenas pelo número
  atualmente ativo. Não reconstruir vínculos antigos por suposição.
- Só é possível preservar a mídia efetivamente recebida e salva. Um download que
  falhou ou um objeto já removido não é recuperado pela migration.
- O uso automático dos envios como contexto recuperável/memória continua pendente;
  não confundir armazenamento com interpretação, indexação ou treinamento.
- A decisão posterior de preservar **prévias geradas** enquanto a conta estiver
  ativa ainda requer alterar retenção e acesso das prévias. A 0058 não a implementa.
- A política após encerramento da conta será definida na fase de encerramento,
  conforme decisão do proprietário; não introduzir exclusão automática nesta etapa.
  Não aplicar aos materiais duráveis a exceção antiga de revisão por sete dias.

## Implantação e evidências

A atualização local ocorreu após pausa coordenada dos processos e backup; o
[CHANGELOG](../CHANGELOG.md) conserva validações e limites. Para outro ambiente,
inventariar claims de exclusão, efeitos desconhecidos e versões em execução;
a 0058 bloqueia claims antigos não resolvidos. API, ingest, correlator, retenção,
processamento e workers devem usar código compatível com materiais sem expiração.
Reverter cegamente código ou backup pode apagar ou perder mensagens posteriores.

Validar em armazenamento falso e PostgreSQL dedicado `_test`, com roles restritas:
todos os tipos após as janelas antigas, deduplicação, isolamento, concorrência com
limpeza, processamento após troca de número e entrega ao número novo. Testes e
mocks locais não homologam Meta nem autorizam chamadas pagas.

Versão anterior integral: [snapshot de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/BL04-whatsapp-durable-materials.md).
