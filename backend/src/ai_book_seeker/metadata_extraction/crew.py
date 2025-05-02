"""
Book Metadata Extraction Crew

This module defines the crew configuration for book metadata extraction
using CrewAI's declarative framework.
"""

from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from langchain_openai import ChatOpenAI

from ai_book_seeker.core.config import OPENAI_PDF_READER_MODEL
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.metadata_extraction.schema import MetadataOutput
from ai_book_seeker.metadata_extraction.tools.pdf_tools import PDFExtractionTool

# Initialize logger
logger = get_logger("metadata_extraction")


@CrewBase
class MetadataExtractionCrew:
    """Crew for extracting metadata from PDF book files"""

    agents: List[BaseAgent]
    tasks: List[Task]
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def pdf_reader(self) -> Agent:
        """Create the PDF reader agent"""
        return Agent(
            config=self.agents_config["pdf_reader"],
            verbose=True,
            llm=ChatOpenAI(model_name=OPENAI_PDF_READER_MODEL),
            tools=[
                PDFExtractionTool(
                    name="extract_text_from_pdf",
                    description="Extract text from a PDF file, trying PyPDF2 first and falling back to OCR if needed.",
                )
            ],
        )

    @agent
    def structure_analyzer(self) -> Agent:
        """Create the structure analyzer agent"""
        return Agent(
            config=self.agents_config["structure_analyzer"],
            verbose=True,
            llm=ChatOpenAI(model_name=OPENAI_PDF_READER_MODEL),
        )

    @agent
    def metadata_summarizer(self) -> Agent:
        """Create the metadata summarizer agent"""
        return Agent(
            config=self.agents_config["metadata_summarizer"],
            verbose=True,
            llm=ChatOpenAI(model_name=OPENAI_PDF_READER_MODEL),
        )

    @agent
    def quality_controller(self) -> Agent:
        """Create the quality controller agent"""
        return Agent(
            config=self.agents_config["quality_controller"],
            verbose=True,
            llm=ChatOpenAI(model_name=OPENAI_PDF_READER_MODEL),
        )

    @task
    def pdf_reader_task(self) -> Task:
        """Create the PDF reader task"""
        pdf_reader_agent = self.pdf_reader()
        return Task(
            config=self.tasks_config["pdf_reader_task"],
            agent=pdf_reader_agent,
        )

    @task
    def structure_analyzer_task(self) -> Task:
        """Create the structure analyzer task"""
        structure_analyzer_agent = self.structure_analyzer()
        return Task(
            config=self.tasks_config["structure_analyzer_task"],
            agent=structure_analyzer_agent,
            context=[self.pdf_reader_task()],
        )

    @task
    def metadata_summarizer_task(self) -> Task:
        """Create the metadata summarizer task"""
        metadata_summarizer_agent = self.metadata_summarizer()
        return Task(
            config=self.tasks_config["metadata_summarizer_task"],
            agent=metadata_summarizer_agent,
            context=[self.pdf_reader_task(), self.structure_analyzer_task()],
            output_pydantic=MetadataOutput,
        )

    @task
    def quality_controller_task(self) -> Task:
        """Create the quality controller task"""
        quality_controller_agent = self.quality_controller()
        return Task(
            config=self.tasks_config["quality_controller_task"],
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
