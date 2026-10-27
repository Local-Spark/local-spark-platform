# BL04 — integração segura de IA visual à prévia

Estado: **desenho pendente de implementação e validação**. Os componentes de
ledger, adapter e resolução de candidatos existentes são isolados; não há ainda
uma geração visual integrada, habilitada ou homologada. Este documento detalha
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

O interpretador do acervo recebe texto do cliente e nomes de candidatos. Seu
contrato interno não verifica consentimento, orçamento nem idempotência; a
integração deve comprovar esses requisitos antes de qualquer chamada externa.
As políticas do ledger isolado restringem o tenant, não validam membership nem
a autorização do ator sobre o negócio; a activity integrada deve verificá-las
antes da reserva e dos efeitos, inclusive após revogação.

## Reserva, Temporal e incerteza

O ledger mínimo usa micros de USD e limite técnico mensal por tenant, padrão
zero; não representa franquia comercial nem todo o custo do cliente. A reserva
precisa ser criada antes de qualquer envio e a decisão deve ser atômica com a
revalidação do `dispatch_fence` e a gravação durável da intenção de envio. Isso
exige integrar a reserva à **mesma transação** da tentativa; chamar o método
atual em uma transação separada não oferece essa garantia. Usar uma operação
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

Gravar o resultado em chave privada exclusiva da tentativa/fence, com hash e
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
