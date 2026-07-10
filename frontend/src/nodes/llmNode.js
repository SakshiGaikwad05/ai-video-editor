import { Position } from 'reactflow';
import { BaseNode } from './baseNode';

export const LLMNode = ({ id }) => {
  const handles = [
    { type: 'target', position: Position.Left, id: `${id}-system`, style: { top: '33%' } },
    { type: 'target', position: Position.Left, id: `${id}-prompt`, style: { top: '66%' } },
    { type: 'source', position: Position.Right, id: `${id}-response` },
  ];

  return (
    <BaseNode title="LLM" handles={handles}>
      <span>This is a LLM.</span>
    </BaseNode>
  );
};
