"""
Service for creating citation network visualizations.
"""
import networkx as nx
import random
from typing import Dict, List, Tuple


class NetworkVisualizationService:
    """Service for generating citation network visualizations."""

    @staticmethod
    def get_random_colors_with_keys(keys: List[str]) -> Dict[str, str]:
        """Randomly assign colors from a predefined list to the given keys."""
        distinct_colors = [
            '#e6194B', '#3cb44b', '#4363d8', '#f58231', '#911eb4',
            '#42d4f4', '#f032e6', '#bfef45', '#fabed4', '#469990',
            '#dcbeff', '#9A6324', '#fffac8', '#800000', '#aaffc3',
            '#808000', '#ffd8b1', '#000075', '#a9a9a9'
        ]

        num_keys = len(keys)

        if num_keys > len(distinct_colors):
            selected_colors = random.choices(distinct_colors, k=num_keys)
        else:
            selected_colors = random.sample(distinct_colors, num_keys)

        return {key: color for key, color in zip(keys, selected_colors)}

    @staticmethod
    def create_network_graph(citation_dict: Dict[str, List[str]]) -> Tuple[nx.DiGraph, Dict]:
        """
        Create a directed graph from citation dictionary.

        Returns:
            Tuple of (graph, color_palette)
        """
        G = nx.DiGraph()

        # Set of all cited cases
        all_cited_cases = set()
        for cited_cases in citation_dict.values():
            all_cited_cases.update(cited_cases)

        # Set of main cases
        main_cases = set(citation_dict.keys())

        # Cases that are both main and cited
        dual_role_cases = main_cases.intersection(all_cited_cases)

        # Generate color palette
        color_palette = NetworkVisualizationService.get_random_colors_with_keys(list(main_cases))

        # Add nodes and edges
        for main_case, cited_cases in citation_dict.items():
            # Add main case node
            if main_case in dual_role_cases:
                G.add_node(main_case, type='dual', color=color_palette[main_case])
            else:
                G.add_node(main_case, type='main', color=color_palette[main_case])

            # Add cited cases and edges
            for cited_case in cited_cases:
                if cited_case in main_cases:
                    if cited_case not in G:
                        G.add_node(cited_case, type='dual', color=color_palette[cited_case])
                else:
                    if cited_case not in G:
                        G.add_node(cited_case, type='cited', color='#1e90ff')

                G.add_edge(main_case, cited_case, color=color_palette[main_case])

        return G, color_palette

    @staticmethod
    def get_network_data_for_viz(citation_dict: Dict[str, List[str]]) -> Dict:
        """
        Generate network data for frontend visualization.

        Returns:
            Dictionary with nodes, edges, and metadata
        """
        G, color_palette = NetworkVisualizationService.create_network_graph(citation_dict)

        # Use spring layout for positioning
        pos = nx.spring_layout(G, k=0.5, seed=42)

        # Prepare nodes data
        nodes = []
        for node in G.nodes():
            node_data = G.nodes[node]
            nodes.append({
                'id': node,
                'label': node,
                'type': node_data.get('type', 'cited'),
                'color': node_data.get('color', '#1e90ff'),
                'x': pos[node][0],
                'y': pos[node][1]
            })

        # Prepare edges data
        edges = []
        for u, v in G.edges():
            edge_data = G.edges[u, v]
            edges.append({
                'source': u,
                'target': v,
                'color': edge_data.get('color', '#888888')
            })

        # Network statistics
        main_cases = set(citation_dict.keys())
        stats = {
            'main_cases': len(main_cases),
            'total_nodes': G.number_of_nodes(),
            'total_edges': G.number_of_edges(),
            'network_density': round(nx.density(G), 4)
        }

        return {
            'nodes': nodes,
            'edges': edges,
            'stats': stats,
            'color_palette': color_palette
        }
