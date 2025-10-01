# User Story 5: Parse and Display Product Information from BuyWisely

**As a** Home Assistant user,
**I want** the integration to extract and display product information (user-friendly name, brand, image, price, offers) from BuyWisely product pages,
**so that** I can see all relevant details for the products I am tracking.

## Acceptance Criteria
- The system uses a robust, state-aware parser to extract product HTML and JSON data from BuyWisely pages, handling all known edge cases (see error/edge case catalog).
- Product details such as a user-friendly name (not the full HTML <title>), brand, image, price (which must be greater than 0.0), and offers are extracted and shown to the user. If the extracted price is 0.0, it indicates an extraction bug.
- The seller URL is always extracted from the offers list (never from fallback or hydration fields).
- If parsing fails, the user is notified with a clear diagnostic message.

---
