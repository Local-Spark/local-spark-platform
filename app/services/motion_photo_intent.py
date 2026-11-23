"""Photo direction projected from the immutable plan, without aesthetic thresholds."""

from typing import Any

from app.schemas.motion_production import MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_generation import construction_plan_hash

PHOTO_INTENT_CONTRACT_V1 = {
    "version": "motion-photo-intent-v1",
    "rules": (
        "Planeje e implemente progressão perceptível pela intenção: cada cena desenvolve sua mensagem, "
        "dirige a atenção e prepara a próxima. Registre isso em development, sustained_value e transition. "
        "Um hold pode sustentar leitura ou contemplação; não substitua intenção por movimento contínuo. "
        "Tipografia: traduza appearance, purpose e attention_order em hierarquia, contraste, tamanho, "
        "quebras de linha e espaço adequados ao quadro final. Preserve texto autorizado e tempo para leitura "
        "nos beats; entrada/saída não devem consumir a janela de leitura. Evite texto sobre área fotográfica "
        "que prejudique contraste ou esconda o protagonista. "
        "Handoffs realizam origin, crossing e destination do plano, preservando a continuidade da atenção. "
        "Implemente em HTML/CSS/SVG/Canvas e seek determinístico conforme os recursos autorizados. "
        "MotionV1 é uma ferramenta disponível, não requisito estético; scale, zoom, efeitos, quantidade de "
        "cortes e CTA não são obrigatórios. Escolha mecanismos pela intenção, sem inventar ação na foto. "
        "photo_implementation_intent é projeção do plano validado: execute seus tempos e relações, "
        "sem replanejar ou alterar a trilha. Na revisão/correção, compare a intenção com os quadros fornecidos; "
        "não presuma movimento entre amostras nem imponha limiares estéticos ou checklist de efeitos."
    ),
}


PHOTO_VISUAL_RULES = (
    "P1: durante todo hold de fotografia, implemente Ken Burns contínuo: scale suave "
    "(referência 1,00→1,06–1,12) e pan leve com margem de cobertura, sem revelar bordas nem cortar "
    "o protagonista. Anime o enquadramento da foto inteira, nunca objetos internos ou falsa filmagem. "
    "Planeje em development/sustained_value o percurso durante a leitura; evite trechos de mais de ~2 s "
    "sem mudança perceptível. Isso é orientação de construção, não limiar automático A5b. "
    "P2: planeje entrada e saída tipográficas com deslocamento/máscara e stagger por linha ou hierarquia "
    "temporal, não só opacity fade + hold. Declare as janelas nos beats; reserve leitura integral e "
    "conclua a saída antes do handoff, mantendo Ken Burns durante a leitura. "
    "P3: na entrega à marca, declare origin/crossing/destination com acento de scale: push ou scale-down "
    "da origem e assentamento do destino. Preserve proporções do logo; máscara/sombra são opcionais. "
    "Use wrappers distintos para foto, texto e handoff para não sobrescrever transforms. "
    "Adapte os exemplos pinados do repertório em scene_init, instancie-os e chame seus retornos em "
    "seek(ms) absoluto; helpers não são instalados automaticamente. Sem relógio incremental ou IO. "
    "Preserve materiais, texto, kit, duração, tempos validados e trilha autorizada. Não replaneje "
    "na implementação. Na revisão compare intenção/evidência, sem inferir movimento entre amostras "
    "ou criar gates estéticos automáticos."
)
PHOTO_INTENT_CONTRACT_V2 = {"version": "motion-photo-intent-v2", "rules": PHOTO_VISUAL_RULES}
PHOTO_QUALITY_RULES = (
    "L1: quando assets/logo.png estiver disponível, declare no plano pelo menos um elemento "
    "role=image com asset_id=assets/logo.png. No HTML do fecho, renderize obrigatoriamente "
    '<img src="assets/logo.png"> visível, seguindo os tempos de fecho/handoff do plano; '
    "declarar o asset no plano não basta. brand_name tipográfico "
    "pode coexistir como copy, mas não substitui o PNG. Preserve proporções e legibilidade da logo. "
    "P4/L2: planeje holds de leitura curtos, de até ~2–2,5 s; divida copy longa em beats legíveis. "
    "Em 15 s, prefira gancho → acento → segundo material vivo → handoff → marca/CTA. "
    "Durante o fecho/handoff, nos tempos definidos pelo plano, mantenha Ken Burns nas fotos/díptico "
    "e micro-movimento de scale/assentamento "
    "na logo até o fim; nenhum fecho de ~2 s ou mais sem mudança perceptível. "
    "L3: foto dominante full-bleed 9:16 com object-fit:cover e foco protegido é a composição padrão. "
    "Evite janela landscape e faixas mortas; justifique inset na intenção quando necessário. "
    "Tipografia/overlay sobre foto com contraste e protagonista protegido, sem cartaz estático. "
    "Ritmo e composição são orientação forte, não gates automáticos A5b; preserve a trilha."
)
PHOTO_INTENT_CONTRACT_V3 = {
    "version": "motion-photo-intent-v3",
    "rules": PHOTO_VISUAL_RULES + " " + PHOTO_QUALITY_RULES,
}


