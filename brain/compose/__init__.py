"""Composing a tailored resume from facts, in two AI steps and one plan between them.

    facts.py     the bank as facts: each `## id` block, with its project
    match.py     1. AI: which facts prove each requirement of the offer, how strongly
    plan.py      2. no AI: which facts go where, bullets per entry (the priorities)
    write.py     3. AI: the bullets, in my style (bank/style.md), each citing its facts, checked
    review.py    I accept, edit or rewrite each entry's bullets before they go on the page
    approved.py  the bullets I accepted, reused next time (bank/approved.yaml)
    pipeline.py  compose_resume(): all of the above, then one page

pipeline.compose_resume() runs it all and fits the page; the result is a selection.yaml whose
bullets carry their text and their facts, plus plan.json (for `review` later).
"""
