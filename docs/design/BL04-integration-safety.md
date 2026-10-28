# BL04 — integração segura de IA visual à prévia

Atualizado em **28/10/2026**. Estado: **preparo de fontes e prévia simulada
implementados; geração real desconectada**. Complementa o
[SDD BL04](../phases/BL04-context-and-ai-production.md) e a
[coordenação transacional](BL04-atomicity-proposal.md).

## O que está ligado e o que está isolado

| Componente | Estado atual |
| --- | --- |
| Briefing/retrieval | Acervo pertinente e kit congelados; Jev opcional no worker local, desligado por padrão e limitado a desenvolvimento/teste. |
| Preparação visual | Confere escopo, versões e hashes; normaliza orientação e remove metadados das cópias, preservando originais. |
| Pedido e ledger | Pedido visual, intenção/fence e reserva transacional; validação das fontes ainda ocorre em outra sessão. |
| Prévia `visual_fake` | JPEG privado com acabamento do kit e marca de simulação, revisão e decisão; sem IA gerando a cena. |
| Adapter/orquestrador real | Existem e têm testes com HTTP/guarda simulados; não conectados ao percurso de clientes. |
| Guarda real | `VisualEffectGuard` é protocolo, sem implementação completa/revisada para efeitos reais. |
| Temporal visual | Workflow/activity separados testados, sem registro no worker ou ligação ao dispatcher. |

Ensaios com fixtures fictícias fora do worker não comprovam esses gates nem
homologação comercial. Rede paga precisa de credenciais e orçamento explícitos
para a execução concreta; autorizações antigas de um ensaio não são recorrentes.

## Contrato de entrada e fontes

O pedido identifica operação, receita/formato, configuração e versões do briefing,
roteiro, contexto, kit, acervo e referências. O hash idempotente inclui o modo de
geração e os campos relevantes; mesmo UUID com conteúdo diferente é conflito.
A API/schema atuais aceitam `local` e `visual_fake`, sem modo real disponível.

O servidor constrói snapshot mínimo verificável: IDs/versões/hashes, fatos e
validades, origem e direitos. Não aceitar chave arbitrária de objeto ou JSON
supostamente autorizado do navegador. Busca lexical encontra candidatos, sem
provar intenção. Ambiguidade pede esclarecimento; ausência de foto real não
permite inventar produto/local e apresentá-lo como documental.

Enviar somente material pertinente e no máximo uma referência do kit do formato
escolhido. Normalizar orientação antes de remover EXIF e metadados equivalentes;
preservar original, registrar hashes e impedir envio de cópia não validada.
Logo, texto, preço e CTA são conferidos literalmente; kit não prova fatos.

## Aceite, acesso e alterações

O [aceite único](ai-as-core-service.md) é a autoridade para texto, imagem,
interpretação e transcrição. Não pedir consentimento visual ou TypeSafe separado.
Direitos sobre fontes, membership, plano, configuração técnica, orçamento e
aprovação da publicação continuam como verificações internas independentes.
O ledger isolado não autentica owner nem comprova suas fontes.

Na admissão revalidar tenant, owner ativo, contrato, acesso, roteiro, direitos,
fontes, versões, validade factual e fence. Mudança solicitada de kit, foto do
acervo ou contexto aguarda as criações admitidas, cancela fila não iniciada e
bloqueia novos inícios. O modo simulado cobre parte dos escritores; o protocolo
completo precisa ser demonstrado. Revisão preservada deve indicar que a peça
foi criada antes da mudança, com publicação sujeita a direitos e aprovação.

O plano vencendo após a admissão permite terminar e revisar a prévia privada;
novas criações e publicação aguardam renovação. A retenção da prévia deve deixar
de expirar automaticamente enquanto a conta estiver ativa. Essas decisões são
**escopo a implementar**, incluindo filtros de acesso, expiração de propostas e
prévias e `MediaRetention`; 0058 não as resolve. Owner revogado não ganha acesso,
e a política após encerramento fica para sua fase própria. Só staff poderá
resolver pendência cujo autor perdeu acesso, com registro/auditoria e acesso
restrito; esse fluxo ainda precisa ser implementado.

## Coordenação, dinheiro e incerteza

A reserva e o fence são atômicos, mas a verificação de fontes/contrato na sessão
owner está separada da sessão correlator. Fechar admissão e recuperação dessa
fronteira com todos os escritores e ordem de locks consistente antes da chamada.
A autorização de desenvolvimento atual usa travas/ledger existentes, sem tabelas
ou grants novos; alternativas de privilégio anteriores estão preservadas como
histórico rejeitado/não aprovado, sem serem requisitos da solução.

O ledger mantém teto mensal por tenant e agregado OpenAI, padrão desativado,
em micros USD. Cobre estimativas das operações que o utilizam, sem garantir
limite de fatura ou custo total do plano. Somente criador de reserva nova pode
submeter uma vez; replay de intenção acompanha o estado existente. Depois de
possível envio, timeout, falha de upload, lease vencida ou reinício não autorizam
reenvio/troca automática de fornecedor nem liberação fictícia do valor reservado.

Persistir custo/uso comprovados e estimativas separadamente; excedente ou valor
incerto exige conciliação. Ainda faltam alerta operacional e recuperação completos.
A agregação pelo mês UTC da submissão não limita todas as cobranças tardias.
Tempos de activity, HTTP, lease e reconciliação precisam de perfil próprio:
[execução Temporal visual](BL04-visual-temporal-execution.md).

## Saída privada, retenção e validação

Objetos de saída são privados e exclusivos por tentativa/fence, com MIME e hash
conferidos. Worker vencido só pode limpar seu próprio objeto, nunca a chave da
execução vencedora. Não manter locks durante download, geração, acabamento ou upload.
Conferir fence, prova de admissão e condições aplicáveis antes da disponibilização.
Logs usam IDs/campos permitidos, sem prompts, imagens, URL assinada ou segredos.

Materiais WhatsApp associados são duráveis e não podem ser excluídos pelo
histórico; limpeza técnica e remoção de foto do acervo são fluxos próprios.
Prévias geradas têm nova decisão de preservação, ainda não implementada;
retenção após encerramento da conta foi adiada para a fase de encerramento, sem
introduzir exclusão automática nesta etapa.

Antes de conectar o real: testes concorrentes com roles reais `_test`, crash entre
commits, resultado incerto sem segundo gasto, limites de orçamento, mudança de
fonte, expiração de plano, revisão preservada, publicação bloqueada, isolamento e
limpeza de órfãos. Só após segurança integrada avaliar qualidade BL04.3: fidelidade,
texto/logo, legibilidade móvel, aceite do titular e custo por peça aceita com refações.

Versão anterior integral: [snapshot de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/BL04-integration-safety.md).
