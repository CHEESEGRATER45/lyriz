#!/usr/bin/env python3
"""
Bengali -> phonetic Roman romanizer.

Aims for how Bengali actually sounds when spoken/sung casually
(e.g. "shamne", "bhasho"), not a strict Sanskrit-style letter-for-letter
transliteration scheme (which is what libraries like indic_transliteration
give you, and why the old output looked garbled/wrong).

English loanwords written in Bengali script (বাস, লাভ, ফোন ...) are looked up
in a dictionary first and come out as the English word ("bus", "love",
"phone") instead of being sounded out letter by letter. Case/plural endings
glued to a loanword (বাসেতে, ফোনটাও, লাভগুলোকে ...) are split off, longest
ending first, and can stack up to two deep (বাসটাকেও -> "bus-take-o").
"""
import sys
import re
import unicodedata

# Independent vowels (used when a vowel stands on its own, not attached to a consonant)
INDEP_VOWELS = {
    'অ': 'o', 'আ': 'a', 'ই': 'i', 'ঈ': 'i', 'উ': 'u', 'ঊ': 'u',
    'ঋ': 'ri', 'এ': 'e', 'ঐ': 'oi', 'ও': 'o', 'ঔ': 'ou',
}

# Vowel signs (matras) attached to a consonant
VOWEL_SIGNS = {
    'া': 'a', 'ি': 'i', 'ী': 'i', 'ু': 'u', 'ূ': 'u',
    'ৃ': 'ri', 'ে': 'e', 'ৈ': 'oi', 'ো': 'o', 'ৌ': 'ou',
}

# Consonants -> base sound (inherent vowel handled separately below)
CONSONANTS = {
    'ক': 'k', 'খ': 'kh', 'গ': 'g', 'ঘ': 'gh', 'ঙ': 'ng',
    'চ': 'ch', 'ছ': 'chh', 'জ': 'j', 'ঝ': 'jh', 'ঞ': 'n',
    'ট': 't', 'ঠ': 'th', 'ড': 'd', 'ঢ': 'dh', 'ণ': 'n',
    'ত': 't', 'থ': 'th', 'দ': 'd', 'ধ': 'dh', 'ন': 'n',
    'প': 'p', 'ফ': 'ph', 'ব': 'b', 'ভ': 'bh', 'ম': 'm',
    'য': 'j', 'র': 'r', 'ল': 'l',
    'শ': 'sh', 'ষ': 'sh', 'স': 'sh',   # sibilants merge to "sh" in spoken Bengali
    'হ': 'h',
    'ৎ': 't',
}

HASANTA = '্'
CHANDRABINDU = 'ঁ'
ANUSVARA = 'ং'
VISARGA = 'ঃ'
NUKTA = '়'

# Nukta letters (ড় ঢ় য়) are stored as base-letter + NUKTA (U+09BC), as two
# separate codepoints -- Bengali nukta sequences are on Unicode's composition
# exclusion list, so NFC normalization will NOT merge them for you.
NUKTA_CONSONANTS = {
    'ড': 'r', 'ঢ': 'rh', 'য': 'y',
}

# A handful of conjuncts (consonant + hasanta + consonant) where the second
# consonant isn't actually pronounced as itself -- e.g. জ্ব is just a heavy
# "j" (জ্বলে -> "jole", not "jobole"). This is NOT an exhaustive list --
# Bengali has many irregular conjunct pronunciations (ক্ষ, জ্ঞ, শ্ব, etc.)
# that a purely rule-based script can't fully cover without a dictionary.
SILENT_SECOND_CONJUNCTS = {
    ('জ', 'ব'): 'j',
}

DIGITS = {
    '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
    '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9',
}

