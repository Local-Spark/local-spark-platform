# Vídeos com gravação real, orientação e voz — proposta de produto

Atualizado em 27/10/2026. Complementa [roadmap](delivery-roadmap-2026-10-27.md),
[BL04](../phases/BL04-context-and-ai-production.md),
[BL05](../phases/BL-brand-library.md#bl05--jornada-completa-local-ajuste-e-proatividade-mínima)
e [F05](../phases/F05-avatar-generative-video.md). Este documento especifica
propostas e gates; **não significa que já foram entregues ou aprovadas comercialmente**.

## Intenção de produto

Priorizar vídeos reconhecíveis do negócio: mãos do proprietário, produto, serviço,
ambiente e voz real quando autorizados. O cliente não precisa aparecer; evitar
assumir que avatar ou cenas geradas serão mais autênticos ou eficazes. A plataforma
oferece sugestões específicas e gravação simples, reduzindo o trabalho criativo
sem prometer aumento de vendas nem garantir menor custo antes de medir.

O primeiro plano de R$ 99 foi definido com **foto e story**; vídeo, quantidade,
limites e preço não estão definidos. Story não implica direito a vídeo. Uma hipótese
de vídeo é recomendação de produto, não uma franquia já vendida ou liberada.

## Dois percursos para vídeos com material real

**Pedido do cliente.** Pelo WhatsApp simulado, o cliente pede, por exemplo: “me
ajuda a mostrar como faço meu cachorro-quente”. Com fatos confirmados e fontes
disponíveis, propor roteiro curto: objetivo, duração aproximada, tomadas possíveis
com mãos, instruções claras de gravação em celular, fala opcional, texto de apoio
e CTA verificável. Pedir esclarecimento quando um preço, data, produto ou
disponibilidade não estiver confirmado. O cliente pode gravar, enviar ou desistir.

**Sugestão proativa.** Na cadência e nos canais consentidos, verificar acesso,
franquia, fuso, contatos, janela de envio e orçamento; não gerar mídia paga nem
publicar simplesmente porque falta uma publicação. Propor um roteiro gravável
com base no contexto válido e na disponibilidade do negócio. A cadência gera uma
proposta, nunca presume aceitação ou recebimento de material. Horários e formatos
são hipóteses até existirem métricas e evidências comparáveis.

Exemplo de mensagem: “Que tal mostrar suas mãos finalizando um cachorro-quente?
Grave três trechos curtos: preparo, montagem e resultado. Se quiser, envie aqui
o vídeo; eu preparo uma prévia para você conferir.” Roteiros variam por setor:
manicure pode mostrar etapas autorizadas e resultado; delivery, montagem e
embalagem; profissional com agenda, bastidores sem expor dados de clientes.

Ao receber vídeo, oferecer receitas explícitas: **original**, preservando áudio e
imagem com ajustes técnicos mínimos; **edição leve**, como cortes, enquadramento,
legendas e texto aprovado; e **motion**, como animação contida de CTA ou elementos
do kit. Preferência configurável deve evitar transições, música ou reconstruções
surpreendentes. Ferramentas como FFmpeg podem executar edição definida; não são um
modelo generativo nem garantem qualidade. Toda receita passa por testes de
qualidade, fidelidade, duração, proporção, acessibilidade e custo antes da liberação.

Prévia individual é privada e revisável. Nenhum upload, roteiro ou aceite de kit
autoriza publicar: aprovação explícita para a versão final, revalidação de material,
direitos, fatos e plano antes do efeito. O material de terceiros, imagem de clientes
e áudio/música exigem direitos adequados; quando incertos pedir material alternativo.
Se o cliente enviar pronto, não afirmar que os direitos foram verificados só porque
o enviou. Legendas devem preservar a fala e permitir revisão de nomes e preços.

## Escopo e sequência

1. **BL04.1:** interpretar pedido, consultar contexto e esclarecer; comparação
   de modelos, sem afirmar que a conversa completa ou geração visual estão prontas.
2. **BL04.2–BL04.3:** imagem e gate de qualidade/custo; não substituir imagem
   real por um ambiente inventado e comparar custo por peça aceita.
3. **BL05.1/BL05.2:** conversa simulada e proatividade mínima. Especificar e
   avaliar roteiro sob pedido e sugestão de gravação, com cadência e permissão.
   Agendamento de mensagens reais depende das regras e homologação Meta. Esta
   entrega não habilita vídeo comercial nem promete edição avançada.
4. **F04 — receita de vídeo real:** implementar por fatias a ingestão, a prévia
   original, edição leve e motion, com revisão visual em negócios consentidos;
   medir tempo, custo completo, taxa de aprovação e qualidade. Ligar a franquias
   e canais autorizados em F06/F07 antes de vender o recurso.
5. **F05 — voz sintética opcional, após o primeiro piloto comercial:** apenas
   depois de comparação de alternativas, aceite de qualidade e custo por vídeo.
   Um experimento isolado com dados fictícios/autorizados pode preceder o piloto,
   sem antecipar a entrega comercial nem substituí-la por um avatar.

## Voz clonada: hipótese, não clonagem do ElevenLabs

O repositório mencionado pelo sócio não foi identificado. Não presumir que uma
implementação que imite API/interface do ElevenLabs contenha os pesos proprietários,
mesma qualidade ou licença de uso comercial. Solicitar o link para avaliar o caso
específico. Candidato independente: [Chatterbox](https://github.com/resemble-ai/chatterbox)
e seu [checkpoint PT-BR](https://huggingface.co/ResembleAI/Chatterbox-Multilingual-pt-br),
que informa licença MIT; conferir também os pesos e componentes efetivamente usados.
O [F5-TTS](https://github.com/SWivid/F5-TTS) distingue código MIT e pesos com
licença não comercial; não tratar o repositório inteiro como liberado para SaaS.

Executar um modelo aberto evita uma taxa de API por chamada, mas requer computação
(possivelmente GPU), armazenamento, fila, segurança, operação e retentativas. Em
baixa utilização, hospedagem dedicada pode custar mais; avaliar CPU/GPU, autoscaling,
latência e custo **por vídeo aceito**, inclusive refações. Comparar voz original,
narração do cliente e modelo aberto com provedor comercial, mantendo custo, direitos
e qualidade PT-BR por sotaque e pronúncia de nome/preço como medições separadas.

Voz clonada exige consentimento específico verificável da pessoa cuja voz será
usada, finalidade, amostra adequada, isolamento por tenant, controles de uso,
revogação e exclusão rastreável de amostras/identidade/artefatos derivados conforme
política aplicável. Retirar consentimento impede novas gerações e interrompe o que
for possível; comunicação de uso e revisão do áudio são requisitos de produto.
Não usar vozes de terceiros sem autorização nem treinar ou avaliar com material de
cliente sem base/autorização própria. Verificar licença, restrições de uso e marca
d'água dos modelos e componentes efetivamente instalados.
