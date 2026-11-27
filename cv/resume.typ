// resume.typ: the resume layout, shared by every language and every tailored version.
// Style lives here and in ninurta.typ; content comes from bank/ through Python
// (python -m brain build ...), which passes it as JSON in sys.inputs.data.
#import "ninurta.typ": accent, ink, muted, rule, fonts, data, rich, header

// Body text size: BASE-SIZE, grown in steps up to MAX-SIZE when the content leaves room
// (see "Filling the page" below).
#let BASE-SIZE = 10.5pt
#let MAX-SIZE = 11.5pt
#let SIZE-STEP = 0.25pt

// A4 for France/EU; "us-letter" for US applications
#set page(paper: "a4", margin: (x: 0.62in, y: 0.5in))
#set text(font: fonts, size: BASE-SIZE, fill: ink, lang: data.at("lang", default: "en"),
          hyphenate: false, number-type: "lining")
#set par(leading: 0.58em, spacing: 0.58em, justify: false)
#set document(title: data.at("title", default: ""), author: data.at("profile", default: (name: "")).name)
#show link: it => it

#set list(marker: text(fill: accent, size: 0.9em)[•], indent: 0.1em, body-indent: 0.55em, spacing: 0.5em)

// Filling the page, when the content is shorter than the page:
//   1. the body text grows from BASE-SIZE to the largest step up to MAX-SIZE that still fits
//      (the name and contact line keep their size);
//   2. what's left is spread over the gaps between two entries (1 share each) and before
//      sections (1.5 shares), at most MAX-EXTRA per share so a page never looks stretched.
// Python reads the fill at BASE-SIZE (<fill>) to decide first whether to add a bullet.
#let MAX-EXTRA = 6pt
#let SECTION-SHARE = 1.5

// EXPERIENCE ───────────── (letter-spaced title, then a hairline to the margin)
#let section(title, extra) = {
  v(12pt + SECTION-SHARE * extra, weak: true)
  grid(columns: (auto, 1fr), column-gutter: 8pt, align: horizon,
    text(size: 0.95em, weight: "bold", fill: accent, tracking: 0.6pt, upper(title)),
    line(length: 100%, stroke: 0.6pt + rule))
  v(6pt, weak: true)
}

// Organisation (semibold) ........ Dates (muted)
// Role (italic)           ........ Location, or the project's link (muted, smaller)
#let entry(e, extra) = {
  v(4pt + extra)   // more air between entries than inside one
  let place = if "link" in e { link(e.link.url, e.link.text) } else { e.location }
  block(below: 0.45em, breakable: false)[
    #text(weight: "semibold", e.org) #h(1fr) #text(fill: muted, e.dates) \
    #emph(e.title) #h(1fr) #text(fill: muted, size: 0.9em, place)
  ]
  if e.bullets.len() > 0 {
    list(..e.bullets.map(rich))
  }
}

#let body(size, extra) = {
  header(data.profile)
  set text(size: size)
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

#layout(page => {
  let height(size) = measure(body(size, 0pt), width: page.width).height
  let natural = height(BASE-SIZE)
  let size = BASE-SIZE
  while size + SIZE-STEP <= MAX-SIZE and height(size + SIZE-STEP) <= page.height {
    size += SIZE-STEP
  }
  let slack = page.height - height(size)
  let extra = if slack > 0pt { calc.min(slack / shares, MAX-EXTRA) } else { 0pt }
  [#metadata((fill: natural / page.height, size: size / 1pt, extra: extra / 1pt))<fill>]
  body(size, extra)
})