PHOTO_AD_RULES = (
    "M1: componha anúncio fotográfico, não cartaz editorial: default full-bleed 9:16 desde o gancho, "
    "foto cobrindo o quadro na maior parte do tempo útil, object-fit:cover e foco protegido. "
    "Texto/CTA são overlays sobre foto com contraste local (scrim/gradiente), nunca grandes faixas creme. "
    "Não aceite como default cartão creme com foto em janela ou abertura só tipográfica de vários segundos. "
    "Inset é exceção: justifique explicitamente em staging.development e scene_direction.composition por que "
    "ajuda a mensagem; não use margens vazias como estilo automático. Não há gate geométrico de área. "
    "M2: no fecho, assets/logo.png é âncora, não favicon ao lado do nome: use largura de referência "
    "32–44% do frame, mínimo orientado de 28% (202 px num frame de 720 px), object-fit:contain, "
    "preservando proporção e área útil da marca. Compense padding transparente do PNG pelo preview; "
    "confira contraste e leitura mobile. brand_name pode acompanhar subordinado ao PNG. "
    "M3: o plano rejeita phase=hold contínuo acima de 2500 ms (inclusive holds consecutivos do mesmo "
    "elemento); prefira 2000–2500 ms para leitura, com entrada/saída e mudança de ideia reais. "
    "Não renomeie hold imóvel como transform nem fragmente hold sem ação só para passar validação. "
    "Cena pode durar mais com desenvolvimento; Ken Burns contínuo é phase=transform com estados distintos. "
    "No fecho use handoffEnd < end: handoffEnd é end_ms da transição staging que chega à última cena; "
    "sem essa transição, é o fim das entradas (phase=enter) da última cena, ou seu start_ms. "
    "Declare foto(s) no fecho e logo quando disponível; de handoffEnd até duration_ms, seus beats "
    "phase=transform devem cobrir toda a janela sem gaps e com start_state != end_state. "
    "Descreva Ken Burns nas fotos e scale contínuo na logo; mantenha visibilidade até end. "
    "Fecho com desenvolvimento pode durar mais que um hold. Tempos vêm do plano, nunca janela fixa 11–15s. "
    "Esses gates conferem declarações/tempos, não pixels, legibilidade, energia ou aceite audiovisual."
)
PHOTO_INTENT_CONTRACT_V4 = {
    "version": "motion-photo-intent-v4",
    "rules": PHOTO_VISUAL_RULES + " " + PHOTO_QUALITY_RULES + " " + PHOTO_AD_RULES,
}


