"""Translate raw Crawl4AI responses into structured course information.

Tweak `CourseRecord` or `EXTRACTION_PROMPT` when you need new fields; the rest
of the pipeline will automatically honour the updated schema.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, List

from crawl4ai import LLMExtractionStrategy
from pydantic import BaseModel, Field, ValidationError

LOGGER = logging.getLogger(__name__)


class CourseRecord(BaseModel):
    """Normalised representation of a UNSW course entry."""

    code: str
    title: str
    uoc: str
    overview: str
    conditions_for_enrolment: str
    faculty: str
    study_level: str
    offering_terms: str
    field_of_education: str
    school: str


class CourseParser:
    """Prepares the LLM extraction prompt and validates the resulting payload."""

    EXTRACTION_PROMPT = """
    You are given HTML from the UNSW Handbook for a single course. Extract the
    following fields and return them as JSON:
      - code: the course code (e.g. COMP1511)
      - title: the course title
      - uoc: units of credit as a string
      - overview: a concise summary paragraph
      - conditions_for_enrolment: prerequisites or enrolment rules
      - faculty: the faculty responsible for the course
      - study_level: Undergraduate or Postgraduate label
      - offering_terms: term availability such as "Term 1" or "Summer".
      - field_of_education: the field of education value as listed on the page
      - school: the school that teaches the course

    Respond with a JSON object matching the schema exactly. Use null for missing
    data. Avoid commentary.
    """.strip()

    def __init__(self, provider: str, placeholder: str = "Not specified") -> None:
        self.provider = provider
        self.placeholder = placeholder

    def build_strategy(self) -> LLMExtractionStrategy:
        """Create a Crawl4AI extraction strategy using the course schema."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is required")

        return LLMExtractionStrategy(
            provider=self.provider,
            api_token=api_key,
            instruction=self.EXTRACTION_PROMPT,
            schema=CourseRecord.model_json_schema(),
            extraction_type="structured",
        )

    def parse_payload(self, raw_payload: str) -> List[CourseRecord]:
        """Convert the LLM JSON string into validated `CourseRecord` objects."""
        try:
            data = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            LOGGER.error("LLM payload was not valid JSON: %s", exc)
            return []

        if isinstance(data, dict):
            items = [data]
        elif isinstance(data, list):
            items = data
        else:
            LOGGER.warning("Unexpected payload type: %s", type(data))
            return []

        records: List[CourseRecord] = []
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                LOGGER.debug("Ignoring non-dict entry at index %d", index)
                continue

            normalised = self._apply_placeholder(item)

            try:
                record = CourseRecord(**normalised)
            except ValidationError as exc:
                LOGGER.warning("Validation failure at index %d: %s", index, exc)
                continue

            records.append(record)

        return records

    def _apply_placeholder(self, item: Dict[str, object]) -> Dict[str, str]:
        """Ensure all required fields are populated and stripped."""
        filled: Dict[str, str] = {}
        for field_name in CourseRecord.model_fields.keys():
            raw_value = item.get(field_name)
            text = self._coerce_to_string(raw_value)
            filled[field_name] = text if text else self.placeholder
        return filled

    @staticmethod
    def _coerce_to_string(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            return value.strip()
        return str(value)
