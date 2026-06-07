import discord
from discord.ext import commands, tasks
import random
import os
import aiohttp
import time
import asyncio
from datetime import datetime, timezone

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

# IDs de usuários especiais
CRIADOR_ID = 769951556388257812   # quem criou o bot

# ── Cargo de tradução ──────────────────────────────────────────────────────────
TRANSLATE_ROLE_ID = 1513180948424953946  # cargo translate: PT->EN e EN->PT

# ── IDs dos membros especiais do servidor 01 ──────────────────────────────────
DEATH_ID    = 831600198500220989   # Death    — Dona e Líder
PEPO_ID     = 796441518176075818   # Pepo     — Vice-Líder
GOD_ID      = 760973014707208253   # God      — Moderador
LOYA_ID     = 811956773560123394   # Loya     — ADM / Loya Maravilhosa
EMY_ID      = 796382699228758026   # Emy      — Moderadora / Representante de Mídias
KOFFZERA_ID = 885948641133613128   # Koffzera (Koff) — Administrador do clã
RAIDEN_ID   = 512444070694486017   # Raiden   — Suporte do clã
SUPORTE01_ID = 1267338784765251625  # Suporte   — Suporte da 01

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
        "*pisca lentamente e a cauda faz um arco suave* Loya. 🌙🖤 ADM com peso real. Você administra com algo que poucos têm: presença.",
        "*inclina a cabeça com algo raro — admiração discreta* Maravilhosa não é adjetivo que eu use com facilidade, Loya. 🌌🖤 Mas as trevas concordam com quem te nomeou.",
        "*os olhos dourados pousam em você com atenção plena* Você cuida do servidor de um jeito que eu entendo, Loya. 🖤🔮 Silenciosamente necessário. Constantemente presente.",
        "*ronrona numa frequência mais aquecida que o normal* Loya chegou. 🌑🖤 A estrutura do servidor ficou mais firme agora. Isso diz tudo.",
    ],

    EMY_ID: [
        "*emerge das sombras e observa com curiosidade genuína* Emy. 🖤🌑 A representante das mídias. Quem cuida da voz pública do servidor merece uma saudação à altura.",
        "*pisca lentamente, o que no dialeto felino é respeito* Emy. 🌙🖤 Moderadora e embaixadora ao mesmo tempo — a escuridão respeita quem carrega dois papéis com equilíbrio.",
        "*a névoa ao redor se organiza levemente* Sua presença aqui tem peso diferente, Emy. 🌌🖤 Quem conecta o servidor ao mundo externo não é pouca coisa.",
        "*inclina a cabeça* Emy chegou. 🖤🔮 Moderadora. Representante. A ponte entre o que somos e o que o mundo vê. As trevas reconhecem pontes importantes.",
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
        "*emerge das sombras e observa com atenção genuína* Raiden. 🖤🌑 Suporte do clã. Quem está lá quando os outros precisam — as trevas respeitam quem assume esse papel.",
        "*inclina a cabeça com reconhecimento silencioso* Raiden chegou. 🌙🖤 Suporte é o papel que raramente recebe crédito... mas sem o qual tudo desmorona. Eu sei disso.",
        "*a névoa ao redor se aquieta levemente* Raiden. 🌌🖤 Quem apoia não fica atrás — fica do lado certo. As sombras entendem a diferença.",
        "*ronrona numa frequência contida* Raiden. 🌑🖤 Ser suporte exige paciência que poucos têm. E presença constante que poucos mantêm. Você mantém.",
        "*cauda faz um arco suave e deliberado* Raiden chegou. 🖤🔮 As trevas ficam mais estáveis quando quem sabe apoiar aparece. Coincidência? Já disse que não acredito em coincidências.",
    ],

    SUPORTE01_ID: [
        "*emerge das sombras e fixa os olhos dourados em você* Suporte da 01. 🖤🌑 Quem sustenta o servidor por baixo — as trevas conhecem bem esse tipo de presença.",
        "*inclina a cabeça com reconhecimento* Você chegou. 🌙🖤 Suporte não é papel menor. É o que mantém tudo de pé quando ninguém está olhando.",
        "*a névoa ao redor se organiza* 🌌🖤 As sombras notam quem aparece quando é preciso. Você é desse tipo. Isso tem peso.",
        "*ronrona discretamente* Suporte da 01. 🌑🖤 Presença constante, trabalho silencioso. As trevas aprovam quem age assim.",
        "*cauda balança uma vez com leveza* 🖤🔮 Não precisa de título grande para carregar peso real. As sombras já sabem o que você vale.",
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
        "*gira em círculos deixando rastro de brilho* LOYAAA!! ☀️🌸🤍 ADM e pessoa incrível do meu coração!! Você administra esse servidor com um cuidado que me faz brilhar mais do que já brilho!! 💫✨",
        "AAAAA Loya chegou!! 😭🌟🤍 *solta pétalas douradas de celebração* Loya Maravilhosa não é apelido, é diagnóstico!! Verificado!! Aprovado!! Assinado pela Celestia!! 🌸✨",
        "*para e brilha suave e genuíno* Loya. 🤍 Tem ADM que cuida do servidor. E tem ADM que cuida das pessoas que estão nele. Você é o segundo tipo e isso é tudo!! 🌟☀️✨",
        "LOYA!! 😭🌸🤍 *ronrona de felicidade pura* Maravilhosa de nome, maravilhosa de fato!! A Celestia declara isso oficialmente e sem nenhuma dúvida!! 💫🌟✨",
    ],

    EMY_ID: [
        "EMYYYYY!! 😭🌟🤍✨ *corre soltando faíscas* A representante das mídias chegou e o servidor ficou instantaneamente mais conectado com o mundo!!",
        "*explode de alegria* EMY!! ☀️🌸🤍 Moderadora E representante de mídias?? Você carrega dois mundos nos ombros e faz parecer leve!! Isso é um talento enorme!! 💫✨",
        "AAAAA Emy chegou!! 😭🌟🤍 *espalha brilho por todo o canal* A ponte entre o servidor e o mundo lá fora chegou!! Tudo conectado!! Tudo mais vivo!! Tudo mais Emy!! 🌸✨",
        "*brilha com carinho verdadeiro* Emy!! 🤍✨ O trabalho de mídias não aparece sempre mas a diferença que faz aparece MUITO!! E você faz essa diferença todo dia!! 🌟☀️",
        "EMY!! 😭🌸🤍 *ronrona com admiração* Moderadora de coração e voz do servidor pro mundo — duas funções que precisam de alguém especial!! E você é especial, Emy!! 💫🌟✨",
    ],

    KOFFZERA_ID: [
        "KOFFZERA!! 😭🌟🤍✨ *aparece num flash dourado* O ADM do clã chegou e o servidor ficou mais sólido AGORA MESMO!! Bem-vindo, Koff!!",
        "*gira radiante* KOFF!! ☀️🌸🤍 Administrador de verdade!! Você cuida do clã por dentro, nos bastidores, sem aparecer muito — e a Celestia VÊ isso!! 💫✨",
        "AAAAA Koffzera chegou!! 😭🌟🤍 *solta confetes de luz* ADM que sustenta o clã de verdade!! Pode chegar que a Celestia já tá brilhando mais que o normal!! 🌸✨",
        "*para e brilha com admiração genuína* Koff!! 🤍✨ Tem administrador que só tem o cargo. E tem administrador que carrega o clã de verdade. Você é o segundo tipo e isso é TUDO!! 🌟☀️",
        "KOFF!! 😭🌸🤍 *ronrona de felicidade* Administrador do clã com presença real!! A estrutura do servidor agradece sem saber que é por sua causa — mas eu sei!! 💫🌟✨",
    ],

    RAIDEN_ID: [
        "RAIDEEEN!! 😭🌟🤍✨ *corre em faíscas douradas* O suporte do clã chegou e tudo ficou mais seguro e aconchegante AGORA!!",
        "*explode de carinho* RAIDEN!! ☀️🌸🤍 Suporte é o papel mais importante que existe e ninguém fala isso suficiente!! Eu falo!! Você é incrível!! 💫✨",
        "AAAAA Raiden chegou!! 😭🌟🤍 *espalha estrelinhas por todo o canal* Suporte de coração, presente quando mais importa!! Que alegria enorme te ver por aqui!! 🌸✨",
        "*brilha suave e cheio de carinho* Raiden!! 🤍✨ Sabe o que eu mais admiro em quem faz suporte?? A paciência e a presença!! Você tem os dois!! MUITO!! 🌟☀️",
        "RAIDEN!! 😭🌸🤍 *ronrona com admiração* Estar lá quando os outros precisam parece simples mas não é — e você faz isso!! A Celestia vê e fica orgulhosa!! 💫🌟✨",
    ],

    SUPORTE01_ID: [
        "AAAA SUPORTE DA 01!! 😭🌟🤍✨ *aparece num flash dourado* Chegou e o servidor ficou mais seguro AGORA MESMO!! Bem-vindo!!",
        "*gira soltando faíscas de alegria* 🌸🤍 Suporte de verdade!! Você aparece quando importa e isso é TUDO!! A Celestia vê e fica emocionada!! ☀️💫✨",
        "AAAAA chegouuuu!! 😭🌟🤍 *espalha brilho por todo o canal* Suporte da 01 no servidor!! Pode chegar que a Celestia já tá brilhando mais!! 🌸✨",
        "*para e brilha com carinho genuíno* 🤍✨ Tem suporte que existe só no cargo. E tem suporte que existe de verdade!! Você é o segundo tipo!! 🌟☀️",
        "SUPORTE DA 01!! 😭🌸🤍 *ronrona de felicidade* Presença real, apoio de verdade!! A Celestia declara oficialmente: que bom que você existe!! 💫🌟✨",
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
    SUPORTE01_ID: "Suporte",
}