PHOTO_CROP_RULES = (
    "Viabilidade de enquadramento (precede os exemplos genéricos de full-bleed/KB): antes de fechar o plano, "
    "examine o preview de cada foto e sua proporção. Full-bleed é preferência, preservar o protagonista "
    "é restrição; não prometa ambas se o recorte não comportar o objeto. Não invente coordenadas exatas "
    "de foco nem preservação integral a partir de uma impressão do preview. "
    "Em scene_direction.composition registre a região essencial a proteger, o enquadramento escolhido "
    "e a margem de movimento; nos beats declare estados inicial/final compatíveis com essa região. "
    "Cover elimina área da fonte quando as proporções diferem: object-position só desloca esse recorte, "
    "não aumenta a área visível. Scale amplia o recorte; pan também consome margem. Verifique o percurso "
    "inteiro, inclusive o maior scale, antes de fixar números no plano. Os valores 1.04→1.12 e focos do "
    "exemplo não são mínimos obrigatórios. Reduza zoom/pan ou escolha outra foto autorizada quando preciso. "
    "Se nenhum cover preservar a região essencial, use composição em camadas: a mesma foto ampliada "
    "como fundo full-frame e foto principal em contain sobre ela, sem cartão creme ou faixas vazias. "
    "Justifique essa exceção em staging.development e scene_direction.composition; mantenha overlay, "
    "ritmo e movimento no fundo, e planeje movimento limitado da foto principal com margem real. "
    "No fecho preserve os transforms contínuos exigidos sem cortar a foto principal; se não houver "
    "margem, reveja a composição no planejamento. Não use objeto cortado como se estivesse inteiro. "
    "Na implementação conserve o plano aprovado: estas alternativas devem ser decididas no planejamento, "
    "não autorizam trocar crop, tempos ou materiais silenciosamente. Havendo incompatibilidade real, "
    "continue retornando requires_plan_revision com motivo específico. Sem gate geométrico ou A5b."
)
PHOTO_INTENT_CONTRACT_V5 = {
    "version": "motion-photo-intent-v5",
    "rules": PHOTO_INTENT_CONTRACT_V4["rules"] + " " + PHOTO_CROP_RULES,
}


PHOTO_ENERGY_RULES = (
    "N1: default real é foto dominante cover 9:16, desde o gancho, com foco e margem protegidos. Proibido "
    "usar janela landscape central + barras blur como estética automática; fundo blur não conta como foto "
    "cover. Contain sobre fundo fotográfico só é exceção por inviabilidade de crop: registre em "
    "staging.development e scene_direction.composition qual região essencial seria cortada, alternativas "
    "examinadas e margem disponível. Preservar protagonista continua precedendo bleed e números de "
    "movimento; não invente viabilidade. N2: planeje KB/overlays perceptíveis também no miolo. Para "
    "declarar energia use start_state/end_state no formato exato scale=1.04 x_pct=0 y_pct=0 (scale "
    "positivo; pan em porcentagem do quadro). Um transform energético requer curva linear e velocidade "
    "média de scale >=0.01/s OU pan em um eixo >=0.5 ponto percentual/s. O gate une intervalos "
    "energéticos de fotos e overlays text/graphic ligados por related_element_ids da foto, dentro da "
    "mesma cena; nenhuma lacuna de energia no plano pode exceder 2500 ms, inclusive começo/fim e entre "
    "cenas. Estados iguais, diferenças de prosa, drift abaixo do limiar, gaps e holds fragmentados não "
    "reiniciam essa janela. Exemplo em 2 s: scale=1.04 x_pct=0 y_pct=0 até scale=1.08 x_pct=0 y_pct=0. Se "
    "crop limitar KB, mantenha foto segura e planeje overlay relacionado com movimento perceptível, "
    "legível e contínuo; não aumente crop para passar o gate. Sem margem e sem alternativa coerente, "
    "revise o plano. M3 continua obrigatório no fecho, inclusive foto e logo até end. N3: logo PNG âncora "
    "sobre foto/fundo fotográfico, sem placa creme/editorial; CTA integrado como overlay com scrim local, "
    "não rodapé de cartaz. Micro-movimento da logo até end. Estes números validam declarações, não "
    "pixels, velocidade instantânea ou qualidade audiovisual; sem A5b. A implementação segue os estados e "
    "tempos aprovados, sem replanejar. N1/N2/N3 refinam as orientações anteriores; exceção de contain "
    "exige inviabilidade de crop, não apenas preferência estética."
)
PHOTO_INTENT_CONTRACT_V6 = {
    "version": "motion-photo-intent-v6",
    "rules": PHOTO_INTENT_CONTRACT_V5["rules"] + " " + PHOTO_ENERGY_RULES,
}


