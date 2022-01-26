import os
from io import BytesIO
from typing import Any, Callable, List, Mapping, Optional, Tuple

import aiofiles
import aiohttp
import matplotlib.image as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageSequence
from bs4 import BeautifulSoup
from discord.ext.commands import BadArgument, Context
from scipy.signal import convolve2d

from crimsobot.data.img import (CAPTION_RULES, EIMG_WIDTH, GIF_RULES, IMAGE_RULES,
                                color_dict, lookup_emoji, rgb_color_list)
from crimsobot.utils import games as crimsogames, tools as c
from crimsobot.utils.color import hex_to_rgb


def gif_frame_transparency(img: Image.Image) -> Image.Image:
    # get alpha mask
    alpha = img.convert('RGBA').split()[-1]
    # convert back to P mode but only using 255 of available 256 colors
    img = img.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
    # set all pixel values in alpha below threshhold to 255 and the rest to 0
    mask = Image.eval(alpha, lambda a: 255 if a <= 88 else 0)
    # paste the color of index 255 and use alpha as a mask
    img.paste(255, mask)  # the transparency index will later be set to 255

    return img


def image_to_buffer(image_list: List[Image.Image], durations: Optional[Tuple[int, ...]] = None,
                    loops: Optional[bool] = None) -> BytesIO:
    fp = BytesIO()

    if not durations:
        image_list[0].save(fp, 'PNG')
    else:
        giffed_frames = []
        for frame in image_list:
            new_frame = gif_frame_transparency(frame)
            giffed_frames.append(new_frame)
        if loops:
            giffed_frames[0].save(fp, format='GIF', transparency=255, append_images=giffed_frames[1:],
                                  save_all=True, duration=durations, loop=0, disposal=2)
        else:
            giffed_frames[0].save(fp, format='GIF', transparency=255, append_images=giffed_frames[1:],
                                  save_all=True, duration=durations, disposal=2)

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


def find_emoji_img(emoji: str) -> Tuple[Optional[str], Optional[str]]:
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
        if 'tenor.com/view' in url:
            async with session.get(url, allow_redirects=False) as response:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                original = soup.find(property='og:image')  # the original GIF has this property in its meta tag
                url = original['content']

        async with session.get(url, allow_redirects=False) as response:
            img_bytes = await response.read()

        await session.close()

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
            big_emoji, emoji_type = find_emoji_img(arg)
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

    fp = image_to_buffer([img])
    return fp


async def make_boop_img(the_booper: str, the_booped: str) -> BytesIO:
    # font selection
    filename = c.clib_path_join('img', 'Roboto-BlackItalic.ttf')
    async with aiofiles.open(filename, 'rb') as f:
        font_bytes = await f.read()
    font = ImageFont.truetype(BytesIO(font_bytes), 36)

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
    filename = c.clib_path_join('img', 'boop.jpg')
    async with aiofiles.open(filename, 'rb') as f:
        img_bytes = await f.read()
    img = Image.open(BytesIO(img_bytes))

    # temp image made to rotate 'the_booped" text'
    txt = Image.new('L', (500, 100))
    d = ImageDraw.Draw(txt)
    draw = ImageDraw.Draw(img)
    d.text((0, 0), the_booped, font=font, fill=255)
    w = txt.rotate(45, expand=1)

    # draw on original image
    draw.text((10, 450), the_booper, font=font, fill=(255, 255, 255))
    img.paste(ImageOps.colorize(w, (0, 0, 0), (255, 255, 255)), (370, 0), w)

    fp = image_to_buffer([img])

    return fp


