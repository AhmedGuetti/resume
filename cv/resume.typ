// resume.typ: the resume layout, shared by every language and every tailored version.
// Style lives here and in ninurta.typ; content comes from bank/ through Python
// (python -m brain build ...), which passes it as JSON in sys.inputs.data.
#import "ninurta.typ": accent, ink, muted, rule, fonts, data, rich, header

// A4 for France/EU; "us-letter" for US applications
#set page(paper: "a4", margin: (x: 0.62in, y: 0.5in))
#set text(font: fonts, size: 10.5pt, fill: ink, lang: data.at("lang", default: "en"),
          hyphenate: false, number-type: "lining")
#set par(leading: 0.58em, spacing: 0.58em, justify: false)
#set document(title: data.at("title", default: ""), author: data.at("profile", default: (name: "")).name)
#show link: it => it

#set list(marker: text(fill: accent, size: 0.9em)[•], indent: 0.1em, body-indent: 0.55em, spacing: 0.5em)

// Filling the page: when the content is shorter than the page, the space left over is
// spread over the gaps between two entries (1 share each) and before sections (1.5 shares),
// at most MAX-EXTRA per share so a short page never looks stretched; the rest stays at
// the bottom. Python reads the page fill (<fill>) to decide whether to add a bullet.
#let MAX-EXTRA = 6pt
#let SECTION-SHARE = 1.5

// EXPERIENCE ───────────── (letter-spaced title, then a hairline to the margin)
#let section(title, extra) = {
  v(12pt + SECTION-SHARE * extra, weak: true)
  grid(columns: (auto, 1fr), column-gutter: 8pt, align: horizon,
    text(size: 10pt, weight: "bold", fill: accent, tracking: 0.6pt, upper(title)),
    line(length: 100%, stroke: 0.6pt + rule))
  v(6pt, weak: true)
}

// Organisation (semibold) ........ Dates (muted)
// Role (italic)           ........ Location (muted, smaller)
#let entry(e, extra) = {
  v(4pt + extra)   // more air between entries than inside one
  block(below: 0.45em, breakable: false)[
    #text(weight: "semibold", e.org) #h(1fr) #text(fill: muted, e.dates) \
    #emph(e.title) #h(1fr) #text(fill: muted, size: 9.5pt, e.location)
  ]
  if e.bullets.len() > 0 {
    list(..e.bullets.map(rich))
  }
}

#let body(extra) = {
  header(data.profile)
  for s in data.sections {
    section(s.title, extra)
    if s.kind == "skills" {
      // Label | values, as a two-column grid
      grid(columns: (auto, 1fr), column-gutter: 10pt, row-gutter: 0.55em,
        ..s.groups.map(g => (text(weight: "semibold", g.label.trim(":")), g.items.join(", "))).flatten())
    } else {
      for (i, e) in s.entries.enumerate() { entry(e, if i == 0 { 0pt } else { extra }) }
    }
  }
}

#let shares = data.sections.map(s => SECTION-SHARE + calc.max(0, s.at("entries", default: ()).len() - 1)).sum(default: 1)

#layout(size => {
  let natural = measure(body(0pt), width: size.width).height
  let slack = size.height - natural
  let extra = if slack > 0pt { calc.min(slack / shares, MAX-EXTRA) } else { 0pt }
  [#metadata((fill: natural / size.height, extra: extra / 1pt))<fill>]
  body(extra)
})
