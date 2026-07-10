import { useState } from 'react';
import { Position } from 'reactflow';
import { BaseNode } from './baseNode';

export const ImageNode = ({ id, data }) => {
  const [prompt, setPrompt] = useState(data?.prompt || '');
  const [model, setModel] = useState(data?.model || 'DALL-E');

  const handles = [
    { type: 'target', position: Position.Left, id: `${id}-prompt` },
    { type: 'source', position: Position.Right, id: `${id}-output` },
  ];

  return (
    <BaseNode title="Image" handles={handles}>
      <label>
        Prompt:
        <input type="text" value={prompt} onChange={(e) => setPrompt(e.target.value)} />
      </label>
      <label>
        Model:
        <select value={model} onChange={(e) => setModel(e.target.value)}>
          <option value="DALL-E">DALL-E</option>
          <option value="Stable Diffusion">Stable Diffusion</option>
          <option value="Midjourney">Midjourney</option>
        </select>
      </label>
    </BaseNode>
  );
};
