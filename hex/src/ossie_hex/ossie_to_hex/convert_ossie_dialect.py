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

from collections.abc import Mapping

from ossie import OssieDialect

from ..hex import HexDialect, HexDialectName
from .context import ExportContext

_DIALECT_NAME_MAP: Mapping[OssieDialect, HexDialectName | None] = {
    OssieDialect.ANSI_SQL: "duckdb",
    # Portable dialects use the project default independently of their parser.
    OssieDialect.OSSIE_SQL_2026: "duckdb",
    OssieDialect.BIGQUERY: "bigquery",
    OssieDialect.DATABRICKS: "databricks",
    OssieDialect.SNOWFLAKE: "snowflake",
    # These are expression languages, not SQL dialects or engines
    OssieDialect.MAQL: None,
    OssieDialect.MDX: None,
    OssieDialect.TABLEAU: None,
    OssieDialect.SIGMA: None,
    OssieDialect.THOUGHTSPOT: None,
    OssieDialect.DAX: None,
    OssieDialect.HOLISTICS_AQL: None,
}


def convert_ossie_dialect(
    ossie_dialect: OssieDialect,
    *,
    ctx: ExportContext,
) -> HexDialect:
    hex_dialect_name = _DIALECT_NAME_MAP.get(ossie_dialect)
    if hex_dialect_name is None:
        ctx.info(
            "Ossie dialect is an expression language; using DuckDB as SQL dialect for Hex semantic project"
        )
        return HexDialect("duckdb")
    return HexDialect(hex_dialect_name)


def infer_hex_dialect(*, ctx: ExportContext) -> HexDialect | None:
    """Infer one project engine from selected variants, allowing portable SQL alongside it."""
    selected = ctx.selected_ossie_dialects
    portable = {OssieDialect.ANSI_SQL, OssieDialect.OSSIE_SQL_2026}
    vendor_dialects = sorted(selected - portable, key=lambda dialect: dialect.value)
    if vendor_dialects:
        engines = [
            convert_ossie_dialect(dialect, ctx=ctx) for dialect in vendor_dialects
        ]
        if any(engine != engines[0] for engine in engines[1:]):
            available = ", ".join(dialect.value for dialect in vendor_dialects)
            ctx.error(
                f"Selected expressions use incompatible dialects: {available}. "
                "A Hex project must use one SQL dialect."
            )
            return None
        return engines[0]
    # Portable expressions do not identify a target engine.
    return HexDialect("duckdb")