# ---------------------------------------------------------------------------
# English loanwords written in Bengali script -> English spelling.
# Format: "<bengali> <english>" pairs, whitespace separated, any number per line.
# Underscore = space in multi-word english (ice_cream). Add more freely.
# ---------------------------------------------------------------------------
_RAW = """
# ---- love / emotions / people ----
লাভ love লাভার lover হার্ট heart হার্টবিট heartbeat ড্রিম dream ড্রিমস dreams
হ্যাপি happy স্যাড sad সরি sorry প্লিজ please থ্যাংক thank থ্যাংকস thanks
থ্যাঙ্কস thanks কিস kiss হাগ hug স্মাইল smile টিয়ার tear টিয়ার্স tears
ক্রাই cry ক্রাইং crying লোনলি lonely লোন্লি lonely পেইন pain ব্রেকআপ breakup
ব্রোকেন broken ফরএভার forever ফরেভার forever নেভার never এভার ever
অলওয়েজ always ফিলিং feeling ফিল feel ফিলস feels ফিলিংস feelings মিস miss
মিসিং missing কেয়ার care ট্রাস্ট trust ফেইথ faith হোপ hope ফিয়ার fear
অ্যাংরি angry এংরি angry ক্রেজি crazy ম্যাড mad ক্রাশ crush ডার্লিং darling
বেবি baby বেবী baby হানি honey সুইট sweet সুইটহার্ট sweetheart
বিউটিফুল beautiful বিউটি beauty কিউট cute প্রিটি pretty হ্যান্ডসাম handsome
সেক্সি sexy হট hot কুল cool স্টাইল style স্টাইলিশ stylish ফ্যাশন fashion
ফ্রেন্ড friend ফ্রেন্ডস friends ফ্রেন্ডশিপ friendship বেস্ট best বেস্টি bestie
বয়ফ্রেন্ড boyfriend গার্লফ্রেন্ড girlfriend বয় boy গার্ল girl ম্যান man
ওম্যান woman কিং king কুইন queen প্রিন্স prince প্রিন্সেস princess
এঞ্জেল angel অ্যাঞ্জেল angel ডেভিল devil গড god হেভেন heaven হেল hell
প্যারাডাইস paradise ম্যাজিক magic মিরাকল miracle লাক luck লাকি lucky ফেট fate
ডেস্টিনি destiny লাইফ life ডেথ death ডাই die লিভিং living সোল soul মাইন্ড mind
বডি body লিপস lips হ্যান্ড hand ফেস face হেয়ার hair স্কিন skin আইজ eyes
ফ্যামিলি family মম mom ড্যাড dad মাম্মি mummy পাপা papa সিস্টার sister
ব্রাদার brother আঙ্কল uncle আন্টি aunty কাজিন cousin ম্যারেজ marriage
ওয়েডিং wedding ব্রাইড bride গ্রুম groom হানিমুন honeymoon ডেট date ডেটিং dating
রিলেশন relation রিলেশনশিপ relationship ইমোশন emotion ইমোশনাল emotional
মেমোরি memory মেমোরিজ memories ফ্লার্ট flirt ডিয়ার dear গ্যাং gang
ম্যাডাম madam স্যার sir মিস্টার mister মিসেস mrs প্রমিস promise উইশ wish
সারপ্রাইজ surprise গিফট gift বার্থডে birthday স্যাক্রিফাইস sacrifice
টেনশন tension স্ট্রেস stress প্রবলেম problem সলিউশন solution

# ---- time ----
টাইম time ডে day নাইট night মর্নিং morning ইভনিং evening টুডে today
টুনাইট tonight টুমরো tomorrow ইয়েস্টারডে yesterday উইক week উইকএন্ড weekend
মান্থ month ইয়ার year আওয়ার hour মিনিট minute সেকেন্ড second নাউ now লেট late
আর্লি early সানডে sunday মানডে monday টিউসডে tuesday ওয়েডনেসডে wednesday
থার্সডে thursday ফ্রাইডে friday স্যাটারডে saturday নিউ new ইয়াং young
ওল্ড old হলিডে holiday ভ্যাকেশন vacation ক্রিসমাস christmas

# ---- music / media ----
সং song সংস songs মিউজিক music মিউজিশিয়ান musician ড্যান্স dance ডান্স dance
ডান্সার dancer ডিজে dj ব্যান্ড band গিটার guitar পিয়ানো piano ড্রাম drum
ড্রামস drums বেস bass বিট beat বিটস beats রিদম rhythm মেলোডি melody
ভয়েস voice সিংগার singer সিঙ্গার singer সিং sing কনসার্ট concert স্টেজ stage
মাইক mic মাইক্রোফোন microphone রেডিও radio অ্যালবাম album ট্র্যাক track
রিমিক্স remix লিরিক্স lyrics রক rock পপ pop জ্যাজ jazz ব্লুজ blues
হিপহপ hip_hop র‍্যাপ rap রেপ rap ডিস্কো disco হেডফোন headphone
হেডফোনস headphones স্পিকার speaker ভলিউম volume প্লে play প্লেলিস্ট playlist
পজ pause রিপিট repeat শাফল shuffle মুভি movie ফিল্ম film সিনেমা cinema
হিরো hero হিরোইন heroine ভিলেন villain সুপারস্টার superstar ড্রামা drama
শো show ফেস্টিভ্যাল festival টিভি tv ভিডিও video ফটো photo ফটোগ্রাফ photograph
পিকচার picture পোস্টার poster আর্ট art আর্টিস্ট artist ডিজাইন design মডেল model

# ---- tech / phone / social ----
ফোন phone মোবাইল mobile মেসেজ message টেক্সট text কলিং calling ইন্টারনেট internet
ওয়াইফাই wifi ফেসবুক facebook ইনস্টাগ্রাম instagram হোয়াটসঅ্যাপ whatsapp
ইউটিউব youtube গুগল google ইমেইল email ইমেল email অনলাইন online অফলাইন offline
লগইন login পাসওয়ার্ড password ডাউনলোড download আপলোড upload স্ক্রিন screen
ক্যামেরা camera সেলফি selfie লাইক like শেয়ার share কমেন্ট comment ফলো follow
ফলোয়ার follower স্টোরি story পোস্ট post ট্রেন্ড trend ভাইরাল viral ব্লক block
ডিলিট delete সেভ save সেন্ড send রিসিভ receive ডিজিটাল digital
কম্পিউটার computer ল্যাপটপ laptop কিবোর্ড keyboard মাউস mouse বাটন button
সুইচ switch চার্জ charge ব্যাটারি battery সিগন্যাল signal নেটওয়ার্ক network
ইনবক্স inbox নোটিফিকেশন notification ট্যাগ tag স্ট্যাটাস status ইমোজি emoji
ভাইব vibe ভাইবস vibes হ্যালো hello

# ---- transport / travel ----
বাস bus ট্রেন train ট্রাম tram ট্যাক্সি taxi কার car বাইক bike সাইকেল cycle
প্লেন plane এয়ারপোর্ট airport স্টেশন station স্টপ stop রোড road স্ট্রিট street
হাইওয়ে highway ট্রাক truck ড্রাইভ drive ড্রাইভার driver রাইড ride ট্রিপ trip
ট্যুর tour জার্নি journey ট্রাভেল travel টিকিট ticket পাসপোর্ট passport
হোটেল hotel ফ্লাইট flight ব্রিজ bridge বোট boat শিপ ship ইঞ্জিন engine
ব্রেক brake স্পিড speed গিয়ার gear ট্রাফিক traffic পার্ক park পার্কিং parking
লেন lane সিটি city কান্ট্রি country ওয়ার্ল্ড world

# ---- home / food / everyday ----
হোম home হাউস house রুম room রুমমেট roommate বেড bed কিচেন kitchen
বাথরুম bathroom গার্ডেন garden ব্যালকনি balcony গেট gate ডোর door
উইন্ডো window ওয়াল wall ফ্লোর floor রুফ roof টেবিল table চেয়ার chair
সোফা sofa ফ্যান fan লাইট light ল্যাম্প lamp ক্যান্ডেল candle ফ্রিজ fridge
কাপ cup গ্লাস glass প্লেট plate কফি coffee টি tea মিল্ক milk জুস juice
ওয়াটার water ওয়াইন wine বিয়ার beer ভডকা vodka হুইস্কি whiskey ড্রিংক drink
ড্রিংকস drinks সিগারেট cigarette চকোলেট chocolate কেক cake আইসক্রিম ice_cream
পিৎজা pizza বার্গার burger স্যান্ডউইচ sandwich চিপস chips কুকি cookie
ব্রেড bread বাটার butter চিজ cheese ডিনার dinner লাঞ্চ lunch
ব্রেকফাস্ট breakfast ফুড food রেস্টুরেন্ট restaurant ক্যাফে cafe ক্লাব club
পাব pub পার্টি party গেম game গেমস games প্লেয়ার player টিম team ম্যাচ match
ফুটবল football ক্রিকেট cricket গোল goal স্কুল school কলেজ college ক্লাস class
ইউনিভার্সিটি university টিচার teacher স্টুডেন্ট student বুক book পেন pen
পেনসিল pencil পেপার paper ডায়েরি diary নোট note ফর্ম form রিপোর্ট report
মিরর mirror ফ্লাশ flash ফ্রেম frame পেইন্ট paint পেইন্টিং painting
ড্রয়িং drawing মানি money ক্যাশ cash ডলার dollar রিচ rich পুওর poor বস boss
ম্যানেজার manager অফিস office জব job ওয়ার্ক work ডিউটি duty বিজি busy
ডক্টর doctor হসপিটাল hospital মেডিসিন medicine ইনজেকশন injection নার্স nurse
পুলিশ police আর্মি army সোলজার soldier ক্যাপ্টেন captain

# ---- colors ----
রেড red ব্লু blue গ্রিন green গ্রীন green ইয়েলো yellow ব্ল্যাক black
হোয়াইট white পিঙ্ক pink পার্পল purple অরেঞ্জ orange গোল্ড gold গোল্ডেন golden
সিলভার silver গ্রে grey ব্রাউন brown কালার color কালারফুল colorful

# ---- nature / world ----
সান sun মুন moon স্টার star স্টারস stars স্কাই sky রেইন rain ওশান ocean
রিভার river ফায়ার fire আইস ice স্নো snow উইন্ড wind স্টর্ম storm
থান্ডার thunder ফ্লাওয়ার flower রোজ rose ফরেস্ট forest মাউন্টেন mountain
আইল্যান্ড island বিচ beach সামার summer উইন্টার winter স্প্রিং spring
অটাম autumn আর্থ earth ইউনিভার্স universe স্পেস space গ্যালাক্সি galaxy
প্ল্যানেট planet নেচার nature ট্রি tree ক্লাউড cloud ক্লাউডস clouds
শ্যাডো shadow

# ---- adjectives / verbs / exclamations ----
ওকে ok ওকেই ok ইয়েস yes নো no বাই bye বাইবাই bye_bye গুড good গুডবাই goodbye
গুডনাইট goodnight ব্যাড bad গ্রেট great নাইস nice ফাইন fine ফানি funny ফান fun
ওয়াইল্ড wild ফ্রি free ফ্রিডম freedom পাওয়ার power পাওয়ারফুল powerful
ফোর্স force ফাইট fight ওয়ার war পিস peace রিয়েল real ফেক fake ট্রু true
ফলস false সিক্রেট secret মিস্ট্রি mystery হিস্ট্রি history সুপার super
মেগা mega আলটিমেট ultimate ফাইনাল final ফার্স্ট first লাস্ট last নেক্সট next
ওয়ান one থ্রি three ফোর four ফাইভ five টেন ten হান্ড্রেড hundred
থাউজ্যান্ড thousand মিলিয়ন million জিরো zero নাম্বার number ক্লিয়ার clear
ক্লোজ close ওপেন open স্টার্ট start এন্ড end ফিনিশ finish রেডি ready
স্টেডি steady গো go কাম come স্লো slow ফাস্ট fast হার্ড hard সফট soft
লাউড loud সাইলেন্ট silent সাইলেন্স silence ডার্ক dark ব্রাইট bright
শাইন shine শাইনিং shining গ্লো glow ফ্লাই fly রান run জাম্প jump রাইজ rise
হেল্প help সেফ safe রিস্ক risk চান্স chance চয়েস choice প্ল্যান plan
আইডিয়া idea রিজন reason ম্যাটার matter সিরিয়াস serious সিম্পল simple
পারফেক্ট perfect অলরাইট alright সিওর sure এক্সকিউজ excuse প্রাইভেট private
পাবলিক public ফ্রন্ট front ব্যাক back রাইট right আপ up ডাউন down আউট out
ওভার over আন্ডার under উইথ with উইদাউট without ইনসাইড inside আউটসাইড outside
টপ top বটম bottom সেন্টার center মিডল middle এজ edge কর্নার corner
লাইন line পয়েন্ট point সার্কেল circle স্কয়ার square ইউ you ওয়ে way
ঘোস্ট ghost ডেমন demon মনস্টার monster জম্বি zombie হরর horror
ক্রিমিনাল criminal জেল jail বম bomb কিল kill ব্লাড blood নাইফ knife
ক্যাচ catch ট্রাই try ফরগেট forget রিমেম্বার remember ফলিং falling
ব্রেথ breathe ব্রিদ breathe টাচ touch হোল্ড hold লেটস lets
"""


