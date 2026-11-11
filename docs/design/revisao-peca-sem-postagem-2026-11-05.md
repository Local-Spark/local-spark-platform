# Revisão e aceite da peça sem postagem — proposta de fatia

Data: 05/11/2026. Esta é uma proposta técnica para a próxima fatia, não uma
funcionalidade entregue. A entrega de geração compreende peça final, revisão,
ajustes, aprovação da peça e download. A postagem e sua autorização específica
ficam para outra fase, conforme [decisões](../DECISIONS.md) e
[plano da v0](plano-v0-imagens-video-motion-2026-11-05.md).

## Lacuna no fluxo existente

- `media-previews` permite listar prévias e obter um link privado temporário
  autorizado para um arquivo concluído. Isso não registra aceite da peça. A
  lista é limitada a 30 itens e pode omitir uma prévia ainda revisável; não deve
  ser usada como fonte de verdade para descobrir os metadados da revisão.
- `editorial-proposals/{id}/script-review` registra a revisão do roteiro. Não
  prova revisão ou aceite do arquivo final.
- `content-deliveries/{id}/decision` é o fluxo legado de decisão para publicação
  simulada. Uma aprovação associa hash, legenda, destino e horário, e coloca
  `publish_state` em `pending`; o processamento atual usa publicação fake. Para
  `full_piece_v1`, esse fluxo requer também `visual_review` com o hash da prévia
  e cinco confirmações verdadeiras. Ele **não é** o aceite isolado da peça.
- Não há, no contrato existente, um aceite durável da peça exata independente
  de postagem. Também não há coleção de páginas de motion revisável e aprovada
  como uma versão única. Consultar apenas a lista limitada de prévias ou usar
  o aceite de roteiro não supre essas lacunas.

## Contrato pretendido

Criar uma revisão própria de peça, em serviço de domínio e rotas/schemas finos,
sem habilitar publicação. Reaproveitar identidades, autorização, armazenamento,
prévias e auditoria existentes onde suas garantias atendam ao contrato; modelar
uma coleção e versões próprias quando necessário, sem reinterpretar uma
aprovação do fluxo legado como aceite da peça.

Cada versão submetida à revisão identifica o negócio, formato e **conjunto
ordenado de artefatos**. Cada entrada contém identidade estável, posição,
tipo de mídia, SHA-256 do arquivo concluído e referência privada autorizada;
o conjunto tem identidade e versão imutáveis. Uma imagem tem um artefato. Um
Reel ou story em vídeo terá um MP4. Um carrossel terá de três a cinco MP4s,
cada um de cinco a oito segundos, em ordem; PNG de apoio é opcional e não
substitui MP4. Metadados são devolvidos pela consulta autorizada da própria
revisão/coleção, mesmo que uma prévia tenha saído da lista de 30; a interface
não exibe IDs internos, hashes, chaves de armazenamento ou URLs brutas do acervo.

Para cada arquivo, disponibilizar link privado temporário gerado após verificar
owner, organização, negócio e acesso ao artefato daquela versão; não armazenar
URL assinada como identidade nem colocá-la no registro de aceite. A visualização
ou download não implica aprovação. O backend valida que artefatos estão
concluídos e pertencem à versão e ao negócio, que ordem, tipos e hashes
correspondem ao conjunto persistido e que a operação diz respeito à versão
corrente. Não confiar apenas em hash ou tenant enviado pelo cliente. Uma
verificação de objeto que requeira rede fica fora de locks de banco e precisa de
controle contra alteração concorrente; o aceite se ancora em identidades e
versões imutáveis, não em links temporários.

A aprovação é uma decisão explícita do proprietário sobre a versão completa.
Para cada artefato sujeito à regra `full_piece_v1`, exigir as cinco confirmações já
previstas pelo contrato existente: preços e condições quando houver, ortografia,
identidade, fidelidade e legibilidade. São declarações humanas, não resultados
de verificação automática. Validar seu vínculo com o hash e a versão revisados;
recusar confirmação incompleta, artefato ausente, conjunto reordenado, hash
incorreto ou versão desatualizada. Erros devem permitir atualizar a revisão sem
perder silenciosamente a decisão. O checklist existente não comprova qualidade
criativa nem aprovação para postagem.

