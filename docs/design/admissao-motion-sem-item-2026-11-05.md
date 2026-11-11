# Próxima fatia durável: admissão motion sem item de catálogo

Proposta para implementação futura; não altera produto nem homologa o pipeline.

## Menor recorte revisável

1. Criar serviço de admissão chamado a partir de um evento WhatsApp já vinculado
   ao negócio, inicialmente protegido por configuração desativada. Ele recebe
   identidade da operação/origem, formato que tenha sido identificado com
   segurança e IDs de material associados pelo servidor. Não confiar em IDs,
   metadados, tenant ou hash fornecidos como autoridade pelo cliente. Reutilizar
   resolução de owner/contrato/plano e os leitores existentes; persistir um
   snapshot restrito e versionado em vez de passar texto, mídias ou credenciais
   pelo evento. Na ausência de candidato lexical, guardar estado explícito
   `sem_candidato_recuperado`, com item opcional: isso não prova ausência de item
   na mensagem, não cria fato e não seleciona um item. Um candidato efetivamente
   escolhido mantém proveniência, versão e revalidação próprias.
2. Associar uma gravação enviada ao pedido Reel/story, com metadados autorizados
   (ID, hash, tamanho, tipo e vínculo), e estado explícito de verificação
   pendente. Quando houver foto recebida para carrossel, tratá-la como material
   enviado, sem exigir foto ou item cadastrado para toda criação geral. Se faltarem
   gravação/fatos essenciais, pedir esclarecimento em vez de reservar ou chamar
   geração; se o material exceder 50 MiB/60s, pedir versão menor sem corte
   automático. Ingestão já limita tamanho/tipos (`material_media.py`); verificar
   bytes, duração e faixa de áudio pelo adapter `motion_media.py` em activity de
   IO fora de locks, nunca só por MIME/duração declarados. Revisar estado e
   fingerprint na transação de commit; se fonte mudou ou acesso/aceite expirou,
   invalidar a tentativa e não prosseguir.
3. O snapshot contém também versão/hash do kit e suas fontes autorizadas,
   fatos vigentes e origem/validade, referência aceita ou estado parcial/ausente,
   formato, skill resolvida por ID/hash e capacidade elegível. Não selecionar
   ficha de estilo deterministicamente nesta etapa: a direção decide mais tarde.
   Builder `motion_direction_input.py` é projeção de snapshot confiável, não
   mecanismo de autorização. Versão/hash de mídias e contexto devem ser
   revalidados imediatamente antes de cada efeito; armazenamento de conteúdo
   sensível usa mecanismo privado/cifrado e HMAC existente, não logs/outbox.
4. Na mesma transação, inserir estado inicial, operação idempotente, auditoria e
   evento outbox com apenas identidades necessárias. Mesmo operation ID + mesmo
   digest reconsulta resultado; mesmo ID com conteúdo diferente gera conflito.
   Leitura/repetição de evento usa UUID e fence duráveis, com recuperação de
   lease. O relay existente deve iniciar workflow Temporal com ID estável e
   política de duplicata; activity faz inspeção e persiste resultado idempotente.
   Fechar em `contexto_validado_sem_execucao` ou `esclarecimento_necessario`;
   não criar preview, cobrar, chamar modelo, expor fluxo ativo ou prometer MP4.
   O evento/worker deve estar gated, pois formatos e renderer ainda não estão
   ligados. Não iniciar publication workflow nem usar aceite legado.

## Locais de mudança esperados

- Migration sucessora do head corrente, sem editar migrations antigas: entidade
  de admissão/snapshot, IDs de origem e grupos/material, formatos motion
  explícitos, estado/versionamento/fingerprint, unicidade por tenant/operação,
  FKs tenant+business compostas e índices; RLS FORCE + permissões mínimas para
  owner e worker restrito. Opção preferível: entidade motion separada, pois o
  constraint `0042_editorial_briefings.py` obriga `catalog_snapshot` para prepared,
  e `0043_intent_usage.py` limita formatos antigos. Alterar essas tabelas pode
  exigir compatibilidade adicional com leitura histórica; não basta adicionar
  três strings. Sem renomear `short_video` histórico como se fosse `reel`.
