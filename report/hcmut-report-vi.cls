\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{hcmut-report-vi}[2025/01/01 Clean class for pdfLaTeX]

% ==========================================
% PASS OPTIONS -> article
% ==========================================
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax
\LoadClass[12pt,a4paper]{article}

% ==========================================
% PACKAGES
% ==========================================
\RequirePackage{anyfontsize,amsmath,amssymb}
\RequirePackage{geometry,graphicx,indentfirst,setspace}
\RequirePackage{booktabs}

% Caption setup
\RequirePackage{caption}
\captionsetup{justification=centering}

\RequirePackage{fancyhdr,hyperref}
\RequirePackage[super,square,sort]{natbib}

% ==========================================
% LANGUAGE & FONTS (pdfLaTeX specific)
% ==========================================

% BẮT BUỘC cho pdfLaTeX để đọc file UTF8
\RequirePackage[utf8]{inputenc}

% BẮT BUỘC cho pdfLaTeX để xử lý tiếng Việt đúng dấu
\RequirePackage[T5]{fontenc}
\RequirePackage{textcomp} % Hỗ trợ thêm ký tự

% Ngôn ngữ tiếng Việt
\RequirePackage[vietnamese]{babel}

% Gói listings và màu
\RequirePackage{listings}
\RequirePackage{xcolor}

% =Gói fontspec và setmonofont đã bị XÓA vì chỉ dành cho LuaLaTeX=

% ==========================================
% LOGO DEFINITIONS
% ==========================================
\newcommand{\HCMUTlogoSmall}{\includegraphics[width=20pt]{graphics/hcmut.png}}
\newcommand{\HCMUTlogoBig}{\includegraphics[scale=0.4]{graphics/hcmut.png}}

% ==========================================
% USER FIELDS
% ==========================================

