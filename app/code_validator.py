import ast
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def extract_code_blocks(answer: str) -> list[dict]:
    """Extract fenced code blocks and their declared languages."""

    pattern = r"```([a-zA-Z0-9_+#.-]*)\s*\n(.*?)```"

    blocks = []

    for match in re.finditer(pattern, answer, re.DOTALL):
        language = match.group(1).strip().lower()
        code = match.group(2).strip()

        if code:
            blocks.append({
                "language": language or "unknown",
                "code": code
            })

    return blocks


def check_with_command(
    command: list[str],
    code: str,
    filename: str,
    timeout: int = 5
) -> dict:
    """Run a syntax/compiler check with a time limit."""

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / filename
        file_path.write_text(code, encoding="utf-8")

        try:
            result = subprocess.run(
                command + [str(file_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=temp_dir
            )

            return {
                "syntax_check": (
                    "passed" if result.returncode == 0 else "failed"
                ),
                "details": (
                    result.stderr.strip()
                    or result.stdout.strip()
                    or "No diagnostic message."
                )
            }

        except subprocess.TimeoutExpired:
            return {
                "syntax_check": "error",
                "details": "Syntax check timed out."
            }

        except OSError as error:
            return {
                "syntax_check": "error",
                "details": str(error)
            }


def execute_python(code: str, timeout: int = 3) -> dict:
    """Execute Python code in a separate process with a timeout."""

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / "check.py"
        file_path.write_text(code, encoding="utf-8")

        try:
            result = subprocess.run(
                [shutil.which("python3") or "python3", str(file_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=temp_dir
            )

            return {
                "execution_check": (
                    "passed" if result.returncode == 0 else "failed"
                ),
                "execution_output": result.stdout.strip(),
                "execution_error": result.stderr.strip()
            }

        except subprocess.TimeoutExpired:
            return {
                "execution_check": "timeout",
                "execution_output": "",
                "execution_error": f"Execution exceeded {timeout} seconds."
            }

        except OSError as error:
            return {
                "execution_check": "error",
                "execution_output": "",
                "execution_error": str(error)
            }

def validate_code(language: str, code: str) -> dict:
    """Check supported code languages and run Python snippets."""
    language = language.lower().strip()

    aliases = {
        "py": "python",
        "js": "javascript",
        "node": "javascript",
        "ts": "typescript",
        "c++": "cpp",
        "cc": "cpp",
        "cxx": "cpp",
        "java": "java"
    }

    language = aliases.get(language, language)

    
    if language == "python":
        try:
            ast.parse(code)
        except SyntaxError as error:
            return {
                "language": language,
                "syntax_check": "failed",
                "details": f"Line {error.lineno}: {error.msg}",
                "execution_check": "not_run",
                "execution_output": "",
                "execution_error": ""
            }

        execution_result = execute_python(code)

        return {
            "language": language,
            "syntax_check": "passed",
            "details": "Python syntax is valid.",
            **execution_result
        }

    if language == "javascript":
        executable = shutil.which("node")

        if not executable:
            return {
                "language": language,
                "syntax_check": "unavailable",
                "details": "Node.js was not found on PATH.",
                "execution_check": "not_run"
            }

        result = check_with_command(
            [executable, "--check"],
            code,
            "check.js"
        )

        return {
            "language": language,
            **result,
            "execution_check": "not_run"
        }

    if language == "typescript":
        executable = shutil.which("tsc")

        if not executable:
            return {
                "language": language,
                "syntax_check": "unavailable",
                "details": "TypeScript compiler (tsc) was not found.",
                "execution_check": "not_run"
            }

        result = check_with_command(
            [executable, "--noEmit", "--skipLibCheck"],
            code,
            "check.ts"
        )

        return {
            "language": language,
            **result,
            "execution_check": "not_run"
        }

    if language == "java":
        executable = shutil.which("javac")

        if not executable:
            return {
                "language": language,
                "syntax_check": "unavailable",
                "details": "Java compiler (javac) was not found.",
                "execution_check": "not_run"
            }

        result = check_with_command(
            [executable],
            code,
            "Main.java",
            timeout=10
        )

        return {
            "language": language,
            **result,
            "execution_check": "not_run"
        }

    if language in {"c", "cpp"}:
        compiler_name = "cc" if language == "c" else "c++"
        executable = shutil.which(compiler_name)

        if not executable:
            return {
                "language": language,
                "syntax_check": "unavailable",
                "details": f"Compiler {compiler_name} was not found.",
                "execution_check": "not_run"
            }

        extension = ".c" if language == "c" else ".cpp"

        result = check_with_command(
            [executable, "-fsyntax-only"],
            code,
            "check" + extension,
            timeout=10
        )

        return {
            "language": language,
            **result,
            "execution_check": "not_run"
        }

    return {
        "language": language or "unknown",
        "syntax_check": "unsupported",
        "details": "This language is not supported yet.",
        "execution_check": "not_run"
    }


def validate_answer_code(answer: str) -> dict:
    """Validate all recognized fenced code blocks in an answer."""

    blocks = extract_code_blocks(answer)

    results = []

    for index, block in enumerate(blocks, start=1):
        results.append({
            "block_number": index,
            **validate_code(
                block["language"],
                block["code"]
            )
        })

    return {
        "code_blocks_found": len(blocks),
        "code_results": results
    }