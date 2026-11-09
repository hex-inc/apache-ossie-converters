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

from ossie import OssieDialect

from .context import ExportContext


def load_ossie_dialect(
    ossie_dialect: OssieDialect | str | None,
    *,
    ctx: ExportContext,
) -> OssieDialect | None:
    """Parse an optional expression preference without assuming a default dialect."""
    if ossie_dialect is None or isinstance(ossie_dialect, OssieDialect):
        return ossie_dialect
    try:
        return OssieDialect(ossie_dialect.upper())
    except ValueError:
        ctx.error(f"Invalid Ossie dialect: {ossie_dialect}.")
        return None
