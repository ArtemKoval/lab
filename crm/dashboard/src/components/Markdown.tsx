import type { Root } from "mdast";
import { findAndReplace } from "mdast-util-find-and-replace";
import ReactMarkdown, { type Components } from "react-markdown";
import { Link } from "react-router";
import remarkGfm from "remark-gfm";
import { casePage } from "../paths";

// A case's id, or an evaluation's copy of one, such as CLM-1003 or CLM-1104-E7.
const CASE_ID = /\bCLM-\d{4}(?:-E\d+)?\b/g;

// Makes each case id in the text a link to the case's page, except in a link
// already, which can't hold another.
function linkCases() {
  return (tree: Root) => {
    findAndReplace(
      tree,
      [
        CASE_ID,
        (caseId: string) => ({
          type: "link",
          url: casePage(caseId),
          children: [{ type: "text", value: caseId }],
        }),
      ],
      { ignore: ["link", "linkReference"] },
    );
  };
}

// A path on the dashboard, such as /cases/CLM-1003, rather than another site,
// which //host also names.
const ownPage = (href: string) =>
  href.startsWith("/") && !href.startsWith("//");

// A link to one of the dashboard's own pages stays in the dashboard; any other
// opens in a tab of its own.
const components: Components = {
  a: ({ href = "", children }) =>
    ownPage(href) ? (
      <Link to={href}>{children}</Link>
    ) : (
      <a href={href} target="_blank" rel="noreferrer">
        {children}
      </a>
    ),
  table: ({ children }) => (
    <div className="answer-table">
      <table>{children}</table>
    </div>
  ),
};

// An answer of the Copilot's, written in Markdown, formatted.
export function Markdown({ text }: Readonly<{ text: string }>) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, linkCases]}
      components={components}
    >
      {text}
    </ReactMarkdown>
  );
}
