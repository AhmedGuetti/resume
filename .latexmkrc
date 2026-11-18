# latexmk config: LuaLaTeX, out-of-tree build
$pdf_mode = 4;                       # 4 = lualatex
$lualatex = 'lualatex -interaction=nonstopmode -halt-on-error -file-line-error -synctex=1 %O %S';
$out_dir  = 'build';
$aux_dir  = 'build';
$max_repeat = 5;
$silent = 1;
ensure_path('TEXINPUTS', './cv//');  # finds resume.cls from any file
