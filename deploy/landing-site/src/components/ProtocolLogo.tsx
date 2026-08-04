import React from 'react';
import mcpSvg from '../assets/protocols/mcp.svg?raw';
import a2aSvg from '../assets/protocols/a2a.svg?raw';
import langchainSvg from '../assets/protocols/langchain.svg?raw';

export type ProtocolLogoKey =
  | 'mcp'
  | 'a2a'
  | 'langgraph'
  | 'computer-use'
  | 'canvaskit'
  | 'a2ui'
  | 'openapi'
  | 'grpc';

const RAW: Partial<Record<ProtocolLogoKey, string>> = {
  mcp: mcpSvg,
  a2a: a2aSvg,
  langgraph: langchainSvg,
};

const TEXT_TOKENS: Partial<Record<ProtocolLogoKey, string>> = {
  a2ui: 'A2UI',
  openapi: 'OAS',
  grpc: 'gRPC',
};

const GLYPH_PATHS: Partial<Record<ProtocolLogoKey, string>> = {
  // brand glyph: three satellites around a core (monochrome, currentColor)
  'computer-use': 'M12 2a2 2 0 1 1 0 4 2 2 0 0 1 0-4Zm0 16a2 2 0 1 1 0 4 2 2 0 0 1 0-4ZM4 10a2 2 0 1 1 0 4 2 2 0 0 1 0-4Zm16 0a2 2 0 1 1 0 4 2 2 0 0 1 0-4ZM8.5 8.5h7v7h-7z',
  canvaskit: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
};

interface Props {
  logo: ProtocolLogoKey;
  className?: string;
}

/** Monochrome protocol mark — all artwork inherits currentColor. */
export const ProtocolLogo: React.FC<Props> = ({ logo, className = 'w-10 h-10' }) => {
  const raw = RAW[logo];
  if (raw) {
    return (
      <span
        className={`inline-flex items-center justify-center [&>svg]:w-full [&>svg]:h-full ${className}`}
        dangerouslySetInnerHTML={{ __html: raw }}
        aria-hidden="true"
      />
    );
  }
  const token = TEXT_TOKENS[logo];
  if (token) {
    return (
      <span className={`inline-flex items-center justify-center font-display text-current ${className}`} aria-hidden="true">
        {token}
      </span>
    );
  }
  const path = GLYPH_PATHS[logo];
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <path d={path} />
    </svg>
  );
};
