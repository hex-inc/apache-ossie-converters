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

import pytest
from inline_snapshot import snapshot
from ossie import OssieAIContextObject, OssieCustomExtension

from ossie_hex.hex import HexDataType
from ossie_hex.ossie_to_hex.context import ExportContext
from ossie_hex.ossie_to_hex.convert_ossie_dataset_metric import (
    convert_ossie_dataset_metric,
)
from tests.ossie_to_hex.utils import Quick
from tests.utils import problems_snapshot


@pytest.fixture
def ctx() -> ExportContext:
    ctx = ExportContext()
    ctx._set_dialects("ANSI_SQL", "duckdb")
    return ctx


def test_name(ctx: ExportContext) -> None:
    """Should preserve the name."""
    name = "bar"
    metric = Quick.metric(name, None, [("OSSIE_SQL_2026", "COUNT(*)")])
    dataset = Quick.dataset("foo", "public.foo", [], [metric])
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is not None
    assert result.id == name
    assert not ctx.problems


def test_description(ctx: ExportContext) -> None:
    """Should preserve the description."""
    description = "Foo bar baz"
    metric = Quick.metric(
        "bar", None, [("OSSIE_SQL_2026", "COUNT(*)")], description=description
    )
    dataset = Quick.dataset("foo", "public.foo", [], [metric])
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is not None
    assert result.description == description
    assert not ctx.problems


def test_default_datatype(ctx: ExportContext) -> None:
    """Should default to NUMBER if no datatype is specified."""
    datatype = None
    metric = Quick.metric("bar", datatype, [("OSSIE_SQL_2026", "COUNT(*)")])
    dataset = Quick.dataset("foo", "public.foo", [], [metric])
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is not None
    assert result.type == HexDataType.NUMBER
    assert not ctx.problems


def test_ai_context(ctx: ExportContext) -> None:
    """Should warn AI context is not supported."""
    ai_context = OssieAIContextObject(synonyms=("foo", "bar"))
    metric = Quick.metric(
        "bar", None, [("OSSIE_SQL_2026", "COUNT(*)")], ai_context=ai_context
    )
    dataset = Quick.dataset("foo", "public.foo", [], [metric])
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is not None
    assert problems_snapshot(ctx.problems) == snapshot("[WARNING] Not supported")


def test_custom_extensions(ctx: ExportContext) -> None:
    """Should warn custom extensions are not supported."""
    custom_extension = OssieCustomExtension(vendor_name="foo", data="bar")
    metric = Quick.metric(
        "bar",
        None,
        [("OSSIE_SQL_2026", "COUNT(*)")],
        custom_extensions=[custom_extension],
    )
    dataset = Quick.dataset("foo", "public.foo", [], [metric])
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is not None
    assert problems_snapshot(ctx.problems) == snapshot("[WARNING] Not supported")


def test_expression_with_no_references(ctx: ExportContext) -> None:
    """Should preserve an expression with no references."""
    expression = "COUNT(*)"
    metric = Quick.metric("bar", None, [("OSSIE_SQL_2026", expression)])
    dataset = Quick.dataset("foo", "public.foo", [], [metric])
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is not None
    assert result.func_sql == snapshot("COUNT(*)")


def test_expression_with_no_references_and_arithmetic(ctx: ExportContext) -> None:
    """Should preserve an expression with no references and multiple functions."""
    expression = "COUNT(*) + SUM(2)"
    metric = Quick.metric("bar", None, [("OSSIE_SQL_2026", expression)])
    dataset = Quick.dataset("foo", "public.foo", [], [metric])
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is not None
    assert result.func_sql == snapshot("COUNT(*) + SUM(2)")


def test_expression_with_source_reference(ctx: ExportContext) -> None:
    """Should preserve an expression with a reference to a column of the dataset's source."""
    expression = "SUM(source.bar)"
    metric = Quick.metric("bar", None, [("OSSIE_SQL_2026", expression)])
    dataset = Quick.dataset("foo", "public.foo", [], [metric])
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is not None
    assert result.func_sql == snapshot("SUM(bar)")
    assert not ctx.problems


def test_expression_with_source_reference_many(ctx: ExportContext) -> None:
    """Should preserve an expression with many references to a column of the dataset's source."""
    expression = 'SUM(source.bar) + SUM(SOURCE.baz) + SUM("Source"."Qux")'
    metric = Quick.metric("bar", None, [("OSSIE_SQL_2026", expression)])
    dataset = Quick.dataset("foo", "public.foo", [], [metric])
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is not None
    assert result.func_sql == snapshot('SUM(bar) + SUM(baz) + SUM("Qux")')
    assert not ctx.problems


def test_expression_with_source_reference_shadowing_field(ctx: ExportContext) -> None:
    """Should resolve `source.column` to the source column even if a field shares its name."""
    expression = "SUM(source.baz) - SUM(baz)"
    metric = Quick.metric("bar", None, [("OSSIE_SQL_2026", expression)])
    dataset = Quick.dataset(
        "foo", "public.foo", [("baz", "Integer", [("OSSIE_SQL_2026", "baz")])], [metric]
    )
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_field("foo", "baz", "baz")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is not None
    assert result.func_sql == snapshot("SUM(baz) - SUM(${baz})")
    assert not ctx.problems


