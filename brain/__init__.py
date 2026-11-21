"""brain: the Python side of Ninurta. Reads the bank, picks content for a job offer,
builds the PDFs.

The packages follow the path of one application:

    bank/     the content (bank/*.md) and Selection: what goes on one resume
    offer/    a job offer: its facts (checked against its text), job.json, duplicates
    pick/     choose the content for an offer (keywords or LLM), fit it on one page
    score/    how well you fit the offer, and where you stand among the applicants
    render/   selection -> LaTeX -> PDF
    llm/      model backends, fallback chain, spending log and budget
    app/      what you type: the CLI, the `apply` pipeline, the ninurta> shell

    paths.py  where everything lives      config.py  config.yaml      errors.py  error types

Who imports whom: app uses everything; pick, score, offer and render use bank and llm
(score reuses pick's helpers, offer's job.json stores score's results); bank and llm
use only paths, config and errors; nothing imports app.
"""
