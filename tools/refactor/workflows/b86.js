export const meta = {
  name: 'b86-poker-alignment',
  description: 'B86: audit the poker variants, unify the shared rules (incl. B36-B39, B42) and NPC behaviour, test every rule against every variant, adversarially review',
  phases: [
    { title: 'Audit', detail: 'rule-by-variant table with file:line' },
    { title: 'Design', detail: 'shared functions in games/poker/core.py' },
    { title: 'Implement', detail: 'one rule group at a time (sequential: same files)' },
    { title: 'Review', detail: 'independent lenses: rules, chips, NPCs, flow' },
    { title: 'Repair', detail: 'fix what the reviews confirm' },
  ],
}

const CONTEXT = `
Repository: C:\\Users\\Dan Fiscus\\Documents\\SolitairePlus (Windows; Bash = Git Bash; PowerShell available).
Git: prefix git commands with GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=safe.directory GIT_CONFIG_VALUE_0='*'. Never change global git config. Never commit.
Python: .venv\\Scripts\\python.exe. One test file: .venv\\Scripts\\python.exe tools\\run_tests.py --worker game <stem>
Brief: docs/dev/RESTRUCTURE_BRIEF.md section 8 "Phase 7: Poker" (B36, B37, B38, B39, B42, B86). Its line numbers refer to the OLD layout; find code by name.
Poker code: engines solitaireplus/games/poker/holdem.py (TexasHoldemGame), five_card_draw.py, seven_card_stud.py, five_o.py, blind_mans_bluff.py, niche_common.py; shared core.py (hand evaluation, PokerHandHistory, formatting), strategy.py (PokerTableReads, NPC strategy), ai.py (NPC decisions), learning.py (rival learning store), recap.py; NPC personalities solitaireplus/npc/personality.py (traits, PokerGrudgeMemory) and personality_chat.py; screens games/poker/holdem_screen.py, five_card_draw_screen.py, seven_card_stud_screen.py, five_o_screen.py, blind_mans_bluff_screen.py. Multiplayer Hold'em is multiplayer/texas_holdem.py (+ multiplayer/poker_ai.py): AUDIT it, but do NOT edit anything under multiplayer/ (Phase 11 merges it onto the shared engine).
Designer decisions (Dan, 2026-11-15): fix odd chips everywhere (B38): odd chips go one at a time starting at the first eligible winner left of the dealer, one shared function in core.py used by every variant. Align all poker variants (B86) - unify the shared rules, keep deliberate differences (Stud's bring-in, Blind Man's Bluff's single card, Five-O's column structure). The original maintainer added: "NPC behavior should be consistent between all variants, including holding grudges and behaving differently based on the amount of cash on hand."
Rules: no 'global' statements in solitaireplus/; keep each variant's visible behaviour unchanged except where a rule is unified or a listed bug fixed; every unified rule gets a test run against every variant through a small adapter; chip conservation: property-style, 1,000 random hands per variant (seeded), total chips constant. Don't run the whole suite; run the poker test files (grep tests/ for poker, holdem, draw, stud, five_o, bluff, recap, strategy, rival).
`

const AUDIT = {
  type: 'object',
  properties: {
    table_markdown: { type: 'string', description: 'markdown table: rows = rules, columns = Hold\'em, Draw, Stud, Five-O, Blind Man\'s Bluff, multiplayer Hold\'em; each cell = current behaviour + file:line' },
    unify: { type: 'array', items: { type: 'object', properties: { rule: { type: 'string' }, target: { type: 'string', description: 'the unified behaviour' }, variants_changing: { type: 'array', items: { type: 'string' } }, bug_ids: { type: 'array', items: { type: 'string' } } }, required: ['rule', 'target', 'variants_changing', 'bug_ids'] } },
    keep_different: { type: 'array', items: { type: 'object', properties: { rule: { type: 'string' }, why: { type: 'string' } }, required: ['rule', 'why'] } },
  },
  required: ['table_markdown', 'unify', 'keep_different'],
}

const audit = await agent(`${CONTEXT}
YOUR TASK (B86 step 1, AUDIT, do not edit any file): read the engines and build the audit table the brief asks for: one row per shared rule, one column per variant (Hold'em, Five-Card Draw, Seven-Card Stud, Five-O, Blind Man's Bluff, multiplayer Hold'em), each cell = current behaviour + file:line. Rows: forced bets (blinds, antes, bring-in) when a player can't cover them; current_bet after a short all-in forced bet; minimum raise and minimum re-raise; raise allowed when <= 1 player can still act (player AND NPC); side-pot building incl. layers with no eligible player; odd-chip distribution; ties and split pots; showdown order and mucking; all-in run-outs (dealing remaining streets/draws without betting); busted players (sit out / removed / rebuy); session start and end resets (timers, logs, quick chat, learning store); NPC action timing and delays; hand evaluation (same evaluator for the same hand type); PLUS, per the maintainer: NPC grudges (PokerGrudgeMemory or similar: which variants record and use them), NPC behaviour by cash on hand (stack-size/short-stack/tenacity logic, which variants apply it), NPC personality traits and rival learning use. Then list the differences to unify (the target behaviour, which variants change, related bug ids B36/B37/B38/B39/B42) and the deliberate differences to keep (with why).`,
  { label: 'audit', phase: 'Audit', schema: AUDIT })