def test_expression_with_source_reference_when_field_named_source(
    ctx: ExportContext,
) -> None:
    """Should error on a source column reference when a field is named `source`."""
    expression = "SUM(source.baz) + COUNT(source)"
    metric = Quick.metric("bar", None, [("OSSIE_SQL_2026", expression)])
    dataset = Quick.dataset(
        "foo",
        "public.foo",
        [("source", "Integer", [("OSSIE_SQL_2026", "source")])],
        [metric],
    )
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_field("foo", "source", "source")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is None
    assert problems_snapshot(ctx.problems) == snapshot(
        "[ERROR] Source column 'baz' cannot be referenced because the dataset declares a field named 'source'"
    )


def test_expression_with_dataset_qualified_reference(ctx: ExportContext) -> None:
    """Should error on references qualified with a dataset name, including its own."""
    expression = "SUM(foo.baz) / COUNT(DISTINCT customers.id) + SUM(a.source.b)"
    metric = Quick.metric("bar", None, [("OSSIE_SQL_2026", expression)])
    dataset = Quick.dataset(
        "foo", "public.foo", [("baz", "Integer", [("OSSIE_SQL_2026", "baz")])], [metric]
    )
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_field("foo", "baz", "baz")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is None
    assert problems_snapshot(ctx.problems) == snapshot("""\
[ERROR] Reference 'foo.baz' must be a field name or 'source.column'

[ERROR] Reference 'customers.id' must be a field name or 'source.column'

[ERROR] Reference 'a.source.b' has too many parts""")


def test_expression_with_field_reference(ctx: ExportContext) -> None:
    """Should preserve an expression with a reference to a field of the parent dataset."""
    expression = "SUM(baz)"
    metric = Quick.metric("bar", None, [("OSSIE_SQL_2026", expression)])
    dataset = Quick.dataset(
        "foo", "public.foo", [("baz", "Integer", [("OSSIE_SQL_2026", "baz")])], [metric]
    )
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_field("foo", "baz", "baz")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is not None
    assert result.func_sql == snapshot("SUM(${baz})")
    assert not ctx.problems


def test_expression_with_field_reference_without_hex_id(ctx: ExportContext) -> None:
    """Should error on a reference to a declared field that has no Hex ID."""
    expression = "SUM(baz)"
    metric = Quick.metric("bar", None, [("OSSIE_SQL_2026", expression)])
    dataset = Quick.dataset(
        "foo", "public.foo", [("baz", "Integer", [("OSSIE_SQL_2026", "baz")])], [metric]
    )
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is None
    assert problems_snapshot(ctx.problems) == snapshot(
        "[ERROR] Field 'baz' has no Hex ID"
    )


def test_expression_with_field_reference_many(ctx: ExportContext) -> None:
    """Should preserve an expression with many references to a field of the parent dataset."""
    expression = "SUM(baz) + SUM(qux) + SUM(corge)"
    metric = Quick.metric("bar", None, [("OSSIE_SQL_2026", expression)])
    dataset = Quick.dataset(
        "foo",
        "public.foo",
        [
            ("baz", "Integer", [("OSSIE_SQL_2026", "baz")]),
            ("qux", "Integer", [("OSSIE_SQL_2026", "qux")]),
            ("corge", "Integer", [("OSSIE_SQL_2026", "corge")]),
        ],
        [metric],
    )
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_field("foo", "baz", "baz")
    ctx.hex_ids.set_for_field("foo", "qux", "qux")
    ctx.hex_ids.set_for_field("foo", "corge", "corge")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is not None
    assert result.func_sql == snapshot("SUM(${baz}) + SUM(${qux}) + SUM(${corge})")
    assert not ctx.problems


def test_expression_with_field_reference_missing(ctx: ExportContext) -> None:
    """Should error on a reference to a field of the parent dataset that is not declared."""
    expression = "SUM(baz)"
    metric = Quick.metric("bar", None, [("OSSIE_SQL_2026", expression)])
    dataset = Quick.dataset("foo", "public.foo", [], [metric])
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is None
    assert problems_snapshot(ctx.problems) == snapshot(
        "[ERROR] Field 'baz' not declared"
    )


def test_expression_with_field_reference_many_missing(ctx: ExportContext) -> None:
    """Should error on many references to a field of the parent dataset that is not declared."""
    expression = "SUM(baz) + SUM(qux) + SUM(corge)"
    metric = Quick.metric("bar", None, [("OSSIE_SQL_2026", expression)])
    dataset = Quick.dataset("foo", "public.foo", [], [metric])
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is None
    assert problems_snapshot(ctx.problems) == snapshot("""\
[ERROR] Field 'baz' not declared

[ERROR] Field 'qux' not declared

[ERROR] Field 'corge' not declared""")


def test_expression_dialect(ctx: ExportContext) -> None:
    """Should preserve the dialect of the expression."""
    ctx._set_dialects("BIGQUERY", "bigquery")
    dialect, expression = "BIGQUERY", "COUNTIF(baz)"
    metric = Quick.metric("bar", None, [(dialect, expression)])
    dataset = Quick.dataset(
        "foo", "public.foo", [("baz", "Boolean", [(dialect, "baz")])], [metric]
    )
    ctx.hex_ids.set_for_dataset("foo", "foo")
    ctx.hex_ids.set_for_field("foo", "baz", "baz")
    ctx.hex_ids.set_for_dataset_metric(dataset.name, metric.name, "bar")

    result = convert_ossie_dataset_metric(metric, dataset, ctx=ctx)

    assert result is not None
    assert result.func_sql == snapshot("COUNTIF(${baz})")
    assert not ctx.problems
