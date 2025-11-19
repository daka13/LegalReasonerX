"""
Service for processing legal precedents and citations.
"""
from typing import Dict, List, Tuple, Optional, Any
from backend.utils.courtlistener import (
    CourtListenerAPI, extract_opinion, get_opinion_type_map
)


class PrecedentService:
    """Service for extracting and analyzing legal precedents."""

    def __init__(self, api_token: str):
        self.api = CourtListenerAPI(api_token)

    def get_precedents(self, case_code: str) -> Dict[str, Any]:
        """
        Process a citation and extract precedent case names.

        Returns:
            Dictionary containing:
            - opinions_per_cluster
            - opinion_to_cluster
            - citation_caseName_map
            - base_opinion_responses_combined
            - precedents_opinion_responses_combined
            - precedents_cluster_responses_combined
            - caseName_to_precedent_map
            - cluster_data_map
        """
        # Get citation information from the API
        lookup_results = self.api.verify_citation_in_text(case_code)

        if not lookup_results:
            raise Exception("API returned no results.")

        # Error mapping
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
            raise Exception(error_dict.get(status, f"Unknown error: status {status}"))

        # Collect all opinion links per cluster
        opinions_per_cluster = {}
        citation_caseName_map = {}

        for result in valid_results:
            for cluster in result.get('clusters', []):
                if cluster.get('sub_opinions') == []:
                    continue

                case_name = cluster.get('case_name')
                citation = result.get("citation")

                opinions_per_cluster[(case_name, citation)] = cluster.get('sub_opinions')
                citation_caseName_map[case_name] = citation

        if not opinions_per_cluster:
            raise Exception("Error: Citations were recognized but no opinions found.")

        base_opinion_responses_combined = {}
        precedents_opinion_responses_combined = {}
        precedents_cluster_responses_combined = []
        caseName_to_precedent_map = {}

        # Process each cluster
        for (case_name, _), opinion_links in opinions_per_cluster.items():
            # Fetch all base opinions
            opinion_responses = self.api.fetch_all_urls_parallel(opinion_links)
            base_opinion_responses_combined.update(opinion_responses)

            # Extract all cited opinion links
            all_cited_opinions = set()
            for url, response in opinion_responses.items():
                if response:
                    all_cited_opinions.update(response.get("opinions_cited", []))

            if not all_cited_opinions:
                continue

            # Fetch all cited opinions
            cited_opinion_responses = self.api.fetch_all_urls_parallel(list(all_cited_opinions))
            precedents_opinion_responses_combined[case_name] = cited_opinion_responses

            # Extract cluster links
            cluster_links = set()
            opinion_to_cluster = {}
            for url, response in cited_opinion_responses.items():
                if response and response.get("cluster"):
                    opinion_to_cluster[url] = response.get("cluster")
                    cluster_links.add(response.get("cluster"))

            # Fetch all cluster data
            cluster_responses = self.api.fetch_all_urls_parallel(list(cluster_links))
            precedents_cluster_responses_combined.append((case_name, cluster_responses))

            # Create mapping from cluster link to case name
            cluster_data_map = {
                url: response.get("case_name")
                for url, response in cluster_responses.items()
                if response
            }

            # Map each opinion to its corresponding case name
            precedents = [
                cluster_data_map[opinion_to_cluster[link]]
                for link in all_cited_opinions
                if link in opinion_to_cluster and opinion_to_cluster[link] in cluster_data_map
            ]

            caseName_to_precedent_map[case_name] = precedents

        return {
            "opinions_per_cluster": opinions_per_cluster,
            "opinion_to_cluster": opinion_to_cluster,
            "citation_caseName_map": citation_caseName_map,
            "base_opinion_responses_combined": base_opinion_responses_combined,
            "precedents_opinion_responses_combined": precedents_opinion_responses_combined,
            "precedents_cluster_responses_combined": precedents_cluster_responses_combined,
            "caseName_to_precedent_map": caseName_to_precedent_map,
            "cluster_data_map": cluster_data_map
        }

    def get_all_opinions(
        self,
        opinions_per_cluster: Dict,
        base_opinion_responses_combined: Dict,
        precedents_opinion_responses_combined: Dict,
        cluster_data_map: Dict,
        opinion_to_cluster: Dict
    ) -> Tuple[Dict, Dict]:
        """Extract all base and precedent opinions."""
        base_opinions = {}
        precedent_opinions = {}

        for (case_name, citation), opinion_links in opinions_per_cluster.items():
            # BASE OPINIONS
            base_opinions[case_name] = []
            for i, opinion_link in enumerate(opinion_links):
                data = base_opinion_responses_combined.get(opinion_link)
                if not data:
                    continue

                opinion = extract_opinion(data)
                if not opinion:
                    continue

                opinion_type = get_opinion_type_map(data.get("type", ""))
                link = f"https://www.courtlistener.com{data.get('absolute_url', '')}"

                details = {
                    f"Base Opinion {i+1}": {
                        "opinion": opinion,
                        "type": opinion_type,
                        "link": link,
                        "citation": citation,
                        "case_name": case_name
                    }
                }
                base_opinions[case_name].append(details)

            # PRECEDENT OPINIONS
            precedent_opinions[case_name] = []
            precedent_responses = precedents_opinion_responses_combined.get(case_name, {})

            for i, (opinion_link, data) in enumerate(precedent_responses.items()):
                if not data:
                    continue

                opinion = extract_opinion(data)
                if not opinion:
                    continue

                opinion_type = get_opinion_type_map(data.get("type", ""))
                link = f"https://www.courtlistener.com{data.get('absolute_url', '')}"

                # Get precedent case name from cluster
                try:
                    precedent_case_name = cluster_data_map[opinion_to_cluster[opinion_link]]
                except KeyError:
                    precedent_case_name = "Unknown Case"

                details = {
                    f"Precedent Opinion {i+1}": {
                        "opinion": opinion,
                        "type": opinion_type,
                        "link": link,
                        "citation": citation,
                        "case_name": precedent_case_name
                    }
                }
                precedent_opinions[case_name].append(details)

        return base_opinions, precedent_opinions
