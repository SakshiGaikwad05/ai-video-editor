import { useState } from 'react';
import { Position } from 'reactflow';
import { BaseNode } from './baseNode';

export const DatabaseNode = ({ id, data }) => {
  const [query, setQuery] = useState(data?.query || '');
  const [collection, setCollection] = useState(data?.collection || '');

  const handles = [
    { type: 'target', position: Position.Left, id: `${id}-query` },
    { type: 'source', position: Position.Right, id: `${id}-result` },
  ];

  return (
    <BaseNode title="Database" handles={handles}>
      <label>
        Collection:
        <input type="text" value={collection} onChange={(e) => setCollection(e.target.value)} />
      </label>
      <label>
        Query:
        <textarea value={query} onChange={(e) => setQuery(e.target.value)} rows={2} />
      </label>
    </BaseNode>
  );
};
