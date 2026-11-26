// ninurta.typ: the look every Ninurta document shares (font, accent color, header).
// resume.typ and letter.typ import it, so a resume and a letter sent together match.
// Change the font or the color here, once.

// Accent: section titles, their rules, bullets and separators. Text stays black,
// so nothing changes for ATS parsers. Muted options that print well in grayscale:
//   #2E6B4F forest green (default)   #1F4E79 navy blue   #355E3B hunter green
//   #7A2E3A burgundy                 #2F5D62 deep teal   #404040 charcoal
#let accent = rgb("#2E6B4F")

// Source Sans 3 if installed (Arch: adobe-source-sans-fonts), else a close sans.
#let fonts = ("Source Sans 3", "Source Sans Pro", "TeX Gyre Heros", "Liberation Sans", "DejaVu Sans")

// The document's data, as JSON, from Python (brain/render/typst.py).
#let data = json(bytes(sys.inputs.at("data", default: "{}")))

// Inline text from the bank: a list of [style, text] runs, style "" | "b" (bold) | "c" (code).
// Strings are placed as text, never parsed as markup: no escaping needed.
#let rich(runs) = runs.map(r => {
  let (style, s) = r
  if style == "b" { strong(s) } else if style == "c" { raw(s) } else { s }
}).join()

#let sep = h(0.45em) + text(fill: accent, baseline: -0.05em)[•] + h(0.45em)

// Name, then one or two contact lines; each item is {text, url?}.
#let header(profile) = align(center)[
  #text(size: 1.9em, weight: "bold", profile.name)
  #v(0.5em, weak: true)
  #for line in profile.contact {
    line.map(item => if "url" in item { link(item.url, item.text) } else { item.text }).join(sep)
    linebreak()
  }
]
