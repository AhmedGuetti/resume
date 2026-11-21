"""How well you fit an offer, and where you stand among the other applicants.

    levels.py        seniority and degree levels read from free text
    candidate.py     your years of experience, level and degree, from the bank
    requirements.py  each requirement of the offer: met / partial / missing, with evidence
    fit.py           FitScore: the 0-100 score, for your whole bank and for this resume
    competition.py   applicants and their seniority (asked to you), and the position verdict

Like everywhere else: the LLM may judge, but must point at evidence in the bank, and
every number is computed by the code.
"""