PHOTO_CONTINUITY_RULES = (
    "O1: estas regras refinam N1–N3. Em TODAS as cenas fotográficas, inclusive miolo e fecho, use cover "
    "9:16 contínuo com protagonista protegido. Não regresse a janela landscape + blur após abertura cover "
    "com o mesmo material viável. Contain+blur não é estilo alternativo: por CADA cena excepcional, "
    "registre em composition a região essencial cortada, alternativas de cover/foto examinadas e margem; "
    "em development explique a inviabilidade e como manter energia. A exceção de uma cena não autoriza "
    "contain nas outras. Crop v5 prevalece; não invente viabilidade nem corte protagonista para cumprir "
    "energia. O2: para novas capturas, um transform energético linear exige no MESMO eixo velocidade de "
    "scale >=0.02/s E amplitude >=0.04, OU pan >=1 ponto percentual/s E amplitude >=2 pontos percentuais. "
    "Substitui os mínimos N2; mantém união global e lacunas <=2500 ms, M3 e overlays relacionados da "
    "mesma cena. Pulsos mínimos fragmentados não contam. Exemplo de miolo em 4 s: scale=1.04 x_pct=0 "
    "y_pct=0 até scale=1.16 x_pct=0 y_pct=0; adapte à margem real, nunca copie crop cegamente. Se "
    "limitado, coordene text/graphic relacionado visível com amplitude suficiente e leitura preservada. "
    "Execute os estados no seek: wrappers separados para KB contínuo e entrada/saída tipográfica com "
    "deslocamento/máscara; opacity zero, camada oculta ou transform sobrescrito não realizam energia. O3: "
    "no fecho renderize assets/logo.png em img overlay sobre foto, wrapper transparente sem background "
    "creme, placa, card, borda ou padding editorial. Não incorpore placa ao redor do PNG. Use scrim "
    "local/gradiente neutro sobre a foto para contraste da marca e CTA; confira CTA durante todo "
    "percurso, reserve leitura, sem desaparecer antes de end. Foto(s), logo e CTA permanecem visíveis, "
    "foto e logo em movimento até end conforme M3. Se o próprio asset impedir este acabamento, peça "
    "revisão do plano; não redesenhe a marca. O1/O3 são instruções de composição e implementação, não "
    "inspeção DOM/pixels; O2 valida declarações, sem A5b ou aceite audiovisual. "
)
PHOTO_INTENT_CONTRACT_V7 = {
    "version": "motion-photo-intent-v7",
    "rules": PHOTO_INTENT_CONTRACT_V6["rules"] + " " + PHOTO_CONTINUITY_RULES,
}


