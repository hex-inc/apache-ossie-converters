# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

from ...util.parse_sql import SQLGlotDialect, exp


class ExportAnalysis:
    """Analyze expressions of Ossie entities."""

    _model_metric_analyses: dict[str, ModelMetricAnalysis | None]
    """Model-scoped metric analysis results; None records a failed analysis."""

    _relationship_analyses: dict[str, RelationshipAnalysis]
    """A mapping of Ossie relationship names to their analyses."""

    def __init__(self) -> None:
        self._model_metric_analyses = {}
        self._relationship_analyses = {}

    def set_for_model_metric(
        self,
        name: str,
        analysis: ModelMetricAnalysis | None,
    ) -> None:
        """Record an Ossie model-scoped metric's analysis result, including failure."""
        self._model_metric_analyses[name] = analysis

    def for_model_metric(self, name: str) -> ModelMetricAnalysis | None:
        """Get a model-scoped metric's result; raise KeyError if no analysis was recorded."""
        return self._model_metric_analyses[name]

    def for_model_metrics(self) -> Iterator[ModelMetricAnalysis]:
        """Get all successful analyses for Ossie model-scoped metrics."""
        return (
            analysis
            for analysis in self._model_metric_analyses.values()
            if analysis is not None
        )

    def set_for_relationship(self, analysis: RelationshipAnalysis | None) -> None:
        """Set the analysis for an Ossie relationship."""
        if analysis is None:
            return
        self._relationship_analyses[analysis.name] = analysis

    def for_relationship(self, name: str) -> RelationshipAnalysis | None:
        """Get the analysis for an Ossie relationship."""
        return self._relationship_analyses.get(name)

    def for_relationships(self) -> Iterator[RelationshipAnalysis]:
        """Get all analyses for Ossie relationships."""
        return iter(self._relationship_analyses.values())


@dataclass(frozen=True)
class ModelMetricAnalysis:
    """Dependencies data needed to assign and convert an Ossie model-scoped metric."""

    name: str
    expr: exp.Expression
    dialect: SQLGlotDialect | None
    dataset_names: tuple[str, ...]


@dataclass(frozen=True)
class RelationshipAnalysis:
    """Dependencies data needed to assign and convert an Ossie relationship."""

    name: str
    """The name of the Ossie relationship."""
    edges: list[RelationshipAnalysisEdge]
    """The edges of the Ossie relationship."""


RelationshipDirection = Literal["from_to", "to_from"]

# tuple keeps them ordered
RELATIONSHIP_DIRECTIONS: tuple[RelationshipDirection, ...] = ("from_to", "to_from")


@dataclass(frozen=True)
class RelationshipAnalysisEdge:
    """A directed placement of an Ossie relationship on a Hex model."""

    direction: RelationshipDirection
    """A direction of the Ossie relationship (from -> to or to -> from)."""
    source: str
    """The name of the Ossie dataset that is the start of the directed edge."""
    target: str
    """The name of the Ossie dataset that is the end of the directed edge."""
