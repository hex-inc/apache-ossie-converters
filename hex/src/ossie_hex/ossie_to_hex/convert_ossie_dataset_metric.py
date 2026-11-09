# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 3
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.


from ossie import OssieDataset, OssieMetric

from ..hex import HexDataType, HexMeasure
from .context import ExportContext
from .convert_ossie_datatype import convert_ossie_datatype
from .convert_ossie_dialect_expression import (
    HexLogicalRef,
    HexPhysicalRef,
    HexRef,
    ResolveError,
    convert_parsed_ossie_dialect_expression,
)
from .load_ossie_dialect_expression import parse_ossie_dialect_expression
from .pick_ossie_dialect_expression import pick_ossie_dialect_expression


def convert_ossie_dataset_metric(
    ossie_metric: OssieMetric,
    ossie_dataset: OssieDataset,
    *,
    ctx: ExportContext,
) -> HexMeasure | None:
    """Convert an Ossie dataset-scoped metric to a measure of its dataset's model."""
    with ctx.problem_scope(ossie_metric.name):
        hex_measure_id = ctx.hex_ids.for_dataset_metric(
            ossie_dataset.name, ossie_metric.name
        )

        description = ossie_metric.description or ""

        with ctx.problem_scope("datatype"):
            datatype = convert_ossie_datatype(
                ossie_metric.datatype,
                HexDataType.NUMBER,
            )

        with ctx.problem_scope("expression"):
            ossie_dialect_expression = pick_ossie_dialect_expression(
                ossie_metric.expression.dialects,
                ctx=ctx,
            )
            if ossie_dialect_expression is None:
                return
            parsed = parse_ossie_dialect_expression(
                ossie_dialect_expression,
                ctx=ctx,
            )

            if parsed is None:
                ctx.error("Unable to parse expression")
                return

            field_names = {field.name for field in ossie_dataset.fields or []}
            # A field named `source` shadows the qualifier for source columns.
            source_is_field = any(name.lower() == "source" for name in field_names)

            # Metric references are unqualified fields of this dataset, or columns of
            # its source qualified with `source` (case insensitive).
            def resolve(table: str | None, name: str) -> HexRef:
                if table is None:
                    if name not in field_names:
                        raise ResolveError(f"Field '{name}' not declared")
                    dimension_id = ctx.hex_ids.for_field(ossie_dataset.name, name)
                    if dimension_id is None:
                        raise ResolveError(f"Field '{name}' has no Hex ID")
                    return HexLogicalRef(dimension_id)
                if table.lower() != "source":
                    raise ResolveError(
                        f"Reference '{table}.{name}' must be a field name or 'source.column'"
                    )
                if source_is_field:
                    raise ResolveError(
                        f"Source column '{name}' cannot be referenced because"
                        + " the dataset declares a field named 'source'"
                    )
                return HexPhysicalRef()

            func_sql = convert_parsed_ossie_dialect_expression(
                parsed.expr,
                parsed.dialect,
                resolve=resolve,
                ctx=ctx,
            )

        with ctx.problem_scope("ai_context"):
            if ossie_metric.ai_context is not None:
                ctx.warn("Not supported", code="ai-context")

        with ctx.problem_scope("custom_extensions"):
            if ossie_metric.custom_extensions is not None:
                ctx.warn("Not supported", code="custom-extensions")

        if hex_measure_id is None or func_sql is None:
            return None

        hex_measure = HexMeasure(
            id=hex_measure_id,
            description=description,
            type=datatype,
            func_sql=func_sql,
        )
        # not set:
        # - name: Ossie does not support display names
        # - visibility: Ossie does not support visibility
        # - func_calc: Ossie does not express Hex calculation language

        return hex_measure
