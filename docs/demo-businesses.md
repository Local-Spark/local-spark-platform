# Cadastros locais de demonstração — 16/11/2026

A pedido do administrador, a base local habitual `meu_braco_direito_platform` foi
limpa **sem backup**. Foram removidos os dez negócios anteriores e as dezesseis
outras contas; a identidade administrativa existente foi preservada, incluindo
senha, MFA e sessões. O resultado contém quatro contas: o administrador e três
identidades fictícias comuns, sem privilégio administrativo.

| Negócio | E-mail fictício | Catálogo | Acervo | Referências indicadas |
| --- | --- | --- | --- | --- |
| Café Aurora | cafe.aurora@example.test | 5 produtos + 1 serviço | 8 fotos | coffeelab_br, sternacafe |
| Ateliê Lia Nails | lia.nails@example.test | 6 serviços | 8 fotos | opibrasil |
| Vértice Seminovos | vertice.autos@example.test | 3 veículos + 3 serviços | 8 fotos | webmotors |

Cada negócio tem endereço declarado, descrição, cidade/UF/IBGE, dez fatos,
preferências editoriais, termos de busca, horários, CTA, preços em reais com
validade, uma promoção temporal, durações/agendamento para serviços, marca
vetorial original com PNG, paleta, tipografia e kit confirmado. Das oito fotos,
duas mostram ambientes e seis estão associadas aos itens. São quinze imagens
originais distintas, reutilizadas onde o assunto é compatível. Não são 24
fotografias exclusivas.

Os dados comerciais, preços, endereços e estoque são **fictícios**. Preços e
horários têm validade até 28/02/2027; promoções de novembro terminam em 01/12/2026,
00h de São Paulo. A preferência de três posts por semana não implementa quota.
As fotos são de banco e recebem identificação de imagem ilustrativa no acervo;
não comprovam instalações, portfólio ou estoque desses negócios.

## Como consultar e alternar

1. Entrar com a conta administrativa habitual e clicar em **Ver meu espaço**.
2. No seletor **Organização**, escolher um dos três negócios.
3. Abrir **Sobre meu negócio** (`/app/context`): abas **Informações e
   preferências**, **Produtos e serviços**, **Meu espaço** e **Referências**.
   As fotos de itens ficam no catálogo; as de ambiente, na aba Meu espaço.
4. Abrir **Kits visuais** (`/app/kits`) para consultar/personalizar a marca.
5. Voltar ao **Laboratório administrativo** (`/admin/creation-lab`) para escolher
   o negócio e fazer pedidos, com teto de gasto definido por ensaio na UI.

Recarregar a página para atualizar as organizações da sessão. Não é preciso
entrar com os e-mails fictícios: essas identidades têm senha nula e não receberam
e-mail de ativação. O onboarding local marca o e-mail fictício como confirmado
apenas para construir o cenário; não representa verificação externa.

A conta administrativa recebeu associação explícita de proprietário nas três
organizações demonstrativas. O seletor já existia no front; nenhuma tela detalhada
foi adicionada ao laboratório. Isso não concede acesso implícito a negócios de
clientes, não altera a política RLS e não habilita o laboratório para clientes.

## Preparação e evidências

- Cadastros criados pelos serviços existentes de onboarding, catálogo, contexto,
  endereço, kit, acervo, referências, aceite de IA e cortesia comercial, usando o
  papel restrito com contexto de tenant/ator. Auditoria e eventos dessas operações
  foram persistidos. O aceite foi registrado pelo administrador nos cenários
  fictícios. Cortesias não representam pagamento e não criam checkout.
- Bootstrap privilegiado limitado à limpeza local, preservação da conta e vínculos
  administrativos explícitos. Limpeza transacional com tabelas temporárias,
  sem arquivo recuperável nem `TRUNCATE ... CASCADE`. Esquema e tabelas de tarifas/
  políticas globais preservados. Não houve migração nem alteração de banco de teste.
- Consultas pelos serviços de sessão e laboratório confirmaram as três organizações
  e os três negócios visíveis para o administrador. Leituras com papel restrito
  confirmaram seis itens, uma promoção, oito fotos e kit confirmado por negócio.
  Totais: quatro contas, três organizações, três negócios, um administrador,
  três aceites, três cortesias, quatro referências e nenhum e-mail na fila.
- Nenhum teste automatizado, `make ci`, build, typecheck ou geração paga foi
  executado, conforme solicitado. A navegação/generation end-to-end será exercitada
  pelo administrador. As marcas SVG foram apenas renderizadas para upload PNG.
