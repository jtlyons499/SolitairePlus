# Poker rule changes

This file lists what changed in the rules of the five single-player poker tables during the restructure sprint
(November 2026): the Phase 7 fixes (B35, B40, B41, B43) and B86, which put all five tables on one shared set of
table rules while keeping each game's own structure. Since Phase 11, online Texas Hold'em and Blind Man's Bluff rooms
use the same rules (see "Online play" at the end). No rule here creates
or loses chips: chip totals are checked after every step of 1,000 seeded random hands per game, and buy-in and
cash-out are tested to move exactly the right money. The technical audit is in [dev/B86_POKER_AUDIT.md](dev/B86_POKER_AUDIT.md).

Examples use a $1,000 buy-in: Texas Hold'em and Five-Card Draw blinds $10/$20; Seven-Card Stud ante $2, bring-in
$5, small bet $10, big bet $20; Five-O Poker ante $10; Blind Man's Bluff ante $8, minimum bet $10.

## Every poker table

- **A forced bet a player cannot cover.**
  Now: a player with chips but less than the blind, ante or bring-in puts in what they have and plays the hand
  all-in for that amount. A player is out only at $0. The session ends when you have $0 or every opponent has $0.
  Before: Texas Hold'em, Five-Card Draw and Seven-Card Stud already worked this way. At Blind Man's Bluff a short
  player sat the hand out, and the session ended as soon as you, or every NPC, had less than the ante. Five-O
  Poker keeps its own rule on purpose: both players need the full ante.

- **The bet to call after a short all-in blind or bring-in (B39).**
  Now: while two or more players can still act, the call is the full blind or bring-in. Once only one player
  with chips is left, that player only has to match what the others really put in. If it already has, it gets
  no turn and the rest of the cards are dealt out. Example: you post the $10 small blind, the big blind has only
  $5 and posts it all-in, and everyone else folds. You are not asked to act, the hand runs out, and your extra
  $5 comes back to you.
  Before: you had to call $10 more (to $20) or fold, and folding gave the big blind all $15. Hold'em used the
  smaller amount only when the hand was dealt heads-up; Draw and Stud always asked for the full amount.
  The same rule skips turns that cannot change anything, such as the big blind's check when everyone else is
  already all-in. Five-O Poker and Blind Man's Bluff have only antes, so this never comes up there.

- **No bet or raise that nobody can answer (B36).**
  Now: nobody may bet or raise unless another player still in the hand has chips to respond.
  Before: at Hold'em, Draw and Stud you were already blocked, but an NPC could still bet or raise when everyone
  else left in the hand was all-in. Five-O Poker and Blind Man's Bluff already blocked everyone.

- **Minimum raise and re-opening the betting.**
  Unchanged: a raise must be at least as big as the last full raise. A short all-in (less than a full raise)
  raises the amount to call, but players who already acted may only call or fold.
  New at Hold'em, Draw and Blind Man's Bluff: several short all-ins that together add up to a full raise do
  re-open the betting. Example: you bet $100, Ada goes all-in for $150, Bo goes all-in for $210 and Cy calls
  $210. You now face $110 more, at least a full $100 raise, so you may raise again. Before: call or fold only.
  (If Ada and Bo were the only others left, nobody could answer a raise, so you could still only call or fold.)
  A single all-in to $150 still does not re-open. Seven-Card Stud keeps "short all-ins never re-open". Five-O
  Poker has one bet size at a time, worked out from the pot.

- **Uncalled chips come back; they are not won.**
  Now: chips nobody matched go back to whoever bet them, and getting them back is not a win. Example: you go
  all-in for $500, the blinds fold, and Cy calls with a last $200 and wins. The result reads "Cy wins $430 with
  Pair of Queens ..." and the log says "Uncalled $300 returned to you." The pot shown after the hand leaves out
  the returned chips ($430).
  Before: the result read "Payouts: You $300 ...; Cy $430 ...". Your own $300 counted as a pot you won, with the
  win sound, career fans and Hold'em achievement credit, and the pot showed $730. Blind Man's Bluff already gave
  uncalled chips back at a showdown (not on a fold win, see its section); it now says so in the result text.

- **Side pots.**
  Now: chips from players who folded join the pot they were paid into instead of making extra side pots.
  Example: you and Cy each put in $100 and the blinds folded $10 and $20. The payout recap (Hold'em only) now
  shows one $230 main pot, and the hand log lists no extra side pots. Before: a $40 main pot, a $30 side pot and
  a $160 side pot, all between the same two players.
  Also, a layer of chips that no live player paid into now goes back exactly to the players who paid it. Before,
  those chips vanished at Hold'em, Draw and Stud, and Blind Man's Bluff could lose an odd chip when refunding
  them (B37, B42). This could only happen in rare spots.

- **Fold wins.**
  Now: when everyone else folds, the hand is settled like a showdown with one player left. The winner wins the
  chips that were matched, and its own unmatched bet comes back as a refund. Example: you go all-in for $1,000
  and both blinds fold. The log says "Uncalled $980 returned to you." and the result says "You win $50." (the
  $30 of blinds plus the first $20 of your bet, which the big blind matched). Your stack ends the same.
  Before: "You win $1,030."
  The same rule means a short all-in player left alone by the folds can never win more than it matched.

- **Odd chips (B38).**
  Now: when a split pot does not divide evenly, the odd chips go one at a time to the tied winners, starting
  with the first one to the dealer's left and going round the table. A tied dealer gets one last. Seven-Card Stud
  shows no dealer button; it keeps a hidden dealer that moves one seat each hand (see its section). Five-O Poker
  and Blind Man's Bluff have no dealer, so the player who acts first that hand comes first (this moves round the
  table each hand), even if that player only checked. Example: you are the dealer and split a $15 pot with Ada on
  your left. Ada gets $8 and you get $7.
  Before: Hold'em and Blind Man's Bluff gave odd chips to the lowest seat, which is usually you (you got $8).
  Draw and Stud gave the first one to the dealer if the dealer was tied. Five-O gave it to the NPC.

