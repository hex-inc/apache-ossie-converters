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

from pathlib import Path
from textwrap import dedent

import pytest


@pytest.fixture
def minimal_ossie_input(tmp_path: Path) -> Path:
    path = tmp_path / "model.yml"
    data = dedent(
        """\
        name: foo
        datasets:
          - name: bar
            source: public.bar
            fields:
              - name: id
                datatype: Integer
                expression:
                  dialects:
                    - dialect: ANSI_SQL
                      expression: id
        """
    )
    path.write_text(data, encoding="utf-8")
    return path


@pytest.fixture
def mixed_dialect_input(tmp_path: Path) -> Path:
    path = tmp_path / "mixed.yml"
    path.write_text(
        dedent(
            """\
            name: mixed
            datasets:
              - name: orders
                source: public.orders
                fields:
                  - name: id
                    datatype: Integer
                    expression:
                      dialects:
                        - dialect: ANSI_SQL
                          expression: id
                  - name: amount
                    datatype: Integer
                    expression:
                      dialects:
                        - dialect: OSSIE_SQL_2026
                          expression: amount
                  - name: positive_amount
                    datatype: Integer
                    expression:
                      dialects:
                        - dialect: SNOWFLAKE
                          expression: IFF(amount > 0, amount, 0)
            metrics:
              - name: total
                datatype: Integer
                expression:
                  dialects:
                    - dialect: SNOWFLAKE
                      expression: SUM(IFF(orders.amount > 0, orders.amount, 0))
            """
        ),
        encoding="utf-8",
    )
    return path
