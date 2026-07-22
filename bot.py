import discord
from discord.ext import commands, tasks
import random
import os
import re
import json
import aiohttp
import time
import asyncio
from collections import defaultdict
from datetime import datetime, timezone, timedelta
try:
    import yt_dlp
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp
# .
# ╔══════════════════════════════════════════════════════════════╗
# ║          AEON & CELESTIA — DOIS GATOS, UMA ALMA             ║
# ║    Aeon: Gato das Trevas  |  Celestia: Gata da Luz          ║
# ╚══════════════════════════════════════════════════════════════╝

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

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
                    _anjo_voice_join.setdefault(membro.id, time.time())

    if not loop_ranking_anjo.is_running():
        loop_ranking_anjo.start()
    # ─────────────────────────────────────────────────────────────────────

    # ── Ranking de Nível (XP): setup ─────────────────────────────────────
    global _xp_stats_lock
    if _xp_stats_lock is None:
        _xp_stats_lock = asyncio.Lock()

    if not loop_ranking_xp.is_running():
        loop_ranking_xp.start()

    # Registra as setinhas ◀ ▶ do ranking como view persistente (sobrevive a reinícios)
    bot.add_view(RankingXPView(total_paginas=2))

    # Registra o menu de escolha de cor como view persistente (sobrevive a reinícios)
    bot.add_view(CorQuadradoView())

    # Registra o menu da Enciclopédia de Criaturas como view persistente (sobrevive a reinícios)
    bot.add_view(EnciclopediaView())
    # ─────────────────────────────────────────────────────────────────────

@bot.event
async def on_member_join(member: discord.Member):
    """Ao entrar no servidor, explica pra pessoa como abrir um ticket
    e avisa que a staff atende em até 24h (pode demorar um pouco, já que
    a maior parte da equipe trabalha/estuda fora do Discord)."""
    if member.bot:
        return

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
            print(f"[ranking-anjo] {member} entrou em call às {agora}")
        elif saiu_da_call:
            inicio = _anjo_voice_join.pop(member.id, None)
            if inicio:
                anjo_stats[member.id]["tempo_call"] += agora - inicio
                print(f"[ranking-anjo] {member} saiu da call — tempo total agora: {anjo_stats[member.id]['tempo_call']:.0f}s")
                asyncio.create_task(_atualizar_ranking_anjo())
        # Trocar de canal de voz mantém a contagem rodando (não é entrada nem saída)
    except Exception as e:
        print(f"[ranking-anjo] ERRO on_voice_state_update para {member}: {e!r}")


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

    if message.author.bot:
        return

    # ── Ranking de Anjos: conta mensagens de quem tem o cargo Anjo ─────────────
    try:
        if message.guild is not None:
            cargo_anjo_rank = message.guild.get_role(CARGO_ANJO_ID)
            if cargo_anjo_rank and cargo_anjo_rank in message.author.roles:
                anjo_stats[message.author.id]["mensagens"] += 1
                print(f"[ranking-anjo] +1 msg para {message.author} ({message.author.id}) — total agora: {anjo_stats[message.author.id]['mensagens']}")
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
CANAL_XP_ID = 1529543505267916942  # canal onde o ranking fica fixo (topo) e os level-ups são anunciados (embaixo)
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
        anjo_stats[atendente_id]["tickets"] += 1
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

anjo_stats: dict = defaultdict(lambda: {"mensagens": 0, "tempo_call": 0.0, "tickets": 0})
_anjo_ranking_message_id = None   # ID da mensagem de ranking já postada (editada, não duplicada)
_anjo_voice_join: dict = {}       # user_id -> time.time() de quando entrou na call
_anjo_stats_lock = None           # criado em on_ready (precisa de event loop rodando)


