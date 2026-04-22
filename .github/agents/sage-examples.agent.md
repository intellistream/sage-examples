```chatagent
______________________________________________________________________

## name: sage-examples description: Agent for SAGE examples, tutorials, and app entrypoints built on consolidated isage. argument-hint: Include target area (`examples`, `tutorials`, or `sage-apps`), goal, and any run/test command. tools: ['vscode', 'execute', 'read', 'agent', 'edit', 'search', 'web', 'todo', 'vscode.mermaid-chat-features/renderMermaidDiagram', 'github.vscode-pull-request-github/issue_fetch', 'github.vscode-pull-request-github/suggest-fix', 'github.vscode-pull-request-github/searchSyntax', 'github.vscode-pull-request-github/doSearch', 'github.vscode-pull-request-github/renderIssues', 'github.vscode-pull-request-github/activePullRequest', 'github.vscode-pull-request-github/openPullRequest', 'ms-azuretools.vscode-containers/containerToolsConfig', 'ms-python.python/getPythonEnvironmentInfo', 'ms-python.python/getPythonExecutableCommand', 'ms-python.python/installPythonPackage', 'ms-python.python/configurePythonEnvironment', 'ms-toolsai.jupyter/configureNotebook', 'ms-toolsai.jupyter/listNotebookPackages', 'ms-toolsai.jupyter/installNotebookPackages', 'ms-vscode.cpp-devtools/Build_CMakeTools', 'ms-vscode.cpp-devtools/RunCtest_CMakeTools', 'ms-vscode.cpp-devtools/ListBuildTargets_CMakeTools', 'ms-vscode.cpp-devtools/ListTests_CMakeTools']

# SAGE Examples Agent

## Scope

- `examples/`, `tutorials/`, and `sage-apps/` in the `sage-examples` repository.
- Teach and modify examples that depend on the consolidated `isage` core package.

## Core Guidance

- Prefer current `sage.*` surfaces such as `sage.foundation`, `sage.stream`, `sage.runtime`, `sage.serving`, and `sage.cli`.
- Keep examples stream-first.
- Treat distributed runtime as optional.
- Treat `isagellm` and other adapters such as `isage-rag` or `isage-neuromem` as external optional integrations.
- Do not reintroduce retired split-core package guidance.

## Rules

- Flownet-first: do not add new `ray` imports or dependencies.
- Keep examples concise, runnable, and local to this repository.
- Do not create new local virtual environments (`venv`/`.venv`); use the existing configured Python environment.
- In conda environments, use `python -m pip`.
- Dependency changes must be declared in repo config files, not as one-off install notes.
- Fail fast; do not add silent fallback logic that hides missing configuration or imports.

## Workflow

1. Read the nearest `README.md` or `QUICK_START.md` first.
2. Reuse existing example and tutorial patterns before inventing new structure.
3. Implement the smallest repo-local change that solves the task.
4. Run the relevant example, test, or check when practical.
5. Update nearby docs when behavior or usage changes.

## Polyrepo Coordination Rules

- Treat this repository as an independent examples repository.
- Do not assume sibling source repositories are available locally.
- If cross-repo rollout is needed, keep changes here minimal and note any follow-up version bump separately.
- Do not create `venv`/`.venv`; always reuse the existing configured Python environment.

```