- Serviço de domínio `motion_admission`/`motion_context` e schemas finos para
  operação, estado e resultado privado; reaproveitar `whatsapp_materials`,
  `visual_context`/service agreement e leitores de fatos/kit/referências apenas
  após extrair suas garantias comuns (o `visual_context` atual exige proposta
  aceita e photo/story; não chamá-lo como se admitisse motion). A rota manual,
  se necessária para observação e teste, precisa de owner e não deve ativar
  automaticamente os formatos. Para a jornada WhatsApp, integrar depois à
  activity existente, preservando respostas de esclarecimento com IDs próprios.
- Relay `services/outbox.py` e contrato `BusinessEvent` existente: acrescentar
  evento dedicado e dispatch gated para workflow novo de motion na mesma fila
  Temporal; workflow determinístico só organiza activities. Alternativa de usar
  dispatcher de propostas com lease depende de sua semântica e deve manter a
  obrigação de outbox transacional; não adicionar Celery/runner/banco paralelo.
- Worker/registro Temporal e testes de replay; activity consulta a operação e
  verifica material. No primeiro incremento, sem chamada paga, reserva de
  provider, transcrição remota, geração, render, revisão ou download. Cada uma
  dessas fases posteriores precisará de identidade/ledger próprios, efeitos
  idempotentes e recuperação de resultado incerto antes de habilitar fluxo.

## Fronteiras e questão prática de associação

`whatsapp_routing.material_group` usa janela fixa de dez minutos por remetente;
isso é agrupamento técnico, não prova de que tudo na janela seja um único
pedido e pode separar mensagens em fronteiras da janela. Não anexar vídeo de
outro pedido só pela proximidade temporal. Preservar vínculo explícito de origem;
se associação de texto e gravação não puder ser estabelecida com segurança ou
houver mais de uma gravação candidata, deixar pendente/esclarecer, sem escolher
arbitrariamente. Implementação precisa definir mecanismo de associação no
contrato existente e verificar como tratar eventos tardios e repetidos; uma
regra de produto adicional só é necessária se se pretender deduzir pedido a
partir de uma associação ambígua, não para manter estado seguro.

A interpretação também precisa receber o contexto do material efetivamente
associado: uma gravação acompanhada de “faça um story” deve poder ser reconhecida
como pedido de edição. Hoje o adapter Jev recebe mensagem, candidatos e formatos,
sem descrição separada de anexos. A integração deve acrescentar metadados
autorizados e limitados ao contrato de entrada, sem fingir que o modelo assistiu
ao vídeo ou converter silenciosamente `story` em `story_video`. Se o vínculo ou
a intenção continuar incerto, manter o esclarecimento. Os casos do ensaio usam
mensagens explícitas e não comprovam esse cenário da jornada.

## Testes e saída

- Unitários: formatos sem alias, sem candidato vs item resolvido, pedido geral,
  fatos insuficientes, skill/kit/referências indisponíveis, uma gravação vs zero
  ou múltiplas, tamanho/duração/corrompido e fingerprint/hash alterados,
  eventos tardios, repetição/colisão de operação e erro estável sem conteúdo.
- Integração DB `_test` com logins restritos: RLS tenant/owner/negócio,
  impedimento de IDs cruzados, auditoria+outbox atômicos, rollback e idempotência
  concorrente, revogação/alteração de contexto durante IO, duplicação do evento,
  perda de lease/fence e falha/recuperação após reinício do worker.
- Temporal local/fakes: replay determinístico, at-least-once sem duplicação,
  indisponibilidade ou reinício de worker e nenhum efeito externo sob transação.
  Verificar que nenhum aceite de peça ou evento de publicação é criado. Testar
  com mídia sintética, `make ci` e cobertura exigida; não usar dados de cliente.
- Saída da fatia: operação e snapshot verificáveis, observáveis somente ao owner,
  com estado honesto; ainda não é geração nem entrega v0. Revisão/ajuste/download
  seguem contrato separado `revisao-peca-sem-postagem-2026-11-05.md`, incluindo
  conjunto ordenado e aceite por versão; não converter aprovação em publicação.
