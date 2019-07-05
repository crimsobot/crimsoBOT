import discord
from discord.ext import commands
import PIL
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageOps
from PIL import ImageEnhance
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
import os
import requests
from io import BytesIO
import numpy as np
import matplotlib.pylab as plt
from scipy.signal import convolve2d

from . import crimsotools as c


def remove_U(word):
    word_U = (word.encode('unicode-escape')).decode('utf-8', 'strict')
    if r'\U' in word_U:
        return word_U.split('\\U')[1]
    if r'\u' in word_U:
        return word_U.split('\\u')[1]
    if r'\x' in word_U:
        return word_U.split('\\x')[1]
    return word

def bigmoji(emoji):
    # custom emojis <[a]:emoji_name:emoji_id>
    if emoji.startswith('<:') or emoji.startswith('<a:'):
        ind = emoji.find(':',3)
        emoji_id = emoji[ind+1:-1]
        if emoji.startswith('<:'):
            path = 'https://cdn.discordapp.com/emojis/'+emoji_id+'.png'
        else:
            path = 'https://cdn.discordapp.com/emojis/'+emoji_id+'.gif'
    # standard emojis
    else:
        list = []
        for i in range(len(emoji)):
            string = emoji[i].encode('unicode-escape') # example result: \U001f990
            list.append(remove_U(string.decode('utf-8')).lstrip('0')) # result: 1f990
        filename = '-'.join(list) 
        # exceptions
        if filename.endswith('20e3'):
            if filename.startswith('*'): # asterisk
                filename = '2a-20e3'
            elif filename.startswith('#'): # hash/pound sign
                filename = '23-20e3'
            else: # numbers zero-nine
                filename = '3'+filename
        path = c.clib_path_join('emoji', '')+filename+'.png'
    # test if real path
    # try:
    #     open(path, 'rb')
    # except OSError:
    #     try:
    #         response = requests.get(path)
    #     except:
    #         return False
    # except:
    #     return False
    return path

def imageFetch(ctx, arg):
    """Determine type of input, return image file."""
    try:
        response = requests.get(arg)
        img = Image.open(BytesIO(response.content))
    except:
        if arg is None: 
            # look for message attachment
            link = ctx.message.attachments[0]['url']
            response = requests.get(link)
            img = Image.open(BytesIO(response.content))
        elif (ctx.message.mentions.__len__()>0):
            # get mentioned user's avatar
            for user in ctx.message.mentions:
                link = user.avatar_url
            response = requests.get(link)
            img = Image.open(BytesIO(response.content))
        else:
            # if not one of the above cases, maybe it's an emoji?
            try:
                img = Image.open(bigmoji(arg))
            except:
                response = requests.get(bigmoji(arg))
                img = Image.open(BytesIO(response.content))
    return img

def hex_to_rgb(input):
    r = int(input[0:2],16); g = int(input[2:4],16); b = int(input[4:6],16)
    return r,g,b # tuple

def color(str):
    """Generate image given a hex value."""
    if str.startswith('#'):
        color = hex_to_rgb(str[1:])
    else:
        color = hex_to_rgb(str)
    img = Image.new('RGB', (300, 100), color)
    img.save(c.clib_path_join('img', 'color.jpg'))

def boop(the_booper,the_booped):
    # font selection
    f = ImageFont.truetype(c.clib_path_join('img', 'Roboto-Blackitalic.ttf'), 36)

    # add line breaks if needed to inputs
    def lineBreak(input):
        ind = 16
        """Add newlines (natrual if possible) to string."""
        if len(input) > ind-1:
            index = [i for i, ltr in enumerate(input) if ltr == ' ']
            if index == [] or max(index) < ind:
                index.append(ind)
        else:
            return input
        for ii in range(0,len(index)):
            if index[ii] >= ind:
                input = input[:index[ii-1]+1] + '\n' + input[index[ii-1]+1:]
                return input

    the_booper = lineBreak(the_booper)
    the_booped = lineBreak(the_booped)

    # open original image
    img = Image.open(c.clib_path_join('img', 'boop.jpg'))

    # temp image made to rotate 'the_booped" text'
    txt = Image.new('L', (500,100))
    d = ImageDraw.Draw(txt)
    draw = ImageDraw.Draw(img)
    d.text((0,0), the_booped, font=f, fill=255)
    w = txt.rotate(45, expand=1)

    # draw on original image
    draw.text((10, 450), the_booper, font=f, fill=(255,255,255))
    img.paste(ImageOps.colorize(w, (0,0,0), (255,255,255)), (370,0), w)
    img.save(c.clib_path_join('img', 'booped.jpg'))

def fishe(ctx, user_input):
    img = imageFetch(ctx, user_input)
    img = img.convert('RGBA')
    img = img.resize((71,105), resample=Image.BICUBIC)
    base = Image.open(c.clib_path_join('img', 'fishe_on_head.png'))
    base.paste(img, (7,4))
    base.save(c.clib_path_join('img', 'needping.png'))