def _load(raw):
    table = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        toks = line.split()
        for k in range(0, len(toks) - 1, 2):
            table[toks[k]] = toks[k + 1].replace('_', ' ')
    return table


LOANWORDS = _load(_RAW)

# Bengali case / plural / emphasis endings often glued to a loanword:
# বাসে, বাসেতে, ফোনটা, ফোনটাও, লাভের, ফ্রেন্ডদেরকে ...
# The lookup below always tries the LONGEST ending first (see _SUFFIX_ORDER),
# so েতে beats তে beats ে, and টাকে beats কে, no matter how this dict is ordered.
# য় (য + nukta) is written with escapes so it matches NFC-normalized text.
_YA = '\u09af\u09bc'

_SUFFIXES = {
    # plural (-gulo family)
    'গুলোকে': 'guloke', 'গুলোতে': 'gulote', 'গুলোর': 'gulor',
    'গুলোও': 'gulo-o', 'গুলোই': 'guloi', 'গুলো': 'gulo',
    'গুলিকে': 'gulike', 'গুলির': 'gulir', 'গুলি': 'guli',
    'গুলা': 'gula',
    # "of / to" for people-type words (-der family)
    'দেরকে': 'derke', 'দেরও': 'dero', 'দেরই': 'derei', 'দের': 'der',
    'েদের': 'eder',
    # -e family (locative / instrumental)
    'েতেও': 'eteo', 'েতেই': 'etei', 'েতে': 'ete',
    'েকেও': 'ekeo', 'েকে': 'eke',
    'েরা': 'era', 'েরও': 'ero', 'েরই': 'erei', 'ের': 'er', 'এর': 'er',
    'েও': 'eo', 'েই': 'ei',
    'ে': 'e',
    # -ta / -ti (the definite article glued on)
    'টাকেও': 'takeo', 'টাতেও': 'tateo',
    'টাকে': 'take', 'টাতে': 'tate', 'টাও': 'tao', 'টাই': 'tai',
    'টার': 'tar', 'টা' + _YA: 'tay', 'টা': 'ta',
    'টিকেও': 'tikeo', 'টিকে': 'tike', 'টিতে': 'tite', 'টিও': 'tio',
    'টিই': 'tii', 'টির': 'tir', 'টি': 'ti',
    'টুকু': 'tuku', 'খানা': 'khana', 'খানি': 'khani',
    # -ke / -te / -ra / -r
    'কেও': 'keo', 'কেই': 'kei', 'কে': 'ke',
    'তেও': 'teo', 'তেই': 'tei', 'তে': 'te',
    'রাও': 'rao', 'রাই': 'rai', 'রা': 'ra',
    'রও': 'ro', 'রই': 'roi', 'র': 'r',
    'রে': 're',
    # bare emphasis particles: বাসও, বাসই
    'ও': 'o', 'ই': 'i',
}

