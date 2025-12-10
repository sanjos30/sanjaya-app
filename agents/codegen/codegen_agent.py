"""Codegen agent for generating code and tests from design contracts."""

import os
import re
from typing import Dict, Any, Optional

from autopilot_core.clients.repo_client import RepoClient
from autopilot_core.clients.llm_client import LLMClient
from agents.codegen.prompts import CODEGEN_SYSTEM_PROMPT, build_codegen_prompt


class CodegenAgent:
    """
    Agent that generates code and tests from design contracts.

    v0 behavior:
    - Parses markdown design contracts in a lightweight way
    - Generates stub code and tests (no real codegen yet)
    - Writes files into the project repository via RepoClient
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize codegen agent.

        Args:
            llm_client: LLM client for code generation (optional). If not provided,
                        falls back to stub generation.
        """
        self.llm_client = llm_client
        self.repo_client = RepoClient()

    # ------------ Public API ------------ #
    def generate_artifacts(
        self,
        project_id: str,
        repo_path: str,
        contract_path: str,
        project_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate code and tests from a design contract and write them to the repo.

        Args:
            project_id: Project identifier
            repo_path: Local path to the project repository
            contract_path: Path to design contract relative to .sanjaya/
            project_config: Loaded project configuration

        Returns:
            dict: Summary of generated artifacts
        """
        # Ensure RepoClient targets the correct repo
        self.repo_client.set_repo_path(repo_path)

        # Load contract text
        full_contract_path = os.path.join(repo_path, ".sanjaya", contract_path)
        if not os.path.exists(full_contract_path):
            raise FileNotFoundError(f"Design contract not found at {full_contract_path}")

        with open(full_contract_path, "r", encoding="utf-8") as f:
            contract_text = f.read()

        feature_slug = self._slug_from_contract_path(contract_path)
        parsed_contract = self._parse_design_contract(contract_text)

        # Extract intent from project config
        intent = project_config.get("intent", {}) or {}

        # Ensure scaffold for known stacks (respecting intent)
        dirs = self._resolve_dirs(project_config)
        self._ensure_scaffold(project_config, dirs, intent)

        code_files = self.generate_code(
            parsed_contract,
            project_config,
            feature_slug,
            design_contract_text=contract_text,
        )
        test_files = self.generate_tests(
            parsed_contract,
            code_files,
            project_config,
            feature_slug,
            design_contract_text=contract_text,
        )

        # Write files to repository
        written_files = []
        for path, content in {**code_files, **test_files}.items():
            self.repo_client.write_file(path, content)
            written_files.append(path)

        return {
            "project_id": project_id,
            "contract_path": contract_path,
            "generated_files": written_files,
            "feature_slug": feature_slug,
        }

    def generate_code(
        self,
        design_contract: Dict[str, Any],
        project_config: Dict[str, Any],
        feature_slug: str,
        design_contract_text: str = "",
    ) -> Dict[str, str]:
        """
        Generate code from design contract using LLM.

        Returns:
            dict: Mapping of file paths to code content (relative to repo root)
        """
        if not self.llm_client:
            raise ValueError("LLM client is required for code generation. Configure OPENAI/ANTHROPIC keys.")

        # Extract intent for decision-making
        intent = project_config.get("intent", {}) or {}
        
        language = str(project_config.get("language", "python")).lower()
        framework = str(project_config.get("framework", "")).lower()
        dirs = self._resolve_dirs(project_config)
        app_dir = dirs["backend_dir"]
        
        # Use intent backend if available
        if intent.get("backend"):
            backend_stack = intent["backend"]
            if backend_stack == "fastapi":
                language = "python"
                framework = "fastapi"

        # Stack-aware filename choices
        if language == "python" and framework == "fastapi":
            code_path = os.path.join(app_dir, f"{feature_slug}_api.py")
        elif language in ("js", "javascript") and framework in ("next", "nextjs"):
            code_path = os.path.join("pages", "api", f"{feature_slug}.ts")
        elif language in ("js", "javascript") or language == "node":
            code_path = os.path.join(app_dir, f"{feature_slug}.js")
        elif language == "php":
            code_path = os.path.join(app_dir, f"{feature_slug}.php")
        else:
            ext = {"php": "php", "python": "py", "js": "js", "ts": "ts"}.get(language, "txt")
            code_path = os.path.join(app_dir, f"{feature_slug}_feature.{ext}")

        stack_hint = f"Stack: language={language}, framework={framework}"
        prompt = build_codegen_prompt(design_contract_text, project_config)
        prompt += f"\n\n{stack_hint}\nGenerate a complete implementation for feature '{feature_slug}'."
        code_content = self.llm_client.generate(
            prompt=prompt,
            system_prompt=CODEGEN_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=2000,
        )

        code_content = self.ensure_conventions(code_content, project_config)
        return {code_path: code_content}

    def generate_tests(
        self,
        design_contract: Dict[str, Any],
        code_files: Dict[str, str],
        project_config: Dict[str, Any],
        feature_slug: str,
        design_contract_text: str = "",
    ) -> Dict[str, str]:
        """
        Generate test files for the code using LLM.

        Returns:
            dict: Mapping of test file paths to content
        """
        if not self.llm_client:
            raise ValueError("LLM client is required for test generation. Configure OPENAI/ANTHROPIC keys.")

        language = str(project_config.get("language", "python")).lower()
        dirs = self._resolve_dirs(project_config)
        test_dir = dirs["tests_dir"]
        framework = str(project_config.get("framework", "")).lower()

        if language == "php":
            test_path = os.path.join(test_dir, f"{feature_slug}Test.php")
        elif language in ("js", "javascript", "node"):
            test_path = os.path.join(test_dir, f"{feature_slug}.test.js")
        else:
            test_ext = {"php": "php", "python": "py", "js": "js", "ts": "ts"}.get(language, "py")
            test_path = os.path.join(test_dir, f"test_{feature_slug}_feature.{test_ext}")

        stack_hint = f"Stack: language={language}, framework={framework}"
        prompt = build_codegen_prompt(design_contract_text, project_config)
        prompt += "\n\nGenerate concise unit tests for the generated code."
        test_content = self.llm_client.generate(
            prompt=prompt,
            system_prompt=CODEGEN_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=800,
        )
        return {test_path: test_content}

    def ensure_conventions(self, code: str, project_config: Dict[str, Any]) -> str:
        """
        Ensure code follows project conventions (minimal stub).
        """
        # Placeholder for future formatting / linting rules
        return code

    # ------------ Helpers ------------ #
    def _slug_from_contract_path(self, contract_path: str) -> str:
        base = os.path.basename(contract_path)
        name, _ = os.path.splitext(base)
        return self._slugify(name)

    def _slugify(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[\\s_]+", "-", text)
        text = re.sub(r"[^a-z0-9-]", "", text)
        text = re.sub(r"-+", "-", text)
        return text.strip("-")

    def _parse_design_contract(self, contract_text: str) -> Dict[str, Any]:
        """
        Very lightweight parser to extract a few key sections from markdown.
        """
        sections = {
            "summary": "",
            "problem": "",
            "user_stories": [],
            "api_design": "",
        }

        current = None
        for line in contract_text.splitlines():
            header = line.strip().lower()
            if header.startswith("## summary"):
                current = "summary"
                continue
            if header.startswith("## problem"):
                current = "problem"
                continue
            if header.startswith("## user story") or header.startswith("## user stories"):
                current = "user_stories"
                continue
            if header.startswith("## api design"):
                current = "api_design"
                continue

            if current == "user_stories" and line.strip().startswith("-"):
                sections["user_stories"].append(line.strip("- ").strip())
            elif current and not line.strip().startswith("##"):
                if sections[current]:
                    sections[current] += "\n" + line
                else:
                    sections[current] = line

        return sections

    # ------------ Scaffold helpers ------------ #
    def _resolve_dirs(self, project_config: Dict[str, Any]) -> Dict[str, str]:
        codebase = project_config.get("codebase", {}) if isinstance(project_config, dict) else {}
        root = codebase.get("root", ".")
        backend_dir = codebase.get("backend_dir", "backend")
        frontend_dir = codebase.get("frontend_dir", "frontend")
        tests_dir = codebase.get("tests_dir", "tests")
        return {
            "root": root,
            "backend_dir": backend_dir if os.path.isabs(backend_dir) else os.path.join(root, backend_dir),
            "frontend_dir": frontend_dir if os.path.isabs(frontend_dir) else os.path.join(root, frontend_dir),
            "tests_dir": tests_dir if os.path.isabs(tests_dir) else os.path.join(root, tests_dir),
        }

    def _ensure_scaffold(self, project_config: Dict[str, Any], dirs: Dict[str, str], intent: Dict[str, Any] = None):
        """
        Ensure scaffold exists for the project stack, respecting intent constraints.
        
        Args:
            project_config: Project configuration
            dirs: Resolved directory paths
            intent: Project intent from questionnaire (optional)
        """
        if intent is None:
            intent = project_config.get("intent", {}) or {}
        
        language = str(project_config.get("language", "python")).lower()
        framework = str(project_config.get("framework", "")).lower()
        stack = project_config.get("stack", {})
        backend_stack = stack.get("backend", language) if isinstance(stack, dict) else language
        
        # Use intent to determine backend if available
        if intent.get("backend"):
            backend_stack = intent["backend"]

        # Scaffold backend if specified
        if backend_stack in ["fastapi", "python"]:
            self._scaffold_fastapi(dirs)
        elif backend_stack in ["nextjs", "next", "node", "javascript", "js"]:
            self._scaffold_next(dirs)
        elif backend_stack == "php":
            self._scaffold_php(dirs)
        
        # Scaffold UI only if intent says so
        if intent.get("ui") == "web":
            ui_framework = intent.get("ui_framework", "none")
            if ui_framework == "nextjs":
                self._scaffold_next(dirs)
            # Add other UI frameworks as needed

    def _write_if_missing(self, rel_path: str, content: str):
        if not self.repo_client.file_exists(rel_path):
            self.repo_client.write_file(rel_path, content)

    def _scaffold_fastapi(self, dirs: Dict[str, str]):
        backend = dirs["backend_dir"]
        tests = dirs["tests_dir"]
        self._write_if_missing(os.path.join(backend, "requirements.txt"), self._fastapi_requirements())
        self._write_if_missing(os.path.join(backend, ".env.example"), self._fastapi_env())
        self._write_if_missing(os.path.join(backend, "app", "__init__.py"), "")
        self._write_if_missing(os.path.join(backend, "app", "api", "__init__.py"), "")
        self._write_if_missing(os.path.join(backend, "app", "core", "__init__.py"), "")
        self._write_if_missing(os.path.join(backend, "app", "models", "__init__.py"), "")
        self._write_if_missing(os.path.join(backend, "app", "main.py"), self._fastapi_main())
        self._write_if_missing(os.path.join(backend, "app", "api", "routes.py"), self._fastapi_routes())
        self._write_if_missing(os.path.join(backend, "app", "core", "config.py"), self._fastapi_config())
        self._write_if_missing(os.path.join(backend, "app", "core", "db.py"), self._fastapi_db())
        self._write_if_missing(os.path.join(tests, "test_health.py"), self._fastapi_test())

    def _fastapi_requirements(self) -> str:
        return "\n".join([
            "fastapi",
            "uvicorn[standard]",
            "pydantic",
            "python-dotenv",
            "SQLAlchemy",
            "pytest",
            "httpx",
            ""
        ])

    def _fastapi_env(self) -> str:
        return "\n".join([
            "DB_DRIVER=mysql",
            "DB_HOST=localhost",
            "DB_PORT=3306",
            "DB_NAME=sanjaya",
            "DB_USER=sanjaya",
            "DB_PASSWORD=change_me",
            ""
        ])

    def _fastapi_main(self) -> str:
        return """from fastapi import FastAPI
from .api.routes import router as api_router

app = FastAPI(title="Sanjaya Service")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(api_router, prefix="/api")
"""

    def _fastapi_routes(self) -> str:
        return """from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
def ping():
    return {"message": "pong"}
"""

    def _fastapi_config(self) -> str:
        return """from pydantic import BaseSettings


class Settings(BaseSettings):
    DB_DRIVER: str = "mysql"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "sanjaya"
    DB_USER: str = "sanjaya"
    DB_PASSWORD: str = "password"

    class Config:
        env_file = ".env"


settings = Settings()
"""

    def _fastapi_db(self) -> str:
        return """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings

DATABASE_URL = (
    f"{settings.DB_DRIVER}://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""

    def _fastapi_test(self) -> str:
        return """from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
"""

    def _scaffold_next(self, dirs: Dict[str, str]):
        frontend = dirs["frontend_dir"]
        tests = os.path.join(dirs["tests_dir"], "frontend")
        self._write_if_missing(os.path.join(frontend, "package.json"), self._next_package())
        self._write_if_missing(os.path.join(frontend, "next.config.mjs"), "export default {};\n")
        self._write_if_missing(os.path.join(frontend, "tsconfig.json"), self._next_tsconfig())
        self._write_if_missing(os.path.join(frontend, ".env.local.example"), "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api\n")
        self._write_if_missing(os.path.join(frontend, "app", "page.tsx"), self._next_page())
        self._write_if_missing(os.path.join(frontend, "public", "favicon.ico"), "")
        self._write_if_missing(os.path.join(tests, "sample.test.tsx"), self._next_sample_test())

    def _next_package(self) -> str:
        return """{
  "name": "sanjaya-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "test": "jest"
  },
  "dependencies": {
    "next": "14.2.0",
    "react": "18.2.0",
    "react-dom": "18.2.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "typescript": "^5.0.0",
    "jest": "^29.0.0",
    "@types/jest": "^29.0.0",
    "ts-jest": "^29.0.0"
  }
}
"""

    def _next_tsconfig(self) -> str:
        return """{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": false,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve"
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
"""

    def _next_page(self) -> str:
        return """export default function HomePage() {
  return (
    <main style={{ padding: "2rem" }}>
      <h1>Sanjaya Frontend</h1>
      <p>This is the minimal Next.js scaffold.</p>
    </main>
  );
}
"""

    def _next_sample_test(self) -> str:
        return """describe('sample', () => {
  it('works', () => {
    expect(true).toBe(true);
  });
});
"""

    def _scaffold_php(self, dirs: Dict[str, str]):
        backend = dirs["backend_dir"]
        tests = os.path.join(dirs["tests_dir"], "php")
        self._write_if_missing(os.path.join(backend, "composer.json"), self._php_composer())
        self._write_if_missing(os.path.join(backend, ".env.example"), self._php_env())
        self._write_if_missing(os.path.join(backend, "public", "index.php"), self._php_index())
        self._write_if_missing(os.path.join(backend, "src", "config.php"), self._php_config())
        self._write_if_missing(os.path.join(backend, "src", "db", "mysql.php"), self._php_mysql())
        self._write_if_missing(os.path.join(backend, "src", "db", "mongo.php"), self._php_mongo())
        self._write_if_missing(os.path.join(tests, "phpunit.xml"), self._php_phpunit())
        self._write_if_missing(os.path.join(tests, "HealthTest.php"), self._php_health_test())

    def _php_composer(self) -> str:
        return """{
  "name": "sanjaya/backend-php",
  "require": {
    "vlucas/phpdotenv": "^5.5",
    "mongodb/mongodb": "^1.16"
  },
  "require-dev": {
    "phpunit/phpunit": "^10.0"
  },
  "autoload": {
    "psr-4": {
      "Sanjaya\\\\": "src/"
    }
  },
  "scripts": {
    "test": "phpunit"
  }
}
"""

    def _php_env(self) -> str:
        return "\n".join([
            "DB_DRIVER=mysql",
            "DB_HOST=localhost",
            "DB_PORT=3306",
            "DB_NAME=sanjaya",
            "DB_USER=sanjaya",
            "DB_PASSWORD=change_me",
            "MONGO_URI=mongodb://user:pass@localhost:27017/sanjaya",
            ""
        ])

    def _php_config(self) -> str:
        return """<?php
declare(strict_types=1);

use Dotenv\\Dotenv;

require __DIR__ . '/../vendor/autoload.php';

$dotenv = Dotenv::createImmutable(__DIR__ . '/..');
$dotenv->load();

function get_db_driver(): string {
    return $_ENV['DB_DRIVER'] ?? 'mysql';
}

function get_mysql_config(): array {
    return [
        'host' => $_ENV['DB_HOST'] ?? 'localhost',
        'port' => $_ENV['DB_PORT'] ?? '3306',
        'name' => $_ENV['DB_NAME'] ?? 'sanjaya',
        'user' => $_ENV['DB_USER'] ?? 'root',
        'password' => $_ENV['DB_PASSWORD'] ?? '',
    ];
}

function get_mongo_uri(): string {
    return $_ENV['MONGO_URI'] ?? 'mongodb://localhost:27017/sanjaya';
}
"""

    def _php_mysql(self) -> str:
        return """<?php
declare(strict_types=1);

require_once __DIR__ . '/../config.php';

function get_mysql_pdo(): PDO {
    $cfg = get_mysql_config();
    $dsn = sprintf(
        'mysql:host=%s;port=%s;dbname=%s;charset=utf8mb4',
        $cfg['host'],
        $cfg['port'],
        $cfg['name']
    );

    return new PDO($dsn, $cfg['user'], $cfg['password'], [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    ]);
}
"""

    def _php_mongo(self) -> str:
        return """<?php
declare(strict_types=1);

require_once __DIR__ . '/../config.php';

function get_mongo_client(): MongoDB\\Client {
    $uri = get_mongo_uri();
    return new MongoDB\\Client($uri);
}
"""

    def _php_index(self) -> str:
        return """<?php
declare(strict_types=1);

require_once __DIR__ . '/../src/config.php';

header('Content-Type: application/json');

echo json_encode([
    'status' => 'ok',
    'stack'  => 'php',
    'driver' => get_db_driver(),
]);
"""

    def _php_phpunit(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8"?>
<phpunit bootstrap="../../backend-php/vendor/autoload.php">
    <testsuites>
        <testsuite name="Sanjaya PHP Test Suite">
            <directory>./</directory>
        </testsuite>
    </testsuites>
</phpunit>
"""

    def _php_health_test(self) -> str:
        return """<?php
declare(strict_types=1);

use PHPUnit\\Framework\\TestCase;

final class HealthTest extends TestCase
{
    public function testHealth(): void
    {
        $response = ['status' => 'ok'];
        $this->assertSame('ok', $response['status']);
    }
}
"""

