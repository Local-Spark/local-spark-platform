# Guia de QA local — três negócios fictícios

Atualizado em 27/10/2026. Este guia prepara cenários para o desenvolvimento e
distingue o que já pode ser exercitado do que ainda precisa ser implementado.
**A criação automática dos negócios e suas imagens ainda não existe.** Não usar
estes nomes, imagens ou preços como negócios reais nem publicar peças deles.

## Estado atual da jornada

- **Disponível localmente:** cadastro/perfil, seleção de negócio, kit de demonstração,
  catálogo manual, promoções e fotos privadas; simulador editorial restrito a
  desenvolvimento/teste; laboratório editorial e publicação simulada existentes.
- **Experimental:** briefing privado recupera acervo em teste com interpretador
  falso injetado. O worker normal não ativa essa interpretação e a tela Conteúdos
  só apresenta o resumo quando a API possui um briefing elegível.
- **Pendente:** conversa semântica com Jev/OpenAI no worker, busca automática do
  acervo na jornada normal, envio de esclarecimento, criação visual integrada com
  IA, envio de prévia ao WhatsApp e publicação real. Assim, não há hoje um teste
  manual verdadeiro da jornada completa de ponta a ponta. A BL04.1 fecha a
  interpretação/contexto; BL04.2 gera a prévia; BL04.3 mede qualidade; BL05
  fecha WhatsApp simulado, revisão e publicação falsa.

## Dados dos cenários planejados

Os valores abaixo são inventados para QA. Antes do uso, criar negócios e mídia
com IDs próprios, permissões owner e sem perturbar o usuário ou negócio real.
Preços são exemplos de BRL. Para uma execução, fornecer validade vigente e uma
outra já vencida; usar fuso `America/Sao_Paulo` e horários com timezone. Não
atribuir o mesmo remetente WhatsApp a negócios diferentes sem validar as regras
do vínculo. A autorização de IA e direitos da mídia são independentes de plano.

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

## Passos manuais que são possíveis agora

1. No backend, inicie as dependências e serviços conforme [README](../../README.md#ambiente-local).
   No VS Code reinicie a configuração **Meu Braço Direito: API (FastAPI)** quando
   código ou migrações mudarem. Inicie o frontend com `npm run dev` no repositório
   `local-spark-web`. Confira web `http://localhost:5173`, Swagger
   `http://localhost:8000/docs`, Temporal `http://localhost:8233` e Mailpit
   `http://localhost:8025`. Se `/health/ready` não estiver saudável, não prossiga.
2. Entre com um usuário **owner** dos negócios fictícios; acesso de operador/admin
   por si só não concede acesso de proprietário ao acervo. Hoje os três cenários
   não foram criados e não existe rotina de seed para eles. Use dados de teste
   apenas em ambiente local; não altere um negócio real para simular os exemplos.
3. Selecione o negócio ativo. Em **Kits visuais**, selecione/edite e confirme o
   kit de demonstração disponível. Ele é ilustrativo: não é um kit comercial
   aprovado nem prova que a peça futura usará a identidade.
4. Em **Sobre meu negócio → Produtos e serviços**, use **Adicionar produto ou
   serviço**; preencha nome, categoria, descrição e preço com data de validade,
   confirme o item e depois use **Adicionar promoção**. Em **Adicionar foto de
   um item**, associe imagem sintética/autorizada ao produto ou serviço.
5. Em **Sobre meu negócio → Meu espaço**, use **Adicionar foto do espaço** e
   escolha a parte do local. Em **Informações e preferências**, confirme fatos
   comerciais pertinentes e suas datas de validade; hoje o roteiro ainda exige
   fato editorial separado do catálogo. Salve e teste trocar de negócio: os
   produtos e fotos não devem vazar para outro negócio.
6. Para testar o reconhecedor limitado, no Swagger autentique-se com sua conta
   de teste e use `POST /api/v1/organizations/{tenant_id}/businesses/{business_id}/editorial-conversation/simulate`.
   Envie um `operation_id` UUID novo e, por exemplo, o texto “Hoje tenho agenda
   livre às 15h”. Esperado: `intent=availability`, `state=awaiting_confirmation`
   e uma resposta pedindo confirmação. A negação “Não tenho agenda livre hoje às
   15h” deve cair em `unknown`/`needs_review`. Este endpoint é um ensaio por
   regras, não envia WhatsApp, não chama Jev nem gera imagem. Repetir a mesma
   operação e payload devolve a mesma decisão; mudar o texto mantendo o UUID
   deve gerar conflito. Somente confirme fatos no negócio fictício.
7. Em **Admin → Operação editorial**, o operador autorizado pode acompanhar
   estados, eventos e tokens quando houver operações editoriais reais no ambiente;
   não há ali trace completo de prompts/respostas nem custo monetário completo.
   O Temporal mostra workflows efetivamente iniciados, não todas as ações da web.

## Roteiro futuro de ponta a ponta — ainda não disponível

Quando BL04.1/BL04.2/BL05 forem integradas: enviar ou simular mensagem, confirmar
recepção e identificar o negócio; verificar briefing e fontes; gerar prévia
privada com orçamento; comparar imagem com produto, local, embalagem e kit;
solicitar ajuste ou aprovar; verificar publicação **falsa**, replay e estados
incertos; inspecionar eventos, duração, uso e custo observado por tentativa.
Repetir para os três negócios, incluindo preço expirado, oferta ambígua, foto
revogada, mudança do kit, negação e ausência de autorização. Com a Meta restrita,
usar somente entrada simulada local; não alegar que já houve WhatsApp real.

Para cada caso registrar: ID da operação, negócio fictício, cenário e versão de
fontes, estado esperado/observado, arte produzida e revisão humana, dados de
uso e custo efetivamente conhecidos, defeito e passos de reprodução. Avaliar no
celular legibilidade, identidade, texto/preço literal e fidelidade ao produto e
ambiente; beleza isolada não é aprovação. O custo por peça aceita inclui todas
as tentativas, não só a última chamada. Não prometer venda ou faturamento.

## OpenCode como ferramenta de investigação

[OpenCode Server](https://opencode.ai/docs/server/) expõe sessões, mensagens e
stream de eventos via HTTP; o [SDK](https://opencode.ai/docs/sdk/) é JS/TS e o
backend Python poderia acessar HTTP. A API, nomes e características dependem da
versão instalada. Pode apoiar QA como ferramenta externa: ler specs, propor casos,
conduzir ações autorizadas contra ambiente de teste, resumir eventos e abrir
relatório. Um evento/sessão do OpenCode descreve o agente, não substitui traces
end-to-end instrumentados no produto nem prova que a publicação aconteceu.

Não está instalado/integrado pelo simples registro desta ideia. Antes de um
spike: dados fictícios, credenciais de teste limitadas, sem acesso a `.env` de
produção, permissões restritas, servidor local/autenticado, controles e teto de
custos, output reprodutível, captura de versão/modelo/latência e avaliação por
resultado verificável. Evitar liberar shell, gravação, rede ou publicação sem
necessidade. Os [controles de permissão](https://opencode.ai/docs/permissions/)
são configuráveis. Comparar com scripts, pytest/Playwright e um runner direto
com os mesmos casos; não presumir ganho de custo ou qualidade.
