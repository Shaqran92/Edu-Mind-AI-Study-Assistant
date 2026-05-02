# core/concept_map.py
"""
Concept map generation and visualization for EduMind.
Creates dark-themed, visually appealing knowledge graphs.
Supports both matplotlib (static) and plotly (interactive) rendering.
"""

import os
from typing import Dict, Any, List, Optional
from core.llm import get_provider
from prompts import CONCEPT_MAP_PROMPT
from config import settings

# Dark theme colors matching EduMind UI
BG_COLOR = '#0d1b2a'
NODE_COLORS = ['#00d4aa', '#0984e3', '#6c5ce7', '#e17055', '#fdcb6e', '#00cec9', '#a29bfe', '#fab1a0']
EDGE_COLOR = '#3d5a80'
EDGE_LABEL_COLOR = '#7b8fa3'
NODE_TEXT_COLOR = '#ffffff'
TITLE_COLOR = '#00d4aa'

# Check for plotly
HAS_PLOTLY = False
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    pass

# Check for matplotlib
HAS_MATPLOTLIB = False
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import networkx as nx
    HAS_MATPLOTLIB = True
except ImportError:
    pass


def generate_and_visualize_concept_map(summary_text: str, output_path: str) -> str:
    """
    Orchestrates concept map generation:
    1. Gets structured data from AI provider
    2. Validates the data
    3. Creates a beautiful dark-themed visualization

    Args:
        summary_text: The summary text to analyze
        output_path: Path to save the final PNG image

    Returns:
        Path to saved image, or empty string on failure
    """
    print("-> Starting concept map generation...")

    # 1. Get structured data from the AI
    provider = get_provider()
    concept_data = provider.concept_map(summary_text)

    # 2. Validate the AI-generated data
    if not _is_valid_concept_data(concept_data):
        print("   - AI returned invalid data for the concept map.")
        print("   - Retrying with a simpler request...")
        simple_prompt = f"Extract a list of 10 key terms from this text: {summary_text[:1000]}"
        try:
            fallback_response = provider.answer(simple_prompt, [])
            nodes = [line.strip('- ').strip() for line in fallback_response.split('\n') if line.strip()]
            concept_data = {"nodes": nodes, "edges": []}
            if not _is_valid_concept_data(concept_data):
                return ""
        except Exception:
            return ""

    # 3. Create and save the visualization
    try:
        image_path = _create_visualization(concept_data, output_path)
        return image_path
    except Exception as e:
        print(f"   - Failed to create visualization: {e}")
        return ""


def generate_interactive_concept_map(summary_text: str, output_path: str) -> Optional[str]:
    """
    Generate an interactive concept map using Plotly.
    Returns path to HTML file, or None if plotly is not available.
    """
    if not HAS_PLOTLY or not HAS_MATPLOTLIB:
        return None
    
    provider = get_provider()
    concept_data = provider.concept_map(summary_text)
    
    if not _is_valid_concept_data(concept_data):
        return None
    
    try:
        html_path = output_path.replace('.png', '.html')
        _create_plotly_visualization(concept_data, html_path)
        return html_path
    except Exception as e:
        print(f"   - Failed to create interactive visualization: {e}")
        return None


def _is_valid_concept_data(data: Dict[str, Any]) -> bool:
    """Check if the data is a valid concept map structure."""
    if not isinstance(data, dict):
        return False
    if "nodes" not in data or "edges" not in data:
        return False
    if not isinstance(data["nodes"], list) or not isinstance(data["edges"], list):
        return False
    return len(data["nodes"]) > 0


