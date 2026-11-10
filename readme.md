# L400: Deliver real impact with Agents

Hands-on Caldova workshop exercises and supporting assets for Microsoft engineers.

- [Workshop and exercises](index.md)
- [Tenant and workstation setup](Instructions/Setup.md)
- [Fabric foundation](Instructions/Fabric-Foundation.md)
- [Procurement action setup](lifecycle/ex2/README.md)
- [Runtime setup and operation](Instructions/Runtime.md)

## Local package validation

Use Python **3.12** for the supplied runtime and its pinned dependencies. From the
repository root on Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/validate_repository.py
```

The checker validates source integrity, package links, Python/notebook syntax, core
data and local tests. It expects exactly the two intentional qualification-regression
failures in the starter. Do not replace the starter with the solution before Exercise 4.
After the learner repair, use `--fixture-state repaired`.

## Information for MCTs

See the [GitHub User Guide for MCTs](https://microsoftlearning.github.io/MCT-User-Guide/).
Submit proposed content/code changes for Microsoft and course-author review through a
pull request. Record the tested commit and keep tenant configuration and evidence out
of the repository.
