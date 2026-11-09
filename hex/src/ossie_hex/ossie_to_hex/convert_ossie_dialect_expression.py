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


from collections.abc import Callable
from dataclasses import dataclass

from ossie import OssieDialectExpression

from ..hex import HexEntityId, HexSql
from ..util.parse_sql import SQLGlotDialect, exp
from .context import ExportContext
from .load_ossie_dialect_expression import parse_ossie_dialect_expression


@dataclass(frozen=True)
class HexLogicalRef:
    """A Hex semantic reference, rendered as `${item}` or `${relation.item}`."""

    item_id: HexEntityId
    relation_id: HexEntityId | None = None


@dataclass(frozen=True)
class HexPhysicalRef:
    """A column of the local base table, rendered unqualified as `column`.

    Has no fields on purpose: rendering reuses the referenced column's original
    identifier, so that its quoting (e.g. `"Qux"`) is preserved.
    """


HexRef = HexLogicalRef | HexPhysicalRef

OssieRefResolver = Callable[[str | None, str], HexRef]
"""A function that resolves the qualifier (None if unqualified) and name of an Ossie
reference (e.g. `dataset.field`) to a Hex reference.

Raises `ResolveError` if the reference cannot be resolved.
"""


class ResolveError(ValueError):
    """Unable to resolve an Ossie reference to a Hex reference."""


def convert_ossie_dialect_expression(
    ossie_dialect_expression: OssieDialectExpression | None,
    *,
    resolve: OssieRefResolver | None,
    ctx: ExportContext,
) -> HexSql | None:
    """Convert an Ossie dialect expression to an equivalent Hex SQL string.

    If a resolver is provided, it is used to resolve Ossie field expression syntax
    to Hex semantic reference syntax.
    """
    if ossie_dialect_expression is None:
        return None

    if resolve is None:
        sql: HexSql = ossie_dialect_expression.expression
        return sql

    parsed = parse_ossie_dialect_expression(ossie_dialect_expression, ctx=ctx)
    if parsed is None:
        return None
    return convert_parsed_ossie_dialect_expression(
        parsed.expr,
        parsed.dialect,
        resolve=resolve,
        ctx=ctx,
    )


def convert_parsed_ossie_dialect_expression(
    expr: exp.Expression,
    dialect: SQLGlotDialect | None,
    *,
    resolve: OssieRefResolver,
    ctx: ExportContext,
) -> HexSql | None:
    """Convert an already parsed Ossie expression to Hex SQL.

    Reports an error for every reference that cannot be resolved, and returns None
    if there were any.
    """
    resolvable = True

    def replace_reference(node: exp.Expression) -> exp.Expression:
        nonlocal resolvable
        if not isinstance(node, exp.Column):
            return node
        # sqlglot reports the table of an unqualified column as "" rather than None.
        table = None if node.table == "" else node.table
        try:
            if node.args.get("db"):
                raise ResolveError(f"Reference '{node.sql()}' has too many parts")
            ref = resolve(table, node.name)
        except ResolveError as e:
            ctx.error(str(e))
            resolvable = False
            return node
        if isinstance(ref, HexPhysicalRef):
            return exp.Column(this=node.this.copy())
        if ref.relation_id is None:
            return exp.Var(this=f"${{{ref.item_id}}}")
        return exp.Var(this=f"${{{ref.relation_id}.{ref.item_id}}}")

    transformed = expr.transform(replace_reference)
    if not resolvable:
        return None
    return transformed.sql(dialect=dialect)
