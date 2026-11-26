// ninurta.typ: the look every Ninurta document shares (font, colors, header).
// resume.typ and letter.typ import it, so a resume and a letter sent together match.
// Change the font or the colors here, once.

// Accent: the name, section titles and bullets. Body text stays near-black,
// so nothing changes for ATS parsers. Muted options that print well in grayscale:
//   #1F3A5F ink navy (default)   #2E6B4F forest green   #355E3B hunter green
//   #7A2E3A burgundy             #2F5D62 deep teal      #404040 charcoal
#let accent = rgb("#1F3A5F")
#let ink    = rgb("#1A1A1A")   // body text
#let muted  = rgb("#5A5A5A")   // secondary text: dates, locations, contact line
#let rule   = rgb("#C9CED6")   // hairlines and separators

// Source Sans 3 if installed (Arch: adobe-source-sans-fonts), else a close sans.
#let fonts = ("Source Sans 3", "Source Sans Pro", "TeX Gyre Heros", "Liberation Sans", "DejaVu Sans")

// The document's data, as JSON, from Python (brain/render/typst.py).
#let data = json(bytes(sys.inputs.at("data", default: "{}")))

// Inline text from the bank: a list of [style, text] runs, style "" | "b" (bold) | "c" (code).
// Strings are placed as text, never parsed as markup: no escaping needed.
#let rich(runs) = runs.map(r => {
  let (style, s) = r
  if style == "b" { text(weight: "semibold", s) } else if style == "c" { raw(s) } else { s }
}).join()

#let sep = h(0.5em) + text(fill: rule)[|] + h(0.5em)

// Name on the left, then every contact item on one muted line; each item is {text, url?}.
// Items never break inside; on a narrower page (the letter) the line wraps between them.
#let header(profile) = {
  text(size: 22pt, weight: "bold", fill: accent, tracking: 0.2pt, profile.name)
  v(9pt, weak: true)
  set par(justify: false)
  text(size: 9.5pt, fill: muted,
    profile.contact.flatten()
      .map(item => box(if "url" in item { link(item.url, item.text) } else { item.text }))
      .join(sep))
  v(4pt)
}