- Consumers antigos de worker, cobrança e e-mail foram parados para a limpeza;
  não havia workflows abertos nas duas filas deste projeto para encerrar.
  Somente o worker exclusivo do laboratório deve ser usado nesta rodada.
- O armazenamento de objetos e o histórico interno do Temporal não foram apagados
  indiscriminadamente: são infraestrutura separada da limpeza relacional. Objetos
  antigos sem referência podem continuar ocupando espaço, mas os cadastros antigos
  não aparecem mais no produto. Não foi criada cópia dos registros removidos.

## Limitações reais identificadas

- O catálogo possui **um único kit-base**, `cafe-pausas/v1`. Cada negócio tem seu
  próprio logo, nome, cores, fontes e textos, mas os layouts disponíveis são os
  mesmos. A preparação não cria três famílias de templates independentes.
- O acervo permanente aceita fotos. Vídeos-fonte para reels continuam sendo anexados
  ao pedido do laboratório. Não foi simulada a existência de clipes no acervo.
- Os perfis de referência estão indicados e selecionados, sem coleta nem análise
  paga do feed. Não foi inventado aprendizado visual do modelo. A busca configurada
  é local, raio de 5 km com origem manual em São Paulo/bairro; não é geocodificação
  verificada. A opção nacional do schema legado é recusada pelo serviço vigente.
- Veículos não têm campos estruturados específicos para ano, km, câmbio e combustível;
  os dados de demonstração estão nas descrições. Marca/versão, laudos, garantias e
  financiamento permanecem sem confirmação para exercitar perguntas factuais.
- Telefones são placeholders sem verificação. WhatsApp, Instagram, pagamento,
  geocodificação e publicação não foram conectados nem falsamente confirmados.
  URLs `.test` são destinos fictícios; não enviam pedidos a estabelecimentos reais.
- Falta um campo próprio de proveniência/licença no cadastro de fotos: nesta carga,
  a origem aparece no título e no manifesto versionado. Também não há flag global
  de negócio demonstrativo; descrição e fatos identificam o cenário.

## Origem das imagens e referências

As imagens foram baixadas do [Pexels](https://www.pexels.com/license/), cuja licença
permite uso pessoal e comercial. A lista de páginas, URLs, tamanho e SHA-256 está em
[`media.json`](../scripts/fixtures/demo-businesses/media.json). O uso aqui é
ilustrativo em ambiente local, sem alegar endosso de pessoas ou marcas retratadas.
As marcas dos três cenários foram criadas em SVG; não são logotipos copiados.

Perfis de inspiração consultados: [Coffee Lab e Sterna](https://vivaacidadenews.com.br/gastronomia/cafes-diferentes-para-provar-em-sao-paulo/),
[OPI Brasil](https://www.instagram.com/opibrasil/) e
[Webmotors](https://www.instagram.com/webmotors/). A indicação não concede direitos
sobre fotos desses perfis; as imagens carregadas vieram do Pexels.

## Manutenção dos cenários

`PYTHONPATH=. .venv/bin/python scripts/seed_demo_businesses.py --admin-id <UUID>`
retoma a carga pelas mesmas identidades de operação, sem limpar novamente.
Fotos ausentes são baixadas das URLs fixas do manifesto, limitadas a 2 MiB e
verificadas por hash; SVG/PNG e dados declarativos estão versionados. Mudança no
conteúdo externo exige revisão do manifesto, nunca aprovação silenciosa.

**Somente para nova limpeza expressamente solicitada**, parar consumidores e
verificar workflows das filas deste projeto; acrescentar
`--reset --confirm-database meu_braco_direito_platform`. A ferramenta exige ambiente
`development`, PostgreSQL em loopback, mesma base de runtime/migração, administrador
ativo igual ao operador configurado do laboratório e revisão exata `0129` para
reset. Não serve para produção, staging ou testes. Não gera backup. Não editar
fixtures e reaplicar sobre cenários usados esperando sobrescrita silenciosa: os
serviços preservam idempotência e recusam payload divergente.

Não é necessário executar essa ferramenta para testar peças: ela foi usada apenas
para preparar os cadastros. Os ensaios continuam sendo feitos pela UI.

## Conferência dos logos e do acervo — 16/11/2026

Os três logos originais já estão vinculados aos respectivos kits confirmados.
Leitura do armazenamento confirmou arquivos disponíveis e hashes íntegros; não
foram substituídos. Os três negócios mantêm oito fotos prontas/ativas cada, incluindo
duas de ambiente. O problema do pedido institucional era a passagem do acervo para
o gerador, não ausência dos arquivos. O fluxo comum passou a incluir uma foto de
ambiente autorizada mesmo sem produto selecionado.
