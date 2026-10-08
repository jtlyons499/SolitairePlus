"""Restore the current Klondike deal without dealing again or awarding rewards."""
import copy
import pygame

DEAL_FIELDS = ('tableau','stock','waste','foundations','deal_status',
               'stock_passes_used','hints_remaining')

def capture_deal(game):
    game._restart_deal = copy.deepcopy({name: getattr(game,name) for name in DEAL_FIELDS})

def restart_hand(game):
    if (game.challenge_id in ('no_undo','all_or_nothing') or game.round_won
            or game.auto_solving or not getattr(game,'_restart_deal',None)):
        return False
    for name,value in copy.deepcopy(game._restart_deal).items():setattr(game,name,value)
    game.move_count=0;game.round_start_ticks=pygame.time.get_ticks()
    game.round_summary=None;game.undo_stack=[];game.selected_card=None;game.selected_source=None
    game.clear_drag();game.flip_animation=None;game.victory_animation=None
    game.hint_data=None;game.hint_start_ticks=0;game.recent_hint_moves=[]
    game.auto_solving=False;game.auto_solve_last_ticks=0;game.auto_solve_steps=0
    return True

class RestartPrompt:
    def __init__(self):
        self.open=False
        self.button=pygame.Rect(533,525,300,55)
        self.yes=pygame.Rect(463,435,210,55)
        self.no=pygame.Rect(693,435,210,55)
    def allowed(self,game,mode):
        return (mode!='head_to_head' and game.challenge_id not in ('no_undo','all_or_nothing')
                and not game.round_won and not game.auto_solving)
    def event(self,event,mouse,game,audio):
        if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:self.open=False
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and mouse is not None:
            if self.no.collidepoint(mouse):self.open=False;audio.play_sound('button_click')
            elif self.yes.collidepoint(mouse):
                if restart_hand(game):audio.play_sound('card_shuffle')
                self.open=False
    def draw(self,surface,mouse):
        shade=pygame.Surface(surface.get_size(),pygame.SRCALPHA);shade.fill((0,0,0,170));surface.blit(shade,(0,0))
        rect=pygame.Rect(413,245,540,285)
        pygame.draw.rect(surface,(24,50,40),rect,border_radius=16)
        pygame.draw.rect(surface,(150,220,190),rect,2,border_radius=16)
        for label,y,size in [('Restart this hand?',305,42),('Same deal. Timer and moves reset.',360,28),('No rewards for the abandoned attempt.',395,26)]:
            text=pygame.font.Font(None,size).render(label,True,(245,245,245));surface.blit(text,text.get_rect(center=(683,y)))
        for button,label in [(self.yes,'Restart Hand'),(self.no,'Cancel')]:
            hover=mouse is not None and button.collidepoint(mouse)
            pygame.draw.rect(surface,(55,110,85) if hover else (35,75,60),button,border_radius=10)
            pygame.draw.rect(surface,(150,220,190),button,2,border_radius=10)
            text=pygame.font.Font(None,30).render(label,True,(255,255,255));surface.blit(text,text.get_rect(center=button.center))
