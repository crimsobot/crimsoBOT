import pickle
import markovify
import random as r
import nltk
import re
import os

script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in

class POSifiedText(markovify.Text):
    def word_split(self, sentence):
        words = re.split(self.word_split_pattern, sentence)
        words = [ "::".join(tag) for tag in nltk.pos_tag(words) ]
        return words

    def word_join(self, words):
        sentence = " ".join(word.split("::")[0] for word in words)
        return sentence

def textClean(input):
    """Clean text for Markov corpus."""
    input = input.upper()
    input = re.sub('[^A-Z0-9 .,?!-\']+',' ',input)
    input = input.replace('\n',' ')
    input = input.replace('\r',' ')
    input = input.replace('\n',' ')
    input = input.replace('\r',' ')
    input = input.replace('  ',' ')
    output = input.replace('  ',' ')
    return output

def learner(list):
    """ input: list
       output: none"""
    # pickle.dump('\n'.join(list), open(script_dir+'\\ref\\crimso.p', 'ab'))
    with open(script_dir+'\\ref\\crimso.txt', 'a', encoding='utf8', errors='ignore') as f:
        f.write('%s\n' % list)
            
def scraper(list):
    """ input: list
       output: none"""
    # pickle.dump('\n'.join(list), open(script_dir+'\\ref\\crimso.p', 'ab'))
    with open(script_dir+'\\ref\\scrape.txt', 'a', encoding='utf8', errors='ignore') as f:
        f.write('%s\n' % list)

def markovScatter(list):
    """Write text file from list of strings."""
    with open(script_dir+'\\ref\\scatterbrain.txt', 'w', encoding='utf8', errors='ignore') as f:
        for item in list:
            if item.startswith('>') == False:
                if item.startswith('?') == False:
                    f.write("%s\n" % item)

    g = open(script_dir+'\\ref\\scatterbrain.txt','r', encoding='utf8', errors='ignore')
    li = g.read()
    g.close()

    # Note: listifying file() leaves \n at end of each list element
    st = "".join(li)
    # comment out next line to get case-sensitive version
    st = st.lower()
    se = set(st.split("\n"))
    text = "\n".join(sorted(se))

    text = text.replace('\n',' ')
    text = text.replace('\r',' ')
    text = text.replace('\n',' ')
    text = text.replace('\r',' ')
    text = text.replace('  ',' ')
    text = text.replace('  ',' ')
    text = text.replace('  ',' ')
    text = text.replace('  ',' ')
    text = text.replace('  ',' ')
    text = text.replace('  ',' ')
    text = text.upper()

    factor = 1

    model = markovify.Text(text, state_size=factor)
    out = None
    while out == None:
        out = model.make_short_sentence(r.randint(40,400))

    return out

def markovPoem(number_lines):
    """Write a poem."""
    g = open(script_dir+'\\ref\\all.txt', encoding='utf8', errors='ignore')
    text1 = g.read()
    g.close()
    text1 = textClean(text1)

    h = open(script_dir+'\\ref\\randoms.txt', encoding='utf8', errors='ignore')
    text2 = h.read()
    h.close()
    text2 = textClean(text2)

    poemFactor = 2

    crimso_model = markovify.Text(text1, state_size=poemFactor)
    other_model = markovify.Text(text2, state_size=poemFactor)
    model = markovify.combine([crimso_model,other_model],[1,2])

    outputPoem = []
    for i in range(int(number_lines)):
        outline = None
        while outline == None:
            outline = model.make_short_sentence(80)
        outputPoem.append(outline)

    outputPoem = '\n'.join(outputPoem)
    return outputPoem

def wisdom():
    """Wisdom."""
    f = open(script_dir+'\\ref\\wisdom.txt', encoding='utf8', errors='ignore')
    text = f.read()
    f.close()

    factor = 3
    model = markovify.Text(text, state_size=factor)

    output = None
    while output == None:
        output = model.make_short_sentence(300)

    return output

def rovin():
    """Wisdom."""
    f = open(script_dir+'\\ref\\rovin.txt', encoding='utf8', errors='ignore')
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
    f = open(script_dir+'\\ref\\crimso.txt', encoding='utf8', errors='ignore')
    text = f.read()
    f.close()

    factor = 2
    model = markovify.NewlineText(text, state_size=factor, retain_original=False)

    output = None
    while output == None:
        output = model.make_sentence()

    return output