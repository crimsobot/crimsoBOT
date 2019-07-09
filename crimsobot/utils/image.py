import os
from io import BytesIO

import json
import matplotlib.pylab as plt
import numpy as np
import requests
from PIL import Image
from PIL import ImageDraw
from PIL import ImageEnhance
from PIL import ImageFont
from PIL import ImageOps
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import LabColor, sRGBColor
from scipy.signal import convolve2d

import crimsobot.utils.tools as c


def remove_unicode_prefix(word):
    word_with_prefix = word.encode('unicode-escape').decode('utf-8', 'strict')

    if r'\U' in word_with_prefix:
        return word_with_prefix.split('\\U')[1]
    if r'\u' in word_with_prefix:
        return word_with_prefix.split('\\u')[1]
    if r'\x' in word_with_prefix:
        return word_with_prefix.split('\\x')[1]

    return word


def bigmoji(emoji):
    # custom emojis <[a]:emoji_name:emoji_id>
    if emoji.startswith('<:') or emoji.startswith('<a:'):
        ind = emoji.find(':', 3)
        emoji_id = emoji[ind + 1:-1]
        if emoji.startswith('<:'):
            path = 'https://cdn.discordapp.com/emojis/' + emoji_id + '.png'
        else:
            path = 'https://cdn.discordapp.com/emojis/' + emoji_id + '.gif'
        emoji_type = 'url'

    # standard emojis
    else:
        characters = []
        for i in range(len(emoji)):
            string = emoji[i].encode('unicode-escape')  # example result: \U001f990
            characters.append(remove_unicode_prefix(string.decode('utf-8')).lstrip('0'))  # result: 1f990

        filename = '-'.join(characters)

        # exceptions
        if filename.endswith('20e3'):
            if filename.startswith('*'):  # asterisk
                filename = '2a-20e3'
            elif filename.startswith('#'):  # hash/pound sign
                filename = '23-20e3'
            else:  # numbers zero-nine
                filename = '3' + filename

        # test if real file
        try:
            path = c.clib_path_join('emoji', '') + filename + '.png'
            emoji_type = 'file'
            f = open(path, 'rb')
            f.close()
        except OSError:
            path = False
            emoji_type = False

    return path, emoji_type


def fetch_image(ctx, arg):
    """Determine type of input, return image file."""

    try:
        response = requests.get(arg)
        img = Image.open(BytesIO(response.content))
    except Exception:
        if arg is None:
            # look for message attachment
            link = ctx.message.attachments[0].url
            response = requests.get(link)
            img = Image.open(BytesIO(response.content))
        elif len(ctx.message.mentions) > 0:
            # get mentioned user's avatar
            for user in ctx.message.mentions:
                link = user.avatar_url
            response = requests.get(link)
            img = Image.open(BytesIO(response.content))
        else:
            # if not one of the above cases, maybe it's an emoji?
            try:
                big_emoji, _ = bigmoji(arg)
                img = Image.open(big_emoji)
            except IOError:
                big_emoji, _ = bigmoji(arg)
                response = requests.get(big_emoji)
                img = Image.open(BytesIO(response.content))

    return img


def hex_to_rgb(color):
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)

    return r, g, b


def make_color_img(hex_str):
    """Generate image given a hex value."""

    if hex_str.startswith('#'):
        color = hex_to_rgb(hex_str[1:])
    else:
        color = hex_to_rgb(hex_str)

    img = Image.new('RGB', (300, 100), color)
    img.save(c.clib_path_join('img', 'color.jpg'))


def boop(the_booper, the_booped):
    # font selection
    f = ImageFont.truetype(c.clib_path_join('img', 'Roboto-BlackItalic.ttf'), 36)

    # add line breaks if needed to inputs
    def add_line_breaks(text):
        """Add newlines (natural if possible) to string."""

        ind = 16
        if len(text) > ind - 1:
            index = [i for i, ltr in enumerate(text) if ltr == ' ']
            if index == [] or max(index) < ind:
                index.append(ind)
        else:
            return text

        for ii in range(0, len(index)):
            if index[ii] >= ind:
                text = text[:index[ii - 1] + 1] + '\n' + text[index[ii - 1] + 1:]
                return text

    the_booper = add_line_breaks(the_booper)
    the_booped = add_line_breaks(the_booped)

    # open original image
    img = Image.open(c.clib_path_join('img', 'boop.jpg'))

    # temp image made to rotate 'the_booped" text'
    txt = Image.new('L', (500, 100))
    d = ImageDraw.Draw(txt)
    draw = ImageDraw.Draw(img)
    d.text((0, 0), the_booped, font=f, fill=255)
    w = txt.rotate(45, expand=1)

    # draw on original image
    draw.text((10, 450), the_booper, font=f, fill=(255, 255, 255))
    img.paste(ImageOps.colorize(w, (0, 0, 0), (255, 255, 255)), (370, 0), w)
    img.save(c.clib_path_join('img', 'booped.jpg'))