def _carregar_anjo_stats() -> None:
    """Carrega estatísticas salvas em disco, se existirem. Roda antes do bot conectar."""
    global _anjo_ranking_message_id
    if not os.path.exists(_ANJO_DATA_FILE):
        return
    try:
        with open(_ANJO_DATA_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        for uid_str, valores in dados.get("stats", {}).items():
            anjo_stats[int(uid_str)] = {
                "mensagens":  valores.get("mensagens", 0),
                "tempo_call": valores.get("tempo_call", 0.0),
                "tickets":    valores.get("tickets", 0),
            }
        _anjo_ranking_message_id = dados.get("ranking_message_id")
    except (json.JSONDecodeError, OSError, ValueError):
        pass


async def _salvar_anjo_stats() -> None:
    """Salva estatísticas em disco de forma atômica (escreve em .tmp e substitui)."""
    dados = {
        "stats": {str(uid): v for uid, v in anjo_stats.items()},
        "ranking_message_id": _anjo_ranking_message_id,
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


def _tempo_call_atual(membro_id: int) -> float:
    """Tempo total em call: sessões já fechadas (salvas) + a sessão atual em
    andamento, se a pessoa estiver em call neste exato momento (contagem 'ao vivo')."""
    base = anjo_stats.get(membro_id, {}).get("tempo_call", 0.0)
    inicio_sessao_atual = _anjo_voice_join.get(membro_id)
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


def _montar_embed_ranking(guild: discord.Guild) -> discord.Embed:
    cargo_anjo = guild.get_role(CARGO_ANJO_ID)
    membros_anjo = cargo_anjo.members if cargo_anjo else []

    linhas = []
    for membro in membros_anjo:
        if membro.bot:
            continue
        s = anjo_stats.get(membro.id, {"mensagens": 0, "tempo_call": 0.0, "tickets": 0})
        tempo_call_ao_vivo = _tempo_call_atual(membro.id)
        pontuacao = (
            s["mensagens"] * _PESO_MENSAGEM
            + (tempo_call_ao_vivo / 60) * _PESO_MINUTO_CALL
            + s["tickets"] * _PESO_TICKET
        )
        linhas.append((membro, s, tempo_call_ao_vivo, pontuacao))

    linhas.sort(key=lambda x: x[3], reverse=True)

    medalhas = ["🥇", "🥈", "🥉"]
    descricao_linhas = []
    if linhas:
        for i, (membro, s, tempo_call_ao_vivo, pontuacao) in enumerate(linhas):
            prefixo = medalhas[i] if i < 3 else f"`#{i + 1:>2}`"
            em_call_agora = " 🔴" if membro.id in _anjo_voice_join else ""
            descricao_linhas.append(
                f"{prefixo} **{membro.display_name}** — 💬 `{s['mensagens']}` msgs · "
                f"🎙️ `{_formatar_tempo_call(tempo_call_ao_vivo)}`{em_call_agora} em call · "
                f"🕊️ `{s['tickets']}` tickets — **{pontuacao:.0f} pts**"
            )
    else:
        descricao_linhas.append("*Nenhum Anjo encontrado no servidor.*")

    embed = discord.Embed(
        title="🕊️ Ranking dos Anjos",
        description="\n".join(descricao_linhas),
        color=0xe8d5f5,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — atualizado automaticamente a cada 1 min")
    return embed


async def _limpar_duplicadas_e_achar_ranking(canal: discord.TextChannel):
    """Varre o histórico do canal, apaga rankings duplicados antigos (deixando
    só o mais recente) e devolve essa mensagem mais recente pra ser editada.
    Serve de rede de segurança caso o ID salvo se perca (ex: deploy sem Volume)."""
    mensagens_ranking = []
    try:
        async for msg in canal.history(limit=50):
            if msg.author.id == bot.user.id and msg.embeds and msg.embeds[0].title == "🕊️ Ranking dos Anjos":
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


async def _atualizar_ranking_anjo() -> None:
    """Atualiza (ou cria, se ainda não existir) a mensagem de ranking no canal de logs anjo."""
    global _anjo_ranking_message_id

    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return

    canal = guild.get_channel(CANAL_RANKING_ANJO_ID)
    if canal is None:
        return

    embed = _montar_embed_ranking(guild)

    mensagem = None
    if _anjo_ranking_message_id:
        try:
            mensagem = await canal.fetch_message(_anjo_ranking_message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            mensagem = None

    # Não achou pelo ID salvo (ex: perdeu o JSON num redeploy sem Volume) —
    # procura no histórico do canal e limpa qualquer duplicada antes de criar uma nova
    if mensagem is None:
        mensagem = await _limpar_duplicadas_e_achar_ranking(canal)

    if mensagem:
        try:
            await mensagem.edit(embed=embed)
            _anjo_ranking_message_id = mensagem.id
        except discord.HTTPException:
            mensagem = None

    if mensagem is None:
        try:
            nova = await canal.send(embed=embed)
            _anjo_ranking_message_id = nova.id
        except discord.HTTPException:
            return

    await _salvar_anjo_stats()


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
    await ctx.send("🕊️ Ranking dos Anjos atualizado! Confira no canal de logs. ✨")


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
        f"**ID da mensagem de ranking salva:** `{_anjo_ranking_message_id}`",
        f"**Entradas em anjo_stats (memória):** {len(anjo_stats)}",
        f"**Pasta de dados usada:** `{_ANJO_DATA_DIR}`",
        f"**Arquivo de dados existe?** {'✅ sim' if os.path.exists(_ANJO_DATA_FILE) else '❌ não'}",
        "",
        "**Conteúdo bruto de anjo_stats:**",
    ]
    if anjo_stats:
        for uid, s in anjo_stats.items():
            membro = guild.get_member(uid)
            nome = membro.display_name if membro else f"<@{uid}>"
            linhas.append(f"`{uid}` ({nome}) — {s}")
    else:
        linhas.append("*vazio — nenhuma mensagem/call/ticket foi registrada ainda em memória*")

    texto = "\n".join(linhas)
    if len(texto) > 1900:
        texto = texto[:1900] + "\n... (cortado)"
    await ctx.send(f"🔍 **Diagnóstico do Ranking de Anjos**\n{texto}")


# Carrega o histórico salvo assim que o módulo sobe — antes mesmo de conectar no Discord
_carregar_anjo_stats()

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

# ── Personalização de cor do quadradinho no ranking ─────────────────────────
# Cada pessoa pode escolher a cor do próprio "quadradinho" (o quadrado que
# se preenche na barra de progresso) através do menu que fica abaixo do
# ranking fixo. A cor da parte vazia da barra continua sempre branca.
_COR_PADRAO = "roxo"
_CORES_QUADRADO = {
    "roxo":     {"emoji": "🟪", "label": "Roxo (padrão)"},
    "azul":     {"emoji": "🟦", "label": "Azul"},
    "vermelho": {"emoji": "🟥", "label": "Vermelho"},
    "verde":    {"emoji": "🟩", "label": "Verde"},
    "amarelo":  {"emoji": "🟨", "label": "Amarelo"},
    "laranja":  {"emoji": "🟧", "label": "Laranja"},
    "marrom":   {"emoji": "🟫", "label": "Marrom"},
    "preto":    {"emoji": "⬛", "label": "Preto"},
}


def _emoji_da_cor(chave: str) -> str:
    """Devolve o emoji do quadradinho preenchido para a cor escolhida
    (ou a cor padrão, se a chave for inválida/desconhecida)."""
    return _CORES_QUADRADO.get(chave, _CORES_QUADRADO[_COR_PADRAO])["emoji"]


# xp_stats[user_id] = {
#     "xp": int (total acumulado), "nivel": int, "level_message_id": int|None,
#     "elegivel": bool (já mandou mensagem em algum dos 3 canais de _XP_CANAIS_RANKING?),
#     "cor": str (chave em _CORES_QUADRADO — cor escolhida pra o próprio quadradinho),
#     "vitorias": int (vitórias na Arena de Batalhas), "derrotas": int (derrotas na Arena de Batalhas),
#     "criaturas": list[str] (ids das criaturas já desbloqueadas na Enciclopédia — começa com as
#                  ⚪ Comuns de graça, e ganha novas como recompensa ao vencer batalhas),
# }
xp_stats: dict = defaultdict(lambda: {"xp": 0, "nivel": 0, "level_message_id": None, "elegivel": False, "cor": _COR_PADRAO, "vitorias": 0, "derrotas": 0, "criaturas": []})
_xp_ultimo_ganho: dict = {}   # user_id -> time.time() do último ganho (cooldown)
_xp_ranking_message_id = None   # ID da ÚNICA mensagem do ranking — navegada com as setinhas ◀ ▶, nunca duplicada
_xp_ranking_pagina_atual: int = 0   # índice (0-based) da página do ranking sendo exibida agora
_xp_cor_message_id = None      # ID da mensagem com o menu de escolha de cor (fica logo abaixo do ranking)
_xp_batalha_info_message_id = None  # ID da mensagem explicando as batalhas (fica logo abaixo da de cor)
_xp_enciclopedia_message_id = None  # ID da mensagem da Enciclopédia de Criaturas (fica por último, embaixo de tudo)
_xp_stats_lock = None          # criado em on_ready (precisa de event loop rodando)


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


def _barra_progresso(atual: int, necessario: int, tamanho: int = 10, cor_emoji: str = "🟪") -> str:
    necessario = max(necessario, 1)
    preenchido = max(0, min(tamanho, round((atual / necessario) * tamanho)))
    return cor_emoji * preenchido + "⬜" * (tamanho - preenchido)


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
    menos, e sozinhas não fazem a pessoa aparecer no ranking.
    """
    if message.guild is None or message.author.bot:
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
            "Toda criatura tem uma **raridade** — ⚪ Comum, 🔵 Raro, 🟣 Épico ou 🟡 Lendário — e quanto mais "
            "rara, menos ela costuma aparecer nos sorteios. Todo mundo já começa com as ⚪ Comuns "
            "desbloqueadas; as demais só saem **de recompensa** pra quem **vence** uma batalha — o jogo "
            "sorteia uma criatura nova (que você ainda não tem) e ela entra pra sua coleção pra sempre. "
            "Quem perde não ganha nada disso. Veja a lista completa na 📖 **Enciclopédia** (mensagem fixa "
            "aqui embaixo) e confira sua coleção com `.criaturas`.\n\n"
            "**5️⃣ Pra poder batalhar**\n"
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
            "pra coleção. 🖤🌑\n\n"
            "👇 Use o menu abaixo pra ver os detalhes (e a imagem) de cada uma, e conferir "
            "**só pra você** se já desbloqueou ou não."
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
    embed.set_footer(text=f"🌑 Aeon & ☀️ Celestia — {len(_BATALHA_CRIATURAS)} criaturas ao todo")
    return embed


class EnciclopediaSelect(discord.ui.Select):
    """Menu de seleção com todas as criaturas. Ao escolher uma, a pessoa recebe
    (de forma privada) a imagem, a raridade e se JÁ desbloqueou aquela criatura."""

    def __init__(self):
        options = [
            discord.SelectOption(
                label=c["nome"][:100],
                value=c["id"],
                description=_RARIDADES[c["raridade"]]["label"],
                emoji=_RARIDADES[c["raridade"]]["emoji"],
            )
            for c in _BATALHA_CRIATURAS
        ]
        super().__init__(
            placeholder="📖 Escolha uma criatura para ver os detalhes...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="enciclopedia_criaturas_select",
        )

    async def callback(self, interaction: discord.Interaction):
        criatura = next((c for c in _BATALHA_CRIATURAS if c["id"] == self.values[0]), None)
        if criatura is None:
            await interaction.response.send_message("⚠️ Criatura não encontrada.", ephemeral=True)
            return

        desbloqueada = criatura["id"] in set(_garantir_criaturas_iniciais(interaction.user.id))
        info_raridade = _RARIDADES[criatura["raridade"]]

        if desbloqueada:
            status = "🔓 **Você já desbloqueou essa criatura!** Ela pode aparecer nas suas batalhas."
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


class EnciclopediaView(discord.ui.View):
    """View persistente (sobrevive a reinícios do bot) com o menu de seleção
    de criaturas da Enciclopédia."""

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(EnciclopediaSelect())


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
    empilhar mensagem nenhuma."""
    global _xp_ranking_message_id, _xp_ranking_pagina_atual

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


_XP_POR_TICK_CALL = 2   # xp ganho a cada 1 min em call de voz — reforço leve, bem menos que mandar mensagem


async def _processar_xp_call(guild: discord.Guild) -> None:
    """A cada 1 minuto (mesmo ritmo do loop de ranking), dá um pouco de xp pra
    quem está numa call de voz agora. É só um reforço — bem menos do que
    mandar mensagem nos canais principais, mas já soma algo. Destravado pra
    todo mundo, sem exigir cargo."""
    for canal_voz in guild.voice_channels:
        for membro in canal_voz.members:
            if membro.bot:
                continue

            dados = xp_stats[membro.id]
            nivel_antigo = dados["nivel"]
            dados["xp"] += _XP_POR_TICK_CALL

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
}
_ORDEM_RARIDADES = ("lendario", "epico", "raro", "comum")  # do mais raro pro mais comum, pra exibição

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

    # ── Raras ───────────────────────────────────────────────────────────
    {"id": "cavaleiro_elemental",     "nome": "Cavaleiro Elemental",          "raridade": "raro",     "gif": "https://i.pinimg.com/originals/f0/6a/a4/f06aa45318cce9f16f2b3e591a138ae1.gif"},
    {"id": "caveira_prisao",          "nome": "Caveira da Prisão",            "raridade": "raro",     "gif": "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEivaQ2fr4t0qnYKfUiXbCeBU2HGF2vMB6oCjiEbAjADBdNYPoOqzEU8jSDdHDwD5xgI7MGL9qj0eH60EgBEaGjgV4JIHDait9dSFusVjLvykhwIWHPa4tfeDhzOr3uhwQfyNtzw7mz-Q9_E/s1600/Phantasm_attack_8.gif"},
    {"id": "eco_luz",                 "nome": "Eco da Luz",                   "raridade": "raro",     "gif": "https://i.pinimg.com/originals/25/83/b2/2583b2768cb33f0165e3a88ac3debbde.gif"},
    {"id": "cientista_louco",         "nome": "Cientista Louco",              "raridade": "raro",     "gif": "https://i.pinimg.com/originals/f7/45/05/f74505bee8fec82f0eb6e925c61b35f2.gif"},
    {"id": "brutal",                  "nome": "O Brutal",                     "raridade": "raro",     "gif": "https://i.pinimg.com/originals/fd/1f/8a/fd1f8aa84a2d1b1d1486c68613216d9d.gif"},
    {"id": "cavaleiro_sinistro",      "nome": "Cavaleiro do Sinistro",        "raridade": "raro",     "gif": "https://i.pinimg.com/originals/1c/3a/9b/1c3a9bc1c91135ff036d1d168d15e474.gif"},

    # ── Épicas ──────────────────────────────────────────────────────────
    {"id": "heroina_esmeraldas",      "nome": "Heroína das Esmeraldas",       "raridade": "epico",    "gif": "https://i.pinimg.com/originals/40/4f/d9/404fd93484c2592c78a13cf25891c156.gif"},
    {"id": "robin_dourado",           "nome": "Robin Dourado",                "raridade": "epico",    "gif": "https://i.pinimg.com/originals/fc/26/21/fc26214b7e21990e483df07f8ee616e8.gif"},
    {"id": "buda_eco",                "nome": "Buda do Eco",                  "raridade": "epico",    "gif": "https://i.pinimg.com/originals/de/cc/64/decc640148693d24cbccfce9262d16ae.gif"},
    {"id": "monstro_portao",          "nome": "O Monstro do Portão",          "raridade": "epico",    "gif": "https://i.pinimg.com/originals/1f/4a/d7/1f4ad7fd9917093bc7463394497fd920.gif"},
    {"id": "ultimo_atlanta",          "nome": "Último de Atlanta",            "raridade": "epico",    "gif": "https://i.pinimg.com/originals/84/a6/8b/84a68ba244c9034c52dcb8002f90a87f.gif"},
    {"id": "guerreiro_trovao",        "nome": "Guerreiro do Trovão",          "raridade": "epico",    "gif": "https://i.pinimg.com/originals/6b/2c/21/6b2c2173d12ddf1f2adae8f0064f772d.gif"},

    # ── Lendárias ───────────────────────────────────────────────────────
    {"id": "ultimo_guerreiro",        "nome": "O Último Guerreiro",           "raridade": "lendario", "gif": "https://gd-hbimg.huaban.com/da5bb9cc8fab68c2c3cabe68a7cc7a10cd277939be96-bBi4DQ"},
    {"id": "lyria_governante",        "nome": "Lyria, a Governante",          "raridade": "lendario", "gif": "https://i.pinimg.com/originals/9e/88/99/9e88991126a8bdd32a89e43ae683f3b4.gif"},
    {"id": "kaiju_eco",               "nome": "Kaiju do Eco",                 "raridade": "lendario", "gif": "https://i.pinimg.com/originals/02/ef/09/02ef09d38f7435de3a2e8d26508a17ec.gif"},
    {"id": "protetor_portao_inferno", "nome": "Protetor do Portão do Inferno","raridade": "lendario", "gif": "https://i.pinimg.com/originals/6d/bc/58/6dbc588871368635891ea6a5f12d3cf2.gif"},
    {"id": "magmata",                 "nome": "O Magmata",                    "raridade": "lendario", "gif": "https://i.redd.it/0jk54f0ocjwy.gif"},
]

def _garantir_criaturas_iniciais(user_id: int) -> list:
    """Garante que a pessoa tenha ao menos as criaturas ⚪ Comuns já
    desbloqueadas — é o "kit inicial" de todo mundo, pra sempre ter algo
    pra invocar numa batalha mesmo antes de vencer a primeira vez.
    Só concede na primeira vez (lista vazia); depois disso o progresso
    (raras, épicas, lendárias) fica só por conta de vitórias."""
    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])
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

