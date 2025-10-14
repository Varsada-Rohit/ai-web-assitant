"""
Page Context Mapper

This module maps routes to their specific page context information.
It allows the summarizer agent to understand what each page is designed to do.
"""

from typing import Optional, List

# Define page-specific contexts for each route
PAGE_CONTEXTS = {
    '/calendar/calendar/configuration/config/agencyProfile': """
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

    '/calendar/calendar/configuration/config/location': """
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

    '/calendar/calendar/engagements/home': """
    ## Engagements Page

    **Purpose:** View and manage engagements (appointments/bookings) registered in the system. Perform actions such as assigning engagements to team members, updating engagement status, and canceling assignments.

    **Primary Goal:** Centralized management of all engagements with filtering, assignment, and status tracking capabilities.

    **Tasks Available:**
    - View all engagements in a filterable table
    - Filter engagements by location, department, engagement type, status, date range, and users
    - Assign engagements to one or multiple team members
    - Update engagement status through predefined status options
    - Cancel engagement assignments
    - View detailed engagement information
    - Sort engagements by Date & Time or Booked On timestamp
    - Export engagement reports and staff reports
    - View personal engagements assigned to the logged-in user

    **Page Layout:**
    1. **Header Section:**
       - Page title: "Engagements"
       - Filter bar with dropdowns and date pickers
       - Reset button to clear all filters
       - Reports dropdown menu (right side)

    2. **Main Content Area:**
       - "My Personal Engagements" collapsible section (shows engagements assigned to current user)
       - Engagement table with sortable columns
       - Pagination controls at bottom

    **Filter Controls:**
    - Location Dropdown (#location-filter) - Filter by location (options: dynamic from system locations, default: "All")
    - Department Dropdown (#department-filter) - Filter by department (options: dynamic, default: "All")
    - Engagement Type Dropdown (#engagement-type-filter) - Filter by type (options: dynamic, default: "All")
    - Status Dropdown (#status-filter) - Filter by status (options: Pending, Completed, No Show, Held, Check-In, Closed, default: "All")
    - From Date Picker (#from-date) - Set start date (format: MM/DD/YYYY)
    - To Date Picker (#to-date) - Set end date (format: MM/DD/YYYY)
    - Users Dropdown (#users-filter) - Filter by assigned user (options: dynamic, default: "All")
    - Reset Button (#reset-filters-btn) - Clear all filters

    **Table Actions (Three-Dot Menu #engagement-actions-menu):**
    - **Assign To** - Opens assignment modal to assign team members
    - **Cancel** - Opens cancellation confirmation dialog
    - **Update Status** - Opens status update modal
    - **View Details** - Opens detailed engagement view

    **Key Workflows:**

    **Workflow 1: Filter Engagements**
    1. Select desired filters (location, department, type, status, date range, or user)
    2. Table automatically updates to show filtered results
    3. Apply multiple filters simultaneously
    4. Click "Reset" to clear all filters
    Expected: Narrowed engagement list matching filter criteria

    **Workflow 2: Assign Engagement to Team Members**
    1. Locate engagement in table
    2. Click three-dot menu in Actions column
    3. Select "Assign To" option
    4. Assignment modal appears showing engagement details
    5. Click "Select Assignees" dropdown
    6. Search for team member(s) or select from list
    7. Select one or multiple assignees (multi-select enabled)
    8. Click "Assign" button
    Expected: Selected team members assigned to engagement, modal closes, table updates

    **Workflow 3: Update Engagement Status**
    1. Locate engagement in table
    2. Click three-dot menu → Select "Update Status"
    3. Status update modal appears with current status selected
    4. Select new status from dropdown (Pending, Completed, No Show, Held, Check-In, Closed)
    5. Click "Update" button
    Expected: Engagement status updated, modal closes, table reflects new status

    **Workflow 4: Cancel Engagement Assignment**
    1. Locate engagement in table
    2. Click three-dot menu → Select "Cancel"
    3. Confirmation dialog: "Are you sure you want to cancel the engagement?"
    4. Click "Confirm" button
    Expected: Engagement assignment cancelled

    **Workflow 5: Download Reports**
    1. Click reports dropdown menu (top-right)
    2. Select report type: Staff Reports or Engagements Reports
    Expected: Report file downloads to device

    **Workflow 6: Sort Engagements**
    1. Click "Date & Time" or "Booked On" column header
    2. First click: Sort ascending, Second click: Sort descending
    Expected: Table reorders based on selected column

    **Forms:**

    **Assign Engagement Form:**
    - Display-Only: Engagement Type, Date & Time, Location, Department
    - Interactive: Select Assignees (multi-select dropdown with search, shows selected as pills/badges)
    - Actions: Cancel, Assign

    **Update Status Form:**
    - Required: Engagement Status dropdown (Pending, Completed, No Show, Held, Check-In, Closed)
    - Actions: Cancel, Update

    **Cancel Engagement Form:**
    - Confirmation message
    - Actions: Cancel, Confirm

    **Table Columns:**
    - Name, Contact Number, Location, Department, Engagement Type
    - Date & Time (sortable), Booked On (sortable)
    - Status, Additional Fields, Assigned To, Actions

    **Pagination:**
    - Default: 10 rows per page
    - Options: 10, 25, 50, or All
    - Display: "1-10 of 47 engagements"
    - Navigation: Previous/Next arrows

    **Conditional Behavior:**
    - My Personal Engagements section: Automatically filtered to logged-in user's assignments
    - Multiple assignees can be selected for a single engagement
    - Reassigning adds new assignees to existing assignments
    - Only Date & Time and Booked On columns are sortable

    **Empty States:**
    - No engagements: "No engagements found. Engagements will appear here once created."
    - No filtered results: "No engagements match your filters. Try adjusting your criteria."
    - No personal engagements: "You have no assigned engagements at this time."
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

    # Partial match (for routes with dynamic segments or query params)
    for page_route, context in PAGE_CONTEXTS.items():
        if page_route in route:
            return context

    return None


def get_all_routes() -> List[str]:
    """
    Get list of all registered routes.

    Returns:
        List of route paths
    """
    return list(PAGE_CONTEXTS.keys())


def add_page_context(route: str, context: str) -> None:
    """
    Dynamically add a new page context.
    Useful for runtime context registration.

    Args:
        route: Route path
        context: Page context description
    """
    PAGE_CONTEXTS[route] = context


def get_target_pages(query: str, web_app_context: str, conversation_history: str) -> Optional[str]:
    """
    Get the target pages for a given query.
    """
    #TODO: make llm call - given question , conversation history , routes list - get the target page route . 
    return "/calendar/calendar/engagements/home"