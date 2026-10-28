# BL04 — integração segura de IA visual à prévia

Estado: **implementação iniciada, geração real ainda não integrada**. Há
consentimento visual independente, preparação de fontes e um fluxo simulado de
prévia com reserva e fence; a chamada real ao adapter permanece bloqueada. Não há
geração visual real integrada ou homologada. Este documento detalha
a ordem necessária e complementa [BL04](../phases/BL04-context-and-ai-production.md).

## Alcance da primeira integração

Criar uma rota interna de prévia de imagem privada para desenvolvimento e teste,
com a flag desligada por padrão e provedor falso nos testes automatizados.
Preservar o renderer local e os contratos existentes; não habilitar o modo em
staging ou produção nem publicação automática. Vídeo, animação e avatar não
estão incluídos. A resposta só pode ser candidata para revisão humana, sem
alegar que o resultado retrata fielmente pessoas, produtos ou locais reais.
A qualidade comercial e o custo por peça aceita dependem de avaliação própria.

## Intenção e fontes versionadas

1. A solicitação identifica explicitamente o modo (`local` ou `visual_ai`),
   mantendo `local` como padrão para registros e clientes anteriores. Incluir
   modo, receita e versões do briefing e do modelo, configurações, contexto,
   roteiro, kit selecionado, acervo e referências no hash idempotente e na
   chave da geração. Repetir operação com payload alterado deve falhar; um
   novo orçamento ou uma revisão é operação explícita, não retry implícito.
2. Persistir snapshot mínimo e verificável das fontes autorizadas: IDs,
   versões e hashes das fotos e do kit, fatos e validades, origem e direitos.
   A busca lexical do acervo oferece candidatos, não prova intenção ou
   identidade. Em caso de ambiguidade, falta de fonte ou referência imprópria,
   interromper e solicitar esclarecimento. Usar somente mídia pertinente e,
   se necessário, no máximo uma referência do kit do formato correspondente.
   O snapshot deve ser criado e armazenado de forma íntegra pelo servidor; a
   revalidação compara os campos estruturados, mas não autentica JSON arbitrário
   do cliente. Uma descrição livre, mesmo confirmada, não comprova preço vigente.
3. Uma foto conceitual não é prova de como é o espaço ou o produto real.
   Preço, promoção, CTA e logo precisam de verificação literal e eventual
   acabamento determinístico; a imagem gerada não garante esses dados.
4. Planejar a mudança dos esquemas e dados persistidos, tipos de mídia,
   dimensões, limpeza, contratos da API e migração sem invalidar prévias
   antigas. O código atual de prévia conhece nome, cor, fato e possível mídia
   WhatsApp; ele **não** possui snapshot suficiente de kit e acervo.

## Consentimento e revalidação

A autorização de gerar imagem e enviar as referências ao fornecedor deve ser
verificada independentemente de a proposta textual ter sido criada com IA ou
com baseline. Definir seu contrato e finalidade antes de habilitar a geração,
incluindo retirada e direitos sobre imagens; não presumir que consentimento
textual autorize automaticamente uma chamada visual.

Verificar organização, responsável, plano, consentimento aplicável, roteiro e
seu estado, fatos e datas no fuso do negócio, versões do kit/acervo e direitos,
disponibilidade e hashes dos arquivos **antes do efeito externo**. Após a
chamada, revalidar antes de disponibilizar o resultado. Alterações, expiração,
exclusão ou revogação invalidam a candidata; o custo ocorrido continua no
ledger. Não manter transação ou lock abertos durante download, chamada de IA,
renderização ou upload. Uma revogação que ocorra durante uma chamada em trânsito
não pode ser desfeita retroativamente: descartar o resultado e registrar o custo.

Atualização de produto: quando o proprietário solicitar a
retirada, impedir imediatamente novas admissões e cancelar o que ainda está na
fila; a retirada efetiva aguardará somente os processos já iniciados. Até que o
protocolo de admissão e retirada esteja ligado ao provedor real, somente a
simulação implementa essa regra. Esta decisão não libera a chamada visual real
nem resolve por si só mudanças concorrentes de fotos, kit ou plano.

O interpretador do acervo recebe texto do cliente e nomes de candidatos. Seu
contrato interno não verifica consentimento, orçamento nem idempotência; a
integração deve comprovar esses requisitos antes de qualquer chamada externa.
As políticas do ledger isolado restringem o tenant, não validam membership nem
a autorização do ator sobre o negócio; a activity integrada deve verificá-las
antes da reserva e dos efeitos, inclusive após revogação.


## Atomicidade e permissões para a integração

O ledger usa a role `meu_braco_direito_correlator`, enquanto consentimento,
briefing, kit, catálogo e fotos usam políticas da role do proprietário. Duas
sessões não compartilham a mesma transação; validar com uma role e reservar com
outra não garante atomicidade. O método `reserve_in_transaction` pressupõe
contexto de tenant e ator já configurado e não autentica o proprietário nem
valida o fence, as fontes ou o consentimento.

A integração precisa, na mesma transação, verificar o proprietário ativo e as
permissões atuais, proteger a tentativa contra troca de fence e serializar sua
validação com alterações ou revogações relevantes, registrar a intenção e
reservar o custo. Definir ordem consistente dos locks e confirmar que todos os
escritores participam do protocolo; consultas comuns em READ COMMITTED, ou um
preflight em outra transação, não impedem essas corridas. Apenas uma reserva
nova e efetivamente confirmada pelo commit permite uma chamada externa.

