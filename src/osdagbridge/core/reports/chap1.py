from osdagbridge.core.reports.report_utils import _tex


def ch1_project_info(m):
    return r"""
\chapter{Project Information}

This section records all project metadata as entered by the designer.

\section{Project and Design Team Details}
\label{sec:project-details}

\begin{longtable}{|L{5.5cm}|L{8.5cm}|}
\caption{\textbf{Project and Design Team Details}}\\
\hline
\textbf{Field} & \textbf{Value} \\[4pt]
\hline
\endfirsthead
\multicolumn{2}{l}{\textit{...continued from previous page}}\\
\hline
\textbf{Field} & \textbf{Value} \\[4pt]
\hline
\endhead
\hline
\multicolumn{2}{r}{\textit{Continued on next page...}}\\
\endfoot
\hline
\endlastfoot
\textbf{Project Name} & """ + _tex(m.project_name) + r""" \\[4pt]
\hline
\textbf{Project Location} & """ + _tex(m.project_location) + r""" \\[4pt]
\hline
\textbf{Designer} & """ + _tex(m.designer) + r""" \\[4pt]
\hline
\textbf{Reviewer} & """ + _tex(m.reviewer) + r""" \\[4pt]
\hline
\textbf{Organization} & """ + _tex(m.company) + r""" \\[4pt]
\hline
\textbf{Client} & """ + _tex(m.client) + r""" \\[4pt]
\hline
\textbf{Software Version} & OsdagBridge \\[4pt]
\hline
\end{longtable}


\section{Applicable Codes and Standards}
\label{sec:codes}

\begin{itemize}
\item Indian Roads Congress (IRC) 5: General Features of Design
\item Indian Roads Congress (IRC) 6: Loads and Load Combinations
\item Indian Roads Congress (IRC) 22: Composite Construction (Limit State Design)
\item Indian Roads Congress (IRC) 24: Steel Road Bridges (Limit State Method)
\item Indian Roads Congress (IRC) 112: Concrete Road Bridges (deck design)
\item Indian Roads Congress Special Publication (IRC SP) 114: Seismic Design of Road Bridges
\item Indian Standard (IS) 800: General Construction in Steel
\item Indian Standard (IS) 2062: Hot Rolled Structural Steel Specification
\item Indian Standard (IS) 6006: Steel Bearings
\end{itemize}
"""


