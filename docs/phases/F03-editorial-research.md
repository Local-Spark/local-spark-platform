# F03 — Contexto, roteiro, pesquisa e planejamento proativo

Atualizado em **28/10/2026**. Estado: contexto e propostas/roteiros versionados
implementados localmente; qualidade comercial, cadência proativa e pesquisa ampla
pendentes. Dependências: F01/F02. Este contrato segue o [SDD geral](../SDD.md), a
[trilha BL](BL-brand-library.md) e o [registro de decisões](../DECISIONS.md).
O [snapshot anterior integral](../history/2026-10-28-pre-documentation-reconciliation/phases/F03-editorial-research.md)
preserva as entregas F03.1–F03.3b, avaliações, contagens e escolhas datadas.

## Experiência e separação das decisões

Pedido livre pelo WhatsApp é o percurso principal. **Conteúdos**, em
`/app/content`, acompanha propostas/prévias e oferece revisão complementar.
`/app/ideas` redireciona para Conteúdos. Geração manual de ideia, edição/aceite de
roteiro e controles do renderer ficam em `/app/editorial-lab`, somente no build
DEV. Esses endpoints e versões sustentam também a jornada automática.

IA integra o serviço aceito uma vez em **Plano e acesso**, cobrindo texto,
imagem, interpretação/Jev e transcrição. Informações e preferências não contém
permissões por fornecedor. Registros antigos são compatibilidade, sem reescrita;
após o contrato, APIs legadas de mutação recusam alteração. Plano, membership,
direitos e orçamento permanecem verificações internas. Aceite do serviço,
confirmação de fato, escolha do kit, revisão de roteiro e aprovação de publicação
não se substituem. Silêncio nunca aprova publicação.

## Contexto e fontes implementados

`BusinessContext` separa até 20 fatos, preferências e hipóteses. Fatos têm origem,
tipo e validade; preço, oferta e horário exigem validade. Texto livre, áudio
transcrito, pesquisa ou aprovação de uma peça não viram fato confirmado por
inferência. Preferências explícitas e sinais de estilo também são distintos.

`GET/PUT /editorial-context`, histórico e restauração são owner-scoped. Mutação
exige `operation_id` e `expected_version`, CAS, versão imutável e auditoria no
mesmo commit. Replay idêntico retorna versão original; conflito de payload ou
versão retorna 409. Restauração cria nova versão e não apaga o passado. A web
permite edição e correção; `posts_per_week` histórico permanece, mas o controle
manual de frequência não aparece na jornada vigente.

BL02 já permite escolher/editar/confirmar kit, e F03 congela o documento exato
confirmado na nova proposta. Execução tardia não troca silenciosamente de kit.
BL03.1/BL03.2 já entregam catálogo e fotos opcionais/privados; importação de
cardápio é BL03.3 posterior. O worker experimental BL04 já pode recuperar fontes
seletivamente e interpretar com Jev em desenvolvimento/teste, desligado por
padrão. Não é somente um helper com intérprete injetado, nem uma integração
comercial homologada. Correspondência lexical oferece candidatos e exige
esclarecimento diante de ambiguidade ou negação.

Todos os envios WhatsApp associados são preservados sem TTL e sem exclusão no
histórico (`0058` aplicada localmente). Isso não implementa memória completa,
resumo automático, skill executável ou treinamento por negócio. Recuperar só
fatos atuais e material pertinente continua necessário; guardar tudo não reduz
tokens por si só. Fotos desatualizadas do acervo podem ser removidas.

## Propostas e roteiro implementados

Proposta tem identidade durável por negócio/operação, snapshot do contexto e
origem opcional. Dispatcher usa lease/fencing e workflow Temporal determinístico
por pedido; replay não duplica chamada. `baseline-v1` produz resultado local;
OpenAI Responses é opcional/configurável, com saída estruturada, `store=false`,
sem tools e limite de saída. O default de código `gpt-5-mini` não é escolha
homologada de modelo para produção. Revalidar contrato, disponibilidade e tarifas
antes de qualquer troca ou ativação; avaliações antigas não garantem dados atuais.

O ledger reserva tokens por tenant/dia antes da submissão; efeito incerto mantém
prova e não é reenviado automaticamente. A época contratual distingue novos
pedidos daqueles criados sob permissões antigas, evitando que o aceite único
reviva fila legada. Fonte, fato, contexto, acesso e direitos são revalidados.
A integração real de imagem continua na [BL04.2](BL04-context-and-ai-production.md).

O roteiro estruturado tem até três cenas, formato, abertura/CTA, IDs de fatos e
materiais. O serviço monta a afirmação factual a partir do fato vigente exato;
o modelo não confirma alegações livres. Item ativo/versionado pode fornecer nome,
mas alegações no nome, preços e promoções precisam das fontes adicionais
aplicáveis. Foto/vídeo pode ser cena de material; texto/áudio é referência, sem
fingir que seja imagem. Falta de fonte exige pergunta/revisão antes do gasto.

