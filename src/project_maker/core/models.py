from __future__ import annotations

from pydantic import BaseModel

from proposal_maker.core.models import ProposalSpec
from quote_maker.core.models import QuoteSpec
from shared.schemas.common import ProjectMeta
from timeline_maker.core.models import TimelineSpec


class ProjectSpec(BaseModel):
    """One YAML file that drives every maker."""

    project: ProjectMeta
    timeline: TimelineSpec
    pricing: QuoteSpec
    proposal: ProposalSpec

    model_config = {"populate_by_name": True}
