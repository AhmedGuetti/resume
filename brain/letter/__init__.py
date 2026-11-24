"""letter: cover letters, assembled from your own paragraphs (bank/letters/) or written
with a coach. You write the text; the model picks, links and checks.

    styles.yaml  the four styles (direct, warm, formal, story): paragraph plans,
                 questions, example openings. Edit it to change how the coach guides you
    styles.py    loads them, and suggests one for an offer (keywords, or a model that
                 must quote the offer)
    voice.py     bank/voice.md: your answers in your own words, your banned phrases
    lint.py      checks a paragraph: clichés, AI tells, resume restating, length
    coach.py     what to show next to a paragraph (your proof, the offer), AI starters
                 and a grammar-only polish, both checked against your bank and rules
    paragraphs.py  bank/letters/: your paragraphs per entry, EN + FR, stale-French check
    assemble.py  pick paragraphs for an offer, one linking sentence, the "why them"
                 draft, translation; every model answer checked
    document.py  letter.md <-> Letter -> LaTeX (cv/coverletter.cls) -> PDF
"""