# longest ending first; ties broken by the ending itself so the order is stable
_SUFFIX_ORDER = sorted(_SUFFIXES.items(), key=lambda kv: (-len(kv[0]), kv[0]))

_MAX_SUFFIX_DEPTH = 2  # how many endings may be stacked (বাস + টা + কে)


def _match(core, depth=0):
    """English form of core (exact, or loanword + up to two endings), else None."""
    if core in LOANWORDS:
        return LOANWORDS[core]
    if depth >= _MAX_SUFFIX_DEPTH:
        return None
    for suf, roman in _SUFFIX_ORDER:
        if core.endswith(suf) and len(core) > len(suf):
            stem = _match(core[:-len(suf)], depth + 1)
            if stem is not None:
                return stem + '-' + roman
    return None


def _loan_lookup(word):
    """Return the English form of a Bengali-script loanword, or None.

    Keeps surrounding punctuation. Tries an exact match first, then
    stem + common endings (appended after a hyphen, e.g. বাসে -> "bus-e",
    বাসেতে -> "bus-ete").
    """
    # peel punctuation off both ends so "বাস," or "(লাভ)" still match.
    # (str.isalnum() is False for Bengali vowel signs, so go by Unicode category.)
    def _is_punct(c):
        return unicodedata.category(c)[0] in 'PSZC'
    start, end = 0, len(word)
    while start < end and _is_punct(word[start]):
        start += 1
    while end > start and _is_punct(word[end - 1]):
        end -= 1
    core = word[start:end]
    if not core:
        return None
    pre, post = word[:start], word[end:]

    hit = _match(core)
    if hit is None:
        return None
    return pre + hit + post


