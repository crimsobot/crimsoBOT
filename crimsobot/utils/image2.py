import os
from io import BytesIO
from typing import List, Optional, Tuple

import aiofiles
import aiohttp
import matplotlib.image as plt
import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageOps
from PIL import ImageSequence
from discord.ext.commands import BadArgument, Context
from scipy.signal import convolve2d

from crimsobot.data.img import color_dict, lookup_emoji, rgb_color_list
from crimsobot.utils import tools as c
from crimsobot.utils.color import hex_to_rgb


def gif_frame_transparency(img: Image.Image) -> Image.Image:
    # get alpha mask
    alpha = img.convert('RGBA').split()[-1]
    # convert back to P mode but only using 255 of available 256 colors
    img = img.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
    # set all pixel values below 128 to 255 and the rest to 0
    mask = Image.eval(alpha, lambda a: 255 if a <= 88 else 0)
    # paste the color of index 255 and use alpha as a mask
    img.paste(255, mask.convert('L'))  # the transparency index is now 255

    return img


def image_to_buffer(list_im: List[Image.Image], durations: Optional[Tuple[int, ...]] = None) -> BytesIO:
    fp = BytesIO()

    if not durations:
        list_im[0].save(fp, 'PNG')
    else:
        giffed_frames = []
        for frame in list_im:
            new_frame = gif_frame_transparency(frame)
            giffed_frames.append(new_frame)
        giffed_frames[0].save(fp, format='GIF', transparency=255, append_images=giffed_frames[1:],
                              save_all=True, duration=durations, loop=0, disposal=2)

    fp.seek(0)
    return fp


def remove_unicode_prefix(word: str) -> str:
    word_with_prefix = word.encode('unicode-escape').decode('utf-8', 'strict')

    if r'\U' in word_with_prefix:
        return word_with_prefix.split('\\U')[1]
    if r'\u' in word_with_prefix:
        return word_with_prefix.split('\\u')[1]
    if r'\x' in word_with_prefix:
        return word_with_prefix.split('\\x')[1]

    return word


def bigmoji(emoji: str) -> Tuple[Optional[str], Optional[str]]:
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

        path = c.clib_path_join('emoji', filename + '.png')
        emoji_type = 'file'

        # Some "old" emojis (pre Emoji v1.0) have the variation indicator '-fe0f' in their Unicode sequence.
        # Well, Discord seems to think so. Twemoji thinks otherwise. So this handles that disagreement.
        if not os.path.exists(path):
            if filename.endswith('-fe0f'):
                filename = filename.replace('-fe0f', '')
            path = c.clib_path_join('emoji', filename + '.png')

    return path, emoji_type


async def fetch_image(ctx: Context, arg: Optional[str]) -> Image.Image:
    """Determine type of input, return image file."""

    session = aiohttp.ClientSession()

    async def open_img_from_url(url: str) -> Image.Image:
        async with session.get(url, allow_redirects=False) as response:
            img_bytes = await response.read()

        return Image.open(BytesIO(img_bytes))

    img = None

    if ctx.message.attachments:
        # get an attachment
        link = ctx.message.attachments[0].url
        img = await open_img_from_url(link)
    elif ctx.message.mentions:
        # get mentioned user's avatar
        link = str(ctx.message.mentions[0].avatar_url)
        img = await open_img_from_url(link)
    elif arg:
        try:
            if arg:
                img = await open_img_from_url(arg)
        except Exception:
            # if not an image url, it's probably an emoji
            big_emoji, emoji_type = bigmoji(arg)
            if big_emoji is None:
                pass
            elif emoji_type == 'file':
                async with aiofiles.open(big_emoji, 'rb') as f:
                    img_bytes = await f.read()
                img = Image.open(BytesIO(img_bytes))
            elif emoji_type == 'url':
                img = await open_img_from_url(big_emoji)

    if not img:
        img = Image.new('RGB', (0, 0), (0, 0, 0))

    await session.close()

    return img


def make_color_img(hex_str: str) -> BytesIO:
    """Generate image given a hex value."""

    if hex_str.startswith('#'):
        color = hex_to_rgb(hex_str[1:])
    else:
        color = hex_to_rgb(hex_str)

    img = Image.new('RGB', (300, 100), color)

    fp = image_to_buffer(img)
    return fp


def boop(the_booper: str, the_booped: str) -> BytesIO:
    # font selection
    f = ImageFont.truetype(c.clib_path_join('img', 'Roboto-BlackItalic.ttf'), 36)

    # add line breaks if needed to inputs
    def add_line_breaks(text: str) -> str:
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

    return image_to_buffer(img)


async def fishe(img: Image.Image, arg: None) -> Image.Image:
    img = img.convert('RGBA')
    img = img.resize((71, 105), resample=Image.BICUBIC)

    base = Image.open(c.clib_path_join('img', 'fishe_on_head.png'))
    base.paste(img, (7, 4))

    return base


