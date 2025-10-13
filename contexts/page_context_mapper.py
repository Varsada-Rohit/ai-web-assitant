"""
Page Context Mapper

This module maps routes to their specific page context information.
It allows the summarizer agent to understand what each page is designed to do.
"""

from typing import Optional

# Define page-specific contexts for each route
PAGE_CONTEXTS = {
    '/calendar/configuration/config/agencyProfile': """
    ## Agency Profile Configuration Page

    **Purpose:** Configure the business/agency profile settings.

    **Key Actions Available:**
    - Upload or change agency logo (image upload)
    - Edit agency title/name (text input)
    - Update agency description (textarea)
    - Save profile changes

    **Expected Elements:**
    - Logo upload area with preview
    - Agency name input field
    - Agency description textarea
    - Save/Update button
    """,

    '/calendar/configuration/config/location': """
    ## Location Management Page

    **Purpose:** View and manage business locations.

    **Key Actions Available:**
    - View list of existing locations
    - Add new location
    - Edit existing location
    - Delete location

    **Expected Form Fields (when adding/editing location):**
    - Location name (required)
    - Address fields:
      * Street address (required)
      * Unit/Suite (optional)
      * City (required)
      * State (required)
      * Zip code (required)

    **Expected Elements:**
    - Location list/table
    - "Add Location" button
    - Location form (appears when adding/editing)
    - Save/Cancel buttons in form
    """,

    '/calendar/crm/home': """
    ## Customer Management (CRM) Page

    **Purpose:** Comprehensive customer management interface for viewing, searching, and managing customers.

    **Primary Actions:**
    1. **Search Customers** - Search input to find customers by name, email, phone
    2. **Add Customer** - Create new customer records manually
    3. **Bulk Upload** - Import multiple customers via CSV/Excel
    4. **Filter** - Filter customers by flag status, customer type, location
    5. **View Logs** - Access activity history and audit trails
    6. **Broadcast Message** - Send SMS/Email to selected customers

    **Customer Table Features:**
    - Columns: Name, Email, Phone, Status, Contact Actions, More Actions
    - Contact options per row:
      * Phone icon → initiate call
      * Video icon → start video call
      * Message icon → send SMS
      * Email icon → send email
      * Document icon → view/add notes
    - Three-dot menu per row:
      * Edit customer info
      * Flag customer
      * Delete customer
      * View/add last note

    **Key Workflows:**
    - **Add Single Customer:** Click "Add Customer" → Fill form (First Name, Last Name, Contact Number, Email, Address) → Create
    - **Broadcast Message:** Select customers (checkboxes) → Click "Message" → Choose SMS/Mail → Compose → Send
    - **Filter Customers:** Click "Filter" → Set criteria → Apply → View filtered results

    **Expected Form Fields (Add Customer):**
    - First Name (required)
    - Last Name (required)
    - Contact Number (required)
    - Email (required)
    - Address fields (optional)
    - Additional details (optional)

    **Broadcast Message Interface:**
    - Recipient selection display
    - Template selection (Mail/SMS tabs)
    - Delivery method radio buttons (By Mail / By SMS)
    - Message textarea
    - Action buttons: Cancel, Save Template, Send
    """,
}


def get_page_context(route: str) -> Optional[str]:
    """
    Get the page-specific context for a given route.

    Args:
        route: The current page route (e.g., '/calendar/crm/home')

    Returns:
        Page-specific context string or None if route not found
    """
    if not route:
        return None

    # Exact match first
    if route in PAGE_CONTEXTS:
        return PAGE_CONTEXTS[route]

    # Partial match (for routes with dynamic segments)
    for page_route, context in PAGE_CONTEXTS.items():
        if page_route in route or route in page_route:
            return context

    return None


def extract_page_context_from_app_context(route: str, web_app_context: str) -> Optional[str]:
    """
    Fallback method: Extract route-specific context from the full web_app_context string.
    Used when route is not in PAGE_CONTEXTS mapping.

    Args:
        route: Current page route (e.g., '/calendar/crm/home')
        web_app_context: Full application context string

    Returns:
        Page-specific context or None if not found
    """
    if not route:
        return None

    # Simple keyword matching
    route_keywords = {
        '/calendar/configuration/config/agencyProfile': 'Agency Profile',
        '/calendar/configuration/config/location': 'Location',
        '/calendar/crm/home': 'Customers',
    }

    # Find matching section in context
    for route_pattern, keyword in route_keywords.items():
        if route_pattern in route:
            # Extract the relevant section from web_app_context
            start_idx = web_app_context.find(f"- {keyword}")
            if start_idx != -1:
                # Find the next section or end
                next_section = web_app_context.find("\n  - ", start_idx + 1)
                if next_section != -1:
                    return web_app_context[start_idx:next_section]
                else:
                    return web_app_context[start_idx:]

    return None