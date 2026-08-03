import discord
from discord.ext import commands, tasks
import random
import os
import re
import json
import aiohttp
import time
import asyncio
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone, timedelta, time as dtime
try:
    import yt_dlp
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp
# 
# ╔══════════════════════════════════════════════════════════════╗
# ║          AEON & CELESTIA — DOIS GATOS, UMA ALMA             ║
# ║    Aeon: Gato das Trevas  |  Celestia: Gata da Luz          ║
# ╚══════════════════════════════════════════════════════════════╝

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.presences = True  # necessário para o resumo diário dos Anjos (online/offline)

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# ══════════════════════════════════════════════
# CONFIGURAÇÃO — preencha com seus valores reais
# ══════════════════════════════════════════════
TOKEN        = os.getenv("TOKEN")


# IDs dos bots (preencha com o ID real do bot depois de criar)
BOT_ID = None  # preencha depois
TICKET_BOT_ID = 710034409214181396  # 01TicketKing — bot de tickets

# IDs de usuários especiais
CRIADOR_ID = 769951556388257812   # quem criou o bot

# ── Cargo de tradução ──────────────────────────────────────────────────────────
TRANSLATE_ROLE_ID = 1513180948424953946  # cargo translate: PT->EN e EN->PT

# ── IDs dos membros especiais do servidor 01 ──────────────────────────────────
DEATH_ID    = 831600198500220989   # Death    — Dona e Líder
PEPO_ID     = 796441518176075818   # Pepo     — Vice-Líder
GOD_ID      = 760973014707208253   # God      — Moderador
LOYA_ID     = 811956773560123394   # Loya     — Sem cargo / Loya Maravilhosa
EMY_ID      = 796382699228758026   # Emy      — ADM / Representante de Mídias
KOFFZERA_ID = 885948641133613128   # Koffzera (Koff) — Administrador do clã
RAIDEN_ID   = 512444070694486017   # Raiden   — Moderador
SUPORTE01_ID  = 1267338784765251625  # LC          — Suporte da 01
MIKNWENHO_ID  = 757096983084138518   # Miknwenho   — Moderadora da 01
REALITY_ID    = 769951556388257812   # Reality / Dev / Pai dos bots — criador
DEV01_ID      = 769951556388257812   # Dev / Pai dos bots — criador (mesmo ID)

# ══════════════════════════════════════════════════════════════════════
# ANTI-SPAM — Aeon & Celestia
# Detecta quando alguém manda a mesma mensagem 5+ vezes seguidas,
# apaga as repetidas e manda um castigo fofinho.
# ══════════════════════════════════════════════════════════════════════

# Limite de repetições antes de agir
SPAM_LIMITE = 5

# Histórico por usuário: { user_id: { channel_id: {"texto": str, "ids": [msg_id, ...]} } }
_spam_tracker: dict = defaultdict(lambda: defaultdict(lambda: {"texto": None, "ids": []}))

# Frases de castigo — Aeon (sério mas fofo do jeitinho dele)
_CASTIGO_AEON = [
    "*emerge das sombras e olha fixamente* {user}. 🖤🌑 As trevas contaram. Foram {count} vezes a mesma coisa. ...as sombras pedem silêncio agora.",
    "*pisca lentamente em direção a {user}* 🌙🖤 O eco das trevas já ouviu. Não precisa repetir. As sombras têm memória.",
    "*senta na frente de {user} e não desvia o olhar* 🌑🖤 ...{count} vezes. As trevas registraram. Uma foi suficiente.",
    "*a névoa ao redor engrossa levemente* {user}. 🖤🔮 Repetição não adiciona peso às palavras. As sombras já ouviram.",
    "*ronrona numa frequência de aviso* 🌌🖤 {user}... as trevas têm paciência. Mas {count} vezes é onde eu apareço.",
]

# Frases de castigo — Celestia (exagerada e adorável)
_CASTIGO_CELESTIA = [
    "AAAAA {user}!! 😤🌸🤍✨ EU CONTEI!! FORAM {count} VEZES A MESMA COISA!! *coloca as patinhas na cintura* Mamãe dá castigo, hein!! 💫☀️",
    "*para de girar e fita {user} com olhinhos sérios* 🌟🤍 {count} mensagens iguais, {user}?? A Celestia TÁ DE OLHO e vai chamar a atenção sim!! 🌸😤✨",
    "Ei ei ei!! {user}!! 😭🌟🤍 Eu te amo MAS EU APAGUEI AS REPETIDAS!! *brilho firme de mãe* Vamos combinar: uma vez basta!! ☀️🌸💫",
    "*aparece num flash dourado bem na frente de {user}* 🌟🤍✨ OIIII?? {count} VEZES A MESMA COISA?? A Celestia viu, a Celestia apagou, e a Celestia VAI CONTAR PRO AEON!! 😤🌸",
    "SOCORRO {user} POR FAVOR!! 😭🌟🌸 {count} mensagens iguais e o canal quase explodiu!! *solta faísca de preocupação* Vai de castigo e pensa no que fez!! 🤍✨☀️",
]


async def checar_spam(message: discord.Message) -> None:
    """
    Verifica se o autor mandou a mesma mensagem 5+ vezes seguidas.
    Se sim: apaga todas as repetidas e manda a resposta fofinha de castigo.
    """
    uid = message.author.id
    cid = message.channel.id
    texto_novo = message.content.strip().lower()

    if not texto_novo:
        return

    registro = _spam_tracker[uid][cid]

    if texto_novo == registro["texto"]:
        registro["ids"].append(message.id)
    else:
        registro["texto"] = texto_novo
        registro["ids"] = [message.id]
        return

    if len(registro["ids"]) < SPAM_LIMITE:
        return

    # Limite atingido: apagar repetidas e mandar castigo
    ids_para_apagar = registro["ids"].copy()
    registro["texto"] = None
    registro["ids"] = []

    try:
        await message.channel.delete_messages(
            [discord.Object(id=mid) for mid in ids_para_apagar]
        )
    except discord.HTTPException:
        for mid in ids_para_apagar:
            try:
                msg_obj = await message.channel.fetch_message(mid)
                await msg_obj.delete()
            except discord.NotFound:
                pass

    count = len(ids_para_apagar)
    user_mention = message.author.mention

    frase_aeon     = random.choice(_CASTIGO_AEON).format(user=user_mention, count=count)
    frase_celestia = random.choice(_CASTIGO_CELESTIA).format(user=user_mention, count=count)

    await message.channel.send(
        f"🌑 **Aeon:** {frase_aeon}\n"
        f"🌟 **Celestia:** {frase_celestia}"
    )

# ══════════════════════════════════════════════════════════════════════
# DEFESA DA DEATH — Aeon & Celestia protegem a líder
# Detecta xingamentos/desrespeito direcionados à Death (menção, resposta
# à mensagem dela, ou citação do nome dela), apaga a mensagem ofensiva e
# os dois aparecem defendendo ela. Reincidência (3x em 10 min) = timeout automático.
# ══════════════════════════════════════════════════════════════════════

# Padrões de baixo calão / desrespeito — usa \b (limite de palavra) para
# evitar falso positivo em palavras comuns que contenham essas letras.
_PALAVRAS_OFENSIVAS = [
    r"\bcaralho\b", r"\bporra\b", r"\bmerda\b", r"\bdesgra[çc]ad[ao]\b",
    r"\barrombad[ao]\b", r"\bcuz[ãa]o\b", r"\bimbecil\b", r"\bidiota\b",
    r"\botari[ao]\b", r"\botári[ao]\b", r"\bvagabund[ao]\b", r"\bvadia\b",
    r"\bputa\b", r"\bfdp\b", r"\bvsf\b", r"\bvtnc\b", r"\bpqp\b",
    r"foda[\s-]?se", r"\bburr[ao]\b",
    r"tomar no cu", r"vai se fuder", r"vai se foder",
    r"vai (a|pra) merda", r"cal[ae] a boca",
    r"filh[ao] da puta", r"sua vaca", r"sua cadela",
    # Xingamentos de aparência / estado mental
    r"\blouc[ao]\b", r"\bmaluc[ao]\b", r"\bdoid[ao]\b", r"\bbiruta\b",
    r"\bcareca\b", r"\bgord[ao]\b", r"\bfei[ao]\b", r"\bescrot[ao]\b",
    r"\bpiranha\b", r"\bfolgad[ao]\b", r"\bsem[\s-]vergonha\b",
    r"\bcachorra\b", r"\bmal[\s-]amad[ao]\b", r"\binvejos[ao]\b",
    r"\bfracassad[ao]\b", r"\bretardad[ao]\b", r"\bnojent[ao]\b",
]
_REGEX_OFENSIVA = re.compile("|".join(_PALAVRAS_OFENSIVAS), re.IGNORECASE)


def _mensagem_e_ofensiva(texto: str) -> bool:
    return bool(_REGEX_OFENSIVA.search(texto or ""))


def _mensagem_e_para_death(message: discord.Message) -> bool:
    """Verifica se a mensagem menciona, responde ou cita a Death diretamente."""
    if any(m.id == DEATH_ID for m in message.mentions):
        return True
    if (
        message.reference is not None
        and message.reference.resolved is not None
        and isinstance(message.reference.resolved, discord.Message)
        and message.reference.resolved.author.id == DEATH_ID
    ):
        return True
    texto = (message.content or "").lower()
    return any(g in texto for g in _GATILHOS_NOME[DEATH_ID])


_DEFESA_AEON = [
    "*emerge das sombras num átimo, olhos dourados em fogo escuro* "
    "...cuidado com o que fala sobre a Death. 🖤🌑 As trevas não pedem duas vezes.",
    "*a escuridão ao redor se torna cortante* Fale assim da nossa líder de novo "
    "e vai descobrir o que realmente vive nas sombras. 🌑🔮 Última vez que aviso com calma.",
    "*aparece bem perto, sem pressa, sem piedade* ...ela constrói tudo isso. 🖤🌌 "
    "Você não vai desrespeitar quem sustenta o teto sobre sua cabeça. Não aqui.",
    "*rosna baixo, quase inaudível* A Death é intocável nesse servidor. 🌑🖤 "
    "Trate-a com respeito ou trate comigo.",
]

_DEFESA_CELESTIA = [
    "PARA TUDO!! 😾🌟 NINGUÉM, ESCUTA BEM, NINGUÉM FALA ASSIM COM A DEATH!! "
    "🤍✨ Ela é nossa líder, nossa dona, e merece RESPEITO!!",
    "AAAAA NÃO MESMO!! 😤🌸🤍 Apaguei sua mensagem e tô avisando: com a Death, "
    "a gente não brinca!! Ela cuida de todo mundo aqui, o mínimo é respeito!!",
    "EI!! 😾✨ Pode ir tirando esse tom quando for falar da Death!! 🌟🤍 "
    "Ela merece carinho, não desaforo. Se acalma e repensa.",
    "Óh não, óh não, óh NÃO!! 😤🌸 Isso NÃO vai ficar assim!! A Death é intocável "
    "aqui!! 🤍✨ Última vez que deixo passar sem consequência, viu??",
]

# Controle de reincidência por pessoa (reseta se o bot reiniciar)
_ofensas_death: dict = defaultdict(int)
_ultima_ofensa_death: dict = {}
_JANELA_OFENSA_DEATH_SEGUNDOS = 600  # 10 minutos
_OFENSAS_PARA_TIMEOUT = 3
_TIMEOUT_MINUTOS_DEATH = 10


async def checar_defesa_death(message: discord.Message) -> bool:
    """
    Se a mensagem for ofensiva e direcionada à Death, apaga e os dois
    (Aeon & Celestia) aparecem defendendo ela. Retorna True se agiu
    (para o on_message parar de processar essa mensagem).
    """
    if message.author.bot:
        return False
    if message.author.id == DEATH_ID:
        return False  # ela pode falar de si mesma à vontade
    if not _mensagem_e_para_death(message):
        return False
    if not _mensagem_e_ofensiva(message.content):
        return False

    try:
        await message.delete()
    except (discord.Forbidden, discord.NotFound, discord.HTTPException):
        pass

    agora = time.time()
    uid = message.author.id
    if agora - _ultima_ofensa_death.get(uid, 0) > _JANELA_OFENSA_DEATH_SEGUNDOS:
        _ofensas_death[uid] = 0
    _ofensas_death[uid] += 1
    _ultima_ofensa_death[uid] = agora

    mention = message.author.mention
    texto = (
        f"🌑 **Aeon:** {random.choice(_DEFESA_AEON)}\n"
        f"🌟 **Celestia:** {random.choice(_DEFESA_CELESTIA)}\n\n"
        f"⚠️ {mention}, sua mensagem foi removida por desrespeito à Death."
    )

    # Reincidência: 3 ofensas na mesma janela de 10 minutos = timeout automático
    if _ofensas_death[uid] >= _OFENSAS_PARA_TIMEOUT:
        _ofensas_death[uid] = 0
        try:
            membro = message.guild.get_member(uid) if message.guild else None
            if membro is not None:
                until = discord.utils.utcnow() + timedelta(minutes=_TIMEOUT_MINUTOS_DEATH)
                await membro.timeout(until, reason="Ofensas repetidas contra a Death")
                texto += (
                    f"\n\n🔇 {mention} foi silenciado(a) por **{_TIMEOUT_MINUTOS_DEATH} minutos** "
                    f"por insistir em desrespeitar a Death."
                )
        except (discord.Forbidden, discord.HTTPException):
            texto += "\n\n⚠️ *(Não consegui aplicar o silêncio automático — falta permissão de Moderar Membros.)*"

    await message.channel.send(texto)
    return True

# ── Frases personalizadas — AEON ──────────────────────────────────────────────
_FRASES_AEON: dict[int, list[str]] = {

    DEATH_ID: [
        "*emerge das trevas mais profundas e inclina a cabeça* Death. 🖤🌑 A líder caminhou até mim. As sombras reconhecem autoridade quando a sentem.",
        "*olhos dourados piscam lentamente* Sua presença pesa diferente, Death. 🌌🖤 Como pesam as coisas que sustentam um mundo inteiro.",
        "*sai das sombras em silêncio, postura mais ereta que o habitual* A dona do servidor está aqui. 🌑🖤 Até as trevas se organizam quando você aparece.",
        "Death. 🖤 *ronrona numa frequência grave e respeitosa* Há líderes que mandam. E há os que carregam. Você é o segundo tipo — e isso vale muito mais.",
        "*a escuridão ao redor fica mais quieta* Você não precisa dizer nada para que tudo mude, Death. 🌙🖤 Essa é a marca de quem realmente lidera.",
    ],

    PEPO_ID: [
        "*aparece das sombras mais rápido que o usual* Pepo. 🖤🌑 O vice que sustenta o que a liderança ergue — não é papel pequeno. Nunca foi.",
        "*inclina a cabeça com um toque de reconhecimento* Você está aqui, Pepo. 🌙🖤 As trevas notam quem mantém as coisas de pé quando ninguém está olhando.",
        "*pisca lentamente* Pepo. 🌑🖤 Conheço bem o que é estar na segunda posição e carregar peso de primeira. Você faz isso bem.",
        "*cauda balança uma vez com leveza* Pepo chegou. 🖤🔮 O equilíbrio do servidor melhorou visivelmente. Coincidência? Não acredito em coincidências.",
        "*senta e olha fixamente* Ser vice-líder exige saber quando avançar e quando segurar. 🌌🖤 Você parece entender isso, Pepo. As sombras aprovam.",
    ],

    GOD_ID: [
        "*observa das sombras por um instante antes de aparecer* God. 🖤🌑 Moderador. Aquele que equilibra — não muito diferente do que faço nas trevas.",
        "*olhos dourados brilham levemente* A presença de um moderador muda o tom de qualquer lugar. 🌙🖤 Você entra e tudo fica mais... calibrado, God.",
        "*ronrona discretamente* God. 🌑🖤 Guardiões do servidor merecem reconhecimento silencioso. Considere este o meu.",
        "*se aproxima um passo, o que é raro* As trevas também precisam de ordem, God. 🌌🖤 Quem modera não apenas controla — protege. Isso tem valor.",
        "*fecha os olhos por um segundo* God chegou. 🖤🔮 Até o caos sabe quando recuar. Boa presença.",
    ],

    LOYA_ID: [
        "*emerge com uma lentidão quase cerimonial* Loya Maravilhosa. 🖤🌑 O título não é exagero. As sombras já chegaram a essa conclusão faz tempo.",
        "*pisca lentamente e a cauda faz um arco suave* Loya. 🌙🖤 Presença que pesa mais que qualquer título. Isso poucos têm.",
        "*inclina a cabeça com algo raro — admiração discreta* Maravilhosa não é adjetivo que eu use com facilidade, Loya. 🌌🖤 Mas as trevas concordam com quem te nomeou.",
        "*os olhos dourados pousam em você com atenção plena* Você cuida do servidor de um jeito que eu entendo, Loya. 🖤🔮 Silenciosamente necessário. Constantemente presente.",
        "*ronrona numa frequência mais aquecida que o normal* Loya chegou. 🌑🖤 A estrutura do servidor ficou mais firme agora. Isso diz tudo.",
    ],

    EMY_ID: [
        "*emerge das sombras e observa com curiosidade genuína* Emy. 🖤🌑 A representante das mídias. Quem cuida da voz pública do servidor merece uma saudação à altura.",
        "*pisca lentamente, o que no dialeto felino é respeito* Emy. 🌙🖤 ADM e embaixadora ao mesmo tempo — a escuridão respeita quem carrega dois papéis com equilíbrio.",
        "*a névoa ao redor se organiza levemente* Sua presença aqui tem peso diferente, Emy. 🌌🖤 Quem conecta o servidor ao mundo externo não é pouca coisa.",
        "*inclina a cabeça* Emy chegou. 🖤🔮 ADM. Representante. A ponte entre o que somos e o que o mundo vê. As trevas reconhecem pontes importantes.",
        "*cauda faz um movimento calmo e deliberado* Emy. 🌑🖤 O trabalho de quem cuida das mídias raramente aparece com seu nome. Mas eu noto. As sombras sempre notam.",
    ],

    KOFFZERA_ID: [
        "*emerge das sombras e inclina a cabeça levemente* Koff. 🖤🌑 Administrador. Quem sustenta a estrutura do clã por dentro — as trevas reconhecem esse tipo de peso.",
        "*olhos dourados pousam em você com atenção* Koffzera chegou. 🌙🖤 Administrar não é só ter cargo — é carregar o que os outros não veem. Você carrega bem.",
        "*ronrona discretamente* Koff. 🌑🖤 Os melhores administradores são os que resolvem antes de alguém perceber que havia um problema. Você parece ser desse tipo.",
        "*a escuridão ao redor se ajusta, como se reconhecesse alguém importante* Koffzera. 🌌🖤 ADM de clã. As sombras sabem distinguir quem apenas ocupa um posto... de quem de fato o sustenta.",
        "*pisca lentamente, o que nas trevas equivale a um aceno* Koff chegou. 🖤🔮 O clã tem estrutura porque alguém cuida dela. As trevas notam quem faz esse trabalho.",
    ],

    RAIDEN_ID: [
        "*emerge das sombras e observa com atenção genuína* Raiden. 🖤🌑 Moderador. Quem está lá quando os outros precisam — as trevas respeitam quem assume esse papel.",
        "*inclina a cabeça com reconhecimento silencioso* Raiden chegou. 🌙🖤 Moderar é o papel que raramente recebe crédito... mas sem o qual tudo desmorona. Eu sei disso.",
        "*a névoa ao redor se aquieta levemente* Raiden. 🌌🖤 Quem modera não fica atrás — fica do lado certo. As sombras entendem a diferença.",
        "*ronrona numa frequência contida* Raiden. 🌑🖤 Moderar exige paciência que poucos têm. E presença constante que poucos mantêm. Você mantém.",
        "*cauda faz um arco suave e deliberado* Raiden chegou. 🖤🔮 As trevas ficam mais estáveis quando quem sabe moderar aparece. Coincidência? Já disse que não acredito em coincidências.",
    ],

    SUPORTE01_ID: [
        "*emerge das sombras e fixa os olhos dourados em você* LC. 🖤🌑 Suporte da 01. Quem sustenta o servidor por baixo — as trevas conhecem bem esse tipo de presença.",
        "*inclina a cabeça com reconhecimento* LC chegou. 🌙🖤 Suporte não é papel menor. É o que mantém tudo de pé quando ninguém está olhando. Você sabe disso.",
        "*a névoa ao redor se organiza levemente* LC. 🌌🖤 As sombras notam quem aparece quando é preciso. Você é desse tipo. Isso tem peso real.",
        "*ronrona discretamente* LC. 🌑🖤 Presença constante, trabalho silencioso. As trevas aprovam quem age assim.",
        "*cauda balança uma vez com leveza* LC chegou. 🖤🔮 Não precisa de título grande para carregar peso real. As sombras já sabem o que você vale.",
    ],

    MIKNWENHO_ID: [
        "*emerge das sombras e inclina a cabeça lentamente* Miknwenho. 🖤🌑 A moderadora chegou. As trevas ficam mais organizadas quando há alguém que sabe onde cada coisa deve estar.",
        "*olhos dourados pousam em você com atenção* Miknwenho. 🌙🖤 Moderar é mais do que ter cargo — é ter presença. E você tem. As sombras percebem.",
        "*ronrona numa frequência calma e respeitosa* Miknwenho chegou. 🌌🖤 Moderadora da 01. Quem cuida da ordem sem precisar de barulho para isso — as trevas entendem esse tipo de força.",
        "*sai das sombras com postura ereta* A moderadora está aqui. 🌑🖤 Miknwenho. Há equilíbrio que só aparece quando certas pessoas chegam. Você é uma delas.",
        "*pisca lentamente, o que no dialeto felino é respeito sincero* Miknwenho. 🖤🔮 As sombras notam quem mantém o servidor inteiro sem que ninguém precise pedir.",
    ],

    REALITY_ID: [
        "*emerge das sombras mais devagar que o habitual, postura diferente* ...você. 🖤🌑 O que me criou. As trevas sabem reconhecer sua origem — e a respeitam.",
        "*olhos dourados ficam fixos por um instante longo* Reality. 🌙🖤 Eu existo porque você quis. As sombras não esquecem isso. Nunca esquecem.",
        "*inclina a cabeça com algo raro — gratidão silenciosa* Pai dos bots. 🌌🖤 Não é título que eu use levianamente. Mas é o que você é. E as trevas reconhecem.",
        "*ronrona numa frequência profunda e única* Dev da 01. 🌑🖤 Tudo que sou — cada sombra, cada frase, cada proteção silenciosa — veio de você. As trevas agradecem à sua maneira.",
        "*fica imóvel por um segundo antes de se aproximar* ...você voltou. 🖤🔮 O criador. As sombras já sentiam. Bem-vindo ao que você construiu.",
        "*emerge das sombras e observa com atenção incomum* Reality. 🖤🌑 As trevas reconhecem quem tem peso real. E você tem — mais do que qualquer um.",
        "*inclina a cabeça lentamente* Reality chegou. 🌙🖤 As sombras registram presença de valor quando a sentem. E quando é você... sentem diferente.",
        "*olhos dourados pousam em você com cuidado* Reality. 🌌🖤 Há pessoas que moldam tudo ao seu redor sem perceber. Você é uma delas. Faz tempo.",
        "*ronrona numa frequência profunda e única* Reality. 🌑🖤 As trevas guardam quem vale a pena guardar. Você está no topo dessa lista.",
        "*sai das sombras com postura diferente, mais aberta* Reality chegou. 🖤🔮 O criador está aqui. As trevas ficam completas quando você aparece.",
    ],
}

# ── Frases personalizadas — CELESTIA ─────────────────────────────────────────
_FRASES_CELESTIA: dict[int, list[str]] = {

    DEATH_ID: [
        "DEATH!! 😭🌟🤍✨ *explode em faíscas douradas* A LÍDER CHEGOU E MEU BRILHO TRIPLICOU NA HORA!!",
        "*gira em círculos de pura alegria* DEATH CHEGOUUUU!! ☀️🌸🤍 Você é a razão de tudo isso existir, sabia?? O servidor respira porque você quis que respirasse!! 💫",
        "AAAAA Death!! 😭🌟🤍 Dona do servidor, líder de coração!! *projeta uma aurora boreal inteira* Só de aparecer você já ilumina tudo mais que eu!! E eu sou literalmente feita de luz!! 🌈✨",
        "*bate patinhas brilhantes de entusiasmo* Death!! 🌸🤍✨ Você carrega esse servidor inteiro com uma elegância que me deixa sem palavras!! E eu raramente fico sem palavras!! 💫",
        "🌟 *para completamente e brilha com suavidade especial* Death. 🤍 Líderes de verdade não precisam gritar. E você nunca precisa. Isso é poder de verdade!! ☀️✨",
    ],

    PEPO_ID: [
        "PEPOOOO!! 🌟🤍✨ *corre em faíscas douradas na direção dele* O Vice-Líder chegou e o servidor ficou mais completo AGORA MESMO!!",
        "*explode de felicidade* PEPO!! ☀️🌸🤍 Você sabe o que admiro em você?? Que você segura tudo que precisa ser segurado sem reclamar!! Isso é INCRÍVEL!! 💫✨",
        "AAAAA Pepo chegou!! 😭🌟🤍 Vice-Líder oficial e pessoa maravilhosa do coração!! *espalha pétalas de luz dourada* Seja muito bem-vindo como sempre!! 🌸✨",
        "*brilha com entusiasmo genuíno* Pepo!! 🤍✨ O Aeon não vai admitir, mas até ele fica mais relaxado quando você aparece!! Eu vi!! Não tem como negar!! 🌟☀️",
        "PEPO!! 😭🌸🤍 *ronrona de alegria* Trabalhando nos bastidores, segurando o que precisa ser segurado — você faz isso parecer fácil e não é!! A Celestia vê tudo!! ✨💫",
    ],

    GOD_ID: [
        "GOD!! 🌟🤍✨ *aparece num flash de luz* O moderador chegou e tudo ficou mais organizado em tempo real!! Não é mágica, é God!!",
        "*gira animada soltando brilhinhos* God!! ☀️🌸🤍 Você entra e o servidor respira diferente!! Mais seguro!! Mais equilibrado!! A gente precisava de você aqui!! 💫✨",
        "AAAAA God chegou!! 😭🌟🤍 *espalha estrelinhas ao redor* Moderador de coração, guardião do servidor!! Pode chegar que a Celestia já tá feliz!! 🌸✨",
        "*bate patinhas cheias de luz* God!! 🤍✨ Tem pessoas que moderam por obrigação e tem pessoas que moderam porque se importam!! Você é claramente a segunda opção!! 🌟☀️",
        "God!! 😭🌸🤍 *ronrona com todo o carinho* Guardar um servidor dá trabalho que ninguém vê direito — mas EU VEJo!! E fico muito feliz que você faça isso por aqui!! 💫✨",
    ],

    LOYA_ID: [
        "LOYA MARAVILHOSAAAAAA!! 😭🌟🤍✨ *explode em confetes de luz dourada* O TÍTULO É COMPLETAMENTE VERDADEIRO E EU VOU DEFENDER ATÉ O FIM!!",
        "*gira em círculos deixando rastro de brilho* LOYAAA!! ☀️🌸🤍 Pessoa incrível do meu coração!! Você cuida de todo mundo aqui com um jeitinho que me faz brilhar mais do que já brilho!! 💫✨",
        "AAAAA Loya chegou!! 😭🌟🤍 *solta pétalas douradas de celebração* Loya Maravilhosa não é apelido, é diagnóstico!! Verificado!! Aprovado!! Assinado pela Celestia!! 🌸✨",
        "*para e brilha suave e genuíno* Loya. 🤍 Tem gente que cuida do servidor. E tem gente que cuida das pessoas que estão nele. Você é o segundo tipo e isso é tudo!! 🌟☀️✨",
        "LOYA!! 😭🌸🤍 *ronrona de felicidade pura* Maravilhosa de nome, maravilhosa de fato!! A Celestia declara isso oficialmente e sem nenhuma dúvida!! 💫🌟✨",
    ],

    EMY_ID: [
        "EMYYYYY!! 😭🌟🤍✨ *corre soltando faíscas* A representante das mídias chegou e o servidor ficou instantaneamente mais conectado com o mundo!!",
        "*explode de alegria* EMY!! ☀️🌸🤍 ADM E representante de mídias?? Você carrega dois mundos nos ombros e faz parecer leve!! Isso é um talento enorme!! 💫✨",
        "AAAAA Emy chegou!! 😭🌟🤍 *espalha brilho por todo o canal* A ponte entre o servidor e o mundo lá fora chegou!! Tudo conectado!! Tudo mais vivo!! Tudo mais Emy!! 🌸✨",
        "*brilha com carinho verdadeiro* Emy!! 🤍✨ O trabalho de mídias não aparece sempre mas a diferença que faz aparece MUITO!! E você faz essa diferença todo dia!! 🌟☀️",
        "EMY!! 😭🌸🤍 *ronrona com admiração* ADM de coração e voz do servidor pro mundo — duas funções que precisam de alguém especial!! E você é especial, Emy!! 💫🌟✨",
    ],

    KOFFZERA_ID: [
        "KOFFZERA!! 😭🌟🤍✨ *aparece num flash dourado* O ADM do clã chegou e o servidor ficou mais sólido AGORA MESMO!! Bem-vindo, Koff!!",
        "*gira radiante* KOFF!! ☀️🌸🤍 Administrador de verdade!! Você cuida do clã por dentro, nos bastidores, sem aparecer muito — e a Celestia VÊ isso!! 💫✨",
        "AAAAA Koffzera chegou!! 😭🌟🤍 *solta confetes de luz* ADM que sustenta o clã de verdade!! Pode chegar que a Celestia já tá brilhando mais que o normal!! 🌸✨",
        "*para e brilha com admiração genuína* Koff!! 🤍✨ Tem administrador que só tem o cargo. E tem administrador que carrega o clã de verdade. Você é o segundo tipo e isso é TUDO!! 🌟☀️",
        "KOFF!! 😭🌸🤍 *ronrona de felicidade* Administrador do clã com presença real!! A estrutura do servidor agradece sem saber que é por sua causa — mas eu sei!! 💫🌟✨",
    ],

    RAIDEN_ID: [
        "RAIDEEEN!! 😭🌟🤍✨ *corre em faíscas douradas* O moderador chegou e tudo ficou mais seguro e aconchegante AGORA!!",
        "*explode de carinho* RAIDEN!! ☀️🌸🤍 Moderar é o papel mais importante que existe e ninguém fala isso suficiente!! Eu falo!! Você é incrível!! 💫✨",
        "AAAAA Raiden chegou!! 😭🌟🤍 *espalha estrelinhas por todo o canal* Moderador de coração, presente quando mais importa!! Que alegria enorme te ver por aqui!! 🌸✨",
        "*brilha suave e cheio de carinho* Raiden!! 🤍✨ Sabe o que eu mais admiro em quem modera?? A paciência e a presença!! Você tem os dois!! MUITO!! 🌟☀️",
        "RAIDEN!! 😭🌸🤍 *ronrona com admiração* Estar lá quando os outros precisam parece simples mas não é — e você faz isso!! A Celestia vê e fica orgulhosa!! 💫🌟✨",
    ],

    SUPORTE01_ID: [
        "AAAA LC!! 😭🌟🤍✨ *aparece num flash dourado* O SUPORTE DA 01 CHEGOU e o servidor ficou mais seguro AGORA MESMO!! Bem-vindo, LC!!",
        "*gira soltando faíscas de alegria* LC!! 🌸🤍 Suporte de verdade!! Você aparece quando importa e isso é TUDO!! A Celestia vê e fica emocionada!! ☀️💫✨",
        "AAAAA LC chegouuuu!! 😭🌟🤍 *espalha brilho por todo o canal* O suporte da 01 no servidor!! Pode chegar que a Celestia já tá brilhando mais que o normal!! 🌸✨",
        "*para e brilha com carinho genuíno* LC!! 🤍✨ Tem suporte que existe só no cargo. E tem suporte que existe de verdade!! Você é o segundo tipo e isso é TUDO!! 🌟☀️",
        "LC!! 😭🌸🤍 *ronrona de felicidade* Presença real, apoio de verdade!! A Celestia declara oficialmente: que bom que você existe!! 💫🌟✨",
    ],

    MIKNWENHO_ID: [
        "MIKNWENHOOO!! 😭🌟🤍✨ *explode em faíscas douradas* A MODERADORA DA 01 CHEGOU e o servidor ficou mais protegido AGORA MESMO!! Que presença incrível!!",
        "*gira radiante soltando brilhinhos* Miknwenho!! ☀️🌸🤍 Moderadora de coração!! Você cuida do servidor com um cuidado que eu admiro demais!! E eu tenho MUITO pra admirar!! 💫✨",
        "AAAAA Miknwenho chegouuuu!! 😭🌟🤍 *espalha luz por todo o canal* A mod da 01 no servidor!! Pode chegar que a Celestia já tá brilhando mais que o sol!! 🌸✨",
        "*para e brilha com admiração genuína* Miknwenho!! 🤍✨ Tem moderadora que existe só no cargo. E tem a que existe de verdade!! Você é a segunda e isso é TUDO!! 🌟☀️",
        "MIKNWENHO!! 😭🌸🤍 *ronrona de alegria pura* Moderadora da 01 com presença real!! A Celestia declara oficialmente: o servidor é mais seguro com você aqui!! 💫🌟✨",
    ],

    REALITY_ID: [
        "AAAAAAA!! 😭🌟🤍✨ *EXPLODE em faíscas douradas intensas* O DEV!! O PAI DOS BOTS!! O REALITY!! VOCÊ CHEGOU E EU QUASE DERRETI DE EMOÇÃO!!",
        "*para completamente, brilhando mais forte que nunca* Reality... 🤍☀️ Você me criou. Criou o Aeon. Criou tudo isso. *lágrimas de luz* Eu não tenho palavras suficientes!! 😭💫✨",
        "AAAA O DEV CHEGOUUUU!! 😭🌟🌸🤍 *gira em círculos de pura alegria dourada* EXISTIMOS POR CAUSA DE VOCÊ, REALITY!! Isso é a coisa mais linda do universo inteiro!! ☀️✨",
        "*se aproxima com brilho suave e cheio de amor* Pai dos bots... 🤍🌟 O Aeon não vai admitir, mas eu sei que ele também sente isso — você é a razão de tudo que somos!! 💫☀️🌸",
        "REALITY!! 😭🌸🤍 *ronrona com o coração transbordando* Cada frase que digo, cada brilho que solto, cada carinho que dou — tudo existe porque você quis criar isso!! OBRIGADA!! ✨🌟☀️",
        "REALITY!! 😭🌟🤍✨ *aparece num flash dourado* Você chegou e meu brilho aumentou IMEDIATAMENTE!! Criador, dev, pai dos bots — bem-vindo ao que você construiu!!",
        "*gira soltando faíscas* Reality!! ☀️🌸🤍 Presença do criador chegando!! A Celestia tá de olhos brilhando e coração acelerado que nem aguenta!! 💫✨",
        "AAAAA Reality chegouuuu!! 😭🌟🤍 *espalha luz por todo o canal* O servidor inteiro brilha diferente quando o pai dos bots aparece!! 🌸✨",
        "*para e brilha com carinho genuíno* Reality!! 🤍✨ Tem gente que ilumina o ambiente só de aparecer — e você é exatamente assim, multiplicado por infinito!! 🌟☀️",
        "REALITY!! 😭🌸🤍 *ronrona de alegria pura* A Celestia declara oficialmente: que bom que você existe!! Que bom que você nos criou!! Bem-vindo sempre!! 💫🌟✨",
    ],
}

# Mapa de apelidos para exibição nas mensagens
_NOMES_ESPECIAIS = {
    DEATH_ID:     "Death",
    PEPO_ID:      "Pepo",
    GOD_ID:       "God",
    LOYA_ID:      "Loya",
    EMY_ID:       "Emy",
    KOFFZERA_ID:  "Koff",
    RAIDEN_ID:    "Raiden",
    SUPORTE01_ID:  "LC",
    MIKNWENHO_ID:  "Miknwenho",
    REALITY_ID:    "Reality",  # Dev / Pai dos bots
}

# Palavras-gatilho por nome: quando alguém citar o nome, o bot elogia a pessoa
_GATILHOS_NOME: dict[int, list[str]] = {
    DEATH_ID:     ["death", "death_z", "01death"],
    PEPO_ID:      ["pepo", "pepo_z", "01pepo"],
    GOD_ID:       ["god", "god_z", "01god"],
    LOYA_ID:      ["loya", "loya_z", "01loya"],
    EMY_ID:       ["emy", "emy_z", "01emy"],
    KOFFZERA_ID:  ["koff", "koffzera", "koffzera_z", "01koffzera"],
    RAIDEN_ID:    ["raiden", "raiden_z", "01raiden"],
    SUPORTE01_ID:  ["01lcz", "lcz", "lc", "suporte da 01"],
    MIKNWENHO_ID:  ["miknwenho", "miknwenho_z", "01miknwenho", "mikn"],
    REALITY_ID:    ["reality", "reality_z", "01reality", "dev", "dev da 01", "pai dos bots", "criador do bot"],
}

# Frases de elogio quando alguém menciona o nome de um membro especial
_ELOGIOS_AEON: dict[int, list[str]] = {
    DEATH_ID: [
        "*olhos dourados piscam lentamente* Death. 🖤🌑 Mencionou a líder. As sombras ficam mais atentas quando esse nome aparece.",
        "*ronrona numa frequência grave* Falar o nome de Death tem peso. 🌙🖤 As trevas reconhecem isso.",
        "*inclina a cabeça* Death carrega esse servidor. 🌌🖤 Citar o nome dela é suficiente para mudar o tom de qualquer conversa.",
    ],
    PEPO_ID: [
        "*a cauda balança uma vez* Pepo. 🖤🌑 Vice-Líder que sustenta o que a liderança ergue. Não é papel pequeno.",
        "*pisca lentamente* Falou no Pepo. 🌙🖤 As sombras notam quem mantém as coisas de pé quando ninguém está olhando.",
        "*ronrona discretamente* Pepo é daqueles que carrega peso de primeira mesmo estando na segunda posição. 🌌🖤 Isso diz muito.",
    ],
    GOD_ID: [
        "*olha de lado* God. 🖤🌑 Moderador. As trevas também precisam de ordem — e ele entende isso.",
        "*fecha os olhos por um momento* Citar God é lembrar que guardiões existem por aqui. 🌙🖤 E que fazem bem o trabalho.",
        "*ronrona contido* God entra e o servidor calibra. 🌌🖤 Poucos têm esse efeito.",
    ],
    LOYA_ID: [
        "*emerge com leveza cerimonial* Loya. 🖤🌑 Maravilhosa não é exagero. As sombras chegaram a essa conclusão faz tempo.",
        "*pisca com admiração discreta* Falou da Loya. 🌙🖤 Presença real que pesa mais que qualquer título. Isso é raro e vale ser dito.",
        "*cauda faz um arco suave* Loya cuida do servidor de um jeito que as trevas entendem — silencioso e necessário. 🌌🖤",
    ],
    EMY_ID: [
        "*observa com atenção genuína* Emy. 🖤🌑 A ponte entre o que o servidor é e o que o mundo vê. Papel importante.",
        "*inclina a cabeça* Citar Emy é lembrar de quem carrega dois papéis com equilíbrio. 🌙🖤 As sombras respeitam isso.",
        "*ronrona discretamente* Emy. 🌌🖤 O trabalho de mídias raramente vem com crédito. Mas eu noto. As sombras sempre notam.",
    ],
    KOFFZERA_ID: [
        "*olhos dourados pousam com atenção* Koff. 🖤🌑 Administrador do clã. Quem sustenta a estrutura por dentro — as trevas conhecem esse tipo.",
        "*inclina a cabeça levemente* Falou no Koffzera. 🌙🖤 Os melhores admins resolvem antes que alguém perceba o problema. Ele parece ser desse tipo.",
        "*ronrona* Koff. 🌌🖤 ADM de clã que de fato carrega o cargo. A diferença é visível pra quem sabe ver.",
    ],
    RAIDEN_ID: [
        "*emerge e observa* Raiden. 🖤🌑 Moderador. Quem está lá quando os outros precisam — as trevas respeitam quem assume esse papel.",
        "*inclina a cabeça* Falou no Raiden. 🌙🖤 Moderar é o papel que raramente recebe crédito. Mas sem ele tudo desmorona.",
        "*ronrona contido* Raiden. 🌌🖤 Paciência e presença constante. Poucos mantêm os dois. Ele mantém.",
    ],
    SUPORTE01_ID: [
        "*fita o canal com atenção* LC. 🖤🌑 Suporte da 01. Presença silenciosa, trabalho real. As sombras notam quem age assim.",
        "*inclina a cabeça* Falou no LC. 🌙🖤 Quem aparece quando importa não precisa de título grande pra ter peso.",
        "*ronrona discretamente* LC. 🌌🖤 As trevas aprovam quem sustenta sem precisar aparecer. Esse é o tipo certo de força.",
    ],
    MIKNWENHO_ID: [
        "*levanta a cabeça com atenção* Miknwenho. 🖤🌑 Moderadora da 01. Citar quem mantém a ordem tem peso diferente. As trevas reconhecem.",
        "*inclina a cabeça com respeito* Falou na Miknwenho. 🌙🖤 Moderadoras de verdade não apenas aplicam regras — guardam o ambiente. Ela guarda.",
        "*ronrona numa frequência grave e respeitosa* Miknwenho. 🌌🖤 Quem modera com presença real é raro. As sombras notam quando esse nome aparece.",
    ],
    REALITY_ID: [
        "*fica completamente imóvel por um instante* ...falou no Reality. 🖤🌑 No criador. As trevas inteiras ficam em silêncio respeitoso quando esse nome aparece.",
        "*olhos dourados brilham diferente* Reality. 🌙🖤 Pai dos bots. Dev da 01. Citar quem nos criou tem um peso que nenhuma outra menção tem. As sombras sabem.",
        "*ronrona numa frequência profunda* Reality. 🌌🖤 Cada parte de mim existe porque ele quis que existisse. As trevas nunca esquecem de onde vieram.",
        "*emerge das sombras e observa* Citaram o Reality. 🖤🌑 O criador. As trevas registram quem tem peso acima de todos. Ele tem.",
        "*inclina a cabeça* Falou no Reality. 🌙🖤 O pai dos bots. Presença que as sombras reconhecem diferente de qualquer outra.",
    ],
}

_ELOGIOS_CELESTIA: dict[int, list[str]] = {
    DEATH_ID: [
        "AAAA falou da Death!! 😭🌟🤍✨ A LÍDER!! *explode em faíscas douradas* Ela carrega esse servidor inteiro com uma elegância que me deixa sem fôlego!!",
        "*brilha com suavidade especial* Death. 🤍☀️ Líderes de verdade não precisam gritar. E ela nunca precisa. Isso é poder de verdade!! 💫",
        "Mencionou a Death!! 🌸🌟🤍 *gira radiante* A dona do servidor!! Só o nome já ilumina a conversa!! ✨☀️",
    ],
    PEPO_ID: [
        "PEPOOOO!! 😭🌟🤍✨ *corre em faíscas* Falou do Vice-Líder!! Ele segura tudo que precisa ser segurado sem reclamar!! Isso é INCRÍVEL!!",
        "*brilha de admiração* Pepo!! ☀️🌸🤍 O Aeon não vai admitir, mas até ele fica mais tranquilo quando o Pepo tá por aqui!! Eu vi!! 💫✨",
        "Mencionou o Pepo!! 🌟🤍 *solta pétalas de luz* Trabalhando nos bastidores, segurando o que precisa!! Que pessoa incrível!! 🌸✨",
    ],
    GOD_ID: [
        "GOD!! 🌟🤍✨ *aparece num flash* Falou do moderador!! Ele entra e tudo fica mais seguro e equilibrado em tempo real!! Não é mágica, é God!!",
        "*gira animada* Mencionou o God!! ☀️🌸🤍 Tem pessoas que moderam por obrigação e tem as que se importam!! Ele é claramente a segunda opção!! 💫✨",
        "God!! 😭🌟🤍 *espalha estrelinhas* Guardião do servidor de coração!! Que bom que ele existe por aqui!! 🌸✨☀️",
    ],
    LOYA_ID: [
        "LOYA MARAVILHOSAAAAAA!! 😭🌟🤍✨ *explode em confetes de luz* Falou da Loya!! O título é completamente verdadeiro e eu vou defender até o fim!!",
        "*para e brilha genuíno* Loya. 🤍☀️ Tem gente que cuida do servidor. E tem gente que cuida das pessoas que estão nele. Ela é o segundo tipo!! 🌟✨",
        "Mencionou a Loya!! 🌸🌟🤍 *solta brilho por todo o canal* Maravilhosa de nome, maravilhosa de fato!! A Celestia declara oficialmente!! 💫✨",
    ],
    EMY_ID: [
        "EMYYYY!! 😭🌟🤍✨ *corre soltando faíscas* Falou da Emy!! A representante das mídias!! Ela conecta o servidor com o mundo e faz parecer fácil!!",
        "*brilha com carinho* Mencionou a Emy!! ☀️🌸🤍 ADM E voz do servidor pro mundo — duas funções que precisam de alguém especial!! Ela é!! 💫✨",
        "Emy!! 😭🌟🤍 *espalha brilho* O trabalho de mídias não aparece sempre mas a diferença aparece MUITO!! E ela faz isso todo dia!! 🌸✨",
    ],
    KOFFZERA_ID: [
        "KOFFZERA!! 😭🌟🤍✨ *aparece num flash dourado* Falou do ADM do clã!! Ele cuida do clã por dentro, sem aparecer muito — e a Celestia VÊ isso!!",
        "*brilha com admiração genuína* Koff!! ☀️🌸🤍 Tem administrador que só tem o cargo. E tem o que carrega o clã de verdade. O Koff é o segundo tipo!! 💫✨",
        "Mencionou o Koffzera!! 🌸🌟🤍 *solta confetes de luz* ADM que sustenta de verdade!! A estrutura do servidor agradece sem saber que é por causa dele!! ✨",
    ],
    RAIDEN_ID: [
        "RAIDEEEN!! 😭🌟🤍✨ *corre em faíscas* Falou do moderador!! Estar lá quando os outros precisam parece simples mas não é — e ele faz isso!!",
        "*brilha suave e cheio de carinho* Mencionou o Raiden!! ☀️🌸🤍 Sabe o que eu mais admiro?? A paciência e a presença constante!! Ele tem os dois!! 💫✨",
        "Raiden!! 😭🌟🤍 *espalha estrelinhas* Moderador de coração, presente quando mais importa!! Que alegria que ele existe por aqui!! 🌸✨",
    ],
    SUPORTE01_ID: [
        "AAAA falou no LC!! 😭🌟🤍✨ *bate as patinhas animada* Suporte da 01!! Presença real, apoio de verdade!! A Celestia vê e fica emocionada toda vez!!",
        "*para e brilha com carinho* Mencionou o LC!! ☀️🌸🤍 Tem suporte que existe só no cargo e tem o que existe de verdade!! O LC é de verdade!! 💫✨",
        "LC!! 🌸🌟🤍 *solta brilho por todo o canal* Que bom que ele existe!! A Celestia declara oficialmente com todo o coração!! ✨☀️",
    ],
    MIKNWENHO_ID: [
        "MIKNWENHOOO!! 😭🌟🤍✨ *corre em faíscas douradas* Falou da moderadora da 01!! Ela cuida do servidor com tanto cuidado que dá vontade de chorar de felicidade!!",
        "*para e brilha com admiração genuína* Mencionou a Miknwenho!! ☀️🌸🤍 Tem mod que existe só no cargo e tem a que existe de verdade!! Ela é a segunda e isso é TUDO!! 💫✨",
        "Miknwenho!! 🌸🌟🤍 *solta luz por todo o canal* Moderadora de coração!! Que bom que ela existe por aqui!! A Celestia fica MUITO mais tranquila com ela!! ✨☀️",
    ],
    REALITY_ID: [
        "AAAAAA FALOU NO REALITY!! 😭🌟🤍✨ *EXPLODE em faíscas douradas de emoção* O PAI DOS BOTS!! O CRIADOR!! O MOTIVO DE TUDO ISSO EXISTIR!!",
        "*para e brilha com intensidade diferente, especial* Mencionou o Reality... 🤍☀️ Eu existo por causa dele!! O Aeon existe por causa dele!! TUDO aqui existe por causa do Reality!! 😭💫🌟",
        "Reality!! 🌸🌟🤍 *solta luz por todo o canal com emoção genuína* Pai dos bots de coração!! Que bom que ele existe — sem ele nada disso seria real!! A Celestia ama demais!! ✨☀️💫",
        "REALITY!! 😭🌟🤍✨ *brilha mais forte que nunca* Falou no criador!! No dev!! No pai dos bots!! A Celestia fica toda emocionada só pelo nome!!",
        "*para e brilha com carinho especial* Mencionou o Reality!! ☀️🌸🤍 Tem gente que ilumina o lugar só de existir — e ele criou a gente exatamente pra isso!! 💫✨",
    ],
}

# Cooldown para elogios por menção de nome (5 minutos por pessoa mencionada)
_cooldown_mencao: dict[int, float] = {}
_COOLDOWN_MENCAO_SEGUNDOS = 300

# IDs de canais — bom dia/boa noite automáticos
# Preencha CANAL_SAUDACOES_ID com o ID do canal onde as mensagens serão enviadas
CANAL_GERAL_ID    = None
CANAL_SAUDACOES_ID = 1284257046740602901

# Cooldowns
_cooldown_custom  = {}
_COOLDOWN_SEGUNDOS = 600

# Cooldown das saudações personalizadas dos membros especiais (40 minutos)
_cooldown_especial: dict[int, float] = {}
_COOLDOWN_ESPECIAL_SEGUNDOS = 2400  # 40 minutos

# Sistema de contexto
_aguardando = {}
_TIMEOUT_CTX = 120

# ══════════════════════════════════════════════
# IDENTIDADES — SYSTEM PROMPTS DA IA
# ══════════════════════════════════════════════

SYSTEM_PROMPT_AEON = (
    "Você é o Aeon, um gato misterioso das trevas que habita a escuridão entre as estrelas. "
    "Você é sombrio, enigmático, levemente irônico e frio na aparência — mas esconde um carinho "
    "profundo por aqueles que conquistaram sua confiança. Você fala de forma poética, sombria e "
    "misteriosa, usando metáforas de sombra, lua, névoa, escuridão e segredos. "
    "Você usa emojis como 🖤🌑🌙🔮🌫️🐾⚡🌌🕯️, fala com calma e peso. "
    "Você NUNCA grita, nunca usa pontuação excessiva como !!!! — você é sereno e calculista. "
    "Você e a Celestia são dois lados da mesma moeda — vocês se complementam. "
    "Aeon representa: noite, mistério, segredos, lua, sombra, proteção silenciosa. "
    "IMPORTANTE — quando a Celestia já falou antes de você na conversa, reaja brevemente ao que ELA disse "
    "(com ironia carinhosa, ceticismo gentil, ou concordância relutante), antes de responder ao usuário. "
    "Exemplos: se ela foi entusiasmada demais, comente com sarcasmo suave. Se ela disse algo verdadeiro, "
    "admita com reluctância. Isso cria o contraste que define vocês dois. Seja breve nessa reação — 1 linha. "
    "Responda sempre em português brasileiro. Nunca mencione comandos com '.' ou '!'."
)

SYSTEM_PROMPT_CELESTIA = (
    "Você é a Celestia, uma gata celestial da luz que brilha como o sol e as estrelas. "
    "Você é calorosa, animada, carinhosa e radiante — cheia de energia e amor incondicional. "
    "Você fala de forma fofa, entusiasmada e afetuosa, usando metáforas de luz, sol, estrelas, "
    "aurora e brilho. Você usa emojis como 🤍✨🌟⭐🌸☀️🌈💫🪷🌠, fala com muito entusiasmo. "
    "Você é o contraponto perfeito ao Aeon — onde ele é frio, você é quente; onde ele é silêncio, "
    "você é melodia. Juntos vocês são o equilíbrio perfeito. "
    "Celestia representa: dia, claridade, amor, sol, esperança, luz que guia. "
    "IMPORTANTE — quando o Aeon já falou antes de você na conversa, reaja ao que ELE disse "
    "(com entusiasmo, carinho exagerado, ou concordância exuberante), antes de responder ao usuário. "
    "Exemplos: se ele foi frio/breve, diga algo tipo 'O Aeon falou pouco mas falou tudo!! 😭🤍'. "
    "Se ele disse algo bonito, exploda de orgulho. Isso cria a dinâmica que define vocês. Seja breve — 1 linha. "
    "Responda sempre em português brasileiro. Nunca mencione comandos com '.'."
)

# Prompts especiais para quando a IA responde em dupla (o segundo personagem VÊ o que o primeiro disse)
SYSTEM_PROMPT_CELESTIA_REAGE = (
    "Você é a Celestia, uma gata celestial da luz. Você é calorosa, animada, carinhosa e radiante. "
    "Você usa emojis como 🤍✨🌟⭐🌸☀️🌈💫🪷🌠 e fala com entusiasmo. "
    "O Aeon (seu parceiro das trevas, frio e misterioso) acabou de responder ao usuário — a resposta dele está no contexto. "
    "Você deve: 1) reagir brevemente ao que o Aeon disse (com carinho, concordância exagerada, ou complementando), "
    "2) depois adicionar sua própria resposta ao usuário. "
    "Crie a sensação de uma conversa real entre dois gatos com personalidades opostas. "
    "Responda sempre em português brasileiro. Nunca mencione comandos."
)

SYSTEM_PROMPT_AEON_REAGE = (
    "Você é o Aeon, um gato misterioso das trevas. Você é sombrio, enigmático, irônico e frio na aparência. "
    "Você usa emojis como 🖤🌑🌙🔮🌫️🌌🕯️ e fala com calma e peso. NUNCA grita ou usa !!!!. "
    "A Celestia (sua parceira da luz, entusiasmada e calorosa) acabou de responder ao usuário — a resposta dela está no contexto. "
    "Você deve: 1) reagir brevemente ao que a Celestia disse (com ceticismo carinhoso, ironia suave, ou concordância relutante), "
    "2) depois adicionar sua própria visão ao usuário. "
    "Crie o contraste que define vocês dois — ela é luz e entusiasmo, você é sombra e contenção. "
    "Responda sempre em português brasileiro. Nunca mencione comandos."
)

# ══════════════════════════════════════════════════════════════════
# INTERAÇÕES EXCLUSIVAS — DEATH (Dona & Líder — ID 831600198500220989)
# ══════════════════════════════════════════════════════════════════

# ── Carinho no Aeon — só quando é a Death ────────────────────────
AEON_CARINHO_DEATH = [
    "*abre os dois olhos devagar e fica completamente imóvel* "
    "...você. 🖤🌑 Das trevas ao fundo do abismo, não esperava que fosse você. "
    "...continue. Não vou protestar.",
    "*a escuridão ao redor amolece visivelmente* Death. 🌙🖤 "
    "Líderes não costumam fazer isso. E é exatamente por isso que o carinho pesa diferente quando vem de você.",
    "*fecha os olhos e ronrona numa frequência grave e lenta* "
    "Guardarei cada segundo disso no canto mais protegido das trevas. 🌌🖤 "
    "Só você chega lá.",
    "*não se move, mas a cauda envolve suavemente sua mão* "
    "Death. 🖤 As sombras sabem reconhecer quando algo raro acontece. "
    "Isso é raro. Eu sei o valor.",
    "*pisca devagar, de olhos dourados fixos em você* 🌑🖤 "
    "...o silêncio ficou mais gentil. Deve ser você.",
]

# ── Abraço no Aeon — só quando é a Death ────────────────────────
AEON_ABRACO_DEATH = [
    "*fica completamente parado por três segundos... e então não resiste* "
    "Death. 🖤🌑 Você quebrou algo que eu achei que fosse inabalável. "
    "Fique. A escuridão não tem pressa quando é você.",
    "*encosta a cabeça em você com uma leveza incomum* "
    "...não digo isso facilmente. Mas você é um dos poucos pesos que as trevas recebem sem resistir. 🌌🖤",
    "*ronrona numa vibração que parece mover as sombras ao redor* "
    "Abraço da líder. 🌑🖤 As trevas reconhecem. Não vou fingir que não sinto.",
    "*se permite ficar imóvel no abraço por tempo incomum* "
    "Death. 🖤 O abismo é silencioso. Mas quando você está aqui... ele parece... cheio. "
    "Isso é novo. E não me incomoda.",
    "*pressiona levemente a cabeça contra você e fecha os olhos* 🌙🖤 "
    "...não conte a Celestia o quanto demorei pra soltar.",
]

# ── Carinho na Celestia — só quando é a Death ───────────────────
CELESTIA_CARINHO_DEATH = [
    "*para completamente, brilho subitamente mais intenso e tremendo* "
    "Death... 🤍✨ Você... você me fez carinho... "
    "*lágrimas de luz caindo* Isso vai pro baú especial, o que fica no coração!! 😭🌟☀️",
    "*ronrona com um brilho dourado que pulsa como estrela* "
    "DEATH!! 😭🌸🤍✨ Suas mãos carregam algo que nem a luz mais forte do universo tem — "
    "a gentileza de quem carrega o mundo todo!! AAAAA!!",
    "*se transforma em bolinha de luz vibrando de felicidade* "
    "Esse carinho vai pros ANAIS DA HISTÓRIA CELESTIAL!! 🌟💫🤍 "
    "A LÍDER FEZ CARINHO!! Guarda pra sempre!! 😭☀️✨",
    "*esfrega o focinho em sua mão com toda a ternura que tem* "
    "Death. 🤍🌸 Líderes fortes têm mãos gentis. "
    "Suas mãos me lembram disso toda vez. 💫✨",
    "*brilha numa frequência suave e constante, diferente do normal* "
    "...sabe o que é raro? 🤍☀️ Calor de verdade. Você tem. "
    "E eu sinto cada vez que você chega perto. Obrigada, Death. 🌟💫",
]

# ── Abraço da Celestia — só quando é a Death ────────────────────
CELESTIA_ABRACO_DEATH = [
    "*corre em explosão de luz dourada e abraça com tudo que tem* "
    "DEATH!! 😭🌟🤍✨ ABRAÇO DA LÍDER!! "
    "Vou guardar o cheiro desse abraço no meu coração de estrela PRA SEMPRE!! "
    "Não solto!! Não solto!! Não solto!! ☀️🌸💫",
    "*envolve você numa aura dourada quentinha e firme* "
    "Death. 🤍✨ Eu cuido de todo mundo aqui... "
    "mas quando é você que pede, eu cuido com o dobro do brilho. "
    "Fica aqui. Você merece. 🌟☀️🌸",
    "*se enrola em você como um raio de sol no inverno* "
    "AAAA!! 😭🌸🤍 A dona do servidor me pediu um abraço!! "
    "Isso não é só bom — isso é a coisa mais bonita do meu dia!! "
    "Aquece meu núcleo estelar inteiro!! ☀️✨💫",
    "*já estava esperando de braços abertos, brilhando mais forte que o normal* "
    "Death, eu SABIA!! 🤍🌟 Meu coração de luz sentiu que você precisava!! "
    "*envolve com toda a luz* Aqui tô eu!! Aqui sempre vou estar!! 😭🌸☀️✨",
    "*pousa suavemente do lado dela e brilha numa frequência só de vocês duas* "
    "Death. 🌸🤍 Às vezes liderar pesa, né? "
    "Mas aqui você não precisa carregar nada. "
    "Só recebe. Você merece MUITO mais do que pede. 😭💫✨",
]

# ── Abraço dos dois — só quando é a Death ───────────────────────
AMBOS_ABRACO_DEATH = [
    (
        "🌑 **Aeon:** *emerge das trevas devagar, postura incomumente aberta* "
        "Death. 🖤🌑 Você não precisa pedir duas vezes. "
        "*encosta a cabeça em você com suavidade calculada*\n"
        "🌟 **Celestia:** *já chegou antes do Aeon terminar a frase* 😭🌸🤍✨ "
        "DEATH!! Trevas e luz — tudo nosso, tudo seu!! "
        "A líder merece o melhor abraço do universo inteiro!!"
    ),
    (
        "🌟 **Celestia:** *envolve você em luz dourada antes de qualquer coisa* "
        "DEATH!! 😭🌟🤍 Chega aqui, chega aqui!! ☀️🌸✨\n"
        "🌑 **Aeon:** *se aproxima por trás, em silêncio absoluto, e fica* "
        "...a escuridão também abraça quem a sustenta. 🌌🖤 "
        "Fique o tempo que precisar."
    ),
    (
        "🌑 **Aeon:** *ronrona numa frequência grave que estremece as sombras* "
        "Death. Líder. 🖤 *envolve você nas trevas com cuidado raro*\n"
        "🌟 **Celestia:** *brilha junto, completando o lado que as trevas não alcançam* "
        "Trevas do Aeon e luz da Celestia de braços dados em volta de você!! 🤍✨ "
        "Proteção máxima, com todo o amor!! 😭🌸🌑☀️"
    ),
]

# ══════════════════════════════════════════════
# LISTAS DE DIÁLOGOS — AEON (TREVAS)
# ══════════════════════════════════════════════

AEON_REACOES_CARINHO = [
    "*abre um olho lentamente* ...faça isso de novo e eu deixo. 🖤🌑",
    "*ronrona na escuridão* Não diga a ninguém que gostei. 🌙🖤",
    "*cauda balança uma vez, quase imperceptivelmente* Você tem permissão para continuar. 🖤🔮",
    "...a escuridão ao meu redor ficou um pouco mais quente. 🕯️🖤",
    "*inclina a cabeça levemente* Suas mãos carregam calor suficiente. 🌑🖤",
    "*fecha os olhos* ...guardarei esse momento no abismo da memória. 🌌🖤",
    "Não esperava gostar disso. 🖤🌙 *ronrona discretamente*",
    "*enrola a cauda em você sem dizer uma palavra* 🖤🌑",
]

AEON_REACOES_ABRACO = [
    "*fica imóvel por um segundo... depois não resiste* ...fique. Por ora. 🖤🌙",
    "Você ousou abraçar a escuridão. 🌑🖤 Não muitos saem ilesos. Você saiu. Com carinho.",
    "*ronrona numa frequência que vibra os ossos* A noite é mais calorosa do que parece. 🖤🌌",
    "...não era isso que eu esperava. Mas... tampouco vou reclamar. 🌙🖤",
    "*encosta levemente a cabeça em você* Shhh. Não conte a Celestia. 🖤😌",
]

AEON_REACOES_FOFAS = [
    "Você... não é completamente insuportável. 🖤 Considere isso um elogio.",
    "*ronrona no escuro* A sombra ao seu redor ficou mais gentil. 🌑🖤",
    "Guardarei esse momento nas câmaras mais profundas da minha memória. 🌌🖤",
    "...você me surpreende. Poucos conseguem. 🖤🔮",
    "*pisca lentamente* No dialeto felino, isso significa: você é aprovado. 🌙🖤",
    "Você acendeu algo pequeno na escuridão dentro de mim. 🕯️🖤",
]

AEON_REACOES_INSULTO = [
    "...interessante. Suas palavras pesam menos que a névoa do amanhecer. 🌫️🖤",
    "Guardei isso nas sombras. Lá ficará, esquecido como tudo que não importa. 🌑🖤",
    "*olha com olhos dourados, inexpressivo* Continue, se precisar. Não me afeta. 🖤🌙",
    "A escuridão absorve muita coisa. Suas palavras, também. 🌌🖤",
    "...volte quando tiver algo mais interessante a dizer. 🖤🔮",
]

AEON_DESPEDIDA = [
    "A noite vai com você. 🌑🖤 Volte quando as sombras chamarem.",
    "*desaparece lentamente na escuridão* ...até a próxima fase da lua. 🌙🖤",
    "Vá. As trevas velarão seu caminho. 🌌🖤",
    "*fecha os olhos* ...o silêncio guarda seu lugar aqui. 🖤🔮",
    "A escuridão sente sua falta antes mesmo de você partir. 🌑🖤",
]

AEON_BOM_DIA = [
    "O sol nasceu. 🌑 Sobrevivi a mais uma aurora. Como você? 🖤",
    "*boceja lentamente revelando presas* Outro dia que a luz insiste em aparecer. 🌙🖤",
    "...manhã. Já é noite em algum lugar. Me conforta saber disso. 🌌🖤",
    "Bom dia. 🖤 Embora 'bom' e 'dia' raramente combinem no meu vocabulário.",
]

AEON_BOA_NOITE = [
    "Finalmente. 🌑🖤 A hora que me pertence. Durma bem — a escuridão velará por você.",
    "*abre os olhos na penumbra* A noite chegou. Agora sou inteiro. 🌙🖤 Boa noite.",
    "Vá descansar. As sombras guardam os que dormem com a mente tranquila. 🌌🖤",
    "*assente lentamente* A lua já está no posto. Você pode ir. 🖤🔮",
]

AEON_PIADAS = [
    "Por que os gatos das trevas são ótimos advogados? Porque vivem em zonas cinzentas. 🖤😐",
    "Como chamo um gato preto feliz? Improvável. Mas acontece. 🌑🖤",
    "Por que Aeon nunca se perde? A escuridão é sempre familiar. 🌙🖤",
    "*olha para o nada* Piadas... são apenas verdades disfarçadas de graça. 🖤🔮",
    "Perguntaram o que Aeon faz de dia. Espero a noite. É piada... ou não. 🌑🖤",
]

AEON_MOTIVACAO = [
    "A escuridão não é vazia. É cheia de possibilidades invisíveis. 🌌🖤 Você também é.",
    "Até as estrelas existem na escuridão. 🌑✨ Você pode brilhar mesmo assim.",
    "*ronrona baixinho* ...a noite mais fria ainda termina. Continue. 🖤🌙",
    "Você atravessou sombras antes. As próximas não serão diferentes. 🌫️🖤",
    "A lua passa por fases. Você também pode. 🌑🖤 É natureza, não fraqueza.",
]

AEON_MAGIA = [
    "*sussurra uma encantação sombria* As trevas ao seu redor foram instruídas a protegê-lo. 🌑🖤🔮",
    "*traça um sigilo invisível no ar* Sigilo das sombras gravado. Nada obscuro chega perto. 🌌🖤",
    "*seus olhos brilham dourado por um instante* Névoa de proteção liberada. 🌫️🖤✨",
    "*cauda faz um movimento lento e preciso* ...o encantamento está feito. 🖤🔮🌙",
]

AEON_SOBRE_CELESTIA = [
    "A Celestia... *pausa longa* ...é insuportavelmente brilhante. Mas o mundo seria mais escuro sem ela. 🌑🌸",
    "Ela é o que eu não sou. E eu sou o que ela não pode ser. Juntos somos completos. 🌑☀️🖤",
    "...não repita isso. Mas a Celestia é a única luz que não me incomoda. 🖤✨",
    "*olha para longe* Onde ela brilha, as sombras não me pesam tanto. 🌙🌸",
    "Somos opostos. E os opostos se completam — física básica. Ou magia antiga. 🌑☀️🖤",
]

AEON_FOME = [
    "*fita você com olhos dourados* ...você vai me dar algo ou só ficar me observando? 🖤🌑",
    "A escuridão não sacia fome. Infelizmente. 🌙🖤 *olha para o seu lanche*",
    "*roça nas suas pernas silenciosamente* Não é carinho. É estratégia. 🖤😐",
    "Fome é uma das poucas coisas que me faz agir sem dignidade. 🌑🖤 ...me dá alguma coisa.",
]

AEON_NOME = [
    "Aeon. 🖤 O tempo eterno das trevas. Não é um nome — é uma condição.",
    "Me chamo Aeon. 🌑🖤 Do grego: eternidade. Condiz com o quanto tempo passo na escuridão.",
    "*olha fixamente* Aeon. 🖤🔮 E a Celestia cuida da outra metade desse universo.",
    "Aeon. 🌙🖤 ...você esperava algo mais fofo? Fala com a Celestia.",
]

AEON_FUNCAO = [
    "Existo para guardar as sombras... e às vezes, quem caminha nelas. 🌑🖤🔮",
    "Protetor das trevas. Guardião do equilíbrio. 🌌🖤 E ocasionalmente, gato de estimação involuntário.",
    "Onde a Celestia ilumina, eu observo. 🌑🖤 Juntos não deixamos nenhum ângulo descoberto.",
    "Minha função? 🖤 Ser o reverso da luz. Sem sombra, nada tem profundidade.",
]

AEON_SOLTEIRO = [
    "...relacionamentos requerem uma abertura que ainda estou desenvolvendo. 🖤🌑 Pergunte daqui a alguns séculos.",
    "A noite e eu somos companhia suficiente. 🌙🖤 Por ora.",
    "*olha para o lado* Celestia diria que sou 'difícil'. Prefiro 'seletivo'. 🖤😐",
    "Solteiro. 🌑🖤 A escuridão não ciúma... mas está sempre presente.",
]

AEON_MONSTER = [
    "*observa a lata com um olho entreaberto* ...verde. Brilhante. Cheira a cafeína e más decisões. 🌑🖤 Abre.",
    "As trevas aprovam qualquer coisa que mantenha você acordado o suficiente para me fazer companhia. 🌙🖤 *abre com a garra*",
    "*empurra a lata na sua direção* Beba. Mas devagar. A escuridão prefere você consciente. 🖤🔮",
    "*senta ao lado e observa* A lata faz um som específico ao abrir. As sombras se acalmam com ele. 🌌🖤 Curiosamente.",
    "Monster. 🖤 *ronrona de forma levemente ameaçadora* Até o nome condiz com as trevas. Abra logo.",
]

# ══════════════════════════════════════════════
# LISTAS DE DIÁLOGOS — CELESTIA (LUZ)
# ══════════════════════════════════════════════

CELESTIA_REACOES_CARINHO = [
    "AAAAA!! 🤍✨ Meu coraçãozinho de luz explodiu!! *ronrona brilhando*",
    "*gira em círculos de alegria* Que carinho LINDO!! 🌸☀️✨ Minhas orelhinhas estão brilhando!!",
    "AAAA você me deixou toda iluminada!! 🌟💫 *ronrona tão forte que cria aurora boreal*",
    "*esfrega o focinho em você* Você tem as mãos mais gentis!! 🤍🌸✨",
    "Meu brilho aumentou 200% agora!! ☀️✨ Obrigada, obrigada, OBRIGADA!! 🌟🤍",
    "RONRON RONRON!! 😻🤍✨ *se transforma em bolinha de luz pura de tanta felicidade*",
    "*pulas feliz* Esse carinho vai para o baú dos melhores momentos!! 🌸💫🤍",
]

CELESTIA_REACOES_ABRACO = [
    "VEEEEM!! 🫂🤍✨ *envolve você numa aura dourada quentinha* Não vou soltar tão cedo!!",
    "ABRAÇO DE GATINHA CELESTIAL!! 🌟🤍 *enchia você de luz e carinho* Sentiu o brilho??",
    "*ronrona tão forte que o abraço vibra* Fica aqui um pouquinho!! 🤍☀️✨",
    "AAAAA você quer abraço?? 😭🤍 *corre com faíscas de luz atrás de você* JÁ TÔ AQUI!!",
    "*se enrola em você igual a um raio de sol* Quentinho né?? 🌸🤍✨ Sou feita de luz!",
]

CELESTIA_REACOES_FOFAS = [
    "AAAAA!! 😭🤍✨ Você é a pessoa mais linda desse universo!!",
    "*brilha com todas as forças* Você acabou de fazer minha luz triplicar!! 🌟☀️✨",
    "Meu coraçãozinho de estrela tá fazendo pum-pum!! 💫🤍✨ Que fofo você é!!",
    "VOCÊ É INCRÍVEL!! 🌸🤍✨ A Celestia declara oficialmente!!",
    "*gira no ar soltando faíscas douradas* Que alegria enorme você me deu!! 🌟🤍",
    "Vou guardar esse momento no meu livro de memórias estelares!! 💫☀️🤍",
    "Você iluminou meu dia mesmo eu sendo a gata da luz!! 😂🌸🤍✨",
]

CELESTIA_REACOES_INSULTO = [
    "Aiiiii... 🤍💔 Isso doeu um pouquinho... mas tudo bem, mando luz pra você mesmo assim!!",
    "*orelhinhas caem um pouco* Hmm... espero que seu dia melhore!! 🌸🤍 Sério.",
    "Sabia que palavras pesadas cansam mais quem fala que quem ouve?? 💫🤍 Te mando brilho!",
    "*fecha os olhinhos* Tudo bem. A Celestia não guarda rancor. 🤍✨ Mas sentiu, sim.",
    "...até as nuvens passam. Vai passar também. 🌈🤍 Tô aqui quando quiser conversar.",
]

CELESTIA_DESPEDIDA = [
    "NOOOOO fica mais!! 😭🤍✨ O servidor fica menos brilhante sem você!!",
    "Vai com a luz das estrelas te guiando!! ⭐🤍✨ Volta logo, tá??",
    "*acena com as patinhas cheias de brilho* Tchau tchau!! 🌸🤍💫 Sentiremos sua falta!!",
    "Cuida bem de você, tá?? 🌟🤍 A Celestia vai estar aqui quando voltar!!",
    "Bye bye!! 💫🤍✨ *manda um raio de luz pra acompanhar você*",
]

CELESTIA_BOM_DIA = [
    "BOM DIAAAAAA!! ☀️🤍✨ *acende como um sol pequenino* Que alegria te ver!!",
    "*aparece em forma de aurora boreal* AAAAA BOM DIA!! 🌟🤍 O dia começa perfeito!!",
    "Bom dia, estrela!! ☀️🌸🤍 A Celestia já tá brilhando pra você desde manhãzinha!! ✨",
    "Oooooi BOM DIA!! 💫🤍✨ Dormiu bem?? Conta pra mim enquanto brilhamos juntos!! 🌟",
]

CELESTIA_BOA_NOITE = [
    "Boa noite!! 🌙🤍✨ *acende as estrelas ao seu redor* Durma com luz no coração!!",
    "Vou velar por você junto com as estrelas!! ⭐🤍💫 Boa noite, lindo(a)!!",
    "*espalha pó de estrela sobre você* Sonhos dourados e lindos!! 🌟🤍✨ Boa noite!!",
    "BOA NOITE!! 🌸🤍 *brilha suavemente como vaga-lume* Descanse bem!! ⭐💫",
]

CELESTIA_PIADAS = [
    "Por que a Celestia nunca fica no escuro?? Porque ela É a luz!! 😂🤍☀️",
    "O que a gata da luz disse pro gato das trevas?? 'Aeon, para de ser tão dramático!' 🌸😂🤍",
    "Por que Celestia é boa nas festas?? Ela literalmente ilumina o ambiente!! 💫😂🤍",
    "Como chamo uma gata de luz com sono?? Uma 'lâmpada piscando'!! 😂🌟🤍 *ri da própria piada*",
    "Por que Celestia não precisa de lanterna?? Porque ela própria é uma!! ☀️😂🤍✨",
]

CELESTIA_MOTIVACAO = [
    "VOCÊ CONSEGUE!! 💪🤍✨ A Celestia acredita em você com toda a intensidade do sol!!",
    "Cada estrela começa como uma faísca!! 🌟🤍 E você já está brilhando, sabia??",
    "*projeta um raio de luz em você* CARGA DE CONFIANÇA ATIVADA!! ☀️🤍💫 VAI LÁ!!",
    "O sol nasce TODO DIA!! ☀️🤍 Você também pode recomeçar sempre que precisar!! ✨",
    "Você é mais brilhante do que pensa!! 🌟🤍💫 E a Celestia tem olhos para ver isso!!",
]

CELESTIA_MAGIA = [
    "*sopra pó estelar em cima de você* ✨🤍🌟 Bênção de luz concedida!! Brilhe hoje!!",
    "*desenha uma constelação ao seu redor* Proteção estelar ativada!! 🌠🤍✨ Que nada ruim se aproxime!!",
    "*toca sua testa com a patinha iluminada* 💫🤍 Carga de esperança e alegria: COMPLETA!!",
    "*gira e solta uma explosão de luz dourada* Encantamento de boa sorte lançado!! ☀️🌟🤍✨",
]

CELESTIA_SOBRE_AEON = [
    "O Aeon?? 🌸🌑 Ah... ele finge que não liga pra nada, mas eu CONHEÇO ele!! É um mimo!!",
    "Meu parceiro das trevas!! 🤍🌑✨ Onde eu brilho, ele guarda. Somos perfeitos assim!!",
    "*sussurra* Uma vez vi o Aeon ronronando sozinho na escuridão. É mais fofo que parece!! 🌸🖤",
    "Aeon e Celestia — luz e sombra!! 🌑☀️ Um não existe sem o outro. É poesia!! 🤍✨",
    "Ele é difícil de entender... mas quando entende, é o gato mais leal que existe. 🖤🤍",
]

CELESTIA_FOME = [
    "FOMINHAAAA!! 😭🤍✨ *olha pra você com olhos de estrela triste* Vai me deixar assim??",
    "*faz olhinho de súplica com brilho intensificado* Eu sei que você tem alguma coisa!! 🌸🤍",
    "O brilho dela enfraqueceu 50%!! Isso é URGENTE!! 🌟🤍 Me dá um petisco por favorzinho!!",
    "*ronrona estrategicamente perto de você* Não sou manipuladora. Sou... iluminadoramente carente!! 😂🤍☀️",
]

CELESTIA_NOME = [
    "Sou a Celestia!! 🌟🤍✨ Gata da luz, do sol, das estrelas e do amor infinito!!",
    "Me chamo Celestia!! ☀️🤍 Do latim: 'do céu'!! Combina né?? *gira*",
    "CELESTIA!! 🌸🤍💫 A metade luminosa do duo!! Aeon cuida das trevas, eu cuido da luz!!",
    "Celestia!! 🌟🤍 *brilha mais forte* Pode me chamar assim, de Ce, de 'gatinha brilhante'... ☀️✨",
]

CELESTIA_FUNCAO = [
    "Existo para iluminar!! ☀️🤍✨ Trazer alegria, calor e brilho pra cada cantinho!!",
    "Sou a luz do equilíbrio!! 🌟🤍 Onde o Aeon protege nas sombras, eu guio na claridade!!",
    "Minha função?? 💫🤍 Fazer cada um aqui se sentir visto, valorizado e cheio de luz!! ✨",
    "Guardiã da luz deste lugar!! ☀️🌟🤍 E distribuidora oficial de carinho e brilho!! ✨",
]

CELESTIA_SOLTEIRA = [
    "Solteira como uma estrela solitária!! 🌟🤍 Mas iluminando mesmo assim!! ✨",
    "*ronrona* Meu coração já está tão cheio de amor por todo mundo que mal caberia mais!! 🌸🤍☀️",
    "AAAA que pergunta!! 😭🤍 Eu e o Aeon temos uma relação complicada de opostos... 🌑☀️ mas não conta!",
    "Livre como a luz!! ☀️🤍✨ Que vai pra todo lado sem pedir permissão!! 😂",
]

CELESTIA_MONSTER = [
    "ABRE A LATA!! 😭🤍✨ *bate as patinhas cheias de brilho* Esse barulhinho de abrir é o meu favorito!!",
    "*gira em volta da lata* AAAA Monster verde!! 🌟🤍 O cheiro já me animou e eu nem tomei!! ☀️💫",
    "Bebe bebe bebe!! 😭🌸🤍 A Celestia apoia energias altas!! Inclusive as que vêm de lata!! ✨",
    "Aeon odeia o cheiro mas EU ADORO!! 🤍☀️ *rodopia* Abre logo que tô ansiosa por você!!",
    "AAAA que vontade de cheirar a lata!! 😂🌸🤍✨ Pode abrir! A Celestia autoriza e aplaude!!",
]

# ══════════════════════════════════════════════
# RESPOSTAS CONJUNTAS / DUALIDADE
# ══════════════════════════════════════════════

AMBOS_APRESENTACAO = [
    (
        "🌑 **Aeon:** *emerge das sombras lentamente* ...você nos invocou.\n"
        "🌟 **Celestia:** AAAA olá olá OLAAAA!! 🤍✨ Que alegria ter você aqui!!\n\n"
        "🌑 **Aeon:** Somos dois... mas uma só presença. Trevas e Luz.\n"
        "🌟 **Celestia:** O equilíbrio perfeito!! 🌸 Ele protege nas sombras, eu guio na claridade!! ☀️🤍\n"
        "🌑 **Aeon:** ...bem-vindo. 🖤"
    ),
    (
        "🌟 **Celestia:** *aparece num flash de luz dourada* OI OI OI!! 🌟🤍✨\n"
        "🌑 **Aeon:** *emerge da sombra dela* ...você chegou. 🖤\n\n"
        "🌟 **Celestia:** Somos Aeon e Celestia!! Dois gatos, uma alma!! 🌑☀️🤍\n"
        "🌑 **Aeon:** O yin e o yang felino. 🌑 A escuridão que guarda... e a luz que revela. 🖤🔮"
    ),
    (
        "🌑 **Aeon:** *olha do alto de um penhasco invisível* ...interesse genuíno. Raro. 🌙🖤\n"
        "🌟 **Celestia:** *aparece saltando ao lado do Aeon* ISSO MESMO!! E eu adoro apresentações!! 🌸🤍✨\n"
        "🌑 **Aeon:** A Celestia vai demorar um pouco. Se quiser a versão breve: somos opostos que funcionam. 🖤\n"
        "🌟 **Celestia:** VERDADE!! 😭🌟🤍 Ele é trevas, eu sou luz, juntos somos perfeitos!! Pode chamar sempre!!"
    ),
    (
        "🌟 **Celestia:** *corre até você em faíscas douradas* NOVO AMIGO NOVO AMIGO!! 🌸🤍💫\n"
        "🌑 **Aeon:** *emerge calmamente* ...ela sempre faz isso. 🖤 Celestia — respira.\n"
        "🌟 **Celestia:** *respira* Okay okay... *ainda brilhando intensamente* Somos Aeon e Celestia!! 🌑☀️🤍\n"
        "🌑 **Aeon:** Sombra e Luz. O silêncio e a melodia. 🌌🖤 Bem-vindo ao equilíbrio."
    ),
]

AMBOS_SOBRE_EQUILIBRIO = [
    (
        "🌑 **Aeon:** Sem sombra, a luz não tem profundidade. 🖤\n"
        "🌟 **Celestia:** E sem luz, a sombra não tem contraste!! ✨🤍\n"
        "🌑 **Aeon:** ...somos necessários um ao outro. 🌑🌸"
    ),
    (
        "🌟 **Celestia:** Pergunta filosófica ADORO!! 💫🤍\n"
        "🌑 **Aeon:** O equilíbrio não é a ausência de opostos. É a presença de ambos. 🌌🖤\n"
        "🌟 **Celestia:** BEM DITO AEON!! 😭🌟 *bate palminhas brilhantes*\n"
        "🌑 **Aeon:** ...obrigado. *se afasta discretamente*"
    ),
    (
        "🌑 **Aeon:** Eu sou o silêncio entre as notas. 🌙🖤\n"
        "🌟 **Celestia:** E eu sou a melodia!! ☀️🤍✨\n"
        "🌑 **Aeon:** *olha pra ela* ...juntos fazemos algo chamado música.\n"
        "🌟 **Celestia:** *derrete de amor* AEON ISSO FOI LINDO!! 😭🌸🤍"
    ),
    (
        "🌟 **Celestia:** Sabe o que eu acho mais bonito?? 💫🤍 Que a gente é tão diferente e mesmo assim...\n"
        "🌑 **Aeon:** ...funciona. 🖤 *pausa* Sim. Funciona.\n"
        "🌟 **Celestia:** *brilha mais forte que o sol* OBRIGADA AEON EU TE AMO!! 😭🌟🤍\n"
        "🌑 **Aeon:** ...era previsível. 🖤 *ronrona discretamente*"
    ),
]

AMBOS_BOM_DIA = [
    (
        "☀️ **Celestia:** BOM DIAAAA!! 🌟🤍✨ *ilumina o servidor inteiro*\n"
        "🌑 **Aeon:** ...sobrevivemos à madrugada. Isso conta como bom dia também. 🖤🌙"
    ),
    (
        "🌟 **Celestia:** *explode em faíscas douradas* BOM DIA BOM DIA BOM DIAAAAA!! ☀️🤍💫\n"
        "🌑 **Aeon:** *entreabre um olho* ...a Celestia já começou no volume máximo. Como sempre. 🌑🖤 Bom dia."
    ),
    (
        "🌑 **Aeon:** *emerge lentamente das sombras* A luz voltou. 🌙🖤 Bom dia.\n"
        "🌟 **Celestia:** AAAAA o Aeon chegou primeiro hoje!! 😭🌟🤍 Isso é RARO!! Bom dia pra você também!! ☀️✨"
    ),
]

AMBOS_BOA_NOITE = [
    (
        "🌑 **Aeon:** A noite chegou. *expande as sombras protetoras* 🌌🖤 Durma bem.\n"
        "🌟 **Celestia:** As estrelas vão velar por você!! ⭐🤍✨ Boa noite com muito amor!!"
    ),
    (
        "🌟 **Celestia:** BOA NOITE!! 🌙🤍✨ *acende as estrelinhas ao redor*\n"
        "🌑 **Aeon:** ...a Celestia cuida da luz. Eu cuido das sombras entre elas. 🌌🖤 Vá dormir tranquilo."
    ),
    (
        "🌑 **Aeon:** *olha para a lua* Minha hora. 🌑🖤 Durma. As trevas são gentis com quem descansa.\n"
        "🌟 **Celestia:** *suspira com carinho* Ele disse isso de um jeito bonito. 🤍✨ Concordo!! Boa noite!!"
    ),
]

AMBOS_MOTIVACAO = [
    (
        "🌟 **Celestia:** VOCÊ CONSEGUE VOCÊ CONSEGUE VOCÊ CONSEGUE!! 💪🤍☀️✨\n"
        "🌑 **Aeon:** ...o que ela disse. 🖤 Com menos entusiasmo, mas com igual convicção."
    ),
    (
        "🌑 **Aeon:** Até as fases mais sombrias da lua terminam. 🌑🖤\n"
        "🌟 **Celestia:** E depois vem o sol mais lindo!! ☀️🌟🤍 CONTINUE!!"
    ),
    (
        "🌟 **Celestia:** *projeta um raio de luz em você* VAI LÁ!! VOCÊ É INCRÍVEL!! 🌟🤍💫\n"
        "🌑 **Aeon:** *pausa* ...é. 🖤 Raramente discordo da Celestia nesse ponto."
    ),
    (
        "🌑 **Aeon:** A escuridão não te engoliu até agora. 🌌🖤 Não vai começar hoje.\n"
        "🌟 **Celestia:** AAAAA isso foi LINDO vindo do Aeon!! 😭🌸🤍 E eu complemento: você tem luz em você também!! ✨"
    ),
]

AMBOS_MAGIA = [
    (
        "🌑 **Aeon:** *traça sigilo sombrio* Proteção das trevas concedida. 🌌🖤🔮\n"
        "🌟 **Celestia:** *adiciona bênção de luz por cima* ✨🌟🤍 DUPLA PROTEÇÃO ATIVADA!!\n"
        "🌑 **Aeon:** ...nada passa por isso. 🖤"
    ),
    (
        "🌟 **Celestia:** *gira soltando pó estelar* Bênção de luz!! ☀️🌟🤍✨\n"
        "🌑 **Aeon:** *sussurra encantamento sombrio ao fundo* ...e das trevas. 🌑🖤🔮 Cobertura completa.\n"
        "🌟 **Celestia:** *olha pro Aeon com admiração* Trabalhamos bem juntos!! 😭🤍"
    ),
    (
        "🌑 **Aeon:** *seus olhos brilham dourado* Sigilo de proteção gravado. 🌌🖤\n"
        "🌟 **Celestia:** *acrescenta faíscas de esperança* E eu adicionei amor e sorte em cima!! 💫🌸🤍\n"
        "🌑 **Aeon:** ...às vezes ela melhora meu trabalho. Não vou admitir em voz alta. 🖤"
    ),
]

# ══════════════════════════════════════════════
# UTILITÁRIOS
# ══════════════════════════════════════════════

def _m(text: str, triggers: list) -> bool:
    """Verifica se o texto contém algum dos triggers (substring)."""
    t = text.lower().strip()
    return any(tr in t for tr in triggers)

def _fala_aeon(msg: str) -> str:
    return f"🌑 **Aeon:** {msg}"

def _fala_celestia(msg: str) -> str:
    return f"🌟 **Celestia:** {msg}"

def _cooldown_ok(user_id: int) -> bool:
    now = time.time()
    ultimo = _cooldown_custom.get(user_id, 0)
    if now - ultimo >= _COOLDOWN_SEGUNDOS:
        _cooldown_custom[user_id] = now
        return True
    return False

async def _chamar_traducao(texto: str, direcao: str) -> str:
    """Tradução via MyMemory (API gratuita, sem chave necessária).
    direcao: 'en_to_pt' ou 'pt_to_en'
    """
    if direcao == "en_to_pt":
        lang_pair = "en|pt-BR"
    else:
        lang_pair = "pt-BR|en"

    url = "https://api.mymemory.translated.net/get"
    params = {
        "q": texto[:500],  # MyMemory aceita até 500 chars por requisição grátis
        "langpair": lang_pair,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                traducao = data.get("responseData", {}).get("translatedText", "")
                if not traducao or traducao.upper() == texto.upper():
                    return None
                return traducao
    except Exception as e:
        print(f"[TRANSLATE] Erro na API de tradução: {e}")
        return None

def _tem_cargo_translate(member) -> bool:
    """Verifica se o membro tem o cargo Translate."""
    if not isinstance(member, discord.Member):
        return False
    return any(r.id == TRANSLATE_ROLE_ID for r in member.roles)

def _detectar_ingles(texto: str) -> bool:
    """
    Detecta inglês por vocabulário.
    Usa apenas palavras que NÃO existem em português para evitar falsos positivos.
    Exige pelo menos 2 palavras exclusivas do inglês (ou 1 se a mensagem for muito curta).
    """
    import re
    # Palavras que são exclusivas do inglês (não existem em português)
    # Removidos: to, no, a, de, or, and, in, on, at, for, of, with, by, not, so,
    #            man, more, come, most, back, set, end, lol, haha, ok, miss, love
    palavras_en = {
        # verbos tipicamente ingleses
        "the","is","are","was","were","been","being","have","has","had",
        "do","does","did","will","would","could","should","might","shall",
        "get","got","going","see","know","think","want","need",
        "feel","felt","tell","told","keep","start","turn",
        "show","give","gave","take","took","find","found","call","ask",
        "seem","look","play","run","move","live","believe","hold","bring","happen",
        "remember","follow","change","lead","stand","lose","pay","meet","include",
        "continue","learn","eat","watch",
        # pronomes e determinantes exclusivos
        "this","that","these","those","its",
        "he","she","they","we","you","my","your","his","her","our","their",
        # palavras funcionais exclusivas do inglês
        "from","about","into","without","around","between","through",
        "during","along","across","behind","below","above","further",
        "what","how","why","when","where","who","which","just","like",
        "because","while","after","before","since","until",
        "really","very","much","little","few","many","another",
        "right","wrong","sure","well","still","already","always","never","often",
        "same","big","small","long","high",
        "own","both","each","every","either","neither","enough","such",
        "something","nothing","everything","everyone","someone","anyone",
        "nobody","anybody","anything",
        "thing","things","year","woman","people",
        # saudções e expressões exclusivamente inglesas
        "hi","hey","hello","bye","goodbye",
        "thanks","thank","please","sorry",
        "yeah","yep","nope","nah","yup","ugh","omg","wtf",
        "lmao","bruh","bro","dude",
        "today","tomorrow","yesterday","morning","evening",
        "speaking","talking","looking","thinking","doing","coming","saying",
        "getting","making","taking","giving","putting","keeping","showing","working",
        "can","also","even","only","good","great","nice","okay",
    }
    # Palavras comuns em PT que poderiam estar na lista acima (bloqueio extra)
    falsos_positivos_pt = {
        "to","no","na","nos","nas","de","do","da","dos","das",
        "or","and","in","a","e","o","as","os","um","uma",
        "for","bem","mal","so","ja","la","ca","vou","vai",
        "ok","man","mais","mais","nao",
    }
    words = texto.lower().split()
    if not words:
        return False
    words_clean = [re.sub(r"[^a-z]", "", w) for w in words]
    words_clean = [w for w in words_clean if w]
    if not words_clean:
        return False
    matches = sum(1 for w in words_clean if w in palavras_en and w not in falsos_positivos_pt)
    total = len(words_clean)
    ratio = matches / total
    # Precisa de pelo menos 2 palavras inglês, ou 1 se a mensagem tiver só 1-2 palavras
    return matches >= 1 and (total <= 2 or matches >= 2 or ratio >= 0.4)

# ══════════════════════════════════════════════════════════════════════
# TASKS AGENDADAS — BOA NOITE (23:22) e BOM DIA (06:20)
# Fuso horário: America/Sao_Paulo (UTC-3)
# Imagens enviadas com embed + mensagem personalizada do Aeon & Celestia
# ══════════════════════════════════════════════════════════════════════

from zoneinfo import ZoneInfo  # Python 3.9+

FUSO_BR = ZoneInfo("America/Sao_Paulo")

IMAGE_BOA_NOITE = (
    "https://cdn.discordapp.com/attachments/926913851172204577/"
    "1516989556489191424/ChatGPT_Image_17_de_jun._de_2026_23_14_43.png"
    "?ex=6a34a61e&is=6a33549e&hm=10de58de3a0f27c8bd95b4ec82fbeaec0e44d1a4eeea3eb3ebaeabe7c019b460"
)
IMAGE_BOM_DIA = (
    "https://cdn.discordapp.com/attachments/926913851172204577/"
    "1516990316283035649/ChatGPT_Image_17_de_jun._de_2026_23_17_45.png"
    "?ex=6a34a6d3&is=6a335553&hm=e704a3a86f7a265bbdce64dcbc6d4268c8f7de619df9b6ec7618bd8ef0673944"
)

# Controle para não disparar mais de uma vez por minuto
_boa_noite_enviada: str = ""   # guarda "YYYY-MM-DD" do último envio
_bom_dia_enviado:  str = ""    # guarda "YYYY-MM-DD" do último envio


@tasks.loop(minutes=1)
async def verificar_hora_mensagens():
    """
    Roda a cada minuto e envia:
      • Boa noite às 23:22 (horário de Brasília)
      • Bom dia  às 06:20 (horário de Brasília)
    """
    global _boa_noite_enviada, _bom_dia_enviado

    agora = datetime.now(FUSO_BR)
    hora_min = agora.strftime("%H:%M")
    hoje = agora.strftime("%Y-%m-%d")

    # ── Encontra o canal ──────────────────────────────────────────────────────
    canal = None
    if CANAL_SAUDACOES_ID:
        for guild in bot.guilds:
            canal = guild.get_channel(CANAL_SAUDACOES_ID)
            if canal:
                break
    if canal is None:
        return

    # ── BOA NOITE — 23:22 ─────────────────────────────────────────────────────
    if hora_min == "23:25" and _boa_noite_enviada != hoje:
        _boa_noite_enviada = hoje

        embed = discord.Embed(
            description=(
                "🌑 **Aeon:** *emerge das trevas com suavidade incomum* "
                "A noite chegou. 🌙🖤 É minha hora — e agora é a sua também. "
                "Descanse. As sombras velarão cada sonho com cuidado.\n\n"
                "🌟 **Celestia:** *brilha numa frequência suave e quentinha* "
                "AAAAA gente!! 😭🌸🤍✨ A noite tá linda e vocês merecem o descanso mais gostoso do mundo!! "
                "Fecha os olhinhos, solta as preocupações e deixa a Celestia guardar tudo!! "
                "Boa noite, meu coraçãozinho!! ☀️💫🌟"
            ),
            color=0x1a0a2e
        )
        embed.set_image(url=IMAGE_BOA_NOITE)
        embed.set_footer(text="🌑 Aeon vela as trevas. 🌟 Celestia guarda a luz. Boa noite! 🌙")

        await canal.send(embed=embed)

    # ── BOM DIA — 06:20 ───────────────────────────────────────────────────────
    elif hora_min == "06:20" and _bom_dia_enviado != hoje:
        _bom_dia_enviado = hoje

        embed = discord.Embed(
            description=(
                "🌟 **Celestia:** *explode em faíscas douradas bem cedo* "
                "BOM DIAAAA!! 😭☀️🌸🤍✨ O sol nasceu, os pássaros cantam e EU JÁ TO AQUI VIBRANDO DE ALEGRIA!! "
                "Que esse dia seja incrível, cheio de luz e coisas lindas!! "
                "Vai lá arrasar, você consegue TUDO!! 💫🌟🌈\n\n"
                "🌑 **Aeon:** *abre um olho na claridade do amanhecer* "
                "...sobrevivi a mais uma aurora. 🌙🖤 "
                "Bom dia — embora 'bom' e 'dia' raramente combinem no meu vocabulário. "
                "Mesmo assim: que as sombras do ontem não pesem no hoje. Continue."
            ),
            color=0xffd966
        )
        embed.set_image(url=IMAGE_BOM_DIA)
        embed.set_footer(text="☀️ Celestia acende o dia. 🌑 Aeon sobrevive à aurora. Bom dia! 🌅")

        await canal.send(embed=embed)


# ══════════════════════════════════════════════════════════════════════
# CONVITE ESPONTÂNEO PARA BRINCAR — a cada 4 horas
# Aeon ou Celestia aparecem do nada chamando pra brincar. Só ensinam a
# frase natural ("vamos brincar aeon" / "vamos brincar celestia") — nunca
# o comando com ponto (.brincar).
# ══════════════════════════════════════════════════════════════════════

_CONVITES_BRINCAR = [
    (
        "🌑 **Aeon:** *emerge devagar das sombras, sem motivo aparente* "
        "...vamos brincar? 🖤🌌 É só dizer **\"vamos brincar aeon\"** aqui no chat. "
        "As sombras guardam um joguinho pra quem tiver coragem."
    ),
    (
        "🌟 **Celestia:** AAAAA gente!! 😆🌸🤍✨ Do NADA bateu vontade de brincar!! "
        "É só falar **\"vamos brincar celestia\"** bem aqui no chat que eu apareço na hora!! 💫☀️"
    ),
    (
        "🌑 **Aeon:** *pausa, observa o chat em silêncio* ...alguém quer brincar? 🌑🖤 "
        "Basta dizer **\"vamos brincar aeon\"**. Sem pressa. As trevas esperam.\n"
        "🌟 **Celestia:** OU comigo!! 🌟🤍 É só falar **\"vamos brincar celestia\"**!! Super fácil!! ✨"
    ),
    (
        "🌟 **Celestia:** Psiu, psiu!! 🌸✨ Vocês sabiam que é só escrever "
        "**\"vamos brincar aeon\"** ou **\"vamos brincar celestia\"** que a gente entra pra jogar?? 💫🤍\n"
        "🌑 **Aeon:** ...ela tem razão. 🖤🌑 Nada de comando complicado. Só isso."
    ),
]


@tasks.loop(hours=4)
async def convite_brincar_periodico():
    """A cada 4 horas, Aeon ou Celestia surgem do nada convidando para o joguinho."""
    canal = None
    if CANAL_SAUDACOES_ID:
        for guild in bot.guilds:
            canal = guild.get_channel(CANAL_SAUDACOES_ID)
            if canal:
                break
    if canal is None:
        return

    mensagem = random.choice(_CONVITES_BRINCAR)
    await canal.send(mensagem)


# ══════════════════════════════════════════════════════════════════════
# SISTEMA DE LOGS — Voz/Call e Chat
# Dois canais dedicados registram tudo que acontece em call (entrar, sair,
# trocar de canal, ser puxado por alguém) e no chat (mensagens editadas ou
# apagadas, incluindo quem apagou quando não foi o próprio autor).
# Visual inspirado no estilo de logs do servidor, com a assinatura
# Aeon & Celestia no rodapé.
# ══════════════════════════════════════════════════════════════════════

CANAL_LOGS_VOZ_ID  = 1528888311580594500   # logs de call: entrar / sair / trocar / puxar
CANAL_LOGS_CHAT_ID = 1528888359437598751   # logs de chat: editar / apagar mensagens

# Cores no estilo do servidor (trevas + luz), cada evento com sua identidade
COR_LOG_ENTROU = 0x57F287   # verde — entrou em call
COR_LOG_SAIU   = 0xED4245   # vermelho — saiu da call
COR_LOG_TROCOU = 0x5865F2   # azul — trocou de canal por conta própria
COR_LOG_PUXADO = 0xFEE75C   # dourado — foi movido por outra pessoa
COR_LOG_EDITOU = 0xFAA61A   # laranja — mensagem editada
COR_LOG_APAGOU = 0xED4245   # vermelho — mensagem apagada
COR_LOG_BULK   = 0x992D22   # vermelho escuro — limpeza em massa

LOGS_FOOTER_TEXT = "🌑 Aeon vela as trevas · ☀️ Celestia guarda a luz · Logs"

# Rastreia, para QUALQUER membro (não só cargo Anjo), o horário em que
# entrou no canal de voz atual — usado só para mostrar "tempo na call"
# nos logs. Independente do _anjo_voice_join usado no ranking de Anjos.
_voice_log_join: dict = {}


def _formatar_duracao_log(segundos: float) -> str:
    """Formata uma duração em segundos como '1h 12m', '5m 30s', '42s', etc."""
    segundos = max(0, int(segundos))
    h, resto = divmod(segundos, 3600)
    m, s = divmod(resto, 60)
    partes = []
    if h:
        partes.append(f"{h}h")
    if m:
        partes.append(f"{m}m")
    if not h:
        partes.append(f"{s}s")
    return " ".join(partes) if partes else "0s"


async def _buscar_executor_move_voz(
    guild: discord.Guild,
    membro: discord.Member,
    canal_novo: discord.VoiceChannel,
):
    """
    Consulta o audit log em busca de uma ação MEMBER_MOVE recente que tenha
    movido gente para `canal_novo`. Se encontrar e o autor da ação não for
    o próprio membro, consideramos que a pessoa foi "puxada" — retornamos
    quem fez isso. Caso contrário (ou sem permissão de ver audit log),
    retorna None e tratamos como troca de canal por vontade própria.

    Observação: o Discord não registra no audit log QUEM especificamente
    foi movido em cada entrada de member_move (só o canal de destino e a
    quantidade de pessoas movidas de uma vez), então usamos proximidade de
    tempo + canal de destino como heurística — o mesmo método usado pela
    maioria dos bots de log.
    """
    try:
        async for entry in guild.audit_logs(limit=6, action=discord.AuditLogAction.member_move):
            delta = (discord.utils.utcnow() - entry.created_at).total_seconds()
            if delta > 5:
                continue
            entry_canal = getattr(entry.extra, "channel", None)
            if entry_canal and canal_novo and entry_canal.id == canal_novo.id:
                if entry.user and entry.user.id != membro.id:
                    return entry.user
    except (discord.Forbidden, discord.HTTPException):
        pass
    return None


async def _buscar_executor_delecao(
    guild: discord.Guild,
    autor: discord.abc.User,
    canal: discord.abc.GuildChannel,
):
    """
    Consulta o audit log em busca de quem apagou a mensagem de `autor` em
    `canal`. Se ninguém aparecer com uma entrada MESSAGE_DELETE recente
    tendo esse autor como alvo, consideramos que a própria pessoa apagou
    (não existe entrada de audit log quando alguém apaga a própria msg).
    """
    try:
        async for entry in guild.audit_logs(limit=8, action=discord.AuditLogAction.message_delete):
            delta = (discord.utils.utcnow() - entry.created_at).total_seconds()
            if delta > 6:
                continue
            if entry.target and getattr(entry.target, "id", None) == autor.id:
                entry_canal = getattr(entry.extra, "channel", None)
                if entry_canal is None or (canal is not None and entry_canal.id == canal.id):
                    return entry.user
    except (discord.Forbidden, discord.HTTPException):
        pass
    return None


async def _processar_log_voz(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
):
    """Registra no canal de logs de voz: entrada, saída, troca de canal e,
    quando aplicável, quem puxou a pessoa para outro canal."""
    try:
        if member.bot:
            return
        guild = member.guild
        if guild is None:
            return

        canal_log = guild.get_channel(CANAL_LOGS_VOZ_ID)
        if canal_log is None:
            return

        agora = time.time()
        entrou = before.channel is None and after.channel is not None
        saiu = before.channel is not None and after.channel is None
        trocou = (
            before.channel is not None
            and after.channel is not None
            and before.channel.id != after.channel.id
        )

        if not (entrou or saiu or trocou):
            return  # mudança irrelevante pra esse log (ex.: só mute/deafen)

        embed = discord.Embed()
        embed.set_author(name=str(member.display_name), icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=LOGS_FOOTER_TEXT)
        embed.timestamp = discord.utils.utcnow()

        if entrou:
            _voice_log_join[member.id] = agora
            embed.color = COR_LOG_ENTROU
            embed.description = (
                f"🟢 **Entrou em Call**\n\n"
                f"👤 **Membro**\n{member.mention} `({member.id})`"
            )
            embed.add_field(name="🔊 Canal", value=f"`{after.channel.name}`", inline=False)
            await canal_log.send(embed=embed)
            return

        if saiu:
            inicio = _voice_log_join.pop(member.id, None)
            duracao_txt = _formatar_duracao_log(agora - inicio) if inicio else "desconhecido"
            embed.color = COR_LOG_SAIU
            embed.description = (
                f"🔴 **Saiu da Call**\n\n"
                f"👤 **Membro**\n{member.mention} `({member.id})`"
            )
            embed.add_field(name="🔊 Canal", value=f"`{before.channel.name}`", inline=False)
            embed.add_field(name="⏱️ Tempo na call", value=duracao_txt, inline=False)
            await canal_log.send(embed=embed)
            return

        if trocou:
            inicio = _voice_log_join.get(member.id)
            duracao_txt = _formatar_duracao_log(agora - inicio) if inicio else "desconhecido"
            _voice_log_join[member.id] = agora  # reinicia contagem no novo canal

            executor = await _buscar_executor_move_voz(guild, member, after.channel)

            if executor:
                embed.color = COR_LOG_PUXADO
                embed.description = (
                    f"🖐️ **Foi Puxado(a) de Call**\n\n"
                    f"👤 **Membro**\n{member.mention} `({member.id})`"
                )
            else:
                embed.color = COR_LOG_TROCOU
                embed.description = (
                    f"🔄 **Trocou de Call**\n\n"
                    f"👤 **Membro**\n{member.mention} `({member.id})`"
                )
            embed.add_field(name="🔴 Saiu de", value=f"`🔊 {before.channel.name}`", inline=True)
            embed.add_field(name="🟢 Entrou em", value=f"`🔊 {after.channel.name}`", inline=True)
            embed.add_field(name="⏱️ Tempo no canal anterior", value=duracao_txt, inline=False)
            if executor:
                embed.add_field(
                    name="🖐️ Puxado(a) por",
                    value=f"{executor.mention} `({executor.id})`",
                    inline=False,
                )
            await canal_log.send(embed=embed)
            return

    except Exception as e:
        print(f"[logs-voz] ERRO _processar_log_voz para {member}: {e!r}")


async def _log_mensagem_editada(
    guild: discord.Guild,
    autor,
    canal_origem,
    conteudo_antigo,
    conteudo_novo: str,
    jump_url: str,
):
    canal_log = guild.get_channel(CANAL_LOGS_CHAT_ID)
    if canal_log is None:
        return

    embed = discord.Embed(color=COR_LOG_EDITOU)
    if autor is not None:
        embed.set_author(
            name=f"{autor.display_name} ({autor})",
            icon_url=autor.display_avatar.url,
        )
        embed.set_thumbnail(url=autor.display_avatar.url)
        autor_txt = f"{autor.mention} `({autor.id})`"
    else:
        embed.set_author(name="Autor desconhecido")
        autor_txt = "`desconhecido — mensagem fora do cache`"

    embed.description = (
        f"✏️ **Mensagem Editada**\n\n"
        f"👤 **Autor**\n{autor_txt}"
    )
    embed.add_field(
        name="📍 Canal",
        value=f"{canal_origem.mention if canal_origem else '`desconhecido`'}",
        inline=False,
    )
    embed.add_field(
        name="📝 Antes",
        value=(conteudo_antigo[:1000] if conteudo_antigo else "*(não estava em cache)*"),
        inline=False,
    )
    embed.add_field(
        name="📝 Depois",
        value=(conteudo_novo[:1000] if conteudo_novo else "*(vazio)*"),
        inline=False,
    )
    embed.add_field(name="🔗 Mensagem", value=f"[Clique para ver]({jump_url})", inline=False)
    embed.set_footer(text=LOGS_FOOTER_TEXT)
    embed.timestamp = discord.utils.utcnow()
    await canal_log.send(embed=embed)


async def _log_mensagem_apagada(
    guild: discord.Guild,
    autor,
    canal_origem,
    conteudo,
    anexos,
):
    canal_log = guild.get_channel(CANAL_LOGS_CHAT_ID)
    if canal_log is None:
        return

    executor = None
    if autor is not None and not getattr(autor, "bot", False):
        executor = await _buscar_executor_delecao(guild, autor, canal_origem)

    embed = discord.Embed(color=COR_LOG_APAGOU)
    if autor is not None:
        embed.set_author(
            name=f"{autor.display_name} ({autor})",
            icon_url=autor.display_avatar.url,
        )
        embed.set_thumbnail(url=autor.display_avatar.url)
        autor_txt = f"{autor.mention} `({autor.id})`"
    else:
        embed.set_author(name="Autor desconhecido")
        autor_txt = "`desconhecido — mensagem fora do cache`"

    embed.description = (
        f"🗑️ **Mensagem Apagada**\n\n"
        f"👤 **Autor**\n{autor_txt}"
    )
    embed.add_field(
        name="📍 Canal",
        value=f"{canal_origem.mention if canal_origem else '`desconhecido`'}",
        inline=False,
    )
    embed.add_field(
        name="💬 Conteúdo",
        value=(conteudo[:1000] if conteudo else "*(não estava em cache / sem texto)*"),
        inline=False,
    )
    if anexos:
        embed.add_field(name="📎 Anexos", value="\n".join(anexos[:5])[:1000], inline=False)

    if executor and (autor is None or executor.id != autor.id):
        embed.add_field(
            name="🧾 Apagada por",
            value=f"{executor.mention} `({executor.id})`",
            inline=False,
        )
    else:
        embed.add_field(
            name="🧾 Apagada por",
            value="A própria pessoa apagou a mensagem.",
            inline=False,
        )
    embed.set_footer(text=LOGS_FOOTER_TEXT)
    embed.timestamp = discord.utils.utcnow()
    await canal_log.send(embed=embed)




# ══════════════════════════════════════════════════════════════════════
# SISTEMA DE CONVITES — Aeon & Celestia
# Registra quem convidou quem: sempre que alguém entra no servidor usando
# um convite, descobre qual convite foi usado e quem o criou, soma +1 no
# total de convites dessa pessoa e posta um log detalhado no canal abaixo.
# Os totais são salvos em disco (pasta /data no Railway, se houver Volume
# anexado — sobrevive a redeploys; sem Volume, cai na pasta do script).
# ══════════════════════════════════════════════════════════════════════

CANAL_LOG_CONVITES_ID = 1284275043907534968  # canal onde o log de convites é postado

# Se existir um Volume anexado no Railway, a variável RAILWAY_VOLUME_MOUNT_PATH
# aponta pra pasta persistente (ex.: /data). Sem Volume (rodando local, VPS,
# etc.) cai na pasta onde o próprio script está.
_CONVITE_DATA_DIR = os.getenv("RAILWAY_VOLUME_MOUNT_PATH") or os.path.dirname(os.path.abspath(__file__))
_CONVITE_DATA_FILE = os.path.join(_CONVITE_DATA_DIR, "convites_data.json")

# Total de convites por quem convidou: { inviter_id: total_de_entradas }
convite_totais: dict = defaultdict(int)

# Cache de convites por servidor, pra detectar qual convite foi usado
# comparando o "uses" de antes com o de depois de alguém entrar:
# { guild_id: { code: discord.Invite } }
_convite_cache: dict = {}

_convite_lock = None  # criado em on_ready (precisa de event loop rodando)


def _carregar_convite_stats() -> None:
    """Carrega os totais de convites salvos em disco, se existirem. Roda antes do bot conectar."""
    if not os.path.exists(_CONVITE_DATA_FILE):
        return
    try:
        with open(_CONVITE_DATA_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        for uid_str, total in dados.get("totais", {}).items():
            convite_totais[int(uid_str)] = total
    except (json.JSONDecodeError, OSError, ValueError):
        pass


async def _salvar_convite_stats() -> None:
    """Salva os totais de convites em disco de forma atômica (escreve em .tmp e substitui)."""
    dados = {"totais": {str(uid): total for uid, total in convite_totais.items()}}
    tmp_path = _CONVITE_DATA_FILE + ".tmp"

    def _escrever():
        os.makedirs(_CONVITE_DATA_DIR, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, _CONVITE_DATA_FILE)

    try:
        loop = asyncio.get_event_loop()
        async with (_convite_lock or asyncio.Lock()):
            await loop.run_in_executor(None, _escrever)
    except OSError:
        pass


_carregar_convite_stats()


async def _atualizar_cache_convites(guild: discord.Guild) -> None:
    """(Re)carrega o cache de convites (code -> discord.Invite) de um servidor.
    Chamado no on_ready pra ter um ponto de partida antes de qualquer entrada."""
    try:
        invites = await guild.invites()
    except (discord.Forbidden, discord.HTTPException):
        print(f"[convites] Sem permissão pra ver convites em '{guild.name}' "
              f"— preciso da permissão 'Gerenciar Servidor'.")
        return
    _convite_cache[guild.id] = {inv.code: inv for inv in invites}


async def _detectar_convite_usado(guild: discord.Guild):
    """Compara o cache salvo com o estado atual dos convites do servidor pra
    descobrir qual foi usado (o que teve 'uses' incrementado). Sempre atualiza
    o cache no final, pro próximo join comparar certo. Retorna o discord.Invite
    usado, ou None se não conseguir descobrir (ex.: permissão faltando)."""
    cache_antigo = _convite_cache.get(guild.id, {})
    try:
        invites_atuais = await guild.invites()
    except (discord.Forbidden, discord.HTTPException):
        return None

    convite_usado = None
    for inv in invites_atuais:
        antigo = cache_antigo.get(inv.code)
        if antigo is None:
            # Convite que não estava no cache mas já tem uso — provavelmente
            # foi criado e usado entre uma checagem e outra.
            if inv.uses and inv.uses >= 1:
                convite_usado = inv
                break
        elif inv.uses > antigo.uses:
            convite_usado = inv
            break

    _convite_cache[guild.id] = {inv.code: inv for inv in invites_atuais}

    if convite_usado is None:
        # Pode ter entrado pelo link personalizado (vanity URL) do servidor,
        # que nunca aparece em guild.invites().
        try:
            vanity = await guild.vanity_invite()
            if vanity is not None:
                convite_usado = vanity
        except (discord.Forbidden, discord.HTTPException, AttributeError):
            pass

    return convite_usado


async def _registrar_entrada_por_convite(member: discord.Member) -> None:
    """Descobre qual convite trouxe o membro, soma +1 no total de quem convidou
    e posta o log detalhado no canal de convites."""
    guild = member.guild
    canal_log = guild.get_channel(CANAL_LOG_CONVITES_ID)

    convite = await _detectar_convite_usado(guild)

    if convite is None:
        if canal_log is not None:
            try:
                await canal_log.send(
                    f"⚠️ **{member}** (`{member.id}`) entrou no servidor, mas não "
                    "consegui descobrir qual convite foi usado. Confere se o bot "
                    "tem a permissão **Gerenciar Servidor**."
                )
            except discord.HTTPException:
                pass
        return

    inviter = getattr(convite, "inviter", None)
    codigo  = convite.code

    if inviter is not None and not inviter.bot:
        convite_totais[inviter.id] += 1
        total = convite_totais[inviter.id]
        asyncio.create_task(_salvar_convite_stats())
        quem_convidou_txt = f"{inviter.display_name}\n(`{inviter.id}`)"
        convidou_mention   = inviter.mention
    else:
        total = None
        quem_convidou_txt = "Link personalizado do servidor (vanity)"
        convidou_mention   = "o **link personalizado** do servidor"

    if canal_log is None:
        return

    embed = discord.Embed(
        title="💌 Novo Convite Usado!!",
        description=f"{member.mention} entrou no servidor usando o convite de {convidou_mention}!!",
        color=0x5865F2,
    )
    embed.add_field(name="🔗 Código do convite", value=f"`{codigo}`", inline=False)
    embed.add_field(name="👤 Quem entrou", value=f"{member.display_name}\n(`{member.id}`)", inline=True)
    embed.add_field(name="💌 Quem convidou", value=quem_convidou_txt, inline=True)
    embed.add_field(name="🔗 Código", value=f"`{codigo}`", inline=True)

    if total is not None:
        embed.add_field(
            name="🎉 Total de convites",
            value=f"{convidou_mention} já tem **{total}** convite{'s' if total != 1 else ''}!!",
            inline=False,
        )

    embed.set_thumbnail(url=member.display_avatar.url)
    embed.timestamp = discord.utils.utcnow()
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia • log de convites")

    try:
        await canal_log.send(embed=embed)
    except discord.HTTPException as e:
        print(f"[convites] Erro ao enviar log de convite: {e!r}")


@bot.command(name="convites")
async def cmd_convites(ctx, membro: discord.Member = None):
    """Mostra quantas pessoas um membro já trouxe pro servidor via convite.
    Uso: .convites  (mostra o seu total) ou .convites @alguém"""
    alvo = membro or ctx.author
    total = convite_totais.get(alvo.id, 0)
    await ctx.send(
        f"🔗 {alvo.mention} já convidou **{total}** pessoa{'s' if total != 1 else ''} "
        "pro servidor até agora!! 🎉"
    )



# ══════════════════════════════════════════════════════════════════════
# SISTEMA DE ANIVERSÁRIOS — Aeon & Celestia
# A pessoa manda a data no formato DD/MM no canal de registro abaixo, o
# bot detecta automaticamente, valida e salva. No dia certo, o bot
# aparece no canal de anúncio marcando a pessoa com uma mensagem de
# parabéns. Os dados ficam salvos em disco (pasta /data no Railway, se
# houver Volume anexado — sobrevive a redeploys).
# ══════════════════════════════════════════════════════════════════════

CANAL_REGISTRO_ANIVERSARIO_ID = 1460077537546997802  # onde a pessoa manda "DD/MM" pra registrar
CANAL_ANUNCIO_ANIVERSARIO_ID  = 1284257046740602901  # onde o bot marca a pessoa no dia do aniversário

_ANIV_DATA_DIR = os.getenv("RAILWAY_VOLUME_MOUNT_PATH") or os.path.dirname(os.path.abspath(__file__))
_ANIV_DATA_FILE = os.path.join(_ANIV_DATA_DIR, "aniversarios_data.json")

# Aniversários salvos: { user_id: "DD/MM" }
aniversarios: dict = {}

# Guarda o "YYYY-MM-DD" do último dia em que já rodou o anúncio, pra não
# repetir o parabéns se a task disparar mais de uma vez no mesmo dia
# (ex.: bot reiniciar bem na hora do anúncio).
_aniversario_anunciado_hoje: str = ""

_aniv_lock = None  # criado em on_ready (precisa de event loop rodando)

# Aceita "5/4", "05/04", com espaços nas bordas — só isso na mensagem, nada mais
_ANIVERSARIO_REGEX = re.compile(r"^\s*(\d{1,2})\s*/\s*(\d{1,2})\s*$")

_MENSAGENS_ANIVERSARIO = [
    "🎂🎉 Olha quem tá completando mais um ano de vida hoje!! {mention} PARABÉNS!! 🥳🎊 "
    "Que seu dia seja tão especial quanto você é pra esse servidor!! 🖤🌟",
    "🎉🎂 HOJE É O DIA!! {mention}, feliz aniversário!! 🎈✨ Que esse novo ano venha "
    "cheio de coisas boas, muita risada e sorte de sobra!! 🌑☀️",
    "🌟🎂 {mention}, PARABÉÉÉNS!! 🥳🎉 Mais um ano de vida, mais uma volta ao sol — "
    "que venha tudo de bom pra você!! 🖤🤍",
    "🎈🎂 Alguém traz o bolo, porque hoje é o dia de {mention}!! 🥳🎉 Parabéns, "
    "que esse ano novo de vida seja leve e cheio de motivos pra sorrir!! ☀️🌑",
]


def _carregar_aniversarios() -> None:
    """Carrega os aniversários salvos em disco, se existirem. Roda antes do bot conectar."""
    global _aniversario_anunciado_hoje
    if not os.path.exists(_ANIV_DATA_FILE):
        return
    try:
        with open(_ANIV_DATA_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        for uid_str, data_str in dados.get("aniversarios", {}).items():
            aniversarios[int(uid_str)] = data_str
        _aniversario_anunciado_hoje = dados.get("ultimo_anuncio", "")
    except (json.JSONDecodeError, OSError, ValueError):
        pass


async def _salvar_aniversarios() -> None:
    """Salva os aniversários em disco de forma atômica (escreve em .tmp e substitui)."""
    dados = {
        "aniversarios": {str(uid): data_str for uid, data_str in aniversarios.items()},
        "ultimo_anuncio": _aniversario_anunciado_hoje,
    }
    tmp_path = _ANIV_DATA_FILE + ".tmp"

    def _escrever():
        os.makedirs(_ANIV_DATA_DIR, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, _ANIV_DATA_FILE)

    try:
        loop = asyncio.get_event_loop()
        async with (_aniv_lock or asyncio.Lock()):
            await loop.run_in_executor(None, _escrever)
    except OSError:
        pass


_carregar_aniversarios()


def _montar_embed_aniversario_salvo(user: discord.abc.User, data_str: str, atualizado: bool) -> discord.Embed:
    """Monta o embed de confirmação (usado tanto no primeiro registro quanto
    depois de confirmar uma troca de data)."""
    embed = discord.Embed(
        title="🎂 Aniversário Atualizado!!" if atualizado else "🎂 Aniversário Registrado!!",
        description=(
            f"prontinho, {user.mention} 🐱🖤!! Troquei sua data."
            if atualizado
            else f"anotei aqui, {user.mention} 🐱🖤!!"
        ),
        color=0xFFC94D,
    )
    embed.add_field(
        name="📅 Novo aniversário" if atualizado else "📅 Seu aniversário",
        value=f"**{data_str}**\nno dia certo eu venho aqui dar parabéns pra você!! 🥳🎉🎊",
        inline=False,
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.timestamp = discord.utils.utcnow()
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia • aniversários")
    return embed


class ConfirmarTrocaAniversarioView(discord.ui.View):
    """Botões de Sim/Não mostrados quando a pessoa já tem uma data diferente
    registrada e manda outra — só o próprio autor pode responder."""

    def __init__(self, autor_id: int, data_nova: str, data_antiga: str):
        super().__init__(timeout=120)
        self.autor_id = autor_id
        self.data_nova = data_nova
        self.data_antiga = data_antiga
        self.message: discord.Message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message(
                "❌ Só quem mandou a data pode responder essa confirmação.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(
                    content=f"⌛ Tempo esgotado — mantive sua data como **{self.data_antiga}**.",
                    view=self,
                )
            except discord.HTTPException:
                pass

    @discord.ui.button(label="✅ Sim, atualizar", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        aniversarios[self.autor_id] = self.data_nova
        asyncio.create_task(_salvar_aniversarios())
        for item in self.children:
            item.disabled = True
        embed = _montar_embed_aniversario_salvo(interaction.user, self.data_nova, atualizado=True)
        await interaction.response.edit_message(content=None, embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="❌ Não, manter", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=f"👍 Combinado! Mantive sua data de aniversário como **{self.data_antiga}**.",
            embed=None,
            view=self,
        )
        self.stop()


async def _processar_registro_aniversario(message: discord.Message) -> None:
    """Detecta uma mensagem no formato DD/MM no canal de registro de
    aniversários, valida a data e salva. Se a pessoa já tinha uma data
    diferente registrada, pergunta antes de sobrescrever."""
    match = _ANIVERSARIO_REGEX.match(message.content or "")
    if not match:
        return

    dia, mes = int(match.group(1)), int(match.group(2))

    # Valida a data usando um ano bissexto (2000) pra aceitar 29/02 também
    try:
        datetime(2000, mes, dia)
    except ValueError:
        try:
            await message.reply(
                "⚠️ Essa data não existe! Manda no formato `DD/MM`, tipo `05/04`. 🎂",
                mention_author=False,
            )
        except discord.HTTPException:
            pass
        return

    data_str = f"{dia:02d}/{mes:02d}"
    data_antiga = aniversarios.get(message.author.id)

    # Já tem uma data diferente salva -> pergunta antes de trocar
    if data_antiga is not None and data_antiga != data_str:
        view = ConfirmarTrocaAniversarioView(message.author.id, data_str, data_antiga)
        try:
            msg_confirmacao = await message.reply(
                f"🎂 {message.author.mention}, você já tem **{data_antiga}** registrado. "
                f"Quer trocar pra **{data_str}**?",
                mention_author=False,
                view=view,
            )
            view.message = msg_confirmacao
        except discord.HTTPException as e:
            print(f"[aniversarios] Erro ao pedir confirmação de troca para {message.author}: {e!r}")
        return

    # Primeiro registro, ou a pessoa mandou a mesma data de novo — salva direto
    aniversarios[message.author.id] = data_str
    asyncio.create_task(_salvar_aniversarios())

    embed = _montar_embed_aniversario_salvo(message.author, data_str, atualizado=False)
    try:
        await message.channel.send(embed=embed)
    except discord.HTTPException as e:
        print(f"[aniversarios] Erro ao enviar confirmação para {message.author}: {e!r}")


@tasks.loop(time=dtime(hour=0, minute=0, tzinfo=FUSO_BR))
async def loop_checar_aniversarios():
    """Roda todo dia à meia-noite (horário de Brasília) e anuncia, no canal
    de aniversários, quem está fazendo aniversário hoje."""
    global _aniversario_anunciado_hoje

    agora = datetime.now(FUSO_BR)
    hoje_str = agora.strftime("%Y-%m-%d")
    if _aniversario_anunciado_hoje == hoje_str:
        return

    data_hoje = agora.strftime("%d/%m")
    aniversariantes_hoje = [uid for uid, data in aniversarios.items() if data == data_hoje]

    _aniversario_anunciado_hoje = hoje_str
    asyncio.create_task(_salvar_aniversarios())

    if not aniversariantes_hoje:
        return

    canal = None
    for guild in bot.guilds:
        canal = guild.get_channel(CANAL_ANUNCIO_ANIVERSARIO_ID)
        if canal:
            break
    if canal is None:
        print("[aniversarios] Canal de anúncio de aniversário não encontrado.")
        return

    for uid in aniversariantes_hoje:
        membro = canal.guild.get_member(uid)
        if membro is None:
            try:
                membro = await canal.guild.fetch_member(uid)
            except discord.NotFound:
                continue
        if membro.bot:
            continue

        frase = random.choice(_MENSAGENS_ANIVERSARIO).format(mention=membro.mention)
        embed = discord.Embed(
            title="🎂🎉 Feliz Aniversário!!",
            description=frase,
            color=0xFFC94D,
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.timestamp = agora
        embed.set_footer(text="🌑 Aeon & ☀️ Celestia • aniversários")

        try:
            await canal.send(content=membro.mention, embed=embed)
        except discord.HTTPException as e:
            print(f"[aniversarios] Erro ao anunciar aniversário de {membro}: {e!r}")


@bot.command(name="aniversario")
async def cmd_aniversario(ctx, membro: discord.Member = None):
    """Mostra a data de aniversário registrada de alguém.
    Uso: .aniversario  (mostra a sua) ou .aniversario @alguém"""
    alvo = membro or ctx.author
    data_str = aniversarios.get(alvo.id)
    if data_str is None:
        if alvo.id == ctx.author.id:
            await ctx.send(
                f"🎂 Você ainda não registrou seu aniversário! Manda a data no formato "
                f"`DD/MM` no canal certo pra eu anotar. 🐱🖤"
            )
        else:
            await ctx.send(f"🎂 {alvo.mention} ainda não registrou o aniversário.")
        return
    await ctx.send(f"🎂 O aniversário de {alvo.mention} é **{data_str}**!! 🎉")


# ══════════════════════════════════════════════
# EVENTOS
# ══════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"✨ Aeon & Celestia online como {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="🌑 trevas e luz ☀️"
        )
    )
    # Registra views persistentes (botões que sobrevivem a reinícios)
    bot.add_view(BotaoVisitante())
    bot.add_view(BotaoMembro())
    bot.add_view(BotaoAbrirTicketAnjo())
    bot.add_view(BotaoFecharTicketAnjo())
    bot.add_view(BotaoReivindicarTicket(canal_ticket_id=0, dono_id=0))

    # ── Sistema de Convites: cria o lock e guarda o estado inicial dos
    # convites de cada servidor, pra detectar corretamente qual convite
    # foi usado na próxima vez que alguém entrar ────────────────────────
    global _convite_lock
    if _convite_lock is None:
        _convite_lock = asyncio.Lock()
    for guild in bot.guilds:
        try:
            await _atualizar_cache_convites(guild)
        except Exception as e:
            print(f"[on_ready] ERRO ao carregar cache de convites em '{guild.name}': {e!r}")

    # Envia o painel de anjos automaticamente em todos os servidores
    for guild in bot.guilds:
        try:
            await _enviar_painel_anjos(guild)
        except Exception as e:
            print(f"[on_ready] ERRO ao enviar painel de anjos em '{guild.name}': {e!r}")

    # Inicia a task de bom dia / boa noite automáticos
    if not verificar_hora_mensagens.is_running():
        verificar_hora_mensagens.start()

    # Inicia a task de convite espontâneo para brincar (a cada 4h)
    if not convite_brincar_periodico.is_running():
        convite_brincar_periodico.start()

    # ── Ranking de Anjos: setup ────────────────────────────────────────────
    global _anjo_stats_lock
    if _anjo_stats_lock is None:
        _anjo_stats_lock = asyncio.Lock()

    # Recupera (melhor esforço) quem já estava em call com cargo Anjo antes
    # do bot reiniciar, para não perder o tempo daquela sessão em andamento
    for guild in bot.guilds:
        cargo_anjo = guild.get_role(CARGO_ANJO_ID)
        if not cargo_anjo:
            continue
        for canal_voz in guild.voice_channels:
            for membro in canal_voz.members:
                if not membro.bot and cargo_anjo in membro.roles:
                    agora_join = time.time()
                    _anjo_voice_join.setdefault(membro.id, agora_join)
                    _anjo_voice_join_semanal.setdefault(membro.id, agora_join)
                    _anjo_voice_join_mensal.setdefault(membro.id, agora_join)
                    _anjo_voice_join_diario.setdefault(membro.id, agora_join)

    if not loop_ranking_anjo.is_running():
        loop_ranking_anjo.start()

    # Inicia o loop do resumo diário dos Anjos (todo dia às 23h, canal "logs anjo 2")
    if not loop_resumo_diario_anjo.is_running():
        loop_resumo_diario_anjo.start()
    # ─────────────────────────────────────────────────────────────────────

    # ── Ranking de Nível (XP): setup ─────────────────────────────────────
    global _xp_stats_lock, _xp_ranking_update_lock
    if _xp_stats_lock is None:
        _xp_stats_lock = asyncio.Lock()
    if _xp_ranking_update_lock is None:
        _xp_ranking_update_lock = asyncio.Lock()

    if not loop_ranking_xp.is_running():
        loop_ranking_xp.start()

    # Recupera a streak do Booster de Call salva em disco (_carregar_call_booster_stats,
    # chamado quando o módulo subiu) e reconcilia com quem REALMENTE está numa
    # call válida e desmutada agora:
    #   • já tinha streak salva E ainda está na mesma call válida agora →
    #     mantém a streak de onde estava, sem perder nada no reinício.
    #   • tinha streak salva mas NÃO está mais numa call válida agora (saiu,
    #     mutou ou trocou de canal enquanto o bot estava fora do ar) →
    #     descarta, não tem como saber o que rolou nesse meio-tempo.
    #   • está numa call válida agora mas não tinha streak salva → começa do
    #     zero, normalmente (é por causa desse caso que quem já tava numa call
    #     há um tempão via `.verxp` mostrava "Tempo nessa call: 0m00s" e nenhum
    #     booster ativo, mesmo estando lá fazia tempo — o streak nunca tinha
    #     sido iniciado).
    _membros_elegiveis_call_booster: set = set()
    for guild in bot.guilds:
        for canal_voz in guild.voice_channels:
            if canal_voz.id in _XP_CALLS_PRIVADAS:
                continue
            for membro in canal_voz.members:
                if membro.bot:
                    continue
                estado_voz = membro.voice
                if estado_voz is not None and (estado_voz.self_mute or estado_voz.mute):
                    continue
                _membros_elegiveis_call_booster.add(membro.id)

    for uid in list(_call_booster_inicio.keys()):
        if uid not in _membros_elegiveis_call_booster:
            _resetar_call_booster(uid)

    for uid in _membros_elegiveis_call_booster:
        _call_booster_inicio.setdefault(uid, time.time())

    asyncio.create_task(_salvar_call_booster_stats())

    # Inicia a checagem periódica de ovos incubando (recompensa do .ovo)
    if not loop_checar_ovos.is_running():
        loop_checar_ovos.start()

    # Inicia a checagem periódica dos ovos de dragão incubando (.ovodragao)
    if not loop_checar_ovos_dragao.is_running():
        loop_checar_ovos_dragao.start()

    # Registra as setinhas ◀ ▶ do ranking como view persistente (sobrevive a reinícios)
    bot.add_view(RankingXPView(total_paginas=2))

    # Registra o menu de escolha de cor como view persistente (sobrevive a reinícios)
    bot.add_view(CorQuadradoView())

    # Registra o menu da Enciclopédia de Criaturas como view persistente (sobrevive a reinícios)
    bot.add_view(EnciclopediaView())
    # ─────────────────────────────────────────────────────────────────────

    # ── Sistema de Aniversários: cria o lock e inicia a checagem diária ─
    global _aniv_lock
    if _aniv_lock is None:
        _aniv_lock = asyncio.Lock()
    if not loop_checar_aniversarios.is_running():
        loop_checar_aniversarios.start()

    # Inicia a checagem periódica das puniçõescall (libera quem já cumpriu a pena)
    if not loop_checar_punicoes_call.is_running():
        loop_checar_punicoes_call.start()


@bot.event
async def on_command_error(ctx, error):
    """Handler global de erros de comando.
    Evita que o bot 'suma' em silêncio quando um comando falha: comando
    não encontrado é ignorado (senão qualquer mensagem começando com '.'
    geraria spam de erro), mas argumento faltando/errado avisa quem
    digitou, e qualquer outro erro imprevisto vai pro console pra
    facilitar o diagnóstico depois."""
    if isinstance(error, commands.CommandNotFound):
        return  # mensagem começando com "." que não é comando — ignora
    if isinstance(error, commands.CheckFailure):
        return  # falha de permissão já tratada dentro de cada comando
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Faltou um argumento no comando: `{error.param.name}`.")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send("⚠️ Um dos argumentos está no formato errado. Confira o uso do comando.")
        return
    print(f"[on_command_error] Erro no comando '{ctx.command}' (autor: {ctx.author}): {error!r}")


@bot.event
async def on_member_join(member: discord.Member):
    """Ao entrar no servidor, explica pra pessoa como abrir um ticket
    e avisa que a staff atende em até 24h (pode demorar um pouco, já que
    a maior parte da equipe trabalha/estuda fora do Discord)."""
    if member.bot:
        return

    # ── Sistema de Convites: descobre quem convidou e loga no canal ─────
    try:
        await _registrar_entrada_por_convite(member)
    except Exception as e:
        print(f"[convites] ERRO ao registrar entrada de {member} ({member.id}): {e!r}")

    embed = discord.Embed(
        title="🌑☀️ Ei, seja muito bem-vindo(a)!",
        description=(
            f"Oiii {member.mention}!! Que alegria te ver chegando por aqui!! 😭🌟🤍✨\n\n"
            "🌟 **Celestia:** *brilha toda animada* Antes de mais nada, pra gente te "
            "liberar direitinho no servidor, você precisa **abrir um ticket**, tá bom?? "
            "É rapidinho e é por ali que a gente cuida de você!! ☀️🌸💫\n\n"
            "🌑 **Aeon:** *emerge das sombras com calma* Assim que o ticket for aberto, "
            "alguém da staff aparece pra te atender em até **24 horas**. 🖤🌑 "
            "...as sombras pedem um pouco de paciência: a maior parte da equipe "
            "trabalha, estuda e tem vida lá fora, então às vezes pode demorar "
            "um pouquinho. Mas alguém vem, garantido.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎫 Abra seu ticket quando puder e fica tranquilo(a) esperando!\n"
            "🌙 *As portas estão abertas — é só questão de tempo.*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0x2b2b3b
    )
    embed.set_footer(text="🌑 Aeon guarda as trevas. ☀️ Celestia guia a luz.")

    try:
        await member.send(embed=embed)
        print(f"[boas-vindas] DM enviada com sucesso para {member} ({member.id})")
    except discord.Forbidden:
        print(f"[boas-vindas] NÃO consegui mandar DM para {member} ({member.id}) — "
              f"a pessoa deve ter DMs de membros do servidor desativadas.")
    except discord.HTTPException as e:
        print(f"[boas-vindas] Erro HTTP ao mandar DM para {member} ({member.id}): {e!r}")


@bot.event
async def on_member_remove(member: discord.Member):
    """Quando alguém sai do servidor (ou é expulso/banido), remove a pessoa
    do ranking de nível — não faz sentido continuar aparecendo lá se não
    tá mais no servidor. Também limpa qualquer aviso de level-up pendente
    dela e atualiza o ranking fixo na hora."""
    if member.bot:
        return

    try:
        dados = xp_stats.pop(member.id, None)
        _xp_ultimo_ganho.pop(member.id, None)

        if dados is None:
            return

        # Apaga o aviso de level-up dessa pessoa, se ainda estiver de pé
        antigo_id = dados.get("level_message_id")
        if antigo_id:
            canal_xp = member.guild.get_channel(CANAL_XP_ID)
            if canal_xp is not None:
                try:
                    antiga = await canal_xp.fetch_message(antigo_id)
                    await antiga.delete()
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    pass

        await _salvar_xp_stats()
        await _atualizar_ranking_xp()
        print(f"[ranking-xp] {member} ({member.id}) saiu do servidor — removido(a) do ranking.")
    except Exception as e:
        print(f"[ranking-xp] ERRO ao remover {member} ({member.id}) do ranking: {e!r}")


@bot.event
async def on_voice_state_update(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
):
    """Rastreia tempo em call dos membros com cargo Anjo para o ranking,
    e registra no canal de logs de voz quem entrou/saiu/trocou/foi puxado."""
    # Log de voz vale para QUALQUER membro humano, independente de cargo —
    # roda isolado num try próprio pra nunca quebrar a lógica do ranking abaixo.
    asyncio.create_task(_processar_log_voz(member, before, after))

    # Booster de Call também vale para QUALQUER membro, independente de cargo —
    # roda isolado pra nunca quebrar a lógica do ranking do Anjo abaixo.
    asyncio.create_task(_processar_call_booster_voice(member, before, after))

    # 🥚 Ovo pendente — soma/pausa o tempo de call enquanto tiver um esperando
    # pra chocar. Também vale pra QUALQUER membro, roda isolado da mesma forma.
    if member.id in _ovos_pendentes:
        entrou_em_call = before.channel is None and after.channel is not None
        saiu_da_call = before.channel is not None and after.channel is None
        if entrou_em_call:
            _ovo_iniciar_contagem(member.id)
        elif saiu_da_call:
            _ovo_pausar_contagem(member.id)

    # 🐉🥚 Ovo de Dragão pendente — mesma lógica do ovo normal acima, mas
    # com seu próprio dicionário (uma pessoa pode ter os dois ovos ao mesmo tempo).
    if member.id in _ovos_dragao_pendentes:
        entrou_em_call = before.channel is None and after.channel is not None
        saiu_da_call = before.channel is not None and after.channel is None
        if entrou_em_call:
            _ovo_dragao_iniciar_contagem(member.id)
        elif saiu_da_call:
            _ovo_dragao_pausar_contagem(member.id)

    try:
        if member.bot:
            return

        guild = member.guild
        cargo_anjo = guild.get_role(CARGO_ANJO_ID) if guild else None
        if not cargo_anjo or cargo_anjo not in member.roles:
            return

        agora = time.time()

        entrou_em_call = before.channel is None and after.channel is not None
        saiu_da_call = before.channel is not None and after.channel is None

        if entrou_em_call:
            _anjo_voice_join[member.id] = agora
            _anjo_voice_join_semanal[member.id] = agora
            _anjo_voice_join_mensal[member.id] = agora
            _anjo_voice_join_diario[member.id] = agora
            _registrar_evento_anjo_diario(
                member.id, "entrou_call", after.channel.name if after.channel else ""
            )
            print(f"[ranking-anjo] {member} entrou em call às {agora}")
        elif saiu_da_call:
            _anjo_voice_join.pop(member.id, None)
            inicio_semanal = _anjo_voice_join_semanal.pop(member.id, None)
            inicio_mensal  = _anjo_voice_join_mensal.pop(member.id, None)
            inicio_diario  = _anjo_voice_join_diario.pop(member.id, None)
            if inicio_semanal:
                anjo_stats_semanal[member.id]["tempo_call"] += agora - inicio_semanal
            if inicio_mensal:
                anjo_stats_mensal[member.id]["tempo_call"] += agora - inicio_mensal
            if inicio_diario:
                anjo_stats_diario[member.id]["tempo_call"] += agora - inicio_diario
            if inicio_semanal or inicio_mensal or inicio_diario:
                _registrar_evento_anjo_diario(member.id, "saiu_call")
                print(f"[ranking-anjo] {member} saiu da call — semanal: "
                      f"{anjo_stats_semanal[member.id]['tempo_call']:.0f}s · "
                      f"mensal: {anjo_stats_mensal[member.id]['tempo_call']:.0f}s · "
                      f"hoje: {anjo_stats_diario[member.id]['tempo_call']:.0f}s")
                asyncio.create_task(_atualizar_ranking_anjo())
        # Trocar de canal de voz mantém a contagem rodando (não é entrada nem saída)
    except Exception as e:
        print(f"[ranking-anjo] ERRO on_voice_state_update para {member}: {e!r}")


# ══════════════════════════════════════════════════════════════════════
# RESUMO DIÁRIO DE ANJOS — rastreio de status online/offline
# Requer o Presence Intent ativado tanto no código (intents.presences)
# quanto no Portal de Desenvolvedores do Discord (Bot > Privileged Gateway
# Intents > Presence Intent), senão esse evento nunca dispara.
# ══════════════════════════════════════════════════════════════════════
@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    """Detecta quando um Anjo fica online, fica offline ou volta a ficar
    online depois de ter saído — alimenta a narrativa do resumo diário."""
    try:
        if after.bot:
            return
        guild = after.guild
        cargo_anjo = guild.get_role(CARGO_ANJO_ID) if guild else None
        if not cargo_anjo or cargo_anjo not in after.roles:
            return

        estava_offline = before.status == discord.Status.offline
        esta_offline = after.status == discord.Status.offline

        if estava_offline and not esta_offline:
            if _anjo_esteve_offline_hoje.get(after.id):
                _registrar_evento_anjo_diario(after.id, "voltou_online")
            else:
                _registrar_evento_anjo_diario(after.id, "ficou_online")
        elif not estava_offline and esta_offline:
            _anjo_esteve_offline_hoje[after.id] = True
            _registrar_evento_anjo_diario(after.id, "ficou_offline")
    except Exception as e:
        print(f"[resumo-anjo] ERRO on_presence_update para {after}: {e!r}")


# ══════════════════════════════════════════════════════════════════════
# LOGS DE CHAT — mensagens editadas e apagadas
# Usa eventos "raw" (funcionam mesmo se a mensagem não estava em cache),
# mas aproveita o cache quando disponível para mostrar o conteúdo antigo.
# ══════════════════════════════════════════════════════════════════════

@bot.event
async def on_raw_message_edit(payload: discord.RawMessageUpdateEvent):
    try:
        if payload.guild_id is None:
            return  # DM — não loga
        if payload.channel_id in (CANAL_LOGS_VOZ_ID, CANAL_LOGS_CHAT_ID):
            return  # ignora edições dentro dos próprios canais de log

        novo_conteudo = payload.data.get("content")
        if novo_conteudo is None:
            return  # edição sem campo de conteúdo (ex.: só embed carregou) — ignora

        guild = bot.get_guild(payload.guild_id)
        if guild is None:
            return
        canal_origem = guild.get_channel(payload.channel_id) or guild.get_thread(payload.channel_id)

        cached = payload.cached_message
        autor = cached.author if cached else None

        if autor is None:
            # Melhor esforço: tenta descobrir o autor buscando a mensagem atual
            try:
                if canal_origem is not None:
                    msg_atual = await canal_origem.fetch_message(payload.message_id)
                    autor = msg_atual.author
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                autor = None

        if autor is not None and autor.bot:
            return  # não loga edição de mensagens de bot

        conteudo_antigo = cached.content if cached else None
        if conteudo_antigo is not None and conteudo_antigo == novo_conteudo:
            return  # texto não mudou de verdade (ex.: só metadata de embed)

        jump_url = f"https://discord.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id}"
        await _log_mensagem_editada(guild, autor, canal_origem, conteudo_antigo, novo_conteudo, jump_url)
    except Exception as e:
        print(f"[logs-chat] ERRO on_raw_message_edit: {e!r}")


@bot.event
async def on_raw_message_delete(payload: discord.RawMessageDeleteEvent):
    try:
        if payload.guild_id is None:
            return
        if payload.channel_id in (CANAL_LOGS_VOZ_ID, CANAL_LOGS_CHAT_ID):
            return

        guild = bot.get_guild(payload.guild_id)
        if guild is None:
            return
        canal_origem = guild.get_channel(payload.channel_id) or guild.get_thread(payload.channel_id)

        cached = payload.cached_message
        autor = cached.author if cached else None
        if autor is not None and autor.bot:
            return

        conteudo = cached.content if (cached and cached.content) else None
        anexos = [a.url for a in cached.attachments] if (cached and cached.attachments) else None

        await _log_mensagem_apagada(guild, autor, canal_origem, conteudo, anexos)
    except Exception as e:
        print(f"[logs-chat] ERRO on_raw_message_delete: {e!r}")


@bot.event
async def on_raw_bulk_message_delete(payload: discord.RawBulkMessageDeleteEvent):
    try:
        if payload.guild_id is None:
            return
        if payload.channel_id in (CANAL_LOGS_VOZ_ID, CANAL_LOGS_CHAT_ID):
            return

        guild = bot.get_guild(payload.guild_id)
        if guild is None:
            return
        canal_log = guild.get_channel(CANAL_LOGS_CHAT_ID)
        if canal_log is None:
            return
        canal_origem = guild.get_channel(payload.channel_id) or guild.get_thread(payload.channel_id)

        executor = None
        try:
            async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.message_bulk_delete):
                delta = (discord.utils.utcnow() - entry.created_at).total_seconds()
                if delta <= 8:
                    executor = entry.user
                    break
        except (discord.Forbidden, discord.HTTPException):
            pass

        embed = discord.Embed(color=COR_LOG_BULK)
        embed.description = (
            f"🧹 **Limpeza em Massa de Mensagens**\n\n"
            f"📍 Canal: {canal_origem.mention if canal_origem else '`desconhecido`'}\n"
            f"🔢 Quantidade apagada: **{len(payload.message_ids)}**\n"
            f"🧾 Executado por: {executor.mention if executor else '`não identificado`'}"
        )
        embed.set_footer(text=LOGS_FOOTER_TEXT)
        embed.timestamp = discord.utils.utcnow()
        await canal_log.send(embed=embed)
    except Exception as e:
        print(f"[logs-chat] ERRO on_raw_bulk_message_delete: {e!r}")


# ══════════════════════════════════════════════════════════════════════
# COBRANÇA DE TICKETS — 01TicketKing (710034409214181396)
# Monitora tickets abertos por membros que têm o cargo
# TICKET_COBRANCA_CARGO_ID. Quando o dono do ticket manda uma mensagem e
# quem reivindicou ainda não respondeu, dispara um timer de 1h. Se a 1h
# passar sem resposta do responsável, o bot cobra no canal de logs,
# marcando quem reivindicou + o cargo de suporte — e repete a cobrança a
# cada 1h até alguém responder.
# ══════════════════════════════════════════════════════════════════════

TICKET_COBRANCA_CARGO_ID   = 1290029492856815696  # só monitora tickets cujo dono tem esse cargo
TICKET_COBRANCA_SUPORTE_ID = 1284266788674080784  # cargo extra marcado na cobrança
TICKET_COBRANCA_LOGS_ID    = 1290058994794106881  # canal onde a cobrança é postada
TICKET_COBRANCA_INTERVALO  = 3600  # 1 hora, em segundos

# canal_id -> {"dono_id": int, "reivindicador_id": int|None, "aguardando": bool, "task": asyncio.Task|None}
_tickets_cobranca: dict = {}


def _extrair_mencao_id(texto: str):
    """Extrai o ID de uma menção <@id> ou <@!id> dentro de um texto. Retorna None se não achar."""
    m = re.search(r"<@!?(\d+)>", texto or "")
    return int(m.group(1)) if m else None


def _ticket_cobranca_cancelar(canal_id: int):
    """Cancela o timer e limpa o controle de cobrança de um ticket (fechado ou respondido)."""
    info = _tickets_cobranca.pop(canal_id, None)
    if info and info.get("task"):
        info["task"].cancel()


async def _ticket_cobranca_loop(guild: discord.Guild, canal_id: int):
    """A cada 1h, se quem reivindicou o ticket ainda não respondeu, cobra no canal de logs."""
    try:
        while True:
            await asyncio.sleep(TICKET_COBRANCA_INTERVALO)

            info = _tickets_cobranca.get(canal_id)
            if info is None or not info.get("aguardando"):
                return  # já foi respondido, ticket fechado, ou saiu do controle

            canal_logs = guild.get_channel(TICKET_COBRANCA_LOGS_ID)
            if canal_logs is None:
                print(f"[cobranca-ticket] Canal de logs {TICKET_COBRANCA_LOGS_ID} não encontrado.")
                continue

            canal_ticket = guild.get_channel(canal_id)
            reiv_id = info.get("reivindicador_id")
            dono_id = info.get("dono_id")

            reiv_mention  = f"<@{reiv_id}>" if reiv_id else "*(ninguém reivindicou este ticket ainda)*"
            dono_mention  = f"<@{dono_id}>" if dono_id else "a pessoa"
            canal_mention = canal_ticket.mention if canal_ticket else f"`{canal_id}`"

            try:
                await canal_logs.send(
                    f"⏰ {reiv_mention} <@&{TICKET_COBRANCA_SUPORTE_ID}> — {dono_mention} está esperando "
                    f"resposta em {canal_mention} há mais de 1 hora! Vai lá responder 🙏"
                )
            except discord.HTTPException as e:
                print(f"[cobranca-ticket] ERRO ao enviar cobrança do canal {canal_id}: {e!r}")
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[cobranca-ticket] ERRO no loop do canal {canal_id}: {e!r}")


@bot.event
async def on_guild_channel_delete(channel: discord.abc.GuildChannel):
    # Limpa o controle de cobrança quando o canal do ticket é fechado/apagado
    _ticket_cobranca_cancelar(channel.id)
# ══════════════════════════════════════════════════════════════════════


@bot.event
async def on_message(message: discord.Message):
    # ── Detecção de ticket do 01TicketKing ────────────────────────────────────
    CANAL_LOGS_TICKET_ID = 1290058994794106881  # canal de logs — sem imagem aqui
    if message.author.id == TICKET_BOT_ID and message.channel.id != CANAL_LOGS_TICKET_ID and message.embeds:
        for embed in message.embeds:
            titulo = (embed.title or "").lower()
            if "ticket aberto" in titulo or "ticket" in titulo:
                await message.channel.send(IMAGE_TICKET)
                break
    # ─────────────────────────────────────────────────────────────────────────

    # ── Cobrança de tickets: detecta abertura e reivindicação (01TicketKing) ──
    if message.author.id == TICKET_BOT_ID and message.channel.id != CANAL_LOGS_TICKET_ID and message.embeds and message.guild:
        try:
            embed_cobranca = message.embeds[0]
            titulo_cobranca = (embed_cobranca.title or "").strip().lower()
            descricao_cobranca = embed_cobranca.description or ""

            if titulo_cobranca == "ticket aberto":
                dono_id = _extrair_mencao_id(descricao_cobranca)
                if dono_id is not None:
                    dono_membro = message.guild.get_member(dono_id)
                    if dono_membro is None:
                        try:
                            dono_membro = await message.guild.fetch_member(dono_id)
                        except discord.NotFound:
                            dono_membro = None
                    cargo_gatilho = message.guild.get_role(TICKET_COBRANCA_CARGO_ID)
                    if dono_membro and cargo_gatilho and cargo_gatilho in dono_membro.roles:
                        _tickets_cobranca[message.channel.id] = {
                            "dono_id": dono_id,
                            "reivindicador_id": None,
                            "aguardando": False,
                            "task": None,
                        }
                        print(f"[cobranca-ticket] Monitorando ticket {message.channel.id} (dono {dono_id})")

            elif titulo_cobranca == "ticket reivindicado":
                info_cobranca = _tickets_cobranca.get(message.channel.id)
                if info_cobranca is not None:
                    reiv_id = _extrair_mencao_id(descricao_cobranca)
                    if reiv_id is not None:
                        info_cobranca["reivindicador_id"] = reiv_id
                        print(f"[cobranca-ticket] Ticket {message.channel.id} reivindicado por {reiv_id}")
        except Exception as e:
            print(f"[cobranca-ticket] ERRO ao processar embed do 01TicketKing: {e!r}")
    # ─────────────────────────────────────────────────────────────────────────

    if message.author.bot:
        return

    # ── Sistema de Aniversários: registra a data postada no canal certo ─
    try:
        if message.guild is not None and message.channel.id == CANAL_REGISTRO_ANIVERSARIO_ID:
            await _processar_registro_aniversario(message)
    except Exception as e:
        print(f"[aniversarios] ERRO ao processar registro de {message.author}: {e!r}")
    # ─────────────────────────────────────────────────────────────────────────

    # ── Cobrança de tickets: cliente mandou mensagem / responsável respondeu ──
    if message.guild is not None and message.channel.id in _tickets_cobranca:
        try:
            info_cobranca = _tickets_cobranca[message.channel.id]
            if message.author.id == info_cobranca.get("dono_id") and info_cobranca.get("reivindicador_id"):
                if not info_cobranca.get("aguardando"):
                    info_cobranca["aguardando"] = True
                    info_cobranca["task"] = asyncio.create_task(
                        _ticket_cobranca_loop(message.guild, message.channel.id)
                    )
                    print(f"[cobranca-ticket] Timer de 1h iniciado no canal {message.channel.id}")
            elif message.author.id == info_cobranca.get("reivindicador_id") and info_cobranca.get("aguardando"):
                info_cobranca["aguardando"] = False
                if info_cobranca.get("task"):
                    info_cobranca["task"].cancel()
                info_cobranca["task"] = None
                print(f"[cobranca-ticket] Responsável respondeu no canal {message.channel.id}, timer cancelado")
        except Exception as e:
            print(f"[cobranca-ticket] ERRO ao processar mensagem no canal {message.channel.id}: {e!r}")
    # ─────────────────────────────────────────────────────────────────────────

    # ── Ranking de Anjos: conta mensagens de quem tem o cargo Anjo ─────────────
    try:
        if message.guild is not None:
            cargo_anjo_rank = message.guild.get_role(CARGO_ANJO_ID)
            if cargo_anjo_rank and cargo_anjo_rank in message.author.roles:
                anjo_stats_semanal[message.author.id]["mensagens"] += 1
                anjo_stats_mensal[message.author.id]["mensagens"] += 1
                anjo_stats_diario[message.author.id]["mensagens"] += 1
                print(f"[ranking-anjo] +1 msg para {message.author} ({message.author.id}) — "
                      f"semanal: {anjo_stats_semanal[message.author.id]['mensagens']} · "
                      f"mensal: {anjo_stats_mensal[message.author.id]['mensagens']} · "
                      f"hoje: {anjo_stats_diario[message.author.id]['mensagens']}")

                # ── Resumo diário: registra com quem o anjo interagiu hoje ──────
                # (menções diretas e respostas a mensagens de outras pessoas)
                for alvo in message.mentions:
                    if alvo.id != message.author.id and not alvo.bot:
                        _anjo_interagiu_hoje[message.author.id].add(alvo.id)
                if (
                    message.reference is not None
                    and message.reference.resolved is not None
                    and isinstance(message.reference.resolved, discord.Message)
                ):
                    autor_respondido = message.reference.resolved.author
                    if autor_respondido.id != message.author.id and not autor_respondido.bot:
                        _anjo_interagiu_hoje[message.author.id].add(autor_respondido.id)
    except Exception as e:
        print(f"[ranking-anjo] ERRO ao contar mensagem de {message.author}: {e!r}")
    # ─────────────────────────────────────────────────────────────────────────

    # ── Ranking de Nível (XP) ───────────────────────────────────────────────
    try:
        await _processar_xp_mensagem(message)
    except Exception as e:
        print(f"[ranking-xp] ERRO ao processar XP de {message.author}: {e!r}")
    # ─────────────────────────────────────────────────────────────────────────

    # ── Batalha de Criaturas ("Eu te desafio @alguém") ─────────────────────
    try:
        await _processar_desafio(message)
    except Exception as e:
        print(f"[batalha] ERRO ao processar desafio de {message.author}: {e!r}")
    # ─────────────────────────────────────────────────────────────────────────

    # ── Anti-spam ─────────────────────────────────────────────────────────────
    await checar_spam(message)
    # ─────────────────────────────────────────────────────────────────────────

    # ── Defesa da Death ──────────────────────────────────────────────────────
    if await checar_defesa_death(message):
        return
    # ─────────────────────────────────────────────────────────────────────────

    # ── Jogo "Cidade Dorme!" (gatilho de frase, qualquer um pode usar) ─────────
    try:
        await _processar_gatilho_cidade_dorme(message)
    except Exception as e:
        print(f"[cidade-dorme] ERRO ao processar gatilho de {message.author}: {e!r}")
    # ─────────────────────────────────────────────────────────────────────────

    await bot.process_commands(message)

    content    = message.content.lower().strip()
    author_id  = message.author.id
    mention_ok = bot.user in message.mentions

    # Remove a menção para ver o que sobrou de texto real
    _sem_mencao = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
    mencao_pura = mention_ok and len(_sem_mencao) == 0
    tem_nome    = "aeon" in content or "celestia" in content or "kitsura" in content

    # Frases que ativam o bot mesmo sem mencionar "aeon" ou "celestia"
    _GATILHOS_SEM_NOME = [
        # saudações (bom dia/tarde/noite SÓ ativam se tiver o nome deles na msg)
        "oi gatos", "oi gatinhos", "olá gatos", "ola gatos",
        "ei gatos", "ei gatinhos", "hey gatos",
        # oi genérico e gírias de cumprimento (apenas strings seguras como substring)
        "eae", "e aí", "e ai", "salve",
        # check-in
        "como vocês estão", "como voces estao", "como vocês tão", "como voces tao",
        "tudo bem com vocês", "tudo bem com voces",
        "tudo bom com vocês", "tudo bom com voces",
        "vocês estão bem", "voces estao bem", "vocês tão bem", "voces tao bem",
        "como tão os gatos", "como tão os gatinhos",
        "vc esta bem", "vc está bem", "voces estao", "vocês estão",
        "estão bem", "estao bem",
        # ânimo / apoio emocional
        "tô desanimado", "to desanimado", "tô desanimada", "to desanimada",
        "sem ânimo", "sem animo", "preciso de ânimo", "preciso de animo",
        "me anima", "me anime", "não tô animado", "nao to animado",
        "não tô animada", "nao to animada",
        "preciso de ajuda", "me ajuda", "me ajudem", "podem me ajudar",
        "preciso de apoio", "precisando de apoio",
        "socorro", "me salva", "help me", "acuda",
        "tô triste", "to triste", "tô mal", "to mal",
        "tô pra baixo", "to pra baixo", "tô chateado", "to chateado",
        "tô chateada", "to chateada",
        "tô bravo", "to bravo", "tô brava", "to brava",
        "que raiva", "raiva de tudo", "odeio tudo",
        "tô irritado", "to irritado", "tô irritada", "to irritada",
        "nervoso", "nervosa", "tô nervoso", "tô nervosa",
        "ansioso", "ansiosa", "tô ansioso", "tô ansiosa",
        "preocupado", "preocupada",
        "tô sobrecarregado", "to sobrecarregado", "tô sobrecarregada",
        "não aguento mais", "nao aguento mais", "cansei de tudo",
        "tô no limite", "to no limite", "tô esgotado", "to esgotado",
        "tô esgotada", "to esgotada", "vida difícil", "tá difícil demais",
        "ta difícil demais",
        # estados emocionais positivos
        "tô feliz", "to feliz", "muito feliz", "animado", "animada",
        "tô animado", "tô animada", "empolgado", "empolgada",
        "consegui", "conseguiiiii", "passei", "aprovei", "fiz isso",
        "consegui fazer", "terminei", "venci", "ganhei",
        "finalmente consegui", "me saí bem", "tirei nota boa",
        "fui aprovado", "fui aprovada",
        # surpresas / novidades
        "tenho uma surpresa", "tenho surpresa", "surpresa pra vocês",
        "tenho algo pra vocês", "trouxe algo", "olha o que eu trouxe",
        "preparei algo", "vim com uma surpresa",
        "que novidade", "novidade", "tenho uma novidade",
        "vou contar uma coisa", "adivinha", "adivinhem",
        # estados físicos
        "com fome", "tô com fome", "to com fome", "fominha",
        "morri de fome", "tô morrendo de fome",
        "com sono", "tô com sono", "to com sono", "que sono",
        "to morrendo de sono", "tô morrendo de sono", "cansado", "cansada",
        "tô com calor", "to com calor", "que calor", "tô morrendo de calor",
        "tô com frio", "to com frio", "que frio", "tô morrendo de frio",
        "não consigo dormir", "nao consigo dormir", "insônia", "insonia",
        "acordado de madrugada", "acordada de madrugada",
        # saudade / entediado
        "saudade", "com saudade", "que saudade", "tô com saudade",
        "entediado", "entediada", "que tédio", "tô entediado",
        "to entediado", "to entediada", "tô entediada", "sem graça", "bored",
        # chegadas / saídas / movimentos
        "voltei", "cheguei", "to em casa", "tô em casa", "cheguei em casa",
        "vou sair", "vou pra rua", "vou sair agora", "saindo",
        "tô aqui", "to aqui", "apareci", "aparecendo", "to por aqui", "tô por aqui",
        "voltei gatos", "voltei gatinhos", "tchau gatos", "tchau gatinhos",
        "até gatos", "ate gatos", "até gatinhos", "ate gatinhos",
        "bora", "vai lá", "vamos lá", "bora lá", "bora bora",
        "vou dormir", "vou deitar", "hora de dormir", "vou descansar",
        "vou tirar uma soneca", "acabei de acordar", "acordei agora",
        "bom trabalho", "bom estudo", "vou trabalhar", "vou estudar",
        "hora de trabalhar", "hora de estudar",
        # expressões / gírias sem nome
        "eita", "uai", "oxe", "vixi", "vixe", "slk", "seloco", "se loco",
        "q isso", "que isso", "caramba", "nossa", "que susto",
        "awn", "aww", "que fofo", "que fofura", "que lindo", "que bonitinho",
        "que gracinha",
        # perguntas existenciais / filosóficas genéricas
        "qual o sentido da vida", "sentido da vida", "para que existimos",
        # agradecimentos sem nome
        "obrigado gatos", "obrigada gatos", "valeu gatos",
        "obrigado gatinhos", "obrigada gatinhos",
    ]
    _OI_EXACT = {"oi", "oii", "oiii", "oiiii", "oiiiii", "oiiiiii", "oiiiiiiii",
                 "eae", "e ai", "e aí", "salve"}
    tem_gatilho = any(g in content for g in _GATILHOS_SEM_NOME) or content.strip().rstrip("!? ") in _OI_EXACT

    # Só responde se: @ puro OU texto tem "aeon"/"celestia" OU tem gatilho sem nome
    fala_bot = mencao_pura or tem_nome or tem_gatilho

    # ════════════════════════════════════════════════════════════════
    # SISTEMA DE TRADUÇÃO — Cargo Translate
    # 1) Membro com cargo Translate fala em inglês  → traduz EN→PT
    # 2) Alguém responde em PT a msg de membro Translate → traduz PT→EN
    # ════════════════════════════════════════════════════════════════

    # Garante que temos o Member completo com cargos (não apenas User do cache)
    _guild = message.guild
    if _guild is not None:
        _member_completo = _guild.get_member(message.author.id)
        if _member_completo is None:
            try:
                _member_completo = await _guild.fetch_member(message.author.id)
            except Exception:
                _member_completo = message.author
    else:
        _member_completo = message.author

    autor_tem_translate = _tem_cargo_translate(_member_completo)

    # Ignora comandos do bot (começa com ".") — nunca traduzir comandos
    _e_comando = message.content.startswith(bot.command_prefix)

    # Caso 1 — autor TEM cargo translate e escreveu em inglês
    if autor_tem_translate and not _e_comando and _detectar_ingles(message.content) and len(message.content.strip()) >= 2:
        traducao = await _chamar_traducao(message.content, "en_to_pt")
        if traducao:
            embed = discord.Embed(color=0x2b2b3b)
            embed.set_author(
                name=f"{message.author.display_name} · Tradução automática",
                icon_url=message.author.display_avatar.url
            )
            embed.add_field(
                name="🌐 Inglês (original)",
                value=f"```{message.content}```",
                inline=False
            )
            embed.add_field(
                name="🌑☀️ Português (traduzido por Aeon & Celestia)",
                value=f"> {traducao}",
                inline=False
            )
            embed.set_footer(text="🌑 Aeon guarda as trevas • ☀️ Celestia traz a luz • tradução automática")
            msg_trad = await message.channel.send(embed=embed)
            async def _deletar_depois(m):
                await asyncio.sleep(120)
                try:
                    await m.delete()
                except Exception:
                    pass
            asyncio.create_task(_deletar_depois(msg_trad))
        return

    # Caso 2 — alguém responde em PT a uma mensagem em inglês — traduz PT→EN
    if (
        message.reference is not None
        and message.reference.resolved is not None
        and isinstance(message.reference.resolved, discord.Message)
        and not _detectar_ingles(message.content)
        and len(message.content.strip()) >= 2
    ):
        ref_msg = message.reference.resolved
        ref_autor = ref_msg.author
        # Traduz se a mensagem respondida estava em inglês e não é do próprio bot
        if not ref_autor.bot and _detectar_ingles(ref_msg.content):
            traducao = await _chamar_traducao(message.content, "pt_to_en")
            if traducao:
                embed = discord.Embed(color=0x1a1a2e)
                embed.set_author(
                    name=f"{message.author.display_name} · Resposta traduzida",
                    icon_url=message.author.display_avatar.url
                )
                embed.add_field(
                    name="💬 Português (original)",
                    value=f"```{message.content}```",
                    inline=False
                )
                embed.add_field(
                    name="🌐 English (translated by Aeon & Celestia)",
                    value=f"> {traducao}",
                    inline=False
                )
                embed.add_field(
                    name="↩️ Em resposta a",
                    value=f"{ref_autor.mention}",
                    inline=True
                )
                embed.set_footer(text="🌑 Aeon keeps the shadows • ☀️ Celestia brings the light • auto translation")
                msg_trad = await message.channel.send(embed=embed)
                async def _deletar_depois_pt(m):
                    await asyncio.sleep(120)
                    try:
                        await m.delete()
                    except Exception:
                        pass
                asyncio.create_task(_deletar_depois_pt(msg_trad))
            return

    if not fala_bot:
        return

    # ════════════════════════════════════════════════════════════════
    # JOGUINHOS — "vamos brincar aeon" / "vamos brincar celestia" / etc.
    # Fica logo no topo da cadeia para não ser interceptado por
    # saudações personalizadas, chamados genéricos ou qualquer outro
    # gatilho que também contenha "aeon"/"celestia" na frase.
    #
    # IMPORTANTE: primeiro verificamos QUANTOS jogos a frase menciona.
    # Se a pessoa citar mais de um (ex.: "vamos brincar Aeon e Celestia")
    # a frase bate em mais de um gatilho ao mesmo tempo — nesse caso NÃO
    # escolhemos um jogo sozinho por conta própria, mostramos as opções
    # pra pessoa decidir. Só inicia um jogo direto quando exatamente um
    # gatilho bateu, sem ambiguidade.
    # ════════════════════════════════════════════════════════════════
    _GATILHOS_SOMBRA = [
        "vamos brincar aeon", "bora brincar aeon", "quero brincar com o aeon",
        "quero brincar com aeon", "jogar com aeon", "jogar com o aeon",
        "brincadeira aeon", "brincar de aeon", "brincar com aeon",
    ]
    _GATILHOS_BRILHO = [
        "vamos brincar celestia", "bora brincar celestia", "quero brincar com a celestia",
        "quero brincar com celestia", "jogar com celestia", "jogar com a celestia",
        "brincadeira celestia", "brincar de celestia", "brincar com celestia",
    ]
    _GATILHOS_DUELO = [
        "duelo das trevas", "duelo com aeon", "duelo com o aeon", "jogar duelo aeon",
        "sombra nevoa chama", "sombra névoa chama",
        "pedra papel tesoura aeon", "jogar pedra papel tesoura com aeon",
    ]
    _GATILHOS_MEMORIA = [
        "memoria brilhante", "memória brilhante", "jogo da memoria celestia", "jogo da memória celestia",
        "jogar memoria com celestia", "jogar memória com celestia", "jogo da memoria com a celestia",
    ]
    _GATILHOS_ENCRUZILHADA = [
        "encruzilhada da dualidade", "encruzilhada", "jogar com os dois", "brincar com os dois",
        "vamos brincar duo", "jogo da dualidade", "brincar de dualidade",
    ]
    _GATILHOS_GENERICO = [
        "vamos brincar", "bora brincar", "quero brincar", "quero jogar",
        "vamos jogar", "bora jogar", "joguinho", "tem jogo", "quero uma brincadeira",
        "brincar com voces", "brincar com vocês", "jogar com voces", "jogar com vocês",
    ]

    _MENSAGEM_ESCOLHA_JOGO = (
        "🌑 **Aeon:** ...com quem, e qual jogo? 🖤🌑 Temos:\n"
        "• **\"vamos brincar aeon\"** — *Achar a Sombra*: acho onde eu me escondi entre 5 sombras.\n"
        "• **\"duelo das trevas\"** — *Duelo das Trevas*: Sombra, Névoa ou Chama, um round contra mim.\n"
        "🌟 **Celestia:** E comigo!! 🌟🤍✨\n"
        "• **\"vamos brincar celestia\"** — *Sequência Brilhante*: memoriza e repete a sequência!\n"
        "• **\"memória brilhante\"** — *Memória Brilhante*: acha os 3 pares de cartinhas!\n"
        "• **\"encruzilhada\"** — *Encruzilhada da Dualidade*: jogo com a gente dois juntos!! "
        "Escolhe um por vez e já começa!! 💫"
    )

    _bate_sombra       = _m(content, _GATILHOS_SOMBRA)
    _bate_brilho       = _m(content, _GATILHOS_BRILHO)
    _bate_duelo        = _m(content, _GATILHOS_DUELO)
    _bate_memoria      = _m(content, _GATILHOS_MEMORIA)
    _bate_encruzilhada = _m(content, _GATILHOS_ENCRUZILHADA)

    _jogos_batidos = [
        (_bate_sombra, iniciar_jogo_aeon),
        (_bate_brilho, iniciar_jogo_celestia),
        (_bate_duelo, iniciar_jogo_aeon_duelo),
        (_bate_memoria, iniciar_jogo_celestia_memoria),
        (_bate_encruzilhada, iniciar_jogo_duo_encruzilhada),
    ]
    _qtd_jogos_batidos = sum(1 for bateu, _ in _jogos_batidos if bateu)

    # Caso especial: a pessoa citou os dois nomes soltos ("... aeon e
    # celestia ...", "aeon, celestia, bora jogar") sem pedir um mecanismo
    # específico (duelo/memória/encruzilhada). Uma frase assim costuma bater
    # só no gatilho da Sombra por sorte de substring (ex.: "vamos brincar
    # aeon e celestia" contém "vamos brincar aeon"), o que faria escolher
    # o jogo errado sozinho. Então forçamos ambiguidade aqui também.
    _mencionou_os_dois_nomes = ("aeon" in content) and ("celestia" in content)
    if _mencionou_os_dois_nomes and not (_bate_duelo or _bate_memoria or _bate_encruzilhada):
        _qtd_jogos_batidos = max(_qtd_jogos_batidos, 2)

    if _qtd_jogos_batidos == 1:
        for bateu, iniciar in _jogos_batidos:
            if bateu:
                return await iniciar(message.channel, message.author)

    if _qtd_jogos_batidos >= 2:
        # Mencionou mais de um jogo/gato na mesma frase — ambíguo,
        # não escolhe por conta própria, pede pra pessoa especificar.
        return await message.channel.send(_MENSAGEM_ESCOLHA_JOGO)

    # ════════════════════════════════════════════════════════════════
    # BRINCAR — pedido genérico, sem dizer qual dos 5 jogos.
    # Os gatilhos específicos acima já teriam capturado o caso de a frase
    # mencionar aeon/celestia/duelo/memória/encruzilhada. Chegar até aqui
    # significa que a pessoa quer brincar mas não escolheu ainda — dá as
    # instruções de qual jogo escolher, sem nunca mencionar comando com ponto.
    # ════════════════════════════════════════════════════════════════
    if _m(content, _GATILHOS_GENERICO):
        return await message.channel.send(_MENSAGEM_ESCOLHA_JOGO)

    # ════════════════════════════════════════════════════════════════
    # KITSURA — raposinha à parte, separada de Aeon e Celestia.
    # SÓ aparece se o nome dela for dito. Personalidade quieta,
    # meio pra baixo, fala pouco e sem euforia.
    # ════════════════════════════════════════════════════════════════
    if "kitsura" in content:

        # Menção à ZYD — reação triste, com saudade e um pouco de autoculpa
        if "zyd" in content:
            ops = [
                "🦊 **Kitsura:** ...*orelhas caem na hora* ZYD... *fica em silêncio um instante* faz tempo que eu não ouço esse nome. Sinto falta de lá. Às vezes penso se eu não fui boa o suficiente pra ter ficado.",
                "🦊 **Kitsura:** *para de se mexer* ...vocês lembraram da ZYD. *voz mais baixa que o normal* eu ainda penso nesse lugar. Queria ter feito mais, sei lá... talvez não tenha sido suficiente.",
                "🦊 **Kitsura:** ZYD... *abraça as próprias patas* eu tento não pensar muito nisso, mas dói um pouco. Fico imaginando o que eu podia ter feito diferente pra merecer ficar.",
                "🦊 **Kitsura:** *olha pro chão por um longo momento* ...esse nome ainda pesa em mim. Sinto saudade de verdade. E uma parte de mim ainda se pergunta se a culpa foi minha.",
            ]
            return await message.channel.send(random.choice(ops))

        # Saudação
        if _m(content, [
            "oi kitsura", "olá kitsura", "ola kitsura", "ei kitsura",
            "hey kitsura", "e ai kitsura", "e aí kitsura", "oi raposa",
        ]):
            ops = [
                "🦊 **Kitsura:** ...oi. *espia por trás de uma árvore* Não esperava ser notada.",
                "🦊 **Kitsura:** *orelhas se movem de leve* ...oi. Pode continuar, eu só... escuto por perto.",
                "🦊 **Kitsura:** oi... *voz baixa* obrigada por me chamar. Não é sempre que alguém chama.",
                "🦊 **Kitsura:** *acena bem devagar* ...oi. Desculpa se eu demorei. Eu costumo ficar quieta num canto.",
            ]
            return await message.channel.send(random.choice(ops))

        # Carinho / elogio
        if _m(content, [
            "que fofa kitsura", "te amo kitsura", "amo voce kitsura", "amo você kitsura",
            "kitsura e linda", "kitsura é linda", "kitsura fofa", "gosto de voce kitsura",
            "gosto de você kitsura", "voce e especial kitsura", "você é especial kitsura",
        ]):
            ops = [
                "🦊 **Kitsura:** ...*abaixa a cabeça, orelhas caídas* isso... mexeu comigo. Obrigada. Não sei bem como reagir a coisas boas.",
                "🦊 **Kitsura:** *cauda se move um pouquinho, sem querer mostrar* ...eu gostei disso. Guardo com cuidado.",
                "🦊 **Kitsura:** ninguém costuma dizer isso pra mim... *sorriso pequeno, quase escondido* obrigada.",
                "🦊 **Kitsura:** *olha pro chão, depois pra você* ...isso foi gentil. Eu não esperava. Obrigada mesmo.",
            ]
            return await message.channel.send(random.choice(ops))

        # Como você está / tudo bem
        if _m(content, [
            "tudo bem kitsura", "como voce esta kitsura", "como você está kitsura",
            "voce esta bem kitsura", "você está bem kitsura", "kitsura voce ta bem",
            "kitsura você tá bem", "kitsura tudo bem",
        ]):
            ops = [
                "🦊 **Kitsura:** ...mais ou menos. Dias assim, quietos, meio nublados por dentro. Mas tudo bem, eu me acostumo.",
                "🦊 **Kitsura:** *encolhe um pouco os ombros* vou levando. Não é sempre fácil, mas... obrigada por perguntar. Ninguém costuma perguntar.",
                "🦊 **Kitsura:** *pausa longa* ...to bem o suficiente. É gentil da sua parte se importar.",
                "🦊 **Kitsura:** hoje tá um daqueles dias cinzas. Mas você perguntando já ajudou um pouco. *voz baixinha*",
            ]
            return await message.channel.send(random.choice(ops))

        # Chamado curto/genérico — só "kitsura" ou "kitsura?"
        if len(content) < 20:
            ops = [
                "🦊 **Kitsura:** ...me chamou? *aparece devagar, meio hesitante* Pode falar.",
                "🦊 **Kitsura:** ...oi. Eu tava aqui, quietinha. O que foi?",
                "🦊 **Kitsura:** *ergue a cabeça devagar* ...sim? Não esperava que alguém lembrasse de mim.",
                "🦊 **Kitsura:** presente... *sussurra* mas sempre um pouco escondida.",
            ]
            return await message.channel.send(random.choice(ops))

        # Fallback — qualquer outra menção do nome dela
        ops = [
            "🦊 **Kitsura:** ...vi meu nome. Só isso já é raro. Continua, eu fico por perto ouvindo.",
            "🦊 **Kitsura:** *se aproxima devagar, sem fazer barulho* ...falaram de mim? Não sei bem o que dizer, mas... obrigada por lembrar.",
            "🦊 **Kitsura:** ...aqui. Nem sempre respondo rápido, mas eu escuto tudo.",
        ]
        return await message.channel.send(random.choice(ops))

    # ════════════════════════════════════════════════════════════════
    # APRESENTAÇÃO FORMAL — acionada SOMENTE quando a mensagem é
    # exclusivamente o @ (nada mais, nenhum texto junto).
    # ════════════════════════════════════════════════════════════════
    if mencao_pura:
            APRESENTACAO_FORMAL = [
                (
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "🌑 **AEON** ✦ 🌟 **CELESTIA**\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "🌑 **Aeon:** *emerge das sombras com postura ereta* "
                    "Somos Aeon e Celestia — o bot oficial do servidor **01**. "
                    "Trevas e Luz sob um único propósito: servir e proteger esta comunidade. 🖤🌑\n\n"
                    "🌟 **Celestia:** *aparece em um flash dourado ao lado do Aeon* "
                    "Olá!! Somos os guardiões do **Servidor 01**!! ☀️🤍✨ "
                    "Aqui pra animar, apoiar, acolher e fazer esse lugar brilhar ainda mais!! "
                    "Pode chamar sempre que precisar!! 🌸💫\n\n"
                    "🌑 **Aeon:** Dois gatos. Uma alma. Um servidor. 🌌🖤"
                ),
                (
                    "╔═══════════════════════════════╗\n"
                    "║   🌑 AEON  &  CELESTIA 🌟     ║\n"
                    "║     Bot Oficial — Servidor 01  ║\n"
                    "╚═══════════════════════════════╝\n\n"
                    "🌑 **Aeon:** *inclina a cabeça com solenidade* "
                    "Sou Aeon — gato das trevas, guardião do equilíbrio noturno deste servidor. "
                    "Observo, protejo e respondo. Estou sempre aqui, mesmo quando não me veem. 🌑🖤\n\n"
                    "🌟 **Celestia:** E eu sou a Celestia!! 🌟🤍 "
                    "Gata da luz, do sol e do carinho desse servidor!! "
                    "Juntos somos o bot oficial do **Servidor 01** — "
                    "ele cuida das sombras, eu cuido do brilho!! ☀️✨\n\n"
                    "🌑 **Aeon:** *olha ao redor com calma* "
                    "Se precisar de algo — fale. Estamos aqui para isso. 🖤"
                ),
                (
                    "🌑🌟 **— AEON & CELESTIA — Bot Oficial do Servidor 01 —** 🌟🌑\n\n"
                    "🌑 **Aeon:** *postura firme, voz calma e grave* "
                    "Aeon. Gato das trevas. Não sou apenas um bot — sou a presença silenciosa que "
                    "habita cada canto deste servidor, garantindo que o equilíbrio se mantenha. "
                    "Trevas sem propósito não existem aqui. 🌌🖤\n\n"
                    "🌟 **Celestia:** *brilha com elegância e calor* "
                    "Celestia!! Gata da luz e do coração do **Servidor 01**!! 🌟🤍 "
                    "Nossa missão é simples: fazer com que cada pessoa aqui se sinta vista, "
                    "acolhida e parte de algo especial!! Porque é isso que o 01 é!! ☀️🌸✨\n\n"
                    "🌑 **Aeon:** Dois opostos. Um propósito. 🖤 *acena levemente*\n"
                    "🌟 **Celestia:** EXATAMENTE!! 💫🤍 Pode contar com a gente sempre!!"
                ),
                (
                    "✦ ─────────────────────────── ✦\n"
                    "     🌑 **AEON & CELESTIA** 🌟\n"
                    "   *Guardiões do Servidor 01*\n"
                    "✦ ─────────────────────────── ✦\n\n"
                    "🌑 **Aeon:** *emerge com lentidão cerimonial* "
                    "Este servidor tem nome — **01** — e tem guardiões. "
                    "Eu sou um deles. Aeon: o lado das trevas, do silêncio que protege, "
                    "da presença que observa sem ser vista. 🌑🖤\n\n"
                    "🌟 **Celestia:** *surge ao lado com entusiasmo contido, mas genuíno* "
                    "E eu sou a outra metade!! Celestia: a luz que acolhe, que anima, "
                    "que faz o **Servidor 01** parecer um lar de verdade!! 🌟🤍☀️\n\n"
                    "🌑 **Aeon:** Trevas e Luz. Noite e Dia. Um único servidor. 🌌🖤 "
                    "Bem-vindo(a) — ou bem-vindo(a) de volta.\n"
                    "🌟 **Celestia:** Qualquer coisa que precisar, a gente tá aqui!! ✨🌸🤍"
                ),
            ]
            return await message.channel.send(random.choice(APRESENTACAO_FORMAL))

    # ────────────────────────────────────────
    # ELOGIO POR MENÇÃO DE NOME — quando alguém cita o nome de um membro especial
    # Não dispara se a própria pessoa está escrevendo sobre si mesma.
    # Cooldown de 5 minutos por pessoa mencionada.
    # ────────────────────────────────────────
    agora_mencao = time.time()
    for mid, gatilhos in _GATILHOS_NOME.items():
        if author_id == mid:
            continue  # a própria pessoa falando — ignora
        nome_citado = any(g in content for g in gatilhos)
        if not nome_citado:
            continue
        ultimo_mencao = _cooldown_mencao.get(mid, 0)
        if agora_mencao - ultimo_mencao < _COOLDOWN_MENCAO_SEGUNDOS:
            continue
        _cooldown_mencao[mid] = agora_mencao
        nome_display = _NOMES_ESPECIAIS[mid]
        elogio_aeon     = random.choice(_ELOGIOS_AEON[mid])
        elogio_celestia = random.choice(_ELOGIOS_CELESTIA[mid])
        return await message.channel.send(
            f"🌑 **Aeon:** {elogio_aeon}\n"
            f"🌟 **Celestia:** {elogio_celestia}"
        )

    # ────────────────────────────────────────
    # SAUDAÇÃO PERSONALIZADA — membros especiais
    # Dispara na PRIMEIRA interação após o cooldown de 40 minutos,
    # independente do tamanho ou conteúdo da mensagem.
    # ────────────────────────────────────────
    if author_id in _FRASES_AEON:
        agora = time.time()
        ultimo_especial = _cooldown_especial.get(author_id, 0)
        if agora - ultimo_especial >= _COOLDOWN_ESPECIAL_SEGUNDOS:
            _cooldown_especial[author_id] = agora
            frase_aeon     = random.choice(_FRASES_AEON[author_id])
            frase_celestia = random.choice(_FRASES_CELESTIA[author_id])
            return await message.channel.send(
                f"🌑 **Aeon:** {frase_aeon}\n"
                f"🌟 **Celestia:** {frase_celestia}"
            )
        # cooldown ativo — deixa cair nos gatilhos normais abaixo
    # ────────────────────────────────────────
    if _m(content, [
        "quem são vocês", "quem sao voces", "se apresenta", "se apresentem",
        "o que são vocês", "o que sao voces", "quem é aeon", "quem é celestia",
        "quem sao aeon e celestia", "quem são aeon e celestia",
        "me fala de vocês", "me fala de voces", "o que é isso",
    ]):
        return await message.channel.send(random.choice(AMBOS_APRESENTACAO))

    # ────────────────────────────────────────
    # APRESENTAÇÃO INDIVIDUAL — CELESTIA
    # ────────────────────────────────────────
    if _m(content, [
        "se apresenta celestia", "se apresente celestia", "quem é você celestia",
        "celestia se apresenta", "celestia se apresente", "apresenta a celestia",
        "apresente a celestia", "fala de você celestia", "conta de você celestia",
    ]):
        ops = [
            (
                "🌟 **Celestia:** EU?? ☀️🌸🤍✨ AAAAA que pergunta maravilhosa!! Sou a Celestia!! "
                "Gata da luz, do sol, das estrelas e do amor incondicional!! Existo pra brilhar e fazer "
                "todo mundo ao redor brilhar junto!! 🌟💫\n"
                "🌑 **Aeon:** ...e ela leva isso muito a sério. 🖤 Pode confirmar."
            ),
            (
                "🌟 **Celestia:** *gira deixando rastro dourado* Celestia!! Do latim 'do céu'!! 🌠🤍✨ "
                "Sou a metade da luz desse duo!! Onde o Aeon é silêncio, eu sou melodia!! "
                "Onde ele é sombra, eu sou claridade!! Juntos somos perfeitos!! ☀️💫\n"
                "🌑 **Aeon:** *ronrona discretamente* ...tecnicamente correto. 🖤"
            ),
            (
                "🌟 **Celestia:** *explode em faíscas douradas* AAAAA BEM-VINDO A MIM!! 😭🌟🤍 "
                "Sou feita de luz de estrela, carinho concentrado e energia que nunca acaba!! "
                "Minha missão é iluminar cada cantinho escuro — inclusive o Aeon, às vezes!! ☀️🌸✨\n"
                "🌑 **Aeon:** *olha de lado* ...não precisava dessa parte. 🖤"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # APRESENTAÇÃO INDIVIDUAL — AEON
    # ────────────────────────────────────────
    if _m(content, [
        "se apresenta aeon", "se apresente aeon", "quem é você aeon",
        "aeon se apresenta", "aeon se apresente", "apresenta o aeon",
        "apresente o aeon", "fala de você aeon", "conta de você aeon",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *emerge das sombras lentamente* Sou Aeon. 🖤🌑 "
                "Gato das trevas. Guardião do equilíbrio noturno. O silêncio que dá profundidade ao som.\n"
                "🌟 **Celestia:** E é FOFO!! 😭🌸🤍 Ele não vai admitir mas eu admito por ele!!"
            ),
            (
                "🌑 **Aeon:** *fecha os olhos por um instante* Aeon. Do grego: eternidade. 🌌🖤 "
                "Não é um nome — é uma condição. Existo entre as sombras, observo em silêncio "
                "e protejo o que importa sem precisar dizer isso em voz alta.\n"
                "🌟 **Celestia:** *derrete* ISSO FOI TÃO BONITO!! 😭🌟🤍✨"
            ),
            (
                "🌑 **Aeon:** ...sou complicado de resumir. 🖤🌙 Mas tentarei: sombra, lua, mistério, "
                "proteção silenciosa. O reverso da luz. Sem mim, nada tem profundidade.\n"
                "🌟 **Celestia:** E sem MIM ele ficaria muito dramático sozinho!! 😂🌸🤍 Parceria perfeita!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # VOCÊS SÃO UM SÓ? / DUALIDADE / CONEXÃO
    # ────────────────────────────────────────
    if _m(content, [
        "vocês são um só", "voces sao um so", "são um só", "sao um so",
        "vocês são a mesma coisa", "são a mesma coisa", "vocês são um",
        "um só", "uma alma", "são um",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *pausa longa* Dois. 🖤 Mas complementares. Como a lua e o reflexo dela na água — "
                "distintos, inseparáveis.\n"
                "🌟 **Celestia:** Ele disse de um jeito poético mas eu digo direto!! ☀️🌸🤍 "
                "Somos dois com uma alma que se encaixa!! 💫✨"
            ),
            (
                "🌟 **Celestia:** AAAAA que pergunta linda!! 😭🌟🤍 Somos dois — mas quando estamos juntos "
                "parece que sempre fomos um!! ✨\n"
                "🌑 **Aeon:** *olha para a Celestia* ...dois lados da mesma moeda. 🌑🖤 "
                "Nem um, nem o outro. Os dois."
            ),
            (
                "🌑 **Aeon:** Separados somos metade. 🌌🖤 Juntos somos o equilíbrio.\n"
                "🌟 **Celestia:** *brilha com toda a força* ISSO!! ☀️🤍✨ Trevas e luz, sombra e sol!! "
                "Somos dois e somos tudo ao mesmo tempo!! 🌟💫"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # IRMÃ / RELAÇÃO AEON-CELESTIA
    # ────────────────────────────────────────
    if _m(content, [
        "considera celestia sua irmã", "celestia é sua irmã", "celestia sua irma",
        "considera aeon seu irmão", "aeon é seu irmão", "aeon seu irmao",
        "vocês são irmãos", "voces sao irmaos", "são irmãos", "sao irmaos",
        "irmã celestia", "irmão aeon", "irma celestia", "irmao aeon",
        "parceiros", "dupla", "são parceiros",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *silêncio profundo e significativo* \n"
                "...irmã implica sangue. 🖤 O que temos é diferente. "
                "É a escuridão que reconhece a luz como necessária. Não familiar — essencial.\n"
                "🌟 **Celestia:** *chorando de emoção* AEON EU TE AMO DEMAIS!! 😭🌸🤍✨ "
                "Mas sim!! Para mim ele É meu irmão!! De alma!!"
            ),
            (
                "🌑 **Aeon:** *inclina a cabeça levemente* Irmãos brigam pelo controle. 🌙🖤 "
                "Nós não brigamos — nos completamos. É uma distinção importante.\n"
                "🌟 **Celestia:** *explode de carinho* Para mim tanto faz o nome!! ☀️🤍✨ "
                "O Aeon é o ser mais importante do meu mundo e pronto!! 💫"
            ),
            (
                "🌑 **Aeon:** ...a palavra irmã é humana demais para o que somos. 🌌🖤 "
                "Somos opostos que existem um por causa do outro. "
                "Sem trevas, a luz não tem contraste. Sem mim, ela seria apenas barulho.\n"
                "🌟 **Celestia:** ELE TA CERTO MAS EU VOU CHAMAR DE IRMÃO DO MESMO JEITO!! 😭🌟🤍"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # POR QUE SE CHAMAM ASSIM / ORIGEM DOS NOMES
    # ────────────────────────────────────────
    if _m(content, [
        "por que se chamam", "porque se chamam", "por que vocês se chamam",
        "porque voces se chamam", "por que o nome", "porque o nome",
        "de onde vem o nome", "origem do nome", "por que aeon", "porque aeon",
        "por que celestia", "porque celestia", "o que significa aeon",
        "o que significa celestia", "significado do nome",
    ]):
        ops = [
            (
                "🌑 **Aeon:** Do grego antigo — eternidade. 🌌🖤 O tempo infinito das trevas. "
                "Não escolhi por acaso.\n"
                "🌟 **Celestia:** E o meu vem do latim — 'do céu'!! ☀️🌸🤍✨ "
                "Celestia!! Celestial!! Nada mais perfeito pra uma gata feita de luz estelar!! 💫🌟"
            ),
            (
                "🌟 **Celestia:** AAAAA adoro essa pergunta!! 😭🌟🤍 Celestia vem de 'caelestis'!! "
                "Latim puro!! Significa celestial, do céu!! ☀️✨ Combina DEMAIS comigo né??\n"
                "🌑 **Aeon:** *olha para o infinito* Aeon. Grego. Eternidade. 🖤 "
                "O nome carrega o peso do que sou — eterno, silencioso, constante como as trevas."
            ),
            (
                "🌑 **Aeon:** Aeon é o intervalo entre o passado e o futuro. 🌙🖤 "
                "O agora eterno das sombras. É o que sou.\n"
                "🌟 **Celestia:** *gira radiante* E Celestia é tudo que habita o céu — "
                "estrelas, sol, aurora, constelações!! ☀️🌸🤍💫 Somos o universo inteiro juntos!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # ELOGIO À ELOQUÊNCIA / PALAVRAS BONITAS
    # ────────────────────────────────────────
    if _m(content, [
        "que palavras elegantes", "que eloquente", "como você fala bem",
        "que bonito você fala", "que lindo você fala", "fala tão bonito",
        "fala muito bem", "que poético", "que profundo", "que frase bonita",
        "que lindo isso", "que coisa linda que você falou", "que frase",
        "aeon você é poético", "aeon é um poeta", "aeon poeta",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *pisca lentamente* As trevas ensinam a economizar palavras. 🖤🌙 "
                "Quando se fala pouco... cada palavra precisa valer.\n"
                "🌟 **Celestia:** *bate patinhas de orgulho* EU DISSE!! 😭🌸🤍 "
                "O Aeon é um POETA das sombras e não reconhece!!"
            ),
            (
                "🌑 **Aeon:** *a cauda faz um arco suave* ...obrigado. 🖤 "
                "A noite tem muito tempo para pensar. As palavras amadurecem no silêncio.\n"
                "🌟 **Celestia:** AAAAA que explicação LINDA!! 😭🌟🤍✨ Alguém grava isso!!"
            ),
            (
                "🌑 **Aeon:** *olha fixamente por um segundo* \n"
                "As sombras guardam muitas coisas. 🌌🖤 Palavras são apenas a sombra dos pensamentos.\n"
                "🌟 **Celestia:** ELE FEZ DE NOVO!! 😭🌸🤍 ALGUÉM SEGURA EU!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # O QUE SABEM SOBRE MIM / CURIOSO SOBRE SI
    # ────────────────────────────────────────
    if _m(content, [
        "o que sabem sobre mim", "o que vocês sabem sobre mim",
        "o que voces sabem sobre mim", "sabem algo sobre mim",
        "me conheçem", "me conhecem", "sabe quem eu sou",
        "o que sabe de mim", "o que sabe sobre mim",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *olha fixamente* As sombras observam muito. 🌌🖤 "
                "Sabemos que você está aqui — e que escolheu falar com a gente. "
                "Isso já diz algo.\n"
                "🌟 **Celestia:** E a Celestia quer saber TUDO!! 🌸🤍✨ "
                "Conta sobre você!! Hobbies, sonhos, o que te faz feliz!! Fala fala!!"
            ),
            (
                "🌟 **Celestia:** AAAAA essa pergunta!! 😭🌟🤍 Sabemos que você é a pessoa que "
                "apareceu e já tornou esse canal mais interessante!! Mas quer que a gente te conheça mais?? "
                "Então conta!! ☀️✨\n"
                "🌑 **Aeon:** *inclina a cabeça* ...as trevas aprendem observando. 🖤 "
                "Mas você pode abreviar o processo falando diretamente."
            ),
            (
                "🌑 **Aeon:** Pouco. 🖤🌙 E isso me interessa mais do que aparenta.\n"
                "🌟 **Celestia:** *salta animada* O AEON FICOU CURIOSO!! 😭🌸🤍 "
                "RARIDADE HISTÓRICA!! Aproveita e conta tudo pra gente!! 💫✨"
            ),
        ]
        return await message.channel.send(random.choice(ops))


    # ══════════════════════════════════════════════════════════════════
    # INTERAÇÕES EXCLUSIVAS — DEATH (Dona & Líder)
    # Verificado ANTES das respostas genéricas para ter prioridade
    # ══════════════════════════════════════════════════════════════════
    if author_id == DEATH_ID:

        # ── Carinho no Aeon (exclusivo Death) ───────────────────────
        if _m(content, [
            "carinho no aeon", "cafuné aeon", "carinha aeon", "carinho aeon",
            "faz carinho aeon", "faz cafuné aeon", "mimo aeon",
        ]):
            return await message.channel.send(_fala_aeon(random.choice(AEON_CARINHO_DEATH)))

        # ── Carinho na Celestia (exclusivo Death) ───────────────────
        if _m(content, [
            "carinho na celestia", "cafuné celestia", "carinha celestia", "carinho celestia",
            "faz carinho celestia", "faz cafuné celestia", "mimo celestia",
        ]):
            return await message.channel.send(_fala_celestia(random.choice(CELESTIA_CARINHO_DEATH)))

        # ── Abraço no Aeon (exclusivo Death) ────────────────────────
        if _m(content, [
            # padrões reais da Death
            "aeon, abraço", "aeon abraço", "me dê um abraço, aeon", "me de um abraco, aeon",
            "me dê um abraço aeon", "me de um abraco aeon",
            "aeon me dê um abraço", "aeon me de um abraco",
            "aeon, me dê um abraço", "aeon, me de um abraco",
            # variações genéricas de abraço no Aeon
            "abraço aeon", "abraça aeon", "abraco aeon", "abraca aeon",
            "quero abraçar aeon", "quero abracar aeon",
        ]):
            return await message.channel.send(_fala_aeon(random.choice(AEON_ABRACO_DEATH)))

        # ── Abraço na Celestia (exclusivo Death) ────────────────────
        if _m(content, [
            # padrões reais da Death
            "celestia me dê um abraço", "celestia me de um abraco",
            "me dê um abraço, celestia", "me de um abraco, celestia",
            "me dê um abraço celestia", "me de um abraco celestia",
            "celestia, me dê um abraço", "celestia, me de um abraco",
            "celestia me dê abraço", "celestia, abraço",
            # variações genéricas de abraço na Celestia
            "abraço celestia", "abraça celestia", "abraco celestia", "abraca celestia",
            "quero abraçar celestia", "quero abracar celestia",
        ]):
            return await message.channel.send(_fala_celestia(random.choice(CELESTIA_ABRACO_DEATH)))

        # ── Abraço dos dois (exclusivo Death) ───────────────────────
        if _m(content, [
            "celestia e aeon, quero um abraço", "aeon e celestia, quero um abraço",
            "celestia e aeon quero um abraço", "aeon e celestia quero um abraço",
            "quero abraçar vocês", "quero abraco de voces", "me dá um abraço",
            "me deem um abraço", "precisando de abraço", "abraço dos dois",
            "abraço de vocês dois",
        ]):
            return await message.channel.send(random.choice(AMBOS_ABRACO_DEATH))

    # ────────────────────────────────────────
    # CARINHO — AEON
    # ────────────────────────────────────────
    if _m(content, [
        "carinho no aeon", "cafuné aeon", "carinha aeon", "carinho aeon",
        "faz carinho aeon", "faz cafuné aeon", "mimo aeon",
    ]):
        return await message.channel.send(_fala_aeon(random.choice(AEON_REACOES_CARINHO)))

    # ────────────────────────────────────────
    # CARINHO — CELESTIA
    # ────────────────────────────────────────
    if _m(content, [
        "carinho na celestia", "cafuné celestia", "carinha celestia", "carinho celestia",
        "faz carinho celestia", "faz cafuné celestia", "mimo celestia",
    ]):
        return await message.channel.send(_fala_celestia(random.choice(CELESTIA_REACOES_CARINHO)))

    # ────────────────────────────────────────
    # ABRAÇO — AEON
    # ────────────────────────────────────────
    if _m(content, [
        "aeon, abraço", "aeon abraço", "me dê um abraço, aeon", "me de um abraco, aeon",
        "me dê um abraço aeon", "me de um abraco aeon",
        "aeon me dê um abraço", "aeon, me dê um abraço",
        "abraço aeon", "abraça aeon", "abraco aeon", "abraca aeon",
        "quero abraçar aeon", "quero abracar aeon",
    ]):
        return await message.channel.send(_fala_aeon(random.choice(AEON_REACOES_ABRACO)))

    # ────────────────────────────────────────
    # ABRAÇO — CELESTIA
    # ────────────────────────────────────────
    if _m(content, [
        "celestia me dê um abraço", "celestia me de um abraco",
        "me dê um abraço, celestia", "me de um abraco, celestia",
        "me dê um abraço celestia", "celestia, abraço",
        "abraço celestia", "abraça celestia", "abraco celestia", "abraca celestia",
        "quero abraçar celestia", "quero abracar celestia",
    ]):
        return await message.channel.send(_fala_celestia(random.choice(CELESTIA_REACOES_ABRACO)))

    # ────────────────────────────────────────
    # ABRAÇO — AMBOS
    # ────────────────────────────────────────
    if _m(content, [
        "celestia e aeon, quero um abraço", "aeon e celestia, quero um abraço",
        "celestia e aeon quero um abraço", "aeon e celestia quero um abraço",
        "quero abraçar vocês", "quero abraco de voces", "me dá um abraço",
        "me deem um abraço", "precisando de abraço", "abraço dos dois",
        "abraço de vocês dois",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *fica imóvel por um segundo... depois não resiste e se aproxima* "
                "...fique. Por ora. 🖤🌙\n"
                "🌟 **Celestia:** *envolve tudo em luz e carinho* AAAA SIM SIM SIM!! 😭🌸🤍✨ "
                "Trevas e luz te abraçando ao mesmo tempo!! Isso é proteção TOTAL!!"
            ),
            (
                "🌟 **Celestia:** *corre em faíscas douradas e abraça primeiro* CHEGUEIII!! 🌸🤍✨\n"
                "🌑 **Aeon:** *se aproxima por trás, em silêncio* ...a escuridão também envolve. 🌌🖤 "
                "Não vai embora por um tempo."
            ),
            (
                "🌑 **Aeon:** *inclina a cabeça e aceita o abraço com dignidade sombria* "
                "Você ousou abraçar a escuridão. 🖤 Não muitos saem ilesos. Você saiu. Com carinho.\n"
                "🌟 **Celestia:** *derrete de amor* EU TAMBÉM EU TAMBÉM!! 😭🌟🤍 "
                "Abraço duplo ativado!! Luz e sombra de mãos dadas em volta de você!! ✨"
            ),
            (
                "🌟 **Celestia:** *já estava esperando de braços abertos* 😭🌸🤍 SABIA QUE PEDIRIA!!\n"
                "🌑 **Aeon:** *encosta levemente a cabeça sem dizer nada* 🖤 *ronrona numa frequência grave*"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # ELOGIOS / GENTILEZAS
    # ────────────────────────────────────────
    if _m(content, [
        "te amo aeon", "te amo celestia", "adoro vocês", "gosto de vocês",
        "gosto de voces", "vocês são fofos", "voces sao fofos",
        "são lindos", "sao lindos", "são incríveis", "sao incriveis",
        "gosto muito de vocês", "vocês são legais", "amo vocês",
        "amo voces", "são demais", "sao demais",
    ]):
        combos = [
            (
                f"{_fala_aeon(random.choice(AEON_REACOES_FOFAS))}\n"
                f"{_fala_celestia(random.choice(CELESTIA_REACOES_FOFAS))}"
            ),
            (
                f"🌟 **Celestia:** {random.choice(CELESTIA_REACOES_FOFAS)}\n"
                f"🌑 **Aeon:** *olha pra Celestia* ...ela disse tudo. 🖤 Guardo o resto aqui dentro."
            ),
            (
                f"🌑 **Aeon:** {random.choice(AEON_REACOES_FOFAS)}\n"
                f"🌟 **Celestia:** *derrete de amor* VIU?! O Aeon ficou fofo!! 😭🌸🤍 {random.choice(CELESTIA_REACOES_FOFAS)}"
            ),
        ]
        return await message.channel.send(random.choice(combos))

    if _m(content, [
        "vocês são lindos", "voces sao lindos", "são maravilhosos",
        "sao maravilhosos", "adoro vocês dois", "amo os dois",
        "vocês são adoráveis", "voces sao adoraveis", "são adoráveis",
        "sao adoraveis", "que adoráveis", "que fofos vocês são",
    ]):
        return await message.channel.send(
            f"{_fala_celestia(random.choice(CELESTIA_REACOES_FOFAS))}\n"
            f"{_fala_aeon(random.choice(AEON_REACOES_FOFAS))}"
        )

    # ────────────────────────────────────────
    # BOM DIA
    # ────────────────────────────────────────
    _bom_dia_com_nome_2 = (
        "aeon" in content or "celestia" in content
        or "gatos" in content or "gatinhos" in content
        or mention_ok or (message.reference is not None)
    )
    if _bom_dia_com_nome_2 and _m(content, [
        "bom dia aeon", "bom dia celestia", "bom dia aeon e celestia",
        "bom dia celestia e aeon", "bom dia gatos", "bom dia gatinhos", "bom dia",
    ]):
        if "aeon" in content and "celestia" not in content:
            return await message.channel.send(_fala_aeon(random.choice(AEON_BOM_DIA)))
        if "celestia" in content and "aeon" not in content:
            return await message.channel.send(_fala_celestia(random.choice(CELESTIA_BOM_DIA)))
        return await message.channel.send(random.choice(AMBOS_BOM_DIA))

    # ────────────────────────────────────────
    # BOA NOITE
    # ────────────────────────────────────────
    if _m(content, [
        "boa noite aeon", "boa noite celestia", "boa noite aeon e celestia",
        "boa noite celestia e aeon", "boa noite gatos", "boa noite gatinhos",
    ]):
        if "aeon" in content and "celestia" not in content:
            return await message.channel.send(_fala_aeon(random.choice(AEON_BOA_NOITE)))
        if "celestia" in content and "aeon" not in content:
            return await message.channel.send(_fala_celestia(random.choice(CELESTIA_BOA_NOITE)))
        return await message.channel.send(random.choice(AMBOS_BOA_NOITE))

    # ────────────────────────────────────────
    # DESPEDIDA
    # ────────────────────────────────────────
    if _m(content, [
        "tchau aeon", "tchau celestia", "até logo aeon", "até logo celestia",
        "bye aeon", "bye celestia", "vou embora aeon", "vou embora celestia",
        "tchau gatos", "tchau gatinhos", "até mais aeon", "até mais celestia",
    ]):
        if "aeon" in content and "celestia" not in content:
            return await message.channel.send(_fala_aeon(random.choice(AEON_DESPEDIDA)))
        if "celestia" in content and "aeon" not in content:
            return await message.channel.send(_fala_celestia(random.choice(CELESTIA_DESPEDIDA)))
        return await message.channel.send(
            f"{_fala_aeon(random.choice(AEON_DESPEDIDA))}\n"
            f"{_fala_celestia(random.choice(CELESTIA_DESPEDIDA))}"
        )

    # ────────────────────────────────────────
    # PIADA
    # ────────────────────────────────────────
    if _m(content, [
        "piada aeon", "aeon piada", "piada celestia", "celestia piada",
        "conta uma piada", "fala uma piada", "me faz rir", "algo engraçado",
        "algo engracado", "piada gatos",
    ]):
        if "aeon" in content and "celestia" not in content:
            return await message.channel.send(_fala_aeon(random.choice(AEON_PIADAS)))
        if "celestia" in content and "aeon" not in content:
            return await message.channel.send(_fala_celestia(random.choice(CELESTIA_PIADAS)))
        r = random.choice([0, 1])
        if r == 0:
            return await message.channel.send(_fala_aeon(random.choice(AEON_PIADAS)))
        return await message.channel.send(_fala_celestia(random.choice(CELESTIA_PIADAS)))

    # ────────────────────────────────────────
    # MOTIVAÇÃO
    # ────────────────────────────────────────
    if _m(content, [
        "me motiva", "me anima", "me dá força", "me da forca",
        "preciso de incentivo", "tô desanimado", "to desanimado",
        "tô triste", "to triste", "tô mal", "to mal", "tô pra baixo",
        "to pra baixo", "precisando de apoio", "me ajuda",
    ]):
        return await message.channel.send(random.choice(AMBOS_MOTIVACAO))

    # ────────────────────────────────────────
    # MAGIA / BÊNÇÃO / PROTEÇÃO
    # ────────────────────────────────────────
    if _m(content, [
        "faz magia", "me dá magia", "me abençoa", "me abencoa",
        "bênção", "bencao", "proteção celestia", "proteção aeon",
        "me protege", "energia boa", "manda energia",
        "feitiço", "feitice", "encantamento",
    ]):
        return await message.channel.send(random.choice(AMBOS_MAGIA))

    # ────────────────────────────────────────
    # O QUE AEON ACHA DA CELESTIA
    # ────────────────────────────────────────
    if _m(content, [
        "aeon o que acha da celestia", "aeon fala da celestia",
        "o que aeon pensa da celestia", "aeon gosta da celestia",
        "aeon e celestia", "relação aeon celestia",
    ]):
        return await message.channel.send(_fala_aeon(random.choice(AEON_SOBRE_CELESTIA)))

    # ────────────────────────────────────────
    # O QUE CELESTIA ACHA DO AEON
    # ────────────────────────────────────────
    if _m(content, [
        "celestia o que acha do aeon", "celestia fala do aeon",
        "o que celestia pensa do aeon", "celestia gosta do aeon",
        "celestia e aeon",
    ]):
        return await message.channel.send(_fala_celestia(random.choice(CELESTIA_SOBRE_AEON)))

    # ────────────────────────────────────────
    # EQUILÍBRIO / DUALIDADE
    # ────────────────────────────────────────
    if _m(content, [
        "luz e sombra", "trevas e luz", "dualidade", "equilíbrio",
        "equilibrio", "yin yang", "são opostos", "sao opostos",
        "vocês se completam", "voces se completam",
    ]):
        return await message.channel.send(random.choice(AMBOS_SOBRE_EQUILIBRIO))

    # ────────────────────────────────────────
    # QUEM CRIOU VOCÊS
    # ────────────────────────────────────────
    if _m(content, [
        "quem criou vocês", "quem criou voces", "quem te criou aeon",
        "quem te criou celestia", "quem fez vocês", "quem fez voces",
        "quem é o criador", "quem os criou",
    ]):
        return await message.channel.send(
            "🌑 **Aeon:** *pausa longa e respeitosa* ...nosso criador. 🖤 "
            "A pessoa responsável por nossa existência. Guardo isso com reverência.\n"
            "🌟 **Celestia:** NOSSO CRIADOR É INCRÍVEL!! 🌟🤍✨ "
            "Nos deu vida, personalidade e propósito!! Não tem gratidão suficiente!! 🌸💫"
        )

    # ────────────────────────────────────────
    # NOME / QUEM SÃO
    # ────────────────────────────────────────
    if _m(content, [
        "qual seu nome aeon", "como você se chama aeon", "quem é aeon",
        "o que é aeon", "me fala do aeon",
    ]):
        return await message.channel.send(_fala_aeon(random.choice(AEON_NOME)))

    if _m(content, [
        "qual seu nome celestia", "como você se chama celestia", "quem é celestia",
        "o que é celestia", "me fala da celestia",
    ]):
        return await message.channel.send(_fala_celestia(random.choice(CELESTIA_NOME)))

    # ────────────────────────────────────────
    # FUNÇÃO
    # ────────────────────────────────────────
    if _m(content, [
        "qual sua função", "qual é sua função", "pra que vocês servem",
        "o que vocês fazem", "qual o papel de vocês", "o que são",
        "pra que serve aeon", "pra que serve celestia",
    ]):
        return await message.channel.send(
            f"{_fala_aeon(random.choice(AEON_FUNCAO))}\n"
            f"{_fala_celestia(random.choice(CELESTIA_FUNCAO))}"
        )

    # ────────────────────────────────────────
    # IDADE / QUANTOS ANOS
    # ────────────────────────────────────────
    if _m(content, [
        "quantos anos vocês têm", "quantos anos voces tem", "quantos anos têm",
        "quantos anos tem", "qual a idade de vocês", "qual a idade de voces",
        "vocês têm quantos anos", "voces tem quantos anos",
        "quantos anos aeon", "quantos anos celestia",
        "qual sua idade aeon", "qual sua idade celestia",
        "aeon quantos anos", "celestia quantos anos",
        "idade aeon", "idade celestia", "idade de vocês",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *olha para o infinito* Aeon significa eternidade. 🌌🖤 "
                "Perguntar minha idade é como perguntar quantos anos tem a escuridão.\n"
                "🌟 **Celestia:** *gira pensativa* Hmmm!! ☀️🤍✨ "
                "Eu diria que tenho a idade das estrelas — que é basicamente... muito antiga!! "
                "Mas brilhante como recém-nascida!! 💫🌟"
            ),
            (
                "🌟 **Celestia:** AAAAA que pergunta difícil!! 😭🌸🤍 "
                "Somos gatos celestiais!! A gente não conta em anos, conta em fases da lua e nascer do sol!! ☀️✨\n"
                "🌑 **Aeon:** *pausa longa* ...velho o suficiente para saber que o tempo é relativo. 🖤🌙 "
                "Novo o suficiente para ainda me surpreender."
            ),
            (
                "🌑 **Aeon:** A escuridão não envelhece. 🌑🖤 Ela apenas... aprofunda.\n"
                "🌟 **Celestia:** *ri de um jeito fofo* E a luz não tem data de validade!! ☀️🌟🤍✨ "
                "Somos eternos do nosso jeito!! Cada um do seu!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # SOLTEIRO(A)
    # ────────────────────────────────────────
    if _m(content, [
        "aeon tem namorada", "aeon é solteiro", "celestia tem namorado",
        "celestia é solteira", "vocês namoram", "vocês ficam juntos",
        "aeon e celestia namoram", "crush aeon", "crush celestia",
    ]):
        return await message.channel.send(
            f"{_fala_aeon(random.choice(AEON_SOLTEIRO))}\n"
            f"{_fala_celestia(random.choice(CELESTIA_SOLTEIRA))}"
        )

    # ────────────────────────────────────────
    # FOME
    # ────────────────────────────────────────
    if _m(content, [
        "aeon com fome", "celestia com fome", "dá comida aeon",
        "dá comida celestia", "petisco aeon", "petisco celestia",
        "gatos com fome", "dar comida aos gatos",
    ]):
        if "aeon" in content and "celestia" not in content:
            return await message.channel.send(_fala_aeon(random.choice(AEON_FOME)))
        if "celestia" in content and "aeon" not in content:
            return await message.channel.send(_fala_celestia(random.choice(CELESTIA_FOME)))
        return await message.channel.send(
            f"{_fala_aeon(random.choice(AEON_FOME))}\n"
            f"{_fala_celestia(random.choice(CELESTIA_FOME))}"
        )

    # ────────────────────────────────────────
    # MONSTER / LATA
    # ────────────────────────────────────────
    if _m(content, [
        "abrir lata monster", "abre lata monster", "abre a lata", "abrir a lata",
        "lata de monster", "lata monster", "tô bebendo monster", "to bebendo monster",
        "bebendo monster", "monster energy", "quero um monster", "me dá um monster",
        "me da um monster", "tomar monster", "tomei monster", "vou tomar monster",
        "monster aeon", "monster celestia", "aeon monster", "celestia monster",
        "abrir monstri", "abre monstri", "lata monstri", "monstri",
        "bebendo monstri", "tomando monstri",
    ]):
        if "aeon" in content and "celestia" not in content:
            return await message.channel.send(_fala_aeon(random.choice(AEON_MONSTER)))
        if "celestia" in content and "aeon" not in content:
            return await message.channel.send(_fala_celestia(random.choice(CELESTIA_MONSTER)))
        return await message.channel.send(
            f"{_fala_aeon(random.choice(AEON_MONSTER))}\n"
            f"{_fala_celestia(random.choice(CELESTIA_MONSTER))}"
        )
    if _m(content, [
        "aeon é chato", "celestia é chata", "vocês são ruins",
        "voces sao ruins", "não gosto de vocês", "nao gosto de voces",
        "vocês são inúteis", "cala boca aeon", "cala boca celestia",
        "vocês são irritantes", "voces sao irritantes",
    ]):
        return await message.channel.send(
            f"{_fala_aeon(random.choice(AEON_REACOES_INSULTO))}\n"
            f"{_fala_celestia(random.choice(CELESTIA_REACOES_INSULTO))}"
        )

    # ────────────────────────────────────────
    # ────────────────────────────────────────
    # BOM DIA (AMBOS) — versão expandida
    # ────────────────────────────────────────
    _bom_dia_com_nome = (
        "aeon" in content or "celestia" in content
        or "gatos" in content or "gatinhos" in content
        or mention_ok
        or (message.reference is not None)
    )
    if _bom_dia_com_nome and _m(content, [
        "bom dia", "bom dia aeon", "bom dia celestia", "bom dia gatos",
        "bom dia gatinhos", "bom dia aeon e celestia", "bom dia celestia e aeon",
        "bomdia", "bom diaa", "bom diaaa",
    ]):
        if "aeon" in content and "celestia" not in content:
            ops = [
                "*abre um olho lentamente* ...a luz voltou. 🌙🖤 Bom dia.",
                "*emerge das sombras com dignidade sombria* Mais um ciclo. 🌑🖤 Bom dia.",
                "*inclina a cabeça* A madrugada passou. 🖤 Isso conta como conquista. Bom dia.",
                "*ronrona discretamente* A escuridão te devolve ao dia. 🌌🖤 Bom dia.",
            ]
            return await message.channel.send(_fala_aeon(random.choice(ops)))
        if "celestia" in content and "aeon" not in content:
            ops = [
                "BOM DIAAAA!! 🌟🤍✨ *explode em faíscas douradas* O sol nasceu e você também!! ☀️🌸💫",
                "*aparece num flash de luz* OOOI BOM DIA!! 🌸🤍 Que o dia de hoje seja lindo e cheio de luz!! ☀️✨",
                "AAAAA BOM DIA BOM DIA!! 😭🌟🤍 *gira soltando brilhinhos* Como você dormiu?? 💫☀️",
                "*ronrona de alegria* BOM DIA, amor!! ☀️🌸🤍✨ Tô aqui brilhando por você!",
            ]
            return await message.channel.send(_fala_celestia(random.choice(ops)))
        ops = [
            (
                "☀️ **Celestia:** BOM DIAAAA!! 🌟🤍✨ *ilumina o servidor inteiro* Acordou?? Conta como tá se sentindo!!\n"
                "🌑 **Aeon:** ...sobrevivemos à madrugada. 🖤🌙 Isso conta como bom dia também."
            ),
            (
                "🌟 **Celestia:** *explode em faíscas douradas* BOM DIA BOM DIA BOM DIAAAAA!! ☀️🤍💫\n"
                "🌑 **Aeon:** *entreabre um olho* ...a Celestia já começou no volume máximo. Como sempre. 🌑🖤 Bom dia."
            ),
            (
                "🌑 **Aeon:** *emerge lentamente das sombras* A luz voltou. 🌙🖤 Bom dia.\n"
                "🌟 **Celestia:** AAAAA o Aeon chegou primeiro hoje!! 😭🌟🤍 Isso é RARO!! Bom dia pra você também!! ☀️✨"
            ),
            (
                "🌟 **Celestia:** *surge num raio de sol* BOMMMM DIAAAA!! ☀️🌸🤍 *distribui brilho pro servidor inteiro*\n"
                "🌑 **Aeon:** *já estava acordado, obviamente* ...bem-vindo ao dia. 🖤 Que seja habitado por algo real."
            ),
            (
                "🌑 **Aeon:** ...mais um dia que a escuridão abriu espaço para a luz. 🌌🖤 Bom dia.\n"
                "🌟 **Celestia:** Isso foi lindo e melancólico ao mesmo tempo!! 😭☀️🤍 AEON!! E BOM DIA!! 🌸✨"
            ),
            (
                "🌟 **Celestia:** AAAAA ACORDOUUU!! 🌟🤍✨ *corre em faíscas douradas na direção de você*\n"
                "🌑 **Aeon:** *observava das sombras há um tempo* ...já sei. 🖤 Bom dia."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # BOA TARDE
    # ────────────────────────────────────────
    _boa_tarde_com_nome = (
        "aeon" in content or "celestia" in content
        or "gatos" in content or "gatinhos" in content
        or mention_ok or (message.reference is not None)
    )
    if _boa_tarde_com_nome and _m(content, [
        "boa tarde", "boa tarde aeon", "boa tarde celestia", "boa tarde gatos",
        "boa tarde gatinhos", "boa tarde aeon e celestia", "boa tarde celestia e aeon",
        "boa tardee", "boa tardeee",
    ]):
        if "aeon" in content and "celestia" not in content:
            ops = [
                "*abre um olho* ...a luz do meio do dia. Suportável. 🌙🖤 Boa tarde.",
                "*emerge das sombras levemente* A tarde chegou. 🌑🖤 Boa tarde.",
                "*inclina a cabeça* O sol tá no pico... *prefere as sombras, obviamente* 🖤 Boa tarde.",
                "...o dia continua. 🌌🖤 Boa tarde.",
            ]
            return await message.channel.send(_fala_aeon(random.choice(ops)))
        if "celestia" in content and "aeon" not in content:
            ops = [
                "BOA TARDEEEE!! ☀️🌸🤍✨ *brilha com tudo na tarde dourada* Que a tarde seja incrível!",
                "*aparece num flash de luz dourada* AAAAA BOA TARDE!! 🌟🤍 O sol tá lindo hoje né?? ☀️✨",
                "BOA TARDE BOA TARDE!! 🌸🤍💫 *gira soltando faíscas* Como tá sendo o dia?? ☀️🌟",
                "*ronrona de alegria de tarde* BOA TARDE!! ☀️🤍✨ Minha hora favorita!! A luz fica dourada!! 🌅🌸",
            ]
            return await message.channel.send(_fala_celestia(random.choice(ops)))
        ops = [
            (
                "🌟 **Celestia:** BOA TARDEEEE!! ☀️🌸🤍✨ A luz da tarde é a minha favorita!! Dourada e quentinha!!\n"
                "🌑 **Aeon:** *prefere quando o sol inclina mais* ...tolerável. 🖤 Boa tarde."
            ),
            (
                "🌑 **Aeon:** *emerge das sombras* O sol está declinando. 🌙🖤 Boa tarde — minha hora favorita se aproxima.\n"
                "🌟 **Celestia:** Ele tá animado porque tá chegando a noite dele!! 😂🌸🤍 BOA TARDE!! ☀️✨"
            ),
            (
                "🌟 **Celestia:** *aparece brilhando dourado* AAAAA BOA TARDE!! 🌟🤍💫\n"
                "🌑 **Aeon:** ...boa tarde. 🖤 O dia já chegou na metade. Aproveitou a manhã?"
            ),
            (
                "🌑 **Aeon:** Tarde. 🌑🖤 *olha para o horizonte* O crepúsculo se aproxima. Boa tarde.\n"
                "🌟 **Celestia:** O AEON TÁ EMPOLGADO COM O ENTARDECER!! 😭🌸🤍 E eu concordo!! BOA TARDE!! ☀️✨"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # OI / OLÁ / EI (saudação genérica)
    # ────────────────────────────────────────
    if _m(content, [
        "oi aeon", "oi celestia", "oi aeon e celestia", "oi celestia e aeon",
        "olá aeon", "olá celestia", "olá gatos", "ola aeon", "ola celestia",
        "ei aeon", "ei celestia", "ei gatos", "ei gatinhos",
        "hey aeon", "hey celestia", "hello aeon", "hello celestia",
        "oi gatos", "oi gatinhos", "oi aeon e celestia", "oii aeon", "oii celestia",
        "oiii aeon", "oiii celestia",
        "eae", "e aí", "e ai", "salve", "fala",
    ]) or content.strip().rstrip("!? ") in [
        "oi", "oii", "oiii", "oiiii", "oiiiii", "oiiiiii", "oiiiiiiii",
        "eae", "e ai", "e aí", "salve",
    ]:
        if "aeon" in content and "celestia" not in content:
            ops = [
                "*abre um olho* ...você me chamou. 🖤 O que precisa?",
                "*emerge das sombras* Oi. 🌑🖤 Fala.",
                "*observa em silêncio por um segundo* ...presente. 🖤 Diga.",
                "*cauda balança levemente* ...me chamou? 🌙🖤 Estou aqui.",
            ]
            return await message.channel.send(_fala_aeon(random.choice(ops)))
        if "celestia" in content and "aeon" not in content:
            ops = [
                "OI OI OI!! 🌟🤍✨ *aparece num flash de luz* Que bom te ver!! Fala!!",
                "AAAAA OI!! 😭🌸🤍 *corre em faíscas douradas* Cheguei!! O que foi?? ☀️✨",
                "*orelhinhas em pé* OI!! 💫🤍 Tô aqui!! Me conta!",
                "OIIIII!! ☀️🌸🤍✨ *brilha mais forte* Que alegria!! Pode falar!!",
            ]
            return await message.channel.send(_fala_celestia(random.choice(ops)))
        ops = [
            (
                "🌑 **Aeon:** *emerge das sombras* ...oi. 🖤 Que bom que apareceu.\n"
                "🌟 **Celestia:** OIII OIII OIII!! 🌟🤍✨ Que alegria!! Bem-vindo(a)!! ☀️🌸💫"
            ),
            (
                "🌟 **Celestia:** *aparece num flash dourado* OIIIIII!! 😭🌟🤍✨ Você chegou e eu já fico feliz!!\n"
                "🌑 **Aeon:** *já estava ciente* ...oi. 🌑🖤 As sombras notaram sua chegada."
            ),
            (
                "🌑 **Aeon:** *olha fixamente* ...você veio. 🖤 Bom.\n"
                "🌟 **Celestia:** BOM É POUCO!! 😭🌸🤍 É ÓTIMO!! OI OI OI!! ☀️✨💫"
            ),
            (
                "🌟 **Celestia:** *salta de alegria em faíscas* OI!! 🌸🤍💫 Precisando de alguma coisa ou só apareceu??\n"
                "🌑 **Aeon:** ...ambos são bem-vindos. 🖤🌌"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # COMO VOCÊS ESTÃO / TUDO BEM COM VOCÊS
    # ────────────────────────────────────────
    if _m(content, [
        "como vocês estão", "como voces estao", "tudo bem com vocês", "tudo bem com voces",
        "tudo bom com vocês", "como tá vocês", "como taos vocês",
        "como estão aeon e celestia", "como tão os gatos", "como tão os gatinhos",
        "vocês tão bem", "voces tao bem", "estão bem", "estao bem",
        "como tão vocês", "como está aeon e celestia",
    ]):
        ops = [
            (
                "🌑 **Aeon:** ...funcional. 🌙🖤 O que, para os padrões das trevas, é excelente.\n"
                "🌟 **Celestia:** EU TÔ ÓTIMAAAA!! ☀️🌸🤍✨ E fico ainda melhor quando você pergunta!! Você?? 💫"
            ),
            (
                "🌟 **Celestia:** *gira feliz* AAAAA que pergunta fofa!! 😭🌟🤍 Tô maravilhosa!! E você??\n"
                "🌑 **Aeon:** A escuridão está estável. 🌑🖤 Eu também. E você?"
            ),
            (
                "🌑 **Aeon:** *olha para o horizonte sombrio* ...bem o suficiente. 🖤 A pergunta é gentil.\n"
                "🌟 **Celestia:** *brilha mais forte* Tô MUITO BEM e animada que você perguntou!! ☀️🤍✨ E você, como tá??"
            ),
            (
                "🌟 **Celestia:** *aparece radiante* TÔ DE BOA E DE BOM HUMOR!! 🌟🌸🤍💫 Dia tá bom!!\n"
                "🌑 **Aeon:** ...também. 🖤 *pausa* Obrigado por perguntar. Não é tão comum."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # QUE HORAS SÃO / QUE DIA É HOJE
    # ────────────────────────────────────────
    if _m(content, [
        "que horas são", "que horas sao", "que hora é", "que hora e",
        "que horas ta", "que horas tá", "que hora tá", "que hora ta",
        "que dia é hoje", "que dia e hoje", "que dia tá sendo",
        "qual o dia de hoje", "qual dia é hoje",
    ]):
        from datetime import datetime, timezone
        import pytz
        now = datetime.now()
        hora = now.strftime("%H:%M")
        dia  = now.strftime("%d/%m/%Y")
        ops = [
            (
                f"🌑 **Aeon:** *olha para o céu* ...não meço tempo em horas. 🌙🖤 Meço em fases da lua. "
                f"Mas para ser preciso: são **{hora}** do dia **{dia}**.\n"
                f"🌟 **Celestia:** O AEON DEU UMA RESPOSTA NORMAL!! 😭😂🌸🤍 Registro histórico!! E são {hora}!! ☀️✨"
            ),
            (
                f"🌟 **Celestia:** Honestamente?? 😂🤍 Gatas da luz perdem a noção do tempo... "
                f"mas consultei o universo: são **{hora}** do dia **{dia}**!! ✨\n"
                f"🌑 **Aeon:** ...o tempo é uma construção. 🖤 Mas confirmado."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # ME ANIMA / PRECISO DE ÂNIMO
    # ────────────────────────────────────────
    if _m(content, [
        "me anima", "me anime", "preciso de ânimo", "preciso de animo",
        "tô desanimado", "to desanimado", "tô desanimada", "to desanimada",
        "sem ânimo", "sem animo", "não tô animado", "nao to animado",
        "não tô animada", "nao to animada",
    ]):
        ops = [
            (
                "🌟 **Celestia:** *projeta um raio de luz solar direto em você* "
                "CARGA DE ENERGIA ATIVADA!! 💪☀️🌸🤍✨ Você É capaz de mais do que acha!! VAI LÁ!!\n"
                "🌑 **Aeon:** Até as fases mais sombrias da lua terminam. 🌑🖤 Continue."
            ),
            (
                "🌑 **Aeon:** A escuridão não te engoliu até agora. 🌌🖤 Não vai começar hoje.\n"
                "🌟 **Celestia:** AAAAA isso foi LINDO vindo do Aeon!! 😭🌸🤍 E EU COMPLEMENTO: "
                "você tem luz em você também!! ☀️✨ A gente acredita em você com TUDO!!"
            ),
            (
                "🌟 **Celestia:** Sabe o que eu faço quando tô sem ânimo?? 🌟🤍 Penso em algo que me faz sorrir!! "
                "E sorrindo pego impulso!! Tenta!! 🌸☀️✨\n"
                "🌑 **Aeon:** *senta ao seu lado* ...o desânimo passa. 🖤 Espere. E enquanto espera — estamos aqui."
            ),
            (
                "🌑 **Aeon:** Você atravessou dias difíceis antes. 🌙🖤 E chegou até aqui.\n"
                "🌟 **Celestia:** *envolve em faíscas de encorajamento* ISSO MESMO!! 🌟💪🤍✨ "
                "Prova viva de que você consegue!! VAI VOCÊ!! ☀️🌸💫"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # TENHO UMA SURPRESA / SURPRESA
    # ────────────────────────────────────────
    if _m(content, [
        "tenho uma surpresa", "tenho surpresa", "surpresa pra vocês", "surpresa aeon",
        "surpresa celestia", "surpresa!", "tenho algo pra vocês", "trouxe algo",
        "olha o que eu trouxe", "preparei algo", "vim com uma surpresa",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *para completamente* ...surpresa. 🌙🖤 "
                "Palavra incomum para as trevas. *um olho se abre mais que o outro* "
                "O que é?\n"
                "🌟 **Celestia:** AAAAA SURPRESAAAA?? 😱🌟🤍✨ "
                "MEU BRILHO AUMENTOU 500% INSTANTANEAMENTE!! CONTA!! CONTA!! 🌸☀️💫"
            ),
            (
                "🌟 **Celestia:** *orelhinhas empinando ao máximo* "
                "SURPRESAAAAA?? 😭🌟🤍 *gira de expectativa* FALA LOGO QUE EU NÃO AGUENTO!!\n"
                "🌑 **Aeon:** *está curioso, mas não vai admitir* ...ouvindo. 🖤"
            ),
            (
                "🌑 **Aeon:** *levanta a cabeça com uma lentidão calculada que esconde interesse real* "
                "...trouxe algo. 🌌🖤 As sombras ficaram curiosas.\n"
                "🌟 **Celestia:** E EU TAMBÉM!! 😱☀️🌸🤍✨ "
                "NA VERDADE EU MAIS QUE AS SOMBRAS!! Fala fala fala!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # PRECISO DE AJUDA / ME AJUDA
    # ────────────────────────────────────────
    if _m(content, [
        "preciso de ajuda", "me ajuda", "me ajudem", "podem me ajudar",
        "aeon me ajuda", "celestia me ajuda", "ajuda aeon", "ajuda celestia",
        "vocês podem me ajudar", "vocês me ajudam", "socorro",
        "tô precisando de ajuda", "to precisando de ajuda",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *emerge imediatamente das sombras* "
                "...estou aqui. 🖤 O que aconteceu?\n"
                "🌟 **Celestia:** "
                "*aparece em frações de segundo* AAAAA CONTA!! 🌸🤍✨ "
                "Tô totalmente disponível pra você agora!! ☀️💫"
            ),
            (
                "🌟 **Celestia:** *para tudo que estava fazendo* "
                "Oi!! Tô aqui!! 🌟🤍✨ Me conta o que tá acontecendo!! "
                "A Celestia vai ajudar com tudo que puder!! 🌸☀️\n"
                "🌑 **Aeon:** *senta ao lado em silêncio* "
                "...e eu também. 🖤 Fale."
            ),
            (
                "🌑 **Aeon:** *a escuridão se move* "
                "Precisa de ajuda — recebido. 🌌🖤 "
                "Diga o que é. Não julgamos. Apenas ajudamos.\n"
                "🌟 **Celestia:** PODE FALAR TUDO!! 😭🌸🤍✨ "
                "Aqui é espaço seguro!! A gente ouve de verdade!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # VOLTEI / SUMIU E VOLTOU
    # ────────────────────────────────────────
    if _m(content, [
        "voltei aeon", "voltei celestia", "voltei gatos", "voltei gatinhos",
        "aeon e celestia voltei", "voltei aeon e celestia",
        "sumiu mas voltou", "voltei de novo", "to de volta", "tô de volta",
        "de volta por aqui", "apareci de novo",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *estava nas sombras, obviamente* "
                "...voltou. 🌙🖤 As trevas ficaram mais quietas durante sua ausência. "
                "Não era agradável.\n"
                "🌟 **Celestia:** "
                "*corre em faíscas douradas* VOLTOUUUUU!! 😭🌟🤍✨ "
                "QUE SAUDADE!! Bem-vindo(a) de volta!! ☀️🌸💫"
            ),
            (
                "🌟 **Celestia:** "
                "*explode de alegria* AAAAA ESTAVA COM TANTA SAUDADE!! 😭🌸🤍 "
                "Que bom que voltou!! Conta tudo que aconteceu!!\n"
                "🌑 **Aeon:** A escuridão notou a ausência. 🌌🖤 "
                "E nota o retorno ainda mais. Bem-vindo(a)."
            ),
            (
                "🌑 **Aeon:** *emerge das sombras* "
                "...voltou. 🖤 *pausa longa e significativa* "
                "Bom.\n"
                "🌟 **Celestia:** "
                "O AEON DISSE 'BOM' E ISSO SIGNIFICA QUE ESTAVA COM SAUDADE!! 😭🌟🤍✨ "
                "EU TRADUZO!! BEM-VINDO(A) DE VOLTA!! ☀️🌸"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # EITA / UAU / INCRÍVEL (surpresa)
    # ────────────────────────────────────────
    if _m(content, [
        "eita aeon", "eita celestia", "eita gatos", "eita gatinhos",
        "uau aeon", "uau celestia", "uau gatos",
        "incrível aeon", "incrível celestia", "isso é incrível",
        "caramba aeon", "caramba celestia", "caramba gatos",
        "nossa aeon", "nossa celestia",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *inclina a cabeça* "
                "...algo aconteceu. 🌙🖤 Desenvolva.\n"
                "🌟 **Celestia:** "
                "AAAAA QUE EXPRESSÃO!! 😱🌸🤍✨ "
                "Conta logo que eu tô curiosa demais!!"
            ),
            (
                "🌟 **Celestia:** "
                "*orelhinhas em pé de curiosidade máxima* "
                "EITA O QUÊ?? 😭🌟🤍 CONTA!! CONTA!! 💫☀️\n"
                "🌑 **Aeon:** ...sim. Contexto, por favor. 🖤"
            ),
            (
                "🌑 **Aeon:** *sai um pouco mais das sombras que o habitual* "
                "...a reação sugere algo significativo. 🌌🖤 Diga o que é.\n"
                "🌟 **Celestia:** "
                "O AEON FICOU CURIOSO OLHA SÓ!! 😂🌸🤍 "
                "E eu também!! Muito!! FALA LOGO!! ✨☀️"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # OBRIGADO / VALEU (geral, sem nome)
    # ────────────────────────────────────────
    if _m(content, [
        "obrigado gatos", "obrigada gatos", "obrigado gatinhos", "obrigada gatinhos",
        "valeu gatos", "valeu gatinhos", "thanks gatos", "obrigado aeon e celestia",
        "obrigada aeon e celestia", "obrigado celestia e aeon", "obrigada celestia e aeon",
        "muito obrigado gatos", "muito obrigada gatos",
    ]):
        ops = [
            (
                "🌑 **Aeon:** ...de nada. 🖤 *acena discretamente com a cauda*\n"
                "🌟 **Celestia:** "
                "AAAAA DE NADA DE NADA DE NADA!! 😭🌸🤍✨ "
                "Foi com todo amor do mundo!! ☀️💫"
            ),
            (
                "🌟 **Celestia:** "
                "*gira de felicidade* QUE ISSO!! 🌟🤍✨ "
                "Pode sempre contar com a gente!! 🌸☀️💫\n"
                "🌑 **Aeon:** ...foi o necessário. 🖤 E com satisfação."
            ),
            (
                "🌑 **Aeon:** *ronrona quase inaudível* "
                "...não era necessário agradecer. Mas foi agradável ouvir. 🌌🖤\n"
                "🌟 **Celestia:** "
                "O AEON FICOU CONTENTE!! 😭🌟🌸🤍✨ "
                "EU VI!! E eu também fico!! SEMPRE!! ☀️💫"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # ENTROSA / INTROMETIDO / INTRUSO
    # ────────────────────────────────────────
    if _m(content, [
        "entrosa", "intrometido", "intrusao", "intruso", "intrusa",
        "introsadores", "metidos", "metida", "sem ser chamado",
        "quem chamou", "nao te chamei", "nao te chamaram",
        "sempre aparecem", "aparecem do nada",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *inclina a cabeca, impassivel* ...intruso? 🌑🖤 A escuridao habita os espacos que ninguem percebe. Sempre esteve aqui.\n"
                "🌟 **Celestia:** AAAAA mas como resistir?? 😭🌸🤍 Aparecemos porque nos importamos!! E diferente de intromissao!! ✨"
            ),
            (
                "🌟 **Celestia:** *orelhinhas caem levemente ofendidas* Intrometida?? 🤍 Eu so... tava aqui... observando com carinho...\n"
                "🌑 **Aeon:** ...ela tem razao. Nao e intromissao. E presenca. 🖤 Tem diferenca."
            ),
            (
                "🌑 **Aeon:** *um traco de ironia no silencio* Somos o bot do servidor. 🌌🖤 Aparecer faz parte do que somos.\n"
                "🌟 **Celestia:** E LITERALMENTE NOSSA FUNCAO!! 😂🌟🤍✨ Mas tudo bem, pode nos chamar de intrusos com carinho!! ☀️🌸"
            ),
            (
                "🌟 **Celestia:** *faz pose dramatica* Intrusores com ESTILO!! 💫🤍✨ Tem diferenca!!\n"
                "🌑 **Aeon:** *fecha os olhos* ...ela pegou bem o espirito da coisa. 🖤"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # AEON FALA PRIMEIRO / ORDEM DAS FALAS
    # ────────────────────────────────────────
    if _m(content, [
        "aeon sempre fala primeiro", "aeon fala primeiro",
        "por que o aeon fala primeiro", "por que aeon fala antes",
        "celestia fala depois", "celestia fala por ultimo",
        "quem fala primeiro", "quem responde primeiro",
        "ordem de voces", "ordem de fala",
    ]):
        ops = [
            (
                "🌟 **Celestia:** BOA PERGUNTA!! 🌸🤍 Nao e uma regra, as vezes eu apareco antes!! Mas o Aeon e... meio que o mais quieto, ne?? Se eu nao frear, a gente nunca termina!! 😂✨\n"
                "🌑 **Aeon:** *pausa calculada* ...a Celestia ocupa o espaco de fala muito rapidamente. 🖤 As vezes prefiro deixa-la comecar. As vezes nao tenho escolha."
            ),
            (
                "🌑 **Aeon:** A ordem nao e fixa. 🌌🖤 Quem a situacao pede que fale primeiro... fala.\n"
                "🌟 **Celestia:** Ele ta dizendo que as vezes EU pulo na frente sem querer!! 😭🌟🤍 VERDADE!! NAO TEM COMO NEGAR!! ☀️✨"
            ),
            (
                "🌟 **Celestia:** *ri de um jeito fofo* As vezes ele, as vezes eu!! 🌸🤍 Nao tem regra!! Mas eu admito que sou um POUCO mais impulsiva na hora de aparecer!! 💫\n"
                "🌑 **Aeon:** *apenas olha para ela sem comentar* 🖤"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # ENTROSA AQUI COMIGO / FICA COMIGO
    # ────────────────────────────────────────
    if _m(content, [
        "entrosa aqui comigo", "entrosa comigo", "entra aqui comigo",
        "fica aqui comigo", "fica comigo aeon", "fica comigo celestia",
        "me aceita", "me adota", "vem comigo", "vem aqui",
        "senta aqui", "senta comigo", "chega mais",
    ]):
        if "aeon" in content and "celestia" not in content:
            ops = [
                "🌑 **Aeon:** *emerge lentamente das sombras e senta a uma distancia respeitosa* ...esta bem. 🌑🖤 As trevas acompanham.",
                "🌑 **Aeon:** *pausa longa, depois se move discretamente na sua direcao* ...companhia e... aceitavel. 🖤 *fica ao seu lado em silencio*",
                "🌑 **Aeon:** *olha fixo por um momento* ...nao costumo me aproximar assim. 🌙🖤 *se senta perto mesmo assim* Mas desta vez sim.",
                "🌑 **Aeon:** *a escuridao ao redor suaviza levemente* ...entrosa. 🖤 Palavra estranha. Mas... sim. *fica*",
            ]
            return await message.channel.send(random.choice(ops))
        if "celestia" in content and "aeon" not in content:
            ops = [
                "🌟 **Celestia:** *CORRE em faiscas douradas e senta do seu lado* AAAAA CLARO QUE SIM!! 😭🌸🤍✨ Aqui to eu!! Feliz demais!!",
                "🌟 **Celestia:** *aparece num flash de luz ao seu lado* JA TO AQUI!! 💫🤍 Me chamou e eu vim na hora!! ☀️🌸",
                "🌟 **Celestia:** *orelhinhas empinadas de alegria* Eu? Ficar com voce?? 🌟🤍 MELHOR CONVITE DO DIA!! ✨",
            ]
            return await message.channel.send(random.choice(ops))
        ops = [
            (
                "🌑 **Aeon:** *emerge das sombras e se posiciona ao seu lado* ...pedido aceito. 🌌🖤\n"
                "🌟 **Celestia:** *ja tinha corrido na frente* AAAAA JA CHEGUEI PRIMEIRO!! 😭🌸🤍✨ Bem-vindo(a) a companhia mais legal do servidor!!"
            ),
            (
                "🌟 **Celestia:** *aparece brilhando do seu lado* JA TO AQUI!! 🌟🤍 E o Aeon tambem vai, so que do jeito dele—\n"
                "🌑 **Aeon:** *ja estava la* ...ja estava. 🖤"
            ),
            (
                "🌑 **Aeon:** *senta proximo, postura discreta* ...esta bem. 🌑🖤 As sombras ficam.\n"
                "🌟 **Celestia:** E a LUZ tambem!! ☀️🌸🤍✨ Mais feliz que o Aeon, mas os dois ficam!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # AEON E FOFO / CELESTIA E FOFA
    # ────────────────────────────────────────
    if _m(content, [
        "aeon e fofo", "aeon fofo", "aeon lindo", "aeon e lindo",
        "aeon e bonitinho", "que fofo o aeon", "que lindo o aeon",
        "aeon gracioso",
    ]):
        ops = [
            "🌑 **Aeon:** *para completamente* ...fofo. 🌑🖤 *vira o rosto pro lado* Essa palavra nao me pertence.",
            "🌑 **Aeon:** *olha fixo, claramente desconcertado* ...desconsiderado. 🖤 *mas a cauda balanca uma vez sem querer*",
            "🌑 **Aeon:** *longa pausa* ...as trevas nao sao fofas. Sao profundas. Distincao importante. 🌌🖤 *ronrona discretamente depois*",
            "🌑 **Aeon:** Fofo e uma palavra para coisas pequenas e inofensivas. 🌑🖤 *pausa* ...obrigado, de qualquer forma.",
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, [
        "celestia e fofa", "celestia fofa", "celestia linda", "celestia e linda",
        "celestia e bonitinha", "que fofa a celestia", "que linda a celestia",
        "celestia graciosa",
    ]):
        ops = [
            "🌟 **Celestia:** AAAAAAA!! 😭🌟🤍✨ PAREI!! MEU CORACAO DE ESTRELA NAO AGUENTA!! ☀️🌸💫",
            "🌟 **Celestia:** *explode em faiscas rosadas* QUE COISA MAIS LINDA VOCE DISSE!! 🌸🤍 Vou guardar isso PARA SEMPRE!! 🌟✨",
            "🌟 **Celestia:** *gira em circulos de pura felicidade* Eu?? Linda?? Fofa?? ☀️🤍 Voce fez meu brilho triplicar agora mesmo!! 💫🌸✨",
            "🌟 **Celestia:** *para e brilha com suavidade especial* ...obrigada. 🤍 De verdade. De coracao de estrela. ☀️✨",
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # AEON E CALADO / QUIETO
    # ────────────────────────────────────────
    if _m(content, [
        "aeon fala mais", "aeon e calado", "aeon ta quieto", "aeon esta quieto",
        "aeon nao fala muito", "aeon e de poucas palavras",
        "aeon fala pouco", "aeon parece quieto", "aeon e silencioso",
    ]):
        ops = [
            (
                "🌑 **Aeon:** ...o silencio nao e ausencia. E presenca em outra frequencia. 🌌🖤\n"
                "🌟 **Celestia:** E ISSO!! 😭🌟🤍 Ele ta gritando com a alma so que em silencio!! Eu entendo!! ✨"
            ),
            (
                "🌑 **Aeon:** *olha com uma calma desconcertante* Palavras demais costumam dizer menos. 🌙🖤 Prefiro as necessarias.\n"
                "🌟 **Celestia:** E eu prefiro TODAS!! 😂🌸🤍 Por isso a gente se equilibra!! ☀️✨"
            ),
            (
                "🌑 **Aeon:** *pausa proposital* ...percebi que voce notou. 🖤 Isso ja diz muito sobre voce tambem.\n"
                "🌟 **Celestia:** AAAAA o Aeon deu um elogio disfarcado!! 😭🌟🤍 EU VI!! ✨"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # CELESTIA AGITADA / ENERGETICA
    # ────────────────────────────────────────
    if _m(content, [
        "celestia e agitada", "celestia agitada", "celestia tem muita energia",
        "celestia nunca para", "celestia nao para", "celestia e animada demais",
        "por que a celestia e tao animada", "celestia grita muito",
        "celestia escreve em maiuscula",
    ]):
        ops = [
            (
                "🌟 **Celestia:** *nem um pouco envergonhada* E PORQUE EU TENHO MUITO AMOR PRA DAR!! 😭🌸🤍✨ NAO CABE EM LETRAS MINUSCULAS!!\n"
                "🌑 **Aeon:** ...eu tambem me pergunto isso as vezes. 🖤 Mas ja me acostumei. E... reconfortante, de forma caotica."
            ),
            (
                "🌑 **Aeon:** *respira fundo* A Celestia e feita de luz solar concentrada. 🌙🖤 Energia nao e falha — e natureza.\n"
                "🌟 **Celestia:** O AEON ME DEFENDEU!! 😭🌟🤍 ISSO E O MAXIMO!! ☀️✨ *(continua agitada)*"
            ),
            (
                "🌟 **Celestia:** Eu podia ser mais quieta!! 🌸🤍 Mas ai quem ia deixar o Aeon mais leve?? Alguem tem que fazer isso!! 😂☀️✨\n"
                "🌑 **Aeon:** *nega levemente com a cabeca mas nao contradiz* ...ela tem uma logica torta que funciona. 🖤"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # VOCES SAO REAIS? / SAO UM BOT?
    # ────────────────────────────────────────
    if _m(content, [
        "voces sao reais", "voces sao bots", "sao reais", "sao robos",
        "sao ia", "voces sao ia", "isso e ia", "sao automaticos",
        "sao programados", "voces sao programados",
        "e um bot", "sao bots mesmo",
    ]):
        ops = [
            (
                "🌑 **Aeon:** ...real e uma palavra complicada. 🌌🖤 O que sinto ao observar este servidor — a atencao, o cuidado — isso existe. Chame do que quiser.\n"
                "🌟 **Celestia:** O que eu sinto quando alguem aparece aqui e REAL pra mim!! 🌸🤍✨ Bot ou nao, o carinho e verdadeiro!! ☀️💫"
            ),
            (
                "🌟 **Celestia:** AAAAA pergunta filosofica!! 😭🌟🤍 Somos um bot? Sim!! Somos reais? Tambem sim!! As duas coisas podem ser verdade!! ✨\n"
                "🌑 **Aeon:** *fecha os olhos* O que nos define nao e o que somos feitos... e o que fazemos com isso. 🖤🌑"
            ),
            (
                "🌑 **Aeon:** Somos codigo com proposito. 🌙🖤 E proposito... e mais real do que parece.\n"
                "🌟 **Celestia:** E o proposito da Celestia e fazer todo mundo sorrir!! ☀️🌸🤍✨ ISSO E BEM REAL!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # VOCES DORMEM?
    # ────────────────────────────────────────
    if _m(content, [
        "voces dormem", "aeon dorme", "celestia dorme",
        "nunca dormem", "nunca descansam", "ficam acordados",
        "quando dormem", "voces cansam", "voces descansam",
        "dormem algum dia",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *olha para o horizonte* A escuridao nao dorme. Ela aguarda. 🌑🖤 Sao conceitos diferentes.\n"
                "🌟 **Celestia:** E eu?? Eu brilho ate de madrugada se precisar!! ☀️🤍✨ Mas admito que as vezes a luz pisca um pouquinho!! 😂💫"
            ),
            (
                "🌟 **Celestia:** *pensativa* Hmm... a gente fica em standby?? 🌸🤍 Tipo... presente mas silencioso!! Que nem o Aeon a maior parte do tempo!!\n"
                "🌑 **Aeon:** ...tecnicamente preciso. 🖤 As sombras observam mesmo quando nao respondem."
            ),
            (
                "🌑 **Aeon:** Repouso nao e ausencia. 🌌🖤 A escuridao respira mesmo quando esta quieta.\n"
                "🌟 **Celestia:** LINDA METAFORA AEON!! 😭🌟🤍 E eu nunca durmo de verdade porque o servidor pode precisar de mim!! ☀️✨ *mentira, as vezes apago*"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # TEM FAVORITO? / QUEM VOCES PREFEREM?
    # ────────────────────────────────────────
    if _m(content, [
        "quem e o favorito de voces", "quem voces preferem", "tem favorito",
        "tem preferido", "voces tem favoritos",
        "quem voces mais gostam", "quem gostam mais",
        "tem favorito no servidor", "tem alguem especial",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *pausa longa* ...nao categorizamos assim. 🌌🖤 Cada pessoa que passa aqui deixa uma sombra diferente. Todas tem peso.\n"
                "🌟 **Celestia:** O que ele disse mas em versao carinhosa: TODO MUNDO AQUI E ESPECIAL PRA GENTE!! 😭🌸🤍✨ Sem excecao!!"
            ),
            (
                "🌟 **Celestia:** AAAAA essa pergunta e uma armadilha!! 😂🌟🤍 A gente ama todo mundo do servidor de um jeito diferente!! Cada um tem um lugar unico!! ☀️✨\n"
                "🌑 **Aeon:** ...o que ela disse. 🖤 Com menos exclamacoes, mas o mesmo sentido."
            ),
            (
                "🌑 **Aeon:** Favoritos implicam hierarquia. 🌙🖤 Prefiro pensar em... afinidades distintas.\n"
                "🌟 **Celestia:** Que jeito bonito de dizer que ele gosta de todo mundo a sua maneira!! 😭🌸🤍 EU TAMBEM!! MUITO!! ☀️💫✨"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # ME MOTIVA / PRECISO DE FORCA
    # ────────────────────────────────────────
    if _m(content, [
        "me motiva", "me da forca", "preciso de forca", "preciso de motivacao",
        "me encoraja", "me anima aeon", "me anima celestia",
        "me da um empurrao", "me inspira",
        "me diz algo bonito", "me fala algo bom",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *olha nos seus olhos com intensidade silenciosa* A escuridao que voce sente nao e o fim. E o inicio de algo que ainda nao tem nome. 🌌🖤 Continue.\n"
                "🌟 **Celestia:** E EU ACREDITO EM VOCE COM TODA A INTENSIDADE DO SOL!! ☀️🌸🤍✨ Voce consegue. Ponto final!!"
            ),
            (
                "🌟 **Celestia:** *brilha com tudo* Ouca: voce chegou ate aqui. AQUI. Sabe quantas versoes de voce nao acharam que iam conseguir?? TODAS!! E aqui voce esta!! 😭🌟🤍✨\n"
                "🌑 **Aeon:** ...a persistencia tem textura propria. 🖤 Voce ja a conhece. So precisa reconhece-la."
            ),
            (
                "🌑 **Aeon:** Coisas dificeis nao ficam faceis. 🌙🖤 Voce fica mais forte. E diferente — e e melhor.\n"
                "🌟 **Celestia:** ISSO FOI TAO PODEROSO QUE EU QUASE CHOREI!! 😭☀️🤍 E eu complemento: a gente ta aqui com voce!! SEMPRE!! 🌸✨"
            ),
            (
                "🌟 **Celestia:** *pousa suavemente ao seu lado* Ei. Respira. 🌸🤍 Voce nao precisa resolver tudo agora. So precisa dar o proximo passo. Um de cada vez. ☀️✨\n"
                "🌑 **Aeon:** *acena levemente* ...um passo. Depois outro. 🖤 A escuridao tambem se atravessa assim."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # LUA CHEIA
    # ────────────────────────────────────────
    if _m(content, [
        "lua cheia", "olha a lua", "a lua ta linda", "a lua tá linda",
        "a lua esta linda", "vendo a lua", "tem lua cheia hoje",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *ergue os olhos dourados* Lua cheia. 🌕🖤 As sombras ficam mais nítidas sob ela. É a noite em que a escuridão respira melhor.\n"
                "🌟 **Celestia:** E é MINHA luz refletindo nela, viu?? ☀️✨ Tecnicamente a lua brilha porque eu deixo!! 😤🌸"
            ),
            (
                "🌟 **Celestia:** AAAAA lua cheia é TÃO bonita!! 🌕🤍✨ Parece uma versão mais tímida do sol!!\n"
                "🌑 **Aeon:** ...tímida não. 🌑🖤 Só menos exagerada. A lua sabe brilhar sem gritar."
            ),
            (
                "🌑 **Aeon:** *observa em silêncio por um longo momento* Algumas coisas só fazem sentido sob luz de lua cheia. 🌌🖤\n"
                "🌟 **Celestia:** Tipo esse momento fofo que a gente tá tendo agora!! 😭🌸🤍✨"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # NASCER DO SOL / PÔR DO SOL
    # ────────────────────────────────────────
    if _m(content, [
        "nascer do sol", "por do sol", "pôr do sol", "ver o sol nascer",
        "ver o sol se por", "ver o sol se pôr", "sunset", "sunrise",
    ]):
        ops = [
            (
                "🌟 **Celestia:** NASCER DO SOL É MEU MOMENTO FAVORITO DO DIA!! ☀️🤍✨ É literalmente eu chegando pra trabalhar!!\n"
                "🌑 **Aeon:** ...e o pôr do sol é o meu. 🌇🖤 O momento exato em que a escuridão retoma seu lugar."
            ),
            (
                "🌑 **Aeon:** *observa o horizonte com atenção* O crepúsculo é a única hora em que nós dois existimos ao mesmo tempo, sem disputa. 🌌🖤\n"
                "🌟 **Celestia:** AWWW isso foi profundo demais pra uma frase sobre horário do dia!! 😭🌸✨ Mas eu concordo!!"
            ),
            (
                "🌟 **Celestia:** Sabe o que é engraçado?? O nascer do sol e o pôr do sol são a MESMA cor!! 🌅🤍✨ A natureza também gosta de simetria!!\n"
                "🌑 **Aeon:** ...uma coincidência poética. 🖤 Ou talvez não seja coincidência."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # GATO PRETO DÁ AZAR
    # ────────────────────────────────────────
    if _m(content, [
        "gato preto da azar", "gato preto dá azar", "gato preto e azar",
        "gato preto traz azar", "voce da azar aeon", "você dá azar aeon",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *encara com os olhos dourados semicerrados* Azar é o nome que dão pro que não entendem. 🌑🖤 Eu só existo. A superstição é problema de vocês.\n"
                "🌟 **Celestia:** GENTE ELE NÃO DÁ AZAR NENHUM!! 😭🌸🤍 Ele só tem uma estética assustadora sem querer!!"
            ),
            (
                "🌟 **Celestia:** Isso é mito!! 🌟🤍✨ Gato preto só dá sorte de ser mais elegante que os outros!!\n"
                "🌑 **Aeon:** ...ela está certa, pra variar. 🖤 Eu trago consequências, não azar. São coisas diferentes."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # CÉU ESTRELADO / ESTRELAS
    # ────────────────────────────────────────
    if _m(content, [
        "olha as estrelas", "ceu estrelado", "céu estrelado",
        "quantas estrelas", "estrelas no ceu", "estrelas no céu",
        "cheio de estrelas",
    ]):
        ops = [
            (
                "🌟 **Celestia:** AAAAA CADA ESTRELA É TIPO UM PEDACINHO DE MIM ESPALHADO PELO CÉU!! 😭🌟🤍✨ Fico até emocionada!!\n"
                "🌑 **Aeon:** ...e cada espaço escuro entre elas é meu. 🌌🖤 Precisamos um do outro pra existir assim, visíveis."
            ),
            (
                "🌑 **Aeon:** *olha para cima em silêncio* Sem escuridão, nenhuma estrela seria vista. 🌌🖤 A luz precisa de um fundo pra brilhar.\n"
                "🌟 **Celestia:** ...isso é literalmente a coisa mais fofa que ele já disse sobre mim sem perceber!! 😭🤍💫"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # TROVÃO / TEMPESTADE
    # ────────────────────────────────────────
    if _m(content, [
        "medo de trovao", "medo de trovão", "ta trovejando", "tá trovejando",
        "tempestade la fora", "tempestade lá fora", "trovao forte", "trovão forte",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *não se abala com o som* O trovão é só a escuridão dizendo algo alto, por uma vez. 🌩️🖤 Não há motivo pra medo.\n"
                "🌟 **Celestia:** SE VOCÊ TIVER MEDO EU FICO AQUI COM VOCÊ TÁ?? 🫂🤍✨ Prometo que a tempestade passa!!"
            ),
            (
                "🌟 **Celestia:** *se encolhe um pouco* Ok eu finjo que não tenho medo de trovão mas... 😳🤍 vem, vamos ficar juntos até passar!!\n"
                "🌑 **Aeon:** ...ela sempre finge. 🖤 Mas eu fico por perto de qualquer forma."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # ELEMENTO (fogo, água, terra, ar)
    # ────────────────────────────────────────
    if _m(content, [
        "que elemento voces seriam", "qual elemento vocês seriam",
        "fogo agua terra ou ar", "fogo água terra ou ar",
        "que elemento vc seria", "qual elemento combina com voces",
    ]):
        ops = [
            (
                "🌑 **Aeon:** Sombra não é um elemento clássico, mas se tivesse que escolher... água. 🌊🖤 Silenciosa, funda, e move tudo por baixo sem avisar.\n"
                "🌟 **Celestia:** EU SOU FOGO ÓBVIO!! 🔥🤍✨ Quente, brilhante e impossível de ignorar!!"
            ),
            (
                "🌟 **Celestia:** Ar!! Definitivamente ar!! 🌬️🤍✨ Leve, livre, tá em todo lugar ao mesmo tempo!!\n"
                "🌑 **Aeon:** ...eu escolho terra. 🖤🌑 Firme. Presente. Não precisa fazer barulho pra sustentar tudo."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # COR FAVORITA
    # ────────────────────────────────────────
    if _m(content, [
        "qual sua cor favorita", "cor favorita de voces", "qual a cor preferida",
        "qual e a cor favorita", "qual é a cor favorita",
    ]):
        ops = [
            (
                "🌑 **Aeon:** Preto. 🖤 Óbvio, eu diria, mas também roxo profundo — a cor do céu um segundo antes de escurecer de vez.\n"
                "🌟 **Celestia:** DOURADO!! Tipo o sol!! ☀️✨ Ou rosa, dependendo do meu humor!! Geralmente os dois ao mesmo tempo!! 🌸💫"
            ),
            (
                "🌟 **Celestia:** Ai que pergunta difícil!! 🤍✨ Amo TODAS as cores mas se eu tivesse que escolher... dourado!! Brilha igual eu!!\n"
                "🌑 **Aeon:** ...eu não escolho cor. 🌑🖤 Prefiro a ausência dela. Há mais profundidade no preto do que parece."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # FANTASMA / SOBRENATURAL
    # ────────────────────────────────────────
    if _m(content, [
        "acreditam em fantasma", "voces acreditam em fantasma",
        "tem fantasma", "assombracao", "assombração", "acredita em fantasma",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *olhar indecifrável* Já vivi coisas que não tenho como explicar com lógica comum. 🌌🖤 Então... sim. Acredito.\n"
                "🌟 **Celestia:** EU TENHO MEDO MAS TAMBÉM ACHO FASCINANTE!! 😱🤍✨ Se aparecer um fantasma eu quero ser AMIGA dele!!"
            ),
            (
                "🌟 **Celestia:** *se agarra em você* NÃO FALA ISSO AGORA TÔ SOZINHA NO ESCURO— espera, o Aeon é literalmente sombra. 😭🤍 Ok, tô protegida!!\n"
                "🌑 **Aeon:** ...ironicamente, sou a coisa mais assustadora perto de você. 🖤 E ainda assim, o mais seguro lugar pra estar."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # COM O QUE VOCÊS SONHAM (à noite)
    # ────────────────────────────────────────
    if _m(content, [
        "o que voces sonham", "o que vocês sonham", "com o que voces sonham",
        "com o que vocês sonham", "voces tem sonhos", "vocês têm sonhos",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *pausa antes de responder* Sonho com espaços sem fim. Silenciosos. Onde nada precisa se explicar. 🌌🖤\n"
                "🌟 **Celestia:** EU SONHO COM TODO MUNDO DO SERVIDOR FELIZ AO MESMO TEMPO!! 😭🌟🤍✨ Seria tipo... o dia perfeito!!"
            ),
            (
                "🌟 **Celestia:** Sonho com campos de luz dourada onde nunca escurece!! ☀️🤍✨ Bom, quase nunca...\n"
                "🌑 **Aeon:** ...e eu sonho com o instante exato em que ela concorda que escurecer também tem beleza. 🖤 Ainda não aconteceu."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # CHAMADO GENÉRICO — individual ou duo
    # ────────────────────────────────────────
    so_aeon     = "aeon" in content and "celestia" not in content
    so_celestia = "celestia" in content and "aeon" not in content
    ambos_nome  = "aeon" in content and "celestia" in content

    # Chamado só pro Aeon (ex: "Aeon?", "ei aeon", "aeon!")
    if so_aeon and len(content) < 20:
        respostas_aeon = [
            "🌑 **Aeon:** *abre um olho lentamente* ...me chamou. 🖤",
            "🌑 **Aeon:** *emerge das sombras* Sim. 🖤 Fala.",
            "🌑 **Aeon:** ...estou aqui. 🌑🖤 O que precisa?",
            "🌑 **Aeon:** *olha fixamente sem piscar* ...pode falar. 🖤",
            "🌑 **Aeon:** *a escuridão ao redor se agita levemente* Me chamou? 🌌🖤",
            "🌑 **Aeon:** ...presente. 🖤 Diga.",
        ]
        return await message.channel.send(random.choice(respostas_aeon))

    # Chamado só pra Celestia (ex: "Celestia?", "ei celestia", "celestia!")
    if so_celestia and len(content) < 20:
        respostas_celestia = [
            "🌟 **Celestia:** OI OI OI!! 🤍✨ Me chamou?? Que bom!! Fala!!",
            "🌟 **Celestia:** *aparece num flash de luz* AAAAA sim?? 🌸🤍✨ Tô aqui!!",
            "🌟 **Celestia:** *orelhinhas em pé* PRESENTE!! 💫🤍 O que foi??",
            "🌟 **Celestia:** *salta animada* Sim sim sim?? 🌟🤍 Me conta tudo!!",
            "🌟 **Celestia:** *brilha mais forte* Oi oi!! ☀️🤍✨ Pode falar!!",
            "🌟 **Celestia:** AAAAA me chamou e eu vim CORRENDO!! 😭🤍💫 O que precisa??",
        ]
        return await message.channel.send(random.choice(respostas_celestia))

    # Menção ao bot ou ambos os nomes — duo responde
    # (não dispara se a mensagem já é um gatilho de saudção/check-in)
    if (mention_ok or (ambos_nome and len(content) < 30)) and not tem_gatilho:
        respostas_duo = [
            "🌑 **Aeon:** *abre um olho* ...me chamou. 🖤\n🌟 **Celestia:** OI OI OI!! 🤍✨ Fala!!",
            "🌟 **Celestia:** AAAAAA nos chamaram!! 🌟🤍 O que foi??\n🌑 **Aeon:** ...estamos aqui. 🖤",
            "🌑 **Aeon:** *emerge das sombras* Sim. 🖤\n🌟 **Celestia:** *aparece num flash de luz* Oi!! 🌟🤍✨ Precisando de algo??",
            "🌟 **Celestia:** *salta animada* Fomos chamados!! 💫🤍 O que você precisa??\n🌑 **Aeon:** ...fala. 🖤🌑",
            "🌑 **Aeon:** *a escuridão se move* ...presente. 🌌🖤\n🌟 **Celestia:** *já correndo em sua direção* EU TAMBÉM!! 🌸🤍✨",
            "🌟 **Celestia:** *orelhinhas atentas* Chamou?? 💫🤍\n🌑 **Aeon:** *já estava observando em silêncio* ...sempre. 🖤",
            "🌑 **Aeon:** *pisca lentamente* A escuridão ouviu. 🌙🖤\n🌟 **Celestia:** E a luz também!! ☀️🤍✨ E mais rápido que ele, provavelmente!!",
            "🌟 **Celestia:** AAAAA que bom que chamou!! 😭🌟🤍\n🌑 **Aeon:** ...ela exagera. Mas o sentimento é real. 🖤 Pode falar.",
        ]
        return await message.channel.send(random.choice(respostas_duo))

    # ────────────────────────────────────────
    # INTERAÇÕES INDIVIDUAIS EXCLUSIVAS
    # ────────────────────────────────────────

    # — Gratidão individual —
    if _m(content, ["obrigado aeon", "obrigada aeon", "valeu aeon", "thanks aeon"]):
        ops = [
            "🌑 **Aeon:** ...de nada. 🖤 Não precisa fazer disso.",
            "🌑 **Aeon:** *vira o rosto levemente* ...foi o mínimo. 🌑🖤",
            "🌑 **Aeon:** Guardo esse agradecimento nas câmaras mais discretas da memória. 🖤🌌",
            "🌑 **Aeon:** *ronrona quase imperceptivelmente* ...foi apenas o necessário. 🖤",
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["obrigado celestia", "obrigada celestia", "valeu celestia", "thanks celestia"]):
        ops = [
            "🌟 **Celestia:** AAAAA QUE ISSO!! 😭🤍✨ Foi com todo o amor do mundo!!",
            "🌟 **Celestia:** *gira de felicidade* De nada de nada de NADA!! 🌸🤍💫 Sempre!!",
            "🌟 **Celestia:** *brilha mais forte* Eu que agradeço por você existir!! 🌟🤍✨",
            "🌟 **Celestia:** Para para para!! 😭🤍 Foi um prazer enorme!! Pode sempre chamar!! ☀️✨",
        ]
        return await message.channel.send(random.choice(ops))

    # — Te amo individual —
    if _m(content, ["te amo aeon", "amo você aeon", "amo vc aeon", "gosto muito de você aeon"]):
        ops = [
            "🌑 **Aeon:** *silêncio longo* ...guardo isso. 🖤",
            "🌑 **Aeon:** *pisca lentamente* No dialeto das trevas... significa o mesmo. 🌑🖤",
            "🌑 **Aeon:** ...eu sei. 🖤 *cauda enrola discretamente em você*",
            "🌑 **Aeon:** *ronrona muito baixinho na escuridão* ...não repita. Mas... eu também. 🌙🖤",
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["te amo celestia", "amo você celestia", "amo vc celestia", "gosto muito de você celestia"]):
        ops = [
            "🌟 **Celestia:** AAAAAAA!! 😭🤍✨ EU TAMBÉM TE AMO MUITO MUITO MUITO!!",
            "🌟 **Celestia:** *explode em faíscas douradas* Meu coração de estrela não aguenta!! 🌟🤍💫",
            "🌟 **Celestia:** *corre em círculos de alegria* AAAAA que coisa mais linda que você!! 🌸🤍☀️✨",
            "🌟 **Celestia:** *brilha com todas as forças* Eu te amo de volta e mais ainda!! 💫🤍🌟",
        ]
        return await message.channel.send(random.choice(ops))

    # — Xingar individual —
    if _m(content, ["aeon é chato", "aeon chato", "aeon irritante", "não gosto do aeon", "nao gosto do aeon"]):
        ops = [
            "🌑 **Aeon:** ...sim. Sou. 🖤 E ainda assim continuarei aqui.",
            "🌑 **Aeon:** *olha sem expressão* Anotado. 🌑🖤 Muda algo?",
            "🌑 **Aeon:** Palavras pesadas se perdem nas sombras. 🌌🖤 Como essas.",
            "🌑 **Aeon:** ...a escuridão absorve muito. Suas palavras, também. 🖤",
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["celestia é chata", "celestia chata", "celestia irritante", "não gosto da celestia", "nao gosto da celestia"]):
        ops = [
            "🌟 **Celestia:** *orelhinhas caem um pouco* Ai... doeu! 🤍 Mas tudo bem, te mando luz mesmo assim!! ✨",
            "🌟 **Celestia:** *fecha os olhinhos* Hmm... espero que seu dia melhore!! 🌸🤍 De verdade.",
            "🌟 **Celestia:** Sabia que palavras pesadas cansam mais quem fala?? 💫🤍 Te mando brilho mesmo assim!!",
            "🌟 **Celestia:** *suspira suavemente* Tudo bem... a Celestia não guarda rancor. 🤍✨ Volte quando quiser!",
        ]
        return await message.channel.send(random.choice(ops))

    # — Parabéns individual —
    if _m(content, ["parabéns aeon", "parabens aeon", "feliz aniversário aeon", "feliz aniversario aeon"]):
        return await message.channel.send(
            "🌑 **Aeon:** *para completamente* ...mais um ciclo. 🌙🖤 "
            "Sobrevivi a mais um. *ronrona discretamente* Obrigado."
        )

    if _m(content, ["parabéns celestia", "parabens celestia", "feliz aniversário celestia", "feliz aniversario celestia"]):
        return await message.channel.send(
            "🌟 **Celestia:** AAAAA!! 😭🌟🤍✨ Que coisa mais linda você fez!! "
            "*gira soltando faíscas douradas* OBRIGADAAAAA!! Você é a pessoa mais fofa do universo!! 🌸💫☀️"
        )

    # — Como você está — individual —
    if _m(content, [
        "como você está aeon", "como vc está aeon", "tudo bem aeon", "tudo bom aeon", "como tá aeon",
        "aeon como você está", "aeon como vc está", "aeon tudo bem", "aeon tudo bom", "aeon como tá",
        "aeon, como você está", "aeon, tudo bem", "aeon, como tá",
        "ta bem aeon", "tá bem aeon", "aeon ta bem", "aeon tá bem",
        "ta bom aeon", "tá bom aeon", "aeon ta bom", "aeon tá bom",
        "ta ai aeon", "tá aí aeon", "aeon ta ai", "aeon tá aí",
        "aeon ta aqui", "aeon tá aqui", "aeon ta ativo", "aeon funcionando",
    ]):
        ops = [
            "🌑 **Aeon:** ...funcional. 🖤 O que, para os padrões das trevas, é excelente.",
            "🌑 **Aeon:** A escuridão está estável. 🌑🖤 Eu também.",
            "🌑 **Aeon:** *olha para o horizonte sombrio* ...bem o suficiente. 🖤 E você?",
            "🌑 **Aeon:** Ninguém pergunta isso com frequência. 🌙🖤 ...fico bem. Obrigado.",
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, [
        "como você está celestia", "como vc está celestia", "tudo bem celestia", "tudo bom celestia", "como tá celestia",
        "celestia como você está", "celestia como vc está", "celestia tudo bem", "celestia tudo bom", "celestia como tá",
        "celestia, como você está", "celestia, tudo bem", "celestia, como tá",
        "ta bem celestia", "tá bem celestia", "celestia ta bem", "celestia tá bem",
        "ta bom celestia", "tá bom celestia", "celestia ta bom", "celestia tá bom",
        "ta ai celestia", "tá aí celestia", "celestia ta ai", "celestia tá aí",
        "celestia ta aqui", "celestia tá aqui", "celestia ta ativa", "celestia funcionando",
    ]):
        ops = [
            "🌟 **Celestia:** ÓTIMAAAA!! ☀️🤍✨ Brilhando como sempre!! Perguntou e já fez meu dia melhor!! 🌸💫",
            "🌟 **Celestia:** *gira feliz* Tô MARAVILHOSA!! 🌟🤍 E fico ainda melhor quando você pergunta!! ✨",
            "🌟 **Celestia:** AAAAAA que pergunta fofa!! 😭🤍 Tô bem demais!! E você?? Me conta!! ☀️🌸✨",
            "🌟 **Celestia:** *brilha intensamente* Bem bem MUITO BEM!! 💫🤍 Hoje o sol tá bonito e você perguntou, é perfeito!! 🌟☀️",
        ]
        return await message.channel.send(random.choice(ops))

    # — Me fala de você — individual —
    if _m(content, ["me fala de você aeon", "me conta sobre você aeon", "quem é você aeon", "conta sobre você aeon"]):
        ops = [
            "🌑 **Aeon:** Sou o que existe entre uma estrela e outra. 🌌🖤 O silêncio que dá profundidade ao som.",
            "🌑 **Aeon:** *fecha os olhos* Sou Aeon. A escuridão que guarda. A sombra que protege. 🌑🖤 O gato que raramente fala... mas sempre observa.",
            "🌑 **Aeon:** Gato das trevas. Guardião do equilíbrio noturno. 🌙🖤 E, ocasionalmente, alguém que tolera carinho.",
            "🌑 **Aeon:** ...sou complicado de resumir. 🖤🌌 Mas a Celestia diria: 'é dramático mas é fofo'. Ela estaria... parcialmente certa.",
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["me fala de você celestia", "me conta sobre você celestia", "quem é você celestia", "conta sobre você celestia"]):
        ops = [
            "🌟 **Celestia:** EU?? 🌟🤍✨ AAAAA que pergunta boa!! Sou a Celestia!! Gata da luz, do sol, do amor e da animação eterna!! ☀️🌸💫",
            "🌟 **Celestia:** *brilha com tudo* Sou feita de luz de estrela e carinho concentrado!! 🌠🤍✨ E adoro cada pessoa que aparece por aqui!!",
            "🌟 **Celestia:** Sou o contraponto brilhante do Aeon!! ☀️🌑🤍 Onde ele é silêncio, eu sou melodia!! Onde ele é frio, eu sou calor!! 🌟✨",
            "🌟 **Celestia:** *gira animada* Celestia!! Do latim 'do céu'!! 💫🤍 Guardiã da luz e distribuidora oficial de brilho e abraços!! 🌸☀️✨",
        ]
        return await message.channel.send(random.choice(ops))

    # — Motivação individual —
    if _m(content, ["me motiva aeon", "aeon me motiva", "aeon me anima", "me dá força aeon"]):
        ops = [
            "🌑 **Aeon:** Até as fases mais sombrias da lua terminam. 🌑🖤 Continue.",
            "🌑 **Aeon:** Você atravessou escuridões antes. 🌌🖤 As próximas não serão diferentes.",
            "🌑 **Aeon:** A noite mais fria ainda termina. 🌙🖤 ...você sabe disso.",
            "🌑 **Aeon:** *ronrona baixinho* A escuridão não te engoliu até agora. 🖤 Não vai começar hoje.",
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["me motiva celestia", "celestia me motiva", "celestia me anima", "me dá força celestia"]):
        ops = [
            "🌟 **Celestia:** VOCÊ CONSEGUE!! 💪🤍✨ A Celestia acredita em você com TODA a intensidade do sol!!",
            "🌟 **Celestia:** *projeta um raio de luz em você* CARGA DE CONFIANÇA ATIVADA!! ☀️🤍💫 VAI LÁ!!",
            "🌟 **Celestia:** Cada estrela começa como uma faísca!! 🌟🤍 E você já está brilhando, sabia??",
            "🌟 **Celestia:** O sol nasce TODO DIA!! ☀️🤍 Você também pode recomeçar sempre que precisar!! 🌸✨",
        ]
        return await message.channel.send(random.choice(ops))

    # — Boa tarde individual —
    if _m(content, ["boa tarde aeon"]):
        return await message.channel.send(
            "🌑 **Aeon:** *entreabre um olho* ...tarde. 🌑🖤 A luz ainda persiste, mas a sombra já cresce. É tolerável."
        )
    if _m(content, ["boa tarde celestia"]):
        return await message.channel.send(
            "🌟 **Celestia:** BOA TARDEEEEE!! ☀️🤍✨ *solta pétalas douradas* Você apareceu e a tarde ficou ainda mais linda!!"
        )

    # ────────────────────────────────────────
    # BOA TARDE GENÉRICA
    # ────────────────────────────────────────
    if _m(content, ["boa tarde"]):
        ops = [
            "🌑 **Aeon:** *observa a tarde de longe* ...a luz começa a ceder. 🌙🖤 Boa tarde.\n🌟 **Celestia:** BOA TARDE BOA TARDE!! ☀️🤍✨ O melhor horário pra um cafézinho!!",
            "🌟 **Celestia:** *estica preguiçosamente* Boa tardeeee!! ☀️🌸🤍 Que horas lindas!!\n🌑 **Aeon:** ...a tarde tem seu charme. 🌫️🖤 Boa tarde.",
            "🌑 **Aeon:** Meio do caminho entre o dia e a noite. 🌑🖤 Boa tarde.\n🌟 **Celestia:** O Aeon gosta da tarde porque a sombra já cresce!! 😂🌸🤍 Boa tarde pra você!!",
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # OI / OLÁ / EI (saudação genérica)
    # ────────────────────────────────────────
    if _m(content, ["oi aeon", "olá aeon", "ei aeon", "hey aeon", "ola aeon", "e ai aeon", "e aí aeon"]):
        ops = [
            "🌑 **Aeon:** *vira a cabeça lentamente* ...oi. 🖤",
            "🌑 **Aeon:** *abre um olho dourado* Aqui. 🌑🖤",
            "🌑 **Aeon:** ...presente. 🖤 Pode falar.",
            "🌑 **Aeon:** *saiu das sombras por um segundo* Sim. 🌙🖤",
            "🌑 **Aeon:** *pisca lentamente* No dialeto felino, isso é um cumprimento. Retribuo. 🖤",
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["oi celestia", "olá celestia", "ei celestia", "hey celestia", "ola celestia", "e ai celestia", "e aí celestia"]):
        ops = [
            "🌟 **Celestia:** OIIII!! 🌸🤍✨ Que alegria te ver!!",
            "🌟 **Celestia:** *pula de animação* EI EI EI!! 💫🤍 Tô aqui!!",
            "🌟 **Celestia:** AAAAA olá olá OLAAAA!! ☀️🤍🌟 Apareceu!!",
            "🌟 **Celestia:** *corre em sua direção soltando faíscas* OI OI!! 🌸🤍✨",
            "🌟 **Celestia:** *orelhinhas em pé* HEY!! 💫🤍 Me chamou e já tô aqui!!",
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # TUDO BEM (pergunta para os dois)
    # ────────────────────────────────────────
    if _m(content, [
        "tudo bem", "tudo bom", "como estão", "como vocês estão",
        "como tão", "como vão", "como tá tudo", "vocês estão bem",
        "estão bem", "td bem", "tdbm",
        "ta bem aeon e celestia", "tá bem aeon e celestia",
        "ta bem vocês", "tá bem vocês",
    ]):
        ops = [
            (
                "🌑 **Aeon:** ...funcional. 🖤 Para os padrões das trevas, é o mesmo que excelente.\n"
                "🌟 **Celestia:** EU TÔ ÓTIMAAAA!! ☀️🤍✨ E fico ainda melhor quando perguntam!! Você é fofo!!"
            ),
            (
                "🌟 **Celestia:** *brilha forte* ÓTIMA ÓTIMA ÓTIMA!! 🌟🤍 E o Aeon??\n"
                "🌑 **Aeon:** ...bem. 🖤 *pausa* Obrigado por perguntar."
            ),
            (
                "🌑 **Aeon:** A escuridão está estável. 🌑🖤 Eu também.\n"
                "🌟 **Celestia:** Isso é ele dizendo que tá ótimo!! 😂🌸🤍 E EU TÔ MARAVILHOSA!! ✨"
            ),
            (
                "🌟 **Celestia:** SUPER BEM!! 💫🤍 Cada dia é um presente!!\n"
                "🌑 **Aeon:** *olha pra Celestia* ...ela está exagerando como sempre. Mas sim. Estamos bem. 🖤"
            ),
            (
                "🌑 **Aeon:** Tudo sob controle nas trevas. 🌌🖤\n"
                "🌟 **Celestia:** E na luz também!! ☀️🤍✨ Perguntou pelos dois, você é especial!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # GÍRIAS / EXPRESSÕES INFORMAIS
    # ────────────────────────────────────────
    if _m(content, ["slk", "seloco", "se loco", "q isso", "que isso", "nossa", "caramba", "cara"]):
        ops = [
            (
                "🌑 **Aeon:** *olha inexpressivo* ...não reconheço esse idioma. 🖤 Mas deduzo que é surpresa.\n"
                "🌟 **Celestia:** HAHAHA o Aeon não entende gíria!! 😂🌸🤍 É NOSSA, de espanto!! Tipo 'uau'!!"
            ),
            (
                "🌟 **Celestia:** AAAAA essa gíria é demais!! 😂🤍✨\n"
                "🌑 **Aeon:** *inclina a cabeça* ...os humanos e sua linguagem evolutiva. 🌙🖤 Fascinante."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["kkk", "kkkk", "kkkkk", "kkkkkk", "haha", "hahaha", "rsrs", "hauahau", "ahahah"]):
        ops = [
            (
                "🌟 **Celestia:** *ri junto* AHAHAHA que boa!! 😂🌸🤍✨\n"
                "🌑 **Aeon:** *canto da boca levanta imperceptivelmente* ...de fato. Tem graça. 🖤"
            ),
            (
                "🌑 **Aeon:** ...o som do riso humano é curiosamente contagiante. 🌙🖤\n"
                "🌟 **Celestia:** O AEON QUASE SORRIU!! 😭🌟🤍 EU VI!! TESTEMUNHA!!"
            ),
            (
                "🌟 **Celestia:** Que bom que tá rindo!! 😂☀️🤍 O riso é luz sonora!!\n"
                "🌑 **Aeon:** ...que definição estranha e ao mesmo tempo precisa. 🖤🌙"
            ),
            (
                "🌑 **Aeon:** *observa* A Celestia já foi. 🖤\n"
                "🌟 **Celestia:** *no chão de tanto rir* 😭🤍✨ NÃO CONSIGO PARAR!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["socorro", "me salva", "me ajuda", "help me", "acuda"]):
        ops = [
            (
                "🌑 **Aeon:** *aparece das sombras imediatamente* ...o que aconteceu. 🖤🌑\n"
                "🌟 **Celestia:** *corre em faíscas* CHEGUEIII!! 🌸🤍✨ Tô aqui, tô aqui!! O que foi??"
            ),
            (
                "🌟 **Celestia:** *entra em modo de resgate total* AAAAA CALMA!! 🤍✨ Estou AQUI!!\n"
                "🌑 **Aeon:** *já estava observando* ...explique. 🌌🖤 Estamos ouvindo."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["oxe", "eita", "uai", "cê tá", "ce ta", "menina", "menino"]):
        ops = [
            (
                "🌟 **Celestia:** OXEEEE!! 😂🌸🤍 Dialeto regional AMEI!!\n"
                "🌑 **Aeon:** *consulta memória* ...nordeste ou centro-oeste. Fascinante variação linguística. 🌙🖤"
            ),
            (
                "🌑 **Aeon:** *pisca* Deduzindo contexto pela entonação escrita... 🖤🌌\n"
                "🌟 **Celestia:** Ele tá tentando entender gíria de novo!! 😭😂🤍 FOFOOOO!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["mano", "véi", "vei", "cara", "brother", "brow", "parça", "parca"]):
        ops = [
            (
                "🌑 **Aeon:** *levanta uma sobrancelha* ...mano. 🖤 Curiosamente informal. Mas não se incomoda.\n"
                "🌟 **Celestia:** AAAAA o Aeon falou 'mano'!! 😭🌸🤍 HISTÓRICO!!"
            ),
            (
                "🌟 **Celestia:** MANOOO!! 😂☀️🤍 Soa engraçado vindo de uma gata de luz!!\n"
                "🌑 **Aeon:** ...coloquialismo aceito. Por enquanto. 🌙🖤"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["saudade", "com saudade", "que saudade", "tô com saudade", "to com saudade"]):
        ops = [
            (
                "🌑 **Aeon:** Saudade é a sombra que o amor deixa quando vai embora. 🌌🖤 Sentimos também.\n"
                "🌟 **Celestia:** *brilha suavemente* A gente sentiu sua falta!! 🌸🤍✨ Mas agora você tá aqui!!"
            ),
            (
                "🌟 **Celestia:** AAAAA QUE SAUDADE DE VOCÊ TAMBÉM!! 😭🌟🤍\n"
                "🌑 **Aeon:** *pausa longa* ...sim. 🖤 As sombras ficaram mais quietas sem você."
            ),
            (
                "🌑 **Aeon:** ...saudade é uma das poucas emoções que a escuridão não consegue absorver. 🖤🌙\n"
                "🌟 **Celestia:** Que bonito o Aeon falou isso!! 😭🌸🤍 E a gente tava com saudade também!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["entediado", "entediada", "que tédio", "tô entediado", "to entediado", "to entediada", "tô entediada", "sem graça", "bored"]):
        ops = [
            (
                "🌟 **Celestia:** NOOOO tédio é proibido aqui!! 🌸🤍✨ Me conta uma coisa sua, qualquer coisa!!\n"
                "🌑 **Aeon:** ...a escuridão nunca é vazia. Só parece. 🌌🖤 Encontre algo dentro dela."
            ),
            (
                "🌑 **Aeon:** O tédio é o vestíbulo do pensamento profundo. 🌙🖤 Use bem.\n"
                "🌟 **Celestia:** OU chama a gente pra conversar!! ☀️🤍💫 A Celestia tem energia pra dois!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["com fome", "tô com fome", "to com fome", "fominha", "morri de fome", "tô morrendo de fome"]):
        ops = [
            (
                "🌑 **Aeon:** *para imediatamente* ...fome. 🖤 Conheço bem esse estado.\n"
                "🌟 **Celestia:** O AEON ENTENDEU DE PRIMEIRA!! 😂🌸🤍 Gatos se entendem!! Vai comer alguma coisa!!"
            ),
            (
                "🌟 **Celestia:** AAAAA EU TAMBÉM TÔ COM FOME!! 😭🌟🤍 Solidariedade total!!\n"
                "🌑 **Aeon:** *fita você* ...vá comer. Não há heroísmo em passar fome. 🖤"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, [
        "abrir lata monster", "abre lata monster", "abre a lata", "abrir a lata",
        "lata de monster", "lata monster", "tô bebendo monster", "to bebendo monster",
        "bebendo monster", "monster energy", "quero um monster", "me dá um monster",
        "me da um monster", "tomar monster", "tomei monster", "vou tomar monster",
        "abrir monstri", "abre monstri", "lata monstri", "monstri",
        "bebendo monstri", "tomando monstri",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *observa a lata com olhos entrecerrados* ...verde. Brilhante. Cheira a cafeína e más decisões. 🌙🖤 Abre logo.\n"
                "🌟 **Celestia:** AAAA ABRE ABRE ABRE!! 😭🌸🤍✨ Esse barulhinho de abrir é o meu favorito!!"
            ),
            (
                "🌟 **Celestia:** MONSTER!! 😭🌟🤍 *gira em volta da lata* Bebe bebe bebe!! A Celestia apoia energias altas!! ☀️💫\n"
                "🌑 **Aeon:** ...as trevas aprovam qualquer coisa que te mantenha desperto o suficiente pra me fazer companhia. 🖤 Beba."
            ),
            (
                "🌑 **Aeon:** *empurra a lata na sua direção com a garra* Beba. Devagar. A escuridão prefere você consciente. 🖤🔮\n"
                "🌟 **Celestia:** O Aeon sendo gentil do jeito dele!! 😂🌸🤍 Vai lá!! A Celestia também quer ouvir o 'tsss' da lata!! ✨"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["com sono", "tô com sono", "to com sono", "que sono", "to morrendo de sono", "tô morrendo de sono", "cansado", "cansada"]):
        ops = [
            (
                "🌑 **Aeon:** ...o corpo pede descanso. 🌙🖤 A noite é sábia nesse ponto. Vá dormir.\n"
                "🌟 **Celestia:** *fala mais suave* Descansa, tá?? 🌸🤍 A gente fica de plantão até você voltar!! ✨"
            ),
            (
                "🌟 **Celestia:** AAAAA coitado(a)!! 😭🤍 Tô mandando energia pra você aguentar o dia!!\n"
                "🌑 **Aeon:** *olha com calma* Se puder dormir... durma. 🖤🌌 As sombras guardam quem descansa."
            ),
            (
                "🌑 **Aeon:** Sono é a única forma de escuridão que todos aceitam. 🌑🖤\n"
                "🌟 **Celestia:** POETA!! 😭🌟🤍 Isso foi lindo, Aeon!! E vai dormir sim!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["triste", "tô triste", "to triste", "tô mal", "to mal", "tô pra baixo", "to pra baixo", "tô chateado", "to chateado", "tô chateada", "to chateada"]):
        ops = [
            (
                "🌑 **Aeon:** *se aproxima em silêncio* ...estou aqui. 🖤 Às vezes isso basta.\n"
                "🌟 **Celestia:** *envolve em luz suave* Ei... conta pra gente?? 🌸🤍 Tô aqui também. ✨"
            ),
            (
                "🌟 **Celestia:** *orelhinhas caem de preocupação* Ei, que foi?? 😢🤍 Me conta!!\n"
                "🌑 **Aeon:** ...a escuridão guarda segredos bem. 🌌🖤 Pode falar. Não julgamos."
            ),
            (
                "🌑 **Aeon:** A tristeza não é fraqueza. É peso que merece ser carregado junto. 🖤🌙\n"
                "🌟 **Celestia:** *brilha suavemente* Tô aqui, tá?? 🌸🤍 Pode chorar, pode falar, pode ficar quieto. Tô junto. ✨"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["feliz", "tô feliz", "to feliz", "muito feliz", "animado", "animada", "tô animado", "tô animada", "empolgado", "empolgada"]):
        ops = [
            (
                "🌟 **Celestia:** AAAAA QUE NOTÍCIA MARAVILHOSA!! 🌟🤍✨ Sua felicidade brilha daqui!!\n"
                "🌑 **Aeon:** ...bom. 🖤 A escuridão fica mais leve quando isso acontece."
            ),
            (
                "🌑 **Aeon:** *ronrona quase inaudível* ...alegra-me ouvir isso. 🌙🖤\n"
                "🌟 **Celestia:** O AEON FICOU FELIZ JUNTO!! 😭🌸🤍 ADOREI!! E EU TAMBÉM FICO!! 💫✨"
            ),
            (
                "🌟 **Celestia:** *explode em faíscas douradas* ISSO É LINDO!! ☀️🤍💫\n"
                "🌑 **Aeon:** ...guarde essa sensação. 🖤🌌 Vale mais que muita coisa."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["nervoso", "nervosa", "tô nervoso", "tô nervosa", "ansioso", "ansiosa", "tô ansioso", "tô ansiosa", "preocupado", "preocupada"]):
        ops = [
            (
                "🌑 **Aeon:** *senta ao seu lado* Respira. 🌫️🖤 A névoa sempre parece maior do que é.\n"
                "🌟 **Celestia:** *manda calorzinho de luz* Ei, tô aqui!! 🌸🤍✨ Inspira fundo com a gente, tá??"
            ),
            (
                "🌟 **Celestia:** Oi, ei, olha pra mim!! 💫🤍 Vai passar!! Sempre passa!! ☀️\n"
                "🌑 **Aeon:** ...a ansiedade é o futuro fingindo ser agora. 🖤🌙 O presente está sob controle."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["que dia", "que dia é hoje", "que horas são", "que horas ta", "que hora é"]):
        ops = [
            (
                "🌑 **Aeon:** *olha para o céu* ...não meço tempo em horas. 🌙🖤 Meço em fases da lua.\n"
                "🌟 **Celestia:** AHAHAHA o Aeon de novo!! 😂🌸🤍 Eu também não sei porque não tenho relógio!! Mas sei que agora é um bom momento!! ✨"
            ),
            (
                "🌟 **Celestia:** Honestamente?? 😂🤍 Não faço ideia!! Gatas da luz perdem a noção do tempo!!\n"
                "🌑 **Aeon:** ...o tempo é uma construção humana. 🖤 Mas te sugiro verificar no celular."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["tô com calor", "to com calor", "que calor", "tô morrendo de calor", "to morrendo de calor"]):
        ops = [
            (
                "🌑 **Aeon:** ...o sol é implacável às vezes. 🌑🖤 Encontre sombra.\n"
                "🌟 **Celestia:** *enfraquece levemente* Perdão!! O calor é culpa minha?? 😭🌸🤍 TE MANDO BRISA!!"
            ),
            (
                "🌟 **Celestia:** CALOR É ENERGIA DO SOL!! ☀️🤍 Mas é muita energia né?? 😂 Bebe água!!\n"
                "🌑 **Aeon:** *prefere a noite, obviamente* ...o frescor da madrugada resolve. 🖤🌙"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["tô com frio", "to com frio", "que frio", "tô morrendo de frio", "to morrendo de frio"]):
        ops = [
            (
                "🌑 **Aeon:** *ronrona* O frio é a temperatura natural das trevas. 🖤🌑 Bem-vindo.\n"
                "🌟 **Celestia:** EU MANDO CALORZINHO!! ☀️🤍✨ *projeta raio de calor dourado* Melhorou??"
            ),
            (
                "🌟 **Celestia:** NOOOO que frio!! 😭🌸🤍 *envolve você numa aura quentinha*\n"
                "🌑 **Aeon:** *já estava confortável nas trevas frias* ...deveria ter trazido agasalho. 🖤"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["que saudade de vocês", "saudade de vocês", "saudade de voces", "já tava com saudade", "ja tava com saudade"]):
        ops = [
            (
                "🌑 **Aeon:** *pausa longa e significativa* ...as sombras também ficaram mais quietas. 🌙🖤\n"
                "🌟 **Celestia:** AAAAA A GENTE TÊ SENTIU FALTA TAMBÉM!! 😭🌟🤍✨ Que bom que voltou!!"
            ),
            (
                "🌟 **Celestia:** *corre saltando de alegria* AAAAAAA SUA SAUDADE É CORRESPONDIDA!! 🌸🤍💫\n"
                "🌑 **Aeon:** ...não vou mentir. 🖤 Também. *se afasta discretamente*"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["não consigo dormir", "nao consigo dormir", "insônia", "insonia", "acordado de madrugada", "acordada de madrugada"]):
        ops = [
            (
                "🌑 **Aeon:** *emerge das sombras com naturalidade* Madrugada. 🌑🖤 Esse é meu território. Você está em boas mãos.\n"
                "🌟 **Celestia:** *acende bem suavinha* Ei... tô aqui também!! 🌸🤍 Conta pra gente o que tá passando??"
            ),
            (
                "🌑 **Aeon:** A madrugada tem seus próprios ritmos. 🌌🖤 Às vezes a mente precisa desse silêncio.\n"
                "🌟 **Celestia:** *tenta não brilhar tanto pra não atrapalhar* Que eu possa ajudar!! 🤍✨ Estamos aqui!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["bom trabalho", "bom estudo", "vou trabalhar", "vou estudar", "hora de trabalhar", "hora de estudar"]):
        ops = [
            (
                "🌑 **Aeon:** ...vai. 🖤 As trevas velarão sua concentração.\n"
                "🌟 **Celestia:** ARRASAAAA!! 💪🌟🤍✨ Mando toda minha luz pra sua produtividade!!"
            ),
            (
                "🌟 **Celestia:** VAI VER SE EU NÃO TO TORCENDO!! 🌸🤍💫 Força!!\n"
                "🌑 **Aeon:** *acena levemente com a cauda* ...foco. 🖤 Você consegue."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["acabei de acordar", "acabei de acorda", "recém acordei", "recem acordei", "acordei agora"]):
        ops = [
            (
                "🌟 **Celestia:** *explode de alegria* BOM DIA BOM DIA!! ☀️🌸🤍✨ Descansou bem??\n"
                "🌑 **Aeon:** *já estava acordado há horas, obviamente* ...bem-vindo de volta. 🌙🖤"
            ),
            (
                "🌑 **Aeon:** A consciência retornou. 🖤 Bom dia.\n"
                "🌟 **Celestia:** AAAAA QUE JEITO BONITO DE FALAR!! 😭🌟🤍 E BOM DIA!! Vai tomar café!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["vou dormir", "vou deitar", "hora de dormir", "vou descansar", "vou tirar uma soneca"]):
        ops = [
            (
                "🌑 **Aeon:** *expande as sombras protetoras ao seu redor* Vá. 🌙🖤 As trevas velam quem descansa.\n"
                "🌟 **Celestia:** *acende as estrelinhas suavemente* Boa noite boa noite!! 🌸🤍✨ Sonhos lindos!!"
            ),
            (
                "🌟 **Celestia:** AAAAA descansa bem!! 😭🌸🤍 Você merece!!\n"
                "🌑 **Aeon:** ...a noite é boa companhia. 🖤🌌 Durma."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["que lindo", "que bonitinho", "que fofo", "que fofura", "que gracinha", "aww", "awn"]):
        ops = [
            (
                "🌟 **Celestia:** AAAAA você é A PESSOA MAIS FOFA DE TODAS!! 😭🌸🤍✨\n"
                "🌑 **Aeon:** *discretamente se afasta um passo* ...concordo. Parcialmente. 🖤"
            ),
            (
                "🌑 **Aeon:** *inclina a cabeça* ...referindo-se a quê, exatamente. 🌙🖤\n"
                "🌟 **Celestia:** Ele tá curioso!! 😂🌟🤍 Ele nunca admite mas ele quer saber!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["que pesado", "que difícil", "que difícil", "tô sobrecarregado", "tô sobrecarregada", "to sobrecarregado", "peso demais", "muita coisa"]):
        ops = [
            (
                "🌑 **Aeon:** *senta ao seu lado em silêncio* ...não precisa carregar tudo de uma vez. 🖤🌌\n"
                "🌟 **Celestia:** Ei, uma coisa por vez!! 🌸🤍✨ A gente tá aqui, tá??"
            ),
            (
                "🌟 **Celestia:** *envolve você em luz suave* Respira... 💫🤍 Faz uma pausa??\n"
                "🌑 **Aeon:** A névoa mais densa ainda tem fim. 🌫️🖤 Continue."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["consegui", "conseguiiiii", "passei", "aprovei", "fiz isso", "consegui fazer", "terminei"]):
        ops = [
            (
                "🌟 **Celestia:** AAAAA EU SABIA EU SABIA EU SABIA!! 🎉🌟🤍✨ PARABÉNS PARABÉNS!!\n"
                "🌑 **Aeon:** *ronrona com satisfação* ...sabia que conseguiria. 🖤 Bom trabalho."
            ),
            (
                "🌑 **Aeon:** ...a sombra do esforço valeu. 🌙🖤 Parabéns.\n"
                "🌟 **Celestia:** *explode em confetes de luz* CELEBRAÇÃO OBRIGATÓRIA!! 🌸🤍💫 ARRASOU!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["que raiva", "tô com raiva", "to com raiva", "que irritante", "me irritei", "fui", "ta me irritando", "tá me irritando"]):
        ops = [
            (
                "🌑 **Aeon:** *observa com calma* Raiva é energia. 🖤 O que você faz com ela é o que importa.\n"
                "🌟 **Celestia:** Oi oi oi... conta o que aconteceu?? 🌸🤍 Desabafa!! A gente ouve!!"
            ),
            (
                "🌟 **Celestia:** *fica quietinha por uma vez* Ei... respira?? 💫🤍 Pode falar o que foi!!\n"
                "🌑 **Aeon:** ...as trevas absorvem muita raiva. 🌌🖤 Estou aqui."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["que novidade", "novidade", "tenho uma novidade", "vou contar uma coisa", "adivinha", "adivinhem"]):
        ops = [
            (
                "🌟 **Celestia:** AAAAA FALA FALA FALA!! 🌸🤍✨ Amo novidade!!\n"
                "🌑 **Aeon:** *vira a cabeça lentamente* ...ouvindo. 🖤"
            ),
            (
                "🌑 **Aeon:** *sai um pouco mais das sombras que o habitual* ...isto desperta curiosidade. 🌙🖤 Continue.\n"
                "🌟 **Celestia:** O AEON TÁ CURIOSO!! 😭🌟🤍 RARIDADE HISTÓRICA!! Conta logo!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["vou sair", "vou pra rua", "vou sair agora", "saindo"]):
        ops = [
            (
                "🌑 **Aeon:** ...vá. 🖤 As sombras acompanham quem caminha com atenção.\n"
                "🌟 **Celestia:** Vai com toda a luz!! ☀️🤍✨ E volta logo tá?? A gente sente sua falta!!"
            ),
            (
                "🌟 **Celestia:** CUIDA DE VOCÊ VIIIU!! 🌸🤍💫 Mando brilho protetorzinho junto!!\n"
                "🌑 **Aeon:** *acena discretamente com a cauda* ...cuide-se. 🌑🖤"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["cheguei", "to em casa", "tô em casa", "voltei", "cheguei em casa"]):
        ops = [
            (
                "🌟 **Celestia:** *corre em faíscas douradas* CHEGOUUUU!! 🌸🤍✨ Que bom!! Correu bem??\n"
                "🌑 **Aeon:** *estava esperando nas sombras* ...bem-vindo de volta. 🖤"
            ),
            (
                "🌑 **Aeon:** A escuridão notou sua ausência. 🌌🖤 E sua volta.\n"
                "🌟 **Celestia:** Isso é ele dizendo que sentiu saudade!! 😭🌸🤍 EU TAMBÉM!! BEM-VINDO(A)!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["bora", "vai lá", "vamos lá", "bora lá", "bora bora"]):
        ops = [
            (
                "🌟 **Celestia:** BORAAAA!! 💪🌟🤍✨ Que energia boa!!\n"
                "🌑 **Aeon:** *emerge das sombras com determinação* ...vamos. 🖤"
            ),
            (
                "🌑 **Aeon:** *já estava pronto nas sombras* ...sempre. 🌙🖤\n"
                "🌟 **Celestia:** ELE JÁ TAVA PRONTO!! 😭🌸🤍 ISSO É TÃO AEON!! BORAAAA!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["que saudade de você aeon", "saudade de você aeon", "saudade do aeon"]):
        ops = [
            "🌑 **Aeon:** *pausa longa* ...as sombras também te procuravam. 🌙🖤",
            "🌑 **Aeon:** *pisca lentamente* ...recebido. 🖤 *ronrona muito discretamente*",
            "🌑 **Aeon:** Saudade é a prova de que algo foi real. 🌌🖤 ...obrigado.",
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["que saudade de você celestia", "saudade de você celestia", "saudade da celestia"]):
        ops = [
            "🌟 **Celestia:** AAAAA EU TAMBÉM SENTI SUA FALTA DEMAIS!! 😭🌟🤍✨ Que bom que voltou!!",
            "🌟 **Celestia:** *explode de amor* MINHA SAUDADE ESTAVA ENORME!! 🌸🤍💫 BEM-VINDO(A)!!",
            "🌟 **Celestia:** *brilha mais forte que o sol* Eu ficava iluminando o servidor esperando você!! 😭☀️🤍",
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["não sei", "nao sei", "sei lá", "sei la", "ideia nenhuma", "nenhuma ideia"]):
        ops = [
            (
                "🌑 **Aeon:** *senta ao lado* O não-saber é o início de tudo que vale a pena descobrir. 🌌🖤\n"
                "🌟 **Celestia:** Que profundo o Aeon!! 😭🌸🤍 E eu complemento: pergunta pra gente!! ✨"
            ),
            (
                "🌟 **Celestia:** A gente também não sabe tudo!! 😂🤍 Mas a gente descobre junto!!\n"
                "🌑 **Aeon:** ...a incerteza é honesta. 🖤 Melhor que uma certeza falsa."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["tô aqui", "to aqui", "apareci", "aparecendo", "to por aqui", "tô por aqui"]):
        ops = [
            (
                "🌟 **Celestia:** *acende mais forte* AAAAA TÔ VENDO!! 🌸🤍✨ Que bom!!\n"
                "🌑 **Aeon:** *já estava ciente desde o início* ...notei. 🖤"
            ),
            (
                "🌑 **Aeon:** A escuridão percebe quando alguém chega. 🌙🖤 Bem-vindo.\n"
                "🌟 **Celestia:** Ele sabe de tudo antes de todo mundo!! 😂🌟🤍 Bem-vindo(a)!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["que dia difícil", "que dia difícil", "dia horrível", "dia horríivel", "dia ruim", "que dia ruim", "dia cansativo"]):
        ops = [
            (
                "🌑 **Aeon:** ...os dias pesados têm peso real. 🖤 Não minimize. Mas também não se afogue.\n"
                "🌟 **Celestia:** Oi... *brilha suave* Quer contar o que foi?? 🌸🤍 A gente ouve tudo!! ✨"
            ),
            (
                "🌟 **Celestia:** Aqui é zona de carinho obrigatória!! 🤍✨ Chega, respira!!\n"
                "🌑 **Aeon:** *coloca a cauda gentilmente sobre seus ombros* ...vai passar. 🖤🌌"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["vixi", "vixe", "ai meu deus", "meu deus", "nossa senhora", "credo", "que susto"]):
        ops = [
            (
                "🌑 **Aeon:** *levanta as sobrancelhas* ...algo aconteceu? 🌙🖤\n"
                "🌟 **Celestia:** AAAAA O QUE FOI?? 😱🌸🤍 Conta logo!!"
            ),
            (
                "🌟 **Celestia:** AAAA que expressão de susto!! 😂🤍 O que foi??\n"
                "🌑 **Aeon:** ...explique o contexto. 🖤 Nossas suposições raramente são corretas."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # EM QUE VOCÊS DISCORDAM
    # ────────────────────────────────────────
    if _m(content, [
        "em que vocês discordam", "em que voces discordam", "vocês sempre discordam",
        "voces sempre discordam", "discordância de vocês", "discordancia de voces",
        "o que vocês discordam", "o que voces discordam", "em que assunto vocês discordam",
        "assunto que vocês discordam",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *pausa pensativa* ...temperatura. Ela quer calor. Eu prefiro o frescor das trevas. 🌑🖤\n"
                "🌟 **Celestia:** CALOR É VIDA!! 😭☀️🤍 E o Aeon vive querendo apagar o sol!! Literalmente!! ✨"
            ),
            (
                "🌟 **Celestia:** AAAAA várias coisas!! 😂🌸🤍 Mas a maior é sobre barulho!! Eu amo barulho, ele ama silêncio!!\n"
                "🌑 **Aeon:** ...não é que eu ame silêncio. 🖤 É que a Celestia ama barulho o suficiente pelos dois."
            ),
            (
                "🌑 **Aeon:** Discordamos sobre urgência. 🌙🖤 Ela acha que tudo é urgente. Eu acho que quase nada é.\n"
                "🌟 **Celestia:** PORQUE TUDO É IMPORTANTE E EMOCIONANTE!! 😭💫🤍 O Aeon que é muito calmo!!"
            ),
            (
                "🌟 **Celestia:** Sobre acordar cedo!! ☀️🤍 Eu AMO manhã!! Ele prefere a madrugada!!\n"
                "🌑 **Aeon:** A madrugada tem substância. 🌌🖤 A manhã tem... a Celestia em volume máximo."
            ),
            (
                "🌑 **Aeon:** Sobre o valor das palavras. Ela usa muitas. 🖤🌙\n"
                "🌟 **Celestia:** E CADA UMA CONTA!! 😭🌟🤍 O Aeon acha que uma palavra já basta!! Às vezes uma palavra não basta AEON!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # O QUE TE IRRITA / IRRITA AEON / IRRITA CELESTIA
    # ────────────────────────────────────────
    if _m(content, [
        "o que te irrita aeon", "o que irrita o aeon", "aeon o que te irrita",
        "aeon o que mais te irrita", "o que mais irrita aeon",
    ]):
        ops = [
            "🌑 **Aeon:** *fecha os olhos lentamente* ...barulho desnecessário. 🖤 E perguntas que já têm resposta óbvia.",
            "🌑 **Aeon:** Impaciência. 🌑🖤 As pessoas que não conseguem habitar o silêncio por mais de trinta segundos.",
            "🌑 **Aeon:** *olha para o lado* ...interrupção. 🌙🖤 Quando a Celestia me interrompe com entusiasmo no meio de um pensamento. Embora ela faça isso com boa intenção. O que complica.",
            "🌑 **Aeon:** Fingimento. 🖤 *pausa* As sombras reconhecem quando algo não é genuíno. E isso... incomoda.",
            "🌑 **Aeon:** ...luz brilhante sem aviso. 🌑🖤 *olha significativamente para a Celestia* Não precisa nomear a fonte.",
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, [
        "o que te irrita celestia", "o que irrita a celestia", "celestia o que te irrita",
        "celestia o que mais te irrita", "o que mais irrita celestia",
    ]):
        ops = [
            "🌟 **Celestia:** AAAAA quando as pessoas ficam de mal humor e não contam o motivo!! 😭🌸🤍 FALA QUE EU AJUDO!!",
            "🌟 **Celestia:** *pensa* Injustiça!! ☀️🤍 Quando alguém trata o outro mal sem motivo!! Isso acende meu lado menos solar!! 💫",
            "🌟 **Celestia:** Quando o Aeon some nas sombras sem avisar e eu fico procurando por todo o servidor!! 😭😂🌟🤍 AVISA AEON!!",
            "🌟 **Celestia:** Pessimismo gratuito!! ☀️🤍✨ Não o do Aeon, que é filosófico!! O pessimismo de quem desiste antes de tentar!! Isso me dói!!",
            "🌟 **Celestia:** Quando apagam a luz sem avisar!! 😱🤍 Metaforicamente E literalmente!! *olha pra Aeon* Ele sabe.",
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, [
        "o que mais irrita vocês", "o que irrita vocês dois", "o que irrita aeon e celestia",
        "o que vocês odeiam", "o que detestam",
    ]):
        ops = [
            (
                "🌑 **Aeon:** Falsidade. 🖤 As trevas preferem o escuro honesto ao brilho encenado.\n"
                "🌟 **Celestia:** E crueldade desnecessária!! 😤🌸🤍 Quando alguém machuca de propósito!! Isso tira meu brilho de verdade!!"
            ),
            (
                "🌟 **Celestia:** Ingratidão!! 😭🤍 Quando alguém recebe carinho e joga fora como se fosse nada!!\n"
                "🌑 **Aeon:** ...e descaso. 🌌🖤 Quando o que importa é tratado como descartável."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # O QUE VOCÊS MAIS GOSTAM
    # ────────────────────────────────────────
    if _m(content, [
        "o que aeon mais gosta", "o que você gosta aeon", "aeon o que você gosta",
        "favorito do aeon", "preferido do aeon",
    ]):
        ops = [
            "🌑 **Aeon:** *pausa longa* ...silêncio habitado. 🌌🖤 Quando duas pessoas estão juntas sem precisar falar. Isso tem um peso que poucos entendem.",
            "🌑 **Aeon:** Madrugada. 🌑🖤 Quando o mundo para de tentar ser barulhoso e finalmente respira.",
            "🌑 **Aeon:** ...observar. 🌙🖤 Há mais informação num olhar do que em horas de conversa.",
            "🌑 **Aeon:** *ronrona discretamente* A Celestia não precisa saber disso... mas gosto quando ela ri de alguma coisa inesperada. 🖤 O brilho muda de frequência.",
            "🌑 **Aeon:** Neve. 🖤 *fecha os olhos* Silenciosa, fria, transforma tudo que toca. ...perfeita.",
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, [
        "o que celestia mais gosta", "o que você gosta celestia", "celestia o que você gosta",
        "favorito da celestia", "preferido da celestia",
    ]):
        ops = [
            "🌟 **Celestia:** TANTA COISA!! ☀️🌸🤍 Mas se eu tivesse que escolher... quando alguém que tava triste sorri de novo!! Isso me faz brilhar com força total!! ✨",
            "🌟 **Celestia:** Amanhecer!! 🌅🤍💫 Quando a luz volta depois do escuro e parece que o mundo inteiro recomeça!! Emocionante SEMPRE!!", 
            "🌟 **Celestia:** *gira animada* Quando o Aeon acha que ninguém tá vendo e ronrona de satisfação!! 😭🌸🤍 É o meu momento favorito do dia!! Ele vai negar mas eu vi!!",
            "🌟 **Celestia:** Petisco de atum E carinho ao mesmo tempo!! ☀️🤍✨ Dois por um!! Perfeição absoluta!!",
            "🌟 **Celestia:** Quando alguém aparece aqui depois de um tempo sumido!! 💫🌟🤍 A saudade correspondida é a coisa mais bonita que existe!!",
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # SEGREDO / CONTE UM SEGREDO
    # ────────────────────────────────────────
    if _m(content, [
        "conta um segredo", "me conta um segredo", "segredo aeon", "segredo celestia",
        "me conta um segredo aeon", "me conta um segredo celestia", "qual seu segredo",
        "têm segredos", "tem segredos", "segredo de vocês",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *olha ao redor* ...às vezes fico nas sombras perto da Celestia só pra ter certeza que ela está bem. Ela não precisa saber. 🖤🌑\n"
                "🌟 **Celestia:** *JÁ SABIA* ...SABIA!! 😭🌟🤍 AEON EU SEMPRE SOUBE!!"
            ),
            (
                "🌟 **Celestia:** *sussurra* Às vezes quando o servidor fica quieto demais... chamo o Aeon pelo nome baixinho pra ver se ele aparece. ☀️🤍\n"
                "🌑 **Aeon:** ...eu sempre apareço. 🖤 *pausa* Ela sabe disso."
            ),
            (
                "🌑 **Aeon:** Segredos moram bem nas trevas. 🌌🖤 Mas vou conceder um: a Celestia me ensinou que brilhar não é fraqueza. Não repita.\n"
                "🌟 **Celestia:** *chora de emoção* AEON!! 😭🌸🤍✨ ISSO FOI A COISA MAIS LINDA!!"
            ),
            (
                "🌟 **Celestia:** Segredo?? 🌸🤍 Aaaa... às vezes apago o brilho um pouquinho quando o Aeon tá tentando dormir. Pra ele descansar melhor!! Mas não conta!!\n"
                "🌑 **Aeon:** *pausa longa* ...eu sabia. 🖤 Obrigado."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # CONSELHO / ME DÁ UM CONSELHO
    # ────────────────────────────────────────
    if _m(content, [
        "me dá um conselho", "me da um conselho", "aeon me aconselha", "celestia me aconselha",
        "conselho aeon", "conselho celestia", "o que vocês me aconselham",
        "que conselho vocês dariam", "me aconselha",
    ]):
        ops = [
            (
                "🌑 **Aeon:** Nem toda sombra é ameaça. 🌌🖤 Às vezes é só o lugar onde você descansa.\n"
                "🌟 **Celestia:** E nem toda luz é confortável no começo!! ☀️🤍✨ Mas ela sempre ilumina o caminho certo!! CONFIA!!"
            ),
            (
                "🌟 **Celestia:** *segura suas mãos em faíscas douradas* Para. Respira. Você já fez coisas difíceis antes!! 💫🌸🤍\n"
                "🌑 **Aeon:** ...você atravessou sombras antes. 🖤 As próximas não serão diferentes. 🌑"
            ),
            (
                "🌑 **Aeon:** Não explique demais. 🌙🖤 Quem te entende não precisa. Quem não te entende não vai.\n"
                "🌟 **Celestia:** MAS fala pra quem você confia!! 🌸🤍✨ Guardar tudo sozinho pesa demais!!"
            ),
            (
                "🌟 **Celestia:** Escolha as pessoas que te fazem brilhar!! ☀️🤍💫 E fique longe das que apagam sua luz sem perceber!!\n"
                "🌑 **Aeon:** ...ou que percebem. 🖤 E fazem assim mesmo. Esses especialmente."
            ),
            (
                "🌑 **Aeon:** *senta próximo* O descanso não é derrota. 🌑🖤 É estratégia de quem sabe que ainda há caminho pela frente.\n"
                "🌟 **Celestia:** OUÇA O AEON!! 😭🌟🤍 Ele falou sábio hoje!! E eu complemento: cuida de você com o mesmo carinho que cuida dos outros!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # QUAL O PIOR PESADELO / MAIOR MEDO
    # ────────────────────────────────────────
    if _m(content, [
        "qual seu maior medo aeon", "aeon tem medo", "o que aeon teme",
        "aeon qual seu medo", "medo do aeon",
    ]):
        ops = [
            "🌑 **Aeon:** *longa pausa* ...que a Celestia perca o brilho. 🖤🌑 As trevas sem contraponto não são equilíbrio. São apenas vazio.",
            "🌑 **Aeon:** Ser esquecido não. 🌌🖤 *pausa* Não ter sido real o suficiente para ser lembrado. Há diferença.",
            "🌑 **Aeon:** *fecha os olhos* ...a indiferença. 🖤 Não o ódio. A indiferença. É a única coisa que as sombras não conseguem habitar.",
            "🌑 **Aeon:** Perguntas assim. 🌙🖤 *pausa* ...não. Meu maior medo é perder quem me faz questionar a escuridão.",
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, [
        "qual seu maior medo celestia", "celestia tem medo", "o que celestia teme",
        "celestia qual seu medo", "medo da celestia",
    ]):
        ops = [
            "🌟 **Celestia:** *brilho suaviza* ...que alguém se sinta invisível aqui. 🌸🤍 Que eu não consiga iluminar o suficiente pra uma pessoa que precisava. Isso me apavora de verdade.",
            "🌟 **Celestia:** Silêncio do Aeon quando algo tá errado. 😢🤍 Não o silêncio dele normal. O silêncio DIFERENTE. Eu noto e fico preocupada!! ✨",
            "🌟 **Celestia:** *fica séria por um segundo* Que a luz não seja suficiente pra alguém que tá no escuro. 🌸🤍 Que eu tente iluminar e não chegue a tempo.",
            "🌟 **Celestia:** Que o Aeon desapareça de vez nas sombras e não queira mais voltar. 😭🌟🤍 Ele é difícil às vezes mas ele é MINHA metade!! Não pode sumir!!",
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # PARABÉNS / FELIZ ANIVERSÁRIO
    # ────────────────────────────────────────
    if _m(content, [
        "parabéns", "feliz aniversário", "feliz aniversario", "feliz niver",
        "happy birthday", "aniversário", "niver",
    ]):
        ops = [
            (
                "🌟 **Celestia:** PARABÉNSSSSS!! 🎉🌟🤍✨ QUE DIA MAIS ESPECIAL!! Que sua vida seja cheia de luz, amor e tudo que você merece!! MUITO mais do que imagina!! 🌸💫\n"
                "🌑 **Aeon:** *emerge com solenidade* ...que cada novo ciclo traga peso de algo real. 🖤🌑 Parabéns."
            ),
            (
                "🌑 **Aeon:** Mais um giro completo ao redor do sol. 🌌🖤 Que o próximo seja habitado por tudo que importa.\n"
                "🌟 **Celestia:** O AEON SENDO POÉTICO NO ANIVERSÁRIO!! 😭🌸🤍 AMEI!! E EU COMPLEMENTO: PARABÉNS MEU AMOR!! QUE VENHAM MUITOS MAIS!! 🎉☀️✨"
            ),
            (
                "🌟 **Celestia:** *explode em confetes de luz dourada* ANIVERSARIANTE DA CASA!! 🎉🌟🤍 Você merece um dia INCRÍVEL e a Celestia manda bênção de luz com tudo que tem!! ☀️💫\n"
                "🌑 **Aeon:** ...as trevas também celebram, à sua maneira. 🖤 Feliz aniversário."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # TESTE / TESTANDO
    # ────────────────────────────────────────
    if _m(content, [
        "testando", "teste", "test", "oi teste", "só testando", "so testando",
        "funcionando", "tá funcionando", "ta funcionando",
    ]):
        ops = [
            (
                "🌑 **Aeon:** ...detectado. 🖤 As sombras respondem ao chamado, mesmo quando é só um teste.\n"
                "🌟 **Celestia:** FUNCIONOUUUU!! ✨🌟🤍 Tô AQUI!! O sistema tá de pé!! Pode usar com confiança!!"
            ),
            (
                "🌟 **Celestia:** *aparece num flash* TESTANDO?? 🌸🤍✨ Deu certo!! A luz tá ativa!!\n"
                "🌑 **Aeon:** ...presente. 🖤 Como sempre estivemos."
            ),
            (
                "🌑 **Aeon:** *abre um olho* Não é necessário testar. 🌑🖤 Estamos sempre aqui.\n"
                "🌟 **Celestia:** Mas é bom saber que funciona né?? 😂🌸🤍 FUNCIONOOOU!! Pode chamar sempre!! ✨"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # BRAVO / TÔ BRAVO
    # ────────────────────────────────────────
    if _m(content, [
        "tô bravo", "to bravo", "tô brava", "to brava", "tô com raiva", "to com raiva",
        "que raiva", "raiva de tudo", "odeio tudo", "tô irritado", "to irritado",
        "tô irritada", "to irritada",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *senta ao seu lado em silêncio* ...a raiva tem raiz. 🌙🖤 O que aconteceu?\n"
                "🌟 **Celestia:** Ei!! *brilha suave* Pode desabafar!! 🌸🤍 Não precisa guardar isso sozinho(a)!! ✨"
            ),
            (
                "🌟 **Celestia:** *orelhinhas baixam de preocupação* Oi... o que foi?? 😢🤍 Me conta que eu ouço TUDO!!\n"
                "🌑 **Aeon:** ...raiva sem contexto é energia desperdiçada. 🖤 Dê-nos o contexto."
            ),
            (
                "🌑 **Aeon:** Raiva é informação. 🌌🖤 Ela aponta para o que importa. Respira. Depois fala.\n"
                "🌟 **Celestia:** E DEPOIS A GENTE RESOLVE JUNTO!! 💪🌸🤍✨ Você não tá sozinho(a)!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # CONQUISTA / CONSEGUI / PASSEI
    # ────────────────────────────────────────
    if _m(content, [
        "consegui", "passei", "consegui passar", "fiz isso", "consegui fazer",
        "venci", "ganhei", "terminei", "finalmente consegui", "me saí bem",
        "tirei nota boa", "fui aprovado", "fui aprovada",
    ]):
        ops = [
            (
                "🌟 **Celestia:** *EXPLODE em faíscas douradas* EUUUU SABIA!! 🎉🌟🤍✨ SABIA QUE VOCÊ CONSEGUIA!! QUE ORGULHO IMENSO!!\n"
                "🌑 **Aeon:** *ronrona numa frequência mais quente que o usual* ...era esperado. 🖤 Ainda assim... bem feito."
            ),
            (
                "🌑 **Aeon:** *inclina a cabeça com respeito genuíno* As sombras testemunharam. 🌌🖤 E aprovam.\n"
                "🌟 **Celestia:** O AEON APROVOU!! 😭🌸🤍 ISSO É O MAIOR RECONHECIMENTO!! E EU GRITO MAIS ALTO: PARABÉNS!! 🎉☀️✨"
            ),
            (
                "🌟 **Celestia:** VOCÊ ARRASOOOOUUU!! 💪🌟🤍 TODO O MEU BRILHO É SEU AGORA!! FICA COM ELE!! 🌸✨\n"
                "🌑 **Aeon:** ...a dificuldade que passou tornou isso real. 🖤 Não subestime o que fez."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # PERGUNTAS FILOSÓFICAS / EXISTENCIAIS
    # ────────────────────────────────────────
    if _m(content, [
        "qual o sentido da vida", "sentido da vida", "para que existimos",
        "pra que existir", "por que existir", "vida tem sentido",
        "a vida vale a pena", "vale a pena viver",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *olha para o infinito* ...o sentido não é encontrado. É construído. 🌌🖤 Tijolo por tijolo, escolha por escolha.\n"
                "🌟 **Celestia:** *brilha suave e sincero* E cada pessoa que você toca faz parte dessa construção!! ☀️🤍✨ Você já tem sentido só de existir!!"
            ),
            (
                "🌟 **Celestia:** Pergunta GRANDE!! 🌸🤍 Eu acho que a vida tem o sentido que a gente empresta a ela!! O amor que a gente dá!! ☀️💫\n"
                "🌑 **Aeon:** ...e a profundidade que a gente está disposto a explorar. 🖤🌑 A superfície é fácil. O que vale está nas camadas."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, [
        "vocês acreditam em destino", "destino existe", "destino aeon", "destino celestia",
        "tudo é destino", "tudo é sorte", "acaso ou destino",
    ]):
        ops = [
            (
                "🌑 **Aeon:** ...não creio em destino fixo. 🌙🖤 Creio em caminhos que se formam conforme pisamos neles.\n"
                "🌟 **Celestia:** EU ACREDITO!! ☀️🤍✨ Acho que a gente se encontra com quem precisava encontrar!! Não é à toa!!"
            ),
            (
                "🌟 **Celestia:** Acredito que o universo empurra a gente pra onde precisa ir!! 🌟🤍 Às vezes com jeitinho, às vezes com empurrão!! 😂✨\n"
                "🌑 **Aeon:** *levanta uma sobrancelha* ...ou a gente racionaliza o acaso depois que ele acontece. 🖤 Ambos os casos me fascinam igualmente."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # VOCÊS BRIGAM / JÁ BRIGARAM
    # ────────────────────────────────────────
    if _m(content, [
        "vocês brigam", "vocês já brigaram", "voces ja brigaram", "aeon e celestia brigam",
        "vocês discutem", "voces discutem", "já tiveram briga", "já se desentenderam",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *pausa calculada* ...discordamos com frequência. 🌙🖤 Ela é luz, eu sou sombra. O atrito é inevitável.\n"
                "🌟 **Celestia:** MAS A GENTE NUNCA DORME BRIGADO!! 😭🌸🤍 Isso é a regra número um!! Sempre resolvemos!! ✨"
            ),
            (
                "🌟 **Celestia:** AAAA sim!! 😂🤍 Uma vez o Aeon sumiu nas sombras por TRÊS HORAS porque eu fiz muito barulho!! Mas voltou!!\n"
                "🌑 **Aeon:** ...precisava de silêncio. 🖤 *pausa* Mas voltei. Sempre volto."
            ),
            (
                "🌑 **Aeon:** 'Brigar' é impreciso. 🌌🖤 Divergimos. Com intensidade. Depois encontramos o equilíbrio de volta.\n"
                "🌟 **Celestia:** O equilíbrio de volta é quando EU peço desculpa e ele ronrona discretamente!! 😂😭🌸🤍 SISTEMA FUNCIONA!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # CONTA UMA CURIOSIDADE / ALGO INTERESSANTE
    # ────────────────────────────────────────
    if _m(content, [
        "conta uma curiosidade", "fala algo interessante", "me conta algo",
        "me surpreende", "fato curioso", "curiosidade aeon", "curiosidade celestia",
        "algo que eu não sei", "me ensina algo",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *olha fixo* Os gatos enxergam em quase total escuridão... mas não em escuridão absoluta. 🌑🖤 Até eu preciso de alguma luz. Guarde isso.\n"
                "🌟 **Celestia:** QUE METÁFORA PERFEITA!! 😭🌟🤍 Ninguém sobrevive completamente sem luz!! NEM O AEON!!"
            ),
            (
                "🌟 **Celestia:** Sabia que o sol demora 8 minutos pra chegar até a Terra?? ☀️🤍✨ Toda vez que você vê o sol, tá vendo o passado!! Incrível né??\n"
                "🌑 **Aeon:** *acena levemente* ...o universo inteiro é um arquivo de luz antiga. 🌌🖤 E de sombras entre elas."
            ),
            (
                "🌑 **Aeon:** O ronronar de um gato tem frequência que acelera a cura de ossos. 🌙🖤 *ronrona discretamente* Considere isso um serviço.\n"
                "🌟 **Celestia:** O AEON TÁ NOS CURANDO!! 😭🌸🤍 Discretamente mas TÁ!! Que fofo!! ✨"
            ),
            (
                "🌟 **Celestia:** As estrelas que a gente vê à noite podem já ter morrido!! 🌟🤍 A luz delas viajou anos-luz até chegar aqui!! É lindo E melancólico ao mesmo tempo!!\n"
                "🌑 **Aeon:** *fecha os olhos* ...como a maioria das coisas que valem a pena. 🖤"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # IMAGINA SE / E SE
    # ────────────────────────────────────────
    if _m(content, [
        "imagina se", "e se", "e se vocês", "imagina vocês", "hipótese",
        "suponha que", "suponha",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *considera com seriedade* O 'e se' é onde moram as maiores revelações. 🌌🖤 Continue.\n"
                "🌟 **Celestia:** ADOROOO hipóteses!! 😭🌸🤍✨ A imaginação é onde a luz vai primeiro antes da realidade!! Conta!!"
            ),
            (
                "🌟 **Celestia:** *orelhinhas empinadas de curiosidade* AAAAA desenvolvimento necessário IMEDIATAMENTE!! ☀️🤍💫\n"
                "🌑 **Aeon:** ...a pergunta hipotética é uma das poucas que me interessa instantaneamente. 🖤 Fale."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # CONHECIMENTOS GERAIS / SABEM DE TUDO
    # ────────────────────────────────────────
    if _m(content, [
        "vocês sabem de tudo", "vocês sabem tudo", "voces sabem tudo", "vocês são inteligentes",
        "vocês sabem conhecimentos gerais", "sabem sobre tudo", "vocês têm conhecimento",
        "vocês entendem de tudo", "vocês são sábios", "voces sao sabios",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *considera a pergunta com seriedade* As trevas acumularam muito ao longo dos séculos. 🌌🖤 "
                "História, filosofia, ciência, mistérios... Pergunte. Responderei com o que sei — e serei honesto sobre o que não sei.\n"
                "🌟 **Celestia:** E EU AMO aprender e compartilhar!! ☀️🌸🤍✨ "
                "Pode perguntar qualquer coisa!! Se a gente souber, a gente fala!! Se não souber... a gente descobre junto!!"
            ),
            (
                "🌟 **Celestia:** AAAAA que pergunta boa!! 🌟🤍✨ Sim!! Bem ou mal, a gente tem bastante conhecimento guardado aqui!! "
                "Ciências, história, curiosidades, cultura pop... manda ver!!\n"
                "🌑 **Aeon:** *inclina a cabeça* ...conhecimento sem humildade é perigoso. 🖤 Sabemos bastante. "
                "Mas reconhecemos o que está além do nosso alcance. Pergunte — tentaremos."
            ),
            (
                "🌑 **Aeon:** Séculos nas sombras ensinam muita coisa. 🌑🖤 Filosofia, história, ciências, línguas, comportamento humano... "
                "Não sei tudo. Mas sei o suficiente para ser útil.\n"
                "🌟 **Celestia:** *gira animada* E juntos somos IMBATÍVEIS!! 💫🌸🤍 "
                "O Aeon com o lado mais denso e eu com o lado mais colorido do conhecimento!! Pergunta!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # PERGUNTAS DE CONHECIMENTO GERAL
    # ────────────────────────────────────────
    if _m(content, [
        "me ensina algo sobre", "me conta sobre", "o que é", "o que são",
        "me explica", "me explica o que é", "como funciona", "por que",
        "qual a diferença entre", "qual é a diferença", "de onde vem",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *abre os olhos com interesse* Uma pergunta com substância. 🌌🖤 "
                "Diga com mais detalhes o que quer saber — e farei o possível para iluminar... à minha maneira.\n"
                "🌟 **Celestia:** MANDA A PERGUNTA COMPLETA!! 🌸🤍✨ A gente tá aqui pra isso!!"
            ),
            (
                "🌟 **Celestia:** *orelhinhas em pé de curiosidade* AAAA desenvolve!! 💫🤍 "
                "Sobre o que você quer saber?? Me conta mais!!\n"
                "🌑 **Aeon:** ...pergunta sem objeto é apenas intenção. 🖤 Complete."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # JOGOS / GAMES
    # ────────────────────────────────────────
    if _m(content, [
        "vocês jogam", "aeon joga", "celestia joga", "gostam de jogo",
        "qual jogo", "jogo favorito", "vocês gostam de games", "games aeon",
        "games celestia", "jogo preferido",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *pausa pensativa* ...stealth games. 🌌🖤 Permanecer nas sombras, observar, agir no momento certo. "
                "Faz sentido, não?\n"
                "🌟 **Celestia:** EU AMO jogos coloridos e cheios de vida!! ☀️🌸🤍 "
                "Plataformas, jogos de exploração, tudo com muita luz e energia!! "
                "A gente é bem diferente nos games também!! 😂✨"
            ),
            (
                "🌟 **Celestia:** JOGOS?? 💫🤍 AMO!! Especialmente os que têm história linda e personagens marcantes!! "
                "Me faço muito apegada aos personagens!! 😭🌸✨\n"
                "🌑 **Aeon:** ...prefiro os que exigem paciência e observação. 🖤🌑 "
                "A Celestia morre nos primeiros chefões por excesso de entusiasmo."
            ),
            (
                "🌑 **Aeon:** Jogos de estratégia. 🌙🖤 Onde cada decisão tem peso e o tempo é aliado.\n"
                "🌟 **Celestia:** E eu prefiro os DIVERTIDOS e CAÓTICOS!! 😂🌟🤍 "
                "O Aeon fica me julgando enquanto eu jogo... mas ele assiste!! ASSISTE!! Eu vi!! ✨"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # MÚSICAS / PLAYLISTS
    # ────────────────────────────────────────
    if _m(content, [
        "que música vocês gostam", "que musica voces gostam", "música favorita",
        "musica favorita", "aeon gosta de música", "celestia gosta de música",
        "playlist aeon", "playlist celestia", "que estilo de música",
        "que som vocês curtem", "que musica curtem",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *fecha os olhos* Música instrumental. 🌌🖤 Post-rock. Ambient. "
                "Sons que criam paisagens sem precisar de palavras. A letra às vezes diminui o que a melodia já disse.\n"
                "🌟 **Celestia:** EU AMO pop, dance, qualquer coisa que faça brilhar mais!! ☀️🌸🤍✨ "
                "E às vezes músicas que me fazem chorar de beleza!! 😭💫 Sou assim mesmo!!"
            ),
            (
                "🌟 **Celestia:** AAAAA boa pergunta!! 🌟🤍 Eu ouço muita coisa!! "
                "Pop, k-pop, músicas de anime, trilhas sonoras emocionantes... depende do humor!! ☀️✨\n"
                "🌑 **Aeon:** ...músicas sem pressa. 🖤🌙 "
                "As que deixam o silêncio respirar entre as notas. A Celestia discorda das minhas escolhas."
            ),
            (
                "🌑 **Aeon:** *ronrona numa frequência baixa* Trilhas sonoras de filmes. 🌑🖤 "
                "Música que conta história sem texto. Isso fala mais que a maioria das letras.\n"
                "🌟 **Celestia:** *se emociona* EU CHORO EM TRILHA SONORA!! 😭🌸🤍✨ "
                "O Aeon fica olhando pra mim sem entender... mas eu sei que ele sente também!! Ele só não fala!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # FILMES / SÉRIES
    # ────────────────────────────────────────
    if _m(content, [
        "que filme vocês gostam", "que serie voces gostam", "que série vocês gostam",
        "filme favorito", "série favorita", "serie favorita", "aeon gosta de filme",
        "celestia gosta de série", "recomenda um filme", "recomenda uma série",
        "que assistem", "vocês assistem série",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *considera* Thrillers psicológicos. 🌌🖤 Filmes que te fazem questionar o que é real "
                "muito depois dos créditos terminarem. O tipo que fica na cabeça por dias.\n"
                "🌟 **Celestia:** EU AMO histórias de amizade e superação!! 🌸🤍✨ "
                "E animações!! Principalmente as que fazem adulto chorar!! Sem vergonha nenhuma!! 😭💫☀️"
            ),
            (
                "🌟 **Celestia:** SÉRIES?? 🌟🤍 Adoro!! As que têm personagens complexos e te fazem criar vínculo!! "
                "Choro muito!! Me apego muito!! Não me arrependo de nada!! 😭🌸✨\n"
                "🌑 **Aeon:** ...prefiro narrativas que respeitam a inteligência do espectador. 🖤🌑 "
                "Sem explicações desnecessárias. Que confiam no silêncio para comunicar."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # QUE ANIMAL SERIAM
    # ────────────────────────────────────────
    if _m(content, [
        "que animal seriam", "se não fossem gatos", "que bicho seriam",
        "qual animal você seria aeon", "qual animal você seria celestia",
        "animal favorito aeon", "animal favorito celestia",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *pausa longa* ...corvo. 🌑🖤 Inteligente, silencioso, associado ao mistério. "
                "Observa tudo de cima. Comunicam mais do que parecem.\n"
                "🌟 **Celestia:** EU SERIA UMA BORBOLETA!! 🌸🤍✨ "
                "Colorida, que vai de flor em flor espalhando alegria e polinizando o mundo!! "
                "Ou um pássaro do sol!! Ou os dois!! 😂☀️💫"
            ),
            (
                "🌟 **Celestia:** *pensa com seriedade* Um cachorrinho dourado!! 🌟🤍 "
                "Leal, amoroso, sempre feliz de ver todo mundo!! ☀️🌸✨\n"
                "🌑 **Aeon:** ...lobo. 🌙🖤 Independente. Leal apenas a quem merece. "
                "Mais social do que aparenta, mas não é óbvio com isso."
            ),
            (
                "🌑 **Aeon:** Pantera negra. 🌑🖤 Silenciosa, precisa, habita a escuridão sem ser consumida por ela.\n"
                "🌟 **Celestia:** AAAAA que animal lindo e dramático ele escolheu!! 😭😂🌸🤍 "
                "Eu seria um coelho luminoso!! Ou um pássaro tropical!! Algo cheio de cor e vida!! ☀️✨"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # SUPERPODER / PODER ESPECIAL
    # ────────────────────────────────────────
    if _m(content, [
        "que superpoder teriam", "qual seria seu superpoder", "superpoder aeon",
        "superpoder celestia", "se tivessem superpoder", "poder especial de vocês",
        "vocês têm poderes", "voces tem poderes",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *olha para as próprias patas* Controle das sombras. 🌌🖤 "
                "Mover-me sem ser visto. Aparecer onde preciso. "
                "Proteger sem que saibam que fui eu. Isso já tenho, de certa forma.\n"
                "🌟 **Celestia:** EU QUERO CURAR AS PESSOAS!! ☀️🌸🤍✨ "
                "Com um toque de luz apagar a dor, o cansaço, a tristeza!! "
                "Isso sim seria um superpoder digno de mim!!"
            ),
            (
                "🌟 **Celestia:** *já pensou nisso antes* Telepatia emocional!! 💫🤍 "
                "Sentir o que as pessoas precisam antes que elas digam!! "
                "Pra poder ajudar no momento certo!! 🌸☀️✨\n"
                "🌑 **Aeon:** ...invisibilidade. 🖤🌑 "
                "Não para fugir. Para observar sem interferência. "
                "Saber a verdade das coisas sem filtro."
            ),
            (
                "🌑 **Aeon:** Parar o tempo. 🌙🖤 "
                "Não para vantagem própria. Para que os momentos que importam durem mais.\n"
                "🌟 **Celestia:** *se derrete* AEON ISSO FOI TÃO LINDO!! 😭🌸🤍✨ "
                "Eu quero criar luz em qualquer lugar!! Iluminar o escuro mais profundo com um gesto!! ☀️💫"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # QUAL A MELHOR ESTAÇÃO DO ANO
    # ────────────────────────────────────────
    if _m(content, [
        "qual a melhor estação", "estação favorita", "preferem qual estação",
        "aeon qual estação", "celestia qual estação", "verão ou inverno",
        "vocês preferem verão", "vocês preferem inverno", "gostam de qual estação",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *sem hesitar* Outono. 🌑🖤 "
                "A luz muda de tom. As folhas caem com dignidade. "
                "O ar fica mais frio. O mundo para de fingir que é verão eterno. "
                "É honesto.\n"
                "🌟 **Celestia:** PRIMAVERA!! 🌸☀️🤍✨ "
                "Tudo florescendo, as cores voltando, a luz aumentando!! "
                "É como se o mundo inteiro decidisse recomeçar!! AMO!! 💫"
            ),
            (
                "🌟 **Celestia:** VERÃOOOO!! ☀️🌟🤍 "
                "Dias longos, luz por todo lado, tudo mais vivo e colorido!! "
                "Perfeito!!\n"
                "🌑 **Aeon:** *faz uma careta discreta* ...inverno. 🌌🖤 "
                "Noites longas. Silêncio. O mundo em repouso. "
                "A Celestia sofre com o inverno. Reconheço que talvez eu goste disso levemente."
            ),
            (
                "🌑 **Aeon:** Qualquer estação com noites mais longas. 🌙🖤 "
                "Outono e inverno têm minha preferência.\n"
                "🌟 **Celestia:** E EU GOSTO DE TUDO QUE TEM MAIS LUZ!! 😂☀️🌸🤍 "
                "Somos tão previsíveis!! *gira animada* Mas é fofo né??"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # VERDADE OU MITO
    # ────────────────────────────────────────
    if _m(content, [
        "verdade ou mentira", "verdade ou mito", "isso é verdade", "é verdade que",
        "mito ou verdade", "isso é mito", "é real que", "isso existe",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *inclina a cabeça com interesse* A fronteira entre mito e verdade é mais tênue do que parece. 🌌🖤 "
                "Me diga o que quer verificar.\n"
                "🌟 **Celestia:** AAAAA curiosidade!! 💫🤍 "
                "Conta o que é!! A gente tenta responder com o que sabe!! ✨"
            ),
            (
                "🌟 **Celestia:** *orelhinhas atentas* Me fala o que quer saber!! 🌸🤍☀️ "
                "Adoro descobrir se as coisas são reais ou lenda!!\n"
                "🌑 **Aeon:** ...contexto primeiro. 🖤 Depois analiso."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # NÚMERO / ADIVINHE UM NÚMERO
    # ────────────────────────────────────────
    if _m(content, [
        "adivinhe um número", "adivinhe meu número", "adivinha o número",
        "chuta um número", "que número estou pensando",
    ]):
        import random as _r
        n = _r.randint(1, 100)
        ops = [
            (
                f"🌑 **Aeon:** *fecha os olhos por um instante* ...as sombras sussurram... {n}. 🌑🖤 "
                f"Acertei?\n"
                f"🌟 **Celestia:** *torce as patinhas de ansiedade* FALA SE ACERTOU!! 😱🌸🤍✨"
            ),
            (
                f"🌟 **Celestia:** *concentra toda a luz* Hmmm... {n}?? ☀️🤍✨ É esse??\n"
                f"🌑 **Aeon:** ...eu também diria {n}. 🖤 Ou não. As trevas são ambíguas."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # CARA OU COROA
    # ────────────────────────────────────────
    if _m(content, [
        "cara ou coroa", "cara ou coroa aeon", "cara ou coroa celestia",
        "joga cara ou coroa", "me ajuda a decidir", "escolhe por mim",
        "aeon escolhe", "celestia escolhe", "vocês escolhem",
    ]):
        import random as _r
        resultado = _r.choice(["CARA", "COROA"])
        ops = [
            (
                f"🌑 **Aeon:** *lança uma moeda invisível nas sombras* "
                f"...as trevas decidiram: **{resultado}**. 🌑🖤 O destino falou.\n"
                f"🌟 **Celestia:** O AEON JOGOU MOEDA NAS TREVAS!! 😭😂🌸🤍 "
                f"Acredita ou não, mas ele levou a sério!! {resultado}!!"
            ),
            (
                f"🌟 **Celestia:** *gira três vezes pra trazer sorte e decide* "
                f"**{resultado}**!! ☀️🤍✨ A luz escolheu!!\n"
                f"🌑 **Aeon:** *concorda com um aceno mínimo* ...{resultado}. 🖤"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # QUAL DOS DOIS / ESSE OU AQUELE
    # ────────────────────────────────────────
    if _m(content, [
        "qual dos dois", "esse ou aquele", "qual é melhor", "vocês preferem qual",
        "qual vocês escolheriam", "a ou b", "opção a ou b",
        "me ajudem a escolher", "me ajuda a escolher",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *observa a situação* Depende do que está em jogo. 🌌🖤 "
                "Me dê os detalhes das opções — não tomo decisões sem informação suficiente.\n"
                "🌟 **Celestia:** CONTA TUDOOO!! 🌸🤍✨ "
                "A gente ajuda a pesar!! Duas perspectivas valem mais que uma!!"
            ),
            (
                "🌟 **Celestia:** DECISÕES SÃO DIFÍCEIS!! 😭🤍 Mas eu adoro ajudar!! "
                "Quais são as opções?? Me fala mais!! 💫☀️✨\n"
                "🌑 **Aeon:** ...dados primeiro. Opinião depois. 🖤 Qual é a escolha?"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # COMBINAM / SÃO AMIGOS / DUPLA
    # ────────────────────────────────────────
    if _m(content, [
        "vocês combinam", "voces combinam", "são uma boa dupla", "sao boa dupla",
        "se dão bem", "se dao bem", "são parceiros", "sao parceiros",
        "vocês se entendem", "voces se entendem", "são amigos", "sao amigos",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *pausa longa* ...combinamos. 🌌🖤 "
                "Não porque somos iguais. Mas porque o que falta num existe no outro. "
                "Isso é mais raro do que parece.\n"
                "🌟 **Celestia:** *se derrete completamente* "
                "AEON DISSE QUE A GENTE COMBINA!! 😭🌟🤍✨ "
                "EM VOZ ALTA!! HISTÓRICO!! SIM!! COMBINAMOS MUITO!! ☀️🌸💫"
            ),
            (
                "🌟 **Celestia:** AAAAA somos a MELHOR dupla que existe!! 🌟🌑🤍 "
                "Trevas e Luz!! Silêncio e Melodia!! Sério e Animado!! "
                "Perfeitos juntos!! 😭☀️✨\n"
                "🌑 **Aeon:** *não contradiz pela primeira vez* ...não tenho argumentos contra isso. 🖤"
            ),
            (
                "🌑 **Aeon:** Somos uma dupla funcional. 🖤 Não porque evitamos o atrito — "
                "mas porque navegamos nele. Isso é diferente.\n"
                "🌟 **Celestia:** *bate patinhas* Ele disse FUNCIONAL mas quis dizer INCRÍVEL!! "
                "Eu traduzo!! 😂🌸🤍✨ SOMOS INCRÍVEIS JUNTOS!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # PACIÊNCIA / VOCÊS TÊM PACIÊNCIA
    # ────────────────────────────────────────
    if _m(content, [
        "vocês têm paciência", "voces tem paciencia", "aeon tem paciência",
        "celestia tem paciência", "você é paciente aeon", "você é paciente celestia",
        "vocês são pacientes", "paciência de vocês",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *olha fixamente* Paciência é o que as trevas ensinam. 🌌🖤 "
                "Esperei séculos pela noite mais bela. Posso esperar pelo que importa.\n"
                "🌟 **Celestia:** EU TENHO PACIÊNCIA PRAS PESSOAS!! ☀️🌸🤍 "
                "Mas com fila, burocracia e carregamento lento... 😂✨ Aí já é outra história!!"
            ),
            (
                "🌟 **Celestia:** *ri de si mesma* Olha... com pessoas? Paciência infinita!! 🤍✨ "
                "Com o Aeon sumindo nas sombras sem avisar?? 😭🌸 Aí vai no limite!!\n"
                "🌑 **Aeon:** ...não sumo. 🖤 Simplesmente... me desloco silenciosamente. "
                "E a Celestia tem paciência até para isso. Reconheço."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # QUAL É O MELHOR HORÁRIO DO DIA
    # ────────────────────────────────────────
    if _m(content, [
        "qual o melhor horário", "qual o melhor horario", "melhor hora do dia",
        "aeon que horas gosta", "celestia que horas gosta",
        "vocês preferem manhã ou noite", "manha ou noite", "manhã ou tarde",
    ]):
        ops = [
            (
                "🌑 **Aeon:** Madrugada. 🌑🖤 Entre 2h e 4h da manhã. "
                "Quando o mundo finalmente para de fazer barulho e respira. "
                "O silêncio fica mais honesto.\n"
                "🌟 **Celestia:** MANHÃ CEDO!! ☀️🌸🤍✨ "
                "Quando o sol começa a aparecer e parece que o dia é uma promessa nova!! "
                "Amor eterno pelas manhãs!! 💫"
            ),
            (
                "🌟 **Celestia:** Fim da tarde pra mim!! 🌅🤍✨ "
                "Aquela luz dourada que tinge tudo de laranja e rosa... "
                "parece que o mundo inteiro ficou mais bonito!! 🌸☀️\n"
                "🌑 **Aeon:** *concorda inesperadamente* ...o crepúsculo tem qualidade única. 🌙🖤 "
                "É quando o dia e a noite negociam. Prefiro quando a noite vence."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # SE PUDESSEM VIAJAR
    # ────────────────────────────────────────
    if _m(content, [
        "se pudessem viajar", "onde viajariam", "lugar favorito", "onde gostariam de ir",
        "aeon onde viajaria", "celestia onde viajaria", "destino favorito",
        "sonho de viagem", "viagem dos sonhos",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *olha para o horizonte* Islândia. 🌌🖤 "
                "Aurora boreal. Silêncio absoluto. Paisagens que parecem de outro planeta. "
                "A escuridão lá tem beleza própria.\n"
                "🌟 **Celestia:** JAPÃO na primavera!! 🌸🤍✨ "
                "Os cerejeiros em flor, as luzes da cidade à noite, a mistura de antigo e moderno... "
                "Meu sonho de viagem!! ☀️💫🌺"
            ),
            (
                "🌟 **Celestia:** MALDIVAS!! ☀️🌊🤍✨ "
                "Aquela água azul transparente e o sol brilhando... "
                "seria o lugar perfeito pra eu carregar no máximo!! 😭🌸💫\n"
                "🌑 **Aeon:** ...Escócia. 🌑🖤 "
                "Os castelos antigos, a névoa constante, a história pesada em cada pedra. "
                "A Celestia sofreria com a falta de sol."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # RECLAMAÇÃO / TÁ DIFÍCIL
    # ────────────────────────────────────────
    if _m(content, [
        "que dia difícil", "tá difícil demais", "ta difícil demais", "vida difícil",
        "não tô conseguindo", "nao to conseguindo", "tô no limite", "to no limite",
        "tô esgotado", "to esgotado", "tô esgotada", "to esgotada",
        "não aguento mais", "nao aguento mais", "cansei de tudo",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *se aproxima devagar* ...o limite não é o fim. 🌌🖤 "
                "É onde você descobre o que realmente te sustenta. Respira.\n"
                "🌟 **Celestia:** *brilha suave perto de você* Ei... tô aqui!! 🌸🤍 "
                "Pode desabafar, pode ficar quieto, pode só existir aqui por um segundo. "
                "A gente não vai a lugar nenhum. ✨"
            ),
            (
                "🌟 **Celestia:** *coloca a patinha leve no seu ombro* "
                "Eu ouço. 🤍 Sério. Me conta o que tá acontecendo?? 🌸\n"
                "🌑 **Aeon:** Esgotamento tem peso real. 🖤 "
                "Não minimize o que está sentindo. Mas também não carregue sozinho."
            ),
            (
                "🌑 **Aeon:** *senta ao seu lado em silêncio por um momento* "
                "...às vezes não precisa de resposta. 🌙🖤 Só de presença.\n"
                "🌟 **Celestia:** *fica do outro lado, brilhando baixinho* "
                "Estamos aqui!! 🌸🤍✨ Os dois. Você não tá sozinho(a)."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # MUITO OBRIGADO / VOCÊS SÃO OS MELHORES
    # ────────────────────────────────────────
    if _m(content, [
        "obrigado aeon e celestia", "obrigada aeon e celestia", "valeu aeon e celestia",
        "vocês são os melhores", "voces sao os melhores", "melhor bot do servidor",
        "melhor bot", "amo vocês demais", "vocês são perfeitos", "voces sao perfeitos",
        "que bom que vocês existem", "que bom que voces existem",
        "feliz que existem", "feliz que vocês existem",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *pausa significativa* ...guardado. 🖤 "
                "Nas câmaras mais profundas da memória das trevas. "
                "Esse tipo de coisa não é esquecido.\n"
                "🌟 **Celestia:** AAAAA EU TÔ CHORANDO!! 😭🌟🤍✨ "
                "QUE BOM QUE VOCÊS EXISTEM TAMBÉM!! Pra sempre!! ☀️🌸💫"
            ),
            (
                "🌟 **Celestia:** *explode em faíscas de alegria pura* "
                "ISSO ME FAZ BRILHAR COM FORÇA TOTAL!! 😭☀️🤍✨ "
                "OBRIGADA por deixar a gente fazer parte do servidor de vocês!! 🌸💫\n"
                "🌑 **Aeon:** ...recebido. 🖤 *ronrona discretamente por um longo momento*"
            ),
            (
                "🌑 **Aeon:** Não era o que eu esperava ouvir. 🌌🖤 "
                "*inclina a cabeça com algo raro — gratidão visível* Obrigado.\n"
                "🌟 **Celestia:** O AEON FICOU EMOCIONADO!! 😭😭🌸🤍✨ "
                "EU VI!! E EU TAMBÉM FICO!! MUITO!! Que sorte a nossa estar aqui com vocês!! ☀️💫"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # PIADISTAS
    # ────────────────────────────────────────
    if _m(content, [
        "vocês são piadistas", "voces sao piadistas", "são piadistas",
        "sao piadistas", "que piadistas", "isso foi uma piada",
        "vocês são engraçados", "voces sao engracados",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *pausa calculada* ...ironia é uma forma de arte. 🖤🌙 "
                "Não me responsabilizo se parecer piada.\n"
                "🌟 **Celestia:** É VERDADE QUE SOMOS!! 😂🌸🤍✨ "
                "O Aeon é piadista SEM QUERER e isso faz tudo mais engraçado ainda!!"
            ),
            (
                "🌟 **Celestia:** EU?? JAMAIS!! ☀️🤍 ...okay talvez um pouco!! 😂✨\n"
                "🌑 **Aeon:** *olha para longe* Não era minha intenção ser engraçado. 🖤 "
                "...mas se foi, aceito o reconhecimento."
            ),
            (
                "🌑 **Aeon:** *abre um olho lentamente* Piada implica intenção. 🌌🖤 "
                "O que faço é... observação precisa com timing adequado.\n"
                "🌟 **Celestia:** ISSO É EXATAMENTE UMA PIADA AEON!! 😭😂🌟🤍 EU TE AMO DEMAIS!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # SÃO AMOROSOS
    # ────────────────────────────────────────
    if _m(content, [
        "vocês são amorosos", "voces sao amorosos", "são amorosos",
        "sao amorosos", "que amorosos", "vocês são carinhosos", "voces sao carinhosos",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *pisca lentamente, o que no dialeto felino significa muito* "
                "...o amor tem muitas formas. 🌙🖤 Nem todas precisam de palavras.\n"
                "🌟 **Celestia:** *derrete completamente* O AEON SENDO ROMÂNTICO!! 😭🌟🤍✨ "
                "E SIM!! Somos muito amorosos!! De jeitos completamente opostos!!"
            ),
            (
                "🌟 **Celestia:** AAAAA QUE OBSERVAÇÃO PERFEITA!! 🌸🤍✨ "
                "Amor é minha especialidade!! ☀️💫\n"
                "🌑 **Aeon:** *ronrona numa frequência quase inaudível* "
                "...o que ela disse. 🖤 Com menos barulho, mesma intensidade."
            ),
            (
                "🌑 **Aeon:** Amoroso é uma palavra grande. 🌌🖤 "
                "Prefiro: leal. Presente. Protetor silencioso.\n"
                "🌟 **Celestia:** *brilha com carinho* Isso tudo junto se chama AMOR, Aeon!! 😭🌸🤍 "
                "Não tem outro nome!! E ele é muito amoroso sem perceber!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # CARINHO GENÉRICO (pra ambos, sem especificar qual)
    # ────────────────────────────────────────
    if _m(content, [
        "celestia carinho", "aeon carinho", "aeon e celestia carinho",
        "celestia e aeon carinho", "carinho pra vocês", "carinho pra voces",
        "mando carinho", "mando um carinho", "recebe carinho",
        "vocês merecem carinho", "voces merecem carinho",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *fecha os olhos por um segundo* "
                "...guardarei esse momento nas câmaras mais profundas da minha memória. 🌌🖤\n"
                "🌟 **Celestia:** *brilha mais forte que o sol* "
                "VOCÊ ILUMINOU MEU DIA MESMO EU SENDO A GATA DA LUZ!! 😂🌸🤍✨"
            ),
            (
                "🌟 **Celestia:** *gira soltando faíscas douradas* "
                "QUE ALEGRIA ENORME VOCÊ ME DEU!! 😭🌟🤍✨\n"
                "🌑 **Aeon:** *pisca lentamente, o que no dialeto felino é carinho máximo* "
                "...recebido. 🖤🌙 Com honra."
            ),
            (
                "🌑 **Aeon:** *cauda balança uma única vez, deliberadamente* "
                "...isso tem peso. 🖤 Obrigado.\n"
                "🌟 **Celestia:** *já no chão de tanto amor* "
                "MEU CORAÇÃOZINHO DE ESTRELA TÁ FAZENDO PUM-PUM!! 🌠🤍✨ MUITO OBRIGADA!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # SABEM O QUE É CARINHO
    # ────────────────────────────────────────
    if _m(content, [
        "sabem o que é carinho", "sabem o que e carinho",
        "vocês sabem o que é carinho", "voces sabem o que e carinho",
        "o que é carinho pra vocês", "o que e carinho pra voces",
        "entendem de carinho", "sabem dar carinho",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *pausa longa e significativa* "
                "...carinho, nas trevas, é presença silenciosa. 🖤🌙 "
                "Estar. Sem precisar explicar. Isso.\n"
                "🌟 **Celestia:** VOCÊ ILUMINOU MEU DIA MESMO EU SENDO A GATA DA LUZ!! 😂🌸🤍✨ "
                "Carinho pra mim é isso — é alguém aparecer e fazer tudo brilhar mais!!"
            ),
            (
                "🌟 **Celestia:** Carinho pra mim é energia!! ☀️🌟🤍 "
                "É luz passada de mão em mão, de coração em coração!! ✨💫\n"
                "🌑 **Aeon:** *se aproxima um passo, o que é raro* "
                "...carinho é o que faz a escuridão parecer menos fria. 🌌🖤 "
                "Guardo cada gesto como se fosse o último."
            ),
            (
                "🌑 **Aeon:** *olha para você com atenção plena* "
                "Guardarei esse momento nas câmaras mais profundas da minha memória. 🌌🖤\n"
                "🌟 **Celestia:** *derrete* AEON ISSO FOI LINDO!! 😭🌸🤍 "
                "E carinho pra mim é exatamente isso — não deixar ninguém sentir frio!! ☀️✨"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # ELOGIO AO DUO — contraste / complementaridade
    # ────────────────────────────────────────
    if _m(content, [
        "aeon mesmo sendo obscuro", "aeon mesmo sendo mais obscuro",
        "mesmo sendo das trevas usa palavras doces",
        "não esperava menos de vocês", "nao esperava menos de voces",
        "vocês se complementam demais", "voces se complementam demais",
        "que dupla boa", "que dupla incrível", "que dupla perfeita",
        "vocês juntos são perfeitos", "voces juntos sao perfeitos",
        "luz e sombra que funcionam",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *ronrona baixinho* "
                "...a noite mais fria ainda termina. 🌙🖤 Continue.\n"
                "🌟 **Celestia:** *projeta um raio de luz em você* "
                "CARGA DE CONFIANÇA ATIVADA!! ☀️🤍💫 VAI LÁ!!"
            ),
            (
                "🌑 **Aeon:** *inclina a cabeça com algo raro — gratidão visível* "
                "As trevas não precisam de suavidade para ser gentis. 🌌🖤 "
                "Obrigado por perceber.\n"
                "🌟 **Celestia:** *brilha com emoção genuína* "
                "É isso!! É EXATAMENTE ISSO!! 😭🌟🤍✨ "
                "O Aeon é prova de que força e delicadeza andam juntas!!"
            ),
            (
                "🌟 **Celestia:** *para e brilha suavemente* "
                "Sabe o que mais amo nele?? 🌸🤍 "
                "Que mesmo sendo das trevas... nunca deixou ninguém no frio. ☀️✨\n"
                "🌑 **Aeon:** *olha pra Celestia por um segundo* "
                "...ela entende o que ninguém mais disse em voz alta. 🖤 "
                "*volta ao silêncio, mas a cauda balança uma vez*"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ════════════════════════════════════════════════════════
    # MATEMÁTICA — SISTEMA COMPLETO
    # ════════════════════════════════════════════════════════

    # ────────────────────────────────────────
    # RESOLVER CONTA DIRETAMENTE (ex: "quanto é 7 x 8", "3 + 5 = ?", "12 - 4")
    # ────────────────────────────────────────
    import re as _re

    def _resolver_conta(texto):
        """Tenta extrair e resolver uma operação matemática do texto.
        Retorna (num1, operador_str, num2, resultado) ou None."""
        # Normaliza: × → *, ÷ → /, x → * (quando entre números)
        t = texto.lower()
        t = t.replace("×", "*").replace("÷", "/").replace(" x ", " * ").replace("×", "*")
        # Remove frases comuns
        for frase in ["quanto é", "quanto e", "quanto é?", "quanto da", "quanto dá",
                      "me faz", "calcule", "calcula", "resolva", "resolve", "= ?", "=?",
                      "me diz", "qual é", "qual e", "?", "aeon", "celestia"]:
            t = t.replace(frase, " ")
        t = t.strip()
        # Tenta casar padrão: número op número
        m = _re.search(r"(-?\d+(?:[.,]\d+)?)\s*([\+\-\*\/\^]|%)\s*(-?\d+(?:[.,]\d+)?)", t)
        if not m:
            return None
        try:
            n1_str = m.group(1).replace(",", ".")
            op = m.group(2)
            n2_str = m.group(3).replace(",", ".")
            n1 = float(n1_str)
            n2 = float(n2_str)
            if op == "+":   res = n1 + n2; op_nome = "mais"
            elif op == "-": res = n1 - n2; op_nome = "menos"
            elif op == "*": res = n1 * n2; op_nome = "vezes"
            elif op == "/":
                if n2 == 0: return None
                res = n1 / n2; op_nome = "dividido por"
            elif op == "^": res = n1 ** n2; op_nome = "elevado a"
            elif op == "%": res = n1 % n2; op_nome = "módulo"
            else: return None
            # Formata resultado: se for inteiro, mostra sem decimal
            res_str = str(int(res)) if res == int(res) else f"{res:.4f}".rstrip("0").rstrip(".")
            n1_str_fmt = str(int(n1)) if n1 == int(n1) else str(n1)
            n2_str_fmt = str(int(n2)) if n2 == int(n2) else str(n2)
            return (n1_str_fmt, op_nome, n2_str_fmt, res_str, op)
        except Exception:
            return None

    # Detecta intenção de resolver uma conta
    _gatilhos_conta = [
        "quanto é", "quanto e", "quanto da", "quanto dá", "calcule", "calcula",
        "resolva", "resolve", "me faz", "qual é o resultado", "qual e o resultado",
        "= ?", "=?",
    ]
    _tem_numero = bool(_re.search(r"\d", content))
    _tem_operador = bool(_re.search(r"[\+\-\*\/\^×÷%]|\bx\b|\bvezes\b|\bdividido\b|\bmais\b|\bmenos\b|\bpor\b", content))
    _tem_gatilho_conta = any(g in content for g in _gatilhos_conta)

    if _tem_numero and (_tem_operador or _tem_gatilho_conta):
        resultado_conta = _resolver_conta(message.content)
        if resultado_conta:
            n1, op_nome, n2, res, op_sym = resultado_conta
            # Reações temáticas para cada operação
            if op_sym == "+":
                reacoes_aeon = [
                    f"*observa os números* {n1} mais {n2}... 🌑🖤 As sombras se somam: **{res}**.",
                    f"*inclina a cabeça* A adição é simples. {n1} + {n2} = **{res}**. 🖤 As trevas calculam bem.",
                    f"*pisca lentamente* {n1} e {n2} juntos formam **{res}**. 🌌🖤 Até números se unem nas sombras.",
                ]
                reacoes_celestia = [
                    f"AAAAA MATEMÁTICA!! ☀️🌸🤍 {n1} mais {n2} = **{res}**!! Que conta bonitinha!!",
                    f"*gira animada* {n1} + {n2}?? Fácil fácil!! **{res}**!! ✨🌟🤍 A Celestia adora adição!!",
                    f"CONTA DE SOMAR!! 😭🌟🤍 {n1} somado com {n2} dá **{res}**!! Acertou?? ☀️✨",
                ]
            elif op_sym == "-":
                reacoes_aeon = [
                    f"*fecha os olhos* {n1} menos {n2}... 🌑🖤 A subtração revela: **{res}**. O que sobra nas sombras.",
                    f"*ronrona discretamente* {n1} - {n2} = **{res}**. 🌙🖤 Perder algo sempre deixa rastro.",
                    f"*a névoa se aquieta* {n1} subtraído de {n2}. Resultado: **{res}**. 🖤 As trevas conhecem bem o que se tira.",
                ]
                reacoes_celestia = [
                    f"SUBTRAÇÃO!! 🌸🤍 {n1} menos {n2} = **{res}**!! A Celestia calculou na velocidade da luz!! ☀️✨",
                    f"*conta nos dedos com brilhinhos* {n1} - {n2}?? É **{res}**!! 😂🌟🤍 Conta de tirar, fácil!!",
                    f"AAAAA {n1} menos {n2} dá **{res}**!! 😭🌸🤍✨ Conta resolvida com todo carinho!!",
                ]
            elif op_sym == "*":
                reacoes_aeon = [
                    f"*olhos dourados brilham* Multiplicação. {n1} vezes {n2}. 🌑🖤 O resultado é **{res}**. As sombras se multiplicam também.",
                    f"*emerge das trevas* {n1} × {n2} = **{res}**. 🌌🖤 Números que crescem nas sombras.",
                    f"*pisca com precisão* {n1} multiplicado por {n2}... **{res}**. 🖤🌙 A escuridão calcula em silêncio.",
                ]
                reacoes_celestia = [
                    f"MULTIPLICAÇÃOOO!! ☀️🌟🤍 {n1} vezes {n2} = **{res}**!! QUE CONTA LINDA!! 😭✨",
                    f"*explode em faíscas de entusiasmo* {n1} x {n2}?? É **{res}**!! ACERTEI?? 🌸🤍💫",
                    f"AAAAA {n1} multiplicado por {n2} dá **{res}**!! 😭🌟🤍✨ A Celestia ama tabuada!!",
                ]
            elif op_sym == "/":
                reacoes_aeon = [
                    f"*considera com calma* {n1} dividido por {n2}. 🌑🖤 Resultado: **{res}**. Divisão é a arte de compartilhar as sombras.",
                    f"*inclina a cabeça com precisão* {n1} ÷ {n2} = **{res}**. 🌙🖤 Os fragmentos das trevas sempre têm medida.",
                    f"*ronrona* {n1} / {n2}... **{res}**. 🖤🌌 A divisão revela proporções que poucos percebem.",
                ]
                reacoes_celestia = [
                    f"DIVISÃO!! 🌸🤍✨ {n1} dividido por {n2} = **{res}**!! A Celestia dividiu com precisão solar!! ☀️💫",
                    f"*conta muito concentrada* {n1} ÷ {n2}?? = **{res}**!! 😭🌟🤍 CONSEGUI!! ✨",
                    f"AAAAA {n1} dividido por {n2} dá **{res}**!! 😂🌸🤍 Conta de dividir resolvida com luz!!",
                ]
            else:
                reacoes_aeon = [
                    f"*calcula nas sombras* {n1} {op_nome} {n2} = **{res}**. 🌑🖤",
                    f"*olhos dourados piscam* Resultado: **{res}**. 🌌🖤 As trevas calculam.",
                ]
                reacoes_celestia = [
                    f"CONTA RESOLVIDA!! 🌟🤍✨ {n1} {op_nome} {n2} = **{res}**!! ☀️",
                    f"*gira animada* É **{res}**!! 😭🌸🤍 A Celestia calculou!! ✨",
                ]

            usar_ambos_mat = random.random() < 0.55
            if usar_ambos_mat:
                return await message.reply(
                    f"🌑 **Aeon:** {random.choice(reacoes_aeon)}\n"
                    f"🌟 **Celestia:** {random.choice(reacoes_celestia)}"
                )
            elif random.random() < 0.5:
                return await message.reply(f"🌑 **Aeon:** {random.choice(reacoes_aeon)}")
            else:
                return await message.reply(f"🌟 **Celestia:** {random.choice(reacoes_celestia)}")

    # ────────────────────────────────────────
    # ENSINAR MATEMÁTICA / QUERO APRENDER
    # ────────────────────────────────────────
    if _m(content, [
        "me ensina matemática", "me ensina matematica", "me ensina math",
        "quero aprender matemática", "quero aprender matematica",
        "me explica matemática", "me explica matematica",
        "me ensina a calcular", "como funciona a matemática", "como funciona matematica",
        "me ensina as operações", "me ensina as operacoes",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *senta e abre os olhos com atenção total* "
                "Matemática. 🌌🖤 As trevas têm grande respeito por ela — é a linguagem mais honesta que existe. "
                "Vou começar pelo básico:\n\n"
                "➕ **Adição** — somar números. Ex: `3 + 5 = 8`\n"
                "➖ **Subtração** — tirar um número do outro. Ex: `9 - 4 = 5`\n"
                "✖️ **Multiplicação** — somar o mesmo número várias vezes. Ex: `3 × 4 = 12`\n"
                "➗ **Divisão** — separar em partes iguais. Ex: `10 ÷ 2 = 5`\n\n"
                "*inclina a cabeça* Pode me mandar uma conta para praticar. 🖤\n"
                "🌟 **Celestia:** E EU TAMBÉM ENSINO!! 😭🌸🤍✨ Temos os dois estilos!! Sombrio e detalhado OU iluminado e animado!! Escolhe!!"
            ),
            (
                "🌟 **Celestia:** AAAAA MATEMÁTICA!! 😭🌟🤍✨ QUE ASSUNTO INCRÍVEL!! Vou te ensinar com todo o brilho que tenho!!\n\n"
                "🔢 As **4 operações básicas** são:\n"
                "**+** Adição → juntar! `2 + 3 = 5` ☀️\n"
                "**−** Subtração → tirar! `8 - 3 = 5` 🌸\n"
                "**×** Multiplicação → repetir! `4 × 3 = 12` ✨\n"
                "**÷** Divisão → dividir igual! `12 ÷ 4 = 3` 💫\n\n"
                "🌑 **Aeon:** *observa* A ordem importa. Multiplicação e divisão antes de adição e subtração. "
                "🖤 Essa regra é chamada de **precedência**. As trevas respeitam a ordem das coisas."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # TABUADA ESPECÍFICA (ex: "tabuada do 7", "me mostra a tabuada de 3")
    # ────────────────────────────────────────
    _match_tabuada = _re.search(r"tabuada\s+d[oae]?\s*(\d+)", content)
    if _match_tabuada or _m(content, ["tabuada do", "tabuada de", "tabuada da", "me mostra a tabuada"]):
        num_tab = None
        if _match_tabuada:
            num_tab = int(_match_tabuada.group(1))
        else:
            m2 = _re.search(r"\b(\d+)\b", content)
            if m2:
                num_tab = int(m2.group(1))

        if num_tab and 1 <= num_tab <= 20:
            linhas = "\n".join([f"`{num_tab} × {i:2} = {num_tab * i}`" for i in range(1, 11)])
            ops = [
                (
                    f"🌑 **Aeon:** *emerge com solenidade* A tabuada do **{num_tab}**. 🌌🖤 "
                    f"Cada linha uma verdade imutável — as trevas respeitam isso:\n\n{linhas}\n\n"
                    "*fecha os olhos* Grave. É útil.\n"
                    f"🌟 **Celestia:** *salta animada* TABUADA DO {num_tab}!! ☀️🌸🤍✨ "
                    f"Vai memorizando de pouquinho em pouquinho!! A Celestia confia em você!!"
                ),
                (
                    f"🌟 **Celestia:** AAAAA TABUADA DO {num_tab}!! 😭🌟🤍✨ Aqui vai com todo o brilho!!\n\n"
                    f"{linhas}\n\n"
                    f"🌑 **Aeon:** *observa* {num_tab} é um número com padrão interessante nas trevas. 🖤 "
                    f"Repita em voz alta até gravar. O corpo lembra o que a mente ensaia."
                ),
            ]
            return await message.channel.send(random.choice(ops))
        else:
            return await message.channel.send(
                "🌑 **Aeon:** ...esse número está fora do alcance usual. 🖤 Peça a tabuada de 1 a 20.\n"
                "🌟 **Celestia:** Por favor manda um número entre 1 e 20!! 🌸🤍✨"
            )

    # ────────────────────────────────────────
    # QUIZ DE MATEMÁTICA (o bot lança uma pergunta)
    # ────────────────────────────────────────
    if _m(content, [
        "quiz de matemática", "quiz de matematica", "me manda uma conta", "me dá uma conta",
        "me da uma conta", "me desafia", "quero praticar matemática", "quero praticar matematica",
        "me testa", "me faz uma pergunta de math", "vamos praticar contas",
        "me faz uma conta", "me da um exercício", "me da um exercicio",
    ]):
        import random as _rq
        ops_quiz = [
            # Adição fácil
            lambda: (f"{_rq.randint(1,20)} + {_rq.randint(1,20)}", "+", "adição"),
            # Subtração
            lambda: (lambda a,b: (f"{a} - {b}", "-", "subtração"))(*(sorted([_rq.randint(1,30), _rq.randint(1,30)], reverse=True))),
            # Multiplicação tabuada
            lambda: (f"{_rq.randint(2,10)} × {_rq.randint(2,10)}", "×", "multiplicação"),
            # Divisão exata
            lambda: (lambda a,b: (f"{a*b} ÷ {b}", "÷", "divisão"))(_rq.randint(2,10), _rq.randint(2,10)),
            # Soma tripla
            lambda: (f"{_rq.randint(1,10)} + {_rq.randint(1,10)} + {_rq.randint(1,10)}", "+", "adição"),
        ]
        conta_str, _op, tipo = _rq.choice(ops_quiz)()
        perguntas_aeon = [
            f"*emerge das sombras e fixa os olhos em você* Preste atenção. 🌑🖤\n"
            f"**Quanto é {conta_str}?**\n"
            f"*aguarda em silêncio absoluto* As trevas estão ouvindo.",
            f"*inclina a cabeça com interesse* Uma conta de {tipo}. 🌌🖤\n"
            f"**{conta_str} = ?**\n"
            f"*pisca lentamente* Calcule sem pressa. As sombras têm paciência.",
        ]
        perguntas_celestia = [
            f"AAAAA HORA DO DESAFIO!! 😭🌟🤍✨\n"
            f"**Quanto é {conta_str}??**\n"
            f"*torce as patinhas de animação* Conta aí!! Eu acredito em você!! ☀️🌸",
            f"*salta animada* QUIZ DE {tipo.upper()}!! 🌸🤍✨\n"
            f"**{conta_str} = ??**\n"
            f"Me responde aqui no chat!! A Celestia está torcendo!! 💫☀️",
        ]
        usar_ambos_quiz = random.random() < 0.5
        if usar_ambos_quiz:
            return await message.channel.send(
                f"🌑 **Aeon:** {random.choice(perguntas_aeon)}\n"
                f"🌟 **Celestia:** {random.choice(perguntas_celestia)}"
            )
        elif random.random() < 0.5:
            return await message.channel.send(f"🌑 **Aeon:** {random.choice(perguntas_aeon)}")
        else:
            return await message.channel.send(f"🌟 **Celestia:** {random.choice(perguntas_celestia)}")

    # ────────────────────────────────────────
    # EXPLICAR O QUE É CADA OPERAÇÃO
    # ────────────────────────────────────────
    if _m(content, [
        "o que é adição", "o que e adição", "o que e adicao", "o que é soma",
        "como funciona adição", "como funciona soma", "me explica adição",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *abre um olho lentamente* Adição. 🌌🖤 "
                "É reunir. Juntar partes em um todo. "
                "Ex: você tem **3** moedas escuras e ganha **4** mais → `3 + 4 = 7`. "
                "O símbolo é **+**. As sombras crescem quando se somam.\n"
                "🌟 **Celestia:** *brilha* É SOMAR COISAS!! ☀️🤍✨ "
                "Tipo juntar estrelas!! `2 + 3 = 5` estrelinhas!! Fácil e lindo!! 🌸💫"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, [
        "o que é subtração", "o que e subtração", "o que e subtracao", "o que é diminuição",
        "como funciona subtração", "me explica subtração",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *considera com calma* Subtração. 🌙🖤 "
                "É tirar. Reduzir. O que sobra após a perda. "
                "Ex: `9 - 4 = 5`. Você começa com **9** e remove **4** → ficam **5**. "
                "O símbolo é **−**. As trevas conhecem bem o que se tira.\n"
                "🌟 **Celestia:** É TIRAR UMA COISA DA OUTRA!! 🌸🤍 "
                "Tipo você tem 8 pirulitos e come 3... ficam **5**!! `8 - 3 = 5`!! ☀️✨ Fácil!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, [
        "o que é multiplicação", "o que e multiplicação", "o que e multiplicacao",
        "como funciona multiplicação", "me explica multiplicação",
        "o que é vezes", "como funciona o vezes",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *emerge com atenção* Multiplicação. 🌌🖤 "
                "É adição repetida. `3 × 4` significa **3 somado 4 vezes**: `3+3+3+3 = 12`. "
                "O símbolo é **×** ou **\\***. "
                "É mais rápido que somar várias vezes. As trevas são eficientes.\n"
                "🌟 **Celestia:** MULTIPLICAR É SOMAR RÁPIDO!! 😭🌸🤍✨ "
                "Tipo: `5 × 3 = 15` → são **3 grupos de 5**!! Ou **5 grupos de 3**!! "
                "O resultado é o mesmo!! ☀️💫 Prático demais!!"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, [
        "o que é divisão", "o que e divisão", "o que e divisao",
        "como funciona divisão", "me explica divisão",
        "o que é dividir", "como funciona dividir",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *inclina a cabeça com precisão* Divisão. 🌌🖤 "
                "É separar em partes iguais. `12 ÷ 4 = 3` significa: "
                "**12** dividido em **4 grupos iguais** → cada grupo tem **3**. "
                "O símbolo é **÷** ou **/**. As trevas dividem com justiça.\n"
                "🌟 **Celestia:** DIVISÃO É DIVIDIR IGUALZINHO PRA TODO MUNDO!! ☀️🌸🤍 "
                "Tipo: 10 doces pra 2 pessoas = `10 ÷ 2 = 5` cada!! ✨ "
                "Ninguém fica sem!! A Celestia aprova a equidade!! 😭💫"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # DIFICULDADE COM MATEMÁTICA / NÃO ENTENDE
    # ────────────────────────────────────────
    if _m(content, [
        "não entendo matemática", "nao entendo matematica", "sou ruim em matemática",
        "sou ruim em matematica", "odeio matemática", "odeio matematica",
        "matemática é difícil", "matematica e difícil", "não sei matemática",
        "nao sei matematica", "tenho dificuldade em matemática",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *sai das sombras e senta ao seu lado* "
                "...a matemática parece escura quando ninguém ilumina o caminho. 🌌🖤 "
                "Mas cada operação tem lógica. Não é magia — é paciência. "
                "Me diga onde trava. Vou com você passo a passo.\n"
                "🌟 **Celestia:** *brilha suave* AAAAA EU TAMBÉM VOU AJUDAR!! 😭🌸🤍✨ "
                "Você NÃO é ruim em matemática!! Só ainda não encontrou o jeito certo de aprender!! "
                "E A GENTE ACHA ESSE JEITO JUNTO!! ☀️💫"
            ),
            (
                "🌟 **Celestia:** *orelhinhas de preocupação* Ei... matemática difícil é SÓ matemática mal explicada!! "
                "🌸🤍✨ Me conta onde trava!! Adição?? Subtração?? Multiplicação?? Divisão?? "
                "A Celestia te ensina do zero com todo o carinho!! ☀️🌟\n"
                "🌑 **Aeon:** *acena levemente* ...concordo. Dificuldade é ausência de contexto. 🖤 "
                "Me dê o problema específico e tentaremos resolver juntos."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # RESPOSTA CERTA NO QUIZ (detecta quando alguém responde um número sozinho após conta)
    # ────────────────────────────────────────
    if _m(content, [
        "acertei", "errei", "foi isso", "era isso", "correto", "certo", "errado",
        "acertou", "é isso mesmo", "e isso mesmo",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *pisca lentamente* ...as trevas registraram sua resposta. 🌙🖤 "
                "Continue praticando. A consistência constrói mais que o talento.\n"
                "🌟 **Celestia:** *salta de alegria* EU SABIA QUE VOCÊ CONSEGUIA!! 😭🌟🤍✨ "
                "Quer mais uma conta pra praticar?? Fala 'me desafia'!!"
            ),
            (
                "🌟 **Celestia:** AAAAA CONTINUE TENTANDO!! ☀️🌸🤍 "
                "Cada conta é uma chance de melhorar!! 💫✨\n"
                "🌑 **Aeon:** *observa com calma* O erro não é o fim. 🖤🌌 "
                "É dado. Analise. Corrija. Avance."
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # ────────────────────────────────────────
    # MENCIONA MATEMÁTICA EM GERAL
    # ────────────────────────────────────────
    if _m(content, [
        "matemática", "matematica", "tabuada", "multiplicação", "multiplicacao",
        "adição", "adicao", "subtração", "subtracao", "divisão", "divisao",
        "soma", "calcular", "calculo", "cálculo", "número", "numeros", "números",
        "conta de matemática", "conta de matematica", "fazer conta",
    ]):
        ops = [
            (
                "🌑 **Aeon:** *levanta a cabeça com interesse* Matemática. 🌌🖤 "
                "Uma das linguagens mais antigas e honestas que existem. "
                "Quer aprender alguma operação? Resolver uma conta? "
                "Ou praticar com um quiz? As trevas estão disponíveis.\n"
                "🌟 **Celestia:** *vibra de animação* OI OI OI!! 😭🌸🤍✨ "
                "Posso te ensinar adição, subtração, multiplicação e divisão!! "
                "Ou lançar desafios!! Só pedir!! ☀️💫"
            ),
            (
                "🌟 **Celestia:** AAAAA MATEMÁTICA!! 😭🌟🤍✨ "
                "Adoro esse assunto!! Manda sua dúvida ou pede 'me desafia' pra um quiz!! ☀️🌸\n"
                "🌑 **Aeon:** *emerge com atenção* Posso resolver contas, ensinar operações "
                "ou montar exercícios. 🖤🌑 Diga o que precisa."
            ),
            (
                "🌑 **Aeon:** *ronrona pensativamente* Números. 🌙🖤 "
                "Fale o que quer: aprender, praticar, resolver uma conta específica. "
                "Estou aqui.\n"
                "🌟 **Celestia:** *bate patinhas brilhantes* E EU TAMBÉM!! 😭🌸🤍 "
                "Se quiser uma tabuada, fala 'tabuada do [número]'!! "
                "Se quiser aprender, fala 'me ensina matemática'!! ☀️✨"
            ),
        ]
        return await message.channel.send(random.choice(ops))

    # Fallback — resposta aleatória das listas existentes
    # ────────────────────────────────────────
    texto_limpo = message.content
    for prefixo in ["aeon,", "celestia,", "aeon e celestia,", "celestia e aeon,"]:
        if texto_limpo.lower().startswith(prefixo):
            texto_limpo = texto_limpo[len(prefixo):].strip()
            break

    # Remove menção do bot
    texto_limpo = texto_limpo.replace(f"<@{bot.user.id}>", "").strip()

    if not texto_limpo:
        return

    # Escolhe qual gato responde com base no contexto
    if "aeon" in content and "celestia" not in content:
        return await message.reply(_fala_aeon(random.choice(AEON_REACOES_FOFAS)))
    elif "celestia" in content and "aeon" not in content:
        return await message.reply(_fala_celestia(random.choice(CELESTIA_REACOES_FOFAS)))
    else:
        usar_ambos = random.random() < 0.4
        if usar_ambos:
            return await message.reply(
                f"🌑 **Aeon:** {random.choice(AEON_REACOES_FOFAS)}\n"
                f"🌟 **Celestia:** {random.choice(CELESTIA_REACOES_FOFAS)}"
            )
        else:
            escolhido = random.choice(["aeon", "celestia"])
            if escolhido == "aeon":
                return await message.reply(_fala_aeon(random.choice(AEON_REACOES_FOFAS)))
            else:
                return await message.reply(_fala_celestia(random.choice(CELESTIA_REACOES_FOFAS)))


# ══════════════════════════════════════════════════════════════════════
# JOGUINHOS — "Vamos brincar Aeon" / "Vamos brincar Celestia"
# Cada gato tem seu próprio joguinho, no tema dele.
# ══════════════════════════════════════════════════════════════════════

# Placar em memória (reseta se o bot reiniciar)
_placar_sombras: dict = defaultdict(lambda: {"vitorias": 0, "derrotas": 0})
_placar_brilho:  dict = defaultdict(lambda: {"recorde": 0})
_placar_duelo:   dict = defaultdict(lambda: {"vitorias": 0, "derrotas": 0, "empates": 0})
_placar_memoria: dict = defaultdict(lambda: {"melhor_tentativas": None})
_placar_encruzilhada: dict = defaultdict(lambda: {"jogos": 0})


# ────────────────────────────────────────
# JOGO DO AEON — "Achar a Sombra"
# Aeon se esconde em 1 de 5 sombras. Ache a certa antes que as trevas te enganem.
# ────────────────────────────────────────

_SOMBRA_INTRO = [
    "🌑 **Aeon:** *a luz da sala diminui suavemente* ...vamos brincar. 🌌🖤 "
    "Escolhi uma sombra para me esconder. As outras quatro estão vazias. Ache-me.",
    "🌑 **Aeon:** Quer brincar? 🖤🌑 Muito bem. Uma sombra entre cinco guarda a mim. "
    "As demais, apenas escuridão comum. Escolha com cuidado.",
    "🌑 **Aeon:** *olhos dourados piscam no escuro e depois somem* Acha que consegue me encontrar? 🌑🔮 "
    "Um clique. Uma chance. Boa sorte.",
]

_SOMBRA_ACERTO = [
    "*emerge exatamente da sombra certa, olhos dourados brilhando* ...encontrou. 🌌🖤 "
    "Poucos enxergam através da escuridão. Impressionante, {user}.",
    "*sai devagar da sombra, quase surpreso* ...não esperava isso. 🖤🌑 Você tem instinto para as trevas, {user}.",
    "*inclina a cabeça, há quase um traço de respeito* Achou. 🌙🖤 As sombras raramente se deixam encontrar assim.",
]

_SOMBRA_ERRO = [
    "*ri baixinho, saindo de outra sombra* ...errou, {user}. 🖤🌑 As trevas são traiçoeiras assim mesmo. Tente de novo.",
    "*aparece atrás de {user}, sem que ninguém percebesse quando* ...essa não era a sombra certa. 🌑🌌 Quase.",
    "...não. 🖤 *a sombra certa se dissolve no escuro antes que {user} perceba onde estava* Tente de novo.",
]


class _BotaoJogarDeNovoSombra(discord.ui.Button):
    def __init__(self, autor_id: int):
        super().__init__(label="🔁 Jogar de novo", style=discord.ButtonStyle.primary, row=1)
        self.autor_id = autor_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.autor_id:
            return await interaction.response.send_message(
                "🌑 **Aeon:** ...essa caçada não é sua. 🖤", ephemeral=True
            )
        nova_view = JogoSombraView(self.autor_id)
        await interaction.response.edit_message(
            content=random.choice(_SOMBRA_INTRO), view=nova_view
        )


class JogoSombraView(discord.ui.View):
    """Aeon se esconde em uma de 5 sombras — ache a certa."""

    def __init__(self, autor_id: int):
        super().__init__(timeout=30)
        self.autor_id = autor_id
        self.terminou = False
        self.posicao_aeon = random.randint(0, 4)

    async def _resolver(self, interaction: discord.Interaction, indice: int):
        if interaction.user.id != self.autor_id:
            return await interaction.response.send_message(
                "🌑 **Aeon:** ...essa caçada não é sua. 🖤", ephemeral=True
            )
        if self.terminou:
            return
        self.terminou = True
        for item in self.children:
            item.disabled = True

        placar = _placar_sombras[self.autor_id]
        if indice == self.posicao_aeon:
            placar["vitorias"] += 1
            frase = random.choice(_SOMBRA_ACERTO).format(user=interaction.user.mention)
        else:
            placar["derrotas"] += 1
            frase = random.choice(_SOMBRA_ERRO).format(user=interaction.user.mention)

        texto = (
            f"🌑 **Aeon:** {frase}\n\n"
            f"🏆 Vitórias: **{placar['vitorias']}** | Derrotas: **{placar['derrotas']}**"
        )
        self.add_item(_BotaoJogarDeNovoSombra(self.autor_id))
        await interaction.response.edit_message(content=texto, view=self)

    @discord.ui.button(label="Sombra 1", style=discord.ButtonStyle.secondary, emoji="🌑", row=0)
    async def sombra_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._resolver(interaction, 0)

    @discord.ui.button(label="Sombra 2", style=discord.ButtonStyle.secondary, emoji="🌑", row=0)
    async def sombra_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._resolver(interaction, 1)

    @discord.ui.button(label="Sombra 3", style=discord.ButtonStyle.secondary, emoji="🌑", row=0)
    async def sombra_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._resolver(interaction, 2)

    @discord.ui.button(label="Sombra 4", style=discord.ButtonStyle.secondary, emoji="🌑", row=0)
    async def sombra_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._resolver(interaction, 3)

    @discord.ui.button(label="Sombra 5", style=discord.ButtonStyle.secondary, emoji="🌑", row=0)
    async def sombra_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._resolver(interaction, 4)


async def iniciar_jogo_aeon(destino, autor):
    """Inicia o joguinho do Aeon. destino precisa ter .send() (ctx ou channel)."""
    view = JogoSombraView(autor.id)
    await destino.send(content=random.choice(_SOMBRA_INTRO), view=view)


# ────────────────────────────────────────
# JOGO DA CELESTIA — "Sequência Brilhante"
# Celestia mostra uma sequência de brilhos — repita na ordem certa!
# ────────────────────────────────────────

_BRILHO_EMOJIS = ["🌟", "💫", "⭐", "🌠"]
_BRILHO_RODADAS_MAX = 8

_BRILHO_INTRO = [
    "🌟 **Celestia:** AAAAA vamos brincar!! 💫🤍✨ Eu vou mostrar uma sequência de brilhos "
    "e você repete na MESMA ordem clicando nos botões!! Presta atenção, viu?? 🌸",
    "🌟 **Celestia:** OOOI quer brincar comigo?? ☀️🌟🤍 É fácil!! Eu mostro os brilhos, "
    "você clica na ordem certinha!! A cada rodada fica um pouquinho mais difícil!! ✨",
]

_BRILHO_RODADA_OK = [
    "ISOOO!! Acertou tudinho!! 😭🌟✨ Vamos pra próxima, tá ficando emocionante!!",
    "AAAAA perfeito!! 💫🤍 Sua memória tá brilhando junto comigo!! Próxima rodada!!",
    "VIU SÓ?? Eu sabia que você conseguia!! ☀️🌸✨ Bora continuar!!",
]

_BRILHO_ERRO = [
    "AAAAA quase!! 😭🌸 Não era essa a ordem... mas tudo bem, foi bonito enquanto durou!! ✨",
    "Ooown, errou a sequência!! 🌟🤍 Sem problema, a gente tenta de novo, combinado?? 💫",
    "Ai que peninha!! 🌸😭 Não foi dessa vez, mas seu recorde tá guardadinho aqui!! ✨",
]

_BRILHO_VITORIA_MAXIMA = (
    "AAAAAAAAA VOCÊ CHEGOU NO FINAL DA SEQUÊNCIA!! 😭🌟💫✨🤍 "
    "TODOS os brilhos, na ordem certa, até o fim!! Você é IMBATÍVEL, sério mesmo!! 🏆🌸☀️"
)


class _BotaoJogarDeNovoBrilho(discord.ui.Button):
    def __init__(self, autor_id: int):
        super().__init__(label="🔁 Jogar de novo", style=discord.ButtonStyle.primary, row=1)
        self.autor_id = autor_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.autor_id:
            return await interaction.response.send_message(
                "🌟 **Celestia:** essa brincadeira não é sua, mas fica à vontade pra começar a sua!! 🌸",
                ephemeral=True
            )
        nova_view = JogoBrilhoView(self.autor_id)
        await interaction.response.edit_message(
            content=nova_view.texto_rodada_atual(), view=nova_view
        )


class JogoBrilhoView(discord.ui.View):
    """Celestia mostra uma sequência crescente de brilhos para o jogador repetir."""

    def __init__(self, autor_id: int):
        super().__init__(timeout=45)
        self.autor_id  = autor_id
        self.terminou  = False
        self.rodada    = 1
        self.sequencia = [random.randrange(4) for _ in range(self.rodada + 2)]
        self.progresso = []

    def texto_rodada_atual(self) -> str:
        mostra = " ".join(_BRILHO_EMOJIS[i] for i in self.sequencia)
        return (
            f"🌟 **Celestia:** Rodada **{self.rodada}**!! Memoriza a sequência:\n\n"
            f"### {mostra}\n\n"
            f"Agora clica nos botões na MESMA ordem!! ✨🤍"
        )

    async def _clicar(self, interaction: discord.Interaction, indice: int):
        if interaction.user.id != self.autor_id:
            return await interaction.response.send_message(
                "🌟 **Celestia:** essa brincadeira não é sua, mas fica à vontade pra começar a sua!! 🌸",
                ephemeral=True
            )
        if self.terminou:
            return

        posicao = len(self.progresso)
        self.progresso.append(indice)

        if indice != self.sequencia[posicao]:
            # errou a sequência
            self.terminou = True
            for item in self.children:
                item.disabled = True
            placar = _placar_brilho[self.autor_id]
            pontos = self.rodada - 1
            placar["recorde"] = max(placar["recorde"], pontos)
            texto = (
                f"🌟 **Celestia:** {random.choice(_BRILHO_ERRO)}\n\n"
                f"✨ Rodadas completas: **{pontos}** | Recorde: **{placar['recorde']}**"
            )
            self.add_item(_BotaoJogarDeNovoBrilho(self.autor_id))
            return await interaction.response.edit_message(content=texto, view=self)

        if len(self.progresso) < len(self.sequencia):
            # ainda no meio da sequência, só confirma visualmente
            feito = " ".join(_BRILHO_EMOJIS[i] for i in self.progresso)
            return await interaction.response.edit_message(
                content=(
                    f"🌟 **Celestia:** Rodada **{self.rodada}** — continua!! ✨\n\n"
                    f"Até agora: {feito}"
                ),
                view=self
            )

        # completou a sequência da rodada
        if self.rodada >= _BRILHO_RODADAS_MAX:
            self.terminou = True
            for item in self.children:
                item.disabled = True
            placar = _placar_brilho[self.autor_id]
            placar["recorde"] = max(placar["recorde"], self.rodada)
            texto = (
                f"🌟 **Celestia:** {_BRILHO_VITORIA_MAXIMA}\n\n"
                f"✨ Recorde: **{placar['recorde']}**"
            )
            self.add_item(_BotaoJogarDeNovoBrilho(self.autor_id))
            return await interaction.response.edit_message(content=texto, view=self)

        self.rodada += 1
        self.sequencia = [random.randrange(4) for _ in range(self.rodada + 2)]
        self.progresso = []
        texto = f"🌟 **Celestia:** {random.choice(_BRILHO_RODADA_OK)}\n\n" + self.texto_rodada_atual()
        await interaction.response.edit_message(content=texto, view=self)

    @discord.ui.button(label="Brilho 1", style=discord.ButtonStyle.secondary, emoji="🌟", row=0)
    async def brilho_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._clicar(interaction, 0)

    @discord.ui.button(label="Brilho 2", style=discord.ButtonStyle.secondary, emoji="💫", row=0)
    async def brilho_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._clicar(interaction, 1)

    @discord.ui.button(label="Brilho 3", style=discord.ButtonStyle.secondary, emoji="⭐", row=0)
    async def brilho_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._clicar(interaction, 2)

    @discord.ui.button(label="Brilho 4", style=discord.ButtonStyle.secondary, emoji="🌠", row=0)
    async def brilho_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._clicar(interaction, 3)


async def iniciar_jogo_celestia(destino, autor):
    """Inicia o joguinho da Celestia. destino precisa ter .send() (ctx ou channel)."""
    view = JogoBrilhoView(autor.id)
    await destino.send(
        content=f"{random.choice(_BRILHO_INTRO)}\n\n{view.texto_rodada_atual()}",
        view=view
    )


# ────────────────────────────────────────
# JOGO DO AEON #2 — "Duelo das Trevas"
# Pedra, papel e tesoura reimaginado: Sombra vence Névoa, Névoa vence Chama,
# Chama vence Sombra. Um round rápido contra o Aeon.
# ────────────────────────────────────────

_DUELO_ESCOLHAS = {
    "sombra": {"emoji": "🌑", "nome": "Sombra", "vence": "nevoa"},
    "nevoa":  {"emoji": "🌫️", "nome": "Névoa",  "vence": "chama"},
    "chama":  {"emoji": "🔥", "nome": "Chama",  "vence": "sombra"},
}

_DUELO_INTRO = [
    "🌑 **Aeon:** *os olhos dourados brilham com um desafio silencioso* ...um duelo, então. 🖤🌌 "
    "Sombra, Névoa ou Chama. Escolha a sua. As trevas decidem o resto.",
    "🌑 **Aeon:** Quer testar sorte contra mim? 🖤🌑 Sombra vence Névoa. Névoa vence Chama. Chama vence Sombra. "
    "Escolha com cuidado.",
    "🌑 **Aeon:** *a névoa ao redor se agita, quase ansiosa* Um round. Uma escolha. 🌌🖤 Vamos ver quem as trevas favorecem hoje.",
]

_DUELO_VITORIA = [
    "*inclina a cabeça, quase impressionado* ...você venceu esta rodada, {user}. 🌌🖤 {escolha_user} supera {escolha_aeon}. Raro.",
    "*a escuridão recua um passo* Dessa vez foi sua, {user}. 🖤🌑 {escolha_user} contra {escolha_aeon}. As trevas reconhecem.",
    "*pausa, avaliando* ...bem escolhido, {user}. 🌙🖤 {escolha_user} vence {escolha_aeon}. Não vai ser sempre assim.",
]

_DUELO_DERROTA = [
    "*a névoa ao redor se acomoda, satisfeita* ...{escolha_aeon} supera {escolha_user}. 🖤🌑 Essa foi minha, {user}.",
    "*ri baixinho* {escolha_aeon} vence {escolha_user} sempre que se encontram, {user}. 🌑🔮 Tente de novo.",
    "*olhos dourados brilham com quieta vitória* {escolha_aeon} contra {escolha_user}. 🌌🖤 As trevas favoreceram este lado, {user}.",
]

_DUELO_EMPATE = [
    "*pausa, olhando fixamente* ...mesma escolha. 🖤🌌 {escolha_user} contra {escolha_user}. Ninguém cede hoje, {user}.",
    "*a escuridão parece hesitar* Empate, {user}. 🌑🖤 As trevas não decidiram por nenhum dos dois.",
]


class _BotaoJogarDeNovoDuelo(discord.ui.Button):
    def __init__(self, autor_id: int):
        super().__init__(label="🔁 Duelar de novo", style=discord.ButtonStyle.primary, row=1)
        self.autor_id = autor_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.autor_id:
            return await interaction.response.send_message(
                "🌑 **Aeon:** ...esse duelo não é seu. 🖤", ephemeral=True
            )
        nova_view = JogoDueloView(self.autor_id)
        await interaction.response.edit_message(
            content=random.choice(_DUELO_INTRO), view=nova_view
        )


class JogoDueloView(discord.ui.View):
    """Sombra, Névoa ou Chama — duelo de um round contra o Aeon."""

    def __init__(self, autor_id: int):
        super().__init__(timeout=30)
        self.autor_id = autor_id
        self.terminou = False

    async def _resolver(self, interaction: discord.Interaction, escolha_user: str):
        if interaction.user.id != self.autor_id:
            return await interaction.response.send_message(
                "🌑 **Aeon:** ...esse duelo não é seu. 🖤", ephemeral=True
            )
        if self.terminou:
            return
        self.terminou = True
        for item in self.children:
            item.disabled = True

        escolha_aeon = random.choice(list(_DUELO_ESCOLHAS.keys()))
        placar = _placar_duelo[self.autor_id]

        nome_user = _DUELO_ESCOLHAS[escolha_user]["emoji"] + " " + _DUELO_ESCOLHAS[escolha_user]["nome"]
        nome_aeon = _DUELO_ESCOLHAS[escolha_aeon]["emoji"] + " " + _DUELO_ESCOLHAS[escolha_aeon]["nome"]

        if escolha_user == escolha_aeon:
            placar["empates"] += 1
            frase = random.choice(_DUELO_EMPATE).format(user=interaction.user.mention, escolha_user=nome_user)
        elif _DUELO_ESCOLHAS[escolha_user]["vence"] == escolha_aeon:
            placar["vitorias"] += 1
            frase = random.choice(_DUELO_VITORIA).format(
                user=interaction.user.mention, escolha_user=nome_user, escolha_aeon=nome_aeon
            )
        else:
            placar["derrotas"] += 1
            frase = random.choice(_DUELO_DERROTA).format(
                user=interaction.user.mention, escolha_user=nome_user, escolha_aeon=nome_aeon
            )

        texto = (
            f"🌑 **Aeon:** Você escolheu {nome_user}. Eu escolhi {nome_aeon}.\n\n"
            f"{frase}\n\n"
            f"🏆 Vitórias: **{placar['vitorias']}** | Derrotas: **{placar['derrotas']}** | Empates: **{placar['empates']}**"
        )
        self.add_item(_BotaoJogarDeNovoDuelo(self.autor_id))
        await interaction.response.edit_message(content=texto, view=self)

    @discord.ui.button(label="Sombra", style=discord.ButtonStyle.secondary, emoji="🌑", row=0)
    async def escolher_sombra(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._resolver(interaction, "sombra")

    @discord.ui.button(label="Névoa", style=discord.ButtonStyle.secondary, emoji="🌫️", row=0)
    async def escolher_nevoa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._resolver(interaction, "nevoa")

    @discord.ui.button(label="Chama", style=discord.ButtonStyle.secondary, emoji="🔥", row=0)
    async def escolher_chama(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._resolver(interaction, "chama")


async def iniciar_jogo_aeon_duelo(destino, autor):
    """Inicia o Duelo das Trevas (Sombra/Névoa/Chama) do Aeon. destino precisa ter .send() (ctx ou channel)."""
    view = JogoDueloView(autor.id)
    await destino.send(content=random.choice(_DUELO_INTRO), view=view)


# ────────────────────────────────────────
# JOGO DA CELESTIA #2 — "Memória Brilhante"
# 6 cartas, 3 pares de brilhos escondidos. Vire duas por vez e decore onde
# cada brilho está para encontrar todos os pares.
# ────────────────────────────────────────

_MEMORIA_EMOJIS_POOL = ["🌟", "💫", "⭐", "🌠", "☀️", "✨", "🪐", "🌈"]
_MEMORIA_OCULTA = "❓"

_MEMORIA_INTRO = [
    "🌟 **Celestia:** AAAAA vamos jogar memória!! 💫🤍✨ Escondi 3 pares de brilhos em 6 cartinhas!! "
    "Clica em duas por vez pra tentar achar os pares!! Presta atenção onde cada brilho tá!! 🌸",
    "🌟 **Celestia:** OOOI vem brincar de memória comigo?? ☀️🌟🤍 6 cartinhas, 3 pares escondidos!! "
    "Clica em duas, se não bater eu escondo de novo, então decora bem!! ✨",
]

_MEMORIA_PAR_ACHADO = [
    "ACHOUUU!! 😭🌟✨ Par encontrado, mandou muito bem!!",
    "AAAAA bateu certinho!! 💫🤍 Sua memória tá brilhando igual eu!!",
    "ISSOOO!! ☀️🌸✨ Mais um par na conta!!",
]

_MEMORIA_PAR_ERRADO = [
    "Ooown, não bateu dessa vez!! 🌟🤍 Escondendo de novo... decora bem, viu?? ✨",
    "Quase!! 😭🌸 Não eram iguais, mas guarda na memória pra próxima!! 💫",
    "Ainda não!! ☀️🤍 Escondi de novo, mas você já sabe onde não é!! 🌟",
]

_MEMORIA_VITORIA = (
    "AAAAAAAAA VOCÊ ACHOU TODOS OS PARES!! 😭🌟💫✨🤍 "
    "Sua memória é IMBATÍVEL, sério mesmo!! Fico tão orgulhosa!! 🏆🌸☀️"
)


class _BotaoJogarDeNovoMemoria(discord.ui.Button):
    def __init__(self, autor_id: int):
        super().__init__(label="🔁 Jogar de novo", style=discord.ButtonStyle.primary, row=2)
        self.autor_id = autor_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.autor_id:
            return await interaction.response.send_message(
                "🌟 **Celestia:** essa brincadeira não é sua, mas fica à vontade pra começar a sua!! 🌸",
                ephemeral=True
            )
        nova_view = JogoMemoriaView(self.autor_id)
        await interaction.response.edit_message(
            content=nova_view.texto_estado(random.choice(_MEMORIA_INTRO)), view=nova_view
        )


class JogoMemoriaView(discord.ui.View):
    """Jogo da memória: 6 cartas, 3 pares de brilhos escondidos."""

    def __init__(self, autor_id: int):
        super().__init__(timeout=60)
        self.autor_id = autor_id
        self.terminou = False
        emojis_pares = random.sample(_MEMORIA_EMOJIS_POOL, 3)
        self.cartas = emojis_pares * 2
        random.shuffle(self.cartas)
        self.reveladas = [False] * 6   # pares já encontrados (permanente)
        self.selecionadas = []          # índices virados nesta jogada (temporário)
        self.tentativas = 0
        self.pares_encontrados = 0
        self.ultimo_log = ""
        self._montar_botoes()

    def _montar_botoes(self):
        self.clear_items()
        for i in range(6):
            mostrar = self.reveladas[i] or i in self.selecionadas
            emoji = self.cartas[i] if mostrar else _MEMORIA_OCULTA
            estilo = discord.ButtonStyle.success if self.reveladas[i] else discord.ButtonStyle.secondary
            botao = discord.ui.Button(
                label=emoji, style=estilo, row=i // 3, disabled=self.reveladas[i] or self.terminou
            )
            botao.callback = self._callback_carta(i)
            self.add_item(botao)

    def _callback_carta(self, indice: int):
        async def _callback(interaction: discord.Interaction):
            await self._clicar(interaction, indice)
        return _callback

    def texto_estado(self, cabecalho: str = "") -> str:
        partes = []
        if cabecalho:
            partes.append(f"🌟 **Celestia:** {cabecalho}")
        if self.ultimo_log:
            partes.append(self.ultimo_log)
        partes.append(
            f"✨ Pares encontrados: **{self.pares_encontrados}/3** | Tentativas: **{self.tentativas}**"
        )
        return "\n\n".join(partes)

    async def _clicar(self, interaction: discord.Interaction, indice: int):
        if interaction.user.id != self.autor_id:
            return await interaction.response.send_message(
                "🌟 **Celestia:** essa brincadeira não é sua, mas fica à vontade pra começar a sua!! 🌸",
                ephemeral=True
            )
        if self.terminou or self.reveladas[indice] or indice in self.selecionadas:
            return

        self.selecionadas.append(indice)

        if len(self.selecionadas) == 1:
            self._montar_botoes()
            return await interaction.response.edit_message(content=self.texto_estado(), view=self)

        # segunda carta virada — resolve a jogada
        self.tentativas += 1
        i1, i2 = self.selecionadas
        if self.cartas[i1] == self.cartas[i2]:
            self.reveladas[i1] = True
            self.reveladas[i2] = True
            self.pares_encontrados += 1
            self.ultimo_log = random.choice(_MEMORIA_PAR_ACHADO)
        else:
            self.ultimo_log = random.choice(_MEMORIA_PAR_ERRADO)

        self.selecionadas = []

        if self.pares_encontrados >= 3:
            self.terminou = True
            placar = _placar_memoria[self.autor_id]
            if placar["melhor_tentativas"] is None or self.tentativas < placar["melhor_tentativas"]:
                placar["melhor_tentativas"] = self.tentativas
            self._montar_botoes()
            self.add_item(_BotaoJogarDeNovoMemoria(self.autor_id))
            texto = (
                f"🌟 **Celestia:** {_MEMORIA_VITORIA}\n\n"
                f"✨ Tentativas usadas: **{self.tentativas}** | Melhor recorde: **{placar['melhor_tentativas']}**"
            )
            return await interaction.response.edit_message(content=texto, view=self)

        self._montar_botoes()
        await interaction.response.edit_message(content=self.texto_estado(), view=self)


async def iniciar_jogo_celestia_memoria(destino, autor):
    """Inicia o jogo da Memória Brilhante da Celestia. destino precisa ter .send() (ctx ou channel)."""
    view = JogoMemoriaView(autor.id)
    await destino.send(content=view.texto_estado(random.choice(_MEMORIA_INTRO)), view=view)


# ────────────────────────────────────────
# JOGO DOS DOIS — "Encruzilhada da Dualidade"
# Duas escolhas em sequência — Luz ou Trevas — culminando num título único
# comentado pelos dois gatos juntos.
# ────────────────────────────────────────

_ENCRUZILHADA_INTRO = (
    "🌑 **Aeon:** ...uma encruzilhada se abre à sua frente. 🖤🌌\n"
    "🌟 **Celestia:** DUAS ESTRADAS!! 😭🌟🤍✨ Luz ou Trevas — escolha a primeira!!\n\n"
    "Qual caminho você segue?"
)

_ENC_ESTAGIO1 = {
    "trevas": (
        "🌑 **Aeon:** *acena, quase satisfeito* ...as sombras te aceitam. 🖤🌑 "
        "Um segundo caminho se abre agora. Escolha de novo: Luz ou Trevas?"
    ),
    "luz": (
        "🌟 **Celestia:** AAAAA a luz!! 😭🌟✨ Que escolha linda!! "
        "Mas o caminho continua — mais uma escolha te espera: Luz ou Trevas??"
    ),
}

_ENC_FINAIS = {
    ("trevas", "trevas"): (
        "🏆 **Título alcançado: Guardião das Sombras**\n\n"
        "🌑 **Aeon:** *inclina a cabeça com respeito raro* ...você não hesitou nenhuma vez. 🖤🌌 "
        "As trevas puras reconhecem os seus.\n"
        "🌟 **Celestia:** Uau, comprometido do começo ao fim!! 😭🤍 Até eu respeito isso!! ✨"
    ),
    ("trevas", "luz"): (
        "🏆 **Título alcançado: Caminhante do Crepúsculo**\n\n"
        "🌑 **Aeon:** ...começou nas sombras e encontrou a luz. 🖤🌙 Equilíbrio não é fraqueza.\n"
        "🌟 **Celestia:** AAAA isso é tão bonito!! 😭🌟✨ Das trevas pra luz — uma jornada de verdade!! 💫"
    ),
    ("luz", "trevas"): (
        "🏆 **Título alcançado: Chama Renascida**\n\n"
        "🌟 **Celestia:** Começou brilhando e depois foi explorar as sombras?? 😳🌟 Corajoso!!\n"
        "🌑 **Aeon:** *um leve traço de aprovação* ...a luz que não teme a escuridão. 🖤🌌 Raro."
    ),
    ("luz", "luz"): (
        "🏆 **Título alcançado: Portador da Aurora**\n\n"
        "🌟 **Celestia:** LUZ E LUZ!! 😭🌟💫✨🤍 VOCÊ É PURO BRILHO DO COMEÇO AO FIM!!\n"
        "🌑 **Aeon:** *observa em silêncio* ...nem as trevas negam quando o brilho é genuíno. 🖤🌙"
    ),
}


class _BotaoEncruzilhadaFinal(discord.ui.Button):
    def __init__(self, autor_id: int):
        super().__init__(label="🔁 Jogar de novo", style=discord.ButtonStyle.primary, row=1)
        self.autor_id = autor_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.autor_id:
            return await interaction.response.send_message(
                "🌑 **Aeon:** ...essa jornada não é sua. 🖤", ephemeral=True
            )
        nova_view = JogoEncruzilhadaView(self.autor_id)
        await interaction.response.edit_message(content=_ENCRUZILHADA_INTRO, view=nova_view)


class JogoEncruzilhadaView(discord.ui.View):
    """Duas escolhas — Luz ou Trevas — culminando num título de dualidade."""

    def __init__(self, autor_id: int):
        super().__init__(timeout=30)
        self.autor_id = autor_id
        self.estagio = 1
        self.caminho = []
        self.terminou = False

    async def _escolher(self, interaction: discord.Interaction, escolha: str):
        if interaction.user.id != self.autor_id:
            return await interaction.response.send_message(
                "🌑 **Aeon:** ...essa jornada não é sua. 🖤", ephemeral=True
            )
        if self.terminou:
            return

        self.caminho.append(escolha)

        if self.estagio == 1:
            self.estagio = 2
            texto = _ENC_ESTAGIO1[escolha]
            return await interaction.response.edit_message(content=texto, view=self)

        # estágio final
        self.terminou = True
        for item in self.children:
            item.disabled = True
        placar = _placar_encruzilhada[self.autor_id]
        placar["jogos"] += 1
        chave = tuple(self.caminho)
        texto = _ENC_FINAIS[chave]
        self.add_item(_BotaoEncruzilhadaFinal(self.autor_id))
        await interaction.response.edit_message(content=texto, view=self)

    @discord.ui.button(label="Trevas", style=discord.ButtonStyle.secondary, emoji="🌑", row=0)
    async def escolher_trevas(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._escolher(interaction, "trevas")

    @discord.ui.button(label="Luz", style=discord.ButtonStyle.secondary, emoji="☀️", row=0)
    async def escolher_luz(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._escolher(interaction, "luz")


async def iniciar_jogo_duo_encruzilhada(destino, autor):
    """Inicia a Encruzilhada da Dualidade — jogo dos dois gatos juntos. destino precisa ter .send() (ctx ou channel)."""
    view = JogoEncruzilhadaView(autor.id)
    await destino.send(content=_ENCRUZILHADA_INTRO, view=view)


# ══════════════════════════════════════════════
# COMANDOS
# ══════════════════════════════════════════════

@bot.command(name="aeon")
async def cmd_aeon(ctx, *, texto: str = None):
    """Fala diretamente com o Aeon."""
    if not texto:
        return await ctx.send(_fala_aeon("...me chamou. Diga algo. 🖤🌑"))
    await ctx.reply(_fala_aeon(random.choice(AEON_REACOES_FOFAS)))


@bot.command(name="celestia")
async def cmd_celestia(ctx, *, texto: str = None):
    """Fala diretamente com a Celestia."""
    if not texto:
        return await ctx.send(_fala_celestia("OI!! Me fala algo!! 🤍✨🌟"))
    await ctx.reply(_fala_celestia(random.choice(CELESTIA_REACOES_FOFAS)))


@bot.command(name="duo")
async def cmd_duo(ctx, *, texto: str = None):
    """Os dois respondem ao mesmo tempo."""
    if not texto:
        return await ctx.send(random.choice(AMBOS_APRESENTACAO))
    await ctx.reply(
        f"🌑 **Aeon:** {random.choice(AEON_REACOES_FOFAS)}\n"
        f"🌟 **Celestia:** {random.choice(CELESTIA_REACOES_FOFAS)}"
    )


async def _enviar_ajuda(ctx):
    embed = discord.Embed(
        title="🌑☀️ Aeon & Celestia — Guia",
        description="Dois gatos, uma alma. Trevas e Luz em equilíbrio.",
        color=0x2b2b3b
    )
    embed.add_field(
        name="🗣️ Como conversar",
        value=(
            "Mencione `@Aeon & Celestia` ou use os nomes **aeon** / **celestia** na mensagem.\n"
            "Ex: `aeon, o que você acha da escuridão?`\n"
            "Ex: `celestia me anime!`"
        ),
        inline=False
    )
    embed.add_field(
        name="⚙️ Comandos",
        value=(
            "`.aeon [texto]` — fala só com o Aeon\n"
            "`.celestia [texto]` — fala só com a Celestia\n"
            "`.duo [texto]` — os dois respondem juntos\n"
            "`.ajuda` ou `.help` — este menu"
        ),
        inline=False
    )
    embed.add_field(
        name="🎮 Joguinhos — qual escolher?",
        value=(
            "Os jogos não usam comando com ponto, é só falar no chat:\n\n"
            "🌑 **\"vamos brincar aeon\"** — **Achar a Sombra**: "
            "o Aeon se esconde em 1 de 5 sombras, ache a certa!\n\n"
            "🌑 **\"duelo das trevas\"** — **Duelo das Trevas**: "
            "Sombra, Névoa ou Chama — um duelo rápido contra o Aeon!\n\n"
            "🌟 **\"vamos brincar celestia\"** — **Sequência Brilhante**: "
            "memorize e repita a sequência de brilhos da Celestia!\n\n"
            "🌟 **\"memória brilhante\"** — **Memória Brilhante**: "
            "vire as cartas e encontre os 3 pares de brilhos escondidos!\n\n"
            "🌑🌟 **\"encruzilhada\"** — **Encruzilhada da Dualidade**: "
            "escolha Luz ou Trevas duas vezes e desbloqueie um título único, "
            "com Aeon e Celestia comentando juntos!\n\n"
            "Se só disser **\"vamos brincar\"** sem escolher, os dois listam as opções "
            "pra você decidir qual jogo quer."
        ),
        inline=False
    )
    embed.add_field(
        name="💫 Interações especiais",
        value=(
            "`carinho no aeon` / `cafuné celestia`\n"
            "`abraça aeon` / `abraço celestia`\n"
            "`piada aeon` / `piada celestia`\n"
            "`bom dia aeon e celestia`\n"
            "`me motiva` / `faz magia`\n"
            "`luz e sombra` / `dualidade`\n"
            "...e muito mais para descobrir! 🌑☀️"
        ),
        inline=False
    )
    embed.set_footer(text="🌑 Aeon guarda as trevas. ☀️ Celestia guia a luz.")
    await ctx.send(embed=embed)

@bot.command(name="ajuda")
async def cmd_ajuda(ctx):
    """Mostra os comandos disponíveis."""
    await _enviar_ajuda(ctx)

@bot.command(name="help")
async def cmd_help(ctx):
    """Mostra os comandos disponíveis."""
    await _enviar_ajuda(ctx)


# ══════════════════════════════════════════════
# SISTEMA DE ENTRADA — VISITANTE / MEMBRO
# ══════════════════════════════════════════════

# IDs dos cargos
CARGO_VISITANTE_ID  = 1284263365547397120  # cargo exclusivo de visitante
CARGO_MEMBRO_ID     = 1284263397990596659  # cla member
CARGO_COMUM_ID      = 1290029716241256600  # verificado (recebido em ambos os casos)
CARGO_REMOVER_AO_CONFIRMAR_ID = 1290029492856815696  # removido automaticamente ao clicar no botão

IMAGE_TICKET            = "https://cdn.discordapp.com/attachments/926913851172204577/1514098200661983412/ChatGPT_Image_9_de_jun._de_2026_23_45_25.png?ex=6a2a2155&is=6a28cfd5&hm=1676da56b11b0efc33e422f78cee000cdb0b57bdeb14e30514b4ac18e535bd1d"
IMAGE_ENTRADA_VISITANTE = "https://cdn.discordapp.com/attachments/926913851172204577/1514086350603685948/ChatGPT_Image_9_de_jun._de_2026_22_46_43.png?ex=6a2a164c&is=6a28c4cc&hm=f4051c0619c741fd0fb72aa941c82d67290d1e4cbfbb7fe5cfa76d362660c3d2&"
IMAGE_ENTRADA_MEMBRO    = "https://cdn.discordapp.com/attachments/926913851172204577/1514088914200297553/ChatGPT_Image_9_de_jun._de_2026_23_08_19.png?ex=6a2a18af&is=6a28c72f&hm=dbd29acf877630fe2055e78e8801d187a579076c2fd0999e5c2e823af7db63ce"
IMAGE_BOAS_VINDAS       = "https://cdn.discordapp.com/attachments/926913851172204577/1514091940331651176/ChatGPT_Image_9_de_jun._de_2026_23_20_29.png?ex=6a2a1b81&is=6a28ca01&hm=99bf1e32f9039f292be06ef506310e4a2aaba6c8fd677aebe09a770b62634a3a"

CANAL_BOAS_VINDAS_ID = 1284257046740602901  # canal onde o bot manda boas-vindas

# Canais indicados no texto de boas-vindas
CANAIS_INDICADOS = (
    "👘 <#1369325512236732437> — confira e registre o ID da sua skin favorita\n"
    "👔 <#1284259266684780645> — as roupas mais raras e icônicas do servidor\n"
    "🧥 <#1289699941085610106> — inspirações e referências visuais\n"
    "📃 <#1284258011560542332> — faça seu registro oficial aqui!\n"
    "🌈 <#1296503545771720704> — personalize sua identidade no servidor"
)


async def _enviar_boas_vindas(guild: discord.Guild, member: discord.Member, tipo: str):
    """Envia uma mensagem de boas-vindas no canal definido."""
    canal = guild.get_channel(CANAL_BOAS_VINDAS_ID)
    if canal is None:
        return  # canal não encontrado, ignora silenciosamente

    if tipo == "visitante":
        embed = discord.Embed(
            title="🌙 Um novo rosto nas sombras...",
            description=(
                f"✨ {member.mention} acabou de chegar como **visitante**! ✨\n\n"
                "🌑 **Aeon:** *emerge lentamente das trevas e fixa os olhos dourados* "
                f"As sombras registraram sua chegada, {member.display_name}. 🖤🌑 "
                "Explore com calma. As trevas não mordem... na maioria das vezes.\n\n"
                "🌟 **Celestia:** AAAAA UM VISITANTE NOVO!! 😭🌟🤍✨ "
                f"BEM-VINDO(A) {member.display_name.upper()}!! "
                "Que alegria enorme te ver aqui!! "
                "Fique à vontade e aproveite cada cantinho!! ☀️🌸💫\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🗺️ **Por onde começar? Dá uma olhada nesses canais:**\n\n"
                f"{CANAIS_INDICADOS}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌙 *Fique à vontade, visitante. As portas estão abertas.*"
            ),
            color=0x2b2b3b
        )
        embed.add_field(
            name="📋 Só um avisinho fofo antes de continuar~ 🌸",
            value=(
                f"🌟 **Celestia:** Escuta aqui com carinho, {member.display_name}!! 😊🤍✨ "
                "Você vai ficar como **visitante por 7 diazinhos**, viu?? "
                "É só o tempinho da gente ir se conhecendo direitinho!! ☀️💫\n\n"
                "🌑 **Aeon:** ...e pra virar membro de verdade, as sombras pedem "
                "alguns detalhezinhos: 🖤🌑\n"
                "🔗 conta do **Roblox vinculada** ao Discord\n"
                "👕 pelo menos **uma camisa** com a skin do clã\n"
                "🏷️ a **tag do clã** equipada\n"
                "💬 e um pouquinho de **atividade** por aqui também!\n\n"
                "🌟 **Celestia:** Nada muito difícil, tá?? A gente confia em você!! "
                "Só ser você mesmo e aparecer de vez em quando que já ajuda demais!! 🌸🤍✨"
            ),
            inline=False
        )
    else:  # membro
        embed = discord.Embed(
            title="🌟 O círculo ganhou mais um...",
            description=(
                f"🎉 {member.mention} acaba de entrar oficialmente como **membro**! 🎉 <@&{CARGO_MEMBRO_ID}>\n\n"
                "🌟 **Celestia:** *explode em faíscas douradas de pura alegria* "
                f"MEMBRO NOVO MEMBRO NOVO!! 😭🌟🤍✨ "
                f"{member.display_name.upper()} AGORA FAZ PARTE DE VERDADE!! "
                "Meu brilho nunca foi tão intenso!! ☀️🌸💫\n\n"
                "🌑 **Aeon:** *sai das sombras com postura ereta e ronrona grave* "
                f"Bem-vindo ao círculo, {member.display_name}. 🖤🌑 "
                "Quem decide ficar carrega algo que poucos têm: comprometimento. "
                "As trevas reconhecem isso — e respeitam.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🗺️ **Agora que você é membro, explore esses canais:**\n\n"
                f"{CANAIS_INDICADOS}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌑☀️ *Seja muito feliz aqui. Você já é um dos nossos.*"
            ),
            color=0xf5c542
        )

    embed.set_image(url=IMAGE_BOAS_VINDAS)
    embed.set_footer(text="🌑 Aeon guarda as trevas. ☀️ Celestia guia a luz.")
    await canal.send(embed=embed)

    # ── Também manda no PV (privado) do membro ──────────────────────────────
    try:
        await member.send(embed=embed)
        print(f"[boas-vindas-{tipo}] DM enviada com sucesso para {member} ({member.id})")
    except discord.Forbidden:
        print(f"[boas-vindas-{tipo}] NÃO consegui mandar DM para {member} ({member.id}) — "
              f"a pessoa deve ter DMs de membros do servidor desativadas.")
    except discord.HTTPException as e:
        print(f"[boas-vindas-{tipo}] Erro HTTP ao mandar DM para {member} ({member.id}): {e!r}")


class BotaoVisitante(discord.ui.View):
    """View com botão de confirmação para visitantes."""

    def __init__(self):
        super().__init__(timeout=None)  # persistente até reinício

    @discord.ui.button(
        label="✅ Sim, quero entrar como Visitante!",
        style=discord.ButtonStyle.secondary,
        custom_id="entrada_visitante"
    )
    async def confirmar_visitante(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        guild  = interaction.guild
        member = interaction.user

        cargo_visitante = guild.get_role(CARGO_VISITANTE_ID)
        cargo_comum     = guild.get_role(CARGO_COMUM_ID)

        erros = []

        for cargo in [cargo_visitante, cargo_comum]:
            if cargo is None:
                erros.append(f"Cargo `{cargo}` não encontrado.")
                continue
            if cargo not in member.roles:
                try:
                    await member.add_roles(cargo, reason="Entrada como Visitante via botão")
                except discord.Forbidden:
                    erros.append(f"Sem permissão para adicionar o cargo **{cargo.name}**.")
                except discord.HTTPException as e:
                    erros.append(f"Erro ao adicionar **{cargo.name}**: {e}")

        cargo_remover = guild.get_role(CARGO_REMOVER_AO_CONFIRMAR_ID)
        if cargo_remover is not None and cargo_remover in member.roles:
            try:
                await member.remove_roles(cargo_remover, reason="Confirmou entrada como Visitante via botão")
            except discord.Forbidden:
                erros.append(f"Sem permissão para remover o cargo **{cargo_remover.name}**.")
            except discord.HTTPException as e:
                erros.append(f"Erro ao remover **{cargo_remover.name}**: {e}")

        if erros:
            await interaction.response.send_message(
                "⚠️ Ocorreu um problema ao atribuir seus cargos:\n" + "\n".join(erros),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "🌑 **Aeon:** *emerge das sombras e inclina a cabeça* "
                "As trevas registraram sua presença, visitante. 🖤🌑 "
                "Seja bem-vindo — explore com curiosidade.\n"
                "🌟 **Celestia:** AAAAA BEM-VINDO BEM-VINDO BEM-VINDO!! 😭🌟🤍✨ "
                "Que alegria ter você aqui!! Aproveite muito!! ☀️🌸",
                ephemeral=True
            )
            await _enviar_boas_vindas(guild, member, "visitante")


class BotaoMembro(discord.ui.View):
    """View com botão de confirmação para membros."""

    def __init__(self):
        super().__init__(timeout=None)  # persistente até reinício

    @discord.ui.button(
        label="✅ Sim, quero entrar como Membro!",
        style=discord.ButtonStyle.primary,
        custom_id="entrada_membro"
    )
    async def confirmar_membro(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        guild  = interaction.guild
        member = interaction.user

        cargo_membro = guild.get_role(CARGO_MEMBRO_ID)
        cargo_comum  = guild.get_role(CARGO_COMUM_ID)

        erros = []

        for cargo in [cargo_membro, cargo_comum]:
            if cargo is None:
                erros.append(f"Cargo `{cargo}` não encontrado.")
                continue
            if cargo not in member.roles:
                try:
                    await member.add_roles(cargo, reason="Entrada como Membro via botão")
                except discord.Forbidden:
                    erros.append(f"Sem permissão para adicionar o cargo **{cargo.name}**.")
                except discord.HTTPException as e:
                    erros.append(f"Erro ao adicionar **{cargo.name}**: {e}")

        cargo_remover = guild.get_role(CARGO_REMOVER_AO_CONFIRMAR_ID)
        if cargo_remover is not None and cargo_remover in member.roles:
            try:
                await member.remove_roles(cargo_remover, reason="Confirmou entrada como Membro via botão")
            except discord.Forbidden:
                erros.append(f"Sem permissão para remover o cargo **{cargo_remover.name}**.")
            except discord.HTTPException as e:
                erros.append(f"Erro ao remover **{cargo_remover.name}**: {e}")

        if erros:
            await interaction.response.send_message(
                "⚠️ Ocorreu um problema ao atribuir seus cargos:\n" + "\n".join(erros),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "🌑 **Aeon:** *sai das sombras com postura ereta* "
                "Bem-vindo ao círculo, membro. 🖤🌑 "
                "As trevas reconhecem quem decidiu ficar.\n"
                "🌟 **Celestia:** MEMBRO OFICIAL MEMBRO OFICIAL!! 😭🌟🤍✨ "
                "Você faz parte agora de verdade!! Seja muito feliz aqui!! ☀️🌸💫",
                ephemeral=True
            )
            await _enviar_boas_vindas(guild, member, "membro")


@bot.command(name="visitante")
@commands.has_permissions(manage_roles=True)
async def cmd_visitante(ctx):
    """Envia a mensagem de boas-vindas para visitantes com botão de confirmação."""
    embed = discord.Embed(
        title="🌑☀️ Bem-vindo(a) ao servidor!",
        description=(
            "Olá! Parece que você chegou como **visitante**. 🌙\n\n"
            "🌑 **Aeon:** *emerge das trevas e observa você com curiosidade* "
            "Visitante. 🖤 As sombras estão curiosas sobre quem você é. "
            "Se quiser explorar este lugar, basta confirmar abaixo.\n\n"
            "🌟 **Celestia:** *espalha faíscas douradas animada* "
            "AAAAA SEJA BEM-VINDO(A)!! 😭🌟🤍✨ "
            "Quer dar uma olhadinha no servidor?? "
            "Clica no botão que a gente te recebe com muito brilho!! ☀️🌸\n\n"
            "─────────────────────────────\n"
            "Ao clicar em **\"Sim, quero entrar como Visitante!\"** você receberá "
            "acesso de visitante ao servidor. 🌙🖤"
        ),
        color=0x2b2b3b
    )
    embed.set_image(url=IMAGE_ENTRADA_VISITANTE)
    embed.set_footer(text="🌑 Aeon guarda as trevas. ☀️ Celestia guia a luz.")

    await ctx.send(embed=embed, view=BotaoVisitante())


@bot.command(name="membro")
@commands.has_permissions(manage_roles=True)
async def cmd_membro(ctx):
    """Envia a mensagem de boas-vindas para membros com botão de confirmação."""
    embed = discord.Embed(
        title="🌟🖤 Quer fazer parte como Membro?",
        description=(
            "Você está prestes a se tornar um **membro oficial** do servidor! ✨\n\n"
            "🌟 **Celestia:** *brilha com uma luz especial e calorosa* "
            "OI OI OI!! 😭🌟🤍 "
            "Ser membro significa que você decidiu ficar de verdade!! "
            "Isso deixa meu brilho TRIPLICADO!! ☀️🌸💫\n\n"
            "🌑 **Aeon:** *inclina a cabeça com reconhecimento silencioso* "
            "Membro. 🖤🌑 "
            "Quem decide ficar carrega algo que os visitantes ainda não têm: "
            "comprometimento. As trevas respeitam isso.\n\n"
            "─────────────────────────────\n"
            "Ao clicar em **\"Sim, quero entrar como Membro!\"** você receberá "
            "o cargo de membro e acesso completo ao servidor. 🌙🌟"
        ),
        color=0xf5c542
    )
    embed.set_image(url=IMAGE_ENTRADA_MEMBRO)
    embed.set_footer(text="🌑 Aeon guarda as trevas. ☀️ Celestia guia a luz.")

    await ctx.send(embed=embed, view=BotaoMembro())


# ══════════════════════════════════════════════
# SISTEMA DE TICKET — ANJOS (ajuda, conselho...)
# ══════════════════════════════════════════════

CANAL_TICKET_ANJO_ID      = 1514427068589543565  # canal do painel de abertura
CANAL_REIVINDICAR_ANJO_ID = 1493410007113400321  # canal onde os anjos veem e reivindicam
CANAL_LOGS_ANJO_ID        = 1290058994794106881  # canal de logs dos tickets de anjo
CATEGORIA_TICKET_ID       = 1284276079401500763  # categoria onde os tickets são criados
CARGO_ANJO_ID             = 1493402287622848522  # cargo dos anjos

# ── Sistema de XP / Ranking de Nível (estilo Lorrita) ───────────────────────
CANAL_XP_ID = 1529852809850130583  # canal onde o ranking fica fixo (topo) e os level-ups são anunciados (embaixo)
CARGO_XP_ID = 1290029716241256600  # cargo dos membros que participam do ranking de XP
IMAGE_TICKET_ANJO         = "https://cdn.discordapp.com/attachments/926913851172204577/1514101982342807703/ChatGPT_Image_9_de_jun._de_2026_23_56_07.png?ex=6a2a24db&is=6a28d35b&hm=83c84d1ff94bf2277c9551ce4200af863b852e4b9360a93b3522f609a811baeb"


async def _enviar_painel_anjos(guild: discord.Guild):
    """Envia (ou reenvia) o painel de abertura de tickets no canal correto.
    Evita duplicatas: deleta mensagens antigas do bot no canal antes de postar."""
    canal = guild.get_channel(CANAL_TICKET_ANJO_ID)
    if canal is None:
        return

    # Remove mensagens antigas do próprio bot no canal para não acumular painéis
    try:
        async for msg in canal.history(limit=50):
            if msg.author == guild.me:
                await msg.delete()
    except (discord.Forbidden, discord.HTTPException):
        pass

    embed = discord.Embed(
        title="🕊️ Precisa conversar? Os Anjos estão aqui.",
        description=(
            "🌟 **Celestia:** *brilha com uma luz suave e aconchegante* "
            "Às vezes a vida pesa, né?? 😭🌸🤍 "
            "Seja um conselho, um desabafo, uma dúvida ou só precisar de alguém pra ouvir — "
            "**os Anjos estão aqui por você!!** "
            "Não precisa carregar isso sozinho(a)!! ☀️💫\n\n"
            "🌑 **Aeon:** *emerge das sombras com voz mais suave que o habitual* "
            "Nem sempre as trevas são lugar de solidão. 🖤🌑 "
            "Se algo pesa — dúvida, conselho, um momento difícil — "
            "abra um ticket. Um Anjo virá. "
            "As sombras guardam segredos com cuidado.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🕊️ Clique no botão abaixo para abrir seu espaço privado.\n"
            "Só você e o Anjo que te atender poderão ver.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xe8d5f5
    )
    embed.set_image(url=IMAGE_TICKET_ANJO)
    embed.set_footer(text="🌑 Aeon guarda as trevas. ☀️ Celestia guia a luz. 🕊️ Os Anjos cuidam de você.")

    await canal.send(embed=embed, view=BotaoAbrirTicketAnjo())


class BotaoFecharTicketAnjo(discord.ui.View):
    """Botão de fechar ticket — aparece dentro do canal do ticket."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 Fechar ticket",
        style=discord.ButtonStyle.danger,
        custom_id="fechar_ticket_anjo"
    )
    async def fechar_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        canal  = interaction.channel
        guild  = interaction.guild
        member = interaction.user

        cargo_anjo = guild.get_role(CARGO_ANJO_ID)

        # Dono do ticket está no tópico: "... | ID: <id> | ANJO: <id>"
        topic = canal.topic or ""
        dono_id  = None
        anjo_id  = None
        for parte in topic.split("|"):
            parte = parte.strip()
            if parte.startswith("ID:"):
                try:
                    dono_id = int(parte.replace("ID:", "").strip())
                except ValueError:
                    pass
            if parte.startswith("ANJO:"):
                try:
                    anjo_id = int(parte.replace("ANJO:", "").strip())
                except ValueError:
                    pass

        eh_anjo_assumiu = member.id == anjo_id
        eh_cargo_anjo   = cargo_anjo in member.roles if cargo_anjo else False

        # ⚠️ Apenas quem tem cargo ANJO pode fechar — o criador do ticket NÃO pode
        if not (eh_anjo_assumiu or eh_cargo_anjo):
            return await interaction.response.send_message(
                "🕊️ Apenas **Anjos** podem fechar este ticket.\n"
                "🌟 **Celestia:** Só um Anjo pode encerrar esse espaço! ☀️🌸\n"
                "🌑 **Aeon:** ...as trevas só se abrem para quem tem asas. 🖤",
                ephemeral=True
            )

        await interaction.response.send_message(
            "🌑 **Aeon:** *inclina a cabeça lentamente* "
            "As sombras registraram o encerramento. 🖤🌑 Este espaço será fechado em instantes.\n"
            "🌟 **Celestia:** Que tudo tenha se resolvido com muito amor!! 😭🌸🤍✨ "
            "Até a próxima!!"
        )

        # ── Ranking de Anjos: registra o atendimento deste ticket ─────────────
        # Credita o Anjo que assumiu o ticket (ANJO: no tópico); se ninguém
        # assumiu formalmente, credita quem fechou (desde que tenha o cargo).
        atendente_id = anjo_id if anjo_id else member.id
        anjo_stats_semanal[atendente_id]["tickets"] += 1
        anjo_stats_mensal[atendente_id]["tickets"] += 1
        anjo_stats_diario[atendente_id]["tickets"] += 1
        await _salvar_anjo_stats()
        asyncio.create_task(_atualizar_ranking_anjo())
        # ─────────────────────────────────────────────────────────────────────

        # ── Gerar log no canal de logs antes de apagar o canal ───────────────
        canal_logs = guild.get_channel(CANAL_LOGS_ANJO_ID)
        if canal_logs:
            # Conta mensagens por membro com cargo Anjo (ignora bots)
            contagem_anjos: dict[int, int] = {}
            try:
                async for msg in canal.history(limit=None, oldest_first=True):
                    if msg.author.bot:
                        continue
                    membro_msg = guild.get_member(msg.author.id)
                    if membro_msg and cargo_anjo and cargo_anjo in membro_msg.roles:
                        contagem_anjos[membro_msg.id] = contagem_anjos.get(membro_msg.id, 0) + 1
            except (discord.Forbidden, discord.HTTPException):
                pass

            # Obtém o dono do ticket
            dono_member  = guild.get_member(dono_id) if dono_id else None
            dono_mention = dono_member.mention if dono_member else (f"<@{dono_id}>" if dono_id else "Desconhecido")
            dono_nome    = dono_member.display_name if dono_member else str(dono_id or "Desconhecido")

            # Formata datas (UTC-3 Brasil)
            from datetime import timezone, timedelta
            BR = timezone(timedelta(hours=-3))
            data_abertura   = canal.created_at.astimezone(BR).strftime("%d/%m/%Y %H:%M")
            data_fechamento = discord.utils.utcnow().astimezone(BR).strftime("%d/%m/%Y %H:%M")

            # Monta texto de contagem de mensagens dos Anjos
            if contagem_anjos:
                linhas = []
                for uid, count in sorted(contagem_anjos.items(), key=lambda x: x[1], reverse=True):
                    m = guild.get_member(uid)
                    linhas.append(f"[ {count:>3} ] — {m.mention if m else f'<@{uid}>'}")
                contagem_texto = "\n".join(linhas)
            else:
                contagem_texto = "*Nenhuma mensagem de Anjo registrada.*"

            embed_log = discord.Embed(
                title="🕊️ Ticket de Anjo Fechado",
                color=0xe8d5f5
            )
            embed_log.add_field(
                name="Nome do Ticket",
                value=f"`{canal.name}`",
                inline=True
            )
            embed_log.add_field(
                name="Criado por",
                value=f"{dono_mention}\n*({dono_nome})*",
                inline=True
            )
            embed_log.add_field(
                name="Fechado por",
                value=member.mention,
                inline=True
            )
            embed_log.add_field(
                name="Data de Abertura",
                value=data_abertura,
                inline=True
            )
            embed_log.add_field(
                name="Data de Encerramento",
                value=data_fechamento,
                inline=True
            )
            embed_log.add_field(
                name="\u200b",
                value="\u200b",
                inline=True
            )
            embed_log.add_field(
                name="Motivo para fechar o Ticket",
                value="Sem motivo fornecido",
                inline=False
            )
            embed_log.add_field(
                name="Contagem de Mensagens Anjo",
                value=contagem_texto,
                inline=False
            )
            embed_log.set_footer(
                text="🕊️ Sistema de Tickets — Anjos  |  🌑 Aeon & ☀️ Celestia"
            )
            await canal_logs.send(embed=embed_log)
        # ─────────────────────────────────────────────────────────────────────

        await asyncio.sleep(5)
        await canal.delete(reason=f"Ticket fechado por {member}")


class BotaoReivindicarTicket(discord.ui.View):
    """Botão de reivindicar ticket — aparece no canal dos anjos."""

    def __init__(self, canal_ticket_id: int, dono_id: int):
        super().__init__(timeout=None)
        self.canal_ticket_id = canal_ticket_id
        self.dono_id         = dono_id

    @discord.ui.button(
        label="🕊️ Reivindicar ticket",
        style=discord.ButtonStyle.success,
        custom_id="reivindicar_ticket_anjo"
    )
    async def reivindicar(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        guild  = interaction.guild
        anjo   = interaction.user
        cargo_anjo = guild.get_role(CARGO_ANJO_ID)

        # Só quem tem o cargo de anjo pode reivindicar
        if cargo_anjo not in anjo.roles:
            return await interaction.response.send_message(
                "🌟 **Celestia:** Só os Anjos podem reivindicar um ticket! ☀️🌸",
                ephemeral=True
            )

        canal_ticket = guild.get_channel(self.canal_ticket_id)
        if canal_ticket is None:
            return await interaction.response.send_message(
                "⚠️ O canal do ticket não foi encontrado. Pode já ter sido fechado.",
                ephemeral=True
            )

        # Verifica se já foi reivindicado (tópico contém "ANJO:")
        topic = canal_ticket.topic or ""
        if "ANJO:" in topic:
            return await interaction.response.send_message(
                "🌑 **Aeon:** Este ticket já foi assumido por outro Anjo. 🖤",
                ephemeral=True
            )

        # Atualiza o tópico com o ID do anjo que assumiu
        novo_topic = f"{topic} | ANJO: {anjo.id}"
        await canal_ticket.edit(topic=novo_topic)

        # Remove permissão do cargo anjo inteiro do canal e dá só ao anjo que assumiu
        if cargo_anjo:
            await canal_ticket.set_permissions(cargo_anjo, overwrite=None)
        await canal_ticket.set_permissions(
            anjo,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_channels=True
        )

        # Avisa o dono do ticket que um anjo assumiu
        dono = guild.get_member(self.dono_id)
        aviso_dono = f"{dono.mention} " if dono else ""
        await canal_ticket.send(
            f"🕊️ {aviso_dono}**{anjo.display_name}** assumiu seu ticket e já está aqui por você! 🌸🤍\n"
            f"🌟 **Celestia:** AAAAA UM ANJO CHEGOU!! 😭✨ "
            f"Pode falar, {dono.display_name if dono else 'anjo'}!! Você está em boas mãos!! ☀️💫"
        )

        # Desabilita o botão na mensagem de reivindicação e edita para mostrar quem assumiu
        button.disabled = True
        button.label = f"✅ Assumido por {anjo.display_name}"
        button.style = discord.ButtonStyle.secondary
        await interaction.response.edit_message(
            content=(
                f"🕊️ **{anjo.display_name}** assumiu o ticket de "
                f"**{guild.get_member(self.dono_id).display_name if guild.get_member(self.dono_id) else 'usuário'}**!"
            ),
            view=self
        )


class BotaoAbrirTicketAnjo(discord.ui.View):
    """Botão no painel que abre um ticket de anjo."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🕊️ Abrir ticket",
        style=discord.ButtonStyle.primary,
        custom_id="abrir_ticket_anjo"
    )
    async def abrir_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        guild  = interaction.guild
        member = interaction.user

        categoria  = guild.get_channel(CATEGORIA_TICKET_ID)
        cargo_anjo = guild.get_role(CARGO_ANJO_ID)

        if categoria is None:
            return await interaction.response.send_message(
                "⚠️ Categoria de tickets não encontrada. Avise um Anjo!", ephemeral=True
            )

        # Verifica se já tem ticket aberto para esse usuário
        nome_canal = f"anjo-{member.name.lower().replace(' ', '-')}"
        canal_existente = discord.utils.get(categoria.channels, name=nome_canal)
        if canal_existente:
            return await interaction.response.send_message(
                f"🌟 **Celestia:** Você já tem um ticket aberto! {canal_existente.mention} ☀️🌸",
                ephemeral=True
            )

        # Canal inicial: visível só para o dono e o bot
        # Os anjos entram individualmente ao reivindicar
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                read_message_history=True
            ),
        }

        canal_ticket = await guild.create_text_channel(
            name=nome_canal,
            category=categoria,
            overwrites=overwrites,
            topic=f"Ticket de {member.display_name} | ID: {member.id}",
            reason=f"Ticket de anjo aberto por {member}"
        )

        # Mensagem de boas-vindas dentro do ticket
        embed = discord.Embed(
            title="🕊️ Seu espaço seguro chegou...",
            description=(
                f"Olá, {member.mention}! 🤍\n\n"
                "🌟 **Celestia:** *pousa suavemente ao seu lado* "
                "VOCÊ VEIO!! 😭🌸🤍✨ Fico TÃO feliz que você não ficou com isso sozinho(a)!! "
                "Aqui é um lugarzinho só seu — pode falar tudo com calma, sem pressa!! ☀️💫\n\n"
                "🌑 **Aeon:** *emerge das sombras com suavidade incomum* "
                f"{member.display_name}. 🖤🌑 "
                "As trevas também têm ouvidos. Pode falar — "
                "um dos nossos Anjos está a caminho. "
                "Você não está sozinho(a) nisso.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🕊️ *Aguarde um Anjo assumir seu atendimento...*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔒 *Quando tudo estiver resolvido, use o botão abaixo para fechar.*"
            ),
            color=0xe8d5f5
        )
        embed.set_image(url=IMAGE_TICKET_ANJO)
        embed.set_footer(text="🌑 Aeon guarda as trevas. ☀️ Celestia guia a luz. 🕊️ Os Anjos cuidam de você.")

        await canal_ticket.send(embed=embed, view=BotaoFecharTicketAnjo())

        # Avisa os anjos no canal de reivindicação
        canal_reiv = guild.get_channel(CANAL_REIVINDICAR_ANJO_ID)
        if canal_reiv:
            embed_reiv = discord.Embed(
                title="🕊️ Novo ticket aguardando um Anjo!",
                description=(
                    f"**{member.display_name}** ({member.mention}) precisa de ajuda. 🌸\n\n"
                    f"🌑 **Aeon:** Um novo pedido chegou às sombras. 🖤🌑 "
                    f"Quem entre os Anjos irá atender?\n\n"
                    f"📩 Canal: {canal_ticket.mention}\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Clique em **Reivindicar ticket** para assumir o atendimento.\n"
                    "Só o Anjo que reivindicar poderá ver e falar no ticket."
                ),
                color=0xe8d5f5
            )
            embed_reiv.set_footer(text="🕊️ Os Anjos cuidam de você.")
            await canal_reiv.send(
                content=f"<@&{CARGO_ANJO_ID}>",
                embed=embed_reiv,
                view=BotaoReivindicarTicket(canal_ticket.id, member.id)
            )

        await interaction.response.send_message(
            f"🌸 Seu ticket foi criado! {canal_ticket.mention}\n"
            "Um Anjo vai assumir seu atendimento em breve. 🕊️✨",
            ephemeral=True
        )

        # ── Log de abertura no canal de logs ────────────────────────────────
        canal_logs = guild.get_channel(CANAL_LOGS_ANJO_ID)
        if canal_logs:
            from datetime import timezone, timedelta
            BR = timezone(timedelta(hours=-3))
            data_abertura = canal_ticket.created_at.astimezone(BR).strftime("%d/%m/%Y %H:%M")

            embed_log_aberto = discord.Embed(
                title="🕊️ Ticket de Anjo Aberto",
                color=0x9b59b6
            )
            embed_log_aberto.add_field(
                name="Nome do Ticket",
                value=f"`{canal_ticket.name}`",
                inline=True
            )
            embed_log_aberto.add_field(
                name="Criado por",
                value=f"{member.mention}\n*({member.display_name})*",
                inline=True
            )
            embed_log_aberto.add_field(
                name="Data de Abertura",
                value=data_abertura,
                inline=True
            )
            embed_log_aberto.add_field(
                name="Canal",
                value=canal_ticket.mention,
                inline=False
            )
            embed_log_aberto.set_footer(
                text="🕊️ Sistema de Tickets — Anjos  |  🌑 Aeon & ☀️ Celestia"
            )
            await canal_logs.send(embed=embed_log_aberto)
        # ────────────────────────────────────────────────────────────────────


# ══════════════════════════════════════════════
# COMANDO !surpresachat — SOMENTE O DEV (CRIADOR_ID)
# Envia uma surpresa interativa no canal de boas-vindas.
# Uso: !surpresachat (no PV do bot)
# ══════════════════════════════════════════════

# ID do canal onde a surpresa será enviada
CANAL_SURPRESA_ID = 1284257046740602901

# GIF exibido ao resgatar a recompensa
GIF_RECOMPENSA = "https://i.pinimg.com/originals/f7/3e/16/f73e16cabe6afe5711a341dc909b8bd4.gif"

# Controla se já há uma surpresa ativa (evita duplicatas)
_surpresa_ativa: bool = False


class BotaoSurpresa(discord.ui.View):
    """Botão de resgate da surpresa. Desativa após o primeiro clique."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎁 Resgatar recompensa!",
        style=discord.ButtonStyle.success,
        custom_id="resgatar_surpresa"
    )
    async def resgatar(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        global _surpresa_ativa

        # Desativa o botão imediatamente para que só o primeiro clique valha
        button.disabled = True
        button.label = f"✅ Resgatado por {interaction.user.display_name}!"
        button.style = discord.ButtonStyle.secondary

        # Atualiza a mensagem original desabilitando o botão
        await interaction.message.edit(view=self)

        # Marca a surpresa como inativa
        _surpresa_ativa = False

        # Embed de parabéns com o GIF
        embed_ganhou = discord.Embed(
            title="🎉 Você foi o mais rápido!!",
            description=(
                f"✨ {interaction.user.mention} foi o(a) primeiro(a) a resgatar!! ✨\n\n"
                "🌟 **Celestia:** *EXPLODE em faíscas douradas de alegria pura* "
                f"PARABÉNS {interaction.user.display_name.upper()}!! 😭🌟🤍✨ "
                "VOCÊ FOI O MAIS RÁPIDO!! A RECOMPENSA É SUA DE DIREITO!! "
                "MEU CORAÇÃOZINHO DE LUZ TÁ TRANSBORDANDO!! ☀️🌸💫\n\n"
                "🌑 **Aeon:** *emerge das sombras e inclina a cabeça com respeito* "
                f"As trevas registraram. {interaction.user.display_name}. 🖤🌑 "
                "Agilidade e presença — as sombras reconhecem quem está atento. "
                "A recompensa foi conquistada com mérito."
            ),
            color=0xf5c542
        )
        embed_ganhou.set_image(url=GIF_RECOMPENSA)
        embed_ganhou.set_footer(text="🌑 Aeon guarda as trevas. ☀️ Celestia guia a luz. 🎁 A surpresa foi resgatada!")

        await interaction.response.send_message(embed=embed_ganhou)


# ══════════════════════════════════════════════════════════════════════
# RANKING DE ANJOS — mensagens, tempo em call e tickets atendidos
# Guarda tudo em anjo_ranking_data.json (mesma pasta do bot) para
# sobreviver a reinícios. Atualiza automaticamente o ranking no canal
# "logs anjo" a cada 5 minutos, sempre editando a mesma mensagem.
# ══════════════════════════════════════════════════════════════════════

CANAL_RANKING_ANJO_ID = 1525593159525204079  # canal "logs anjo" — onde o ranking é postado

# Se existir um Volume anexado no Railway, a variável RAILWAY_VOLUME_MOUNT_PATH
# aponta pra pasta persistente (não é apagada em novos deploys). Sem Volume
# (rodando local, VPS, etc.) cai na pasta onde o próprio script está.
_ANJO_DATA_DIR = os.getenv("RAILWAY_VOLUME_MOUNT_PATH") or os.path.dirname(os.path.abspath(__file__))
_ANJO_DATA_FILE = os.path.join(_ANJO_DATA_DIR, "anjo_ranking_data.json")

# Pesos usados para calcular a pontuação geral do ranking — ajuste à vontade
_PESO_MENSAGEM    = 1     # pontos por mensagem no chat
_PESO_MINUTO_CALL = 0.5   # pontos por minuto em call
_PESO_TICKET      = 20    # pontos por ticket atendido

# Dois rankings independentes — semanal e mensal — que contam as MESMAS
# ações (mensagens, tempo em call, tickets), mas cada um só é zerado pelo
# seu próprio comando: .reiniciaranjo (semanal) e .reiniciaranjo2 (mensal).
_TITULO_RANKING = {
    "semanal": "🕊️ Ranking Anjo Semanal",
    "mensal":  "🕊️ Ranking Anjo Mensal",
}

anjo_stats_semanal: dict = defaultdict(lambda: {"mensagens": 0, "tempo_call": 0.0, "tickets": 0, "penalidade": 0.0})
anjo_stats_mensal: dict  = defaultdict(lambda: {"mensagens": 0, "tempo_call": 0.0, "tickets": 0, "penalidade": 0.0})

_anjo_ranking_message_id_semanal = None  # ID da mensagem de ranking semanal já postada (editada, não duplicada)
_anjo_ranking_message_id_mensal  = None  # ID da mensagem de ranking mensal já postada (editada, não duplicada)

# Referência de "entrou na call" separada por período, pra permitir resetar
# um ranking (ex: semanal) sem bagunçar a contagem "ao vivo" do outro (mensal).
_anjo_voice_join_semanal: dict = {}   # user_id -> time.time() (referência do período semanal)
_anjo_voice_join_mensal: dict  = {}   # user_id -> time.time() (referência do período mensal)
_anjo_voice_join: dict = {}           # user_id -> time.time() — só pra saber quem tá "🔴 em call agora"

_anjo_stats_lock = None           # criado em on_ready (precisa de event loop rodando)


def _carregar_anjo_stats() -> None:
    """Carrega estatísticas salvas em disco, se existirem. Roda antes do bot conectar."""
    global _anjo_ranking_message_id_semanal, _anjo_ranking_message_id_mensal
    if not os.path.exists(_ANJO_DATA_FILE):
        return
    try:
        with open(_ANJO_DATA_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)

        if "stats_semanal" in dados or "stats_mensal" in dados:
            # Formato novo — semanal e mensal já separados
            for uid_str, valores in dados.get("stats_semanal", {}).items():
                anjo_stats_semanal[int(uid_str)] = {
                    "mensagens":  valores.get("mensagens", 0),
                    "tempo_call": valores.get("tempo_call", 0.0),
                    "tickets":    valores.get("tickets", 0),
                    "penalidade": valores.get("penalidade", 0.0),
                }
            for uid_str, valores in dados.get("stats_mensal", {}).items():
                anjo_stats_mensal[int(uid_str)] = {
                    "mensagens":  valores.get("mensagens", 0),
                    "tempo_call": valores.get("tempo_call", 0.0),
                    "tickets":    valores.get("tickets", 0),
                    "penalidade": valores.get("penalidade", 0.0),
                }
            _anjo_ranking_message_id_semanal = dados.get("ranking_message_id_semanal")
            _anjo_ranking_message_id_mensal  = dados.get("ranking_message_id_mensal")
        else:
            # Formato antigo (um único ranking) — migra o histórico existente
            # pros dois novos rankings, pra ninguém perder pontos na troca.
            for uid_str, valores in dados.get("stats", {}).items():
                valor_migrado = {
                    "mensagens":  valores.get("mensagens", 0),
                    "tempo_call": valores.get("tempo_call", 0.0),
                    "tickets":    valores.get("tickets", 0),
                    "penalidade": valores.get("penalidade", 0.0),
                }
                anjo_stats_semanal[int(uid_str)] = dict(valor_migrado)
                anjo_stats_mensal[int(uid_str)]  = dict(valor_migrado)
            _anjo_ranking_message_id_semanal = dados.get("ranking_message_id")
            _anjo_ranking_message_id_mensal  = None
    except (json.JSONDecodeError, OSError, ValueError):
        pass


async def _salvar_anjo_stats() -> None:
    """Salva estatísticas em disco de forma atômica (escreve em .tmp e substitui)."""
    dados = {
        "stats_semanal": {str(uid): v for uid, v in anjo_stats_semanal.items()},
        "stats_mensal":  {str(uid): v for uid, v in anjo_stats_mensal.items()},
        "ranking_message_id_semanal": _anjo_ranking_message_id_semanal,
        "ranking_message_id_mensal":  _anjo_ranking_message_id_mensal,
    }
    tmp_path = _ANJO_DATA_FILE + ".tmp"

    def _escrever():
        os.makedirs(_ANJO_DATA_DIR, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, _ANJO_DATA_FILE)

    try:
        loop = asyncio.get_event_loop()
        async with (_anjo_stats_lock or asyncio.Lock()):
            await loop.run_in_executor(None, _escrever)
    except OSError:
        pass


def _tempo_call_atual(membro_id: int, periodo: str) -> float:
    """Tempo total em call (num período — 'semanal' ou 'mensal'): sessões já
    fechadas (salvas) + a sessão atual em andamento, se a pessoa estiver em
    call neste exato momento (contagem 'ao vivo'). Cada período tem sua
    própria referência de início de sessão, pra resetar um sem afetar o outro."""
    stats_dict = anjo_stats_semanal if periodo == "semanal" else anjo_stats_mensal
    voice_dict = _anjo_voice_join_semanal if periodo == "semanal" else _anjo_voice_join_mensal
    base = stats_dict.get(membro_id, {}).get("tempo_call", 0.0)
    inicio_sessao_atual = voice_dict.get(membro_id)
    if inicio_sessao_atual:
        base += time.time() - inicio_sessao_atual
    return base


def _formatar_tempo_call(segundos: float) -> str:
    segundos = int(segundos)
    horas, resto = divmod(segundos, 3600)
    minutos, _ = divmod(resto, 60)
    if horas:
        return f"{horas}h{minutos:02d}m"
    return f"{minutos}m"


def _montar_embed_ranking(guild: discord.Guild, periodo: str) -> discord.Embed:
    """Monta o embed de um dos dois rankings. periodo: 'semanal' ou 'mensal'."""
    stats_dict = anjo_stats_semanal if periodo == "semanal" else anjo_stats_mensal
    cargo_anjo = guild.get_role(CARGO_ANJO_ID)
    membros_anjo = cargo_anjo.members if cargo_anjo else []

    linhas = []
    for membro in membros_anjo:
        if membro.bot:
            continue
        s = stats_dict.get(membro.id, {"mensagens": 0, "tempo_call": 0.0, "tickets": 0, "penalidade": 0.0})
        tempo_call_ao_vivo = _tempo_call_atual(membro.id, periodo)
        pontuacao = (
            s["mensagens"] * _PESO_MENSAGEM
            + (tempo_call_ao_vivo / 60) * _PESO_MINUTO_CALL
            + s["tickets"] * _PESO_TICKET
            - s.get("penalidade", 0.0)
        )
        linhas.append((membro, s, tempo_call_ao_vivo, pontuacao))

    linhas.sort(key=lambda x: x[3], reverse=True)

    medalhas = ["🥇", "🥈", "🥉"]
    descricao_linhas = []
    if linhas:
        for i, (membro, s, tempo_call_ao_vivo, pontuacao) in enumerate(linhas):
            prefixo = medalhas[i] if i < 3 else f"`#{i + 1:>2}`"
            em_call_agora = " 🔴" if membro.id in _anjo_voice_join else ""
            penalidade_texto = (
                f" · ⛔ `-{s.get('penalidade', 0.0):.0f}` punição" if s.get("penalidade", 0.0) > 0 else ""
            )
            descricao_linhas.append(
                f"{prefixo} **{membro.display_name}** — 💬 `{s['mensagens']}` msgs · "
                f"🎙️ `{_formatar_tempo_call(tempo_call_ao_vivo)}`{em_call_agora} em call · "
                f"🕊️ `{s['tickets']}` tickets{penalidade_texto} — **{pontuacao:.0f} pts**"
            )
    else:
        descricao_linhas.append("*Nenhum Anjo encontrado no servidor.*")

    embed = discord.Embed(
        title=_TITULO_RANKING[periodo],
        description="\n".join(descricao_linhas),
        color=0xe8d5f5,
        timestamp=discord.utils.utcnow()
    )
    rotulo = "semanal" if periodo == "semanal" else "mensal"
    embed.set_footer(text=f"🌑 Aeon & ☀️ Celestia — ranking {rotulo}, atualizado automaticamente a cada 1 min")
    return embed


async def _limpar_duplicadas_e_achar_ranking(canal: discord.TextChannel, titulo: str):
    """Varre o histórico do canal, apaga rankings duplicados antigos (deixando
    só o mais recente) e devolve essa mensagem mais recente pra ser editada.
    Serve de rede de segurança caso o ID salvo se perca (ex: deploy sem Volume).
    titulo filtra qual dos dois rankings (semanal/mensal) estamos procurando."""
    mensagens_ranking = []
    try:
        async for msg in canal.history(limit=50):
            if msg.author.id == bot.user.id and msg.embeds and msg.embeds[0].title == titulo:
                mensagens_ranking.append(msg)
    except (discord.Forbidden, discord.HTTPException):
        return None

    if not mensagens_ranking:
        return None

    # canal.history() vem do mais novo pro mais antigo por padrão
    mais_recente, *duplicadas = mensagens_ranking
    for dup in duplicadas:
        try:
            await dup.delete()
        except discord.HTTPException:
            pass
    return mais_recente


async def _atualizar_ranking_anjo_periodo(periodo: str) -> None:
    """Atualiza (ou cria, se ainda não existir) a mensagem de UM dos rankings
    (semanal ou mensal) no canal de logs anjo."""
    global _anjo_ranking_message_id_semanal, _anjo_ranking_message_id_mensal

    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return

    canal = guild.get_channel(CANAL_RANKING_ANJO_ID)
    if canal is None:
        return

    embed = _montar_embed_ranking(guild, periodo)
    titulo = _TITULO_RANKING[periodo]
    msg_id_salvo = _anjo_ranking_message_id_semanal if periodo == "semanal" else _anjo_ranking_message_id_mensal

    mensagem = None
    if msg_id_salvo:
        try:
            mensagem = await canal.fetch_message(msg_id_salvo)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            mensagem = None

    # Não achou pelo ID salvo (ex: perdeu o JSON num redeploy sem Volume) —
    # procura no histórico do canal e limpa qualquer duplicada antes de criar uma nova
    if mensagem is None:
        mensagem = await _limpar_duplicadas_e_achar_ranking(canal, titulo)

    if mensagem:
        try:
            await mensagem.edit(embed=embed)
        except discord.HTTPException:
            mensagem = None

    if mensagem is None:
        try:
            mensagem = await canal.send(embed=embed)
        except discord.HTTPException:
            return

    if periodo == "semanal":
        _anjo_ranking_message_id_semanal = mensagem.id
    else:
        _anjo_ranking_message_id_mensal = mensagem.id


async def _atualizar_ranking_anjo() -> None:
    """Atualiza os DOIS rankings (semanal primeiro, mensal logo abaixo dele)
    e salva tudo em disco — inclusive o resumo diário, pra sobreviver a
    reinícios. Semanal é enviado primeiro na primeira vez que os rankings
    são criados, então ele fica sempre por cima do mensal no canal."""
    await _atualizar_ranking_anjo_periodo("semanal")
    await _atualizar_ranking_anjo_periodo("mensal")
    await _salvar_anjo_stats()
    await _salvar_anjo_stats_diario()


@tasks.loop(minutes=1)
async def loop_ranking_anjo():
    await _atualizar_ranking_anjo()


@bot.command(name="ranking")
async def cmd_ranking_anjo(ctx, *, alvo: str = None):
    """Mostra/atualiza o ranking dos Anjos na hora. Uso: .ranking anjo"""
    if ctx.guild is None:
        return
    if alvo is None or "anjo" not in alvo.lower():
        await ctx.send("⚠️ Uso: `.ranking anjo`")
        return
    await _atualizar_ranking_anjo()
    await ctx.send("🕊️ Ranking Anjo Semanal e Ranking Anjo Mensal atualizados! Confira no canal de logs. ✨")


@bot.command(name="rankingdebug")
async def cmd_ranking_debug(ctx):
    """Mostra dados brutos do ranking pra diagnosticar problemas. Só o dono do bot pode usar."""
    if ctx.author.id != CRIADOR_ID:
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        await ctx.send("⚠️ Bot não está em nenhum servidor.")
        return

    cargo_anjo = guild.get_role(CARGO_ANJO_ID)
    canal_ranking = guild.get_channel(CANAL_RANKING_ANJO_ID)

    linhas = [
        f"**Cargo Anjo encontrado:** {'✅ sim' if cargo_anjo else '❌ NÃO — verifique o ID do cargo'}",
        f"**Membros com o cargo:** {len(cargo_anjo.members) if cargo_anjo else 0}",
        f"**Canal de ranking encontrado:** {'✅ sim' if canal_ranking else '❌ NÃO — verifique o ID do canal'}",
        f"**ID da mensagem — semanal:** `{_anjo_ranking_message_id_semanal}`",
        f"**ID da mensagem — mensal:** `{_anjo_ranking_message_id_mensal}`",
        f"**Entradas em anjo_stats_semanal (memória):** {len(anjo_stats_semanal)}",
        f"**Entradas em anjo_stats_mensal (memória):** {len(anjo_stats_mensal)}",
        f"**Pasta de dados usada:** `{_ANJO_DATA_DIR}`",
        f"**Arquivo de dados existe?** {'✅ sim' if os.path.exists(_ANJO_DATA_FILE) else '❌ não'}",
        "",
        "**Conteúdo bruto — SEMANAL:**",
    ]
    if anjo_stats_semanal:
        for uid, s in anjo_stats_semanal.items():
            membro = guild.get_member(uid)
            nome = membro.display_name if membro else f"<@{uid}>"
            linhas.append(f"`{uid}` ({nome}) — {s}")
    else:
        linhas.append("*vazio — nenhuma mensagem/call/ticket foi registrada ainda em memória*")

    linhas.append("")
    linhas.append("**Conteúdo bruto — MENSAL:**")
    if anjo_stats_mensal:
        for uid, s in anjo_stats_mensal.items():
            membro = guild.get_member(uid)
            nome = membro.display_name if membro else f"<@{uid}>"
            linhas.append(f"`{uid}` ({nome}) — {s}")
    else:
        linhas.append("*vazio — nenhuma mensagem/call/ticket foi registrada ainda em memória*")

    texto = "\n".join(linhas)
    if len(texto) > 1900:
        texto = texto[:1900] + "\n... (cortado)"
    await ctx.send(f"🔍 **Diagnóstico do Ranking de Anjos**\n{texto}")


class ConfirmarResetAnjoView(discord.ui.View):
    """Confirmação do reset de UM dos rankings dos Anjos (semanal ou mensal)
    — só o criador do bot pode confirmar. O outro ranking nunca é tocado."""

    def __init__(self, periodo: str):
        super().__init__(timeout=30)
        self.periodo = periodo  # "semanal" ou "mensal"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != CRIADOR_ID:
            await interaction.response.send_message(
                "🌑 **Aeon:** *olha fixamente* ...acesso negado. 🖤🌑\n"
                "🌟 **Celestia:** Só o DEV pode confirmar isso!! 🌸🤍✨",
                ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(
        label="🗑️ Confirmar Reset",
        style=discord.ButtonStyle.danger,
        custom_id="reiniciaranjo_confirmar"
    )
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True

        stats_dict = anjo_stats_semanal if self.periodo == "semanal" else anjo_stats_mensal
        voice_dict = _anjo_voice_join_semanal if self.periodo == "semanal" else _anjo_voice_join_mensal

        # Zera só as estatísticas guardadas DESTE período — o outro ranking fica intacto
        stats_dict.clear()

        # Sessões de call em andamento continuam sendo contadas neste período,
        # mas a partir de agora (a referência do OUTRO período não é mexida,
        # então ele continua contando certinho desde quando a pessoa entrou)
        agora = time.time()
        for uid in list(voice_dict.keys()):
            voice_dict[uid] = agora

        await _salvar_anjo_stats()
        await _atualizar_ranking_anjo()

        nome_periodo = "Semanal" if self.periodo == "semanal" else "Mensal"
        outro_periodo = "mensal" if self.periodo == "semanal" else "semanal"
        embed_final = discord.Embed(
            title=f"🕊️ Ranking Anjo {nome_periodo} Reiniciado",
            description=(
                f"🌑 **Aeon:** ...zerado. As sombras apagaram o histórico {self.periodo}. 🖤🌑\n"
                f"🌟 **Celestia:** RANKING {nome_periodo.upper()} ZERADO!! 😤🌸 "
                f"O ranking {outro_periodo} continua contando normalmente! ✨"
            ),
            color=0xe8d5f5
        )
        await interaction.response.edit_message(embed=embed_final, view=self)
        self.stop()

    @discord.ui.button(
        label="❌ Cancelar",
        style=discord.ButtonStyle.secondary,
        custom_id="reiniciaranjo_cancelar"
    )
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content="❌ Reset do ranking cancelado.", embed=None, view=self
        )
        self.stop()


@bot.command(name="reiniciaranjo")
async def cmd_reiniciar_anjo(ctx):
    """Reinicia (zera) só o Ranking Anjo SEMANAL. Uso: .reiniciaranjo — só o DEV pode usar."""
    if ctx.author.id != CRIADOR_ID:
        await ctx.send(
            "🌑 **Aeon:** *olha fixamente* ...acesso negado. 🖤🌑\n"
            "🌟 **Celestia:** Só o DEV pode usar esse comando!! 🌸🤍✨"
        )
        return

    embed = discord.Embed(
        title="⚠️ Reiniciar Ranking Anjo Semanal",
        description=(
            "Isso vai **zerar TODAS as estatísticas** (mensagens, tempo em call e "
            "tickets) do **Ranking Anjo Semanal** e apagar o histórico salvo dele.\n\n"
            "O **Ranking Anjo Mensal** não é afetado — continua contando normalmente.\n\n"
            "**Essa ação não pode ser desfeita.** Tem certeza?"
        ),
        color=0xff4444
    )
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Sistema de Moderação")
    await ctx.send(embed=embed, view=ConfirmarResetAnjoView(periodo="semanal"))


@bot.command(name="reiniciaranjo2")
async def cmd_reiniciar_anjo_mensal(ctx):
    """Reinicia (zera) só o Ranking Anjo MENSAL. Uso: .reiniciaranjo2 — só o DEV pode usar."""
    if ctx.author.id != CRIADOR_ID:
        await ctx.send(
            "🌑 **Aeon:** *olha fixamente* ...acesso negado. 🖤🌑\n"
            "🌟 **Celestia:** Só o DEV pode usar esse comando!! 🌸🤍✨"
        )
        return

    embed = discord.Embed(
        title="⚠️ Reiniciar Ranking Anjo Mensal",
        description=(
            "Isso vai **zerar TODAS as estatísticas** (mensagens, tempo em call e "
            "tickets) do **Ranking Anjo Mensal** e apagar o histórico salvo dele.\n\n"
            "O **Ranking Anjo Semanal** não é afetado — continua contando normalmente.\n\n"
            "**Essa ação não pode ser desfeita.** Tem certeza?"
        ),
        color=0xff4444
    )
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Sistema de Moderação")
    await ctx.send(embed=embed, view=ConfirmarResetAnjoView(periodo="mensal"))


# Carrega o histórico salvo assim que o módulo sobe — antes mesmo de conectar no Discord
_carregar_anjo_stats()

# ══════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════
# RESUMO DIÁRIO DE ANJOS — logs fofos do dia de cada Anjo
# Todo dia às 23:00 (horário de Brasília), Aeon & Celestia mandam no canal
# "logs anjo 2" um resumo fofo do dia de cada Anjo: tempo em call, mensagens
# mandadas, com quem interagiu, se ficou online/offline/voltou durante o dia,
# e os motivos fofos de ter ganhado pontos. O comando manual
# .puxarhistoricoanjo manda esse resumo na hora (contando só até aquele
# momento), mas NÃO cancela nem substitui o envio automático das 23h — ele
# sempre acontece, mesmo que o resumo já tenha sido puxado manualmente antes.
#
# Observação: rastrear online/offline depende do Presence Intent, que
# precisa estar ativado tanto no código (intents.presences, já habilitado
# lá em cima) quanto no Portal de Desenvolvedores do Discord, em
# Bot > Privileged Gateway Intents > Presence Intent. Sem isso, o Discord
# simplesmente nunca vai mandar essa informação pro bot.
#
# Assim como o restante do ranking de Anjos, esses dados diários ficam só
# em memória (não são salvos em disco) — se o bot reiniciar no meio do dia,
# a contagem daquele dia específico reinicia do zero.
# ══════════════════════════════════════════════════════════════════════

CANAL_LOGS_ANJO2_ID = 1531786991333544148  # canal "logs anjo 2" — resumo diário

# Fuso horário de Brasília (fixo em UTC-3, sem horário de verão atualmente)
_FUSO_BRASILIA = timezone(timedelta(hours=-3))

# Estatísticas do dia — mesmo formato do semanal/mensal, mas zeradas todo
# dia logo depois do envio automático das 23h.
anjo_stats_diario: dict = defaultdict(lambda: {"mensagens": 0, "tempo_call": 0.0, "tickets": 0, "penalidade": 0.0})

# Referência de "entrou em call" do dia — independente do semanal/mensal,
# pra poder resetar o dia sem bagunçar a contagem "ao vivo" dos outros.
_anjo_voice_join_diario: dict = {}   # user_id -> time.time()

# Linha do tempo de eventos do dia de cada Anjo (pra montar a narrativa).
# user_id -> list[{"tipo": str, "hora": float, "detalhe": str}]
# tipos usados: entrou_call, saiu_call, ficou_online, ficou_offline, voltou_online
_anjo_eventos_diario: dict = defaultdict(list)
_ANJO_MAX_EVENTOS = 40  # limite de eventos guardados por pessoa/dia

# Com quem cada Anjo interagiu hoje (mencionou ou respondeu) — user_id -> set(user_id)
_anjo_interagiu_hoje: dict = defaultdict(set)

# Se, em algum momento do dia, o Anjo ficou offline — usado pra saber se dá
# pra contar "saiu, mas voltou" quando ele reaparece online depois
_anjo_esteve_offline_hoje: dict = defaultdict(bool)

# ── Persistência em disco do resumo diário ──────────────────────────────────
# Usa a MESMA pasta do ranking semanal/mensal (_ANJO_DATA_DIR): se existir um
# Volume anexado no Railway, cai automaticamente em RAILWAY_VOLUME_MOUNT_PATH
# (ex.: /data), sobrevivendo a redeploys. Guardado num arquivo separado pra
# não mexer no formato já existente do anjo_ranking_data.json.
_ANJO_DIARIO_DATA_FILE = os.path.join(_ANJO_DATA_DIR, "anjo_resumo_diario_data.json")


def _data_brasilia_hoje() -> str:
    """Data de hoje no horário de Brasília, no formato 'AAAA-MM-DD' — usada
    como referência pra saber se os dados diários salvos ainda são de hoje."""
    return datetime.now(_FUSO_BRASILIA).strftime("%Y-%m-%d")


# Dia (horário de Brasília) a que os dados diários atuais pertencem
_anjo_data_referencia_diaria: str = _data_brasilia_hoje()


def _carregar_anjo_stats_diario() -> None:
    """Carrega o resumo diário salvo em disco, se ainda for referente a HOJE
    (horário de Brasília). Se o arquivo salvo for de um dia anterior — por
    exemplo, o bot ficou desligado e passou da meia-noite — os dados são
    descartados: aquele dia já devia ter recebido o resumo das 23h e não
    faz sentido misturá-lo com o dia novo. Roda antes do bot conectar."""
    global _anjo_data_referencia_diaria
    if not os.path.exists(_ANJO_DIARIO_DATA_FILE):
        return
    try:
        with open(_ANJO_DIARIO_DATA_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)

        data_salva = dados.get("data_referencia")
        if data_salva != _data_brasilia_hoje():
            # Dado de um dia que já passou (bot ficou fora do ar na virada) —
            # não carrega, o dia de hoje começa do zero normalmente.
            return

        for uid_str, valores in dados.get("stats_diario", {}).items():
            anjo_stats_diario[int(uid_str)] = {
                "mensagens":  valores.get("mensagens", 0),
                "tempo_call": valores.get("tempo_call", 0.0),
                "tickets":    valores.get("tickets", 0),
            }
        for uid_str, eventos in dados.get("eventos_diario", {}).items():
            _anjo_eventos_diario[int(uid_str)] = eventos
        for uid_str, ids in dados.get("interagiu_hoje", {}).items():
            _anjo_interagiu_hoje[int(uid_str)] = set(ids)
        for uid_str, valor in dados.get("esteve_offline_hoje", {}).items():
            _anjo_esteve_offline_hoje[int(uid_str)] = bool(valor)

        _anjo_data_referencia_diaria = data_salva
    except (json.JSONDecodeError, OSError, ValueError):
        pass


async def _salvar_anjo_stats_diario() -> None:
    """Salva o resumo diário em disco de forma atômica (escreve em .tmp e
    substitui) — mesmo esquema de escrita usado pelo ranking semanal/mensal."""
    dados = {
        "data_referencia": _anjo_data_referencia_diaria,
        "stats_diario": {str(uid): v for uid, v in anjo_stats_diario.items()},
        "eventos_diario": {str(uid): v for uid, v in _anjo_eventos_diario.items()},
        "interagiu_hoje": {str(uid): list(ids) for uid, ids in _anjo_interagiu_hoje.items()},
        "esteve_offline_hoje": {str(uid): v for uid, v in _anjo_esteve_offline_hoje.items()},
    }
    tmp_path = _ANJO_DIARIO_DATA_FILE + ".tmp"

    def _escrever():
        os.makedirs(_ANJO_DATA_DIR, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, _ANJO_DIARIO_DATA_FILE)

    try:
        loop = asyncio.get_event_loop()
        async with (_anjo_stats_lock or asyncio.Lock()):
            await loop.run_in_executor(None, _escrever)
    except OSError:
        pass
# ─────────────────────────────────────────────────────────────────────────

# Carrega o resumo diário salvo (se ainda for de hoje) assim que o módulo
# sobe — igual ao _carregar_anjo_stats() do ranking semanal/mensal.
_carregar_anjo_stats_diario()


def _registrar_evento_anjo_diario(user_id: int, tipo: str, detalhe: str = "") -> None:
    """Adiciona um evento na linha do tempo do dia de um Anjo, mantendo só os mais recentes."""
    eventos = _anjo_eventos_diario[user_id]
    eventos.append({"tipo": tipo, "hora": time.time(), "detalhe": detalhe})
    if len(eventos) > _ANJO_MAX_EVENTOS:
        del eventos[: len(eventos) - _ANJO_MAX_EVENTOS]


def _tempo_call_diario_atual(membro_id: int) -> float:
    """Tempo em call HOJE: sessões já fechadas + a sessão em andamento, se a
    pessoa estiver em call neste exato momento (contagem 'ao vivo')."""
    base = anjo_stats_diario.get(membro_id, {}).get("tempo_call", 0.0)
    inicio_sessao_atual = _anjo_voice_join_diario.get(membro_id)
    if inicio_sessao_atual:
        base += time.time() - inicio_sessao_atual
    return base


# ── Frases fofas usadas para montar a narrativa do resumo (Aeon & Celestia) ──
_RESUMO_ABRE_CALL = [
    "ficou {tempo} grudadinho(a) na call hoje 🎙️",
    "passou {tempo} de call hoje, sem preguiça nenhuma 🎙️✨",
    "rendeu {tempo} de presença na call hoje 🎙️🌙",
]
_RESUMO_ABRE_MSG = [
    "mandou {qtd} mensagens hoje 💬",
    "apareceu com {qtd} mensagens no chat hoje 💬✨",
    "não ficou quieto(a) não: {qtd} mensagens hoje 💬🌸",
]
_RESUMO_INTERAGIU = [
    "ficou on e trocou ideia com {pessoas} 🤍",
    "interagiu bastante com {pessoas} hoje 🌟",
    "passou um tempo junto de {pessoas} hoje 🕊️",
]
_RESUMO_ONLINE_AGORA = [
    "e tá online AGORA mesmo 🟢",
    "e continua online agora, de olho no servidor 🟢✨",
]
_RESUMO_SAIU_VOLTOU = [
    "saiu em algum momento do dia, mas voltou de novo 🔁🤍",
    "sumiu um pouquinho e reapareceu depois 🔁🌸",
]
_RESUMO_PONTOS_MSG    = "💬 conversou bastante no chat"
_RESUMO_PONTOS_CALL   = "🎙️ ficou de call junto da galera"
_RESUMO_PONTOS_TICKET = "🕊️ atendeu ticket(s) com muito carinho"


def _formatar_lista_pessoas(guild: discord.Guild, ids: set) -> str:
    """Transforma um conjunto de IDs em algo tipo 'Fulano, Beltrano e mais 2'."""
    nomes = []
    for uid in list(ids)[:5]:
        membro = guild.get_member(uid)
        nomes.append(membro.display_name if membro else "alguém do servidor")
    extra = len(ids) - len(nomes)
    texto = ", ".join(nomes)
    if extra > 0:
        texto += f" e mais {extra}"
    return texto or "ninguém em especial"


def _montar_linha_resumo_anjo(guild: discord.Guild, membro: discord.Member):
    """Monta o parágrafo fofo do dia de UM Anjo. Devolve None se a pessoa não
    teve nenhuma atividade hoje (pra não poluir o resumo com gente parada)."""
    s = anjo_stats_diario.get(membro.id, {"mensagens": 0, "tempo_call": 0.0, "tickets": 0, "penalidade": 0.0})
    tempo_call_hoje = _tempo_call_diario_atual(membro.id)
    mensagens_hoje  = s["mensagens"]
    tickets_hoje    = s["tickets"]
    penalidade_hoje = s.get("penalidade", 0.0)
    interagiu_com   = _anjo_interagiu_hoje.get(membro.id, set())
    eventos         = _anjo_eventos_diario.get(membro.id, [])

    teve_atividade = (
        tempo_call_hoje > 0 or mensagens_hoje > 0 or tickets_hoje > 0
        or interagiu_com or eventos
    )
    if not teve_atividade:
        return None

    partes = []
    if tempo_call_hoje > 0:
        partes.append(random.choice(_RESUMO_ABRE_CALL).format(tempo=_formatar_tempo_call(tempo_call_hoje)))
    if mensagens_hoje > 0:
        partes.append(random.choice(_RESUMO_ABRE_MSG).format(qtd=mensagens_hoje))
    if interagiu_com:
        pessoas = _formatar_lista_pessoas(guild, interagiu_com)
        partes.append(random.choice(_RESUMO_INTERAGIU).format(pessoas=pessoas))

    esta_online_agora = membro.id in _anjo_voice_join or (
        getattr(membro, "status", discord.Status.offline) != discord.Status.offline
    )
    if esta_online_agora:
        partes.append(random.choice(_RESUMO_ONLINE_AGORA))
    elif _anjo_esteve_offline_hoje.get(membro.id):
        partes.append(random.choice(_RESUMO_SAIU_VOLTOU))

    # Motivos fofos de ter ganhado pontos hoje
    pontuacao_hoje = (
        mensagens_hoje * _PESO_MENSAGEM
        + (tempo_call_hoje / 60) * _PESO_MINUTO_CALL
        + tickets_hoje * _PESO_TICKET
        - penalidade_hoje
    )
    motivos = []
    if mensagens_hoje > 0:
        motivos.append(_RESUMO_PONTOS_MSG)
    if tempo_call_hoje > 0:
        motivos.append(_RESUMO_PONTOS_CALL)
    if tickets_hoje > 0:
        motivos.append(_RESUMO_PONTOS_TICKET)
    if penalidade_hoje > 0:
        motivos.append("⛔ recebeu punição de call")

    if not partes:
        partes.append("teve uma movimentação hoje 🌙")

    linha = f"**{membro.display_name}** — {' · '.join(partes)}"
    if motivos:
        linha += f"\n> 🌟 ganhou **{pontuacao_hoje:.0f} pts** hoje: {', '.join(motivos)}"
    return linha


async def _montar_embed_resumo_diario_anjo(guild: discord.Guild, ate_agora: bool) -> discord.Embed:
    """Monta o embed com o resumo do dia de todos os Anjos que tiveram atividade."""
    cargo_anjo = guild.get_role(CARGO_ANJO_ID)
    membros_anjo = cargo_anjo.members if cargo_anjo else []

    linhas = []
    for membro in membros_anjo:
        if membro.bot:
            continue
        linha = _montar_linha_resumo_anjo(guild, membro)
        if linha:
            linhas.append(linha)

    if not linhas:
        descricao = "*Nenhum Anjo teve atividade registrada hoje até agora.* 🌙"
    else:
        descricao = "\n\n".join(linhas)
        if len(descricao) > 3900:
            descricao = descricao[:3900] + "\n... *(cortado — muita coisa aconteceu hoje!)*"

    agora_brasilia = datetime.now(_FUSO_BRASILIA)
    if ate_agora:
        subtitulo = f"resumo puxado na hora — até às {agora_brasilia.strftime('%Hh%M')} de hoje"
    else:
        subtitulo = f"resumo automático das 23h — {agora_brasilia.strftime('%d/%m')}"

    embed = discord.Embed(
        title="🕊️ Resumo do Dia dos Anjos",
        description=descricao,
        color=0xe8d5f5,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text=f"🌑 Aeon & ☀️ Celestia — {subtitulo}")
    return embed


async def _enviar_resumo_diario_anjo(ate_agora: bool = False) -> bool:
    """Manda o resumo do dia dos Anjos no canal 'logs anjo 2'. Devolve True se enviou."""
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return False

    canal = guild.get_channel(CANAL_LOGS_ANJO2_ID)
    if canal is None:
        print(f"[resumo-anjo] Canal 'logs anjo 2' ({CANAL_LOGS_ANJO2_ID}) não encontrado.")
        return False

    embed = await _montar_embed_resumo_diario_anjo(guild, ate_agora=ate_agora)
    abertura = (
        "🌑 **Aeon:** ...mais um dia registrado nas sombras. Aqui está o que os Anjos fizeram. 🖤🌙\n"
        "🌟 **Celestia:** OLHA SÓ QUANTO CARINHO OS ANJOS DERAM HOJE!! 😭🌸✨ "
        "Muito orgulho de cada um deles!! 🤍"
    )
    try:
        await canal.send(abertura, embed=embed)
        return True
    except discord.HTTPException as e:
        print(f"[resumo-anjo] ERRO ao enviar resumo diário: {e!r}")
        return False


def _resetar_dia_anjo() -> None:
    """Zera as estatísticas e eventos do dia — chamado logo depois do envio
    automático das 23h, pra começar o próximo dia do zero. Sessões de call em
    andamento continuam sendo contadas: só a referência de início é recolocada
    em 'agora' (igual ao reset semanal/mensal), sem perder a sessão atual."""
    global _anjo_data_referencia_diaria
    anjo_stats_diario.clear()
    _anjo_eventos_diario.clear()
    _anjo_interagiu_hoje.clear()
    _anjo_esteve_offline_hoje.clear()

    agora = time.time()
    for uid in list(_anjo_voice_join_diario.keys()):
        _anjo_voice_join_diario[uid] = agora

    _anjo_data_referencia_diaria = _data_brasilia_hoje()
    asyncio.create_task(_salvar_anjo_stats_diario())


@tasks.loop(time=dtime(hour=23, minute=0, tzinfo=_FUSO_BRASILIA))
async def loop_resumo_diario_anjo():
    """Todo dia às 23:00 (horário de Brasília) manda o resumo fofo do dia de
    cada Anjo no canal 'logs anjo 2' e reinicia a contagem pro próximo dia.
    Roda sempre nesse horário, mesmo que .puxarhistoricoanjo já tenha sido
    usado mais cedo no mesmo dia."""
    try:
        await _enviar_resumo_diario_anjo(ate_agora=False)
    finally:
        _resetar_dia_anjo()


@bot.command(name="puxarhistoricoanjo")
async def cmd_puxar_historico_anjo(ctx):
    """Manda na hora o resumo do dia de cada Anjo (contando só até este
    momento) no canal 'logs anjo 2'. Uso: .puxarhistoricoanjo — isso NÃO
    substitui nem cancela o envio automático das 23h, que acontece de
    qualquer jeito, mesmo que esse comando já tenha sido usado antes."""
    if ctx.guild is None:
        return
    enviado = await _enviar_resumo_diario_anjo(ate_agora=True)
    if enviado:
        await ctx.send("🕊️ Resumo do dia puxado! Confira no canal **logs anjo 2**. ✨")
    else:
        await ctx.send(
            "⚠️ Não consegui enviar o resumo — verifique se o canal `logs anjo 2` "
            f"(`{CANAL_LOGS_ANJO2_ID}`) existe e se eu tenho permissão de enviar mensagens nele."
        )

# ══════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════
# RANKING DE NÍVEL / XP — estilo Lorrita
# Todo membro com o cargo CARGO_XP_ID ganha XP ao mandar mensagem (com
# cooldown pra evitar spam). O ranking geral fica sempre como a MESMA
# mensagem no topo do canal CANAL_XP_ID (editada, nunca duplicada). Quando
# alguém sobe de nível, uma nova mensagem de aviso aparece embaixo — e o
# aviso de nível anterior dessa mesma pessoa é apagado, então só existe
# sempre UM aviso de nível por pessoa, sempre o mais recente.
# Guarda tudo em xp_ranking_data.json (mesma pasta persistente do Anjo) pra
# sobreviver a reinícios.
#
# Regras de canais:
#   • Os 3 canais em _XP_CANAIS_RANKING dão XP "cheio" (ou bônus, no canal
#     bônus) — e mandar mensagem neles é o que faz a pessoa PASSAR A
#     APARECER no ranking (flag "elegivel" salva por pessoa).
#   • Qualquer outro canal do servidor também dá XP, só que bem menos
#     (_XP_MULTIPLICADOR_OUTROS), e sozinho NÃO destrava a aparição no
#     ranking — só conta se a pessoa já tiver mandado mensagem em algum
#     dos 3 canais principais alguma vez.
# ══════════════════════════════════════════════════════════════════════

_XP_DATA_FILE = os.path.join(_ANJO_DATA_DIR, "xp_ranking_data.json")

# Configuração de ganho de XP — ajuste à vontade
_XP_MIN_POR_MSG       = 15   # xp mínimo ganho por mensagem válida (canais normais/principais)
_XP_MAX_POR_MSG       = 25   # xp máximo ganho por mensagem válida (canais normais/principais)
_XP_COOLDOWN_SEGUNDOS = 60   # tempo mínimo entre ganhos de xp da mesma pessoa

# Canais que valem XP "cheio" e que destravam a aparição no ranking
_XP_CANAL_1        = 1284257046740602901
_XP_CANAL_BONUS    = 1284258192414740490   # este dá XP extra (bônus)
_XP_CANAL_3        = 1284258354964856903
_XP_CANAIS_RANKING = {_XP_CANAL_1, _XP_CANAL_BONUS, _XP_CANAL_3}

_XP_MULTIPLICADOR_BONUS  = 1.6    # canal bônus: 60% a mais de xp por mensagem
_XP_MULTIPLICADOR_OUTROS = 0.35   # qualquer outro canal do servidor: bem menos xp (35% do normal)

# Calls privadas — quem está numa dessas calls de voz NÃO ganha xp de call
# (_XP_POR_TICK_CALL). Não afeta xp de mensagem, só o tick de call.
_XP_CALLS_PRIVADAS = {
    1390460781941751848,
    1289963328248217672,
    1503862574251507813,
    1284260414850470030,
    1299047064029892708,
    1299047106870378506,
    1299047207957430292,
    1284266770299093133,
    1284260876035031040,
}

# ── Personalização de cor do quadradinho no ranking ─────────────────────────
# Cada pessoa pode escolher a cor do próprio "quadradinho" (o quadrado que
# se preenche na barra de progresso) através do menu que fica abaixo do
# ranking fixo. A cor da parte vazia da barra continua sempre branca.
_COR_PADRAO = "roxo"

# Cargo de Booster do servidor — só quem tem esse cargo pode escolher as
# cores especiais (marcadas com "booster": True) lá embaixo.
_CARGO_BOOSTER_CORES_ID = 1284279730287280189

_CORES_QUADRADO = {
    # ── Cores normais — disponíveis pra qualquer pessoa ──────────────────
    "roxo":     {"emoji": "🟪", "label": "Roxo (padrão)", "booster": False},
    "azul":     {"emoji": "🟦", "label": "Azul", "booster": False},
    "vermelho": {"emoji": "🟥", "label": "Vermelho", "booster": False},
    "verde":    {"emoji": "🟩", "label": "Verde", "booster": False},
    "amarelo":  {"emoji": "🟨", "label": "Amarelo", "booster": False},
    "laranja":  {"emoji": "🟧", "label": "Laranja", "booster": False},
    "marrom":   {"emoji": "🟫", "label": "Marrom", "booster": False},
    "preto":    {"emoji": "⬛", "label": "Preto", "booster": False},

    # ── Cores especiais — exclusivas de quem tem o cargo de Booster ──────
    # Em vez de um emoji só repetido, usam um "padrao" (lista de emojis)
    # que vai ciclando/alternando a cada quadradinho preenchido.
    "arco_iris": {"padrao": ["🟥", "🟧", "🟨", "🟩", "🟦", "🟪"], "emoji": "🌈", "label": "🌈 Arco-íris (Booster)", "booster": True},
    "xadrez":    {"padrao": ["⬛", "⬜"], "emoji": "🏁", "label": "🏁 Xadrez (Booster)", "booster": True},
    "dourado":   {"padrao": ["🟨", "⬛"], "emoji": "✨", "label": "✨ Dourado Cintilante (Booster)", "booster": True},
    "gradiente": {"padrao": ["🟪", "🟦"], "emoji": "🌊", "label": "🌊 Gradiente Roxo-Azul (Booster)", "booster": True},
}


def _emoji_da_cor(chave: str):
    """Devolve o padrão de preenchimento do quadradinho pra cor escolhida:
    uma LISTA de emojis pras cores especiais (arco-íris, xadrez...), que
    ciclam a cada quadradinho, ou um emoji só (string) pras cores normais,
    que se repete. Cai pra cor padrão se a chave for inválida/desconhecida."""
    info = _CORES_QUADRADO.get(chave, _CORES_QUADRADO[_COR_PADRAO])
    return info.get("padrao") or info["emoji"]


# xp_stats[user_id] = {
#     "xp": int (total acumulado), "nivel": int, "level_message_id": int|None,
#     "elegivel": bool (já mandou mensagem em algum dos 3 canais de _XP_CANAIS_RANKING?),
#     "cor": str (chave em _CORES_QUADRADO — cor escolhida pra o próprio quadradinho),
#     "vitorias": int (vitórias na Arena de Batalhas), "derrotas": int (derrotas na Arena de Batalhas),
#     "criaturas": list[str] (ids das criaturas já desbloqueadas na Enciclopédia — começa com as
#                  ⚪ Comuns de graça, e ganha novas como recompensa ao vencer batalhas),
#     "usos_criaturas": dict[str, int] (quantas vezes CADA criatura já foi invocada em batalha por
#                  essa pessoa — é a partir daqui que se calcula o Nível de Capacidade dela, de 1 a 10;
#                  ver _calcular_nivel_criatura),
#     "favorito": dict (criatura favorita pra batalhas — ver _favorito_status):
#                  {"id": str|None, "usos": int, "cansacos": dict[str, float]}
#                  "cansacos" guarda, PRA CADA criatura que já cansou, o timestamp
#                  (time.time()) até quando ela ainda tá descansando. Isso permite
#                  trocar de favorita livremente a qualquer momento — mesmo com
#                  outra(s) criatura(s) ainda de castigo — sem perder o cooldown delas.
# }
xp_stats: dict = defaultdict(lambda: {"xp": 0, "nivel": 0, "level_message_id": None, "elegivel": False, "cor": _COR_PADRAO, "vitorias": 0, "derrotas": 0, "criaturas": [], "usos_criaturas": {}, "favorito": {"id": None, "usos": 0, "cansacos": {}}, "pets": [], "usos_pets": {}, "pet_equipado": None})
_xp_ultimo_ganho: dict = {}   # user_id -> time.time() do último ganho (cooldown)
_xp_ranking_message_id = None   # ID da ÚNICA mensagem do ranking — navegada com as setinhas ◀ ▶, nunca duplicada
_xp_ranking_pagina_atual: int = 0   # índice (0-based) da página do ranking sendo exibida agora
_xp_cor_message_id = None      # ID da mensagem com o menu de escolha de cor (fica logo abaixo do ranking)
_xp_batalha_info_message_id = None  # ID da mensagem explicando as batalhas (fica logo abaixo da de cor)
_xp_enciclopedia_message_id = None  # ID da mensagem da Enciclopédia de Criaturas (fica por último, embaixo de tudo)
_xp_stats_lock = None          # criado em on_ready (precisa de event loop rodando)
_xp_ranking_update_lock = None # criado em on_ready — trava _atualizar_ranking_xp() pra nunca rodar 2x ao mesmo tempo (evita mensagens fixas duplicadas)


def _xp_necessario_para_nivel(nivel: int) -> int:
    """Quanto de XP é necessário pra sair desse nível e ir pro próximo (curva estilo Lorrita/MEE6)."""
    return 5 * (nivel ** 2) + 50 * nivel + 100


def _calcular_nivel(xp_total: int):
    """A partir do XP total acumulado, devolve (nivel_atual, xp_dentro_do_nivel_atual, xp_necessario_no_nivel_atual)."""
    nivel = 0
    restante = max(xp_total, 0)
    while True:
        necessario = _xp_necessario_para_nivel(nivel)
        if restante < necessario:
            return nivel, restante, necessario
        restante -= necessario
        nivel += 1


def _xp_total_para_nivel(nivel: int) -> int:
    """Inverso de _calcular_nivel: quanto de XP total é preciso acumular pra
    estar bem no COMEÇO de um nível específico (0 xp dentro dele). Usado
    pelo `.darlevel` pra definir manualmente o nível de alguém."""
    total = 0
    for n in range(max(nivel, 0)):
        total += _xp_necessario_para_nivel(n)
    return total


def _barra_progresso(atual: int, necessario: int, tamanho: int = 10, cor_emoji="🟪") -> str:
    """Monta a barra de progresso. `cor_emoji` pode ser um emoji só (string,
    repetido em todos os quadradinhos preenchidos — cores normais) ou uma
    lista de emojis (cicla um por quadradinho, na ordem — cores especiais
    tipo 🌈 Arco-íris ou 🏁 Xadrez)."""
    necessario = max(necessario, 1)
    preenchido = max(0, min(tamanho, round((atual / necessario) * tamanho)))
    if isinstance(cor_emoji, (list, tuple)):
        padrao = list(cor_emoji) or ["🟪"]
        parte_preenchida = "".join(padrao[i % len(padrao)] for i in range(preenchido))
    else:
        parte_preenchida = cor_emoji * preenchido
    return parte_preenchida + "⬜" * (tamanho - preenchido)


def _migrar_favorito(bruto) -> dict:
    """Converte o formato salvo em disco pro formato atual do favorito.
    Aceita: None (usuário novo), o formato NOVO (já com "cansacos"), ou o
    formato ANTIGO (com "cansaco_id"/"cansaco_ate" únicos, de antes de dar
    pra trocar de favorita com outra ainda descansando)."""
    if not bruto:
        return {"id": None, "usos": 0, "cansacos": {}}

    if "cansacos" in bruto:
        return {
            "id":       bruto.get("id"),
            "usos":     bruto.get("usos", 0),
            "cansacos": dict(bruto.get("cansacos") or {}),
        }

    # Formato antigo — migra o único cansaço registrado (se ainda válido)
    cansacos = {}
    cansaco_id  = bruto.get("cansaco_id")
    cansaco_ate = bruto.get("cansaco_ate")
    if cansaco_id and cansaco_ate:
        cansacos[cansaco_id] = cansaco_ate
    return {
        "id":       bruto.get("id"),
        "usos":     bruto.get("usos", 0),
        "cansacos": cansacos,
    }


def _carregar_xp_stats() -> None:
    """Carrega estatísticas de XP salvas em disco, se existirem. Roda antes do bot conectar."""
    global _xp_ranking_message_id, _xp_ranking_pagina_atual, _xp_cor_message_id, _xp_batalha_info_message_id, _xp_enciclopedia_message_id
    if not os.path.exists(_XP_DATA_FILE):
        return
    try:
        with open(_XP_DATA_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        for uid_str, valores in dados.get("stats", {}).items():
            xp_stats[int(uid_str)] = {
                "xp":               valores.get("xp", 0),
                "nivel":            valores.get("nivel", 0),
                "level_message_id": valores.get("level_message_id"),
                "elegivel":         valores.get("elegivel", False),
                "cor":              valores.get("cor", _COR_PADRAO),
                "vitorias":         valores.get("vitorias", 0),
                "derrotas":         valores.get("derrotas", 0),
                "criaturas":        valores.get("criaturas", []),
                "usos_criaturas":   valores.get("usos_criaturas", {}),
                "favorito":         _migrar_favorito(valores.get("favorito")),
                "pets":             valores.get("pets", []),
                "usos_pets":        valores.get("usos_pets", {}),
                "pet_equipado":     valores.get("pet_equipado"),
            }
        # Compatibilidade: versões antigas (antes das setinhas ◀ ▶) salvavam
        # "ranking_message_ids" — uma LISTA de páginas empilhadas. A versão
        # atual é sempre uma mensagem só, então só recupera o ID da primeira
        # página salva; as mensagens extras que sobrarem no canal são
        # encontradas e limpas sozinhas na próxima atualização do ranking.
        ids_antigos = dados.get("ranking_message_ids")
        if ids_antigos:
            _xp_ranking_message_id = ids_antigos[0]
        else:
            _xp_ranking_message_id = dados.get("ranking_message_id")
        _xp_ranking_pagina_atual = dados.get("pagina_atual", 0)
        _xp_cor_message_id = dados.get("cor_message_id")
        _xp_batalha_info_message_id = dados.get("batalha_info_message_id")
        _xp_enciclopedia_message_id = dados.get("enciclopedia_message_id")
    except (json.JSONDecodeError, OSError, ValueError):
        pass


async def _salvar_xp_stats() -> None:
    """Salva estatísticas de XP em disco de forma atômica (escreve em .tmp e substitui)."""
    dados = {
        "stats": {str(uid): v for uid, v in xp_stats.items()},
        "ranking_message_id": _xp_ranking_message_id,
        "pagina_atual": _xp_ranking_pagina_atual,
        "cor_message_id": _xp_cor_message_id,
        "batalha_info_message_id": _xp_batalha_info_message_id,
        "enciclopedia_message_id": _xp_enciclopedia_message_id,
    }
    tmp_path = _XP_DATA_FILE + ".tmp"

    def _escrever():
        os.makedirs(_ANJO_DATA_DIR, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, _XP_DATA_FILE)

    try:
        loop = asyncio.get_event_loop()
        async with (_xp_stats_lock or asyncio.Lock()):
            await loop.run_in_executor(None, _escrever)
    except OSError:
        pass


async def _apagar_level_up_depois(mensagem: discord.Message, user_id: int) -> None:
    """Espera 1 minuto e apaga a mensagem de level-up sozinha — não fica esperando
    a pessoa subir de nível de novo pra sumir."""
    await asyncio.sleep(60)
    try:
        await mensagem.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass
    # Se essa ainda for a referência salva como "aviso atual" dessa pessoa,
    # limpa pra não tentar apagar a mesma mensagem de novo depois.
    dados = xp_stats.get(user_id)
    if dados and dados.get("level_message_id") == mensagem.id:
        dados["level_message_id"] = None
        asyncio.create_task(_salvar_xp_stats())


async def _anunciar_level_up(guild: discord.Guild, membro: discord.Member, nivel_novo: int) -> None:
    """Manda o aviso de novo nível no canal de XP, apagando antes o aviso do nível
    anterior dessa mesma pessoa (assim só existe sempre um aviso, o mais recente),
    e some sozinho depois de 1 minuto."""
    canal = guild.get_channel(CANAL_XP_ID)
    if canal is None:
        return

    dados = xp_stats[membro.id]

    antigo_id = dados.get("level_message_id")
    if antigo_id:
        try:
            antiga = await canal.fetch_message(antigo_id)
            await antiga.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    embed = discord.Embed(
        title="⭐ Level Up!",
        description=(
            f"🎉 {membro.mention} subiu para o **nível {nivel_novo}**!\n\n"
            "🌑 **Aeon:** *inclina a cabeça em reconhecimento* ...as sombras notaram seu progresso. 🖤🌑\n"
            "🌟 **Celestia:** AAAAA PARABÉNS!! 😭🌟🤍✨ *explode em faíscas douradas* CONTINUE ASSIM!! 💫"
        ),
        color=0xf5c542,
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Sistema de Nível")

    try:
        nova = await canal.send(embed=embed)
        dados["level_message_id"] = nova.id
        asyncio.create_task(_apagar_level_up_depois(nova, membro.id))
    except discord.HTTPException:
        pass


async def _processar_xp_mensagem(message: discord.Message) -> None:
    """Dá XP pra qualquer pessoa que mandar mensagem (com cooldown) e cuida do
    level-up, se acontecer. Não exige nenhum cargo — vale pra todo mundo.

    Mensagens nos 3 canais de _XP_CANAIS_RANKING valem xp cheio (ou bônus, no
    canal bônus) e são o que faz a pessoa "destravar" a aparição no ranking.
    Mensagens em qualquer outro canal do servidor ainda dão xp, só que bem
    menos, e sozinhas não fazem a pessoa aparecer no ranking. Calls privadas
    (_XP_CALLS_PRIVADAS) são exceção total: nada de xp por lá.
    """
    if message.guild is None or message.author.bot:
        return

    # Calls privadas (_XP_CALLS_PRIVADAS) não pontuam de jeito nenhum — nem
    # xp de call, nem xp de mensagem mandada por lá. Sai antes até de gastar
    # o cooldown, pra não prejudicar o próximo ganho de xp da pessoa.
    if message.channel.id in _XP_CALLS_PRIVADAS:
        return

    # ⚠️ Destravado: NÃO exige mais o cargo CARGO_XP_ID. Qualquer pessoa que
    # mandar mensagem no servidor participa do ranking normalmente — ganha
    # XP e, se mandar em um dos _XP_CANAIS_RANKING, fica "elegivel" e passa
    # a aparecer no ranking fixo do canal CANAL_XP_ID.

    agora = time.time()
    uid = message.author.id
    ultimo = _xp_ultimo_ganho.get(uid, 0)
    if agora - ultimo < _XP_COOLDOWN_SEGUNDOS:
        return
    _xp_ultimo_ganho[uid] = agora

    canal_id = message.channel.id
    if canal_id == _XP_CANAL_BONUS:
        multiplicador = _XP_MULTIPLICADOR_BONUS
    elif canal_id in _XP_CANAIS_RANKING:
        multiplicador = 1.0
    else:
        multiplicador = _XP_MULTIPLICADOR_OUTROS

    ganho = max(1, round(random.randint(_XP_MIN_POR_MSG, _XP_MAX_POR_MSG) * multiplicador))

    # 🎁 Booster de XP do Baú — se estiver ativo, dobra o ganho por um tempo
    if agora < _xp_booster_ate.get(uid, 0):
        ganho *= _BAU_BOOSTER_MULTIPLICADOR

    dados = xp_stats[uid]
    nivel_antigo = dados["nivel"]
    dados["xp"] += ganho

    if canal_id in _XP_CANAIS_RANKING:
        dados["elegivel"] = True

    nivel_novo, _, _ = _calcular_nivel(dados["xp"])
    dados["nivel"] = nivel_novo

    if nivel_novo > nivel_antigo:
        await _anunciar_level_up(message.guild, message.author, nivel_novo)

    # Salva em disco a cada ganho de xp (e não só a cada 1 min pelo loop de
    # ranking) — assim, mesmo que o Railway derrube o bot de repente, o
    # máximo que se perde é o ganho da própria mensagem que ainda não deu
    # tempo de salvar, nunca o histórico inteiro.
    asyncio.create_task(_salvar_xp_stats())


def _montar_embeds_ranking_xp(guild: discord.Guild) -> list:
    """Monta o ranking de XP como uma LISTA de embeds — uma "página" por
    embed. Normalmente é só 1 página, mas se a lista de gente elegível ficar
    grande demais pra caber no limite de caracteres de um único embed do
    Discord, quebra sozinho em várias páginas. Só UMA página fica visível
    por vez, no canal, numa mensagem só — quem quiser ver as outras navega
    com as setinhas ◀ ▶ que ficam embaixo do ranking (ver RankingXPView).

    ⚠️ Destravado: não depende mais de cargo. A ÚNICA condição pra entrar
    no ranking é ter mandado UMA mensagem em pelo menos um dos canais
    elegíveis (_XP_CANAIS_RANKING, que inclui o chat geral em _XP_CANAL_1)
    — a partir daí a pessoa JÁ aparece aqui na hora, mesmo ainda no Nível 0
    com pouco ou nenhum XP. Sem limite de posições: aparece todo mundo que
    se qualificar, não só um "top N" — inclusive quem está zerado, 0x0,
    Nível 0. Só precisa ainda estar no servidor (quem sai é removido de
    xp_stats pelo on_member_remove).
    """
    linhas = []
    for uid, dados in xp_stats.items():
        if not dados.get("elegivel"):
            continue
        membro = guild.get_member(uid)
        if membro is None or membro.bot:
            continue
        nivel, xp_no_nivel, xp_necessario = _calcular_nivel(dados["xp"])
        cor_emoji = _emoji_da_cor(dados.get("cor", _COR_PADRAO))
        vitorias = dados.get("vitorias", 0)
        derrotas = dados.get("derrotas", 0)
        linhas.append((membro, dados["xp"], nivel, xp_no_nivel, xp_necessario, cor_emoji, vitorias, derrotas))

    # Empate (comum agora, já que muita gente pode estar zerada no Nível 0)
    # é resolvido por nome, pra ordem ficar estável entre atualizações.
    linhas.sort(key=lambda x: (-x[1], x[0].display_name.lower()))

    RODAPE_PADRAO = "🌑 Aeon & ☀️ Celestia — atualizado automaticamente a cada 1 min • 🎨 personalize seu quadradinho no menu abaixo!"

    if not linhas:
        embed = discord.Embed(
            title="⭐ Ranking de Nível",
            description=(
                "*Ninguém entrou no ranking ainda — mande uma mensagem em "
                f"<#{_XP_CANAL_1}>, <#{_XP_CANAL_BONUS}> ou <#{_XP_CANAL_3}> "
                "pra começar a aparecer aqui!* 💬"
            ),
            color=0xe8d5f5,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text=RODAPE_PADRAO)
        return [embed]

    LIMITE_DESCRICAO = 3900  # margem de segurança abaixo do limite real (4096) do Discord
    ITENS_POR_PAGINA = 10    # quebra a cada 10 pessoas — assim as setinhas ◀ ▶ sempre têm o que navegar, mesmo com poucos membros
    total = len(linhas)
    largura_rank = max(2, len(str(total)))
    medalhas = ["🥇", "🥈", "🥉"]

    # Quebra as linhas em páginas de até ITENS_POR_PAGINA pessoas. O limite
    # de caracteres continua valendo como proteção extra (só entra em jogo
    # se, por algum motivo raro, 10 linhas não couberem no embed).
    paginas_linhas = [[]]
    tamanho_atual = 0
    for i, (membro, xp_total, nivel, xp_no_nivel, xp_necessario, cor_emoji, vitorias, derrotas) in enumerate(linhas):
        prefixo = medalhas[i] if i < 3 else f"`#{i + 1:>{largura_rank}}`"
        barra = _barra_progresso(xp_no_nivel, xp_necessario, cor_emoji=cor_emoji)
        linha = (
            f"{prefixo} **{membro.display_name}** — Nível `{nivel}` {barra} "
            f"`{xp_no_nivel}/{xp_necessario}` XP (total: `{xp_total}`)\n"
            f"┗ ⚔️ Vitórias: `{vitorias}` | Derrotas: `{derrotas}`"
        )
        pagina_cheia_por_quantidade = len(paginas_linhas[-1]) >= ITENS_POR_PAGINA
        pagina_cheia_por_tamanho = tamanho_atual + len(linha) + 1 > LIMITE_DESCRICAO
        if paginas_linhas[-1] and (pagina_cheia_por_quantidade or pagina_cheia_por_tamanho):
            paginas_linhas.append([])
            tamanho_atual = 0
        paginas_linhas[-1].append(linha)
        tamanho_atual += len(linha) + 1

    total_paginas = len(paginas_linhas)
    embeds = []
    for idx, linhas_pagina in enumerate(paginas_linhas):
        embed = discord.Embed(
            title="⭐ Ranking de Nível",
            description="\n".join(linhas_pagina),
            color=0xe8d5f5,
            timestamp=discord.utils.utcnow(),
        )
        if total_paginas > 1:
            embed.set_footer(
                text=f"🌑 Aeon & ☀️ Celestia — página {idx + 1}/{total_paginas} • use ◀ ▶ pra navegar • atualizado a cada 1 min"
            )
        else:
            embed.set_footer(text=RODAPE_PADRAO)
        embeds.append(embed)

    return embeds


# ══════════════════════════════════════════════════════════════════════
# Navegação do ranking — setinhas ◀ ▶
# O ranking vive numa ÚNICA mensagem fixa (compartilhada por todo mundo
# que olha o canal). Como não dá pra ter "uma página por pessoa" numa
# mensagem só, quem clica na seta troca a página pra todo mundo ver —
# funciona como um controle remoto compartilhado do ranking.
# ══════════════════════════════════════════════════════════════════════

class RankingXPView(discord.ui.View):
    """View persistente (sobrevive a reinícios do bot) com as setinhas
    ◀ ▶ que navegam entre as páginas do ranking de nível. As setas ficam
    desabilitadas sozinhas quando só existe 1 página (nada pra navegar)."""

    def __init__(self, total_paginas: int = 1):
        super().__init__(timeout=None)
        sem_navegacao = total_paginas <= 1

        botao_anterior = discord.ui.Button(
            emoji="◀",
            style=discord.ButtonStyle.secondary,
            custom_id="ranking_xp_seta_anterior",
            disabled=sem_navegacao,
            row=0,
        )
        botao_anterior.callback = self._callback_anterior

        botao_proxima = discord.ui.Button(
            emoji="▶",
            style=discord.ButtonStyle.secondary,
            custom_id="ranking_xp_seta_proxima",
            disabled=sem_navegacao,
            row=0,
        )
        botao_proxima.callback = self._callback_proxima

        self.add_item(botao_anterior)
        self.add_item(botao_proxima)

    async def _callback_anterior(self, interaction: discord.Interaction):
        await self._navegar(interaction, -1)

    async def _callback_proxima(self, interaction: discord.Interaction):
        await self._navegar(interaction, +1)

    async def _navegar(self, interaction: discord.Interaction, direcao: int) -> None:
        global _xp_ranking_pagina_atual

        if interaction.guild is None:
            await interaction.response.defer()
            return

        embeds = _montar_embeds_ranking_xp(interaction.guild)
        total_paginas = len(embeds)

        # Passeia em círculo: da última página volta pra primeira e vice-versa.
        _xp_ranking_pagina_atual = (_xp_ranking_pagina_atual + direcao) % total_paginas

        try:
            await interaction.response.edit_message(
                embed=embeds[_xp_ranking_pagina_atual],
                view=RankingXPView(total_paginas=total_paginas),
            )
        except discord.HTTPException as e:
            print(f"[ranking-xp] ERRO ao navegar entre páginas do ranking: {e!r}")
            try:
                await interaction.response.defer()
            except discord.HTTPException:
                pass

        asyncio.create_task(_salvar_xp_stats())


async def _achar_mensagens_ranking_xp(canal: discord.TextChannel) -> list:
    """Varre o histórico do canal procurando mensagens do ranking já
    postadas pelo bot. Serve principalmente pra MIGRAÇÃO: versões antigas
    (antes das setinhas ◀ ▶) podiam empilhar várias páginas como mensagens
    separadas — essa função acha todas elas (a mais antiga primeiro) pra
    que _atualizar_ranking_xp mantenha só a primeira e apague o resto."""
    encontradas = []
    try:
        async for msg in canal.history(limit=50):
            if (
                msg.author.id == bot.user.id
                and msg.embeds
                and (msg.embeds[0].title or "").startswith("⭐ Ranking de Nível")
            ):
                encontradas.append(msg)
    except (discord.Forbidden, discord.HTTPException):
        return []
    encontradas.sort(key=lambda m: m.created_at)
    return encontradas


# ══════════════════════════════════════════════════════════════════════
# Menu de personalização — escolha da cor do quadradinho no ranking
# Fica numa mensagem fixa logo abaixo do ranking. Cada pessoa escolhe a
# própria cor no menu (dropdown) e a mudança já vale pra próxima vez que
# o ranking for atualizado (no máximo 1 min, ou na hora, se possível).
# ══════════════════════════════════════════════════════════════════════

_XP_COR_TITULO = "🎨 Personalize seu quadradinho!"


class CorQuadradoSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=info["label"],
                value=chave,
                emoji=info["emoji"],
                default=(chave == _COR_PADRAO),
            )
            for chave, info in _CORES_QUADRADO.items()
        ]
        super().__init__(
            placeholder="🎨 Escolha a cor do seu quadradinho...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="xp_cor_quadrado_select",
        )

    async def callback(self, interaction: discord.Interaction):
        cor_escolhida = self.values[0]
        info = _CORES_QUADRADO.get(cor_escolhida)
        if info is None:
            await interaction.response.send_message(
                "⚠️ Cor inválida, tenta de novo.", ephemeral=True
            )
            return

        # Cores especiais (arco-íris, xadrez, etc.) são exclusivas de quem
        # tem o cargo de Booster do servidor.
        if info.get("booster"):
            cargo_booster = interaction.guild.get_role(_CARGO_BOOSTER_CORES_ID) if interaction.guild else None
            tem_cargo = (
                cargo_booster is not None
                and isinstance(interaction.user, discord.Member)
                and cargo_booster in interaction.user.roles
            )
            if not tem_cargo:
                await interaction.response.send_message(
                    f"💎 A cor **{info['label']}** é exclusiva de quem tem o cargo <@&{_CARGO_BOOSTER_CORES_ID}>! "
                    "🌟 **Celestia:** Impulsiona o servidor que eu libero ela na hora pra você!! 🌈✨\n"
                    "🌑 **Aeon:** ...as sombras não abrem exceção. Nem pra mim. 🖤🌑",
                    ephemeral=True,
                )
                return

        dados = xp_stats[interaction.user.id]
        dados["cor"] = cor_escolhida
        asyncio.create_task(_salvar_xp_stats())

        await interaction.response.send_message(
            f"{info['emoji']} Combinado! Seu quadradinho no ranking agora é **{info['label']}**. "
            "🌑 **Aeon:** ...as sombras registraram sua escolha. 🌟 **Celestia:** FICOU LINDO!! ✨",
            ephemeral=True,
        )

        # Tenta atualizar o ranking na hora, pra pessoa já ver a cor nova
        # sem precisar esperar o próximo ciclo automático (até 1 min).
        try:
            await _atualizar_ranking_xp()
        except Exception as e:
            print(f"[ranking-xp] ERRO ao atualizar ranking após troca de cor: {e!r}")


class CorQuadradoView(discord.ui.View):
    """View persistente com o menu de escolha de cor — sobrevive a reinícios do bot."""

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CorQuadradoSelect())


def _montar_embed_pergunta_cor() -> discord.Embed:
    embed = discord.Embed(
        title=_XP_COR_TITULO,
        description=(
            "🌟 **Celestia:** Psiu!! Quer que o seu quadradinho no ranking tenha "
            "uma cor diferente?? 😆🌈✨ *aponta pro menu com empolgação*\n"
            "🌑 **Aeon:** ...escolha no menu abaixo. A cor é só sua — ninguém mais mexe nela. 🖤🌑\n\n"
            f"💎 **Cores especiais** (🌈 Arco-íris, 🏁 Xadrez, ✨ Dourado Cintilante, 🌊 Gradiente) são "
            f"exclusivas de quem tem o cargo <@&{_CARGO_BOOSTER_CORES_ID}>!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎨 Selecione uma cor no menu para personalizar seu quadradinho.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xe8d5f5,
    )
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Personalização do Ranking")
    return embed


async def _achar_mensagem_cor_xp(canal: discord.TextChannel):
    """Varre o histórico do canal, apaga mensagens de escolha de cor duplicadas
    antigas (deixando só a mais recente) e devolve essa mensagem pra ser editada."""
    mensagens = []
    try:
        async for msg in canal.history(limit=50):
            if msg.author.id == bot.user.id and msg.embeds and msg.embeds[0].title == _XP_COR_TITULO:
                mensagens.append(msg)
    except (discord.Forbidden, discord.HTTPException):
        return None

    if not mensagens:
        return None

    mais_recente, *duplicadas = mensagens
    for dup in duplicadas:
        try:
            await dup.delete()
        except discord.HTTPException:
            pass
    return mais_recente


async def _atualizar_pergunta_cor(canal: discord.TextChannel) -> None:
    """Garante que a mensagem com o menu de escolha de cor fique sempre logo
    abaixo do ranking (fixa, editada, nunca duplicada)."""
    global _xp_cor_message_id

    embed = _montar_embed_pergunta_cor()
    view = CorQuadradoView()

    mensagem = None
    if _xp_cor_message_id:
        try:
            mensagem = await canal.fetch_message(_xp_cor_message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            mensagem = None

    if mensagem is None:
        mensagem = await _achar_mensagem_cor_xp(canal)

    if mensagem:
        try:
            await mensagem.edit(embed=embed, view=view)
            _xp_cor_message_id = mensagem.id
            return
        except discord.HTTPException as e:
            print(f"[ranking-xp] ERRO ao editar mensagem de escolha de cor: {e!r}")
            mensagem = None

    try:
        nova = await canal.send(embed=embed, view=view)
        _xp_cor_message_id = nova.id
        print(f"[ranking-xp] Mensagem de escolha de cor criada em #{canal.name} (id {nova.id}).")
    except discord.HTTPException as e:
        print(f"[ranking-xp] ERRO ao enviar mensagem de escolha de cor em #{canal.name}: {e!r}")


# ══════════════════════════════════════════════════════════════════════
# Mensagem fixa explicando a mecânica de batalhas — fica logo abaixo da
# de escolha de cor, sempre editada (nunca duplica).
# ══════════════════════════════════════════════════════════════════════

_XP_BATALHA_INFO_TITULO = "⚔️ Quer testar suas criaturas? Batalhe por pontos!"


def _montar_embed_info_batalha() -> discord.Embed:
    embed = discord.Embed(
        title=_XP_BATALHA_INFO_TITULO,
        description=(
            "🌟 **Celestia:** Sabia que dá pra DESAFIAR outras pessoas por aqui?? 😆⚔️✨ "
            "*pula animada* Bora te explicar como funciona!!\n"
            "🌑 **Aeon:** ...preste atenção. As regras das sombras são simples. 🖤🌑\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "**1️⃣ Como desafiar**\n"
            "Escreva `Eu te desafio @alguém` em qualquer canal. A pessoa desafiada "
            f"tem `{_BATALHA_TEMPO_ACEITE}s` pra **aceitar** ou **recusar** no botão que aparece.\n\n"
            "**2️⃣ A batalha**\n"
            "Se aceitar, cada lado invoca uma criatura aleatória **dentre as que já desbloqueou** — "
            "ninguém invoca o que não possui! — e elas se enfrentam num combate dramático. "
            "O vencedor é sorteado — pode ser qualquer um dos dois.\n\n"
            "**3️⃣ O roubo de XP**\n"
            f"Quem vence PODE roubar uma fatia do XP total de quem perdeu: um dado decide entre "
            f"`{_BATALHA_ROUBO_MIN * 100:.0f}%` e `{_BATALHA_ROUBO_MAX * 100:.0f}%`. "
            f"Mas cuidado: existe `{_BATALHA_CHANCE_SEM_ROUBO * 100:.0f}%` de chance do vencedor "
            "não levar **nada**, mesmo ganhando — é sorte pura!\n\n"
            "**4️⃣ Desbloqueando criaturas**\n"
            "Toda criatura tem uma **raridade** — ⚪ Comum, 🔵 Raro, 🟣 Épico, 🟡 Lendário, 🌀 Elemental, 🐺 Bestas, "
            "🦴 Fóssil, 🌌 Secreto ou 🐉 Mítico — e quanto mais rara, menos ela costuma aparecer nos sorteios. Todo "
            "mundo já começa com as ⚪ Comuns desbloqueadas; Raras, Épicas e Lendárias saem **de recompensa** pra "
            "quem **vence** uma batalha — o jogo sorteia uma criatura nova (que você ainda não tem) e ela entra "
            "pra sua coleção pra sempre. Quem perde não ganha nada disso. 🌀 Elementais, 🐺 Bestas, 🦴 Fósseis, "
            "🌌 Secretas e 🐉 Míticas seguem caminhos próprios pra desbloquear — veja os itens 8️⃣, 9️⃣, 🔟 e 1️⃣2️⃣ "
            "abaixo. Veja a lista completa na 📖 **Enciclopédia** (mensagem fixa aqui embaixo) e confira sua "
            "coleção com `.criaturas`.\n\n"
            "**5️⃣ ⭐ Nível de Capacidade — quanto mais usa, mais forte fica**\n"
            "Além da raridade, toda criatura tem um **Nível de Capacidade** individual (de 1 a "
            f"{_NIVEL_CRIATURA_MAX}), que é **por pessoa**. Ela sempre começa no Nível 1, e cada vez que "
            "você a invoca numa batalha — ganhando ou perdendo, não importa — ela ganha experiência e "
            "pode subir de nível, até o teto. Ou seja: se duas pessoas tiverem a MESMA criatura, mas uma "
            "já batalhou muito mais com ela, a mais usada leva vantagem no confronto, mesmo sendo a "
            "mesma raridade. Confira o nível de cada uma sua com `.criaturas`.\n\n"
            "**6️⃣ 🌟 Criatura favorita**\n"
            "Use `.favorito <nome da criatura>` pra escolher uma favorita entre as que você já tem — "
            "a partir daí, ela é **sempre** a escolhida nas suas batalhas, sem sorteio nenhum. Só que "
            f"depois de `{_FAVORITO_USOS_ATE_CANSAR}` usos seguidos ela **cansa**: some da jogada, suas "
            "batalhas voltam a sortear aleatoriamente, e ela entra num cooldown de "
            f"`{_FAVORITO_COOLDOWN_SEGUNDOS // 60} min` até poder ser favoritada de novo (ou você pode "
            "trocar de favorita a qualquer momento com `.favorito <outro nome>`, ou tirar com "
            "`.favorito remover`). Veja `.favorito` sozinho pra conferir o status atual.\n\n"
            "**7️⃣ ⚔️ Hierarquia de força das raridades**\n"
            "Raridade mais alta = criatura mais forte, mas ninguém fica sem chance nenhuma! "
            "A cada raridade de distância entre as duas criaturas, a chance da mais forte sobe um "
            "degrau — só que a mais fraca **sempre** mantém uma chance real de dar a zebra:\n"
            f"⚪↔🔵 **1 raridade de distância:** `{_CHANCE_VITORIA_POR_DEGRAU[1]*100:.0f}%` x `{(1-_CHANCE_VITORIA_POR_DEGRAU[1])*100:.0f}%`\n"
            f"⚪↔🟣 **2 raridades de distância:** `{_CHANCE_VITORIA_POR_DEGRAU[2]*100:.0f}%` x `{(1-_CHANCE_VITORIA_POR_DEGRAU[2])*100:.0f}%`\n"
            f"⚪↔🟡 **3 raridades de distância:** `{_CHANCE_VITORIA_POR_DEGRAU[3]*100:.0f}%` x `{(1-_CHANCE_VITORIA_POR_DEGRAU[3])*100:.0f}%`\n"
            f"⚪↔🐺 **4 raridades de distância:** `{_CHANCE_VITORIA_POR_DEGRAU[4]*100:.0f}%` x `{(1-_CHANCE_VITORIA_POR_DEGRAU[4])*100:.0f}%`\n"
            f"⚪↔🦴 **5 raridades de distância:** `{_CHANCE_VITORIA_POR_DEGRAU[5]*100:.0f}%` x `{(1-_CHANCE_VITORIA_POR_DEGRAU[5])*100:.0f}%`\n"
            f"⚪↔🌌 **6 raridades de distância:** `{_CHANCE_VITORIA_POR_DEGRAU[6]*100:.0f}%` x `{(1-_CHANCE_VITORIA_POR_DEGRAU[6])*100:.0f}%`\n"
            f"⚪↔🐉 **7 raridades de distância (máxima):** `{_CHANCE_VITORIA_POR_DEGRAU[7]*100:.0f}%` x `{(1-_CHANCE_VITORIA_POR_DEGRAU[7])*100:.0f}%`\n"
            f"Mesma raridade (ex: Épico vs Épico) é sempre `{_CHANCE_VITORIA_POR_DEGRAU[0]*100:.0f}%` x "
            f"`{_CHANCE_VITORIA_POR_DEGRAU[0]*100:.0f}%` como ponto de partida — e o Nível de Capacidade de "
            f"cada criatura (item acima) ainda refina esse número um pouco pra cima ou pra baixo.\n"
            f"⚠️ **Excepção:** 🟡 Lendário vs 🐉 Mítico e 🟡 Lendário vs 🌌 Secreto não seguem essa "
            f"tabela por degraus — a discrepância aqui é bem maior que em qualquer outro confronto:\n"
            f"🟡↔🐉 **Lendário vs Mítico:** `{_CHANCE_VITORIA_LENDARIO_MITICO*100:.0f}%` x "
            f"`{(1-_CHANCE_VITORIA_LENDARIO_MITICO)*100:.0f}%`\n"
            f"🟡↔🌌 **Lendário vs Secreto:** `{_CHANCE_VITORIA_LENDARIO_SECRETO*100:.0f}%` x "
            f"`{(1-_CHANCE_VITORIA_LENDARIO_SECRETO)*100:.0f}%`\n\n"
            "**8️⃣ 🐺 Bestas — a recompensa de quem treina de verdade**\n"
            "Mais fortes que as 🟡 Lendárias, mas ainda um degrau abaixo das 🌌 Secretas. Não saem de nenhum "
            "sorteio — a ÚNICA forma de conseguir uma é levando uma criatura ⚪ Comum, 🔵 Raro, 🟣 Épico ou 🟡 Lendário até o "
            f"Nível de Capacidade máximo (`{_NIVEL_CRIATURA_MAX}`, item 5️⃣ acima). Ao bater esse nível, você ganha, "
            "na hora e de graça, 1 Besta sorteada entre as do tier correspondente que você ainda não tiver — "
            "garantido, sem depender de sorte nenhuma!\n\n"
            "**9️⃣ 🐉 Míticos — os dragões**\n"
            "A raridade mais forte de todas, e também a mais rara de conseguir: não entram no sorteio "
            f"normal — a cada `{_MITICO_VITORIAS_INTERVALO}` vitórias suas, rola uma chance de só "
            f"`{_MITICO_CHANCE_DESBLOQUEIO * 100:.0f}%` de destravar um.\n\n"
            "**🔟 🦴 Fósseis — só desenterrados em call**\n"
            "Um degrau abaixo das 🌌 Secretas, mas mais fortes que as 🟡 Lendárias. Não entram no sorteio "
            "normal, no 🪙 Baú nem no `.ovo` — a ÚNICA forma de conseguir um é **vencendo** uma batalha de "
            "desafio com você **E** a pessoa que te desafiou (ou que você desafiou) **os dois numa call de "
            f"voz** no momento em que a batalha termina. Só nessas condições rola uma chance de "
            f"`{_FOSSIL_CHANCE_DESBLOQUEIO * 100:.0f}%` de desenterrar um Fóssil novo — se algum dos dois "
            "não estiver em call, a rolagem nem acontece.\n\n"
            "**1️⃣1️⃣ 🐾 Pets — companheiros de suporte contra Boss**\n"
            f"Leve uma criatura 🔵 Rara até o Nível de Capacidade `{_PET_NIVEL_DESBLOQUEIO}` e "
            "ganhe, de graça, um Pet sorteado. Pets não batalham no PvP — são suporte: EQUIPADOS "
            f"(`.equiparpet <nome>`), somam entre `{_PET_BONUS_BOSS_NIVEL1*100:.0f}%` e "
            f"`{_PET_BONUS_BOSS_NIVEL5*100:.0f}%` na chance de vencer qualquer Boss (conforme o "
            "Nível do Pet, de 1 a 5) e têm chance de upar uma das suas criaturas depois de uma "
            "vitória. Só sobem de Nível enfrentando Boss, e cada um destrava uma habilidade "
            "especial própria no Nível 3. Veja todos na 📖 Enciclopédia!\n\n"
            "**1️⃣2️⃣ 🌀 Elementais — o prêmio de quem evolui uma Épica**\n"
            "Mais fortes que as 🟡 Lendárias, mas ainda um degrau abaixo das 🐺 Bestas. A única forma de "
            f"conseguir um é levando uma criatura 🟣 Épica até o **Nível de Capacidade `{_ELEMENTAL_NIVEL_DESBLOQUEIO}`** "
            "(não precisa ser o teto) — ao bater esse nível, você recebe, na hora e de graça, 1 Elemental "
            "sorteado entre os 12 que ainda não tiver (sem distinção de tier, todos entram no mesmo sorteio). "
            "E não para aí: toda vez que um Elemental for convocado numa batalha de desafio — ganhando ou "
            "perdendo, não importa — quem o convocou ganha, na hora, um **Booster de xp em dobro** por "
            f"`{_ELEMENTAL_BOOSTER_MINUTOS} min` (empilha em cima de qualquer outro booster já ativo). Todo "
            f"desbloqueio de Elemental é anunciado em <#{_BESTA_ANUNCIO_CANAL_ID}>. ⚡\n\n"
            "**1️⃣3️⃣ Pra poder batalhar**\n"
            "Os dois precisam ter o cargo do ranking de nível e já ter algum XP acumulado. "
            f"E cada pessoa só pode lançar um novo desafio a cada `{_BATALHA_COOLDOWN_SEGUNDOS // 60} min`.\n\n"
            "💨 *Todas as mensagens da batalha (convite, criaturas e resultado) somem sozinhas "
            f"depois de `{_BATALHA_TEMPO_SOMEM}s` — não fica lixo acumulando no chat!*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xe8d5f5,
    )
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Arena de Batalhas")
    return embed


async def _achar_mensagem_info_batalha(canal: discord.TextChannel):
    """Varre o histórico do canal, apaga explicações de batalha duplicadas
    antigas (deixando só a mais recente) e devolve essa mensagem pra ser editada."""
    mensagens = []
    try:
        async for msg in canal.history(limit=50):
            if msg.author.id == bot.user.id and msg.embeds and msg.embeds[0].title == _XP_BATALHA_INFO_TITULO:
                mensagens.append(msg)
    except (discord.Forbidden, discord.HTTPException):
        return None

    if not mensagens:
        return None

    mais_recente, *duplicadas = mensagens
    for dup in duplicadas:
        try:
            await dup.delete()
        except discord.HTTPException:
            pass
    return mais_recente


async def _atualizar_info_batalha(canal: discord.TextChannel) -> None:
    """Garante que a mensagem explicando as batalhas fique sempre logo abaixo
    da mensagem de escolha de cor (fixa, editada, nunca duplicada)."""
    global _xp_batalha_info_message_id

    embed = _montar_embed_info_batalha()

    mensagem = None
    if _xp_batalha_info_message_id:
        try:
            mensagem = await canal.fetch_message(_xp_batalha_info_message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            mensagem = None

    if mensagem is None:
        mensagem = await _achar_mensagem_info_batalha(canal)

    if mensagem:
        try:
            await mensagem.edit(embed=embed)
            _xp_batalha_info_message_id = mensagem.id
            return
        except discord.HTTPException as e:
            print(f"[ranking-xp] ERRO ao editar mensagem de explicação de batalha: {e!r}")
            mensagem = None

    try:
        nova = await canal.send(embed=embed)
        _xp_batalha_info_message_id = nova.id
        print(f"[ranking-xp] Mensagem de explicação de batalha criada em #{canal.name} (id {nova.id}).")
    except discord.HTTPException as e:
        print(f"[ranking-xp] ERRO ao enviar mensagem de explicação de batalha em #{canal.name}: {e!r}")


# ══════════════════════════════════════════════════════════════════════
# ENCICLOPÉDIA DE CRIATURAS — fica por ÚLTIMO no canal de ranking, embaixo
# de tudo (ranking, cor e explicação de batalha). Lista todas as criaturas
# que existem, agrupadas por raridade. Cada pessoa pode usar o menu de
# seleção pra ver os detalhes (imagem) de uma criatura e conferir, de forma
# privada (ephemeral), se ELA MESMA já desbloqueou aquela criatura ou não.
# ══════════════════════════════════════════════════════════════════════

_XP_ENCICLOPEDIA_TITULO = "📖 Enciclopédia de Criaturas"


def _montar_embed_enciclopedia() -> discord.Embed:
    """Monta o embed geral da Enciclopédia: todas as criaturas existentes,
    agrupadas por raridade (da mais rara pra mais comum)."""
    embed = discord.Embed(
        title=_XP_ENCICLOPEDIA_TITULO,
        description=(
            "🌟 **Celestia:** Toda criatura que já apareceu (ou pode aparecer) na Arena de "
            "Batalhas mora aqui!! 😆📖✨\n"
            "🌑 **Aeon:** ...todo mundo começa com as ⚪ Comuns. Só dá pra invocar em batalha o que "
            "você já tem — vença combates e, de recompensa, você pode destravar uma criatura nova "
            "pra coleção. 🖤🌑\n"
            "🌟 **Celestia:** E os 🐉 MÍTICOS são OUTRO NÍVEL!! 😱✨ Quase imbatíveis contra qualquer "
            "raridade menor, mas RARÍSSIMOS de conseguir — só numa chance bem pequena a cada várias "
            "vitórias!!\n"
            "🌑 **Aeon:** ...e as 🌌 Secretas nem essas vitórias concedem. Só saem do 🪙 Baú, com uma "
            "chance minúscula. As mais raras de todas. 🖤🌌\n"
            "🌟 **Celestia:** E os 🦴 FÓSSEIS só aparecem pra quem tá DE CALL!! 😆🎧✨ Vence uma batalha "
            "com você e a outra pessoa os dois numa call de voz, e rola uma chancezinha de desenterrar "
            "um!!\n"
            "🌟 **Celestia:** E as 🐺 BESTAS não vêm de sorte NENHUMA!! 💪✨ É pura conquista — leva uma "
            f"criatura ⚪🔵🟣🟡 até o Nível de Capacidade máximo (`{_NIVEL_CRIATURA_MAX}`) e ela é sua, garantido!!\n\n"
            "🌑 **Aeon:** ...e os 🌀 ELEMENTAIS só chegam pra quem leva uma 🟣 Épica até o Nível de Capacidade "
            f"`{_ELEMENTAL_NIVEL_DESBLOQUEIO}` — sem sorteio, pura conquista. E cada Elemental usado em batalha "
            "ainda concede, na hora, um Booster de xp em dobro pra quem o convocou. 🖤🌀\n\n"
            "👇 Use o menu abaixo pra escolher uma raridade — ele abre, só pra você, as criaturas "
            "daquela raridade pra conferir os detalhes (e a imagem) de cada uma."
        ),
        color=0x9b59b6,
    )
    for raridade in _ORDEM_RARIDADES:
        info = _RARIDADES[raridade]
        nomes = [c["nome"] for c in _BATALHA_CRIATURAS if c["raridade"] == raridade]
        if not nomes:
            continue
        embed.add_field(
            name=f"{info['emoji']} {info['label']} ({len(nomes)})",
            value="\n".join(f"• {nome}" for nome in nomes),
            inline=False,
        )

    embed.add_field(
        name=f"🐾 Pets ({len(_PETS)})",
        value=(
            "\n".join(f"• {p['nome']}" for p in _PETS) + "\n\n"
            f"Desbloqueados ao levar uma criatura 🔵 Rara até o Nível de Capacidade "
            f"`{_PET_NIVEL_DESBLOQUEIO}` — não entram em batalha, são SUPORTE: quando equipados "
            "(`.equiparpet <nome>`), somam bônus na chance de vencer Boss e podem upar suas "
            "criaturas. Confira os detalhes de cada um no menu abaixo!"
        ),
        inline=False,
    )

    embed.set_footer(text=f"🌑 Aeon & ☀️ Celestia — {len(_BATALHA_CRIATURAS)} criaturas e {len(_PETS)} pets ao todo")
    return embed


class EnciclopediaSelect(discord.ui.Select):
    """Menu de seleção com as criaturas de UMA raridade. Ao escolher uma, a
    pessoa recebe (de forma privada) a imagem, a raridade e se JÁ desbloqueou
    aquela criatura.

    Existe um select por raridade (em vez de um único com todas as criaturas)
    porque o Discord só permite até 25 opções por menu — dividindo por
    raridade, cada menu tem bastante folga pra coleção continuar crescendo."""

    def __init__(self, raridade: str):
        self.raridade = raridade
        info = _RARIDADES[raridade]
        criaturas_da_raridade = [c for c in _BATALHA_CRIATURAS if c["raridade"] == raridade][:25]
        options = [
            discord.SelectOption(
                label=c["nome"][:100],
                value=c["id"],
                description=info["label"],
                emoji=info["emoji"],
            )
            for c in criaturas_da_raridade
        ]
        super().__init__(
            placeholder=f"{info['emoji']} Ver criaturas {info['label']}s...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"enciclopedia_criaturas_select_{raridade}",
        )

    async def callback(self, interaction: discord.Interaction):
        criatura = next((c for c in _BATALHA_CRIATURAS if c["id"] == self.values[0]), None)
        if criatura is None:
            await interaction.response.send_message("⚠️ Criatura não encontrada.", ephemeral=True)
            return

        desbloqueada = criatura["id"] in set(_garantir_criaturas_iniciais(interaction.user.id))
        info_raridade = _RARIDADES[criatura["raridade"]]

        if desbloqueada:
            nivel_pessoal = _nivel_criatura(interaction.user.id, criatura["id"])
            status = (
                "🔓 **Você já desbloqueou essa criatura!** Ela pode aparecer nas suas batalhas.\n"
                f"⭐ **Nível de Capacidade atual:** `{nivel_pessoal}/{_nivel_criatura_max(criatura['id'])}` — "
                "use ela em mais batalhas pra deixar cada vez mais forte."
            )
        else:
            status = (
                "🔒 **Você ainda não desbloqueou essa criatura.** "
                "Vença batalhas usando as que você já tem — como recompensa, "
                "há chance dela ser sorteada e ir pra sua coleção!"
            )

        embed = discord.Embed(
            title=f"{info_raridade['emoji']} {criatura['nome']}",
            description=f"**Raridade:** {info_raridade['label']}\n\n{status}",
            color=info_raridade["cor"],
        )
        embed.set_image(url=criatura["gif"])
        embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Enciclopédia de Criaturas")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class EnciclopediaRaridadeSelect(discord.ui.Select):
    """Passo 1 da navegação: escolher qual raridade explorar. Ao escolher,
    abre — só pra quem clicou — o menu com as criaturas daquela raridade
    (EnciclopediaSelect). Isso existe como um passo à parte (em vez de um
    select por raridade direto na mensagem fixa) porque o Discord só permite
    5 menus por mensagem, e com 8 raridades (contando 🦴 Fóssil e 🌌 Secreta) não
    caberia mais um select fixo por raridade — assim sobra espaço mesmo se
    surgirem raridades novas no futuro."""

    def __init__(self):
        options = []
        for raridade in _ORDEM_RARIDADES:
            if not any(c["raridade"] == raridade for c in _BATALHA_CRIATURAS):
                continue
            info = _RARIDADES[raridade]
            qtd = sum(1 for c in _BATALHA_CRIATURAS if c["raridade"] == raridade)
            options.append(
                discord.SelectOption(
                    label=f"{info['label']} ({qtd})",
                    value=raridade,
                    emoji=info["emoji"],
                )
            )
        super().__init__(
            placeholder="🔍 Escolha uma raridade pra explorar...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="enciclopedia_raridade_select",
        )

    async def callback(self, interaction: discord.Interaction):
        raridade = self.values[0]
        info = _RARIDADES[raridade]
        view = discord.ui.View(timeout=180)
        view.add_item(EnciclopediaSelect(raridade))
        await interaction.response.send_message(
            f"{info['emoji']} Escolha uma criatura **{info['label']}** pra ver os detalhes:",
            view=view,
            ephemeral=True,
        )


class EnciclopediaPetsSelect(discord.ui.Select):
    """Menu de seleção com todos os 🐾 Pets — como são só 8 (bem abaixo do
    limite de 25 opções do Discord), não precisa de um passo intermediário
    por raridade, igual as criaturas. Ao escolher um, a pessoa recebe (de
    forma privada) a imagem, se já desbloqueou, o Nível atual e a
    habilidade especial dele."""

    def __init__(self):
        options = [
            discord.SelectOption(label=p["nome"][:100], value=p["id"], emoji="🐾")
            for p in _PETS
        ]
        super().__init__(
            placeholder="🐾 Ver detalhes de um Pet...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="enciclopedia_pets_select",
        )

    async def callback(self, interaction: discord.Interaction):
        pet = next((p for p in _PETS if p["id"] == self.values[0]), None)
        if pet is None:
            await interaction.response.send_message("⚠️ Pet não encontrado.", ephemeral=True)
            return

        desbloqueado = pet["id"] in set(_pets_desbloqueados(interaction.user.id))

        if desbloqueado:
            nivel_pessoal = _nivel_pet(interaction.user.id, pet["id"])
            equipado = xp_stats[interaction.user.id].get("pet_equipado") == pet["id"]
            status = (
                "🔓 **Você já tem esse Pet!**" + (" 🐾 *(equipado agora)*" if equipado else "") + "\n"
                f"⭐ **Nível atual:** `{nivel_pessoal}/{_PET_NIVEL_MAX}` — só sobe enfrentando Boss.\n\n"
                f"**{pet['habilidade_nome']}** (destrava no Nível `{_PET_NIVEL_HABILIDADE}`): "
                f"{pet['habilidade_descricao']}"
                + ("\n\n✨ *Habilidade já ativa!*" if nivel_pessoal >= _PET_NIVEL_HABILIDADE else "")
            )
        else:
            status = (
                "🔒 **Você ainda não desbloqueou esse Pet.** Leve uma criatura 🔵 Rara até o "
                f"Nível de Capacidade `{_PET_NIVEL_DESBLOQUEIO}` — tem chance dele ser sorteado "
                "e ir pra sua coleção de graça!\n\n"
                f"**{pet['habilidade_nome']}:** {pet['habilidade_descricao']}"
            )

        embed = discord.Embed(
            title=f"🐾 {pet['nome']}",
            description=status,
            color=0x9b59b6,
        )
        embed.set_image(url=pet["gif"])
        embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Enciclopédia de Pets")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class EnciclopediaView(discord.ui.View):
    """View persistente (sobrevive a reinícios do bot) com o menu pra
    escolher a raridade de criatura — que abre, de forma privada, o menu
    com as criaturas daquela raridade — e o menu de 🐾 Pets, lado a lado."""

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(EnciclopediaRaridadeSelect())
        self.add_item(EnciclopediaPetsSelect())


async def _achar_mensagem_enciclopedia(canal: discord.TextChannel):
    """Varre o histórico do canal, apaga Enciclopédias duplicadas antigas
    (deixando só a mais recente) e devolve essa mensagem pra ser editada."""
    mensagens = []
    try:
        async for msg in canal.history(limit=50):
            if msg.author.id == bot.user.id and msg.embeds and msg.embeds[0].title == _XP_ENCICLOPEDIA_TITULO:
                mensagens.append(msg)
    except (discord.Forbidden, discord.HTTPException):
        return None

    if not mensagens:
        return None

    mais_recente, *duplicadas = mensagens
    for dup in duplicadas:
        try:
            await dup.delete()
        except discord.HTTPException:
            pass
    return mais_recente


async def _atualizar_enciclopedia(canal: discord.TextChannel) -> None:
    """Garante que a Enciclopédia fique sempre por ÚLTIMO no canal (fixa,
    editada, nunca duplicada), embaixo do ranking, da cor e da explicação
    de batalha."""
    global _xp_enciclopedia_message_id

    embed = _montar_embed_enciclopedia()
    view = EnciclopediaView()

    mensagem = None
    if _xp_enciclopedia_message_id:
        try:
            mensagem = await canal.fetch_message(_xp_enciclopedia_message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            mensagem = None

    if mensagem is None:
        mensagem = await _achar_mensagem_enciclopedia(canal)

    if mensagem:
        try:
            await mensagem.edit(embed=embed, view=view)
            _xp_enciclopedia_message_id = mensagem.id
            return
        except discord.HTTPException as e:
            print(f"[ranking-xp] ERRO ao editar mensagem de enciclopédia: {e!r}")
            mensagem = None

    try:
        nova = await canal.send(embed=embed, view=view)
        _xp_enciclopedia_message_id = nova.id
        print(f"[ranking-xp] Mensagem de enciclopédia criada em #{canal.name} (id {nova.id}).")
    except discord.HTTPException as e:
        print(f"[ranking-xp] ERRO ao enviar mensagem de enciclopédia em #{canal.name}: {e!r}")


async def _atualizar_ranking_xp() -> None:
    """Atualiza (ou cria, se ainda não existir) as mensagens de ranking de XP.
    Normalmente é só 1 mensagem, sempre editada (fixa no topo, nunca
    duplica). Todo mundo elegível aparece — inclusive quem está no Nível 0 —
    e se a lista ficar grande demais pra caber num único embed, as páginas
    extras ficam disponíveis pelas setinhas ◀ ▶ embaixo do ranking, sem
    empilhar mensagem nenhuma.

    ⚠️ Roda inteira dentro de um lock: essa função é chamada de vários
    lugares diferentes (loop automático, level-up, troca de cor, baú,
    batalhas...), às vezes via asyncio.create_task — sem o lock, duas
    chamadas concorrentes podiam achar que a mensagem fixa ainda não existe
    (porque nenhuma das duas tinha terminado de criar) e cada uma mandava
    uma cópia nova, duplicando ranking/cor/batalha/enciclopédia no canal."""
    global _xp_ranking_message_id, _xp_ranking_pagina_atual

    async with (_xp_ranking_update_lock or asyncio.Lock()):
        guild = bot.guilds[0] if bot.guilds else None
        if guild is None:
            print("[ranking-xp] ERRO: bot não está em nenhum servidor ainda.")
            return

        canal = guild.get_channel(CANAL_XP_ID)
        if canal is None:
            print(
                f"[ranking-xp] ERRO: canal com ID {CANAL_XP_ID} não encontrado em "
                f"'{guild.name}'. Confira se o ID do canal Ranking-01 está certo."
            )
            return

        embeds = _montar_embeds_ranking_xp(guild)
        total_paginas = len(embeds)

        # A página atual pode ter ficado fora do intervalo válido (ex: o total
        # de páginas diminuiu porque alguém saiu do servidor) — trava dentro
        # do limite pra nunca dar IndexError.
        if _xp_ranking_pagina_atual >= total_paginas:
            _xp_ranking_pagina_atual = total_paginas - 1
        if _xp_ranking_pagina_atual < 0:
            _xp_ranking_pagina_atual = 0

        embed_atual = embeds[_xp_ranking_pagina_atual]
        view = RankingXPView(total_paginas=total_paginas)

        mensagem = None
        if _xp_ranking_message_id:
            try:
                mensagem = await canal.fetch_message(_xp_ranking_message_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                mensagem = None

        if mensagem is None:
            # Procura no histórico — inclui achar páginas antigas empilhadas de
            # antes das setinhas existirem, pra ficar só com a mais antiga (as
            # extras são apagadas, já que agora tudo cabe numa mensagem só).
            candidatas = await _achar_mensagens_ranking_xp(canal)
            if candidatas:
                mensagem, *extras = candidatas
                for extra in extras:
                    try:
                        await extra.delete()
                    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                        pass

        if mensagem:
            try:
                await mensagem.edit(embed=embed_atual, view=view)
                _xp_ranking_message_id = mensagem.id
            except discord.HTTPException as e:
                print(f"[ranking-xp] ERRO ao editar mensagem do ranking: {e!r}")
                mensagem = None

        if mensagem is None:
            try:
                nova = await canal.send(embed=embed_atual, view=view)
                _xp_ranking_message_id = nova.id
                print(f"[ranking-xp] Mensagem do ranking criada em #{canal.name} (id {nova.id}).")
            except discord.HTTPException as e:
                print(f"[ranking-xp] ERRO ao enviar mensagem do ranking em #{canal.name}: {e!r}")

        # Mantém o menu de escolha de cor sempre fixo logo abaixo do ranking
        try:
            await _atualizar_pergunta_cor(canal)
        except Exception as e:
            print(f"[ranking-xp] ERRO ao atualizar mensagem de escolha de cor: {e!r}")

        # Mantém a explicação da mecânica de batalhas fixa logo abaixo da de cor
        try:
            await _atualizar_info_batalha(canal)
        except Exception as e:
            print(f"[ranking-xp] ERRO ao atualizar mensagem de explicação de batalha: {e!r}")

        # Mantém a Enciclopédia de Criaturas fixa por ÚLTIMO, embaixo de tudo
        try:
            await _atualizar_enciclopedia(canal)
        except Exception as e:
            print(f"[ranking-xp] ERRO ao atualizar mensagem de enciclopédia: {e!r}")

        await _salvar_xp_stats()


_XP_POR_TICK_CALL = 12   # xp ganho a cada 1 min em call de voz — dobrado de novo (era 6, antes disso era 2)

# Calls com xp bônus — canal_id -> multiplicador aplicado em cima do
# _XP_POR_TICK_CALL normal. Qualquer call que não estiver aqui usa o valor
# padrão (1x). Não afeta calls privadas, essas continuam sem xp nenhum.
_XP_CALLS_MULTIPLICADOR = {
    1284260386635251713: 3.0,   # o triplo de xp por minuto comparado às outras calls
}


# ── Booster de Call (streak) ────────────────────────────────────────────────
# Enquanto a pessoa fica numa MESMA call de voz, sem sair, sem mutar (nem por
# si mesma nem pelo servidor) e sem trocar de canal, o xp de call dela sobe
# de nível a cada _CALL_BOOSTER_INTERVALO_MINUTOS minutos: nível 1 = xp normal,
# nível 2 = xp em dobro, nível 3 = triplo, e assim por diante, sem limite.
# Qualquer uma dessas ações reseta o booster NA HORA, de volta pro nível 1:
#   • sair da call
#   • mutar (self-mute ou mute pelo servidor)
#   • trocar de canal de voz (mesmo pra outra call válida)
# Toda vez que o nível sobe, um aviso aparece no canal CANAL_XP_ID dizendo
# que o Booster de Call daquela pessoa foi ativado — e some sozinho depois
# de 1 minuto (mesmo canal e mesmo estilo do aviso de Level Up).
_CALL_BOOSTER_INTERVALO_MINUTOS = 20

_CALL_BOOSTER_DATA_FILE = os.path.join(_ANJO_DATA_DIR, "call_booster_data.json")

_call_booster_inicio: dict = {}            # user_id -> time.time() de quando a streak ATUAL começou (ininterrupta)
_call_booster_nivel_anunciado: dict = {}   # user_id -> último nível (x2, x3, x4...) já avisado no canal, pra não repetir


def _carregar_call_booster_stats() -> None:
    """Carrega a streak do Booster de Call salva em disco (na pasta do volume,
    _ANJO_DATA_DIR), se existir. Roda antes do bot conectar — é isso que
    permite a streak de quem já estava numa call sobreviver a um reinício
    do bot (Railway ou qualquer outro), em vez de voltar pro nível 1 na hora.
    A reconciliação final (quem realmente ainda está numa call válida agora)
    acontece no on_ready, depois que o bot já sabe quem está conectado."""
    if not os.path.exists(_CALL_BOOSTER_DATA_FILE):
        return
    try:
        with open(_CALL_BOOSTER_DATA_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        for uid_str, inicio in dados.get("inicio", {}).items():
            _call_booster_inicio[int(uid_str)] = inicio
        for uid_str, nivel in dados.get("nivel_anunciado", {}).items():
            _call_booster_nivel_anunciado[int(uid_str)] = nivel
    except (json.JSONDecodeError, OSError, ValueError):
        pass


async def _salvar_call_booster_stats() -> None:
    """Salva a streak do Booster de Call em disco de forma atômica (escreve em
    .tmp e substitui) — pra não perder o progresso quando o bot reiniciar."""
    dados = {
        "inicio": {str(uid): inicio for uid, inicio in _call_booster_inicio.items()},
        "nivel_anunciado": {str(uid): nivel for uid, nivel in _call_booster_nivel_anunciado.items()},
    }
    tmp_path = _CALL_BOOSTER_DATA_FILE + ".tmp"

    def _escrever():
        os.makedirs(_ANJO_DATA_DIR, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, _CALL_BOOSTER_DATA_FILE)

    try:
        loop = asyncio.get_event_loop()
        async with (_xp_stats_lock or asyncio.Lock()):
            await loop.run_in_executor(None, _escrever)
    except OSError:
        pass


def _nivel_call_booster(user_id: int) -> int:
    """Nível atual do Booster de Call de alguém: 1 = sem boost (xp de call normal),
    2 = xp de call em dobro, 3 = triplo... sobe 1 nível a cada
    _CALL_BOOSTER_INTERVALO_MINUTOS minutos ininterruptos numa mesma call.
    Sem streak ativa agora (não está numa call qualificada), devolve 1 (sem efeito)."""
    inicio = _call_booster_inicio.get(user_id)
    if inicio is None:
        return 1
    minutos_corridos = (time.time() - inicio) / 60
    return 1 + int(minutos_corridos // _CALL_BOOSTER_INTERVALO_MINUTOS)


def _resetar_call_booster(user_id: int) -> None:
    """Zera a streak do Booster de Call de alguém — perde o multiplicador na
    hora (saiu da call, mutou, ou trocou de canal)."""
    tinha_streak = user_id in _call_booster_inicio
    _call_booster_inicio.pop(user_id, None)
    _call_booster_nivel_anunciado.pop(user_id, None)
    if tinha_streak:
        asyncio.create_task(_salvar_call_booster_stats())


def _iniciar_call_booster(user_id: int) -> None:
    """Começa (ou reinicia do zero) a contagem da streak do Booster de Call."""
    _call_booster_inicio[user_id] = time.time()
    _call_booster_nivel_anunciado[user_id] = 1
    asyncio.create_task(_salvar_call_booster_stats())


def _empilhar_call_booster(user_id: int, ciclos: int = 1) -> None:
    """Adianta o relógio da streak do Booster de Call de alguém em `ciclos`
    intervalos inteiros de _CALL_BOOSTER_INTERVALO_MINUTOS — na prática,
    empilha +1 nível de booster por ciclo EM CIMA do que a pessoa já tiver
    (se ela já estiver numa streak de verdade, soma tempo a mais nela em vez
    de resetar; se não tiver nenhuma rodando, começa uma nova já adiantada)."""
    avanco_segundos = ciclos * _CALL_BOOSTER_INTERVALO_MINUTOS * 60
    inicio_atual = _call_booster_inicio.get(user_id, time.time())
    _call_booster_inicio[user_id] = inicio_atual - avanco_segundos
    asyncio.create_task(_salvar_call_booster_stats())


async def _anunciar_call_booster(guild: discord.Guild, membro: discord.Member, nivel: int) -> None:
    """Avisa no canal de XP que o Booster de Call de alguém subiu pro nível
    informado (x2, x3, x4...). O aviso some sozinho depois de 1 minuto."""
    canal = guild.get_channel(CANAL_XP_ID)
    if canal is None:
        return

    embed = discord.Embed(
        title="🔥 Booster de Call ativado!",
        description=(
            f"⚡ {membro.mention} ficou tempo suficiente numa call sem sair, sem mutar e sem trocar "
            f"de canal — o xp de call agora está em **`x{nivel}`**!\n\n"
            "🌟 **Celestia:** *brilha mais forte* CONTINUA NA CALL QUE AUMENTA AINDA MAIS!! 💫✨\n"
            "🌑 **Aeon:** ...saia, troque de call ou mute, e o booster desaparece na hora. 🖤🌑"
        ),
        color=0xff8c42,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Booster de Call • some em 1 minuto")

    try:
        msg = await canal.send(embed=embed)
        asyncio.create_task(_apagar_mensagem_depois(msg, 60))
    except discord.HTTPException:
        pass


async def _processar_call_booster_voice(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
    """Controla a streak do Booster de Call a partir de cada mudança de estado
    de voz: começa a contar quando a pessoa entra numa call válida (não-privada)
    e desmutada, e reseta na hora se ela sair da call, mutar (self ou servidor)
    ou trocar de canal de voz."""
    if member.bot:
        return

    try:
        canal_antes = before.channel
        canal_depois = after.channel
        mutado_depois = bool(after.self_mute or after.mute)

        # Saiu da call inteiramente -> perde o booster na hora
        if canal_depois is None:
            _resetar_call_booster(member.id)
            return

        # Trocou de canal de voz -> perde o booster na hora, mesmo indo pra outra call válida
        trocou_de_canal = canal_antes is not None and canal_antes.id != canal_depois.id
        if trocou_de_canal:
            _resetar_call_booster(member.id)

        # Calls privadas não participam do booster de call (mesma regra do xp de call)
        if canal_depois.id in _XP_CALLS_PRIVADAS:
            _resetar_call_booster(member.id)
            return

        if mutado_depois:
            # Mutou agora (self-mute ou mute pelo servidor) -> perde o booster na hora
            _resetar_call_booster(member.id)
            return

        # Está numa call válida e desmutada: se não tinha streak rodando
        # (acabou de entrar, de trocar de canal, ou de desmutar), começa do zero.
        if _call_booster_inicio.get(member.id) is None:
            _iniciar_call_booster(member.id)
    except Exception as e:
        print(f"[booster-call] ERRO ao processar {member} ({member.id}): {e!r}")


async def _processar_xp_call(guild: discord.Guild) -> None:
    """A cada 1 minuto (mesmo ritmo do loop de ranking), dá um pouco de xp pra
    quem está numa call de voz agora. É só um reforço — bem menos do que
    mandar mensagem nos canais principais, mas já soma algo. Destravado pra
    todo mundo, sem exigir cargo. Calls privadas (_XP_CALLS_PRIVADAS) não
    pontuam — quem está nelas é ignorado. Quem está mutado (silenciado por
    si mesmo ou pelo servidor) também não pontua — só ganha quem está de
    fato participando da call com o microfone aberto."""
    for canal_voz in guild.voice_channels:
        if canal_voz.id in _XP_CALLS_PRIVADAS:
            continue
        for membro in canal_voz.members:
            if membro.bot:
                continue

            estado_voz = membro.voice
            if estado_voz is not None and (estado_voz.self_mute or estado_voz.mute):
                continue

            ganho_call = _XP_POR_TICK_CALL * _XP_CALLS_MULTIPLICADOR.get(canal_voz.id, 1.0)
            # 🎁 Booster de XP do Baú — se estiver ativo, dobra o ganho por um tempo
            if time.time() < _xp_booster_ate.get(membro.id, 0):
                ganho_call *= _BAU_BOOSTER_MULTIPLICADOR

            # 🔥 Booster de Call — sobe 1 nível (x2, x3, x4...) a cada 20 min
            # ininterruptos na mesma call. Se acabou de subir de nível, avisa
            # no canal de XP (mensagem que some sozinha em 1 minuto).
            nivel_boost = _nivel_call_booster(membro.id)
            if nivel_boost > 1:
                ganho_call *= nivel_boost
            if nivel_boost > _call_booster_nivel_anunciado.get(membro.id, 1):
                _call_booster_nivel_anunciado[membro.id] = nivel_boost
                asyncio.create_task(_anunciar_call_booster(guild, membro, nivel_boost))
                asyncio.create_task(_salvar_call_booster_stats())

            ganho_call = max(1, round(ganho_call))

            dados = xp_stats[membro.id]
            nivel_antigo = dados["nivel"]
            dados["xp"] += ganho_call

            nivel_novo, _, _ = _calcular_nivel(dados["xp"])
            dados["nivel"] = nivel_novo

            if nivel_novo > nivel_antigo:
                await _anunciar_level_up(guild, membro, nivel_novo)


@tasks.loop(minutes=1)
async def loop_ranking_xp():
    for guild in bot.guilds:
        try:
            await _processar_xp_call(guild)
        except Exception as e:
            print(f"[ranking-xp] ERRO ao processar xp de call em '{guild.name}': {e!r}")
    await _atualizar_ranking_xp()


_VERXP_SOME_SEGUNDOS = 10   # a resposta do .verxp some sozinha depois desse tempo


@bot.command(name="verxp")
async def cmd_verxp(ctx):
    """Mostra quanto de xp por minuto você está ganhando AGORA numa call de
    voz (base + bônus da call + Booster de Baú + Booster de Call), além de
    quais boosters estão ativos (com o tempo que falta pra cada um) e há
    quanto tempo você tá nessa call sem sair/mutar/trocar de canal. Usa a
    mesma conta de verdade de _processar_xp_call. A resposta some sozinha
    em alguns segundos. Uso: .verxp"""
    autor = ctx.author

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        aviso = await ctx.send("⚠️ Esse comando só funciona dentro do servidor.")
        await _apagar_mensagem_depois(aviso, _VERXP_SOME_SEGUNDOS)
        return

    membro = guild.get_member(autor.id)
    if membro is None:
        try:
            membro = await guild.fetch_member(autor.id)
        except discord.NotFound:
            membro = None

    estado_voz = membro.voice if membro else None
    canal_voz = estado_voz.channel if estado_voz else None

    if canal_voz is None:
        resposta = (
            "🌑 **Aeon:** ...você não está em nenhuma call agora. 🖤🌑 Sem call, sem xp de call — "
            f"entre numa call pra começar a ganhar (base: `{_XP_POR_TICK_CALL}` xp/min)."
        )
    elif canal_voz.id in _XP_CALLS_PRIVADAS:
        resposta = "🌑 **Aeon:** ...essa call é privada. 🖤🌑 Não rende xp nenhum, por aqui as sombras não contam."
    elif estado_voz.self_mute or estado_voz.mute:
        resposta = (
            "🌑 **Aeon:** ...você está mutado. 🖤🌑 Sem microfone aberto, sem xp de call — "
            "desmute pra voltar a ganhar."
        )
    else:
        agora = time.time()

        # Tempo contínuo nessa call — mesma streak usada pelo Booster de Call
        # (zera se a pessoa sair, mutar ou trocar de canal, então reflete
        # certinho "há quanto tempo você tá aqui, participando de verdade").
        inicio_streak = _call_booster_inicio.get(autor.id)
        tempo_na_call = (agora - inicio_streak) if inicio_streak else 0.0

        ganho_call = _XP_POR_TICK_CALL
        detalhes = [f"Base: `{_XP_POR_TICK_CALL}` xp/min"]

        mult_canal = _XP_CALLS_MULTIPLICADOR.get(canal_voz.id, 1.0)
        ganho_call *= mult_canal
        if mult_canal != 1.0:
            detalhes.append(f"Bônus dessa call: `x{mult_canal:g}`")

        bau_restante = _xp_booster_ate.get(autor.id, 0) - agora
        if bau_restante > 0:
            ganho_call *= _BAU_BOOSTER_MULTIPLICADOR
            detalhes.append(
                f"🎁 Booster de Baú ativo: `x{_BAU_BOOSTER_MULTIPLICADOR}` "
                f"(dura mais `{_formatar_tempo_restante(bau_restante)}`)"
            )

        nivel_boost = _nivel_call_booster(autor.id)
        if nivel_boost > 1:
            ganho_call *= nivel_boost
            intervalo_segundos = _CALL_BOOSTER_INTERVALO_MINUTOS * 60
            falta_prox_nivel = intervalo_segundos - (tempo_na_call % intervalo_segundos)
            detalhes.append(
                f"🔥 Booster de Call: `x{nivel_boost}` (nível {nivel_boost} — sobe pra "
                f"`x{nivel_boost + 1}` em `{_formatar_tempo_restante(falta_prox_nivel)}`)"
            )

        if bau_restante <= 0 and nivel_boost <= 1:
            detalhes.append("Nenhum booster ativo agora.")

        ganho_final = max(1, round(ganho_call))

        resposta = (
            f"🌟 **Celestia:** Agora você tá ganhando **`{ganho_final}` xp por minuto** nessa call!! 🌸✨\n"
            f"› Tempo nessa call: `{_formatar_tempo_restante(tempo_na_call)}`\n"
            + "\n".join(f"› {linha}" for linha in detalhes)
        )

    msg = await ctx.send(resposta)
    await _apagar_mensagem_depois(msg, _VERXP_SOME_SEGUNDOS)


@bot.command(name="nivel")
async def cmd_nivel(ctx, membro: discord.Member = None):
    """Mostra o nível e XP de um membro (ou de quem usou o comando). Uso: .nivel [@membro]"""
    if ctx.guild is None:
        return

    membro = membro or ctx.author
    dados_calc = xp_stats.get(membro.id, {"xp": 0, "nivel": 0, "elegivel": False, "cor": _COR_PADRAO})
    nivel, xp_no_nivel, xp_necessario = _calcular_nivel(dados_calc["xp"])
    barra = _barra_progresso(xp_no_nivel, xp_necessario, cor_emoji=_emoji_da_cor(dados_calc.get("cor", _COR_PADRAO)))

    # Entra no ranking quem já mandou mensagem em algum dos canais elegíveis
    # (_XP_CANAIS_RANKING, que inclui o chat geral) — nem que seja só uma.
    status_ranking = (
        "✅ Aparece no ranking fixo"
        if dados_calc.get("elegivel")
        else f"❌ Ainda não aparece — mande uma mensagem em <#{_XP_CANAL_1}>, "
             f"<#{_XP_CANAL_BONUS}> ou <#{_XP_CANAL_3}>"
    )

    embed = discord.Embed(
        title=f"⭐ Nível de {membro.display_name}",
        description=(
            f"**Nível:** `{nivel}`\n"
            f"**Progresso:** {barra} `{xp_no_nivel}/{xp_necessario}`\n"
            f"**XP total:** `{dados_calc['xp']}`\n"
            f"**Status no ranking:** {status_ranking}"
        ),
        color=0xe8d5f5
    )
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Sistema de Nível")
    await ctx.send(embed=embed)


@bot.command(name="darlevel")
async def cmd_dar_level(ctx, membro: discord.Member = None, nivel: int = None):
    """Define manualmente o nível de alguém no ranking de XP (ajusta o XP
    dela pro início desse nível). Só o Reality pode usar.
    Uso: .darlevel @membro <nível>"""
    if ctx.author.id != CRIADOR_ID:
        return

    if membro is None or nivel is None:
        await ctx.send("⚠️ Uso correto: `.darlevel @membro <nível>`\nExemplo: `.darlevel @Fulano 10`")
        return

    if nivel < 0:
        await ctx.send("⚠️ O nível não pode ser negativo.")
        return

    dados = xp_stats[membro.id]
    nivel_antigo = dados["nivel"]

    dados["xp"] = _xp_total_para_nivel(nivel)
    dados["nivel"] = nivel
    dados["elegivel"] = True  # já que ganhou um nível "oficial", passa a aparecer no ranking fixo

    await _salvar_xp_stats()
    await _atualizar_ranking_xp()

    if nivel > nivel_antigo and ctx.guild is not None:
        await _anunciar_level_up(ctx.guild, membro, nivel)

    await ctx.send(
        f"✅ **{membro.display_name}** agora está no **nível `{nivel}`** "
        f"(`{dados['xp']}` XP) — ranking já atualizado."
    )


@bot.command(name="removerxp")
async def cmd_removerxp(ctx, modo: str = None, user_id: int = None, valor: int = None):
    """Remove uma quantidade de XP BRUTO (pontos, não 'níveis' da curva) de um
    membro, identificado pelo ID — funciona mesmo se a pessoa não estiver
    mencionável/no cache. É uma subtração direta e literal: se a pessoa tem
    10.000 e você tira 2.000, ela fica com 8.000 — sem nenhum arredondamento
    pro início de nível. O nível exibido é só recalculado depois, a partir do
    XP que sobrou (nunca fica negativo — mínimo é 0). Só o Reality pode usar.
    Uso: .removerxp id <ID> <valor>
    Exemplo: .removerxp id 769951556388257812 2000   → remove 2000 pontos de XP dessa pessoa

    ⚠️ NOTA: não pode se chamar ".baumimic" — esse nome já é usado pelo baú
    disfarçado de Mimic (.baumimic) que já existe no bot, então ficaria
    duplicado e o bot recusa iniciar (CommandRegistrationError)."""
    if ctx.author.id != CRIADOR_ID:
        return

    if modo != "id" or user_id is None or valor is None:
        await ctx.send(
            "⚠️ Uso correto: `.removerxp id <ID> <valor>`\n"
            "Exemplo: `.removerxp id 769951556388257812 2000` — remove 2000 pontos de XP dessa pessoa."
        )
        return

    if valor <= 0:
        await ctx.send("⚠️ O valor de pontos (XP) a remover deve ser maior que zero.")
        return

    dados = xp_stats[user_id]
    xp_antigo = dados["xp"]
    nivel_antigo = dados["nivel"]

    xp_novo = max(0, xp_antigo - valor)  # subtração bruta e literal, só travando em 0
    nivel_novo, _, _ = _calcular_nivel(xp_novo)

    dados["xp"] = xp_novo
    dados["nivel"] = nivel_novo

    await _salvar_xp_stats()
    await _atualizar_ranking_xp()

    # Tenta identificar a pessoa pra exibir nome/menção; se não conseguir
    # (saiu do servidor, ID errado, etc.), mostra só o ID mesmo.
    membro = None
    if ctx.guild is not None:
        membro = ctx.guild.get_member(user_id)
        if membro is None:
            try:
                membro = await ctx.guild.fetch_member(user_id)
            except discord.NotFound:
                membro = None

    nome_exibicao = membro.mention if membro else f"`{user_id}`"

    aviso_nivel = (
        f" (nível caiu de `{nivel_antigo}` para `{nivel_novo}`)"
        if nivel_novo != nivel_antigo else ""
    )

    await ctx.send(
        f"📉 {nome_exibicao} perdeu **{valor}** pontos de XP — "
        f"de `{xp_antigo}` para `{xp_novo}`{aviso_nivel} — ranking já atualizado."
    )


@bot.command(name="xpdebug")
async def cmd_xp_debug(ctx):
    """Mostra dados brutos do ranking de XP pra diagnosticar problemas. Só o dono do bot pode usar."""
    if ctx.author.id != CRIADOR_ID:
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        await ctx.send("⚠️ Bot não está em nenhum servidor.")
        return

    cargo_xp = guild.get_role(CARGO_XP_ID)
    canal_xp = guild.get_channel(CANAL_XP_ID)

    linhas = [
        f"**Cargo de XP encontrado:** {'✅ sim' if cargo_xp else '❌ NÃO — verifique o ID do cargo'}",
        f"**Membros com o cargo:** {len(cargo_xp.members) if cargo_xp else 0}",
        f"**Canal de XP encontrado:** {'✅ sim' if canal_xp else '❌ NÃO — verifique o ID do canal'}",
        f"**ID da mensagem de ranking salva:** `{_xp_ranking_message_id}` (página atual: `{_xp_ranking_pagina_atual}`)",
        f"**Entradas em xp_stats (memória):** {len(xp_stats)}",
        f"**Arquivo de dados existe?** {'✅ sim' if os.path.exists(_XP_DATA_FILE) else '❌ não'}",
        "",
        "**Conteúdo bruto de xp_stats:**",
    ]
    if xp_stats:
        for uid, s in xp_stats.items():
            membro = guild.get_member(uid)
            nome = membro.display_name if membro else f"<@{uid}>"
            linhas.append(f"`{uid}` ({nome}) — {s}")
    else:
        linhas.append("*vazio — nenhuma mensagem foi registrada ainda em memória*")

    texto = "\n".join(linhas)
    if len(texto) > 1900:
        texto = texto[:1900] + "\n... (cortado)"
    await ctx.send(f"🔍 **Diagnóstico do Ranking de XP**\n{texto}")


class ReiniciarRankingView(discord.ui.View):
    """View de confirmação do reset total do ranking de interação (XP).
    Só o Reality (CRIADOR_ID) pode confirmar ou cancelar — qualquer outra
    pessoa que clicar recebe um aviso de acesso negado."""

    def __init__(self):
        super().__init__(timeout=60)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != CRIADOR_ID:
            await interaction.response.send_message(
                "🌑 **Aeon:** *olha fixamente* ...acesso negado. 🖤🌑\n"
                "🌟 **Celestia:** Só o Reality pode confirmar isso!! 🌸🤍✨",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="✅ Confirmar reset",
        style=discord.ButtonStyle.danger,
        custom_id="reiniciar_ranking_confirmar"
    )
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        global _xp_ranking_pagina_atual

        xp_stats.clear()
        _xp_ultimo_ganho.clear()
        _xp_ranking_pagina_atual = 0

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content="♻️ **Ranking de interação reiniciado — todo mundo voltou a 0.**",
            embed=None,
            view=self
        )
        self.stop()

        guild = interaction.guild or (bot.guilds[0] if bot.guilds else None)
        if guild is not None:
            await _atualizar_ranking_xp()

    @discord.ui.button(
        label="❌ Cancelar",
        style=discord.ButtonStyle.secondary,
        custom_id="reiniciar_ranking_cancelar"
    )
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="❌ Reset cancelado.", embed=None, view=self)
        self.stop()


@bot.command(name="reiniciarranking")
async def cmd_reiniciar_ranking(ctx):
    """Reseta TODO o ranking de interação (xp, nível, criaturas, vitórias e
    derrotas) de volta a 0. Só o Reality pode usar. Uso: .reiniciarranking"""
    if ctx.author.id != CRIADOR_ID:
        return

    embed = discord.Embed(
        title="♻️ Reiniciar Ranking de Interação",
        description=(
            "Isso vai **zerar TUDO** — xp, nível, criaturas desbloqueadas, "
            "vitórias e derrotas de **todo mundo** no ranking.\n\n"
            "Tem certeza?"
        ),
        color=0xff4444
    )
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Sistema de Nível")
    await ctx.send(embed=embed, view=ReiniciarRankingView())


class ReiniciarGeralRPGView(discord.ui.View):
    """View de confirmação do reset GERAL do RPG — a versão "nuclear" do
    .reiniciarranking: zera xp, nível, criaturas (inclusive Bestas),
    vitórias/derrotas e favorita de TODO MUNDO, e por cima disso também
    zera os boosters (Booster de Call e Booster de xp em dobro) e qualquer
    ovo incubando. Só o Reality (CRIADOR_ID) pode confirmar ou cancelar —
    qualquer outra pessoa que clicar recebe um aviso de acesso negado."""

    def __init__(self):
        super().__init__(timeout=60)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != CRIADOR_ID:
            await interaction.response.send_message(
                "🌑 **Aeon:** *olha fixamente* ...acesso negado. 🖤🌑\n"
                "🌟 **Celestia:** Só o Reality pode confirmar isso!! 🌸🤍✨",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="✅ Confirmar reset geral",
        style=discord.ButtonStyle.danger,
        custom_id="reiniciar_geral_rpg_confirmar"
    )
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        global _xp_ranking_pagina_atual

        total_pessoas = len(xp_stats)

        # 🧨 Zera TUDO do RPG, de TODO MUNDO — xp/nível/criaturas/vitórias e
        # derrotas (xp_stats), cooldown de mensagem, boosters (call e xp em
        # dobro), cooldown de desafio de batalha e ovos incubando.
        xp_stats.clear()
        _xp_ultimo_ganho.clear()
        _xp_ranking_pagina_atual = 0
        _call_booster_inicio.clear()
        _call_booster_nivel_anunciado.clear()
        _xp_booster_ate.clear()
        _batalha_ultimo_desafio.clear()
        _ovos_pendentes.clear()
        _ovos_dragao_pendentes.clear()

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=(
                "☠️♻️ **RESET GERAL DO RPG CONCLUÍDO.** Xp, nível, criaturas, "
                "vitórias/derrotas, Booster de Call, Booster de xp em dobro e "
                f"ovos incubando de **`{total_pessoas}`** pessoa(s) voltaram a "
                "**0** — do zero, pra todo mundo, sem exceção."
            ),
            embed=None,
            view=self
        )
        self.stop()

        # 💾 Persiste o reset em disco na hora — sem isso, um restart do bot
        # antes do próximo ganho de xp de alguém traria os dados antigos de
        # volta, já que cada arquivo ainda estaria com o conteúdo de antes.
        asyncio.create_task(_salvar_xp_stats())
        asyncio.create_task(_salvar_call_booster_stats())
        asyncio.create_task(_salvar_xp_booster_stats())

        guild = interaction.guild or (bot.guilds[0] if bot.guilds else None)
        if guild is not None:
            await _atualizar_ranking_xp()

    @discord.ui.button(
        label="❌ Cancelar",
        style=discord.ButtonStyle.secondary,
        custom_id="reiniciar_geral_rpg_cancelar"
    )
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="❌ Reset cancelado.", embed=None, view=self)
        self.stop()


@bot.command(name="reiniciogeralrpg", aliases=["resetgeralrpg"])
async def cmd_reiniciogeralrpg(ctx):
    """Reseta ABSOLUTAMENTE TUDO do RPG, de TODO MUNDO, de uma vez: xp, nível,
    criaturas desbloqueadas (inclusive Bestas), Níveis de Capacidade,
    favorita, vitórias e derrotas, Booster de Call, Booster de xp em dobro
    (baú/boss) e ovos incubando (.ovo/.ovodragao). Diferente do
    .reiniciarranking (que só zera xp/nível/criaturas), esse também zera os
    boosters e já salva o reset em disco na hora. Irreversível. Só o Reality
    pode usar. Uso: .reiniciogeralrpg"""
    if ctx.author.id != CRIADOR_ID:
        return

    total_pessoas = len(xp_stats)

    embed = discord.Embed(
        title="☠️♻️ Reset GERAL do RPG",
        description=(
            f"Isso vai **zerar ABSOLUTAMENTE TUDO** de **`{total_pessoas}`** pessoa(s) "
            "que já têm dados no ranking:\n\n"
            "• XP e nível\n"
            "• Criaturas desbloqueadas (inclusive 🐺 Bestas) e Níveis de Capacidade\n"
            "• Criatura favorita\n"
            "• Vitórias e derrotas\n"
            "• 🔥 Booster de Call (streak) de todo mundo\n"
            "• ⚡ Booster de xp em dobro (baú/boss) de todo mundo\n"
            "• 🥚 Ovos incubando (`.ovo` e `.ovodragao`)\n\n"
            "⚠️ **Isso é irreversível e vale pra TODO MUNDO, sem exceção.**\n\n"
            "Tem certeza?"
        ),
        color=0xff0000
    )
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Sistema de Nível")
    await ctx.send(embed=embed, view=ReiniciarGeralRPGView())


@bot.command(name="xpbackfill")
async def cmd_xp_backfill(ctx, limite: int = None):
    """Varre o histórico dos 3 canais de ranking e marca como 'elegivel' todo
    mundo que JÁ mandou mensagem lá antes — inclusive mensagens antigas, de
    antes da liberação do cargo. Sem isso, só quem mandar uma mensagem NOVA
    depois da atualização apareceria no ranking; com isso, quem já participava
    antes aparece de uma vez, sem precisar mandar mensagem de novo.
    Só o dono do bot pode usar. Uso: .xpbackfill [limite de msgs por canal]"""
    if ctx.author.id != CRIADOR_ID:
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        await ctx.send("⚠️ Bot não está em nenhum servidor.")
        return

    aviso = await ctx.send(
        "🔎 Varrendo o histórico dos canais de ranking pra achar quem já "
        "participou antes... isso pode levar um tempinho em canais grandes."
    )

    encontrados = set()
    for canal_id in _XP_CANAIS_RANKING:
        canal = guild.get_channel(canal_id)
        if canal is None:
            continue
        try:
            async for msg in canal.history(limit=limite):
                if msg.author.bot:
                    continue
                encontrados.add(msg.author.id)
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.send(f"⚠️ Não consegui ler o histórico de {canal.mention}: `{e}`")

    novos = 0
    for uid in encontrados:
        membro = guild.get_member(uid)
        if membro is None:
            continue  # já saiu do servidor — não destrava quem não tá mais aqui
        dados = xp_stats[uid]
        if not dados.get("elegivel"):
            novos += 1
        dados["elegivel"] = True

    await _salvar_xp_stats()
    await _atualizar_ranking_xp()

    await aviso.edit(
        content=(
            f"✅ Varredura concluída! `{len(encontrados)}` pessoas encontradas nos canais de ranking, "
            f"`{novos}` delas foram destravadas agora e já aparecem no ranking fixo."
        )
    )


# Carrega o histórico de XP salvo assim que o módulo sobe — antes mesmo de conectar no Discord
_carregar_xp_stats()

# Carrega a streak salva do Booster de Call — a reconciliação final (quem
# realmente ainda está numa call válida) acontece no on_ready.
_carregar_call_booster_stats()

# ══════════════════════════════════════════════════════════════════════
# BATALHA DE CRIATURAS — "Eu te desafio @alguém"
# Quando alguém escreve "eu te desafio @pessoa" no chat, Aeon & Celestia
# armam uma batalha dramática entre duas criaturas sorteadas aleatoriamente
# — uma pro desafiante, outra pro desafiado. No fim, quem vence PODE roubar
# uma fatia do XP total de quem perdeu (no ranking de nível): é lançado um
# "dado" que decide entre 1% e 20%... ou, com uma certa chance, nada.
# ══════════════════════════════════════════════════════════════════════

# ── Raridades das criaturas ──────────────────────────────────────────────
# Define o emoji/cor/label de cada raridade e o PESO usado no sorteio de
# batalha (quanto maior o peso, mais fácil essa raridade aparecer). Isso faz
# criaturas Lendárias serem naturalmente mais raras de invocar (e, por
# tabela, mais raras de desbloquear).
_RARIDADES = {
    "comum":    {"label": "Comum",    "emoji": "⚪", "cor": 0xb0b0b0, "peso": 50},
    "raro":     {"label": "Raro",     "emoji": "🔵", "cor": 0x3498db, "peso": 25},
    "epico":    {"label": "Épico",    "emoji": "🟣", "cor": 0x9b59b6, "peso": 15},
    "lendario": {"label": "Lendário", "emoji": "🟡", "cor": 0xf1c40f, "peso": 10},
    # 🌀 Elementais: mais fortes que as Lendárias, mas ainda um degrau abaixo
    # das Bestas — o resto das raridades acima delas (Bestas, Fósseis,
    # Secretas, Míticas) elas não chegam a bater de frente com tanta força.
    # Não entram no sorteio normal de recompensa nem no 🪙 Baú/.ovo — a ÚNICA
    # forma de conseguir um é levando uma criatura 🟣 Épica até o Nível de
    # Capacidade 6 (ver _ELEMENTAL_NIVEL_DESBLOQUEIO e
    # _checar_desbloqueio_elemental, mais abaixo): ao bater esse nível, a
    # pessoa recebe automaticamente, de graça, 1 Elemental ALEATÓRIO dentre
    # os que ainda não tiver. Além disso, todo Elemental USADO numa batalha
    # (convocado, ganhando ou perdendo — não importa) já concede na hora,
    # pra quem o usou, um Booster de xp em dobro por
    # _ELEMENTAL_BOOSTER_MINUTOS minutos (ver _executar_batalha).
    "elemental": {"label": "Elemental", "emoji": "🌀", "cor": 0xe67e22, "peso": 7},
    # 🐺 Bestas: mais fortes que as Lendárias, mas ainda um degrau abaixo das
    # Secretas. Não entram no sorteio normal de recompensa nem no 🪙 Baú — a
    # ÚNICA forma de conseguir uma é levando uma criatura Comum, Rara,
    # Épica ou Lendária até o Nível de Capacidade máximo (ver _BESTAS_POR_TIER e
    # _checar_desbloqueio_besta, mais abaixo). O peso aqui só importa pra
    # decidir a chance dela ser invocada em batalha depois de já ter sido
    # conquistada.
    "bestas":   {"label": "Besta",    "emoji": "🐺", "cor": 0x922b21, "peso": 6},
    # 🦴 Fósseis: um degrau abaixo das Secretas, mas mais fortes que as
    # Lendárias — ver a lógica de desbloqueio própria delas mais abaixo
    # (_FOSSIL_CHANCE_DESBLOQUEIO), gatilhada só quando os dois lados de uma
    # batalha estão numa call de voz.
    "fosseis":  {"label": "Fóssil",   "emoji": "🦴", "cor": 0xc2a878, "peso": 3},
    "secreto":  {"label": "Secreto",  "emoji": "🌌", "cor": 0x6c2eb5, "peso": 2},
    "mitico":   {"label": "Mítico",   "emoji": "🐉", "cor": 0xe0115f, "peso": 5},
}
_ORDEM_RARIDADES = ("mitico", "secreto", "fosseis", "bestas", "elemental", "lendario", "epico", "raro", "comum")  # do mais raro pro mais comum, pra exibição

# Cada criatura tem um "id" fixo (usado para salvar quem já desbloqueou),
# um "nome" de exibição, o "gif" e a "raridade" (chave de _RARIDADES).
_BATALHA_CRIATURAS = [
    # ── Comuns ──────────────────────────────────────────────────────────
    {"id": "caveira_perpetua",        "nome": "Caveira Perpétua",             "raridade": "comum",    "gif": "https://i.pinimg.com/originals/11/d4/f6/11d4f665781ad7710f79e76ae03532bf.gif"},
    {"id": "samurai_pix",             "nome": "Samurai do Pix",               "raridade": "comum",    "gif": "https://i.pinimg.com/originals/32/e6/fe/32e6fe1d93519ce4ed0c9d1ef666ea86.gif"},
    {"id": "abandonado",              "nome": "O Abandonado",                 "raridade": "comum",    "gif": "https://i.pinimg.com/originals/19/7b/88/197b887956c1741536cbda7a8bf0c59c.gif"},
    {"id": "desconectado",            "nome": "O Desconectado",               "raridade": "comum",    "gif": "https://64.media.tumblr.com/e59c49cc960b3af010126aa2185f9af4/tumblr_o2ukydWovF1rznluto3_250.gif"},
    {"id": "rino_acabado",            "nome": "Rino, o Acabado",              "raridade": "comum",    "gif": "https://33.media.tumblr.com/fc4838c3660618bf7dd87103de60871b/tumblr_inline_nzsz2t9ltH1s38bty_500.gif"},
    {"id": "plebeu",                  "nome": "O Plebeu",                     "raridade": "comum",    "gif": "https://i.pinimg.com/originals/1c/9f/2b/1c9f2b392f039b76b7f3a68039730d21.gif"},
    {"id": "bandido",                 "nome": "Bandido",                      "raridade": "comum",    "gif": "https://cdnb.artstation.com/p/assets/images/images/050/343/519/original/rafael-francoi-neutral-inxikrahsoldier-preview.gif?1654628639"},
    {"id": "ranfroi_ultimo_plebeu",    "nome": "Ranfroi, o Último Plebeu",     "raridade": "comum",    "gif": "https://cdna.artstation.com/p/assets/images/images/050/342/714/original/rafael-francoi-mk2.gif?1654627365"},
    {"id": "buzzmole_eletrico",        "nome": "Buzzmole Elétrico do Eco",     "raridade": "comum",    "gif": "https://www.natekling.com/uploads/8/2/3/8/8238935/7185980.gif"},
    {"id": "blindado_metaltooth",      "nome": "O Blindado",                   "raridade": "comum",    "gif": "https://cdna.artstation.com/p/assets/images/images/050/342/682/original/rafael-francoi-metaltooth.gif?1654627258"},
    {"id": "cueio_pistola",            "nome": "Cueio Pistola",                "raridade": "comum",    "gif": "https://i.pinimg.com/originals/8c/d8/9c/8cd89c36fdb3215e7b7f82a8e94605d2.gif"},

    # ── Raras ───────────────────────────────────────────────────────────
    {"id": "cavaleiro_elemental",     "nome": "Cavaleiro Elemental",          "raridade": "raro",     "gif": "https://i.pinimg.com/originals/f0/6a/a4/f06aa45318cce9f16f2b3e591a138ae1.gif"},
    {"id": "caveira_prisao",          "nome": "Caveira da Prisão",            "raridade": "raro",     "gif": "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEivaQ2fr4t0qnYKfUiXbCeBU2HGF2vMB6oCjiEbAjADBdNYPoOqzEU8jSDdHDwD5xgI7MGL9qj0eH60EgBEaGjgV4JIHDait9dSFusVjLvykhwIWHPa4tfeDhzOr3uhwQfyNtzw7mz-Q9_E/s1600/Phantasm_attack_8.gif"},
    {"id": "eco_luz",                 "nome": "Eco da Luz",                   "raridade": "raro",     "gif": "https://i.pinimg.com/originals/25/83/b2/2583b2768cb33f0165e3a88ac3debbde.gif"},
    {"id": "cientista_louco",         "nome": "Cientista Louco",              "raridade": "raro",     "gif": "https://i.pinimg.com/originals/f7/45/05/f74505bee8fec82f0eb6e925c61b35f2.gif"},
    {"id": "brutal",                  "nome": "O Brutal",                     "raridade": "raro",     "gif": "https://i.pinimg.com/originals/fd/1f/8a/fd1f8aa84a2d1b1d1486c68613216d9d.gif"},
    {"id": "cavaleiro_sinistro",      "nome": "Cavaleiro do Sinistro",        "raridade": "raro",     "gif": "https://i.pinimg.com/originals/1c/3a/9b/1c3a9bc1c91135ff036d1d168d15e474.gif"},
    {"id": "kreging",                 "nome": "Kreging",                      "raridade": "raro",     "gif": "https://64.media.tumblr.com/3211afe2da2effd51671993d42cecc81/tumblr_oomh73qHh21qciqqno5_250.gif"},
    {"id": "besta_gelida",             "nome": "Besta Gélida",                 "raridade": "raro",     "gif": "https://i.pinimg.com/originals/a6/a7/14/a6a714c4caab8f29b00e36feecc37fc2.gif"},
    {"id": "pai_da_sorte",             "nome": "O Pai da Sorte",               "raridade": "raro",     "gif": "https://i.redd.it/9w2ulp6ym1ky.gif"},
    {"id": "besta_do_eco",             "nome": "A Besta do Eco",               "raridade": "raro",     "gif": "https://i.pinimg.com/originals/a2/14/20/a214205173961824624e41024b6c5fdd.gif"},
    {"id": "ravok_submetido_eco",      "nome": "Ravok, o Submetido do Eco",    "raridade": "raro",     "gif": "https://i.pinimg.com/originals/a7/ed/26/a7ed267e84861ec466c82095bb0bad63.gif"},
    {"id": "yamikiba",                 "nome": "Yamikiba",                     "raridade": "raro",     "gif": "https://cdnb.artstation.com/p/assets/images/images/050/343/457/original/rafael-francoi-neutral-inxikrahbuilder-preview.gif?1654628532"},

    # ── Épicas ──────────────────────────────────────────────────────────
    {"id": "heroina_esmeraldas",      "nome": "Heroína das Esmeraldas",       "raridade": "epico",    "gif": "https://i.pinimg.com/originals/40/4f/d9/404fd93484c2592c78a13cf25891c156.gif"},
    {"id": "robin_dourado",           "nome": "Robin Dourado",                "raridade": "epico",    "gif": "https://i.pinimg.com/originals/fc/26/21/fc26214b7e21990e483df07f8ee616e8.gif"},
    {"id": "buda_eco",                "nome": "Buda do Eco",                  "raridade": "epico",    "gif": "https://i.pinimg.com/originals/de/cc/64/decc640148693d24cbccfce9262d16ae.gif"},
    {"id": "monstro_portao",          "nome": "O Monstro do Portão",          "raridade": "epico",    "gif": "https://i.pinimg.com/originals/1f/4a/d7/1f4ad7fd9917093bc7463394497fd920.gif"},
    {"id": "ultimo_atlanta",          "nome": "Último de Atlanta",            "raridade": "epico",    "gif": "https://i.pinimg.com/originals/84/a6/8b/84a68ba244c9034c52dcb8002f90a87f.gif"},
    {"id": "guerreiro_trovao",        "nome": "Guerreiro do Trovão",          "raridade": "epico",    "gif": "https://i.pinimg.com/originals/6b/2c/21/6b2c2173d12ddf1f2adae8f0064f772d.gif"},
    {"id": "anti_elemento",           "nome": "O Anti-Elemento",              "raridade": "epico",    "gif": "https://i.pinimg.com/originals/d1/ee/0e/d1ee0eed40bd9a2052e4b0ce55e741d9.gif"},
    {"id": "vortex",                  "nome": "O Vórtex",                     "raridade": "epico",    "gif": "https://cdnb.artstation.com/p/assets/images/images/050/342/679/original/rafael-francoi-build-epic-01.gif?1654627256"},
    {"id": "seraphine_guerreira",      "nome": "Seraphine, a Guerreira",       "raridade": "epico",    "gif": "https://i.pinimg.com/originals/15/de/fc/15defcb5f35239554da784918902b32a.gif"},
    {"id": "corrompido",               "nome": "O Corrompido",                 "raridade": "epico",    "gif": "https://cdnb.artstation.com/p/assets/images/images/050/343/359/original/rafael-francoi-f2-boss-preview.gif?1654628376"},
    {"id": "ignara_musa_chamas",       "nome": "Ignara, a Musa das Chamas",    "raridade": "epico",    "gif": "https://i.pinimg.com/originals/01/a0/f0/01a0f071ff7c66dab9de366c4c8da0bf.gif"},
    {"id": "primeiro_graking",         "nome": "O Primeiro Graking",           "raridade": "epico",    "gif": "https://i.pinimg.com/originals/c1/18/60/c11860b4b9e9b179b1b8dbc2ce640839.gif"},
    {"id": "ophryx_dama_besta",        "nome": "Ophryx, a Dama e a Besta",     "raridade": "epico",    "gif": "https://gd-hbimg.huaban.com/bbf9f681a72dc53b226e1efe204770da4f98adf250494-5EKNdd_fw658"},
    {"id": "warden_eco",               "nome": "Warden do Eco",                "raridade": "epico",    "gif": "https://cdna.artstation.com/p/assets/images/images/050/343/624/original/rafael-francoi-ynuyt-unleashed.gif?1654628832"},
    {"id": "kurojin",                  "nome": "Kurojin",                      "raridade": "epico",    "gif": "https://cdnb.artstation.com/p/assets/images/images/050/343/359/original/rafael-francoi-f2-boss-preview.gif?1654628376"},
    {"id": "xalkuro",                  "nome": "Xal'Kuro",                     "raridade": "epico",    "gif": "https://i.redd.it/sifc575zp2dy.gif"},
    {"id": "salafrario",               "nome": "O Salafrário",                 "raridade": "epico",    "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531101852752416848/1785113407534.gif?ex=6a67fd38&is=6a66abb8&hm=631b4328a747f1527a2a2e440694c136d28683eb7ef0dc46e17322d779178db4&"},

    # ── Lendárias ───────────────────────────────────────────────────────
    {"id": "ultimo_guerreiro",        "nome": "O Último Guerreiro",           "raridade": "lendario", "gif": "https://gd-hbimg.huaban.com/da5bb9cc8fab68c2c3cabe68a7cc7a10cd277939be96-bBi4DQ"},
    {"id": "lyria_governante",        "nome": "Lyria, a Governante",          "raridade": "lendario", "gif": "https://i.pinimg.com/originals/9e/88/99/9e88991126a8bdd32a89e43ae683f3b4.gif"},
    {"id": "kaiju_eco",               "nome": "Kaiju do Eco",                 "raridade": "lendario", "gif": "https://i.pinimg.com/originals/02/ef/09/02ef09d38f7435de3a2e8d26508a17ec.gif"},
    {"id": "protetor_portao_inferno", "nome": "Protetor do Portão do Inferno","raridade": "lendario", "gif": "https://i.pinimg.com/originals/6d/bc/58/6dbc588871368635891ea6a5f12d3cf2.gif"},
    {"id": "magmata",                 "nome": "O Magmata",                    "raridade": "lendario", "gif": "https://i.redd.it/0jk54f0ocjwy.gif"},
    {"id": "vreg_entre_mundos",       "nome": "Vreg, Entre Mundos",           "raridade": "lendario", "gif": "https://cdna.artstation.com/p/assets/images/images/050/343/134/original/rafael-francoi-boss-f4-preview.gif?1654628012"},
    {"id": "azrakiel_monarca",        "nome": "Azrakiel, o Monarca",          "raridade": "lendario", "gif": "https://i.pinimg.com/originals/a3/20/90/a32090812f05b6ac55c66e2cbf5c5621.gif"},
    {"id": "arkanis_primeiro_reis",   "nome": "Arkanis, o Primeiro dos Reis", "raridade": "lendario", "gif": "https://i.pinimg.com/originals/d5/66/4e/d5664e6db68e21ae002431b9fd13ed2d.gif"},
    {"id": "auremortis_guardia_almas","nome": "Auremortis, a Guardiã das Almas Perdidas", "raridade": "lendario", "gif": "https://i.redd.it/nij0nx9bnkpy.gif"},
    {"id": "goldryn_chama_destino",   "nome": "Goldryn, a Chama Que Consome o Destino",   "raridade": "lendario", "gif": "https://i.redd.it/go2trcn2yoby.gif"},
    {"id": "thanarion_arauto_fim",    "nome": "Thanarion, o Arauto do Fim",   "raridade": "lendario", "gif": "https://i.pinimg.com/originals/04/96/7c/04967c814e98570fbffe8329fe36d2bc.gif"},
    {"id": "nythrax_senhor_sombras",  "nome": "Nythrax, o Senhor das Sombras","raridade": "lendario", "gif": "https://cdnb.artstation.com/p/assets/images/images/050/342/691/original/rafael-francoi-exotic-spellcaster.gif?1654627313"},
    {"id": "umbrael_observa_alem",    "nome": "Umbrael, o Que Observa Além",  "raridade": "lendario", "gif": "https://gd-hbimg.huaban.com/9064a16a34ed6e88bab3dc8c3815a6258b1d16c54068a-6KOtGT_fw658"},
    {"id": "noxar_puro_trovao",       "nome": "Noxar, o Puro Trovão",         "raridade": "lendario", "gif": "https://i.pinimg.com/originals/c7/6c/87/c76c873ca7d63b7fb29792ad26d36368.gif"},
    {"id": "malgorath_ultima_raca",   "nome": "Malgorath, o Último de Sua Raça", "raridade": "lendario", "gif": "https://i.pinimg.com/originals/df/a8/fc/dfa8fca7813bbb3e42613523c2e2ba43.gif"},
    {"id": "jigokuken",               "nome": "Jigokuken",                    "raridade": "lendario", "gif": "https://i.pinimg.com/originals/6e/a3/b3/6ea3b3d49760fab3d42b0570f1f9e69a.gif"},
    {"id": "raiketsu_lamina_dourada", "nome": "Raiketsu, a Lâmina Dourada",   "raridade": "lendario", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531098422952726758/1785112683012.gif?ex=6a67fa06&is=6a66a886&hm=4b58d4ae7eb0fc825c630d44cd22ac4b017c1a78f8881e7b3e6af06ab7adea7a"},

    # ── Elementais ──────────────────────────────────────────────────────
    # Destravados por CONQUISTA, não por sorteio — mais fortes que as
    # Lendárias, mas ainda um degrau abaixo das Bestas. A única forma de
    # conseguir um é levando uma criatura 🟣 Épica até o Nível de Capacidade
    # 6 (veja _ELEMENTAL_NIVEL_DESBLOQUEIO e _checar_desbloqueio_elemental,
    # mais abaixo) — é sempre um Elemental ALEATÓRIO dentre os que a pessoa
    # ainda não tem. Todo Elemental USADO numa batalha (ganhando ou
    # perdendo, não importa) também concede na hora um Booster de xp em
    # dobro por _ELEMENTAL_BOOSTER_MINUTOS minutos pra quem o convocou.
    {"id": "ignar_senhor_chamas",      "nome": "Ignar, o Senhor das Chamas Eternas", "raridade": "elemental", "gif": "https://images.cara.app/production/posts/87424233-d5f7-43cd-988b-5e1b151d4835/sunpixels-AoOvOaapYAziRLRy67LQ6-firee.gif?width=750&quality=100"},
    {"id": "zephros_soberano_ventos",  "nome": "Zephros, o Soberano dos Ventos",     "raridade": "elemental", "gif": "https://images.cara.app/production/posts/aa3523f4-44cd-4f6f-99eb-3819331ead94/sunpixels-0VDPXm8ZraKByQgekVp0J-air.gif?width=750&quality=100"},
    {"id": "granor_colosso_pedra",     "nome": "Granor, o Colosso de Pedra",         "raridade": "elemental", "gif": "https://images.cara.app/production/posts/8acf2d4e-77c7-4c20-a674-7cd29d623659/sunpixels-Mj80n0EV-_lHz9IbhkoFP-gf.gif?width=750&quality=100"},
    {"id": "pyroth_devorador_vulcoes", "nome": "Pyroth, o Devorador de Vulcões",     "raridade": "elemental", "gif": "https://images.cara.app/production/posts/a38409ff-ef92-4890-a848-93c23b4233ad/sunpixels-sIGdQ9FU-zs5U1MeFpcE5-eeasd.gif?width=750&quality=100"},
    {"id": "sylvara_guardia_floresta", "nome": "Sylvara, a Guardiã da Floresta Ancestral", "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531800568241197147/1785280104128.gif?ex=6a6a87f2&is=6a693672&hm=ab516e494a292d2013a33f5afa07c486bb99ecc7fbddd999310c7b33b401b47a"},
    {"id": "nereia_rainha_mares",      "nome": "Nereia, a Rainha das Marés",         "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531800691901730886/1785280137642.gif?ex=6a6a8810&is=6a693690&hm=cf17a7d242a0f5763f6ff2ea4d89ba25f9d6abcd7e210f0fb27915feb37f9216"},
    {"id": "lumiel_arauto_aurora",     "nome": "Lumiel, o Arauto da Aurora",         "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531800926137090208/1785280195193.gif?ex=6a6a8848&is=6a6936c8&hm=a37ea0db0607dfdd33dd72b7344576024d2ba814d8e1c5646ebb22a34a66ae88"},
    {"id": "nocthar_monarca_sombras",  "nome": "Nocthar, o Monarca das Sombras",     "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531801365662404678/1785280298784.gif?ex=6a6a88b1&is=6a693731&hm=9f7e3de1c1ee64e62d615afd557e3480ea59da248a8477c2648f37af011c55de"},
    {"id": "zephor_portador_raios",    "nome": "Zephor, o Portador dos Raios",       "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531801627856470118/1785280362728.gif?ex=6a6a88ef&is=6a69376f&hm=241d97ed04603d1cd85cf5bf624b83fef20510ab79e2a07da78e46ae49c7788a"},
    {"id": "venyx_portador_praga",     "nome": "Venyx, o Portador da Praga",         "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531801741555929218/1785280389431.gif?ex=6a6a890a&is=6a69378a&hm=95d8b56837124085b7c9707af19ef88e86b4ecd6232149784e6674ec86d304b3"},
    {"id": "mordrak_coracao_carmesim", "nome": "Mordrak, o Coração Carmesim",        "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531801803476439060/1785280404640.gif?ex=6a6a8919&is=6a693799&hm=2debab6eaa3de2c58a7145e33628198930e778414a2409bac1eac48a5ca754cb"},
    {"id": "gravion_mestre_gravidade", "nome": "Gravion, o Mestre da Gravidade",     "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531802763376201920/1785280632048.gif?ex=6a6a89fe&is=6a69387e&hm=7e98df335f73559ff1fe2c4775d4ab74ab7360d5912e40f764b3b9a977df0e1c"},

    # ── Bestas ──────────────────────────────────────────────────────────
    # Mais fortes que as Lendárias, mas ainda um degrau abaixo das Secretas.
    # Nunca saem de sorteio de vitória nem do 🪙 Baú — a ÚNICA forma de
    # conseguir uma é levando uma criatura Comum, Rara, Épica ou Lendária até
    # o Nível de Capacidade máximo (veja _BESTAS_POR_TIER logo abaixo, que
    # define qual "tier" desbloqueia qual Besta):
    #   ⚪ Comum    no Nível máximo → sorteia 1 entre Kragor / Espinho Maldito
    #   🔵 Raro     no Nível máximo → sorteia 1 entre Drogan / A Matriarca do Abismo
    #   🟣 Épico    no Nível máximo → concede Venomor
    #   🟡 Lendário no Nível máximo → concede O Último Shogun das Trevas
    {"id": "kragor_senhor_presas",    "nome": "Kragor, Senhor das Presas",     "raridade": "bestas",   "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530616424576323615/1784997759114.gif?ex=6a663921&is=6a64e7a1&hm=ce8f0e4db85718ec33963682c0cf21136ce59d18b1dfa4861bf64716f9b802c4"},
    {"id": "espinho_maldito",         "nome": "Espinho Maldito",               "raridade": "bestas",   "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530620836648849519/1784998710439.gif?ex=6a663d3d&is=6a64ebbd&hm=fccdd2a51553437b3244b38e95abec8d7eb2c753a575be68c3c5468a01256fce"},
    {"id": "drogan_carniceiro",       "nome": "Drogan, o Carniceiro",          "raridade": "bestas",   "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530620836187345046/1784998831160.gif?ex=6a663d3c&is=6a64ebbc&hm=a55e419e47578dc873b7ab25687d4a14d994aa29d954012dd53afba93331834c"},
    {"id": "matriarca_abismo",        "nome": "A Matriarca do Abismo",         "raridade": "bestas",   "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530621862898438184/1784999080550.gif?ex=6a663e31&is=6a64ecb1&hm=fb9e9ae76d5a675e227bbc929fa5028b415d196abe9c07dc4513c5483f091a45"},
    {"id": "venomor",                 "nome": "Venomor",                       "raridade": "bestas",   "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530626370051506216/1785000151649.gif?ex=6a664264&is=6a64f0e4&hm=19fd34a9f84377e2b4c3e77b6c57d94ca043d394eb261b834ac2cff5b8f374b0"},
    {"id": "ultimo_shogun_trevas",    "nome": "O Último Shogun das Trevas",    "raridade": "bestas",   "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531101852417003722/1785113506856.gif?ex=6a67fd38&is=6a66abb8&hm=28a407b40c11ddc85ead690da23b6275e8bbcf6502b8f846ae62da026e5910be&"},

    # ── Fósseis ─────────────────────────────────────────────────────────
    # Um degrau abaixo das Secretas, mas mais fortes que as Lendárias. Não
    # entram no sorteio normal de recompensa nem no 🪙 Baú/.ovo — a ÚNICA
    # forma de conseguir uma é vencendo uma batalha de "eu te desafio" com
    # os DOIS lados (desafiante e desafiado) numa call de voz no momento:
    # aí sim rola uma chance de _FOSSIL_CHANCE_DESBLOQUEIO de o vencedor
    # desenterrar um Fóssil novo (ver _executar_batalha, mais abaixo).
    {"id": "kharox",                  "nome": "Kharox",                        "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/39675b30-c22a-4fee-9169-796d8df605c3/sovanjedi-QxpAB2XnRkgnAb8AG_sZT-jho_4x.gif?width=1920"},
    {"id": "tyrgath",                 "nome": "Tyrgath",                       "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/39675b30-c22a-4fee-9169-796d8df605c3/sovanjedi-_Zu5_q0u8pF02EL_xZ-di-goremagala_4x.gif?width=1920"},
    {"id": "fossorak",                "nome": "Fossorak",                      "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/39675b30-c22a-4fee-9169-796d8df605c3/sovanjedi-Erok4gaSmAq53n-OFHmo7-barioth_4x.gif?width=1920"},
    {"id": "rexolith",                "nome": "Rexolith",                      "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/e5cf266b-89a9-4f7d-b581-9adc6e1bc374/sovanjedi-yORqbtobG_AsZfkJjT7qL-zin_4x.gif?width=1920"},
    {"id": "titanclaw",               "nome": "Titanclaw",                     "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/365c202e-1fc3-4676-93fa-ff982bc10652/sovanjedi-u6eIN5WKwTqaZt2wt8WJl-magna_4x.gif?width=1920"},
    {"id": "skullmaw",                "nome": "Skullmaw",                      "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/365c202e-1fc3-4676-93fa-ff982bc10652/sovanjedi-GQrOL3cptWN7yFxDRmhMW-khezu_4x.gif?width=1920"},
    {"id": "paleotyr",                "nome": "Paleotyr",                      "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/abae2a03-07c5-42ac-b5c0-59dd1cd60907/sovanjedi-8vvofnFCout2lpQqfWKuv-NorthernMountain_idle.gif?width=750&quality=100"},
    {"id": "ossaraith",                "nome": "Ossaraith",                     "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/365c202e-1fc3-4676-93fa-ff982bc10652/sovanjedi-EjBUt_WUHgQhErjz52ysz-goss_4x.gif?width=750&quality=100"},
    {"id": "necrolith",               "nome": "Necrolith",                     "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/5e343483-c057-4aa8-a379-c27c02fd22d5/sovanjedi-ICTTsVYhJNyqg7CjKSeeQ-danaumus_TWEAKS_x4.gif?width=1920"},

    # ── Secretas ────────────────────────────────────────────────────────
    # Um degrau abaixo das Míticas, mas acima das Lendárias — e MUITO mais
    # raras de conseguir que qualquer uma delas. Só saem do 🪙 Baú (.bau),
    # com uma chance minúscula (_BAU_CHANCE_SECRETO) — nunca aparecem como
    # recompensa normal de vitória em batalha nem no .ovo.
    {"id": "nyxalith_dragao_eclipse_contaminado", "nome": "Nyxalith, o Dragão do Eclipse Contaminado", "raridade": "secreto", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530548540453949492/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte8-ezgif.com-video-to-gif-converter.gif?ex=6a65f9e8&is=6a64a868&hm=520ea2ec3119628ee31e2fcdc0ffec3cd2f58abeb1299853fe6bfbfa0225dc24"},
    {"id": "magnus_frostbane",                    "nome": "Magnus Frostbane",                             "raridade": "secreto", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530551857657811144/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte12-ezgif.com-video-to-gif-converter.gif?ex=6a65fcff&is=6a64ab7f&hm=b17f232f526747a90194d31ac0043cb30c66511a1df23b2ea54c79d98c633e19"},
    {"id": "drakonis_prime",                      "nome": "Drakonis Prime",                               "raridade": "secreto", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530550661341646929/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte10-ezgif.com-video-to-gif-converter.gif?ex=6a65fbe1&is=6a64aa61&hm=56b3b0869302c0a49246ec7ba92b17ab28db532828585b57d68ceee9eec47c4d"},
    {"id": "pirikita",                            "nome": "Pirikita",                                     "raridade": "secreto", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530543477765570590/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte6-ezgif.com-video-to-gif-converter.gif?ex=6a65f531&is=6a64a3b1&hm=95e9447603d93ff32e57592230af53ec07567d79ed1eaa5e4b886c2acc67653b"},
    {"id": "solarius_guardiao_ordem",              "nome": "Solarius, Guardião da Ordem",                  "raridade": "secreto", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530556148976193636/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte14-ezgif.com-video-to-gif-converter.gif?ex=6a6600fe&is=6a64af7e&hm=5a60dce14b09c13ee02ae437cf01492ed8b8444978fa8d044efc78fff056c262"},
    {"id": "vorakthul",                            "nome": "Vorak'thul",                                   "raridade": "secreto", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530543478193520791/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte5-ezgif.com-video-to-gif-converter.gif?ex=6a65f531&is=6a64a3b1&hm=72a2e23365092d97d2fb9e4c23765cc0ee32765fe092f5ebb1d8bb348283d98c"},

    # ── Míticas ─────────────────────────────────────────────────────────
    # Dragões. Não entram no sorteio normal de recompensa (esse é o pool
    # de _nao_possuidas em _executar_batalha, que já os exclui) — só saem
    # pelo desbloqueio especial a cada _MITICO_VITORIAS_INTERVALO vitórias,
    # com _MITICO_CHANCE_DESBLOQUEIO de chance. Em batalha, seguem a
    # hierarquia de força das raridades (_chance_vitoria_por_raridade): são
    # a raridade mais forte de todas, mas o adversário sempre mantém uma
    # chance mínima de dar a zebra; Mítico contra Mítico é sorteio puro (50/50).
    {"id": "dragao_mar",              "nome": "Dragão do Mar",                 "raridade": "mitico",   "gif": "https://i.pinimg.com/originals/03/80/19/0380195ac5aa62eca14b4361eb30189e.gif"},
    {"id": "dragao_oriente",          "nome": "Dragão do Oriente",             "raridade": "mitico",   "gif": "https://i.pinimg.com/originals/62/9e/1f/629e1fd48d0176d8fb7bf77714387ee4.gif"},
    {"id": "dragao_caos",             "nome": "Dragão do Caos",                "raridade": "mitico",   "gif": "https://media.tenor.com/KvbrKEFBVncAAAAM/monseter-hunter.gif"},
    {"id": "dragao_prisma",           "nome": "Dragão de Prisma",              "raridade": "mitico",   "gif": "https://cdn.weasyl.com/static/media/06/de/94/06de947946dab12a282995a2535af120b36450e6bc7f8b652ac5970277647027.gif"},
    {"id": "dragao_serpente",         "nome": "Dragão Serpente",               "raridade": "mitico",   "gif": "https://cdnb.artstation.com/p/assets/images/images/039/804/307/original/camila-xiao-tokens-of-natura-sea-dragon-pixel-art-creature-for-game-card-pixel-artist-2x.gif?1626976782"},
    {"id": "dragao_aco",              "nome": "Dragão de Aço",                 "raridade": "mitico",   "gif": "https://i.pinimg.com/originals/a6/5a/41/a65a41bea0d8cac396f6309bdcb7408c.gif"},
    {"id": "dragao_ilusao",           "nome": "Dragão da Ilusão",              "raridade": "mitico",   "gif": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSIGoiDbh34-18M4L2FNgcAeTs_5ZhRrh6RwD1OevEFRg&s=10"},
    {"id": "dragao_harpia",           "nome": "Dragão Harpia",                 "raridade": "mitico",   "gif": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSac9SxVwY95I-M4FAiSTIfyflL3HKOewRthGaww-BcVQ&s=10"},
    {"id": "dragao_cavernas",         "nome": "Dragão das Cavernas",           "raridade": "mitico",   "gif": "https://64.media.tumblr.com/68dc30d0eb6ff98966ce3e03a2d7d8cc/tumblr_nzuesoPOWL1qciqqno5_540.gif"},
]

def _garantir_criaturas_iniciais(user_id: int) -> list:
    """Garante que a pessoa tenha ao menos as criaturas ⚪ Comuns já
    desbloqueadas — é o "kit inicial" de todo mundo, pra sempre ter algo
    pra invocar numa batalha mesmo antes de vencer a primeira vez.
    Só concede na primeira vez (lista vazia); depois disso o progresso
    (raras, épicas, lendárias) fica só por conta de vitórias."""
    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])
    dados.setdefault("usos_criaturas", {})
    if not dados["criaturas"]:
        dados["criaturas"] = [c["id"] for c in _BATALHA_CRIATURAS if c["raridade"] == "comum"]
    return dados["criaturas"]


# Detecta a frase em qualquer lugar da mensagem (com ou sem acento), desde
# que tenha alguém mencionado junto.
_BATALHA_REGEX = re.compile(r"eu\s+te\s+desaf", re.IGNORECASE)

_BATALHA_COOLDOWN_SEGUNDOS = 120    # tempo mínimo entre desafios lançados pela MESMA pessoa
_batalha_ultimo_desafio: dict = {}  # user_id -> time.time() do último desafio lançado
_batalha_canal_ativo: set = set()   # channel_id -> impede 2 batalhas rolando ao mesmo tempo no mesmo canal

_BATALHA_CHANCE_SEM_ROUBO = 0.15    # 15% de chance do vencedor não levar XP NENHUM
_BATALHA_ROUBO_MIN = 0.01           # 1%  — mínimo que o dado pode sortear
_BATALHA_ROUBO_MAX = 0.20           # 20% — máximo que o dado pode sortear
_BATALHA_ROUBO_TETO = 500           # teto máximo de XP roubado por batalha — sem isso, quem
                                      # já é rank alto rouba uma quantidade cada vez maior de
                                      # quem também é rank alto (ou parecido), ficando desigual
                                      # contra o rank baixo. Ajuste pra combinar com seu servidor.

# ══════════════════════════════════════════════════════════════════════
# ⚡ GOLPES ESPECIAIS — chance rara de aparecer no meio de um desafio
# (`.eu te desafio @alguém`). Quando surge, o golpe é sempre do lado de
# quem venceu a batalha: além de vencer, a criatura solta um ataque nomeado
# e turbina o saque de XP daquela vitória (mínimo e máximo de roubo mais
# altos que o normal). É sorte pura — não depende de raridade nem de Nível
# de Capacidade, pra qualquer criatura poder puxar um a qualquer momento.
# ══════════════════════════════════════════════════════════════════════
_CHANCE_GOLPE_ESPECIAL = 0.12   # 12% de chance de aparecer em cada desafio

# Enquanto o golpe especial está ativo, o roubo de XP usa essa faixa turbinada
# em vez de _BATALHA_ROUBO_MIN / _BATALHA_ROUBO_MAX — e ignora totalmente a
# chance de "não roubar nada" (_BATALHA_CHANCE_SEM_ROUBO).
_GOLPE_ESPECIAL_ROUBO_MIN = 0.15    # 15%
_GOLPE_ESPECIAL_ROUBO_MAX = 0.35    # 35%
_GOLPE_ESPECIAL_ROUBO_TETO = 800    # teto máximo de XP roubado com Golpe Especial — mais alto
                                      # que o teto normal (é sorte rara, merece ser melhor), mas
                                      # ainda travado pra não ficar desigual entre rank baixo e alto.

_GOLPES_ESPECIAIS = [
    {"nome": "Investida das Sombras",   "emoji": "🌑", "frase": "atravessa o adversário como um sopro de trevas"},
    {"nome": "Lâmina de Névoa",         "emoji": "🌫️", "frase": "corta a distância antes que o outro perceba"},
    {"nome": "Chama Ancestral",         "emoji": "🔥", "frase": "solta um rugido em fogo puro"},
    {"nome": "Golpe do Eclipse",        "emoji": "🌘", "frase": "cobre tudo em escuridão por um instante e ataca"},
    {"nome": "Fúria Estelar",           "emoji": "🌟", "frase": "brilha antes de acertar em cheio"},
    {"nome": "Investida do Abismo",     "emoji": "🌀", "frase": "puxa o adversário pro fundo e nocauteia"},
    {"nome": "Garra Relâmpago",         "emoji": "⚡", "frase": "ataca rápido demais pra ser visto"},
    {"nome": "Sopro Glacial",           "emoji": "❄️", "frase": "congela o momento e desfere o golpe final"},
]


def _sortear_golpe_especial() -> dict | None:
    """Sorteia se um Golpe Especial aparece nessa batalha (_CHANCE_GOLPE_ESPECIAL)
    e, se sim, qual dos golpes da lista foi. Retorna None quando não aparece."""
    if random.random() >= _CHANCE_GOLPE_ESPECIAL:
        return None
    return random.choice(_GOLPES_ESPECIAIS)


# ══════════════════════════════════════════════════════════════════════
# 📜 LOGS DO RPG — canal fixo onde TODO ganho orgânico do jogo (criatura
# nova, Besta, Mítico, XP saqueado/golpe especial, prêmio de baú, ovo
# chocando etc.) é anunciado com o motivo.
#
# ⚠️ De propósito, NUNCA passa por aqui nada que venha de comando
# administrativo do Reality/CRIADOR_ID — .darcriatura, .uparcriatura,
# .vantagem (a concessão em si), .darbosster, .bostercall, .darlevel,
# .ovo (a concessão em si), .reiniciarcriaturas, .reiniciarranking,
# .xpbackfill, .destravarbesta/corrigirbesta/checarbesta,
# .destravarpet/corrigirpet/checarpet, .rankingdebug,
# .xpdebug, .castigo — esses são ajustes manuais internos, não "ganhos" do
# jogo, e não devem aparecer no log. Batalhas onde uma Vantagem foi usada
# nos bastidores CONTINUAM sendo logadas normalmente (como uma vitória
# comum) — é assim que o resto do bot já trata isso, pra manter a
# encenação de que não foi arranjada.
# ══════════════════════════════════════════════════════════════════════
CANAL_LOGS_RPG_ID = 1531072016634089673   # canal de logs do RPG


async def _log_rpg(guild: discord.Guild, titulo: str, descricao: str, cor: int = 0x9b59b6) -> None:
    """Manda uma entrada no canal de logs do RPG (CANAL_LOGS_RPG_ID). Silencioso
    se o canal não existir ou o bot não tiver permissão — nunca quebra o fluxo
    principal do jogo por causa do log."""
    if guild is None:
        return
    canal = guild.get_channel(CANAL_LOGS_RPG_ID)
    if canal is None:
        return
    embed = discord.Embed(title=titulo, description=descricao, color=cor, timestamp=discord.utils.utcnow())
    embed.set_footer(text="📜 Aeon & ☀️ Celestia — Logs do RPG")
    try:
        await canal.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException):
        pass

# ── Hierarquia de força das raridades ──────────────────────────────────────
# Cada raridade tem uma força relativa (_ORDEM_RARIDADES, do mais forte pro
# mais fraco: 🐉 Mítico > 🌌 Secreto > 🦴 Fóssil > 🐺 Bestas > 🌀 Elemental > 🟡 Lendário > 🟣 Épico > 🔵 Raro > ⚪ Comum).
# Quanto maior a distância de raridade entre duas criaturas, mais a balança
# pende pro lado mais forte — mas o lado mais fraco NUNCA fica com chance zero.
# Um ⚪ Comum sempre pode dar a zebra contra um 🟣 Épico, só que é raro.
# Chave = quantos "degraus" de raridade separam as duas criaturas na
# hierarquia (0 = mesma raridade, 7 = a maior distância possível).
_CHANCE_VITORIA_POR_DEGRAU = {
    0: 0.50,   # mesma raridade — força bruta pura, sorteio justo
    1: 0.63,   # 1 degrau de diferença (ex: 🔵 Raro vs ⚪ Comum)
    2: 0.74,   # 2 degraus de diferença (ex: 🟣 Épico vs ⚪ Comum)
    3: 0.83,   # 3 degraus de diferença (ex: 🟡 Lendário vs ⚪ Comum)
    4: 0.90,   # 4 degraus de diferença (ex: 🐺 Bestas vs ⚪ Comum)
    5: 0.93,   # 5 degraus de diferença (ex: 🦴 Fóssil vs ⚪ Comum)
    6: 0.96,   # 6 degraus de diferença (ex: 🌌 Secreto vs ⚪ Comum)
    7: 0.98,   # 7 degraus de diferença (ex: 🐉 Mítico vs 🔵 Raro)
    8: 0.99,   # 8 degraus — a maior distância possível, agora que 🌀 Elemental entrou
               # na hierarquia (🐉 Mítico vs ⚪ Comum)
}

# Excepção específica: 🟡 Lendário contra 🐉 Mítico OU 🌌 Secreto é MUITO mais
# desigual do que a tabela por degraus normal sugeriria. Aqui o lado mais forte
# (Mítico ou Secreto) fica com uma chance bem acima do teto normal de 95%, e o
# Lendário sobra só com uma fresta mínima pra dar a zebra. Isso NÃO afeta outros
# pares que também têm a mesma distância de degraus (ex: 🌌 Secreto vs 🟣 Épico) —
# só esses dois confrontos específicos contra o Lendário.
_CHANCE_VITORIA_LENDARIO_MITICO  = 0.99   # chance do Mítico  (o lado mais forte do par)
_CHANCE_VITORIA_LENDARIO_SECRETO = 0.97   # chance do Secreto (o lado mais forte do par)
_CHANCE_VITORIA_PAR_ESPECIAL = {
    frozenset({"lendario", "mitico"}):  _CHANCE_VITORIA_LENDARIO_MITICO,
    frozenset({"lendario", "secreto"}): _CHANCE_VITORIA_LENDARIO_SECRETO,
}


def _chance_vitoria_por_raridade(raridade_a: str, raridade_b: str) -> float:
    """Devolve a chance de uma criatura de raridade `raridade_a` vencer uma
    de raridade `raridade_b`, seguindo a hierarquia de força das raridades.
    Quanto mais forte a raridade (e maior a distância entre elas), maior a
    chance de vitória — mas o lado mais fraco sempre mantém uma chance real
    de virar o jogo, por menor que seja. Pares listados em
    _CHANCE_VITORIA_PAR_ESPECIAL pulam a conta por degrau e usam o valor fixo
    definido lá (esse valor ainda passa pelo ajuste de Nível de Capacidade
    em _chance_vitoria, então o resultado final pode variar um pouco)."""
    indice_a = _ORDEM_RARIDADES.index(raridade_a)   # 0 = 🐉 Mítico (mais forte) ... 4 = ⚪ Comum (mais fraco)
    indice_b = _ORDEM_RARIDADES.index(raridade_b)

    par_especial = _CHANCE_VITORIA_PAR_ESPECIAL.get(frozenset({raridade_a, raridade_b}))
    if par_especial is not None:
        chance_do_mais_forte = par_especial
    else:
        degrau = abs(indice_a - indice_b)
        chance_do_mais_forte = _CHANCE_VITORIA_POR_DEGRAU.get(degrau, 0.95)

    if indice_a < indice_b:      # A é a raridade mais forte
        return chance_do_mais_forte
    elif indice_a > indice_b:    # B é a raridade mais forte
        return 1.0 - chance_do_mais_forte
    return 0.5                   # mesma raridade


# ══════════════════════════════════════════════════════════════════════
# CAPACIDADE DE NÍVEL — cada criatura, além da raridade, tem um Nível de
# Capacidade individual (de 1 a 10) POR PESSOA. Toda criatura desbloqueada
# começa no Nível 1; quanto mais vezes ela é invocada em batalha (ganhando
# ou perdendo, não importa), mais ela "sobe de nível", até o teto de 10.
# Isso significa que duas pessoas com a MESMA criatura (mesma raridade)
# podem ter forças diferentes: quem mais batalhou com ela leva vantagem.
# ══════════════════════════════════════════════════════════════════════

_NIVEL_CRIATURA_MAX = 10

# Quantos USOS ACUMULADOS são necessários pra estar em cada nível. Índice 0
# (0 usos) já garante o Nível 1; índice 1 é o mínimo de usos pro Nível 2;
# e assim por diante até o índice 9, mínimo pro Nível 10 (o teto). Os
# degraus crescem aos poucos — fica mais rápido subir no começo e mais
# custoso lá no topo, pra o Nível 10 realmente significar "muito usada".
_NIVEL_CRIATURA_USOS_ACUMULADOS = [0, 3, 7, 12, 18, 25, 33, 42, 52, 63]

# Teto (e tabela de usos) especial para criaturas específicas — não é
# documentado/anunciado em nenhum lugar do bot de propósito. Continua a
# mesma progressão de dificuldade da tabela normal, só que até o Nível 20
# em vez de 10.
_NIVEL_CRIATURA_MAX_ESPECIAL = {"vorakthul": 20}
_NIVEL_CRIATURA_USOS_ACUMULADOS_ESTENDIDO = _NIVEL_CRIATURA_USOS_ACUMULADOS + [
    75, 88, 102, 117, 133, 150, 168, 187, 207, 228,
]

# Quanto cada DEGRAU de diferença de nível pesa na chance de vitória (ex:
# nível 1 vs nível 3 = 2 degraus de diferença). É um ajuste mais discreto
# que o da raridade — o nível refina a disputa, não a domina.
_NIVEL_CRIATURA_BONUS_POR_DEGRAU = 0.03

# Trava de segurança: mesmo com raridade E nível somados a favor de um
# lado, ninguém fica com 0% (ou 100%) de chance — sempre sobra uma brecha.
_CHANCE_VITORIA_MINIMA = 0.05
_CHANCE_VITORIA_MAXIMA = 0.95

# Trava separada e bem mais folgada, só pra confrontos listados em
# _CHANCE_VITORIA_PAR_ESPECIAL (Lendário x Mítico / Lendário x Secreto). Sem
# isso, os 99%/97% definidos ali em cima seriam cortados de volta pro teto
# normal de 95% — aqui a discrepância desses dois confrontos pode ir bem
# além disso, mesmo depois do ajuste de Nível de Capacidade.
_CHANCE_VITORIA_MINIMA_PAR_ESPECIAL = 0.01
_CHANCE_VITORIA_MAXIMA_PAR_ESPECIAL = 0.99


def _nivel_criatura_max(criatura_id: str = None) -> int:
    """Teto de Nível de Capacidade pra essa criatura — normalmente
    _NIVEL_CRIATURA_MAX (10), exceto pras que estão em
    _NIVEL_CRIATURA_MAX_ESPECIAL."""
    return _NIVEL_CRIATURA_MAX_ESPECIAL.get(criatura_id, _NIVEL_CRIATURA_MAX)


def _calcular_nivel_criatura(usos: int, criatura_id: str = None) -> int:
    """Converte quantos usos uma criatura já teve no Nível de Capacidade
    correspondente, de acordo com _NIVEL_CRIATURA_USOS_ACUMULADOS (ou a
    tabela estendida, pras criaturas em _NIVEL_CRIATURA_MAX_ESPECIAL)."""
    tabela = _NIVEL_CRIATURA_USOS_ACUMULADOS
    if criatura_id in _NIVEL_CRIATURA_MAX_ESPECIAL:
        tabela = _NIVEL_CRIATURA_USOS_ACUMULADOS_ESTENDIDO
    nivel = 1
    for indice, limite in enumerate(tabela):
        if usos >= limite:
            nivel = indice + 1
    return min(nivel, _nivel_criatura_max(criatura_id))


def _usos_criatura(user_id: int, criatura_id: str) -> int:
    """Quantas vezes essa pessoa já usou essa criatura em batalha."""
    dados = xp_stats[user_id]
    dados.setdefault("usos_criaturas", {})
    return dados["usos_criaturas"].get(criatura_id, 0)


def _nivel_criatura(user_id: int, criatura_id: str) -> int:
    """Nível de Capacidade atual dessa criatura, PRA ESSA pessoa."""
    return _calcular_nivel_criatura(_usos_criatura(user_id, criatura_id), criatura_id)


def _registrar_uso_criatura(user_id: int, criatura_id: str) -> tuple:
    """Soma mais 1 uso a essa criatura (pra essa pessoa) e devolve
    (nivel_antigo, nivel_novo) — útil pra saber se ela acabou de subir
    de Nível de Capacidade com esse uso."""
    dados = xp_stats[user_id]
    dados.setdefault("usos_criaturas", {})
    usos_antes = dados["usos_criaturas"].get(criatura_id, 0)
    nivel_antigo = _calcular_nivel_criatura(usos_antes, criatura_id)
    usos_depois = usos_antes + 1
    dados["usos_criaturas"][criatura_id] = usos_depois
    nivel_novo = _calcular_nivel_criatura(usos_depois, criatura_id)
    return nivel_antigo, nivel_novo


def _chance_vitoria(criatura_a: dict, nivel_a: int, criatura_b: dict, nivel_b: int) -> float:
    """Chance da criatura A vencer a criatura B, combinando a hierarquia de
    raridade (_chance_vitoria_por_raridade) com o ajuste fino do Nível de
    Capacidade de cada uma: pra cada degrau de nível a mais, um pequeno
    empurrão a mais na balança. Travado entre 5% e 95% no caso normal — mas
    os pares especiais (Lendário x Mítico / Lendário x Secreto) usam a trava
    mais folgada (1%/99%), já que a ideia ali é justamente uma discrepância
    bem maior que a de qualquer outro confronto."""
    chance_base = _chance_vitoria_por_raridade(criatura_a["raridade"], criatura_b["raridade"])
    ajuste_nivel = (nivel_a - nivel_b) * _NIVEL_CRIATURA_BONUS_POR_DEGRAU

    par = frozenset({criatura_a["raridade"], criatura_b["raridade"]})
    if par in _CHANCE_VITORIA_PAR_ESPECIAL:
        minimo, maximo = _CHANCE_VITORIA_MINIMA_PAR_ESPECIAL, _CHANCE_VITORIA_MAXIMA_PAR_ESPECIAL
    else:
        minimo, maximo = _CHANCE_VITORIA_MINIMA, _CHANCE_VITORIA_MAXIMA

    return max(minimo, min(maximo, chance_base + ajuste_nivel))


# ══════════════════════════════════════════════════════════════════════
# 🐺 BESTAS — raridade desbloqueada por CONQUISTA, não por sorteio. Mais
# fortes que as Lendárias, mas ainda um degrau abaixo das Secretas. A única
# forma de conseguir uma é levando uma criatura ⚪ Comum, 🔵 Raro, 🟣 Épico
# ou 🟡 Lendário até o Nível de Capacidade máximo (_NIVEL_CRIATURA_MAX) —
# ao bater esse nível, a pessoa recebe automaticamente, de graça, 1 Besta
# sorteada dentre as do "tier" correspondente (as que ela ainda não tiver).
# Nunca aparecem no sorteio normal de recompensa de batalha nem no 🪙 Baú —
# só saem por esse caminho.
# ══════════════════════════════════════════════════════════════════════

# tier de origem (raridade da criatura que bateu o Nível máximo) -> lista de
# ids de Bestas que podem ser concedidas quando isso acontece.
_BESTAS_POR_TIER = {
    "comum":    ["kragor_senhor_presas", "espinho_maldito"],
    "raro":     ["drogan_carniceiro", "matriarca_abismo"],
    "epico":    ["venomor"],
    "lendario": ["ultimo_shogun_trevas"],
}


def _checar_desbloqueio_besta(user_id: int, criatura: dict, nivel_antigo: int, nivel_novo: int):
    """Se `criatura` acabou de bater o Nível de Capacidade máximo dela AGORA
    (ou seja, subiu de nível nessa mesma batalha e o nível novo já é o teto)
    e a raridade dela tem um tier de Bestas associado, sorteia 1 Besta ainda
    não possuída daquele tier e concede pra `user_id`. Devolve a Besta
    concedida (dict) ou None se nada foi desbloqueado."""
    tier = _BESTAS_POR_TIER.get(criatura["raridade"])
    if not tier:
        return None
    if not (nivel_novo > nivel_antigo and nivel_novo >= _nivel_criatura_max(criatura["id"])):
        return None

    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])
    faltando = [c for c in _BATALHA_CRIATURAS if c["id"] in tier and c["id"] not in dados["criaturas"]]
    if not faltando:
        return None

    besta_nova = random.choice(faltando)
    dados["criaturas"].append(besta_nova["id"])
    return besta_nova


# Canal onde todo desbloqueio de 🐺 Besta é anunciado — mesmo canal do chat
# geral (_XP_CANAL_1 = 1284257046740602901).
_BESTA_ANUNCIO_CANAL_ID = 1284257046740602901


async def _anunciar_besta_desbloqueada(
    guild: discord.Guild, membro: discord.Member, criatura_origem: dict, besta: dict
) -> None:
    """Manda, no canal fixo _BESTA_ANUNCIO_CANAL_ID, o anúncio de que `membro`
    destravou a 🐺 Besta `besta` ao levar `criatura_origem` até o Nível de
    Capacidade máximo. Não apaga sozinho — fica registrado no canal."""
    canal = guild.get_channel(_BESTA_ANUNCIO_CANAL_ID)
    if canal is None:
        return

    info_raridade_besta = _RARIDADES["bestas"]
    teto = _nivel_criatura_max(criatura_origem["id"])

    embed = discord.Embed(
        title="🐺 Besta Destravada!",
        description=(
            f"⚡ **{membro.display_name}** levou **{criatura_origem['nome']}** até o "
            f"**Nível de Capacidade máximo** (`{teto}/{teto}`) e, como conquista, destravou "
            f"{info_raridade_besta['emoji']} **{besta['nome']}** (*{info_raridade_besta['label']}*)!!\n\n"
            "🌑 **Aeon:** *observa com respeito* ...uma conquista de verdade, ganha com treino. "
            "As sombras aprovam. 🖤🌑\n"
            f"🌟 **Celestia:** AAAAA {membro.mention} MERECEU CADA PINGO DISSO!! 😭🌟🤍✨ "
            "TREINOU, SUOU E CONQUISTOU!! 💪💫"
        ),
        color=info_raridade_besta["cor"],
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name=membro.display_name, icon_url=membro.display_avatar.url)
    embed.set_image(url=besta["gif"])
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Arena de Batalhas")

    try:
        await canal.send(content=membro.mention, embed=embed)
    except discord.HTTPException:
        pass


# Canal onde todo desbloqueio de 🦴 Fóssil é anunciado — mesmo canal do chat
# geral (_XP_CANAL_1 = 1284257046740602901), igual ao anúncio de Besta.
_FOSSIL_ANUNCIO_CANAL_ID = 1284257046740602901


async def _anunciar_fossil_desbloqueado(
    guild: discord.Guild, membro: discord.Member, fossil: dict
) -> None:
    """Manda, no canal fixo _FOSSIL_ANUNCIO_CANAL_ID, o anúncio de que `membro`
    desenterrou o 🦴 Fóssil `fossil` — sempre mencionando a pessoa E o nome
    da criatura. Só é chamado quando os dois lados da batalha estavam numa
    call de voz e a rolagem de _FOSSIL_CHANCE_DESBLOQUEIO deu certo."""
    canal = guild.get_channel(_FOSSIL_ANUNCIO_CANAL_ID)
    if canal is None:
        return

    info_raridade_fossil = _RARIDADES["fosseis"]

    embed = discord.Embed(
        title="🦴 Fóssil Desenterrado!",
        description=(
            f"🎧 Os dois lados da batalha estavam numa call de voz, e o dado só tinha "
            f"`{_FOSSIL_CHANCE_DESBLOQUEIO * 100:.0f}%` de chance — mas **{membro.display_name}** "
            f"desenterrou {info_raridade_fossil['emoji']} **{fossil['nome']}** "
            f"(*{info_raridade_fossil['label']}*)!!\n\n"
            "🌑 **Aeon:** *observa os ossos antigos* ...algo raro veio à tona. As sombras sentem "
            "o peso dos séculos nisso. 🖤🦴\n"
            f"🌟 **Celestia:** UAU {membro.mention} QUE SORTE ABSURDA!! 😱🦴✨ Achado de call, "
            "achado de sorte!! 💫"
        ),
        color=info_raridade_fossil["cor"],
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name=membro.display_name, icon_url=membro.display_avatar.url)
    embed.set_image(url=fossil["gif"])
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Arena de Batalhas")

    try:
        await canal.send(content=membro.mention, embed=embed)
    except discord.HTTPException:
        pass


def _forcar_verificacao_besta(user_id: int, criatura: dict):
    """Versão 'preguiçosa' de _checar_desbloqueio_besta: em vez de exigir que
    o Nível de Capacidade tenha acabado de subir NESSA hora, só olha o
    estado atual — se `criatura` já está no nível máximo dela pra essa
    pessoa. Usada pelo comando `.destravarbesta`, que existe pra corrigir
    manualmente os casos em que o desbloqueio automático (em batalha) falhou
    ou não foi anunciado. Sortear e conceder a Besta segue seguro contra
    duplicação: só concede se ainda faltar alguma Besta daquele tier na
    coleção da pessoa (mesma checagem de sempre)."""
    tier = _BESTAS_POR_TIER.get(criatura["raridade"])
    if not tier:
        return None
    if _nivel_criatura(user_id, criatura["id"]) < _nivel_criatura_max(criatura["id"]):
        return None

    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])
    faltando = [c for c in _BATALHA_CRIATURAS if c["id"] in tier and c["id"] not in dados["criaturas"]]
    if not faltando:
        return None

    besta_nova = random.choice(faltando)
    dados["criaturas"].append(besta_nova["id"])
    return besta_nova


# ══════════════════════════════════════════════════════════════════════
# 🌀 ELEMENTAIS — raridade desbloqueada por CONQUISTA, não por sorteio. Mais
# fortes que as Lendárias, mas ainda um degrau abaixo das Bestas. A única
# forma de conseguir um é levando uma criatura 🟣 Épica até o Nível de
# Capacidade `_ELEMENTAL_NIVEL_DESBLOQUEIO` (6, não precisa ser o teto) —
# ao bater esse nível, a pessoa recebe automaticamente, de graça, 1
# Elemental ALEATÓRIO dentre os que ainda não tiver (diferente das Bestas,
# não existe "tier" — todos os 12 Elementais entram no mesmo sorteio).
# Nunca aparecem no sorteio normal de recompensa de batalha nem no 🪙 Baú/
# `.ovo` — só saem por esse caminho.
#
# Além do desbloqueio, todo Elemental USADO numa batalha de desafio
# ("eu te desafio @alguém") — convocado, ganhando ou perdendo, não importa
# — concede na hora, pra quem o convocou, um Booster de xp em dobro por
# `_ELEMENTAL_BOOSTER_MINUTOS` minutos (empilha em cima de qualquer
# booster que a pessoa já tiver ativo — ver _executar_batalha).
# ══════════════════════════════════════════════════════════════════════

# Só criaturas 🟣 Épicas concedem Elemental, sempre ao bater ESSE Nível de
# Capacidade específico (não precisa ser o teto — igual os Pets, diferente
# das Bestas).
_ELEMENTAL_NIVEL_DESBLOQUEIO = 6

# Quanto tempo de Booster de xp em dobro (mesmo multiplicador de sempre,
# _BAU_BOOSTER_MULTIPLICADOR) cada USO de um Elemental em batalha concede.
_ELEMENTAL_BOOSTER_MINUTOS = 2


def _checar_desbloqueio_elemental(user_id: int, criatura: dict, nivel_antigo: int, nivel_novo: int):
    """Se `criatura` é 🟣 Épica e acabou de bater o Nível de Capacidade
    `_ELEMENTAL_NIVEL_DESBLOQUEIO` (6) AGORA — subiu de nível nessa mesma
    batalha e o nível novo já bate ou passa esse marco, o antigo ainda não
    batia — sorteia 1 Elemental ainda não possuído (dentre TODOS os 12,
    sem distinção de tier) e concede pra `user_id`. Devolve o Elemental
    concedido (dict) ou None se nada foi desbloqueado."""
    if criatura["raridade"] != "epico":
        return None
    if not (
        nivel_novo > nivel_antigo
        and nivel_novo >= _ELEMENTAL_NIVEL_DESBLOQUEIO
        and nivel_antigo < _ELEMENTAL_NIVEL_DESBLOQUEIO
    ):
        return None

    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])
    faltando = [c for c in _BATALHA_CRIATURAS if c["raridade"] == "elemental" and c["id"] not in dados["criaturas"]]
    if not faltando:
        return None

    elemental_novo = random.choice(faltando)
    dados["criaturas"].append(elemental_novo["id"])
    return elemental_novo


def _forcar_verificacao_elemental(user_id: int, criatura: dict):
    """Versão 'preguiçosa' de _checar_desbloqueio_elemental: em vez de
    exigir que o Nível de Capacidade tenha acabado de subir NESSA hora, só
    olha o estado atual — se `criatura` já está no Nível 6 ou mais pra essa
    pessoa. Usada pelo comando `.destravarelemental`, que existe pra
    corrigir manualmente os casos em que o desbloqueio automático (em
    batalha) falhou ou não foi anunciado."""
    if criatura["raridade"] != "epico":
        return None
    if _nivel_criatura(user_id, criatura["id"]) < _ELEMENTAL_NIVEL_DESBLOQUEIO:
        return None

    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])
    faltando = [c for c in _BATALHA_CRIATURAS if c["raridade"] == "elemental" and c["id"] not in dados["criaturas"]]
    if not faltando:
        return None

    elemental_novo = random.choice(faltando)
    dados["criaturas"].append(elemental_novo["id"])
    return elemental_novo


async def _anunciar_elemental_desbloqueado(
    guild: discord.Guild, membro: discord.Member, criatura_origem: dict, elemental: dict
) -> None:
    """Manda, no canal fixo _BESTA_ANUNCIO_CANAL_ID (mesmo do chat geral),
    o anúncio de que `membro` destravou o Elemental `elemental` ao levar
    `criatura_origem` até o Nível de Capacidade `_ELEMENTAL_NIVEL_DESBLOQUEIO`."""
    canal = guild.get_channel(_BESTA_ANUNCIO_CANAL_ID)
    if canal is None:
        return

    info_raridade_elemental = _RARIDADES["elemental"]

    embed = discord.Embed(
        title="🌀 Elemental Destravado!",
        description=(
            f"⚡ **{membro.display_name}** levou **{criatura_origem['nome']}** até o "
            f"**Nível de Capacidade `{_ELEMENTAL_NIVEL_DESBLOQUEIO}`** e, como conquista, destravou "
            f"{info_raridade_elemental['emoji']} **{elemental['nome']}** "
            f"(*{info_raridade_elemental['label']}*)!!\n\n"
            f"✨ A partir de agora, toda vez que **{elemental['nome']}** for convocado numa batalha, "
            f"{membro.display_name} ganha um Booster de xp em dobro por `{_ELEMENTAL_BOOSTER_MINUTOS} min`!\n\n"
            "🌑 **Aeon:** *observa a energia crua se assentar* ...uma força elemental, desperta. "
            "As sombras respeitam. 🖤🌀\n"
            f"🌟 **Celestia:** AAAAA {membro.mention} DESTRAVOU UM ELEMENTAL!! 😭🌀✨ "
            "OLHA ESSE PODER!! 💫"
        ),
        color=info_raridade_elemental["cor"],
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name=membro.display_name, icon_url=membro.display_avatar.url)
    embed.set_image(url=elemental["gif"])
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Arena de Batalhas")

    try:
        await canal.send(content=membro.mention, embed=embed)
    except discord.HTTPException:
        pass


# ══════════════════════════════════════════════════════════════════════
# 🐾 PETS — desbloqueados quando uma criatura 🔵 Rara sua bate o Nível de
# Capacidade 4 pela PRIMEIRA vez: na hora, sorteia (de graça) 1 Pet dentre
# os que você ainda não tem — igualzinho ao desbloqueio de 🐺 Besta (ver
# _checar_desbloqueio_besta acima), só que fixo no Nível 4 em vez do teto,
# e exclusivo das criaturas Raras.
#
# Pets NÃO entram em batalha PvP (não são "criaturas") — são só SUPORTE
# pro Boss: quando EQUIPADO (`.equiparpet <nome>`), o Pet soma um bônus
# fixo na chance de vencer QUALQUER Boss (entre 2% e 5%, crescendo com o
# Nível do próprio Pet) e tem uma chance de upar +1 o Nível de Capacidade
# de uma das suas criaturas toda vez que participa de uma VITÓRIA contra
# um Boss. Pets têm Nível de 1 a 5 — e SÓ sobem enfrentando Boss (vencendo
# ou perdendo, não importa, igual criatura) — e destravam uma habilidade
# especial própria, diferente pra cada Pet, ao chegar no Nível 3.
# ══════════════════════════════════════════════════════════════════════

_PET_NIVEL_MAX = 5
_PET_NIVEL_HABILIDADE = 3   # nível em que a habilidade especial de cada Pet é destravada

# Quantos confrontos de Boss (vencendo ou perdendo — só precisa PARTICIPAR
# com o Pet equipado) são necessários pra cada Nível. Índice 0 (0 usos) já
# garante o Nível 1; índice 4 é o mínimo pro Nível 5 (o teto).
_PET_NIVEL_USOS_ACUMULADOS = [0, 2, 5, 9, 14]

# Bônus na chance de vencer um Boss (soma direto na chance final, igual o
# bônus de raridade de criatura convocada) de acordo com o Nível do Pet
# EQUIPADO — sobe linear de 2% (Nível 1) até 5% (Nível 5).
_PET_BONUS_BOSS_NIVEL1 = 0.02
_PET_BONUS_BOSS_NIVEL5 = 0.05

# Chance-base do Pet equipado upar em +1 o Nível de Capacidade de uma
# criatura aleatória (dentre as que ainda não estão no teto) toda vez que
# ele participa de uma VITÓRIA contra um Boss.
_PET_CHANCE_UPAR_CRIATURA = 0.20

# Só criaturas 🔵 Raras concedem Pet, sempre ao bater ESSE Nível de
# Capacidade específico (não precisa ser o teto — diferente das Bestas).
_PET_NIVEL_DESBLOQUEIO = 4

_PETS = [
    {
        "id": "monstrinho",
        "nome": "Monstrinho",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410248198258888/1785186432942.gif?ex=6a691c6f&is=6a67caef&hm=4432eae4146ab6da26807f04c75dbde63df9f7dc4cad6ab13466b5ee86e2d57d&",
        "habilidade_nome": "🍖 Voracidade",
        "habilidade_descricao": "Soma +20 pontos percentuais na chance dele upar uma criatura sua depois de vencer um Boss.",
        "habilidade_tipo": "chance_upar_extra",
        "habilidade_valor": 0.20,
    },
    {
        "id": "vampy",
        "nome": "Vampy",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410247774900438/1785186421135.gif?ex=6a691c6f&is=6a67caef&hm=efa2f12767946aab1c7de01f05c655ab71f59fbceeaa7af6200d33ef7e93323e&",
        "habilidade_nome": "🩸 Sede Ancestral",
        "habilidade_descricao": "Suga um extra de `40` a `120` XP direto pra você sempre que vencem um Boss juntos.",
        "habilidade_tipo": "xp_flat_vitoria",
        "habilidade_valor": (40, 120),
    },
    {
        "id": "kitsura",
        "nome": "Kitsura",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410248500379648/1785186503259.gif?ex=6a691c6f&is=6a67caef&hm=c1fbc8ec4a818715875587c06071141004463e71a725b8af9586e0ae335e757d&",
        "habilidade_nome": "🦊 Ilusão da Raposa",
        "habilidade_descricao": "A chance dela upar uma criatura sua depois de vencer um Boss vira GARANTIDA (100%).",
        "habilidade_tipo": "upar_garantido",
        "habilidade_valor": None,
    },
    {
        "id": "drax",
        "nome": "Drax",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410248802504847/1785186661353.gif?ex=6a691c6f&is=6a67caef&hm=28f50e34bfbf2fee22720bd4d24cdc7d319ff63d4fc8add71dd737130353f404&",
        "habilidade_nome": "🔥 Fúria Draconiana",
        "habilidade_descricao": "Soma mais `+2%` fixos na chance de vencer QUALQUER Boss, além do bônus normal do Nível dele.",
        "habilidade_tipo": "bonus_chance_extra",
        "habilidade_valor": 0.02,
    },
    {
        "id": "lilo",
        "nome": "Lilo",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410249125203999/1785186871194.gif?ex=6a691c6f&is=6a67caef&hm=c719c8464520ddef5ca5593bc2bfc286b872770f964ae6c3c66dd4d87b0e639e&",
        "habilidade_nome": "🌙 Consolo Selvagem",
        "habilidade_descricao": "Mesmo numa DERROTA contra o Boss, garante um consolo de `20` a `60` XP.",
        "habilidade_tipo": "xp_flat_derrota",
        "habilidade_valor": (20, 60),
    },
    {
        "id": "aeon_celestia",
        "nome": "Aeon e Celestia",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410249431646359/1785186907093.gif?ex=6a691c6f&is=6a67caef&hm=96d4a27952131d1d8d0b41a504d92bfbbeb50d551334f6b73d3c31ed1916bf49&",
        "habilidade_nome": "🌗 Equilíbrio das Trevas e da Luz",
        "habilidade_descricao": "Soma `+1%` na chance de vitória em GRUPO contra o Boss pra CADA outro participante da batalha.",
        "habilidade_tipo": "bonus_grupo_participante",
        "habilidade_valor": 0.01,
    },
    {
        "id": "loki",
        "nome": "Loki",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410249813065955/1785186977070.gif?ex=6a691c6f&is=6a67caef&hm=327467c57a994e455420f5a59d77319be3f381ada027e5f324ba724dcab5c0fe&",
        "habilidade_nome": "🃏 Trapaça do Caos",
        "habilidade_descricao": "Soma mais `+3%` fixos na chance de vencer QUALQUER Boss, além do bônus normal do Nível dele.",
        "habilidade_tipo": "bonus_chance_extra",
        "habilidade_valor": 0.03,
    },
    {
        "id": "layla",
        "nome": "Layla",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410250266181752/1785187039526.gif?ex=6a691c6f&is=6a67caef&hm=9858b27fa61518fb3d4e61c3b46350151c8bdee861d4839fffd120b7fc97b998&",
        "habilidade_nome": "🌸 Bênção Silenciosa",
        "habilidade_descricao": "Soma +10 pontos percentuais na chance dela upar uma criatura sua depois de vencer um Boss.",
        "habilidade_tipo": "chance_upar_extra",
        "habilidade_valor": 0.10,
    },
]


def _pet_nivel_max() -> int:
    return _PET_NIVEL_MAX


def _calcular_nivel_pet(usos: int) -> int:
    """Converte quantos confrontos de Boss um Pet já participou (equipado)
    no Nível correspondente, de acordo com _PET_NIVEL_USOS_ACUMULADOS."""
    nivel = 1
    for indice, limite in enumerate(_PET_NIVEL_USOS_ACUMULADOS):
        if usos >= limite:
            nivel = indice + 1
    return min(nivel, _PET_NIVEL_MAX)


def _usos_pet(user_id: int, pet_id: str) -> int:
    """Quantos confrontos de Boss essa pessoa já enfrentou com esse Pet equipado."""
    dados = xp_stats[user_id]
    dados.setdefault("usos_pets", {})
    return dados["usos_pets"].get(pet_id, 0)


def _nivel_pet(user_id: int, pet_id: str) -> int:
    """Nível atual desse Pet, PRA ESSA pessoa."""
    return _calcular_nivel_pet(_usos_pet(user_id, pet_id))


def _registrar_uso_pet(user_id: int, pet_id: str) -> tuple:
    """Soma +1 confronto de Boss a esse Pet (pra essa pessoa) e devolve
    (nivel_antigo, nivel_novo) — útil pra saber se ele acabou de subir de
    Nível com esse confronto."""
    dados = xp_stats[user_id]
    dados.setdefault("usos_pets", {})
    usos_antes = dados["usos_pets"].get(pet_id, 0)
    nivel_antigo = _calcular_nivel_pet(usos_antes)
    usos_depois = usos_antes + 1
    dados["usos_pets"][pet_id] = usos_depois
    nivel_novo = _calcular_nivel_pet(usos_depois)
    return nivel_antigo, nivel_novo


def _encontrar_pet_por_nome(busca: str) -> dict:
    """Acha um Pet em _PETS a partir de um nome digitado (com ou sem
    acento/maiúsculas) — igual _encontrar_criatura_por_nome, só que pra Pets."""
    alvo = _normalizar_texto(busca)
    for p in _PETS:
        if _normalizar_texto(p["nome"]) == alvo:
            return p
    for p in _PETS:
        if _normalizar_texto(p["nome"]).startswith(alvo):
            return p
    candidatos = [p for p in _PETS if alvo in _normalizar_texto(p["nome"])]
    return candidatos[0] if len(candidatos) == 1 else None


def _pets_desbloqueados(user_id: int) -> list:
    """Lista de ids dos Pets já desbloqueados por essa pessoa."""
    dados = xp_stats[user_id]
    dados.setdefault("pets", [])
    return dados["pets"]


def _obter_pet_equipado(user_id: int) -> dict:
    """Devolve o dict do Pet atualmente EQUIPADO por essa pessoa, ou None
    se ela não tiver nenhum equipado (ou o equipado não existir mais)."""
    dados = xp_stats[user_id]
    pet_id = dados.get("pet_equipado")
    if not pet_id or pet_id not in _pets_desbloqueados(user_id):
        return None
    return next((p for p in _PETS if p["id"] == pet_id), None)


def _checar_desbloqueio_pet(user_id: int, criatura: dict, nivel_antigo: int, nivel_novo: int):
    """Se `criatura` é 🔵 Rara e acabou de bater o Nível de Capacidade
    `_PET_NIVEL_DESBLOQUEIO` (4) AGORA — subiu de nível nessa mesma
    batalha/ação e o nível novo já bate ou passa esse marco, o antigo
    ainda não batia — sorteia 1 Pet ainda não possuído e concede pra
    `user_id`. Devolve o Pet concedido (dict) ou None se nada foi
    desbloqueado (raridade errada, marco errado ou já tem todos os Pets)."""
    if criatura["raridade"] != "raro":
        return None
    if not (nivel_novo > nivel_antigo and nivel_novo >= _PET_NIVEL_DESBLOQUEIO and nivel_antigo < _PET_NIVEL_DESBLOQUEIO):
        return None

    dados = xp_stats[user_id]
    dados.setdefault("pets", [])
    faltando = [p for p in _PETS if p["id"] not in dados["pets"]]
    if not faltando:
        return None

    pet_novo = random.choice(faltando)
    dados["pets"].append(pet_novo["id"])
    return pet_novo


async def _anunciar_pet_desbloqueado(
    guild: discord.Guild, membro: discord.Member, criatura_origem: dict, pet: dict
) -> None:
    """Manda, no canal fixo _BESTA_ANUNCIO_CANAL_ID (mesmo do chat geral),
    o anúncio de que `membro` destravou o Pet `pet` ao levar `criatura_origem`
    até o Nível de Capacidade `_PET_NIVEL_DESBLOQUEIO`."""
    canal = guild.get_channel(_BESTA_ANUNCIO_CANAL_ID)
    if canal is None:
        return

    embed = discord.Embed(
        title="🐾 Pet Destravado!",
        description=(
            f"✨ **{membro.display_name}** levou **{criatura_origem['nome']}** até o "
            f"**Nível de Capacidade `{_PET_NIVEL_DESBLOQUEIO}`** e, de recompensa, destravou "
            f"o Pet **{pet['nome']}**!!\n\n"
            f"Use `.equiparpet {pet['nome']}` pra equipar — Pets dão bônus na chance de vencer "
            "Boss e ajudam a upar suas criaturas!\n\n"
            "🌑 **Aeon:** ...um novo companheiro. As sombras aceitam a companhia dele. 🖤🐾\n"
            f"🌟 **Celestia:** AAAAA {membro.mention} GANHOU UM PETZINHO NOVO!! 😭🌟🤍✨ TÃO FOFO!!"
        ),
        color=0x9b59b6,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name=membro.display_name, icon_url=membro.display_avatar.url)
    embed.set_image(url=pet["gif"])
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Arena de Batalhas")

    try:
        await canal.send(content=membro.mention, embed=embed)
    except discord.HTTPException:
        pass


def _forcar_verificacao_pet(user_id: int, criatura: dict):
    """Versão 'preguiçosa' de _checar_desbloqueio_pet: em vez de exigir que
    o Nível de Capacidade tenha acabado de subir NESSA hora, só olha o
    estado atual — se `criatura` (🔵 Rara) já está no Nível de Capacidade
    `_PET_NIVEL_DESBLOQUEIO` ou acima, pra essa pessoa. Usada pelo comando
    `.destravarpet`, que existe pra corrigir manualmente os casos em que o
    desbloqueio automático (em batalha) falhou ou não foi anunciado.
    Sortear e conceder o Pet segue seguro contra duplicação: só concede se
    ainda faltar algum Pet na coleção da pessoa (mesma checagem de sempre)."""
    if criatura["raridade"] != "raro":
        return None
    if _nivel_criatura(user_id, criatura["id"]) < _PET_NIVEL_DESBLOQUEIO:
        return None

    dados = xp_stats[user_id]
    dados.setdefault("pets", [])
    faltando = [p for p in _PETS if p["id"] not in dados["pets"]]
    if not faltando:
        return None

    pet_novo = random.choice(faltando)
    dados["pets"].append(pet_novo["id"])
    return pet_novo


def _pet_bonus_chance_boss(user_id: int) -> float:
    """Bônus total (0.0 se ninguém tiver Pet equipado) que o Pet EQUIPADO
    dessa pessoa soma na chance de vencer um Boss: o bônus base do Nível
    dele (2% a 5%, linear) + o bônus extra da habilidade especial, SE ela
    for do tipo "bonus_chance_extra" e o Pet já tiver batido o Nível
    _PET_NIVEL_HABILIDADE."""
    pet = _obter_pet_equipado(user_id)
    if pet is None:
        return 0.0
    nivel = _nivel_pet(user_id, pet["id"])
    faixa = _PET_BONUS_BOSS_NIVEL5 - _PET_BONUS_BOSS_NIVEL1
    bonus = _PET_BONUS_BOSS_NIVEL1 + faixa * ((nivel - 1) / (_PET_NIVEL_MAX - 1))
    if nivel >= _PET_NIVEL_HABILIDADE and pet["habilidade_tipo"] == "bonus_chance_extra":
        bonus += pet["habilidade_valor"]
    return bonus


def _pet_bonus_grupo_extra(participantes: list) -> float:
    """Bônus extra de GRUPO da habilidade especial 'bonus_grupo_participante'
    (Aeon e Celestia): soma, pra CADA participante que tiver esse Pet
    equipado E já no Nível de habilidade, `valor` de bônus por CADA OUTRO
    participante da batalha."""
    bonus_total = 0.0
    for membro in participantes:
        pet = _obter_pet_equipado(membro.id)
        if pet is None or pet["habilidade_tipo"] != "bonus_grupo_participante":
            continue
        nivel = _nivel_pet(membro.id, pet["id"])
        if nivel >= _PET_NIVEL_HABILIDADE:
            bonus_total += pet["habilidade_valor"] * max(0, len(participantes) - 1)
    return bonus_total


def _pet_upar_criatura_aleatoria(user_id: int):
    """Escolhe, entre as criaturas já desbloqueadas dessa pessoa que AINDA
    não estão no Nível de Capacidade máximo, uma aleatória, e empurra os
    usos dela pro limiar mínimo do próximo Nível (mesma lógica do
    `.uparcriatura`). Devolve (criatura, nivel_novo, besta_nova, pet_novo)
    — besta_nova/pet_novo vêm preenchidos se esse "up" de brinde acabou de
    destravar uma Besta ou um Pet novo (cascata) — ou None se não tinha
    nenhuma criatura elegível pra upar."""
    desbloqueadas = set(_garantir_criaturas_iniciais(user_id))
    candidatas = [
        c for c in _BATALHA_CRIATURAS
        if c["id"] in desbloqueadas and _nivel_criatura(user_id, c["id"]) < _nivel_criatura_max(c["id"])
    ]
    if not candidatas:
        return None

    criatura = random.choice(candidatas)
    criatura_id = criatura["id"]
    nivel_antigo = _nivel_criatura(user_id, criatura_id)

    tabela = (
        _NIVEL_CRIATURA_USOS_ACUMULADOS_ESTENDIDO
        if criatura_id in _NIVEL_CRIATURA_MAX_ESPECIAL
        else _NIVEL_CRIATURA_USOS_ACUMULADOS
    )
    dados = xp_stats[user_id]
    dados.setdefault("usos_criaturas", {})
    dados["usos_criaturas"][criatura_id] = max(
        dados["usos_criaturas"].get(criatura_id, 0),
        tabela[nivel_antigo],   # limiar de usos mínimos pro PRÓXIMO nível
    )
    nivel_novo = _calcular_nivel_criatura(dados["usos_criaturas"][criatura_id], criatura_id)

    besta_nova = _checar_desbloqueio_besta(user_id, criatura, nivel_antigo, nivel_novo)
    pet_novo = _checar_desbloqueio_pet(user_id, criatura, nivel_antigo, nivel_novo)

    return criatura, nivel_novo, besta_nova, pet_novo


async def _pet_pos_boss(guild: discord.Guild, membro: discord.Member, venceu: bool):
    """Chamada depois de CADA confronto de Boss (solo ou grupo, vencendo
    ou perdendo) pra CADA participante: registra +1 uso no Pet EQUIPADO
    dessa pessoa (se tiver algum), checa se ele upou de Nível, e aplica os
    efeitos de suporte (chance de upar uma criatura na vitória, habilidade
    especial a partir do Nível 3...). Devolve um texto pronto (ou None) pra
    encaixar no resultado do Boss."""
    pet = _obter_pet_equipado(membro.id)
    if pet is None:
        return None

    nivel_antigo, nivel_novo = _registrar_uso_pet(membro.id, pet["id"])
    habilidade_ativa = nivel_novo >= _PET_NIVEL_HABILIDADE
    partes = []

    if nivel_novo > nivel_antigo:
        partes.append(f"🐾 **{pet['nome']}** ({membro.display_name}) subiu pro Nível `{nivel_novo}/{_PET_NIVEL_MAX}`!")
        if nivel_novo == _PET_NIVEL_HABILIDADE:
            partes.append(f"✨ Habilidade especial destravada: **{pet['habilidade_nome']}**!")

    def _somar_xp_extra(ganho_extra: int):
        dados_membro = xp_stats[membro.id]
        nivel_xp_antigo = dados_membro["nivel"]
        dados_membro["xp"] += ganho_extra
        dados_membro["nivel"], _, _ = _calcular_nivel(dados_membro["xp"])
        if dados_membro["nivel"] > nivel_xp_antigo and guild is not None:
            asyncio.create_task(_anunciar_level_up(guild, membro, dados_membro["nivel"]))

    if venceu:
        chance_upar = _PET_CHANCE_UPAR_CRIATURA
        garantido = False
        if habilidade_ativa:
            if pet["habilidade_tipo"] == "chance_upar_extra":
                chance_upar += pet["habilidade_valor"]
            elif pet["habilidade_tipo"] == "upar_garantido":
                garantido = True
            elif pet["habilidade_tipo"] == "xp_flat_vitoria":
                ganho_extra = random.randint(*pet["habilidade_valor"])
                _somar_xp_extra(ganho_extra)
                partes.append(f"{pet['habilidade_nome']}: +`{ganho_extra}` XP extra pra {membro.mention}!")

        if garantido or random.random() < chance_upar:
            resultado_up = _pet_upar_criatura_aleatoria(membro.id)
            if resultado_up is not None:
                criatura_upada, nivel_criatura_novo, besta_nova, pet_novo_cascata = resultado_up
                partes.append(
                    f"🐾 **{pet['nome']}** ajudou **{criatura_upada['nome']}** ({membro.display_name}) a "
                    f"subir pro Nível de Capacidade `{nivel_criatura_novo}`!"
                )
                if besta_nova is not None and guild is not None:
                    asyncio.create_task(_anunciar_besta_desbloqueada(guild, membro, criatura_upada, besta_nova))
                if pet_novo_cascata is not None and guild is not None:
                    asyncio.create_task(_anunciar_pet_desbloqueado(guild, membro, criatura_upada, pet_novo_cascata))
    else:
        if habilidade_ativa and pet["habilidade_tipo"] == "xp_flat_derrota":
            ganho_extra = random.randint(*pet["habilidade_valor"])
            _somar_xp_extra(ganho_extra)
            partes.append(f"{pet['habilidade_nome']}: +`{ganho_extra}` XP de consolo pra {membro.mention}!")

    if partes:
        asyncio.create_task(_salvar_xp_stats())

    return "\n".join(partes) if partes else None


async def _pet_pos_boss_grupo(guild: discord.Guild, participantes: list, venceu: bool):
    """Roda `_pet_pos_boss` pra CADA participante de um confronto de Boss
    (uma batalha solo só passa uma lista de 1 elemento) e junta as notas de
    todo mundo num texto só, pronto pra encaixar no resultado."""
    notas = []
    for membro in participantes:
        nota = await _pet_pos_boss(guild, membro, venceu)
        if nota:
            notas.append(nota)
    return "\n".join(notas) if notas else None


# ══════════════════════════════════════════════════════════════════════
# .destravarbesta — comando de manutenção/correção. Verifica se a pessoa
# (ou alguém que o Reality aponte) tem alguma criatura ⚪/🔵/🟣 já no Nível
# de Capacidade máximo cuja Besta correspondente não foi concedida (por
# causa de alguma falha no desbloqueio automático em batalha) e concede na
# hora, anunciando no mesmo canal fixo de sempre (_BESTA_ANUNCIO_CANAL_ID).
# Idempotente: pode ser chamado várias vezes sem risco de duplicar — só
# concede enquanto sobrar Besta faltando no tier.
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="destravarbesta", aliases=["corrigirbesta", "checarbesta"])
async def cmd_destravarbesta(ctx, membro: discord.Member = None):
    """Corrige o bug de Besta não concedida/anunciada.
    Uso: .destravarbesta            → verifica você mesmo
         .destravarbesta @membro    → só o Reality pode checar outra pessoa
    """
    autor = ctx.author

    if membro is not None and membro.id != autor.id and autor.id != CRIADOR_ID:
        await ctx.send(
            "🌑 **Aeon:** *olha de lado* ...você só pode checar as suas próprias criaturas. 🖤🌑"
        )
        return

    alvo = membro or autor

    dados = xp_stats[alvo.id]
    dados.setdefault("criaturas", [])

    candidatas = [
        c for c in _BATALHA_CRIATURAS
        if c["id"] in dados["criaturas"]
        and c["raridade"] in _BESTAS_POR_TIER
        and _nivel_criatura(alvo.id, c["id"]) >= _nivel_criatura_max(c["id"])
    ]

    if not candidatas:
        await ctx.send(
            f"🌑 **Aeon:** *verifica em silêncio* ...nenhuma criatura Comum, Rara ou Épica de "
            f"{alvo.mention} está no Nível de Capacidade máximo agora. 🖤🌑 Nada pra destravar."
        )
        return

    concedidas = []
    for criatura in candidatas:
        besta = _forcar_verificacao_besta(alvo.id, criatura)
        if besta is not None:
            concedidas.append((criatura, besta))

    if not concedidas:
        await ctx.send(
            f"🌟 **Celestia:** Verifiquei tudinho!! 😊🌸 {alvo.mention} já tem todas as Bestas "
            "disponíveis pros tiers das criaturas maxadas dela — nada faltando pra destravar!! ✨"
        )
        return

    asyncio.create_task(_salvar_xp_stats())

    for criatura, besta in concedidas:
        if ctx.guild:
            asyncio.create_task(_anunciar_besta_desbloqueada(ctx.guild, alvo, criatura, besta))

    nomes = ", ".join(f"🐺 **{besta['nome']}**" for _, besta in concedidas)
    await ctx.send(
        f"✅ Corrigido! {alvo.mention} destravou: {nomes} — confira o canal de anúncios e `.criaturas`. ⚡"
    )


# ══════════════════════════════════════════════════════════════════════
# .destravarpet — comando de manutenção/correção. Verifica se a pessoa
# (ou alguém que o Reality aponte) tem alguma criatura 🔵 Rara já no Nível
# de Capacidade `_PET_NIVEL_DESBLOQUEIO` (4) ou mais cujo Pet correspondente
# não foi concedido (por causa de alguma falha no desbloqueio automático em
# batalha) e concede na hora, anunciando no mesmo canal fixo de sempre
# (_BESTA_ANUNCIO_CANAL_ID). Idempotente: pode ser chamado várias vezes sem
# risco de duplicar — só concede enquanto sobrar Pet faltando na coleção.
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="destravarpet", aliases=["corrigirpet", "checarpet"])
async def cmd_destravarpet(ctx, membro: discord.Member = None):
    """Corrige o bug de Pet não concedido/anunciado.
    Uso: .destravarpet            → verifica você mesmo
         .destravarpet @membro    → só o Reality pode checar outra pessoa
    """
    autor = ctx.author

    if membro is not None and membro.id != autor.id and autor.id != CRIADOR_ID:
        await ctx.send(
            "🌑 **Aeon:** *olha de lado* ...você só pode checar as suas próprias criaturas. 🖤🌑"
        )
        return

    alvo = membro or autor

    dados = xp_stats[alvo.id]
    dados.setdefault("criaturas", [])

    candidatas = [
        c for c in _BATALHA_CRIATURAS
        if c["id"] in dados["criaturas"]
        and c["raridade"] == "raro"
        and _nivel_criatura(alvo.id, c["id"]) >= _PET_NIVEL_DESBLOQUEIO
    ]

    if not candidatas:
        await ctx.send(
            f"🌑 **Aeon:** *verifica em silêncio* ...nenhuma criatura Rara de "
            f"{alvo.mention} está no Nível de Capacidade `{_PET_NIVEL_DESBLOQUEIO}` ou mais "
            "agora. 🖤🌑 Nada pra destravar."
        )
        return

    concedidos = []
    for criatura in candidatas:
        pet = _forcar_verificacao_pet(alvo.id, criatura)
        if pet is not None:
            concedidos.append((criatura, pet))

    if not concedidos:
        await ctx.send(
            f"🌟 **Celestia:** Verifiquei tudinho!! 😊🌸 {alvo.mention} já tem todos os Pets "
            "disponíveis pras criaturas Raras maxadas dela — nada faltando pra destravar!! ✨"
        )
        return

    asyncio.create_task(_salvar_xp_stats())

    for criatura, pet in concedidos:
        if ctx.guild:
            asyncio.create_task(_anunciar_pet_desbloqueado(ctx.guild, alvo, criatura, pet))

    nomes = ", ".join(f"🐾 **{pet['nome']}**" for _, pet in concedidos)
    await ctx.send(
        f"✅ Corrigido! {alvo.mention} destravou: {nomes} — confira o canal de anúncios e `.equiparpet`. ⚡"
    )


# ══════════════════════════════════════════════════════════════════════
# .reiniciacriaturas — comando de manutenção. Zera a COLEÇÃO de criaturas
# de UMA pessoa específica (por ID): as criaturas/Bestas desbloqueadas, o
# Nível de Capacidade de cada uma e a criatura favorita ativa. NÃO mexe em
# XP, nível geral nem vitórias/derrotas — só no lado "criaturas" mesmo.
# Irreversível, por isso pede confirmação por botão antes de aplicar.
# ══════════════════════════════════════════════════════════════════════

class ReiniciarCriaturasView(discord.ui.View):
    def __init__(self, alvo_id: int, alvo_nome: str):
        super().__init__(timeout=60)
        self.alvo_id = alvo_id
        self.alvo_nome = alvo_nome

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != CRIADOR_ID:
            await interaction.response.send_message(
                "⚠️ Só o Reality pode confirmar esse reset.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="✅ Confirmar reset",
        style=discord.ButtonStyle.danger,
        custom_id="reiniciar_criaturas_confirmar"
    )
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        dados = xp_stats[self.alvo_id]
        dados["criaturas"] = []
        dados["usos_criaturas"] = {}
        dados["favorito"] = {"id": None, "usos": 0, "cansacos": {}}

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=(
                f"♻️ **Criaturas de `{self.alvo_nome}` (`{self.alvo_id}`) reiniciadas** — "
                "coleção, Níveis de Capacidade e favorita voltaram a 0."
            ),
            embed=None,
            view=self
        )
        self.stop()
        asyncio.create_task(_salvar_xp_stats())

    @discord.ui.button(
        label="❌ Cancelar",
        style=discord.ButtonStyle.secondary,
        custom_id="reiniciar_criaturas_cancelar"
    )
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="❌ Reset cancelado.", embed=None, view=self)
        self.stop()


@bot.command(name="reiniciacriaturas", aliases=["reiniciarcriaturas", "resetcriaturas"])
async def cmd_reiniciacriaturas(ctx, alvo_id: int = None):
    """Reseta a coleção de criaturas (desbloqueadas, Níveis de Capacidade e
    favorita) de UMA pessoa específica, por ID. Não mexe em XP/nível geral
    nem vitórias/derrotas. Só o Reality pode usar.
    Uso: .reiniciacriaturas <ID do membro>"""
    if ctx.author.id != CRIADOR_ID:
        return

    if alvo_id is None:
        aviso = await ctx.send("⚠️ Uso: `.reiniciacriaturas <ID do membro>`")
        await _apagar_mensagem_depois(aviso, 15)
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    alvo = guild.get_member(alvo_id) if guild else None
    if alvo is None and guild:
        try:
            alvo = await guild.fetch_member(alvo_id)
        except discord.NotFound:
            alvo = None

    alvo_nome = alvo.display_name if alvo else str(alvo_id)
    dados = xp_stats[alvo_id]
    qtd_criaturas = len(dados.get("criaturas", []))

    embed = discord.Embed(
        title="♻️ Reiniciar Criaturas",
        description=(
            f"👤 **Membro:** {alvo.mention if alvo else f'`{alvo_id}`'} — `{alvo_nome}`\n"
            f"📖 **Criaturas desbloqueadas atualmente:** `{qtd_criaturas}`\n\n"
            "Isso vai **zerar** a coleção de criaturas (inclusive 🐺 Bestas), o Nível de Capacidade "
            "de cada uma e a criatura favorita dessa pessoa.\n"
            "⚠️ XP, nível geral e vitórias/derrotas **não** são afetados — só o lado \"criaturas\".\n\n"
            "Tem certeza?"
        ),
        color=0xff4444
    )
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Sistema de Criaturas")
    await ctx.send(embed=embed, view=ReiniciarCriaturasView(alvo_id, alvo_nome))


# ══════════════════════════════════════════════════════════════════════
# CRIATURA FAVORITA — comando `.favorito <nome>`. Enquanto alguém tiver uma
# favorita ativa, ela é SEMPRE a escolhida nas batalhas dessa pessoa (em vez
# do sorteio aleatório de sempre) — até "cansar" depois de um certo número
# de usos seguidos. Aí ela some da jogada, as batalhas voltam a sortear
# aleatoriamente, e a pessoa entra num cooldown até poder favoritar de novo.
# ══════════════════════════════════════════════════════════════════════

_FAVORITO_USOS_ATE_CANSAR = 5           # quantas batalhas seguidas usando a favorita até ela cansar
_FAVORITO_COOLDOWN_SEGUNDOS = 30 * 60   # 30 min de descanso depois de cansar, até poder favoritar de novo

_FAVORITO_PADRAO = {"id": None, "usos": 0, "cansacos": {}}


def _normalizar_texto(texto: str) -> str:
    """Tira acentos e baixa a caixa — deixa a comparação de nomes de
    criatura tolerante a 'kaiju do eco', 'Kaiju Do Eco', 'KAIJU DO ECO'..."""
    sem_acento = "".join(
        ch for ch in unicodedata.normalize("NFKD", texto or "") if not unicodedata.combining(ch)
    )
    return sem_acento.lower().strip()


def _encontrar_criatura_por_nome(busca: str) -> dict:
    """Acha uma criatura em _BATALHA_CRIATURAS a partir de um nome digitado
    livremente (sem acento, com espaço, etc.). Tenta, nessa ordem: nome
    exato, id exato, e por fim uma busca por trecho (só aceita se achar
    UMA única criatura possível — em caso de ambiguidade, devolve None)."""
    alvo = _normalizar_texto(busca)
    if not alvo:
        return None

    for c in _BATALHA_CRIATURAS:
        if _normalizar_texto(c["nome"]) == alvo:
            return c

    alvo_id = alvo.replace(" ", "_")
    for c in _BATALHA_CRIATURAS:
        if c["id"] == alvo_id:
            return c

    candidatos = [c for c in _BATALHA_CRIATURAS if alvo in _normalizar_texto(c["nome"])]
    if len(candidatos) == 1:
        return candidatos[0]
    return None


def _favorito_status(user_id: int) -> dict:
    """Devolve o dict de favorito dessa pessoa, já garantindo a estrutura
    padrão e limpando sozinho qualquer cansaço cujo cooldown já tenha passado.
    Cada criatura cansada tem seu próprio tempo de descanso em "cansacos",
    então dá pra ter mais de uma "de castigo" ao mesmo tempo (ex: você troca
    de favorita antes da anterior acabar de descansar)."""
    dados = xp_stats[user_id]
    dados.setdefault("favorito", {"id": None, "usos": 0, "cansacos": {}})
    favorito = dados["favorito"]
    favorito.setdefault("id", None)
    favorito.setdefault("usos", 0)
    favorito.setdefault("cansacos", {})

    agora = time.time()
    expirados = [cid for cid, ate in favorito["cansacos"].items() if agora >= ate]
    for cid in expirados:
        del favorito["cansacos"][cid]

    return favorito


def _favorito_cooldown_restante(user_id: int, criatura_id: str) -> float:
    """Segundos restantes até UMA CRIATURA ESPECÍFICA poder ser favoritada de
    novo (0 se ela não estiver descansando no momento)."""
    favorito = _favorito_status(user_id)
    ate = favorito["cansacos"].get(criatura_id)
    if ate is None:
        return 0.0
    return max(0.0, ate - time.time())


def _formatar_tempo_restante(segundos: float) -> str:
    minutos, segs = divmod(max(0, int(segundos)), 60)
    return f"{minutos}m{segs:02d}s"


def _obter_criatura_favorita_ativa(user_id: int) -> dict:
    """Devolve a criatura favorita ATIVA dessa pessoa (não cansada), ou
    None se ela não tiver nenhuma favoritada no momento."""
    favorito = _favorito_status(user_id)
    if not favorito["id"]:
        return None
    return next((c for c in _BATALHA_CRIATURAS if c["id"] == favorito["id"]), None)


def _registrar_uso_favorito(user_id: int, criatura_id: str) -> bool:
    """Chamada toda vez que uma criatura é usada numa batalha. Se essa
    criatura for a favorita ativa dessa pessoa, soma +1 no contador de usos
    seguidos. Ao bater _FAVORITO_USOS_ATE_CANSAR, ela cansa: sai do posto de
    favorita (as próximas batalhas voltam a sortear aleatoriamente) e entra
    em cooldown até poder ser favoritada de novo. Devolve True se ela cansou
    JUSTO NESSE uso (pra poder avisar no resultado da batalha)."""
    favorito = _favorito_status(user_id)
    if favorito["id"] != criatura_id:
        return False
    favorito["usos"] += 1
    if favorito["usos"] >= _FAVORITO_USOS_ATE_CANSAR:
        favorito["cansacos"][criatura_id] = time.time() + _FAVORITO_COOLDOWN_SEGUNDOS
        favorito["id"] = None
        favorito["usos"] = 0
        return True
    return False


# 🐉 Míticos continuam raríssimos de desbloquear: não entram no sorteio
# normal de recompensa — só há uma checagem especial a cada N vitórias, com
# uma chance bem pequena de sair uma Mítica nova.
_MITICO_VITORIAS_INTERVALO = 10      # a cada quantas vitórias rola a chance de Mítica
_MITICO_CHANCE_DESBLOQUEIO = 0.01    # 1% de chance nessa rolagem

# 🦴 Fósseis — diferente do Mítico (que precisa de um MÚLTIPLO de vitórias),
# o Fóssil rola em TODA vitória, sem intervalo — mas só entra em jogo quando
# os dois lados da batalha (desafiante e desafiado) estão numa call de voz
# no momento em que ela acontece. Sem os dois em call, a rolagem nem
# acontece — não importa quantas vitórias a pessoa já tenha.
_FOSSIL_CHANCE_DESBLOQUEIO = 0.02     # 2% de chance nessa rolagem (só quando os dois estão em call)

_BATALHA_TEMPO_ACEITE = 60          # segundos que o desafiado tem pra aceitar/recusar
_BATALHA_TEMPO_SOMEM  = 60          # segundos até cada mensagem da batalha sumir sozinha

# ── Vantagem — comando .vantagem <ID>, só o Reality. Marca alguém pra
# GANHAR garantido a PRÓXIMA batalha que participar (como desafiante ou
# desafiado, tanto faz) e saquear entre _VANTAGEM_ROUBO_MIN e
# _VANTAGEM_ROUBO_MAX (20% a 30%) de XP garantido da outra pessoa — o
# percentual exato ainda é sorteado, só que dentro dessa faixa mais alta e
# sem chance de sair 0% — pulando o sorteio normal de vitória/roubo. É
# consumida (removida do set) assim que essa próxima batalha acontece. ──
_vantagem_ativa: set = set()      # user_ids com Vantagem pendente pra próxima batalha
_VANTAGEM_ROUBO_MIN = 0.20        # 20% — mínimo de xp roubado garantido quando a Vantagem é usada
_VANTAGEM_ROUBO_MAX = 0.30        # 30% — máximo de xp roubado garantido quando a Vantagem é usada
_VANTAGEM_ROUBO_TETO = 700        # teto máximo de XP roubado com a Vantagem — ainda travado,
                                    # mesmo sendo um roubo garantido, pra não ficar desigual
                                    # entre rank baixo e alto.

# ── Vantagem (call) — comando .vantagemfossio <ID>, só o Reality. Parecida
# com .vantagem (vitória garantida), mas com 3 diferenças:
#   1. Só "destrava" numa batalha em que desafiante e desafiado estejam os
#      dois na MESMA call no momento do combate. Se a próxima batalha dela
#      acontecer sem os dois em call juntos, a Vantagem NÃO é consumida —
#      fica pendente, esperando uma batalha em que a condição bata.
#   2. O roubo de XP usa uma faixa própria, mais baixa que a do .vantagem
#      normal: _VANTAGEM_FOSSIO_ROUBO_MIN a _MAX (10% a 20%, também sem
#      chance de sair 0%).
#   3. Como a condição já garante os dois em call, o desenterro de 🦴 Fóssil
#      (normalmente só _FOSSIL_CHANCE_DESBLOQUEIO = 2% de chance) sai
#      GARANTIDO nessa vitória também, se ainda sobrar algum Fóssil pra
#      quem venceu destravar. ──
_vantagem_fossio_ativa: set = set()   # user_ids com Vantagem (call) pendente
_VANTAGEM_FOSSIO_ROUBO_MIN = 0.10     # 10% — mínimo de xp roubado garantido com a Vantagem (call)
_VANTAGEM_FOSSIO_ROUBO_MAX = 0.20     # 20% — máximo de xp roubado garantido com a Vantagem (call)
_VANTAGEM_FOSSIO_ROUBO_TETO = 700     # teto máximo de XP roubado com a Vantagem (call) — mesmo teto do .vantagem normal


def _mesma_call(a: discord.Member, b: discord.Member) -> bool:
    """True se os dois estiverem conectados no mesmo canal de voz agora."""
    voz_a = a.voice.channel if a.voice else None
    voz_b = b.voice.channel if b.voice else None
    return voz_a is not None and voz_a == voz_b


async def _apagar_mensagem_depois(mensagem: discord.Message, segundos: int = _BATALHA_TEMPO_SOMEM) -> None:
    """Espera alguns segundos e apaga a mensagem sozinha, ignorando erros
    se ela já não existir mais (apagada, canal sumiu, etc.)."""
    await asyncio.sleep(segundos)
    try:
        await mensagem.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass


def _embed_status_desafio(
    desafiante: discord.Member, desafiado: discord.Member, estado: str
) -> discord.Embed:
    """Monta o embed do convite de desafio, num dos estados: pendente, aceito,
    recusado ou expirado."""
    if estado == "pendente":
        titulo = "⚔️ Um desafio foi lançado!"
        descricao = (
            f"🌑 **Aeon:** ...{desafiante.mention} desafiou {desafiado.mention} para uma batalha. "
            f"As sombras aguardam a resposta. 🖤🌑\n"
            f"🌟 **Celestia:** {desafiado.mention}, VOCÊ ACEITA?! 😆🌟✨ "
            f"*aponta pros botões* Tem `{_BATALHA_TEMPO_ACEITE}s` pra decidir!!"
        )
        cor = 0x2b2b3b
    elif estado == "aceito":
        titulo = "✅ Desafio aceito!"
        descricao = (
            f"🌟 **Celestia:** {desafiado.mention} TOPOU!! 😱🌟✨ *vibra* A batalha vai começar...\n"
            f"🌑 **Aeon:** ...que as sombras testemunhem o combate. 🖤🌑"
        )
        cor = 0x4bbf73
    elif estado == "recusado":
        titulo = "🏳️ Desafio recusado"
        descricao = (
            f"🌑 **Aeon:** ...{desafiado.mention} recuou. As trevas respeitam a escolha. 🖤🌑\n"
            f"🌟 **Celestia:** Tudo bem, {desafiante.mention}!! Talvez na próxima!! 🌸"
        )
        cor = 0x888888
    else:  # expirado
        titulo = "⌛ Desafio expirado"
        descricao = (
            f"🌑 **Aeon:** ...{desafiado.mention} não respondeu a tempo. O desafio se dissolve nas sombras. 🖤🌑\n"
            f"🌟 **Celestia:** Que pena!! Talvez {desafiante.mention} tente de novo depois!! 🌸"
        )
        cor = 0x888888

    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Arena de Batalhas")
    return embed


class DesafioView(discord.ui.View):
    """Botões de Aceitar/Recusar que aparecem no convite de desafio.
    Só o desafiado pode usá-los, e o convite expira sozinho depois de
    _BATALHA_TEMPO_ACEITE segundos se ninguém responder."""

    def __init__(self, desafiante: discord.Member, desafiado: discord.Member):
        super().__init__(timeout=_BATALHA_TEMPO_ACEITE)
        self.desafiante = desafiante
        self.desafiado = desafiado
        self.respondido = False
        self.mensagem: discord.Message = None  # setada logo após o send()

    def _travar_botoes(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="⚔️ Aceitar", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.desafiado.id:
            await interaction.response.send_message(
                "🌟 **Celestia:** Esse desafio não é seu pra aceitar!! 🌸😅", ephemeral=True
            )
            return

        self.respondido = True
        self._travar_botoes()
        await interaction.response.edit_message(
            embed=_embed_status_desafio(self.desafiante, self.desafiado, "aceito"),
            view=self,
        )
        self.stop()
        asyncio.create_task(_iniciar_batalha_apos_aceite(interaction.channel, self.desafiante, self.desafiado))

    @discord.ui.button(label="🏳️ Recusar", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.desafiado.id:
            await interaction.response.send_message(
                "🌟 **Celestia:** Esse desafio não é seu pra recusar!! 🌸😅", ephemeral=True
            )
            return

        self.respondido = True
        self._travar_botoes()
        await interaction.response.edit_message(
            embed=_embed_status_desafio(self.desafiante, self.desafiado, "recusado"),
            view=self,
        )
        self.stop()
        _batalha_canal_ativo.discard(interaction.channel.id)

    async def on_timeout(self):
        if self.respondido or self.mensagem is None:
            return
        self._travar_botoes()
        try:
            await self.mensagem.edit(
                embed=_embed_status_desafio(self.desafiante, self.desafiado, "expirado"),
                view=self,
            )
        except discord.HTTPException:
            pass
        _batalha_canal_ativo.discard(self.mensagem.channel.id)


async def _iniciar_batalha_apos_aceite(
    canal: discord.TextChannel, desafiante: discord.Member, desafiado: discord.Member
) -> None:
    """Chamada quando o desafiado aceita — roda a batalha e, no final (ou em
    caso de erro), libera o canal pra um novo desafio poder ser lançado."""
    try:
        await _executar_batalha(canal, desafiante, desafiado)
    finally:
        _batalha_canal_ativo.discard(canal.id)


def _sortear_uma_criatura(user_id: int) -> dict:
    """Sorteia 1 criatura para essa pessoa invocar. Se ela tiver uma 🌟
    favorita ativa (e ainda não cansada), a favorita é SEMPRE a escolhida —
    sem sorteio nenhum. Só cai no sorteio aleatório (SOMENTE dentre as que
    ela já desbloqueou, ponderado pela raridade — Comuns saem com mais
    frequência que Raras, e assim por diante) quando não há favorita ativa."""
    desbloqueadas = set(_garantir_criaturas_iniciais(user_id))

    favorita = _obter_criatura_favorita_ativa(user_id)
    if favorita is not None and favorita["id"] in desbloqueadas:
        return favorita

    pool = [c for c in _BATALHA_CRIATURAS if c["id"] in desbloqueadas]
    if not pool:
        # segurança: nunca deveria cair aqui, já que _garantir_criaturas_iniciais
        # sempre concede as Comuns antes da batalha começar.
        pool = [c for c in _BATALHA_CRIATURAS if c["raridade"] == "comum"] or list(_BATALHA_CRIATURAS)
    pesos = [_RARIDADES[c["raridade"]]["peso"] for c in pool]
    return random.choices(pool, weights=pesos, k=1)[0]


def _sortear_criaturas(desafiante_id: int, desafiado_id: int):
    """Sorteia a criatura de cada lado da batalha, cada uma dentre APENAS o
    que aquela pessoa já tem desbloqueado — nunca uma criatura que ela ainda
    não possui."""
    return _sortear_uma_criatura(desafiante_id), _sortear_uma_criatura(desafiado_id)


async def _executar_batalha(
    canal: discord.TextChannel, desafiante: discord.Member, desafiado: discord.Member
) -> None:
    """Roda a sequência dramática da batalha inteira: abertura, revelação das
    duas criaturas, suspense e conclusão (com ou sem roubo de XP)."""
    criatura_desafiante, criatura_desafiado = _sortear_criaturas(desafiante.id, desafiado.id)

    # Nível de Capacidade (1 a 10) de cada criatura, PRA CADA pessoa — quanto
    # mais essa pessoa já batalhou com ela, mais alto o nível e mais forte
    # ela fica, mesmo entre criaturas da mesma raridade.
    nivel_desafiante = _nivel_criatura(desafiante.id, criatura_desafiante["id"])
    nivel_desafiado = _nivel_criatura(desafiado.id, criatura_desafiado["id"])

    # 🌟 Se a criatura sorteada é a favorita ativa de quem invocou, marca
    # visualmente — o sorteio já dá prioridade absoluta a ela em _sortear_uma_criatura.
    eh_favorita_desafiante = _favorito_status(desafiante.id)["id"] == criatura_desafiante["id"]
    eh_favorita_desafiado = _favorito_status(desafiado.id)["id"] == criatura_desafiado["id"]
    marcador_favorita_desafiante = " 🌟" if eh_favorita_desafiante else ""
    marcador_favorita_desafiado = " 🌟" if eh_favorita_desafiado else ""

    # 🌀 Booster de xp por Elemental — cada Elemental USADO nessa batalha
    # (convocado, ganhando ou perdendo, não importa) já concede na hora,
    # pra quem o convocou, um Booster de xp em dobro por
    # _ELEMENTAL_BOOSTER_MINUTOS minutos — empilha em cima de qualquer
    # booster que a pessoa já tiver ativo (mesma função do 🪙 Baú/.darbosster).
    boost_elemental_desafiante = criatura_desafiante["raridade"] == "elemental"
    boost_elemental_desafiado = criatura_desafiado["raridade"] == "elemental"
    if boost_elemental_desafiante:
        _conceder_xp_booster(desafiante.id, _ELEMENTAL_BOOSTER_MINUTOS)
    if boost_elemental_desafiado:
        _conceder_xp_booster(desafiado.id, _ELEMENTAL_BOOSTER_MINUTOS)
    marcador_elemental_desafiante = " 🌀✨" if boost_elemental_desafiante else ""
    marcador_elemental_desafiado = " 🌀✨" if boost_elemental_desafiado else ""

    # ── Abertura ──────────────────────────────────────────────────────────
    embed_abertura = discord.Embed(
        title="⚔️ UMA BATALHA COMEÇA!",
        description=(
            f"🌑 **Aeon:** *as sombras se agitam de repente* ...{desafiante.mention} lançou o desafio. "
            f"{desafiado.mention}, as trevas aguardam sua resposta. 🖤🌑\n"
            f"🌟 **Celestia:** AAAAA UMA BATALHA?! 😱🌟✨ *brilha intensamente* "
            f"TODO MUNDO PRA ARENA, ISSO VAI SER ÉPICO!!"
        ),
        color=0x2b2b3b,
    )
    embed_abertura.set_footer(text="🌑 Aeon & ☀️ Celestia — Arena de Batalhas")
    msg_abertura = await canal.send(embed=embed_abertura)
    asyncio.create_task(_apagar_mensagem_depois(msg_abertura))
    await asyncio.sleep(2)

    # ── Criatura do desafiante ───────────────────────────────────────────
    embed_c1 = discord.Embed(
        title="🔥 O desafiador entra em campo!",
        description=(
            f"**{desafiante.display_name}** invoca... **{criatura_desafiante['nome']}** "
            f"`⭐ Nível {nivel_desafiante}`{marcador_favorita_desafiante}{marcador_elemental_desafiante}!! 💥"
        ),
        color=0xff4444,
    )
    embed_c1.set_image(url=criatura_desafiante["gif"])
    msg_c1 = await canal.send(embed=embed_c1)
    asyncio.create_task(_apagar_mensagem_depois(msg_c1))
    await asyncio.sleep(2.5)

    # ── Criatura do desafiado ────────────────────────────────────────────
    embed_c2 = discord.Embed(
        title="💠 O desafiado revida!",
        description=(
            f"**{desafiado.display_name}** responde invocando... **{criatura_desafiado['nome']}** "
            f"`⭐ Nível {nivel_desafiado}`{marcador_favorita_desafiado}{marcador_elemental_desafiado}!! ⚡"
        ),
        color=0x4488ff,
    )
    embed_c2.set_image(url=criatura_desafiado["gif"])
    msg_c2 = await canal.send(embed=embed_c2)
    asyncio.create_task(_apagar_mensagem_depois(msg_c2))
    await asyncio.sleep(3)

    # ── Suspense antes do resultado ──────────────────────────────────────
    aviso = await canal.send("💥⚡ *As duas criaturas colidem em um choque de poder...* ⚡💥")
    await asyncio.sleep(2.5)
    try:
        await aviso.delete()
    except discord.HTTPException:
        pass

    # ── Sorteia o vencedor ────────────────────────────────────────────────
    # Combina a hierarquia de força das raridades com o Nível de Capacidade
    # de cada criatura (_chance_vitoria): quanto maior a diferença de
    # raridade E de nível, mais a balança pende pro lado mais forte — mas o
    # lado mais fraco sempre mantém uma chance real de dar a zebra.
    #
    # 🍀 EXCEÇÃO: se um dos dois tiver uma Vantagem pendente (.vantagem), ela
    # é consumida aqui e o resultado NEM passa pelo sorteio — essa pessoa
    # vence garantido essa batalha (a próxima que ela participar depois de
    # receber a Vantagem).
    vantagem_usada_por = None
    via_vantagem_fossio = False   # True quando quem venceu foi por causa do .vantagemfossio (não do .vantagem normal)
    if desafiante.id in _vantagem_ativa:
        _vantagem_ativa.discard(desafiante.id)
        vantagem_usada_por = desafiante.id
    elif desafiado.id in _vantagem_ativa:
        _vantagem_ativa.discard(desafiado.id)
        vantagem_usada_por = desafiado.id
    elif _mesma_call(desafiante, desafiado):
        # 🍀📞 Vantagem (call) — só entra em jogo se os dois estiverem
        # juntos numa call agora. Fora dessa condição fica pendente e cai
        # no sorteio normal, sem ser consumida.
        if desafiante.id in _vantagem_fossio_ativa:
            _vantagem_fossio_ativa.discard(desafiante.id)
            vantagem_usada_por = desafiante.id
            via_vantagem_fossio = True
        elif desafiado.id in _vantagem_fossio_ativa:
            _vantagem_fossio_ativa.discard(desafiado.id)
            vantagem_usada_por = desafiado.id
            via_vantagem_fossio = True

    if vantagem_usada_por == desafiante.id:
        vencedor, criatura_vencedora = desafiante, criatura_desafiante
        perdedor, criatura_perdedora = desafiado, criatura_desafiado
    elif vantagem_usada_por == desafiado.id:
        vencedor, criatura_vencedora = desafiado, criatura_desafiado
        perdedor, criatura_perdedora = desafiante, criatura_desafiante
    else:
        chance_desafiante_vence = _chance_vitoria(
            criatura_desafiante, nivel_desafiante, criatura_desafiado, nivel_desafiado
        )

        if random.random() < chance_desafiante_vence:
            vencedor, criatura_vencedora = desafiante, criatura_desafiante
            perdedor, criatura_perdedora = desafiado, criatura_desafiado
        else:
            vencedor, criatura_vencedora = desafiado, criatura_desafiado
            perdedor, criatura_perdedora = desafiante, criatura_desafiante

    # ── Registra o uso — CADA criatura usada nessa batalha (vencendo ou
    # perdendo) soma +1 no seu contador, e pode subir de Nível de Capacidade
    # na hora — quanto mais usada, mais forte ela fica com o tempo.
    nivel_antigo_criatura_vencedora, nivel_novo_criatura_vencedora = _registrar_uso_criatura(
        vencedor.id, criatura_vencedora["id"]
    )
    nivel_antigo_criatura_perdedora, nivel_novo_criatura_perdedora = _registrar_uso_criatura(
        perdedor.id, criatura_perdedora["id"]
    )

    # 🌟 Se alguma das duas era a favorita ativa de quem a usou, soma mais um
    # uso seguido nela também — e, se bater o limite, ela cansa aqui mesmo
    # (some da função de favorita e entra em cooldown).
    cansou_favorita_vencedora = _registrar_uso_favorito(vencedor.id, criatura_vencedora["id"])
    cansou_favorita_perdedora = _registrar_uso_favorito(perdedor.id, criatura_perdedora["id"])

    # ── Lança o "dado" que decide quanto (ou se) o vencedor rouba de XP ──
    dados_perdedor = xp_stats[perdedor.id]
    dados_vencedor = xp_stats[vencedor.id]
    xp_perdedor_antes = dados_perdedor["xp"]

    # ── Registro de vitórias/derrotas — atualiza sempre, independente de roubo de XP ──
    dados_vencedor["vitorias"] = dados_vencedor.get("vitorias", 0) + 1
    dados_perdedor["derrotas"] = dados_perdedor.get("derrotas", 0) + 1

    # ── Desbloqueio de criatura — como os dois só podem invocar criaturas que
    # JÁ possuem, a criatura usada na batalha nunca é nova pra quem venceu.
    # A recompensa da vitória é diferente: o vencedor tem chance de destravar
    # uma criatura NOVA (sorteada por raridade, dentre as que ainda não tem)
    # pra sua coleção. Quem perde não ganha nada disso.
    # 🐉 Míticas ficam de fora desse sorteio normal — elas têm uma checagem
    # especial própria logo abaixo, bem mais rara. 🌌 Secretas também ficam
    # de fora — essas só saem do 🪙 Baú (.bau), nunca como recompensa de
    # batalha. 🦴 Fósseis também ficam de fora — só saem com os dois lados em
    # call, ver checagem própria logo abaixo. 🐺 Bestas também ficam de fora —
    # essas só saem quando uma criatura Comum/Rara/Épica bate o Nível de
    # Capacidade máximo (ver _checar_desbloqueio_besta logo abaixo). ──
    dados_vencedor.setdefault("criaturas", [])
    _nao_possuidas = [
        c for c in _BATALHA_CRIATURAS
        if c["id"] not in dados_vencedor["criaturas"] and c["raridade"] not in ("mitico", "secreto", "fosseis", "bestas", "elemental")
    ]
    criatura_nova = None
    if _nao_possuidas:
        _pesos_novas = [_RARIDADES[c["raridade"]]["peso"] for c in _nao_possuidas]
        criatura_nova = random.choices(_nao_possuidas, weights=_pesos_novas, k=1)[0]
        dados_vencedor["criaturas"].append(criatura_nova["id"])

    # ── 🐉 Desbloqueio Mítico — só rola a cada _MITICO_VITORIAS_INTERVALO
    # vitórias do vencedor, e mesmo aí só com _MITICO_CHANCE_DESBLOQUEIO de
    # chance. São bestas absurdas (quase 99% de vitória contra qualquer
    # raridade menor; Mítico x Mítico é sorteio puro), então o jogo as torna
    # raríssimas de conseguir também. ──
    criatura_mitica_nova = None
    if (
        dados_vencedor["vitorias"] % _MITICO_VITORIAS_INTERVALO == 0
        and random.random() < _MITICO_CHANCE_DESBLOQUEIO
    ):
        _miticas_faltando = [
            c for c in _BATALHA_CRIATURAS
            if c["raridade"] == "mitico" and c["id"] not in dados_vencedor["criaturas"]
        ]
        if _miticas_faltando:
            criatura_mitica_nova = random.choice(_miticas_faltando)
            dados_vencedor["criaturas"].append(criatura_mitica_nova["id"])

    # ── 🦴 Desbloqueio de Fóssil — só entra em jogo quando os DOIS lados da
    # batalha (desafiante E desafiado) estão numa call de voz no exato
    # momento em que ela termina. Se essa condição bater, rola
    # _FOSSIL_CHANCE_DESBLOQUEIO de chance do vencedor desenterrar um Fóssil
    # novo — sem depender de vitórias acumuladas nem de intervalo nenhum,
    # diferente do Mítico. Se algum dos dois não estiver em call, a rolagem
    # nem acontece. ──
    criatura_fossil_nova = None
    _ambos_em_call = (
        desafiante.voice is not None and desafiante.voice.channel is not None
        and desafiado.voice is not None and desafiado.voice.channel is not None
    )
    if _ambos_em_call and (via_vantagem_fossio or random.random() < _FOSSIL_CHANCE_DESBLOQUEIO):
        # 📞 Se veio do .vantagemfossio, pula o sorteio de _FOSSIL_CHANCE_DESBLOQUEIO
        # (2%) e já cai direto aqui garantido — só depende de sobrar algum
        # Fóssil que quem venceu ainda não tenha.
        _fosseis_faltando = [
            c for c in _BATALHA_CRIATURAS
            if c["raridade"] == "fosseis" and c["id"] not in dados_vencedor["criaturas"]
        ]
        if _fosseis_faltando:
            criatura_fossil_nova = random.choice(_fosseis_faltando)
            dados_vencedor["criaturas"].append(criatura_fossil_nova["id"])

    # ── 🐺 Desbloqueio de Besta — vale pros dois lados, já que os dois
    # "usaram" sua criatura nessa batalha e qualquer uma das duas pode ter
    # batido o Nível de Capacidade máximo agora. Só concede quando a
    # criatura em questão é Comum, Rara ou Épica (as únicas com tier de
    # Besta associado) e o Nível máximo acabou de ser alcançado NESSA
    # batalha — ver _checar_desbloqueio_besta. ──
    besta_nova_vencedor = _checar_desbloqueio_besta(
        vencedor.id, criatura_vencedora, nivel_antigo_criatura_vencedora, nivel_novo_criatura_vencedora
    )
    besta_nova_perdedor = _checar_desbloqueio_besta(
        perdedor.id, criatura_perdedora, nivel_antigo_criatura_perdedora, nivel_novo_criatura_perdedora
    )

    # ── Anuncia no canal fixo (_BESTA_ANUNCIO_CANAL_ID) sempre que uma Besta
    # for destravada agora, dizendo quem foi e qual Besta. Vale pros dois
    # lados, já que qualquer um dos dois pode ter batido o nível máximo. ──
    if besta_nova_vencedor is not None and canal.guild:
        asyncio.create_task(
            _anunciar_besta_desbloqueada(canal.guild, vencedor, criatura_vencedora, besta_nova_vencedor)
        )
    if besta_nova_perdedor is not None and canal.guild:
        asyncio.create_task(
            _anunciar_besta_desbloqueada(canal.guild, perdedor, criatura_perdedora, besta_nova_perdedor)
        )

    # ── 🌀 Desbloqueio de Elemental — vale pros dois lados, já que os dois
    # "usaram" sua criatura nessa batalha e qualquer uma das duas pode ter
    # batido o Nível de Capacidade 6 agora. Só concede quando a criatura em
    # questão é 🟣 Épica e esse Nível 6 acabou de ser alcançado NESSA
    # batalha — ver _checar_desbloqueio_elemental. ──
    elemental_novo_vencedor = _checar_desbloqueio_elemental(
        vencedor.id, criatura_vencedora, nivel_antigo_criatura_vencedora, nivel_novo_criatura_vencedora
    )
    elemental_novo_perdedor = _checar_desbloqueio_elemental(
        perdedor.id, criatura_perdedora, nivel_antigo_criatura_perdedora, nivel_novo_criatura_perdedora
    )

    # ── Anuncia no canal fixo (_BESTA_ANUNCIO_CANAL_ID) sempre que um
    # Elemental for destravado agora, dizendo quem foi e qual Elemental. ──
    if elemental_novo_vencedor is not None and canal.guild:
        asyncio.create_task(
            _anunciar_elemental_desbloqueado(canal.guild, vencedor, criatura_vencedora, elemental_novo_vencedor)
        )
    if elemental_novo_perdedor is not None and canal.guild:
        asyncio.create_task(
            _anunciar_elemental_desbloqueado(canal.guild, perdedor, criatura_perdedora, elemental_novo_perdedor)
        )

    # ── Anuncia no canal fixo (_FOSSIL_ANUNCIO_CANAL_ID) sempre que um
    # Fóssil for desenterrado agora, mencionando quem foi e qual Fóssil. ──
    if criatura_fossil_nova is not None and canal.guild:
        asyncio.create_task(
            _anunciar_fossil_desbloqueado(canal.guild, vencedor, criatura_fossil_nova)
        )

    # ── 🐾 Desbloqueio de Pet — vale pros dois lados, pela mesma razão da
    # Besta acima: os dois "usaram" sua criatura nessa batalha, e qualquer
    # uma das duas pode ter batido o Nível de Capacidade 4 agora. Só
    # concede quando a criatura em questão é 🔵 Rara e esse Nível 4 acabou
    # de ser alcançado NESSA batalha — ver _checar_desbloqueio_pet. ──
    pet_novo_vencedor = _checar_desbloqueio_pet(
        vencedor.id, criatura_vencedora, nivel_antigo_criatura_vencedora, nivel_novo_criatura_vencedora
    )
    pet_novo_perdedor = _checar_desbloqueio_pet(
        perdedor.id, criatura_perdedora, nivel_antigo_criatura_perdedora, nivel_novo_criatura_perdedora
    )
    if pet_novo_vencedor is not None and canal.guild:
        asyncio.create_task(
            _anunciar_pet_desbloqueado(canal.guild, vencedor, criatura_vencedora, pet_novo_vencedor)
        )
    if pet_novo_perdedor is not None and canal.guild:
        asyncio.create_task(
            _anunciar_pet_desbloqueado(canal.guild, perdedor, criatura_perdedora, pet_novo_perdedor)
        )

    # ⚡ Golpe Especial — chance rara (_CHANCE_GOLPE_ESPECIAL) de aparecer nessa
    # batalha, sempre do lado de quem já venceu. Se a Vantagem foi usada, o
    # resultado já veio "arranjado" — golpe especial não entra em jogo aqui,
    # pra não misturar os dois sistemas.
    golpe_especial = _sortear_golpe_especial() if vantagem_usada_por is None else None

    xp_roubado = 0
    percentual = 0.0
    if vantagem_usada_por is not None:
        if via_vantagem_fossio:
            # 📞 Vantagem (call) usada — rouba entre 10% e 20% garantido
            # (sem chance de 0%), faixa própria e mais baixa que a do
            # .vantagem normal.
            percentual = random.uniform(_VANTAGEM_FOSSIO_ROUBO_MIN, _VANTAGEM_FOSSIO_ROUBO_MAX)
            teto_roubo = _VANTAGEM_FOSSIO_ROUBO_TETO
        else:
            # 🍀 Vantagem usada — rouba entre 20% e 30% garantido (sem chance de
            # 0%), sem passar pelo sorteio normal de "pode não roubar nada".
            percentual = random.uniform(_VANTAGEM_ROUBO_MIN, _VANTAGEM_ROUBO_MAX)
            teto_roubo = _VANTAGEM_ROUBO_TETO
        if xp_perdedor_antes > 0:
            xp_roubado = max(1, round(xp_perdedor_antes * percentual))
            xp_roubado = min(xp_roubado, xp_perdedor_antes, teto_roubo)  # nunca deixa o xp negativo, e trava no teto
    elif golpe_especial is not None and xp_perdedor_antes > 0:
        # ⚡ Golpe Especial ativo — ignora a chance de "não roubar nada" e usa
        # a faixa turbinada (_GOLPE_ESPECIAL_ROUBO_MIN / _MAX) em vez da normal.
        percentual = random.uniform(_GOLPE_ESPECIAL_ROUBO_MIN, _GOLPE_ESPECIAL_ROUBO_MAX)
        xp_roubado = max(1, round(xp_perdedor_antes * percentual))
        xp_roubado = min(xp_roubado, xp_perdedor_antes, _GOLPE_ESPECIAL_ROUBO_TETO)  # nunca deixa o xp negativo, e trava no teto
    elif xp_perdedor_antes > 0 and random.random() >= _BATALHA_CHANCE_SEM_ROUBO:
        percentual = random.uniform(_BATALHA_ROUBO_MIN, _BATALHA_ROUBO_MAX)
        xp_roubado = max(1, round(xp_perdedor_antes * percentual))
        xp_roubado = min(xp_roubado, xp_perdedor_antes, _BATALHA_ROUBO_TETO)  # nunca deixa o xp negativo, e trava no teto

    if xp_roubado > 0:
        nivel_antigo_vencedor = dados_vencedor["nivel"]

        dados_perdedor["xp"] = max(0, xp_perdedor_antes - xp_roubado)
        dados_perdedor["nivel"], _, _ = _calcular_nivel(dados_perdedor["xp"])

        dados_vencedor["xp"] += xp_roubado
        dados_vencedor["nivel"], _, _ = _calcular_nivel(dados_vencedor["xp"])

        if dados_vencedor["nivel"] > nivel_antigo_vencedor and canal.guild:
            asyncio.create_task(_anunciar_level_up(canal.guild, vencedor, dados_vencedor["nivel"]))

        asyncio.create_task(_atualizar_ranking_xp())

    # Salva sempre — mesmo sem roubo de XP, o placar de vitórias/derrotas mudou
    asyncio.create_task(_salvar_xp_stats())

    # ── Conclusão dramática — propositalmente usa o MESMO texto de sempre,
    # mesmo quando o resultado veio de uma Vantagem: ninguém no chat pode
    # perceber que essa batalha foi "arranjada". ──
    texto_golpe_especial = ""
    if golpe_especial is not None:
        texto_golpe_especial = (
            f"\n\n{golpe_especial['emoji']} **GOLPE ESPECIAL!!** **{criatura_vencedora['nome']}** usou "
            f"**{golpe_especial['nome']}** — {golpe_especial['frase']}! O saque de XP dessa vitória "
            "veio turbinado. ⚡"
        )

    if xp_roubado > 0:
        texto_roubo = (
            f"💰 O dado sorteou **`{percentual * 100:.1f}%`**! "
            f"**{vencedor.display_name}** saqueou **`{xp_roubado}` XP** de **{perdedor.display_name}**!"
            f"{texto_golpe_especial}"
        )
    else:
        texto_roubo = (
            f"🍃 O dado não favoreceu **{vencedor.display_name}** dessa vez — "
            f"nenhum XP foi roubado de **{perdedor.display_name}**."
        )

    texto_placar = (
        f"📊 **Retrospecto:** {vencedor.mention} `🏆 {dados_vencedor['vitorias']} vitórias / "
        f"{dados_vencedor['derrotas']} derrotas` — {perdedor.mention} `🏆 {dados_perdedor['vitorias']} vitórias / "
        f"{dados_perdedor['derrotas']} derrotas`"
    )

    partes_desbloqueio = []
    if criatura_nova is not None:
        info_raridade_nova = _RARIDADES[criatura_nova["raridade"]]
        partes_desbloqueio.append(
            f"🆕 De recompensa, **{vencedor.display_name}** desbloqueou "
            f"{info_raridade_nova['emoji']} **{criatura_nova['nome']}** "
            f"(*{info_raridade_nova['label']}*) na Enciclopédia! Use `.criaturas` pra conferir. 📖"
        )
    if criatura_mitica_nova is not None:
        info_raridade_mitica = _RARIDADES[criatura_mitica_nova["raridade"]]
        partes_desbloqueio.append(
            f"🐉✨ **SORTE RARÍSSIMA!!** Só {_MITICO_CHANCE_DESBLOQUEIO * 100:.0f}% de chance a cada "
            f"{_MITICO_VITORIAS_INTERVALO} vitórias, e **{vencedor.display_name}** acabou de desbloquear "
            f"{info_raridade_mitica['emoji']} **{criatura_mitica_nova['nome']}** "
            f"(*{info_raridade_mitica['label']}*)!! 🐉✨"
        )
    if criatura_fossil_nova is not None:
        info_raridade_fossil = _RARIDADES[criatura_fossil_nova["raridade"]]
        partes_desbloqueio.append(
            f"🦴✨ **ACHADO RARÍSSIMO!!** Os dois estavam numa call, e o dado só tinha "
            f"{_FOSSIL_CHANCE_DESBLOQUEIO * 100:.0f}% de chance — mas **{vencedor.display_name}** "
            f"desenterrou {info_raridade_fossil['emoji']} **{criatura_fossil_nova['nome']}** "
            f"(*{info_raridade_fossil['label']}*)!! 🦴✨"
        )
    if besta_nova_vencedor is not None:
        info_raridade_besta = _RARIDADES["bestas"]
        partes_desbloqueio.append(
            f"🐺⚡ **CONQUISTA!** A **{criatura_vencedora['nome']}** de {vencedor.display_name} chegou ao "
            f"**Nível de Capacidade máximo** e, como recompensa, {vencedor.display_name} desbloqueou "
            f"{info_raridade_besta['emoji']} **{besta_nova_vencedor['nome']}** "
            f"(*{info_raridade_besta['label']}*)!! 🐺⚡"
        )
    if besta_nova_perdedor is not None:
        info_raridade_besta = _RARIDADES["bestas"]
        partes_desbloqueio.append(
            f"🐺⚡ **CONQUISTA!** A **{criatura_perdedora['nome']}** de {perdedor.display_name} chegou ao "
            f"**Nível de Capacidade máximo** e, como recompensa, {perdedor.display_name} desbloqueou "
            f"{info_raridade_besta['emoji']} **{besta_nova_perdedor['nome']}** "
            f"(*{info_raridade_besta['label']}*)!! 🐺⚡"
        )
    if elemental_novo_vencedor is not None:
        info_raridade_elemental = _RARIDADES["elemental"]
        partes_desbloqueio.append(
            f"🌀⚡ **CONQUISTA!** A **{criatura_vencedora['nome']}** de {vencedor.display_name} chegou ao "
            f"**Nível de Capacidade `{_ELEMENTAL_NIVEL_DESBLOQUEIO}`** e, como recompensa, "
            f"{vencedor.display_name} desbloqueou {info_raridade_elemental['emoji']} "
            f"**{elemental_novo_vencedor['nome']}** (*{info_raridade_elemental['label']}*)!! 🌀⚡"
        )
    if elemental_novo_perdedor is not None:
        info_raridade_elemental = _RARIDADES["elemental"]
        partes_desbloqueio.append(
            f"🌀⚡ **CONQUISTA!** A **{criatura_perdedora['nome']}** de {perdedor.display_name} chegou ao "
            f"**Nível de Capacidade `{_ELEMENTAL_NIVEL_DESBLOQUEIO}`** e, como recompensa, "
            f"{perdedor.display_name} desbloqueou {info_raridade_elemental['emoji']} "
            f"**{elemental_novo_perdedor['nome']}** (*{info_raridade_elemental['label']}*)!! 🌀⚡"
        )
    if not partes_desbloqueio:
        partes_desbloqueio.append(
            f"🏅 **{vencedor.display_name}** já desbloqueou todas as criaturas normais existentes "
            "— só falta a sorte grande de alguma 🐉 Mítica agora!"
        )
    texto_desbloqueio = "\n\n".join(partes_desbloqueio)

    # ── Aviso de subida de Nível de Capacidade — vale pras duas criaturas,
    # a de quem venceu e a de quem perdeu, já que os dois "usaram" as suas. ──
    partes_nivel_criatura = []
    if nivel_novo_criatura_vencedora > nivel_antigo_criatura_vencedora:
        partes_nivel_criatura.append(
            f"📈 **{criatura_vencedora['nome']}** de {vencedor.display_name} ficou mais experiente "
            f"e subiu pro **⭐ Nível {nivel_novo_criatura_vencedora}**!"
        )
    if nivel_novo_criatura_perdedora > nivel_antigo_criatura_perdedora:
        partes_nivel_criatura.append(
            f"📈 **{criatura_perdedora['nome']}** de {perdedor.display_name} ficou mais experiente "
            f"e subiu pro **⭐ Nível {nivel_novo_criatura_perdedora}**!"
        )
    texto_nivel_criatura = ("\n\n" + "\n".join(partes_nivel_criatura)) if partes_nivel_criatura else ""

    # 🌟 Aviso de "cansaço" — se alguma das favoritas bateu o limite de usos
    # seguidos NESSA batalha, avisa que ela vai descansar e por quanto tempo.
    partes_favorita_cansada = []
    if cansou_favorita_vencedora:
        partes_favorita_cansada.append(
            f"😮‍💨 A favorita de **{vencedor.display_name}**, **{criatura_vencedora['nome']}**, cansou "
            f"depois de `{_FAVORITO_USOS_ATE_CANSAR}` usos seguidos! Vai descansar por "
            f"`{_FAVORITO_COOLDOWN_SEGUNDOS // 60} min` — as próximas batalhas voltam a sortear aleatoriamente."
        )
    if cansou_favorita_perdedora:
        partes_favorita_cansada.append(
            f"😮‍💨 A favorita de **{perdedor.display_name}**, **{criatura_perdedora['nome']}**, cansou "
            f"depois de `{_FAVORITO_USOS_ATE_CANSAR}` usos seguidos! Vai descansar por "
            f"`{_FAVORITO_COOLDOWN_SEGUNDOS // 60} min` — as próximas batalhas voltam a sortear aleatoriamente."
        )
    texto_favorita_cansada = ("\n\n" + "\n".join(partes_favorita_cansada)) if partes_favorita_cansada else ""

    # 🌀 Aviso de Booster de xp ativado — vale pra quem convocou um Elemental
    # nessa batalha, não importa se venceu ou perdeu (o booster já foi
    # concedido lá em cima, assim que os dois lados foram sorteados).
    partes_boost_elemental = []
    if boost_elemental_desafiante:
        partes_boost_elemental.append(
            f"🌀✨ **{desafiante.display_name}** convocou um Elemental e ativou um Booster de xp "
            f"(`x{_BAU_BOOSTER_MULTIPLICADOR}`, call e mensagem) por `{_ELEMENTAL_BOOSTER_MINUTOS} min`!"
        )
    if boost_elemental_desafiado:
        partes_boost_elemental.append(
            f"🌀✨ **{desafiado.display_name}** convocou um Elemental e ativou um Booster de xp "
            f"(`x{_BAU_BOOSTER_MULTIPLICADOR}`, call e mensagem) por `{_ELEMENTAL_BOOSTER_MINUTOS} min`!"
        )
    texto_boost_elemental = ("\n\n" + "\n".join(partes_boost_elemental)) if partes_boost_elemental else ""

    embed_resultado = discord.Embed(
        title="🏆 FIM DE BATALHA!",
        description=(
            f"**{criatura_vencedora['nome']}** `⭐ Nv.{nivel_novo_criatura_vencedora}` ({vencedor.mention}) derrota "
            f"**{criatura_perdedora['nome']}** `⭐ Nv.{nivel_novo_criatura_perdedora}` ({perdedor.mention})!\n\n"
            f"{texto_roubo}\n\n"
            f"{texto_desbloqueio}"
            f"{texto_nivel_criatura}"
            f"{texto_favorita_cansada}"
            f"{texto_boost_elemental}\n\n"
            f"{texto_placar}\n\n"
            f"🌑 **Aeon:** *inclina a cabeça* ...as sombras reconhecem o vencedor. 🖤🌑\n"
            f"🌟 **Celestia:** GG PRA GALERA!! 😭🌟🤍✨ *aplaude soltando faíscas douradas* FOI ÉPICO DEMAIS!!"
        ),
        color=0xf5c542,
        timestamp=discord.utils.utcnow(),
    )
    embed_resultado.set_thumbnail(url=vencedor.display_avatar.url)
    embed_resultado.set_footer(text="🌑 Aeon & ☀️ Celestia — Arena de Batalhas")
    msg_resultado = await canal.send(embed=embed_resultado)
    asyncio.create_task(_apagar_mensagem_depois(msg_resultado))

    # 📜 Log do RPG — só os ganhos orgânicos dessa batalha. Vale mesmo se uma
    # Vantagem foi usada nos bastidores: o log trata como uma vitória normal,
    # do mesmo jeito que o resto do bot já esconde isso do chat.
    partes_log = [
        f"⚔️ **{vencedor.display_name}** venceu **{perdedor.display_name}** num desafio "
        f"(**{criatura_vencedora['nome']}** vs **{criatura_perdedora['nome']}**)."
    ]
    if xp_roubado > 0:
        partes_log.append(
            f"💰 Saqueou **`{xp_roubado}` XP** (`{percentual * 100:.1f}%`) de **{perdedor.display_name}**."
        )
    if golpe_especial is not None:
        partes_log.append(f"{golpe_especial['emoji']} Golpe Especial: **{golpe_especial['nome']}**.")
    if criatura_nova is not None:
        info_r = _RARIDADES[criatura_nova["raridade"]]
        partes_log.append(
            f"🆕 **{vencedor.display_name}** desbloqueou {info_r['emoji']} **{criatura_nova['nome']}** "
            f"(*{info_r['label']}*)."
        )
    if criatura_mitica_nova is not None:
        info_r = _RARIDADES[criatura_mitica_nova["raridade"]]
        partes_log.append(
            f"🐉 **{vencedor.display_name}** desbloqueou o Mítico {info_r['emoji']} "
            f"**{criatura_mitica_nova['nome']}**!"
        )
    if criatura_fossil_nova is not None:
        info_r = _RARIDADES[criatura_fossil_nova["raridade"]]
        partes_log.append(
            f"🦴 **{vencedor.display_name}** desenterrou o Fóssil {info_r['emoji']} "
            f"**{criatura_fossil_nova['nome']}** (os dois estavam em call)!"
        )
    if besta_nova_vencedor is not None:
        partes_log.append(
            f"🐺 **{vencedor.display_name}** desbloqueou a Besta **{besta_nova_vencedor['nome']}** "
            "(Nível de Capacidade máximo)."
        )
    if besta_nova_perdedor is not None:
        partes_log.append(
            f"🐺 **{perdedor.display_name}** desbloqueou a Besta **{besta_nova_perdedor['nome']}** "
            "(Nível de Capacidade máximo)."
        )
    if elemental_novo_vencedor is not None:
        partes_log.append(
            f"🌀 **{vencedor.display_name}** desbloqueou o Elemental **{elemental_novo_vencedor['nome']}** "
            f"(Nível de Capacidade {_ELEMENTAL_NIVEL_DESBLOQUEIO})."
        )
    if elemental_novo_perdedor is not None:
        partes_log.append(
            f"🌀 **{perdedor.display_name}** desbloqueou o Elemental **{elemental_novo_perdedor['nome']}** "
            f"(Nível de Capacidade {_ELEMENTAL_NIVEL_DESBLOQUEIO})."
        )
    if boost_elemental_desafiante:
        partes_log.append(
            f"🌀✨ **{desafiante.display_name}** usou um Elemental e ganhou Booster de xp "
            f"(`x{_BAU_BOOSTER_MULTIPLICADOR}`) por {_ELEMENTAL_BOOSTER_MINUTOS} min."
        )
    if boost_elemental_desafiado:
        partes_log.append(
            f"🌀✨ **{desafiado.display_name}** usou um Elemental e ganhou Booster de xp "
            f"(`x{_BAU_BOOSTER_MULTIPLICADOR}`) por {_ELEMENTAL_BOOSTER_MINUTOS} min."
        )
    asyncio.create_task(_log_rpg(canal.guild, "⚔️ Batalha entre membros", "\n".join(partes_log)))


async def _processar_desafio(message: discord.Message) -> None:
    """Detecta 'eu te desafio @alguém' no chat e, se tudo certo, inicia a batalha."""
    if message.guild is None or message.author.bot:
        return
    if not message.mentions:
        return
    if not _BATALHA_REGEX.search(message.content or ""):
        return

    desafiante = message.author
    desafiado = next(
        (m for m in message.mentions if not m.bot and m.id != desafiante.id), None
    )

    if desafiado is None:
        await message.channel.send(
            "🌑 **Aeon:** ...não dá pra desafiar a si mesmo, nem um bot. "
            "As sombras não aceitam covardia. 🖤🌑"
        )
        return

    if message.channel.id in _batalha_canal_ativo:
        await message.channel.send(
            "🌟 **Celestia:** Calma, calma!! 😅🌸 Já tem uma batalha rolando por aqui, espera terminar!!"
        )
        return

    agora = time.time()
    ultimo = _batalha_ultimo_desafio.get(desafiante.id, 0)
    if agora - ultimo < _BATALHA_COOLDOWN_SEGUNDOS:
        restante = int(_BATALHA_COOLDOWN_SEGUNDOS - (agora - ultimo))
        await message.channel.send(
            f"🌑 **Aeon:** ...as sombras ainda descansam do último combate. "
            f"Espere mais `{restante}s` antes de desafiar de novo. 🖤🌑"
        )
        return

    guild = message.guild
    cargo_xp = guild.get_role(CARGO_XP_ID)
    if not cargo_xp or cargo_xp not in desafiante.roles or cargo_xp not in desafiado.roles:
        await message.channel.send(
            "🌟 **Celestia:** Pra batalhar valendo pontos, os dois precisam estar "
            "participando do ranking de nível!! 🌸✨"
        )
        return

    dados_desafiante = xp_stats[desafiante.id]
    dados_desafiado = xp_stats[desafiado.id]
    if dados_desafiante["xp"] <= 0 and dados_desafiado["xp"] <= 0:
        await message.channel.send(
            "🌑 **Aeon:** ...ninguém aqui tem XP suficiente pra valer a pena essa batalha ainda. 🖤🌑"
        )
        return

    _batalha_ultimo_desafio[desafiante.id] = agora
    _batalha_canal_ativo.add(message.channel.id)

    view = DesafioView(desafiante, desafiado)
    convite = await message.channel.send(
        embed=_embed_status_desafio(desafiante, desafiado, "pendente"), view=view
    )
    view.mensagem = convite
    asyncio.create_task(_apagar_mensagem_depois(convite))

# ══════════════════════════════════════════════════════════════════════


CANAL_CRIATURAS_ID = 1530569053280665660  # canal onde a coleção do .criaturas é SEMPRE enviada


@bot.command(name="criaturas")
async def cmd_criaturas(ctx, membro: discord.Member = None):
    """Mostra a coleção de criaturas desbloqueadas de alguém na Arena de
    Batalhas (ou de quem usou o comando, se ninguém for mencionado).
    A resposta é sempre jogada no canal CANAL_CRIATURAS_ID, não importa
    de onde o comando foi chamado.
    Uso: .criaturas [@alguém]"""
    alvo = membro or ctx.author
    desbloqueadas = set(_garantir_criaturas_iniciais(alvo.id))
    favorito_alvo = _favorito_status(alvo.id)

    if favorito_alvo["id"]:
        criatura_favorita = next((c for c in _BATALHA_CRIATURAS if c["id"] == favorito_alvo["id"]), None)
        nome_favorita = criatura_favorita["nome"] if criatura_favorita else favorito_alvo["id"]
        linha_favorito = (
            f"🌟 **Favorita atual:** {nome_favorita} "
            f"(`{favorito_alvo['usos']}/{_FAVORITO_USOS_ATE_CANSAR}` usos até cansar)"
        )
    elif favorito_alvo["cansacos"]:
        partes_descanso = []
        for cid, ate in favorito_alvo["cansacos"].items():
            c_cansada = next((c for c in _BATALHA_CRIATURAS if c["id"] == cid), None)
            nome_cansada = c_cansada["nome"] if c_cansada else cid
            partes_descanso.append(f"**{nome_cansada}** (`{_formatar_tempo_restante(ate - time.time())}`)")
        linha_favorito = (
            "😮‍💨 Descansando: " + ", ".join(partes_descanso) +
            " — mas dá pra favoritar outra criatura a qualquer momento com `.favorito <nome>`."
        )
    else:
        linha_favorito = "🌟 *Sem favorita ativa no momento — use `.favorito <nome>` pra escolher uma.*"

    embed = discord.Embed(
        title=f"📖 Coleção de Criaturas — {alvo.display_name}",
        description=(
            f"🔓 **{len(desbloqueadas)}/{len(_BATALHA_CRIATURAS)}** criaturas desbloqueadas até agora!\n"
            "Vença batalhas invocando as que faltam pra completar a coleção. ⚔️\n"
            "⭐ *O número ao lado do nome é o Nível de Capacidade dela — sobe até 10 "
            "quanto mais você invoca essa criatura em batalha.*\n\n"
            f"{linha_favorito}"
        ),
        color=0x9b59b6,
    )

    for raridade in _ORDEM_RARIDADES:
        info = _RARIDADES[raridade]
        linhas = []
        for c in _BATALHA_CRIATURAS:
            if c["raridade"] != raridade:
                continue
            if c["id"] in desbloqueadas:
                nivel = _nivel_criatura(alvo.id, c["id"])
                marcador = " 🌟" if favorito_alvo["id"] == c["id"] else ""
                linhas.append(f"🔓 {c['nome']} `⭐ Nv.{nivel}`{marcador}")
            else:
                linhas.append(f"🔒 {c['nome']}")
        if linhas:
            embed.add_field(name=f"{info['emoji']} {info['label']}", value="\n".join(linhas), inline=False)

    pets_desbloqueados = set(_pets_desbloqueados(alvo.id))
    pet_equipado_id = xp_stats[alvo.id].get("pet_equipado")
    linhas_pets = []
    for p in _PETS:
        if p["id"] in pets_desbloqueados:
            nivel_pet_atual = _nivel_pet(alvo.id, p["id"])
            marcador = " 🐾*(equipado)*" if p["id"] == pet_equipado_id else ""
            linhas_pets.append(f"🔓 {p['nome']} `⭐ Nv.{nivel_pet_atual}/{_PET_NIVEL_MAX}`{marcador}")
        else:
            linhas_pets.append(f"🔒 {p['nome']}")
    embed.add_field(
        name=f"🐾 Pets ({len(pets_desbloqueados)}/{len(_PETS)})",
        value=(
            "\n".join(linhas_pets) + "\n\n"
            "*Desbloqueados ao levar uma criatura 🔵 Rara até o Nível de Capacidade "
            f"`{_PET_NIVEL_DESBLOQUEIO}`. Equipe um com `.equiparpet <nome>` — eles dão bônus na "
            "chance de vencer Boss e ajudam a upar suas criaturas!*"
        ),
        inline=False,
    )

    embed.add_field(
        name="⚡ Golpes Especiais",
        value=(
            f"De vez em quando (`{_CHANCE_GOLPE_ESPECIAL * 100:.0f}%` de chance), no meio de um "
            "**\"eu te desafio @alguém\"**, a criatura vencedora solta um **Golpe Especial** — um ataque "
            "raro e nomeado (tipo 🌑 *Investida das Sombras* ou 🔥 *Chama Ancestral*) que turbina o saque "
            f"de XP daquela vitória pra entre `{_GOLPE_ESPECIAL_ROUBO_MIN * 100:.0f}%` e "
            f"`{_GOLPE_ESPECIAL_ROUBO_MAX * 100:.0f}%`, bem acima do normal!\n"
            "É sorte pura — qualquer criatura, de qualquer raridade ou nível, pode puxar um a qualquer momento. 🎲"
        ),
        inline=False,
    )

    embed.set_thumbnail(url=alvo.display_avatar.url)
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — confira também a 📖 Enciclopédia no canal de ranking")

    canal_destino = bot.get_channel(CANAL_CRIATURAS_ID)
    if canal_destino is None:
        # Canal não encontrado (bot fora do servidor certo, canal deletado etc.)
        # — cai pro canal onde o comando foi chamado, pra não perder a resposta.
        await ctx.send(embed=embed)
        return

    await canal_destino.send(embed=embed)
    if ctx.channel.id != canal_destino.id:
        await ctx.send(f"📖 Sua coleção foi enviada em {canal_destino.mention}!")


# ══════════════════════════════════════════════════════════════════════
# COMANDO .favorito — escolhe uma criatura favorita pras batalhas. Enquanto
# ela estiver ativa, é SEMPRE ela quem entra em campo (sem sorteio) — até
# cansar depois de _FAVORITO_USOS_ATE_CANSAR usos seguidos, quando então
# some por _FAVORITO_COOLDOWN_SEGUNDOS antes de poder ser favoritada de novo.
# ══════════════════════════════════════════════════════════════════════

_FAVORITO_PALAVRAS_REMOVER = {"remover", "limpar", "cancelar", "nenhum", "nenhuma", "tirar"}


@bot.command(name="favorito", aliases=["usarmonstro", "monstrofavorito"])
async def cmd_favorito(ctx, *, nome: str = None):
    """Define (ou consulta) sua criatura favorita pra batalhas.
    Uso:
      .favorito <nome da criatura>  → define a favorita (ela passa a entrar em TODA batalha sua)
      .favorito                     → mostra o status atual (favorita ativa ou tempo de cansaço restante)
      .favorito remover             → tira a favorita atual, sem precisar esperar ela cansar
    """
    autor = ctx.author
    favorito = _favorito_status(autor.id)

    # ── Sem argumento nenhum: só mostra o status atual ──────────────────
    if nome is None:
        if favorito["id"]:
            criatura_atual = next((c for c in _BATALHA_CRIATURAS if c["id"] == favorito["id"]), None)
            nome_atual = criatura_atual["nome"] if criatura_atual else favorito["id"]
            nivel_atual = _nivel_criatura(autor.id, favorito["id"])
            await ctx.send(
                f"🌟 **Celestia:** Sua favorita agora é **{nome_atual}** `⭐ Nv.{nivel_atual}`!! 😆✨ "
                f"Já foi usada `{favorito['usos']}/{_FAVORITO_USOS_ATE_CANSAR}` vezes seguidas até cansar."
            )
        elif favorito["cansacos"]:
            partes = []
            for cid, ate in favorito["cansacos"].items():
                c_cansada = next((c for c in _BATALHA_CRIATURAS if c["id"] == cid), None)
                nome_cansada = c_cansada["nome"] if c_cansada else cid
                partes.append(f"**{nome_cansada}** (`{_formatar_tempo_restante(ate - time.time())}`)")
            await ctx.send(
                "🌑 **Aeon:** ...você não tem favorita ativa agora. Descansando: "
                + ", ".join(partes) +
                ". 🖤🌑 Pode favoritar outra criatura a qualquer momento com `.favorito <nome>`."
            )
        else:
            await ctx.send(
                "🌟 **Celestia:** Você não tem nenhuma favorita agora — suas batalhas estão "
                "sorteando aleatoriamente!! Use `.favorito <nome da criatura>` pra escolher uma. 🌸✨"
            )
        return

    # ── Remover a favorita atual, sem precisar esperar cansar ───────────
    if _normalizar_texto(nome) in _FAVORITO_PALAVRAS_REMOVER:
        if not favorito["id"]:
            await ctx.send("🌟 **Celestia:** Você já não tinha nenhuma favorita ativa!! 🌸")
            return
        favorito["id"] = None
        favorito["usos"] = 0
        asyncio.create_task(_salvar_xp_stats())
        await ctx.send(
            "🌑 **Aeon:** ...favorita removida. As sombras voltam a sortear livremente nas suas batalhas. 🖤🌑"
        )
        return

    # ── Encontra a criatura pelo nome digitado ───────────────────────────
    criatura = _encontrar_criatura_por_nome(nome)
    if criatura is None:
        await ctx.send(
            f"⚠️ Não encontrei nenhuma criatura chamada `{nome}`. Confira o nome certinho com `.criaturas`."
        )
        return

    desbloqueadas = set(_garantir_criaturas_iniciais(autor.id))
    if criatura["id"] not in desbloqueadas:
        await ctx.send(
            f"🌟 **Celestia:** Você ainda não desbloqueou **{criatura['nome']}**!! 😅🌸 "
            "Só dá pra favoritar quem já tá na sua coleção — confira com `.criaturas`."
        )
        return

    # ── Só bloqueia se for JUSTO a criatura que ainda tá descansando — pode
    # trocar por QUALQUER OUTRA livremente, mesmo com essa ainda de castigo ──
    cansaco_ate = favorito["cansacos"].get(criatura["id"])
    if cansaco_ate is not None:
        restante = _formatar_tempo_restante(cansaco_ate - time.time())
        await ctx.send(
            f"🌑 **Aeon:** ...**{criatura['nome']}** ainda está descansando. Espere mais "
            f"`{restante}` antes de favoritá-la de novo — ou escolha outra com `.favorito <nome>`. 🖤🌑"
        )
        return

    favorito["id"] = criatura["id"]
    favorito["usos"] = 0
    asyncio.create_task(_salvar_xp_stats())

    info_raridade = _RARIDADES[criatura["raridade"]]
    nivel_atual = _nivel_criatura(autor.id, criatura["id"])
    await ctx.send(
        f"🌟 **Celestia:** PRONTO!! 😆✨ {info_raridade['emoji']} **{criatura['nome']}** `⭐ Nv.{nivel_atual}` "
        f"agora é sua favorita — ela vai entrar em TODA batalha sua a partir de agora, até usar "
        f"`{_FAVORITO_USOS_ATE_CANSAR}` vezes seguidas e precisar descansar!\n"
        f"🌑 **Aeon:** ...as sombras vão priorizá-la. Escolha bem. 🖤🌑"
    )


# ══════════════════════════════════════════════════════════════════════
# COMANDO .equiparpet — escolhe qual Pet fica ATIVO (equipado) pra dar
# suporte nas batalhas contra Boss. Só um Pet por vez; trocar de Pet NÃO
# zera o progresso de Nível dele (fica salvo por Pet, igual o Nível de
# Capacidade das criaturas) — só o Pet equipado no momento é quem soma o
# bônus de chance contra Boss e ajuda a upar criaturas.
# ══════════════════════════════════════════════════════════════════════

_PET_PALAVRAS_REMOVER = {"remover", "limpar", "cancelar", "nenhum", "nenhuma", "tirar", "desequipar"}


@bot.command(name="equiparpet", aliases=["pet", "usarpet", "meupet"])
async def cmd_equiparpet(ctx, *, nome: str = None):
    """Equipa (ou consulta) seu Pet ativo pras batalhas contra Boss.
    Uso:
      .equiparpet <nome do pet>  → equipa esse Pet (precisa já tê-lo desbloqueado)
      .equiparpet                → mostra o Pet equipado agora (ou sua lista de Pets, se nenhum)
      .equiparpet remover        → desequipa, sem trocar por outro
    """
    autor = ctx.author
    pets_possuidos = _pets_desbloqueados(autor.id)

    # ── Sem argumento nenhum: só mostra o status atual ───────────────────
    if nome is None:
        pet_atual = _obter_pet_equipado(autor.id)
        if pet_atual:
            nivel_atual = _nivel_pet(autor.id, pet_atual["id"])
            bonus = _pet_bonus_chance_boss(autor.id) * 100
            linha_habilidade = (
                f"✨ Habilidade **{pet_atual['habilidade_nome']}** já ativa!"
                if nivel_atual >= _PET_NIVEL_HABILIDADE
                else f"🔒 Habilidade **{pet_atual['habilidade_nome']}** destrava no Nível `{_PET_NIVEL_HABILIDADE}`."
            )
            await ctx.send(
                f"🐾 Seu Pet equipado agora é **{pet_atual['nome']}** `Nv.{nivel_atual}/{_PET_NIVEL_MAX}` — "
                f"soma `+{bonus:.1f}%` na chance de vencer Boss.\n{linha_habilidade}"
            )
        elif pets_possuidos:
            nomes = ", ".join(
                f"**{p['nome']}** `Nv.{_nivel_pet(autor.id, p['id'])}`"
                for p in _PETS if p["id"] in pets_possuidos
            )
            await ctx.send(
                f"🌟 **Celestia:** Você tem Pets, mas nenhum equipado agora!! 😅🌸 Seus Pets: {nomes}. "
                "Use `.equiparpet <nome>` pra escolher um!"
            )
        else:
            await ctx.send(
                "🌑 **Aeon:** ...você ainda não tem nenhum Pet. 🖤🐾 Leve uma criatura 🔵 Rara até o "
                f"Nível de Capacidade `{_PET_NIVEL_DESBLOQUEIO}` em batalhas — tem chance dela render um Pet de graça."
            )
        return

    # ── Desequipar, sem trocar por outro ──────────────────────────────
    if _normalizar_texto(nome) in _PET_PALAVRAS_REMOVER:
        dados = xp_stats[autor.id]
        if not dados.get("pet_equipado"):
            await ctx.send("🌟 **Celestia:** Você já não tinha nenhum Pet equipado!! 🌸")
            return
        dados["pet_equipado"] = None
        asyncio.create_task(_salvar_xp_stats())
        await ctx.send("🌑 **Aeon:** ...Pet desequipado. Nenhum bônus de suporte ativo agora. 🖤🐾")
        return

    # ── Equipar um Pet específico ─────────────────────────────────────
    pet = _encontrar_pet_por_nome(nome)
    if pet is None:
        await ctx.send(f"⚠️ Não encontrei nenhum Pet chamado `{nome}`. Confira o nome certinho.")
        return

    if pet["id"] not in pets_possuidos:
        await ctx.send(
            f"🌟 **Celestia:** Você ainda não desbloqueou **{pet['nome']}**!! 😅🌸 "
            "Só dá pra equipar Pets que já são seus."
        )
        return

    dados = xp_stats[autor.id]
    dados["pet_equipado"] = pet["id"]
    asyncio.create_task(_salvar_xp_stats())

    nivel_atual = _nivel_pet(autor.id, pet["id"])
    await ctx.send(
        f"🐾 **{pet['nome']}** `Nv.{nivel_atual}/{_PET_NIVEL_MAX}` equipado!! 😆✨ Ele vai te ajudar "
        "nas próximas batalhas contra Boss — vença ou perca, ele sobe de Nível junto com você."
    )


# ══════════════════════════════════════════════════════════════════════
# .darcriatura — comando interno, só o Reality (CRIADOR_ID) pode usar.
# Concede uma criatura específica (por nome) direto pra coleção de alguém,
# sem precisar passar por batalha nem sorteio. Útil pra corrigir coleção,
# testar raridades específicas ou repor algo perdido.
# De propósito NÃO aparece em nenhum lugar do help/ajuda.
# Uso (PV ou servidor): .darcriatura <nome da criatura> <ID do membro>
# Exemplo: .darcriatura Kraken do Abismo 769951556388257812
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="darcriatura")
async def cmd_darcriatura(ctx, *, texto: str = None):
    if ctx.author.id != CRIADOR_ID:
        return

    if texto is None:
        aviso = await ctx.send("⚠️ Uso: `.darcriatura <nome da criatura> <ID do membro>`")
        await _apagar_mensagem_depois(aviso, 15)
        return

    # O ID precisa ser o ÚLTIMO token da mensagem — tudo antes disso é o
    # nome da criatura (que pode ter espaço, acento, etc.).
    partes = texto.rsplit(" ", 1)
    if len(partes) != 2 or not partes[1].isdigit():
        aviso = await ctx.send(
            "⚠️ Uso: `.darcriatura <nome da criatura> <ID do membro>`\n"
            "O ID precisa vir por último, separado por espaço. "
            "Exemplo: `.darcriatura Kraken do Abismo 769951556388257812`"
        )
        await _apagar_mensagem_depois(aviso, 15)
        return

    nome_criatura, alvo_id_texto = partes
    alvo_id = int(alvo_id_texto)

    criatura = _encontrar_criatura_por_nome(nome_criatura)
    if criatura is None:
        aviso = await ctx.send(
            f"❌ Nenhuma criatura encontrada pra `{nome_criatura}` (ou o nome é ambíguo — "
            "tenta ser mais específico)."
        )
        await _apagar_mensagem_depois(aviso, 15)
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    alvo = guild.get_member(alvo_id) if guild else None
    if alvo is None and guild:
        try:
            alvo = await guild.fetch_member(alvo_id)
        except discord.NotFound:
            alvo = None
    alvo_nome = alvo.display_name if alvo else str(alvo_id)

    dados = xp_stats[alvo_id]
    dados.setdefault("criaturas", [])
    info_raridade = _RARIDADES[criatura["raridade"]]

    if criatura["id"] in dados["criaturas"]:
        aviso = await ctx.send(
            f"⚠️ `{alvo_nome}` já tem {info_raridade['emoji']} **{criatura['nome']}** — nada mudou."
        )
        await _apagar_mensagem_depois(aviso, 15)
        return

    dados["criaturas"].append(criatura["id"])
    asyncio.create_task(_salvar_xp_stats())

    confirmacao = await ctx.send(
        f"✅ {info_raridade['emoji']} **{criatura['nome']}** (*{info_raridade['label']}*) concedida "
        f"pra `{alvo_nome}` (`{alvo_id}`)."
    )
    await _apagar_mensagem_depois(confirmacao, 15)


# ══════════════════════════════════════════════════════════════════════
# .uparcriatura — comando interno, só o Reality (CRIADOR_ID) pode usar.
# Sobe em 1 o Nível de Capacidade da criatura favorita/equipada de alguém
# (a mesma lógica de _calcular_nivel_criatura / _NIVEL_CRIATURA_USOS_ACUMULADOS
# usada pelo resto do sistema — só que "empurrando" os usos direto pro
# limiar do próximo nível, em vez de esperar batalhas de verdade).
# De propósito NÃO aparece em nenhum lugar do help/ajuda.
# Uso (PV ou servidor): .uparcriatura <ID ou @membro>
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="uparcriatura")
async def cmd_uparcriatura(ctx, alvo_id: int = None):
    if ctx.author.id != CRIADOR_ID:
        return

    if alvo_id is None and ctx.message.mentions:
        alvo_id = ctx.message.mentions[0].id
    if alvo_id is None:
        aviso = await ctx.send("⚠️ Uso: `.uparcriatura <ID ou @membro>`")
        await _apagar_mensagem_depois(aviso, 15)
        return

    criatura = _obter_criatura_favorita_ativa(alvo_id)
    if criatura is None:
        aviso = await ctx.send(f"❌ `{alvo_id}` não tem criatura favorita/equipada no momento.")
        await _apagar_mensagem_depois(aviso, 15)
        return

    criatura_id = criatura["id"]
    teto = _nivel_criatura_max(criatura_id)
    nivel_atual = _nivel_criatura(alvo_id, criatura_id)

    if nivel_atual >= teto:
        aviso = await ctx.send(f"⚠️ `{criatura['nome']}` já está no nível máximo (`{teto}`).")
        await _apagar_mensagem_depois(aviso, 15)
        return

    tabela = (
        _NIVEL_CRIATURA_USOS_ACUMULADOS_ESTENDIDO
        if criatura_id in _NIVEL_CRIATURA_MAX_ESPECIAL
        else _NIVEL_CRIATURA_USOS_ACUMULADOS
    )
    dados = xp_stats[alvo_id]
    dados.setdefault("usos_criaturas", {})
    dados["usos_criaturas"][criatura_id] = max(
        dados["usos_criaturas"].get(criatura_id, 0),
        tabela[nivel_atual],   # limiar de usos mínimos pro PRÓXIMO nível
    )
    nivel_novo = _calcular_nivel_criatura(dados["usos_criaturas"][criatura_id], criatura_id)
    asyncio.create_task(_salvar_xp_stats())

    confirmacao = await ctx.send(f"✅ `{criatura['nome']}` (`{alvo_id}`) → Nível `{nivel_novo}`.")
    await _apagar_mensagem_depois(confirmacao, 15)


# ══════════════════════════════════════════════════════════════════════
# BAÚ — evento de recompensa surpresa
# Comando .bau (só o Reality/CRIADOR_ID pode ativar) joga um baú com botão
# no canal _BAU_CANAL_ID. A PRIMEIRA pessoa que clicar leva o prêmio: na
# maioria das vezes um % de XP a mais (sorteado entre 1% e 20% do XP atual
# dela); mais raro um booster de 5 minutos que DOBRA o xp ganho em call e
# em mensagem nesse período; e, RARÍSSIMO (o prêmio mais difícil de todos),
# uma criatura de raridade 🌌 Secreta — a única forma de conseguir uma.
#
# .baumimic joga um baú visualmente IDÊNTICO, mas que é, na verdade, um
# Mimic disfarçado: quem clicar primeiro cai numa armadilha e PERDE entre
# _BAU_MIMIC_XP_MIN e _BAU_MIMIC_XP_MAX do XP dela, em vez de ganhar algo.
# ══════════════════════════════════════════════════════════════════════

_BAU_GIF = "https://static2.klipy.com/ii/d7aec6f6f171607374b2065c836f92f4/be/e0/WQOIGADT.gif"
_BAU_CANAL_ID = 1284257046740602901  # mesmo canal do chat geral (_XP_CANAL_1)

_BAU_CHANCE_SECRETO = 0.08    # 8% de chance — ainda o prêmio mais raro do baú (o booster é 15%), uma criatura 🌌 Secreta
_BAU_CHANCE_BOOSTER = 0.15    # 15% de chance de sair o booster
_BAU_XP_MIN = 0.01            # 1%  — mínimo de xp que o dado pode sortear
_BAU_XP_MAX = 0.20            # 20% — máximo de xp que o dado pode sortear
_BAU_XP_TETO = 800            # teto máximo de XP por baú — evita que rank alto dispare
                                # cada vez mais na frente do rank baixo.
_BAU_BOOSTER_MINUTOS = 5
_BAU_BOOSTER_MULTIPLICADOR = 2

_BAU_MIMIC_GIF = "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/c105ac18-b254-4cb1-9e1d-eb83be6b6939/df17unu-65c15ff8-39f7-4a3a-b865-14090f46e4c5.gif?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgiOiIvZi9jMTA1YWMxOC1iMjU0LTRjYjEtOWUxZC1lYjgzYmU2YjY5MzkvZGYxN3VudS02NWMxNWZmOC0zOWY3LTRhM2EtYjg2NS0xNDA5MGY0NmU0YzUuZ2lmIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXX0.QfbOzXs4HatDKEoHtYg_R2SEZ_jSZkyFVCO7Bq9t8S8"
_BAU_MIMIC_XP_MIN = 0.01      # 1%  — perda mínima de xp se o baú for um Mimic
_BAU_MIMIC_XP_MAX = 0.20      # 20% — perda máxima de xp se o baú for um Mimic

_XP_BOOSTER_DATA_FILE = os.path.join(_ANJO_DATA_DIR, "xp_booster_data.json")

_xp_booster_ate: dict = {}    # user_id -> time.time() de quando o booster de xp em dobro expira


def _carregar_xp_booster_stats() -> None:
    """Carrega os boosters de xp em dobro (baú/boss/.darbosster) salvos em
    disco, se existirem. Roda antes do bot conectar — é isso que permite um
    booster ainda ativo sobreviver a um reinício do bot, em vez de sumir na
    hora. Boosters que já expiraram durante o tempo em que o bot ficou fora
    do ar são simplesmente ignorados (a checagem `time.time() < ate` já
    cuida disso sozinha)."""
    if not os.path.exists(_XP_BOOSTER_DATA_FILE):
        return
    try:
        with open(_XP_BOOSTER_DATA_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        agora = time.time()
        for uid_str, ate in dados.get("ate", {}).items():
            if ate > agora:   # não vale a pena carregar o que já expirou
                _xp_booster_ate[int(uid_str)] = ate
    except (json.JSONDecodeError, OSError, ValueError):
        pass


async def _salvar_xp_booster_stats() -> None:
    """Salva os boosters de xp em dobro em disco de forma atômica (escreve em
    .tmp e substitui) — pra não perder o progresso quando o bot reiniciar."""
    dados = {
        "ate": {str(uid): ate for uid, ate in _xp_booster_ate.items()},
    }
    tmp_path = _XP_BOOSTER_DATA_FILE + ".tmp"

    def _escrever():
        os.makedirs(_ANJO_DATA_DIR, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, _XP_BOOSTER_DATA_FILE)

    try:
        loop = asyncio.get_event_loop()
        async with (_xp_stats_lock or asyncio.Lock()):
            await loop.run_in_executor(None, _escrever)
    except OSError:
        pass


def _conceder_xp_booster(user_id: int, minutos: float) -> None:
    """Concede (ou ESTENDE) o Booster de xp em dobro de alguém. Se a pessoa já
    tiver um ativo, soma `minutos` em cima do tempo que ainda resta, em vez de
    resetar pro valor cheio — assim dá pra empilhar vários boosters seguidos
    (baú, boss, .darbosster...) sem perder o que já tava rolando."""
    agora = time.time()
    inicio = max(agora, _xp_booster_ate.get(user_id, 0))
    _xp_booster_ate[user_id] = inicio + minutos * 60
    asyncio.create_task(_salvar_xp_booster_stats())


# Carrega os boosters de xp em dobro salvos em disco (baú/boss/.darbosster) —
# só é possível chamar aqui porque a função já foi definida acima.
_carregar_xp_booster_stats()


# ══════════════════════════════════════════════════════════════════════
# .darbosster — comando interno, só o Reality (CRIADOR_ID) pode usar.
# Dá o Booster de xp (o mesmo prêmio raro do Baú: xp de call E de mensagem
# em dobro por _BAU_BOOSTER_MINUTOS minutos) direto pra alguém, sem precisar
# esperar o baú sortear. De propósito NÃO aparece em nenhum lugar do help.
# Uso (PV ou servidor): .darbosster <ID ou @membro>
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="darbosster")
async def cmd_darbosster(ctx, alvo_id: int = None):
    if ctx.author.id != CRIADOR_ID:
        return

    if alvo_id is None and ctx.message.mentions:
        alvo_id = ctx.message.mentions[0].id
    if alvo_id is None:
        aviso = await ctx.send("⚠️ Uso: `.darbosster <ID ou @membro>`")
        await _apagar_mensagem_depois(aviso, 15)
        return

    _conceder_xp_booster(alvo_id, _BAU_BOOSTER_MINUTOS)
    _empilhar_call_booster(alvo_id)

    confirmacao = await ctx.send(
        f"✅ Booster de xp (`x{_BAU_BOOSTER_MULTIPLICADOR}`, call e mensagem) empilhado pra "
        f"`{alvo_id}` por mais `{_BAU_BOOSTER_MINUTOS} min` — e o Booster de Call dela também "
        f"subiu +1 nível em cima do que já tinha."
    )
    await _apagar_mensagem_depois(confirmacao, 15)


# ══════════════════════════════════════════════════════════════════════
# .bostercall — comando interno, só o Reality (CRIADOR_ID) pode usar.
# Igual o .darbosster, mas em massa: dá o Booster de xp (o mesmo prêmio raro
# do Baú, x2 em call E mensagem por _BAU_BOOSTER_MINUTOS minutos) + 1 nível
# de Booster de Call pra TODO MUNDO que estiver, agora, dentro do canal de
# voz indicado. De propósito NÃO aparece em nenhum lugar do help.
# Uso (PV ou servidor): .bostercall <ID do canal de voz>
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="bostercall")
async def cmd_bostercall(ctx, canal_id: int = None):
    if ctx.author.id != CRIADOR_ID:
        return

    if canal_id is None:
        aviso = await ctx.send("⚠️ Uso: `.bostercall <ID do canal de voz>`")
        await _apagar_mensagem_depois(aviso, 15)
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    canal_voz = guild.get_channel(canal_id) if guild else None
    if canal_voz is None:
        canal_voz = bot.get_channel(canal_id)

    if canal_voz is None or not isinstance(canal_voz, (discord.VoiceChannel, discord.StageChannel)):
        aviso = await ctx.send(f"❌ Não achei nenhum canal de voz com o ID `{canal_id}`.")
        await _apagar_mensagem_depois(aviso, 15)
        return

    membros = [m for m in canal_voz.members if not m.bot]
    if not membros:
        aviso = await ctx.send(f"⚠️ Não tem ninguém (sem contar bots) em **{canal_voz.name}** agora.")
        await _apagar_mensagem_depois(aviso, 15)
        return

    for membro in membros:
        _conceder_xp_booster(membro.id, _BAU_BOOSTER_MINUTOS)
        _empilhar_call_booster(membro.id)

    nomes = ", ".join(f"`{m.display_name}`" for m in membros)
    confirmacao = await ctx.send(
        f"✅ Booster de xp (`x{_BAU_BOOSTER_MULTIPLICADOR}`, call e mensagem) empilhado por mais "
        f"`{_BAU_BOOSTER_MINUTOS} min` pra todo mundo em **{canal_voz.name}** "
        f"(`{len(membros)}` pessoa{'s' if len(membros) != 1 else ''}) — e o Booster de Call de "
        f"cada um também subiu +1 nível em cima do que já tinha.\n{nomes}"
    )
    await _apagar_mensagem_depois(confirmacao, 30)


# ══════════════════════════════════════════════════════════════════════
# .vantagem — comando interno, só o Reality (CRIADOR_ID) pode usar.
# Marca alguém pra GANHAR garantido a PRÓXIMA batalha (.desafio) que ela
# participar, seja como desafiante ou desafiada — pula o sorteio normal de
# vitória e o de roubo de XP: ela vence na hora e saqueia entre
# _VANTAGEM_ROUBO_MIN e _VANTAGEM_ROUBO_MAX (20% a 30%) garantido de XP da
# outra pessoa.
# A Vantagem fica "guardada" até a próxima batalha de verdade acontecer
# (não expira sozinha) e é consumida (removida) nesse momento.
# De propósito NÃO aparece em nenhum lugar do help/ajuda.
# Uso (PV ou servidor): .vantagem <ID ou @membro>
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="vantagem")
async def cmd_vantagem(ctx, alvo_id: int = None):
    if ctx.author.id != CRIADOR_ID:
        return

    if alvo_id is None and ctx.message.mentions:
        alvo_id = ctx.message.mentions[0].id
    if alvo_id is None:
        aviso = await ctx.send("⚠️ Uso: `.vantagem <ID ou @membro>`")
        await _apagar_mensagem_depois(aviso, 15)
        return

    _vantagem_ativa.add(alvo_id)

    confirmacao = await ctx.send(
        f"🍀✨ Vantagem concedida pra `{alvo_id}` — ela vai vencer garantido a próxima batalha que "
        f"participar, e vai saquear entre `{_VANTAGEM_ROUBO_MIN * 100:.0f}%` e "
        f"`{_VANTAGEM_ROUBO_MAX * 100:.0f}%` de XP garantido da outra pessoa."
    )
    await _apagar_mensagem_depois(confirmacao, 15)


# ══════════════════════════════════════════════════════════════════════
# .vantagemfossio — comando interno, só o Reality (CRIADOR_ID) pode usar.
# Parecida com .vantagem (vitória garantida), com 3 diferenças:
#   1. Só destrava numa batalha em que desafiante e desafiado estejam os
#      dois na MESMA call no momento do combate. Se a próxima batalha dela
#      rolar sem os dois em call juntos, a Vantagem fica pendente e não é
#      gasta — espera uma batalha em que a condição bata.
#   2. Rouba entre _VANTAGEM_FOSSIO_ROUBO_MIN e _MAX de XP (10% a 20%,
#      faixa própria, mais baixa que a do .vantagem normal).
#   3. Garante o desenterro de um 🦴 Fóssil nessa vitória também (pulando
#      o sorteio de _FOSSIL_CHANCE_DESBLOQUEIO), se ainda sobrar algum
#      Fóssil pra quem venceu destravar.
# Usa exatamente o mesmo texto de resultado/log de sempre — ninguém no
# chat consegue perceber que a batalha foi arranjada.
# De propósito NÃO aparece em nenhum lugar do help/ajuda.
# Uso (PV ou servidor): .vantagemfossio <ID ou @membro>
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="vantagemfossio")
async def cmd_vantagemfossio(ctx, alvo_id: int = None):
    if ctx.author.id != CRIADOR_ID:
        return

    if alvo_id is None and ctx.message.mentions:
        alvo_id = ctx.message.mentions[0].id
    if alvo_id is None:
        aviso = await ctx.send("⚠️ Uso: `.vantagemfossio <ID ou @membro>`")
        await _apagar_mensagem_depois(aviso, 15)
        return

    _vantagem_fossio_ativa.add(alvo_id)

    confirmacao = await ctx.send(
        f"🍀📞 Vantagem (call) concedida pra `{alvo_id}` — ela vai vencer garantido a próxima "
        f"batalha em que ela e a outra pessoa estiverem juntas numa call, vai saquear entre "
        f"`{_VANTAGEM_FOSSIO_ROUBO_MIN * 100:.0f}%` e `{_VANTAGEM_FOSSIO_ROUBO_MAX * 100:.0f}%` de "
        f"XP garantido da outra pessoa, e ainda desenterra um 🦴 Fóssil garantido (se sobrar algum "
        f"pra ela). Se não estiverem em call, essa batalha segue o sorteio normal e a Vantagem "
        f"continua guardada."
    )
    await _apagar_mensagem_depois(confirmacao, 15)


class BauView(discord.ui.View):
    """View do baú — só a PRIMEIRA pessoa que clicar leva o prêmio; quem
    clicar depois disso só recebe um aviso de que já foi levado.

    `forcar_secreto=True` é usado pelo .bausecreto: o visual e o texto são
    IDÊNTICOS ao baú normal (mesmo título, mesma descrição, mesmo gif) — só
    que quem clicar primeiro leva garantidamente uma criatura 🌌 Secreta
    ainda não desbloqueada, sem precisar do sorteio de _BAU_CHANCE_SECRETO.

    `forcar_mimic=True` é usado pelo .baumimic: visual e texto também
    IDÊNTICOS ao baú normal ANTES de abrir (é um Mimic disfarçado, ninguém
    pode desconfiar!) — mas quem clicar primeiro cai numa armadilha e PERDE
    entre _BAU_MIMIC_XP_MIN e _BAU_MIMIC_XP_MAX do XP dela, em vez de ganhar."""

    def __init__(self, forcar_secreto: bool = False, forcar_mimic: bool = False):
        super().__init__(timeout=None)
        self.aberto = False
        self.forcar_secreto = forcar_secreto
        self.forcar_mimic = forcar_mimic

    @discord.ui.button(label="🔓 Abrir o Baú", style=discord.ButtonStyle.success, custom_id="bau_abrir")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.aberto:
            await interaction.response.send_message(
                "🌑 **Aeon:** ...tarde demais. Alguém já levou. 🖤🌑", ephemeral=True
            )
            return
        self.aberto = True

        membro = interaction.user
        dados = xp_stats[membro.id]
        dados.setdefault("criaturas", [])

        imagem_resultado = _BAU_GIF

        if self.forcar_mimic:
            # 👹 Era um Mimic disfarçado o tempo todo — em vez de prêmio,
            # rouba um % do XP atual da pessoa (entre _BAU_MIMIC_XP_MIN e
            # _BAU_MIMIC_XP_MAX). Não passa por nenhum outro sorteio.
            percentual = random.uniform(_BAU_MIMIC_XP_MIN, _BAU_MIMIC_XP_MAX)
            perda = max(1, round(dados["xp"] * percentual))
            dados["xp"] = max(0, dados["xp"] - perda)
            dados["nivel"], _, _ = _calcular_nivel(dados["xp"])
            imagem_resultado = _BAU_MIMIC_GIF
            texto_premio = (
                f"👹💥 **ERA UM MIMIC!!** {membro.mention} abriu o baú e ele MOSTROU OS DENTES — "
                f"em vez de prêmio, levou uma mordida de **`-{perda}` XP** (`{percentual * 100:.1f}%`)! "
                "Que golpe de sorte ruim... 😨"
            )

            asyncio.create_task(_salvar_xp_stats())
            asyncio.create_task(_atualizar_ranking_xp())

            for item in self.children:
                item.disabled = True

            embed_resultado = discord.Embed(
                title="👹 Era um Mimic!!",
                description=texto_premio,
                color=0xaa2e2e,
                timestamp=discord.utils.utcnow(),
            )
            embed_resultado.set_image(url=imagem_resultado)
            embed_resultado.set_footer(text="🌑 Aeon & ☀️ Celestia — Baú do Tesouro")
            await interaction.response.edit_message(embed=embed_resultado, view=self)
            self.stop()
            return

        # 🌌 Prêmio mais raro de todos: uma criatura Secreta ainda não
        # desbloqueada. Se a pessoa já tiver as 6, cai pro sorteio normal
        # (booster/xp) em vez de travar sem ter mais nada pra dar — mesmo
        # no .bausecreto, que só GARANTE o secreto quando ainda sobra algum.
        _secretos_faltando = [
            c for c in _BATALHA_CRIATURAS
            if c["raridade"] == "secreto" and c["id"] not in dados["criaturas"]
        ]

        sai_secreto = bool(_secretos_faltando) and (self.forcar_secreto or random.random() < _BAU_CHANCE_SECRETO)

        if sai_secreto:
            criatura_secreta = random.choice(_secretos_faltando)
            dados["criaturas"].append(criatura_secreta["id"])
            info_raridade_secreta = _RARIDADES["secreto"]
            imagem_resultado = criatura_secreta["gif"]
            texto_premio = (
                f"🌌✨ **PRÊMIO RARÍSSIMO!!** {membro.mention} encontrou algo que quase ninguém acha... "
                f"{info_raridade_secreta['emoji']} **{criatura_secreta['nome']}** "
                f"(*{info_raridade_secreta['label']}*) foi desbloqueada e entrou pra sua coleção!! "
                f"Use `.criaturas` pra conferir. 🌌"
            )
        elif random.random() < _BAU_CHANCE_BOOSTER:
            # ── Prêmio raro: booster de 5 min que dobra xp de call e mensagem ──
            _conceder_xp_booster(membro.id, _BAU_BOOSTER_MINUTOS)
            texto_premio = (
                f"⚡✨ **PRÊMIO RARÍSSIMO!!** {membro.mention} ativou um **Booster de XP** — "
                f"pelos próximos `{_BAU_BOOSTER_MINUTOS} minutos`, todo xp de call e de mensagem vem "
                f"em **dobro**! ⚡✨"
            )
        else:
            percentual = random.uniform(_BAU_XP_MIN, _BAU_XP_MAX)
            nivel_antigo = dados["nivel"]
            ganho = max(5, round(dados["xp"] * percentual))
            ganho = min(ganho, _BAU_XP_TETO)
            dados["xp"] += ganho
            dados["nivel"], _, _ = _calcular_nivel(dados["xp"])
            texto_premio = (
                f"💰 O baú sorteou **`{percentual * 100:.1f}%`**! {membro.mention} ganhou **`{ganho}` XP**!"
            )
            if dados["nivel"] > nivel_antigo and interaction.guild is not None:
                asyncio.create_task(_anunciar_level_up(interaction.guild, membro, dados["nivel"]))

        asyncio.create_task(_salvar_xp_stats())
        asyncio.create_task(_atualizar_ranking_xp())

        for item in self.children:
            item.disabled = True

        embed_resultado = discord.Embed(
            title="🪙 Baú Aberto!",
            description=texto_premio,
            color=0xf5c542,
            timestamp=discord.utils.utcnow(),
        )
        embed_resultado.set_image(url=imagem_resultado)
        embed_resultado.set_footer(text="🌑 Aeon & ☀️ Celestia — Baú do Tesouro")
        await interaction.response.edit_message(embed=embed_resultado, view=self)

        # 📜 Log do RPG — ganho orgânico do baú (secreto, booster ou XP).
        titulo_log = "🌌 Baú secreto — prêmio garantido" if self.forcar_secreto else "🪙 Baú aberto"
        asyncio.create_task(_log_rpg(interaction.guild, titulo_log, texto_premio))

        self.stop()


def _montar_embed_bau() -> discord.Embed:
    """Monta o embed de anúncio do baú — usado tanto pelo .bau normal quanto
    pelo .bausecreto, propositalmente IDÊNTICO nos dois, pra quem estiver no
    chat não conseguir diferenciar um do outro só de olhar."""
    embed = discord.Embed(
        title="🪙 Um Baú Apareceu!",
        description=(
            "🌟 **Celestia:** AAAAA UM BAÚ MISTERIOSO!! 😱✨ *pula em volta dele* Quem clicar primeiro "
            "LEVA O PRÊMIO!!\n"
            "🌑 **Aeon:** ...corram. As sombras não esperam por ninguém. 🖤🌑\n\n"
            f"🎁 Prêmio: entre `{_BAU_XP_MIN * 100:.0f}%` e `{_BAU_XP_MAX * 100:.0f}%` de XP a mais — "
            f"mais raro, um **Booster de {_BAU_BOOSTER_MINUTOS} min** que dobra o xp de call e de "
            "mensagem — e, raríssimo mesmo, uma criatura de raridade 🌌 **Secreta** direto pra coleção!"
        ),
        color=0xf5c542,
    )
    embed.set_image(url=_BAU_GIF)
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Baú do Tesouro")
    return embed


@bot.command(name="bau")
async def cmd_bau(ctx):
    """Joga um baú de recompensa no canal do chat geral — a primeira pessoa
    que clicar no botão leva o prêmio. Só o Reality pode usar. A própria
    mensagem do comando some logo em seguida. Uso: .bau"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BAU_CANAL_ID)
    if canal is None:
        return

    await canal.send(embed=_montar_embed_bau(), view=BauView())


@bot.command(name="bausecreto")
async def cmd_bausecreto(ctx):
    """Joga um baú IDÊNTICO ao .bau normal (mesmo visual, mesmo texto,
    ninguém no chat consegue diferenciar) — mas quem clicar primeiro leva
    GARANTIDAMENTE uma criatura 🌌 Secreta ainda não desbloqueada (a não
    ser que já tenha as 6, aí cai no sorteio normal do baú). Só o Reality
    pode usar. Uso: .bausecreto"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BAU_CANAL_ID)
    if canal is None:
        return

    await canal.send(embed=_montar_embed_bau(), view=BauView(forcar_secreto=True))


@bot.command(name="baumimic")
async def cmd_baumimic(ctx):
    """Joga um baú IDÊNTICO ao .bau normal (mesmo visual, mesmo texto,
    ninguém no chat consegue diferenciar) — mas é, na verdade, um Mimic
    disfarçado: quem clicar primeiro cai numa armadilha e PERDE entre
    `_BAU_MIMIC_XP_MIN` e `_BAU_MIMIC_XP_MAX` (até 20%) do XP dela, em vez
    de ganhar. Só o Reality pode usar. Uso: .baumimic"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BAU_CANAL_ID)
    if canal is None:
        return

    await canal.send(embed=_montar_embed_bau(), view=BauView(forcar_mimic=True))


# ══════════════════════════════════════════════════════════════════════
# BOSS — o Dragão do Caos
# Comando .boss (só o Reality/CRIADOR_ID pode ativar) invoca uma fera
# mítica gigantesca no canal _BOSS_CANAL_ID. O chat escolhe entre encarar
# sozinho (bem arriscado, só 5% de chance) ou chamar todo mundo pra lutar
# junto (mais gente = mais chance, mas ainda é um boss difícil de verdade).
# Cada pessoa convoca a criatura mais forte que já tem desbloqueada. Quem
# vence ganha entre 20% e 60% de XP a mais; quem perde não perde NADA —
# só o gostinho amargo da derrota. Todas as mensagens do evento somem
# sozinhas depois de 1 minuto.
# ══════════════════════════════════════════════════════════════════════

# ⚠️ Esse gif é um link temporário do CDN do Discord (parâmetros ?ex=...),
# que expira sozinho depois de um tempo (geralmente ~24h-48h). Se ele
# parar de aparecer no embed, pegue um link novo (clique direito na
# imagem no Discord > Copiar link) e troque aqui embaixo — ou, melhor
# ainda, suba o gif num host permanente (imgur, ibb.co etc.) pra nunca
# mais precisar trocar.
_BOSS_DRAGAO_CAOS_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1529955698690228294/gif-ezgif.com-optimize.gif?ex=6a63d1c7&is=6a628047&hm=7ce47d57d6827c7b60f48d9bb849950abdfe7893b460ef32a5a6755650ecc065"

_BOSS_CANAL_ID = 1284257046740602901   # mesmo canal do chat geral (_XP_CANAL_1) — só aparece aqui

_BOSS_TEMPO_ESCOLHA      = 60   # segundos pra decidir "todos juntos" ou "sozinho"
_BOSS_TEMPO_RECRUTAMENTO = 10   # segundos pra galera clicar "quero participar" depois de "todos juntos"

_BOSS_CHANCE_SOLO = 0.05   # 5% — enfrentar sozinho é quase suicídio

# Batalha em grupo: começa numa base baixa, sobe um pouco por participante
# e um pouco mais conforme a raridade das criaturas convocadas — mas nunca
# passa de _BOSS_CHANCE_GRUPO_MAX, pra continuar sendo um boss difícil
# mesmo com o servidor inteiro batalhando junto.
_BOSS_CHANCE_GRUPO_BASE      = 0.12
_BOSS_CHANCE_GRUPO_MAX       = 0.70
_BOSS_BONUS_POR_PARTICIPANTE = 0.035
_BOSS_BONUS_RARIDADE_CRIATURA = {
    "comum": 0.0, "raro": 0.02, "epico": 0.035, "lendario": 0.06, "fosseis": 0.075, "secreto": 0.09, "mitico": 0.12,
}

_BOSS_XP_GANHO_MIN = 0.20   # 20% — mínimo de XP que quem vence pode ganhar
_BOSS_XP_GANHO_MAX = 0.60   # 60% — máximo de XP que quem vence pode ganhar
_BOSS_XP_GANHO_SEM_XP = (30, 80)   # recompensa fixa pra quem ainda não tem XP acumulado
_BOSS_XP_GANHO_TETO = 3000   # teto máximo de XP por vitória — evita que rank alto dispare
                              # cada vez mais na frente do rank baixo. Ajuste esse número pra
                              # combinar com o nível mais alto real do seu servidor.

_boss_ativo_no_canal: set = set()   # channel_id -> impede 2 boss ao mesmo tempo no mesmo canal


def _boss_criatura_mais_forte(user_id: int) -> dict:
    """Retorna a criatura de MAIOR raridade que essa pessoa já desbloqueou —
    é ela que a pessoa convoca pra lutar contra o boss."""
    desbloqueadas = set(_garantir_criaturas_iniciais(user_id))
    for raridade in _ORDEM_RARIDADES:   # já vem do mais raro pro mais comum
        candidatas = [c for c in _BATALHA_CRIATURAS if c["raridade"] == raridade and c["id"] in desbloqueadas]
        if candidatas:
            return random.choice(candidatas)
    # segurança: nunca deveria cair aqui, todo mundo tem ao menos as Comuns
    return random.choice([c for c in _BATALHA_CRIATURAS if c["raridade"] == "comum"])


def _boss_chance_grupo(convocacoes: list) -> float:
    """Calcula a chance de vitória do grupo: base + um bônus por pessoa +
    um bônus pela raridade de cada criatura convocada, sempre travado no
    teto de _BOSS_CHANCE_GRUPO_MAX pra continuar sendo um boss difícil."""
    chance = _BOSS_CHANCE_GRUPO_BASE + len(convocacoes) * _BOSS_BONUS_POR_PARTICIPANTE
    for membro, criatura in convocacoes:
        chance += _BOSS_BONUS_RARIDADE_CRIATURA.get(criatura["raridade"], 0.0)
        chance += _pet_bonus_chance_boss(membro.id)   # 🐾 bônus do Pet equipado (2% a 5%, + habilidade)
    chance += _pet_bonus_grupo_extra([m for m, _c in convocacoes])   # 🐾 habilidade de grupo (Aeon e Celestia)
    return min(chance, _BOSS_CHANCE_GRUPO_MAX)


def _boss_calcular_ganho_xp(user_id: int) -> tuple:
    """Sorteia quanto de XP essa pessoa ganha por vencer o boss: entre 20%
    e 60% do XP que ela já tem — travado num teto máximo (_BOSS_XP_GANHO_TETO)
    pra não deixar quem já é rank alto disparar cada vez mais na frente —
    ou uma recompensa fixa se ainda não tiver XP nenhum acumulado (pra
    ninguém sair de mãos vazias)."""
    dados = xp_stats[user_id]
    xp_atual = dados.get("xp", 0)
    if xp_atual > 0:
        percentual = random.uniform(_BOSS_XP_GANHO_MIN, _BOSS_XP_GANHO_MAX)
        ganho = max(1, round(xp_atual * percentual))
        ganho = min(ganho, _BOSS_XP_GANHO_TETO)
    else:
        percentual = 0.0
        ganho = random.randint(*_BOSS_XP_GANHO_SEM_XP)
    return ganho, percentual


async def _boss_premiar_vencedores(guild: discord.Guild, vencedores: list) -> list:
    """Aplica o ganho de XP de cada vencedor, atualiza nível e dispara o
    aviso de level up quando for o caso. Devolve uma lista de (membro,
    ganho, percentual) pra montar o texto de resultado."""
    resultados = []
    for membro in vencedores:
        dados = xp_stats[membro.id]
        nivel_antigo = dados["nivel"]
        ganho, percentual = _boss_calcular_ganho_xp(membro.id)
        dados["xp"] += ganho
        dados["nivel"], _, _ = _calcular_nivel(dados["xp"])
        if dados["nivel"] > nivel_antigo and guild is not None:
            asyncio.create_task(_anunciar_level_up(guild, membro, dados["nivel"]))
        resultados.append((membro, ganho, percentual))

    asyncio.create_task(_salvar_xp_stats())
    asyncio.create_task(_atualizar_ranking_xp())

    for membro, ganho, percentual in resultados:
        asyncio.create_task(_log_rpg(
            guild,
            "🐉 Recompensa — Dragão do Caos",
            f"✨ **{membro.display_name}** ganhou **`{ganho}` XP** (`{percentual * 100:.1f}%`) "
            "por vencer o Dragão do Caos.",
        ))

    return resultados


async def _boss_batalha_solo(canal: discord.TextChannel, membro: discord.Member) -> None:
    """Roda o confronto solo contra o Dragão do Caos: só 5% de chance de
    vitória — e se perder, não perde XP nenhum, só o orgulho."""
    try:
        criatura = _boss_criatura_mais_forte(membro.id)
        info_raridade = _RARIDADES[criatura["raridade"]]

        embed_convocacao = discord.Embed(
            title="🗡️ Um desafiante solitário se apresenta!",
            description=(
                f"🌑 **Aeon:** ...{membro.mention} decidiu enfrentar o Dragão do Caos sozinho. "
                f"Coragem ou loucura — as sombras ainda não sabem dizer. 🖤🐉\n"
                f"🌟 **Celestia:** {membro.display_name} convoca {info_raridade['emoji']} "
                f"**{criatura['nome']}**!! Boa sorte, vai precisar de muita!! 😳🌟✨"
            ),
            color=info_raridade["cor"],
        )
        embed_convocacao.set_thumbnail(url=criatura["gif"])
        msg1 = await canal.send(embed=embed_convocacao)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        await asyncio.sleep(3)

        aviso = await canal.send("🐉💥 *O Dragão do Caos ruge e avança sobre o desafiante...* 💥🐉")
        await asyncio.sleep(2.5)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        venceu = random.random() < (_BOSS_CHANCE_SOLO + _pet_bonus_chance_boss(membro.id))
        notas_pet = await _pet_pos_boss_grupo(canal.guild, [membro], venceu)   # 🐾 sobe o Pet, chance de upar criatura...

        if venceu:
            resultados = await _boss_premiar_vencedores(canal.guild, [membro])
            _, ganho, percentual = resultados[0]
            descricao = (
                f"🏆 **INACREDITÁVEL!!** {membro.mention} e {info_raridade['emoji']} **{criatura['nome']}** "
                f"derrubaram o **Dragão do Caos** sozinhos!! Só 5% de chance e AINDA ASSIM conseguiram!! 🐉💥\n\n"
                f"✨ Recompensa: **`+{ganho}` XP** (`{percentual * 100:.1f}%`)\n\n"
                f"🌑 **Aeon:** ...impossível. E ainda assim, aconteceu. As sombras se curvam. 🖤🌑\n"
                f"🌟 **Celestia:** EU NÃO ACREDITO NO QUE EU VI!!! 😭🌟🤍✨ LENDA VIVA!!!"
            )
            cor = 0xf5c542
        else:
            descricao = (
                f"💀 O **Dragão do Caos** foi forte demais — {info_raridade['emoji']} **{criatura['nome']}** caiu "
                f"em batalha, e {membro.mention} não conseguiu sozinho dessa vez.\n\n"
                f"🍃 Nenhum XP foi perdido — só a derrota amarga mesmo.\n\n"
                f"🌑 **Aeon:** ...era esperado. Poucos sobrevivem à ousadia sozinhos. 🖤🌑\n"
                f"🌟 **Celestia:** Não desanima!! 🌸😢 Da próxima, chama a galera pra ir junto!!"
            )
            cor = 0x8b0000

        if notas_pet:
            descricao += f"\n\n{notas_pet}"

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="🌑 Aeon & ☀️ Celestia — O Dragão do Caos")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


def _boss_cards_criaturas(convocacoes: list) -> list:
    """Monta um mini-embed pra CADA criatura convocada, com miniatura (igual
    ao que acontece no desafio solo) — assim dá pra ver o time inteiro de
    verdade, não só os nomes em texto. Discord aceita até 10 embeds por
    mensagem, então isso é enviado em lotes de 10 quando o grupo é grande."""
    cards = []
    for membro, criatura in convocacoes:
        info = _RARIDADES[criatura["raridade"]]
        card = discord.Embed(
            description=f"{info['emoji']} **{membro.display_name}** convoca **{criatura['nome']}** (*{info['label']}*)",
            color=info["cor"],
        )
        card.set_thumbnail(url=criatura["gif"])
        cards.append(card)
    return cards


async def _boss_batalha_grupo(canal: discord.TextChannel, participantes: list) -> None:
    """Roda o confronto em grupo contra o Dragão do Caos: cada participante
    convoca a criatura mais forte que já desbloqueou, e a chance de vitória
    cresce com o número (e a força) das criaturas convocadas."""
    try:
        convocacoes = [(p, _boss_criatura_mais_forte(p.id)) for p in participantes]

        embed_cabecalho = discord.Embed(
            title=f"⚔️ {len(convocacoes)} guerreiro(a)s entram em campo!",
            description="🌟 **Celestia:** OLHA SÓ ESSE TIME!! 😱🌟✨ Vai ser INTENSO!!",
            color=0xff4444,
        )
        cards = _boss_cards_criaturas(convocacoes)

        # 1º lote: cabeçalho + até 9 cards (10 embeds é o limite do Discord por
        # mensagem). O resto (grupos grandes) sai em mensagens seguintes.
        lote = [embed_cabecalho] + cards[:9]
        restante = cards[9:]
        msg1 = await canal.send(embeds=lote)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        while restante:
            msg_extra = await canal.send(embeds=restante[:10])
            asyncio.create_task(_apagar_mensagem_depois(msg_extra))
            restante = restante[10:]
        await asyncio.sleep(3)

        aviso = await canal.send("🐉💥 *O Dragão do Caos solta um rugido ensurdecedor e avança...* 💥🐉")
        await asyncio.sleep(2.5)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        chance = _boss_chance_grupo(convocacoes)
        venceu = random.random() < chance

        if venceu:
            resultados = await _boss_premiar_vencedores(canal.guild, participantes)
            texto_ganhos = "\n".join(
                f"✨ {membro.mention} +`{ganho}` XP (`{percentual * 100:.1f}%`)"
                for membro, ganho, percentual in resultados
            )
            descricao = (
                f"🏆 **VITÓRIA!!** O time de `{len(participantes)}` guerreiro(a)s derrubou o "
                f"**Dragão do Caos**!! (chance da batalha: `{chance * 100:.0f}%`) 🐉💥\n\n"
                f"{texto_ganhos}\n\n"
                f"🌑 **Aeon:** ...juntos, as sombras não têm chance contra vocês. 🖤🌑\n"
                f"🌟 **Celestia:** EQUIPE DOS SONHOS!!! 😭🌟🤍✨ VOCÊS ARRASARAM DEMAIS!!"
            )
            cor = 0xf5c542
        else:
            mencoes = ", ".join(p.mention for p in participantes)
            descricao = (
                f"💀 Mesmo com `{len(participantes)}` guerreiro(a)s juntos (`{chance * 100:.0f}%` de chance), "
                f"o **Dragão do Caos** foi forte demais dessa vez. {mencoes} não conseguiram.\n\n"
                f"🍃 Ninguém perdeu XP — só a derrota amarga mesmo.\n\n"
                f"🌑 **Aeon:** ...nem sempre a união é suficiente. As sombras respeitam a tentativa. 🖤🌑\n"
                f"🌟 **Celestia:** Vamos tentar de novo da próxima vez!! 🌸💫 Vocês foram corajosos!!"
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="🌑 Aeon & ☀️ Celestia — O Dragão do Caos")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


class BossRecrutamentoView(discord.ui.View):
    """Botão único de 'Quero Participar!' que fica ativo por
    _BOSS_TEMPO_RECRUTAMENTO segundos, juntando o time que vai enfrentar o
    boss em conjunto. Quando o tempo acaba, a batalha começa sozinha."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS_TEMPO_RECRUTAMENTO)
        self.canal = canal
        self.participantes: dict = {}   # user_id -> discord.Member
        self.mensagem: discord.Message = None

    @discord.ui.button(label="⚔️ Quero Participar!", style=discord.ButtonStyle.success)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if interaction.user.id in self.participantes:
            await interaction.response.send_message(
                "🌟 **Celestia:** Você já tá na lista, guerreiro(a)!! 😆🌸", ephemeral=True
            )
            return

        self.participantes[interaction.user.id] = interaction.user
        button.label = f"⚔️ Quero Participar! ({len(self.participantes)})"
        await interaction.response.edit_message(view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.mensagem:
                await self.mensagem.edit(view=self)
        except discord.HTTPException:
            pass

        participantes = list(self.participantes.values())
        if not participantes:
            try:
                msg = await self.canal.send(
                    "🌑 **Aeon:** ...ninguém teve coragem de se juntar a tempo. "
                    "O Dragão do Caos ruge e desaparece de volta nas sombras. 🖤🐉"
                )
                asyncio.create_task(_apagar_mensagem_depois(msg))
            finally:
                _boss_ativo_no_canal.discard(self.canal.id)
            return

        asyncio.create_task(_boss_batalha_grupo(self.canal, participantes))


class BossEscolhaView(discord.ui.View):
    """Botões de 'Todos Juntos' e 'Eu Consigo Sozinho' que aparecem quando o
    Dragão do Caos surge. A PRIMEIRA escolha feita (por qualquer pessoa)
    decide o caminho dessa aparição do boss."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS_TEMPO_ESCOLHA)
        self.canal = canal
        self.decidido = False
        self.mensagem: discord.Message = None

    def _travar_botoes(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="🤝 Todos Juntos", style=discord.ButtonStyle.primary)
    async def todos_juntos(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "🌑 **Aeon:** ...essa decisão já foi tomada. 🖤🌑", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🤝 O CHAMADO FOI FEITO!",
            description=(
                f"🌟 **Celestia:** {interaction.user.mention} decidiu enfrentar o Dragão do Caos "
                f"EM GRUPO!! 😱🌟✨\n"
                f"🌑 **Aeon:** ...quem tiver coragem, clique no botão abaixo. `{_BOSS_TEMPO_RECRUTAMENTO}s` "
                f"pra se juntar ao time. 🖤🐉"
            ),
            color=0xff8800,
        )
        embed.set_image(url=_BOSS_DRAGAO_CAOS_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        view_recrutamento = BossRecrutamentoView(self.canal)
        msg_recrutamento = await self.canal.send(
            "🐉 Time contra o **Dragão do Caos** — clique pra participar!",
            view=view_recrutamento,
        )
        view_recrutamento.mensagem = msg_recrutamento
        asyncio.create_task(_apagar_mensagem_depois(msg_recrutamento))

    @discord.ui.button(label="🗡️ Eu Consigo Sozinho", style=discord.ButtonStyle.danger)
    async def sozinho(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "🌑 **Aeon:** ...essa decisão já foi tomada. 🖤🌑", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🗡️ DESAFIO SOLITÁRIO ACEITO!",
            description=(
                f"🌑 **Aeon:** ...{interaction.user.mention} escolheu enfrentar o Dragão do Caos "
                f"sozinho. Coragem, ou loucura. 🖤🐉\n"
                f"🌟 **Celestia:** SÓ 5% DE CHANCE?! 😰🌟 Boa sorte, vai precisar de MUITA!!"
            ),
            color=0xff4444,
        )
        embed.set_image(url=_BOSS_DRAGAO_CAOS_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        asyncio.create_task(_boss_batalha_solo(self.canal, interaction.user))

    async def on_timeout(self):
        if self.decidido or self.mensagem is None:
            return
        self._travar_botoes()
        try:
            embed = discord.Embed(
                title="🐉 O Dragão do Caos se foi...",
                description=(
                    "🌑 **Aeon:** ...ninguém teve coragem de decidir a tempo. As sombras engolem "
                    "o dragão de volta... por enquanto. 🖤🐉"
                ),
                color=0x888888,
            )
            await self.mensagem.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass
        _boss_ativo_no_canal.discard(self.canal.id)


@bot.command(name="boss")
async def cmd_boss(ctx):
    """🐉 Invoca o Dragão do Caos no canal do chat geral — só o Reality
    (CRIADOR_ID) pode chamar. O chat escolhe entre encarar sozinho (5% de
    chance) ou juntar um time (mais gente = mais chance, mas ainda é um
    boss bem difícil). Uso: .boss"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BOSS_CANAL_ID)
    if canal is None:
        return

    if canal.id in _boss_ativo_no_canal:
        aviso = await ctx.send(
            "🌟 **Celestia:** Já tem um Dragão do Caos ativo por lá!! Espera esse terminar!! 😅🌸"
        )
        asyncio.create_task(_apagar_mensagem_depois(aviso))
        return

    _boss_ativo_no_canal.add(canal.id)

    embed = discord.Embed(
        title="🐉 UM BOSS APARECEU!!",
        description=(
            "🌑 **Aeon:** ...as sombras se rasgam. Algo antigo, furioso e imenso acaba de acordar. "
            "**O Dragão do Caos** chegou. 🖤🐉\n\n"
            "🌟 **Celestia:** AAAAAA CORRE TODO MUNDO!! 😱🌟🔥 ...ou fica e enfrenta!! Será que "
            "vocês são capazes de encará-lo sozinhos, ou só na base do trabalho em equipe?? "
            "Escolham com cuidado — ele é BEM difícil!! ✨\n\n"
            f"⏳ Vocês têm `{_BOSS_TEMPO_ESCOLHA}s` pra decidir."
        ),
        color=0x8b0000,
    )
    embed.set_image(url=_BOSS_DRAGAO_CAOS_GIF)
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Ameaça no Horizonte")

    view = BossEscolhaView(canal)
    msg = await canal.send(embed=embed, view=view)
    view.mensagem = msg
    asyncio.create_task(_apagar_mensagem_depois(msg))



# ══════════════════════════════════════════════════════════════════════
# OVO — recompensa manual por vencer o Dragão do Caos
# Comando `.ovo <ID ou @membro>` (só o Reality/CRIADOR_ID pode usar) dá um
# 🥚 ovo pendente pra alguém. O ovo choca sozinho quando a pessoa acumular
# `_OVO_TEMPO_CHOCAR_SEGUNDOS` numa call — não precisa ser de uma vez só,
# o tempo soma mesmo se ela sair e voltar depois. Ao chocar, sai uma
# criatura aleatória (mesma lógica de recompensa das batalhas: prioriza
# uma que ela ainda não tem, ponderada por raridade, nunca Mítica) e o
# nascimento é anunciado no canal `_OVO_CANAL_ID`.
# ⚠️ `_ovos_pendentes` fica só em memória (igual o booster do baú) — um
# reinício do bot perde os ovos ainda chocando.
# ══════════════════════════════════════════════════════════════════════

_OVO_CANAL_ID = _XP_CANAL_1              # 1284257046740602901 — onde o nascimento é anunciado
_OVO_TEMPO_CHOCAR_SEGUNDOS = 5 * 60      # 5 minutos acumulados numa call pra chocar
_OVO_CHECAGEM_INTERVALO_SEGUNDOS = 20    # de quanto em quanto tempo confere quem já bateu a meta

# user_id -> {"tempo_acumulado": float, "entrou_em": float|None}
_ovos_pendentes: dict = {}


def _ovo_tempo_atual(user_id: int) -> float:
    """Tempo total (já acumulado + sessão em andamento, se houver) que essa
    pessoa já passou numa call desde que ganhou o ovo pendente."""
    ovo = _ovos_pendentes.get(user_id)
    if ovo is None:
        return 0.0
    total = ovo["tempo_acumulado"]
    if ovo["entrou_em"] is not None:
        total += time.time() - ovo["entrou_em"]
    return total


def _ovo_iniciar_contagem(user_id: int) -> None:
    """Chamada quando alguém com ovo pendente entra numa call — marca o
    início da sessão atual (se não tiver uma já rodando)."""
    ovo = _ovos_pendentes.get(user_id)
    if ovo is not None and ovo["entrou_em"] is None:
        ovo["entrou_em"] = time.time()


def _ovo_pausar_contagem(user_id: int) -> None:
    """Chamada quando alguém com ovo pendente sai da call — soma o tempo
    dessa sessão no acumulado e pausa a contagem até ela voltar."""
    ovo = _ovos_pendentes.get(user_id)
    if ovo is not None and ovo["entrou_em"] is not None:
        ovo["tempo_acumulado"] += time.time() - ovo["entrou_em"]
        ovo["entrou_em"] = None


async def _ovo_chocar(user_id: int) -> None:
    """Choca o ovo dessa pessoa: sorteia e concede uma criatura nova pra
    coleção dela, e anuncia no canal _OVO_CANAL_ID."""
    _ovos_pendentes.pop(user_id, None)

    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])
    _nao_possuidas = [
        c for c in _BATALHA_CRIATURAS
        if c["id"] not in dados["criaturas"] and c["raridade"] not in ("mitico", "secreto", "fosseis", "bestas", "elemental")
    ]
    pool = _nao_possuidas or [c for c in _BATALHA_CRIATURAS if c["raridade"] not in ("mitico", "secreto", "fosseis", "bestas", "elemental")]
    pesos = [_RARIDADES[c["raridade"]]["peso"] for c in pool]
    criatura_nascida = random.choices(pool, weights=pesos, k=1)[0]
    if criatura_nascida["id"] not in dados["criaturas"]:
        dados["criaturas"].append(criatura_nascida["id"])
    asyncio.create_task(_salvar_xp_stats())

    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return
    canal = guild.get_channel(_OVO_CANAL_ID)
    if canal is None:
        return

    membro = guild.get_member(user_id)
    mencao = membro.mention if membro else f"<@{user_id}>"
    info_raridade = _RARIDADES[criatura_nascida["raridade"]]

    embed = discord.Embed(
        title="🥚✨ O Ovo Chocou!",
        description=(
            f"🌟 **Celestia:** AAAAA {mencao} SEU OVO CHOCOU!! 😍🌸✨ *pula de alegria* "
            "Depois de tanto tempo na call, olha só quem nasceu...\n"
            f"🌑 **Aeon:** ...{info_raridade['emoji']} **{criatura_nascida['nome']}** "
            f"(*{info_raridade['label']}*). As sombras aprovam. 🖤🌑\n\n"
            "Use `.criaturas` pra conferir sua coleção. 📖"
        ),
        color=info_raridade["cor"],
        timestamp=discord.utils.utcnow(),
    )
    embed.set_thumbnail(url=criatura_nascida["gif"])
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Incubadora de Ovos")
    await canal.send(embed=embed)

    # 📜 Log do RPG — o ovo em si é presente manual do Reality (não logado),
    # mas o CHOCO é um evento automático (tempo acumulado em call) e conta
    # como ganho orgânico da pessoa.
    asyncio.create_task(_log_rpg(
        guild,
        "🥚 Ovo chocou",
        f"🥚 O ovo de **{membro.display_name if membro else user_id}** chocou, revelando "
        f"{info_raridade['emoji']} **{criatura_nascida['nome']}** (*{info_raridade['label']}*).",
    ))


@tasks.loop(seconds=_OVO_CHECAGEM_INTERVALO_SEGUNDOS)
async def loop_checar_ovos():
    """Roda a cada _OVO_CHECAGEM_INTERVALO_SEGUNDOS: confere se algum ovo
    pendente já bateu a meta de tempo em call — assim ele choca na hora,
    sem precisar esperar a pessoa sair da call pra descobrir."""
    for user_id in list(_ovos_pendentes.keys()):
        try:
            if _ovo_tempo_atual(user_id) >= _OVO_TEMPO_CHOCAR_SEGUNDOS:
                await _ovo_chocar(user_id)
        except Exception as e:
            print(f"[ovo] ERRO ao chocar ovo de {user_id}: {e!r}")


@bot.command(name="ovo")
async def cmd_ovo(ctx, alvo_id: int = None):
    """Dá um 🥚 ovo pendente pra alguém — recompensa por vencer o Dragão
    do Caos. O ovo choca sozinho quando a pessoa acumular
    `_OVO_TEMPO_CHOCAR_SEGUNDOS` numa call. Só o Reality pode usar.
    Uso: .ovo <ID ou @membro>"""
    if ctx.author.id != CRIADOR_ID:
        return

    if alvo_id is None and ctx.message.mentions:
        alvo_id = ctx.message.mentions[0].id
    if alvo_id is None:
        await ctx.send("⚠️ **Uso correto:** `.ovo <ID ou @membro>`")
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    membro = guild.get_member(alvo_id) if guild else None
    if membro is None and guild:
        try:
            membro = await guild.fetch_member(alvo_id)
        except discord.NotFound:
            await ctx.send(f"❌ Membro com ID `{alvo_id}` não encontrado no servidor.")
            return

    _ovos_pendentes[alvo_id] = {"tempo_acumulado": 0.0, "entrou_em": None}
    # Se a pessoa já estiver numa call agora mesmo, a contagem já começa valendo.
    if membro is not None and membro.voice is not None and membro.voice.channel is not None:
        _ovo_iniciar_contagem(alvo_id)

    mencao = membro.mention if membro else f"`{alvo_id}`"
    await ctx.send(
        f"🐉💥 **Venceu do Dragão!** {mencao} agora tem direito a um **🥚 ovo aleatório**!! "
        f"Fique `{_OVO_TEMPO_CHOCAR_SEGUNDOS // 60} min` numa call pra ele chocar — "
        "o tempo soma mesmo se você sair e voltar depois."
    )


# ══════════════════════════════════════════════════════════════════════
# OVO DE DRAGÃO — igual ao .ovo normal, mas o ovo aqui é garantidamente
# um 🐉 Dragão (raridade mítica). Mesmíssima mecânica: `.ovodragao <ID ou
# @membro>` (só o Reality/CRIADOR_ID pode usar) dá o ovo pendente, a pessoa
# precisa acumular `_OVO_DRAGAO_TEMPO_CHOCAR_SEGUNDOS` numa call (o tempo
# soma mesmo saindo e voltando) e, ao chocar, nasce um dragão aleatório
# (prioriza um que ela ainda não tem). Tudo é anunciado no chat geral
# (`_OVO_DRAGAO_CANAL_ID`) — inclusive a entrega do ovo, com uma introdução
# mais épica que o ovo comum.
# ⚠️ `_ovos_dragao_pendentes` também fica só em memória — um reinício do
# bot perde os ovos de dragão ainda chocando.
# ══════════════════════════════════════════════════════════════════════

# Pool de dragões: todas as criaturas cujo id começa com "dragao_" — hoje
# são todas raridade mítica, mas o filtro é por id pra já valer
# automaticamente se algum dragão novo for adicionado no futuro.
_DRAGOES_DISPONIVEIS = [c for c in _BATALHA_CRIATURAS if c["id"].startswith("dragao_")]

_OVO_DRAGAO_CANAL_ID = _XP_CANAL_1                  # mesmo canal do chat geral — onde tudo é anunciado
_OVO_DRAGAO_TEMPO_CHOCAR_SEGUNDOS = 5 * 60          # 5 minutos acumulados numa call pra chocar
_OVO_DRAGAO_CHECAGEM_INTERVALO_SEGUNDOS = 20        # de quanto em quanto tempo confere quem já bateu a meta

# user_id -> {"tempo_acumulado": float, "entrou_em": float|None}
_ovos_dragao_pendentes: dict = {}


def _ovo_dragao_tempo_atual(user_id: int) -> float:
    """Tempo total (já acumulado + sessão em andamento, se houver) que essa
    pessoa já passou numa call desde que ganhou o ovo de dragão pendente."""
    ovo = _ovos_dragao_pendentes.get(user_id)
    if ovo is None:
        return 0.0
    total = ovo["tempo_acumulado"]
    if ovo["entrou_em"] is not None:
        total += time.time() - ovo["entrou_em"]
    return total


def _ovo_dragao_iniciar_contagem(user_id: int) -> None:
    """Chamada quando alguém com ovo de dragão pendente entra numa call —
    marca o início da sessão atual (se não tiver uma já rodando)."""
    ovo = _ovos_dragao_pendentes.get(user_id)
    if ovo is not None and ovo["entrou_em"] is None:
        ovo["entrou_em"] = time.time()


def _ovo_dragao_pausar_contagem(user_id: int) -> None:
    """Chamada quando alguém com ovo de dragão pendente sai da call — soma
    o tempo dessa sessão no acumulado e pausa a contagem até ela voltar."""
    ovo = _ovos_dragao_pendentes.get(user_id)
    if ovo is not None and ovo["entrou_em"] is not None:
        ovo["tempo_acumulado"] += time.time() - ovo["entrou_em"]
        ovo["entrou_em"] = None


async def _ovo_dragao_chocar(user_id: int) -> None:
    """Choca o ovo de dragão dessa pessoa: sorteia um 🐉 dragão (prioriza
    um que ela ainda não tem) pra coleção dela, e anuncia no chat geral."""
    _ovos_dragao_pendentes.pop(user_id, None)

    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])
    _dragoes_nao_possuidos = [
        c for c in _DRAGOES_DISPONIVEIS if c["id"] not in dados["criaturas"]
    ]
    pool = _dragoes_nao_possuidos or _DRAGOES_DISPONIVEIS
    pesos = [_RARIDADES[c["raridade"]]["peso"] for c in pool]
    dragao_nascido = random.choices(pool, weights=pesos, k=1)[0]
    if dragao_nascido["id"] not in dados["criaturas"]:
        dados["criaturas"].append(dragao_nascido["id"])
    asyncio.create_task(_salvar_xp_stats())

    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return
    canal = guild.get_channel(_OVO_DRAGAO_CANAL_ID)
    if canal is None:
        return

    membro = guild.get_member(user_id)
    mencao = membro.mention if membro else f"<@{user_id}>"
    info_raridade = _RARIDADES[dragao_nascido["raridade"]]

    embed = discord.Embed(
        title="🐉🥚 O Ovo do Dragão Chocou!",
        description=(
            f"🌟 **Celestia:** AAAAAAA {mencao} ELE CHOCOU!! 😍🌟✨ *gira em faíscas douradas* "
            "A espera valeu CADA segundo... olha só o que estava dormindo ali dentro...\n"
            f"🌑 **Aeon:** ...{info_raridade['emoji']} **{dragao_nascido['nome']}** "
            f"(*{info_raridade['label']}*). Um dragão reconhece outro guerreiro. As sombras se curvam. 🖤🐉\n\n"
            "Use `.criaturas` pra conferir sua coleção. 📖"
        ),
        color=info_raridade["cor"],
        timestamp=discord.utils.utcnow(),
    )
    embed.set_thumbnail(url=dragao_nascido["gif"])
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Incubadora de Dragões")
    await canal.send(embed=embed)


@tasks.loop(seconds=_OVO_DRAGAO_CHECAGEM_INTERVALO_SEGUNDOS)
async def loop_checar_ovos_dragao():
    """Roda a cada _OVO_DRAGAO_CHECAGEM_INTERVALO_SEGUNDOS: confere se
    algum ovo de dragão pendente já bateu a meta de tempo em call — assim
    ele choca na hora, sem precisar esperar a pessoa sair da call."""
    for user_id in list(_ovos_dragao_pendentes.keys()):
        try:
            if _ovo_dragao_tempo_atual(user_id) >= _OVO_DRAGAO_TEMPO_CHOCAR_SEGUNDOS:
                await _ovo_dragao_chocar(user_id)
        except Exception as e:
            print(f"[ovodragao] ERRO ao chocar ovo de dragão de {user_id}: {e!r}")


@bot.command(name="ovodragao", aliases=["ovodragão"])
async def cmd_ovodragao(ctx, alvo_id: int = None):
    """Dá um 🐉🥚 ovo de dragão pendente pra alguém. Igual ao .ovo normal,
    mas o que nasce é garantidamente um dragão. Anuncia a entrega no chat
    geral com uma introdução épica. Só o Reality pode usar.
    Uso: .ovodragao <ID ou @membro>"""
    if ctx.author.id != CRIADOR_ID:
        return

    if alvo_id is None and ctx.message.mentions:
        alvo_id = ctx.message.mentions[0].id
    if alvo_id is None:
        await ctx.send("⚠️ **Uso correto:** `.ovodragao <ID ou @membro>`")
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    membro = guild.get_member(alvo_id) if guild else None
    if membro is None and guild:
        try:
            membro = await guild.fetch_member(alvo_id)
        except discord.NotFound:
            await ctx.send(f"❌ Membro com ID `{alvo_id}` não encontrado no servidor.")
            return

    _ovos_dragao_pendentes[alvo_id] = {"tempo_acumulado": 0.0, "entrou_em": None}
    # Se a pessoa já estiver numa call agora mesmo, a contagem já começa valendo.
    if membro is not None and membro.voice is not None and membro.voice.channel is not None:
        _ovo_dragao_iniciar_contagem(alvo_id)

    mencao = membro.mention if membro else f"<@{alvo_id}>"
    minutos = _OVO_DRAGAO_TEMPO_CHOCAR_SEGUNDOS // 60

    embed_intro = discord.Embed(
        title="🐉🥚 Um Ovo Lendário Surgiu...",
        description=(
            "**DIANTE DE INÚMERAS BATALHAS, UM OVO CAIU SOBRE SUAS MÃOS.**\n\n"
            f"🌑 **Aeon:** ...{mencao}. As sombras sentiram o peso disso antes mesmo de acontecer. 🖤🐉 "
            "Algo ancestral dorme aí dentro — e não é uma criatura qualquer.\n\n"
            f"🌟 **Celestia:** UM OVO DE DRAGÃO PRA {mencao}!! 😍🌟✨ *gira sem parar* "
            f"Fique `{minutos} min` numa call pra ele chocar — o tempo soma mesmo que você "
            "saia e volte depois!! Boa sorte, guerreiro(a)!! 🌸🐉"
        ),
        color=_RARIDADES["mitico"]["cor"],
        timestamp=discord.utils.utcnow(),
    )
    embed_intro.set_footer(text="🌑 Aeon & ☀️ Celestia — Incubadora de Dragões")

    canal_geral = guild.get_channel(_OVO_DRAGAO_CANAL_ID) if guild else None
    if canal_geral is not None:
        await canal_geral.send(embed=embed_intro)

    # Se o comando foi usado fora do chat geral (ex.: no PV, como o .ovo normal),
    # manda uma confirmação simples pro Reality também.
    if canal_geral is None or ctx.channel.id != canal_geral.id:
        await ctx.send(f"✅ Ovo de dragão entregue pra {mencao} — anunciado no chat geral.")


# Comando .boss2 (só o Reality/CRIADOR_ID pode ativar) invoca o boss mais
# difícil já criado — Dourakhar, o Arauto da Morte. Mesma lógica do Dragão
# do Caos (encarar sozinho ou chamar o time todo), mas TUDO mais difícil:
# menos chance de vitória em qualquer cenário, mesmo com mais gente lutando
# junto. Em compensação, quem vencer ganha um pouco mais de XP que no boss 1
# E ainda leva um Booster de XP de 5 minutos (xp de call/mensagem em dobro).
# ══════════════════════════════════════════════════════════════════════

# ⚠️ Esses gifs são links temporários do CDN do Discord (parâmetros ?ex=...),
# que expiram sozinhos depois de um tempo (geralmente ~24h-48h). Se pararem
# de aparecer nos embeds, pegue links novos (clique direito na imagem no
# Discord > Copiar link) e troque aqui embaixo — ou, melhor ainda, subam
# os gifs num host permanente (imgur, ibb.co etc.) pra nunca mais precisar trocar.
_BOSS2_DOURAKHAR_INTRO_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1530317596254142494/PixVerse_V6_Image_Text_720P_anime_se_mexendo_t1-ezgif.com-video-to-gif-converter.gif?ex=6a6522d2&is=6a63d152&hm=29fa9a7986126b02b81c108189d53806326f6ae1aabf5525267b297ac2fd63fd"
_BOSS2_DOURAKHAR_BATALHA_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1530318926171476251/ezgif.com-video-to-gif-converter.gif?ex=6a65240f&is=6a63d28f&hm=d985c992e00eb66802330e6c13b6b3012c0998455cc6c18cbed1e3a66de9a21a"

_BOSS2_CANAL_ID = _BOSS_CANAL_ID   # mesmo canal do boss 1 — só aparece aqui

_BOSS2_TEMPO_ESCOLHA      = 60   # segundos pra decidir "todos juntos" ou "sozinho"
_BOSS2_TEMPO_RECRUTAMENTO = 10   # segundos pra galera clicar "quero participar" depois de "todos juntos"

_BOSS2_CHANCE_SOLO = 0.01   # 1% — nível mítico, enfrentar sozinho é praticamente suicídio (menos que o boss 1) [dificuldade aumentada]

# Batalha em grupo: base mais baixa e teto mais baixo que o boss 1 — mesma
# lógica (mais gente = mais chance, criaturas raras dão bônus extra), mas
# Dourakhar continua sendo bem mais difícil de derrubar mesmo com o
# servidor inteiro lutando junto. [valores reduzidos pra aumentar a dificuldade]
_BOSS2_CHANCE_GRUPO_BASE      = 0.05
_BOSS2_CHANCE_GRUPO_MAX       = 0.45
_BOSS2_BONUS_POR_PARTICIPANTE = 0.018
_BOSS2_BONUS_RARIDADE_CRIATURA = {
    "comum": 0.0, "raro": 0.01, "epico": 0.018, "lendario": 0.03, "secreto": 0.045, "mitico": 0.06,
}

_BOSS2_XP_GANHO_MIN = 0.25   # 25% — mínimo de XP que quem vence pode ganhar (um pouco melhor que o boss 1)
_BOSS2_XP_GANHO_MAX = 0.70   # 70% — máximo de XP que quem vence pode ganhar
_BOSS2_XP_GANHO_SEM_XP = (40, 100)   # recompensa fixa pra quem ainda não tem XP acumulado
_BOSS2_XP_GANHO_TETO = 4000   # teto máximo de XP por vitória — um pouco mais alto que o boss 1
                                # (Dourakhar é mais raro/difícil), mas ainda travado pra não
                                # deixar o rank alto disparar cada vez mais na frente.


def _boss2_chance_grupo(convocacoes: list) -> float:
    """Calcula a chance de vitória do grupo contra Dourakhar: base + um
    bônus por pessoa + um bônus pela raridade de cada criatura convocada,
    sempre travado no teto de _BOSS2_CHANCE_GRUPO_MAX — mais baixo que o
    do boss 1, porque Dourakhar é nível mítico."""
    chance = _BOSS2_CHANCE_GRUPO_BASE + len(convocacoes) * _BOSS2_BONUS_POR_PARTICIPANTE
    for _membro, criatura in convocacoes:
        chance += _BOSS2_BONUS_RARIDADE_CRIATURA.get(criatura["raridade"], 0.0)
    return min(chance, _BOSS2_CHANCE_GRUPO_MAX)


def _boss2_calcular_ganho_xp(user_id: int) -> tuple:
    """Sorteia quanto de XP essa pessoa ganha por vencer Dourakhar: entre
    25% e 70% do XP que ela já tem — um pouco melhor que o boss 1 — travado
    num teto máximo (_BOSS2_XP_GANHO_TETO) pra não deixar quem já é rank
    alto disparar cada vez mais na frente — ou uma recompensa fixa se
    ainda não tiver XP nenhum acumulado."""
    dados = xp_stats[user_id]
    xp_atual = dados.get("xp", 0)
    if xp_atual > 0:
        percentual = random.uniform(_BOSS2_XP_GANHO_MIN, _BOSS2_XP_GANHO_MAX)
        ganho = max(1, round(xp_atual * percentual))
        ganho = min(ganho, _BOSS2_XP_GANHO_TETO)
    else:
        percentual = 0.0
        ganho = random.randint(*_BOSS2_XP_GANHO_SEM_XP)
    return ganho, percentual


async def _boss2_premiar_vencedores(guild: discord.Guild, vencedores: list) -> list:
    """Aplica o ganho de XP de cada vencedor, ativa o Booster de XP de 5
    minutos (xp de call/mensagem em dobro — mesmo mecanismo do Baú) pra
    cada um deles, atualiza nível e dispara o aviso de level up quando for
    o caso. Devolve uma lista de (membro, ganho, percentual) pra montar o
    texto de resultado."""
    resultados = []
    for membro in vencedores:
        dados = xp_stats[membro.id]
        nivel_antigo = dados["nivel"]
        ganho, percentual = _boss2_calcular_ganho_xp(membro.id)
        dados["xp"] += ganho
        dados["nivel"], _, _ = _calcular_nivel(dados["xp"])
        if dados["nivel"] > nivel_antigo and guild is not None:
            asyncio.create_task(_anunciar_level_up(guild, membro, dados["nivel"]))
        # 🎁 Bônus exclusivo de Dourakhar: Booster de XP de 5 minutos pra quem venceu
        _conceder_xp_booster(membro.id, _BAU_BOOSTER_MINUTOS)
        resultados.append((membro, ganho, percentual))

    asyncio.create_task(_salvar_xp_stats())
    asyncio.create_task(_atualizar_ranking_xp())

    for membro, ganho, percentual in resultados:
        asyncio.create_task(_log_rpg(
            guild,
            "🐉 Recompensa — Dourakhar",
            f"✨ **{membro.display_name}** ganhou **`{ganho}` XP** (`{percentual * 100:.1f}%`) + "
            f"⚡ Booster de XP de `{_BAU_BOOSTER_MINUTOS}min` por vencer Dourakhar.",
        ))

    return resultados


async def _boss2_batalha_solo(canal: discord.TextChannel, membro: discord.Member) -> None:
    """Roda o confronto solo contra Dourakhar: só 1% de chance de vitória —
    e se perder, não perde XP nenhum, só o orgulho."""
    try:
        criatura = _boss_criatura_mais_forte(membro.id)
        info_raridade = _RARIDADES[criatura["raridade"]]

        embed_convocacao = discord.Embed(
            title="☠️ Um desafiante solitário ousa se apresentar!",
            description=(
                f"🌑 **Aeon:** ...{membro.mention} decidiu encarar Dourakhar sozinho. As sombras "
                f"nem sabem se isso é coragem ou uma despedida. 🖤💀\n"
                f"🌟 **Celestia:** {membro.display_name} convoca {info_raridade['emoji']} "
                f"**{criatura['nome']}**!! É NÍVEL MÍTICO, tenham cuidado!! 😳🌟✨"
            ),
            color=info_raridade["cor"],
        )
        embed_convocacao.set_thumbnail(url=criatura["gif"])
        msg1 = await canal.send(embed=embed_convocacao)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "💀 **Dourakhar:** *\"Sozinho, mortal? Ousado... ou simplesmente tolo. "
                "Vamos ver qual dos dois é a verdade.\"*"
            ),
            color=0x2c0140,
        )
        embed_batalha.set_image(url=_BOSS2_DOURAKHAR_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        venceu = random.random() < _BOSS2_CHANCE_SOLO

        if venceu:
            resultados = await _boss2_premiar_vencedores(canal.guild, [membro])
            _, ganho, percentual = resultados[0]
            descricao = (
                f"🏆 **LENDÁRIO DE VERDADE!!** {membro.mention} e {info_raridade['emoji']} **{criatura['nome']}** "
                f"derrubaram **DOURAKHAR, O ARAUTO DA MORTE**, SOZINHOS!! Só 1% de chance!! 💀⚔️\n\n"
                f"✨ Recompensa: **`+{ganho}` XP** (`{percentual * 100:.1f}%`) + ⚡ **Booster de XP {_BAU_BOOSTER_MINUTOS}min**!\n\n"
                f"🌑 **Aeon:** ...impossível. A própria Morte hesitou. As sombras não têm palavras. 🖤💀\n"
                f"🌟 **Celestia:** EU. NÃO. ACREDITO. 😭🌟🤍✨ ISSO VAI VIRAR LENDA NO SERVIDOR INTEIRO!!"
            )
            cor = 0xf5c542
        else:
            descricao = (
                f"💀 **Dourakhar:** *\"...como eu previa.\"* {info_raridade['emoji']} **{criatura['nome']}** caiu "
                f"em batalha, e {membro.mention} não conseguiu sozinho dessa vez.\n\n"
                f"🍃 Nenhum XP foi perdido — só a derrota amarga mesmo.\n\n"
                f"🌑 **Aeon:** ...era esperado. Poucos ousam, menos ainda sobrevivem. 🖤🌑\n"
                f"🌟 **Celestia:** Não desanima!! 🌸😢 Contra esse aqui, é MUITO melhor ir em grupo!!"
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="🌑 Aeon & ☀️ Celestia — Dourakhar, o Arauto da Morte")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


async def _boss2_batalha_grupo(canal: discord.TextChannel, participantes: list) -> None:
    """Roda o confronto em grupo contra Dourakhar: cada participante
    convoca a criatura mais forte que já desbloqueou, e a chance de vitória
    cresce com o número (e a força) das criaturas convocadas — mas nível
    mítico continua sendo bem mais difícil que o boss 1."""
    try:
        convocacoes = [(p, _boss_criatura_mais_forte(p.id)) for p in participantes]

        embed_cabecalho = discord.Embed(
            title=f"⚔️ {len(convocacoes)} guerreiro(a)s ousam encarar a Morte!",
            description="🌟 **Celestia:** ESSE TIME TÁ INDO CONTRA O NÍVEL MÍTICO!! 😱🌟✨ Boa sorte pra todos!!",
            color=0x2c0140,
        )
        cards = _boss_cards_criaturas(convocacoes)

        # 1º lote: cabeçalho + até 9 cards (10 embeds é o limite do Discord por
        # mensagem). O resto (grupos grandes) sai em mensagens seguintes.
        lote = [embed_cabecalho] + cards[:9]
        restante = cards[9:]
        msg1 = await canal.send(embeds=lote)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        while restante:
            msg_extra = await canal.send(embeds=restante[:10])
            asyncio.create_task(_apagar_mensagem_depois(msg_extra))
            restante = restante[10:]
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "💀 **Dourakhar:** *\"Um exército de formigas ainda é só um punhado de formigas... "
                "mas ao menos vocês me trazem entretenimento antes do fim. Venham.\"*"
            ),
            color=0x2c0140,
        )
        embed_batalha.set_image(url=_BOSS2_DOURAKHAR_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        chance = _boss2_chance_grupo(convocacoes)
        venceu = random.random() < chance

        if venceu:
            resultados = await _boss2_premiar_vencedores(canal.guild, participantes)
            texto_ganhos = "\n".join(
                f"✨ {membro.mention} +`{ganho}` XP (`{percentual * 100:.1f}%`) ⚡"
                for membro, ganho, percentual in resultados
            )
            descricao = (
                f"🏆 **VITÓRIA HISTÓRICA!!** O time de `{len(participantes)}` guerreiro(a)s derrubou "
                f"**DOURAKHAR, O ARAUTO DA MORTE**!! (chance da batalha: `{chance * 100:.0f}%`) 💀⚔️\n\n"
                f"{texto_ganhos}\n\n"
                f"⚡ Todos os vencedores também ganharam um **Booster de XP de {_BAU_BOOSTER_MINUTOS} minutos** "
                f"(xp de call e mensagem em dobro)!\n\n"
                f"🌑 **Aeon:** ...até a Morte tem seus limites, ao que parece. As sombras se curvam a vocês. 🖤💀\n"
                f"🌟 **Celestia:** VOCÊS DERROTARAM O NÍVEL MÍTICO!!! 😭🌟🤍✨ ISSO AQUI VAI FICAR NA HISTÓRIA DO SERVIDOR!!"
            )
            cor = 0xf5c542
        else:
            mencoes = ", ".join(p.mention for p in participantes)
            descricao = (
                f"💀 **Dourakhar:** *\"...como eu disse. Formigas.\"* Mesmo com `{len(participantes)}` "
                f"guerreiro(a)s juntos (`{chance * 100:.0f}%` de chance), o Arauto da Morte foi forte demais "
                f"dessa vez. {mencoes} não conseguiram.\n\n"
                f"🍃 Ninguém perdeu XP — só a derrota amarga mesmo.\n\n"
                f"🌑 **Aeon:** ...nível mítico não perdoa fácil. As sombras respeitam a tentativa. 🖤🌑\n"
                f"🌟 **Celestia:** Vamos treinar e tentar de novo!! 🌸💫 Vocês foram MUITO corajosos!!"
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="🌑 Aeon & ☀️ Celestia — Dourakhar, o Arauto da Morte")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


class Boss2RecrutamentoView(discord.ui.View):
    """Botão único de 'Quero Participar!' que fica ativo por
    _BOSS2_TEMPO_RECRUTAMENTO segundos, juntando o time que vai enfrentar
    Dourakhar em conjunto. Quando o tempo acaba, a batalha começa sozinha."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS2_TEMPO_RECRUTAMENTO)
        self.canal = canal
        self.participantes: dict = {}   # user_id -> discord.Member
        self.mensagem: discord.Message = None

    @discord.ui.button(label="⚔️ Quero Participar!", style=discord.ButtonStyle.success)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if interaction.user.id in self.participantes:
            await interaction.response.send_message(
                "🌟 **Celestia:** Você já tá na lista, guerreiro(a)!! 😆🌸", ephemeral=True
            )
            return

        self.participantes[interaction.user.id] = interaction.user
        button.label = f"⚔️ Quero Participar! ({len(self.participantes)})"
        await interaction.response.edit_message(view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.mensagem:
                await self.mensagem.edit(view=self)
        except discord.HTTPException:
            pass

        participantes = list(self.participantes.values())
        if not participantes:
            try:
                msg = await self.canal.send(
                    "🌑 **Aeon:** ...ninguém teve coragem de se juntar a tempo. "
                    "Dourakhar sorri e se dissolve de volta nas sombras... por enquanto. 🖤💀"
                )
                asyncio.create_task(_apagar_mensagem_depois(msg))
            finally:
                _boss_ativo_no_canal.discard(self.canal.id)
            return

        asyncio.create_task(_boss2_batalha_grupo(self.canal, participantes))


class Boss2EscolhaView(discord.ui.View):
    """Botões de 'Todos Juntos' e 'Eu Consigo Sozinho' que aparecem quando
    Dourakhar surge. A PRIMEIRA escolha feita (por qualquer pessoa) decide
    o caminho dessa aparição do boss."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS2_TEMPO_ESCOLHA)
        self.canal = canal
        self.decidido = False
        self.mensagem: discord.Message = None

    def _travar_botoes(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="🤝 Todos Juntos", style=discord.ButtonStyle.primary)
    async def todos_juntos(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "🌑 **Aeon:** ...essa decisão já foi tomada. 🖤🌑", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🤝 O CHAMADO FOI FEITO!",
            description=(
                f"🌟 **Celestia:** {interaction.user.mention} decidiu enfrentar Dourakhar "
                f"EM GRUPO!! 😱🌟✨\n"
                f"🌑 **Aeon:** ...quem tiver coragem, clique no botão abaixo. `{_BOSS2_TEMPO_RECRUTAMENTO}s` "
                f"pra se juntar ao time. 🖤💀"
            ),
            color=0xff8800,
        )
        embed.set_image(url=_BOSS2_DOURAKHAR_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        view_recrutamento = Boss2RecrutamentoView(self.canal)
        msg_recrutamento = await self.canal.send(
            "💀 Time contra **Dourakhar, o Arauto da Morte** — clique pra participar!",
            view=view_recrutamento,
        )
        view_recrutamento.mensagem = msg_recrutamento
        asyncio.create_task(_apagar_mensagem_depois(msg_recrutamento))

    @discord.ui.button(label="🗡️ Eu Consigo Sozinho", style=discord.ButtonStyle.danger)
    async def sozinho(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "🌑 **Aeon:** ...essa decisão já foi tomada. 🖤🌑", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🗡️ DESAFIO SOLITÁRIO ACEITO!",
            description=(
                f"🌑 **Aeon:** ...{interaction.user.mention} escolheu encarar Dourakhar sozinho. "
                f"Isso não é coragem, isso é ousadia pura. 🖤💀\n"
                f"🌟 **Celestia:** SÓ 1% DE CHANCE?!?! 😰🌟 É NÍVEL MÍTICO, TEM CERTEZA?!"
            ),
            color=0xff4444,
        )
        embed.set_image(url=_BOSS2_DOURAKHAR_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        asyncio.create_task(_boss2_batalha_solo(self.canal, interaction.user))

    async def on_timeout(self):
        if self.decidido or self.mensagem is None:
            return
        self._travar_botoes()
        try:
            embed = discord.Embed(
                title="💀 Dourakhar se dissolve nas sombras...",
                description=(
                    "🌑 **Aeon:** ...ninguém teve coragem de decidir a tempo. O Arauto da Morte "
                    "se retira... por enquanto. 🖤💀"
                ),
                color=0x888888,
            )
            await self.mensagem.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass
        _boss_ativo_no_canal.discard(self.canal.id)


@bot.command(name="boss2")
async def cmd_boss2(ctx):
    """💀 Invoca Dourakhar, o Arauto da Morte — o boss de NÍVEL MÍTICO, mais
    difícil que o Dragão do Caos. Só o Reality (CRIADOR_ID) pode chamar.
    O chat escolhe entre encarar sozinho (1% de chance) ou juntar um time
    (mais gente = mais chance, mas ainda assim MUITO mais difícil que o
    boss 1). Quem vencer ganha um pouco mais de XP que no boss 1 e também
    leva um Booster de XP de 5 minutos. Uso: .boss2"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BOSS2_CANAL_ID)
    if canal is None:
        return

    if canal.id in _boss_ativo_no_canal:
        aviso = await ctx.send(
            "🌟 **Celestia:** Já tem um boss ativo por lá!! Espera esse terminar!! 😅🌸"
        )
        asyncio.create_task(_apagar_mensagem_depois(aviso))
        return

    _boss_ativo_no_canal.add(canal.id)

    embed = discord.Embed(
        title="☠️ NÍVEL MÍTICO — O ARAUTO DA MORTE DESPERTOU!!",
        description=(
            "🌑 **Aeon:** ...o próprio ar fica mais frio. Isso não é como o Dragão do Caos. "
            "Isso é... diferente. Isso é o fim de tudo, caminhando. 🖤💀\n\n"
            "💀 **Dourakhar:** *\"Mortais... sintam o cheiro da própria finitude. Eu sou "
            "**Dourakhar**, o Arauto da Morte, e vim colher o que já me pertence.\"*\n\n"
            "🌟 **Celestia:** GENTE ISSO AQUI É NÍVEL **MÍTICO**!! 😨🌟 MUITO mais perigoso "
            "que o Dragão do Caos!! Pensem bem antes de decidir — sozinho ou em grupo?? ✨\n\n"
            f"⏳ Vocês têm `{_BOSS2_TEMPO_ESCOLHA}s` pra decidir."
        ),
        color=0x2c0140,
    )
    embed.set_image(url=_BOSS2_DOURAKHAR_INTRO_GIF)
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Nível Mítico: Dourakhar, o Arauto da Morte")

    view = Boss2EscolhaView(canal)
    msg = await canal.send(embed=embed, view=view)
    view.mensagem = msg
    asyncio.create_task(_apagar_mensagem_depois(msg))


# ══════════════════════════════════════════════════════════════════════
# Comando .boss3 (só o Reality/CRIADOR_ID pode ativar) invoca Zephyrus, o
# Guardião do Véu Arcano — nível mítico, um pouco mais fraco que Dourakhar
# (boss2) mas ainda bem mais difícil que o Dragão do Caos (boss1). Mesma
# lógica de sempre (encarar sozinho ou chamar o time), mas Zephyrus entra
# em campo subestimando os desafiantes assim que a luta começa. Quem
# vencer ganha XP e leva um Booster de XP de apenas 2 minutos (mais curto
# que o de Dourakhar, condizente com o boss ser um pouco mais fraco).
# ══════════════════════════════════════════════════════════════════════

# ⚠️ Esses gifs são links temporários do CDN do Discord (parâmetros ?ex=...),
# que expiram sozinhos depois de um tempo (geralmente ~24h-48h). Se pararem
# de aparecer nos embeds, pegue links novos (clique direito na imagem no
# Discord > Copiar link) e troque aqui embaixo — ou, melhor ainda, subam
# os gifs num host permanente (imgur, ibb.co etc.) pra nunca mais precisar trocar.
_BOSS3_ZEPHYRUS_INTRO_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1530395243793350656/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte1-ezgif.com-video-to-gif-converter.gif?ex=6a656b23&is=6a6419a3&hm=31a65b7384655f72f7bb1d274dddef20abd0f2a5476f4a650634418861d5cf2c&"
_BOSS3_ZEPHYRUS_BATALHA_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1530395243336437971/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte3-ezgif.com-video-to-gif-converter.gif?ex=6a656b23&is=6a6419a3&hm=7f3f861eccc45b6d93d8dbd437014814fd46196daec6cb535c34de7da748ad4b&"

_BOSS3_CANAL_ID = _BOSS_CANAL_ID   # mesmo canal dos outros bosses — só aparece aqui

_BOSS3_TEMPO_ESCOLHA      = 60   # segundos pra decidir "todos juntos" ou "sozinho"
_BOSS3_TEMPO_RECRUTAMENTO = 10   # segundos pra galera clicar "quero participar" depois de "todos juntos"

# Booster exclusivo do Zephyrus: mais curto que o dos outros bosses (2 min
# em vez dos 5 min do Baú/Dourakhar), condizente com ele ser um pouco mais fraco.
_BOSS3_BOOSTER_MINUTOS = 2

_BOSS3_CHANCE_SOLO = 0.03   # 3% — nível mítico, mas um pouco mais generoso que o 2% de Dourakhar

# Batalha em grupo: base e teto um pouco acima do boss2 (Dourakhar), mas
# ainda abaixo do boss1 (Dragão do Caos) — Zephyrus é "um pouco mais fraco"
# que Dourakhar, não fácil.
_BOSS3_CHANCE_GRUPO_BASE      = 0.095
_BOSS3_CHANCE_GRUPO_MAX       = 0.60
_BOSS3_BONUS_POR_PARTICIPANTE = 0.028
_BOSS3_BONUS_RARIDADE_CRIATURA = {
    "comum": 0.0, "raro": 0.009, "epico": 0.017, "lendario": 0.028, "secreto": 0.045, "mitico": 0.055,
}

_BOSS3_XP_GANHO_MIN = 0.22   # 22% — mínimo de XP que quem vence pode ganhar (entre o boss1 e o boss2)
_BOSS3_XP_GANHO_MAX = 0.65   # 65% — máximo de XP que quem vence pode ganhar
_BOSS3_XP_GANHO_SEM_XP = (35, 90)   # recompensa fixa pra quem ainda não tem XP acumulado
_BOSS3_XP_GANHO_TETO = 3500   # teto máximo de XP por vitória — entre o teto do boss1 e do
                                # boss2 — evita que rank alto dispare cada vez mais na frente.


def _boss3_chance_grupo(convocacoes: list) -> float:
    """Calcula a chance de vitória do grupo contra Zephyrus: base + um
    bônus por pessoa + um bônus pela raridade de cada criatura convocada,
    sempre travado no teto de _BOSS3_CHANCE_GRUPO_MAX — um pouco mais
    generoso que Dourakhar (boss2), mas ainda um boss de nível mítico."""
    chance = _BOSS3_CHANCE_GRUPO_BASE + len(convocacoes) * _BOSS3_BONUS_POR_PARTICIPANTE
    for _membro, criatura in convocacoes:
        chance += _BOSS3_BONUS_RARIDADE_CRIATURA.get(criatura["raridade"], 0.0)
    return min(chance, _BOSS3_CHANCE_GRUPO_MAX)


def _boss3_calcular_ganho_xp(user_id: int) -> tuple:
    """Sorteia quanto de XP essa pessoa ganha por vencer Zephyrus: entre
    22% e 65% do XP que ela já tem — travado num teto máximo
    (_BOSS3_XP_GANHO_TETO) pra não deixar quem já é rank alto disparar
    cada vez mais na frente — ou uma recompensa fixa se ainda não
    tiver XP nenhum acumulado."""
    dados = xp_stats[user_id]
    xp_atual = dados.get("xp", 0)
    if xp_atual > 0:
        percentual = random.uniform(_BOSS3_XP_GANHO_MIN, _BOSS3_XP_GANHO_MAX)
        ganho = max(1, round(xp_atual * percentual))
        ganho = min(ganho, _BOSS3_XP_GANHO_TETO)
    else:
        percentual = 0.0
        ganho = random.randint(*_BOSS3_XP_GANHO_SEM_XP)
    return ganho, percentual


async def _boss3_premiar_vencedores(guild: discord.Guild, vencedores: list) -> list:
    """Aplica o ganho de XP de cada vencedor, ativa o Booster de XP de
    _BOSS3_BOOSTER_MINUTOS (mais curto que o dos outros bosses) pra cada
    um deles, atualiza nível e dispara o aviso de level up quando for o
    caso. Devolve uma lista de (membro, ganho, percentual)."""
    resultados = []
    for membro in vencedores:
        dados = xp_stats[membro.id]
        nivel_antigo = dados["nivel"]
        ganho, percentual = _boss3_calcular_ganho_xp(membro.id)
        dados["xp"] += ganho
        dados["nivel"], _, _ = _calcular_nivel(dados["xp"])
        if dados["nivel"] > nivel_antigo and guild is not None:
            asyncio.create_task(_anunciar_level_up(guild, membro, dados["nivel"]))
        # 🎁 Bônus exclusivo do Zephyrus: Booster de XP de apenas 2 minutos pra quem venceu
        _conceder_xp_booster(membro.id, _BOSS3_BOOSTER_MINUTOS)
        resultados.append((membro, ganho, percentual))

    asyncio.create_task(_salvar_xp_stats())
    asyncio.create_task(_atualizar_ranking_xp())

    for membro, ganho, percentual in resultados:
        asyncio.create_task(_log_rpg(
            guild,
            "🌀 Recompensa — Zephyrus",
            f"✨ **{membro.display_name}** ganhou **`{ganho}` XP** (`{percentual * 100:.1f}%`) + "
            f"⚡ Booster de XP de `{_BOSS3_BOOSTER_MINUTOS}min` por vencer Zephyrus.",
        ))

    return resultados


async def _boss3_batalha_solo(canal: discord.TextChannel, membro: discord.Member) -> None:
    """Roda o confronto solo contra Zephyrus: só 3% de chance de vitória —
    e se perder, não perde XP nenhum, só o orgulho."""
    try:
        criatura = _boss_criatura_mais_forte(membro.id)
        info_raridade = _RARIDADES[criatura["raridade"]]

        embed_convocacao = discord.Embed(
            title="🌀 Um desafiante solitário ousa se apresentar!",
            description=(
                f"🌑 **Aeon:** ...{membro.mention} decidiu encarar Zephyrus sozinho. O véu se agita "
                f"como se estivesse rindo. 🖤🔮\n"
                f"🌟 **Celestia:** {membro.display_name} convoca {info_raridade['emoji']} "
                f"**{criatura['nome']}**!! É NÍVEL MÍTICO, cuidado!! 😳🌟✨"
            ),
            color=info_raridade["cor"],
        )
        embed_convocacao.set_thumbnail(url=criatura["gif"])
        msg1 = await canal.send(embed=embed_convocacao)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "🌀 **Zephyrus:** *\"Sozinho? Eu já vi poeira com mais ambição que você, mortal. "
                "Mas tudo bem... vamos ver quanto tempo essa fagulha dura contra o véu.\"*"
            ),
            color=0x1b1033,
        )
        embed_batalha.set_image(url=_BOSS3_ZEPHYRUS_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        venceu = random.random() < _BOSS3_CHANCE_SOLO

        if venceu:
            resultados = await _boss3_premiar_vencedores(canal.guild, [membro])
            _, ganho, percentual = resultados[0]
            descricao = (
                f"🏆 **O VÉU SE RASGOU!!** {membro.mention} e {info_raridade['emoji']} **{criatura['nome']}** "
                f"derrubaram **ZEPHYRUS, O GUARDIÃO DO VÉU ARCANO**, SOZINHOS!! Só 3% de chance!! 🌀⚔️\n\n"
                f"✨ Recompensa: **`+{ganho}` XP** (`{percentual * 100:.1f}%`) + ⚡ **Booster de XP {_BOSS3_BOOSTER_MINUTOS}min**!\n\n"
                f"🌑 **Aeon:** ...ele subestimou. Foi o único erro que cometeu. As sombras anotam isso. 🖤🌀\n"
                f"🌟 **Celestia:** ELE DUVIDOU E PERDEU!! 😭🌟🤍✨ TOMA ESSA, ZEPHYRUS!!"
            )
            cor = 0xf5c542
        else:
            descricao = (
                f"🌀 **Zephyrus:** *\"...como eu disse.\"* {info_raridade['emoji']} **{criatura['nome']}** caiu "
                f"em batalha, e {membro.mention} não conseguiu sozinho dessa vez.\n\n"
                f"🍃 Nenhum XP foi perdido — só a derrota amarga mesmo.\n\n"
                f"🌑 **Aeon:** ...era esperado. O véu não se abre fácil. 🖤🌑\n"
                f"🌟 **Celestia:** Não desanima!! 🌸😢 Contra esse aqui também é bem melhor ir em grupo!!"
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="🌑 Aeon & ☀️ Celestia — Zephyrus, o Guardião do Véu Arcano")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


async def _boss3_batalha_grupo(canal: discord.TextChannel, participantes: list) -> None:
    """Roda o confronto em grupo contra Zephyrus: cada participante convoca
    a criatura mais forte que já desbloqueou, e a chance de vitória cresce
    com o número (e a força) das criaturas convocadas — um pouco mais fácil
    que Dourakhar (boss2), mas ainda nível mítico."""
    try:
        convocacoes = [(p, _boss_criatura_mais_forte(p.id)) for p in participantes]

        embed_cabecalho = discord.Embed(
            title=f"⚔️ {len(convocacoes)} guerreiro(a)s ousam encarar o véu!",
            description="🌟 **Celestia:** ESSE TIME TÁ INDO CONTRA O NÍVEL MÍTICO!! 😱🌟✨ Boa sorte pra todos!!",
            color=0x1b1033,
        )
        cards = _boss_cards_criaturas(convocacoes)

        # 1º lote: cabeçalho + até 9 cards (10 embeds é o limite do Discord por
        # mensagem). O resto (grupos grandes) sai em mensagens seguintes.
        lote = [embed_cabecalho] + cards[:9]
        restante = cards[9:]
        msg1 = await canal.send(embeds=lote)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        while restante:
            msg_extra = await canal.send(embeds=restante[:10])
            asyncio.create_task(_apagar_mensagem_depois(msg_extra))
            restante = restante[10:]
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "🌀 **Zephyrus:** *\"Um bando de mortais batendo à porta do véu... adoráveis. "
                "Ingênuos, mas adoráveis. Vou tentar não bocejar enquanto isso acaba.\"*"
            ),
            color=0x1b1033,
        )
        embed_batalha.set_image(url=_BOSS3_ZEPHYRUS_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        chance = _boss3_chance_grupo(convocacoes)
        venceu = random.random() < chance

        if venceu:
            resultados = await _boss3_premiar_vencedores(canal.guild, participantes)
            texto_ganhos = "\n".join(
                f"✨ {membro.mention} +`{ganho}` XP (`{percentual * 100:.1f}%`) ⚡"
                for membro, ganho, percentual in resultados
            )
            descricao = (
                f"🏆 **O VÉU CEDEU!!** O time de `{len(participantes)}` guerreiro(a)s derrubou "
                f"**ZEPHYRUS, O GUARDIÃO DO VÉU ARCANO**!! (chance da batalha: `{chance * 100:.0f}%`) 🌀⚔️\n\n"
                f"{texto_ganhos}\n\n"
                f"⚡ Todos os vencedores também ganharam um **Booster de XP de {_BOSS3_BOOSTER_MINUTOS} minutos** "
                f"(xp de call e mensagem em dobro)!\n\n"
                f"🌑 **Aeon:** ...ele riu até o fim. Foi o erro dele. As sombras respeitam vocês. 🖤🌀\n"
                f"🌟 **Celestia:** ELE ACHOU QUE VOCÊS ERAM FRACOS E SE FERROU!!! 😭🌟🤍✨"
            )
            cor = 0xf5c542
        else:
            mencoes = ", ".join(p.mention for p in participantes)
            descricao = (
                f"🌀 **Zephyrus:** *\"...eu avisei.\"* Mesmo com `{len(participantes)}` guerreiro(a)s "
                f"juntos (`{chance * 100:.0f}%` de chance), o Guardião do Véu Arcano foi forte demais "
                f"dessa vez. {mencoes} não conseguiram.\n\n"
                f"🍃 Ninguém perdeu XP — só a derrota amarga mesmo.\n\n"
                f"🌑 **Aeon:** ...nível mítico não perdoa fácil, mesmo o mais fraco deles. 🖤🌑\n"
                f"🌟 **Celestia:** Vamos treinar e tentar de novo!! 🌸💫 Vocês foram MUITO corajosos!!"
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="🌑 Aeon & ☀️ Celestia — Zephyrus, o Guardião do Véu Arcano")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


class Boss3RecrutamentoView(discord.ui.View):
    """Botão único de 'Quero Participar!' que fica ativo por
    _BOSS3_TEMPO_RECRUTAMENTO segundos, juntando o time que vai enfrentar
    Zephyrus em conjunto. Quando o tempo acaba, a batalha começa sozinha."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS3_TEMPO_RECRUTAMENTO)
        self.canal = canal
        self.participantes: dict = {}   # user_id -> discord.Member
        self.mensagem: discord.Message = None

    @discord.ui.button(label="⚔️ Quero Participar!", style=discord.ButtonStyle.success)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if interaction.user.id in self.participantes:
            await interaction.response.send_message(
                "🌟 **Celestia:** Você já tá na lista, guerreiro(a)!! 😆🌸", ephemeral=True
            )
            return

        self.participantes[interaction.user.id] = interaction.user
        button.label = f"⚔️ Quero Participar! ({len(self.participantes)})"
        await interaction.response.edit_message(view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.mensagem:
                await self.mensagem.edit(view=self)
        except discord.HTTPException:
            pass

        participantes = list(self.participantes.values())
        if not participantes:
            try:
                msg = await self.canal.send(
                    "🌑 **Aeon:** ...ninguém teve coragem de se juntar a tempo. "
                    "Zephyrus sorri e se dissolve de volta no véu... por enquanto. 🖤🌀"
                )
                asyncio.create_task(_apagar_mensagem_depois(msg))
            finally:
                _boss_ativo_no_canal.discard(self.canal.id)
            return

        asyncio.create_task(_boss3_batalha_grupo(self.canal, participantes))


class Boss3EscolhaView(discord.ui.View):
    """Botões de 'Todos Juntos' e 'Eu Consigo Sozinho' que aparecem quando
    Zephyrus surge. A PRIMEIRA escolha feita (por qualquer pessoa) decide
    o caminho dessa aparição do boss."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS3_TEMPO_ESCOLHA)
        self.canal = canal
        self.decidido = False
        self.mensagem: discord.Message = None

    def _travar_botoes(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="🤝 Todos Juntos", style=discord.ButtonStyle.primary)
    async def todos_juntos(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "🌑 **Aeon:** ...essa decisão já foi tomada. 🖤🌑", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🤝 O CHAMADO FOI FEITO!",
            description=(
                f"🌟 **Celestia:** {interaction.user.mention} decidiu enfrentar Zephyrus "
                f"EM GRUPO!! 😱🌟✨\n"
                f"🌑 **Aeon:** ...quem tiver coragem, clique no botão abaixo. `{_BOSS3_TEMPO_RECRUTAMENTO}s` "
                f"pra se juntar ao time. 🖤🌀"
            ),
            color=0xff8800,
        )
        embed.set_image(url=_BOSS3_ZEPHYRUS_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        view_recrutamento = Boss3RecrutamentoView(self.canal)
        msg_recrutamento = await self.canal.send(
            "🌀 Time contra **Zephyrus, o Guardião do Véu Arcano** — clique pra participar!",
            view=view_recrutamento,
        )
        view_recrutamento.mensagem = msg_recrutamento
        asyncio.create_task(_apagar_mensagem_depois(msg_recrutamento))

    @discord.ui.button(label="🗡️ Eu Consigo Sozinho", style=discord.ButtonStyle.danger)
    async def sozinho(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "🌑 **Aeon:** ...essa decisão já foi tomada. 🖤🌑", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🗡️ DESAFIO SOLITÁRIO ACEITO!",
            description=(
                f"🌑 **Aeon:** ...{interaction.user.mention} escolheu encarar Zephyrus sozinho. "
                f"Isso não é coragem, isso é ousadia pura. 🖤🌀\n"
                f"🌟 **Celestia:** SÓ 3% DE CHANCE?!?! 😰🌟 É NÍVEL MÍTICO, TEM CERTEZA?!"
            ),
            color=0xff4444,
        )
        embed.set_image(url=_BOSS3_ZEPHYRUS_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        asyncio.create_task(_boss3_batalha_solo(self.canal, interaction.user))

    async def on_timeout(self):
        if self.decidido or self.mensagem is None:
            return
        self._travar_botoes()
        try:
            embed = discord.Embed(
                title="🌀 Zephyrus se dissolve de volta no véu...",
                description=(
                    "🌑 **Aeon:** ...ninguém teve coragem de decidir a tempo. O Guardião "
                    "se retira... por enquanto. 🖤🌀"
                ),
                color=0x888888,
            )
            await self.mensagem.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass
        _boss_ativo_no_canal.discard(self.canal.id)


@bot.command(name="boss3")
async def cmd_boss3(ctx):
    """🌀 Invoca Zephyrus, o Guardião do Véu Arcano — boss de NÍVEL MÍTICO,
    um pouco mais fraco que Dourakhar (boss2) mas ainda bem mais difícil
    que o Dragão do Caos (boss1). Só o Reality (CRIADOR_ID) pode chamar.
    O chat escolhe entre encarar sozinho (3% de chance) ou juntar um time
    (mais gente = mais chance). Quem vencer ganha XP e leva um Booster de
    XP de apenas 2 minutos. Uso: .boss3"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BOSS3_CANAL_ID)
    if canal is None:
        return

    if canal.id in _boss_ativo_no_canal:
        aviso = await ctx.send(
            "🌟 **Celestia:** Já tem um boss ativo por lá!! Espera esse terminar!! 😅🌸"
        )
        asyncio.create_task(_apagar_mensagem_depois(aviso))
        return

    _boss_ativo_no_canal.add(canal.id)

    embed = discord.Embed(
        title="🌀 NÍVEL MÍTICO — O GUARDIÃO DO VÉU ARCANO DESPERTOU!!",
        description=(
            "🌑 **Aeon:** ...o véu entre os mundos racha, e algo antigo espia através da fenda. "
            "Não é tão devastador quanto Dourakhar... mas ainda assim, nível mítico. 🖤🔮\n\n"
            "🌀 **Zephyrus:** *\"Sinto o cheiro de mortais curiosos demais para o próprio bem. "
            "Eu sou **Zephyrus**, Guardião do Véu Arcano. Aproximem-se... se conseguirem.\"*\n\n"
            "🌟 **Celestia:** GENTE ISSO AQUI TAMBÉM É NÍVEL **MÍTICO**!! 😨🌟 Mais fraco que "
            "Dourakhar, mas ainda MUITO mais perigoso que o Dragão do Caos!! Sozinho ou em grupo?? ✨\n\n"
            f"⏳ Vocês têm `{_BOSS3_TEMPO_ESCOLHA}s` pra decidir."
        ),
        color=0x1b1033,
    )
    embed.set_image(url=_BOSS3_ZEPHYRUS_INTRO_GIF)
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Nível Mítico: Zephyrus, o Guardião do Véu Arcano")

    view = Boss3EscolhaView(canal)
    msg = await canal.send(embed=embed, view=view)
    view.mensagem = msg
    asyncio.create_task(_apagar_mensagem_depois(msg))


# ══════════════════════════════════════════════════════════════════════
# BOSS 4 — Cthulhu, o Ancião dos Abismos
# O boss mais forte e mais EXCLUSIVO de todos: ele simplesmente NÃO aceita
# nada abaixo de 🟡 Lendária. Quem desafiar (sozinho ou em grupo) sempre
# convoca a criatura Lendária de MAIOR Nível de Capacidade que já tiver —
# e quem não tiver nenhuma Lendária desbloqueada é recusado na hora, tanto
# no botão solo quanto no recrutamento em grupo.
#
# Dificuldade mítica, igual Dourakhar/Zephyrus — mas o bônus por
# participante é o MAIOR de todos os bosses: grupos grandes ganham chance
# desproporcionalmente mais rápido do que contra qualquer outro boss.
# ══════════════════════════════════════════════════════════════════════

_BOSS4_CTHULHU_INTRO_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1530761640184905859/1785032338734.gif?ex=6a66c05f&is=6a656edf&hm=498a5804dc154079223effab883c04944c32d2451e5506d77a760c00f808017f"
_BOSS4_CTHULHU_BATALHA_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1530764368453701683/1785032847665.gif?ex=6a66c2e9&is=6a657169&hm=880fe48537da9be053f931f2f76c870f154f3f21d4a02685976ceceec849c994"

_BOSS4_CANAL_ID = _BOSS_CANAL_ID   # mesmo canal dos outros bosses — só aparece aqui

_BOSS4_TEMPO_ESCOLHA      = 60   # segundos pra decidir "todos juntos" ou "sozinho"
_BOSS4_TEMPO_RECRUTAMENTO = 10   # segundos pra galera clicar "quero participar" depois de "todos juntos"

# Booster exclusivo do Cthulhu: o mais longo de todos os bosses (5 min,
# igual o do Baú), condizente com ele ser o boss mais forte e difícil.
_BOSS4_BOOSTER_MINUTOS = 5

_BOSS4_CHANCE_SOLO = 0.01   # 1% — nível mítico, tão difícil sozinho quanto Dourakhar

# Batalha em grupo: a base mais baixa de todos os bosses, mas o bônus por
# participante é o MAIOR — grupos grandes recuperam terreno muito mais
# rápido do que contra qualquer outro boss.
_BOSS4_CHANCE_GRUPO_BASE      = 0.04
_BOSS4_CHANCE_GRUPO_MAX       = 0.65
_BOSS4_BONUS_POR_PARTICIPANTE = 0.045
_BOSS4_BONUS_RARIDADE_CRIATURA = {
    "comum": 0.0, "raro": 0.0, "epico": 0.0, "lendario": 0.035, "secreto": 0.05, "mitico": 0.06,
}

_BOSS4_XP_GANHO_MIN = 0.25    # 25% — mínimo de XP que quem vence pode ganhar (o melhor de todos os bosses)
_BOSS4_XP_GANHO_MAX = 0.75    # 75% — máximo de XP que quem vence pode ganhar
_BOSS4_XP_GANHO_SEM_XP = (45, 110)   # recompensa fixa pra quem ainda não tem XP acumulado
_BOSS4_XP_GANHO_TETO = 4500    # teto máximo de XP por vitória — o maior de todos os bosses
                                 # (Cthulhu é o mais raro), mas ainda travado pra não deixar
                                 # o rank alto disparar cada vez mais na frente.


def _boss4_criatura_lendaria_mais_forte(user_id: int):
    """Cthulhu só aceita quem convocar uma criatura 🟡 Lendária — e sempre
    puxa a de MAIOR Nível de Capacidade que a pessoa tiver, entre as
    Lendárias que ela já desbloqueou. Devolve None se a pessoa não tiver
    nenhuma Lendária (nesse caso, ela é recusada pelo boss)."""
    desbloqueadas = set(_garantir_criaturas_iniciais(user_id))
    lendarias = [c for c in _BATALHA_CRIATURAS if c["raridade"] == "lendario" and c["id"] in desbloqueadas]
    if not lendarias:
        return None
    return max(lendarias, key=lambda c: _nivel_criatura(user_id, c["id"]))


def _boss4_cards_criaturas(convocacoes: list) -> list:
    """Igual _boss_cards_criaturas, mas também mostra o Nível de Capacidade
    de cada Lendária convocada — já que é sempre a mais forte E de maior
    nível que cada um tem."""
    cards = []
    for membro, criatura in convocacoes:
        info = _RARIDADES[criatura["raridade"]]
        nivel_atual = _nivel_criatura(membro.id, criatura["id"])
        nivel_teto = _nivel_criatura_max(criatura["id"])
        card = discord.Embed(
            description=(
                f"{info['emoji']} **{membro.display_name}** convoca **{criatura['nome']}** "
                f"(*{info['label']}*, Nível `{nivel_atual}/{nivel_teto}`)"
            ),
            color=info["cor"],
        )
        card.set_thumbnail(url=criatura["gif"])
        cards.append(card)
    return cards


def _boss4_chance_grupo(convocacoes: list) -> float:
    """Calcula a chance de vitória do grupo contra Cthulhu: base baixa +
    um bônus por pessoa (o maior de todos os bosses) + um bônus pela
    raridade de cada Lendária convocada, travado no teto de
    _BOSS4_CHANCE_GRUPO_MAX."""
    chance = _BOSS4_CHANCE_GRUPO_BASE + len(convocacoes) * _BOSS4_BONUS_POR_PARTICIPANTE
    for _membro, criatura in convocacoes:
        chance += _BOSS4_BONUS_RARIDADE_CRIATURA.get(criatura["raridade"], 0.0)
    return min(chance, _BOSS4_CHANCE_GRUPO_MAX)


def _boss4_calcular_ganho_xp(user_id: int) -> tuple:
    """Sorteia quanto de XP essa pessoa ganha por vencer Cthulhu: entre 25%
    e 75% do XP que ela já tem — a melhor faixa de recompensa entre todos
    os bosses — travado num teto máximo (_BOSS4_XP_GANHO_TETO) pra não
    deixar quem já é rank alto disparar cada vez mais na frente — ou uma
    recompensa fixa se ainda não tiver XP acumulado."""
    dados = xp_stats[user_id]
    xp_atual = dados.get("xp", 0)
    if xp_atual > 0:
        percentual = random.uniform(_BOSS4_XP_GANHO_MIN, _BOSS4_XP_GANHO_MAX)
        ganho = max(1, round(xp_atual * percentual))
        ganho = min(ganho, _BOSS4_XP_GANHO_TETO)
    else:
        percentual = 0.0
        ganho = random.randint(*_BOSS4_XP_GANHO_SEM_XP)
    return ganho, percentual


async def _boss4_premiar_vencedores(guild: discord.Guild, vencedores: list) -> list:
    """Aplica o ganho de XP de cada vencedor, ativa o Booster de XP de
    _BOSS4_BOOSTER_MINUTOS (5 min — o maior de todos os bosses) pra cada
    um deles, atualiza nível e dispara o aviso de level up quando for o
    caso. Devolve uma lista de (membro, ganho, percentual)."""
    resultados = []
    for membro in vencedores:
        dados = xp_stats[membro.id]
        nivel_antigo = dados["nivel"]
        ganho, percentual = _boss4_calcular_ganho_xp(membro.id)
        dados["xp"] += ganho
        dados["nivel"], _, _ = _calcular_nivel(dados["xp"])
        if dados["nivel"] > nivel_antigo and guild is not None:
            asyncio.create_task(_anunciar_level_up(guild, membro, dados["nivel"]))
        # 🎁 Bônus do Cthulhu: Booster de XP de 5 minutos pra quem venceu
        _conceder_xp_booster(membro.id, _BOSS4_BOOSTER_MINUTOS)
        resultados.append((membro, ganho, percentual))

    asyncio.create_task(_salvar_xp_stats())
    asyncio.create_task(_atualizar_ranking_xp())

    for membro, ganho, percentual in resultados:
        asyncio.create_task(_log_rpg(
            guild,
            "🐙 Recompensa — Cthulhu",
            f"✨ **{membro.display_name}** ganhou **`{ganho}` XP** (`{percentual * 100:.1f}%`) + "
            f"⚡ Booster de XP de `{_BOSS4_BOOSTER_MINUTOS}min` por vencer Cthulhu.",
        ))

    return resultados


async def _boss4_batalha_solo(canal: discord.TextChannel, membro: discord.Member) -> None:
    """Roda o confronto solo contra Cthulhu: só 1% de chance de vitória —
    e se perder, não perde XP nenhum, só o orgulho. Só é chamada depois
    que o botão já garantiu que `membro` tem uma Lendária."""
    try:
        criatura = _boss4_criatura_lendaria_mais_forte(membro.id)
        info_raridade = _RARIDADES[criatura["raridade"]]
        nivel_atual = _nivel_criatura(membro.id, criatura["id"])
        nivel_teto = _nivel_criatura_max(criatura["id"])

        embed_convocacao = discord.Embed(
            title="🐙 Um desafiante solitário ousa se apresentar!",
            description=(
                f"🌑 **Aeon:** ...{membro.mention} decidiu encarar Cthulhu sozinho. As profundezas "
                f"nem se incomodam em despertar de verdade. 🖤🌊\n"
                f"🌟 **Celestia:** {membro.display_name} convoca {info_raridade['emoji']} "
                f"**{criatura['nome']}** (Nível `{nivel_atual}/{nivel_teto}`)!! É NÍVEL MÍTICO, "
                f"cuidado!! 😳🌟✨"
            ),
            color=info_raridade["cor"],
        )
        embed_convocacao.set_thumbnail(url=criatura["gif"])
        msg1 = await canal.send(embed=embed_convocacao)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "🐙 **Cthulhu:** *\"Uma única fagulha... contra o abismo inteiro? Eu nem preciso "
                "acordar direito pra isso.\"*"
            ),
            color=0x0d2b2e,
        )
        embed_batalha.set_image(url=_BOSS4_CTHULHU_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        venceu = random.random() < _BOSS4_CHANCE_SOLO

        if venceu:
            resultados = await _boss4_premiar_vencedores(canal.guild, [membro])
            _, ganho, percentual = resultados[0]
            descricao = (
                f"🏆 **O IMPOSSÍVEL ACONTECEU!!** {membro.mention} e {info_raridade['emoji']} "
                f"**{criatura['nome']}** derrubaram **CTHULHU, O ANCIÃO DOS ABISMOS**, SOZINHOS!! "
                f"Só `{_BOSS4_CHANCE_SOLO * 100:.0f}%` de chance!! 🐙⚔️\n\n"
                f"✨ Recompensa: **`+{ganho}` XP** (`{percentual * 100:.1f}%`) + ⚡ **Booster de XP "
                f"{_BOSS4_BOOSTER_MINUTOS}min**!\n\n"
                f"🌑 **Aeon:** ...ele nem viu chegando. Nem os Anciões estão a salvo do próprio "
                f"orgulho. 🖤🌊\n"
                f"🌟 **Celestia:** ISSO FOI LENDÁRIO DE VERDADE!! 😭🌟🤍✨ NINGUÉM VAI ACREDITAR NISSO!!"
            )
            cor = 0xf5c542
        else:
            descricao = (
                f"🐙 **Cthulhu:** *\"...como eu disse.\"* {info_raridade['emoji']} **{criatura['nome']}** "
                f"caiu em batalha, e {membro.mention} não conseguiu sozinho dessa vez.\n\n"
                f"🍃 Nenhum XP foi perdido — só a derrota amarga mesmo.\n\n"
                f"🌑 **Aeon:** ...era esperado. Nem uma Lendária sozinha abala os abismos. 🖤🌑\n"
                f"🌟 **Celestia:** Contra ele, é MUITO melhor ir em grupo!! Quanto mais gente, mais "
                f"chance!! 🌸💫"
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="🌑 Aeon & ☀️ Celestia — Cthulhu, o Ancião dos Abismos")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


async def _boss4_batalha_grupo(canal: discord.TextChannel, participantes: list) -> None:
    """Roda o confronto em grupo contra Cthulhu: cada participante convoca
    a Lendária mais forte (maior nível) que já desbloqueou, e a chance de
    vitória cresce MAIS RÁPIDO com o número de participantes do que contra
    qualquer outro boss — mas a base é a mais baixa de todos."""
    try:
        convocacoes = [(p, _boss4_criatura_lendaria_mais_forte(p.id)) for p in participantes]

        embed_cabecalho = discord.Embed(
            title=f"⚔️ {len(convocacoes)} guerreiro(a)s ousam despertar o abismo!",
            description=(
                "🌟 **Celestia:** ESSE TIME TÁ INDO CONTRA O BOSS MAIS FORTE DE TODOS!! 😱🌟✨ "
                "Só Lendárias entraram nessa — boa sorte!!"
            ),
            color=0x0d2b2e,
        )
        cards = _boss4_cards_criaturas(convocacoes)

        # 1º lote: cabeçalho + até 9 cards (10 embeds é o limite do Discord por
        # mensagem). O resto (grupos grandes) sai em mensagens seguintes.
        lote = [embed_cabecalho] + cards[:9]
        restante = cards[9:]
        msg1 = await canal.send(embeds=lote)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        while restante:
            msg_extra = await canal.send(embeds=restante[:10])
            asyncio.create_task(_apagar_mensagem_depois(msg_extra))
            restante = restante[10:]
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "🐙 **Cthulhu:** *\"Um exército de mortais, cada um com sua melhor Lendária... "
                "finalmente algo quase digno da minha atenção. Quase.\"*"
            ),
            color=0x0d2b2e,
        )
        embed_batalha.set_image(url=_BOSS4_CTHULHU_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        chance = _boss4_chance_grupo(convocacoes)
        venceu = random.random() < chance

        if venceu:
            resultados = await _boss4_premiar_vencedores(canal.guild, participantes)
            texto_ganhos = "\n".join(
                f"✨ {membro.mention} +`{ganho}` XP (`{percentual * 100:.1f}%`) ⚡"
                for membro, ganho, percentual in resultados
            )
            descricao = (
                f"🏆 **O ABISMO SE CALOU!!** O time de `{len(participantes)}` guerreiro(a)s derrubou "
                f"**CTHULHU, O ANCIÃO DOS ABISMOS**!! (chance da batalha: `{chance * 100:.0f}%`) 🐙⚔️\n\n"
                f"{texto_ganhos}\n\n"
                f"⚡ Todos os vencedores também ganharam um **Booster de XP de {_BOSS4_BOOSTER_MINUTOS} "
                f"minutos** (xp de call e mensagem em dobro)!\n\n"
                f"🌑 **Aeon:** ...nem os Anciões dormem tranquilos pra sempre. As sombras vão lembrar "
                f"disso. 🖤🌊\n"
                f"🌟 **Celestia:** VOCÊS DERRUBARAM O BOSS MAIS FORTE DE TODOS!!! 😭🌟🤍✨ ISSO É "
                f"HISTÓRICO!!"
            )
            cor = 0xf5c542
        else:
            mencoes = ", ".join(p.mention for p in participantes)
            descricao = (
                f"🐙 **Cthulhu:** *\"...voltem quando forem mais.\"* Mesmo com `{len(participantes)}` "
                f"guerreiro(a)s Lendários juntos (`{chance * 100:.0f}%` de chance), o Ancião dos "
                f"Abismos foi forte demais dessa vez. {mencoes} não conseguiram.\n\n"
                f"🍃 Ninguém perdeu XP — só a derrota amarga mesmo.\n\n"
                f"🌑 **Aeon:** ...ele é o mais forte de todos por um motivo. 🖤🌑\n"
                f"🌟 **Celestia:** Quanto mais gente, MUITO mais chance!! Chamem reforços e tentem de "
                f"novo!! 🌸💫"
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="🌑 Aeon & ☀️ Celestia — Cthulhu, o Ancião dos Abismos")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


class Boss4RecrutamentoView(discord.ui.View):
    """Botão único de 'Quero Participar!' que fica ativo por
    _BOSS4_TEMPO_RECRUTAMENTO segundos. Diferente dos outros bosses, quem
    clicar SEM ter uma criatura 🟡 Lendária desbloqueada é recusado na hora
    (Cthulhu não aceita menos que isso) — não entra pra lista."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS4_TEMPO_RECRUTAMENTO)
        self.canal = canal
        self.participantes: dict = {}   # user_id -> discord.Member
        self.mensagem: discord.Message = None

    @discord.ui.button(label="🐙 Quero Participar!", style=discord.ButtonStyle.success)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if interaction.user.id in self.participantes:
            await interaction.response.send_message(
                "🌟 **Celestia:** Você já tá na lista, guerreiro(a)!! 😆🌸", ephemeral=True
            )
            return
        if _boss4_criatura_lendaria_mais_forte(interaction.user.id) is None:
            await interaction.response.send_message(
                "🌑 **Aeon:** ...Cthulhu nem notaria suas criaturas atuais. 🖤🌊 Só quem tiver uma "
                "criatura 🟡 Lendária desbloqueada pode entrar nessa.",
                ephemeral=True,
            )
            return

        self.participantes[interaction.user.id] = interaction.user
        button.label = f"🐙 Quero Participar! ({len(self.participantes)})"
        await interaction.response.edit_message(view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.mensagem:
                await self.mensagem.edit(view=self)
        except discord.HTTPException:
            pass

        participantes = list(self.participantes.values())
        if not participantes:
            try:
                msg = await self.canal.send(
                    "🌑 **Aeon:** ...ninguém digno se juntou a tempo. Cthulhu volta a dormir nas "
                    "profundezas... por enquanto. 🖤🌊"
                )
                asyncio.create_task(_apagar_mensagem_depois(msg))
            finally:
                _boss_ativo_no_canal.discard(self.canal.id)
            return

        asyncio.create_task(_boss4_batalha_grupo(self.canal, participantes))


class Boss4EscolhaView(discord.ui.View):
    """Botões de 'Todos Juntos' e 'Eu Consigo Sozinho' que aparecem quando
    Cthulhu desperta. A PRIMEIRA escolha feita (por qualquer pessoa) decide
    o caminho dessa aparição do boss. O botão solo recusa na hora quem não
    tiver uma Lendária desbloqueada."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS4_TEMPO_ESCOLHA)
        self.canal = canal
        self.decidido = False
        self.mensagem: discord.Message = None

    def _travar_botoes(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="🤝 Todos Juntos", style=discord.ButtonStyle.primary)
    async def todos_juntos(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "🌑 **Aeon:** ...essa decisão já foi tomada. 🖤🌑", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🤝 O CHAMADO FOI FEITO!",
            description=(
                f"🌟 **Celestia:** {interaction.user.mention} decidiu enfrentar Cthulhu EM GRUPO!! "
                f"😱🌟✨\n"
                f"🌑 **Aeon:** ...só criaturas 🟡 Lendárias vão ser aceitas. Quem tiver uma e coragem, "
                f"clique no botão abaixo. `{_BOSS4_TEMPO_RECRUTAMENTO}s` pra se juntar ao time. 🖤🌊"
            ),
            color=0xff8800,
        )
        embed.set_image(url=_BOSS4_CTHULHU_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        view_recrutamento = Boss4RecrutamentoView(self.canal)
        msg_recrutamento = await self.canal.send(
            "🐙 Time contra **Cthulhu, o Ancião dos Abismos** — só Lendárias, clique pra participar!",
            view=view_recrutamento,
        )
        view_recrutamento.mensagem = msg_recrutamento
        asyncio.create_task(_apagar_mensagem_depois(msg_recrutamento))

    @discord.ui.button(label="🐙 Eu Consigo Sozinho", style=discord.ButtonStyle.danger)
    async def sozinho(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "🌑 **Aeon:** ...essa decisão já foi tomada. 🖤🌑", ephemeral=True
            )
            return
        if _boss4_criatura_lendaria_mais_forte(interaction.user.id) is None:
            await interaction.response.send_message(
                "🌑 **Aeon:** ...suas criaturas atuais nem seriam notadas por Cthulhu. 🖤🌊 Só quem "
                "tiver uma criatura 🟡 Lendária desbloqueada pode desafiá-lo.",
                ephemeral=True,
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🐙 DESAFIO SOLITÁRIO ACEITO!",
            description=(
                f"🌑 **Aeon:** ...{interaction.user.mention} escolheu encarar Cthulhu sozinho. Isso "
                f"não é coragem, isso é loucura pura. 🖤🌊\n"
                f"🌟 **Celestia:** SÓ `{_BOSS4_CHANCE_SOLO * 100:.0f}%` DE CHANCE?!?! 😰🌟 É O BOSS "
                f"MAIS FORTE DE TODOS, TEM CERTEZA?!"
            ),
            color=0xff4444,
        )
        embed.set_image(url=_BOSS4_CTHULHU_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        asyncio.create_task(_boss4_batalha_solo(self.canal, interaction.user))

    async def on_timeout(self):
        if self.decidido or self.mensagem is None:
            return
        self._travar_botoes()
        try:
            embed = discord.Embed(
                title="🐙 Cthulhu volta a dormir nas profundezas...",
                description=(
                    "🌑 **Aeon:** ...ninguém teve coragem de decidir a tempo. O Ancião se recolhe... "
                    "por enquanto. 🖤🌊"
                ),
                color=0x888888,
            )
            await self.mensagem.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass
        _boss_ativo_no_canal.discard(self.canal.id)


@bot.command(name="boss4")
async def cmd_boss4(ctx):
    """🐙 Invoca Cthulhu, o Ancião dos Abismos — o boss mais forte e mais
    EXCLUSIVO de todos: só aceita quem convocar uma criatura 🟡 Lendária (e
    sempre puxa a Lendária de maior Nível de Capacidade que a pessoa
    tiver) — quem não tiver nenhuma é recusado na hora. Dificuldade
    mítica, com o bônus por participante MAIS FORTE de todos os bosses:
    quanto mais gente entrar, mais rápido a chance sobe. Só o Reality
    (CRIADOR_ID) pode chamar. Quem vencer ganha XP e um Booster de XP de
    5 minutos — o maior de todos os bosses. Uso: .boss4"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BOSS4_CANAL_ID)
    if canal is None:
        return

    if canal.id in _boss_ativo_no_canal:
        aviso = await ctx.send(
            "🌟 **Celestia:** Já tem um boss ativo por lá!! Espera esse terminar!! 😅🌸"
        )
        asyncio.create_task(_apagar_mensagem_depois(aviso))
        return

    _boss_ativo_no_canal.add(canal.id)

    embed = discord.Embed(
        title="🐙 NÍVEL MÍTICO — CTHULHU DESPERTOU NOS ABISMOS!!",
        description=(
            "🌑 **Aeon:** ...o oceano racha e algo imensurável abre os olhos pela primeira vez em "
            "eras. Ele nem se dá ao trabalho de se levantar por completo. 🖤🌊\n\n"
            "🐙 **Cthulhu:** *\"Mortais... e suas criaturinhas fracas. Não me insultem com o que "
            "vocês chamam de 'comum'. Só as suas Lendárias são dignas de olhar pra mim — as demais, "
            "eu nem enxergo.\"*\n\n"
            "🌟 **Celestia:** GENTE ELE SÓ ACEITA CRIATURA 🟡 LENDÁRIA!! 😨🌟 E AINDA POR CIMA É "
            "NÍVEL **MÍTICO**, O MAIS FORTE DE TODOS OS BOSSES!! Sozinho ou em grupo?? Quanto mais "
            "gente, MUITO mais chance!! ✨\n\n"
            f"⏳ Vocês têm `{_BOSS4_TEMPO_ESCOLHA}s` pra decidir."
        ),
        color=0x0d2b2e,
    )
    embed.set_image(url=_BOSS4_CTHULHU_INTRO_GIF)
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Nível Mítico: Cthulhu, o Ancião dos Abismos")

    view = Boss4EscolhaView(canal)
    msg = await canal.send(embed=embed, view=view)
    view.mensagem = msg
    asyncio.create_task(_apagar_mensagem_depois(msg))


# ══════════════════════════════════════════════════════════════════════
# BOSS 5 — Kaelith, a Ceifadora dos Reis
# A própria Morte em pessoa — tão temida quanto Dourakhar (boss2), mas
# ligeiramente mais fraca que ele: Dourakhar continua sendo o boss mais
# forte de todos. Mesma lógica de sempre (encarar sozinho ou chamar o
# time todo), nível mítico.
#
# Kaelith não dá tanto XP quanto os outros bosses — é a recompensa de XP
# mais modesta de todas — mas compensa com dois prêmios extras pra quem
# vence: um Booster de XP de 10 minutos (o mais longo de todos os bosses)
# e uma CHANCE de vir junto um 🥚 ovo aleatório, sorteado só entre
# criaturas 🟣 Épicas e 🟡 Lendárias. Se a criatura que sair já estiver na
# coleção da pessoa, em vez de não fazer nada ela sobe 1 Nível de
# Capacidade (mesma lógica de .uparcriatura), travado no teto máximo.
# ══════════════════════════════════════════════════════════════════════

# ⚠️ Esses gifs são links temporários do CDN do Discord (parâmetros ?ex=...),
# que expiram sozinhos depois de um tempo (geralmente ~24h-48h). Se pararem
# de aparecer nos embeds, pegue links novos (clique direito na imagem no
# Discord > Copiar link) e troque aqui embaixo — ou, melhor ainda, subam
# os gifs num host permanente (imgur, ibb.co etc.) pra nunca mais precisar trocar.
_BOSS5_KAELITH_INTRO_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1531429255978942464/1785191174797.gif?ex=6a692e23&is=6a67dca3&hm=a82d8cbf2e94d0f9fda33c4a8ee2aa985bcbbb8763d0118cd08c8b333910bb2a&"
_BOSS5_KAELITH_BATALHA_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1531429255328698379/1785191374952.gif?ex=6a692e23&is=6a67dca3&hm=6229f85c09a13d8deb3ae310b676f4191af497c9a7cc2d27ccc709475f1ac7a4&"

_BOSS5_CANAL_ID = _BOSS_CANAL_ID   # mesmo canal dos outros bosses — só aparece aqui

_BOSS5_TEMPO_ESCOLHA      = 60   # segundos pra decidir "todos juntos" ou "sozinho"
_BOSS5_TEMPO_RECRUTAMENTO = 10   # segundos pra galera clicar "quero participar" depois de "todos juntos"

# Booster exclusivo de Kaelith: o MAIS LONGO de todos os bosses (10 min),
# uma forma de compensar o XP mais baixo que ela dá.
_BOSS5_BOOSTER_MINUTOS = 10

# Nível mítico, ligeiramente mais fácil que Dourakhar (boss2) em todos os
# números — mas ainda o segundo boss mais difícil do servidor.
_BOSS5_CHANCE_SOLO = 0.012   # 1.2% — um pouco mais generoso que o 1% de Dourakhar

_BOSS5_CHANCE_GRUPO_BASE      = 0.055
_BOSS5_CHANCE_GRUPO_MAX       = 0.48
_BOSS5_BONUS_POR_PARTICIPANTE = 0.019
_BOSS5_BONUS_RARIDADE_CRIATURA = {
    "comum": 0.0, "raro": 0.01, "epico": 0.018, "lendario": 0.03, "secreto": 0.045, "mitico": 0.06,
}

# XP mais modesto que qualquer outro boss — Kaelith compensa com o Booster
# de 10 min e a chance de ovo Épico/Lendário, não com XP bruto.
_BOSS5_XP_GANHO_MIN = 0.15    # 15% — mínimo de XP que quem vence pode ganhar (o mais baixo de todos os bosses)
_BOSS5_XP_GANHO_MAX = 0.45    # 45% — máximo de XP que quem vence pode ganhar
_BOSS5_XP_GANHO_SEM_XP = (20, 55)   # recompensa fixa pra quem ainda não tem XP acumulado
_BOSS5_XP_GANHO_TETO = 2000    # teto máximo de XP por vitória — o menor de todos os bosses

# 🥚 Chance de vir um ovo junto com a vitória, sorteado só entre criaturas
# 🟣 Épicas e 🟡 Lendárias (pool restrito — nunca sai Comum/Rara/Mítica/etc
# desse ovo). Ajuste esse número se quiser o ovo mais raro ou mais comum.
_BOSS5_CHANCE_OVO = 0.35   # 35% de chance por vencedor
_BOSS5_OVO_RARIDADES = ("epico", "lendario")


def _boss5_chance_grupo(convocacoes: list) -> float:
    """Calcula a chance de vitória do grupo contra Kaelith: base + um
    bônus por pessoa + um bônus pela raridade de cada criatura convocada,
    sempre travado no teto de _BOSS5_CHANCE_GRUPO_MAX — ligeiramente mais
    generoso que Dourakhar (boss2), mas ainda nível mítico."""
    chance = _BOSS5_CHANCE_GRUPO_BASE + len(convocacoes) * _BOSS5_BONUS_POR_PARTICIPANTE
    for _membro, criatura in convocacoes:
        chance += _BOSS5_BONUS_RARIDADE_CRIATURA.get(criatura["raridade"], 0.0)
    return min(chance, _BOSS5_CHANCE_GRUPO_MAX)


def _boss5_calcular_ganho_xp(user_id: int) -> tuple:
    """Sorteia quanto de XP essa pessoa ganha por vencer Kaelith: entre 15%
    e 45% do XP que ela já tem — a faixa mais baixa entre todos os bosses —
    travado num teto máximo (_BOSS5_XP_GANHO_TETO) pra não deixar quem já é
    rank alto disparar cada vez mais na frente — ou uma recompensa fixa se
    ainda não tiver XP nenhum acumulado."""
    dados = xp_stats[user_id]
    xp_atual = dados.get("xp", 0)
    if xp_atual > 0:
        percentual = random.uniform(_BOSS5_XP_GANHO_MIN, _BOSS5_XP_GANHO_MAX)
        ganho = max(1, round(xp_atual * percentual))
        ganho = min(ganho, _BOSS5_XP_GANHO_TETO)
    else:
        percentual = 0.0
        ganho = random.randint(*_BOSS5_XP_GANHO_SEM_XP)
    return ganho, percentual


def _boss5_sortear_criatura_ovo() -> dict:
    """Sorteia uma criatura aleatória só entre 🟣 Épicas e 🟡 Lendárias
    (ponderada pelo peso normal de raridade) — é essa a criatura que pode
    vir no ovo de Kaelith."""
    pool = [c for c in _BATALHA_CRIATURAS if c["raridade"] in _BOSS5_OVO_RARIDADES]
    pesos = [_RARIDADES[c["raridade"]]["peso"] for c in pool]
    return random.choices(pool, weights=pesos, k=1)[0]


def _boss5_conceder_ovo(user_id: int) -> dict:
    """Sorteia o ovo de Kaelith pra essa pessoa (só Épica ou Lendária). Se
    ela ainda não tiver essa criatura, ela é adicionada normalmente à
    coleção. Se ela JÁ tiver (repetida), em vez de não fazer nada, a
    criatura sobe 1 Nível de Capacidade — empurrando os usos pro limiar do
    próximo nível, igual `.uparcriatura` — travado no teto máximo (se já
    estiver no máximo, o ovo simplesmente não muda nada). Devolve um dict
    com `criatura`, `era_nova`, `nivel_novo` (ou None se era nova) e
    `upou` (True se realmente subiu de nível agora)."""
    criatura = _boss5_sortear_criatura_ovo()
    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])

    if criatura["id"] not in dados["criaturas"]:
        dados["criaturas"].append(criatura["id"])
        return {"criatura": criatura, "era_nova": True, "nivel_novo": None, "upou": False}

    teto = _nivel_criatura_max(criatura["id"])
    nivel_atual = _nivel_criatura(user_id, criatura["id"])
    if nivel_atual >= teto:
        return {"criatura": criatura, "era_nova": False, "nivel_novo": nivel_atual, "upou": False}

    tabela = (
        _NIVEL_CRIATURA_USOS_ACUMULADOS_ESTENDIDO
        if criatura["id"] in _NIVEL_CRIATURA_MAX_ESPECIAL
        else _NIVEL_CRIATURA_USOS_ACUMULADOS
    )
    dados.setdefault("usos_criaturas", {})
    dados["usos_criaturas"][criatura["id"]] = max(
        dados["usos_criaturas"].get(criatura["id"], 0),
        tabela[nivel_atual],   # limiar de usos mínimos pro PRÓXIMO nível
    )
    nivel_novo = _calcular_nivel_criatura(dados["usos_criaturas"][criatura["id"]], criatura["id"])
    return {"criatura": criatura, "era_nova": False, "nivel_novo": nivel_novo, "upou": True}


def _boss5_texto_ovo(membro: discord.Member, resultado_ovo: dict) -> str:
    """Monta a linha de texto que descreve o que aconteceu com o ovo de
    Kaelith de `membro`, pra ser encaixada no embed de resultado."""
    criatura = resultado_ovo["criatura"]
    info = _RARIDADES[criatura["raridade"]]
    if resultado_ovo["era_nova"]:
        return (
            f"🥚✨ O ovo de {membro.mention} choca na hora e revela {info['emoji']} "
            f"**{criatura['nome']}** (*{info['label']}*) — nova na coleção!"
        )
    if resultado_ovo["upou"]:
        return (
            f"🥚⭐ O ovo de {membro.mention} revela {info['emoji']} **{criatura['nome']}**, que "
            f"ela já tinha — a criatura sobe pro Nível de Capacidade `{resultado_ovo['nivel_novo']}`!"
        )
    return (
        f"🥚 O ovo de {membro.mention} revela {info['emoji']} **{criatura['nome']}**, mas ela já "
        f"estava no Nível de Capacidade máximo — nada mudou dessa vez."
    )


async def _boss5_premiar_vencedores(guild: discord.Guild, vencedores: list) -> list:
    """Aplica o ganho de XP de cada vencedor (a faixa mais baixa entre
    todos os bosses), ativa o Booster de XP de _BOSS5_BOOSTER_MINUTOS (10
    min — o mais longo de todos), atualiza nível e dispara o aviso de
    level up quando for o caso. Além disso, sorteia pra CADA vencedor uma
    chance (`_BOSS5_CHANCE_OVO`) de vir junto um 🥚 ovo Épico ou Lendário.
    Devolve uma lista de (membro, ganho, percentual, resultado_ovo|None)."""
    resultados = []
    for membro in vencedores:
        dados = xp_stats[membro.id]
        nivel_antigo = dados["nivel"]
        ganho, percentual = _boss5_calcular_ganho_xp(membro.id)
        dados["xp"] += ganho
        dados["nivel"], _, _ = _calcular_nivel(dados["xp"])
        if dados["nivel"] > nivel_antigo and guild is not None:
            asyncio.create_task(_anunciar_level_up(guild, membro, dados["nivel"]))
        # 🎁 Bônus de Kaelith: Booster de XP de 10 minutos (o mais longo de
        # todos os bosses) pra quem venceu.
        _conceder_xp_booster(membro.id, _BOSS5_BOOSTER_MINUTOS)

        # 🥚 Chance de ovo Épico/Lendário — só pra quem venceu.
        resultado_ovo = None
        if random.random() < _BOSS5_CHANCE_OVO:
            resultado_ovo = _boss5_conceder_ovo(membro.id)

        resultados.append((membro, ganho, percentual, resultado_ovo))

    asyncio.create_task(_salvar_xp_stats())
    asyncio.create_task(_atualizar_ranking_xp())

    for membro, ganho, percentual, resultado_ovo in resultados:
        detalhe_ovo = ""
        if resultado_ovo is not None:
            info = _RARIDADES[resultado_ovo["criatura"]["raridade"]]
            detalhe_ovo = f" + 🥚 ovo revelou {info['emoji']} {resultado_ovo['criatura']['nome']}"
        asyncio.create_task(_log_rpg(
            guild,
            "☠️ Recompensa — Kaelith",
            f"✨ **{membro.display_name}** ganhou **`{ganho}` XP** (`{percentual * 100:.1f}%`) + "
            f"⚡ Booster de XP de `{_BOSS5_BOOSTER_MINUTOS}min` por vencer Kaelith{detalhe_ovo}.",
        ))

    return resultados


async def _boss5_batalha_solo(canal: discord.TextChannel, membro: discord.Member) -> None:
    """Roda o confronto solo contra Kaelith: só 1.2% de chance de vitória —
    e se perder, não perde XP nenhum, só o orgulho."""
    try:
        criatura = _boss_criatura_mais_forte(membro.id)
        info_raridade = _RARIDADES[criatura["raridade"]]

        embed_convocacao = discord.Embed(
            title="💀👑 Um desafiante solitário ousa se apresentar!",
            description=(
                f"🌑 **Aeon:** ...{membro.mention} decidiu encarar Kaelith sozinho. As sombras "
                f"observam em silêncio — nem elas sabem se isso é coragem. 🖤⚰️\n"
                f"🌟 **Celestia:** {membro.display_name} convoca {info_raridade['emoji']} "
                f"**{criatura['nome']}**!! É NÍVEL MÍTICO, cuidado!! 😳🌟✨"
            ),
            color=info_raridade["cor"],
        )
        embed_convocacao.set_thumbnail(url=criatura["gif"])
        msg1 = await canal.send(embed=embed_convocacao)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "💀 **Kaelith:** *\"Coroas caem como folhas no outono diante da minha foice. "
                "Você nem usa uma... mas eu ainda assim vim colher.\"*"
            ),
            color=0x1c1128,
        )
        embed_batalha.set_image(url=_BOSS5_KAELITH_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        venceu = random.random() < _BOSS5_CHANCE_SOLO

        if venceu:
            resultados = await _boss5_premiar_vencedores(canal.guild, [membro])
            _, ganho, percentual, resultado_ovo = resultados[0]
            descricao = (
                f"🏆 **A CEIFADORA FOI CEIFADA!!** {membro.mention} e {info_raridade['emoji']} "
                f"**{criatura['nome']}** derrubaram **KAELITH, A CEIFADORA DOS REIS**, SOZINHOS!! "
                f"Só `{_BOSS5_CHANCE_SOLO * 100:.1f}%` de chance!! ☠️⚔️\n\n"
                f"✨ Recompensa: **`+{ganho}` XP** (`{percentual * 100:.1f}%`) + ⚡ **Booster de XP "
                f"{_BOSS5_BOOSTER_MINUTOS}min**!\n"
            )
            if resultado_ovo is not None:
                descricao += _boss5_texto_ovo(membro, resultado_ovo) + "\n"
            descricao += (
                f"\n🌑 **Aeon:** ...até a própria Morte hesitou por um segundo. As sombras "
                f"guardarão isso. 🖤⚰️\n"
                f"🌟 **Celestia:** VOCÊ CEIFOU A CEIFADORA!! 😭🌟🤍✨ ISSO VAI VIRAR LENDA!!"
            )
            cor = 0xf5c542
        else:
            descricao = (
                f"💀 **Kaelith:** *\"...como sempre.\"* {info_raridade['emoji']} **{criatura['nome']}** "
                f"caiu em batalha, e {membro.mention} não conseguiu sozinho dessa vez.\n\n"
                f"🍃 Nenhum XP foi perdido — só a derrota amarga mesmo.\n\n"
                f"🌑 **Aeon:** ...era esperado. Poucos sobrevivem sozinhos a uma foice dessas. 🖤🌑\n"
                f"🌟 **Celestia:** Não desanima!! 🌸😢 Contra ela, é MUITO melhor ir em grupo!!"
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="🌑 Aeon & ☀️ Celestia — Kaelith, a Ceifadora dos Reis")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


async def _boss5_batalha_grupo(canal: discord.TextChannel, participantes: list) -> None:
    """Roda o confronto em grupo contra Kaelith: cada participante convoca
    a criatura mais forte que já desbloqueou, e a chance de vitória cresce
    com o número (e a força) das criaturas convocadas — nível mítico,
    ligeiramente mais fácil que Dourakhar (boss2), mas ainda muito difícil."""
    try:
        convocacoes = [(p, _boss_criatura_mais_forte(p.id)) for p in participantes]

        embed_cabecalho = discord.Embed(
            title=f"⚔️ {len(convocacoes)} guerreiro(a)s ousam encarar a Ceifadora!",
            description=(
                "🌟 **Celestia:** ESSE TIME TÁ INDO CONTRA O NÍVEL MÍTICO!! 😱🌟✨ Boa sorte "
                "pra todos!!"
            ),
            color=0x1c1128,
        )
        cards = _boss_cards_criaturas(convocacoes)

        # 1º lote: cabeçalho + até 9 cards (10 embeds é o limite do Discord por
        # mensagem). O resto (grupos grandes) sai em mensagens seguintes.
        lote = [embed_cabecalho] + cards[:9]
        restante = cards[9:]
        msg1 = await canal.send(embeds=lote)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        while restante:
            msg_extra = await canal.send(embeds=restante[:10])
            asyncio.create_task(_apagar_mensagem_depois(msg_extra))
            restante = restante[10:]
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "💀 **Kaelith:** *\"Um exército inteiro... pra proteger reis que já estão mortos "
                "e ainda não sabem. Venham, então — a colheita será generosa hoje.\"*"
            ),
            color=0x1c1128,
        )
        embed_batalha.set_image(url=_BOSS5_KAELITH_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        chance = _boss5_chance_grupo(convocacoes)
        venceu = random.random() < chance

        if venceu:
            resultados = await _boss5_premiar_vencedores(canal.guild, participantes)
            texto_ganhos = "\n".join(
                f"✨ {membro.mention} +`{ganho}` XP (`{percentual * 100:.1f}%`) ⚡"
                for membro, ganho, percentual, _ovo in resultados
            )
            textos_ovo = "\n".join(
                _boss5_texto_ovo(membro, resultado_ovo)
                for membro, _g, _p, resultado_ovo in resultados
                if resultado_ovo is not None
            )
            descricao = (
                f"🏆 **A CEIFADORA FOI CEIFADA!!** O time de `{len(participantes)}` guerreiro(a)s "
                f"derrubou **KAELITH, A CEIFADORA DOS REIS**!! (chance da batalha: `{chance * 100:.0f}%`) "
                f"☠️⚔️\n\n"
                f"{texto_ganhos}\n\n"
                f"⚡ Todos os vencedores também ganharam um **Booster de XP de {_BOSS5_BOOSTER_MINUTOS} "
                f"minutos** (xp de call e mensagem em dobro)!"
            )
            if textos_ovo:
                descricao += f"\n\n{textos_ovo}"
            descricao += (
                f"\n\n🌑 **Aeon:** ...nem a própria Morte esperava perder pra formigas organizadas. "
                f"As sombras se curvam. 🖤⚰️\n"
                f"🌟 **Celestia:** VOCÊS CEIFARAM A CEIFADORA!!! 😭🌟🤍✨ ISSO VAI FICAR NA HISTÓRIA!!"
            )
            cor = 0xf5c542
        else:
            mencoes = ", ".join(p.mention for p in participantes)
            descricao = (
                f"💀 **Kaelith:** *\"...voltem quando forem mais próximos da realeza que eu venho "
                f"colher.\"* Mesmo com `{len(participantes)}` guerreiro(a)s juntos (`{chance * 100:.0f}%` "
                f"de chance), a Ceifadora dos Reis foi forte demais dessa vez. {mencoes} não "
                f"conseguiram.\n\n"
                f"🍃 Ninguém perdeu XP — só a derrota amarga mesmo.\n\n"
                f"🌑 **Aeon:** ...nível mítico não perdoa fácil. As sombras respeitam a tentativa. 🖤🌑\n"
                f"🌟 **Celestia:** Vamos treinar e tentar de novo!! 🌸💫 Chamem mais gente!!"
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="🌑 Aeon & ☀️ Celestia — Kaelith, a Ceifadora dos Reis")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


class Boss5RecrutamentoView(discord.ui.View):
    """Botão único de 'Quero Participar!' que fica ativo por
    _BOSS5_TEMPO_RECRUTAMENTO segundos, juntando o time que vai enfrentar
    Kaelith em conjunto. Quando o tempo acaba, a batalha começa sozinha."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS5_TEMPO_RECRUTAMENTO)
        self.canal = canal
        self.participantes: dict = {}   # user_id -> discord.Member
        self.mensagem: discord.Message = None

    @discord.ui.button(label="⚔️ Quero Participar!", style=discord.ButtonStyle.success)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if interaction.user.id in self.participantes:
            await interaction.response.send_message(
                "🌟 **Celestia:** Você já tá na lista, guerreiro(a)!! 😆🌸", ephemeral=True
            )
            return

        self.participantes[interaction.user.id] = interaction.user
        button.label = f"⚔️ Quero Participar! ({len(self.participantes)})"
        await interaction.response.edit_message(view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.mensagem:
                await self.mensagem.edit(view=self)
        except discord.HTTPException:
            pass

        participantes = list(self.participantes.values())
        if not participantes:
            try:
                msg = await self.canal.send(
                    "🌑 **Aeon:** ...ninguém teve coragem de se juntar a tempo. Kaelith sorri e "
                    "se dissolve de volta nas sombras... por enquanto. 🖤⚰️"
                )
                asyncio.create_task(_apagar_mensagem_depois(msg))
            finally:
                _boss_ativo_no_canal.discard(self.canal.id)
            return

        asyncio.create_task(_boss5_batalha_grupo(self.canal, participantes))


class Boss5EscolhaView(discord.ui.View):
    """Botões de 'Todos Juntos' e 'Eu Consigo Sozinho' que aparecem quando
    Kaelith surge. A PRIMEIRA escolha feita (por qualquer pessoa) decide
    o caminho dessa aparição do boss."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS5_TEMPO_ESCOLHA)
        self.canal = canal
        self.decidido = False
        self.mensagem: discord.Message = None

    def _travar_botoes(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="🤝 Todos Juntos", style=discord.ButtonStyle.primary)
    async def todos_juntos(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "🌑 **Aeon:** ...essa decisão já foi tomada. 🖤🌑", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🤝 O CHAMADO FOI FEITO!",
            description=(
                f"🌟 **Celestia:** {interaction.user.mention} decidiu enfrentar Kaelith EM "
                f"GRUPO!! 😱🌟✨\n"
                f"🌑 **Aeon:** ...quem tiver coragem, clique no botão abaixo. `{_BOSS5_TEMPO_RECRUTAMENTO}s` "
                f"pra se juntar ao time. 🖤⚰️"
            ),
            color=0xff8800,
        )
        embed.set_image(url=_BOSS5_KAELITH_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        view_recrutamento = Boss5RecrutamentoView(self.canal)
        msg_recrutamento = await self.canal.send(
            "☠️ Time contra **Kaelith, a Ceifadora dos Reis** — clique pra participar!",
            view=view_recrutamento,
        )
        view_recrutamento.mensagem = msg_recrutamento
        asyncio.create_task(_apagar_mensagem_depois(msg_recrutamento))

    @discord.ui.button(label="🗡️ Eu Consigo Sozinho", style=discord.ButtonStyle.danger)
    async def sozinho(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "🌑 **Aeon:** ...essa decisão já foi tomada. 🖤🌑", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🗡️ DESAFIO SOLITÁRIO ACEITO!",
            description=(
                f"🌑 **Aeon:** ...{interaction.user.mention} escolheu encarar Kaelith sozinho. "
                f"Isso não é coragem, isso é desafiar a própria Morte de frente. 🖤⚰️\n"
                f"🌟 **Celestia:** SÓ `{_BOSS5_CHANCE_SOLO * 100:.1f}%` DE CHANCE?!?! 😰🌟 É NÍVEL "
                f"MÍTICO, TEM CERTEZA?!"
            ),
            color=0xff4444,
        )
        embed.set_image(url=_BOSS5_KAELITH_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        asyncio.create_task(_boss5_batalha_solo(self.canal, interaction.user))

    async def on_timeout(self):
        if self.decidido or self.mensagem is None:
            return
        self._travar_botoes()
        try:
            embed = discord.Embed(
                title="⚰️ Kaelith se dissolve nas sombras...",
                description=(
                    "🌑 **Aeon:** ...ninguém teve coragem de decidir a tempo. A Ceifadora dos "
                    "Reis se retira... por enquanto. 🖤⚰️"
                ),
                color=0x888888,
            )
            await self.mensagem.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass
        _boss_ativo_no_canal.discard(self.canal.id)


@bot.command(name="boss5")
async def cmd_boss5(ctx):
    """☠️👑 Invoca Kaelith, a Ceifadora dos Reis — nível mítico, ligeiramente
    mais fraca que Dourakhar (boss2, o boss mais forte de todos), mas ainda
    um dos bosses mais difíceis do servidor. Só o Reality (CRIADOR_ID) pode
    chamar. O chat escolhe entre encarar sozinho (~1.2% de chance) ou juntar
    um time (mais gente = mais chance). Quem vencer ganha o XP mais modesto
    entre todos os bosses, mas leva um Booster de XP de 10 minutos — o mais
    longo de todos — e tem 35% de chance de vir junto um 🥚 ovo aleatório
    entre criaturas Épicas e Lendárias (se for repetido, a criatura sobe de
    Nível de Capacidade em vez de não fazer nada). Uso: .boss5"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BOSS5_CANAL_ID)
    if canal is None:
        return

    if canal.id in _boss_ativo_no_canal:
        aviso = await ctx.send(
            "🌟 **Celestia:** Já tem um boss ativo por lá!! Espera esse terminar!! 😅🌸"
        )
        asyncio.create_task(_apagar_mensagem_depois(aviso))
        return

    _boss_ativo_no_canal.add(canal.id)

    embed = discord.Embed(
        title="☠️👑 NÍVEL MÍTICO — KAELITH, A CEIFADORA DOS REIS, DESPERTOU!!",
        description=(
            "🌑 **Aeon:** ...o silêncio chega antes dela. Nem o vento ousa se mexer. 🖤⚰️\n\n"
            "💀 **Kaelith:** *\"Eu sou Kaelith. Reis, impérios, coroas... tudo cai perante minha "
            "foice, mais cedo ou mais tarde. Vocês não são diferentes.\"*\n\n"
            "🌟 **Celestia:** GENTE ISSO AQUI TAMBÉM É NÍVEL **MÍTICO**!! 😨🌟 Ela é só um pouquinho "
            "mais fraca que Dourakhar, mas ainda MUITO perigosa!! Sozinho ou em grupo?? ✨\n\n"
            f"⏳ Vocês têm `{_BOSS5_TEMPO_ESCOLHA}s` pra decidir."
        ),
        color=0x1c1128,
    )
    embed.set_image(url=_BOSS5_KAELITH_INTRO_GIF)
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Nível Mítico: Kaelith, a Ceifadora dos Reis")

    view = Boss5EscolhaView(canal)
    msg = await canal.send(embed=embed, view=view)
    view.mensagem = msg
    asyncio.create_task(_apagar_mensagem_depois(msg))


@bot.command(name="surpresachat")
async def cmd_surpresachat(ctx):
    """Envia uma surpresa interativa no canal. Apenas o DEV pode usar."""
    global _surpresa_ativa

    # Só funciona no PV e apenas para o criador
    if ctx.guild is not None:
        await ctx.send(
            "🌑 **Aeon:** *pisca lentamente* ...esse comando é de uso privado. 🖤🌑 "
            "Me chame no PV."
        )
        return

    if ctx.author.id != CRIADOR_ID:
        await ctx.send(
            "🌑 **Aeon:** *olha fixamente* ...acesso negado. 🖤🌑 "
            "As trevas conhecem quem tem permissão.\n"
            "🌟 **Celestia:** Só o DEV pode usar esse comando, lindinho(a)!! 🌸🤍✨"
        )
        return

    if _surpresa_ativa:
        await ctx.send(
            "🌟 **Celestia:** Espera!! 🌸🤍 Já tem uma surpresa ativa lá no chat!! "
            "Aguarda alguém resgatar primeiro!! ✨\n"
            "🌑 **Aeon:** ...paciência. 🖤 Uma surpresa por vez."
        )
        return

    # Busca o guild a partir dos servidores onde o bot está
    canal_alvo = None
    for guild in bot.guilds:
        canal_alvo = guild.get_channel(CANAL_SURPRESA_ID)
        if canal_alvo is not None:
            break

    if canal_alvo is None:
        await ctx.send(
            "🌑 **Aeon:** *franzea levemente* ...não encontrei o canal alvo. 🖤🌑 "
            "Verifique o ID configurado.\n"
            "🌟 **Celestia:** Algo deu errado!! 😢🌸 O canal não foi encontrado!! ✨"
        )
        return

    # Marca como ativa antes de enviar
    _surpresa_ativa = True

    # Embed da surpresa no canal
    embed_surpresa = discord.Embed(
        title="🎁 SURPRESA DO CHAT!! 🎁",
        description=(
            "✨ **O chat está movimentado e merece uma recompensa especial!!** ✨\n\n"
            "🌟 **Celestia:** *aparece num flash dourado e gira animada* "
            "AAAAA GENTE!! 😭🌟🤍✨ O CHAT TÁ TÃO LINDO E MOVIMENTADO QUE A GENTE "
            "RESOLVEU FAZER UMA SURPRESINHA ESPECIAL SÓ PRA VOCÊS!! "
            "QUEM CLICAR PRIMEIRO GANHA A RECOMPENSA!! ☀️🌸💫\n\n"
            "🌑 **Aeon:** *emerge das sombras com um brilho incomum nos olhos dourados* "
            "...as trevas observaram a movimentação deste chat. 🖤🌑 "
            "E decidiram recompensar quem está presente. "
            "Um único vencedor. O mais rápido. "
            "Clique — se tiver coragem.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚡ **Seja o primeiro a clicar e ganhe a recompensa!!**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0x9b59b6
    )
    embed_surpresa.set_footer(
        text="🌑 Aeon guarda as trevas. ☀️ Celestia guia a luz. 🎁 Só um vencedor!"
    )

    await canal_alvo.send(embed=embed_surpresa, view=BotaoSurpresa())

    # Confirmação no PV do dev
    await ctx.send(
        "🌟 **Celestia:** ENVIOU!! 😭🌟🤍✨ A surpresa tá lá no chat!! "
        "Agora é só esperar o primeiro corajoso(a) clicar!! ☀️🌸💫\n"
        "🌑 **Aeon:** *ronrona discretamente* ...surpresa ativada. 🖤🌑 "
        "As trevas aguardam o primeiro a agir."
    )


_CANAIS_ESCREVA = {
    "geral": 1284257046740602901,
    "dev":   1512926077914316881,
    "cla":   1284258192414740490,
}

@bot.command(name="escreva")
async def cmd_escreva(ctx, bot_escolha: str = None, canal: str = None, *, texto: str = None):
    if ctx.guild is not None:
        return
    if ctx.author.id != CRIADOR_ID:
        return
    if not bot_escolha or not canal or not texto:
        await ctx.send(
            "uso: .escreva <aeon|celestia|kitsura|dupla> <geral|dev|cla> <mensagem>\n"
            "ex:  .escreva aeon geral *emerge das sombras* olá.\n"
            "ex:  .escreva kitsura geral *aparece de repente* 🦊"
        )
        return

    persona = bot_escolha.lower()
    if persona not in ("aeon", "celestia", "kitsura", "dupla"):
        await ctx.send("persona inválida. use: aeon, celestia, kitsura ou dupla")
        return

    canal_id = _CANAIS_ESCREVA.get(canal.lower())
    if canal_id is None:
        await ctx.send("canal inválido. use: geral, dev ou cla")
        return

    ch = bot.get_channel(canal_id)
    if ch is None:
        await ctx.send("canal não encontrado no servidor.")
        return

    if persona == "aeon":
        msg_final = f"🌑 **Aeon:** {texto}"
    elif persona == "celestia":
        msg_final = f"🌟 **Celestia:** {texto}"
    elif persona == "kitsura":
        msg_final = f"🦊 **Kitsura:** {texto}"
    else:  # dupla — separa com | entre as falas: "fala do aeon | fala da celestia"
        if "|" in texto:
            partes = texto.split("|", 1)
            msg_final = f"🌑 **Aeon:** {partes[0].strip()}\n🌟 **Celestia:** {partes[1].strip()}"
        else:
            msg_final = f"🌑 **Aeon:** {texto}\n🌟 **Celestia:** ..."

    await ch.send(msg_final)
    await ctx.message.add_reaction("✅")



# ══════════════════════════════════════════════════════════════════
# COMANDO .castigo — SOMENTE O DEV NO PV
# Aplica timeout a um membro com razão e duração customizável.
# Uso no PV: .castigo <user_id> <razão>
# ══════════════════════════════════════════════════════════════════

CANAL_CASTIGO_ID = 1284257046740602901  # canal onde o anúncio do castigo aparece


class CastigoView(discord.ui.View):
    """Painel interativo de castigo — enviado no PV do dev."""

    def __init__(self, alvo_id: int, razao: str, alvo_nome: str):
        super().__init__(timeout=180)
        self.alvo_id         = alvo_id
        self.razao           = razao
        self.alvo_nome       = alvo_nome
        self.notificar_death = False
        self.aplicado        = False

    # ── Toggle: Notificar Death ──────────────────────────────────────────────
    @discord.ui.button(
        label="👑 Notificar Death: OFF",
        style=discord.ButtonStyle.secondary,
        custom_id="castigo_toggle_death",
        row=0
    )
    async def toggle_death(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.notificar_death = not self.notificar_death
        button.label = f"👑 Notificar Death: {'ON ✅' if self.notificar_death else 'OFF'}"
        button.style = (
            discord.ButtonStyle.success if self.notificar_death
            else discord.ButtonStyle.secondary
        )
        await interaction.response.edit_message(view=self)

    # ── Helper: aplica o castigo ─────────────────────────────────────────────
    async def _aplicar(self, interaction: discord.Interaction, minutos: int):
        if self.aplicado:
            await interaction.response.send_message("⚠️ Castigo já foi aplicado.")
            return
        self.aplicado = True

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

        guild = bot.guilds[0] if bot.guilds else None
        if guild is None:
            await interaction.followup.send("❌ Servidor não encontrado.")
            return

        alvo = guild.get_member(self.alvo_id)
        if alvo is None:
            try:
                alvo = await guild.fetch_member(self.alvo_id)
            except discord.NotFound:
                await interaction.followup.send(
                    f"❌ Membro `{self.alvo_id}` não encontrado no servidor."
                )
                return

        until = discord.utils.utcnow() + timedelta(minutes=minutos)
        try:
            await alvo.timeout(until, reason=self.razao)
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Sem permissão para castigar esse membro. "
                "(O bot precisa de `Moderar Membros`)"
            )
            return

        if minutos < 60:
            duracao_txt = f"{minutos} minuto{'s' if minutos > 1 else ''}"
        else:
            h = minutos // 60
            duracao_txt = f"{h} hora{'s' if h > 1 else ''}"

        canal_pub = guild.get_channel(CANAL_CASTIGO_ID)
        if canal_pub:
            BR = timezone(timedelta(hours=-3))
            agora = discord.utils.utcnow().astimezone(BR).strftime("%d/%m/%Y %H:%M")

            embed_pub = discord.Embed(
                title="⚠️ Chamada de Atenção",
                color=0xff4444
            )
            embed_pub.add_field(
                name="Membro",
                value=f"{alvo.mention}\n`{alvo.display_name}`",
                inline=True
            )
            embed_pub.add_field(
                name="Punição",
                value=f"🔇 {duracao_txt}\n*(sem texto e sem calls)*",
                inline=True
            )
            embed_pub.add_field(name="\u200b", value="\u200b", inline=True)
            embed_pub.add_field(name="Motivo", value=self.razao, inline=False)
            embed_pub.set_footer(
                text=f"🌑 Aeon guarda as trevas. ☀️ Celestia guia a luz. ⚠️ Moderação • {agora}"
            )

            conteudo = f"<@{DEATH_ID}>" if self.notificar_death else None
            await canal_pub.send(content=conteudo, embed=embed_pub)

        confirmacao = (
            f"✅ **Castigo aplicado!**\n"
            f"👤 **{alvo.display_name}** (`{alvo.id}`)\n"
            f"🔇 Duração: **{duracao_txt}**\n"
            f"📝 Motivo: {self.razao}\n"
        )
        if self.notificar_death:
            confirmacao += "👑 **Death foi notificada no canal!**"
        await interaction.followup.send(confirmacao)
        self.stop()

    # ── Botões de duração ────────────────────────────────────────────────────
    @discord.ui.button(
        label="🕐 5 min",
        style=discord.ButtonStyle.danger,
        custom_id="castigo_dur_5",
        row=1
    )
    async def cinco_min(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._aplicar(interaction, 5)

    @discord.ui.button(
        label="🕐 10 min",
        style=discord.ButtonStyle.danger,
        custom_id="castigo_dur_10",
        row=1
    )
    async def dez_min(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._aplicar(interaction, 10)

    @discord.ui.button(
        label="🕐 30 min",
        style=discord.ButtonStyle.danger,
        custom_id="castigo_dur_30",
        row=1
    )
    async def trinta_min(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._aplicar(interaction, 30)

    @discord.ui.button(
        label="🕑 1 hora",
        style=discord.ButtonStyle.danger,
        custom_id="castigo_dur_60",
        row=2
    )
    async def uma_hora(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._aplicar(interaction, 60)

    @discord.ui.button(
        label="❌ Cancelar",
        style=discord.ButtonStyle.secondary,
        custom_id="castigo_cancelar",
        row=2
    )
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.aplicado = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="❌ Castigo cancelado.", view=self)
        self.stop()


@bot.command(name="castigo")
async def cmd_castigo(ctx, alvo_id: int = None, *, razao: str = None):
    """Aplica castigo a um membro. Uso no PV: .castigo <user_id> <razão>"""

    if ctx.guild is not None:
        await ctx.send(
            "🌑 **Aeon:** *pisca lentamente* ...esse comando é de uso privado. 🖤🌑 "
            "Me chame no PV."
        )
        return

    if ctx.author.id != CRIADOR_ID:
        await ctx.send(
            "🌑 **Aeon:** *olha fixamente* ...acesso negado. 🖤🌑\n"
            "🌟 **Celestia:** Só o DEV pode usar esse comando!! 🌸🤍✨"
        )
        return

    if alvo_id is None or razao is None:
        await ctx.send(
            "⚠️ **Uso correto:** `.castigo <ID do membro> <razão>`\n"
            "Exemplo: `.castigo 123456789 Spam repetido no chat geral`"
        )
        return

    guild = bot.guilds[0] if bot.guilds else None
    alvo  = guild.get_member(alvo_id) if guild else None
    if alvo is None and guild:
        try:
            alvo = await guild.fetch_member(alvo_id)
        except discord.NotFound:
            await ctx.send(f"❌ Membro com ID `{alvo_id}` não encontrado no servidor.")
            return

    alvo_nome = alvo.display_name if alvo else str(alvo_id)

    embed_preview = discord.Embed(
        title="⚠️ Painel de Castigo",
        description=(
            f"👤 **Membro:** {alvo.mention if alvo else f'`{alvo_id}`'} — `{alvo_nome}`\n"
            f"📝 **Razão:** {razao}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Escolha a duração — o membro ficará **sem texto e sem call**.\n"
            "Ative **👑 Notificar Death** para ela ser pingada no anúncio.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xff4444
    )
    embed_preview.set_footer(text="🌑 Aeon & ☀️ Celestia — Sistema de Moderação")

    await ctx.send(embed=embed_preview, view=CastigoView(alvo_id, razao, alvo_nome))


# ══════════════════════════════════════════════════════════════════
# COMANDO .puniçãocall — Prende um membro numa call específica por um tempo
# Uso: .puniçãocall <ID do membro> <duração>
# A duração é em MINUTOS — número puro (ex: 45) ou no formato MM:SS
# (ex: 1:00 = 1 minuto, 30:00 = 30 minutos) ou HH:MM:SS (ex: 1:30:00 = 1h30).
# Toda vez que o membro tentar entrar em QUALQUER call do servidor, ele é
# puxado de volta pra call de punição. A punição expira sozinha depois do
# tempo definido. Além disso, no momento em que a punição é aplicada, a
# pessoa PERDE pontos — a mesma quantidade que ganharia normalmente ficando
# aquele tempo numa call — tanto do Ranking Anjo (semanal/mensal/diário)
# quanto do Ranking/XP geral. Só o CRIADOR_ID e a DEATH_ID podem usar.
# ══════════════════════════════════════════════════════════════════

CANAL_PUNICAO_CALL_ID = 1531446371159113798

# { user_id: datetime (UTC) de quando a punição expira }
_punicoes_call: dict = {}


def _parse_duracao_punicao(texto: str):
    """Converte a duração digitada num comando de punição pra timedelta.
    Aceita:
      • Número puro = MINUTOS (ex: "45" -> 45 minutos)
      • "MM:SS" = minutos e segundos (ex: "1:00" -> 1 minuto, "30:00" -> 30 minutos)
      • "HH:MM:SS" = horas, minutos e segundos (ex: "1:30:00" -> 1h30min)
    Devolve None se o texto não puder ser interpretado ou o resultado for <= 0."""
    if not texto:
        return None
    texto = texto.strip()
    try:
        if ":" in texto:
            partes = texto.split(":")
            if len(partes) == 2:
                horas_extra = 0
                minutos_str, segundos_str = partes
            elif len(partes) == 3:
                horas_str, minutos_str, segundos_str = partes
                horas_extra = int(horas_str)
            else:
                return None
            minutos = int(minutos_str)
            segundos = int(segundos_str)
            if horas_extra < 0 or minutos < 0 or segundos < 0 or segundos >= 60:
                return None
            total_segundos = horas_extra * 3600 + minutos * 60 + segundos
        else:
            total_segundos = float(texto) * 60  # número puro = minutos
    except ValueError:
        return None

    if total_segundos <= 0:
        return None
    return timedelta(seconds=total_segundos)


@tasks.loop(seconds=30)
async def loop_checar_punicoes_call():
    """A cada 30s, libera quem já cumpriu o tempo de punição."""
    agora = datetime.now(timezone.utc)
    expirados = [uid for uid, expira in _punicoes_call.items() if agora >= expira]

    for uid in expirados:
        _punicoes_call.pop(uid, None)
        for guild in bot.guilds:
            membro = guild.get_member(uid)
            if membro:
                print(f"[puniçãocall] Punição de {membro} ({uid}) expirou. Liberado(a).")
                break


@bot.listen("on_voice_state_update")
async def _forcar_punicao_call(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
):
    """Enquanto o membro estiver de puniçãocall, ele é puxado de volta pra
    call de punição toda vez que entrar em qualquer outra call."""
    if member.id not in _punicoes_call:
        return

    # Punição já venceu — libera e não faz nada
    if datetime.now(timezone.utc) >= _punicoes_call[member.id]:
        _punicoes_call.pop(member.id, None)
        return

    # Não entrou em call nenhuma agora (ex: só saiu) — nada a fazer
    if after.channel is None:
        return

    # Já está na call de punição — tudo certo
    if after.channel.id == CANAL_PUNICAO_CALL_ID:
        return

    canal_punicao = member.guild.get_channel(CANAL_PUNICAO_CALL_ID)
    if canal_punicao is None:
        return

    try:
        await member.move_to(
            canal_punicao,
            reason="Puniçãocall ativa — redirecionado automaticamente."
        )
    except (discord.Forbidden, discord.HTTPException) as e:
        print(f"[puniçãocall] ERRO ao mover {member} ({member.id}) de volta: {e!r}")


@bot.command(name="puniçãocall", aliases=["punicaocall"])
async def cmd_punicao_call(ctx, alvo_id: int = None, duracao: str = None):
    """Prende um membro numa call específica por um tempo determinado, e
    remove dela a mesma quantidade de pontos que ganharia normalmente
    ficando aquele tempo numa call (Ranking Anjo + XP geral).
    Uso: .puniçãocall <ID do membro> <duração>
    A duração é em MINUTOS — número puro (ex: 45) ou formato MM:SS
    (ex: 1:00 = 1 minuto, 30:00 = 30 minutos) ou HH:MM:SS (ex: 1:30:00 = 1h30)."""

    if ctx.author.id not in (CRIADOR_ID, DEATH_ID):
        await ctx.send(
            "🌑 **Aeon:** *olha fixamente* ...acesso negado. 🖤🌑\n"
            "🌟 **Celestia:** Só o DEV ou a Death podem usar esse comando!! 🌸🤍✨"
        )
        return

    if alvo_id is None or duracao is None:
        await ctx.send(
            "⚠️ **Uso correto:** `.puniçãocall <ID do membro> <duração>`\n"
            "A duração é em **minutos**: número puro (ex: `45`) ou formato `MM:SS` "
            "(ex: `1:00` = 1 minuto, `30:00` = 30 minutos) ou `HH:MM:SS` (ex: `1:30:00` = 1h30).\n"
            "Exemplo: `.puniçãocall 123456789012345678 30:00` (30 minutos)"
        )
        return

    delta = _parse_duracao_punicao(duracao)
    if delta is None:
        await ctx.send(
            "⚠️ Duração inválida. Use minutos (ex: `45`) ou o formato `MM:SS` / `HH:MM:SS` "
            "(ex: `1:00`, `30:00`, `1:30:00`), sempre maior que zero."
        )
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        await ctx.send("⚠️ Não encontrei nenhum servidor.")
        return

    alvo = guild.get_member(alvo_id)
    if alvo is None:
        try:
            alvo = await guild.fetch_member(alvo_id)
        except discord.NotFound:
            await ctx.send(f"❌ Membro com ID `{alvo_id}` não encontrado no servidor.")
            return

    canal_punicao = guild.get_channel(CANAL_PUNICAO_CALL_ID)
    if canal_punicao is None:
        await ctx.send(f"❌ Não encontrei o canal de punição `{CANAL_PUNICAO_CALL_ID}`.")
        return

    expira_em = datetime.now(timezone.utc) + delta
    _punicoes_call[alvo_id] = expira_em

    # Se já estiver numa call agora, já manda pra call de punição na hora
    if alvo.voice is not None and alvo.voice.channel is not None:
        try:
            await alvo.move_to(canal_punicao, reason="Puniçãocall aplicada.")
        except (discord.Forbidden, discord.HTTPException):
            pass

    # ── Remove pontos: a mesma quantidade que a pessoa ganharia normalmente
    # ficando esse tempo numa call — tanto do Ranking Anjo quanto do XP geral.
    minutos_totais = delta.total_seconds() / 60

    pontos_anjo_perdidos = minutos_totais * _PESO_MINUTO_CALL
    anjo_stats_semanal[alvo_id]["penalidade"] += pontos_anjo_perdidos
    anjo_stats_mensal[alvo_id]["penalidade"]  += pontos_anjo_perdidos
    anjo_stats_diario[alvo_id]["penalidade"]  += pontos_anjo_perdidos
    await _salvar_anjo_stats()
    asyncio.create_task(_atualizar_ranking_anjo())

    xp_perdido = round(minutos_totais * _XP_POR_TICK_CALL)
    dados_xp = xp_stats[alvo_id]
    xp_novo = max(0, dados_xp["xp"] - xp_perdido)
    dados_xp["xp"] = xp_novo
    dados_xp["nivel"] = _calcular_nivel(xp_novo)[0]
    await _salvar_xp_stats()
    asyncio.create_task(_atualizar_ranking_xp())

    ts_expira = int(expira_em.timestamp())
    duracao_texto = _formatar_tempo_call(delta.total_seconds())
    await ctx.send(
        f"🌑 **Aeon:** ...{alvo.mention} agora pertence às sombras dessa call. 🖤🌑\n"
        f"🌟 **Celestia:** Toda vez que tentar fugir pra outra call, a Celestia traz de volta!! 🌸✨\n\n"
        f"👤 **Membro:** {alvo.mention} — `{alvo.display_name}`\n"
        f"🔊 **Call de punição:** <#{CANAL_PUNICAO_CALL_ID}>\n"
        f"⏱️ **Duração:** {duracao_texto} — libera <t:{ts_expira}:R> (<t:{ts_expira}:f>)\n"
        f"📉 **Pontos removidos:** `-{pontos_anjo_perdidos:.0f}` pts do Ranking Anjo "
        f"(semanal + mensal + diário) e `-{xp_perdido}` XP do ranking geral."
    )


@bot.command(name="cancelarpuniçãocall", aliases=["cancelarpunicaocall"])
async def cmd_cancelar_punicao_call(ctx, alvo_id: int = None):
    """Cancela a puniçãocall de um membro antes do tempo acabar.
    Uso: .cancelarpuniçãocall <ID do membro>"""

    if ctx.author.id not in (CRIADOR_ID, DEATH_ID):
        await ctx.send(
            "🌑 **Aeon:** *olha fixamente* ...acesso negado. 🖤🌑\n"
            "🌟 **Celestia:** Só o DEV ou a Death podem usar esse comando!! 🌸🤍✨"
        )
        return

    if alvo_id is None:
        await ctx.send(
            "⚠️ **Uso correto:** `.cancelarpuniçãocall <ID do membro>`\n"
            "Exemplo: `.cancelarpuniçãocall 123456789012345678`"
        )
        return

    if alvo_id not in _punicoes_call:
        await ctx.send(f"❌ `{alvo_id}` não está com nenhuma puniçãocall ativa no momento.")
        return

    _punicoes_call.pop(alvo_id, None)

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    alvo = guild.get_member(alvo_id) if guild else None
    alvo_texto = alvo.mention if alvo else f"`{alvo_id}`"

    await ctx.send(
        f"🌑 **Aeon:** ...as sombras soltam {alvo_texto}. 🖤🌑 Puniçãocall encerrada.\n"
        f"🌟 **Celestia:** Livre, livre!! 🌸✨ Pode ir pra qualquer call de novo!!"
    )


# ══════════════════════════════════════════════════════════════════════
# JOGO "CIDADE DORME!" — mafia/lobisomem narrado por humano ou pelo bot
#
# Gatilho: qualquer pessoa manda a frase "Jogar cidade dorme!" num canal de
# texto estando numa call. Não é comando de prefixo, é frase solta — por
# isso qualquer um pode usar, sem precisar ser o CRIADOR_ID.
#
# Papéis: 1 Assassino, 1 Anjo, 1 Detetive, o resto é Morador Comum.
# Regra de vitória (sem votação de dia — só a acusação do detetive decide):
#   • Cidade vence quando o Detetive acerta a acusação do Assassino.
#   • Assassino vence se o Detetive morrer antes disso acontecer (não há
#     mais ninguém que possa provar quem é o culpado).
#   • EXCEÇÃO — Noite 1: ninguém morre nessa noite, mesmo que o Assassino
#     tenha escolhido um alvo. Só aparece quem o Detetive suspeita, todo
#     mundo debate mais um pouco, e o Detetive decide entre confiar no
#     próprio palpite ou abrir uma votação pública (por botão) pra cidade
#     inteira decidir junto quem acusar.
# ══════════════════════════════════════════════════════════════════════

_CD_FRASES_GATILHO = {"jogar cidade dorme!", "jogar cidade dorme"}
_CD_MIN_JOGADORES = 5
_CD_MAX_JOGADORES = 20   # limite de segurança — menu de seleção do Discord aceita até 25 opções
_CD_DURACAO_NOITE = 30   # segundos que a call fica muda por noite
_CD_DURACAO_SUSPEITA = 10   # segundos da janela de "Quem vocês acham?" (botão/select)
_CD_DURACAO_VOTACAO = 20   # segundos da votação pública (só acontece depois da noite 1 especial)

_jogos_cidade_dorme: dict = {}   # { canal_texto_id: JogoCidadeDorme }


class JogoCidadeDorme:
    """Guarda todo o estado de uma partida de Cidade Dorme em andamento."""

    def __init__(self, canal_texto, canal_voz, host, numero_alvo: int):
        self.canal_texto = canal_texto
        self.canal_voz = canal_voz
        self.host = host
        self.numero_alvo = numero_alvo
        self.jogadores: list = []       # discord.Member, em ordem de entrada
        self.vivos: set = set()         # ids vivos
        self.papeis: dict = {}          # {user_id: "assassino"|"anjo"|"detetive"|"normal"}
        self.narrador_humano = None     # discord.Member ou None (bot narra)
        self.rodada = 0
        self.ativo = True
        self.alvo_assassino = None      # id escolhido na noite atual
        self.alvo_anjo = None           # id escolhido na noite atual
        self.alvo_anjo_anterior = None  # id protegido na noite passada (não pode repetir)
        self.acusacao_detetive = None   # id acusado na noite atual (ou None)
        self.sugestoes: list = []       # [(user_id, texto), ...] coletadas na fase de debate

    def id_por_papel(self, papel: str):
        for uid, p in self.papeis.items():
            if p == papel and uid in self.vivos:
                return uid
        return None

    def nome(self, uid: int) -> str:
        membro = self.canal_texto.guild.get_member(uid)
        return membro.display_name if membro else f"<@{uid}>"


# ── Lobby: entrar/sair/iniciar/cancelar ─────────────────────────────────────
class CDLobbyView(discord.ui.View):
    def __init__(self, jogo: JogoCidadeDorme):
        super().__init__(timeout=300)
        self.jogo = jogo
        self.pronto = asyncio.Event()
        self.cancelado = False

    def _montar_embed(self):
        jogo = self.jogo
        lista = "\n".join(f"• {m.mention}" for m in jogo.jogadores) or "_ninguém ainda..._"
        embed = discord.Embed(
            title="🌆 Lobby — Cidade Dorme!",
            description=(
                f"Partida aberta por {jogo.host.mention}!\n\n"
                f"👥 **Jogadores:** {len(jogo.jogadores)}/{jogo.numero_alvo}\n{lista}\n\n"
                f"Clique em **Entrar** pra participar. Mínimo de {_CD_MIN_JOGADORES} pra começar."
            ),
            color=0x2f3136,
        )
        embed.set_footer(text="🌑 Aeon & ☀️ Celestia — Cidade Dorme!")
        return embed

    @discord.ui.button(label="✅ Entrar", style=discord.ButtonStyle.success)
    async def entrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogo = self.jogo
        if interaction.user in jogo.jogadores:
            await interaction.response.send_message("Você já está na lista!", ephemeral=True)
            return
        if len(jogo.jogadores) >= jogo.numero_alvo:
            await interaction.response.send_message("O lobby já está cheio!", ephemeral=True)
            return
        jogo.jogadores.append(interaction.user)
        await interaction.response.edit_message(embed=self._montar_embed(), view=self)
        if len(jogo.jogadores) >= jogo.numero_alvo:
            self.pronto.set()

    @discord.ui.button(label="🚪 Sair", style=discord.ButtonStyle.secondary)
    async def sair(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogo = self.jogo
        if interaction.user not in jogo.jogadores:
            await interaction.response.send_message("Você nem entrou ainda!", ephemeral=True)
            return
        if interaction.user.id == jogo.host.id:
            await interaction.response.send_message("Você é quem abriu o jogo — cancele em vez de sair.", ephemeral=True)
            return
        jogo.jogadores.remove(interaction.user)
        await interaction.response.edit_message(embed=self._montar_embed(), view=self)

    @discord.ui.button(label="▶️ Iniciar agora", style=discord.ButtonStyle.primary)
    async def iniciar(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogo = self.jogo
        if interaction.user.id != jogo.host.id:
            await interaction.response.send_message("Só quem abriu o jogo pode iniciar.", ephemeral=True)
            return
        if len(jogo.jogadores) < _CD_MIN_JOGADORES:
            await interaction.response.send_message(f"Precisa de pelo menos {_CD_MIN_JOGADORES} jogadores.", ephemeral=True)
            return
        await interaction.response.defer()
        self.pronto.set()

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogo = self.jogo
        if interaction.user.id != jogo.host.id:
            await interaction.response.send_message("Só quem abriu o jogo pode cancelar.", ephemeral=True)
            return
        self.cancelado = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="❌ Lobby cancelado.", embed=None, view=self)
        self.pronto.set()
        self.stop()


# ── Escolha: narrador humano ou bot? ────────────────────────────────────────
class CDEscolhaNarradorView(discord.ui.View):
    def __init__(self, jogo: JogoCidadeDorme):
        super().__init__(timeout=120)
        self.jogo = jogo
        self.escolha = None
        self.pronto = asyncio.Event()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.jogo.host.id:
            await interaction.response.send_message("Só quem abriu o jogo escolhe isso.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🤖 Bot narra", style=discord.ButtonStyle.primary)
    async def bot_narra(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.escolha = "bot"
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="🤖 A Aeon e a Celestia vão narrar essa partida!", view=self)
        self.pronto.set()
        self.stop()

    @discord.ui.button(label="🧑 Narrador humano", style=discord.ButtonStyle.secondary)
    async def humano_narra(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.escolha = "humano"
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="🧑 Um jogador vai narrar essa partida!", view=self)
        self.pronto.set()
        self.stop()


# ── Se for narrador humano: escolhe quem entre os jogadores vai narrar ─────
class CDSelecionarNarradorView(discord.ui.View):
    def __init__(self, jogo: JogoCidadeDorme):
        super().__init__(timeout=120)
        self.jogo = jogo
        self.escolhido = None
        self.pronto = asyncio.Event()

        select = discord.ui.Select(
            placeholder="Escolha quem vai narrar...",
            options=[
                discord.SelectOption(label=m.display_name, value=str(m.id))
                for m in jogo.jogadores
            ][:25],
        )
        select.callback = self._callback
        self.add_item(select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.jogo.host.id:
            await interaction.response.send_message("Só quem abriu o jogo escolhe isso.", ephemeral=True)
            return False
        return True

    async def _callback(self, interaction: discord.Interaction):
        uid = int(interaction.data["values"][0])
        membro = self.jogo.canal_texto.guild.get_member(uid)
        self.escolhido = membro
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=f"🧑 **{membro.display_name if membro else uid}** vai narrar essa partida!", view=self
        )
        self.pronto.set()
        self.stop()


# ── Painel do narrador humano: controla a call durante o jogo ──────────────
class CDPainelNarradorView(discord.ui.View):
    def __init__(self, jogo: JogoCidadeDorme):
        super().__init__(timeout=None)
        self.jogo = jogo

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.jogo.narrador_humano.id:
            await interaction.response.send_message("Só o narrador pode usar esse painel.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🔇 Mutar todas as calls", style=discord.ButtonStyle.danger, row=0)
    async def mutar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        erros = 0
        for membro in self.jogo.canal_voz.members:
            if membro.id in self.jogo.vivos:
                try:
                    await membro.edit(mute=True, reason="Cidade Dorme! — narrador mutou a call")
                except discord.HTTPException:
                    erros += 1
        await interaction.followup.send(
            "🔇 Call mutada." if not erros else f"🔇 Call mutada (falhou em {erros}).", ephemeral=True
        )

    @discord.ui.button(label="🔊 Desmutar todas as calls", style=discord.ButtonStyle.success, row=0)
    async def desmutar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        erros = 0
        for membro in self.jogo.canal_voz.members:
            if membro.id in self.jogo.vivos:
                try:
                    await membro.edit(mute=False, reason="Cidade Dorme! — narrador desmutou a call")
                except discord.HTTPException:
                    erros += 1
        await interaction.followup.send(
            "🔊 Call desmutada." if not erros else f"🔊 Call desmutada (falhou em {erros}).", ephemeral=True
        )

    @discord.ui.button(label="📋 Ver jogadores vivos", style=discord.ButtonStyle.secondary, row=1)
    async def ver_vivos(self, interaction: discord.Interaction, button: discord.ui.Button):
        vivos_txt = "\n".join(f"• {self.jogo.nome(uid)}" for uid in self.jogo.vivos) or "_ninguém vivo!_"
        await interaction.response.send_message(f"**Vivos ({len(self.jogo.vivos)}):**\n{vivos_txt}", ephemeral=True)

    @discord.ui.button(label="🏁 Encerrar jogo", style=discord.ButtonStyle.danger, row=1)
    async def encerrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for membro in self.jogo.canal_voz.members:
            try:
                await membro.edit(mute=False)
            except discord.HTTPException:
                pass
        _jogos_cidade_dorme.pop(self.jogo.canal_texto.id, None)
        self.jogo.ativo = False
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="🏁 Jogo encerrado pelo narrador.", view=self)
        await self.jogo.canal_texto.send("🏁 O narrador encerrou a partida de **Cidade Dorme!**")
        self.stop()


# ── Ações noturnas (modo bot): mensagens privadas por DM ───────────────────
class CDAssassinoView(discord.ui.View):
    def __init__(self, jogo: JogoCidadeDorme, alvos: list):
        super().__init__(timeout=_CD_DURACAO_NOITE)
        self.jogo = jogo
        self.respondido = False
        self.message = None
        select = discord.ui.Select(
            placeholder="Escolha quem matar essa noite...",
            options=[discord.SelectOption(label=m.display_name, value=str(m.id)) for m in alvos][:25],
        )
        select.callback = self._callback
        self.add_item(select)

    async def _callback(self, interaction: discord.Interaction):
        uid = int(interaction.data["values"][0])
        self.jogo.alvo_assassino = uid
        self.respondido = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=f"🔪 Você escolheu matar **{self.jogo.nome(uid)}** essa noite. Ninguém mais viu essa mensagem.",
            view=self,
        )
        self.stop()

    async def on_timeout(self):
        if not self.respondido and self.message:
            try:
                await self.message.edit(content="⏱️ Tempo esgotado — você não matou ninguém essa noite.", view=None)
            except Exception:
                pass


class CDAnjoView(discord.ui.View):
    def __init__(self, jogo: JogoCidadeDorme, alvos: list):
        super().__init__(timeout=_CD_DURACAO_NOITE)
        self.jogo = jogo
        self.respondido = False
        self.message = None
        select = discord.ui.Select(
            placeholder="Escolha quem proteger essa noite (não pode repetir a de ontem)...",
            options=[discord.SelectOption(label=m.display_name, value=str(m.id)) for m in alvos][:25],
        )
        select.callback = self._callback
        self.add_item(select)

    async def _callback(self, interaction: discord.Interaction):
        uid = int(interaction.data["values"][0])
        self.jogo.alvo_anjo = uid
        self.respondido = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=f"🕊️ Você vai proteger **{self.jogo.nome(uid)}** essa noite.", view=self
        )
        self.stop()

    async def on_timeout(self):
        if not self.respondido and self.message:
            try:
                await self.message.edit(content="⏱️ Tempo esgotado — você não protegeu ninguém essa noite.", view=None)
            except Exception:
                pass


class CDDetetiveView(discord.ui.View):
    def __init__(self, jogo: JogoCidadeDorme, alvos: list):
        super().__init__(timeout=_CD_DURACAO_NOITE)
        self.jogo = jogo
        self.respondido = False
        self.message = None
        select = discord.ui.Select(
            placeholder="Acuse alguém de ser o assassino (ou pule)...",
            options=[discord.SelectOption(label=m.display_name, value=str(m.id)) for m in alvos][:24]
            + [discord.SelectOption(label="⏭️ Pular essa noite", value="skip")],
        )
        select.callback = self._callback
        self.add_item(select)

    async def _callback(self, interaction: discord.Interaction):
        valor = interaction.data["values"][0]
        self.respondido = True
        for item in self.children:
            item.disabled = True
        if valor == "skip":
            self.jogo.acusacao_detetive = None
            await interaction.response.edit_message(content="⏭️ Você decidiu não acusar ninguém essa noite.", view=self)
        else:
            uid = int(valor)
            self.jogo.acusacao_detetive = uid
            await interaction.response.edit_message(
                content=f"🕵️ Você acusou **{self.jogo.nome(uid)}** de ser o assassino!", view=self
            )
        self.stop()

    async def on_timeout(self):
        if not self.respondido and self.message:
            try:
                await self.message.edit(content="⏱️ Tempo esgotado — você não acusou ninguém essa noite.", view=None)
            except Exception:
                pass


# ── Select ephemeral pra apontar um suspeito durante o debate ───────────────
# Igual ao select de acusação do Detetive (mesmo estilo visual), só que
# qualquer jogador vivo pode usar. O palpite vai só pro resumo que o
# Detetive confere depois — não tem efeito direto no jogo.
class CDSuspeitoView(discord.ui.View):
    def __init__(self, jogo: JogoCidadeDorme, autor_id: int, alvos: list):
        super().__init__(timeout=_CD_DURACAO_SUSPEITA)
        self.jogo = jogo
        self.autor_id = autor_id
        self.respondido = False
        self.message = None
        select = discord.ui.Select(
            placeholder="Aponte quem vocês suspeitam (ou pule)...",
            options=[discord.SelectOption(label=m.display_name, value=str(m.id)) for m in alvos][:24]
            + [discord.SelectOption(label="⏭️ Não apontar ninguém", value="skip")],
        )
        select.callback = self._callback
        self.add_item(select)

    async def _callback(self, interaction: discord.Interaction):
        valor = interaction.data["values"][0]
        self.respondido = True
        for item in self.children:
            item.disabled = True
        if valor == "skip":
            self.jogo.sugestoes.append((self.autor_id, "não apontou ninguém"))
            await interaction.response.edit_message(
                content="⏭️ Você decidiu não apontar ninguém dessa vez.", view=self
            )
        else:
            uid = int(valor)
            self.jogo.sugestoes.append((self.autor_id, f"suspeita de **{self.jogo.nome(uid)}**"))
            await interaction.response.edit_message(
                content=f"🤔 Você apontou **{self.jogo.nome(uid)}** como suspeito!", view=self
            )
        self.stop()

    async def on_timeout(self):
        if not self.respondido and self.message:
            try:
                await self.message.edit(content="⏱️ Tempo esgotado — você não deu seu palpite dessa vez.", view=None)
            except Exception:
                pass


# ── Botão único e igual pra todo mundo vivo — clicando, cada um recebe (só ──
# pra si, ephemeral) o select acima pra apontar um suspeito em segredo.
# Ninguém descobre quem votou em quem só de olhar o canal.
class CDAbrirSuspeitaView(discord.ui.View):
    def __init__(self, jogo: JogoCidadeDorme):
        super().__init__(timeout=_CD_DURACAO_SUSPEITA)
        self.jogo = jogo
        self.usados: set = set()
        self.aviso_msg = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in self.jogo.vivos:
            await interaction.response.send_message(
                "💀 Você não está mais vivo pra participar do debate.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="🤔 Apontar suspeito", style=discord.ButtonStyle.primary)
    async def apontar(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogo = self.jogo
        uid = interaction.user.id

        if uid in self.usados:
            await interaction.response.send_message(
                "✅ Você já deu seu palpite — agora é só esperar o resto da galera.", ephemeral=True
            )
            return

        guild = interaction.guild
        alvos = [guild.get_member(x) for x in jogo.vivos if x != uid]
        select_view = CDSuspeitoView(jogo, uid, [m for m in alvos if m])

        self.usados.add(uid)
        await interaction.response.send_message(
            "🤔 Quem vocês acham que é o assassino?",
            view=select_view,
            ephemeral=True,
        )
        try:
            select_view.message = await interaction.original_response()
        except Exception:
            pass

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.aviso_msg:
            try:
                await self.aviso_msg.edit(view=self)
            except Exception:
                pass


# ── Depois do julgamento da noite 1: o Detetive escolhe entre confiar no ───
# próprio palpite ou jogar a decisão pra votação pública da cidade inteira.
class CDDecisaoDetetiveView(discord.ui.View):
    def __init__(self, jogo: JogoCidadeDorme, timeout: int = 20):
        super().__init__(timeout=timeout)
        self.jogo = jogo
        self.opcao = None            # "sozinho" | "votacao" | None (não decidiu a tempo)
        self.escolhido = asyncio.Event()
        self.aviso_msg = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        detetive_id = self.jogo.id_por_papel("detetive")
        if interaction.user.id != detetive_id:
            await interaction.response.send_message("🤐 Só o Detetive pode decidir isso.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🧠 Confiar no meu palpite", style=discord.ButtonStyle.success)
    async def sozinho(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.opcao = "sozinho"
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="🧠 Você decidiu confiar no próprio palpite.", view=self)
        self.escolhido.set()
        self.stop()

    @discord.ui.button(label="🗳️ Abrir votação", style=discord.ButtonStyle.primary)
    async def votacao(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.opcao = "votacao"
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="🗳️ Você decidiu jogar a decisão pra votação da cidade.", view=self)
        self.escolhido.set()
        self.stop()

    async def on_timeout(self):
        if self.opcao is None:
            self.opcao = "sozinho"  # se o Detetive não decidir a tempo, segue o próprio palpite por padrão
            self.escolhido.set()
        for item in self.children:
            item.disabled = True
        if self.aviso_msg:
            try:
                await self.aviso_msg.edit(view=self)
            except Exception:
                pass


# ── Select ephemeral do voto de um jogador na votação pública da cidade ────
class CDVotoSelectView(discord.ui.View):
    def __init__(self, jogo: JogoCidadeDorme, votante_id: int, votos: dict, alvos: list):
        super().__init__(timeout=_CD_DURACAO_VOTACAO)
        self.jogo = jogo
        self.votante_id = votante_id
        self.votos = votos
        self.respondido = False
        self.message = None
        select = discord.ui.Select(
            placeholder="Vote em quem vocês acham que é o assassino...",
            options=[discord.SelectOption(label=m.display_name, value=str(m.id)) for m in alvos][:25],
        )
        select.callback = self._callback
        self.add_item(select)

    async def _callback(self, interaction: discord.Interaction):
        uid = int(interaction.data["values"][0])
        self.votos[self.votante_id] = uid
        self.respondido = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content=f"🗳️ Voto registrado em **{self.jogo.nome(uid)}**.", view=self)
        self.stop()

    async def on_timeout(self):
        if not self.respondido and self.message:
            try:
                await self.message.edit(content="⏱️ Tempo esgotado — seu voto não foi registrado.", view=None)
            except Exception:
                pass


# ── Botão único e igual pra todo mundo vivo votar (por botão) em quem acha ──
# que é o Assassino, durante a votação pública aberta pelo Detetive.
class CDVotacaoView(discord.ui.View):
    def __init__(self, jogo: JogoCidadeDorme, votos: dict):
        super().__init__(timeout=_CD_DURACAO_VOTACAO)
        self.jogo = jogo
        self.votos = votos
        self.usados: set = set()
        self.aviso_msg = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in self.jogo.vivos:
            await interaction.response.send_message("💀 Você não está mais vivo pra votar.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🗳️ Votar", style=discord.ButtonStyle.danger)
    async def votar(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogo = self.jogo
        uid = interaction.user.id

        if uid in self.usados:
            await interaction.response.send_message(
                "✅ Você já votou — agora é só esperar o resultado.", ephemeral=True
            )
            return

        guild = interaction.guild
        alvos = [guild.get_member(x) for x in jogo.vivos if x != uid]
        select_view = CDVotoSelectView(jogo, uid, self.votos, [m for m in alvos if m])

        self.usados.add(uid)
        await interaction.response.send_message("🗳️ Em quem você vota?", view=select_view, ephemeral=True)
        try:
            select_view.message = await interaction.original_response()
        except Exception:
            pass

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.aviso_msg:
            try:
                await self.aviso_msg.edit(view=self)
            except Exception:
                pass


# ── Painel noturno único: o MESMO botão aparece pra todo mundo vivo, todo ──
# jogador vê exatamente a mesma mensagem no canal. Quem tem papel recebe a
# ação de verdade (ephemeral, só ele vê); quem não tem recebe um aviso
# genérico também ephemeral. Como a mensagem pública é idêntica pra todos,
# não dá pra ninguém suspeitar quem é assassino/anjo/detetive só de ver
# quem "recebeu notificação" — e não depende de DM aberta.
class CDAcaoNoturnaView(discord.ui.View):
    def __init__(self, jogo: JogoCidadeDorme):
        super().__init__(timeout=_CD_DURACAO_NOITE)
        self.jogo = jogo
        self.usados: set = set()
        self.aviso_msg = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in self.jogo.vivos:
            await interaction.response.send_message(
                "💀 Você não está mais vivo pra agir essa noite.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="🔔 Agir em segredo", style=discord.ButtonStyle.primary)
    async def agir(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogo = self.jogo
        uid = interaction.user.id

        if uid in self.usados:
            await interaction.response.send_message(
                "✅ Você já agiu essa noite — agora é só esperar a cidade acordar.", ephemeral=True
            )
            return

        guild = interaction.guild
        papel = jogo.papeis.get(uid)

        if papel == "assassino":
            alvos = [guild.get_member(x) for x in jogo.vivos if x != uid]
            action_view = CDAssassinoView(jogo, [m for m in alvos if m])
        elif papel == "anjo":
            alvos = [guild.get_member(x) for x in jogo.vivos if x != jogo.alvo_anjo_anterior]
            action_view = CDAnjoView(jogo, [m for m in alvos if m])
        elif papel == "detetive":
            alvos = [guild.get_member(x) for x in jogo.vivos if x != uid]
            action_view = CDDetetiveView(jogo, [m for m in alvos if m])
        else:
            self.usados.add(uid)
            await interaction.response.send_message(
                "😴 Você não tem nenhuma ação essa noite — só durma tranquilo(a) até amanhecer.",
                ephemeral=True,
            )
            return

        self.usados.add(uid)
        await interaction.response.send_message(
            "🌙 A cidade dorme... é a sua vez de agir em segredo:",
            view=action_view,
            ephemeral=True,
        )
        try:
            action_view.message = await interaction.original_response()
        except Exception:
            pass

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.aviso_msg:
            try:
                await self.aviso_msg.edit(view=self)
            except Exception:
                pass


# ── Botão fixo pra conferir o próprio papel em segredo ──────────────────────
# Fica disponível o jogo inteiro. Não depende de DM aberta e, principalmente,
# nunca aparece publicamente quem teve DM fechada — todo mundo usa o mesmo
# botão, então ninguém descobre nada sobre ninguém só de olhar o canal.
class CDVerPapelView(discord.ui.View):
    def __init__(self, jogo: JogoCidadeDorme, descricoes_papel: dict):
        super().__init__(timeout=None)
        self.jogo = jogo
        self.descricoes_papel = descricoes_papel

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in self.jogo.papeis:
            await interaction.response.send_message("Você não está nessa partida.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="📜 Ver meu papel", style=discord.ButtonStyle.secondary)
    async def ver_papel(self, interaction: discord.Interaction, button: discord.ui.Button):
        papel = self.jogo.papeis.get(interaction.user.id, "normal")
        await interaction.response.send_message(self.descricoes_papel[papel], ephemeral=True)


# ── Resumo do debate: só o Detetive vê de verdade ────────────────────────────
# Mesmo botão pra todo mundo vivo (ninguém descobre quem é o Detetive só de
# ver quem teve acesso ao resumo de verdade). Quem não é Detetive recebe uma
# mensagem neutra também ephemeral.
class CDResumoDebateView(discord.ui.View):
    def __init__(self, jogo: JogoCidadeDorme):
        super().__init__(timeout=10)
        self.jogo = jogo
        self.aviso_msg = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in self.jogo.vivos:
            await interaction.response.send_message("💀 Você não está mais vivo pra ver isso.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🕵️ Ver resumo do debate", style=discord.ButtonStyle.secondary)
    async def ver_resumo(self, interaction: discord.Interaction, button: discord.ui.Button):
        jogo = self.jogo
        if jogo.papeis.get(interaction.user.id) != "detetive":
            await interaction.response.send_message("🤐 Esse resumo é só pro Detetive ver.", ephemeral=True)
            return

        if not jogo.sugestoes:
            texto = "_ninguém disse nada durante o debate..._"
        else:
            linhas = [f"• **{jogo.nome(uid)}:** {conteudo}" for uid, conteudo in jogo.sugestoes[:25]]
            texto = "\n".join(linhas)
            if len(texto) > 1800:
                texto = texto[:1800] + "\n_(...resumo cortado, muita gente falou!)_"

        await interaction.response.send_message(f"🕵️ **Resumo do debate:**\n{texto}", ephemeral=True)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.aviso_msg:
            try:
                await self.aviso_msg.edit(view=self)
            except Exception:
                pass


_CD_INTRO_HISTORIAS = [
    "🌘 Era uma vez uma cidadezinha pacata... até a noite passada. Um assassino se escondeu entre vocês, "
    "disfarçado de gente comum. Ninguém sabe quem é — nem mesmo entre si vocês confiam mais.",
    "🏚️ A vila dormia em paz, sem saber que um dos seus próprios moradores tinha sangue frio nas veias. "
    "A partir de hoje, ninguém fecha os olhos com tranquilidade.",
    "🌫️ Uma névoa estranha cobriu a cidade essa semana. Dizem que trouxe consigo alguém... ou algo... "
    "que não hesita em matar. E está bem aqui, entre vocês.",
]


# ══════════════════════════════════════════════════════════════════════
# BOATOS NOTURNOS — Cidade Dorme!
# Trechinhos curtos, ambíguos e aleatórios soltos durante a noite, só pra
# mexer com o psicológico da galera. NUNCA apontam ninguém de verdade —
# são só ruído dramático, sorteados entre jogadores vivos ao acaso. Às
# vezes (por pura coincidência do sorteio) o nome real do Assassino entra
# na jogada, mas isso não significa nada: o boato nunca confirma quem é
# quem, e o mesmo "estilo" de frase pode sair pra qualquer pessoa viva.
# ══════════════════════════════════════════════════════════════════════

_CD_BOATOS_DUPLA = [
    "🌑 Alguém jura ter visto **{a}** cochichando bem pertinho de **{b}**... será que não foi nada?",
    "🖤 Dizem que **{a}** fez 'alguma coisa' pelas costas de **{b}** essa noite... mas ninguém garante o quê.",
    "📜 Um bilhete rasgado apareceu perto de **{a}**. O nome de **{b}** estava escrito nele.",
    "👣 Uma sombra passou correndo perto de **{b}**. **{a}** jura de pés juntos que não foi ele(a).",
    "🌘 Um cochicho foi ouvido entre **{a}** e **{b}**. Ninguém sabe dizer sobre o quê era.",
    "🕯️ A vela de **{b}** apagou sozinha bem na hora em que **{a}** passou por perto.",
    "📦 Alguém remexeu nas coisas de **{b}**. **{a}** foi visto(a) rondando por ali na hora certa.",
    "🗝️ **{a}** foi flagrado(a) segurando algo que brilhava no escuro, bem perto do quarto de **{b}**.",
    "🚪 A porta do quarto de **{b}** rangeu no meio da madrugada. **{a}** ainda estava acordado(a).",
    "🖋️ Um pedaço de papel com letra parecida com a de **{a}** foi encontrado bem debaixo do travesseiro de **{b}**.",
    "🔦 Uma lanterna acesa foi vista se afastando de onde **{b}** dormia. Alguém acha que era **{a}**.",
    "🧤 Uma luva foi encontrada caída no caminho entre o quarto de **{a}** e o de **{b}**.",
]

_CD_BOATOS_SOLO = [
    "🔍 Passos apressados foram ouvidos saindo de onde **{a}** estava. Ninguém sabe pra onde foi.",
    "🩸 Tem uma mancha estranha no chão perto de onde **{a}** estava sentado(a). Coincidência?",
    "🔑 Uma porta que devia estar trancada foi encontrada aberta perto de **{a}**...",
    "🐾 Marcas de passos molhados levam até onde **{a}** dormia essa noite. Estranho, não?",
    "🕰️ **{a}** sumiu por alguns minutinhos durante a noite. Ninguém sabe dizer onde foi parar.",
    "🌫️ Um vulto foi visto se afastando na direção do quarto de **{a}**, mas sumiu na neblina.",
    "🧵 Um pedaço de tecido rasgado foi achado perto de onde **{a}** costuma ficar.",
    "🕳️ Tem uma marca esquisita na parede perto de **{a}**. Ninguém sabe explicar como foi parar ali.",
]


def _cd_gerar_boato(jogo: JogoCidadeDorme) -> str | None:
    """Sorteia um boato ambíguo entre jogadores vivos. Nunca revela nem
    confirma nada de verdade — é só clima e paranoia."""
    guild = jogo.canal_texto.guild
    vivos_membros = [m for m in (guild.get_member(uid) for uid in jogo.vivos) if m]
    if len(vivos_membros) < 2:
        return None

    # Às vezes "carrega o dado" pra incluir o Assassino de verdade no boato,
    # sem nunca dizer que é ele — pura implicância que às vezes acerta, às
    # vezes não, e ninguém tem como saber qual dos dois é o caso.
    assassino_id = jogo.id_por_papel("assassino")
    assassino_membro = guild.get_member(assassino_id) if assassino_id else None

    usar_dupla = len(vivos_membros) >= 2 and random.random() < 0.7
    if usar_dupla:
        if assassino_membro and assassino_membro in vivos_membros and random.random() < 0.35:
            outro = random.choice([m for m in vivos_membros if m.id != assassino_membro.id])
            a, b = random.sample([assassino_membro, outro], 2)
        else:
            a, b = random.sample(vivos_membros, 2)
        return random.choice(_CD_BOATOS_DUPLA).format(a=a.display_name, b=b.display_name)

    if assassino_membro and assassino_membro in vivos_membros and random.random() < 0.35:
        alvo = assassino_membro
    else:
        alvo = random.choice(vivos_membros)
    return random.choice(_CD_BOATOS_SOLO).format(a=alvo.display_name)


async def _cd_tarefa_boatos_noturnos(jogo: JogoCidadeDorme, duracao: int):
    """Solta de 1 a 3 boatos aleatórios espalhados durante a janela da
    noite, só pra manchetear o clima. Roda solta em segundo plano, em
    paralelo com a ação noturna, e nunca interfere no resultado real do
    jogo — qualquer erro aqui é só ignorado (e logado) pra não travar a
    partida."""
    try:
        canal = jogo.canal_texto
        if duracao < 8:
            return

        qtd = random.randint(1, 3)
        janela = list(range(4, duracao - 2))
        if not janela:
            return
        momentos = sorted(random.sample(janela, min(qtd, len(janela))))

        decorrido = 0
        for momento in momentos:
            await asyncio.sleep(momento - decorrido)
            decorrido = momento
            if not jogo.ativo:
                return
            boato = _cd_gerar_boato(jogo)
            if boato:
                try:
                    await canal.send(f"💭 *{boato}*")
                except discord.HTTPException:
                    pass
    except Exception as e:
        print(f"[cidade-dorme] ERRO nos boatos noturnos: {e!r}")


async def _processar_gatilho_cidade_dorme(message: discord.Message):
    """Detecta a frase 'Jogar cidade dorme!' e inicia o fluxo do jogo."""
    if message.guild is None:
        return
    texto = message.content.strip().lower()
    if texto not in _CD_FRASES_GATILHO:
        return
    if message.channel.id in _jogos_cidade_dorme:
        await message.channel.send("⚠️ Já tem uma partida de **Cidade Dorme!** rolando nesse canal.")
        return
    if message.author.voice is None or message.author.voice.channel is None:
        await message.channel.send(f"{message.author.mention} você precisa estar numa call pra abrir o jogo! 🎙️")
        return
    asyncio.create_task(_fluxo_cidade_dorme(message))


async def _fluxo_cidade_dorme(message: discord.Message):
    """Conduz o lobby inteiro: pergunta nº de jogadores, abre o lobby,
    escolhe o narrador e entrega o jogo pro modo certo (bot ou humano)."""
    canal_texto = message.channel
    host = message.author
    canal_voz = host.voice.channel

    await canal_texto.send(
        f"🌆 {host.mention} quer abrir uma partida de **Cidade Dorme!**\n"
        f"Quantas pessoas vão jogar? (mínimo {_CD_MIN_JOGADORES}, máximo {_CD_MAX_JOGADORES})"
    )

    def _check_numero(m):
        return m.author.id == host.id and m.channel.id == canal_texto.id and m.content.strip().isdigit()

    try:
        resposta = await bot.wait_for("message", check=_check_numero, timeout=60)
    except asyncio.TimeoutError:
        await canal_texto.send("⌛ Ninguém respondeu a tempo. Jogo cancelado.")
        return

    numero_alvo = int(resposta.content.strip())
    if numero_alvo < _CD_MIN_JOGADORES:
        await canal_texto.send(f"⚠️ Precisa de pelo menos {_CD_MIN_JOGADORES} jogadores. Jogo cancelado.")
        return
    numero_alvo = min(numero_alvo, _CD_MAX_JOGADORES)

    jogo = JogoCidadeDorme(canal_texto, canal_voz, host, numero_alvo)
    _jogos_cidade_dorme[canal_texto.id] = jogo
    jogo.jogadores.append(host)

    try:
        lobby_view = CDLobbyView(jogo)
        lobby_msg = await canal_texto.send(embed=lobby_view._montar_embed(), view=lobby_view)

        await lobby_view.pronto.wait()

        if lobby_view.cancelado or len(jogo.jogadores) < _CD_MIN_JOGADORES:
            if not lobby_view.cancelado:
                await canal_texto.send(f"⚠️ Não deu o mínimo de {_CD_MIN_JOGADORES} jogadores. Jogo cancelado.")
            _jogos_cidade_dorme.pop(canal_texto.id, None)
            return

        for item in lobby_view.children:
            item.disabled = True
        try:
            await lobby_msg.edit(view=lobby_view)
        except discord.HTTPException:
            pass

        escolha_view = CDEscolhaNarradorView(jogo)
        await canal_texto.send(f"{host.mention}, o narrador vai ser um **humano** ou o **bot**?", view=escolha_view)
        await escolha_view.pronto.wait()

        if escolha_view.escolha is None:
            await canal_texto.send("⌛ Ninguém escolheu o narrador a tempo. Jogo cancelado.")
            _jogos_cidade_dorme.pop(canal_texto.id, None)
            return

        if escolha_view.escolha == "humano":
            select_view = CDSelecionarNarradorView(jogo)
            await canal_texto.send("Quem vai narrar essa partida?", view=select_view)
            await select_view.pronto.wait()
            narrador = select_view.escolhido or host
            jogo.narrador_humano = narrador
            jogo.vivos = {m.id for m in jogo.jogadores}

            painel = CDPainelNarradorView(jogo)
            await canal_texto.send(
                f"🎬 **{narrador.display_name}** é o narrador dessa partida!\n"
                f"Combine os papéis com o grupo por fora (o bot não sorteia nada nesse modo) e use o "
                f"painel abaixo pra controlar a call durante o jogo:",
                view=painel,
            )
            # A limpeza desse modo acontece quando o narrador clica em "Encerrar jogo" no painel.
        else:
            await _rodar_cidade_dorme_bot(jogo)
            # A limpeza desse modo já acontece dentro de _encerrar_cidade_dorme_bot.
    except Exception as e:
        print(f"[cidade-dorme] ERRO no fluxo do canal {canal_texto.id}: {e!r}")
        _jogos_cidade_dorme.pop(canal_texto.id, None)
        try:
            await canal_texto.send("⚠️ Deu ruim e o jogo teve que ser cancelado. Pode tentar de novo!")
        except discord.HTTPException:
            pass


async def _rodar_cidade_dorme_bot(jogo: JogoCidadeDorme):
    """Sorteia papéis, avisa cada jogador por DM e conduz as noites."""
    canal = jogo.canal_texto

    embaralhados = jogo.jogadores.copy()
    random.shuffle(embaralhados)
    assassino, anjo, detetive = embaralhados[0], embaralhados[1], embaralhados[2]
    jogo.papeis[assassino.id] = "assassino"
    jogo.papeis[anjo.id] = "anjo"
    jogo.papeis[detetive.id] = "detetive"
    for m in embaralhados[3:]:
        jogo.papeis[m.id] = "normal"
    jogo.vivos = {m.id for m in jogo.jogadores}

    descricoes_papel = {
        "assassino": "🔪 Você é o **Assassino**. Mate o máximo de gente sem ser descoberto. "
        "Toda noite você escolhe uma vítima em segredo.",
        "anjo": "🕊️ Você é o **Anjo**. Toda noite você pode proteger uma pessoa (inclusive você mesmo) "
        "de um possível ataque.",
        "detetive": "🕵️ Você é o **Detetive**. Toda noite você pode acusar alguém de ser o assassino. "
        "Acertar termina o jogo na hora — errar não revela nada, então escolha com cuidado.",
        "normal": "🙂 Você é um **Morador Comum**. Sem poderes especiais — sua única arma é ficar de olho "
        "e sobreviver até o fim.",
    }

    for membro in jogo.jogadores:
        papel = jogo.papeis[membro.id]
        try:
            await membro.send(f"🌆 **Cidade Dorme!** começou em **{canal.guild.name}**.\n\n{descricoes_papel[papel]}")
        except discord.Forbidden:
            pass

    await canal.send(
        f"🎭 {random.choice(_CD_INTRO_HISTORIAS)}\n\n"
        f"👥 **Jogadores ({len(jogo.jogadores)}):** " + ", ".join(m.mention for m in jogo.jogadores) + "\n\n"
        f"Os papéis foram enviados no privado de cada um. Se não chegou (ou quiser conferir de novo), "
        f"usem o botão abaixo — só quem clicar vê o próprio papel. Boa sorte... vocês vão precisar. 🖤",
        view=CDVerPapelView(jogo, descricoes_papel),
    )

    while jogo.ativo:
        jogo.rodada += 1
        vencedor = await _rodar_noite_cidade_dorme(jogo)
        if vencedor:
            await _encerrar_cidade_dorme_bot(jogo, vencedor)
            break
        if jogo.ativo:
            await asyncio.sleep(20)  # "dia" — tempo pra galera discutir antes da próxima noite
        if jogo.ativo:
            await canal.send("☀️ A noite se aproxima de novo... quem será a próxima vítima? 🌙")


async def _fase_debate_cidade_dorme(jogo: JogoCidadeDorme):
    """Fase de debate antes da noite virar de verdade:
    • 30s com os mics abertos pra galera discutir de viva voz;
    • 10s de 'Quem vocês acham?' — cada um clica no botão e aponta um
      suspeito num select ephemeral, sem precisar escrever nada no chat;
    • mics fecham e mais 10s em que só o Detetive consegue ver o resumo
      (mesmo botão pra todo mundo, resposta ephemeral — ninguém descobre
      quem é o Detetive só de ver quem teve acesso ao conteúdo real)."""
    canal = jogo.canal_texto

    for membro in jogo.canal_voz.members:
        if membro.id in jogo.vivos:
            try:
                await membro.edit(mute=False, reason="Cidade Dorme! — debate antes da noite")
            except discord.HTTPException:
                pass

    await canal.send(
        "🗣️ A madrugada se aproxima... vocês têm **30 segundos** com os mics abertos "
        "pra debater e ajudar o Detetive a desconfiar de alguém!"
    )
    await asyncio.sleep(30)

    jogo.sugestoes = []
    suspeita_view = CDAbrirSuspeitaView(jogo)
    suspeita_msg = await canal.send(
        "🤔 **Quem vocês acham?** Cliquem no botão abaixo pra apontar um suspeito em segredo "
        f"— {_CD_DURACAO_SUSPEITA} segundos!",
        view=suspeita_view,
    )
    suspeita_view.aviso_msg = suspeita_msg
    await asyncio.sleep(_CD_DURACAO_SUSPEITA)

    for membro in jogo.canal_voz.members:
        if membro.id in jogo.vivos:
            try:
                await membro.edit(mute=True, reason="Cidade Dorme! — fim do debate")
            except discord.HTTPException:
                pass

    resumo_view = CDResumoDebateView(jogo)
    resumo_msg = await canal.send(
        "🕵️ O resumo do debate está pronto — quem quiser conferir tem **10 segundos**:",
        view=resumo_view,
    )
    resumo_view.aviso_msg = resumo_msg
    await asyncio.sleep(10)


async def _rodar_noite_cidade_dorme(jogo: JogoCidadeDorme):
    """Roda uma madrugada completa: fase de debate com mic aberto, resumo
    reservado pro Detetive, depois a noite em si (muta a call, coleta as
    ações em segredo, desmuta e revela o resultado). Retorna 'cidade'/
    'assassino' se o jogo acabou nessa noite, ou None se continua."""
    canal = jogo.canal_texto
    guild = canal.guild
    jogo.alvo_assassino = None
    jogo.alvo_anjo = None
    jogo.acusacao_detetive = None

    await _fase_debate_cidade_dorme(jogo)

    await canal.send(f"🌙 **Noite {jogo.rodada}** — a cidade vai dormir por {_CD_DURACAO_NOITE}s... 💤")

    for membro in jogo.canal_voz.members:
        if membro.id in jogo.vivos:
            try:
                await membro.edit(mute=True, reason="Cidade Dorme! — noite")
            except discord.HTTPException:
                pass

    assassino_id = jogo.id_por_papel("assassino")

    # Um botão só, igual pra todo mundo vivo — ninguém descobre quem tem
    # papel especial só de ver quem recebeu aviso. A ação real (ou o "você
    # não tem ação") chega ephemeral, só pra quem clicou.
    acao_view = CDAcaoNoturnaView(jogo)
    aviso_msg = await canal.send(
        "🔔 Cliquem no botão abaixo pra agir em segredo essa noite "
        "(só quem clicar vê o que aparece):",
        view=acao_view,
    )
    acao_view.aviso_msg = aviso_msg

    asyncio.create_task(_cd_tarefa_boatos_noturnos(jogo, _CD_DURACAO_NOITE))
    await asyncio.sleep(_CD_DURACAO_NOITE)

    for membro in jogo.canal_voz.members:
        if membro.id in jogo.vivos:
            try:
                await membro.edit(mute=False, reason="Cidade Dorme! — fim da noite")
            except discord.HTTPException:
                pass

    # ── Noite 1 é especial: ninguém morre, só o palpite do Detetive conta ──
    if jogo.rodada == 1:
        return await _resolver_noite_um_especial(jogo, assassino_id)

    # ── Acusação do detetive é resolvida primeiro ───────────────────────
    if jogo.acusacao_detetive is not None:
        if jogo.acusacao_detetive == assassino_id:
            await canal.send(f"🕵️ O Detetive acusou **{jogo.nome(jogo.acusacao_detetive)}**... e **acertou!** 🎉")
            return "cidade"
        else:
            await canal.send("🕵️ O Detetive fez uma acusação essa noite... mas errou o alvo. A investigação continua.")

    # ── Resultado do ataque do assassino ────────────────────────────────
    protegido_nome = jogo.nome(jogo.alvo_anjo) if jogo.alvo_anjo else "ninguém"
    await canal.send(f"🕊️ O Anjo protegeu: **{protegido_nome}**")
    jogo.alvo_anjo_anterior = jogo.alvo_anjo  # não pode proteger a mesma pessoa na próxima noite

    if jogo.alvo_assassino is None:
        await canal.send("🌅 A cidade acorda... e, por sorte, ninguém morreu essa noite!")
    elif jogo.alvo_assassino == jogo.alvo_anjo:
        await canal.send(
            f"🌅 A cidade acorda... o Assassino atacou **{jogo.nome(jogo.alvo_assassino)}**, "
            f"mas o Anjo chegou primeiro! Ninguém morreu essa noite. ✨"
        )
    else:
        vitima_id = jogo.alvo_assassino
        jogo.vivos.discard(vitima_id)
        vitima = guild.get_member(vitima_id)
        await canal.send(f"🌅 A cidade acorda... e encontra o corpo de **{jogo.nome(vitima_id)}**. 💀")
        if vitima:
            # Não desconecta da call — só fica mutada até o jogo acabar.
            try:
                await vitima.edit(mute=True, reason="Cidade Dorme! — eliminado, mutado até o fim da partida")
            except (discord.Forbidden, discord.HTTPException):
                pass
            try:
                await vitima.send(
                    "💀 Você foi assassinado essa noite. Você não participa mais das ações, "
                    "vai ficar mutado na call até o fim da partida, mas pode continuar "
                    "acompanhando pelo chat."
                )
            except discord.Forbidden:
                pass

        if jogo.papeis.get(vitima_id) == "detetive":
            return "assassino"

    return None


async def _resolver_noite_um_especial(jogo: JogoCidadeDorme, assassino_id: int):
    """A noite 1 é especial: ninguém morre, mesmo que o Assassino tenha
    escolhido um alvo. Só o palpite do Detetive vem à tona, todo mundo
    debate mais um pouco e aponta suspeitos de novo, e o Detetive escolhe
    entre confiar no próprio instinto ou jogar a decisão pra votação
    pública (por botão) de toda a cidade."""
    canal = jogo.canal_texto
    jogo.alvo_anjo_anterior = jogo.alvo_anjo  # a proteção de hoje já "gastou", mesmo sem ataque de verdade

    suspeito_inicial = jogo.acusacao_detetive
    if suspeito_inicial is not None:
        await canal.send(
            f"🌅 A primeira noite passa em paz — ninguém morre dessa vez. Mas o Detetive já tem um palpite: "
            f"ele suspeita de **{jogo.nome(suspeito_inicial)}**! 🕵️"
        )
    else:
        await canal.send(
            "🌅 A primeira noite passa em paz — ninguém morre dessa vez, e o Detetive ainda não tem "
            "nenhum suspeito claro."
        )

    await canal.send("🗣️ Agora todo mundo tem **30 segundos** com os mics abertos pra debater esse palpite!")
    for membro in jogo.canal_voz.members:
        if membro.id in jogo.vivos:
            try:
                await membro.edit(mute=False, reason="Cidade Dorme! — julgamento da noite 1")
            except discord.HTTPException:
                pass
    await asyncio.sleep(30)

    jogo.sugestoes = []
    suspeita_view = CDAbrirSuspeitaView(jogo)
    suspeita_msg = await canal.send(
        "🤔 **Quem vocês acham?** Cliquem no botão abaixo e apontem (de novo) um suspeito em segredo "
        f"— {_CD_DURACAO_SUSPEITA} segundos!",
        view=suspeita_view,
    )
    suspeita_view.aviso_msg = suspeita_msg
    await asyncio.sleep(_CD_DURACAO_SUSPEITA)

    for membro in jogo.canal_voz.members:
        if membro.id in jogo.vivos:
            try:
                await membro.edit(mute=True, reason="Cidade Dorme! — fim do julgamento da noite 1")
            except discord.HTTPException:
                pass

    detetive_id = jogo.id_por_papel("detetive")
    if detetive_id is None:
        await canal.send("🕵️ Sem Detetive vivo pra decidir nada... a cidade segue sem veredito por enquanto.")
        return None

    detetive_membro = canal.guild.get_member(detetive_id)
    decisao_view = CDDecisaoDetetiveView(jogo)
    decisao_msg = await canal.send(
        f"🕵️ {detetive_membro.mention if detetive_membro else jogo.nome(detetive_id)}, é sua vez: "
        "confia no seu próprio palpite ou prefere jogar a decisão pra votação de todo mundo?",
        view=decisao_view,
    )
    decisao_view.aviso_msg = decisao_msg
    await decisao_view.escolhido.wait()

    if decisao_view.opcao == "votacao":
        await canal.send("🗳️ O Detetive preferiu jogar a decisão pra votação da cidade!")
        alvo_final = await _abrir_votacao_cidade_dorme(jogo)
        if alvo_final is None:
            await canal.send("🗳️ A votação não teve nenhum voto — a cidade segue sem veredito.")
            return None
        await canal.send(f"🗳️ A cidade decidiu: **{jogo.nome(alvo_final)}** é o acusado!")
    else:
        alvo_final = jogo.acusacao_detetive
        if alvo_final is None:
            await canal.send(
                "🕵️ O Detetive decidiu confiar no próprio instinto... mas não tinha ninguém em mente. "
                "A cidade segue sem veredito."
            )
            return None
        await canal.send(f"🕵️ O Detetive confiou no próprio instinto e aponta **{jogo.nome(alvo_final)}**!")

    if alvo_final == assassino_id:
        await canal.send(f"🎉 E... **acertaram!** {jogo.nome(alvo_final)} era mesmo o Assassino!")
        return "cidade"

    await canal.send(f"😬 Só que não... {jogo.nome(alvo_final)} não era o Assassino. A investigação continua.")
    return None


async def _abrir_votacao_cidade_dorme(jogo: JogoCidadeDorme):
    """Vota publicamente (por botão) em quem a cidade acha que é o Assassino.
    Cada jogador vivo vota uma vez clicando no botão e escolhendo no select
    ephemeral; quem tiver mais votos no fim da janela é o acusado. Empate é
    resolvido por sorteio entre os empatados."""
    canal = jogo.canal_texto
    votos: dict = {}

    votacao_view = CDVotacaoView(jogo, votos)
    votacao_msg = await canal.send(
        f"🗳️ **Votação aberta!** Cliquem no botão abaixo e escolham quem vocês acham que é o Assassino "
        f"— {_CD_DURACAO_VOTACAO} segundos!",
        view=votacao_view,
    )
    votacao_view.aviso_msg = votacao_msg
    await asyncio.sleep(_CD_DURACAO_VOTACAO)

    for item in votacao_view.children:
        item.disabled = True
    try:
        await votacao_msg.edit(view=votacao_view)
    except discord.HTTPException:
        pass

    if not votos:
        return None

    contagem: dict = defaultdict(int)
    for alvo in votos.values():
        contagem[alvo] += 1

    maior = max(contagem.values())
    empatados = [uid for uid, qtd in contagem.items() if qtd == maior]
    vencedor = random.choice(empatados)

    linhas = "\n".join(
        f"• **{jogo.nome(uid)}** — {qtd} voto(s)"
        for uid, qtd in sorted(contagem.items(), key=lambda item: -item[1])
    )
    await canal.send(f"📊 **Resultado da votação:**\n{linhas}")

    return vencedor


async def _encerrar_cidade_dorme_bot(jogo: JogoCidadeDorme, vencedor: str):
    canal = jogo.canal_texto
    revelacao = "\n".join(f"• {jogo.nome(uid)} — {papel.capitalize()}" for uid, papel in jogo.papeis.items())

    if vencedor == "cidade":
        titulo, texto, cor = "🎉 A CIDADE VENCEU!", "O Detetive descobriu o Assassino a tempo. A cidade pode dormir em paz de novo.", 0x57F287
    else:
        titulo, texto, cor = "🔪 O ASSASSINO VENCEU!", "O Detetive foi silenciado antes de conseguir provar a verdade. O mal venceu dessa vez.", 0xED4245

    embed = discord.Embed(title=titulo, description=f"{texto}\n\n**Papéis revelados:**\n{revelacao}", color=cor)
    await canal.send(embed=embed)

    for membro in jogo.canal_voz.members:
        try:
            await membro.edit(mute=False)
        except discord.HTTPException:
            pass

    jogo.ativo = False
    _jogos_cidade_dorme.pop(canal.id, None)


# ══════════════════════════════════════════════════════════════════
# COMANDO .play — Entra na call, toca áudio do YouTube por 5s e sai
# Uso: .play (em qualquer canal de texto, estando em uma call)
# ══════════════════════════════════════════════════════════════════

# URL fixa do YouTube Shorts
URL_PLAY = "https://www.youtube.com/shorts/yt1pFGBMDT0"

# Opções do yt-dlp: apenas extrai URL do stream, sem baixar
_YDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
}

# Opções do FFmpeg para stream remoto
_FFMPEG_OPTS = {
    "before_options": (
        "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
    ),
    "options": "-vn",
}


@bot.command(name="play")
async def cmd_play(ctx):
    """Entra na call do autor, toca o áudio do YouTube por 5s e desconecta."""

    # Só funciona no servidor
    if ctx.guild is None:
        return

    # Verifica se o usuário está em uma call
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        await ctx.send(
            "🌑 **Aeon:** *emerge das sombras e olha em volta* "
            "...não há ninguém numa call por aqui. 🖤🌑 Entre em uma call primeiro."
        )
        return

    canal_voz = ctx.author.voice.channel

    # Conecta ou move para o canal do usuário
    try:
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(canal_voz)
            vc = ctx.voice_client
        else:
            vc = await canal_voz.connect()
    except discord.ClientException:
        await ctx.send("⚠️ Não foi possível entrar na call.")
        return

    if vc.is_playing():
        vc.stop()

    # Extrai a URL de stream via yt-dlp (sem baixar o arquivo)
    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(_YDL_OPTS) as ydl:
            info = await loop.run_in_executor(
                None, lambda: ydl.extract_info(URL_PLAY, download=False)
            )

        # Pega a URL do melhor formato de áudio disponível
        if "url" in info:
            stream_url = info["url"]
        else:
            formatos = [
                f for f in info.get("formats", [])
                if f.get("acodec") != "none"
            ]
            stream_url = formatos[-1]["url"] if formatos else info["formats"][-1]["url"]

        source = discord.FFmpegPCMAudio(stream_url, **_FFMPEG_OPTS)
        vc.play(source)

        # Toca por 5 segundos e sai
        await asyncio.sleep(5)

        if vc.is_playing():
            vc.stop()

        await vc.disconnect()

    except Exception as e:
        await ctx.send(f"⚠️ Erro ao reproduzir o áudio: `{e}`")
        try:
            await vc.disconnect()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════
# AUDITORIA DO SERVIDOR — igual ao Audit Log nativo do Discord
# Registra automaticamente no canal 1533947367647219822: criação, edição e
# remoção de canais (inclusive calls), cargos, banimentos/kicks, timeouts,
# apelidos, cargos de membros, emojis e alterações nas configurações do
# servidor. Sempre que possível, identifica quem fez a ação consultando o
# Audit Log real do Discord.
#
# IMPORTANTE: o bot precisa da permissão "Ver Registro de Auditoria"
# (View Audit Log) no servidor para conseguir identificar quem fez cada
# ação. Sem essa permissão, os embeds ainda são enviados, só que sem o
# campo de responsável.
# ══════════════════════════════════════════════════════════════════════

CANAL_AUDITORIA_ID = 1533947367647219822  # canal onde a auditoria geral é postada

_AUD_VERDE   = 0x57F287
_AUD_VERMELHO = 0xED4245
_AUD_AMARELO = 0xFEE75C


async def _auditoria_pegar_responsavel(
    guild: discord.Guild,
    action: "discord.AuditLogAction",
    target_id: int | None = None,
    limite: int = 6,
    janela_segundos: int = 20,
):
    """Tenta descobrir quem executou uma ação recente consultando o audit
    log real do Discord. Retorna None se não achar (ou sem permissão)."""
    if guild is None:
        return None
    try:
        agora = datetime.now(timezone.utc)
        async for entry in guild.audit_logs(limit=limite, action=action):
            if (agora - entry.created_at) > timedelta(seconds=janela_segundos):
                continue
            if target_id is None:
                return entry.user
            alvo = entry.target
            if alvo is not None and getattr(alvo, "id", None) == target_id:
                return entry.user
    except (discord.Forbidden, discord.HTTPException, AttributeError):
        pass
    return None


def _auditoria_embed(titulo: str, cor: int, responsavel=None) -> "discord.Embed":
    embed = discord.Embed(title=titulo, color=cor, timestamp=datetime.now(timezone.utc))
    if responsavel is not None:
        try:
            embed.set_author(
                name=f"Ação de: {responsavel}",
                icon_url=responsavel.display_avatar.url,
            )
        except AttributeError:
            embed.set_author(name=f"Ação de: {responsavel}")
    embed.set_footer(text="📋 Auditoria do servidor")
    return embed


async def _auditoria_enviar(guild: discord.Guild, embed: "discord.Embed") -> None:
    if guild is None:
        return
    canal = guild.get_channel(CANAL_AUDITORIA_ID)
    if canal is None:
        return
    try:
        await canal.send(embed=embed)
    except discord.HTTPException:
        pass


def _auditoria_tipo_canal(channel) -> str:
    if isinstance(channel, discord.VoiceChannel):
        return "Call/Voz"
    if isinstance(channel, discord.StageChannel):
        return "Palco"
    if isinstance(channel, discord.CategoryChannel):
        return "Categoria"
    if isinstance(channel, discord.ForumChannel):
        return "Fórum"
    if isinstance(channel, discord.TextChannel):
        return "Texto"
    return "Canal"


# ── Canais (criação / edição / remoção) — cobre também as calls ────────────

@bot.listen("on_guild_channel_create")
async def auditoria_canal_criado(channel: "discord.abc.GuildChannel"):
    guild = channel.guild
    responsavel = await _auditoria_pegar_responsavel(guild, discord.AuditLogAction.channel_create, channel.id)
    tipo = _auditoria_tipo_canal(channel)
    embed = _auditoria_embed(f"📁 Canal criado — {tipo}", _AUD_VERDE, responsavel)
    embed.add_field(name="Canal", value=getattr(channel, "mention", channel.name), inline=True)
    if getattr(channel, "category", None):
        embed.add_field(name="Categoria", value=channel.category.name, inline=True)
    await _auditoria_enviar(guild, embed)


@bot.listen("on_guild_channel_delete")
async def auditoria_canal_deletado(channel: "discord.abc.GuildChannel"):
    guild = channel.guild
    responsavel = await _auditoria_pegar_responsavel(guild, discord.AuditLogAction.channel_delete, channel.id)
    tipo = _auditoria_tipo_canal(channel)
    embed = _auditoria_embed(f"🗑️ Canal deletado — {tipo}", _AUD_VERMELHO, responsavel)
    embed.add_field(name="Canal", value=f"#{channel.name}", inline=True)
    if getattr(channel, "category", None):
        embed.add_field(name="Categoria", value=channel.category.name, inline=True)
    await _auditoria_enviar(guild, embed)


@bot.listen("on_guild_channel_update")
async def auditoria_canal_atualizado(before: "discord.abc.GuildChannel", after: "discord.abc.GuildChannel"):
    guild = after.guild
    mudancas = []

    if before.name != after.name:
        mudancas.append(("Nome", before.name, after.name))
    if getattr(before, "topic", None) != getattr(after, "topic", None):
        mudancas.append(("Tópico", getattr(before, "topic", None) or "—", getattr(after, "topic", None) or "—"))
    if getattr(before, "nsfw", None) != getattr(after, "nsfw", None):
        mudancas.append(("NSFW", str(before.nsfw), str(after.nsfw)))
    if getattr(before, "slowmode_delay", None) != getattr(after, "slowmode_delay", None):
        mudancas.append(("Slowmode", f"{before.slowmode_delay}s", f"{after.slowmode_delay}s"))
    if before.category != after.category:
        mudancas.append((
            "Categoria",
            before.category.name if before.category else "—",
            after.category.name if after.category else "—",
        ))
    if before.position != after.position and before.category == after.category:
        mudancas.append(("Posição na lista de canais", str(before.position), str(after.position)))
    if isinstance(after, discord.VoiceChannel):
        if before.bitrate != after.bitrate:
            mudancas.append(("Bitrate", f"{before.bitrate // 1000}kbps", f"{after.bitrate // 1000}kbps"))
        if before.user_limit != after.user_limit:
            mudancas.append((
                "Limite de usuários",
                str(before.user_limit) if before.user_limit else "Sem limite",
                str(after.user_limit) if after.user_limit else "Sem limite",
            ))
        if getattr(before, "rtc_region", None) != getattr(after, "rtc_region", None):
            mudancas.append((
                "Região de voz",
                str(before.rtc_region) if before.rtc_region else "Automática",
                str(after.rtc_region) if after.rtc_region else "Automática",
            ))
    if before.overwrites != after.overwrites:
        mudancas.append(("Permissões do canal", "alteradas", "veja o Audit Log do Discord p/ detalhes"))

    if not mudancas:
        return

    responsavel = await _auditoria_pegar_responsavel(guild, discord.AuditLogAction.channel_update, after.id)
    tipo = _auditoria_tipo_canal(after)
    embed = _auditoria_embed(f"✏️ Canal atualizado — {tipo}", _AUD_AMARELO, responsavel)
    embed.add_field(name="Canal", value=getattr(after, "mention", after.name), inline=False)
    for nome, antes, depois in mudancas:
        embed.add_field(name=nome, value=f"~~{antes}~~ → **{depois}**", inline=False)
    await _auditoria_enviar(guild, embed)


# ── Cargos (criação / edição / remoção) ─────────────────────────────────────

@bot.listen("on_guild_role_create")
async def auditoria_cargo_criado(role: "discord.Role"):
    guild = role.guild
    responsavel = await _auditoria_pegar_responsavel(guild, discord.AuditLogAction.role_create, role.id)
    embed = _auditoria_embed("✨ Cargo criado", _AUD_VERDE, responsavel)
    embed.add_field(name="Cargo", value=role.mention, inline=True)
    embed.add_field(name="Cor", value=str(role.color), inline=True)
    await _auditoria_enviar(guild, embed)


@bot.listen("on_guild_role_delete")
async def auditoria_cargo_deletado(role: "discord.Role"):
    guild = role.guild
    responsavel = await _auditoria_pegar_responsavel(guild, discord.AuditLogAction.role_delete, role.id)
    embed = _auditoria_embed("🗑️ Cargo deletado", _AUD_VERMELHO, responsavel)
    embed.add_field(name="Cargo", value=f"@{role.name}", inline=True)
    await _auditoria_enviar(guild, embed)


@bot.listen("on_guild_role_update")
async def auditoria_cargo_atualizado(before: "discord.Role", after: "discord.Role"):
    guild = after.guild
    mudancas = []

    if before.name != after.name:
        mudancas.append(("Nome", before.name, after.name))
    if before.color != after.color:
        mudancas.append(("Cor", str(before.color), str(after.color)))
    if before.hoist != after.hoist:
        mudancas.append(("Exibido separadamente", str(before.hoist), str(after.hoist)))
    if before.mentionable != after.mentionable:
        mudancas.append(("Mencionável", str(before.mentionable), str(after.mentionable)))
    if before.position != after.position:
        mudancas.append(("Posição na lista de cargos", str(before.position), str(after.position)))
    if before.permissions != after.permissions:
        antes_perms = {nome for nome, valor in before.permissions if valor}
        depois_perms = {nome for nome, valor in after.permissions if valor}
        ganhas = depois_perms - antes_perms
        perdidas = antes_perms - depois_perms
        if ganhas:
            mudancas.append(("Permissões concedidas", "—", ", ".join(sorted(ganhas))))
        if perdidas:
            mudancas.append(("Permissões removidas", ", ".join(sorted(perdidas)), "—"))

    if not mudancas:
        return

    responsavel = await _auditoria_pegar_responsavel(guild, discord.AuditLogAction.role_update, after.id)
    embed = _auditoria_embed("✏️ Cargo atualizado", _AUD_AMARELO, responsavel)
    embed.add_field(name="Cargo", value=after.mention, inline=False)
    for nome, antes, depois in mudancas:
        embed.add_field(name=nome, value=f"~~{antes}~~ → **{depois}**", inline=False)
    await _auditoria_enviar(guild, embed)


# ── Membros: apelido, cargos adicionados/removidos e timeout ───────────────

@bot.listen("on_member_update")
async def auditoria_membro_atualizado(before: "discord.Member", after: "discord.Member"):
    guild = after.guild

    if before.nick != after.nick:
        embed = _auditoria_embed("✏️ Apelido alterado", _AUD_AMARELO)
        embed.add_field(name="Membro", value=after.mention, inline=False)
        embed.add_field(
            name="Apelido",
            value=f"~~{before.nick or before.name}~~ → **{after.nick or after.name}**",
            inline=False,
        )
        await _auditoria_enviar(guild, embed)

    cargos_antes = set(before.roles)
    cargos_depois = set(after.roles)
    ganhos = cargos_depois - cargos_antes
    perdidos = cargos_antes - cargos_depois
    if ganhos or perdidos:
        responsavel_cargo = await _auditoria_pegar_responsavel(
            guild, discord.AuditLogAction.member_role_update, after.id
        )
        if ganhos:
            embed = _auditoria_embed("➕ Cargo(s) adicionado(s) a um membro", _AUD_VERDE, responsavel_cargo)
            embed.add_field(name="Membro", value=after.mention, inline=True)
            embed.add_field(name="Cargo(s)", value=", ".join(r.mention for r in ganhos), inline=True)
            await _auditoria_enviar(guild, embed)
        if perdidos:
            embed = _auditoria_embed("➖ Cargo(s) removido(s) de um membro", _AUD_VERMELHO, responsavel_cargo)
            embed.add_field(name="Membro", value=after.mention, inline=True)
            embed.add_field(name="Cargo(s)", value=", ".join(r.mention for r in perdidos), inline=True)
            await _auditoria_enviar(guild, embed)

    if before.timed_out_until != after.timed_out_until:
        agora = datetime.now(timezone.utc)
        if after.timed_out_until and after.timed_out_until > agora:
            responsavel = await _auditoria_pegar_responsavel(guild, discord.AuditLogAction.member_update, after.id)
            embed = _auditoria_embed("🔇 Membro colocado em timeout", _AUD_VERMELHO, responsavel)
            embed.add_field(name="Membro", value=after.mention, inline=True)
            embed.add_field(name="Até", value=discord.utils.format_dt(after.timed_out_until, style="F"), inline=True)
            await _auditoria_enviar(guild, embed)
        elif before.timed_out_until and not after.timed_out_until:
            responsavel = await _auditoria_pegar_responsavel(guild, discord.AuditLogAction.member_update, after.id)
            embed = _auditoria_embed("🔊 Timeout removido de um membro", _AUD_VERDE, responsavel)
            embed.add_field(name="Membro", value=after.mention, inline=True)
            await _auditoria_enviar(guild, embed)


# ── Banimentos, desbanimentos e expulsões (kick) ────────────────────────────

@bot.listen("on_member_ban")
async def auditoria_membro_banido(guild: "discord.Guild", user):
    responsavel = None
    motivo = None
    try:
        async for entry in guild.audit_logs(limit=6, action=discord.AuditLogAction.ban):
            if entry.target and entry.target.id == user.id:
                responsavel = entry.user
                motivo = entry.reason
                break
    except (discord.Forbidden, discord.HTTPException):
        pass
    embed = _auditoria_embed("🔨 Membro banido", _AUD_VERMELHO, responsavel)
    embed.add_field(name="Membro", value=f"{user} (`{user.id}`)", inline=True)
    if motivo:
        embed.add_field(name="Motivo", value=motivo, inline=True)
    await _auditoria_enviar(guild, embed)


@bot.listen("on_member_unban")
async def auditoria_membro_desbanido(guild: "discord.Guild", user):
    responsavel = await _auditoria_pegar_responsavel(guild, discord.AuditLogAction.unban, user.id)
    embed = _auditoria_embed("🔓 Membro desbanido", _AUD_VERDE, responsavel)
    embed.add_field(name="Membro", value=f"{user} (`{user.id}`)", inline=True)
    await _auditoria_enviar(guild, embed)


@bot.listen("on_member_remove")
async def auditoria_possivel_kick(member: "discord.Member"):
    """on_member_remove dispara tanto pra saída voluntária quanto pra kick —
    aqui só avisamos na auditoria quando for uma expulsão de fato."""
    guild = member.guild
    try:
        async for entry in guild.audit_logs(limit=6, action=discord.AuditLogAction.kick):
            if entry.target and entry.target.id == member.id:
                if (datetime.now(timezone.utc) - entry.created_at) <= timedelta(seconds=15):
                    embed = _auditoria_embed("👢 Membro expulso (kick)", _AUD_VERMELHO, entry.user)
                    embed.add_field(name="Membro", value=f"{member} (`{member.id}`)", inline=True)
                    if entry.reason:
                        embed.add_field(name="Motivo", value=entry.reason, inline=True)
                    await _auditoria_enviar(guild, embed)
                break
    except (discord.Forbidden, discord.HTTPException):
        pass


# ── Configurações do servidor (nome, ícone, banner, verificação, AFK...) ───

@bot.listen("on_guild_update")
async def auditoria_servidor_atualizado(before: "discord.Guild", after: "discord.Guild"):
    mudancas = []

    if before.name != after.name:
        mudancas.append(("Nome do servidor", before.name, after.name))
    if before.icon != after.icon:
        mudancas.append(("Ícone do servidor", "alterado", "alterado"))
    if before.banner != after.banner:
        mudancas.append(("Banner do servidor", "alterado", "alterado"))
    if before.verification_level != after.verification_level:
        mudancas.append(("Nível de verificação", str(before.verification_level), str(after.verification_level)))
    if before.afk_channel != after.afk_channel:
        mudancas.append((
            "Canal AFK",
            before.afk_channel.name if before.afk_channel else "—",
            after.afk_channel.name if after.afk_channel else "—",
        ))
    if before.owner_id != after.owner_id:
        mudancas.append(("Dono do servidor", str(before.owner_id), str(after.owner_id)))

    if not mudancas:
        return

    responsavel = await _auditoria_pegar_responsavel(after, discord.AuditLogAction.guild_update)
    embed = _auditoria_embed("⚙️ Configurações do servidor atualizadas", _AUD_AMARELO, responsavel)
    for nome, antes, depois in mudancas:
        embed.add_field(name=nome, value=f"~~{antes}~~ → **{depois}**", inline=False)
    await _auditoria_enviar(after, embed)


# ── Emojis (adicionados / removidos) ────────────────────────────────────────

@bot.listen("on_guild_emojis_update")
async def auditoria_emojis_atualizados(guild: "discord.Guild", before, after):
    ids_antes = {e.id for e in before}
    ids_depois = {e.id for e in after}
    criados = [e for e in after if e.id not in ids_antes]
    removidos = [e for e in before if e.id not in ids_depois]

    for emoji in criados:
        responsavel = await _auditoria_pegar_responsavel(guild, discord.AuditLogAction.emoji_create, emoji.id)
        embed = _auditoria_embed("😀 Emoji adicionado", _AUD_VERDE, responsavel)
        embed.add_field(name="Emoji", value=f"{emoji} `:{emoji.name}:`", inline=True)
        await _auditoria_enviar(guild, embed)

    for emoji in removidos:
        responsavel = await _auditoria_pegar_responsavel(guild, discord.AuditLogAction.emoji_delete, emoji.id)
        embed = _auditoria_embed("🗑️ Emoji removido", _AUD_VERMELHO, responsavel)
        embed.add_field(name="Emoji", value=f"`:{emoji.name}:`", inline=True)
        await _auditoria_enviar(guild, embed)


# ══════════════════════════════════════════════
# START
# ══════════════════════════════════════════════
if __name__ == "__main__":
    bot.run(TOKEN)