## Estados e alterações

O desenho deve distinguir pelo menos `em_preparacao`, `pronta_para_revisao`,
`ajuste_solicitado` e `aprovada`, além de falha/indisponibilidade quando a
produção ou o arquivo não estiverem prontos. Nomes definitivos são de contrato;
os estados representam uma versão e suas transições, não estados de publicação.
A versão aprovada e o histórico de decisões permanecem identificáveis. Uma nova
versão exige nova revisão e novo aceite; aprovação histórica não aprova conteúdo
posterior. Não disponibilizar um conjunto parcialmente produzido como versão
completa pronta para aprovação; falhas parciais precisam ser apresentadas e
recuperadas sem declarar sucesso.

Ao solicitar ajuste em uma página, identificar a página, a versão de origem e o
pedido; preservar as demais páginas e sua ordem. Se a execução exigir mudança
em outras páginas, registrar e apresentar previamente o alcance proposto e
aguardar confirmação explícita antes de alterá-las. Se o cliente não confirmar,
não expandir a alteração. Confirmar alcance não aprova a peça. Quando a nova
versão estiver completa, apresentar a sequência inteira e solicitar nova
aprovação. Uma repetição do mesmo pedido ou confirmação usa a mesma identidade
de operação; não duplicar o efeito. Efeitos assíncronos de ajuste/render usam
identidade durável e Temporal, com retomada e tratamento explícito de resultado
incerto, sem rede sob locks.

## Persistência, autorização e retenção

A transação que registra decisão precisa aplicar RLS e roles restritas e
verificar proprietário e vínculo com o negócio. Uma identidade de operação e um
hash canônico do pedido permitem repetição idempotente: mesma operação e mesmo
conteúdo retornam o resultado anterior; mesma operação com conteúdo diferente
falha. Serializar decisões concorrentes para que duas versões não recebam aceite
como se ambas fossem correntes. Registrar autor, versão, conjunto ordenado,
hashes e confirmações relevantes em dados duráveis e auditoria transacional,
sem logs de conteúdo privado ou credenciais. Caso uma etapa assíncrona seja
necessária, gravar sua identidade e evento/outbox próprios na mesma transação;
aceitar a peça não cria `publish_state`, pedido ou evento de publicação.

Aplicar C04 aos envios WhatsApp vinculados ao negócio e C09 às prévias e peças
concluídas e sua proveniência: não expirar automaticamente esses arquivos com a
conta ativa. O prazo da URL assinada e a validade factual ou da decisão são
conceitos distintos de retenção. O prazo após encerramento segue P03 pendente;
não inventar exclusão automática. Evitar duplicar o conteúdo privado em logs,
Git, eventos ou payloads públicos.

## Próxima fatia e verificação

1. Implementar primeiro o aceite separado para uma imagem concluída, com
   contrato de revisão e artefato suficiente para evoluir para coleção, acesso
   privado por artefato e checklist explícito vinculado à versão. Manter
   inalterado o comportamento legado de publicação simulada; não ligar o novo
   aceite a ele. Entregar UI apenas quando o contrato do backend existir.
2. Acrescentar depois a coleção ordenada de carrossel, persistência de versões,
   recuperação de falha parcial e protocolo de ajuste por página com confirmação
   de expansão. Reel/story poderão usar o mesmo contrato de coleção de um item,
   após o pipeline de mídia e render estar disponível.
3. Testar unitariamente schemas, estados, ordenação, hashes, confirmações,
   replay e conflitos; testar integração com PostgreSQL dedicado `_test` e logins
   restritos para RLS, owner/negócio, concorrência, auditoria/outbox, retenção,
   links privados e proibição de publicação implícita. Testar na web checkboxes,
   falhas, alterações de versão e revisão em conjunto, incluindo browser e
   cobertura exigida pelo repositório. Rodar `make ci` no backend. Usar mídia
   sintética local e nenhum conteúdo de clientes nos testes de fundação.
