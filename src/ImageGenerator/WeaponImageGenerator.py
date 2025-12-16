from DataTypes import CardMetadata, CardType, Rarity
from ImageGenerator.CardImageGenerator import CardImageGenerator
from typing import Tuple


class WeaponImageGenerator(CardImageGenerator):
    CARDTYPE = CardType.WEAPON

    def get_attack_text_offset(self, attack: int, is_double_digit: bool) -> Tuple[int, int, int]:
        if is_double_digit:
            return 0, -20, 150
        return 40, -30, 170

    def get_health_text_offset(self, health: int, is_double_digit: bool) -> Tuple[int, int, int]:
        if is_double_digit:
            return 4, -10, 150
        return 34, -20, 170

    def get_mana_text_offset(self, manacost: int, is_double_digit: bool) -> Tuple[int, int, int]:
        if is_double_digit:
            return -8, -35, 180
        return 35, -45, 200

    def get_name_text_offset(self) -> Tuple[int, int, int, int]:
        return 6, 6, 4, 9

    def get_name_banner_vertical_offset(self, text_arc_height: int, background_height: int, calculated_offset: int) -> int:
        return 45

    def get_name_banner_curve_degree(self, calculated_curve_degree: float) -> float:
        return -1

    def get_description_text_offset(self) -> Tuple[int, int]:
        return 0, 0

    def get_framed_picture_shadow_offset(self, base_offset: Tuple[int, int]) -> Tuple[int, int]:
        return base_offset[0] - 38, base_offset[1] + 33

    def get_framed_picture_avatar_offset(self, base_offset: Tuple[int, int]) -> Tuple[int, int]:
        return base_offset[0] - 38, base_offset[1] + 33

    def get_tribe_text_offset(self, text_length: int) -> Tuple[int, int]:
        w = 245 + 13.5
        w -= text_length * 13.5
        return int(w), 32

    def generate(self, meta: CardMetadata):
        self.generate_base_card(meta.classtype)

        picture_offset = (119, 14)
        new_card = self.generate_framed_picture(meta.picture, picture_offset, meta.move_x, meta.move_y, meta.zoom)

        if meta.rarity == Rarity.LEGENDARY:
            dragon = self.generate_legendary_dragon()
            t_offset = (int(self.foundation.width/2 - dragon.width + self.FOUNDATION_PADDING_W/2 + 300), 
                        int(-15 + self.FOUNDATION_PADDING_H/2))
            new_card = self.combine_images(new_card, dragon, t_offset)

        gem = self.generate_rarity_gem(meta.rarity)
        t_offset = (int(self.foundation.width/2 - gem.width + self.FOUNDATION_PADDING_W/2 + 18), 
                    int(565 + self.FOUNDATION_PADDING_H/2))
        new_card = self.combine_images(new_card, gem, t_offset)

        mana = self.generate_managem(meta.manacost)
        t_offset = (int(15), 
                    int(15 + self.FOUNDATION_PADDING_H/2))
        new_card = self.combine_images(new_card, mana, t_offset)

        name_banner = self.generate_name_banner(meta.name)
        t_offset = (int(self.base_card.width - name_banner.width + self.FOUNDATION_PADDING_W/2 - 2), 
                    int(500 + self.FOUNDATION_PADDING_H/2))
        new_card = self.combine_images(new_card, name_banner, t_offset)

        if meta.description:
            description_text = self.generate_description_on_card(meta.description, 500)
            t_offset = (int(self.foundation.width/2 - description_text.width/2 + self.FOUNDATION_PADDING_W/2 - 35), 
                        int(745 + self.FOUNDATION_PADDING_H/2))
            new_card.paste(description_text, t_offset, mask=description_text)

        if meta.tribe:
            tribe = self.generate_tribe(meta.tribe)
            t_offset = (int(self.foundation.width/2 - 200 - self.FOUNDATION_PADDING_H/2), 
                        int(self.base_card.height - 28 - self.FOUNDATION_PADDING_H/2))
            new_card = self.combine_images(new_card, tribe, t_offset)
            
        attack = self.generate_attack(meta.attack)
        t_offset = (int(35), 
                    int(self.base_card.height - 60 - self.FOUNDATION_PADDING_H/2))
        new_card = self.combine_images(new_card, attack, t_offset)

        health = self.generate_health(meta.health)
        t_offset = (int(self.foundation.width - 130 - self.FOUNDATION_PADDING_H/2), 
                    int(self.base_card.height - 75 - self.FOUNDATION_PADDING_H/2))
        new_card = self.combine_images(new_card, health, t_offset)


        return new_card

