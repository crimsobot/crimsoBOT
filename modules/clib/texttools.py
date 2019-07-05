import re
from datetime import datetime

from . import astronomy, crimsotools as c


def block(input):
    block = ":regional_indicator_"
    numbs = ["zero","one","two","three","four","five","six","seven","eight","nine"]

    input = input.lower()
    input = re.sub('[^A-Za-z0-9 .?!]+',' ',input)

    output = ""
    n = len(input)

    for ii in range(n):
        isNum = 0
        # numeral
        try:
            int(input[ii])
            output += ":"
            output += numbs[int(input[ii])]
            output += ":\u200A"
            isNum = 1
        except ValueError:
            pass
        # space
        if input[ii] == " ":
            output += "  "
        # punctuation
        elif input[ii] == ".":
            output += "    "
        elif input[ii] == "?":
            output += ":question:"
        elif input[ii] == "!":
            output += ":exclamation:"
            # standard letter
        elif isNum == 0:
            output += ""
            output += block
            output += input[ii]
            output += ":\u200A"

    return output

def superscript(text):
    text = text.replace('a','ᵃ')
    text = text.replace('b','ᵇ')
    text = text.replace('c','ᶜ')
    text = text.replace('d','ᵈ')
    text = text.replace('e','ᵉ')
    text = text.replace('f','ᶠ')
    text = text.replace('g','ᵍ')
    text = text.replace('h','ʰ')
    text = text.replace('i','ᶦ')
    text = text.replace('j','ʲ')
    text = text.replace('k','ᵏ')
    text = text.replace('l','ˡ')
    text = text.replace('m','ᵐ')
    text = text.replace('n','ⁿ')
    text = text.replace('o','ᵒ')
    text = text.replace('p','ᵖ')
    text = text.replace('q','ᵠ')
    text = text.replace('r','ʳ')
    text = text.replace('s','ˢ')
    text = text.replace('t','ᵗ')
    text = text.replace('u','ᵘ')
    text = text.replace('v','ᵛ')
    text = text.replace('w','ʷ')
    text = text.replace('x','ˣ')
    text = text.replace('y','ʸ')
    text = text.replace('z','ᶻ')
    text = text.replace('A','ᴬ')
    text = text.replace('B','ᴮ')
    text = text.replace('C','ᶜ')
    text = text.replace('D','ᴰ')
    text = text.replace('E','ᴱ')
    text = text.replace('F','ᶠ')
    text = text.replace('G','ᴳ')
    text = text.replace('H','ᴴ')
    text = text.replace('I','ᴵ')
    text = text.replace('J','ᴶ')
    text = text.replace('K','ᴷ')
    text = text.replace('L','ᴸ')
    text = text.replace('M','ᴹ')
    text = text.replace('N','ᴺ')
    text = text.replace('O','ᴼ')
    text = text.replace('P','ᴾ')
    text = text.replace('Q','ᵠ')
    text = text.replace('R','ᴿ')
    text = text.replace('S','ˢ')
    text = text.replace('T','ᵀ')
    text = text.replace('U','ᵁ')
    text = text.replace('V','ⱽ')
    text = text.replace('W','ᵂ')
    text = text.replace('X','ˣ')
    text = text.replace('Y','ʸ')
    text = text.replace('Z','ᶻ')
    text = text.replace('1','¹')
    text = text.replace('2','²')
    text = text.replace('3','³')
    text = text.replace('4','⁴')
    text = text.replace('5','⁵')
    text = text.replace('6','⁶')
    text = text.replace('7','⁷')
    text = text.replace('8','⁸')
    text = text.replace('9','⁹')
    text = text.replace('0','⁰')
    text = text.replace('-','⁻')
    text = text.replace('=','⁼')
    text = text.replace('+','⁺')
    text = text.replace('?','ˀ')
    text = text.replace('!','ᵎ')
    text = text.replace('.','·')
    return text

def swap(text,char1,char2):
    text = text.replace(char1,'$$$$$')
    text = text.replace(char2,char1)
    text = text.replace('$$$$$',char2)
    return text