async def xok(img: Image.Image, arg: None) -> Image.Image:
    img = img.convert('RGBA')

    width, height = img.size
    ratio = width / 120
    img = img.resize((int(width / ratio), int(height / ratio)), resample=Image.BICUBIC)

    width, height = img.size
    base = Image.open(c.clib_path_join('img', 'xokked_base.png'))
    base.paste(img, (30, 118 - int(height / 2)))

    return base


async def ban_overlay(img: Image.Image, arg: None) -> Image.Image:
    img = img.convert('RGBA')

    width, height = img.size
    if max(width, height) > 500:
        ratio = max(width, height) / 500
        img = img.resize((int(width / ratio), int(height / ratio)), resample=Image.BICUBIC)

    width, height = img.size
    ban = Image.open(c.clib_path_join('img', 'ban.png'))
    ban = ban.resize((width, height), resample=Image.BICUBIC)

    img.paste(ban, (0, 0), ban)

    return img


async def pingbadge(img: Image.Image, position: int) -> Image.Image:
    # resize input image
    img = img.convert('RGBA')

    width, height = img.size
    if max(width, height) > 500:
        ratio = max(width, height) / 500
        img = img.resize((int(width / ratio), int(height / ratio)), resample=Image.BICUBIC)

    width, height = img.size
    size = int(width / 3)
    badge = Image.open(c.clib_path_join('img', 'roundping.png'))
    badge = badge.resize((size, size), resample=Image.BICUBIC)

    if position == 1:
        corner = (0, 0)
    elif position == 2:
        corner = (width - size, 0)
    elif position == 3:
        corner = (0, height - size)
    elif position == 4:
        corner = (width - size, height - size)
    else:
        raise BadArgument('Invalid position.')

    img.paste(badge, corner, badge)

    return img


async def lateralus_cover(img: Image.Image, arg: None) -> Image.Image:
    img = img.convert('RGBA')

    # 1. determine user image size, resize to fit in its place
    width, height = img.size
    ratio = width / 333
    img = img.resize((int(width / ratio), int(height / ratio)), resample=Image.BICUBIC)
    # get new size
    width, height = img.size

    # 2. paste into cover back (462 x 462 pixels)
    back = Image.open(c.clib_path_join('img', 'lateralus_back.png'))
    back.paste(img, (65, 129), img)

    # 3. paste wordmark over result
    wordmark = Image.open(c.clib_path_join('img', 'lateralus_wordmark.png'))
    back.paste(wordmark, (0, 0), wordmark)
    back.save('back.png')
    return back


async def aenima_cover(img: Image.Image, arg: None) -> Image.Image:
    # 1. determine user image size, resize to fit in its place
    width, height = img.size
    ratio = width / 180
    img = img.resize((int(width / ratio), int(height / ratio)), resample=Image.BICUBIC)
    # get new size
    width, height = img.size

    # 2. paste over white bg
    bg = Image.new('RGBA', (500, 500), (255, 255, 255, 255))
    position = int(250 - height/2)
    bg.paste(img, (163, position), img)

    # 3. paste cover over result
    cover = Image.open(c.clib_path_join('img', 'aenima_cover.png'))
    bg.alpha_composite(cover, (0, 0))

    return bg


def quantizetopalette(silf: Image, palette: Image) -> Image.Image:
    """Convert an RGB or L mode image to use a given P image's palette."""

    silf.load()
    palette.load()  # use palette from reference image made below
    im = silf.im.convert('P', 0, palette.im)  # 0 = dithering OFF

    return silf._new(im)


async def make_emoji_image(ctx: Context, user_input: Optional[str]) -> List[str]:
    """Make image from emojis!"""

    # get image
    input_image = await fetch_image(ctx, user_input)
    input_image = input_image.convert('RGB')

    # Nyquist sampling apply here? just to be safe
    n = len(color_dict) * 2
    # quantize while still large (because i am paranoid about alising)
    input_image = input_image.quantize(colors=n, method=1, kmeans=n)

    # check that image is not too tall, then resize
    width, height = input_image.size
    ratio = height / width
    if ratio > 3:
        # return a list of string(s) to remain consistent
        return ['Image is too long!']
    input_image = input_image.resize((36, int(36 * ratio)), resample=Image.BICUBIC)

    # first: quantize to palette (has to be RGB mode for that)
    palette = Image.new('P', (1, 1))
    palette.putpalette([i for sub in rgb_color_list for i in sub])
    input_image = input_image.convert('RGB', dither=0)
    input_image_p = input_image.quantize(palette=palette, dither=0)

    # create dict to match palette number with actual color (for later step)
    # keys = palette integers; values = RGB tuples
    color_list = input_image_p.getcolors()
    color_list_p = sorted(color_list, key=lambda tup: tup[0], reverse=True)
    color_keys = []
    for color in color_list_p:
        color_keys.append(color[1])

    # now for the value tuples
    input_image_rgb = input_image_p.convert('RGB')
    color_list = input_image_rgb.getcolors()
    color_list_rgb = sorted(color_list, key=lambda tup: tup[0], reverse=True)
    color_values = []
    for color in color_list_rgb:
        color_values.append(color[1])

    # and finally, the dict
    image_dict = dict(zip(color_keys, color_values))

    # numpy image is array of the "palette keys" as strings
    numpy_image = np.array(input_image_p, dtype=str)

    # lookup emoji once per color, then replace in image array
    for key, value in image_dict.items():
        # convert key to hex format (string) for lookup_emoji()
        hex_color = '%02x%02x%02x' % value
        emoji = lookup_emoji(hex_color)
        # replace all instances in the numpy image
        numpy_image[numpy_image == str(key)] = [emoji]

    # numpy_image now needs to be "stringed" out, row by row
    string_list = []
    for row in numpy_image:
        string_list.append(''.join(row))

    return string_list