PHOTO_DENSE_RULES = (
    "Q1: cover 9:16 em TODAS as cenas fotográficas, inclusive cada cena do miolo e fecho. Prefira fotos "
    "autorizadas cujo protagonista caiba em cover; não é obrigatório usar todas. Proibido alternar cover no "
    "gancho com janela+blur no miolo por conveniência. Contain+blur é exceção rara por cena, nunca estilo: "
    "composition deve identificar asset, região essencial, alternativas examinadas e margem no percurso; "
    "development deve explicar por que outra foto autorizada não resolve. Se várias cenas exigirem exceção, "
    "reveja seleção/composição antes de aprovar; não sacrifique crop v5. Q2: mantém velocidade/amplitude O2 e "
    "M3; substitui a tolerância de lacunas por <=500 ms globalmente (inclusive início, fim e fronteiras) e "
    "exige união energética >=80% da duração de CADA cena fotográfica. Sobreposições contam uma vez; energia "
    "de outra cena não compensa miolo parado. KB contínuo durante leitura, com text/graphic relacionado "
    "visível quando crop restringir movimento. Entradas/saídas claras e leitura legível; não conte apenas "
    "pulsos nas trocas, opacity zero, camada oculta ou transform sobrescrito. Q3: fecho com img "
    "assets/logo.png sobre foto; wrapper transparente, background:none, border:0, padding:0, box-shadow:none. "
    "Proibido card/placa creme inclusive em ancestrais/pseudo-elementos. Scrim neutro local pertence à foto, "
    "nunca caixa da marca. CTA separado do wrapper de saída, legível até end; foto/logo movem até end. Se o "
    "PNG tiver placa incorporada, requires_plan_revision, sem editar identidade. Revise cada cena na "
    "implementação, não apenas o gancho; helpers são adaptados/instanciados em scene_init e chamados por seek "
    "absoluto. Q1/Q3 são instruções, não gates DOM/geométricos; Q2 mede declarações, não visibilidade nos "
    "pixels. Sem A5b nem aceite E2E."
)
PHOTO_INTENT_CONTRACT_V8 = {
    "version": "motion-photo-intent-v8",
    "rules": PHOTO_INTENT_CONTRACT_V7["rules"] + " " + PHOTO_DENSE_RULES,
}


PHOTO_HARD_RULES = (
    "R1–R3 substituem as ressalvas soft de Q1/Q3: validação obrigatória do plano e DOM em cada seek. "
    "Cada cena fotográfica declara photo_layout={mode:cover|contain_blur, primary_element_id, "
    "crop_exception:null|{asset_id,essential_region,alternatives_rejected,safe_motion}}. Cover sem exceção; "
    "contain_blur exige todos os campos não vazios e asset da foto primária. No máximo UMA exceção, "
    "em no máximo 1/3 das cenas fotográficas; cover exclusivo ocupa >=2/3 da duração total, "
    "descontando sobreposições com exceções. Se inviável, revise seleção/plano; crop v5 prevalece. "
    "Cada elemento verificado usa id DOM idêntico ao id do plano; fotos/logo são img com src do asset. "
    "Foto cover ocupa todo viewport 9:16, object-fit:cover, sem clipping/janela em ancestrais. "
    "Use makePhotoSceneMotion por cena e chame cada retorno em seek(ms), com estados numéricos "
    "canônicos de todos os transforms energéticos. O DOM deve executar translate em px equivalentes "
    "a x_pct/y_pct do VIEWPORT, seguido de scale uniforme no nó identificado, sem rotação/skew. "
    "Wrappers de entrada/saída separados. A guarda não anima nem corrige crop. Q2/O2 e M3 continuam. "
    "Toda cena com energia exige ao menos um candidato visível executando o estado interpolado exato; "
    "overlays relacionados continuam disponíveis para crop restrito. "
    "Última cena declara photo_closing={brand_element_id:id|null,surface:transparent_overlay, "
    "cta_element_id:id de text autorizado}. Logo disponível exige referência à img assets/logo.png. "
    "Logo e ancestrais: background transparente, sem background-image, borda, padding, sombra ou "
    "pseudo-elemento pintado. CTA separado, branco com text-shadow preto opaco, fonte >=24px em 720px, "
    "dentro do quadro e visível até end. Contraste local não autoriza inventar CTA/copy. "
    "De handoffEnd até end, fotos/logo têm transforms lineares numéricos distintos, e ficam visíveis. "
    "Sem placa embutida no PNG; nesse caso requires_plan_revision. A guarda DOM rejeita divergências "
    "na execução, não mede pixels/energia percebida ou transparência interna do PNG. Sem A5b/aceite E2E."
)
PHOTO_INTENT_CONTRACT_V9 = {
    "version": "motion-photo-intent-v9",
    "dom_guard_sha256": "613ab2765a44d194793ef44c888709e9acfec68660e1e75d4ee88ef941c649f8",
    "rules": PHOTO_INTENT_CONTRACT_V8["rules"] + " " + PHOTO_HARD_RULES,
}