_BATALHA_TEMPO_ACEITE = 60          # segundos que o desafiado tem pra aceitar/recusar
_BATALHA_TEMPO_SOMEM  = 60          # segundos até cada mensagem da batalha sumir sozinha


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
    """Sorteia 1 criatura para essa pessoa invocar — SOMENTE dentre as que
    ela já desbloqueou (ninguém pode invocar o que ainda não possui). O
    sorteio continua PONDERADO pela raridade — entre as que ela tem, Comuns
    saem com mais frequência que Raras, e assim por diante."""
    desbloqueadas = set(_garantir_criaturas_iniciais(user_id))
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
        description=f"**{desafiante.display_name}** invoca... **{criatura_desafiante['nome']}**!! 💥",
        color=0xff4444,
    )
    embed_c1.set_image(url=criatura_desafiante["gif"])
    msg_c1 = await canal.send(embed=embed_c1)
    asyncio.create_task(_apagar_mensagem_depois(msg_c1))
    await asyncio.sleep(2.5)

    # ── Criatura do desafiado ────────────────────────────────────────────
    embed_c2 = discord.Embed(
        title="💠 O desafiado revida!",
        description=f"**{desafiado.display_name}** responde invocando... **{criatura_desafiado['nome']}**!! ⚡",
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

    # ── Sorteia o vencedor (50/50) ───────────────────────────────────────
    if random.random() < 0.5:
        vencedor, criatura_vencedora = desafiante, criatura_desafiante
        perdedor, criatura_perdedora = desafiado, criatura_desafiado
    else:
        vencedor, criatura_vencedora = desafiado, criatura_desafiado
        perdedor, criatura_perdedora = desafiante, criatura_desafiante

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
    # pra sua coleção. Quem perde não ganha nada disso. ──
    dados_vencedor.setdefault("criaturas", [])
    _nao_possuidas = [c for c in _BATALHA_CRIATURAS if c["id"] not in dados_vencedor["criaturas"]]
    criatura_nova = None
    if _nao_possuidas:
        _pesos_novas = [_RARIDADES[c["raridade"]]["peso"] for c in _nao_possuidas]
        criatura_nova = random.choices(_nao_possuidas, weights=_pesos_novas, k=1)[0]
        dados_vencedor["criaturas"].append(criatura_nova["id"])

    xp_roubado = 0
    percentual = 0.0
    if xp_perdedor_antes > 0 and random.random() >= _BATALHA_CHANCE_SEM_ROUBO:
        percentual = random.uniform(_BATALHA_ROUBO_MIN, _BATALHA_ROUBO_MAX)
        xp_roubado = max(1, round(xp_perdedor_antes * percentual))
        xp_roubado = min(xp_roubado, xp_perdedor_antes)  # nunca deixa o xp negativo

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

    # ── Conclusão dramática ───────────────────────────────────────────────
    if xp_roubado > 0:
        texto_roubo = (
            f"💰 O dado sorteou **`{percentual * 100:.1f}%`**! "
            f"**{vencedor.display_name}** saqueou **`{xp_roubado}` XP** de **{perdedor.display_name}**!"
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

    if criatura_nova is not None:
        info_raridade_nova = _RARIDADES[criatura_nova["raridade"]]
        texto_desbloqueio = (
            f"🆕 De recompensa, **{vencedor.display_name}** desbloqueou "
            f"{info_raridade_nova['emoji']} **{criatura_nova['nome']}** "
            f"(*{info_raridade_nova['label']}*) na Enciclopédia! Use `.criaturas` pra conferir. 📖"
        )
    else:
        texto_desbloqueio = (
            f"🏅 **{vencedor.display_name}** já desbloqueou todas as criaturas existentes — "
            "coleção completa!"
        )

    embed_resultado = discord.Embed(
        title="🏆 FIM DE BATALHA!",
        description=(
            f"**{criatura_vencedora['nome']}** ({vencedor.mention}) derrota "
            f"**{criatura_perdedora['nome']}** ({perdedor.mention})!\n\n"
            f"{texto_roubo}\n\n"
            f"{texto_desbloqueio}\n\n"
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


@bot.command(name="criaturas")
async def cmd_criaturas(ctx, membro: discord.Member = None):
    """Mostra a coleção de criaturas desbloqueadas de alguém na Arena de
    Batalhas (ou de quem usou o comando, se ninguém for mencionado).
    Uso: .criaturas [@alguém]"""
    alvo = membro or ctx.author
    desbloqueadas = set(_garantir_criaturas_iniciais(alvo.id))

    embed = discord.Embed(
        title=f"📖 Coleção de Criaturas — {alvo.display_name}",
        description=(
            f"🔓 **{len(desbloqueadas)}/{len(_BATALHA_CRIATURAS)}** criaturas desbloqueadas até agora!\n"
            "Vença batalhas invocando as que faltam pra completar a coleção. ⚔️"
        ),
        color=0x9b59b6,
    )

    for raridade in _ORDEM_RARIDADES:
        info = _RARIDADES[raridade]
        linhas = [
            f"{'🔓' if c['id'] in desbloqueadas else '🔒'} {c['nome']}"
            for c in _BATALHA_CRIATURAS
            if c["raridade"] == raridade
        ]
        if linhas:
            embed.add_field(name=f"{info['emoji']} {info['label']}", value="\n".join(linhas), inline=False)

    embed.set_thumbnail(url=alvo.display_avatar.url)
    embed.set_footer(text="🌑 Aeon & ☀️ Celestia — confira também a 📖 Enciclopédia no canal de ranking")
    await ctx.send(embed=embed)


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


# ══════════════════════════════════════════════
# START
# ══════════════════════════════════════════════
if __name__ == "__main__":
    bot.run(TOKEN)
