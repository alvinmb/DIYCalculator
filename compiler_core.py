from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class CompileResult:
    success: bool
    messages: List[str]
    bytecode: bytes | None = None


class Compiler:
    """
    Skeleton for the DIY Calculator language compiler.
    Replace the stub methods with your real implementation.
    """

    def compile_source(self, source: str) -> CompileResult:
        source = source.replace("\r\n", "\n")

        if not source.strip():
            return CompileResult(
                success=False,
                messages=["No source code provided."],
                bytecode=None,
            )

        try:
            tokens = self._lex(source)
            ast = self._parse(tokens)
            bytecode = self._generate_bytecode(ast)

            return CompileResult(
                success=True,
                messages=["Compilation successful."],
                bytecode=bytecode,
            )
        except Exception as exc:
            return CompileResult(
                success=False,
                messages=[f"Compilation failed: {exc}"],
                bytecode=None,
            )

    # --- Stubs to replace with real logic ---

    def _lex(self, source: str) -> List[Tuple[str, str]]:
        """
        Turn source into a list of (token_type, value).
        Replace this with your real lexer.
        """
        tokens: List[Tuple[str, str]] = []
        for line_no, line in enumerate(source.split("\n"), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            # Example: treat whole line as a single 'LINE' token
            tokens.append(("LINE", stripped))
        return tokens

    def _parse(self, tokens: List[Tuple[str, str]]):
        """
        Build an AST from tokens.
        Replace this with your real parser.
        """
        # For now, just return tokens as a fake AST
        return tokens

    def _generate_bytecode(self, ast) -> bytes:
        """
        Generate bytecode for the DIY Calculator VM.
        Replace this with your real code generator.
        """
        # Dummy: encode lines as UTF-8 joined with newlines
        lines = [node[1] for node in ast]
        joined = "\n".join(lines)
        return joined.encode("utf-8")