async def make_emoji_image(ctx: Context, user_input: Optional[str], platform: str) -> List[str]:
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

    final_width = EIMG_WIDTH[platform]
    input_image = input_image.resize((final_width, int(final_width * ratio)), resample=Image.BICUBIC)

    # first: quantize to palette (has to be RGB mode for that)
    palette = Image.new('P', (1, 1))
    palette.putpalette([i for sub in rgb_color_list for i in sub])
    input_image = input_image.convert('RGB', dither=0)
    input_image_p = input_image.quantize(palette=palette, dither=0)

    # create dict to match palette number with actual color (for later step)
    # keys = palette integers; values = RGB tuples
    color_list_p = input_image_p.getcolors()  # type: List[Tuple[int, int]]
    color_list_p = sorted(color_list_p, key=lambda tup: tup[0], reverse=True)
    color_keys = []
    for color_p in color_list_p:
        color_keys.append(color_p[1])

    # now for the value tuples
    input_image_rgb = input_image_p.convert('RGB')
    color_list_rgb = input_image_rgb.getcolors()  # type: List[Tuple[int, Tuple[int, int, int]]]
    color_list_rgb = sorted(color_list_rgb, key=lambda tup: tup[0], reverse=True)
    color_values = []
    for color_rgb in color_list_rgb:
        color_values.append(color_rgb[1])

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
    # zero-width space to force Discord to display emojis at text height
    spacer = '' if platform == 'desktop' else '\u200B'
    for row in numpy_image:
        string_list.append(f'{spacer}{"".join(row)}')

    return string_list


def make_mosaic(colors: List[Tuple[int, int, int]]) -> BytesIO:
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

    fp = image_to_buffer([mosaic])
    return fp


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
    resample = image_to_buffer([img])

    img_colors = img.convert('RGB').getcolors()  # type: List[Tuple[int, Tuple[int, int, int]]]
    img_colors = sorted(img_colors, key=lambda tup: tup[0], reverse=True)
    colors = []
    hex_colors = []
    for ii in range(0, len(img_colors)):
        colors.append(img_colors[ii][1])
        hex_colors.append('#%02x%02x%02x' % img_colors[ii][1])

    # call the mosaic maker!
    mosaic = make_mosaic(colors)

    return ' '.join(hex_colors), mosaic, resample


# below are the blocking image functions (that suupport GIF) which require the executor_function wrapper
def make_acid_img(img: Image.Image, window: int) -> Image.Image:
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
    acid_raster_np = np.stack(acid_raster, axis=2).astype('uint8')
    acid_raster_fp = BytesIO()
    plt.imsave(acid_raster_fp, acid_raster_np)
    acid_raster_fp.seek(0)

    # open as PIL image to apply alpha mask
    img = Image.open(acid_raster_fp)
    img.putalpha(alpha)

    return img


def make_aenima_img(img: Image.Image, arg: None) -> Image.Image:
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
    with Image.open(c.clib_path_join('img', 'aenima_cover.png')) as cover:
        bg.alpha_composite(cover, (0, 0))

    return bg


def make_captioned_img(img: Image.Image, caption: str) -> Image.Image:
    """Captions an image!"""
    # 1. determine image size, resize to standardize text addition
    width, height = img.size
    ratio = width / CAPTION_RULES['width']
    img = img.resize((int(width / ratio), int(height / ratio)), resample=Image.BICUBIC)
    # get new size
    width_new, height_new = img.size

    # 2. split caption as naturally as possible
    caption_list = c.crimsplit(caption, ' ', CAPTION_RULES['str_len'])  # type: List[str]
    caption_list = [row.strip() for row in caption_list]
    caption_str = '\n'.join(caption_list)
    final_caption_list = caption_str.split('\n')  # this allows the user to split the caption with their own newlines

    # 3. fetch font
    filename = c.clib_path_join('img', 'Roboto-BlackItalic.ttf')
    with open(filename, 'rb') as f:
        font_bytes = f.read()
    font = ImageFont.truetype(BytesIO(font_bytes), CAPTION_RULES['font_size'])

    # 4. draw text image
    extra_height = CAPTION_RULES['line_height'] * len(final_caption_list) + CAPTION_RULES['buffer_bottom']
    text_image = Image.new('RGB', (width_new, extra_height), (255, 255, 255))
    draw_on_text_image = ImageDraw.Draw(text_image)

    for idx, line in enumerate(final_caption_list):
        position = (CAPTION_RULES['buffer_width'], idx * CAPTION_RULES['line_height'])
        draw_on_text_image.text(position, line, font=font, fill=(0, 0, 0))

    # 5. paste input image
    final_image = Image.new('RGBA', (width_new, height_new + extra_height), (0, 0, 0, 0))
    final_image.paste(text_image, (0, 0))
    final_image.paste(img, (0, extra_height))

    return final_image


