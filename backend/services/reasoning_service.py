"""
Service for AI-powered legal reasoning analysis.
"""
from typing import Dict, List, Optional
from openai import OpenAI
import os


class ReasoningService:
    """Service for analyzing legal reasoning using AI."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def extract_argument(self, base_opinion_text: str) -> str:
        """Extract the legal argument from a base opinion."""
        if not self.client:
            raise Exception("OpenAI API key not configured")

        argument_backstory = """
        You are a seasoned argument developer who analyzes base opinions and extracts the argument.
        This argument will then be passed to another agent to understand how the precedent supports the argument.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": argument_backstory},
                {"role": "user", "content": f"What is the argument in {base_opinion_text}"}
            ]
        )

        return response.choices[0].message.content

    def analyze_precedents(self, argument: str, precedent_opinion_text: str) -> str:
        """Analyze how precedents support the legal argument."""
        if not self.client:
            raise Exception("OpenAI API key not configured")

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

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": precedent_backstory},
                {"role": "user", "content": f"Based on this argument {argument} perform your analysis and include the source link where necessary: {precedent_opinion_text}"}
            ]
        )

        return response.choices[0].message.content

    def extract_entities(self, base_opinion_text: str, precedent_opinion_text: str) -> str:
        """Extract key legal entities from opinions."""
        if not self.client:
            raise Exception("OpenAI API key not configured")

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Entity Recognizer and extractor. Output in a structured list format."},
                {"role": "user", "content": f"Extract the entities and their role or position in {base_opinion_text} and {precedent_opinion_text}"}
            ]
        )

        return response.choices[0].message.content

    def perform_full_analysis(
        self,
        base_opinion_text: str,
        precedent_opinion_text: str
    ) -> Dict[str, str]:
        """
        Perform full legal reasoning analysis.

        Returns:
            Dictionary with argument, analysis, and entities
        """
        # Extract argument
        argument = self.extract_argument(base_opinion_text)

        # Analyze precedents
        analysis = self.analyze_precedents(argument, precedent_opinion_text)

        return {
            "argument": argument,
            "analysis": analysis
        }