def _romanize_word(word):
    out = []
    n = len(word)
    i = 0
    last_was_i_sound = False  # for the য -> "y" glide heuristic (e.g. লুকিয়ে -> lukiye)

    # index of the last consonant/independent-vowel character in the word;
    # used to decide if a bare consonant's inherent vowel survives (-> "o")
    # or drops (word-final position).
    last_letter_idx = -1
    for j, ch in enumerate(word):
        if ch in CONSONANTS or ch in INDEP_VOWELS:
            last_letter_idx = j

    while i < n:
        ch = word[i]

        if ch in DIGITS:
            out.append(DIGITS[ch])
            i += 1
            continue

        if ch in CONSONANTS:
            base = CONSONANTS[ch]
            consumed = 1  # how many source chars this consonant token took (1, or 2 w/ nukta)

            nxt = word[i + 1] if i + 1 < n else ''
            if nxt == NUKTA and ch in NUKTA_CONSONANTS:
                base = NUKTA_CONSONANTS[ch]
                consumed = 2
                nxt = word[i + 2] if i + 2 < n else ''
            elif nxt == HASANTA and (ch, word[i + 2:i + 3]) in SILENT_SECOND_CONJUNCTS:
                base = SILENT_SECOND_CONJUNCTS[(ch, word[i + 2])]
                consumed = 3
                nxt = word[i + 3] if i + 3 < n else ''

            if ch == 'য' and consumed == 1 and last_was_i_sound:
                base = 'y'  # glide after an i/e sound (e.g. লুকিয়ে -> lukiye)

            if nxt == HASANTA:
                # conjunct: inherent vowel dropped, glue straight to next consonant
                out.append(base)
                last_was_i_sound = False
                i += consumed + 1
                continue

            if nxt in VOWEL_SIGNS:
                vowel = VOWEL_SIGNS[nxt]
                out.append(base + vowel)
                last_was_i_sound = (vowel == 'i')
                i += consumed + 1
                continue

            # bare consonant: no matra, no hasanta -> inherent vowel
            if i == last_letter_idx:
                out.append(base)           # word-final: schwa dropped
            else:
                out.append(base + 'o')     # mid-word: realized as short "o"
            last_was_i_sound = False
            i += consumed
            continue

        if ch in INDEP_VOWELS:
            out.append(INDEP_VOWELS[ch])
            last_was_i_sound = ch in ('ই', 'ঈ')
            i += 1
            continue

        if ch == ANUSVARA:
            out.append('ng')
            i += 1
            continue

        if ch == VISARGA:
            out.append('h')
            i += 1
            continue

        if ch == CHANDRABINDU:
            i += 1  # nasalization, approximated as silent
            continue

        out.append(ch)  # punctuation, latin text, etc. pass through untouched
        last_was_i_sound = False
        i += 1

    return ''.join(out)


def _romanize_token(tok):
    """Loanword dictionary first, then the normal phonetic rules."""
    hit = _loan_lookup(tok)
    return hit if hit else _romanize_word(tok)


def romanize(text):
    text = unicodedata.normalize('NFC', text)
    parts = re.split(r'(\s+)', text)
    result = ''.join(p if p.isspace() else _romanize_token(p) for p in parts)
    # capitalize the first letter of the line (each call is one lyric verse/line)
    for idx, c in enumerate(result):
        if c.isalpha():
            result = result[:idx] + c.upper() + result[idx + 1:]
            break
    return result


def main():
    if len(sys.argv) > 1:
        text = ' '.join(sys.argv[1:])
    else:
        text = sys.stdin.read()
    print(romanize(text.strip()))


if __name__ == '__main__':
    main()