def make_lateralus_img(img: Image.Image, arg: None) -> Image.Image:
    img = img.convert('RGBA')

    # 1. determine user image size, resize to fit in its place
    width, height = img.size
    ratio = width / 333
    img = img.resize((int(width / ratio), int(height / ratio)), resample=Image.BICUBIC)

    with Image.open(c.clib_path_join('img', 'lateralus_back.png')) as back:
        back.load()

    # 2. paste into cover back (462 x 462 pixels)
    back.paste(img, (65, 129), img)

    # 3. paste wordmark over result
    with Image.open(c.clib_path_join('img', 'lateralus_wordmark.png')) as wordmark:
        back.paste(wordmark, (0, 0), wordmark)

    return back


def make_needban_img(img: Image.Image, arg: None) -> Image.Image:
    img = img.convert('RGBA')

    width, height = img.size
    if max(width, height) > 500:
        ratio = max(width, height) / 500
        img = img.resize((int(width / ratio), int(height / ratio)), resample=Image.BICUBIC)

    width, height = img.size
    with Image.open(c.clib_path_join('img', 'ban.png')) as ban:
        ban = ban.resize((width, height), resample=Image.BICUBIC)
        img.paste(ban, (0, 0), ban)

    return img


def make_needping_img(img: Image.Image, arg: None) -> Image.Image:
    img = img.convert('RGBA')
    img = img.resize((71, 105), resample=Image.BICUBIC)

    with Image.open(c.clib_path_join('img', 'fishe_on_head.png')) as base:
        base.load()

    base.paste(img, (7, 4))

    return base


def make_pingbadge_img(img: Image.Image, position: int) -> Image.Image:
    # resize input image
    img = img.convert('RGBA')

    width, height = img.size
    if max(width, height) > 500:
        ratio = max(width, height) / 500
        img = img.resize((int(width / ratio), int(height / ratio)), resample=Image.BICUBIC)

    width, height = img.size
    size = int(width / 3)

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

    with Image.open(c.clib_path_join('img', 'roundping.png')) as badge:
        badge = badge.resize((size, size), resample=Image.BICUBIC)
        img.paste(badge, corner, badge)

    return img


def make_xokked_img(img: Image.Image, arg: None) -> Image.Image:
    img = img.convert('RGBA')

    width, height = img.size
    ratio = width / 120
    img = img.resize((int(width / ratio), int(height / ratio)), resample=Image.BICUBIC)

    with Image.open(c.clib_path_join('img', 'xokked_base.png')) as base:
        base.load()

    _, height = img.size
    base.paste(img, (30, 118 - int(height / 2)))

    return base


def resize_img(img: Image.Image, scale: float) -> Image.Image:
    width, height = img.size
    img = img.resize((int(width * scale), int(height * scale)), resample=Image.ANTIALIAS)

    return img


