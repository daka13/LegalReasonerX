# app.py
import streamlit as st
import requests
import re
import time
import json
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgba
import plotly.graph_objects as go
import random
import concurrent.futures
from functools import lru_cache
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import os

# Set page configuration
st.set_page_config(
    page_title="LegalReasonerX",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #1E3A8A;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .info-box {
        background-color: #F0F7FF;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #BFDBFE;
        margin-bottom: 1rem;
    }
    .citation-box {
        background-color: #F0FFF4;
        padding: 0.5rem;
        border-radius: 0.5rem;
        border: 1px solid #C6F6D5;
        margin-bottom: 0.5rem;
    }
    .error-box {
        background-color: #FEF2F2;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #FECACA;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Application title
st.markdown("<h1 class='main-header'>LegalReasonerX: Legal Document Analysis System</h1>", unsafe_allow_html=True)

# Initialize API token
if 'api_token' not in st.session_state:
    st.session_state.api_token = ""

# Check if OpenAI API key exists in environment variables
openai_api_key = os.environ.get('OPENAI_API_KEY', '')

# Sidebar for API tokens and settings
with st.sidebar:
    st.header("Settings")
    
    # CourtListener API token
    court_listener_token = st.text_input(
        "CourtListener API Token", 
        value=st.session_state.api_token,
        type="password",
        help="Enter your CourtListener API token. You can get one by registering at https://www.courtlistener.com/."
    )
    
    # OpenAI API key (if needed for reasoning framework)
    openai_key = st.text_input(
        "OpenAI API Key (Optional)",
        value=openai_api_key,
        type="password",
        help="Enter your OpenAI API key if you want to use the precedent-driven reasoning framework."
    )
    
    # Save buttons
    if st.button("Save API Keys"):
        st.session_state.api_token = court_listener_token
        os.environ['OPENAI_API_KEY'] = openai_key
        st.success("API keys saved!")
    
    st.divider()
    st.markdown("### About")
    st.markdown("""
    **LegalReasonerX** is a framework for legal document analysis and reasoning. 
    It can extract citations, identify precedents, visualize citation networks, 
    and analyze legal reasoning patterns.
    """)

# Main tab interface
tabs = st.tabs(["Citation Lookup", "Precedent Network", "Opinion Analysis", "Reasoning Framework"])

# Utility functions
def make_get_request(url, api_token):
    """Make a GET request to the CourtListener API."""
    headers = {'Authorization': f'Token {api_token}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code} - {response.text}")
        return None

def verify_citation_in_text(text, api_token):
    """Verify citations within text using the Citation Lookup API."""
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    headers = {
        "Authorization": f"Token {api_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"text": text}
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code} - {response.text}")
        return None

# Cache responses
@lru_cache(maxsize=1024)
def make_get_request_cached(url, api_token):
    """Cached version of make_get_request"""
    return make_get_request(url, api_token)

def fetch_all_urls_parallel(urls, api_token, max_workers=10):
    """Fetch multiple URLs in parallel using ThreadPoolExecutor"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Map URLs to futures and collect results
        future_to_url = {executor.submit(make_get_request_cached, url, api_token): url for url in urls}
        results = {}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results[url] = future.result()
            except Exception as exc:
                st.error(f"Error fetching {url}: {exc}")
                results[url] = None
    return results

def get_precedents(case_code, api_token):
    """Process a citation and extract precedent case names."""
    
    # Show a spinner while processing
    with st.spinner("Processing citation and extracting precedents..."):
        # Get citation information from the API
        lookup_results = verify_citation_in_text(case_code, api_token)
        
        if not lookup_results:
            return "API returned no results."
        
        # Error mapping for better error handling
        error_dict = {
            404: "[Not Found] Citation is valid but not found in CourtListener.",
            400: "[Bad Request] Citation format recognized but reporter not in our system.",
            300: "[Multiple Choices] Citation matched multiple items in CourtListener.",
            429: "[Too Many Requests] Only 250 citations can be processed in a single request."
        }
        
        # Filter to valid results
        valid_results = [r for r in lookup_results if r.get('status') == 200 and r.get('clusters')]
        
        if not valid_results:
            status = lookup_results[0].get('status')
            return error_dict.get(status, f"Unknown error: status {status}")
        
        # Collect all opinion links per cluster
        opinions_per_cluster = {}
        citation_caseName_map = {}
        for result in valid_results:
            for cluster in result.get('clusters', []):
                all_opinion_links = []
                if cluster.get('sub_opinions') == []:
                    continue
                all_opinion_links.extend(cluster.get('sub_opinions'))
                opinions_per_cluster[(cluster.get('case_name'), result.get("citation"))] = cluster.get('sub_opinions')
                citation_caseName_map[cluster.get('case_name')] = result.get("citation")
        
        if not opinions_per_cluster:
            return "Error: Citations were recognized but no opinions found."
        
        base_opinion_responses_combined = {}
        precedents_opinion_responses_combined = {}
        precedents_cluster_responses_combined = []
        caseName_to_precedent_map = {}
        
        # Parallel fetch all opinions
        for (case_name, _), opinion_links in opinions_per_cluster.items():
            opinion_responses = fetch_all_urls_parallel(opinion_links, api_token)
            base_opinion_responses_combined.update(opinion_responses)
            
            # Extract all cited opinion links
            all_cited_opinions = set()
            for url, response in opinion_responses.items():
                if response:
                    all_cited_opinions.update(response.get("opinions_cited"))
            
            if not all_cited_opinions:
                st.info(f"{case_name} has no precedents found.")
                continue
            
            # Parallel fetch all cited opinions to get their clusters
            cited_opinion_responses = fetch_all_urls_parallel(all_cited_opinions, api_token)
            precedents_opinion_responses_combined.update({case_name: cited_opinion_responses})
            
            # Extract cluster links
            cluster_links = set()
            opinion_to_cluster = {}
            for url, response in cited_opinion_responses.items():
                if response and response.get("cluster"):
                    opinion_to_cluster[url] = response.get("cluster")
                    cluster_links.add(response.get("cluster"))
            
            # Parallel fetch all cluster data
            cluster_responses = fetch_all_urls_parallel(cluster_links, api_token)
            precedents_cluster_responses_combined.append((case_name, cluster_responses))
            
            # Create mapping from cluster link to case name
            cluster_data_map = {url: response.get("case_name") 
                               for url, response in cluster_responses.items() 
                               if response}
            
            # Map each opinion to its corresponding case name
            precedents = [cluster_data_map[opinion_to_cluster[link]] 
                         for link in all_cited_opinions 
                         if link in opinion_to_cluster and opinion_to_cluster[link] in cluster_data_map]
            
            caseName_to_precedent_map[case_name] = precedents
        
        return (opinions_per_cluster, opinion_to_cluster, citation_caseName_map, 
                base_opinion_responses_combined, precedents_opinion_responses_combined, 
                precedents_cluster_responses_combined, caseName_to_precedent_map, cluster_data_map)

# Visualization functions
def get_random_colors_with_keys(keys):
    """Randomly assign colors from a predefined list to the given keys."""
    distinct_colors = [
        '#e6194B', '#3cb44b', '#4363d8', '#f58231', '#911eb4',
        '#42d4f4', '#f032e6', '#bfef45', '#fabed4', '#469990',
        '#dcbeff', '#9A6324', '#fffac8', '#800000', '#aaffc3',
        '#808000', '#ffd8b1', '#000075', '#a9a9a9'
    ]
    
    num_keys = len(keys)
    
    # Select colors (with potential repeats if more keys than colors)
    if num_keys > len(distinct_colors):
        selected_colors = random.choices(distinct_colors, k=num_keys)
    else:
        selected_colors = random.sample(distinct_colors, num_keys)
    
    # Create a dictionary mapping keys to colors
    color_dict = {key: color for key, color in zip(keys, selected_colors)}
    
    return color_dict

def create_static_citation_network(citation_dict, output_file='citation_network.png',
                                  color_palette=None, figsize=(12, 10), dpi=300):
    """Create a static citation network visualization."""
    # Create a directed graph
    G = nx.DiGraph()
    
    # Set of all cited cases to identify cases that are both main and cited
    all_cited_cases = set()
    for cited_cases in citation_dict.values():
        all_cited_cases.update(cited_cases)
    
    # Set of main cases
    main_cases = set(citation_dict.keys())
    
    # Cases that are both main and cited
    dual_role_cases = main_cases.intersection(all_cited_cases)
    
    # Generate color palette if not provided
    if color_palette is None:
        color_palette = get_random_colors_with_keys(main_cases)
    
    # Add nodes and edges from the citation dictionary
    for main_case, cited_cases in citation_dict.items():
        # Add main case node with its attributes
        if main_case in dual_role_cases:
            G.add_node(main_case, type='dual', color=color_palette[main_case])
        else:
            G.add_node(main_case, type='main', color=color_palette[main_case])
        
        # Add cited cases and edges
        for cited_case in cited_cases:
            if cited_case in main_cases:
                # This cited case is also a main case
                if cited_case not in G:
                    G.add_node(cited_case, type='dual', color=color_palette[cited_case])
            else:
                # This is only a cited case
                if cited_case not in G:
                    G.add_node(cited_case, type='cited', color='#1e90ff')
            
            G.add_edge(main_case, cited_case, color=color_palette[main_case])
    
    # Create abbreviated labels for display
    def abbreviate_case_name(name):
        if len(name) > 25:
            parts = name.split(' v. ') if ' v. ' in name else [name]
            if len(parts) > 1:
                return f"{parts[0][:10]}... v.\n{parts[1][:10]}..."
            else:
                return name[:20] + "..."
        return name.replace(' v. ', ' v.\n')
    
    # Create a figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Use a spring layout for positioning nodes
    pos = nx.spring_layout(G, k=0.5, seed=42)
    
    # Add a subtle background grid
    plt.grid(alpha=0.1)
    
    # Draw edges with different colors for each main case
    edge_colors = []
    for u, v in G.edges():
        edge_colors.append(G.edges[u, v]['color'])
    
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.7, arrows=True,
                         edge_color=edge_colors, arrowsize=15)
    
    # Draw nodes with different colors and sizes based on type
    node_colors = []
    node_sizes = []
    node_borders = []
    node_border_widths = []
    
    for node in G.nodes():
        node_type = G.nodes[node]['type']
        color = G.nodes[node]['color']
        
        if node_type == 'main':
            node_sizes.append(1000)
            node_borders.append('black')
            node_border_widths.append(2)
        elif node_type == 'dual':
            node_sizes.append(800)
            # Create a lighter background for the border
            node_borders.append('white')
            node_border_widths.append(3)
        else:  # 'cited'
            node_sizes.append(500)
            node_borders.append('#888888')
            node_border_widths.append(1)
        
        node_colors.append(color)
    
    # Draw the nodes
    nx.draw_networkx_nodes(G, pos, node_color=node_colors,
                         node_size=node_sizes, alpha=0.9,
                         edgecolors=node_borders, linewidths=node_border_widths)
    
    # Create labels with abbreviated names
    labels = {node: abbreviate_case_name(node) for node in G.nodes()}
    
    # Draw the labels with a slight offset to avoid overlap with nodes
    label_pos = {k: (v[0], v[1] - 0.05) for k, v in pos.items()}
    nx.draw_networkx_labels(G, label_pos, labels=labels, font_size=9,
                          font_family='sans-serif', font_weight='bold')
    
    # Add legend for main cases
    legend_patches = []
    for case, color in color_palette.items():
        if case in G.nodes():
            if G.nodes[case]['type'] == 'main':
                label = f"Main: {abbreviate_case_name(case)}"
            else:
                label = f"Dual: {abbreviate_case_name(case)}"
            patch = mpatches.Patch(color=color, label=label)
            legend_patches.append(patch)
    
    # Add a legend entry for cited cases
    if any(G.nodes[n]['type'] == 'cited' for n in G.nodes()):
        cited_patch = mpatches.Patch(color='#1e90ff', label='Cited Cases')
        legend_patches.append(cited_patch)
    
    # Create the legend with a smaller font
    plt.legend(handles=legend_patches, ncol=2, fontsize=8)
    
    # Set title and remove axis
    plt.title("Citation Network", fontsize=16, pad=20)
    plt.axis('off')
    
    # Add network statistics as text
    stats_text = (
        f"Network Statistics:\n"
        f"Main Cases: {len(main_cases)}\n"
        f"Total Nodes: {G.number_of_nodes()}\n"
        f"Total Edges: {G.number_of_edges()}\n"
        f"Network Density: {nx.density(G):.3f}"
    )
    
    plt.text(0.02, 0.02, stats_text, transform=plt.gca().transAxes,
            fontsize=9, verticalalignment='bottom',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.7))
    
    # Adjust layout
    plt.tight_layout()
    
    return fig, G

def create_interactive_citation_network(citation_dict, color_palette=None):
    """Create an interactive citation network visualization using Plotly."""
    # Create a directed graph
    G = nx.DiGraph()
    
    # Set of all cited cases to identify cases that are both main and cited
    all_cited_cases = set()
    for cited_cases in citation_dict.values():
        all_cited_cases.update(cited_cases)
    
    # Set of main cases
    main_cases = set(citation_dict.keys())
    
    # Cases that are both main and cited
    dual_role_cases = main_cases.intersection(all_cited_cases)
    
    # Generate color palette if not provided
    if color_palette is None:
        color_palette = get_random_colors_with_keys(main_cases)
    
    # Add nodes and edges from the citation dictionary
    for main_case, cited_cases in citation_dict.items():
        # Add main case node
        if main_case in dual_role_cases:
            G.add_node(main_case, type='dual', color=color_palette[main_case])
        else:
            G.add_node(main_case, type='main', color=color_palette[main_case])
        
        # Add cited cases and edges
        for cited_case in cited_cases:
            if cited_case in main_cases:
                # This cited case is also a main case
                if cited_case not in G:
                    G.add_node(cited_case, type='dual', color=color_palette[cited_case])
            else:
                # This is only a cited case
                if cited_case not in G:
                    G.add_node(cited_case, type='cited', color='#1e90ff')
            
            G.add_edge(main_case, cited_case, color=color_palette[main_case])
    
    # Use spring layout for node positioning with fixed seed for reproducibility
    pos = nx.spring_layout(G, k=0.5, seed=42)
    
    # Create abbreviated labels for display
    def abbreviate_case_name(name):
        if len(name) > 25:
            parts = name.split(' v. ') if ' v. ' in name else [name]
            if len(parts) > 1:
                return f"{parts[0][:12]}... v. {parts[1][:12]}..."
            else:
                return name[:25] + "..."
        return name
    
    # Prepare separate node traces for main, cited, and dual-role cases
    node_traces = []
    
    # Create separate traces for each main case (for legend)
    for main_case in main_cases:
        node_color = color_palette[main_case]
        nodes_of_this_type = [n for n in G.nodes() if n == main_case or 
                             (G.nodes[n].get('type') == 'cited' and (main_case, n) in G.edges())]
        
        if main_case in G.nodes() and G.nodes[main_case]['type'] in ['main', 'dual']:
            trace = go.Scatter(
                x=[pos[main_case][0]],
                y=[pos[main_case][1]],
                mode='markers+text',
                marker=dict(
                    color=node_color,
                    size=25,
                    line=dict(width=1, color='black')
                ),
                text=[abbreviate_case_name(main_case)],
                textposition="top center",
                textfont=dict(
                    color="black",  # Black text
                    size=12,        # Slightly larger
                    family="Arial"
                ),
                hoverinfo='text',
                hovertext=[main_case],
                name=f"Main: {abbreviate_case_name(main_case)}"
            )
            node_traces.append(trace)
    
    # Add trace for cited cases (not main cases)
    cited_only_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'cited']
    if cited_only_nodes:
        cited_trace = go.Scatter(
            x=[pos[n][0] for n in cited_only_nodes],
            y=[pos[n][1] for n in cited_only_nodes],
            mode='markers+text',
            marker=dict(
                color='#1e90ff',
                size=15,
                line=dict(width=1, color='black')
            ),
            text=[abbreviate_case_name(n) for n in cited_only_nodes],
            textposition="bottom center",
            textfont=dict(
                color="black",
                size=12,
                family="Arial"
            ),
            hoverinfo='text',
            hovertext=cited_only_nodes,
            name='Cited Cases Only'
        )
        node_traces.append(cited_trace)
    
    # Add trace for dual-role cases (both main and cited)
    dual_role_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'dual' and n != main_case]
    if dual_role_nodes:
        for node in dual_role_nodes:
            dual_trace = go.Scatter(
                x=[pos[node][0]],
                y=[pos[node][1]],
                mode='markers+text',
                marker=dict(
                    color=G.nodes[node]['color'],
                    size=20,
                    line=dict(width=2, color='white')
                ),
                text=[abbreviate_case_name(node)],
                textposition="bottom center",
                textfont=dict(
                    color="black",
                    size=12,
                    family="Arial"
                ),
                hoverinfo='text',
                hovertext=[node],
                name=f"Dual: {abbreviate_case_name(node)}"
            )
            node_traces.append(dual_trace)
    
    # Create edge traces
    edge_traces = []
    
    # Group edges by main case for coloring
    for main_case in main_cases:
        edge_x = []
        edge_y = []
        
        # Get edges from this main case
        case_edges = [(u, v) for u, v in G.edges() if u == main_case]
        
        for edge in case_edges:
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            # Calculate the arrow endpoint (slightly before the actual node)
            ratio = 0.9  # How far along the edge to place the arrowhead
            arrow_x = x0 + ratio * (x1 - x0)
            arrow_y = y0 + ratio * (y1 - y0)
            
            edge_x.extend([x0, arrow_x, None])
            edge_y.extend([y0, arrow_y, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1.5, color=color_palette[main_case]),
            hoverinfo='none',
            mode='lines',
            name=f"Citations from {abbreviate_case_name(main_case)}"
        )
        edge_traces.append(edge_trace)
    
    # Create figure with all traces
    fig = go.Figure(
        data=edge_traces + node_traces,
        layout=go.Layout(
            title="Precedent Network",
            title_font=dict(family="Arial", size=20, color="black"),  # Ensure title is visible
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=800,
            paper_bgcolor='white',  # White background for the figure
            plot_bgcolor='white',   # White background for the plot area
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor="black",
                borderwidth=1,
                font=dict(
                    size=14,
                    color="black"
                )
            )
        )
    )
    
    # Improve hover labels
    fig.update_layout(hoverlabel=dict(
        bgcolor="#333333",
        font_size=14,
        font_family="Arial",
        font_color="white",
        bordercolor="white"
    ))
    
    # Add arrows to the edges
    annotations = []
    for main_case in main_cases:
        case_edges = [(u, v) for u, v in G.edges() if u == main_case]
        for u, v in case_edges:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            
            # Calculate the arrow endpoint
            ratio = 0.9
            arrow_x = x0 + ratio * (x1 - x0)
            arrow_y = y0 + ratio * (y1 - y0)
            
            annotations.append(dict(
                ax=x0, ay=y0,
                axref='x', ayref='y',
                x=arrow_x, y=arrow_y,
                xref='x', yref='y',
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=1,
                arrowcolor=color_palette[main_case]
            ))
    
    fig.update_layout(annotations=annotations)
    
    # Add network metrics as annotations with better visibility
    metrics_text = (
        f"<b>Network Metrics:</b><br>"
        f"Main Cases: {len(main_cases)}<br>"
        f"Total Nodes: {G.number_of_nodes()}<br>"
        f"Total Edges: {G.number_of_edges()}<br>"
        f"Network Density: {nx.density(G):.4f}<br>"
    )
    
    fig.add_annotation(
        x=0.01, y=0.01,
        xref="paper", yref="paper",
        text=metrics_text,
        showarrow=False,
        font=dict(family="Arial", size=12, color="black"),
        align="left",
        bgcolor="rgba(255, 255, 255, 0.9)",
        bordercolor="black",
        borderwidth=1,
        borderpad=4
    )
    
    return fig, G

# Opinion extraction and analysis functions
def extract_text_from_html(html_string):
    """Parse HTML and extract text content."""
    if not html_string:
        return ""
    
    try:
        # Parse the HTML
        soup = BeautifulSoup(html_string, 'html.parser')
        
        # Extract all text
        text = soup.get_text()
        
        # Normalize whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        st.error(f"Error processing HTML: {e}")
        return ""

def extract_text_from_xml(xml_string):
    """Parse XML and extract text content."""
    if not xml_string:
        return ""
    
    try:
        # Parse the XML
        root = ET.fromstring(xml_string)
        
        # Extract all text
        text_list = _extract_text_recursive(root)
        
        # Normalize whitespace
        text = '\n'.join(line.strip() for line in text_list if line.strip())
        text = text.replace('\n\n', '\n')  # Remove double newlines
        
        return text
    except ET.ParseError as e:
        st.error(f"Error parsing XML: {e}")
        return ""
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return ""

def _extract_text_recursive(element):
    """Recursively extract text from an XML element and its children."""
    text_list = []
    if element.text:
        text_list.append(element.text)
    for child in element:
        text_list.extend(_extract_text_recursive(child))
    if element.tail:
        text_list.append(element.tail)
    return text_list

def extract_opinion(data):
    """Extract opinion text from various formats."""
    if data.get("html_with_citations") != "":
        opinion = extract_text_from_html(data.get("html_with_citations"))
    elif data.get("html_columbia") != "":
        opinion = extract_text_from_html(data.get("html_columbia"))
    elif data.get("html_lawbox") != "":
        opinion = extract_text_from_html(data.get("html_lawbox"))
    elif data.get("xml_harvard") != "":
        opinion = extract_text_from_xml(data.get("xml_harvard"))
    elif data.get("html_anon_2020") != "":
        opinion = extract_text_from_html(data.get("html_anon_2020"))
    elif data.get("html") != "":
        opinion = extract_text_from_html(data.get("html"))
    else:
        opinion = data.get("plain_text")
    
    return opinion

def get_opinion_type_map(opinion_type):
    """Map opinion type codes to readable names."""
    type_map = {
        "010combined": "Combined Opinion", 
        "020lead": "Lead Opinion", 
        "030concurrence": "Concurrence Opinion",
        "040dissent": "Dissent",
        "015unamimous": "Unanimous Opinion", 
        "025plurality": "Plurality Opinion", 
        "035concurrenceinpart": "In Part Opinion",
        "050addendum": "Addendum", 
        "060remittitur": "Remittitur", 
        "070rehearing": "Rehearing", 
        "080onthemerits": "On the Merits",
        "090onmotiontostrike": "On Motion to Strike Cost Bill", 
        "100trialcourt": "Trial Court Document"
    }
    return type_map.get(opinion_type, "Unknown Opinion Type")

def get_all_opinions(opinions_per_cluster, base_opinion_responses_combined,
                     precedents_opinion_responses_combined, cluster_data_map,
                     opinion_to_cluster):
    """Extract all base and precedent opinions."""
    base_opinions = {}
    precedent_opinions = {}
    
    for (case_name, citation), opinion_links in opinions_per_cluster.items():
        # BASE OPINION
        base_opinions[case_name] = []
        for i, opinion_link in enumerate(opinion_links):
            data = base_opinion_responses_combined[opinion_link]
            
            # Extract details
            details = {}
            # Opinion text
            opinion = extract_opinion(data)
            if opinion is None:
                continue
            # Opinion type
            opinion_type = get_opinion_type_map(data.get("type"))
            # Opinion link
            link = f"https://www.courtlistener.com{data.get('absolute_url')}"
            
            details[f"Base Opinion {i+1}"] = {
                "opinion": opinion, 
                "type": opinion_type,
                "link": link,
                "citation": citation,
                "case_name": case_name
            }
            
            base_opinions[case_name].append(details)
        
        # PRECEDENT OPINIONS
        precedent_opinions[case_name] = []
        for i, (opinion_link, data) in enumerate(precedents_opinion_responses_combined[case_name].items()):
            details = {}
            # Opinion text
            opinion = extract_opinion(data)
            if opinion is None:
                continue
            # Opinion type
            opinion_type = get_opinion_type_map(data.get("type"))
            # Opinion link
            link = f"https://www.courtlistener.com{data.get('absolute_url')}"
            
            # Get precedent case name from cluster
            try:
                precedent_case_name = cluster_data_map[opinion_to_cluster[opinion_link]]
            except KeyError:
                precedent_case_name = "Unknown Case"
            
            details[f"Precedent Opinion {i+1}"] = {
                "opinion": opinion, 
                "type": opinion_type,
                "link": link,
                "citation": citation,
                "case_name": precedent_case_name
            }
            
            precedent_opinions[case_name].append(details)
    
    return base_opinions, precedent_opinions

def create_formatted_data(opinion_data, case_name):
    """Format opinion data for display or processing."""
    all_opinion = ""
    delimiter = "="*50
    
    for precedent in opinion_data[case_name]:
        for title, data in precedent.items():
            opinion = (
                f"{title}\n"
                f"Case name: {data['case_name']}\n"
                f"Opinion type: {data['type']}\n"
                f"Source link: {data['link']}\n\n"
                f"{data['opinion']}\n{delimiter}\n\n"
            )
            all_opinion += opinion
    
    return all_opinion

# Add this near the top of your app, before any other elements
st.markdown("""
<style>
.info-box {
    background-color: white;  /* Keep your white background */
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 15px;
    margin-bottom: 15px;
    color: #333;  /* This sets the text color to dark gray */
}

.citation-box {
    background-color: #f9f9f9;
    border-left: 3px solid #2c3e50;
    padding: 10px;
    margin: 10px 0;
    color: black;  /* Black text */
    font-weight: bold;  /* Bold text */
}

.error-box {
    background-color: #ffebee;
    border: 1px solid #ffcdd2;
    border-radius: 5px;
    padding: 15px;
    margin-bottom: 15px;
    color: #b71c1c;  /* Dark red text */
}

/* Style for subheaders */
.sub-header {
    color: #2c3e50;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)


# Implementation for Citation Lookup tab
with tabs[0]:
    st.markdown("<h2 class='sub-header'>Citation Lookup</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    Use this tool to verify legal citations and extract precedent cases. 
    Enter a legal citation (e.g., "179 U.S. 77") or a text containing citations.
    </div>
    """, unsafe_allow_html=True)
    
    # Input for citation or text with citations
    citation_input = st.text_area(
        "Enter a legal citation or text with citations",
        height=100,
        key="citation_input",
        help="Example: 179 U.S. 77 or Warner-Jenkinson Co. v. Hilton Davis Chemical Co., 520 U.S. 17 (1997)"
    )
    
    # Check if API token is set
    if not st.session_state.api_token:
        st.warning("Please enter your CourtListener API token in the sidebar before proceeding.")
        process_citation = False
    else:
        process_citation = st.button("Process Citation")
    
    if process_citation and citation_input:
        result = get_precedents(citation_input, st.session_state.api_token)
        
        if isinstance(result, str):
            # Display error message
            st.error(result)
        else:
            # Unpack the result
            (opinions_per_cluster, opinion_to_cluster, citation_caseName_map, 
             base_opinion_responses_combined, precedents_opinion_responses_combined, 
             precedents_cluster_responses_combined, caseName_to_precedent_map, 
             cluster_data_map) = result
            
            # Save the result in session state for use in other tabs
            st.session_state.precedent_data = {
                "opinions_per_cluster": opinions_per_cluster,
                "opinion_to_cluster": opinion_to_cluster,
                "citation_caseName_map": citation_caseName_map,
                "base_opinion_responses_combined": base_opinion_responses_combined,
                "precedents_opinion_responses_combined": precedents_opinion_responses_combined,
                "precedents_cluster_responses_combined": precedents_cluster_responses_combined,
                "caseName_to_precedent_map": caseName_to_precedent_map,
                "cluster_data_map": cluster_data_map
            }
            
            # Display the citation mapping
            st.markdown("<h3 class='sub-header'>Citation Information</h3>", unsafe_allow_html=True)
            
            # Create a table of citations
            citation_df = pd.DataFrame(
                [(case, citation) for case, citation in citation_caseName_map.items()],
                columns=["Case Name", "Citation"]
            )
            st.dataframe(citation_df, use_container_width=True)
            
            # Display precedent information
            st.markdown("<h3 class='sub-header'>Precedent Cases</h3>", unsafe_allow_html=True)
            
            # Create tabs for each main case
            case_tabs = st.tabs(list(caseName_to_precedent_map.keys()))
            
            for i, (case_name, precedents) in enumerate(caseName_to_precedent_map.items()):
                with case_tabs[i]:
                    if precedents:
                        st.markdown(f"**{case_name}** cites the following cases:")
                        
                        # Display precedents in a formatted way
                        for precedent in precedents:
                            st.markdown(f"""
                            <div class="citation-box">
                            {precedent}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Show total count
                        st.info(f"Total precedents cited: {len(precedents)}")
                    else:
                        st.info("No precedents found for this case.")

# Implementation for Precedent Network tab
with tabs[1]:
    st.markdown("<h2 class='sub-header'>Precedent Network Visualization</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    This tool visualizes the citation network between cases. It shows which cases cite which other cases,
    helping you understand the precedent relationships.
    </div>
    """, unsafe_allow_html=True)
    
    # Check if we have precedent data
    if 'precedent_data' not in st.session_state:
        st.warning("Please first process a citation in the Citation Lookup tab.")
    else:
        # Offer visualization options
        viz_type = st.radio(
            "Select visualization type:",
            ["Static Network", "Interactive Network"],
            horizontal=True
        )
        
        # Get the data from session state
        precedent_data = st.session_state.precedent_data
        caseName_to_precedent_map = precedent_data["caseName_to_precedent_map"]
        
        if viz_type == "Static Network":
            # Create static visualization
            fig, G = create_static_citation_network(caseName_to_precedent_map)
            st.pyplot(fig)
            
            # Show network statistics
            st.markdown("<h3 class='sub-header'>Network Statistics</h3>", unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Main Cases", len(caseName_to_precedent_map.keys()))
            with col2:
                st.metric("Total Nodes", G.number_of_nodes())
            with col3:
                st.metric("Total Edges", G.number_of_edges())
            with col4:
                st.metric("Network Density", f"{nx.density(G):.4f}")
            
        else:  # Interactive Network
            # Create interactive visualization
            fig, G = create_interactive_citation_network(caseName_to_precedent_map)
            st.plotly_chart(fig, use_container_width=True)
            
            # Legend for interactive chart
            st.markdown("""
            **Interactive Controls:**
            - Hover over nodes to see full case names
            - Click and drag to pan
            - Scroll to zoom
            - Double-click on legend items to isolate them
            - Click on legend items to toggle visibility
            """)

# Implementation for Opinion Analysis tab
with tabs[2]:
    st.markdown("<h2 class='sub-header'>Opinion Extraction & Analysis</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    This tool extracts and analyzes opinions from legal cases. It allows you to view the full text 
    of opinions and understand the legal reasoning.
    </div>
    """, unsafe_allow_html=True)
    
    # Check if we have precedent data
    if 'precedent_data' not in st.session_state:
        st.warning("Please first process a citation in the Citation Lookup tab.")
    else:
        # Get the data from session state
        precedent_data = st.session_state.precedent_data
        
        # Extract opinions
        with st.spinner("Extracting opinions..."):
            # Get all opinions (base and precedent)
            base_opinions, precedent_opinions = get_all_opinions(
                precedent_data["opinions_per_cluster"],
                precedent_data["base_opinion_responses_combined"],
                precedent_data["precedents_opinion_responses_combined"],
                precedent_data["cluster_data_map"],
                precedent_data["opinion_to_cluster"]
            )
            
            # Save opinions in session state
            st.session_state.base_opinions = base_opinions
            st.session_state.precedent_opinions = precedent_opinions
        
        # Display options for viewing opinions
        case_names = list(base_opinions.keys())
        selected_case = st.selectbox("Select a case:", case_names)
        
        opinion_type = st.radio(
            "Select opinion type:",
            ["Base Opinion", "Precedent Opinions"],
            horizontal=True
        )
        
        if opinion_type == "Base Opinion":
            # Display base opinions
            if selected_case in base_opinions and base_opinions[selected_case]:
                # Create tabs for multiple opinions if they exist
                opinion_tabs = st.tabs([list(opinion.keys())[0] for opinion in base_opinions[selected_case]])
                
                for i, opinion_data in enumerate(base_opinions[selected_case]):
                    with opinion_tabs[i]:
                        opinion_title = list(opinion_data.keys())[0]
                        opinion_details = opinion_data[opinion_title]
                        
                        # Display opinion metadata
                        st.markdown(f"""
                        **Case Name:** {opinion_details['case_name']}  
                        **Citation:** {opinion_details['citation']}  
                        **Opinion Type:** {opinion_details['type']}  
                        **Source:** [{opinion_details['link']}]({opinion_details['link']})
                        """)
                        
                        # Display full text of opinion in an expandable section
                        with st.expander("View Full Opinion", expanded=False):
                            st.markdown(opinion_details['opinion'])
                        
                        # Option to analyze entities in the opinion
                        if st.button(f"Extract Entities from {opinion_title}", key=f"entities_{i}"):
                            with st.spinner("Extracting entities..."):
                                # This would typically use an NLP model or OpenAI API
                                # For now, just display a placeholder
                                st.markdown("""
                                **Extracted Entities:**
                                - Judge Smith: Presiding judge
                                - Jane Doe: Plaintiff
                                - John Smith: Defendant
                                - Acme Corp: Corporate entity
                                """)
            else:
                st.info(f"No base opinions found for {selected_case}.")
        
        else:  # Precedent Opinions
            # Display precedent opinions
            if selected_case in precedent_opinions and precedent_opinions[selected_case]:
                # Create a selection for precedent opinions
                precedent_list = [list(opinion.keys())[0] for opinion in precedent_opinions[selected_case]]
                selected_precedent = st.selectbox("Select a precedent opinion:", precedent_list)
                
                # Find the selected precedent
                for opinion_data in precedent_opinions[selected_case]:
                    if selected_precedent in opinion_data:
                        opinion_details = opinion_data[selected_precedent]
                        
                        # Display opinion metadata
                        st.markdown(f"""
                        **Case Name:** {opinion_details['case_name']}  
                        **Citation:** {opinion_details['citation']}  
                        **Opinion Type:** {opinion_details['type']}  
                        **Source:** [{opinion_details['link']}]({opinion_details['link']})
                        """)
                        
                        # Display full text of opinion in an expandable section
                        with st.expander("View Full Opinion", expanded=False):
                            st.markdown(opinion_details['opinion'])
                        
                        # # Option to compare with base opinion
                        # if st.button("Compare with Base Opinion"):
                        #     st.markdown("<h3 class='sub-header'>Opinion Comparison</h3>", unsafe_allow_html=True)
                        #     st.info("This feature would use NLP to compare the base and precedent opinions, highlighting similarities and differences in legal reasoning.")
                
                # Show total count
                st.info(f"Total precedent opinions: {len(precedent_opinions[selected_case])}")
            else:
                st.info(f"No precedent opinions found for {selected_case}.")

# Implementation for Reasoning Framework tab
with tabs[3]:
    st.markdown("<h2 class='sub-header'>Precedent-Driven Reasoning Framework</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    This advanced tool uses AI to analyze how precedent cases support legal arguments in the base case.
    It extracts the legal reasoning and connects it to supporting precedents.
    
    ⚠️ Note: This feature requires an OpenAI API key to be set in the sidebar.
    </div>
    """, unsafe_allow_html=True)
    
    # Check if we have opinion data and OpenAI API key
    if 'base_opinions' not in st.session_state or 'precedent_opinions' not in st.session_state:
        st.warning("Please first process a citation and extract opinions in the previous tabs.")
    elif not os.environ.get('OPENAI_API_KEY'):
        st.warning("Please enter your OpenAI API key in the sidebar to use this feature.")
    else:
        try:
            # Import OpenAI
            from openai import OpenAI
            client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
            
            # Get the opinions from session state
            base_opinions = st.session_state.base_opinions
            precedent_opinions = st.session_state.precedent_opinions
            
            # Select a case for analysis
            case_names = list(base_opinions.keys())
            selected_case = st.selectbox("Select a case for analysis:", case_names)
            
            if st.button("Run Reasoning Analysis"):
                with st.spinner("Analyzing legal reasoning... This may take a minute or two."):
                    # Format the opinions for analysis
                    base_opinion_text = create_formatted_data(base_opinions, selected_case)
                    precedent_opinion_text = create_formatted_data(precedent_opinions, selected_case)
                    
                    # Argument extraction prompt
                    argument_backstory = """
                    You are a seasoned argument developer who analyzes base opinions and extracts the argument.
                    This argument will then be passed to another agent to understand how the precedent supports the argument.
                    """
                    
                    # Extract the argument from base opinion
                    argument_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": argument_backstory},
                            {"role": "user", "content": f"What is the argument in {base_opinion_text}"}
                        ]
                    )
                    
                    argument = argument_response.choices[0].message.content
                    
                    # Save argument in session state
                    st.session_state.argument = argument
                    
                    # Precedent analysis prompt
                    precedent_backstory = """
                    You are a highly experienced Legal Analyst, renowned for your exceptional ability to deconstruct complex judicial opinions and master the application of stare decisis.
                    You possess a deep knowledge of common law principles and excel at identifying the precise ratio decidendi of a case, distinguishing it from dicta, and mapping its legal reasoning.
                    
                    You will analyze how precedent cases support the provided legal argument. For each precedent, identify:
                    1. The specific point in the argument it supports
                    2. The relevant material facts and legal issues
                    3. The holding and ratio decidendi
                    4. How the precedent logically connects to and supports the argument
                    5. The strength and relevance of the precedent
                    
                    Include the source link where necessary. Format your response in Markdown.
                    """
                    
                    # Analyze the precedents
                    analysis_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": precedent_backstory},
                            {"role": "user", "content": f"Based on this argument {argument} perform your analysis and include the source link where necessary: {precedent_opinion_text}"}
                        ]
                    )
                    
                    analysis = analysis_response.choices[0].message.content
                    
                    # Save analysis in session state
                    st.session_state.analysis = analysis
                
                # Display the argument
                st.markdown("<h3 class='sub-header'>Legal Argument</h3>", unsafe_allow_html=True)
                st.markdown(st.session_state.argument)
                
                # Display the precedent analysis
                st.markdown("<h3 class='sub-header'>Precedent Analysis</h3>", unsafe_allow_html=True)
                st.markdown(st.session_state.analysis)
                
                # Entity extraction (optional)
                if st.button("Extract Key Entities"):
                    with st.spinner("Extracting entities..."):
                        # Extract entities from base opinion and precedents
                        entity_response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": "Entity Recognizer and extractor, Output in a list only"},
                                {"role": "user", "content": f"Extract the entities and their role or position in {base_opinion_text} and {precedent_opinion_text}"}
                            ]
                        )
                        
                        entities = entity_response.choices[0].message.content
                        
                        # Display entities
                        st.markdown("<h3 class='sub-header'>Key Entities</h3>", unsafe_allow_html=True)
                        st.markdown(entities)
            
            # If analysis has been run previously, show it
            elif 'analysis' in st.session_state:
                # Display the argument
                st.markdown("<h3 class='sub-header'>Legal Argument</h3>", unsafe_allow_html=True)
                st.markdown(st.session_state.argument)
                
                # Display the precedent analysis
                st.markdown("<h3 class='sub-header'>Precedent Analysis</h3>", unsafe_allow_html=True)
                st.markdown(st.session_state.analysis)
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.markdown("""
            <div class="error-box">
            This feature requires a valid OpenAI API key and may incur costs. 
            Please check your API key and try again.
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #888;">
    LegalReasonerX &copy; 2023 | A Framework for Legal Document Analysis and Reasoning<br>
    Created by David Akinboro
    </div>
    """, 
    unsafe_allow_html=True
)