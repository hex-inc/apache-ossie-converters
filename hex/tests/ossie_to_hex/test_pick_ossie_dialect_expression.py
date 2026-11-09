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

from collections.abc import Iterator

import pytest
from inline_snapshot import snapshot

from ossie_hex.ossie_to_hex.context import ExportContext
from ossie_hex.ossie_to_hex.pick_ossie_dialect_expression import (
    pick_ossie_dialect_expression,
)
from tests.ossie_to_hex.utils import Quick
from tests.utils import problems_snapshot


@pytest.fixture
def ctx() -> Iterator[ExportContext]:
    ctx = ExportContext()
    with ctx.phase_scope("load"):
        yield ctx


@pytest.mark.parametrize("preferred", ["ANSI_SQL", "SNOWFLAKE"])
def test_picks_preferred_variant(ctx: ExportContext, preferred: str) -> None:
    preferred_dialect = Quick.dialect(preferred)
    ctx.set_ossie_dialect(preferred_dialect)
    expression = Quick.expression(
        [
            ("DAX", "SELECT FROM"),
            ("ANSI_SQL", "foo.bar"),
            ("SNOWFLAKE", "foo.bar + 1"),
        ]
    )

    result = pick_ossie_dialect_expression(expression.dialects, ctx=ctx)

    selected = next(
        entry for entry in expression.dialects if entry.dialect == preferred
    )
    assert result is selected
    assert problems_snapshot(ctx.problems) == snapshot("")


@pytest.mark.parametrize("preferred", [None, "ANSI_SQL", "OSSIE_SQL_2026", "SNOWFLAKE"])
@pytest.mark.parametrize("dialect", ["ANSI_SQL", "OSSIE_SQL_2026", "SNOWFLAKE"])
def test_uses_sole_variant_quietly(
    ctx: ExportContext, preferred: str | None, dialect: str
) -> None:
    ctx.set_ossie_dialect(Quick.dialect(preferred) if preferred else None)
    expression = Quick.expression([(dialect, "foo.bar")])

    result = pick_ossie_dialect_expression(expression.dialects, ctx=ctx)

    assert result is expression.dialects[0]
    assert not ctx.problems
    assert ctx.selected_ossie_dialects == {Quick.dialect(dialect)}


@pytest.mark.parametrize("preferred", [None, "SNOWFLAKE"])
def test_requires_matching_preference_for_multiple_variants(
    ctx: ExportContext, preferred: str | None
) -> None:
    ctx.set_ossie_dialect(Quick.dialect(preferred) if preferred else None)
    expression = Quick.expression(
        [("ANSI_SQL", "foo.bar"), ("OSSIE_SQL_2026", "foo.bar")]
    )

    result = pick_ossie_dialect_expression(expression.dialects, ctx=ctx)

    assert result is None
    assert len(ctx.problems) == 1
    assert ctx.problems[0].severity == "error"
    assert "--dialect" in ctx.problems[0].message
    assert "ANSI_SQL" in ctx.problems[0].message
    assert "OSSIE_SQL_2026" in ctx.problems[0].message
    assert not ctx.selected_ossie_dialects


def test_reports_missing_variants(ctx: ExportContext) -> None:
    result = pick_ossie_dialect_expression([], ctx=ctx)

    assert result is None
    assert problems_snapshot(ctx.problems) == snapshot(
        "[ERROR] Expression has no dialect variants."
    )


def test_repeated_matching_dialect_is_ambiguous(ctx: ExportContext) -> None:
    ctx.set_ossie_dialect(Quick.dialect("ANSI_SQL"))
    expression = Quick.expression(
        [("ANSI_SQL", "foo.bar"), ("ANSI_SQL", "foo.bar + 1")]
    )

    result = pick_ossie_dialect_expression(expression.dialects, ctx=ctx)

    assert result is None
    assert len(ctx.problems) == 1
    assert "multiple ANSI_SQL variants" in ctx.problems[0].message


def test_does_not_repeat_selection_errors_during_conversion(ctx: ExportContext) -> None:
    expression = Quick.expression(
        [("ANSI_SQL", "foo.bar"), ("SNOWFLAKE", "foo.bar + 1")]
    )
    pick_ossie_dialect_expression(expression.dialects, ctx=ctx)
    with ctx.phase_scope("convert"):
        result = pick_ossie_dialect_expression(expression.dialects, ctx=ctx)

    assert result is None
    assert len(ctx.problems) == 1
