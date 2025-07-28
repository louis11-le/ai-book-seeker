"""
Book Metadata Extraction Crew

This module defines the crew configuration for book metadata extraction
using CrewAI's declarative framework.

All configuration (model selection, etc.) is accessed via the centralized AppSettings config object.
Do not use direct environment variable access or hardcoded values; use only AppSettings.
"""

from pathlib import Path
from typing import List

import yaml
from ai_book_seeker.core.config import AppSettings
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.metadata_extraction.schema import MetadataOutput
from ai_book_seeker.metadata_extraction.tools.pdf_tools import PDFExtractionTool
from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from langchain_openai import ChatOpenAI

# Initialize logger
logger = get_logger("metadata_extraction")

# Load agent and task configs from YAML
AGENTS_CONFIG_PATH = Path(__file__).parent / "config" / "agents.yaml"
TASKS_CONFIG_PATH = Path(__file__).parent / "config" / "tasks.yaml"
with open(AGENTS_CONFIG_PATH, "r", encoding="utf-8") as f:
    agents_config = yaml.safe_load(f)
with open(TASKS_CONFIG_PATH, "r", encoding="utf-8") as f:
    tasks_config = yaml.safe_load(f)


@CrewBase
class MetadataExtractionCrew:
    """Crew for extracting metadata from PDF book files"""

    agents: List[BaseAgent]
    tasks: List[Task]
    agents_config = agents_config
    tasks_config = tasks_config

    def __init__(self, settings: AppSettings):
        """
        Initialize the MetadataExtractionCrew with settings.

        Args:
            settings: Application settings containing configuration
        """
        self.settings = settings

    @agent
    def pdf_reader(self) -> Agent:
        """Create the PDF reader agent (model from config)"""
        cfg = self.agents_config["pdf_reader"]
        return Agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg["backstory"],
            verbose=True,
            llm=ChatOpenAI(model=self.settings.openai.model),
            tools=[
                PDFExtractionTool(
                    name="extract_text_from_pdf",
                    description="Extract text from a PDF file, trying PyPDF2 first and falling back to OCR if needed.",
                )
            ],
        )

    @agent
    def structure_analyzer(self) -> Agent:
        """Create the structure analyzer agent (model from config)"""
        cfg = self.agents_config["structure_analyzer"]
        return Agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg["backstory"],
            verbose=True,
            llm=ChatOpenAI(model=self.settings.openai.model),
        )

    @agent
    def metadata_summarizer(self) -> Agent:
        """Create the metadata summarizer agent (model from config)"""
        cfg = self.agents_config["metadata_summarizer"]
        return Agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg["backstory"],
            verbose=True,
            llm=ChatOpenAI(model=self.settings.openai.model),
        )

    @agent
    def quality_controller(self) -> Agent:
        """Create the quality controller agent (model from config)"""
        cfg = self.agents_config["quality_controller"]
        return Agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg["backstory"],
            verbose=True,
            llm=ChatOpenAI(model=self.settings.openai.model),
        )

    @task
    def pdf_reader_task(self) -> Task:
        """Create the PDF reader task"""
        pdf_reader_agent = self.pdf_reader()
        cfg = self.tasks_config["pdf_reader_task"]
        return Task(
            description=cfg["description"],
            expected_output=cfg["expected_output"],
            agent=pdf_reader_agent,
        )

    @task
    def structure_analyzer_task(self) -> Task:
        """Create the structure analyzer task"""
        structure_analyzer_agent = self.structure_analyzer()
        cfg = self.tasks_config["structure_analyzer_task"]
        return Task(
            description=cfg["description"],
            expected_output=cfg["expected_output"],
            agent=structure_analyzer_agent,
            context=[self.pdf_reader_task()],
        )

    @task
    def metadata_summarizer_task(self) -> Task:
        """Create the metadata summarizer task"""
        metadata_summarizer_agent = self.metadata_summarizer()
        cfg = self.tasks_config["metadata_summarizer_task"]
        return Task(
            description=cfg["description"],
            expected_output=cfg["expected_output"],
            agent=metadata_summarizer_agent,
            context=[self.pdf_reader_task(), self.structure_analyzer_task()],
            output_pydantic=MetadataOutput,
        )

    @task
    def quality_controller_task(self) -> Task:
        """Create the quality controller task"""
        quality_controller_agent = self.quality_controller()
        cfg = self.tasks_config["quality_controller_task"]
        return Task(
            description=cfg["description"],
            expected_output=cfg["expected_output"],
            agent=quality_controller_agent,
            context=[self.metadata_summarizer_task()],
            output_pydantic=MetadataOutput,
        )

    @crew
    def crew(self) -> Crew:
        """Create the metadata extraction crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
            process=Process.sequential,  # Sequential execution is the key
        )


def create_metadata_extraction_crew(settings: AppSettings) -> MetadataExtractionCrew:
    """
    Create a MetadataExtractionCrew instance using the provided settings.

    Args:
        settings: Application settings containing configuration

    Returns:
        MetadataExtractionCrew: Configured crew instance
    """
    return MetadataExtractionCrew(settings)
