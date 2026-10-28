# BL04.2 — quarentena de upload e versões antigas

A migração 0055 adiciona uma marca persistida e uma constraint para uma foto
em quarentena. Na mesma transação do descarte, a aplicação marca a linha como
quarentenada, privada, arquivada, pendente, sem proprietário de upload e na
versão zero. Uma consulta de um worker antigo que tentasse alterar essa linha
para `deleting` é rejeitada pela constraint antes de poder remover o objeto.
A constraint não altera as regras de exclusão de fotos prontas legadas.
A migração interrompe o upgrade se encontrar uma foto com SHA em `deleting`
sem prova de envio único; um operador precisa investigar o efeito externo
antes de continuar. O downgrade é bloqueado enquanto houver linha em quarentena.

O teste de integração exerce essa instrução antiga com a role restrita do app,
depois de descartar a foto e antes de soltar um writer atrasado. A chave continua
privada e sem uso. A regra não demonstra que um PUT ou DELETE já iniciados
antes da migração tenham terminado e não identifica objetos que já tenham sido
removidos e depois recriados por uma tentativa antiga. Antes de qualquer rollout
com versões mistas, migrar o banco antes da versão nova e drenar comprovadamente
os processos antigos e seus efeitos externos. A limpeza dos objetos em
quarentena e a evidência de drenagem ainda não foram implementadas; 0055 não é
aprovação de deploy ou garantia de exclusão física.
