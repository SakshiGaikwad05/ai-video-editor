import { Handle } from 'reactflow';

export const BaseNode = ({ title, children, handles = [], style = {} }) => {
  return (
    <div className="node-card" style={style}>
      <div className="node-title">{title}</div>

      <div className="node-content">{children}</div>

      {handles.map((handle) => (
        <Handle
          key={handle.id}
          type={handle.type}
          position={handle.position}
          id={handle.id}
          style={handle.style}
        />
      ))}
    </div>
  );
};
