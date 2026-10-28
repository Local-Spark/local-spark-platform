# Uso de IA como parte do serviço

Decisão de produto em 28/10/2026: o cliente contrata o Meu Braço Direito para
criar conteúdo com IA. A experiência deve explicar isso de forma simples na
contratação, sem apresentar controles separados para OpenAI, TypeSafe, texto,
imagem ou transcrição. A escolha do fornecedor é uma decisão técnica da
plataforma, dentro do serviço apresentado ao cliente.

O proprietário confirmou expressamente que a transcrição por IA dos áudios
enviados ao WhatsApp integra o serviço contratado, sem confirmação separada.
Também definiu que cada negócio terá sua própria conta, organização, aceite e
cobrança. A cobrança atual é por organização; a garantia de um único negócio
por organização está implementada e aplicada à base local, conforme o
[registro](one-business-per-organization.md).

O cadastro do negócio ocorre antes da contratação. Os termos de onboarding
`2026-10` são de validação local e não descrevem a oferta comercial de IA; não
serão usados como prova retroativa de ciência da nova versão. Os documentos
definitivos ainda precisam ser preparados antes da operação comercial.

## Jornada desejada

1. O cliente vê, antes de contratar ou ativar o serviço, uma explicação única:
   informações do negócio e os materiais enviados podem ser processados com IA
   e fornecedores para preparar conteúdos. Termos e política devem ter versões
   identificáveis e estáveis, acessíveis ao cliente.
2. Aceito o contrato aplicável e confirmado o acesso por assinatura ou patrocínio,
   o negócio pode usar as capacidades contratadas sem habilitar cada fornecedor.
   Cadastro, checkout aberto e redirecionamento não comprovam pagamento.
3. As contas já criadas recebem os termos atualizados **uma única vez antes de
   usar o serviço**. O aceite antigo ou o pagamento não serão convertidos
   silenciosamente em aceite dos novos termos.
4. O cliente continua escolhendo e controlando materiais do próprio negócio,
   conectando suas redes e aprovando publicações. Voz sintética e avatar próprios
   continuam fora da primeira oferta e exigem decisão específica quando houver
   implementação; esta decisão não aprova essas funcionalidades.

## Implementação atual — 28/10/2026

O aceite único tem GET/POST por negócio, exige owner e uma ação explícita sobre
versão/hash exatos e grava auditoria na mesma transação. Não escreve permissões
por fornecedor nem configura credenciais. O registro contratual é a autoridade
para novos processamentos de texto, imagem, interpretação e transcrição; as
recusas antigas são preservadas como histórico. Pedidos editoriais anteriores
não recebem a geração contratual de novos pedidos, evitando reativação da fila.
Mudanças ou efeitos visuais pendentes bloqueiam o primeiro aceite até conclusão.

Plano e acesso apresenta o check único antes do checkout; a API de contratação
recusa criar checkout sem o contrato atual. Conta já existente recebe o mesmo
aceite antes de usar as rotas de serviço. As telas WhatsApp e Informações e
preferências deixam de consultar ou alterar permissões individuais. Desconectar
o WhatsApp desliga o canal; não retira o aceite contratual. Status financeiro,
configuração técnica, orçamento e aprovação final da peça seguem próprios.

A flag de enforcement permanece para compatibilidade de testes e implantação;
a web apresenta o aceite mesmo quando ela está desligada. Não houve migração de
dados, mudança de credenciais, cobrança ou chamada real de IA nesta entrega.
O modo visual real continua sem ligação ao worker. Os termos continuam locais.

## Histórico da transição técnica anterior (superado pela implementação acima)

Estado da implementação nesta rodada: a migration `0056`, a leitura do aviso
versionado e a aceitação transacional interna foram exercitadas na base `_test`.
O endpoint público ainda não oferece POST, e a exigência está desativada por
padrão em desenvolvimento. A tela preparada não está ligada à jornada, e os
controles separados ainda existem. Não ativar enforcement no WhatsApp: uma
mensagem sem aceite pode ser marcada como falha definitiva. O proprietário
esclareceu que não há clientes em produção e que o canal será conectado após
contratação e aceite; não será criada uma fila especial para mensagens anteriores.
Os vínculos e mensagens já existentes no ambiente de teste precisam ser
considerados antes de ligar essa exigência.
O aviso é somente de validação local e seu hash não representa os documentos
comerciais definitivos. A migration `0056` foi aplicada ao banco de
desenvolvimento; isso não ativa o POST nem conecta a tela.

Na revisão de 28/10, a tentativa de expor o POST com reativação de permissões
anteriores foi rejeitada pela revisão automática por risco de ativar serviços e
por verificações ainda não comprovadas. Um teste isolado confirmou que algumas
evidências de atividades iniciadas são visíveis com RLS, mas não comprova que
os eventos sejam uma prova suficiente para liberar a transição. A experiência
de aceite único continua pendente, sem ligar fornecedores automaticamente.

Hoje o backend ainda verifica autorizações por fornecedor e finalidade em tabelas
distintas. Retirar seus botões sem substituir essas verificações impediria o uso;
nem pagamento nem aceite anterior as ativa automaticamente. A primeira entrega
deve registrar a versão nova, negócio, ator, horário e decisão, de forma
idempotente e auditável, e conectar esse registro aos controles existentes ou a
uma política interna equivalente. Os registros históricos e recusas anteriores
serão preservados; não remover tabelas ou colunas sem a aprovação ponto a ponto
já solicitada pelo usuário. Clientes existentes só mudam de condição após aceitar
a nova versão apresentada.

Para a jornada simples funcionar, a web deve substituir os controles separados
somente quando o backend tiver essa transição, incluindo tratamento de plano
inativo, patrocínio, troca de negócio, erro, replay e versão antiga. A ativação
de IA não implica que fornecedores ainda não conectados estejam funcionando:
a geração visual real permanece pendente da BL04.2.

Os controles internos de isolamento de negócios, gasto, idempotência, uso apenas
de materiais do negócio e aprovação da peça permanecem. Eles não são perguntas
para o cliente. O tratamento de pedidos de exclusão ou mudança durante processos
em andamento continua conforme a decisão anterior; a simplificação contratual não
implica apagar dados nem presumir que efeitos externos terminaram.

Antes de uso comercial, revisar o texto e as condições aplicáveis; aceite
versionado, por si só, não comprova que documentos preliminares estejam prontos
para contratação comercial. Homologação de fornecedores e da jornada continua
necessária.
