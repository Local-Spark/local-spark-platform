# Snapshot editorial de referências sugeridas

Atualização de 04/11: a [fatia 0110](reference-generation-context.md) implementa
este plano em cópia isolada, com validação unitária e dependência do leitor 0108.
O texto abaixo registra o diagnóstico que motivou a entrega; o contrato novo
fica no documento vinculado e não implica homologação comercial.

Hoje, ao criar uma proposta, o serviço copia as referências manuais ativas para
`editorial_proposals.owner_reference_snapshot`, com @, nota do titular, origem
`owner` e acesso `not_checked`. A geração editorial lê essa cópia e informa ao
modelo que os perfis não foram analisados. A geração visual usa o mesmo
snapshot da proposta. Um teste integrado cobre a troca das referências depois da
criação: a proposta anterior continua com a indicação original.

As referências sugeridas ainda não entram nessa jornada. A seleção real e a
publicação continuam privadas/inativas; a seleção proposta identifica
resultado, candidata e Place ID, mas não registra ainda uma versão comprovada
da associação com o perfil nem uma análise de seu feed. O contrato puro
`reference_learning_projection` apenas filtra análises fornecidas por um futuro
serviço confiável; não busca posts, verifica sua origem ou produz aprendizados.

O próximo recorte de integração deverá acrescentar um snapshot separado e
versionado de referências sugeridas e aprendizados autorizados à proposta,
sem alterar o significado nem reescrever `owner_reference_snapshot`. A criação
da proposta deverá capturar uma seleção consistente sob a mesma coordenação
transacional usada nas alterações de seleção. O snapshot deverá identificar a
versão da associação, a análise derivada efetivamente vinculada e sua cobertura
parcial quando aplicável. Ausência de análise deverá continuar explícita, sem
atribuir estilo ou fatos inventados à referência.

A geração editorial e a visual deverão ler a mesma cópia da proposta. Uma troca
posterior de referências não deve substituir silenciosamente conteúdo histórico;
qualquer revalidação de autorização antes de um efeito pago deve ocorrer de
forma explícita, sem inventar uma nova versão para a proposta antiga. Nenhum
post, imagem ou legenda brutos devem entrar no snapshot, em Temporal, auditoria
ou outbox.

Antes de ligar esse recorte ao produto, ainda são necessários publicação e
seleção reais comprovadas, associação do Instagram com proveniência e versão,
coleta e análise autorizadas, sem persistência local das publicações,
arquivo durável apenas dos padrões derivados, isolamento por organização e
negócio, auditoria/outbox e testes de concorrência, histórico, revogação e
replay. A validação sintática da projeção não prova que texto seja derivado nem
que uma instrução inserida por terceiro será ignorada; essas propriedades
precisam de validação própria. Esta nota não cria schema nem ativa integração.
