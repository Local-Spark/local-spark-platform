# BL03 — Acervo opcional em Sobre meu negócio

Atualizado em **28/10/2026**. Estado: BL03.1/BL03.2 implementadas localmente e verificadas; BL03.3 planejada.
Complementa a [trilha BL](BL-brand-library.md), o [SDD](../SDD.md) e a
[jornada completa de entrega](../design/delivery-roadmap-2026-10-27.md).

**Decisão posterior:** o cliente pode remover fotos desatualizadas deste
acervo, por exemplo após mudar a aparência da loja. Isso é diferente do histórico
de envios pelo WhatsApp, que deve ser preservado sem opção de exclusão
de texto, foto, áudio e vídeo. Essa preservação já está implementada para envios
associados, com `0058` aplicada localmente; não significa cadastrá-los
automaticamente como produtos, fatos ou memória pesquisável. Ver
[decisões vigentes](../DECISIONS.md).

## Resultado e limites

O proprietário pode cadastrar produtos, serviços, promoções e fotos reais do
item ou do espaço dentro de Sobre meu negócio. Tudo é privado, opcional e
progressivo; não exige plano ativo, kit escolhido ou preenchimento completo para
concluir cadastro/checkout. Sugerir começar por poucos itens, sem um catálogo de
ecommerce ou novo menu lateral. Nenhuma informação vira postagem nesta fase.

O acervo é fonte de contexto para BL04. Um pedido como “crie uma imagem
de um croissant” deve recuperar automaticamente o item e suas fontes; o cliente
não precisa escolher produto/serviço a cada pedido. Esse retrieval já existe no
worker experimental de desenvolvimento/teste da
[BL04](BL04-context-and-ai-production.md), desligado por padrão; geração visual
real integrada e qualidade ainda pendem. Não são entrega própria da BL03.
O cadastro não faz chamadas de IA nem exige Meta.

Fatos livres anteriores continuam em Informações e preferências. Não converter
texto livre em produto/preço silenciosamente. Antes da geração BL04, ligar fontes
e resolver conflitos entre fato e cadastro com pergunta quando houver divergência.

## Experiência web

A página `/app/context` reúne três seções:

1. **Informações e preferências:** contexto/fatos atuais, histórico e alteração
   de versão. O aceite único de IA fica em **Plano e acesso**; não há permissões
   por fornecedor ou modalidade nesta seção.
2. **Produtos e serviços:** criar e editar ficha, confirmar ou arquivar, ordenar,
   promoções separadas com período definido. O histórico de versões está na API;
   uma tela de histórico do catálogo não foi incluída nesta entrega. Foto pode ser
   anexada a um item confirmado. Serviço aceita duração e instrução de agendamento.
3. **Meu espaço:** fotos da fachada, balcão, sala ou ambiente, com nome, ordem,
   confirmação de direitos e estado. Não obriga vínculo com produto.

Usar o negócio ativo compartilhado. Ao trocar organização/negócio, descartar
formulário, seleção de arquivo e links privados da tela anterior. Conflito não
sobrescreve silenciosamente a versão nova; orientar recarregar e revisar. Retry
incerto mantém operação/payload originais. Loading, vazio, erros, foco e celular
seguem os componentes semânticos existentes. A confirmação manual distingue
rascunho de informação disponível para uso futuro pela IA.

## Catálogo e fonte factual

`Offering`: UUID, tipo `product|service`, nome, descrição, categoria, sinônimos,
ordem, estado `draft|active|archived`, moeda BRL e preço opcional em centavos.
Preço e `price_valid_until` (data) devem ser fornecidos juntos. Duração e forma de
agendamento só pertencem a serviços. Expiração de preço não transforma o item
em inexistente nem permite reutilizar a oferta vencida. BL04 resolverá validade
no fuso do negócio antes de uso.

`Promotion`: UUID próprio, item do mesmo catálogo, título/descrição, estado,
preço opcional e intervalo com início/fim e fuso explícito. Oferta ativa exige
item ativo. Confirmar promoção é decisão do dono; não há inferência por LLM.

O catálogo é um snapshot versionado com projeções normalizadas de itens e
promoções. O PUT inteiro cria/edita/ordena/arquiva atomicamente; IDs antigos
não somem por omissão. Arquivar preserva proveniência e vínculos de fotos.
Restauração exige revisão e nova gravação, sem reescrever versões anteriores.

Prefixo: `/api/v1/organizations/{tenant_id}/businesses/{business_id}`.