- **Who counts as the winner of a hand.**
  Now one rule everywhere. You won a hand (or tied, if you shared) when you won a pot that two or more players
  could win. A pot only one player could win (its own extra chips plus folded players' chips) counts as a win
  only if that player is up on the hand. A fold win is always a win. This decides the win sound, the winner
  highlight, the payout-chip animation, the Hold'em hand achievements, the Blind Man's Bluff won/tied/lost
  counts, which NPCs talk as winners at the showdown and in Quick Chat replies, and, at Blind Man's Bluff,
  whether NPCs read a shown card as weak. (At Hold'em, Draw and Stud an NPC reads a shown hand as weak by its
  category, high card or one pair, whoever won.) Example: you put in $100, Ada is all-in for $60 and wins the main
  pot, and Bo put in $100 and then folded. The $80 side pot can only go to you, so you get it, but you are $20
  down on the hand: no win sound, no fans.
  Before: at Hold'em, Draw and Stud anyone who got chips back counted as a winner, uncalled chips included.

- **Career fans for a hand** (Hold'em, Draw and Stud; Five-O Poker and Blind Man's Bluff pay fans only at
  cash-out).
  Now: paid on your net for the hand (what you got back minus what you put in), and only when it is above $0.
  Examples: the $1,000 shove the blinds fold to pays fans on $30. If you put in $50, win the $150 main pot and Bo
  wins a $100 side pot, you get fans on $100.
  Before: at Hold'em and Draw, fans were paid on the total of every pot in the hand, including pots other players
  won and your own uncalled chips ($1,030 and $250 in these examples). At Seven-Card Stud a showdown win paid fans
  on $1, or on the pot of an earlier fold win (see its section).

- **All-in run-outs and play after you fold.**
  Now: once nobody can bet any more, the remaining cards or draws are dealt without betting. After you fold, the
  NPCs still in the hand keep betting at their normal pace.
  Before: after you folded, Hold'em dealt the rest of the board at once and went straight to the showdown, even
  when an NPC had just bet and nobody had answered. All-in run-outs were already dealt one street at a time.
  Draw and Stud already played on. Blind Man's Bluff played on, but instantly (see NPC thinking time). In Five-O
  Poker your fold ends the hand.

- **Session start and end.**
  Now: every table starts a session with a clean slate: chat history, the Quick Chat menu and queued NPC replies,
  the last session's grudges and NPC reads, and the table timers. Every timer is cleared when the session ends.
  Before: Hold'em kept the last session's chat. Draw, Stud, Five-O Poker and Blind Man's Bluff could open with
  Quick Chat replies left over from the last session.

- **NPC thinking time.**
  Now: every NPC waits the Table Speed delay before it acts (slow 1.8 s, normal 1.2 s, fast 0.6 s). Blind Man's
  Bluff shows which NPC is thinking during the pause, and Five-O Poker now shows it before its opening bet too.
  Table Speed is set in the Options of the Hold'em, Draw or Stud table and also applies at Five-O Poker and
  Blind Man's Bluff.
  Before: Hold'em, Draw and Stud already did this. Five-O Poker waited 0.65 s before answering your bet and made
  its opening bet at once, and Blind Man's Bluff NPCs acted instantly.

- **How NPCs decide** (the original maintainer's request: the same NPC behaviour at every table).
  - Cash on hand: an NPC whose stack grows past 1.15 times the buy-in plays bolder, up to the full effect at 2.5
    times. Where bet sizes are free, its own bets are softly capped relative to the buy-in (not at Five-O Poker,
    whose bet size is worked out from the pot). New at Blind Man's Bluff. Before, a big stack had no effect there;
    a short stack already changed its play, as at every table (it took a stand sooner, and a call that cost most
    of its stack weighed more).
  - Grudges: an NPC that loses a contested showdown holds a grudge against the winner. The more it put in, the
    stronger the grudge (its chips in the hand divided by the buy-in). The grudge presses only on the last player
    who made a full bet or raise. Five-O Poker already had grudges, always with the same weight; it now weighs
    them by chips in the hand, as above. Blind Man's Bluff no longer counts a short all-in as that bet.
  - Skill: from the NPC's career rating for that game, or its skill tier if it has no rating. New at Five-O Poker
    and for Five-Card Draw discards. Blind Man's Bluff has no career rating, so it still uses the skill tier.
  - Reads: NPCs watch every public action and showdown, the more skilled ones use what they see for advanced
    strategy, and they track your habits. New at Five-O Poker and Blind Man's Bluff.
  - Rival learning (career mode): rivals remember what they saw you do across sessions. Now also at Five-O Poker
    and Blind Man's Bluff (saves can hold the two new games; older saves load unchanged). An all-in NPC keeps
    learning from the hand it is still playing.
  - One betting round counts as a final round. Pessimistic NPCs at Blind Man's Bluff now fold and check less with
    weak cards.
  - Table talk: the same chance to talk after each action as at Hold'em (from 12% after a check up to 72% after
    going all-in, a little more for unpredictable NPCs) and the same kinds of lines. Before: 22% at Blind Man's
    Bluff and 25% at Five-O Poker.
  - Showdown talk (Hold'em, Draw and Stud) follows the new winner rule. An NPC says its "split pot" line only
    when it really shared a pot. Before, any hand with two or more winners counted as a split, so an NPC that
    took a different pot, or only got its own uncalled chips back, could talk about splitting. An NPC that won
    another pot no longer reacts as a loser.
  - Quick Chat after you fold: while you are out of the hand, the lines that sway NPC decisions ("I'm bored",
    "I've got a great hand") are hidden. The social lines stay.

- **Achievements.** Only Texas Hold'em has per-hand achievements; they changed (see its section). The table-clear
  achievement now counts once per session at Hold'em too (B35), as it already did at Draw and Stud.

### Open choices for the designer (every table)

These shared rules were set by default during the sprint and can still change.

- Fold wins return the winner's own uncalled bet.
- A pot only one player could win counts as a win only when that player is up on the hand.
- Winning a contested side pot while losing money on the hand still plays the win sound and highlight; only fans
  need a profit.
- The winner rule also applies to NPC seats.
- Quick Chat after you fold hides the lines that sway NPCs; the social lines stay.
- Blind Man's Bluff short stacks now play all-in instead of sitting out.

## Texas Hold'em

### What changed

- **A new session after busting (B35).**
  Before: if you busted or cleared the table and pressed Return before the 5-second end countdown finished, the
  next Hold'em session could end on its first frame.
  Now: every new session starts with no timers running.
- **Table-clear bonus (B35).**
  Before: the table-clear fans and the tables-cleared achievement count were given once per app run. A second
  table clear in a later session paid nothing.
  Now: once per session, as at Draw and Stud.
- **After you fold.**
  Before: with two or more NPCs left, the rest of the board was dealt at once and the hand went straight to the
  showdown, even if an NPC had just bet and nobody had answered.
  Now: the NPCs play the hand out street by street at the normal NPC and street delays. Next Hand and Return
  appear once they finish. At slow speed with four NPCs, a preflop fold usually means about 30 seconds of
  watching, and up to about 50 (about 20 seconds at normal speed).
- **The bet to call after a short big blind.**
  Before: the smaller amount was used only when the hand was dealt heads-up.
  Now: at any table size, and also when folds leave one player with chips (see Every poker table).
- **Odd chips.**
  Before: the lowest seat, usually you, got them.
  Now: the first tied winner to the dealer's left, dealer last.
- **Payout details recap.**
  - Eligible line (B43): before, a pot won because everyone else folded showed a blank "Eligible:" line. Now it
    names the winner.
  - Uncalled chips have their own "Returned (uncalled):" block ("Uncalled $980 returned to you"). Before, at a
    showdown they showed as a side pot you won, with your hand named ("Side pot 1: $15 — 5-high Straight"); on
    a fold win they were part of the main pot ("Main pot: $1,030 — Everyone else folded"). "You received" still
    counts them, so your net for the hand is unchanged.
  - Folded players' chips no longer show as extra side pots (one $230 main pot instead of $40, $30 and $160).
  - A side pot only one player could win says "Nobody else could win it" instead of naming a winning hand.
  - A fold win reads "Main pot: $50 — Everyone else folded", with the returned chips listed below.
- **Result line.** In "Payouts: You $20; Ada $248 with A-high." a player who only collected a pot nobody else
  could win gets no hand named.
- **Pot achievements.**
  Before: Four-Figure Pot ($1,000 from a single pot) and Monster Pot ($25,000) looked at the total of every pot
  you were paid in the hand, your own uncalled chips included. The $1,000 shove the blinds fold to counted as a
  $1,030 pot.
  Now: they count your share of the largest single pot you won. Table Profit adds your pot winnings, without
  returned chips. First Pot, Ten Pots, Table Regular, Centurion, Straight Flush and Royal Flush count only hands
  you won under the new winner rule.
- **Chat and controls at session start.**
  Before: the CHAT tab still held the last session's messages. A new session could also open with a half-typed
  bet amount, a bet slider still being dragged or the Quick Chat menu open.
  Now: all of that is cleared.
- **All-table rules that change something here:** NPCs can no longer bet into players who are all all-in;
  several short all-ins can re-open the betting; uncalled chips are returned, also on fold wins ("You win $50.");
  folded players' chips no longer make extra side pots, and chips no live player paid into are no longer lost;
  fans are paid on your net; the new winner rule; while you are folded, Quick Chat hides the lines that sway
  NPCs.

### What stayed the same on purpose

- Blinds: small blind 1% of the buy-in, big blind twice that.
- Position labels the NPCs use (blinds, button, cutoff).
- The automatic next deal and the 5-second end-of-session countdown.
- At showdown every live hand is shown, in seat order; nobody mucks.

### Open choices for the designer

- After you fold, NPCs play out at the normal delays (usually about 30 s at slow speed, up to about 50 s); a
  spectator fast-forward could be added.
- Fold wins return the winner's own uncalled bet ("Uncalled $980 returned to you. You win $50."); it used to say
  "You win $1,030".
- Winning a contested side pot (one another player could also win) while losing money on the hand still plays
  the win sound and highlight; only fans need a profit.
- The winner rule also applies to NPC seats (the winner highlight, the payout chips and the hand history).
- The NPC "shown weak" read here goes by the hand shown (high card or one pair), not by who won.
- Quick Chat after you fold hides the lines that sway NPCs; the social lines stay.
- Only Hold'em shows the Payout details recap.

## Five-Card Draw

### What changed

- **The deck runs out during the draw (B41).**
  Before: when the deck was empty, a discarded card silently stayed in the hand, and the log still said the
  player drew the full number of cards.
  Now: the cards already thrown away in this draw are shuffled into a new deck ("The deck is empty; the discards
  are shuffled in."). A player's discards join that pile only after the player has drawn, so nobody gets their
  own cards straight back. If even that pile is empty, the player keeps the old card and the log says so ("The
  deck ran out: Ada keeps 1 card."). The seat shows the number of cards actually drawn. With you and four NPCs
  the draw needs at most 46 of the 52 cards (25 dealt, up to 5 for you and up to 4 for each NPC, which always
  keeps a card), so this cannot happen at today's table.
- **The bet to call after a short big blind (B39).**
  Before: always the full big blind. In the example above (big blind all-in for $5, everyone else folds) you had
  to call $10 more or fold.
  Now: you are not asked to call. The draw still happens and you choose your discards as usual. There is no more
  betting, and at the showdown your extra $5 comes back. If the big blind had put in more than your small blind
  (say all-in for $15), you would call only the $5 difference instead of $10.
- **Odd chips.**
  Before: the dealer got the first odd chip if tied, then the players from the dealer's left.
  Now: the first tied winner to the dealer's left, dealer last.
- **NPC discards** now use the same skill as the NPC's betting: its Five-Card Draw career rating.
  Before: only its skill tier. Only NPCs with a Draw rating play differently.
- **All-table rules that change something here:** NPCs can no longer bet into players who are all all-in;
  several short all-ins can re-open the betting; uncalled chips are returned, also on fold wins; folded players'
  chips no longer make extra side pots, and chips no live player paid into are no longer lost; fans are paid on
  your net (before: on every pot in the hand); the new winner rule; Quick Chat starts empty each session; while
  you are folded, Quick Chat hides the lines that sway NPCs.

### What stayed the same on purpose

- The draw: NPCs draw at once, and if you are all-in you still choose your discards (the draw is not a bet).
- Blinds: 1% and 2% of the buy-in, as at Hold'em.
- NPC boldness from cash on hand is toned down (x0.80) before the draw, when less is known.
- Position labels (blinds, button, cutoff).
- The automatic next deal and the 5-second end-of-session countdown.
- At showdown every live hand is shown, in seat order; nobody mucks.

### Open choices for the designer

- Fold wins return the winner's own uncalled bet; stacks end the same.
- Winning a contested side pot (one another player could also win) while losing money on the hand still plays
  the win sound and highlight; only fans need a profit.
- The winner rule also applies to NPC seats (the winner highlight, the payout chips and the hand history).
- The NPC "shown weak" read here goes by the hand shown (high card or one pair), not by who won.
- Quick Chat after you fold hides the lines that sway NPCs; the social lines stay.
- Draw could show the Payout details recap too; today only Hold'em does.

## Seven-Card Stud

### What changed

- **The bring-in when the lowest card has no chips left (B40).**
  Example: Ada has exactly $2, antes it and is all-in, and has the lowest door card.
  Before: Ada was given the bring-in but could not post it, and the next player still faced a $5 bet nobody had
  made.
  Now: the bring-in goes to the next-lowest door card that has chips ("Bo posts the bring-in $5."). If only one
  player still has chips (for example heads-up against an NPC that antes its last chips), that player posts the
  bring-in whatever its door card, and it comes straight back ("You post the bring-in $5." ... "Uncalled $5
  returned to you."). Only if nobody has chips does it stay on the lowest card, and the hand runs out.
- **The bet to call after a short bring-in (B39).**
  Example: the low card has only $3 left after the ante and brings it in for $3, all-in.
  Before: everyone had to call the full $5.
  Now: while two or more other players can act, the call is still $5. Once only one player with chips is left
  against it (for example after the others fold), that player calls $3.
- **Fixed-limit betting with short all-ins.**
  - Before: a short all-in raise used up one of the three raises allowed per round. Example on Fourth Street:
    Ada bets $10, Bo raises to $20, Cy is all-in for $24. Cy's all-in was counted as the second raise.
    Now: only full raises count, so only Bo's raise is counted.
  - Unchanged: short all-ins never re-open the betting for players who already acted, even when several add up
    to a full bet. (Hold'em, Draw and Blind Man's Bluff now re-open in that case.)
  - Completing the bring-in after a short all-in. Example: Ada brings it in for $5, Bo is all-in for $8, and you
    complete to $10. Before: your completion counted as a $2 raise, so Ada and anyone who had called $5 could only
    call. Now: completing to the small bet is a full bet, and they may raise.
- **Pot display and hand log.**
  Before: after a showdown the table showed "Pot: $0" (or the pot of an earlier hand won by a fold). The payout
  chips did not fly to the winner (or were sized from that old pot), and career fans for a showdown win were
  based on that same figure ($1 when it read $0). The hand log also listed a "Main pot" or "Side pot" line for
  every layer of folded players' chips, even when there was no real side pot.
  Now: the pot shows what was settled, the payout chips fly to the winners after every showdown, fans follow the
  net rule, and pot lines appear only for real side pots, with the winning hand.
- **Speech bubbles.**
  Before: NPC speech bubbles showed even with Table Chat Pop-ups turned off.
  Now: they are hidden when it is off, as at Hold'em and Draw. The chat log still gets every line.
- **Odd chips.**
  Before: the dealer got the first odd chip if tied.
  Now: the first tied winner to the dealer's left, dealer last. Stud shows no dealer button: the dealer is a
  hidden marker that moves one seat to the left each hand, and the first card of each deal goes to the player on
  its left.
- **All-table rules that change something here:** NPCs can no longer bet into players who are all all-in;
  uncalled chips are returned, also on fold wins; folded players' chips no longer make extra side pots, and chips
  no live player paid into are no longer lost; fans are paid on your net; the new winner rule; Quick Chat starts
  empty each session; while you are folded, Quick Chat hides the lines that sway NPCs (before, every line was
  offered).

### What stayed the same on purpose

- Antes, the bring-in by the lowest door card, fixed-limit betting (small bet on Third and Fourth Street, big bet
  on Fifth to Seventh), completing the bring-in, the 3-raise cap, and first to act by the best exposed hand.
  This is the traditional Seven-Card Stud structure.
- Stakes: the small bet is 1% of the buy-in; the ante is 20% and the bring-in 50% of the small bet.
- NPC boldness from cash on hand is scaled by street, from 0.45 on Third Street to 0.85 on Seventh.
- No position labels (Stud acts by the exposed cards).
- The automatic next deal and the 5-second end-of-session countdown.
- At showdown every live hand is shown, all seven cards, in seat order; nobody mucks.

### Open choices for the designer

- Short all-ins never re-open the betting and never count toward the 3-raise cap. The tournament limit rule (an
  all-in of at least half a bet re-opens) is not used.
- When the lowest card is all-in, the bring-in goes to the next-lowest card that can post. The usual casino rule
  gives it to the player on the all-in player's left; the two can differ whenever two or more other players
  still have chips.
- Fold wins return the winner's own uncalled bet; stacks end the same.
- Winning a contested side pot (one another player could also win) while losing money on the hand still plays
  the win sound and highlight; only fans need a profit.
- The winner rule also applies to NPC seats (the winner highlight, the payout chips and the hand history).
- The NPC "shown weak" read here goes by the hand shown (high card or one pair), not by who won.
- Quick Chat after you fold hides the lines that sway NPCs; the social lines stay.
- Stud could show the Payout details recap too; today only Hold'em does.

## Five-O Poker

### What changed

- **The NPC may raise.**
  Before: facing your bet, the NPC could only call or fold.
  Now: it may raise on the same terms as you, to the table's one bet size, up to 3 raises in the round. Example
  with the 1/2 POT preset: you bet $20, and the NPC may raise to $40. The prompt says "Call, raise or fold." only
  when you can raise, otherwise "Call or fold." (before, an NPC's opening bet always said "Call or fold.", even
  when you could raise, and its bet after you checked always said "Call, raise or fold.", even when that bet used
  up the smaller stack and there was no raise button).
- **NPC thinking time.**
  Before: the NPC always answered after 0.65 s, whatever the Table Speed, and made its opening bet instantly.
  Now: it waits the Table Speed delay (1.8 / 1.2 / 0.6 s) for every betting decision. Its opening bet now waits
  too, and shows "<name> is considering the action…" as its other decisions already did. Card placements are
  still instant. Table Speed is set in the Options of the Hold'em, Draw or Stud table; Five-O's own Options has
  only Column reveal and Column sounds.
- **Bet-size buttons are locked while the NPC thinks.**
  The NPC sizes its bets from the preset you last picked (1/4 POT, 1/2 POT, POT, MAX).
  Before: you could change the size of the bet the NPC was about to make.
  Now: the buttons are greyed out until it has acted.
- **What the NPC decides from.**
  Before: personality traits, its skill tier, cash-on-hand boldness, Quick Chat effects and a simple grudge.
  Now also: skill from its Five-O career rating (for betting and for choosing columns), reads of your play with
  advanced strategy for the more skilled NPCs, memory of your habits, and career rival learning.
- **Grudges.**
  Before: a grudge was recorded only when you won a showdown, always the same amount (0.55 for the most bitter
  NPC).
  Now: as at every table, it is recorded when the NPC loses a contested showdown (not a split, not a fold). Each
  loss adds a fixed part plus a part set by the chips the NPC put in divided by the buy-in. For the most bitter
  NPC, a $50 hand at a $1,000 buy-in now adds 0.33, and a hand where it put in more than half the buy-in (for
  example after a MAX bet) adds more than before, up to 0.80.
- **Fold wins.**
  Before: "Ada folds. You win $40." (both antes of $10 plus your $20 bet).
  Now: "Ada folds. You win $20 (uncalled $20 returned)." Your stack ends the same.
- **Quitting in the middle of a hand.**
  Before: if you pressed Quit and Cash Out while the NPC was still thinking about your bet, it got the whole pot,
  your unanswered bet included ("You fold. Ada wins $40."; with a $20 bet you left with $970).
  Now: your unanswered bet comes back and only the matched chips are lost ("You fold. Ada wins $20. Uncalled $20
  returned to you."; you leave with $990).
- **Odd chips.**
  Before: on a split pot the NPC got the odd chip.
  Now: the player who acts first that hand gets it (this alternates hand by hand), even if that player only
  checked. Five-O pots are always even in practice, so nothing changes in play.
- **NPC table talk is shown.**
  Before: the NPC's talk was worked out but never shown.
  Now: it appears in the chat strip at the bottom left as "Name: line". The NPC Table Chat setting (in the
  Options of the Hold'em, Draw or Stud table) turns it on or off; Table Chat Pop-ups does not affect it. The strip
  also stays visible during the column reveal.
- **Quick Chat starts empty each session** (menu closed, no replies left over).

### What stayed the same on purpose

- The column structure: heads-up; five columns, each with its fourth card face down; one betting round; one bet
  size worked out from the pot and capped at the smaller stack (a bet can put a player all-in, but it can always
  be called in full, so there are no uncalled chips at a showdown and no side pots); winning 3 of the 5 columns
  takes the pot, otherwise it is split; the columns are revealed one by one.
- The full ante: when either player has less than the ante, the session ends.
- Ante: 1% of the buy-in, at least $5.
- Next Hand and Cash Out are pressed by hand; there is no automatic deal.
- There is no hand-win sound.

### Open choices for the designer

- Fold wins return the winner's own uncalled bet ("(uncalled $20 returned)"); stacks end the same as before,
  except when you quit mid-hand (above).
- Five-O's one pot is always contested, so the winner rule changes nothing here.
- The NPC "shown weak" read here means the seat won nothing.
- Five-O has no hand-win sound.
- The NPC's bet and raise size is the bet-size preset you last picked; the presets are locked while it thinks.
- Seeded runs: the NPC now draws random numbers when it weighs a raise, and its talk changed, so a replay
  recorded before the sprint goes differently from the NPC's first answer to a bet or its first line of talk,
  often by the second hand's deal. In career, an NPC with a Five-O rating can also place its cards differently
  from the first hand.

## Blind Man's Bluff

### What changed

- **Short stacks play all-in.**
  Before: a player with less than the ante sat the hand out. When you, or every NPC, had less than the ante, the
  session was over: Next Hand was greyed out and you could only cash out.
  Now: everyone with chips is dealt in. A short player antes all it has and plays the hand all-in, with a side
  pot for the rest. The session ends only when you or every NPC has $0. Example: you have $5 and the ante is $8.
  You ante $5 and can win $5 from each player (a $20 main pot); the other $9 of antes form a side pot for the
  NPCs.
- **NPCs take their time.**
  Before: every NPC turn happened instantly.
  Now: each NPC waits the Table Speed delay, the table shows "<name> is thinking…", and your buttons wait until
  it is your turn.
- **What NPCs decide from.**
  Before: personality traits, the skill tier, Quick Chat effects, grudges, and its own stack as at every table
  (how big a call is next to it, and the short-stack rule). A stack grown past the buy-in had no effect.
  Now also: cash on hand (bolder above 1.15 times the buy-in; an NPC with more than the buy-in keeps its own bets
  to a soft cap of the buy-in, up to 1.5 times the buy-in when very rich; it is a habit, not a table limit),
  reads of every player with advanced strategy for the more skilled NPCs, memory of your habits, and career
  rival learning. The more skilled NPCs do not bet or raise more than the deepest live opponent can match
  (before, any NPC could bet its whole stack and get the unmatched part back). Pessimistic NPCs fold and check
  less with weak cards, because the single round now counts as a final round. Skill still comes from the skill
  tier (there is no Blind Man's Bluff rating).
- **Odd chips.**
  Before: the lowest seat, usually you, got them.
  Now: the player with the opening action (named on the "Opening action" badge) gets the first, even if it only
  checked, then round the table.
- **Won, tied and lost counts.**
  Before: a hand counted as a tie whenever you and another player each won a pot. So winning the main pot while
  another player won a side pot was a tie, and so was losing the main pot while collecting a side pot only you
  could win, even when you lost money on the hand.
  Now: the shared winner rule (see Every poker table). The first case is a win; the second is a loss, or a win if
  you are up on the hand. The counts matter: a session counts as won when you finish up on chips or win more
  hands than you lose.
- **Re-opening the betting.** Several short all-ins that add up to a full raise now let a player who already
  acted raise again (before: call or fold only).
- **The stake line and prompts.**
  - When your stack is short of a full raise: "Bet $300 • All-in raise to $380", matching the button.
  - On your turn, when you may not raise, the line shows only "Bet $40" (no "Minimum raise to ..." after it).
  - "Ante $8" alone when it is not your turn to open. Before, the line could read "Open $0-$0" after the hand.
  - Raising is named only when you may raise: "Call $40 or fold blind." Before, the prompt always offered a raise.
- **Fold wins.**
  Before: "You wins $48 after the folds." (four antes of $8 plus your uncalled $16 bet, the 1/2 POT button).
  Now: "You win $32 after the folds. Uncalled $16 returned to you." Your stack ends the same.
- **Showdown result.** "Payouts:" lists only pot winnings, followed by "Uncalled $N returned to Name." for
  chips nobody matched. Before, returned chips were silently added to the payout amounts, or not mentioned.
- **Win sound.** Chips that only come back to you (or a pot nobody else could win, collected while losing
  money) play the chip sound, not the win sound.
- **Quick Chat starts empty each session** (menu closed, no replies left over).
- **All-table rules that change something here:** an NPC's grudge presses only on the last player who made a
  full bet or raise (before, a short all-in counted); NPCs talk as often as at Hold'em (before: 22% after any
  action); while you are out of the hand, Quick Chat hides the lines that sway NPCs.

### What stayed the same on purpose

- The single card: the highest rank wins, suits never break ties, there is one betting round, and you see every
  card except your own.
- Ante: 0.8% of the buy-in, at least $5. The smallest opening bet is 1% of the buy-in, and never less than the
  ante.
- Next Hand and Cash Out are pressed by hand; there is no automatic deal.

### Open choices for the designer

- Short stacks now play all-in on a short ante instead of sitting out, and the session ends only at $0.
- Fold wins return the winner's own uncalled bet; stacks end the same.
- Winning a contested side pot (one another player could also win) while losing money on the hand still plays
  the win sound and highlight, and counts as a won hand (before: a tie). That can make the session count as won.
- The winner rule also applies to NPC seats (gold border, the "shown weak" read).
- The NPC "shown weak" read here means a seat that bet or raised was not a winner of the hand. A seat that only
  collected a side pot nobody else could win, while losing money, counts as weak too.
- Quick Chat after you fold hides the lines that sway NPCs; the social lines stay.
- Seeded runs: NPCs now decide from more inputs and talk at a different rate, so a seeded replay recorded before
  the sprint plays differently from the first NPC decision or talk line that differs (often in the first hand
  or two), and deals differently after that.

## Online play

Since Phase 11 the multiplayer app has no copies of the poker rules left. LAN play and the offline practice table
are gone; what remains is online rooms.

### Texas Hold'em rooms

- **Shared with the single-player table:** a room plays on the same Hold'em engine, so every rule in "Every poker
  table" and "Texas Hold'em" above applies, including:
  - the bet to call after a short all-in blind;
  - no bet or raise that nobody can answer. The host refuses it for guests too, and a guest's Raise button stays
    off. Before, the host and the guests could raise when everyone else left was all-in;
  - minimum raises, and short all-ins that together re-open the betting;
  - uncalled chips come back and are not won, and folded players' chips join the pot they were paid into
    instead of making extra side pots (for example one $4,025 pot instead of $100, $1,725 and $2,200 pots);
  - odd chips to the first winner left of the dealer, and the same rule for who counts as a winner.
- **Fold wins.** A fold win settles like a showdown with one player left. Example: a guest raises to $150 and
  everyone folds. "Last pot" and the Payout History now show a $125 main pot, and the Payout History adds
  "Returned (uncalled): Uncalled $100 returned to Guest 3". Before: a $225 pot. The guest's stack ends the same.
- **A short blind plays.** A seat whose blind puts it all in now plays the hand and can win the pots it paid
  into. Before, it was shown as busted for the whole hand, left out of every pot, and lost its blind.
- **NPCs** in a room decide with the single-player NPC code, including its short-stack rule: a stubborn NPC with
  a short stack folds less (in one measured spot, from 66% to 38% of the time). Layered NPC portraits gain the
  outline layer that single-player draws.
- **Stays room-specific:**
  - up to six people, with NPCs in the other seats; the host chooses the starting stack ($1,000 to $25,000) and
    the table speed;
  - the room's own chat instead of Quick Chat, so nothing nudges the NPCs;
  - the 6-second pause before the next hand. Each player's screen now counts it down on its own clock, so the
    countdown no longer makes a guest's action arrive "too late";
  - buying back in for the starting stack, a busted NPC replaced by a new one, sitting out, a busted host
    spectating (no empty "You are dealt" line any more), and a player who left the room folded automatically
    on their turn;
  - a late joiner takes a knocked-out NPC's seat first and buys in for the starting stack. Only when every NPC
    still has chips does the joiner take over an NPC's seat and its stack, as before;
  - the room's Payout History, not the single-player recap. Its footnote now reads "Amounts above are gross
    payouts and returned uncalled bets; your own wagers were already deducted.";
  - multiplayer XP. A pot gives XP only if someone other than its winners paid into it, so returned chips, or a
    pot two players split from only their own chips, give none. A pot that holds a folded player's chips still
    does.

### Blind Man's Bluff rooms

- **Shared with single-player Blind Man's Bluff:**
  - uncalled chips come back, and so does a layer that only folded players paid into;
  - a fold win: the survivor wins the matched chips and gets its uncalled bet back;
  - odd chips go to the player with the opening action first, then round the table;
  - nobody may bet or raise unless another player still in the hand has chips to answer, and several short
    all-ins that add up to a full raise re-open the betting. The Raise button follows the host's rule;
  - who won the hand, and the win sound only for winners (returned chips are not a win).
- **Short stacks.** A raise from a stack too short for the minimum raise is an all-in for what it has, and an
  amount that does not beat the bet is a call. Before, it was recorded wrongly.
- **Stays room-specific:**
  - four seats, and the room's own ante (0.8% of the starting stack, at least $5) and bet unit (2%, at least $10);
  - a seat with less than the ante watches the hand instead of playing it all-in. When fewer than two seats can
    ante, the table shows "Table finished";
  - the room's NPCs use their own simpler decisions, not the single-player NPC code;
  - the next hand is dealt automatically a few seconds after the result;
  - a player who leaves the room on their turn checks, or folds when they owe chips, after a short pause. Their
    seat keeps being dealt in and paying antes until a newcomer takes it or it can no longer pay the ante;
  - players who join during a hand sit down at the next hand. They buy in for the starting stack in an empty or
    broke seat; otherwise they play on with the chips of the seat they take.

## Not rule changes

These changed what you see, not the rules.

- Game log (Hold'em, Draw, Stud): a line too long to show at a readable size (a split pot or a long side-pot or
  payout line) now wraps onto extra rows instead of being squashed or running out of the panel. A line that is
  only a little too wide still shrinks onto one row, exactly as before. The mouse wheel scrolls one row at a
  time, and text no longer spills out of the panel.
- Hand history wording: "Main pot $150: You win. Winning hand: A-high. You receive $150." (was "You wins ...
  Each receives"); "split between you and Ada ... Each winner receives $10 (odd chip to Ada)" (was "(plus odd
  chips in seat order)"); "Side pot 1 $200: nobody else could win it; Ada collects $200." Draw and Stud pot
  lines now name the winning hand, as Hold'em's did.
- Payout details recap (Hold'em): lines under each pot stay indented, a heading never ends a page, and a pot
  split by a page break repeats its heading as "(continued)" on the next page.
- Five-O Poker: a two-row hand result moves up to stay clear of the chat strip. Blind Man's Bluff: a long result
  wraps onto two rows, and the hint is shorter ("Everyone else can see your card. Read their betting.").
- Fonts are made once and reused instead of every frame (B44); the tables look the same.
- Hold'em: the debug keys F7, Space and B no longer work at the table (D1).

## Where the rules live

- `solitaireplus/games/poker/core.py`: the shared table rules (hand ranking, the bet to call after a short blind
  or bring-in, raising and re-opening, pots, refunds, fold wins, odd chips, who won, when a session is over).
  Each engine posts its own blinds, antes and bring-in. Five-O Poker keeps its own session-end rule.
- `solitaireplus/games/poker/holdem.py`: the Hold'em engine. Five-Card Draw and Seven-Card Stud are built on it
  and share its betting, showdown and fold-win code; each game's own structure is in `five_card_draw.py`,
  `seven_card_stud.py`, `five_o.py` and `blind_mans_bluff.py`. The engine's class is built from topic modules:
  `holdem_seats.py` (blinds, seat order, whose turn it is), `holdem_betting.py` (the betting rules and the
  player's actions), `holdem_npc.py` (NPC actions and bet sizing), `holdem_pots.py` (side pots, pot awards,
  fold wins) and `holdem_showdown.py` (the showdown); `holdem.py` keeps the session, the hand flow and the deal.
- `solitaireplus/games/poker/npc_inputs.py`: what every NPC decides from (cash on hand, skill, grudges, reads,
  rival learning); grudges are recorded in `solitaireplus/npc/personality.py`.
- `solitaireplus/games/poker/recap.py` (the payout recap and the net used for fans), `table_timers.py` (table
  timers), `log_rows.py` (log wrapping) and `holdem_chat.py` (how often NPCs talk, showdown talk).
- `solitaireplus/games/poker/ai.py` and `strategy.py` (how NPCs use their inputs; a single betting round counts
  as a final round), `quick_chat.py` (which Quick Chat lines show while you are out of the hand),
  `variant_quick_chat.py` (the Quick Chat reset at Draw, Stud, Five-O Poker and Blind Man's Bluff) and
  `holdem_ui_options.py` (the Table Speed delay every table uses; `holdem_ui.py` re-exports it).
- `solitaireplus/profile/achievements.py`: the Hold'em pot achievements.
- Technical audit and designer choices: [dev/B86_POKER_AUDIT.md](dev/B86_POKER_AUDIT.md).
