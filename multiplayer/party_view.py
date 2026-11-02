"""Four-seat multiplayer UI for Score-Four, Blind Man's Bluff and Roulette."""
from __future__ import annotations

import math
from fractions import Fraction
import pygame

import score_four_ui as sfui
from score_four import ScoreFourGame
from roulette import AMERICAN_WHEEL_ORDER, RED_NUMBERS
from party_authority import SKILL_LABELS, STACK_OPTIONS, ROULETTE_TIMERS, SCORE_FOUR_DIFFICULTIES
from mp_widgets import wooden_button
from mp_toast import LeaveToast
from mp_chat import MultiplayerChat
from texas_holdem_ui import draw_holdem_glossy_button, get_card_key

WHITE = (246, 239, 216)
MUTED = (190, 204, 197)
GOLD = (242, 202, 79)
PANEL = (12, 30, 25, 225)
ROULETTE_PLAYER_COLORS = (
    (72, 145, 235),
    (236, 184, 58),
    (170, 95, 225),
    (48, 196, 151),
)


class PartyView:
    def __init__(self, surface, assets, appearance, sound=None):
        self.surface = surface
        self.assets = assets
        self.appearance = appearance
        self.buttons = []
        self.mouse = (-1, -1)
        self.font = pygame.font.SysFont("cambria", 23, bold=True)
        self.small = pygame.font.SysFont("cambria", 18, bold=True)
        self.large = pygame.font.SysFont("cambria", 34, bold=True)
        self.score_game = ScoreFourGame()
        self.score_round = -1
        self.score_sent_round = -1
        self.score_number_rects = []
        self.score_operator_rects = {}
        self.bluff_raise = 100
        self.roulette_chip = 50
        self.roulette_phase = None
        self.roulette_phase_started = 0
        self.roulette_bet_targets = {}
        self.leave_toast = LeaveToast()
        self.chat = MultiplayerChat()
        self.chat_open = False
        self.sound = sound
        self._sfx_state = {}

    def text(self, value, pos, font=None, color=WHITE, center=False):
        label = (font or self.font).render(str(value), True, color)
        self.surface.blit(label, label.get_rect(center=pos) if center else pos)
        return label

    def panel(self, rect, fill=PANEL, border=(144, 165, 159), width=1, radius=12):
        rect = pygame.Rect(rect)
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(layer, fill, layer.get_rect(), border_radius=radius)
        self.surface.blit(layer, rect)
        pygame.draw.rect(self.surface, border, rect, width, border_radius=radius)
        return rect

    def button(self, label, rect, action, enabled=True, selected=False):
        rect = pygame.Rect(rect)
        draw_holdem_glossy_button(
            self.surface, rect, label, self.mouse, self.small, enabled,
            selected=selected, attention=False,
        )
        if enabled:
            self.buttons.append((rect, action))
        return rect

    def avatar(self, table, seat, rect):
        row = table.message.get("seats", [])[seat]
        if row.get("kind") == "Human":
            public = table.public_profiles.get(row.get("identity"), {})
            self.appearance.avatar(self.surface, public, rect, row.get("name", "Player"))
        elif row.get("kind") == "NPC":
            npc = row.get("npc")
            drawn = False
            if isinstance(npc, dict):
                try:
                    self.assets.portrait(npc, rect)
                    drawn = True
                except (AttributeError, KeyError, TypeError, pygame.error):
                    drawn = False
            if not drawn:
                pygame.draw.ellipse(self.surface, (50, 72, 65), rect)
                label = self.small.render("CPU", True, GOLD)
                self.surface.blit(label, label.get_rect(center=rect.center))
                pygame.draw.ellipse(self.surface, (210, 221, 214), rect, 2)
        else:
            pygame.draw.ellipse(self.surface, (35, 46, 42), rect)
            pygame.draw.ellipse(self.surface, (95, 111, 104), rect, 1)

    def is_text_entry_active(self):
        # Treat an open chat overlay as an active UI layer even before the
        # text box itself has focus. This lets Escape close chat first instead
        # of accidentally leaving the multiplayer room.
        return bool(self.chat_open)

    def _play(self, key):
        if callable(self.sound):
            self.sound(key)

    def _chat_rects(self):
        return pygame.Rect(946, 458, 286, 36), pygame.Rect(1240, 458, 72, 36)

    def _chat_panel_rect(self):
        return pygame.Rect(918, 154, 414, 358)

    def draw_chat_button(self, table):
        messages = table.message.get("chat_messages", [])
        unread = self.chat.sync_unread(messages, self.chat_open)
        label = "CHAT" + (" •" if unread else "")
        self.button(label, (1170, 72, 160, 36), "chat_toggle", True, selected=self.chat_open)

    def draw_chat_overlay(self, table):
        if not self.chat_open:
            return
        rect = self._chat_panel_rect()
        shade = pygame.Surface(rect.size, pygame.SRCALPHA)
        shade.fill((5, 13, 12, 246))
        self.surface.blit(shade, rect.topleft)
        pygame.draw.rect(self.surface, GOLD, rect, 2, border_radius=14)
        self.text("TABLE CHAT", (rect.x + 22, rect.y + 18), self.font, GOLD)
        self.text("Custom messages • Enter sends", (rect.x + 22, rect.y + 50), self.small, MUTED)
        self.chat.draw_messages(
            self.surface, table.message.get("chat_messages", []),
            pygame.Rect(rect.x + 22, rect.y + 82, rect.width - 44, 205),
            self.small, MUTED, GOLD, max_lines=8,
        )
        input_rect, send_rect = self._chat_rects()
        self.panel(input_rect, (8, 20, 18, 245), GOLD if self.chat.active else (126,148,140), 2 if self.chat.active else 1, 8)
        placeholder = self.chat.text if self.chat.text else "Type a message…"
        color = WHITE if self.chat.text else (155,170,164)
        shown = MultiplayerChat._fit(self.small, placeholder + ("|" if self.chat.active else ""), input_rect.w - 18)
        self.text(shown, (input_rect.x + 9, input_rect.y + 8), self.small, color)
        draw_holdem_glossy_button(self.surface, send_rect, "SEND", self.mouse, self.small, bool(self.chat.text.strip()))

    @staticmethod
    def _bet_signature(all_bets):
        rows=[]
        for seat,bets in enumerate(all_bets or []):
            for bet in bets or []:
                rows.append((seat,str(bet.get("type")),str(bet.get("value")),int(bet.get("amount",0) or 0)))
        return tuple(sorted(rows))

    def sync_sfx(self, table):
        m=table.message
        if m.get("type") not in ("party_state",):
            self._sfx_state.pop(table.mode, None)
            return
        mode=table.mode
        previous=self._sfx_state.get(mode)
        current={"revision":m.get("revision",0),"phase":m.get("phase")}
        if mode=="blind_mans_bluff":
            current.update(hand=m.get("hand_number"),actions=tuple(m.get("actions",[])),winners=tuple(m.get("winners",[])))
            if previous:
                if current["hand"]!=previous.get("hand"):
                    self._play("card_shuffle")
                old_actions=previous.get("actions",())
                for i,action in enumerate(current["actions"]):
                    old=old_actions[i] if i<len(old_actions) else ""
                    if not action or action==old:
                        continue
                    lower=action.lower()
                    if "check" in lower:self._play("check")
                    elif any(word in lower for word in ("call","bet","rais")):
                        self._play(("chips_1","chips_2","chips_3")[int(m.get("revision",0))%3])
                    elif "fold" in lower:self._play("card_move")
                if current["phase"]=="result" and previous.get("phase")!="result":
                    self._play("card_flip")
                    if m.get("your_seat") in current["winners"]:self._play("hand_win")
        elif mode=="roulette":
            bets=self._bet_signature(m.get("all_bets",[]));total=sum(row[3] for row in bets)
            current.update(bets=bets,total=total,result=m.get("result"),net=tuple(m.get("last_net",[])))
            if previous:
                if total!=previous.get("total",0):
                    self._play(("chips_1","chips_2","chips_3")[int(m.get("revision",0))%3])
                if current["phase"]=="result" and previous.get("phase")!="result":
                    seat=m.get("your_seat")
                    nets=current["net"]
                    if isinstance(seat,int) and seat<len(nets) and nets[seat]>0:self._play("hand_win")
        elif mode=="score_four":
            current.update(round=m.get("round_number"),winner=m.get("round_winner"),match=m.get("match_winner"))
            if previous:
                if current["round"]!=previous.get("round"):self._play("button_click")
                if current["winner"] is not None and previous.get("winner") is None and current["winner"]==m.get("your_seat"):
                    self._play("hand_win")
        self._sfx_state[mode]=current

    # ------------------------------------------------------------------
    # Shared room lobby
    # ------------------------------------------------------------------
    def draw_lobby(self, table):
        m = table.message
        self.appearance.background(self.surface)
        shade = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA); shade.fill((0,0,0,55)); self.surface.blit(shade,(0,0))
        self.panel((65, 62, 1236, 648), (8, 28, 22, 235), (220, 227, 220), 2, 16)
        self.text(m.get("title", "Multiplayer"), (100, 88), self.large, GOLD)
        self.text("Room code", (100, 138), self.small, MUTED)
        self.text(table.code or "...", (100, 162), pygame.font.Font(None, 48), WHITE)
        self.text("Share only this 5-digit code. The joining player does not need to choose the game first.", (100, 208), self.small, MUTED)

        # Four seat cards.
        seats = m.get("seats", [])
        for i in range(4):
            row = seats[i] if i < len(seats) else {"kind":"Empty","name":"Open seat","skill":"mid"}
            x = 100 + i * 292
            rect = self.panel((x, 255, 260, 190), (14, 42, 33, 230), GOLD if row.get("kind") == "Human" else (145,165,157), 2 if row.get("kind") == "Human" else 1)
            self.avatar(table, i, pygame.Rect(x+18, y:=275, 66, 66))
            self.text(f"Seat {i+1}", (x+98, 273), self.small, MUTED)
            self.text(row.get("name", "Open seat")[:18], (x+98, 299), self.font)
            kind = row.get("kind", "Empty")
            subtitle = kind
            if kind == "NPC": subtitle += " • " + SKILL_LABELS.get(row.get("skill", "mid"), "Skilled")
            if kind == "Human" and not row.get("connected", True): subtitle += " • Disconnected"
            self.text(subtitle, (x+98, 329), self.small, MUTED)
            if table.hosting and i > 0 and kind != "Human":
                self.button("Remove NPC" if kind == "NPC" else "Add NPC", (x+18, 365, 110, 34), ("npc_toggle", i))
                if kind == "NPC":
                    self.button("Reroll", (x+138, 365, 104, 34), ("npc_reroll", i))
            if kind == "NPC":
                self.text(SKILL_LABELS.get(row.get("skill", "mid"), "Skilled"), (x+190, 414), self.small, GOLD, True)

        # Mode-specific host configuration.
        self.panel((100, 475, 1168, 150), (13, 38, 30, 220), (130,151,143), 1)
        if table.mode == "score_four":
            self.text("Puzzle difficulty", (125, 493), self.small, MUTED)
            labels = {"easy":"Easy", "standard":"Standard", "difficult":"Difficult", "extreme":"Extreme"}
            for j, key in enumerate(SCORE_FOUR_DIFFICULTIES):
                self.button(labels[key], (125+j*150, 525, 138, 38), ("difficulty", key), table.hosting, selected=m.get("difficulty") == key)
            self.text("Every player gets the exact same four numbers. First to solve earns the round; first to 3 wins.", (125, 580), self.small, MUTED)
        elif table.mode == "blind_mans_bluff":
            self.text("Starting cash", (125, 493), self.small, MUTED)
            for j, amount in enumerate(STACK_OPTIONS):
                self.button(f"${amount:,}", (125+j*150, 525, 138, 38), ("stack", amount), table.hosting, selected=m.get("starting_stack") == amount)
            self.text("A broke human remains at the table as a spectator.", (125, 580), self.small, MUTED)
        elif table.mode == "roulette":
            self.text("Starting cash", (125, 488), self.small, MUTED)
            for j, amount in enumerate(STACK_OPTIONS):
                self.button(f"${amount:,}", (125+j*145, 516, 132, 34), ("stack", amount), table.hosting, selected=m.get("starting_stack") == amount)
            self.text("Bet timer", (745, 488), self.small, MUTED)
            for j, seconds in enumerate(ROULETTE_TIMERS):
                self.button(f"{seconds}s", (745+j*112, 516, 98, 34), ("timer", seconds), table.hosting, selected=m.get("bet_seconds") == seconds)
            self.text("Everyone bets on the same wheel. Broke humans remain as spectators.", (125, 580), self.small, MUTED)

        if table.hosting:
            self.button("START GAME", (1000, 642, 240, 50), "start", bool(m.get("can_start")))
        else:
            self.text("Host is configuring the room...", (1120, 666), self.small, MUTED, True)
        if m.get("notice"):
            self.text(m["notice"], (110, 650), self.small, GOLD)
        if m.get("waiting_names"):
            self.text("Waiting for lobby: " + ", ".join(m["waiting_names"]), (110, 680), self.small, MUTED)

    def lobby_event(self, table, action):
        if action == "start": return table.act("start")
        if not isinstance(action, tuple): return False
        kind = action[0]
        if kind == "npc_toggle": return table.act("npc_toggle", {"seat": action[1]})
        if kind == "npc_skill": return table.act("npc_skill", {"seat": action[1], "delta": action[2]})
        if kind == "npc_reroll": return table.act("npc_reroll", {"seat": action[1]})
        if kind == "difficulty": return table.act("difficulty", action[1])
        if kind == "stack": return table.act("stack", action[1])
        if kind == "timer": return table.act("timer", action[1])
        return False

    # ------------------------------------------------------------------
    # Score-Four
    # ------------------------------------------------------------------
    def sync_score_four(self, m):
        round_number = int(m.get("round_number", 0))
        if round_number == self.score_round:
            if m.get("phase") != "round": self.score_game.round_complete = True
            return
        self.score_round = round_number
        self.score_sent_round = -1
        self.score_game.mode = "multiplayer"
        self.score_game.original_numbers = list(m.get("numbers", []))
        self.score_game.card_suits = list(m.get("suits", []))
        self.score_game.values = [Fraction(n) for n in self.score_game.original_numbers]
        self.score_game.selected_index = None
        self.score_game.selected_operator = None
        self.score_game.undo_stack = []
        self.score_game.round_complete = False
        self.score_game.session_complete = False
        self.score_game.puzzles_completed = 0
        self.score_game.puzzles_required = 999

    def draw_score_four(self, table):
        m = table.message; self.sync_score_four(m); game = self.score_game
        sfui.background(self.surface); sfui.logo(self.surface)
        self.buttons = []
        # Four-player score strip above the familiar calculator.
        scores = m.get("scores", [0,0,0,0]); seats = m.get("seats", [])
        for i in range(4):
            x = 130 + i * 286
            row = seats[i] if i < len(seats) else {"name":"Open","kind":"Empty"}
            self.panel((x, 116, 255, 48), (13, 29, 48, 225), GOLD if i == m.get("round_winner") else (67,96,127), 2 if i == m.get("round_winner") else 1)
            self.text(f"{row.get('name','Open')[:14]}  {scores[i] if i < len(scores) else 0}/3", (x+127, 140), self.small, WHITE, True)

        # Same card row and calculator geometry as single-player Score-Four.
        for index, number in enumerate(game.original_numbers):
            rank = {1:'A',11:'J',12:'Q',13:'K'}.get(number, str(number))
            suit = game.card_suits[index] if index < len(game.card_suits) else 'Spades'
            image = self.assets.cards.get(rank + {'Spades':'S','Hearts':'H','Clubs':'C','Diamonds':'D'}[suit])
            rect = pygame.Rect(445 + index*124, 180, 104, 146)
            if image: self.surface.blit(pygame.transform.smoothscale(image, rect.size), rect)
            else: sfui.panel(self.surface, rect, (232,238,245,245), (167,190,218)); sfui.text(self.surface, rank, rect.center, 62, (19,30,48), True)
        sfui.text(self.surface, f"Round {m.get('round_number',1)} • Combine two values at a time to make 24", (683, 348), 29, sfui.MUTED, True)

        self.score_number_rects = []
        for index, value in enumerate(game.values):
            rect = pygame.Rect(505 + (index % 2)*186, 372 + (index // 2)*80, 170, 68)
            self.score_number_rects.append(rect)
            label = '—' if value is None else str(value.numerator) if value.denominator == 1 else f'{value.numerator}/{value.denominator}'
            sfui.button(self.surface, rect, label, self.mouse, enabled=value is not None and m.get("phase") == "round", selected=index == game.selected_index)
        self.score_operator_rects = {}
        for index, operator in enumerate(('+','-','*','/')):
            rect = pygame.Rect(505+index*94, 535, 76, 57); self.score_operator_rects[operator] = rect
            sfui.button(self.surface, rect, {'*':'×','/':'÷','-':'−'}.get(operator,operator), self.mouse, enabled=m.get("phase") == "round", selected=game.selected_operator == operator)
        self.button("Undo", (505, 614, 116, 42), "score_undo", m.get("phase") == "round")
        self.button("Reset", (635, 614, 116, 42), "score_reset", m.get("phase") == "round")

        phase = m.get("phase")
        if phase in ("round_result", "match_result"):
            shade = pygame.Surface((760,145), pygame.SRCALPHA); shade.fill((7,14,25,238)); self.surface.blit(shade,(303,585))
            winner = m.get("match_winner") if phase == "match_result" else m.get("round_winner")
            name = seats[winner]["name"] if winner is not None and winner < len(seats) else "Player"
            title = f"{name} wins the match!" if phase == "match_result" else f"{name} solved it first!"
            self.text(title, (683, 615), self.large, GOLD, True)
            if phase == "round_result":
                your = m.get("your_seat"); ready = your in m.get("ready_seats", [])
                self.button("READY" if not ready else "READY ✓", (573, 665, 220, 46), "ready", not ready)
                self.text("Next round begins when every connected human is ready.", (683, 720), self.small, MUTED, True)
            elif table.hosting:
                self.button("REMATCH", (445, 665, 220, 46), "rematch")
                self.button("ROOM LOBBY", (700, 665, 220, 46), "return_lobby")

    def score_event(self, table, mouse):
        m = table.message
        if m.get("phase") == "round":
            for i, rect in enumerate(self.score_number_rects):
                if rect.collidepoint(mouse):
                    self.score_game.select_number(i)
                    if self.score_game.is_solved() and self.score_sent_round != self.score_round:
                        self.score_sent_round = self.score_round; table.act("solved")
                    return True
            for operator, rect in self.score_operator_rects.items():
                if rect.collidepoint(mouse): self.score_game.select_operator(operator); return True
        return False

    # ------------------------------------------------------------------
    # Blind Man's Bluff
    # ------------------------------------------------------------------
    def draw_bluff(self, table):
        m=table.message; self.appearance.background(self.surface); self.buttons=[]
        self.appearance.felt(self.surface, pygame.Rect(158, 150, 1050, 430))
        self.panel((24,22,700,82),(8,24,20,232),(147,169,160),1,14)
        self.text("BLIND MAN'S BLUFF", (46, 36), self.large, GOLD)
        self.text(f"Hand {m.get('hand_number',0)}  •  Ante ${m.get('ante',0):,}  •  Pot ${m.get('pot',0):,}", (48, 78), self.small, MUTED)
        self.draw_chat_button(table)
        positions=((505,610),(95,315),(510,150),(1000,315)); seats=m.get('seats',[]); cards=m.get('cards',[]); stacks=m.get('stacks',[0]*4); folded=m.get('folded',[True]*4); actions=m.get('actions',['']*4)
        for i,(x,y) in enumerate(positions):
            row=seats[i]; active=m.get('current_actor')==i and m.get('phase')=='betting'
            self.avatar(table,i,pygame.Rect(x,y,64,64))
            badge=self.panel((x+74,y,205,62),(12,27,24,230),GOLD if active else (145,165,157),3 if active else 1)
            self.text(row.get('name','Open')[:16],(x+86,y+7),self.small)
            skill=(" • "+SKILL_LABELS.get(row.get('skill','mid'),'Skilled')) if row.get('kind')=='NPC' else ''
            self.text(f"${stacks[i]:,}{skill}",(x+86,y+34),self.small,MUTED)
            if row.get('spectator'): self.text("SPECTATING",(x+178,y+77),self.small,GOLD,True)
            elif actions[i]: self.text(actions[i],(x+178,y+77),self.small,MUTED,True)
            # Forehead card above seat: viewer's own card intentionally hidden.
            card=cards[i] if i < len(cards) else None
            rect=pygame.Rect(x+95,y-118,78,108)
            image=self.assets.cards.get(get_card_key(card),self.assets.back) if card else self.assets.back
            self.surface.blit(pygame.transform.smoothscale(image,rect.size),rect)
            if folded[i] and card is not None:
                veil=pygame.Surface(rect.size,pygame.SRCALPHA);veil.fill((20,20,20,125));self.surface.blit(veil,rect)
            if active: pygame.draw.rect(self.surface,GOLD,rect,3,border_radius=6)

        your_turn=(m.get('phase')=='betting' and m.get('current_actor')==m.get('your_seat') and not m.get('spectating'))
        self.panel((900,610,430,125),(10,26,22,235),GOLD if your_turn else (150,169,160),2 if your_turn else 1)
        if your_turn:
            self.text("YOUR TURN",(1115,606),self.small,GOLD,True)
        if m.get('spectating'):
            self.text("You are spectating",(1115,640),self.font,GOLD,True)
            self.text("You can keep watching after going broke.",(1115,675),self.small,MUTED,True)
        elif m.get('phase')=='betting' and m.get('current_actor')==m.get('your_seat'):
            seat=m.get('your_seat'); due=max(0,m.get('current_bet',0)-m.get('round_bets',[0]*4)[seat]); maximum=m.get('stacks',[0]*4)[seat]+m.get('round_bets',[0]*4)[seat]
            minimum=min(maximum,m.get('minimum_raise_to',m.get('bet_unit',10)))
            self.bluff_raise=max(minimum,min(maximum,self.bluff_raise or minimum))
            self.button("FOLD",(920,625,105,42),"fold")
            self.button(f"CALL ${due:,}" if due else "CHECK",(1035,625,130,42),"check_call")
            self.button(("RAISE" if m.get('current_bet') else "BET")+f" ${self.bluff_raise:,}",(1175,625,135,42),"bet_raise",maximum>m.get('current_bet',0))
            for j,(label,value) in enumerate((("MIN",minimum),("2×",min(maximum,max(minimum,m.get('current_bet',0)+m.get('bet_unit',10)*2))),("MAX",maximum))):
                self.button(label,(940+j*115,684,100,34),("bluff_amount",value))
        else:
            self.text(m.get('result_text','Waiting for the next action.'),(1115,660),self.small,MUTED,True)
        if m.get('phase')=='result':
            self.panel((330,500,706,62),(8,15,14,235),GOLD,2)
            self.text(m.get('result_text','Hand complete'),(683,531),self.font,GOLD,True)

    # ------------------------------------------------------------------
    # Roulette
    # ------------------------------------------------------------------
    def roulette_bet_amount(self, m, bet_type, value):
        return sum(int(b.get('amount',0)) for b in m.get('bets',[]) if b.get('type')==bet_type and b.get('value')==value)

    def draw_roulette_wheel(self, m):
        cx,cy=1080,335; outer=92; inner=40; count=len(AMERICAN_WHEEL_ORDER); sector=math.tau/count
        phase=m.get('phase'); result=m.get('result'); progress=0.0
        now = pygame.time.get_ticks()
        if phase != self.roulette_phase:
            self.roulette_phase = phase
            self.roulette_phase_started = now
        if phase=='spinning': progress=max(0.0,min(1.0,(now-self.roulette_phase_started)/4500.0))
        elif phase=='result': progress=1.0
        eased=1-(1-progress)**3; rotation=math.tau*4*eased
        pygame.draw.circle(self.surface,(5,5,5),(cx+4,cy+5),outer+8)
        pygame.draw.circle(self.surface,(120,106,78),(cx,cy),outer+14,2)
        for idx,number in enumerate(AMERICAN_WHEEL_ORDER):
            a=-math.pi/2+idx*sector+rotation;b=a+sector
            color=(24,128,69) if number in ('0','00') else (172,42,42) if int(number) in RED_NUMBERS else (28,30,33)
            pts=[(cx+math.cos(a)*inner,cy+math.sin(a)*inner),(cx+math.cos(a)*outer,cy+math.sin(a)*outer),(cx+math.cos(b)*outer,cy+math.sin(b)*outer),(cx+math.cos(b)*inner,cy+math.sin(b)*inner)]
            pygame.draw.polygon(self.surface,color,pts)
        pygame.draw.circle(self.surface,WHITE,(cx,cy),outer,3);pygame.draw.circle(self.surface,(176,145,72),(cx,cy),inner);pygame.draw.circle(self.surface,WHITE,(cx,cy),inner,2)

        ball = None
        pocket_radius = (outer + inner) / 2 + 4
        if phase == 'spinning':
            # The host already chose the authoritative result when spinning
            # begins.  Use that result only to animate the ball so it visibly
            # decelerates into the same pocket instead of jumping there when
            # the result phase starts.
            if result in AMERICAN_WHEEL_ORDER:
                idx = AMERICAN_WHEEL_ORDER.index(result)
                target_angle = -math.pi/2 + (idx + .5) * sector
            else:
                target_angle = -math.pi/2
            ball_eased = 1 - (1 - progress) ** 3
            ball_angle = target_angle + math.tau * 7.35 * (1 - ball_eased)
            ball_radius = (outer + 11) + (pocket_radius - (outer + 11)) * (progress ** 1.7)
            ball = (round(cx + math.cos(ball_angle) * ball_radius), round(cy + math.sin(ball_angle) * ball_radius))
        elif phase == 'result' and result in AMERICAN_WHEEL_ORDER:
            idx = AMERICAN_WHEEL_ORDER.index(result)
            ball_angle = -math.pi/2 + (idx + .5) * sector
            ball = (round(cx + math.cos(ball_angle) * pocket_radius), round(cy + math.sin(ball_angle) * pocket_radius))
        if ball:
            pygame.draw.circle(self.surface,(0,0,0),(ball[0]+2,ball[1]+3),7)
            pygame.draw.circle(self.surface,(250,247,229),ball,6)
            pygame.draw.circle(self.surface,(205,198,176),ball,6,1)

        center='...' if phase=='spinning' else str(result) if result is not None and phase=='result' else '?'
        self.text(center,(cx,cy),self.font,WHITE,True)

    def _draw_roulette_table_chips(self, m):
        offsets = ((-12,-11),(12,-11),(-12,11),(12,11))
        tiny = pygame.font.Font(None, 13)
        for seat, bets in enumerate(m.get('all_bets', [])[:4]):
            color = ROULETTE_PLAYER_COLORS[seat]
            for bet in bets:
                rect = self.roulette_bet_targets.get((bet.get('type'), bet.get('value')))
                if rect is None:
                    continue
                dx,dy = offsets[seat]
                center = (rect.centerx + dx, rect.centery + dy)
                pygame.draw.circle(self.surface,(10,12,12),center,10)
                pygame.draw.circle(self.surface,color,center,9)
                pygame.draw.circle(self.surface,WHITE,center,9,1)
                amount = int(bet.get('amount',0))
                label = f"{amount//1000}k" if amount >= 1000 and amount % 1000 == 0 else str(amount)
                image = tiny.render(label, True, (255,255,255))
                if image.get_width() > 16:
                    image = pygame.transform.smoothscale(image,(16,image.get_height()))
                self.surface.blit(image,image.get_rect(center=center))

    def draw_roulette(self, table):
        m=table.message; self.appearance.background(self.surface); self.buttons=[]
        self.panel((24,22,700,82),(8,24,20,232),(147,169,160),1,14)
        self.text("ROULETTE",(46,36),self.large,GOLD)
        self.text(f"Round {m.get('round_number',1)}",(48,78),self.small,MUTED)
        phase=m.get('phase'); seconds=m.get('seconds_left')
        status = f"BETTING • {seconds}s" if phase=='betting' else "WHEEL SPINNING" if phase=='spinning' else "RESULT" if phase=='result' else "TABLE FINISHED"
        self.panel((475,42,225,42),(16,35,29,230),GOLD,1,12)
        self.text(status,(587,63),self.small,GOLD,True)
        self.draw_chat_button(table)
        self.draw_roulette_wheel(m)

        # Player strips now use the same portrait-first hierarchy as the poker tables.
        seats=m.get('seats',[]); stacks=m.get('stacks',[0]*4); nets=m.get('last_net',[0]*4)
        for i,row in enumerate(seats):
            x=55+i*255
            self.panel((x,112,232,72),(12,31,26,225),GOLD if i==m.get('your_seat') else (125,148,138),2 if i==m.get('your_seat') else 1)
            self.avatar(table,i,pygame.Rect(x+10,119,48,48))
            pygame.draw.circle(self.surface, ROULETTE_PLAYER_COLORS[i], (x+62, 124), 6)
            pygame.draw.circle(self.surface, WHITE, (x+62, 124), 6, 1)
            self.text(row.get('name','Open')[:14],(x+70,120),self.small)
            detail=f"${stacks[i]:,}"+(f"  ({nets[i]:+d})" if phase=='result' and nets[i] else '')
            if row.get('spectator'):detail+=' • Spectating'
            self.text(detail,(x+70,148),self.small,MUTED)

        # American board: 0 / 00 plus 1-36, visually close to the base roulette table.
        board=pygame.Rect(62,205,820,390); self.panel(board,(16,22,20,235),(225,230,225),2,4)
        self.roulette_cells=[]; self.roulette_bet_targets={}
        zero_rect=pygame.Rect(75,217,82,77); zero2_rect=pygame.Rect(75,302,82,77)
        for label,rect in (("0",zero_rect),("00",zero2_rect)):
            pygame.draw.rect(self.surface,(26,118,66),rect);pygame.draw.rect(self.surface,WHITE,rect,2);self.text(label,rect.center,self.small,WHITE,True);self.roulette_cells.append((rect,"number",label));self.roulette_bet_targets[("number",label)]=rect
        start_x=165;cell_w=57;cell_h=55
        for number in range(1,37):
            col=(number-1)//3; row=(number-1)%3
            rect=pygame.Rect(start_x+col*cell_w,217+(2-row)*cell_h,cell_w,cell_h)
            color=(165,42,42) if number in RED_NUMBERS else (24,27,29)
            pygame.draw.rect(self.surface,color,rect);pygame.draw.rect(self.surface,WHITE,rect,1);self.text(str(number),rect.center,self.small,WHITE,True)
            self.roulette_cells.append((rect,"number",str(number)));self.roulette_bet_targets[("number",str(number))]=rect
        outside=(("RED","color","red"),("BLACK","color","black"),("ODD","parity","odd"),("EVEN","parity","even"),("1-18","range","low"),("19-36","range","high"))
        for j,(label,t,v) in enumerate(outside):
            rect=pygame.Rect(165+j*112,405,104,44);self.button(label,rect,("roulette_bet",t,v),phase=='betting' and not m.get('spectating'));self.roulette_bet_targets[(t,v)]=rect
        for j,(label,v) in enumerate((("1st 12",1),("2nd 12",2),("3rd 12",3))):
            rect=pygame.Rect(165+j*224,462,216,44);self.button(label,rect,("roulette_bet","dozen",v),phase=='betting' and not m.get('spectating'));self.roulette_bet_targets[("dozen",v)]=rect
        for j,(label,v) in enumerate((("Column 1",1),("Column 2",2),("Column 3",3))):
            rect=pygame.Rect(165+j*224,518,216,44);self.button(label,rect,("roulette_bet","column",v),phase=='betting' and not m.get('spectating'));self.roulette_bet_targets[("column",v)]=rect

        self._draw_roulette_table_chips(m)

        # Chip tray and player's current bets.
        self.panel((62,620,820,110),(12,31,26,230),(140,160,152),1)
        self.text("Chip",(82,635),self.small,MUTED)
        for j,value in enumerate((10,50,100,500)):
            self.button(f"${value}",(145+j*102,628,90,38),("chip",value),phase=='betting' and not m.get('spectating'),selected=self.roulette_chip==value)
        total=sum(int(b.get('amount',0)) for b in m.get('bets',[]))
        self.text(f"Your bets: ${total:,}",(590,638),self.small)
        self.button("CLEAR BETS",(670,678,180,36),"clear_bets",phase=='betting' and total>0 and not m.get('spectating'))
        if m.get('spectating'):
            self.text("Broke • Spectating the wheel",(1080,505),self.font,GOLD,True)
        elif phase=='betting':
            self.text("Click a chip, then a number or outside bet.",(1080,505),self.small,MUTED,True)
        elif phase=='result':
            self.text(f"Result: {m.get('result')}",(1080,505),self.font,GOLD,True)

    # ------------------------------------------------------------------
    def draw(self, table, mouse=None):
        if mouse is not None: self.mouse=mouse
        self.buttons=[]
        self.leave_toast.sync(table)
        if table.failed:
            self.appearance.background(self.surface)
            self.text("Connection ended", (683, 315), self.large, GOLD, True)
            detail = str(getattr(table, "status", "Disconnected") or "Disconnected")[:100]
            self.text(detail, (683, 360), self.small, MUTED, True)
            return
        m=table.message
        if m.get('type') in ('connecting',):
            self.appearance.background(self.surface); self.text("Connecting to relay...",(683,330),self.large,GOLD,True)
            return
        if m.get('type')=='lobby':
            self.draw_lobby(table)
        elif table.mode=='score_four':
            self.draw_score_four(table)
        elif table.mode=='blind_mans_bluff':
            self.draw_bluff(table)
        elif table.mode=='roulette':
            self.draw_roulette(table)
        else:
            self.appearance.background(self.surface); self.text("Waiting for game state...",(683,330),self.large,GOLD,True)
        if table.mode in ('blind_mans_bluff','roulette'):
            self.draw_chat_overlay(table)
        self.leave_toast.draw(self.surface, self.small)

    def event(self, event, mouse, table):
        if table.mode in ('blind_mans_bluff','roulette') and self.chat_open:
            # Escape closes the chat layer before the global multiplayer loop
            # gets a chance to interpret it as "leave room".
            if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE and not self.chat.editing:
                self.chat_open=False;self.chat.close();return True
            input_rect,send_rect=self._chat_rects()
            if self.chat.event(event,mouse,table,input_rect,send_rect):return True
            if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and not self._chat_panel_rect().collidepoint(mouse):
                self.chat_open=False;self.chat.close();return True
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        m=table.message
        if m.get('type')=='lobby':
            for rect,action in self.buttons:
                if rect.collidepoint(mouse): return self.lobby_event(table,action)
            return False
        for rect,action in self.buttons:
            if rect.collidepoint(mouse) and action=='chat_toggle':
                self.chat_open=not self.chat_open
                if not self.chat_open:self.chat.close()
                return True
        if table.mode=='score_four':
            if self.score_event(table,mouse): return True
            for rect,action in self.buttons:
                if not rect.collidepoint(mouse):continue
                if action=='score_undo':self.score_game.undo();return True
                if action=='score_reset':self.score_game.reset_current_puzzle();return True
                if action=='ready':return table.act('ready')
                if action=='rematch':return table.act('rematch')
                if action=='return_lobby':return table.act('return_lobby')
            return False
        if table.mode=='blind_mans_bluff':
            for rect,action in self.buttons:
                if not rect.collidepoint(mouse):continue
                if isinstance(action,tuple) and action[0]=='bluff_amount':self.bluff_raise=action[1];return True
                if action=='bet_raise':return table.act('bet_raise',self.bluff_raise)
                if action in ('fold','check_call'):return table.act(action)
            return False
        if table.mode=='roulette':
            # Number cells are intentionally handled separately because they do not use button chrome.
            if m.get('phase')=='betting' and not m.get('spectating'):
                for rect,t,v in getattr(self,'roulette_cells',[]):
                    if rect.collidepoint(mouse): return table.act('bet',{'type':t,'value':v,'amount':self.roulette_chip})
            for rect,action in self.buttons:
                if not rect.collidepoint(mouse):continue
                if isinstance(action,tuple) and action[0]=='chip':self.roulette_chip=action[1];return True
                if isinstance(action,tuple) and action[0]=='roulette_bet':return table.act('bet',{'type':action[1],'value':action[2],'amount':self.roulette_chip})
                if action=='clear_bets':return table.act('clear_bets')
            return False
        return False
