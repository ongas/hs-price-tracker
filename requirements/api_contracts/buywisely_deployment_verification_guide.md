# BuyWisely Service Deployment & Verification Guide

This guide provides step-by-step instructions for deploying and verifying the BuyWisely service integration, ensuring a fool-proof and repeatable process.

---

## 1. Pre-Deployment Checklist
- [ ] All code changes committed and pushed to the correct branch.
- [ ] All tests (unit, BDD, edge cases) pass locally.
- [ ] Linting (ruff/flake8) passes with no errors.
- [ ] Documentation is up to date.

---

## 2. Deployment Steps
1. **Activate Conda Environment**
   ```bash
   conda activate homeassistant
   echo $CONDA_DEFAULT_ENV  # Should output 'homeassistant'
   ```
2. **Run Linter and Tests**
   ```bash
   ruff check --fix .
   pytest
   ```
3. **Deploy to Home Assistant**
   ```bash
   ./scripts/DEPLOYMENT_SCRIPT.sh
   ```
4. **Restart Home Assistant**
   ```bash
   cd ../../docker
   docker compose restart homeassistant
   ```
5. **Clear and Tail Logs**
   ```bash
   rm ../../docker/config/home-assistant.log
   tail -f ../../docker/config/home-assistant.log
   ```

---

## 3. Post-Deployment Verification
- [ ] Use the Home Assistant UI or API to trigger a BuyWisely entity update.
- [ ] Confirm entity state and attributes are updated as expected.
- [ ] Check Home Assistant logs for:
    - Hydration data and offers list logs
    - Extraction diagnostics
    - Error/edge case logs (if applicable)
- [ ] Use provided test data to simulate all core and edge cases.
- [ ] Validate that all acceptance criteria and BDD scenarios are met.

---

## 4. Rollback Procedure
- [ ] If issues are found, revert to the previous working commit:
   ```bash
   git checkout <previous_commit>
   ./scripts/DEPLOYMENT_SCRIPT.sh
   docker compose restart homeassistant
   ```
- [ ] Document the issue and resolution steps.

---

## 5. Troubleshooting
- Check conda environment and dependencies.
- Review logs for missing fields, HTTP errors, or parsing failures.
- Use test data and mock fixtures to reproduce and debug issues.
- Consult error handling and edge case catalog for expected log messages and outcomes.

---

This guide must be updated as deployment or verification steps evolve.