def fishe(ctx, user_input):
    img = fetch_image(ctx, user_input)
    img = img.convert('RGBA')
    img = img.resize((71, 105), resample=Image.BICUBIC)

    base = Image.open(c.clib_path_join('img', 'fishe_on_head.png'))
    base.paste(img, (7, 4))
    base.save(c.clib_path_join('img', 'needping.png'))


def xok(ctx, user_input):
    img = fetch_image(ctx, user_input)
    img = img.convert('RGBA')

    width, height = img.size
    ratio = width / 120
    img = img.resize((int(width / ratio), int(height / ratio)), resample=Image.BICUBIC)

    width, height = img.size
    base = Image.open(c.clib_path_join('img', 'xokked_base.png'))
    base.paste(img, (30, 118 - int(height / 2)))

    filename = c.clib_path_join('img', 'get_xokked.png')
    base.save(filename)

    return filename


def ban_overlay(ctx, user_input):
    img = fetch_image(ctx, user_input)
    img = img.convert('RGBA')

    width, height = img.size
    if max(width, height) > 500:
        ratio = max(width, height) / 500
        img = img.resize((int(width / ratio), int(height / ratio)), resample=Image.BICUBIC)

    width, height = img.size
    ban = Image.open(c.clib_path_join('img', 'ban.png'))
    ban = ban.resize((width, height), resample=Image.BICUBIC)

    img.paste(ban, (0, 0), ban)
    img.save(c.clib_path_join('img', 'needban.png'))


def pingbadge(ctx, user_input, pos):
    img = fetch_image(ctx, user_input)
    img = img.convert('RGBA')

    width, height = img.size
    if max(width, height) > 500:
        ratio = max(width, height) / 500
        img = img.resize((int(width / ratio), int(height / ratio)), resample=Image.BICUBIC)

    width, height = img.size
    size = int(width / 3)
    badge = Image.open(c.clib_path_join('img', 'roundping.png'))
    badge = badge.resize((size, size), resample=Image.BICUBIC)

    if pos == '1':
        corner = (0, 0)
    elif pos == '2':
        corner = (width - size, 0)
    elif pos == '3':
        corner = (0, height - size)
    elif pos == '4':
        corner = (width - size, height - size)
    else:
        return False

    img.paste(badge, corner, badge)
    img.save(c.clib_path_join('img', 'pingbadge.png'))


# so begins EMOJI IMAGE
def hex_to_srgb(base):
    # hex_in to tuple
    r_ = '0x' + base[0:2]
    g_ = '0x' + base[2:4]
    b_ = '0x' + base[4:6]
    r_ = int(r_, 16) / 255
    g_ = int(g_, 16) / 255
    b_ = int(b_, 16) / 255

    color_rgb = sRGBColor(r_, g_, b_)
    color = convert_color(color_rgb, LabColor)

    return color


# color lists
color_list = []
with open(c.clib_path_join('img', 'colors.txt'), 'r') as file:
    [color_list.append(line[0:6]) for line in file]

srgb_color_list = []
[srgb_color_list.append(hex_to_srgb(color)) for color in color_list]


def quantizetopalette(silf, palette, dither=False):
    """Convert an RGB or L mode image to use a given P image's palette."""

    silf.load()
    palette.load()  # use palette from reference image made below
    im = silf.im.convert('P', 0, palette.im)  # 0 = dithering OFF

    return silf._new(im)


# these are needed to make the PIL palette list [r1, g1, b1, ..., rn, gn, bn]
rgb = []
[rgb.append(hex_to_rgb(color)) for color in color_list]

palettedata = [i for sub in rgb for i in sub]  # list of tuples to list


# this is the list of colors and the emojis to which they correspond
with open(c.clib_path_join('img', 'colors.json'), 'r') as file:
    color_dict = json.loads(file.read())


def lookup_emoji(hex_in):
    """search (bc quantizing palette not working)"""

    color_in = hex_to_srgb(hex_in)
    nearest = min(srgb_color_list, key=lambda fc: delta_e_cie2000(color_in, fc))
    nearest = convert_color(nearest, sRGBColor)
    nearest = nearest.get_rgb_hex()

    for key, value in color_dict.items():
        if nearest == key:
            return value