PHOTO_INTENT_CONTRACT = {
    "version": "motion-photo-intent-v10",
    "dom_guard_sha256": "91523765064601fa9156cdad7e3c9ada00b95821071bc7332455c3d66553ba3b",
    "rules": PHOTO_INTENT_CONTRACT_V9["rules"]
    + (
        " R3.1: durante dissolução de saída aprovada em staging, de no máximo 500 ms e inteiramente "
        "no overlap das duas cenas, somente a foto de origem pode ficar abaixo de 95% de opacidade. "
        "A foto primária de destino já deve estar totalmente visível (>=95% em cada ancestral), "
        "executando seu layout e energia aprovados. Sem essa cobertura, a saída continua bloqueada. "
        "Não dissolve ambas para zero; entrada com fotografia coberta pela origem, seguida de fade "
        "apenas da origem. Fora dessa janela permanece o gate integral. M3/logo até end intactos. "
        "CTA: entrada segue os beats aprovados; legibilidade integral desde o fim da entrada ou "
        "handoffEnd (o maior), com pelo menos 1500 ms de leitura contínua até end. Inset zero é "
        "máscara aberta, não clipping; inset não zero continua bloqueado durante leitura."
    ),
}


def photo_intent_rules(context: dict[str, Any]) -> str:
    contract = context.get("photo_intent_contract")
    if contract is None:
        return ""
    if contract not in (
        PHOTO_INTENT_CONTRACT_V1,
        PHOTO_INTENT_CONTRACT_V2,
        PHOTO_INTENT_CONTRACT_V3,
        PHOTO_INTENT_CONTRACT_V4,
        PHOTO_INTENT_CONTRACT_V5,
        PHOTO_INTENT_CONTRACT_V6,
        PHOTO_INTENT_CONTRACT_V7,
        PHOTO_INTENT_CONTRACT_V8,
        PHOTO_INTENT_CONTRACT_V9,
        PHOTO_INTENT_CONTRACT,
    ):
        raise AuthError("MOTION_PHOTO_INTENT_CONTRACT_INVALID", 409)
    from app.services.motion_photo_finish import PHOTO_FINISH_CONTRACT, finish_enabled
    from app.services.motion_photo_polish import polish_enabled

    return (
        str(contract["rules"])
        + (" " + PHOTO_FINISH_CONTRACT["rules"] if finish_enabled(context) else "")
        + (" " + str(context["photo_polish_contract"]["rules"]) if polish_enabled(context) else "")
    )


def implementation_intent(
    plan: MotionConstructionPlan, contract: dict[str, Any] = PHOTO_INTENT_CONTRACT
) -> dict[str, Any]:
    """Keep exact declared beats and direction; do not infer reading speed or effects."""
    photo_intent_rules({"photo_intent_contract": contract})
    assert plan.motion_plan is not None and plan.scene_direction is not None and plan.staging is not None
    directions = {scene.scene_id: scene for scene in plan.scene_direction.scenes}
    moments = {moment.scene_id: moment for moment in plan.staging.moments}
    return {
        "version": contract["version"],
        **({"visual_execution": contract["rules"]} if contract != PHOTO_INTENT_CONTRACT_V1 else {}),
        "plan_sha256": construction_plan_hash(plan),
        "scenes": [
            {
                "scene_id": scene.id,
                "start_ms": scene.start_ms,
                "end_ms": scene.end_ms,
                "message": scene.message,
                **({"photo_layout": scene.photo_layout.model_dump(mode="json")} if scene.photo_layout else {}),
                **({"photo_closing": scene.photo_closing.model_dump(mode="json")} if scene.photo_closing else {}),
                "direction": directions[scene.id].model_dump(mode="json"),
                "progression_and_handoff": moments[scene.id].model_dump(mode="json"),
                "typography": [element.model_dump(mode="json") for element in scene.elements if element.role == "text"],
            }
            for scene in plan.motion_plan.scenes
        ],
    }
