% resume.cls — Ninurta resume layout, shared by every language and every tailored version.
% Style lives here; content lives in bank/ (resume-<lang>.tex is generated from it).
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{resume}[2026/11/18 Resume class v3 (compact, accent color)]

\DeclareOption*{\PassOptionsToPackage{\CurrentOption}{babel}}
\ProcessOptions\relax
\LoadClass[10pt]{article}

% A4 for France/EU; swap a4paper -> letterpaper for US applications
\RequirePackage[a4paper,margin=0.6in,top=0.5in,bottom=0.5in]{geometry}
% Font, accent color, \sep and \cvheader: shared with the cover letter (ninurta.sty)
\RequirePackage{ninurta}
\RequirePackage{babel}
\RequirePackage{titlesec}
\RequirePackage{enumitem}
\RequirePackage[hidelinks]{hyperref}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\raggedbottom

% Section headings: bold caps with a rule underneath, both in the accent color
\titleformat{\section}{\bfseries\normalsize\color{accent}}{}{0pt}{\MakeUppercase}[\vspace{-5pt}{\color{accent}\rule{\textwidth}{0.5pt}}]
\titlespacing*{\section}{0pt}{7pt}{4pt}

\setlist[itemize]{leftmargin=1.2em,itemsep=0pt,topsep=1pt,parsep=0pt,partopsep=0pt,
  label={\color{accent}\textbullet}}

% \cventry{Role}{Organisation}{Dates}{Location}  then an itemize of bullets
% Renders:  Organisation (bold) ........ Location (bold)
%           Role (italic)    ........... Dates (italic)
\newcommand{\cventry}[4]{%
  \vspace{3pt}%
  {\bfseries #2}\hfill {\bfseries #4}\\[-1pt]
  {\itshape #1}\hfill {\itshape #3}\par}

% Skills block: \begin{cvskills} \cvskill{Label}{items} ... \end{cvskills}
\newenvironment{cvskills}{\begin{itemize}}{\end{itemize}}
\newcommand{\cvskill}[2]{\item \textbf{#1:} #2}
