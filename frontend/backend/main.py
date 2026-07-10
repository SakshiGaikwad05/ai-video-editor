from collections import deque

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_methods=['*'],
    allow_headers=['*'],
)

class PipelineData(BaseModel):
    nodes: list
    edges: list

@app.get('/')
def read_root():
    return {'Ping': 'Pong'}

@app.post('/pipelines/parse')
def parse_pipeline(data: PipelineData):
    edges = data.edges
    nodes = data.nodes

    num_nodes = len(nodes)
    num_edges = len(edges)
    is_dag = _is_dag(edges, nodes)

    return {'num_nodes': num_nodes, 'num_edges': num_edges, 'is_dag': is_dag}


def _is_dag(edges: list, nodes: list) -> bool:
    adj = {}
    in_degree = {}

    for node in nodes:
        nid = node['id']
        adj[nid] = []
        in_degree[nid] = 0

    for edge in edges:
        src = edge['source']
        tgt = edge['target']
        if src not in adj:
            adj[src] = []
            in_degree[src] = 0
        if tgt not in adj:
            adj[tgt] = []
            in_degree[tgt] = 0
        adj[src].append(tgt)
        in_degree[tgt] += 1

    queue = deque([n for n in in_degree if in_degree[n] == 0])
    visited = 0

    while queue:
        node = queue.popleft()
        visited += 1
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return visited == len(in_degree)