def make_mosaic(colors: List[int]) -> BytesIO:
    """Make a mosaic!"""
    # first, some stuff
    width = 50
    height = 100

    # generate tile for each passed color
    tiles = []
    for color in colors:
        tile = Image.new('RGB', (width, height), color)
        tiles.append(tile)

    rows = 1
    columns = len(colors)

    # creates a new empty image, RGB mode
    mosaic = Image.new('RGB', (int(columns * width), int(rows * height)))

    k = 0
    for j in range(0, rows * height, height):
        for i in range(0, columns * width, width):
            mosaic.paste(tiles[k], (i, j))
            k = k + 1

    return image_to_buffer(mosaic)


async def get_image_palette(ctx: Context, n: int, user_input: Optional[str]) -> Tuple[str, BytesIO, BytesIO]:
    """Get colors of image palette!"""

    # get image from url
    img = await fetch_image(ctx, user_input)
    img = img.convert('RGBA')

    width, height = img.size
    if max(width, height) > 800:
        ratio = max(width, height) / 800
        img = img.resize((int(width / ratio), int(height / ratio)),
                         resample=Image.BICUBIC)

    # change transparent BG to white, bc I don't know why
    background = Image.new('RGB', img.size, (255, 255, 255))
    background.paste(img, mask=img.split()[3])  # 3 is the alpha channel

    img = background.quantize(colors=n, method=1, kmeans=n)
    resample = image_to_buffer(img)

    img_colors = img.convert('RGB').getcolors()
    img_colors = sorted(img_colors, key=lambda tup: tup[0], reverse=True)
    colors = []
    hex_colors = []
    for ii in range(0, len(img_colors)):
        colors.append(img_colors[ii][1])
        hex_colors.append('#%02x%02x%02x' % img_colors[ii][1])

    # call the mosaic maker!
    mosaic = make_mosaic(colors)

    return ' '.join(hex_colors), mosaic, resample


async def acid(img: Image.Image, window: int) -> Image.Image:
    # get image size, resize if too big
    width, height = img.size
    if max(width, height) > 500:
        ratio = max(width, height) / 500
        img = img.resize((int(width / ratio), int(height / ratio)), resample=Image.BICUBIC)

    # alpha mask (for later)
    alpha = img.convert('RGBA').split()[-1]
    img = img.convert('RGB')

    # open as raster
    raster = plt.pil_to_array(img)

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
    acid_raster_fp = BytesIO()
    plt.imsave(acid_raster_fp, acid_raster)
    acid_raster_fp.seek(0)

    # open as PIL image to apply alpha mask
    img = Image.open(acid_raster_fp)
    img.putalpha(alpha)

    return img


async def process_image(ctx: Context, image: Optional[str], effect: str, arg: Optional[int] = None
                        ) -> Optional[BytesIO]:
    # grab user image and covert to RGBA
    img = await fetch_image(ctx, image)

    # if too many frames, kick it out
    if (getattr(img, 'is_animated', False)) and img.n_frames > 50:
        await ctx.send('`Too many frames!`', delete_after=10)
        return None

    # this will only loop once for still images
    frame_list, durations = [], []
    for _ in ImageSequence.Iterator(img):
        # if not animated, will throw KeyError
        try:
            durations.append(img.info['duration'])
        except KeyError:
            # an empty tuple for durations tells image_to_buffer that image is still
            pass

        function_dict = {
            'fishe': fishe,
            'xok': xok,
            'ban': ban_overlay,
            'pingbadge': pingbadge,
            'lateralus': lateralus_cover,
            'aenima': aenima_cover,
            'acidify': acid,
        }

        # TODO: how do we type-hint function_dict properly?
        img_out = await function_dict[effect](img.convert('RGBA'), arg)  # type: ignore
        frame_list.append(img_out)

    fp = image_to_buffer(frame_list, tuple(durations))
    return fp
