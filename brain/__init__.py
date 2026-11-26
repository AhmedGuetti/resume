"""brain: the Python side of Ninurta. Reads the bank, picks content for a job offer,
builds the PDFs.

The packages follow the path of one application:

    bank/     the content (bank/*.md) and Selection: what goes on one resume
    offer/    a job offer: its facts (checked against its text), job.json, duplicates
    pick/     the LLM chooses the content for an offer; fit it on one page
    score/    how well you fit the offer, and where you stand among the applicants
    gaps/     gap interview: your answers about missing requirements -> bank bullets you approve
    render/   selection -> data -> PDF (Typst, cv/*.typ)
    letter/   the cover letter coach: four styles, your voice, checks, letter.md -> PDF
    llm/      model backends, fallback chain, spending log and budget
    app/      what you type: every command (commands.py), the CLI and shell built from it, `apply`

    paths.py  where everything lives      config.py  config.yaml      errors.py  error types

Who imports whom: app uses everything; pick, score, offer, render and letter use bank and llm
(score reuses pick's helpers, offer's job.json stores score's results); bank and llm
use only paths, config and errors; nothing imports app.
"""
