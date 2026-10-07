"""Calculator-inspired Score-Four screens at the game's 1366×768 canvas."""
from pathlib import Path
import time
import pygame
from score_four_difficulty import DIFFICULTIES

WHITE = (241, 247, 255)
MUTED = (163, 182, 208)
CYAN = (105, 220, 244)
DIFFICULTY_RECTS = {key: pygame.Rect(273, 205 + index*105, 820, 88) for index, key in enumerate(DIFFICULTIES)}
BACK_RECT = pygame.Rect(583, 660, 200, 48)
LAYOUT_RECT = pygame.Rect(1070, 22, 270, 46)
_LOGOS = {}
_BACKGROUND = {}
RATING_INFO_RECT = pygame.Rect(28, 22, 216, 46)
RATING_CLOSE_RECT = pygame.Rect(563, 550, 240, 50)

def strategy_reward(namespace, base):
    from career_ratings import reward_scale
    rating = (namespace or {}).get('career_ratings', {}).get('strategy', 1000)
    return round(float(rating) + base * reward_scale(rating)) - round(float(rating))

def handle_rating_info_click(mouse, game):
    if game.rating_info_open:
        if RATING_CLOSE_RECT.collidepoint(mouse): game.rating_info_open = False
        return True
    if RATING_INFO_RECT.collidepoint(mouse):
        game.rating_info_open = True
        return True
    return False

def draw_rating_info(surface, mouse, namespace):
    namespace = namespace or {}
    game = namespace.get('score_four_game')
    button(surface, RATING_INFO_RECT, 'Rating rewards', mouse)
    if game is None or not game.rating_info_open:
        return
    from career_ratings import reward_scale
    rating = namespace.get('career_ratings', {}).get('strategy', 1000)
    multiplier = reward_scale(rating)
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175)); surface.blit(overlay, (0, 0))
    panel(surface, (353, 188, 660, 446), (10, 20, 34, 255), CYAN)
    text(surface, 'STRATEGY RATING REWARDS', (683, 233), 38, CYAN, True)
    rows = [
        'Win rewards gently decrease as your rating rises.',
        'Each full 100 points above 1,000 reduces rewards by 0.5%.',
        f'Your Strategy rating: {round(rating):,}  •  Reward multiplier: {multiplier*100:g}%',
        f'Standard Solo: 50 base becomes +{strategy_reward(namespace, 50)} Strategy now',
        'The rewards shown before play include this adjustment.',
        'Competitive losses: −10 Strategy. Free Play is unrated.',
    ]
    for index, row in enumerate(rows):
        text(surface, row, (683, 297+index*36), 27, WHITE, True)
    button(surface, RATING_CLOSE_RECT, 'Close', mouse)

def draw_opponent_panel(surface, game, namespace):
    opponent = namespace.get('score_four_opponent_npc') or {}
    panel(surface, (32, 176, 360, 160))
    portrait = pygame.Rect(48, 192, 86, 86)
    draw = namespace.get('draw_npc_portrait')
    if draw and opponent:
        draw(opponent, portrait, 'score_four')
    name = opponent.get('name', 'Opponent')
    size = 32
    font = pygame.font.Font(None, size)
    while font.size(name)[0] > 222 and size > 20:
        size -= 1
        font = pygame.font.Font(None, size)
    surface.blit(font.render(name, True, WHITE), (152, 193))
    tier = {'low': 'Casual', 'mid': 'Skilled', 'strong': 'Expert', 'elite': 'Master'}.get(opponent.get('skill_tier'), 'Rival')
    text(surface, tier, (152, 230), 27, CYAN)
    label = 'Finished' if game.round_complete else 'Thinking…'
    text(surface, label, (48, 280), 24, MUTED)
    progress_fn = namespace.get('get_score_four_npc_progress')
    progress = progress_fn() if progress_fn else min(1.0, max(0.0, time.monotonic()-game.round_start_time)/max(1.0, game.npc_solve_time_seconds))
    bar = pygame.Rect(48, 309, 328, 12)
    pygame.draw.rect(surface, (34, 49, 68), bar, border_radius=6)
    if progress > 0:
        fill = bar.copy(); fill.width = max(1, round(bar.width*max(0.0, min(1.0, progress))))
        pygame.draw.rect(surface, CYAN, fill, border_radius=6)