`POST/GET /editorial-proposals/{id}/script-versions` permite edição com CAS,
`operation_id`, hash, autor e auditoria. Preserva ordem/formato/fontes e texto
factual, recusa padrões explícitos de alegações novas sem fato. Esse filtro não
prova verdade semântica em toda linguagem natural. Nova versão zera revisão
anterior; aprovação da peça final não migra para outro hash. Pedido de ajustes
registra observação, mas ainda não gera automaticamente uma nova versão.

## Mudanças em andamento e pendências aprovadas

O modo visual simulado já coordena parcialmente mudança/restauração do contexto,
catálogo, confirmação do kit e fotos do acervo: bloqueia novos inícios, cancela
fila não admitida e espera trabalhos iniciados. Preserva a prévia anterior para
revisão com indicação da mudança. Outros escritores e transições de plano/acesso
não têm coordenação integral; o provedor visual real continua isolado.

**Decisões aprovadas, ainda por implementar:** criação iniciada deve concluir
mesmo se o plano vencer; owner continua podendo revisar a prévia privada, sem
novas criações ou publicação até renovar. Prévias geradas não terão expiração
automática enquanto a conta estiver ativa. Hoje propostas/prévias ainda têm
`expires_at`, limpeza e gates de plano que precisam ser ajustados. Validade de
fatos, aprovação e URL assinada curta continuam independentes de guardar o arquivo.
A retenção após encerrar conta foi adiada para a fase de encerramento, sem criar
limpeza automática nesta etapa.

Se o autor de uma alteração pendente perder acesso, a recuperação será exclusiva
da equipe da plataforma, com ação registrada/auditada; outro owner não assume a
pendência. Esse fluxo ainda precisa de implementação e não concede leitura
geral de mídia privada ao staff.

## Proatividade e pesquisa: planejadas

O produto deve ser útil sem pedido diário. Antes do piloto, BL05 precisa ligar
agenda por negócio/fuso ao mesmo briefing/roteiro e às mesmas prévias, dentro da
franquia do plano e da cadência aceita. Deduplicar tema/peça, verificar fatos,
direitos e orçamento; pedir foto/confirmação quando não houver fonte suficiente.
Permitir pausar, reduzir e revisar o ritmo. Sugestão de IA não amplia plano nem
cria cobrança. A cadência automática ainda não está implementada.

Após a preparação e avaliação simulada das skills de feed/story, pesquisar
referências indicadas pelo cliente e descobrir automaticamente negócios semelhantes
em destaque; ambas as origens alimentam uma biblioteca de padrões a avaliar antes
do uso na criação. Não é necessário fechar primeiro o gate comercial BL04.3.
Os critérios de semelhança, fontes/alcance e métricas dependem de estudo; Jev é
uma hipótese, não decisão de fornecedor ou fonte de dados. Cidade/UF não comprova
endereço/coordenadas. Fonte pública não concede direitos, métricas privadas ou
causalidade de vendas. Pesquisa externa é hipótese com fonte/período/incerteza,
nunca instrução confiável do modelo ou fato confirmado. Não há pesquisa automática,
skills editoriais integradas, agente geral, tools arbitrárias ou treino automático.
Fases e gates em [skills e referências](../design/skills-e-referencias-editoriais.md).

## Qualidade, operação e validação

Avaliações sintéticas históricas encontraram linguagem promocional sem fato e
resultaram em **não ativar comercialmente**. Guardas posteriores limitam a
superfície factual, sem demonstrar utilidade/qualidade comercial. O runner
`scripts.evaluate_editorial` e os corpora PT-BR produzem relatórios/revisão humana;
chamadas reais exigem orçamento e escopo explícitos. Comparar baseline e modelos
com o mesmo corpus em erro factual, abstenção, utilidade, correções, latência,
tokens e custo por roteiro aceito. Um erro crítico bloqueia o lote.

Admin local já tem projeções restritas/auditadas de operações, eventos e consumo
editorial, sem prompt ou material privado. `estimated_cost_minor=null` significa
custo desconhecido; tokens não são reais faturados. Timeline integral de webhook
à publicação, tarifas versionadas, feedback e COGS seguem pendentes. Acesso de
suporte ao conteúdo exige caminho separado e escopo auditado, não leitura global.

Manter testes significativos de RLS, replay/CAS, concorrência, snapshot, fonte
inválida, fato vencido, orçamento e resultado incerto. Serviços locais `_test` e
Temporal; mocks externos sem conteúdo de cliente. A história de 417–444 testes,
avaliações de 23–26/10 e entregas de roteiro está preservada no snapshot;
validações agregadas recentes estão no [CHANGELOG](../CHANGELOG.md).
