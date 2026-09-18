#!/usr/bin/env python3
"""
Bengali -> phonetic Roman romanizer.

Aims for how Bengali actually sounds when spoken/sung casually
(e.g. "shamne", "bhasho"), not a strict Sanskrit-style letter-for-letter
transliteration scheme (which is what libraries like indic_transliteration
give you, and why the old output looked garbled/wrong).
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


def romanize(text):
    text = unicodedata.normalize('NFC', text)
    parts = re.split(r'(\s+)', text)
    result = ''.join(p if p.isspace() else _romanize_word(p) for p in parts)
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
    main()#!/usr/bin/env python3
"""
Bengali -> phonetic Roman romanizer.

Aims for how Bengali actually sounds when spoken/sung casually
(e.g. "shamne", "bhasho"), not a strict Sanskrit-style letter-for-letter
transliteration scheme (which is what libraries like indic_transliteration
give you, and why the old output looked garbled/wrong).
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


def romanize(text):
    text = unicodedata.normalize('NFC', text)
    parts = re.split(r'(\s+)', text)
    return ''.join(p if p.isspace() else _romanize_word(p) for p in parts)


def main():
    if len(sys.argv) > 1:
        text = ' '.join(sys.argv[1:])
    else:
        text = sys.stdin.read()
    print(romanize(text.strip()))


if __name__ == '__main__':
    main()
