# Guia de QA local — cenários fictícios

Atualizado em **08/11/2026**. Guia de desenvolvimento, sem execução implícita.
Os três cenários originais de 28/10 continuam abaixo, com ligação ao quarto caso,
a cafeteria dos ensaios de motion. **Este guia não cria negócios nem fornece seed
automático**; artefatos dos ensaios não demonstram cadastro desses negócios. Usar dados sintéticos/autorizados, sem editar
negócio real ou publicar as peças. [SDD](../SDD.md),
[BL04](../phases/BL04-context-and-ai-production.md) e [decisões](../DECISIONS.md)
definem estado e critérios vigentes.

## Estado atual da jornada

| Capacidade | O que pode ser verificado |
| --- | --- |
| Conta/negócio/plano | Onboarding, um negócio por organização, aceite único em Plano e acesso, assinatura sandbox/patrocínio quando configurados. |
| Kit e acervo | Escolha/edição/histórico do kit demo; itens, promoções e fotos privadas do produto/espaço. Sem qualidade comercial homologada. |
| WhatsApp | Vínculo, processamento e histórico durável de todos os tipos associados; troca de número e destino novo cobertos na entrega simulada. |
| Intenção/retrieval | Jev e recuperação do acervo opcionais no worker dev/test, desligados por padrão. Não é memória geral ou conversa completa. |
| Visual fake | Prepara fontes, pedido/reserva e JPEG privado com kit e marca explícita de simulação; não chama gerador de imagem real. |
| Visual real | `visual_ai` está conectado localmente; uma imagem real privada de feed foi gerada no ensaio BL04.2. Fonte, credencial e orçamento explícitos continuam necessários; não é qualidade comercial comprovada. |
| Motion | Intensa/Dog/Luma são ensaios locais; o protótipo de inspeção/correção existe, mas a prova comparativa válida e a integração ainda estão pendentes. |
| Produção/revisão | Propostas, roteiro, prévias técnicas, candidata e decisão/publicação falsas; pedido de ajuste ainda não regenera. |
| Pendente | Qualidade BL04.3, ciclo de revisão por formato, jornada automática completa e proatividade BL05, prévia/ajuste/aprovação/download e WhatsApp oficial. Postagem Instagram é posterior. |

Há teste técnico local com Temporal/PostgreSQL e provedor/armazenamento falsos,
a partir de material já processado, até prévia fake e revisão. Ele não demonstra
webhook real nem o percurso completo manual. Não habilitar Jev ou OpenAI para
executar este roteiro básico: chamadas pagas exigem configuração e teto próprios.

## Dados dos cenários planejados

Os valores abaixo são inventados para QA. Antes do uso, criar negócios e mídia
com IDs próprios, permissões owner e sem perturbar o usuário ou negócio real.
Preços são exemplos de BRL. Para uma execução, fornecer validade vigente e uma
outra já vencida; usar fuso `America/Sao_Paulo` e horários com timezone. Não
atribuir o mesmo remetente WhatsApp a negócios diferentes sem validar as regras
do vínculo. O aceite único do serviço, os direitos da mídia e o acesso por plano são
verificações distintas. Usar conta/organização própria para cada negócio.

### 1. Ponto do Dog — loja física fictícia

Perfil: franquia fictícia com balcão, salão e retirada. Cores: vermelho escuro,
creme e amarelo. Tom descontraído. Produto principal: **Dog da Casa**, pão,
salsicha, molho e batata palha, R$ 19,90. Outros itens: **Dog Duplo**, R$ 25,90,
e **Refrigerante lata**, R$ 7,00. Oferta com datas explícitas: Dog da Casa e
refrigerante por R$ 24,90. Fotografar/gerar referências **fictícias**, coerentes
entre si: fachada, balcão/salão e cada item. Nome e preço não são prova de uma
franquia real. Testar: “Crie um post do Dog da Casa na nossa loja”; “Hoje o Dog
da Casa está R$ 19,90”; “Não quero divulgar o Dog Duplo”.

