"""
PDG Nodes Helper Module.

Provides utilities for constructing PDGNode instances from AST statements.
"""

from typing import List, Optional
from objective2.models import ASTStatement, PDGNode


class PDGNodeBuilder:
    """Utility to build PDGNode objects from AST statements."""

    @staticmethod
    def from_ast_statement(stmt: ASTStatement) -> PDGNode:
        return PDGNode(
            node_id=stmt.node_id,
            line_number=stmt.line_number,
            source_code=stmt.source_code,
            statement_type=stmt.ast_type,
            reads=list(stmt.reads),
            writes=list(stmt.writes),
            function_name=stmt.function_name,
            executed=False,
            execution_count=0,
            runtime_values={},
            failure_related=False,
        )
