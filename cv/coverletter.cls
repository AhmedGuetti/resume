% coverletter.cls — Ninurta cover letter layout. Same font, color and header as the
% resume (both load ninurta.sty), so a letter and a resume sent together look like a set.
% Content lives in cv/company/<name>/letter.md; letter-<lang>.tex is generated from it.
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{coverletter}[2026/11/21 Cover letter class v1]

\DeclareOption*{\PassOptionsToPackage{\CurrentOption}{babel}}
\ProcessOptions\relax
\LoadClass[10pt]{article}

% Wider margins than the resume: a letter is read as prose, short lines read faster.
\RequirePackage[a4paper,margin=0.95in,top=0.6in,bottom=0.8in]{geometry}
\RequirePackage{ninurta}
\RequirePackage{babel}
\RequirePackage[hidelinks]{hyperref}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.75em}
\linespread{1.1}
\AtBeginDocument{\frenchspacing}   % one space after a full stop, in every language
\raggedbottom

% \letterhead{Name}{contact line}: the resume's header, with an accent rule under it
\newcommand{\letterhead}[2]{%
  \cvheader{#1}{#2}%
  \vspace{-4pt}{\color{accent}\rule{\textwidth}{0.5pt}}\par\vspace{1.2em}}

% \letterto{recipient lines, separated by \\}{place and date}
% Recipient on the left, place and date on the right, on the same line.
\newcommand{\letterto}[2]{%
  \begin{minipage}[t]{0.55\textwidth}\raggedright #1\end{minipage}%
  \hfill
  \begin{minipage}[t]{0.4\textwidth}\raggedleft #2\end{minipage}\par\vspace{1em}}

% \lettersubject{Label}{text}: "Subject: ..." with the label in the accent color
\newcommand{\lettersubject}[2]{{\bfseries{\color{accent}#1}\ #2}\par\vspace{0.4em}}

% \lettersignoff{closing}{name}
\newcommand{\lettersignoff}[2]{%
  \par\vspace{0.4em}#1\par\vspace{1.6em}{\bfseries #2}\par}