### 2. Dog em Casa — delivery fictício

Perfil: cozinha de produção e entrega, sem salão aberto ao público. Cores: azul
escuro, amarelo e branco. Produtos: **Dog Tradicional**, R$ 18,90; **Dog Cheddar**,
R$ 23,90; **Combo Duplo**, R$ 39,90. Oferta com validade explícita: Combo Duplo
por R$ 35,90. Referências fictícias consistentes: cozinha, embalagem fechada,
produto na embalagem e composição de cada item. Testar: “Mostre o Dog Cheddar
na nossa embalagem”; “Crie uma promoção do Combo Duplo”; “Qual o preço do Dog
Tradicional?”. Ausência de foto não autoriza inventar embalagem ou entrega grátis.

### 3. Estúdio da Luma — manicure fictícia

Perfil: profissional com espaço próprio e atendimento agendado. Cores: rosa
queimado, branco e areia. Serviços: **Manicure clássica**, R$ 35, duração 45 min;
**Esmaltação em gel**, R$ 65, duração 90 min; **Pé e mão**, R$ 65, duração
90 min. Oferta com validade explícita: manicure clássica por R$ 30. Referências
fictícias consistentes: espaço/mesa, materiais e resultado de cada serviço, sem
usar imagem identificável de pessoa real sem autorização. Testar: “Hoje tenho
agenda livre às 15h”; “Crie um story da esmaltação em gel”; “Não tenho horário
livre hoje”. Agendamento e disponibilidade não devem ser inventados.

### 4. Cafeteria — referência Intensa

O [caso fictício de cafeteria](../design/v0-motion-etapa-0-formatos-e-casos.md)
usa kit e material próprios do ensaio. **Intensa** identifica a referência
criativa, não um segmento ou cliente real. O [registro de validação motion](motion-registro-de-validacao.md)
conserva o feedback e a origem das peças. Usar os fatos e direitos congelados
no caso correspondente; não copiar preços dos cenários de alimentação acima.
A prova atual de revisão compara Intensa, Dog e Luma.

Os quatro cenários são exemplos para validação. O titular ainda não definiu
participantes reais e escolheu piloto por autoatendimento com cobrança; preço,
franquias, capacidade e início da operação dependem das próximas entregas.

## Passos manuais disponíveis