def upsidedown(text):
    text = swap(text,'a','ɐ')
    text = swap(text,'b','q')
    text = swap(text,'c','ɔ')
    text = swap(text,'d','p')
    text = swap(text,'e','ǝ')
    text = swap(text,'f','ɟ')
    text = swap(text,'g','ƃ')
    text = swap(text,'h','ɥ')
    text = swap(text,'i','ᴉ')
    text = swap(text,'j','ɾ')
    text = swap(text,'k','ʞ')
    text = swap(text,'l','l')
    text = swap(text,'m','ɯ')
    text = swap(text,'n','u')
    text = swap(text,'o','o')
    # text = swap(text,'p','d')
    # text = swap(text,'q','b')
    text = swap(text,'r','ɹ')
    text = swap(text,'s','s')
    text = swap(text,'t','ʇ')
    # text = swap(text,'u','n')
    text = swap(text,'v','ʌ')
    text = swap(text,'w','ʍ')
    text = swap(text,'x','x')
    text = swap(text,'y','ʎ')
    text = swap(text,'z','z')
    text = swap(text,'A','∀')
    text = swap(text,'B','𐐒')
    text = swap(text,'C','Ɔ')
    text = swap(text,'D','◖')
    text = swap(text,'E','Ǝ')
    text = swap(text,'F','Ⅎ')
    text = swap(text,'G','פ')
    text = swap(text,'H','H')
    text = swap(text,'I','I')
    text = swap(text,'J','ſ')
    text = swap(text,'K','ꓘ')
    text = swap(text,'L','˥')
    text = swap(text,'M','W')
    text = swap(text,'N','N')
    text = swap(text,'O','O')
    text = swap(text,'P','Ԁ')
    text = swap(text,'Q','Ό')
    text = swap(text,'R','ᴚ')
    text = swap(text,'S','S')
    text = swap(text,'T','┴')
    text = swap(text,'U','∩')
    text = swap(text,'V','Λ')
    # text = swap(text,'W','M')
    text = swap(text,'X','X')
    text = swap(text,'Y','⅄')
    text = swap(text,'Z','Z')
    text = swap(text,'.','˙')
    text = swap(text,',','\'')
    text = swap(text,';','؛')
    text = swap(text,'"','„')
    text = swap(text,'_','‾')
    text = swap(text,'<','>')
    text = swap(text,'(',')')
    text = swap(text,'{','}')
    text = swap(text,'[',']')
    text = swap(text,'\\','/')
    text = swap(text,'!','¡')
    text = swap(text,'?','¿')
    text = swap(text,'&','⅋')
    text = swap(text,'_','‾')
    text = swap(text,'0','0')
    text = swap(text,'1','Ɩ')
    text = swap(text,'2','ᄅ')
    text = swap(text,'3','Ɛ')
    text = swap(text,'4','ᔭ')
    text = swap(text,'5','ϛ')
    text = swap(text,'6','9')
    text = swap(text,'7','ㄥ')
    text = swap(text,'8','8')
    # text = swap(text,'9','6')

    text = text[::-1]
    return text

def emojitime(emoji, location):
    # add space if regional indicator
    keep_space = False
    regs = ['🇦','🇧','🇨','🇩','🇪','🇫','🇬','🇭','🇮','🇯','🇰','🇱','🇲','🇳','🇴','🇵','🇶','🇷','🇸','🇹','🇺','🇻','🇼','🇽','🇾','🇿']
    for reg in regs:
        if reg in emoji:
            keep_space = True
            continue
    # get the time where they are
    loc = astronomy.where_are_you(location)
    now = astronomy.swaptz(datetime.utcnow(), loc.latitude, loc.longitude)
    hh = str(format(now.hour, '02d'))
    mm = str(format(now.minute, '02d'))
    time_string = '{}:{}'.format(hh,mm)
    # then the file of things...
    filename = c.clib_path_join('text', 'emojidigits.txt')
    with open(filename, encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    # remove space
    if keep_space is False:
        lines = [line.replace(' ','') for line in lines] # remove spaces
    lines = [line.replace('\n','') for line in lines] # remove newlines
    lines = [line.replace('e', emoji) for line in lines] # replace 'e' with emoji
    emoji_digits = []
    for char in time_string:
        try:
            digit = 5 * int(char)
        except ValueError:
            digit = 5 * 10
        emoji_digits.append(lines[digit:digit+5])
    # reshape list of strings
    emoji_digits_reshape = ['\u200B\n']
    for i in range(0,5):
        line = []
        for digit in emoji_digits:
            line.append(digit[i])
        line = '   '.join(line)
        emoji_digits_reshape.append(line)
    return '\u2005\n'.join(emoji_digits_reshape)

['\u200b\n\n<a:kisslemon:554601640758476801><a:kisslemon:554601640758476801><a:kisslemon:554601640758476801>   <a:kisslemon:554601640758476801><a:kisslemon:554601640758476801><a:kisslemon:554601640758476801>   <:blank:589560784485613570>   <a:kisslemon:554601640758476801><a:kisslemon:554601640758476801><a:kisslemon:554601640758476801>   <a:kisslemon:554601640758476801><a:kisslemon:554601640758476801><a:kisslemon:554601640758476801>\n<:blank:589560784485613570><:blank:589560784485613570><a:kisslemon:554601640758476801>   <:blank:589560784485613570><:blank:589560784485613570><a:kisslemon:554601640758476801>   �🔴   <:blank:589560784485613570><:blank:589560784485613570><a:kisslemon:554601640758476801>   <:blank:589560784485613570><:blank:589560784485613570><a:kisslemon:554601640758476801>\n<a:kisslemon:554601640758476801><a:kisslemon:5546016458476801><a:kisslemon:554601640758476801>   <a:kisslemon:554601640758476801><a:kisslemon:554601640758476801><a:kisslemon:554601640758476801>   <:blank:589560784485613570>   <a:kisslemon:554601640758476801><a:kisslemon:554601640758476801><a:kisslemon:554601640758476801>   <a:kisslemon:554601640758476801><a:kisslemon:554601640758476801><a:kisslemon:554601640758476801>\n<a:kisslemon:554601640758476801><:blank:589560784485613570><:blank:589560784485613570>   <:blank:589560784485613570><:blank:589560784485613570><a:kisslemon:554601640758476801>   �🔴   <:blank:5895684485613570><:blank:589560784485613570><a:kisslemon:554601640758476801>   <a:kisslemon:554601640758476801><:blank:589560784485613570><:blank:589560784485613570>\n<a:kisslemon:554601640758476801><a:kisslemon:554601640758476801><a:kisslemon:554601640758476801>   <a:kisslemon:554601640758476801><a:kisslemon:554601640758476801><a:kisslemon:554601640758476801>   <:blank:589560784485613570>   <a:kisslemon:554601640758476801><a:kisslemon:554601640758476801><a:kisslemon:554601640758476801>   <a:kisslemon:554601640758476801><a:kisslemon:554601640758476801><a:kisslemon:554601640758476801>                                \u200b']