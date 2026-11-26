// resume.typ: the resume layout, shared by every language and every tailored version.
// Style lives here and in ninurta.typ; content comes from bank/ through Python
// (python -m brain build ...), which passes it as JSON in sys.inputs.data.
#import "ninurta.typ": accent, fonts, data, rich, header

// A4 for France/EU; "us-letter" for US applications
#set page(paper: "a4", margin: (x: 0.6in, y: 0.5in))
#set text(font: fonts, size: 10.5pt, lang: data.at("lang", default: "en"), hyphenate: false)
#set par(leading: 0.55em, spacing: 0.55em, justify: false)
#set document(title: data.at("title", default: ""), author: data.at("profile", default: (name: "")).name)
#show link: it => it

#set list(marker: text(fill: accent)[•], indent: 0.2em, body-indent: 0.6em, spacing: 0.55em)

#let section(title) = {
  v(11pt, weak: true)
  text(weight: "bold", fill: accent, upper(title))
  v(5pt, weak: true)
  line(length: 100%, stroke: 0.5pt + accent)
  v(7pt, weak: true)
}

// Organisation (bold) ........ Location (bold)
// Role (italic)      ......... Dates (italic)
#let entry(e) = {
  v(7pt, weak: true)
  block(below: 0.5em)[
    *#e.org* #h(1fr) *#e.location* \
    _#e.title _ #h(1fr) _#e.dates _
  ]
  if e.bullets.len() > 0 {
    list(..e.bullets.map(rich))
  }
}

#header(data.profile)

#for s in data.sections {
  section(s.title)
  if s.kind == "skills" {
    list(..s.groups.map(g => [*#g.label* #g.items.join(", ")]))
  } else {
    for e in s.entries { entry(e) }
  }
}
