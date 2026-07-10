import { useState } from 'react';
import { Position } from 'reactflow';
import { BaseNode } from './baseNode';

export const DelayNode = ({ id, data }) => {
  const [duration, setDuration] = useState(data?.duration || 1);
  const [unit, setUnit] = useState(data?.unit || 'seconds');

  const handles = [
    { type: 'target', position: Position.Left, id: `${id}-input` },
    { type: 'source', position: Position.Right, id: `${id}-output` },
  ];

  return (
    <BaseNode title="Delay" handles={handles}>
      <label>
        Duration:
        <input type="number" min={0} value={duration} onChange={(e) => setDuration(Number(e.target.value))} />
      </label>
      <label>
        Unit:
        <select value={unit} onChange={(e) => setUnit(e.target.value)}>
          <option value="seconds">Seconds</option>
          <option value="minutes">Minutes</option>
          <option value="hours">Hours</option>
        </select>
      </label>
    </BaseNode>
  );
};
