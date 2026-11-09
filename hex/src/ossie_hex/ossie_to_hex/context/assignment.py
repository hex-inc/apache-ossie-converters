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

from dataclasses import dataclass

from .analysis import RelationshipDirection


class ExportAssignment:
    """Store placements chosen by the assignment planner."""

    def __init__(self) -> None:
        self._model_metric_assignments: dict[str, ModelMetricAssignment] = {}
        self._relationship_assignments: dict[str, list[RelationshipAssignment]] = {}

    def for_model_metric(self, name: str) -> ModelMetricAssignment | None:
        return self._model_metric_assignments.get(name)

    def for_relationship(self, name: str) -> list[RelationshipAssignment]:
        return self._relationship_assignments.get(name, [])

    def set_for_relationship(self, assignment: RelationshipAssignment | None) -> None:
        if assignment is None:
            return
        self._relationship_assignments[assignment.name] = [assignment]

    def set_for_model_metric(self, assignment: ModelMetricAssignment) -> None:
        self._model_metric_assignments[assignment.name] = assignment


@dataclass(frozen=True)
class ModelMetricAssignment:
    """The assignment of a model-scoped metric to a parent dataset and optional relationship."""

    name: str
    """The name of the Ossie model-scoped metric."""
    source: str
    """The name of the Ossie dataset that should be the parent of the model-scoped metric."""
    relationship: RelationshipAssignment | None
    """The assignment for the Ossie relationship that's required for the model-scoped metric, if any."""


@dataclass(frozen=True)
class RelationshipAssignment:
    """The assignment of a relationship from a parent dataset to a target dataset."""

    name: str
    """The name of the Ossie relationship."""
    direction: RelationshipDirection
    """A direction of the Ossie relationship (from -> to or to -> from)."""
    source: str
    """The name of the Ossie dataset that is the start of the directed edge."""
    target: str
    """The name of the Ossie dataset that is the end of the directed edge."""