def _create_visualization(data: Dict[str, Any], output_path: str) -> str:
    """Create a beautiful dark-themed concept map visualization with proper sizing."""
    if not HAS_MATPLOTLIB:
        print("   - matplotlib not available for visualization.")
        return ""
    
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    G = nx.DiGraph()

    # Add nodes
    for node in nodes:
        if isinstance(node, str) and node.strip():
            G.add_node(node.strip())

    # Add edges — handle both list and dict formats
    valid_edge_count = 0
    node_set = set(G.nodes())
    if edges:
        for edge in edges:
            source, target, label = None, None, ""
            if isinstance(edge, list) and len(edge) >= 2:
                source = str(edge[0]).strip()
                target = str(edge[1]).strip()
                label = str(edge[2]).strip() if len(edge) > 2 and edge[2] else ""
            elif isinstance(edge, dict):
                source = str(edge.get('source') or edge.get('from') or edge.get('src', '')).strip()
                target = str(edge.get('target') or edge.get('to') or edge.get('dst', '')).strip()
                label = str(edge.get('label') or edge.get('relationship') or edge.get('relation', '')).strip()
            
            if source and target and source in node_set and target in node_set:
                G.add_edge(source, target, label=label)
                valid_edge_count += 1

    # Auto-generate edges if AI returned none
    if valid_edge_count == 0 and G.number_of_nodes() > 1:
        node_list = list(G.nodes())
        for i in range(len(node_list) - 1):
            G.add_edge(node_list[i], node_list[i + 1], label="relates to")
            valid_edge_count += 1

    if G.number_of_nodes() == 0:
        print("   - No nodes to visualize.")
        return ""

    print(f"   - Visualizing {G.number_of_nodes()} nodes, {valid_edge_count} edges.")

    # ─── Dynamic figure sizing based on node count ───
    num_nodes = G.number_of_nodes()
    if num_nodes <= 5:
        figsize = (12, 8)
        font_size = 12
        node_base = 3000
    elif num_nodes <= 10:
        figsize = (16, 11)
        font_size = 11
        node_base = 2500
    elif num_nodes <= 15:
        figsize = (20, 14)
        font_size = 10
        node_base = 2200
    else:
        figsize = (24, 16)
        font_size = 9
        node_base = 2000

    fig, ax = plt.subplots(figsize=figsize, dpi=150)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    # Layout selection
    pos = None
    try:
        if G.number_of_nodes() <= 20:
            pos = nx.kamada_kawai_layout(G)
        else:
            pos = nx.spring_layout(G, k=1.5, iterations=80, seed=42)
    except Exception:
        try:
            pos = nx.spring_layout(G, k=1.2, iterations=60, seed=42)
        except Exception:
            pos = nx.circular_layout(G)

    # Node sizing based on degree (importance)
    degrees = dict(G.degree())
    min_deg = min(degrees.values(), default=1)
    max_deg = max(degrees.values(), default=1)
    deg_range = max(1, max_deg - min_deg)

    node_sizes = []
    node_colors = []
    for i, node in enumerate(G.nodes()):
        normalized = (degrees[node] - min_deg) / deg_range
        size = node_base + normalized * 3000
        node_sizes.append(size)
        node_colors.append(NODE_COLORS[i % len(NODE_COLORS)])

    # Draw edges with curved connections
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color=EDGE_COLOR,
        width=2.0,
        alpha=0.6,
        arrows=True,
        arrowstyle='-|>',
        arrowsize=20,
        connectionstyle="arc3,rad=0.08",
        min_source_margin=25,
        min_target_margin=25
    )

    # Draw nodes with glow effect
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_size=[s * 1.4 for s in node_sizes],
        node_color=node_colors,
        alpha=0.15,
        linewidths=0
    )
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        alpha=0.9,
        edgecolors='#ffffff',
        linewidths=1.5
    )

    # Draw node labels with word wrapping
    labels = {}
    for node in G.nodes():
        # Wrap long labels
        if len(node) > 15:
            mid = len(node) // 2
            space_idx = node.find(' ', mid)
            if space_idx > 0:
                labels[node] = node[:space_idx] + '\n' + node[space_idx+1:]
            else:
                labels[node] = node
        else:
            labels[node] = node
    
    nx.draw_networkx_labels(
        G, pos, labels=labels, ax=ax,
        font_size=font_size,
        font_weight='bold',
        font_color=NODE_TEXT_COLOR,
        font_family='sans-serif'
    )

    # Draw edge labels
    edge_labels = nx.get_edge_attributes(G, 'label')
    non_empty_labels = {k: v for k, v in edge_labels.items() if v}
    if non_empty_labels:
        nx.draw_networkx_edge_labels(
            G, pos, ax=ax,
            edge_labels=non_empty_labels,
            font_color=EDGE_LABEL_COLOR,
            font_size=max(7, font_size - 2),
            font_family='sans-serif',
            bbox=dict(boxstyle='round,pad=0.2', facecolor=BG_COLOR, edgecolor='none', alpha=0.8)
        )

    # Title
    ax.set_title(
        "Knowledge Concept Map",
        fontsize=min(22, font_size + 8), fontweight='bold', color=TITLE_COLOR,
        pad=20, fontfamily='sans-serif'
    )

    ax.set_axis_off()
    ax.margins(0.12)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.94, bottom=0.02)

    # Save
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    fig.savefig(output_path, format='PNG', facecolor=BG_COLOR, edgecolor='none',
                dpi=150, bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)

    print(f"   - Concept map saved to {output_path}")
    return output_path


def _create_plotly_visualization(data: Dict[str, Any], output_path: str) -> str:
    """Create an interactive concept map using Plotly."""
    if not HAS_PLOTLY or not HAS_MATPLOTLIB:
        return ""
    
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    
    G = nx.DiGraph()
    for node in nodes:
        if isinstance(node, str) and node.strip():
            G.add_node(node.strip())
    
    node_set = set(G.nodes())
    for edge in edges:
        source, target, label = None, None, ""
        if isinstance(edge, list) and len(edge) >= 2:
            source = str(edge[0]).strip()
            target = str(edge[1]).strip()
            label = str(edge[2]).strip() if len(edge) > 2 and edge[2] else ""
        elif isinstance(edge, dict):
            source = str(edge.get('source') or edge.get('from', '')).strip()
            target = str(edge.get('target') or edge.get('to', '')).strip()
            label = str(edge.get('label') or edge.get('relationship', '')).strip()
        
        if source and target and source in node_set and target in node_set:
            G.add_edge(source, target, label=label)
    
    if G.number_of_nodes() == 0:
        return ""
    
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Create edge traces
    edge_x = []
    edge_y = []
    edge_text = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_text.append(edge[2].get('label', ''))
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color=EDGE_COLOR),
        hoverinfo='none',
        mode='lines'
    )
    
    # Create node traces
    node_x = [pos[node][0] for node in G.nodes()]
    node_y = [pos[node][1] for node in G.nodes()]
    node_text = list(G.nodes())
    node_colors_list = [NODE_COLORS[i % len(NODE_COLORS)] for i in range(len(G.nodes()))]
    
    degrees = dict(G.degree())
    node_sizes = [20 + degrees[node] * 10 for node in G.nodes()]
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition="top center",
        textfont=dict(size=12, color='white', family='sans-serif'),
        marker=dict(
            size=node_sizes,
            color=node_colors_list,
            line=dict(width=2, color='white'),
            opacity=0.9
        )
    )
    
    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title=dict(text='Knowledge Concept Map', 
                                   font=dict(size=20, color=TITLE_COLOR)),
                        showlegend=False,
                        hovermode='closest',
                        paper_bgcolor=BG_COLOR,
                        plot_bgcolor=BG_COLOR,
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        margin=dict(l=20, r=20, t=50, b=20)
                    ))
    
    fig.write_html(output_path)
    print(f"   - Interactive concept map saved to {output_path}")
    return output_path