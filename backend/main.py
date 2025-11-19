"""
FastAPI backend for LegalReasonerX.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os

from backend.services.precedent_service import PrecedentService
from backend.services.network_service import NetworkVisualizationService
from backend.services.reasoning_service import ReasoningService

app = FastAPI(
    title="LegalReasonerX API",
    description="API for legal document analysis and reasoning",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")


# Pydantic models
class CitationRequest(BaseModel):
    citation: str
    api_token: str


class NetworkRequest(BaseModel):
    citation_dict: Dict[str, list]


class ReasoningRequest(BaseModel):
    base_opinion_text: str
    precedent_opinion_text: str
    openai_api_key: Optional[str] = None


class OpinionRequest(BaseModel):
    api_token: str
    precedent_data: Dict[str, Any]


# Routes for serving HTML pages
@app.get("/")
async def root():
    """Serve the landing page."""
    return FileResponse("frontend/index.html")


@app.get("/citation-lookup")
async def citation_lookup_page():
    """Serve the citation lookup page."""
    return FileResponse("frontend/citation-lookup.html")


@app.get("/network-viz")
async def network_viz_page():
    """Serve the network visualization page."""
    return FileResponse("frontend/network-viz.html")


@app.get("/opinion-analysis")
async def opinion_analysis_page():
    """Serve the opinion analysis page."""
    return FileResponse("frontend/opinion-analysis.html")


@app.get("/reasoning")
async def reasoning_page():
    """Serve the reasoning framework page."""
    return FileResponse("frontend/reasoning.html")


# API endpoints
@app.post("/api/process-citation")
async def process_citation(request: CitationRequest):
    """
    Process a legal citation and extract precedents.

    Args:
        citation: Legal citation text
        api_token: CourtListener API token

    Returns:
        Precedent data including case mappings and opinions
    """
    try:
        service = PrecedentService(request.api_token)
        result = service.get_precedents(request.citation)

        # Convert tuple keys to string keys for JSON serialization
        opinions_per_cluster_serializable = {
            f"{k[0]}||{k[1]}": v for k, v in result["opinions_per_cluster"].items()
        }

        return {
            "success": True,
            "data": {
                "opinions_per_cluster": opinions_per_cluster_serializable,
                "citation_caseName_map": result["citation_caseName_map"],
                "caseName_to_precedent_map": result["caseName_to_precedent_map"],
                "opinion_to_cluster": result["opinion_to_cluster"],
                "base_opinion_responses_combined": result["base_opinion_responses_combined"],
                "precedents_opinion_responses_combined": result["precedents_opinion_responses_combined"],
                "cluster_data_map": result["cluster_data_map"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/generate-network")
async def generate_network(request: NetworkRequest):
    """
    Generate citation network visualization data.

    Args:
        citation_dict: Dictionary mapping case names to cited cases

    Returns:
        Network data with nodes, edges, and statistics
    """
    try:
        service = NetworkVisualizationService()
        network_data = service.get_network_data_for_viz(request.citation_dict)

        return {
            "success": True,
            "data": network_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/extract-opinions")
async def extract_opinions(request: OpinionRequest):
    """
    Extract base and precedent opinions from precedent data.

    Args:
        api_token: CourtListener API token
        precedent_data: Data from process-citation endpoint

    Returns:
        Base and precedent opinions
    """
    try:
        service = PrecedentService(request.api_token)

        # Reconstruct tuple keys
        opinions_per_cluster = {}
        for key, value in request.precedent_data.get("opinions_per_cluster", {}).items():
            parts = key.split("||")
            if len(parts) == 2:
                opinions_per_cluster[(parts[0], parts[1])] = value

        base_opinions, precedent_opinions = service.get_all_opinions(
            opinions_per_cluster,
            request.precedent_data.get("base_opinion_responses_combined", {}),
            request.precedent_data.get("precedents_opinion_responses_combined", {}),
            request.precedent_data.get("cluster_data_map", {}),
            request.precedent_data.get("opinion_to_cluster", {})
        )

        return {
            "success": True,
            "data": {
                "base_opinions": base_opinions,
                "precedent_opinions": precedent_opinions
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/analyze-reasoning")
async def analyze_reasoning(request: ReasoningRequest):
    """
    Perform AI-powered legal reasoning analysis.

    Args:
        base_opinion_text: Text of the base opinion
        precedent_opinion_text: Text of precedent opinions
        openai_api_key: Optional OpenAI API key

    Returns:
        Legal argument and precedent analysis
    """
    try:
        service = ReasoningService(request.openai_api_key)
        result = service.perform_full_analysis(
            request.base_opinion_text,
            request.precedent_opinion_text
        )

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/extract-entities")
async def extract_entities(request: ReasoningRequest):
    """
    Extract legal entities from opinions.

    Args:
        base_opinion_text: Text of the base opinion
        precedent_opinion_text: Text of precedent opinions
        openai_api_key: Optional OpenAI API key

    Returns:
        Extracted entities
    """
    try:
        service = ReasoningService(request.openai_api_key)
        entities = service.extract_entities(
            request.base_opinion_text,
            request.precedent_opinion_text
        )

        return {
            "success": True,
            "data": {"entities": entities}
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "LegalReasonerX API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