1. Inicie dependências/serviços conforme [ambiente local](../../README.md#ambiente-local).
   Reinicie API/workers após mudança de código/migration. Inicie a web do repo
   `local-spark-web`; confira `/health/ready`, Swagger, Temporal e Mailpit nos
   endereços configurados pelo README. Banco de teste deve ser dedicado `_test`,
   sem limpeza/migração da base de desenvolvimento para executar suíte.
2. Use owner de conta fictícia, organização/negócio próprios para cada cenário.
   Staff não é owner apenas por ser operador. Em **Plano e acesso**, confirme a
   versão do aceite único; verifique que não há checks por modelo/transcrição
   em WhatsApp ou Informações e preferências. Checkout sem aceite deve falhar,
   e replay do aceite não deve reativar permissões legadas ou ligar provedores.
3. Em **Kits visuais**, escolha/edite/confirme o kit disponível. Ele é ilustrativo:
   não constitui qualidade/direitos comerciais nem aprovação de publicação.
4. Em **Sobre meu negócio → Produtos e serviços**, adicione item com nome,
   categoria e descrição; preço/promoção precisam de validade explícita. Inclua
   foto sintética/autorizada de item e foto em **Meu espaço**. Confirme fatos
   variáveis em **Informações e preferências**. Um nome ativo/versionado de item
   já pode ser fonte do roteiro; nome não confirma preço ou alegação comercial.
   Confira isolamento usando outra conta/negócio de QA.
5. Confira separação do histórico WhatsApp e acervo: envios associados permanecem
   sem botão/API de exclusão para texto, foto, áudio e vídeo; foto desatualizada
   do acervo continua removível. Copiar foto ao acervo exige ação/direitos próprios.
   Trocar o número não muda tenant/negócio da origem; entrega fake aguarda o
   número novo ativo/verificado. Isso não afirma entrega real pela Meta.
6. Para o reconhecedor por regras, use o endpoint autenticado
   `POST /api/v1/organizations/{tenant_id}/businesses/{business_id}/editorial-conversation/simulate`
   com `operation_id` novo e “Hoje tenho agenda livre às 15h”. Esperado:
   `intent=availability`, `state=awaiting_confirmation` e pedido de confirmação.
   Negação deve cair em `unknown`/`needs_review`. Esse endpoint não chama Jev,
   envia WhatsApp ou gera imagem. Replay idêntico conserva decisão; mesmo UUID
   com texto alterado gera conflito. Confirme fatos somente no cenário fictício.
7. Quando houver prévia `visual_fake` criada pelo percurso técnico configurado,
   confira marca de simulação, kit, fontes e decisão privada. Não apresentá-la
   como imagem de IA real ou peça liberada para publicação. Em **Admin → Operação
   editorial**, acompanhe eventos/estados/tokens efetivamente existentes: não há
   custo monetário completo nem trace integral de prompts. Temporal mostra
   workflows iniciados, não cada CRUD da web.

## Critérios de regressão e extensões pendentes

C08/C09 abaixo já possuem implementação e testes no recorte local
`visual_fake`/`visual_ai`, conforme a [BL04](../phases/BL04-context-and-ai-production.md).
Devem orientar regressão e extensão ao renderer legado/motion, sem presumir
que o roteiro manual completo ou a futura integração já foram executados.
C10 continua adiado e os demais escritores conservam seus limites de cobertura:

- Plano vence depois da admissão: concluir a criação, permitir revisão privada,
  impedir novas criações e publicação até renovar (C08).
- Prévia e proveniência permanecem consultáveis sem expiração automática enquanto
  a conta estiver ativa (C09). URL temporária, validade factual e aprovação têm
  prazos próprios, sem equivaler à remoção do arquivo.
- Autor da mudança perde acesso: manter pendência explícita e resolver somente
  por staff autorizado, com ação registrada/auditada; outro owner não assume (C10).
- Demais escritores de contexto/kit/fotos/roteiro e estados incertos precisam
  seguir a coordenação; não presumir cobertura completa porque o fake cobre parte.

Retenção após encerramento foi adiada para essa fase, sem exclusão automática
nesta etapa. Franquias/quantidades dependem da medição BL04.3/F07.

## Roteiro completo futuro

Em BL04/BL05: entrada simulada → negócio identificado → briefing/fontes → prévia
privada com budget → comparação com produto/local/kit → ajuste versionado →
aprovação da peça → download. Postagem será uma etapa posterior, com autorização
própria. Incluir dia sem mensagem, preço vencido, oferta
ambígua, foto do acervo removida, kit alterado, negação, conta sem aceite e origem
insuficiente. Não usar retirada individual de IA como caminho de cliente.

Registrar operação, negócio, versões/fontes, esperado/observado, arte e revisão
humana, duração, uso/custo conhecidos, defeito e reprodução. Custo por peça aceita
inclui refações/descartes; beleza isolada não prova fidelidade ou faturamento.
WhatsApp real depende de homologação própria, sem bloquear mocks locais.
Instagram oficial não é condição do piloto inicial de geração e download.

OpenCode permanece candidato externo de investigação, sem instalação/integração.
O estudo anterior está no snapshot; sua eventual adoção exige versão, dados,
permissões e custo avaliados, sem substituir telemetria/testes do produto.

Versão anterior integral: [snapshot de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/evals/manual-qa-negocios-ficticios.md).
