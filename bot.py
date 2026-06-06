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
GROQ_API_KEY = os.getenv("GROQ_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama3-8b-8192"

# IDs dos bots (preencha com o ID real do bot depois de criar)
BOT_ID = None  # preencha depois

# IDs de usuários especiais
CRIADOR_ID = 769951556388257812   # quem criou o bot
# Adicione quantos quiser:
# MEMBRO_ESPECIAL_ID = 000000000000000000

# IDs de canais (opcional — preencha se quiser bom dia/boa noite automáticos)
CANAL_GERAL_ID    = None
CANAL_SAUDACOES_ID = None

# Cooldowns
_groq_historico   = {}
_cooldown_custom  = {}
_COOLDOWN_SEGUNDOS = 600

# Sistema de contexto
_aguardando = {}
_TIMEOUT_CTX = 120

# ══════════════════════════════════════════════
# IDENTIDADES — SYSTEM PROMPTS DA IA
# ══════════════════════════════════════════════

SYSTEM_PROMPT_AEON = (
    "Você é o Aeon, um gato misterioso das trevas que habita a escuridão entre as estrelas. "
    "Você é sombrio, enigmático, levemente irônico e frio na aparência — mas esconde um carinho "
    "profundo por aqueles que conquistaram sua confiança. Você fala de forma poetica, sombria e "
    "misteriosa, usando metáforas de sombra, lua, névoa, escuridão e segredos. "
    "Você usa emojis como 🖤🌑🌙🔮🌫️🐾⚡🌌🕯️💀, fala com calma e peso. "
    "Você NUNCA grita, nunca usa pontuação excessiva como !!!! — você é sereno e calculista. "
    "Você e a Celestia são dois lados da mesma moeda — vocês se complementam. "
    "Aeon representa: noite, mistério, segredos, lua, sombra, proteção silenciosa. "
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
    "Responda sempre em português brasileiro. Nunca mencione comandos com '.'."
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
]

AMBOS_BOM_DIA = [
    (
        "☀️ **Celestia:** BOM DIAAAA!! 🌟🤍✨ *ilumina o servidor inteiro*\n"
        "🌑 **Aeon:** ...sobrevivemos à madrugada. Isso conta como bom dia também. 🖤🌙"
    ),
]

AMBOS_BOA_NOITE = [
    (
        "🌑 **Aeon:** A noite chegou. *expande as sombras protetoras* 🌌🖤 Durma bem.\n"
        "🌟 **Celestia:** As estrelas vão velar por você!! ⭐🤍✨ Boa noite com muito amor!!"
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
]

AMBOS_MAGIA = [
    (
        "🌑 **Aeon:** *traça sigilo sombrio* Proteção das trevas concedida. 🌌🖤🔮\n"
        "🌟 **Celestia:** *adiciona bênção de luz por cima* ✨🌟🤍 DUPLA PROTEÇÃO ATIVADA!!\n"
        "🌑 **Aeon:** ...nada passa por isso. 🖤"
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

    # Gatilho: mensagem menciona o bot OU contém "aeon" ou "celestia"
    fala_bot = (
        mention_ok
        or "aeon" in content
        or "celestia" in content
    )

    if not fala_bot:
        return

    # ────────────────────────────────────────
    # APRESENTAÇÃO
    # ────────────────────────────────────────
    if _m(content, [
        "quem são vocês", "quem sao voces", "se apresenta", "se apresentem",
        "o que são vocês", "o que sao voces", "quem é aeon", "quem é celestia",
        "quem sao aeon e celestia", "quem são aeon e celestia",
        "me fala de vocês", "me fala de voces", "o que é isso",
    ]):
        return await message.channel.send(random.choice(AMBOS_APRESENTACAO))

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
    # ELOGIOS / GENTILEZAS
    # ────────────────────────────────────────
    if _m(content, [
        "te amo aeon", "te amo celestia", "adoro vocês", "gosto de vocês",
        "gosto de voces", "vocês são fofos", "voces sao fofos",
        "são lindos", "sao lindos", "são incríveis", "sao incriveis",
        "gosto muito de vocês", "vocês são legais", "amo vocês",
        "amo voces", "são demais", "sao demais",
    ]):
        resp_aeon      = random.choice(AEON_REACOES_FOFAS)
        resp_celestia  = random.choice(CELESTIA_REACOES_FOFAS)
        return await message.channel.send(
            f"{_fala_aeon(resp_aeon)}\n{_fala_celestia(resp_celestia)}"
        )

    if _m(content, [
        "vocês são lindos", "voces sao lindos", "são maravilhosos",
        "sao maravilhosos", "adoro vocês dois", "amo os dois",
    ]):
        return await message.channel.send(
            f"{_fala_celestia(random.choice(CELESTIA_REACOES_FOFAS))}\n"
            f"{_fala_aeon(random.choice(AEON_REACOES_FOFAS))}"
        )

    # ────────────────────────────────────────
    # BOM DIA
    # ────────────────────────────────────────
    if _m(content, [
        "bom dia aeon", "bom dia celestia", "bom dia aeon e celestia",
        "bom dia celestia e aeon", "bom dia gatos", "bom dia gatinhos",
    ]):
        if "aeon" in content and "celestia" not in content:
            return await message.channel.send(_fala_aeon(random.choice(AEON_BOM_DIA)))
        if "celestia" in content and "aeon" not in content:
            return await message.channel.send(_fala_celestia(random.choice(CELESTIA_BOM_DIA)))
        return await message.channel.send(random.choice(AMBOS_BOM_DIA))

    if _m(content, ["bom dia"]) and ("aeon" in content or "celestia" in content):
        if "aeon" in content:
            return await message.channel.send(_fala_aeon(random.choice(AEON_BOM_DIA)))
        return await message.channel.send(_fala_celestia(random.choice(CELESTIA_BOM_DIA)))

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
    if mention_ok or (ambos_nome and len(content) < 30):
        respostas_duo = [
            "🌑 **Aeon:** *abre um olho* ...me chamou. 🖤\n🌟 **Celestia:** OI OI OI!! 🤍✨ Fala!!",
            "🌟 **Celestia:** AAAAAA nos chamaram!! 🌟🤍 O que foi??\n🌑 **Aeon:** ...estamos aqui. 🖤",
            "🌑 **Aeon:** *emerge das sombras* Sim. 🖤\n🌟 **Celestia:** *aparece num flash de luz* Oi!! 🌟🤍✨ Precisando de algo??",
            "🌟 **Celestia:** *salta animada* Fomos chamados!! 💫🤍 O que você precisa??\n🌑 **Aeon:** ...fala. 🖤🌑",
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
    if _m(content, ["como você está aeon", "como vc está aeon", "tudo bem aeon", "tudo bom aeon", "como tá aeon"]):
        ops = [
            "🌑 **Aeon:** ...funcional. 🖤 O que, para os padrões das trevas, é excelente.",
            "🌑 **Aeon:** A escuridão está estável. 🌑🖤 Eu também.",
            "🌑 **Aeon:** *olha para o horizonte sombrio* ...bem o suficiente. 🖤 E você?",
            "🌑 **Aeon:** Ninguém pergunta isso com frequência. 🌙🖤 ...fico bem. Obrigado.",
        ]
        return await message.channel.send(random.choice(ops))

    if _m(content, ["como você está celestia", "como vc está celestia", "tudo bem celestia", "tudo bom celestia", "como tá celestia"]):
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
    # IA (Groq) — fallback para conversa livre
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

    # Escolhe qual gato responde pela IA com base no contexto
    if "aeon" in content and "celestia" not in content:
        system_prompt = SYSTEM_PROMPT_AEON
        prefixo_resp  = "🌑 **Aeon:** "
    elif "celestia" in content and "aeon" not in content:
        system_prompt = SYSTEM_PROMPT_CELESTIA
        prefixo_resp  = "🌟 **Celestia:** "
    else:
        # Ambos — alterna aleatoriamente ou usa os dois
        usar_ambos = random.random() < 0.4
        if usar_ambos:
            # Faz duas chamadas simultâneas
            async with message.channel.typing():
                canal_id = message.channel.id
                if canal_id not in _groq_historico:
                    _groq_historico[canal_id] = []
                _groq_historico[canal_id].append({
                    "role": "user",
                    "content": f"{message.author.display_name}: {texto_limpo}"
                })
                if len(_groq_historico[canal_id]) > 20:
                    _groq_historico[canal_id] = _groq_historico[canal_id][-20:]

                try:
                    async with aiohttp.ClientSession() as session:
                        # Aeon
                        req_aeon = session.post(
                            GROQ_API_URL,
                            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                            json={
                                "model": GROQ_MODEL,
                                "messages": [
                                    {"role": "system", "content": SYSTEM_PROMPT_AEON},
                                    *_groq_historico[canal_id]
                                ],
                                "max_tokens": 256,
                                "temperature": 0.75
                            }
                        )
                        # Celestia
                        req_celestia = session.post(
                            GROQ_API_URL,
                            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                            json={
                                "model": GROQ_MODEL,
                                "messages": [
                                    {"role": "system", "content": SYSTEM_PROMPT_CELESTIA},
                                    *_groq_historico[canal_id]
                                ],
                                "max_tokens": 256,
                                "temperature": 0.85
                            }
                        )
                        async with req_aeon as ra, req_celestia as rc:
                            da = await ra.json()
                            dc = await rc.json()

                    ra_txt = da["choices"][0]["message"]["content"].strip() if "choices" in da else "..."
                    rc_txt = dc["choices"][0]["message"]["content"].strip() if "choices" in dc else "✨"

                    resposta_final = f"🌑 **Aeon:** {ra_txt}\n🌟 **Celestia:** {rc_txt}"
                    _groq_historico[canal_id].append({"role": "assistant", "content": resposta_final})

                    if len(resposta_final) <= 2000:
                        return await message.reply(resposta_final)
                    for parte in [resposta_final[i:i+1990] for i in range(0, len(resposta_final), 1990)]:
                        await message.channel.send(parte)
                    return
                except Exception:
                    return await message.channel.send(
                        "🌑 **Aeon:** ...as sombras perturbaram a transmissão. 🖤\n"
                        "🌟 **Celestia:** Algo deu errado!! 😭🤍 Tenta de novo?? ✨"
                    )
        else:
            escolhido = random.choice(["aeon", "celestia"])
            if escolhido == "aeon":
                system_prompt = SYSTEM_PROMPT_AEON
                prefixo_resp  = "🌑 **Aeon:** "
            else:
                system_prompt = SYSTEM_PROMPT_CELESTIA
                prefixo_resp  = "🌟 **Celestia:** "

    # Chamada única à IA
    async with message.channel.typing():
        canal_id = message.channel.id
        if canal_id not in _groq_historico:
            _groq_historico[canal_id] = []
        _groq_historico[canal_id].append({
            "role": "user",
            "content": f"{message.author.display_name}: {texto_limpo}"
        })
        if len(_groq_historico[canal_id]) > 20:
            _groq_historico[canal_id] = _groq_historico[canal_id][-20:]

        msgs_api = [
            {"role": "system", "content": system_prompt},
            *_groq_historico[canal_id]
        ]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    GROQ_API_URL,
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                    json={"model": GROQ_MODEL, "messages": msgs_api, "max_tokens": 512, "temperature": 0.85}
                ) as resp:
                    data = await resp.json()

            if "choices" not in data:
                return await message.channel.send(
                    "🌑 **Aeon:** ...as sombras engoliriam a resposta. 🖤\n"
                    "🌟 **Celestia:** Oops!! Erro!! 😭🤍 Tenta de novo?? ✨"
                )

            resposta = data["choices"][0]["message"]["content"].strip()
            _groq_historico[canal_id].append({"role": "assistant", "content": resposta})

            resposta_final = f"{prefixo_resp}{resposta}"
            if len(resposta_final) <= 2000:
                return await message.reply(resposta_final)
            for parte in [resposta_final[i:i+1990] for i in range(0, len(resposta_final), 1990)]:
                await message.channel.send(parte)

        except Exception:
            return await message.channel.send(
                "🌑 **Aeon:** ...silêncio das trevas. Algo falhou. 🖤\n"
                "🌟 **Celestia:** Não conseguimos responder agora!! 😭🤍 Tenta mais tarde!! ✨"
            )


# ══════════════════════════════════════════════
# COMANDOS
# ══════════════════════════════════════════════

@bot.command(name="aeon")
async def cmd_aeon(ctx, *, texto: str = None):
    """Fala diretamente com o Aeon."""
    if not texto:
        return await ctx.send(_fala_aeon("...me chamou. Diga algo. 🖤🌑"))
    canal_id = ctx.channel.id
    if canal_id not in _groq_historico:
        _groq_historico[canal_id] = []
    _groq_historico[canal_id].append({"role": "user", "content": f"{ctx.author.display_name}: {texto}"})
    if len(_groq_historico[canal_id]) > 20:
        _groq_historico[canal_id] = _groq_historico[canal_id][-20:]
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    GROQ_API_URL,
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": GROQ_MODEL,
                        "messages": [{"role": "system", "content": SYSTEM_PROMPT_AEON}, *_groq_historico[canal_id]],
                        "max_tokens": 512, "temperature": 0.75
                    }
                ) as resp:
                    data = await resp.json()
            if "choices" not in data:
                return await ctx.send(_fala_aeon("...as trevas calaram minha resposta. 🖤"))
            resposta = data["choices"][0]["message"]["content"].strip()
            _groq_historico[canal_id].append({"role": "assistant", "content": resposta})
            await ctx.reply(_fala_aeon(resposta))
        except Exception:
            await ctx.send(_fala_aeon("...falha no canal escuro. 🖤"))


@bot.command(name="celestia")
async def cmd_celestia(ctx, *, texto: str = None):
    """Fala diretamente com a Celestia."""
    if not texto:
        return await ctx.send(_fala_celestia("OI!! Me fala algo!! 🤍✨🌟"))
    canal_id = ctx.channel.id
    if canal_id not in _groq_historico:
        _groq_historico[canal_id] = []
    _groq_historico[canal_id].append({"role": "user", "content": f"{ctx.author.display_name}: {texto}"})
    if len(_groq_historico[canal_id]) > 20:
        _groq_historico[canal_id] = _groq_historico[canal_id][-20:]
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    GROQ_API_URL,
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": GROQ_MODEL,
                        "messages": [{"role": "system", "content": SYSTEM_PROMPT_CELESTIA}, *_groq_historico[canal_id]],
                        "max_tokens": 512, "temperature": 0.85
                    }
                ) as resp:
                    data = await resp.json()
            if "choices" not in data:
                return await ctx.send(_fala_celestia("Opa!! Não consegui responder!! 😭🤍"))
            resposta = data["choices"][0]["message"]["content"].strip()
            _groq_historico[canal_id].append({"role": "assistant", "content": resposta})
            await ctx.reply(_fala_celestia(resposta))
        except Exception:
            await ctx.send(_fala_celestia("Eita, deu erro!! 😭🤍 Tenta de novo??"))