const DESIGN = {
  type: 'object',
  properties: {
    plan_markdown: { type: 'string' },
    groups: { type: 'array', items: { type: 'object', properties: { key: { type: 'string' }, instructions: { type: 'string' } }, required: ['key', 'instructions'] } },
  },
  required: ['plan_markdown', 'groups'],
}

const design = await agent(`${CONTEXT}
YOUR TASK (B86 step 2, DESIGN, do not edit any file): from this audit, design the unification. For each rule to unify, define ONE shared function in solitaireplus/games/poker/core.py (or a new games/poker/rules.py if core.py should stay about cards/evaluation - decide and say why), its signature and exact semantics, and how each variant engine calls it. Cover: forced bets vs short stacks + current_bet after a short all-in (B39), raise guard when <= 1 player can act for player and NPC (B36), side-pot builder incl. layers with no eligible player - return those chips to their contributors (B37), odd-chip split starting left of the dealer (B38) incl. Blind Man's Bluff refund remainder and its tie counting (B42), ties/split pots, run-outs, session resets; and NPC behaviour consistency (grudges, cash-on-hand behaviour, traits, rival learning) so every variant's NPCs use the same shared decision inputs. Split the work into 4-7 sequential implementation groups (each self-contained, with tests to write). Audit:
${JSON.stringify(audit)}`,
  { label: 'design', phase: 'Design', schema: DESIGN })

const IMPL = {
  type: 'object',
  properties: { key: { type: 'string' }, files_changed: { type: 'array', items: { type: 'string' } }, tests_added: { type: 'array', items: { type: 'string' } }, tests_pass: { type: 'boolean' }, behaviour_changes: { type: 'string' }, notes: { type: 'string' } },
  required: ['key', 'files_changed', 'tests_added', 'tests_pass', 'behaviour_changes', 'notes'],
}

const done = []
for (const group of design.groups) {
  const result = await agent(`${CONTEXT}
YOUR TASK (B86 step 3, IMPLEMENT group "${group.key}"): ${group.instructions}
Overall plan:\n${design.plan_markdown}
Groups already done (their changes are in the checkout): ${JSON.stringify(done)}
Write the tests first (they must fail on the current code where a bug is involved), implement, run the poker test files. Edit with the Edit tool; never rewrite whole files; re-read before editing.`,
    { label: `impl:${group.key}`, phase: 'Implement', schema: IMPL })
  done.push(result)
}

const VERDICT = {
  type: 'object',
  properties: { lens: { type: 'string' }, problems: { type: 'array', items: { type: 'object', properties: { what: { type: 'string' }, where: { type: 'string' }, severity: { type: 'string' } }, required: ['what', 'where', 'severity'] } }, notes: { type: 'string' } },
  required: ['lens', 'problems', 'notes'],
}
const LENSES = [
  'poker rules correctness (forced bets, raises, side pots, odd chips, ties) against standard rules and the design',
  'chip conservation and money flow (career/sandbox cash in and out of sessions, payouts, refunds)',
  'NPC behaviour (decisions, grudges, cash-on-hand behaviour, learning) - regressions and inconsistencies between variants',
  'game flow and UI (session start/end, recaps, timers, screens still showing the right things), plus tests that do not really test the rule',
]
const reviews = await parallel(LENSES.map((lens) => () => agent(`${CONTEXT}
YOUR TASK (B86 step 4, REVIEW, do not edit files): review the whole B86 change (git diff of solitaireplus/games/poker/, solitaireplus/npc/ and the new tests) through this lens: ${lens}. Run the poker tests. Report concrete problems with file:line and severity (high/medium/low). Default to reporting a problem when unsure. Design:\n${design.plan_markdown}\nImplementation reports: ${JSON.stringify(done)}`,
  { label: `review:${lens.split(' ')[0]}`, phase: 'Review', schema: VERDICT })))

const problems = reviews.filter(Boolean).flatMap((r) => r.problems.filter((p) => p.severity !== 'low').map((p) => ({ ...p, lens: r.lens })))
let repair = null
if (problems.length) {
  repair = await agent(`${CONTEXT}
YOUR TASK (B86 step 5, REPAIR): independent reviewers reported these problems with the B86 change. Verify each one; fix the real ones (with a test each); explain why the others are not problems. Run the poker tests afterwards.
${JSON.stringify(problems)}`,
    { label: 'repair', phase: 'Repair', schema: IMPL })
}
return { audit, design, done, reviews, repair }
