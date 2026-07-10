import { useState, useMemo, useRef, useEffect } from 'react';
import { Position } from 'reactflow';
import { BaseNode } from './baseNode';

const VARIABLE_PATTERN = /{{\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*}}/g;
const CHAR_WIDTH = 7.5;
const NODE_PADDING = 32;
const MIN_NODE_WIDTH = 220;
const MAX_NODE_WIDTH = 500;

export const TextNode = ({ id, data }) => {
  const [currText, setCurrText] = useState(data?.text || '{{input}}');
  const textareaRef = useRef(null);

  const handleTextChange = (e) => {
    setCurrText(e.target.value);
  };

  const variables = useMemo(() => {
    const unique = new Set();
    VARIABLE_PATTERN.lastIndex = 0;
    let match;
    while ((match = VARIABLE_PATTERN.exec(currText)) !== null) {
      unique.add(match[1]);
    }
    return Array.from(unique);
  }, [currText]);

  const nodeWidth = useMemo(() => {
    const lines = currText.split('\n');
    const longest = lines.reduce((max, line) => Math.max(max, line.length), 0);
    return Math.min(MAX_NODE_WIDTH, Math.max(MIN_NODE_WIDTH, longest * CHAR_WIDTH + NODE_PADDING));
  }, [currText]);

  const handles = useMemo(() => {
    const count = variables.length;
    const targets = variables.map((name, i) => ({
      type: 'target',
      position: Position.Left,
      id: `${id}-${name}`,
      style: { top: `${((i + 1) / (count + 1)) * 100}%` },
    }));

    return [
      { type: 'source', position: Position.Right, id: `${id}-output` },
      ...targets,
    ];
  }, [id, variables]);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = ta.scrollHeight + 'px';
  }, [currText]);

  return (
    <BaseNode title="Text" handles={handles} style={{ width: nodeWidth }}>
      <label>
        Text:
        <textarea
          ref={textareaRef}
          value={currText}
          onChange={handleTextChange}
          rows={1}
          style={{ resize: 'none', overflow: 'hidden' }}
        />
      </label>
    </BaseNode>
  );
};