def make_emoji_image(ctx, user_input):
    """Make image from emojis!"""

    # create palette image
    palimage = Image.new('P', (16, 16))
    palimage.putpalette(palettedata)

    # get image from url
    img = fetch_image(ctx, user_input)
    img = img.convert('RGB')
    converter = ImageEnhance.Color(img)
    img = converter.enhance(1.4)
    converter = ImageEnhance.Contrast(img)
    img = converter.enhance(1.2)

    # resize to be 36 emojis wide
    width, height = img.size
    ratio = height / width
    if ratio > 3:
        return False
    img = img.resize((36, int(36 * ratio)), resample=Image.BICUBIC)

    # newimage is then quantized to palette
    newimage = quantizetopalette(img, palimage, dither=False)

    # find color of each pixel, turn into emoji in string
    rgb_im = newimage.convert('RGB', dither=None)
    newimage.save(c.clib_path_join('img', 'eimg.png'))

    f = open(c.clib_path_join('img', 'emoji.txt'), 'w', encoding='utf-8',
             errors='ignore')

    x, y = img.size
    for yy in range(0, y):
        msg_string = ''
        for xx in range(0, x):
            color = rgb_im.getpixel((xx, yy))
            color = '%02x%02x%02x' % color
            emoji = lookup_emoji(color)
            msg_string = msg_string + emoji

        f.write(msg_string + '\n')

    f.close()


def make_emoji_image_v2(ctx, user_input):
    """Make image from emojis!"""

    # create palette image
    palimage = Image.new('P', (16, 16))
    palimage.putpalette(palettedata)

    # get image from url
    img = fetch_image(ctx, user_input)
    img = img.convert('RGBA')

    # Nyquist sampling apply here?
    n = 26 * 2
    img.load()  # required for png.split()

    background = Image.new('RGB', img.size, (0, 0, 0))
    background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
    img = background.quantize(colors=n, method=1, kmeans=n)

    width, height = img.size
    ratio = height / width
    if ratio > 3:
        return False
    img = img.resize((36, int(36 * ratio)), resample=Image.BICUBIC)
    img.save(c.clib_path_join('img', 'eimg2.png'))
    img = img.convert('RGB', dither=None)

    f = open(c.clib_path_join('img', 'emoji.txt'), 'w', encoding='utf-8',
             errors='ignore')

    x, y = img.size
    for yy in range(0, y):
        msg_string = ''
        for xx in range(0, x):
            color = img.getpixel((xx, yy))
            color = '%02x%02x%02x' % color
            emoji = lookup_emoji(color)
            msg_string = msg_string + emoji

        f.write(msg_string + '\n')

    f.close()


def make_mosaic(colors):
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

    img_list = []
    rows = 1
    columns = len(colors)

    for file in os.listdir(img_path):
        if file.endswith('.jpg'):
            img_list.append(Image.open(os.path.join(img_path, file)))

    # creates a new empty image, RGB mode
    mosaic = Image.new('RGB', (int(columns * width), int(rows * height)))

    k = 0
    for j in range(0, rows * height, height):
        for i in range(0, columns * width, width):
            mosaic.paste(img_list[k], (i, j))
            k = k + 1

    mosaic.save(c.clib_path_join('img', 'mosaic.png'))


def get_image_palette(ctx, n, user_input):
    """Get colors of image palette!"""

    # get image from url
    img = fetch_image(ctx, user_input)
    img = img.convert('RGBA')

    width, height = img.size
    if max(width, height) > 800:
        ratio = max(width, height) / 800
        img = img.resize((int(width / ratio), int(height / ratio)),
                         resample=Image.BICUBIC)
    img.save(c.clib_path_join('img', 'before.png'))

    # change transparent BG to white, bc I don't know why
    img.load()  # required for png.split()

    background = Image.new('RGB', img.size, (255, 255, 255))
    background.paste(img, mask=img.split()[3])  # 3 is the alpha channel

    img = background.quantize(colors=n, method=1, kmeans=n)
    img.save(c.clib_path_join('img', 'resample.png'))

    img_colors = img.convert('RGB').getcolors()
    img_colors = sorted(img_colors, key=lambda tup: tup[0], reverse=True)
    colors = []
    hex_colors = []
    for ii in range(0, len(img_colors)):
        colors.append(img_colors[ii][1])
        hex_colors.append('#%02x%02x%02x' % img_colors[ii][1])

    # call the mosaic maker!
    make_mosaic(colors)

    return ' '.join(hex_colors)


def acid(ctx, window, user_input):
    img = fetch_image(ctx, user_input)

    width, height = img.size
    if max(width, height) > 500:
        ratio = max(width, height) / 500
        img = img.resize((int(width / ratio), int(height / ratio)), resample=Image.BICUBIC)

    # alpha mask
    img2 = img.convert('RGBA')
    alpha = img2.split()[-1]
    img = img.convert('RGB')
    img.save(c.clib_path_join('img', 'acid_before.jpg'))

    # open as raster
    raster = plt.imread(c.clib_path_join('img', 'acid_before.jpg'))

    # create acidify kernel
    kernel = np.ones((window + 1, window + 1))
    kernel /= (window + 1)

    # depth = number of channels
    _, _, depth = raster.shape
    acid_raster = []
    for channel in range(depth):
        acid_channel = convolve2d(raster[:, :, channel], kernel, mode='same', boundary='symm')
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
