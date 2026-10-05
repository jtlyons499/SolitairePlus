"""Cryptid card faces using the artist's 900x1260 frame and 800x96 panel."""
from collections import OrderedDict
from pathlib import Path
import textwrap
import pygame

from cryptid_creatures import ROOT

CARD_SIZE = (900, 1260)
ART_RECT = pygame.Rect(52, 176, 796, 432)
MOVE_RECTS = tuple(pygame.Rect(50, y, 800, 96) for y in (738, 846, 954, 1062))
STYLE_COLORS = {"Slam":(155,92,65), "Slash":(160,72,87), "Air":(62,133,174),
                "Ethereal":(120,86,167), "Elemental":(65,145,99),
                "Corruption":(112,133,50), "Munition":(79,113,141)}


class CryptidCardRenderer:
    def __init__(self, catalog, art_root=None):
        self.catalog = catalog
        self.art_root = Path(art_root) if art_root else ROOT / "assets" / "cryptid_creatures"
        self._fonts = {}
        self._images = {}
        self._faces = OrderedDict()
        self._inventory = None

    def refresh(self):
        paths = [self.art_root/"card_frame.png", self.art_root/"move_panel.png", self.art_root/"creature_pack.png",
                 *sorted((self.art_root/"creatures").glob("*.png"))]
        inventory = tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in paths if p.is_file())
        if inventory != self._inventory:
            self._inventory = inventory
            self._images.clear()
            self._faces.clear()

    def font(self, size, bold=False):
        key = (int(size),bold)
        if key not in self._fonts:
            if not pygame.font.get_init():
                pygame.font.init()
            f = pygame.font.Font(None,int(size))
            f.set_bold(bold)
            self._fonts[key] = f
        return self._fonts[key]

    def _image(self, relative):
        if relative not in self._images:
            try:
                loaded = pygame.image.load(str(self.art_root/relative))
                self._images[relative] = loaded.convert_alpha() if pygame.display.get_surface() else loaded
            except (OSError, pygame.error):
                self._images[relative] = None
        return self._images[relative]

    def _text(self, surface, text, rect, size=42, color=(23,27,31), bold=False):
        rect = pygame.Rect(rect)
        while size > 18 and self.font(size,bold).size(str(text))[0] > rect.w:
            size -= 1
        rendered = self.font(size,bold).render(str(text),True,color)
        surface.blit(rendered, rendered.get_rect(midleft=(rect.x,rect.centery)))

    def _emblem(self, surface, card):
        style = card.get("attack_style", "Ethereal" if card["kind"]=="arena" else "Elemental")
        color = STYLE_COLORS[style]
        pygame.draw.rect(surface,tuple(min(255,c+70) for c in color),ART_RECT)
        center = ART_RECT.center
        pygame.draw.circle(surface,(240,235,217),center,156)
        pygame.draw.circle(surface,color,center,142,9)
        # A printed style seal is part of the card design, not a fabricated
        # creature picture. Custom illustrations replace it without changing data.
        letter = self.font(176,True).render(style[0],True,color)
        surface.blit(letter,letter.get_rect(center=(center[0],center[1]-16)))
        label = self.font(34,True).render(style.upper() if card["kind"]=="creature" else card["kind"].upper(),True,color)
        surface.blit(label,label.get_rect(center=(center[0],center[1]+92)))

    def _native(self, card_id, creature=None):
        card = self.catalog.cards[card_id]
        surface = pygame.Surface(CARD_SIZE,pygame.SRCALPHA)
        # The entire art window has an opaque foundation below the frame's hole.
        self._emblem(surface,card)
        illustration = self._image("creatures/"+card["art"])
        if illustration:
            pygame.draw.rect(surface,(232,224,204),ART_RECT)
            ratio = min(ART_RECT.w/illustration.get_width(),ART_RECT.h/illustration.get_height())
            scaled = pygame.transform.smoothscale(illustration,(max(1,round(illustration.get_width()*ratio)),max(1,round(illustration.get_height()*ratio))))
            surface.blit(scaled,scaled.get_rect(center=ART_RECT.center))
        frame = self._image("card_frame.png")
        if frame:
            surface.blit(frame if frame.get_size()==CARD_SIZE else pygame.transform.smoothscale(frame,CARD_SIZE),(0,0))
        else:
            body = pygame.Surface(CARD_SIZE,pygame.SRCALPHA)
            pygame.draw.rect(body,(245,237,214),(20,20,860,1220),border_radius=32)
            pygame.draw.rect(body,(45,55,48),(20,20,860,1220),3,border_radius=32)
            pygame.draw.rect(body,(0,0,0,0),ART_RECT)
            surface.blit(body,(0,0))
        self._text(surface,card["name"],(62,52,426,54),54,bold=True)
        if card["kind"]=="creature":
            self._text(surface,f"HP {creature.hp if creature else card['hp']}",(542,52,132,54),44,bold=True)
            self._text(surface,f"AP {creature.ap if creature else card['ap']}",(710,52,132,54),44,bold=True)
            self._text(surface,card["era"].upper()+"  /  "+card["rarity"],(64,123,764,30),30)
            for x,label,value in ((60,"ARMOR",card["armor"]),(336,"ATTACK",card["attack_style"]),(612,"DEFENSE",card["defense_style"])):
                self._text(surface,label,(x,634,226,26),25,bold=True)
                self._text(surface,value,(x,668,226,42),39,bold=True)
            moves = [self.catalog.moves[mid] for mid in card["moves"]]
        else:
            self._text(surface,f"F {card['focus']}",(542,52,132,54),46,bold=True)
            self._text(surface,"CARD",(710,52,132,54),37,bold=True)
            self._text(surface,card["kind"].upper()+"  /  "+card["rarity"],(64,123,764,30),30)
            for x,label,value in ((60,"KIND",card["kind"].title()),(336,"TARGET",card["target"].title()),(612,"FOCUS",str(card["focus"]))):
                self._text(surface,label,(x,634,226,26),25,bold=True)
                self._text(surface,value,(x,668,226,42),39,bold=True)
            moves = [dict(card,kind="support",uses=None)]
        panel = self._image("move_panel.png")
        for index,move in enumerate(moves):
            rect = MOVE_RECTS[index]
            if panel:
                surface.blit(panel if panel.get_size()==rect.size else pygame.transform.smoothscale(panel,rect.size),rect)
            else:
                pygame.draw.rect(surface,(222,226,228),rect,border_radius=12)
                pygame.draw.rect(surface,(45,55,65),rect,2,border_radius=12)
            self._text(surface,move["name"],(rect.x+16,rect.y+5,rect.w-32,37),39,bold=True)
            uses = creature.uses.get(move["id"],move["uses"]) if creature else move["uses"]
            suffix = "Unlimited" if uses is None else f"Uses {uses}"
            detail = (f"{move['style']}  |  AP {move['ap_damage']} / HP {move['hp_damage']}" if move["kind"]=="attack" else move["kind"].title())
            detail += f"  |  F {move['focus']}  |  {suffix}" if card["kind"]=="creature" else f"  |  F {move['focus']}"
            self._text(surface,detail,(rect.x+16,rect.y+49,rect.w-32,36),29)
        if card["kind"] != "creature":
            for index,line in enumerate(textwrap.wrap(card["description"],width=48)):
                self._text(surface,line,(64,866+index*43,770,40),32)
        self._text(surface,card["id"],(62,1177,660,34),25)
        self._text(surface,"(+) INFO",(740,1177,100,34),25,bold=True)
        return surface

    def render(self, card_id, size=(180,252), creature=None):
        size = tuple(map(int,size))
        state = (creature.hp,creature.ap,tuple(creature.uses.items())) if creature else None
        key = (card_id,size,state)
        if key in self._faces:
            self._faces.move_to_end(key)
            return self._faces[key]
        native = self._native(card_id,creature)
        result = native if size==CARD_SIZE else pygame.transform.smoothscale(native,size)
        self._faces[key] = result
        while len(self._faces)>128:
            self._faces.popitem(last=False)
        return result
