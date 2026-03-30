______________________________________________________________________

## name: sage-examples description: Agent for SAGE examples/tutorials/apps with runnable minimal changes. argument-hint: Include target folder (`examples`, `tutorials`, or `sage-apps`), goal, and run command. tools: ['vscode', 'execute', 'read', 'agent', 'edit', 'search', 'web', 'todo', 'vscode.mermaid-chat-features/renderMermaidDiagram', 'github.vscode-pull-request-github/issue_fetch', 'github.vscode-pull-request-github/suggest-fix', 'github.vscode-pull-request-github/searchSyntax', 'github.vscode-pull-request-github/doSearch', 'github.vscode-pull-request-github/renderIssues', 'github.vscode-pull-request-github/activePullRequest', 'github.vscode-pull-request-github/openPullRequest', 'ms-azuretools.vscode-containers/containerToolsConfig', 'ms-python.python/getPythonEnvironmentInfo', 'ms-python.python/getPythonExecutableCommand', 'ms-python.python/installPythonPackage', 'ms-python.python/configurePythonEnvironment', 'ms-toolsai.jupyter/configureNotebook', 'ms-toolsai.jupyter/listNotebookPackages', 'ms-toolsai.jupyter/installNotebookPackages', 'ms-vscode.cpp-devtools/Build_CMakeTools', 'ms-vscode.cpp-devtools/RunCtest_CMakeTools', 'ms-vscode.cpp-devtools/ListBuildTargets_CMakeTools', 'ms-vscode.cpp-devtools/ListTests_CMakeTools']

# SAGE Examples Agent

## Scope

- `examples/`, `tutorials/`, `sage-apps/` in `sage-examples` repo.

## Rules

- Flownet-first: no new `ray` imports/dependencies.
- Keep examples concise and runnable; avoid core-framework refactors here.
- Do not create new local virtual environments (`venv`/`.venv`); use the existing configured Python
  environment.
- In conda environments, use `python -m pip`.
- Dependency changes must go to repo config files, not one-off install notes.

## Workflow

1. Read nearest README/QUICK_START first.
1. Implement minimal local change.
1. Run relevant example/test and update nearby docs if behavior changed.

## Polyrepo coordination rules

- Treat this repository as the only local source tree; do not assume sibling repositories exist.
- If a task spans multiple repositories, implement only this repo and explicitly list follow-up
  repo/version-bump actions.
- Do not create `venv`/`.venv`; always use the existing configured Python environment.
