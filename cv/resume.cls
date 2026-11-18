% resume.cls — shared layout for every language version.
% Style lives here; content lives in resume-<lang>.tex. Change one, not both.
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{resume}[2026/11/18 Resume class]

\DeclareOption*{\PassOptionsToPackage{\CurrentOption}{babel}}
\ProcessOptions\relax
\LoadClass[10pt]{article}

\RequirePackage[a4paper,margin=1.5cm,top=1.2cm,bottom=1.2cm]{geometry}
\RequirePackage{fontspec}
\setmainfont{TeX Gyre Heros}
\RequirePackage{babel}
\RequirePackage{xcolor}
\RequirePackage{titlesec}
\RequirePackage{enumitem}
\RequirePackage{tabularx}
\RequirePackage[hidelinks]{hyperref}

\definecolor{accent}{HTML}{1F4E79}
\definecolor{muted}{HTML}{555555}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\linespread{1.05}
\frenchspacing

% Section headings: small caps + rule
\titleformat{\section}{\large\bfseries\color{accent}\scshape}{}{0pt}{}[\vspace{-6pt}\color{accent}\rule{\linewidth}{0.6pt}]
\titlespacing*{\section}{0pt}{8pt}{4pt}

\setlist[itemize]{leftmargin=1.1em,itemsep=1pt,topsep=2pt,parsep=0pt,label=\textbullet}

% \cvheader{Name}{Title}{contact line}
\newcommand{\cvheader}[3]{%
  \begin{center}
    {\Huge\bfseries #1}\\[3pt]
    {\large\color{accent} #2}\\[4pt]
    {\small\color{muted} #3}
  \end{center}\vspace{-4pt}}

% \cventry{Role}{Organisation}{Dates}{Location}  then an itemize of bullets
\newcommand{\cventry}[4]{%
  \par\noindent\textbf{#1}\hfill{\small\color{muted}#3}\\
  {\itshape #2}\hfill{\small\color{muted}#4}\par\vspace{1pt}}

% \cvskill{Label}{Items}
\newcommand{\cvskill}[2]{\noindent\textbf{#1:} #2\par\vspace{1pt}}
