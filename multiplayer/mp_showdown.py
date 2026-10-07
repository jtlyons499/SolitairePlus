"""Readable complete payout explanations without a forced results overlay."""


def payout_lines(game):
    lines=[]
    for number,pot in enumerate(game.last_pot_awards):
        label='Main pot' if number==0 else f'Side pot {number}'
        winners=pot.get('winners',[])
        lines.append(f'{label}: ${pot.get("amount",0):,}'+(' — split' if len(winners)>1 else ''))
        lines.append(pot.get('hand') or 'Won uncontested: everyone else folded.')
        share=pot.get('share',pot.get('amount',0)//max(1,len(winners)));extra=pot.get('remainder',0)
        for j,seat in enumerate(winners):
            lines.append(f'{game.names[seat]} receives ${share+(1 if j<extra else 0):,}')
        if len(winners)>1:lines.append('Equal best five-card hands; hole cards may differ.')
        lines.append('')
    return lines or [game.result_text or 'Hand complete.']


def compact_result(game):
    awards=game.last_pot_awards
    if not awards:return ['Hand complete.']
    first=awards[0];winners=first.get('winners',[])
    title=f'Main pot split {len(winners)} ways' if len(winners)>1 else game.names[winners[0]]+' wins' if winners else 'Hand complete'
    description=(first.get('hand') or 'Uncontested').split(',')[0]
    if len(awards)>1:description+=f' • {len(awards)-1} side pot(s)'
    return [title,description]
