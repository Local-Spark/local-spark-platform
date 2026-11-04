# Entrada efêmera para análise de referências

Estado atual em 04/11: o contrato abaixo já está integrado à
[execução](reference-learning-execution.md), com guardas, downloader, ledger e
snapshot. A decisão mais recente admite somente autoria direta, incluindo capas
e legendas de vídeos/Reels. O texto das etapas de integração abaixo preserva a
especificação preparatória; não representa pendências atuais de implementação.

`reference_feed_analysis_input` prepara, somente em memória, os posts acessíveis
retornados pelo adapter de feed para uma futura análise. O objeto vincula a
referência e a versão da associação ao perfil e à execução informados, conserva
até 20 posts, legendas e todas as imagens acessíveis dos carrosséis. O limite de
20 posts corresponde à decisão do titular; não há limite fixo de imagens por
post. A resposta do fornecedor tem o limite técnico de 1 MB: se for excedido, a
consulta falha como incerta, sem alegar cobertura completa. Nenhuma imagem é
baixada e nenhum padrão é extraído nessa etapa.

O contrato recusa perfis divergentes, identificadores inválidos, posts repetidos,
URLs fora dos hosts permitidos pelo adapter e resultados inconsistentes. Ele
preserva a indicação de análise parcial. Uma resposta `available` mantém
cobertura **não confirmada**: não prova que todos os posts foram acessados.
Quando não há post acessível, não cria entrada para análise.

O objeto e os posts ocultam seu conteúdo em `repr`, e os erros usam códigos
estáveis. Eles ainda contêm dados de terceiros em memória. Não podem ser
retornados ou serializados em resultados de workflow Temporal, logs, auditoria,
outbox, banco, arquivos ou outros armazenamentos. A activity futura deve
consumir o conteúdo em sua própria execução e devolver somente identificadores
ou resultados derivados autorizados.

Este contrato valida forma e consistência, **não autentica a execução, a origem
dos posts, a titularidade do perfil nem a associação à referência**. Antes de
integrar ou ativar a análise, faltam:

- Carregar a seleção e a versão de associação autorizadas, e verificar o perfil,
  o efeito, a execução e os recursos retornados contra provas duráveis.
- Admitir cada efeito com orçamento, HMAC, fence e recuperação; respeitar a
  janela aplicável à referência e não repetir automaticamente efeito incerto.
- Implementar obtenção das imagens com limites de bytes e pixels e proteção
  contra destinos internos, redirecionamentos e alterações de DNS. A checagem
  atual de hostname não autoriza, por si só, qualquer download.
- Manter os posts e as imagens exclusivamente em memória na nossa plataforma;
  o titular não exige exclusão dos recursos internos do Apify e não haverá
  chamadas `DELETE` para esses recursos.
- Implementar a análise de tom, temas, formatos e elementos visuais gerais,
  dimensões definidas pelo titular, e definir o provedor de análise; testar
  saída estruturada, parcialidade e proteção contra copiar legendas ou
  seguir instruções contidas nos posts. Validação sintática não comprova que
  o resultado seja derivado ou seguro.
- Persistir apenas aprendizados autorizados e sua proveniência, com isolamento,
  auditoria/outbox sem conteúdo bruto e atualização da versão da associação.
  Integrar um snapshot validado ao fluxo editorial e visual somente após essas
  garantias.