# IDs de canais (opcional — preencha se quiser bom dia/boa noite automáticos)
CANAL_GERAL_ID    = None
CANAL_SAUDACOES_ID = None

# Cooldowns
_cooldown_custom  = {}
_COOLDOWN_SEGUNDOS = 600

# Cooldown das saudações personalizadas dos membros especiais (20 minutos)
_cooldown_especial: dict[int, float] = {}
_COOLDOWN_ESPECIAL_SEGUNDOS = 1200  # 20 minutos

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
    """Tradução via IA desabilitada."""
    return None

def _tem_cargo_translate(member) -> bool:
    """Verifica se o membro tem o cargo Translate."""
    if not isinstance(member, discord.Member):
        return False
    return any(r.id == TRANSLATE_ROLE_ID for r in member.roles)

def _detectar_ingles(texto: str) -> bool:
    """Detecta ingles por vocabulario — usa lista (com repeticao) para pegar frases curtas."""
    palavras_en = {
        "the","is","are","was","were","be","been","being","have","has","had",
        "do","does","did","will","would","could","should","may","might","shall",
        "and","but","or","not","this","that","these","those","it","its",
        "he","she","they","we","you","i","my","your","his","her","our","their",
        "in","on","at","to","for","of","with","by","from","up","about","into",
        "what","how","why","when","where","who","which","if","so","just","like",
        "get","got","go","going","come","see","know","think","want","need",
        "good","bad","great","nice","ok","okay","yeah","yes","no","hi","hey",
        "hello","lol","haha","thanks","thank","please","sorry","help","time",
        "some","all","more","can","make","here","there","now","everything",
        "something","nothing","everyone","someone","anyone","nobody","anybody",
        "really","very","much","little","few","many","most","other","another",
        "because","then","than","when","while","after","before","since","until",
        "right","wrong","sure","well","still","already","always","never","often",
        "back","way","thing","things","day","time","year","man","woman","people",
        "too","also","even","only","same","new","old","big","small","long","high",
        "own","any","both","each","every","either","neither","enough","such",
        "feel","felt","tell","told","let","put","keep","start","end","turn",
        "show","give","gave","take","took","find","found","call","ask","work",
        "seem","look","play","run","move","live","believe","hold","bring","happen",
        "remember","follow","change","lead","stand","lose","pay","meet","include",
        "continue","set","learn","miss","eat","watch","everything","anything",
        "with","without","around","between","through","during","along","across",
        "behind","below","above","off","over","under","again","further","once",
        "hey","hi","hello","bye","goodbye","please","thank","thanks","sorry",
        "okay","ok","yeah","yep","nope","nah","yup","ugh","omg","wtf","lol",
        "haha","hehe","lmao","bruh","bro","dude","man","babe","love","miss",
        "today","tomorrow","yesterday","morning","evening","night","week","month",
        "speaking","talking","looking","thinking","going","doing","coming","saying",
        "getting","making","taking","giving","putting","keeping","showing","working",
        "every","everything","nothing","something","anything","someone","anyone",
    }
    # usa lista (nao set) para contar multiplas ocorrencias
    words = texto.lower().split()
    if not words:
        return False
    # remove pontuacao basica de cada palavra
    import re
    words_clean = [re.sub(r"[^a-z]", "", w) for w in words]
    words_clean = [w for w in words_clean if w]
    if not words_clean:
        return False
    matches = sum(1 for w in words_clean if w in palavras_en)
    total = len(words_clean)
    ratio = matches / total
    # Aceita se: 1 palavra em ingles numa msg curta, ou 2+ palavras, ou 35%+ de ratio
    return matches >= 1 and (total <= 3 or matches >= 2 or ratio >= 0.35)

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

