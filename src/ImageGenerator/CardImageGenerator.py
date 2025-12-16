from io import BytesIO
from typing import Tuple
from wand.image import Image as WandImage
from wand.drawing import Drawing

from PIL import Image, ImageFont, ImageDraw
import re
from DataTypes import CardMetadata, CardType, ClassType, Rarity

from PIL import Image
from io import BytesIO
from PyQt5.QtCore import QFile
import math

import sys, os

class Validate:

    def has_cyrillic(text):
        return bool(re.search('[\u0400-\u04FF]', text))

class GenerationError(BaseException):
    pass

class VirtualException(BaseException):
    pass

class CardImageGenerator:
    CARDTYPE = 0

    _image_cache = {}
    _font_cache = {}
    _name_banner_cache = {}

    font_base_path = ""
    if getattr(sys, 'frozen', False):
        font_base_path = os.path.join(sys._MEIPASS, 'fonts/')
    else:
        font_base_path = 'src/assets/fonts/'

    RESOURCE_FONT_PATH = font_base_path + "Belwe Bd BT Bold.ttf"
    RESOURCE_FONT_C_PATH = font_base_path + "Arial.ttf"

    RESOURCE_FONT_DESCR_PATH = font_base_path + "FRAMDCN.ttf"
    RESOURCE_FONT_DESCR_BOLD_PATH = font_base_path + "FRADMCN.ttf"
    RESOURCE_FONT_DESCR_ITALIC_PATH = font_base_path + "FRAMDCN.ttf"

    BASE_CARD_RESOLUTION = (600,154)
    MAX_NAME_SIZE = 30

    FOUNDATION_PADDING_W = 100
    FOUNDATION_PADDING_H = 100

    def __init__(self) -> None:
        cardtype = CardType(self.CARDTYPE).name
        base_path = f":Cardbuilder\\{cardtype}\\"
        
        self.RESOURCE_BASECARD_PATH = base_path + f"BASECARDS\\Card_Inhand_{cardtype}_"
        self.RESOURCE_MINION_DROPSHADOW = base_path + f"Card_Inhand_{cardtype}_DropShadow.png"
        self.RESOURCE_MINION_FRAME_MASK = base_path + "mask3.png"
        self.RESOURCE_GEM_COMMON_PATH = base_path + f"Card_Inhand_{cardtype}_Gem_Common.png"
        self.RESOURCE_GEM_RARE_PATH = base_path + f"Card_Inhand_{cardtype}_Gem_Rare.png"
        self.RESOURCE_GEM_EPIC_PATH = base_path + f"Card_Inhand_{cardtype}_Gem_Epic.png"
        self.RESOURCE_GEM_LEGENDARY_PATH = base_path + f"Card_Inhand_{cardtype}_Gem_Legendary.png"
        self.RESOURCE_LEGENDARY_DRAGON_PATH = base_path + f"Card_Inhand_{cardtype}_LegendaryDragon.png"
        self.RESOURCE_NAME_BANNER_PATH = base_path + f"Card_Inhand_BannerAtlas_{cardtype}_Title.png"
        if cardtype != "WEAPON":
            self.RESOURCE_DESCRIPTION_BANNER_PATH = base_path + f"Card_Inhand_BannerAtlas_{cardtype}_Text.png"
        else:
            self.RESOURCE_DESCRIPTION_BANNER_PATH = None
        self.RESOURCE_TRIBE_PLAQUE_PATH = base_path + f"Card_Inhand_BannerAtlas_{cardtype}_TribePlaque.png"
        self.RESOURCE_MANATEXTURE_PATH = base_path + "manatexture.png"
        self.RESOURCE_ATTACKTEXTURE_PATH = base_path + "attacktexture.png"
        self.RESOURCE_HEALTHTEXTURE_PATH = base_path + "healthtexture.png"

    def generate(self, card_metadata: CardMetadata):
        raise VirtualException("Method was not implemented")

    def generate_base_card(self, class_type: ClassType):
        path = ''
        if class_type is None:
            raise GenerationError("No CardType specified")
        else:
            path = self.RESOURCE_BASECARD_PATH + ClassType(class_type).name + ".png"
        
        self.base_card = self.ImageFromRes(path).convert('RGBA')
        
        self.foundation = Image.new('RGBA', size=(self.base_card.width + self.FOUNDATION_PADDING_W,
                                                    self.base_card.height+ self.FOUNDATION_PADDING_H))

    def generate_framed_picture(self, picture_bytes: bytes, offset: tuple, move_x: int=0, move_y: int=0, zoom: int=0):
        if not picture_bytes:
            picture = Image.new('RGBA', (1,1))
        else:
            picture = Image.open(BytesIO(picture_bytes))
        frame = self.ImageFromRes(self.RESOURCE_MINION_FRAME_MASK).convert('RGBA')
        shadow = self.ImageFromRes(self.RESOURCE_MINION_DROPSHADOW).convert('RGBA')

        p_x, p_y = picture.size
        s_x, s_y = frame.size

        def resize(picture: Image, difference: int = 0) -> Image:
            k = picture.width/picture.height
            if p_x >= p_y:
                # For Horizontal/Square images

                picture = picture.resize( (int(picture.width + difference * k),
                                    int(picture.height + difference )), 
                                    Image.Resampling.BILINEAR)
            else:
                picture = picture.resize( (int(picture.width + difference), 
                                    int(picture.height + difference/k) ), 
                                    Image.Resampling.BILINEAR)
            return picture

        ###### I #####
        # Enlarge low-wide image to match picture-frame size #
        if p_y < s_y:
            picture = resize(picture, frame.height - picture.height)
            
        ###### II #####
        # Enlarge high-narrow image to match picture-frame size #
        elif p_x < s_x:
            picture = resize(picture, frame.width - picture.width)

        if zoom:
            picture = resize(picture, zoom)

        p_x, p_y = picture.size

        crop_x1 = (p_x-s_x)/2
        crop_y1 = (p_y-s_y)/2
        crop_x2 = (p_x-s_x)/2 + s_x
        crop_y2 = (p_y-s_y)/2 + s_y

        picture = picture.crop(box=[crop_x1+move_x, crop_y1+move_y, crop_x2+move_x, crop_y2+move_y])

        if picture.size != frame.size:
            picture = picture.resize(frame.size, Image.Resampling.BILINEAR)

        bc_w, bc_h = self.base_card.size
        f_w, f_h = self.foundation.size
        base_x = int((f_w-bc_w)/2) + offset[0]
        base_y = int((f_h-bc_h)/2) + offset[1]
        
        avatar_offset = self.get_framed_picture_avatar_offset((base_x, base_y))
        shadow_offset = self.get_framed_picture_shadow_offset((base_x, base_y))
        
        avatar = Image.composite(picture, self.foundation, frame)
        self.foundation.paste(avatar, avatar_offset, mask=avatar)
        self.foundation.paste(shadow, shadow_offset, mask=shadow)

        t_offset = ((f_w - bc_w) // 2, ((f_h - bc_h) // 2))
        self.foundation.paste(self.base_card, t_offset, mask=self.base_card)

        return self.foundation

    def generate_name_banner(self, text: str) -> Image:
        if not text:
            return self.ImageFromRes(self.RESOURCE_NAME_BANNER_PATH).convert('RGBA')
        
        if len(text) > self.MAX_NAME_SIZE:
            raise RuntimeError("Card name length cannot exceed 30.")

        font = self.RESOURCE_FONT_PATH
        if Validate.has_cyrillic(text):
            font = self.RESOURCE_FONT_C_PATH

        cache_key = (text, self.CARDTYPE, font)
        if cache_key in CardImageGenerator._name_banner_cache:
            return CardImageGenerator._name_banner_cache[cache_key].copy()

        background = self.ImageFromRes(self.RESOURCE_NAME_BANNER_PATH).convert('RGBA')

        font_size, curve_degree, offset = self.get_text_adjust_params(
            self.get_text_size_for_12px_font(font, text)
        )


        """
        Uses ImageMagik / wand.
        """
        img = WandImage(width=1, height=1, resolution=self.BASE_CARD_RESOLUTION)
        
        with Drawing() as draw:
            draw.font = font
            draw.font_size = font_size
            
            metrics = draw.get_font_metrics(img, text)
            height, width = int(metrics.text_height), int(metrics.text_width)
            
            img.resize(width=width+15, height=height+30)
            
            text_x, text_y, outline_start, outline_end = self.get_name_text_offset()
            
            draw.stroke_color = "black"
            draw.stroke_width = 4
            draw.fill_color = "black"
            draw.text(text_x, height+text_y, text)

            draw.stroke_color = "none"
            draw.stroke_width = 0
            draw.fill_color = "white"
            draw.text(text_x, height+text_y, text)
            draw(img)
        
        img.virtual_pixel = 'transparent'

        final_curve_degree = self.get_name_banner_curve_degree(curve_degree)
        if final_curve_degree >= 0:
            img.distort('arc', (final_curve_degree, 0))

        img.format = 'png'

        text_arc = Image.open(BytesIO(img.make_blob('png'))).convert('RGBA')
        bg_w, bg_h = background.size
        img_w, img_h = text_arc.size
        vertical_offset = self.get_name_banner_vertical_offset(img_h, bg_h, offset)
        t_offset = ((bg_w - img_w) // 2, ((bg_h - img_h) - vertical_offset))

        name_banner = self.combine_images(background, text_arc, t_offset)

        CardImageGenerator._name_banner_cache[cache_key] = name_banner
        return name_banner.copy()

    def generate_description_banner(self, text: str) -> Image:
        if self.RESOURCE_DESCRIPTION_BANNER_PATH is None:
            raise GenerationError("Description banner is not supported for this card type")
                    
        BANNER_WIDTH = 580
        BANNER_HEIGHT = 300

        descrtiption_banner = self.ImageFromRes(self.RESOURCE_DESCRIPTION_BANNER_PATH).convert('RGBA')

        if not text:
            return descrtiption_banner

        font = self.get_font(self.RESOURCE_FONT_DESCR_PATH, 53)
        font_bold = self.get_font(self.RESOURCE_FONT_DESCR_BOLD_PATH, 53)
        font_italic = self.get_font_italic(self.RESOURCE_FONT_DESCR_ITALIC_PATH, 53)

        lines_of_text = self.text_wrap(text, font_bold, BANNER_WIDTH)

        if len(lines_of_text) == 1:
            HEIGHT_OFFSET = 100
            FONT_SIZE = 53
            LINE_SPACING_INC = 0
        if len(lines_of_text) == 2:
            HEIGHT_OFFSET = 110
            FONT_SIZE = 52
            LINE_SPACING_INC = 50
        if len(lines_of_text) == 3:
            HEIGHT_OFFSET = 90
            FONT_SIZE = 53
            LINE_SPACING_INC = 50
        if len(lines_of_text) == 4:
            HEIGHT_OFFSET = 60
            FONT_SIZE = 43
            LINE_SPACING_INC = 50
        if len(lines_of_text) == 5:
            HEIGHT_OFFSET = 60
            FONT_SIZE = 34
            LINE_SPACING_INC = 40
        if len(lines_of_text) == 6:
            HEIGHT_OFFSET = 35
            FONT_SIZE = 29
            LINE_SPACING_INC = 35
        if len(lines_of_text) == 7:
            HEIGHT_OFFSET = 35
            FONT_SIZE = 29
            LINE_SPACING_INC = 35
        if len(lines_of_text) == 8:
            HEIGHT_OFFSET = 16
            FONT_SIZE = 29
            LINE_SPACING_INC = 35
        if len(lines_of_text) > 8:
            raise RuntimeError("Card description is too long (max 8 lines)")

        font = self.get_font(self.RESOURCE_FONT_DESCR_PATH, FONT_SIZE)
        font_bold = self.get_font(self.RESOURCE_FONT_DESCR_BOLD_PATH, FONT_SIZE)
        font_italic = self.get_font_italic(self.RESOURCE_FONT_DESCR_ITALIC_PATH, FONT_SIZE)

        W, H = (BANNER_WIDTH, BANNER_HEIGHT)
        image = Image.new('RGBA', (W, H))

        next_line_spacing = 0
        current_font = font
        is_bold = False
        is_italic = False
        for line in lines_of_text:

            limage = Image.new('RGBA', (W, H))
            ldraw = ImageDraw.Draw(limage)
            next_symbol_spacing = 0
            skip_times = 0
            for symbol in range(len(line)):
                if skip_times > 0:
                    skip_times -= 1
                    continue
                if symbol < len(line) - 1 and line[symbol] == '/' and line[symbol+1] == 'b':
                    skip_times += 1
                    is_bold = True
                    if is_italic:
                        current_font = font_bold
                    else:
                        current_font = font_bold
                    continue
                if symbol < len(line) - 2 and line[symbol] == '/' and line[symbol+1] == '/' and line[symbol+2] == 'b':
                    skip_times += 2
                    is_bold = False
                    if is_italic:
                        current_font = font_italic
                    else:
                        current_font = font
                    continue
                if symbol < len(line) - 1 and line[symbol] == '/' and line[symbol+1] == 'i':
                    skip_times += 1
                    is_italic = True
                    if is_bold:
                        current_font = font_bold
                    else:
                        current_font = font_italic
                    continue
                if symbol < len(line) - 2 and line[symbol] == '/' and line[symbol+1] == '/' and line[symbol+2] == 'i':
                    skip_times += 2
                    is_italic = False
                    if is_bold:
                        current_font = font_bold
                    else:
                        current_font = font
                    continue
                if symbol < len(line) - 2 and line[symbol] == '/' and line[symbol+1] == '/' and line[symbol+2] == '0':
                    skip_times += 2
                    ldraw.text((next_symbol_spacing, 0), ' ', font=current_font, fill='black')
                    wSize = current_font.getlength(' ')
                    next_symbol_spacing += wSize
                    continue
                
                if is_italic:
                    char_width = int(current_font.getlength(line[symbol]))
                    char_height = int(FONT_SIZE * 1.2)
                    padding_left = max(int(char_width * 0.6), int(char_height * 0.3))
                    padding_right = int(char_width * 0.3)
                    char_img = Image.new('RGBA', (char_width + padding_left + padding_right, char_height))
                    char_draw = ImageDraw.Draw(char_img)
                    char_draw.text((padding_left, 0), line[symbol], font=current_font, fill='black')
                    char_img = char_img.transform(char_img.size, Image.AFFINE, (1, 0.3, 0, 0, 1, 0), fillcolor=(0, 0, 0, 0))
                    paste_x = int(next_symbol_spacing - padding_left * 0.3)
                    limage.paste(char_img, (paste_x, 0), mask=char_img)
                    wSize = current_font.getlength(line[symbol])
                else:
                    ldraw.text((next_symbol_spacing, 0), line[symbol], font=current_font, fill='black')
                    wSize = current_font.getlength(line[symbol])

                wSize = current_font.getlength(line[symbol])
                next_symbol_spacing += wSize
            image.paste(limage, (int((W-next_symbol_spacing)/2), next_line_spacing+HEIGHT_OFFSET), mask=limage)
            next_line_spacing += LINE_SPACING_INC
            
        
        bg_w, bg_h = descrtiption_banner.size
        img_w, img_h = image.size        
        t_offset = ((bg_w - img_w) // 2, ((bg_h - img_h) // 2))

        descrtiption_banner.paste(image, t_offset, mask=image)

        return descrtiption_banner

    def generate_rarity_gem(self, rarity: Rarity = Rarity.NONE) -> Image:
        if rarity == Rarity.COMMON:
            path = self.RESOURCE_GEM_COMMON_PATH
        elif rarity == Rarity.RARE:
            path = self.RESOURCE_GEM_RARE_PATH
        elif rarity == Rarity.EPIC:
            path = self.RESOURCE_GEM_EPIC_PATH
        elif rarity == Rarity.LEGENDARY:
            path = self.RESOURCE_GEM_LEGENDARY_PATH
        elif rarity == Rarity.NONE:
            return Image.new('RGBA', (0,0))

        return self.ImageFromRes(path, 'r').convert('RGBA')

    def generate_legendary_dragon(self):
        return self.ImageFromRes(self.RESOURCE_LEGENDARY_DRAGON_PATH, 'r').convert('RGBA')

    def get_mana_text_offset(self, manacost: int, is_double_digit: bool) -> Tuple[int, int, int]:
        if is_double_digit:
            return -8, -35, 180
        return 35, -45, 200

    def get_attack_text_offset(self, attack: int, is_double_digit: bool) -> Tuple[int, int, int]:
        if is_double_digit:
            return 55, 30, 150
        return 90, 20, 170

    def get_health_text_offset(self, health: int, is_double_digit: bool) -> Tuple[int, int, int]:
        if is_double_digit:
            return 21, 20, 150
        return 55, 10, 170

    def get_name_text_offset(self) -> Tuple[int, int, int, int]:
        return 6, 6, 4, 9

    def get_name_banner_vertical_offset(self, text_arc_height: int, background_height: int, calculated_offset: int) -> int:
        return calculated_offset

    def get_name_banner_curve_degree(self, calculated_curve_degree: float) -> float:
        return calculated_curve_degree

    def get_description_text_offset(self) -> Tuple[int, int]:
        return 0, 0

    def get_framed_picture_shadow_offset(self, base_offset: Tuple[int, int]) -> Tuple[int, int]:
        return base_offset

    def get_framed_picture_avatar_offset(self, base_offset: Tuple[int, int]) -> Tuple[int, int]:
        return base_offset

    def get_tribe_text_offset(self, text_length: int) -> Tuple[int, int]:
        w = 245 + 13.5
        w -= text_length * 13.5
        return int(w), 32

    def _draw_text_with_outline(self, draw: ImageDraw, pos: tuple, text: str, font, fill='white', outline='black', outline_width=3):
        x, y = pos
        draw.text((x, y), text, font=font, fill=fill, stroke_width=outline_width, stroke_fill=outline)

    def generate_managem(self, manacost: int = None) -> Image:
        managem = self.ImageFromRes(self.RESOURCE_MANATEXTURE_PATH, 'r').convert('RGBA')

        if manacost is None:
            return managem
        
        draw = ImageDraw.Draw(managem)
        
        if manacost is not None and manacost < 100 and manacost > -1:
            is_double_digit = manacost >= 10
            w, h, font_size = self.get_mana_text_offset(manacost, is_double_digit)
            font = self.get_font(self.RESOURCE_FONT_PATH, font_size)
            self._draw_text_with_outline(draw, (w, h), str(manacost), font)

        return managem

    def generate_attack(self, attack: int = None) -> Image:
        attack_gem = self.ImageFromRes(self.RESOURCE_ATTACKTEXTURE_PATH, 'r').convert('RGBA')
        
        draw = ImageDraw.Draw(attack_gem)
        
        if attack is not None and attack < 100:
            is_double_digit = attack >= 10 or attack < 0
            w, h, font_size = self.get_attack_text_offset(attack, is_double_digit)
            font = self.get_font(self.RESOURCE_FONT_PATH, font_size)
            self._draw_text_with_outline(draw, (w, h), str(attack), font)

        return attack_gem

    def generate_health(self, health: int = None) -> Image:
        health_gem = self.ImageFromRes(self.RESOURCE_HEALTHTEXTURE_PATH, 'r').convert('RGBA')
        
        draw = ImageDraw.Draw(health_gem)
        
        if health is not None and health < 100:
            is_double_digit = health >= 10 or health < 0
            w, h, font_size = self.get_health_text_offset(health, is_double_digit)
            font = self.get_font(self.RESOURCE_FONT_PATH, font_size)
            self._draw_text_with_outline(draw, (w, h), str(health), font)

        return health_gem
    
    def generate_description_on_card(self, text: str, max_width: int = 500) -> Image:
        if not text:
            return Image.new('RGBA', (1, 1))
        
        font = self.get_font(self.RESOURCE_FONT_DESCR_PATH, 40)
        font_bold = self.get_font(self.RESOURCE_FONT_DESCR_BOLD_PATH, 40)
        font_italic = self.get_font_italic(self.RESOURCE_FONT_DESCR_ITALIC_PATH, 40)
        
        lines_of_text = self.text_wrap(text, font_bold, max_width)
        
        if len(lines_of_text) > 6:
            raise RuntimeError("Card description is too long (max 6 lines for weapon)")
        
        font_size = 40
        if len(lines_of_text) >= 4:
            font_size = 35
        if len(lines_of_text) >= 5:
            font_size = 30
        
        font = self.get_font(self.RESOURCE_FONT_DESCR_PATH, font_size)
        font_bold = self.get_font(self.RESOURCE_FONT_DESCR_BOLD_PATH, font_size)
        font_italic = self.get_font_italic(self.RESOURCE_FONT_DESCR_ITALIC_PATH, font_size)
        
        line_height = int(font_size * 1.2)
        total_height = len(lines_of_text) * line_height
        
        text_image = Image.new('RGBA', (max_width, total_height))
        draw = ImageDraw.Draw(text_image)
        
        current_y = 0
        current_font = font
        is_bold = False
        is_italic = False
        for line in lines_of_text:
            line_image = Image.new('RGBA', (max_width, line_height))
            line_draw = ImageDraw.Draw(line_image)
            next_symbol_spacing = 0
            skip_times = 0
            
            for symbol in range(len(line)):
                if skip_times > 0:
                    skip_times -= 1
                    continue
                if symbol < len(line) - 1 and line[symbol] == '/' and line[symbol+1] == 'b':
                    skip_times += 1
                    is_bold = True
                    if is_italic:
                        current_font = font_bold
                    else:
                        current_font = font_bold
                    continue
                if symbol < len(line) - 2 and line[symbol] == '/' and line[symbol+1] == '/' and line[symbol+2] == 'b':
                    skip_times += 2
                    is_bold = False
                    if is_italic:
                        current_font = font_italic
                    else:
                        current_font = font
                    continue
                if symbol < len(line) - 1 and line[symbol] == '/' and line[symbol+1] == 'i':
                    skip_times += 1
                    is_italic = True
                    if is_bold:
                        current_font = font_bold
                    else:
                        current_font = font_italic
                    continue
                if symbol < len(line) - 2 and line[symbol] == '/' and line[symbol+1] == '/' and line[symbol+2] == 'i':
                    skip_times += 2
                    is_italic = False
                    if is_bold:
                        current_font = font_bold
                    else:
                        current_font = font
                    continue
                if symbol < len(line) - 2 and line[symbol] == '/' and line[symbol+1] == '/' and line[symbol+2] == '0':
                    skip_times += 2
                    text_x_offset, text_y_offset = self.get_description_text_offset()
                    line_draw.text((next_symbol_spacing + text_x_offset, 0 + text_y_offset), ' ', font=current_font, fill='white')
                    wSize = current_font.getlength(' ')
                    next_symbol_spacing += wSize
                    continue
                
                text_x_offset, text_y_offset = self.get_description_text_offset()
                if is_italic:
                    char_width = int(current_font.getlength(line[symbol]))
                    char_height = int(font_size * 1.2)
                    padding_left = max(int(char_width * 0.6), int(char_height * 0.3))
                    padding_right = int(char_width * 0.3)
                    char_img = Image.new('RGBA', (char_width + padding_left + padding_right, char_height))
                    char_draw = ImageDraw.Draw(char_img)
                    char_draw.text((padding_left, 0), line[symbol], font=current_font, fill='white')
                    char_img = char_img.transform(char_img.size, Image.AFFINE, (1, 0.3, 0, 0, 1, 0), fillcolor=(0, 0, 0, 0))
                    paste_x = int(next_symbol_spacing + text_x_offset - padding_left * 0.3)
                    line_image.paste(char_img, (paste_x, int(text_y_offset)), mask=char_img)
                    wSize = current_font.getlength(line[symbol])
                else:
                    line_draw.text((next_symbol_spacing + text_x_offset, 0 + text_y_offset), line[symbol], font=current_font, fill='white')
                    wSize = current_font.getlength(line[symbol])
                next_symbol_spacing += wSize
            
            line_width = next_symbol_spacing
            text_image.paste(line_image, (int((max_width - line_width) / 2), current_y), mask=line_image)
            current_y += line_height
        
        return text_image
    
    def generate_tribe(self, text: str = None) -> Image:
        tribe = self.ImageFromRes(self.RESOURCE_TRIBE_PLAQUE_PATH, 'r').convert('RGBA')

        if not text:
            return tribe
        if len(text) > 10:
            return tribe

        draw = ImageDraw.Draw(tribe)

        font = self.get_font(self.RESOURCE_FONT_PATH, 44)
        if Validate.has_cyrillic(text):
            font = self.get_font(self.RESOURCE_FONT_C_PATH, 44)

        w, h = self.get_tribe_text_offset(len(text))
        self._draw_text_with_outline(draw, (w, h), text, font, outline_width=2)

        return tribe

    def combine_images(self, background, image, t_offset=None) -> Image:
        if isinstance(background, str):
            background = self.ImageFromRes(background).convert('RGBA')
        if isinstance(image, str):
            image = self.ImageFromRes(image).convert('RGBA')

        if not t_offset:
            bg_w, bg_h = background.size
            img_w, img_h = image.size
            t_offset = ((bg_w - img_w) // 2, ((bg_h - img_h) // 2))

        background.paste(image, t_offset, mask=image)
        return background
    
    def _strip_formatting(self, text: str) -> str:
        result = text
        result = result.replace('/b', '')
        result = result.replace('//b', '')
        result = result.replace('/i', '')
        result = result.replace('//i', '')
        result = result.replace('//0', ' ')
        return result
    
    def text_wrap(self, text, font, max_width, strip=False) -> list:
        lines = []
        
        text_without_formatting = self._strip_formatting(text)
        if font.getlength(text_without_formatting) <= max_width:
            lines.append(text)
        else:
            words = text.split(' ')
            i = 0
            while i < len(words):
                line = ''
                line_without_formatting = ''
                while i < len(words):
                    word = words[i]
                    test_line = line + word + " "
                    test_line_without_formatting = self._strip_formatting(test_line)
                    if font.getlength(test_line_without_formatting) <= max_width:
                        line = test_line
                        line_without_formatting = test_line_without_formatting
                        i += 1
                        if word.endswith('//0') and i < len(words):
                            next_word = words[i]
                            test_line_with_join = line + next_word + " "
                            test_line_with_join_without_formatting = self._strip_formatting(test_line_with_join)
                            if font.getlength(test_line_with_join_without_formatting) <= max_width:
                                line = test_line_with_join
                                line_without_formatting = test_line_with_join_without_formatting
                                i += 1
                            else:
                                break
                    else:
                        break
                if not line:
                    line = words[i]
                    i += 1
                lines.append(line.rstrip())

        # Support \n newline
        # Only one per line TODO: multiple per line
        try:
            for i in range(len(lines)):
                if '\n' in lines[i]:
                    first_half, second_half = lines.pop(i).split('\n')
                    lines.insert(i, second_half.strip())
                    lines.insert(i, first_half.strip())
        except ValueError:
            pass
        
        lines = list(filter(None, lines))
        if strip:
            lines = list(map(str.strip, lines))

        return lines

    def get_text_size_for_12px_font(self, font_path: str, text: str) -> int:
        font = self.get_font(font_path, 12)
        size = font.getlength(text)
        return size
        
    def get_text_adjust_params(self, text_size_px: int) -> Tuple[int,int,int]:
        return  int(self.get_font_size(text_size_px)),    \
                int(self.get_curve_degree(text_size_px)), \
                int(self.get_offset(text_size_px))

    def get_font_size(self, text_size_px: int) -> float:
        x = text_size_px
        return -0.001586925873221*(x**2)+0.081728927577078*x+68.110135256781558

    def get_curve_degree(self, text_size_px: int) -> float:
        x = text_size_px
        return -0.000010731420018*(x**3)+0.002294332290798*(x**2)+0.006577248376604*x+19.527607034700898

    def get_offset(self, text_size_px: int) -> float:
        x = text_size_px
        #return 0.000004841197185*(x**3)+0.000805895575798*(x**2)-0.490495518803842*x+110.555105881367560
        return 0.000000000000000*(x**8)+0.000000000000000*(x**7)+0.000000000310011*(x**6) \
        -0.000000170873051*(x**5)+0.000036060789004*(x**4)-0.003637973111197*(x**3) \
        +0.180793592168535*(x**2)-4.461212339169927*x+140.206273116060634

    def get_font(self, font_path: str, size: int):
        cache_key = (font_path, size)
        if cache_key in CardImageGenerator._font_cache:
            return CardImageGenerator._font_cache[cache_key]
        try:
            font = ImageFont.truetype(font_path, size)
            CardImageGenerator._font_cache[cache_key] = font
            return font
        except OSError as e:
            raise GenerationError("Отсутствует шрифт " + font_path)
    
    def get_font_italic(self, font_path: str, size: int):
        cache_key = (font_path, size, 'italic')
        if cache_key in CardImageGenerator._font_cache:
            return CardImageGenerator._font_cache[cache_key]
        try:
            font = ImageFont.truetype(font_path, size)
            CardImageGenerator._font_cache[cache_key] = font
            return font
        except OSError as e:
            raise GenerationError("Отсутствует шрифт " + font_path)
        
    def ImageFromRes(self, path: str, mode = 'r') -> Image:
        if path in CardImageGenerator._image_cache:
            return CardImageGenerator._image_cache[path].copy()
        
        file = QFile(path)
        if not file.open(QFile.ReadOnly):
            raise GenerationError("Unable to open resource file")

        data = file.readAll()
        file.close()

        img = Image.open(BytesIO(data), mode)
        CardImageGenerator._image_cache[path] = img
        return img.copy()

