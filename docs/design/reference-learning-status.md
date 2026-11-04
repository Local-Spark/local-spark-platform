# Leitura dos aprendizados das referências

`GET /api/v1/organizations/{tenant}/businesses/{business}/reference-learnings`
usa sessão autenticada, transação tenant/ator e titular ativo. O serviço chama
`reference_read_learning_status` de 0108; nenhuma consulta externa, agendamento,
sincronização de associações ou escrita faz parte da leitura.

Cada referência expõe ID próprio, versão da associação, origem, perfil e nome
opcional obtido do Apify; estado da análise, estado de atualização e datas;
e somente os padrões gerais de conteúdo/visual persistidos. A projeção não
retorna legendas, URLs de imagens, publicações, credenciais ou metadados Google.
O contrato rejeita padrão sem análise concluída/parcial e análise sem identidade
ou data. Falha de validação retorna código estável, sem encadear dados privados.

O painel fica na etapa de referências da jornada. Exibe disponibilidade parcial
e mantém aprendizados válidos durante a atualização. “Atualizar status” faz GET;
não inicia nova análise nem altera o ciclo de seis meses. Alterações de seleção,
perfil ou referências manuais invalidam a leitura. Vazio, espera e falha têm
estados próprios. O cronograma e os efeitos continuam sob 0108/0109 e Temporal.

Validação: 16 testes unitários/100% de linhas e branches; dois testes HTTP em
PostgreSQL exclusivo `_test` com logins restritos. As provas exercitam dois
titulares, viewer/outro tenant/sessão ausente, padrões de análise parcial,
nome persistido e contagem inalterada de efeitos/eventos/auditorias ao consultar.
Jev usa MockTransport e conteúdo fictício. Nenhuma chamada paga foi realizada.
