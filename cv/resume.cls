% resume.cls — Ninurta resume layout, shared by every language and every tailored version.
% Style lives here; content lives in bank/ (resume-<lang>.tex is generated from it).
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{resume}[2026/11/18 Resume class v3 (compact, accent color)]

\DeclareOption*{\PassOptionsToPackage{\CurrentOption}{babel}}
\ProcessOptions\relax
\LoadClass[10pt]{article}

% A4 for France/EU; swap a4paper -> letterpaper for US applications
\RequirePackage[a4paper,margin=0.6in,top=0.5in,bottom=0.5in]{geometry}
\RequirePackage{fontspec}
% Main font. Source Sans 3 if installed (Arch: adobe-source-sans-fonts),
% otherwise TeX Gyre Heros (Helvetica clone, ships with TeX Live).
\IfFontExistsTF{Source Sans 3}
  {\setmainfont{Source Sans 3}[Scale=1.05]}   % 10pt x 1.05 = 10.5pt; 11pt no longer fits on one page
  {\setmainfont{TeX Gyre Heros}}
\RequirePackage{babel}
\RequirePackage{xcolor}
\RequirePackage{titlesec}
\RequirePackage{enumitem}
\RequirePackage[hidelinks]{hyperref}

% ---------- Accent color ----------
% Used for section titles, their rules, and bullets. Text stays black, so
% nothing changes for ATS parsers. To swap the color, change the hex below.
% Some muted options that stay readable on white and in grayscale print:
%   2E6B4F  forest green (default)     1F4E79  navy blue
%   355E3B  hunter green               7A2E3A  burgundy
%   2F5D62  deep teal                  404040  charcoal (near-black)
\definecolor{accent}{HTML}{2E6B4F}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\raggedbottom

% Section headings: bold caps with a rule underneath, both in the accent color
\titleformat{\section}{\bfseries\normalsize\color{accent}}{}{0pt}{\MakeUppercase}[\vspace{-5pt}{\color{accent}\rule{\textwidth}{0.5pt}}]
\titlespacing*{\section}{0pt}{7pt}{4pt}

\setlist[itemize]{leftmargin=1.2em,itemsep=0pt,topsep=1pt,parsep=0pt,partopsep=0pt,
  label={\color{accent}\textbullet}}

% Bullet separator for the contact line
\newcommand{\sep}{\ {\color{accent}\raisebox{0.1ex}{$\bullet$}}\ }

% \cvheader{Name}{contact line}
\newcommand{\cvheader}[2]{%
  \begin{center}
    {\LARGE\bfseries #1}\\[3pt]
    #2
  \end{center}}

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