| API | Contrato |
| --- | --- |
| `GET /catalog` | Documento atual; versão zero e listas vazias antes do primeiro cadastro. |
| `PUT /catalog` | `operation_id`, `expected_version`, offerings e promotions; CAS, replay exato e auditoria. |
| `GET /catalog/history` | Até 50 versões recentes, com ator e data. |
| `GET /catalog/versions/{version}` | Snapshot imutável escolhido pelo proprietário. |

Erros de versão/operação são 409, versão ausente 404, payload inválido 422.
A resposta de um replay é a original, mesmo que a versão corrente tenha mudado.

## Fotos privadas e aproveitamento de WhatsApp

A foto pertence a um item **ou** a uma categoria do espaço, nunca aos dois.
Entrada por upload PNG/JPEG/WebP até 2 MiB, normalizada sem EXIF, com limites de
pixel/dimensão e corpo HTTP antes de parse. Guardar hash, origem, direito,
versão, destino e estado; não persistir URL assinada como identidade da foto.

| API sob `/collection/photos` | Contrato |
| --- | --- |
| `GET` | Fotos do negócio; estados internos de upload/exclusão não aparecem como arquivo pronto. |
| `POST` | Conteúdo base64, MIME, destino, título/ordem, operação e aceite explícito de direitos. |
| `POST /from-whatsapp` | Material de imagem pronto/autorizado do mesmo negócio, confirmação de direitos e cópia própria ao acervo. |
| `PATCH /{id}` | Metadata e active/archived, com operação e versão esperada. |
| `GET /{id}/url` | URL privada temporária, validade de até 120 segundos. |
| `GET /{id}/history` | Versões e ações do registro. |
| `DELETE /{id}` | Operação e versão; bloqueia novos links e inicia remoção recuperável do objeto. |
| `GET /removals` | Quantidade de remoções pendentes do próprio negócio. |
| `POST /reconcile` | Recuperação owner-scoped de intents/exclusões pendentes. |

A cópia não é uma referência ao objeto WhatsApp: copia bytes para chave própria
do acervo, sem baixar URL arbitrária do cliente. O envio associado é preservado;
remover a foto do acervo não oferece exclusão do envio original. Replay da promoção
recupera a operação anterior sem depender de o material original ainda existir.
Origem e hashes permanecem para rastreabilidade, sem expor object keys na web.

Estado interno e lease/fencing protegem IO interrompido e concorrente. Não fazer
upload/download/delete externo segurando row lock. A autorização e precondições
são verificadas novamente ao finalizar. Exclusão falha permanece recuperável e
não torna o objeto visível novamente. Links emitidos antes da remoção podem
funcionar até vencer; arquivamento não é exclusão física.

## Segurança, persistência e implementação

- Owner, tenant, negócio e membership válidos em todo acesso; staff não recebe
  leitura automática. FORCE RLS e roles restritas, sem schema por tenant.
- FK composta impede foto/promoção vinculada a item de outro negócio/tenant.
- Migração nova 0039: cabeçalho/versões do catálogo, offerings e promotions.
  Migração nova 0040: fotos, versões e intents de upload/remoção do acervo.
- Snapshot, projeções, versão e auditoria na mesma transação; sem workflow-recibo
  de CRUD. IO de mídia tem intenção durável e recuperação limitada ao proprietário.
- O correlator/LLM não recebe bypass ou acesso global às tabelas nesta fase.
  A leitura experimental BL04 já usa escopo próprio e snapshots das fontes,
  sem acesso global ao correlator/LLM.
- Biblioteca pública de kits é independente; não copiar fotos de cliente para ela.

## BL03.3 — Importação automática de fotos de cardápio (planejada)

Decisão do proprietário em 27/10/2026: a entrega atual é cadastro manual e fotos;
fica explicitamente prevista a leitura de fotos de cardápio/tabela de serviços
para extrair dados e preencher o acervo automaticamente. Esta extensão não está
implementada nem bloqueia a BL03.1/BL03.2 ou a primeira peça da BL04.

Fluxo futuro: dono envia uma ou mais páginas autorizadas → intent de importação
com orçamento → OCR/visão/extração estruturada → candidatos de itens/serviços,
seções, descrições, preços, tamanhos/variações/adicionais e condições que estejam
legíveis → fichas de acervo preenchidas como rascunhos → revisão resumida e
confirmação do proprietário. Não exigir redigitar os campos extraídos. Fotos de
produtos existentes no cardápio só viram mídia do acervo após revisar qualidade,
direitos e correspondência com o item; não gerar uma foto substituta como real.