@c.executor_function
def process_lower_level(img: Image.Image, effect: str, arg: int) -> BytesIO:
    # this will only loop once for still images
    frame_list, durations = [], []

    # if a GIF loops, it will have the attribute loop = 0; if not, then attribute does not exist
    try:
        img.info['loop']
        image_loop = True
    except KeyError:
        image_loop = False
        pass

    for _ in ImageSequence.Iterator(img):
        # if not animated, will throw KeyError
        try:
            duration = img.info['duration']  # type: int
            durations.append(duration)
        except KeyError:
            # an empty tuple for durations tells image_to_buffer that image is still
            pass

        function_dict: Mapping[str, Callable] = {
            'acid': make_acid_img,
            'aenima': make_aenima_img,
            'caption': make_captioned_img,
            'lateralus': make_lateralus_img,
            'needban': make_needban_img,
            'needping': make_needping_img,
            'pingbadge': make_pingbadge_img,
            'xokked': make_xokked_img,
            'resize': resize_img,
        }

        # these are no longer coroutines
        img_out = function_dict[effect](img.convert('RGBA'), arg)
        frame_list.append(img_out)

    fp = image_to_buffer(frame_list, tuple(durations), image_loop)

    return fp


async def process_image(ctx: Context, image: Optional[str], effect: str, arg: Optional[int] = None) -> Tuple[Any, Any]:
    # grab user image and covert to RGBA
    img = await fetch_image(ctx, image)

    is_gif = getattr(img, 'is_animated', False)

    if is_gif:
        if img.n_frames > GIF_RULES['max_frames']:
            embed = c.crimbed(
                title='OOF',
                descr=f"That's too many frames! The limit is **{GIF_RULES['max_frames']}**.",
                footer='Gotta draw the line somewhere ¯\\_(ツ)_/¯',
                color_name='orange',
                thumb_name='weary',
            )

            await ctx.send(embed=embed)
            return None, None

        else:
            cost = img.n_frames * GIF_RULES['cost_per_frame']
            bal = await crimsogames.check_balance(ctx.author)
            if bal < cost:
                embed = c.crimbed(
                    title="**GIFs ain't free!**",
                    descr='\n'.join([
                        "You can't afford to process this GIF!",
                        (
                            f'{img.n_frames} frames \u2A09 '
                            f'\u20A2{GIF_RULES["cost_per_frame"]:.2f}/frame = '
                            f'**\u20A2{cost:.2f}**'
                        ),  # lord help me it's ugly but it's flake-y
                        f'Your balance: **\u20A2{bal:.2f}**',
                    ]),
                    footer='Play games to win crimsoCOIN! Type `>help Games` for a list.',
                    thumb_name='weary',
                    color_name='orange',
                )

                await ctx.send(embed=embed)
                return None, None

            else:
                # debit the user, credit the bot
                await crimsogames.win(ctx.author, -cost)
                await crimsogames.win(ctx.guild.me, cost)
                new_bal = await crimsogames.check_balance(ctx.author)

            # this embed will keep user updated on processing status; will be edited below as it progresses
            embed = c.crimbed(
                title='PLS TO HOLD...',
                descr='\n'.join([
                    f'Processing GIF for **{ctx.author}**...',
                    f'{img.width} \u2A09 {img.height} pixels · {img.n_frames} frames',
                ]),
                footer=f'GIF cost: \u20A2{cost:.2f} · Your balance: \u20A2{bal:.2f} ➡️ \u20A2{new_bal:.2f}',
                color_name='yellow',
                thumb_name='wizard',
            )
            msg = await ctx.send(embed=embed)

    # original image begins processing
    fp = await process_lower_level(img, effect, arg)
    n_bytes = fp.getbuffer().nbytes

    # if file too large to send via Discord, then resize
    while n_bytes > IMAGE_RULES['max_filesize']:
        if is_gif:
            embed.title = 'RESIZING...'
            await msg.edit(embed=embed)

        # recursively resize image until it meets Discord filesize limit
        img = Image.open(fp)
        scale = 0.9 * IMAGE_RULES['max_filesize'] / n_bytes  # 0.9x bias to help ensure it comes in under max size

        fp = await process_lower_level(img, 'resize', scale)
        n_bytes = fp.getbuffer().nbytes

    if is_gif:
        embed.title = 'COMPLETE!'
        embed.description = f'Processed GIF for **{ctx.author}**!'
        embed.color = 0x5AC037
        await msg.edit(embed=embed)

    return fp, img.format