def xok(ctx, user_input):
    img = imageFetch(ctx, user_input)
    img = img.convert('RGBA')
    width, height = img.size
    ratio = width / 120
    img = img.resize((int(width/ratio),int(height/ratio)), resample=Image.BICUBIC)
    width, height = img.size
    base = Image.open(c.clib_path_join('img', 'xokked_base.png'))
    base.paste(img, (30, 118-int(height/2)))
    filename = c.clib_path_join('img', 'get_xokked.png')
    base.save(filename)
    return filename

def ban_overlay(ctx, user_input):
    img = imageFetch(ctx, user_input)
    img = img.convert('RGBA')
    width, height = img.size
    if max(width, height) > 500:
        ratio = max(width,height) / 500
        img = img.resize((int(width/ratio),int(height/ratio)), resample=Image.BICUBIC)
    width, height = img.size
    ban = Image.open(c.clib_path_join('img', 'ban.png'))
    ban = ban.resize((width, height), resample=Image.BICUBIC)
    img.paste(ban, (0,0), ban)
    img.save(c.clib_path_join('img', 'needban.png'))

def pingbadge(ctx, user_input, pos):
    img = imageFetch(ctx, user_input)
    img = img.convert('RGBA')
    width, height = img.size
    if max(width, height) > 500:
        ratio = max(width,height) / 500
        img = img.resize((int(width/ratio),int(height/ratio)), resample=Image.BICUBIC)
    width, height = img.size
    size = int(width/3)
    badge = Image.open(c.clib_path_join('img', 'roundping.png'))
    badge = badge.resize((size, size), resample=Image.BICUBIC)
    if pos == '1':
        corner = (0, 0)
    elif pos == '2':
        corner = (width-size, 0)
    elif pos == '3':
        corner = (0, height-size)
    elif pos == '4':
        corner = (width-size, height-size)
    else:
        return False
    img.paste(badge, corner, badge)
    img.save(c.clib_path_join('img', 'pingbadge.png'))

### so begins EMOJI IMAGE
def hex_to_sRGB(base):
    # hex_in to tuple
    r_ = '0x'+base[0:2]; g_ = '0x'+base[2:4]; b_ = '0x'+base[4:6]
    r_ = int(r_,16)/255; g_ = int(g_,16)/255; b_ = int(b_,16)/255
    color_rgb = sRGBColor(r_,g_,b_)
    color = convert_color(color_rgb, LabColor)
    return color

# color lists
colorList = []
with open(c.clib_path_join('img', 'colors.txt'), 'r') as file:
    [colorList.append(line[0:6]) for line in file]

colorList_sRGB = []
[colorList_sRGB.append(hex_to_sRGB(color)) for color in colorList]

def quantizetopalette(silf, palette, dither=False):
    """Convert an RGB or L mode image to use a given P image's palette."""
    silf.load()
    palette.load() # use palette from reference image made below
    im = silf.im.convert('P', 0, palette.im) # 0 = dithering OFF
    return silf._new(im)

# these are needed to make the PIL palette list [r1, g1, b1, ..., rn, gn, bn]
rgb = []
[rgb.append(hex_to_rgb(color)) for color in colorList]

palettedata = [i for sub in rgb for i in sub] # list of tuples to list

def emojiLookup(hex_in):
    """search (bc quantizing palette not working)"""
    color_in = hex_to_sRGB(hex_in)
    nearest = min(colorList_sRGB, key=lambda fc:delta_e_cie2000(color_in, fc))
    nearest = convert_color(nearest, sRGBColor)
    nearest = nearest.get_rgb_hex()
    with open(c.clib_path_join('img', 'colors.txt'), 'r') as file:
        for line in file:
            if nearest[1:] in line:
                return line[7:-1]

def emojiImage(ctx, user_input):
    """Make image from emojis!"""
    # create palette image
    palimage = Image.new('P', (16, 16))
    palimage.putpalette(palettedata)
    # get image from url
    img = imageFetch(ctx, user_input)
    img = img.convert("RGB")
    converter = ImageEnhance.Color(img)
    img = converter.enhance(1.4)
    converter = ImageEnhance.Contrast(img)
    img = converter.enhance(1.2)
    # resize to be 36 emojis wide
    width, height = img.size
    ratio = height / width
    if ratio > 3:
        return False
    img = img.resize((36,int(36*ratio)),resample=Image.BICUBIC)
    # newimage is then quantized to palette
    newimage = quantizetopalette(img, palimage, dither=False)
    # find color of each pixel, turn into emoji in string
    rgb_im = newimage.convert('RGB',dither=None)
    newimage.save(c.clib_path_join('img', 'eimg.png'))
    x,y = newimage.size
    x,y = img.size
    f = open(c.clib_path_join('img', 'emoji.txt'), 'w', encoding='utf-8', \
             errors='ignore')
    for yy in range(0,y):
        msg_string = ''
        for xx in range(0,x):
            color = rgb_im.getpixel((xx,yy))
            color = '%02x%02x%02x' % color
            emoji = emojiLookup(color)
            msg_string = msg_string+emoji
        f.write(msg_string+'\n')
    f.close()

