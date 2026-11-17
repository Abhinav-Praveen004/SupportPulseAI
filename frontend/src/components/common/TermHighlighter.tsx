import React from 'react';

interface TermHighlighterProps {
  text: string;
  terms: Array<{ ngram: string; score: number }>;
}

export const TermHighlighter: React.FC<TermHighlighterProps> = ({ text, terms }) => {
  if (!terms || terms.length === 0) {
    return <span className="text-slate-800 dark:text-slate-200">{text}</span>;
  }

  // Extract clean n-grams for matching
  const validTerms = terms
    .map((t) => t.ngram.trim().toLowerCase())
    .filter((t) => t.length > 2);

  if (validTerms.length === 0) {
    return <span className="text-slate-800 dark:text-slate-200">{text}</span>;
  }

  // Build regex matching any of the top n-grams
  const escaped = validTerms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const regex = new RegExp(`(${escaped.join('|')})`, 'gi');

  const parts = text.split(regex);

  return (
    <div className="leading-relaxed">
      {parts.map((part, index) => {
        const isMatch = validTerms.includes(part.toLowerCase());
        if (isMatch) {
          const matchedTerm = terms.find((t) => t.ngram.toLowerCase() === part.toLowerCase());
          const score = matchedTerm ? matchedTerm.score : null;
          return (
            <mark
              key={index}
              className="bg-brand-100 dark:bg-brand-950/80 text-brand-900 dark:text-brand-200 border-b-2 border-brand-500 px-1 py-0.5 rounded-sm font-medium transition-colors"
              title={score ? `Model impact weight: +${score.toFixed(3)}` : undefined}
            >
              {part}
            </mark>
          );
        }
        return <span key={index}>{part}</span>;
      })}
    </div>
  );
};
