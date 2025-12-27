import json
import os
import sys
import asyncio
from typing import List, Tuple, Dict, Any

# Add the parent directory to sys.path to allow importing from common
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.config import Config
from common.models import Anomaly, AnomalySummary  # Import AnomalySummary
from datetime import datetime, timezone

# from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import ValidationError  # Import ValidationError for explicit handling


class LLMSummarizer:
    """
    Handles LLM-based summarization of anomalies using LangChain and Ollama.
    This class is designed to be imported and used by other services.
    """

    def __init__(self):
        # Initialize the Ollama LLM client
        self.ollama_base_url = f"http://{Config.OLLAMA_HOST}:{Config.OLLAMA_PORT}"
        self.llm = None
        self.status_llm = None

        try:
            self.llm = ChatOllama(
                base_url=self.ollama_base_url,
                model=Config.LLM_MODEL_NAME,
                temperature=Config.LLM_TEMPERATURE,
            )

            self.status_llm = ChatOllama(
                base_url=self.ollama_base_url,
                model=Config.LLM_MODEL_NAME,
                temperature=0.1,  # Keep temperature low for status checks
                num_predict=2,  # Expect only 'Y' or similar
            )

            print(
                f"LLM Summarizer: Successfully connected to Ollama at {self.ollama_base_url}"
            )
        except Exception as e:
            print(
                f"LLM Summarizer: Could not connect to Ollama at {self.ollama_base_url}. Error: {e}"
            )

        # Define the Pydantic parser for the AnomalySummary model
        self.parser = PydanticOutputParser(pydantic_object=AnomalySummary)

        # Define the prompt template for anomaly summarization
        self.prompt_template = PromptTemplate(
            input_variables=["anomalies_data"],
            partial_variables={
                "format_instructions": self.parser.get_format_instructions()
            },
            template="""You are an expert system for a water treatment facility.
            Your task is to analyze a list of sensor anomalies and provide a concise, structured summary.
            
            *Guidelines for Summary Generation:*
            1.  *Overall Status*: Determine the overall operational status based on the anomalies. Choose from 'Normal', 'Minor Issues', 'Moderate Concern', 'Critical'.
            2.  *Summary Message*: Provide a human-readable overview of the anomalies. Highlight the issues, including their values and time.
            3.  *Anomaly Counts*: You MUST include the total number of anomalies detected in the field anomalies_count.
            4.  *Conciseness*: Your response must be as brief as possible while still conveying comprehensive analytics.

            *Output Format*:
            {format_instructions}

            *Anomalies to Analyze (if any):*
            {anomalies_data}

            *Summary:*
            """,
        )

        # Create an LLMChain only if LLM was initialized successfully
        self.llm_chain = None
        self.status_chain = None

        if self.llm:
            self.llm_chain = self.prompt_template | self.llm | self.parser
            self.status_chain = (
                PromptTemplate(
                    input_variables=[], template="Reply with only the letter 'Y'."
                )
                | self.status_llm
            )

            print(
                f"LLM Summarizer initialized with Ollama model: {Config.LLM_MODEL_NAME} at {self.ollama_base_url}"
            )
        else:
            print(
                "LLM Summarizer initialized without a functional LLM chain due to prior errors."
            )

    async def generate_summary(
        self, anomalies: List[Anomaly]
    ) -> Tuple[bool, str | AnomalySummary]:
        """
        Generates a structured summary from a list of anomalies asynchronously.
        Returns a tuple: (success_status: bool, summary_output: str | AnomalySummary)
        If successful, summary_output is an AnomalySummary object.
        If unsuccessful, summary_output is an error string.
        """
        if not self.llm_chain:
            return (
                False,
                "LLM Summarizer is not active or not initialized properly. Cannot generate summary.",
            )

        if not anomalies:
            return True, AnomalySummary(
                overall_status="Normal",
                summary_message="No anomalies detected in the recent period.",
                anomalies_count=0,
                timestamp=datetime.now(timezone.utc),
            )

        # Format anomalies into a string for the LLM
        anomalies_str = ""
        for anomaly in anomalies:
            anomalies_str += f"- {anomaly.model_dump_json()}\n"

        try:
            # ⏱️ Appel SANS timeout — attend la réponse complète pour gérer les générations longues
            summary_object = await self.llm_chain.ainvoke(
                {"anomalies_data": anomalies_str}
            )
            print("Successfully generated and parsed LLM summary.")
            return True, summary_object

        except ValidationError as ve:
            error_message = f"Failed to parse LLM response due to validation error: {ve}\nRaw LLM output might not conform to the expected schema."
            print(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Error generating LLM summary: {e}"
            print(error_message)
            return False, error_message

    async def check_llm_status(self) -> Tuple[bool, str]:
        """
        Checks the LLM's responsiveness by asking it to reply with a single letter 'Y'.
        Returns a tuple: (success_status: bool, response_text: str)
        """
        if not self.status_chain:
            return (
                False,
                "LLM Summarizer status checker is not active or not initialized properly.",
            )

        try:
            response = await self.status_chain.ainvoke({})
            cleaned_response = response.content.strip().upper()
            if "Y" in cleaned_response:
                print("LLM status check successful: Received 'Y'.")
                return True, "Y"
            else:
                print(
                    f"LLM status check failed: Received '{cleaned_response}' instead of 'Y'."
                )
                return False, f"Unexpected response: {cleaned_response}"
        except Exception as e:
            print(f"Error during LLM status check: {e}")
            return False, f"LLM status check failed due to error: {e}"