def emojiImage2(ctx, user_input):
    """Make image from emojis!"""
    # create palette image
    palimage = Image.new('P', (16, 16))
    palimage.putpalette(palettedata)
    # get image from url
    img = imageFetch(ctx, user_input)
    img = img.convert('RGBA')
    # Nyquist sampling apply here?
    n = 26*2
    img.load() # required for png.split()
    background = Image.new("RGB", img.size, (0, 0, 0))
    background.paste(img, mask=img.split()[3]) # 3 is the alpha channel
    img = background.quantize(colors=n, method=1, kmeans=n)
    width, height = img.size
    ratio = height / width
    if ratio > 3:
        return False
    img = img.resize((36,int(36*ratio)),resample=Image.BICUBIC)
    img.save(c.clib_path_join('img', 'eimg2.png'))
    img = img.convert('RGB',dither=None)
    x,y = img.size
    f = open(c.clib_path_join('img', 'emoji.txt'), 'w', encoding='utf-8', \
             errors='ignore')
    for yy in range(0,y):
        msg_string = ''
        for xx in range(0,x):
            color = img.getpixel((xx,yy))
            color = '%02x%02x%02x' % color
            emoji = emojiLookup(color)
            msg_string = msg_string+emoji
        f.write(msg_string+'\n')
    f.close()

def makeMosaic(colors):
    """Make a mosaic!"""
    # first, some stuff
    img_path = c.clib_path_join('img', 'mosaicTiles')
    width = 50
    height = 100
    
    # delete tiles
    for f in os.listdir(img_path):
        if f != '.gitignore':
            os.remove(os.path.join(img_path, f))

    # generate tile for each passed color
    counter = 1
    for color in colors:
        img = Image.new('RGB', (width, height), color)
        img.save(os.path.join(img_path, str('%02i' % counter) + '.jpg'))
        counter += 1

    img_list   = []
    img_text   = []
    rows       = 1
    columns    = len(colors)

    for file in os.listdir(img_path):
        if file.endswith('.jpg'):
            img_list.append(Image.open(img_path + file))

    #creates a new empty image, RGB mode
    mosaic = Image.new('RGB', (int(columns*width), int(rows*height)))

    k = 0
    for j in range(0, rows*height, height):
        for i in range( 0, columns*width, width):
            mosaic.paste(img_list[k], (i,j))
            k = k + 1

    mosaic.save(c.clib_path_join('img', 'mosaic.png'))

def imagePalette(ctx, n, user_input):
    """Get colors of image palette!"""
    # get image from url
    img = imageFetch(ctx, user_input)
    img = img.convert('RGBA')
    width, height = img.size
    if max(width, height) > 800:
        ratio = max(width,height) / 800
        img = img.resize((int(width/ratio),int(height/ratio)),
                         resample=Image.BICUBIC)
    img.save(c.clib_path_join('img', 'before.png'))
    # change transparent BG to white, bc I don't know why
    img.load() # required for png.split()
    background = Image.new("RGB", img.size, (255, 255, 255))
    background.paste(img, mask=img.split()[3]) # 3 is the alpha channel
    img = background.quantize(colors=n, method=1, kmeans=n)
    img.save(c.clib_path_join('img', 'resample.png'))
    list = img.convert('RGB').getcolors()
    list = sorted(list, key=lambda tup: tup[0],reverse=True)
    colors = []
    hex = []
    for ii in range(0,len(list)):
        colors.append(list[ii][1])
        hex.append('#%02x%02x%02x' % list[ii][1])
    # call the mosaic maker!
    makeMosaic(colors)
    return ' '.join(hex)

def acid(ctx, window, user_input):
    img = imageFetch(ctx, user_input)
    width, height = img.size
    if max(width, height) > 500:
        ratio = max(width,height) / 500
        img = img.resize((int(width/ratio),int(height/ratio)), resample=Image.BICUBIC)
    # alpha mask
    img2 = img.convert('RGBA')
    alpha = img2.split()[-1]
    img = img.convert('RGB')
    img.save(c.clib_path_join('img', 'acid_before.jpg'))
    # open as raster
    raster = plt.imread(c.clib_path_join('img', 'acid_before.jpg'))
    # create acidify kernel
    kernel = np.ones((window+1,window+1))
    kernel /= (window+1)
    # depth = number of channels
    _, _, depth = raster.shape
    acid_raster = []
    for channel in range(depth):
        acid_channel = convolve2d(raster[:,:,channel], kernel, mode='same', boundary='symm')
        acid_raster.append(acid_channel)
    acid_raster = np.stack(acid_raster, axis=2).astype('uint8')
    plt.imsave(c.clib_path_join('img', 'acid.png'), acid_raster)
    # open as PIL image to apply alpha mask
    img = Image.open(c.clib_path_join('img', 'acid.png'))
    img.putalpha(alpha)
    filename = c.clib_path_join('img', 'acid_.png')
    img.save(filename)
    return filename
    # acid = Image.open(c.clib_path_join('img', 'acid.jpg'))
    # acid = Image.blend(img,acid,0.618)
    # acid.save(c.clib_path_join('img', 'acid.png'))
