// letter.typ: the cover letter layout. Same font, color and header as the resume
// (both import ninurta.typ), so a letter and a resume sent together look like a set.
// Content comes from cv/company/<name>/letter.md through Python (python -m brain letter ...).
#import "ninurta.typ": accent, fonts, data, rich, header

// Wider margins than the resume: a letter is read as prose, short lines read faster.
#set page(paper: "a4", margin: (x: 0.95in, top: 0.6in, bottom: 0.8in))
// Justified and hyphenated like a printed letter: it is read by people, not parsed.
#set text(font: fonts, size: 10.5pt, lang: data.at("lang", default: "en"), hyphenate: true)
#set par(leading: 0.68em, spacing: 1.3em, justify: true)
#set document(title: data.at("title", default: ""), author: data.profile.name)

#header(data.profile)
#v(0.6em)
#line(length: 100%, stroke: 0.5pt + accent)
#v(1.2em)

// Recipient on the left, place and date on the right, on the same line.
#grid(columns: (55%, 1fr),
  data.recipient.join(linebreak()),
  align(right, data.when))
#v(1em)

#if data.subject != "" {
  text(weight: "bold")[#text(fill: accent, data.subject_label) #data.subject]
  v(0.4em)
}

#data.salutation

#for p in data.paragraphs [
  #rich(p)

]

#v(0.4em)
#data.signoff
#v(1.6em)
*#data.profile.name*
