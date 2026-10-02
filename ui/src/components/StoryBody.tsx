import type { ReactNode } from "react";

// A deliberately small Markdown vocabulary. React escapes all text; no raw HTML.
function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*\n]+\*\*|\*[^*\n]+\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**') ? <strong key={i}>{part.slice(2,-2)}</strong> :
    part.startsWith('*') && part.endsWith('*') ? <em key={i}>{part.slice(1,-1)}</em> : part);
}
export function StoryBody({ text }: { text: string }) {
  return <div className="story-prose">{text.split(/\n\s*\n/).map((block, i) => {
    if (block.startsWith('## ')) return <h2 key={i}>{inline(block.slice(3))}</h2>;
    if (block.startsWith('> ')) return <blockquote key={i}>{inline(block.replace(/^> ?/gm,''))}</blockquote>;
    if (block.split('\n').every(line => line.startsWith('- '))) return <ul key={i}>{block.split('\n').map((line,j) => <li key={j}>{inline(line.slice(2))}</li>)}</ul>;
    return <p key={i}>{inline(block)}</p>;
  })}</div>;
}
