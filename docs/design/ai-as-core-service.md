# Uso de IA como parte do serviço

Atualizado em **28/10/2026**. **Decisão aceita e implementada localmente:**
IA integra o serviço contratado. O cliente concorda uma vez em **Plano e acesso**,
antes de novo checkout, com interpretação, texto, imagem e transcrição de áudio.
Não existem etapas de escolha/ativação por OpenAI, TypeSafe, modelo ou modalidade
na web. WhatsApp e Informações e preferências não oferecem esses controles.

## Jornada e autoridade

Cada negócio tem sua própria conta/organização e aceite. Contas existentes aceitam
a versão atual uma única vez antes de usar as rotas de serviço. Pagamento e aceite
antigo não são convertidos retroativamente em concordância com termos novos.
Desconectar WhatsApp desliga o canal, sem retirar o contrato do serviço.

GET/POST por negócio exigem owner e ação explícita sobre versão/hash exatos do
aviso. O POST grava contrato, ator, data e auditoria na mesma transação, de modo
idempotente. Não inicializa, reativa nem reescreve consentimentos individuais.
Recusas e registros antigos permanecem imutáveis como história/compatibilidade.
Após o contrato, mutações individuais retornam
`SERVICE_AGREEMENT_MANAGES_PROCESSING`; não são caminho de produto.

A geração contratual distinta em `consent_generation` vincula novos pedidos ao
aviso aceito, inclusive baseline local; pedidos pagos antigos não revivem com o
aceite. Timestamps legados usados em fingerprints de prévias antigas são mantidos.
O primeiro aceite bloqueia enquanto existirem mudanças/efeitos visuais pendentes,
sem fingir conclusão desses processos ou habilitar seu fornecedor.

## Controles internos e limites

Configuração de provedores, membership, acesso financeiro, orçamento, direitos
sobre fontes, fatos vigentes e aprovação específica da peça continuam próprios.
Contrato não confirma pagamento nem aciona publicação. O modo real visual continua
desconectado, mesmo com aceite válido. Voz sintética/avatar ficam após o piloto e
precisarão de decisão específica quando implementados; o aviso atual não os libera.

`service_agreement_required` continua como flag de transição em desenvolvimento e
testes, desligada por padrão; a web apresenta o aceite mesmo assim. Produção exige
enforcement. A conexão comercial do canal ocorre após contratação/aceite, sem
nova fila especial de mensagens anteriores. Termos/política atuais são **textos de
validação local**, ainda precisam de versão comercial definitiva.

Se o plano vencer durante uma criação admitida, a regra aceita é terminar e manter
revisão privada; novos trabalhos e publicação aguardam renovação. Prévias devem
ficar preservadas enquanto a conta estiver ativa. Esses comportamentos ainda
requerem implementação; não criar toggles de fornecedor para resolvê-los.
A recuperação quando o autor perde acesso será exclusiva de staff, com ação
restrita e auditada, ainda a implementar. Retenção após encerramento foi adiada
para sua fase, sem exclusão automática agora. Ver [registro de decisões](../DECISIONS.md).

## Evidência e continuidade

A entrega do aceite registrou backend com suíte de 1.583 testes mais complemento
de 24 testes (sete novos), atingindo 100% de linhas/branches; web com 360 testes,
cobertura integral, build e três jornadas Chromium. Isso não equivale a uma nova
execução durante esta revisão documental, nem homologa Meta/IA visual real.

O desenho anterior tentou reativar permissões com o POST e recebeu rejeição da
revisão automática. Essa alternativa foi abandonada; a implementação preserva
histórico e registra somente o contrato. O snapshot anterior conserva a análise,
sem transformá-la em plano futuro. Próximo desenvolvimento permanece BL04.2:
[coordenação de fontes, acesso e orçamento](BL04-atomicity-proposal.md).

Versão anterior integral: [snapshot de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/ai-as-core-service.md).
