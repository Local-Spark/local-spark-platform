# Uma organização por negócio

Decisão do proprietário em 28/10/2026: cada negócio terá sua própria conta de
cliente e organização. Negócios distintos, inclusive unidades de franquia,
usam contas separadas. Cada organização tem sua assinatura ou patrocínio e o
aceite de seu único negócio. A transcrição e os demais usos de IA integram o
serviço contratado.

## Situação atual

- O onboarding já cria organização e negócio juntos e registra uma inscrição
  por conta. O código local da API agora recusa um segundo negócio na mesma
  organização; o ambiente em execução precisa ser atualizado para receber essa
  mudança.
- Cobrança, checkout, eventos Stripe e patrocínio já são por organização. Com
  a regra garantida, podem continuar assim; não é necessário adotar o desenho
  anterior de acrescentar negócio às tabelas de cobrança.
- O aceite `0056` já é por negócio e foi aprovado para reaproveitamento; a
  integração do aceite único continua pendente.
- Inicialmente havia quatro organizações na base local: três com um negócio e
  uma com dois registros de teste. Após autorização do proprietário, os dois
  registros de teste e suas respostas de idempotência foram removidos em uma
  transação; a organização ficou sem negócio. O patrocínio histórico inativo,
  as auditorias e os eventos entregues e processados foram preservados. Foi
  criado um backup privado do PostgreSQL e sua restauração validada em base
  temporária. A migration foi aplicada à base local após aprovação posterior.
- Operadores e convites administrativos são independentes de cadastro de
  negócio; o modelo de um negócio por organização de cliente não exige que um
  operador crie negócio. Não se decide aqui a futura colaboração de usuários
  no mesmo negócio.

## Proteção aprovada e implementação

1. Fazer a API recusar a criação de um segundo negócio na mesma organização.
   Uma repetição com a mesma chave de idempotência deve continuar devolvendo a
   resposta original. Em criações concorrentes, somente uma pode ser concluída.
2. O proprietário aprovou preparar uma restrição de unicidade em
   `businesses.tenant_id`. A migration `0057_one_business_per_tenant` foi
   preparada e deve parar caso existam organizações com mais de um negócio,
   sem alterar esses dados. Ela foi aplicada ao banco local após aprovação
   específica. A
   restrição garante no máximo um negócio por organização; o onboarding cria o
   negócio junto com a organização em uma transação.

   A base local passou de `0050_visual_pending_changes` para
   `0057_one_business_per_tenant`; o endpoint de prontidão respondeu 200.
3. Simplificar a interface do cliente para a conta/negócio atual, preservando
   acesso a informações existentes enquanto a situação local anterior não for
   resolvida. Organização existente sem negócio deve ter recuperação definida;
   hoje pode ocorrer um redirecionamento entre seletor e onboarding.
4. Continuar o aceite único e testar que cobrança, patrocínio e acesso de uma
   conta não liberam outra. Essa simplificação não resolve automaticamente os
   registros antigos de autorização nem comprova a geração visual real.

A organização que tinha dois negócios de teste não os possui mais, após a
remoção autorizada; o histórico financeiro e as auditorias permanecem. As
migrations intermediárias foram aplicadas após revisão e aprovação.
Não cancelar, criar ou atribuir assinaturas automaticamente.

### Avaliação local solicitada: manter Local demo shop

Após avaliar `Local demo shop` e confirmar que os registros eram de teste, o
proprietário autorizou remover ambos os negócios de `Local demonstration`.
Eles não possuíam perfil, acervo ou mídia associados, nem proprietário com
conta de login. Os dois registros e as respostas idempotentes de suas criações
foram removidos. A organização e seu patrocínio revogado, quatro auditorias e
dois eventos entregues/processados foram preservados e conferidos.

Uma cópia privada do PostgreSQL foi criada antes da operação, restaurada em uma
base temporária e usada para validar a limpeza; ela não inclui mídia no
armazenamento de objetos nem estado do Temporal. A remoção e a migração foram
operações separadas, cada uma em sua própria transação.

As migrations intermediárias são 0051, 0053, 0054, 0055 e 0056. A 0055 verifica
exclusões de fotos sem resultado comprovado e pode marcar quarentenas; a 0054
mantém histórico, mas propostas antigas pendentes podem precisar de revisão.
As consultas anteriores à atualização não encontraram exclusões incertas nem
propostas pendentes. A [comparação de cada migration](local-migrations-0050-0057-review.md)
registra os efeitos e a aprovação da atualização local.

## Validação prevista

Testar cadastro, concorrência, idempotência, isolamento entre contas, Stripe
sandbox e patrocínio independentes, acesso do operador sem negócio e recuperação
de dados locais. Preservar históricos, trabalhar na base `_test` para testes e
não acionar serviços pagos durante a validação.

Resultado desta entrega: CI do backend passou com 1.530 testes e 100% de
cobertura, incluindo concorrência, replay, isolamento entre contas e preflight
da migration com duplicatas na base `_test`. A migration foi aplicada também no
ambiente local; isso não equivale à homologação comercial da cobrança.
