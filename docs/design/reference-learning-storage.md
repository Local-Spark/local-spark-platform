# Associações, análises e agenda de referências

A migração 0108 torna a seleção aceita a autoridade para analisar um Instagram.
Referências manuais e sugestões escolhidas entram na mesma projeção versionada.
O identificador da referência e a versão positiva da associação são separados da
versão da correção de perfil: o perfil original retornado pelo Apify também recebe
uma versão canônica positiva. A confirmação de até três sugestões, a indicação
manual, a remoção e a correção de um perfil sincronizam essa autoridade na mesma
transação, com audit/outbox. Uma correção de candidato ainda não escolhido não
agenda análise.

O primeiro evento de análise é criado no aceite. Uma troca de perfil cria outra
associação e uma janela imediata; a anterior perde autorização. A agenda seguinte
usa a data do aceite mais N períodos de seis meses em UTC. Cada data é calculada
diretamente a partir do aceite, para que o ajuste de fevereiro não transforme um
aceite em 31 de agosto em atualizações futuras no dia 28. Uma execução atrasada
agenda o próximo aniversário futuro, sem gerar várias coletas de compensação.
Temporal executa os eventos; essa camada somente persiste a autoridade e a agenda.

Cada janela permite um efeito de coleta e conserva o identificador do run Apify
antes da consulta ao resultado. Identidade da operação, executor, perfil, versão,
build, tarifa, credencial e compromisso do pedido são revalidados. Retomadas
consultam o mesmo run. Falta de configuração ou orçamento antes da coleta mantém
a janela bloqueada, sem iniciar outro período de seis meses. A orquestração também
mantém a mesma janela quando o orçamento termina durante a análise das imagens.

O banco recebe somente padrões próprios de tom, temas, formatos e elementos
visuais, códigos estruturados já comprovados por efeitos Jev concluídos, contagens
e metadados técnicos. Não recebe legendas, publicações, URLs de imagens nem bytes
das imagens. O nome do perfil pode ser conservado quando a resposta já obtida do
Apify o fornece para o Instagram esperado, sem consulta adicional. O nome tem até
200 caracteres, sem controles; sua ausência mantém o identificador do perfil.
Não há limpeza remota de armazenamentos do Apify.

`reference_capture_generation_context` captura todas as referências atualmente
escolhidas, sem truncar a coleção manual, e os aprendizados da associação exata.
`reference_generation_context_is_current` permite revalidar essa versão antes de
um efeito pago. Novas referências não alteram um snapshot anterior; remoções e
trocas de perfil o tornam incompatível. Aprendizados anteriores da mesma associação
continuam identificados como tais enquanto a atualização ainda não os substituiu.

`reference_read_learning_status` é uma leitura autorizada para titulares ativos,
compartilhada entre os titulares do negócio. Retorna estado da análise, estado da
atualização, última análise, próxima data, padrões e nome disponíveis. A leitura
não cria associações, janelas ou efeitos. Tokens de execução e conteúdo do fornecedor
não são retornados. Execução permanece vinculada ao titular e evento duráveis que
a autorizaram; revogação bloqueia novos efeitos.

A ordem de locks é autorização do titular, cabeça compartilhada das referências,
linhas manuais e, quando existe admissão financeira, o lock de custos. A requisição
de rede ocorre após o commit. As funções financeiras originais continuam privadas;
o runtime recebe somente o caminho que exige a seleção canônica.

Validação desta fatia: banco exclusivo `_test`, logins restritos, migração até 0109
e retorno vazio a 0107 seguido de upgrade; testes de aceite, replay, versão,
recuperação do run, padrões comprovados, nome, indisponibilidade, bloqueio por
orçamento e agenda. A execução HTTP simulada, o snapshot editorial/visual e a tela
de status são integrados pelas fatias seguintes. Isso não substitui o ensaio real
controlado nem a validação comercial da BL04.
