# BL04 — integração segura de IA visual à prévia

Atualizado em **29/10/2026**. Estado: **parte 2 conectada com validação final em
andamento e HTTP simulado; primeira chamada paga pendente**. Complementa o
[SDD BL04](../phases/BL04-context-and-ai-production.md) e a
[coordenação transacional](BL04-atomicity-proposal.md).

## O que está ligado e o que está isolado

| Componente | Estado atual |
| --- | --- |
| Briefing/retrieval | Acervo pertinente e kit congelados; Jev opcional no worker local, desligado por padrão e limitado a desenvolvimento/teste. |
| Preparação visual | Confere escopo, versões e hashes; normaliza orientação e remove metadados das cópias, preservando originais. |
| Pedido e ledger | Pedido visual, intenção/fence e reserva transacional; validação das fontes ainda ocorre em outra sessão. |
| Prévia `visual_fake` | JPEG privado com acabamento do kit e marca de simulação, revisão e decisão; sem IA gerando a cena. |
| Adapter/orquestrador real | Conectados pelo runner à prévia `visual_ai`; testes usam adapter real com transporte HTTP simulado. |
| Guarda concreta | `DatabaseVisualEffectGuard` e claims revalidam fonte/owner/aceite/plano, reserva/fence, claim única e commit privado. |
| Temporal visual | Workflow/activity próprios registrados com opt-in, dispatcher com ID estável e lease de 12 minutos. |

Ensaios com fixtures fictícias fora do worker não comprovam esses gates nem
homologação comercial. Rede paga precisa de credenciais e orçamento explícitos
para a execução concreta; autorizações antigas de um ensaio não são recorrentes.

## Contrato de entrada e fontes

O pedido identifica operação, receita/formato, configuração e versões do briefing,
roteiro, contexto, kit, acervo e referências. O hash idempotente inclui o modo de
geração e os campos relevantes; mesmo UUID com conteúdo diferente é conflito.
A API/schema aceitam `local`, `visual_fake` e `visual_ai`. A migration 0059 exige
fingerprint visual e recusa downgrade com linhas `visual_ai`, sem novos grants;
foi aplicada somente ao `_test`. O modo real exige opt-in separado, com flag
desligada/reserva zero por padrão, chaves, C01 e tetos por tenant/agregado.

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
bloqueia novos inícios. Os dois modos visuais coordenam os escritores atuais no
[protocolo da guarda](BL04-effect-guard.md); novos writers precisam respeitá-lo.
Revisão preservada indica que a peça
foi criada antes da mudança, com publicação sujeita a direitos e aprovação.

O plano vencendo após a admissão permite terminar e revisar a prévia privada;
novas criações e publicação aguardam renovação. Prévias concluídas e proveniência
não são apagadas por prazo; tentativas visuais iniciadas sem resultado resolvido
também são conservadas. Revisão concluída não exige execução visual habilitada;
aprovação e validade factual continuam com prazos próprios. Owner revogado não ganha acesso,
e a política após encerramento fica para sua fase própria. Só staff poderá
resolver pendência cujo autor perdeu acesso, com registro/auditoria e acesso
restrito; a implementação C10 foi adiada pelo proprietário e a exceção fica bloqueada.

## Coordenação, dinheiro e incerteza

A reserva e o fence são atômicos, mas a verificação de fontes/contrato na sessão
owner está separada da sessão correlator. O run durável congela fontes entre
os commits; ordem de locks e recuperação são documentadas na guarda concreta.
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
Prévias concluídas/proveniência e tentativas visuais incertas são preservadas;
retenção após encerramento da conta foi adiada para a fase de encerramento, sem
introduzir exclusão automática nesta etapa.

Validação da conexão com roles reais `_test`, HTTP simulado e Temporal local:
testes concorrentes, crash entre
commits, resultado incerto sem segundo gasto, limites de orçamento, mudança de
fonte, expiração de plano, revisão preservada, publicação bloqueada, isolamento e
proteção de objetos incertos. Limpeza física de órfãos e varredura de recuperação
seguem como evolução operacional, mantendo exceções bloqueadas. A parte 3 exige
fontes/credenciais/teto de gasto explicitamente autorizados antes da chamada paga.
Depois avaliar qualidade BL04.3: fidelidade,
texto/logo, legibilidade móvel, aceite do titular e custo por peça aceita com refações.

Versão anterior integral: [snapshot de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/BL04-integration-safety.md).
