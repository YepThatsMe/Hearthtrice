from Widgets.components.DataTypes import CardMetadata, CardType, Rarity
from Widgets.components.ImageGenerator.CardImageGenerator import CardImageGenerator

class SpellImageGenerator(CardImageGenerator):
    CARDTYPE = CardType.SPELL

    def generate(self, meta: CardMetadata):
        self.generate_base_card(meta.classtype)

        # PICTURE
        picture_offset = (78, 48)
        new_card = self.generate_framed_picture(meta.picture, picture_offset, meta.move_x, meta.move_y, meta.zoom)

        # DESCRIPTION BANNER
        text_banner = self.generate_description_banner(meta.description)
        t_offset = (int(self.base_card.width - text_banner.width + self.FOUNDATION_PADDING_W/2 - 75), 
                    int(570 + self.FOUNDATION_PADDING_H/2))
        new_card = self.combine_images(new_card, text_banner, t_offset)
        
        # RARITY GEM
        gem = self.generate_rarity_gem(meta.rarity)
        t_offset = (int(self.foundation.width/2 - gem.width + self.FOUNDATION_PADDING_W/2 + 48), 
                    int(518 + self.FOUNDATION_PADDING_H/2))
        new_card = self.combine_images(new_card, gem, t_offset)
        
        # DRAGON
        if meta.rarity == Rarity.LEGENDARY:
            dragon = self.generate_legendary_dragon()
            t_offset = (int(self.foundation.width/2 - dragon.width + self.FOUNDATION_PADDING_W/2 + 355), 
                        int(-65 + self.FOUNDATION_PADDING_H/2))
            new_card = self.combine_images(new_card, dragon, t_offset)

        # NAME BANNER
        name_banner = self.generate_name_banner(meta.name)
        t_offset = (int(self.base_card.width - name_banner.width + self.FOUNDATION_PADDING_W/2 - 8), 
                    int(410 + self.FOUNDATION_PADDING_H/2))
        new_card = self.combine_images(new_card, name_banner, t_offset)

        # MANA
        mana = self.generate_managem(meta.manacost)
        t_offset = (int(15), 
                    int(-35 + self.FOUNDATION_PADDING_H/2))
        new_card = self.combine_images(new_card, mana, t_offset)

        # TRIBE
        if meta.tribe:
            tribe = self.generate_tribe(meta.tribe)
            t_offset = (int(self.foundation.width/2 - 200 - self.FOUNDATION_PADDING_H/2), 
            int(self.base_card.height - 25 - self.FOUNDATION_PADDING_H/2))
            new_card = self.combine_images(new_card, tribe, t_offset)

        return new_card