%%% Vietnames names %%%
\newcommand{\@upperuniname}{Đại học quốc gia Thành phố Hồ Chí Minh}
\newcommand{\@uniname}{Trường Đại học Bách Khoa Thành phố Hồ Chí Minh}
\newcommand{\@deptname}{Khoa khoa học và kỹ thuật máy tính}
\newcommand{\deptname}[1]{\renewcommand{\@deptname}{#1}}

\newcommand{\@coursename}{Course name}
\newcommand{\coursename}[1]{\renewcommand{\@coursename}{#1}}

\newcommand{\@reporttype}{Assignment Report}
\newcommand{\reporttype}[1]{\renewcommand{\@reporttype}{#1}}

\renewcommand{\@title}{Report title}

\newcommand{\@advisor}{ADVISOR}
\newcommand{\advisor}[1]{\renewcommand{\@advisor}{#1}}

\newcommand{\@stuname}{STUDENT: H (xxxxxxx)}
\newcommand{\stuname}[1]{\renewcommand{\@stuname}{#1}}

\newcommand{\@reportplace}{Hồ Chí Minh}
\newcommand{\reportplace}[1]{\renewcommand{\@reportplace}{#1}}
\newcommand{\@reporttime}{%
    \ifcase\month 0/\or Tháng 1/\or Tháng 2/\or Tháng 3/\or Tháng 4/\or Tháng 5/\or Tháng 6/%
    \or Tháng 7/\or Tháng 8/\or Tháng 9/\or Tháng 10/\or Tháng 11/\or Tháng 12/%
    \fi\space\the\year
}



% ==========================================
% LAYOUT SETUP
% ==========================================
\geometry{
    paper=a4paper,
    left=3cm,
    right=2cm,
    vmargin=2cm,
    includeheadfoot=true,
    headheight=38pt
}

\onehalfspacing
\raggedbottom
\renewcommand{\arraystretch}{1.2}

\setcounter{secnumdepth}{3}
\setcounter{tocdepth}{3}

\AtBeginDocument{\counterwithin{equation}{section}}
\AtBeginDocument{\counterwithin{table}{section}}
\AtBeginDocument{\counterwithin{figure}{section}}
\AtBeginDocument{\counterwithin{lstlisting}{section}}

% ==========================================
% HYPERREF SETUP
% ==========================================
\hypersetup{
    colorlinks=true,
    linkcolor=black,
    citecolor=red,
    urlcolor=blue
}

% ==========================================
% LISTINGS SETUP (Sửa lỗi đảo chữ tiếng Việt)
% ==========================================
\lstset{
basicstyle=\ttfamily\footnotesize,
columns=fullflexible,
breaklines=true,
postbreak=\mbox{\textcolor{red}{$\hookrightarrow$}\space},
keepspaces=true,
showstringspaces=false,
commentstyle=\color{green!50!black},
keywordstyle=\color{blue},
stringstyle=\color{red},
% Dùng literate để SỬA LỖI ĐẢO CHỮ TIẾNG VIỆT (Hoạt động trên cả pdfLaTeX)
literate=
    {á}{{á}}1 {à}{{à}}1 {ả}{{ả}}1 {ã}{{ã}}1 {ạ}{{ạ}}1
{ă}{{ă}}1 {ắ}{{ắ}}1 {ằ}{{ằ}}1 {ẳ}{{ẳ}}1 {ẵ}{{ẵ}}1 {ặ}{{ặ}}1
{â}{{â}}1 {ấ}{{ấ}}1 {ầ}{{ầ}}1 {ẩ}{{ẩ}}1 {ẫ}{{ẫ}}1 {ậ}{{ậ}}1
{Á}{{Á}}1 {À}{{À}}1 {Ả}{{Ả}}1 {Ã}{{Ã}}1 {Ạ}{{Ạ}}1
{Ă}{{Ă}}1 {Ắ}{{Ắ}}1 {Ằ}{{Ằ}}1 {Ẳ}{{Ẳ}}1 {Ẵ}{{Ẵ}}1 {Ặ}{{Ặ}}1
{Â}{{Â}}1 {Ấ}{{Ấ}}1 {Ầ}{{Ầ}}1 {Ẩ}{{Ẩ}}1 {Ẫ}{{Ẫ}}1 {Ậ}{{Ậ}}1
{đ}{{đ}}1 {Đ}{{Đ}}1
{é}{{é}}1 {è}{{è}}1 {ẻ}{{ẻ}}1 {ẽ}{{ẽ}}1 {ẹ}{{ẹ}}1
{ê}{{ê}}1 {ế}{{ế}}1 {ề}{{ề}}1 {ể}{{ể}}1 {ễ}{{ễ}}1 {ệ}{{ệ}}1
{É}{{É}}1 {È}{{È}}1 {Ẻ}{{Ẻ}}1 {Ẽ}{{Ẽ}}1 {Ẹ}{{Ẹ}}1
{Ê}{{Ê}}1 {Ế}{{Ế}}1 {Ề}{{Ề}}1 {Ể}{{Ể}}1 {Ễ}{{Ễ}}1 {Ệ}{{Ệ}}1
{í}{{í}}1 {ì}{{ì}}1 {ỉ}{{ỉ}}1 {ĩ}{{ĩ}}1 {ị}{{ị}}1
{Í}{{Í}}1 {Ì}{{Ì}}1 {Ỉ}{{Ỉ}}1 {Ĩ}{{Ĩ}}1 {Ị}{{Ị}}1
{ó}{{ó}}1 {ò}{{ò}}1 {ỏ}{{ỏ}}1 {õ}{{õ}}1 {ọ}{{ọ}}1
{ô}{{ô}}1 {ố}{{ố}}1 {ồ}{{ồ}}1 {ổ}{{ổ}}1 {ỗ}{{ỗ}}1 {ộ}{{ộ}}1
{ơ}{{ơ}}1 {ớ}{{ớ}}1 {ờ}{{ờ}}1 {ở}{{ở}}1 {ỡ}{{ỡ}}1 {ợ}{{ợ}}1
{Ó}{{Ó}}1 {Ò}{{Ò}}1 {Ỏ}{{Ỏ}}1 {Õ}{{Õ}}1 {Ọ}{{Ọ}}1
{Ô}{{Ô}}1 {Ố}{{Ố}}1 {Ồ}{{Ồ}}1 {Ổ}{{Ổ}}1 {Ỗ}{{ỗ}}1 {Ộ}{{Ộ}}1
{Ơ}{{Ơ}}1 {Ớ}{{Ớ}}1 {Ờ}{{Ờ}}1 {Ở}{{Ở}}1 {Ỡ}{{Ỡ}}1 {Ợ}{{Ợ}}1
{ú}{{ú}}1 {ù}{{ù}}1 {ủ}{{ủ}}1 {ũ}{{ũ}}1 {ụ}{{ụ}}1
{ư}{{ư}}1 {ứ}{{ứ}}1 {ừ}{{ừ}}1 {ử}{{ử}}1 {ữ}{{ữ}}1 {ự}{{ự}}1
{Ú}{{Ú}}1 {Ù}{{Ù}}1 {Ủ}{{Ủ}}1 {Ũ}{{Ũ}}1 {Ụ}{{Ụ}}1
{Ư}{{Ư}}1 {Ứ}{{Ứ}}1 {Ừ}{{Ừ}}1 {Ử}{{Ử}}1 {Ữ}{{Ữ}}1 {Ự}{{Ự}}1
{ý}{{ý}}1 {ỳ}{{ỳ}}1 {ỷ}{{ỷ}}1 {ỹ}{{ỹ}}1 {ỵ}{{ỵ}}1
{Ý}{{Ý}}1 {Ỳ}{{Ỳ}}1 {Ỷ}{{Ỷ}}1 {Ỹ}{{Ỹ}}1 {Ỵ}{{Ỵ}}1
}

% ==========================================
% HEADER & FOOTER (Hỗ trợ Twoside/Oneside)
% =Sửa lỗi lặp code=
% ==========================================
\pagestyle{fancy}
\fancyhf{} % Xóa sạch header/footer cũ
\renewcommand{\headrulewidth}{0.3pt}
\renewcommand{\footrulewidth}{0pt}

% Định nghĩa khối nội dung Header (để đỡ phải viết lại 2 lần)
% Định nghĩa nội dung cho trang LẺ (Odd) - Logo bên phải (giống code cũ của bạn)
\newcommand{\@HeaderContentOdd}{
    \begin{tabular}{rl}
        \begin{tabular}{l}
            \ttfamily\@uniname \\[2pt]
            \hspace{6.5em}\ttfamily\@deptname
        \end{tabular}
         & \HCMUTlogoSmall
    \end{tabular}
}

% Định nghĩa nội dung cho trang CHẴN (Even) - Logo bên trái (phiên bản "lật")
\newcommand{\@HeaderContentEven}{
    \begin{tabular}{lr} % <-- Đổi thành 'lr'
        \HCMUTlogoSmall & % <-- Logo đứng trước
        \begin{tabular}{l}
            \ttfamily\@uniname \\[2pt]
            \ttfamily\@deptname % <-- Text đứng sau, bỏ hspace vì đã căn lề trái
        \end{tabular}
    \end{tabular}
}

% Kiểm tra chế độ in (Twoside hay Oneside)
\if@twoside
    % --- TRƯỜNG HỢP TWOSIDE (In 2 mặt) ---
    % RO = Right Odd (Phải trang lẻ) -> Dùng nội dung Lẻ
    % LE = Left Even (Trái trang chẵn) -> Dùng nội dung Chẵn
    \fancyhead[RO]{\@HeaderContentOdd}
    \fancyhead[LE]{\@HeaderContentEven}
\else
    % --- TRƯỜNG HỢP ONESIDE (Mặc định) ---
    % Luôn nằm bên phải -> Dùng nội dung Lẻ
    \fancyhead[R]{\@HeaderContentOdd}
\fi

% Số trang luôn nằm giữa
\fancyfoot[C]{\thepage}

% ==========================================
% COVER PAGE COMMAND
% ==========================================
\newcommand{\coverpage}{
    \pagestyle{empty}
    \vspace*{-3\baselineskip}
    \begin{center}
        \MakeUppercase{\@upperuniname}\\
        \MakeUppercase{\@uniname}\\
        \MakeUppercase{\@deptname}

        \vfill \HCMUTlogoBig \vfill

        \bfseries
        \begin{tabular}{c}
            \Large\@coursename                                 \\[4pt] \midrule \\[4pt]
            \Large\@reporttype                                 \\[8pt]
            \Huge\parbox[c]{0.8\linewidth}{\centering \@title} \\[6pt] \bottomrule
        \end{tabular}

        \vfill
        \mdseries
        \begin{tabular}{rll}
            GVHD:                & \@advisor \\
            Sinh viên thực hiện: & \@stuname
        \end{tabular}
        \vfill
        \MakeUppercase{\@reportplace, \@reporttime}
    \end{center}
    \cleardoublepage
    \pagestyle{fancy}
}

% ==========================================
% LIST COMMANDS (SỬA LỖI TOC/BABEL)
% ==========================================
\makeatletter

% 1. Đặt tên tiếng Việt (Dùng AtBeginDocument để ghi đè Babel)
% Bật lên khi dùng tiếng việt
\AtBeginDocument{
    \renewcommand{\listfigurename}{Danh sách hình vẽ}
    \renewcommand{\listtablename}{Danh sách bảng}
    \renewcommand{\lstlistlistingname}{Danh sách đoạn mã}
    \renewcommand{\contentsname}{Mục lục}
}


% 2. Định nghĩa lại lệnh in danh sách để:
%    - Tự động thêm vào Mục lục (TOC)
%    - Ngắt trang
% ==========================================
% LIST COMMANDS (SỬA LỖI TOC/BABEL)
% ==========================================
\makeatletter

% 1. Đặt tên tiếng Việt (Dùng AtBeginDocument để ghi đè Babel)
\AtBeginDocument{
    \renewcommand{\listfigurename}{Danh sách hình vẽ}
    \renewcommand{\listtablename}{Danh sách bảng}
    \renewcommand{\lstlistlistingname}{Danh sách đoạn mã}
    \renewcommand{\contentsname}{Mục lục}
}

% 2. Định nghĩa lại lệnh in danh sách
% Thêm vào mục lục để khối đầu tài liệu được liệt kê đầy đủ
\renewcommand{\listoffigures}{%
    % \cleardoublepage
    \phantomsection
    \addcontentsline{toc}{section}{\listfigurename}
    \section*{\listfigurename}
    \@starttoc{lof}
}

\renewcommand{\listoftables}{%
    % \cleardoublepage
    \phantomsection
    \addcontentsline{toc}{section}{\listtablename}
    \section*{\listtablename}
    \@starttoc{lot}
}

\renewcommand{\lstlistoflistings}{%
    % \cleardoublepage
    \phantomsection
    \addcontentsline{toc}{section}{\lstlistlistingname}
    \section*{\lstlistlistingname}
    \@starttoc{lol}
}

% 3. Sửa lệnh TOC (Giữ nguyên)
\renewcommand{\tableofcontents}{%
    % \cleardoublepage
    \phantomsection
    \addcontentsline{toc}{section}{\contentsname}
    \section*{\contentsname}
    \@starttoc{toc}
}

\makeatother