@bot.command(name="duo")
async def cmd_duo(ctx, *, texto: str = None):
    """Os dois respondem ao mesmo tempo."""
    if not texto:
        return await ctx.send(random.choice(AMBOS_APRESENTACAO))
    canal_id = ctx.channel.id
    if canal_id not in _groq_historico:
        _groq_historico[canal_id] = []
    _groq_historico[canal_id].append({"role": "user", "content": f"{ctx.author.display_name}: {texto}"})
    if len(_groq_historico[canal_id]) > 20:
        _groq_historico[canal_id] = _groq_historico[canal_id][-20:]
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                ra = await (await session.post(
                    GROQ_API_URL,
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                    json={"model": GROQ_MODEL,
                          "messages": [{"role": "system", "content": SYSTEM_PROMPT_AEON}, *_groq_historico[canal_id]],
                          "max_tokens": 256, "temperature": 0.75}
                )).json()
                rc = await (await session.post(
                    GROQ_API_URL,
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                    json={"model": GROQ_MODEL,
                          "messages": [{"role": "system", "content": SYSTEM_PROMPT_CELESTIA}, *_groq_historico[canal_id]],
                          "max_tokens": 256, "temperature": 0.85}
                )).json()
            ta = ra["choices"][0]["message"]["content"].strip() if "choices" in ra else "..."
            tc = rc["choices"][0]["message"]["content"].strip() if "choices" in rc else "✨"
            final = f"🌑 **Aeon:** {ta}\n🌟 **Celestia:** {tc}"
            _groq_historico[canal_id].append({"role": "assistant", "content": final})
            await ctx.reply(final)
        except Exception:
            await ctx.send(
                "🌑 **Aeon:** ...interferência nas trevas. 🖤\n"
                "🌟 **Celestia:** Algo errado!! 😭🤍 Tenta de novo?? ✨"
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
