import React, { useEffect, useState } from 'react';

/**
 * Types one harness verb at a time — plan… route… dispatch… — then
 * backspaces it away and moves to the next. Pure timers, no deps.
 * Under prefers-reduced-motion it renders the verbs as a static list.
 */
const WORDS = ['plan', 'route', 'dispatch', 'verify', 'normalize', 'render'];
const TYPE_MS = 85;
const DELETE_MS = 40;
const HOLD_MS = 1500;

export const TypedWord: React.FC<{ className?: string }> = ({ className }) => {
  const [reduced] = useState(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  );
  const [wordIndex, setWordIndex] = useState(0);
  const [text, setText] = useState('');
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (reduced) return;
    const word = WORDS[wordIndex];
    let timer: number;
    if (!deleting) {
      if (text.length < word.length) {
        timer = window.setTimeout(() => setText(word.slice(0, text.length + 1)), TYPE_MS);
      } else {
        timer = window.setTimeout(() => setDeleting(true), HOLD_MS);
      }
    } else if (text.length > 0) {
      timer = window.setTimeout(() => setText(text.slice(0, -1)), DELETE_MS);
    } else {
      setWordIndex((wordIndex + 1) % WORDS.length);
      setDeleting(false);
    }
    return () => window.clearTimeout(timer);
  }, [reduced, text, deleting, wordIndex]);

  if (reduced) {
    return <span className={className}>{WORDS.join(' · ')}</span>;
  }

  return (
    <span className={className} aria-label={WORDS.join(', ')}>
      <span aria-hidden="true">
        {text}
        {text.length > 0 && <span className="text-[var(--faint)]">…</span>}
        <span className="caret" />
      </span>
    </span>
  );
};
