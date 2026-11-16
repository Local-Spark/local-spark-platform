# Fluxo único de criação por mensagem

## Decisão e escopo

O administrador exige que laboratório e produto compartilhem o processamento de
mensagens, incluindo feed, story e reel. As diferenças permitidas são autenticação,
pagador, persistência privada, entrada e entrega. A UI não escolhe formato, catálogo,
fotos do acervo nem pausas criativas exclusivas do administrador.

A implementação de 16/11/2026 conecta novas mensagens de ambos os canais a
`MessageCreation`, pelo mesmo `CreationLabProductionWorkflow`. Os nomes físicos
`creation_lab_*` foram preservados para compatibilidade de históricos; não indicam
mais um algoritmo alternativo para mensagens produtivas. `origin` e `flow_version`
são imutáveis. Não é apenas reutilização do provedor ou do prompt.

## Caminho implementado

1. WhatsApp autentica/correlaciona e normaliza o material existente. A atividade
   `request_message_creation` cria uma execução vinculada ao evento real e ao
   proprietário do canal. O laboratório cria o mesmo contrato a partir de um
   rascunho privado e do anexo enviado. Não fabrica canal, remetente ou proprietário.
2. Ambos enfileiram a identidade durável `creation_lab.requested` no outbox e
   executam o coordenador comum no worker dedicado Temporal. Nenhuma chamada de
   modelo ocorre na rota HTTP ou dentro de transações com locks.
3. Áudio passa pela mesma normalização/transcrição e reserva antes da chamada;
   transcrições anteriores concluídas são reutilizadas. Texto e legenda seguem
   para `resolve_catalog_context`, com os mesmos critérios conservadores de
   seleção, ambiguidade, negação e recaptura do catálogo. Jev recebe os três formatos.
4. O formato é identificado pela mensagem. Sem formato explícito, vídeo implica
   reel, imagem implica feed e texto implica story. Formato não suportado,
   informações insuficientes ou reel sem vídeo produzem perguntas. Não existe
   confirmação administrativa adicional do catálogo. Sem correspondência, pode
   usar os fatos e a marca confirmados, sem inventar um item.
5. Feed/story passam pelo mesmo serviço editorial/visual, com referências do
   catálogo e revalidação de contexto antes dos efeitos. Reel passa pelo
   `MotionOrchestrator` produtivo, com o contrato normal de `MotionRequest`, sem
   forçar preparação, storyboard ou aprovação apenas no laboratório.
6. Perguntas suspendem a execução. Respostas e ajustes produzem uma continuação
   identificada, com pedido composto, vínculo ao conteúdo anterior e saldo
   restante. Não repetem operações pagas nem renovam o orçamento. WhatsApp exige
   referência explícita a uma mensagem do mesmo negócio/remetente; não associa
   uma mensagem nova à última pergunta por suposição.
7. O laboratório mantém versões/anexos privados, trace e SSE. A origem WhatsApp
   projeta o resultado em `content_pieces`, disponível na revisão existente, e
   registra perguntas/resultados para o proprietário. A entrega WhatsApp permanece
   **simulada**, como a integração anterior; recibos são identificados como locais.
   A aprovação visual continua na revisão de versão exata; comandos isolados de
   aprovação/descartar não são transformados em nova geração paga.

## Autorização e custos

- API do laboratório tem dependência explícita de acesso exclusivo ao administrador
  configurado, além da autorização dos serviços. Um cliente proprietário não ganha
  acesso à API administrativa por ter uma execução produtiva.
- RLS de execução produtiva exige proprietário ativo, ator e identidade interna da
  execução. O escopo não vem de header do cliente. Referências produtivas usam o
  leitor produtivo; o administrador usa a capacidade de leitura já restrita.
- WhatsApp revalida plano, aceite, canal, origem e validade dos materiais antes dos
  efeitos. O laboratório mantém a exceção autorizada de plano e orçamento separado.
- Efeitos produtivos reservam no ledger comercial, com teto mensal por negócio e
  teto global OpenAI; Jev também mantém a reserva diária. Efeitos administrativos
  não escrevem nesses ledgers. Estimativa não vira fatura: valores desconhecidos
  continuam reservados. Estimativa acima da reserva aumenta a exposição nos tetos
  comercial/global sem registrar uma fatura fictícia. A configuração comercial
  não é habilitada pelo laboratório.
- O teto do ensaio é único por peça, informado na UI. Transcrição, interpretação,
  imagem e vídeo consomem esse mesmo saldo; não há cotas por etapa para o usuário.
  A reserva de áudio é calculada internamente pela duração, arredondada para cima
  em minutos, usando a tarifa documentada de US$ 0,0045/minuto do modelo existente
  `gpt-transcribe`, conferida em 16/11/2026. A versão da tarifa fica no trace.
  Fonte: https://developers.openai.com/api/docs/models/gpt-transcribe.md.
  Credenciais/habilitação do provedor continuam obrigatórias, sem ativação comercial
  causada pelo laboratório.
- Apenas o anexo ativo compõe a mensagem. Antes de iniciar, novo upload substitui
  o anterior; arquivos antigos permanecem disponíveis no histórico. Upload
  indefinido impede outro envio. Anexos herdados seguem para a continuação; um novo
  material de resposta pode substituí-los. Áudio já transcrito não é cobrado outra
  vez numa resposta textual.
- Trace expira sete dias após o encerramento. Anexos, peças, auditoria e custos
  permanecem. Texto original/transcrição são entrada do pedido, não trace de modelo.

## Compatibilidade e operação

Migrações aditivas `0130_message_creation_scope` e `0131_message_creation_funding`
aplicadas somente ao PostgreSQL
local habitual, após conferir que havia apenas um rascunho e nenhuma execução
ativa. Novos rascunhos usam `auto`/`automatic`/versão 2. Rascunhos legados são
somente leitura para início: a UI orienta usar como novo pedido. Execuções e
respostas produtivas anteriores conservam o caminho legado, com patches Temporal,
sem reinterpretar histórico de aprovações.

API, worker geral de WhatsApp e worker dedicado de criação precisam carregar o
código atualizado. O worker dedicado foi recarregado nesta alteração. Integrações
externas, publicação e novas gerações pagas não foram acionadas. Para ambiente
novo, aplicar a migração antes de iniciar os processos.

## Validação e limites

Realizadas revisão de código, conferência de sintaxe Python, lint de símbolos,
formatação Python/TSX, aplicação da migração local e inicialização do worker.
Adicionados testes unitários de encaminhamento comum para as duas origens e os
três formatos, recusa de evento de outro negócio e isolamento da saída privada.
**Não executados**, conforme instrução do usuário; também não foram executados
build, typecheck, suíte PostgreSQL, CI ou geração paga. Não há alegação de cobertura
100%, paridade funcional demonstrada ou melhoria de qualidade visual validada.

Aceite manual pelo administrador: mensagem de feed, story e reel com vídeo;
reel sem vídeo seguido de resposta com material; ausência de item no catálogo;
pergunta factual e resposta; ajuste de peça concluída; substituição de anexo;
interrupção por teto; reconexão SSE; impossibilidade de acesso por cliente;
conferência das reservas e das peças privadas. Áudio utiliza o mesmo teto da peça, sem orçamento adicional. Melhorias estéticas de motion e limites semanais por formato
continuam na etapa seguinte, não foram misturadas à unificação.