São alternativas a avaliar: uma role dedicada à geração visual, com acesso
mínimo por tenant e proprietário ativo, ou uma função `SECURITY DEFINER` de
escopo restrito e `search_path` fixo, executada por role sem login e sujeita a
políticas RLS específicas. Nenhuma deve usar `BYPASSRLS` ou ampliar acesso sem
necessidade. A estratégia de lock deve considerar que locks de linha exigem
privilégios adicionais; não conceder atualizações amplas apenas para obtê-los.
Cobrir isolamento, revogação concorrente, fence, rollback e replay em testes de
integração antes de habilitar chamadas reais.

## Reserva, Temporal e incerteza

O ledger mínimo usa micros de USD e limite técnico mensal por tenant, padrão
zero; não representa franquia comercial nem todo o custo do cliente. A reserva
precisa ser criada antes de qualquer envio e a decisão deve ser atômica com a
revalidação do `dispatch_fence` e a gravação durável da intenção de envio. O
fluxo simulado usa `reserve_in_transaction` na mesma transação que o fence e a
intenção; porém a validação das fontes ainda ocorre em outra sessão. Isso não
autoriza efeito externo. Usar uma operação
estável por tentativa lógica, não o número de fence, que muda no redispatch.

Somente o criador de uma reserva nova pode iniciar a chamada. Replay de uma
intenção existente nunca autoriza nova chamada: enquanto houver worker ativo,
acompanhar; após prazo ou perda de estado, marcar como `uncertain` e manter a
reserva. A conciliação deve distinguir uma falha comprovadamente anterior ao
consumo de uma resposta perdida; não presumir que timeout, erro HTTP, falha de
upload, perda de lease ou reinício do processo signifiquem custo zero. Não
retentar nem trocar fornecedor automaticamente após possível submissão.

O custo **efetivamente comprovado** pode liquidar a reserva; custo maior do que
ela deve ser persistido e alertado. Tokens e metadados de `usage` não são por
si só o valor faturado: guardar estimativa e tabela de preços separadamente,
com versão e origem, e manter valor incerto até conciliação quando não houver
prova. O ledger atual registra evento de excesso, mas não entrega alerta
operacional nem reconciliação automática. O teto mensal por tenant não impõe
o teto global do ensaio de até US$ 1 autorizado para dados fictícios: será
necessário implementá-lo antes de qualquer chamada real desse ensaio.

A activity atual tem prazo de 2 minutos, o adapter permite até 180 segundos e
o dispatcher pode redistribuir depois de 3 minutos. Ajustar e testar esses
prazos e o comportamento do dispatcher como um conjunto: duração maior não
substitui o protocolo acima. O fence impede publicação por um worker antigo,
mas não impede sozinho uma cobrança externa. Um worker tardio pode registrar
um custo comprovado; só pode disponibilizar a imagem se a tentativa ainda
possuir fence válido e as fontes e permissões continuarem válidas.

O ledger agrega pelo mês UTC de submissão da reserva; uma reserva incerta de
um mês anterior não ocupa o teto do mês seguinte. Portanto não garante um teto
mensal pelo faturamento efetivo do provedor nem limita sozinho cobranças tardias.
A reserva aceita uma estimativa fornecida pelo chamador, que deve usar tabela
versionada e estimativa conservadora; um valor real maior só é registrado após
o gasto e exige alerta, reconciliação e bloqueios comerciais apropriados.

## Objetos privados e retenção

O renderer local agora grava em chave privada exclusiva do fence, impedindo que
um worker antigo apague o arquivo da tentativa vencedora. A integração de IA
precisará preservar essa propriedade. Gravar o resultado com hash e
mime conferidos. Um worker vencido deve apagar apenas o objeto que ele próprio
criou; não usar uma chave compartilhada que permita sobrescrever ou apagar
resultado de outra tentativa. Adaptar a retenção, exclusão e limpeza de órfãos
para essas chaves e para referências revogadas. Logs e auditoria não devem
expor imagens, prompts, credenciais ou conteúdo privado por padrão.

Antes de envio ao fornecedor, verificar autorização e gerar uma cópia privada
normalizada, removendo metadados como GPS, aparelho e data/hora (EXIF e outros
metadados equivalentes). Normalizar a orientação visual antes de remover EXIF,
preservar o original e registrar versão/hash e consentimento da derivada. Testar
orientação e fidelidade visual com exemplos reais antes de produção. O acervo já
normaliza imagens; verificar o mesmo requisito para fontes recebidas pelo
WhatsApp. Se a minimização não tiver sido validada para uma fonte, bloquear o
envio da imagem não normalizada ao provedor.

## Ordem e testes

1. Fechar contrato de seleção semântica e snapshot, consentimento e migração;
   manter o caminho local compatível e o modo visual desligado.
2. Integrar reserva atômica ao controle de tentativa e Temporal. Incluir
   estados de envio/resultado que não convertam `uncertain` em retry.
3. Conectar adapter falso e armazenamento privado por tentativa; verificar
   fontes antes/depois do efeito e impedir disponibilização sem revisão.
4. Testar corridas pela última reserva e pelo fence, replay com conflito,
   colisão entre workers, crash antes/depois do envio, timeout, resposta tardia,
   custo acima da reserva, custo desconhecido, falha de armazenamento, limpeza
   de órfãos, revogação, alteração de fatos/kit/fotos, validade e isolamento
   entre tenants. Não usar chamadas pagas em CI.
5. Um [ensaio sintético isolado](../evals/bl04-visual-synthetic-story-2026-10-27.md)
   já foi realizado fora do fluxo integrado. Antes de qualquer chamada real pelo
   fluxo integrado, implementar os controles e o teto global explícito e medir
   custos. A homologação comercial exige os gates de qualidade e aceite da BL04
   e não depende apenas de uma resposta do modelo.
