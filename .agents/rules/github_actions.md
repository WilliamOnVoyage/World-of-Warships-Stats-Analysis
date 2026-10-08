# Mandatory GitHub Actions Check Rule

> [!IMPORTANT]
> **ABSOLUTE LAW FOR ALL AGENTS AND DEVELOPERS IN THIS REPOSITORY:**
> Whenever pushing ANY change to this repository (`git push`), the triggered GitHub Action workflow runs **MUST BE CHECKED AND MUST PASS**.

## Required Workflow on Every Push
1. **Execute Push:** Commit and push changes to the remote branch.
2. **Monitor GitHub Actions:** Immediately check the status of the triggered workflow using GitHub CLI:
   ```bash
   gh run list --limit 3
   gh run watch <run-id>
   ```
3. **Verify Passing Status:** Confirm that every job (e.g., `Backend Tests`, `Frontend Tests`, `Lint`, `Build`) completes with `conclusion: success`.
4. **Immediate Remediation if Failed:** If any job fails:
   - Inspect failure logs immediately using `gh run view <run-id> --log-failed`.
   - Resolve the exact failure (linting, type errors, test failures, or build issues).
   - Re-test locally with `npm run lint`, `npm run test`, `npm run build`, and `pytest`.
   - Push the fix and verify that the new GitHub Action run passes.
5. **Never report completion** until the GitHub Action run is verified as passing.
