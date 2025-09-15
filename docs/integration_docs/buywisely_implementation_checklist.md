# BuyWisely Service Implementation Checklist & Coding Standards

This checklist ensures a fool-proof, step-by-step process for implementing the BuyWisely service integration, along with coding standards for consistency and maintainability.

---

## 1. Implementation Checklist

1. **Requirements Review**
   - [ ] Read all user stories, BDD features, API/data contract, error catalog, and acceptance tests.

2. **Directory & File Setup**
   - [ ] Create `services/buywisely/` directory.
   - [ ] Add `engine.py`, `parser.py`, `data_transformer.py`, `const.py`, `setup.py`.
   - [ ] Add/Update test files and mock data as needed.

3. **Engine Implementation**
   - [ ] Implement HTTP GET for product page.
   - [ ] Handle HTTP/network errors with diagnostics.

4. **Parser Implementation**
   - [ ] Extract hydration JSON from HTML.
   - [ ] Parse product and offers data robustly.
   - [ ] Handle all edge cases and malformed data.
   - [ ] Log full hydration data and extraction steps.

5. **Data Transformer Implementation**
   - [ ] Map parsed data to `ItemData` model.
   - [ ] Set entity `url` to lowest-priced offer's `seller_product_url` only.
   - [ ] Handle missing/invalid offers as per error catalog.

6. **Integration with Home Assistant**
   - [ ] Register service in `setup.py`.
   - [ ] Ensure entity state and attributes update correctly.

7. **Diagnostics & Logging**
   - [ ] Log all required diagnostics at each step.
   - [ ] Ensure logs are accessible in Home Assistant log file.

8. **Testing**
   - [ ] Use provided test data and mock fixtures for all core and edge cases.
   - [ ] Validate against BDD acceptance tests.
   - [ ] Add/Update pytests as needed.

9. **Documentation**
   - [ ] Update developer guide and service documentation.
   - [ ] Document any deviations or new edge cases.

10. **Code Review & Verification**
    - [ ] Review code for adherence to checklist and standards.
    - [ ] Verify all acceptance criteria and diagnostics are met.

---

## 2. Coding Standards
- Use clear, descriptive variable and function names.
- Add docstrings to all public functions and classes.
- Use type hints for all function signatures.
- Handle all exceptions explicitly; never use bare except.
- Use logging for all diagnostics, not print.
- Follow PEP8 and project ruff/flake8 configuration.
- Avoid hardcoding values; use constants/configs.
- Keep functions small and focused.
- Write tests for all new logic and edge cases.
- Update documentation with every change.

---

This checklist and standards must be followed for every new service integration and updated as the project evolves.