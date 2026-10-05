"""Free Play launcher, catalogue, card inspector and Cryptid battle controls."""
import random
import textwrap
import pygame

from cryptid_cards import CryptidCardRenderer, STYLE_COLORS
from cryptid_creatures import Action, CryptidBattle, CryptidCatalog, DEFENSES, HAND_LIMIT, damage_breakdown
from cryptid_creatures_ai import choose_cryptid_action
from npc_personality import personality_summary
from cryptid_battle_feedback import BattleFeedback, BattleSounds, snapshot
from cryptid_encounter_view import draw_encounter
from cryptid_collection_ui import CryptidCollectionView
from cryptid_collection import deck_errors, transaction


BG = (17,30,33)
PANEL = (27,46,49)
TEXT = (242,237,218)
MUTED = (179,198,194)
GOLD = (241,196,101)


class CryptidScreen:
    def __init__(self, catalog=None):
        self.catalog = catalog or CryptidCatalog()
        self.renderer = CryptidCardRenderer(self.catalog)
        self.deck_keys = list(self.catalog.decks)
        self.deck_index = 0
        self.npcs = []
        self.npc_index = 0
        self.page = "menu"
        self.battle = None
        self.library_page = 0
        self.library_filter = "all"
        self.inspection = None
        self.rules_open = False
        self.inspect_scroll = 0
        self.selected_hand = None
        self.targets = []
        self.buttons = []
        self.cards_on_screen = []
        self.controls_page = None
        self.next_npc_action = 0
        self.next_refresh = 0
        self.feedback = BattleFeedback()
        self.sounds = BattleSounds()
        self.feedback_now = 0
        self._last_update = None
        self._pending_auto_end = False
        self.hand_page = 0
        self.sfx_volume = .6
        self.auto_end = True
        self.damage_open = False
        self.last_card_click = (-1,0)
        self.collection = None
        self.collection_view = None
        self.persist_collection = None
        self.on_career_result = None
        self.career_mode = False
        self.temporary_collection = False
        self.battle_serial = 0
        self.result_claimed = False
        self.next_reward_retry = 0
        self.notice = ""

    def enter(self, npcs=()):
        self.career_mode=False
        self.collection=None
        self.collection_view=None
        self.persist_collection=None
        self.on_career_result=None
        self.feedback.active=False
        self.npcs = list(npcs) or [{"id":"practice_keeper","name":"Keeper"}]
        self.npc_index = random.randrange(len(self.npcs))
        self.page = "menu"
        self.battle = None
        self.inspection = None
        self.targets = []
        self.rules_open = False
        self.damage_open = False
        self.renderer.refresh()

    def enter_career(self,npcs,state,persist=None,on_result=None,temporary=False):
        self.enter(npcs)
        self.career_mode=True
        self.temporary_collection=bool(temporary)
        self.collection=state
        self.persist_collection=persist
        self.on_career_result=on_result
        self.collection_view=CryptidCollectionView(self,state,persist)
        self.page='career_home'

    @property
    def npc(self):
        return self.npcs[self.npc_index] if self.npcs else {"id":"practice_keeper","name":"Keeper"}

    def start_battle(self, seed=None):
        if not self.claim_result():return
        opponent_deck = self.deck_keys[(self.deck_index+1) % len(self.deck_keys)]
        player_cards=None
        if self.career_mode:
            player_cards=self.collection['decks'][self.collection['active_deck']]['cards']
            errors=deck_errors(player_cards,self.collection['owned'],self.catalog)
            if errors:
                self.collection_view.message=' '.join(errors)
                return
            try:
                transaction(self.collection,lambda:self.collection.update(battle_serial=self.collection['battle_serial']+1),self.persist_collection)
            except OSError as error:
                self.collection_view.message='Could not save battle entry: '+str(error)
                return
            self.battle_serial=self.collection['battle_serial']
        self.result_claimed=False
        self.next_reward_retry=0
        self.battle = CryptidBattle(self.catalog,self.deck_keys[self.deck_index],opponent_deck,seed,player_cards=player_cards)
        self.page = "battle"
        self.feedback = BattleFeedback()
        self.feedback_now = pygame.time.get_ticks()
        self._last_update = self.feedback_now
        self._pending_auto_end = False
        self.hand_page = 0
        self.damage_open = False
        self.last_card_click = (-1,0)
        self.selected_hand = None
        self.inspection = None
        self.targets = []
        self.notice = ""
        self.next_npc_action = pygame.time.get_ticks()+140

    def update(self, now):
        if now >= self.next_refresh:
            self.renderer.refresh()
            self.next_refresh=now+2000
        delta=0 if self._last_update is None else max(0,now-self._last_update)
        self._last_update=now
        if self.collection_view:
            self.collection_view.update(now,bool(self.inspection or self.rules_open or self.damage_open))
        if self.page!='battle' or not self.battle:return
        if self.inspection or self.rules_open or self.damage_open:return
        self.feedback_now+=delta
        self.sounds.volume=self.sfx_volume
        was_active=self.feedback.active
        self.feedback.advance(self.feedback_now,self.sounds)
        if self.feedback.active:return
        if was_active:
            self.next_npc_action=self.feedback_now+140
            if self._pending_auto_end:
                self._pending_auto_end=False
                if Action('end') in self.battle.legal_actions(0):
                    self._perform(Action('end'),0)
                    return
        if self.battle.winner is not None:self.claim_result()
        if (self.battle.winner is not None or self.battle.turn!=1 or self.feedback_now<self.next_npc_action):return
        action=choose_cryptid_action(self.battle,self.npc)
        if action:self._perform(action,1)
        self.next_npc_action=self.feedback_now+140

    def claim_result(self):
        if not self.career_mode or not self.battle or self.battle.winner is None or self.result_claimed:return True
        if self.feedback_now<self.next_reward_retry:return False
        if not self.on_career_result:
            self.result_claimed=True
            return True
        try:
            reward=self.on_career_result(self.battle_serial,self.battle.winner)
            self.result_claimed=True
            if reward:
                self.feedback.message=f"Battle complete: +{reward['xp']} XP, +{reward['packs']} creature pack(s)."
                self.notice=self.feedback.message
            return True
        except OSError:
            self.next_reward_retry=self.feedback_now+1500
            self.notice='Could not save battle rewards. Try again before leaving.'
            if self.collection_view:self.collection_view.message=self.notice
            return False

    def _perform(self,action,seat):
        before=snapshot(self.battle)
        if not self.battle.act(action):return False
        self.feedback.start(before,self.battle,action,seat,self.feedback_now)
        return True

    def _text(self, surface, value, x, y, size=28, color=TEXT, bold=False):
        rendered = self.renderer.font(size,bold).render(str(value),True,color)
        surface.blit(rendered,(x,y))
        return rendered.get_height()

    def _wrap(self, surface, value, x, y, width, size=26, color=MUTED):
        words = str(value).split()
        lines, line = [], ""
        for word in words:
            trial = (line+" "+word).strip()
            if line and self.renderer.font(size).size(trial)[0] > width:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
        for line in lines:
            self._text(surface,line,x,y,size,color)
            y += size+3
        return y

    def _button(self, surface, rect, label, command, mouse=None, enabled=True, selected=False, size=24):
        rect = pygame.Rect(rect)
        hover = mouse is not None and rect.collidepoint(mouse)
        fill = (56,94,82) if enabled and hover else (39,69,64) if enabled else (43,49,50)
        pygame.draw.rect(surface,fill,rect,border_radius=8)
        pygame.draw.rect(surface,GOLD if selected or enabled and hover else (105,135,126),rect,2,border_radius=8)
        rendered = self.renderer.font(size,True).render(label,True,TEXT if enabled else (130,142,140))
        if rendered.get_width() > rect.w-18:
            rendered = self.renderer.font(max(16,size-4),True).render(label,True,TEXT if enabled else MUTED)
        surface.blit(rendered,rendered.get_rect(center=rect.center))
        if enabled:
            self.buttons.append((rect,command))

    def _card(self, surface, card_id, rect, creature=None, tag=None, selected=False):
        rect = pygame.Rect(rect)
        surface.blit(self.renderer.render(card_id,rect.size,creature),rect)
        if selected:
            pygame.draw.rect(surface,GOLD,rect.inflate(6,6),3,border_radius=8)
        self.cards_on_screen.append((rect,card_id,creature,tag))

    def draw(self, surface, mouse=None):
        surface.fill(BG)
        background = self.renderer._image("background.png")
        if background is not None:
            surface.blit(pygame.transform.smoothscale(background, surface.get_size()), (0, 0))
        self.buttons, self.cards_on_screen = [], []
        self.controls_page = self.page
        if self.page=='battle' and self.battle:
            name=self.npc.get('name','Opponent')
            self._text(surface,f"CRYPTID CREATURES  |  vs {name}  |  Turn {self.battle.turn_number}",20,20,29,GOLD,True)
        else:self._text(surface,"CRYPTID CREATURES",28,20,39,GOLD,True)
        self._button(surface,(1174,18,164,46),"Return",("return",),mouse)
        if self.collection_view and self.page in ('career_home','collection','builder','packs','pack_open'):
            self.collection_view.draw(surface,mouse)
        elif self.page == "menu":
            self._draw_menu(surface,mouse)
        elif self.page == "library":
            self._draw_library(surface,mouse)
        else:
            self._draw_battle(surface,mouse)
        if self.damage_open:
            self._draw_damage(surface,mouse)
        elif self.rules_open:
            self._draw_rules(surface,mouse)
        elif self.inspection:
            self._draw_inspection(surface,mouse)
        elif self.targets:
            self._draw_targets(surface,mouse)

    def _draw_menu(self, surface, mouse):
        name = self.npc.get("name","Keeper")
        self._button(surface,(42,86,660,48),f"Opponent: {name}  |  Next opponent",("opponent",),mouse)
        self._button(surface,(720,86,320,48),"Battle Rules",("rules",),mouse)
        self._button(surface,(1060,86,278,48),"Card Library",("library",),mouse)
        for index,key in enumerate(self.deck_keys):
            deck = self.catalog.decks[key]
            rect = pygame.Rect(42+index*434,154,414,444)
            pygame.draw.rect(surface,PANEL,rect,border_radius=12)
            self._button(surface,(rect.x+16,rect.y+14,382,46),deck["name"],("deck",index),mouse,selected=index==self.deck_index,size=29)
            self._card(surface,deck["cards"][0],(rect.x+118,rect.y+80,180,252),tag="menu")
            self._wrap(surface,deck["description"],rect.x+20,rect.y+350,374,23)
            self._text(surface,"8 creature cards  /  22 support and arena",rect.x+20,rect.y+414,19,MUTED)
        self._text(surface,personality_summary(self.npc),46,614,24,MUTED)
        self._button(surface,(443,650,480,60),"Start Practice Battle",("start",),mouse,size=30)
        self._text(surface,"One active + three Docket slots. Two Focus per turn. Three knockouts to win.",42,731,22,MUTED)

    def _library_ids(self):
        return [cid for cid,c in self.catalog.cards.items()
                if self.library_filter=="all" or c["kind"]==self.library_filter
                or self.library_filter=="support" and c["kind"]=="arena"]

    def _draw_library(self,surface,mouse):
        for index,(key,label) in enumerate((("all","All 60"),("creature","Creatures"),("support","Support / Arena"))):
            self._button(surface,(40+index*228,78,214,42),label,("filter",key),mouse,selected=self.library_filter==key)
        self._button(surface,(1060,78,278,42),"Starter Decks",("menu",),mouse)
        ids = self._library_ids()
        pages = max(1,(len(ids)+9)//10)
        self.library_page = max(0,min(self.library_page,pages-1))
        for index,cid in enumerate(ids[self.library_page*10:self.library_page*10+10]):
            self._card(surface,cid,(70+(index%5)*254,133+(index//5)*283,190,266),tag="library")
        self._button(surface,(40,710,180,42),"Previous",("page",-1),mouse,enabled=self.library_page>0)
        self._text(surface,f"Page {self.library_page+1} / {pages}  |  Click a card for full rules and moves.",330,721,23,MUTED)
        self._button(surface,(1158,710,180,42),"Next",("page",1),mouse,enabled=self.library_page<pages-1)

    def _battle_status(self):
        b = self.battle
        if b.winner is not None:
            return "You win!" if b.winner==0 else "Opponent wins." if b.winner==1 else "Draw."
        if b.turn==1:
            return "Opponent is thinking..."
        if not b.sides[0].active:
            return "Choose a Docket creature or a creature in hand to promote."
        if len(b.sides[0].hand)>HAND_LIMIT:
            return "Hand full: click one card to discard."
        return "Your turn. Select support, choose a move, or switch a Docket creature."

    def _preview(self, move):
        b=self.battle
        if not b or not b.sides[0].active or not b.sides[1].active or move['kind']!='attack':
            return None
        own,enemy=b.sides[0].active,b.sides[1].active
        return damage_breakdown(move,own,enemy,b.card(own.card_id),b.card(enemy.card_id),b.arena,0)

    def _draw_battle(self,surface,mouse):
        draw_encounter(self,surface,mouse)

    def _draw_damage(self,surface,mouse):
        self._shade(surface)
        pygame.draw.rect(surface,PANEL,(70,62,1226,644),border_radius=16)
        self.buttons,self.cards_on_screen=[],[]
        self._text(surface,'DAMAGE DETAILS',102,88,36,GOLD,True)
        self._button(surface,(1110,84,154,44),'Close',('close_damage',),mouse)
        hit=self.battle.last_hit
        y=150
        if hit:
            y+=self._text(surface,hit['name']+f" — {hit['ap_loss']} armor / {hit['hp_loss']} HP",102,y,32,GOLD,True)+14
            for step in hit['steps']:y=self._wrap(surface,step,102,y,1160,28,TEXT)+7
        else:y=self._wrap(surface,'No attack yet. Move buttons show damage against the current opponent.',102,y,1160,28,TEXT)+10
        y+=12
        self._text(surface,'RECENT BATTLE EVENTS',102,y,28,GOLD,True);y+=35
        old=surface.get_clip();surface.set_clip(pygame.Rect(100,y,1164,680-y))
        for item in list(self.battle.log)[-5:]:y=self._wrap(surface,item,102,y,1160,26,TEXT)+6
        surface.set_clip(old)

    def inspect(self,card_id,creature=None):
        self.inspection = (card_id,creature)
        self.inspect_scroll = 0

    def _shade(self,surface):
        shade = pygame.Surface(surface.get_size(),pygame.SRCALPHA)
        shade.fill((0,0,0,195))
        surface.blit(shade,(0,0))

    def _draw_inspection(self,surface,mouse):
        self._shade(surface)
        pygame.draw.rect(surface,(31,45,47),(54,48,1258,674),border_radius=16)
        cid,creature = self.inspection
        card = self.catalog.cards[cid]
        self._text(surface,card["name"],86,70,38,GOLD,True)
        # Isolate modal controls from all underlying game buttons and cards.
        self.buttons, self.cards_on_screen = [], []
        self._button(surface,(1130,67,152,44),"Close",("close",),mouse)
        surface.blit(self.renderer.render(cid,(410,574),creature),(92,127))
        clip = pygame.Rect(542,133,738,557)
        old_clip = surface.get_clip()
        surface.set_clip(clip)
        y = clip.y-self.inspect_scroll
        y = self._wrap(surface,card["description"],clip.x,y,clip.w-16,26,TEXT)+22
        if card["kind"]=="creature":
            if creature:
                y = self._wrap(surface,f"Current HP {creature.hp}/{card['hp']} · AP {creature.ap}/{card['ap']} · "+(", ".join(creature.conditions) or "No conditions"),clip.x,y,clip.w-16,24)+12
            y = self._wrap(surface,f"{card['era']} · {card['armor']} · HP {card['hp']} / AP {card['ap']} · {card['attack_style']} / {card['defense_style']}",clip.x,y,clip.w-16,24)+16
            resist,weak = DEFENSES[card["defense_style"]]
            y = self._wrap(surface,"Resists: "+", ".join(sorted(resist)),clip.x,y,clip.w-16,23)+6
            y = self._wrap(surface,"Weak to: "+", ".join(sorted(weak)),clip.x,y,clip.w-16,23)+24
            for mid in card["moves"]:
                m = self.catalog.moves[mid]
                uses = creature.uses[mid] if creature else m["uses"]
                y += self._text(surface,m["name"]+f"  ·  Focus {m['focus']}  ·  "+("Unlimited" if uses is None else f"Uses {uses}"),clip.x,y,27,GOLD,True)+5
                if m["kind"]=="attack":
                    y += self._text(surface,f"{m['style']} · AP {m['ap_damage']} / HP {m['hp_damage']}",clip.x,y,24,TEXT)+5
                y = self._wrap(surface,m["description"],clip.x,y,clip.w-16,23)+7
                if m.get("condition"):
                    y = self._wrap(surface,f"{round(m['condition_chance']*100)}% chance of {m['condition'].title()}.",clip.x,y,clip.w-16,23)+7
                if m.get("self_damage"):
                    r=m["self_damage"]
                    y = self._wrap(surface,f"Recoil: {r['ap']} AP / {r['hp']} HP to self.",clip.x,y,clip.w-16,23)+7
                y += 15
        else:
            y = self._wrap(surface,f"{card['kind'].title()} · Focus {card['focus']} · Target: {card['target']}",clip.x,y,clip.w-16,26)+22
        y = self._wrap(surface,"Armor first: a hit that starts against armor uses its AP damage, including overflow. With no armor, use HP damage. Combined type/arena multipliers cap at 2x. One creature move per turn.",clip.x,y,clip.w-16,22)+16
        self.inspect_max_scroll = max(0,y+self.inspect_scroll-clip.bottom)
        self.inspect_scroll = min(self.inspect_scroll,self.inspect_max_scroll)
        surface.set_clip(old_clip)
        if self.inspect_max_scroll:
            self._text(surface,"Scroll for more details",1010,696,20,MUTED)

    def _draw_targets(self,surface,mouse):
        self._shade(surface)
        rect=pygame.Rect(430,170,506,110+len(self.targets)*58)
        pygame.draw.rect(surface,PANEL,rect,border_radius=12)
        self.buttons, self.cards_on_screen = [], []
        self._text(surface,"Choose a friendly target",rect.x+24,rect.y+20,29,GOLD,True)
        side=self.battle.sides[0]
        for i,action in enumerate(self.targets):
            creature=self.battle._target(side,action.target)
            name=self.battle.card(creature.card_id)["name"]
            self._button(surface,(rect.x+24,rect.y+68+i*58,458,48),("Active: " if action.target==0 else "Docket: ")+name,("act",action),mouse)
        self._button(surface,(rect.x+24,rect.bottom-42,458,34),"Cancel",("cancel_target",),mouse,size=20)

    def _draw_rules(self,surface,mouse):
        self._shade(surface)
        pygame.draw.rect(surface,PANEL,(70,62,1226,644),border_radius=16)
        self.buttons,self.cards_on_screen=[],[]
        self._text(surface,"BATTLE RULES",102,88,36,GOLD,True)
        self._button(surface,(1110,84,154,44),"Close",("close_rules",),mouse)
        paragraphs = [
            "Win by scoring three knockouts, or by leaving your opponent unable to field a creature from hand or Docket.",
            "You start with one active creature and one on the Docket. Up to three Docket creatures are allowed. Each starter deck has 30 cards.",
            "Focus rises by two at the start of your turn, up to six. Deploying a creature to the Docket costs one. Support cards show their own costs.",
            "Use one creature move per turn: attack, guard, repair or arena. Switching costs one Focus and is allowed once per turn. It does not grant another move.",
            "Armor is hit first. A 50 AP / 30 HP move against 40 AP removes that armor and 10 HP. With zero armor before the hit, it instead deals 30 HP.",
            "Resistance halves damage; weakness doubles it. Matching your attack style adds 10%. Combined type and arena modifiers cap at 2x. Only one arena is active.",
            "Sick costs 7-12 HP at the start of a turn. Stun rolls a die: odd skips one move, even recovers; either way it then clears. Spent makes all styles effective.",
            "Steeled grants resistance; Sharpened attacks exploit weakness. Opposing bonuses cancel. Repairs stop at printed maxima. Guard effects refresh, never stack.",
            "The hand limit is ten: choose a discard if over it. An empty deck causes increasing fatigue damage: 3 HP, then 6, then 9, and so on.",
            "Select a hand card then Play Selected. Click your Docket to switch or promote. Right-click cards to inspect. Space ends your turn; Escape closes a popup or returns to decks.",
        ]
        y=150
        for index,line in enumerate(paragraphs,1):
            y=self._wrap(surface,f"{index}. {line}",102,y,1160,23,TEXT)+12

    def _act(self,action):
        if self.feedback.active:return
        if self.battle and self.battle.turn==0 and self._perform(action,0):
            self.selected_hand=None
            self.targets=[]
            self.notice=""
            self._pending_auto_end=self.auto_end and action.kind in ('move','struggle')
            self.next_npc_action=self.feedback_now+140
        else:self.notice="That action is no longer available."

    def _choose_actions(self,actions):
        if self.feedback.active:return
        if len(actions)==1:
            self._act(actions[0])
        elif actions:
            self.targets=list(actions)

    def handle_event(self,event,mouse=None):
        if self.collection_view and not (self.inspection or self.rules_open or self.damage_open):
            handled=self.collection_view.handle_key(event)
            if handled=='return':return 'return'
            if handled:return None
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE:
                if self.damage_open:
                    self.damage_open=False
                elif self.rules_open:
                    self.rules_open=False
                elif self.inspection:
                    self.inspection=None
                elif self.targets:
                    self.targets=[]
                elif self.page!="menu":
                    if not self.claim_result():return None
                    self.page="career_home" if self.career_mode else "menu"
                    self.feedback.active=False
                    self._pending_auto_end=False
                else:
                    return "return"
            elif not self.feedback.active and not self.inspection and not self.targets and not self.rules_open and not self.damage_open:
                if event.key==pygame.K_SPACE and self.page=="battle" and self.battle.turn==0:
                    self._act(Action("end"))
                elif event.key==pygame.K_RETURN and self.page=="menu":
                    self.start_battle()
            return None
        if event.type==pygame.MOUSEWHEEL and self.inspection:
            self.inspect_scroll=max(0,min(getattr(self,"inspect_max_scroll",0),self.inspect_scroll-event.y*55))
            return None
        if event.type!=pygame.MOUSEBUTTONDOWN or mouse is None or self.controls_page!=self.page:
            return None
        if event.button==1:
            for rect,command in self.buttons:
                if not rect.collidepoint(mouse):
                    continue
                name=command[0]
                if name=="return":return "return"
                if name.startswith('cc_') and self.collection_view:
                    self.collection_view.command(command)
                    return None
                if name=="close":self.inspection=None
                elif name=="damage":self.damage_open=True
                elif name=="close_damage":self.damage_open=False
                elif name=="auto_end" and not self.feedback.active:self.auto_end=not self.auto_end
                elif name=="hand_page":self.hand_page+=command[1]
                elif name=="close_rules":self.rules_open=False
                elif name=="rules":self.rules_open=True
                elif name=="cancel_target":self.targets=[]
                elif name=="menu":
                    if not self.claim_result():return None
                    self.page="career_home" if self.career_mode else "menu";self.targets=[];self.selected_hand=None
                    self.feedback.active=False;self._pending_auto_end=False
                elif name=="library":self.page="library"
                elif name=="opponent":self.npc_index=(self.npc_index+1)%len(self.npcs)
                elif name=="deck":self.deck_index=command[1]
                elif name=="filter":self.library_filter=command[1];self.library_page=0
                elif name=="page":self.library_page+=command[1]
                elif name=="start":self.start_battle()
                elif name=="act":self._act(command[1])
                elif name=="actions":self._choose_actions(command[1])
                elif name=="inspect_selected" and self.selected_hand is not None:
                    hand=self.battle.sides[0].hand
                    if 0<=self.selected_hand<len(hand):self.inspect(hand[self.selected_hand])
                return None
        if self.inspection or self.targets or self.rules_open or self.damage_open:
            return None
        for rect,cid,creature,tag in self.cards_on_screen:
            if not rect.collidepoint(mouse):
                continue
            if event.button==3 or tag in ("library","menu"):
                self.inspect(cid,creature)
            elif event.button==1 and isinstance(tag,tuple):
                b=self.battle
                if tag[0]=="hand":
                    if b.turn==0 and b.winner is None and not self.feedback.active:
                        index=tag[1]
                        if not b.sides[0].active:self._act(Action("promote",index,0))
                        elif len(b.sides[0].hand)>HAND_LIMIT:self._act(Action("discard",index))
                        else:
                            now=pygame.time.get_ticks()
                            previous,tick=self.last_card_click
                            self.selected_hand=index
                            self.last_card_click=(index,now)
                            if previous==index and now-tick<400:
                                self._choose_actions([a for a in b.legal_actions(0) if a.kind=='play' and a.index==index])
                                self.last_card_click=(-1,0)
                elif tag[0]=="docket" and tag[1]==0 and b.turn==0 and not self.feedback.active:
                    self._act(Action("switch",tag[2]) if b.sides[0].active else Action("promote",tag[2],1))
                else:
                    self.inspect(cid,creature)
            return None
        return None
