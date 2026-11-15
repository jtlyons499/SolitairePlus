export const meta = {
  name: 'phase-fixes',
  description: 'Fix one restructure phase\'s bugs (test first), each fix adversarially reviewed',
  phases: [
    { title: 'Fix', detail: 'one agent per bug, test first' },
    { title: 'Review', detail: 'adversarial review of each fix' },
  ],
}

// args: { phase: 'Phase 3', layout: '<text describing where the area code lives now>', tasks: [{key, prompt}] }
const CONTEXT = `
Repository: C:\\Users\\Dan Fiscus\\Documents\\SolitairePlus (Windows; Bash tool = Git Bash; PowerShell also available).
Git refuses this repo ("dubious ownership") unless git commands are prefixed with: GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=safe.directory GIT_CONFIG_VALUE_0='*'   Never change global git config. Never commit.
Python: .venv\\Scripts\\python.exe (pygame-ce 2.5.8). Run one test file:  .venv\\Scripts\\python.exe tools\\run_tests.py --worker game <test_file_stem>
The bug list is docs/dev/RESTRUCTURE_BRIEF.md section 8 (${args.phase}). Its line numbers refer to the OLD main.py (commit 154b890): find code by function/variable names.
Code layout now:
- solitaireplus/app/state.py: shared variables (state.name). state_names.py: STATE_* constants. app/loop.py: main loop + SCREENS registry (screen modules have handle_event(event), draw(), optional update(now), late_update(), enter(), leave()).
- solitaireplus/legacy.py: old main.py code not yet moved. app/window.py, app/fonts.py, app/sounds.py ('audio'), app/assets.py, ui/buttons.py, ui/text.py (alias ui_text; get_font() font cache: use it instead of creating fonts in drawing code), ui/panels.py, ui/backgrounds.py, ui/cursors.py.
${args.layout}
- tests/support/locate.py finds functions anywhere in main.py + solitaireplus/** (locate.function_node, locate.exec_functions(names, env) with automatic stand-ins for state/fonts/... backed by env, locate.namespace(env, nodes)).
- tools/screen_harness.py renders screens headless: .venv\\Scripts\\python.exe tools\\screen_harness.py render --scene NAME --jobs 1 --out .harness_out/<yourdir> (list scenes with: list). Look at the PNG when your fix changes a screen.
Working rules (other agents fix other bugs in this same checkout right now):
- Touch only what your bug needs. Edit with the Edit tool (exact replacement); never rewrite whole existing files or run formatters; re-read a file right before editing it.
- No 'global' statements and no globals() in solitaireplus/ (use state.x for shared state, or a mutable holder for module-private caches).
- Every fix needs a regression test that FAILS before the fix and PASSES after: write it first, run it, see it fail, then fix. Prefer a new tests/test_<topic>.py (unittest style).
- Run only your own test files and existing test files covering the code you changed; never the whole suite or screen_harness compare.
- Minimal, behaviour-preserving apart from the bug; if the intended behaviour is ambiguous, take the conservative choice and say so.
`

const RESULT = {
  type: 'object',
  properties: {
    bugs: { type: 'array', items: { type: 'string' } },
    files_changed: { type: 'array', items: { type: 'string' } },
    tests_added: { type: 'array', items: { type: 'string' } },
    failed_before_fix: { type: 'boolean' },
    passes_after_fix: { type: 'boolean' },
    summary: { type: 'string' },
    visible_changes: { type: 'string', description: 'screens a player would see change (harness scene names if known), or "none"' },
    new_findings: { type: 'array', items: { type: 'string' }, description: 'other bugs noticed but NOT fixed' },
  },
  required: ['bugs', 'files_changed', 'tests_added', 'failed_before_fix', 'passes_after_fix', 'summary', 'visible_changes', 'new_findings'],
}

const VERDICT = {
  type: 'object',
  properties: {
    bugs: { type: 'array', items: { type: 'string' } },
    fixed: { type: 'boolean' },
    regressions: { type: 'array', items: { type: 'string' } },
    test_is_meaningful: { type: 'boolean' },
    tests_pass: { type: 'boolean' },
    notes: { type: 'string' },
  },
  required: ['bugs', 'fixed', 'regressions', 'test_is_meaningful', 'tests_pass', 'notes'],
}

const results = await pipeline(
  args.tasks,
  (task) => agent(`${CONTEXT}\nYOUR TASK (${task.key}):\n${task.prompt}\n\nReturn the structured result.`,
    { label: `fix:${task.key}`, phase: 'Fix', schema: RESULT }),
  (result, task) => agent(`${CONTEXT}\nYOUR TASK: adversarially review the fix for ${task.key} that another agent just made in this checkout. Do NOT edit any file.
Its task:\n${task.prompt}\nIts report: ${JSON.stringify(result)}
1. Read the brief's entry for ${task.key} and the diff of the files it changed (git diff -- <files>; other agents' edits may appear in shared files - judge only the hunks that belong to ${task.key}).
2. Look hard for: paths where the bug still happens; behaviour changed beyond the bug; missed call sites; new crashes or edge cases; 'global' statements; pixel changes on screens that should not change.
3. Judge whether the regression test really fails on the old code and checks the bug itself.
4. Run the test files involved.
Default to reporting a problem when unsure. Return the structured verdict.`,
    { label: `review:${task.key}`, phase: 'Review', schema: VERDICT }),
)
return args.tasks.map((task, index) => ({ task: task.key, review: results[index] }))