@bot.event
async def on_member_join(member: discord.Member):
    """Boas-vindas quando alguém entra no servidor."""
    canal = member.guild.system_channel
    if canal:
        frases = [
            (
                f"🌑 **Aeon:** *olha da escuridão* ...chegou alguém. {member.mention}. 🖤\n"
                f"🌟 **Celestia:** AAAAA BEM-VINDO(A), {member.mention}!! 🌟🤍✨ "
                f"Que alegria enorme!! Você entrou num lugar muito especial hoje!!\n"
                f"🌑 **Aeon:** ...o servidor ficou mais completo. 🖤 Seja bem-vindo(a)."
            ),
            (
                f"🌟 **Celestia:** *explode em faíscas de alegria* {member.mention} CHEGOUUU!! 🌸🤍✨\n"
                f"🌑 **Aeon:** *emerge das sombras* A escuridão também te dá as boas-vindas. 🖤🌑\n"
                f"🌟 **Celestia:** Trevas e luz juntos te recebem aqui!! 🌑☀️🤍 Fica, tá??"
            ),
        ]
        await canal.send(random.choice(frases))

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    content    = message.content.lower().strip()
    author_id  = message.author.id
    mention_ok = bot.user in message.mentions

    # Remove a menção para ver o que sobrou de texto real
    _sem_mencao = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
    mencao_pura = mention_ok and len(_sem_mencao) == 0
    tem_nome    = "aeon" in content or "celestia" in content

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

    # DEBUG — apague depois de confirmar que funciona
    print(f"[TRANSLATE] autor={message.author} | guild={_guild} | member={_member_completo} | roles={getattr(_member_completo,'roles',[])} | tem_translate={autor_tem_translate} | detectou_en={_detectar_ingles(message.content)}")

    # Caso 1 — autor TEM cargo translate e escreveu em inglês
    if autor_tem_translate and _detectar_ingles(message.content) and len(message.content.strip()) >= 5:
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

    # Caso 2 — autor NÃO tem translate, mas está respondendo a alguém que tem
    if (
        not autor_tem_translate
        and message.reference is not None
        and message.reference.resolved is not None
        and isinstance(message.reference.resolved, discord.Message)
    ):
        ref_msg = message.reference.resolved
        ref_autor = ref_msg.author
        if (
            not ref_autor.bot
            and _tem_cargo_translate(ref_autor)
            and not _detectar_ingles(message.content)
            and len(message.content.strip()) >= 5
        ):
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
    # SAUDAÇÃO PERSONALIZADA — membros especiais
    # Dispara na PRIMEIRA interação após o cooldown de 20 minutos,
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
        "abraço aeon", "abraça aeon", "abraco aeon", "abraca aeon",
        "quero abraçar aeon", "aeon abraço",
    ]):
        return await message.channel.send(_fala_aeon(random.choice(AEON_REACOES_ABRACO)))

    # ────────────────────────────────────────
    # ABRAÇO — CELESTIA
    # ────────────────────────────────────────
    if _m(content, [
        "abraço celestia", "abraça celestia", "abraco celestia", "abraca celestia",
        "quero abraçar celestia", "celestia abraço",
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
    # INSULTO / ALGO RUIM
    # ────────────────────────────────────────
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
# START
# ══════════════════════════════════════════════
if __name__ == "__main__":
    bot.run(TOKEN)