Cada campo guarda página/região/fonte, texto observado e incerteza. Destacar
ilegível, preço inconsistente, unidade/variação ambígua e item repetido; não
prometer extrair o que não está visível. Validade ausente não é inventada:
guardar o preço extraído como candidato e pedir data/condição antes de confirmá-lo
como preço utilizável. Permitir aplicar a validade confirmada a um conjunto.

Reimportar não duplica fichas, não arquiva um item porque outra página faltou e
não sobrescreve alterações confirmadas posteriormente. Apresentar diferenças e
usar versão/CAS no aceite. Ausência de resposta não confirma dados. A mesma
capacidade atende lista de preços de salão, manicure e profissionais de serviço.

Executar como processo durável Temporal, com upload privado, operação idempotente,
ledger de todas as tentativas, limites de páginas/bytes/orçamento e recuperação
para chamada externa ambígua. Reaproveitar o contrato multimodal/custo da BL04;
escolher fornecedor/modelo em eval de menus PT-BR, tabelas, gírias e fotos ruins.
Critério de saída: uma foto legível preenche vários itens reais sem cadastro
manual, ambiguidades ficam evidentes e confirmação conserva isolamento e fontes.

## Aceite e verificação

Cadastrar produto e serviço, salvar rascunho, confirmar, alterar preço/validade,
criar/arquivar promoção, ordenar e arquivar item. Mostrar data de preço vencida
sem usá-la em geração. Fotos de item/espaço: upload, URL curta, mudança de
metadata/ordem, arquivamento e exclusão recuperável. Promover imagem WhatsApp com
aceite e comprovar cópia/replay independente da origem. Outro tenant/viewer/staff
sem propriedade não lê nem altera dados.

Testar replay, conflito de payload/versão, gravação concorrente, falha de audit
com rollback, validação de fotos/corpo, falha de armazenamento e lease vencida.
UI cobre troca de negócio, formulários opcionais, estados e uma jornada de
navegador. Integrações usam apenas banco `_test` e mídia sintética; nenhuma
chamada paga, publicação ou migração na base do usuário como parte dos testes.
Registrar gate final no CHANGELOG ao concluir a entrega.

## Estado ao concluir BL03.1 e BL03.2

Cadastro manual e fotos estão integrados localmente na API e na web. `make ci`
passou com **806 testes** e **100% de cobertura de linhas/ramos**; a web passou
**293 testes** com **100% nos quatro critérios**, build e jornada Chromium em
desktop/celular usando APIs simuladas. Em 27/10, após erro de consulta por banco
na versão 0037, as migrações 0038–0040 foram aplicadas ao desenvolvimento. O
catálogo do negócio informado foi consultado pelo serviço usando a role restrita
e RLS; API pronta e cobrança reconstruída. O bucket local está configurado no
`.env` de desenvolvimento. Um smoke com imagem sintética verificou upload,
leitura, URL temporária e remoção apenas do objeto de teste.

A evidência acima corresponde ao fechamento original de BL03.1/BL03.2.
Importação de cardápio (BL03.3) e geração visual real permanecem posteriores;
a consulta experimental do acervo já foi integrada na BL04. Fotos de entrada:
JPEG/PNG/WebP até 2 MiB;
o histórico do catálogo/fotos é oferecido pela API, sem tela de histórico nesta
fatia. A reconciliação de exclusão é acionada pelo proprietário e no próximo
upload; varredura automática global e política de capacidade permanecem F08.
A promoção de fotos reais do WhatsApp precisa da integração Meta homologada ou
de dados de teste; o teste de navegador usou dados e mídia fictícios.

## Coordenação posterior e decisões ainda por implementar

No modo visual simulado, criação/alteração/exclusão de fotos e mudanças do
catálogo podem aguardar trabalhos admitidos. A fila é durável, bloqueia novas
criações e preserva a prévia anterior para revisão. O autor pode descartar upload
incerto após lease; a chave fica privada em quarentena, sem limpeza física
automática. Outros escritores e casos de concorrência ainda precisam completar
a coordenação BL04. Não executar rede sob row lock.

Se o autor perder acesso, a recuperação da alteração pendente será exclusiva da
equipe da plataforma, por ação registrada/auditada; outro owner não assume a
pendência. Essa decisão está aprovada, mas o fluxo de staff ainda não existe e
não concede leitura irrestrita de mídia. Ver [registro](../DECISIONS.md).
A [versão anterior deste SDD](../history/2026-10-28-pre-documentation-reconciliation/phases/BL03-business-collection.md)
preserva o estado no fechamento da entrega original.
