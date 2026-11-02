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

from ossie import OssieDialectExpression

from .context import ExportContext


def pick_ossie_dialect_expression(
    ossie_dialect_expressions: list[OssieDialectExpression],
    *,
    ctx: ExportContext,
) -> OssieDialectExpression | None:
    """Use a sole variant, or resolve multiple variants with an explicit preference."""
    if len(ossie_dialect_expressions) == 1:
        choice = ossie_dialect_expressions[0]
    else:
        matches = [
            entry
            for entry in ossie_dialect_expressions
            if entry.dialect == ctx.ossie_dialect
        ]
        if len(matches) == 1:
            choice = matches[0]
        else:
            if ctx.current_phase_name == "load":
                available = ", ".join(
                    entry.dialect.value for entry in ossie_dialect_expressions
                )
                if not ossie_dialect_expressions:
                    ctx.error("Expression has no dialect variants.")
                elif ctx.ossie_dialect is None:
                    ctx.error(
                        f"Expression has multiple dialect variants: {available}. "
                        "Select one with --dialect."
                    )
                elif not matches:
                    ctx.error(
                        f"Expression has no {ctx.ossie_dialect.value} variant. "
                        f"Available dialects: {available}. Select one with --dialect."
                    )
                else:
                    ctx.error(
                        f"Expression has multiple {ctx.ossie_dialect.value} variants; "
                        "provide exactly one variant for the selected dialect."
                    )
            return None
    ctx.selected_ossie_dialects.add(choice.dialect)
    return choice