def logo(surface, center=(683, 63), size=(390, 104)):
    path = 'assets/score_four/logo.png'
    if path not in _LOGOS:
        try: _LOGOS[path] = pygame.image.load(path).convert_alpha()
        except (OSError, pygame.error): _LOGOS[path] = None
    image = _LOGOS[path]
    if image is None:
        text(surface, 'SCORE-FOUR', center, 48, center=True)
    else:
        ratio = min(size[0]/image.get_width(), size[1]/image.get_height())
        image = pygame.transform.smoothscale(image, (int(image.get_width()*ratio), int(image.get_height()*ratio)))
        surface.blit(image, image.get_rect(center=center))

def layout_button(surface, game, mouse):
    button(surface, LAYOUT_RECT, 'Layout: ' + ('Compact' if getattr(game, 'layout', 'compact') == 'compact' else 'Wide'), mouse)

def toggle_layout(game):
    game.layout = 'wide' if getattr(game, 'layout', 'compact') == 'compact' else 'compact'

def play_control_sound(audio, action):
    name = 'score_four_' + action
    path = Path('assets/sounds') / (name + '.wav')
    if name not in audio.sounds and path.is_file():
        try: audio.load_sound(name, str(path))
        except (OSError, pygame.error): pass
    audio.play_sound(name if name in audio.sounds else 'button_click')

def draw_mode_select(surface, game, mouse, namespace):
    background(surface)
    logo(surface, (683, 134), (600, 160))
    text(surface, 'Choose your challenge', (683, 252), 36, MUTED, True)
    for key, label, x, description in (
        ('score_four_solo_rect', 'Solo', 358, 'Solve three puzzles at your chosen difficulty'),
        ('score_four_competitive_rect', 'Competitive', 703, 'Race a rival. First to three wins')):
        namespace[key].update(x, 323, 305, 80)
        button(surface, namespace[key], label, mouse)
        # Separate description rows keep both choices readable.
    text(surface, 'Solo: three puzzles, four difficulty levels', (683, 453), 29, MUTED, True)
    text(surface, 'Competitive: race a rival to three wins', (683, 495), 29, MUTED, True)
    namespace['score_four_mode_return_rect'].update(583, 638, 200, 50)
    button(surface, namespace['score_four_mode_return_rect'], 'Return', mouse)
    layout_button(surface, game, mouse)
    draw_rating_info(surface, mouse, namespace)

def text(surface, value, position, size=28, color=WHITE, center=False):
    label = pygame.font.Font(None, size).render(str(value), True, color)
    surface.blit(label, label.get_rect(center=position) if center else position)

def panel(surface, rect, color=(16, 25, 43, 215), border=(67, 96, 127)):
    rect = pygame.Rect(rect)
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, color, layer.get_rect(), border_radius=18)
    surface.blit(layer, rect)
    pygame.draw.rect(surface, border, rect, 1, border_radius=18)

def button(surface, rect, label, mouse, enabled=True, selected=False):
    rect = pygame.Rect(rect)
    hover = enabled and mouse is not None and rect.collidepoint(mouse)
    panel(surface, rect, (36, 62, 83, 235) if hover or selected else (20, 35, 55, 225), CYAN if hover or selected else (66, 91, 123))
    text(surface, label, rect.center, 29, WHITE if enabled else MUTED, True)

def background(surface):
    path = 'assets/score_four/background.png'
    if path not in _BACKGROUND:
        try: _BACKGROUND[path] = pygame.image.load(path).convert()
        except (OSError, pygame.error): _BACKGROUND[path] = None
    source = _BACKGROUND[path]
    if source is not None:
        key = surface.get_size()
        if key not in _BACKGROUND:
            _BACKGROUND[key] = pygame.transform.smoothscale(source, key)
        surface.blit(_BACKGROUND[key], (0, 0))
        return
    surface.fill((8, 15, 29))
    for x in range(0, 1366, 42):
        pygame.draw.line(surface, (13, 23, 39), (x, 0), (x, 768))
    for y in range(0, 768, 42):
        pygame.draw.line(surface, (13, 23, 39), (0, y), (1366, y))

