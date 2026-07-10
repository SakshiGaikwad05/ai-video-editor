import { useState } from 'react';
import { Position } from 'reactflow';
import { BaseNode } from './baseNode';

export const EmailNode = ({ id, data }) => {
  const [recipient, setRecipient] = useState(data?.recipient || '');
  const [subject, setSubject] = useState(data?.subject || '');
  const [attachReport, setAttachReport] = useState(data?.attachReport || false);

  const handles = [
    { type: 'target', position: Position.Left, id: `${id}-trigger` },
  ];

  return (
    <BaseNode title="Email" handles={handles}>
      <label>
        To:
        <input type="text" value={recipient} onChange={(e) => setRecipient(e.target.value)} />
      </label>
      <label>
        Subject:
        <input type="text" value={subject} onChange={(e) => setSubject(e.target.value)} />
      </label>
      <label>
        <input type="checkbox" checked={attachReport} onChange={(e) => setAttachReport(e.target.checked)} />
        Attach report
      </label>
    </BaseNode>
  );
};
