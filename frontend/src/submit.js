import { useStore } from './store';
import { shallow } from 'zustand/shallow';

export const SubmitButton = () => {
    const { nodes, edges } = useStore(
        (state) => ({ nodes: state.nodes, edges: state.edges }),
        shallow
    );

    const handleSubmit = async () => {
        try {
            const res = await fetch('http://localhost:8000/pipelines/parse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nodes, edges }),
            });

            if (!res.ok) {
                throw new Error(`Server error (${res.status})`);
            }

            const data = await res.json();
            if (typeof data.num_nodes !== 'number' || typeof data.num_edges !== 'number' || typeof data.is_dag !== 'boolean') {
                throw new Error('Invalid response from server');
            }

            alert(
`Pipeline Analysis

Nodes: ${data.num_nodes}
Edges: ${data.num_edges}
Is DAG: ${data.is_dag ? 'Yes' : 'No'}`
            );
        } catch (err) {
            alert(`Error: ${err.message}`);
        }
    };

    return (
        <div className="submit-container">
            <button type="submit" className="submit-button" onClick={handleSubmit}>
                Submit
            </button>
        </div>
    );
}