def draw_difficulty_select(surface, mouse, namespace=None):
    background(surface)
    logo(surface, (683, 73), (450, 120))
    text(surface, 'Choose your puzzle difficulty', (683, 136), 32, MUTED, True)
    for key, rect in DIFFICULTY_RECTS.items():
        name, description, reward = DIFFICULTIES[key]
        button(surface, rect, '', mouse)
        text(surface, name, (rect.x + 24, rect.y + 12), 34)
        text(surface, description, (rect.x + 24, rect.y + 48), 27, MUTED)
        text(surface, f'+{strategy_reward(namespace, reward)} Strategy', (rect.right - 212, rect.y + 17), 26, CYAN)
    button(surface, BACK_RECT, 'Back', mouse)
    text(surface, 'Rewards include your current Strategy rating adjustment', (683, 178), 24, MUTED, True)
    draw_rating_info(surface, mouse, namespace)

def difficulty_action(mouse):
    if BACK_RECT.collidepoint(mouse): return 'back'
    return next((key for key, rect in DIFFICULTY_RECTS.items() if rect.collidepoint(mouse)), None)

def draw_score_four_table(surface, game, mouse, namespace):
    background(surface)
    compact = getattr(game, 'layout', 'compact') == 'compact'
    logo(surface)
    layout_button(surface, game, mouse)
    if game.mode == 'solo':
        status = f'{DIFFICULTIES[game.difficulty][0]}  •  Solved {game.puzzles_completed}/{game.puzzles_required}'
    else:
        opponent = (namespace.get('score_four_opponent_npc') or {}).get('name', 'Opponent')
        status = f'You {game.player_score} : {game.npc_score} {opponent}  •  Round {game.round_number}'
    text(surface, status, (683, 134), 34, CYAN, True)
    if game.mode == 'competitive': draw_opponent_panel(surface, game, namespace)
    fronts = getattr(namespace.get('game'), 'card_fronts', {})
    for index, number in enumerate(game.original_numbers):
        rank = {1: 'A', 11: 'J', 12: 'Q', 13: 'K'}.get(number, str(number))
        suit = getattr(game, 'card_suits', ['Spades', 'Hearts', 'Clubs', 'Diamonds'])[index]
        image = fronts.get(rank + {'Spades': 'S', 'Hearts': 'H', 'Clubs': 'C', 'Diamonds': 'D'}[suit])
        rect = pygame.Rect(445 + index*124, 164, 104, 146)
        if image is not None:
            surface.blit(pygame.transform.smoothscale(image, rect.size), rect)
        else:
            panel(surface, rect, (232, 238, 245, 245), (167, 190, 218))
            text(surface, rank, rect.center, 62, (19, 30, 48), True)
    text(surface, 'Combine two values at a time to make 24', (683, 334), 29, MUTED, True)
    namespace['score_four_number_rects'].clear()
    for index, value in enumerate(game.values):
        rect = pygame.Rect(505 + (index % 2)*186, 358 + (index // 2)*80, 170, 68) if compact else pygame.Rect(298+index*198, 358, 177, 96)
        namespace['score_four_number_rects'].append(rect)
        label = '—' if value is None else str(value.numerator) if value.denominator == 1 else f'{value.numerator}/{value.denominator}'
        button(surface, rect, label, mouse, enabled=value is not None and not game.round_complete, selected=index == game.selected_index)
    namespace['score_four_operator_rects'].clear()
    for index, operator in enumerate(('+', '-', '*', '/')):
        rect = pygame.Rect(505+index*94, 521, 76, 57) if compact else pygame.Rect(395+index*148, 483, 132, 65)
        namespace['score_four_operator_rects'][operator] = rect
        button(surface, rect, {'*':'×', '/':'÷', '-':'−'}.get(operator, operator), mouse, enabled=not game.round_complete, selected=game.selected_operator == operator)
    control_y = 596 if compact else 570
    for name, label, index in (('score_four_undo_rect', 'Undo', 0), ('score_four_reset_rect', 'Reset', 1), ('score_four_hint_rect', 'Hint', 2), ('score_four_exit_rect', 'Return', 3)):
        rect = pygame.Rect(427+index*132, control_y, 116, 46)
        namespace[name] = rect
        enabled = game.solo_hint_available() if name == 'score_four_hint_rect' else not game.round_complete if name in ('score_four_undo_rect', 'score_four_reset_rect') else True
        if name == 'score_four_hint_rect' and game.mode == 'solo' and not game.round_complete:
            # A translucent fill lives inside the button, under its label.
            hover = enabled and mouse is not None and rect.collidepoint(mouse)
            panel(surface, rect, (20, 35, 55, 225), CYAN if hover or enabled else (66, 91, 123))
            progress = game.solo_hint_progress()
            fill = hint_meter_surface(rect.size, progress)
            surface.blit(fill, rect)
            label = 'Hint' if enabled else f'Hint {max(1, int(30*(1-progress)+.999))}s'
            text(surface, label, rect.center, 27, WHITE, True)
        else:
            button(surface, rect, label, mouse, enabled=enabled)
    if game.mode == 'competitive' and not game.match_complete and not game.round_complete:
        preview = namespace.get('preview_competitive_rating')
        opponent = namespace.get('score_four_opponent_npc')
        if namespace.get('current_game_mode') == 'free':
            line = 'Practice match • No rating changes'
        elif preview:
            gain, loss = preview('score_four', opponent, True), preview('score_four', opponent, False)
            line = f'Win: {gain:+d} Strategy  •  Loss: {loss:+d} Strategy'
        else:
            line = 'Competitive wins earn Strategy; losses cost 10 Strategy'
        text(surface, line, (683, 680), 27, MUTED, True)
    if game.hint_text and not game.round_complete:
        words, rows = game.hint_text.split(), ['']
        font = pygame.font.Font(None, 28)
        for word in words:
            trial = (rows[-1] + ' ' + word).strip()
            if font.size(trial)[0] > 1000: rows.append(word)
            else: rows[-1] = trial
        for index, row in enumerate(rows[:3]): text(surface, row, (683, 680+index*27), 28, CYAN, True)
    if game.session_complete or game.match_complete:
        panel(surface, (363, 355, 640, 290), (8, 17, 29, 250), CYAN)
        won = game.mode == 'solo' or game.match_winner == 'player'
        text(surface, 'PUZZLES COMPLETE' if game.mode == 'solo' else 'YOU WIN' if won else 'YOU LOSE', (683, 411), 45, CYAN, True)
        if game.mode == 'competitive':
            opponent = (namespace.get('score_four_opponent_npc') or {}).get('name', 'Opponent')
            text(surface, f'You {game.player_score} — {game.npc_score} {opponent}', (683, 453), 30, WHITE, True)
        if namespace.get('current_game_mode') == 'free':
            text(surface, 'Practice complete • No rating changes', (683, 502), 28, MUTED, True)
        else:
            change = getattr(game, 'last_rating_change', None)
            if change is None:
                if game.mode == 'solo': change = strategy_reward(namespace, DIFFICULTIES[game.difficulty][2])
                elif namespace.get('preview_competitive_rating'):
                    change = namespace['preview_competitive_rating']('score_four', namespace.get('score_four_opponent_npc'), won)
                else: change = game.competitive_reward if won else -10
            text(surface, f'{round(change):+d} Strategy', (683, 502), 32, CYAN if change >= 0 else (255, 150, 150), True)
        namespace['score_four_complete_rect'] = pygame.Rect(563, 550, 240, 54)
        namespace['score_four_match_continue_rect'] = namespace['score_four_complete_rect'].copy()
        button(surface, namespace['score_four_complete_rect'], 'Continue', mouse)
    elif game.round_complete:
        text(surface, 'SOLVED!' if game.mode == 'solo' or game.round_result == 'player' else 'Opponent solved it', (683, 685), 40, CYAN, True)
    if game.round_complete and not getattr(game, '_solved_sound_played', False):
        if namespace.get('audio') and (game.mode == 'solo' or game.round_result == 'player'):
            play_control_sound(namespace['audio'], 'solved')
        game._solved_sound_played = True
    elif not game.round_complete:
        game._solved_sound_played = False
    draw_rating_info(surface, mouse, namespace)


def hint_meter_surface(size, progress):
    """Clip a full rounded meter instead of rounding a narrow progress sliver."""
    fill = pygame.Surface(size, pygame.SRCALPHA)
    inset = fill.get_rect().inflate(-6, -6)
    width = round(inset.width * max(0.0, min(1.0, progress)))
    if width:
        fill.set_clip(pygame.Rect(inset.x, inset.y, width, inset.height))
        pygame.draw.rect(fill, (73, 157, 191, 110), inset, border_radius=12)
        fill.set_clip(None)
    return fill
