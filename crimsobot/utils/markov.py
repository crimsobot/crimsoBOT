import random as r
import re

import markovify
import nltk

from crimsobot.utils import tools as c


class POSifiedText(markovify.Text):
    def word_split(self, sentence):
        words = re.split(self.word_split_pattern, sentence)
        words = ['::'.join(tag) for tag in nltk.pos_tag(words)]

        return words

    def word_join(self, words):
        sentence = ' '.join(word.split('::')[0] for word in words)

        return sentence


def clean_text(text):
    """Clean text for Markov corpus."""

    text = text.upper()
    text = re.sub(r"[^A-Z0-9 .,?!\-']+", ' ', text)
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('  ', ' ')
    text = text.replace('  ', ' ')

    return text


def learner(msg):
    """ input: list
       output: none"""

    # pickle.dump('\n'.join(list), open(c.clib_path_join('text', 'crimso.p'), 'ab'))
    with open(c.clib_path_join('text', 'crimso.txt'), 'a', encoding='utf8', errors='ignore') as f:
        f.write('%s\n' % msg)


def scraper(msg):
    """ input: list
       output: none"""

    # pickle.dump('\n'.join(list), open(c.clib_path_join('text', 'crimso.p'), 'ab'))
    with open(c.clib_path_join('text', 'scrape.txt'), 'a', encoding='utf8', errors='ignore') as f:
        f.write('%s\n' % msg)


def scatter(msg_list):
    """Write text file from list of strings."""

    with open(c.clib_path_join('text', 'scatterbrain.txt'), 'w', encoding='utf8', errors='ignore') as f:
        for item in msg_list:
            if not item.startswith('>'):
                if not item.startswith('?'):
                    f.write('%s\n' % item)

    g = open(c.clib_path_join('text', 'scatterbrain.txt'), 'r', encoding='utf8', errors='ignore')
    li = g.read()
    g.close()

    # Note: listifying file() leaves \n at end of each list element
    st = ''.join(li)
    # comment out next line to get case-sensitive version
    st = st.lower()
    se = set(st.split('\n'))
    text = '\n'.join(sorted(se))

    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('  ', ' ')
    text = text.replace('  ', ' ')
    text = text.replace('  ', ' ')
    text = text.replace('  ', ' ')
    text = text.replace('  ', ' ')
    text = text.replace('  ', ' ')
    text = text.upper()

    factor = 1

    model = markovify.Text(text, state_size=factor)
    out = None
    while out is None:
        out = model.make_short_sentence(r.randint(40, 400))

    return out


def poem(number_lines):
    """Write a poem."""

    g = open(c.clib_path_join('text', 'all.txt'), encoding='utf8', errors='ignore')
    text1 = g.read()
    g.close()
    text1 = clean_text(text1)

    h = open(c.clib_path_join('text', 'randoms.txt'), encoding='utf8', errors='ignore')
    text2 = h.read()
    h.close()
    text2 = clean_text(text2)

    poem_factor = 2

    crimso_model = markovify.Text(text1, state_size=poem_factor)
    other_model = markovify.Text(text2, state_size=poem_factor)
    model = markovify.combine([crimso_model, other_model], [1, 2])

    output_poem = []
    for _ in range(int(number_lines)):
        outline = None
        while outline is None:
            outline = model.make_short_sentence(80)
        output_poem.append(outline)

    output_poem = '\n'.join(output_poem)
    return output_poem


def wisdom():
    """Wisdom."""

    f = open(c.clib_path_join('text', 'wisdom.txt'), encoding='utf8', errors='ignore')
    text = f.read()
    f.close()

    factor = 3
    model = markovify.Text(text, state_size=factor)

    output = None
    while output is None:
        output = model.make_short_sentence(300)

    return output


def rovin():
    """Wisdom."""

    f = open(c.clib_path_join('text', 'rovin.txt'), encoding='utf8', errors='ignore')
    text = f.read()
    f.close()

    factor = 3
    model = markovify.Text(text, state_size=factor)

    output = []
    while len(output) < 5:
        output.append(model.make_short_sentence(300))
    output = ' '.join(output)

    return output


def crimso():
    f = open(c.clib_path_join('text', 'crimso.txt'), encoding='utf8', errors='ignore')
    text = f.read()
    f.close()

    factor = 2
    model = markovify.NewlineText(text, state_size=factor, retain_original=False)

    output = None
    while output is None:
        output = model.make_sentence()

    return output
