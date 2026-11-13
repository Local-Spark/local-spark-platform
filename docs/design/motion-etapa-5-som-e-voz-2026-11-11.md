# Etapa 5 — som com função e voz protegida

**Continuação de 12/11:** [planejamento audiovisual revisável](motion-planejamento-audiovisual-revisavel-2026-11-12.md)
integra dois candidatos públicos CC0 locais e seleção/omissão estruturada pelo
plano, com vínculo à ação e compilação para o mixer existente. O caminho manual
abaixo permanece; suas declarações de direitos/não duplicação não são fabricadas
no modo proposto. Sem escuta, adequação/duplicação/inteligibilidade continuam
pendentes. Sem geração paga ou nova peça nesta continuação.

Data: 11/11/2026. Implementação técnica local; escuta e aceite pendentes.

## Contrato e decisões

- A API aceita até oito eventos opcionais, com material existente do negócio,
  papel de música ou efeito, início, trecho, ganho e fades. O titular confirma
  os direitos e que o som não duplica a fonte; são declarações, não perícia de
  licença ou detecção automática de duplicação. Sem seleção, mantém-se v1.
- A captura consulta o acervo existente com escopo de tenant/negócio, integridade
  e disponibilidade, registra vínculos pela estrutura existente e valida bytes,
  hash, tipo e duração antes da chamada ao modelo. Nenhum acervo foi consultado
  ou material escolhido nesta verificação. Para uma comparação futura, falta
  selecionar som adequado e confirmar seus direitos e sua relação com a fonte.
- O plano original fornecido ao modelo continua sujeito à igualdade integral.
  A trilha adicional é compilada pelo servidor, separadamente, vinculada ao
  contexto e à identidade durável do render. O ramo original mantém seu asset,
  ordem, trecho, offset e ganho; ele não recebe fade ou compressão. O modelo não
  escolhe nem altera complementos. Efeitos são posicionados por seleção explícita,
  sem gerar uma receita automática ou obrigatória por palavra.
- O mixer existente usa o original como sinal de controle e comprime somente a
  música, quando solicitado; efeitos não recebem ducking. Fonte com voz e música
  já misturadas continua inseparável: a compressão reage à mistura inteira.
  Cabe ao titular adaptar ou omitir complementos após ouvir a fonte.
- A saída decodificada é medida em loudness integrado e pico de amostra; não há
  alvo universal, limitador nem garantia de ausência de clipping em toda mistura.
  Pico de amostra não é true peak. A reencodificação final não é bit a bit igual
  à fonte; a integridade assegurada refere-se ao ramo antes da mixagem.

## Evidência e limitações

Foram executados 182 testes Python dirigidos e seis Node, além de Ruff e Mypy nos
módulos alterados. A fixture Node sintetiza sinais locais descartáveis e usa
FFmpeg real: verifica intervalo do efeito, fades, redução de música durante a
voz, contribuição original e pico abaixo de 1 nessa fixture; também mede loudness
e pico. O teste do orquestrador confere a entrega do plano e sua identidade, e o
adapter exige as medições no resultado v2. Isso não é uma escuta humana nem uma
comparação A/B e não comprova a qualidade sonora ou visual de um Reel real.

Não houve chamada paga, geração/download de asset real, consulta a conteúdo do
cliente, nova peça ou uso de banco. Nenhum serviço foi iniciado. O estado dos
cinco serviços previamente interrompidos não foi confirmado. Não se executou CI
integral; o gate de merge de 100% continua vigente. A imagem fixada do executor
não foi reconstruída nem exercitada com esse contrato: antes de uso efetivo é
necessário reconstruir, fixar a nova imagem e validar a integração no ambiente
autorizado. A interface de escolha de sons não foi criada; a seleção está no
contrato da API. Sem biblioteca musical autorizada selecionada, o fluxo segue
com a gravação original.

Escuta/A-B da peça e da fonte, verificação dos direitos e da ausência de sons
duplicados, escolha de materiais e aceite criativo continuam pendentes. Etapa 6
não foi iniciada e depende do OK do titular.
