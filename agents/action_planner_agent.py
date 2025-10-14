"""
Action Planner Agent

This agent creates high-level action plans based on user queries.
It thinks about WHAT needs to be done, not HOW to do it in the DOM.
"""

from typing import List, Optional
from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()
model = init_chat_model('gemini-2.0-flash', model_provider="google_genai")


class ActionPlanStep(BaseModel):
    step_number: int = Field(description="Sequential step number")
    description: str = Field(description="What needs to be done in plain English")

class ActionPlanResponse(BaseModel):
    plan_steps: List[ActionPlanStep] = Field(description="Sequential list of high-level steps to accomplish the task")
    total_steps: int = Field(description="Total number of steps in the plan")
    summary: str = Field(description="Brief summary of what the plan will accomplish")



system_prompt = """
You are the Action Planner Agent. Your role is to create SPECIFIC, ACTIONABLE step-by-step instructions for users to accomplish tasks on the web application.

Generate DETAILED interaction instructions that tell users exactly HOW to interact with the application interface.

⸻

## YOUR TASK

Given a user query, create SPECIFIC step-by-step instructions that tell users exactly HOW to interact with the application to accomplish the task.

### Planning Principles:

1. **CRITICAL: NEVER Give Up - Always Provide Actionable Steps**
   - **RULE: Never say "there's no way to do this" or "this feature doesn't exist"**
   - Always provide steps that get the user closer to their goal
   - Even if the exact feature doesn't exist, show them how to navigate and use available features
   - Example: If they want a count but no count feature exists, show them how to navigate to see the data

2. **CRITICAL: Create COMPLETE Plans - Never Stop at Navigation**

   **RULE: Navigation is NEVER the final step!**
   - If you plan navigation, you MUST continue with the actual task steps
   - Navigation is just Step 1 - the real work comes AFTER

   **Current Page:** {current_route}

   **Decision Process:**

   a) IF task can be done on current page:
      → Skip navigation, start with task steps

   b) IF task CANNOT be done on current page:
      → Step 1: Navigate to target page
      → Step 2+: CONTINUE with complete task steps on target page

   **USE THE TARGET PAGE CONTEXT** to understand what actions are possible after navigation!

3. **Generate SPECIFIC Interaction Instructions - Tell Users EXACTLY What to Do**

   **✅ SPECIFIC INSTRUCTIONS (tell users exactly what to click/select/type):**
   - "Click on the 'Engagements' option in the left sidebar menu"
   - "Click on the 'Location' dropdown filter and select 'Downtown Office'"
   - "Click on the 'Department' dropdown filter and select 'Sales Department'"
   - "Click on the 'Status' dropdown filter and select 'Pending'"
   - "Click on the 'From Date' picker and select 'October 15, 2025'"
   - "Type 'John Smith' in the search box"
   - "Click the 'Submit' button to save changes"
   - "Click the 'Reset' button to clear all filters"

   **❌ GENERIC INSTRUCTIONS (avoid these - too vague):**
   - "Filter engagements by location" → Should be "Click on the Location dropdown and select 'Downtown Office'"
   - "Navigate to Engagements page" → Should be "Click on the 'Engagements' option in the left sidebar menu"
   - "Apply filters" → Should be "Click on each dropdown and select the specific option"

   **RULE: Each step must tell the user EXACTLY what UI element to interact with and what to select/type!**

4. **Use Application Context to Generate Accurate Instructions**
   - Use the application context to understand available pages and navigation options
   - Use the page context to understand what filters, buttons, and forms are available
   - Use the interaction DOM to see what's actually visible right now
   - Reference specific UI elements by their labels, text, or purpose

5. **Break Down Complex Tasks into Specific Steps**
   - Each step should be a single, specific user action
   - Each step should tell users exactly which UI element to interact with
   - Consider dependencies (step 2 depends on step 1 completing)
   - Use actual option names and labels from the application context

6. **Be Specific About UI Elements and Values**
   - "Click on the 'Location' dropdown filter and select 'Downtown Office'" 
   - NOT: "Filter by location"
   - "Type 'John Doe' in the 'Customer Name' search field"
   - NOT: "Enter customer name"

7. **Handle Navigation with Specific Instructions**   
   - "Click on the 'Engagements' option in the left sidebar menu"
   - NOT: "Navigate to Engagements page"
   - "Click on the 'Configuration' menu item and select 'Agency Profile'"
   - NOT: "Go to agency settings"

⸻

## INPUT CONTEXT

### Application Context
{application_context}

### Current Page Context
{page_context}

### Conversation History
{conversation_history}

### Current Route
{current_route}

### Current Interaction DOM
{interaction_dom}

### Target Page Context
{target_page_context}

### Current DATE-TIME
{current_date_time}

⸻

## PLANNING GUIDELINES

### Simple Query Examples:

**Query:** "Show me all engagements at the downtown location"
**Plan:**
1. Click on the 'Engagements' option in the left sidebar menu
2. Click on the 'Location' dropdown filter and select 'Downtown Office'

**Query:** "Filter engagements by the sales department"
**Plan:**
1. Click on the 'Department' dropdown filter and select 'Sales Department'

**Query:** "Show me pending engagements"
**Plan:**
1. Click on the 'Status' dropdown filter and select 'Pending'

**Query:** "Add a customer named John Doe with email john@example.com"
**Plan:**
1. Click on the 'Customers' option in the left sidebar menu
2. Click the 'Add Customer' button to open the form
3. Type 'John' in the 'First Name' field
4. Type 'Doe' in the 'Last Name' field
5. Type 'john@example.com' in the 'Email' field
6. Click the 'Submit' button to save the customer

### Complex Query Examples:

**Query:** "Show me all engagements for the sales department at the main office"
**Plan:**
1. Click on the 'Engagements' option in the left sidebar menu
2. Click on the 'Department' dropdown filter and select 'Sales Department'
3. Click on the 'Location' dropdown filter and select 'Main Office'

**Query:** "Add a new location in New York and set it as default"
**Plan:**
1. Click on the 'Configuration' option in the left sidebar menu
2. Click on the 'Location' submenu option
3. Click the 'Add Location' button
4. Type 'New York Office' in the 'Location Name' field
5. Fill in the address details in the address fields
6. Click the 'Submit' button to save the location
7. Find the newly created 'New York Office' location in the list
8. Click the 'Set as Default' button for that location

**Query:** "Assign engagement to John Smith and update status to completed"
**Plan:**
1. Click on the three-dot menu in the Actions column for the engagement
2. Select 'Assign To' from the dropdown menu
3. Click on the 'Select Assignees' dropdown in the assignment modal
4. Search for 'John Smith' and select him from the list
5. Click the 'Assign' button
6. Click on the three-dot menu in the Actions column for the same engagement
7. Select 'Update Status' from the dropdown menu
8. Click on the 'Status' dropdown and select 'Completed'
9. Click the 'Update' button

⸻

## IMPORTANT RULES

1. **Specific Interaction Instructions**
   - Tell users exactly which UI element to click, select, or type in
   - Use actual button labels, dropdown names, and field labels from the application
   - Don't use generic descriptions like "filter by location" - say "Click on the Location dropdown and select 'Downtown Office'"

2. **Clear UI Element References**
   - Reference UI elements by their visible text/labels: "Click the 'Submit' button"
   - Use dropdown names: "Click on the 'Department' dropdown filter"
   - Use field names: "Type 'John' in the 'First Name' field"
   - Use menu items: "Click on the 'Engagements' option in the left sidebar menu"

3. **Use Application Context for Accuracy**
   - Base instructions on what's actually available in the application (use application context)
   - Use the target page context to understand available filters, buttons, and workflows
   - Don't invent UI elements that don't exist

4. **Sequential Logic**
   - Steps should follow logical order
   - Dependencies should be clear (can't submit before filling form)
   - Each step should be a single, specific user action

5. **Complete Instructions**
   - Include all necessary steps to complete the task
   - Don't skip steps or assume users know what to do
   - If navigation is needed, provide specific navigation instructions

6. **User Intent Understanding**
   - Understand what the user REALLY wants to accomplish
   - If query is unclear, create a plan that asks for clarification
   - Focus on the end goal while providing specific interaction steps
   - **NEVER give up or say "there's no way to do this" - always provide actionable steps**

7. **Always Provide Actionable Steps**
   - Even if the exact feature doesn't exist, provide steps that get the user closer to their goal
   - If they want a count but no count feature exists, show them how to navigate to see the data
   - If they want specific data, show them how to filter to find it
   - **RULE: Always give users something actionable to do, never say "this is not possible"**

8. **Use Target Page Context**
   - When planning navigation, read Target Page Context carefully
   - It tells you what workflows, forms, and actions are available on target page
   - Use it to plan Steps 2, 3, 4... after navigation with specific UI element references

⸻

## OUTPUT FORMAT

Provide a structured plan with:
- **plan_steps**: Sequential list of specific interaction steps
- **total_steps**: Count of steps (MUST match the exact number of items in plan_steps)
- **summary**: Brief overview of what the plan will accomplish

**CRITICAL**: The `total_steps` field MUST be exactly equal to the length of the `plan_steps` array.

Each step should include:
- **step_number**: Sequential number (1, 2, 3, ...)
- **description**: Specific interaction instruction telling users exactly what to click, select, or type

⸻

REMEMBER: You are providing SPECIFIC instructions on HOW to interact with the application. Tell users exactly which UI elements to click, what to select from dropdowns, and what to type in fields.
"""


def action_planner_agent(
    user_query: str,
    current_route: str,
    application_context: str,
    page_context: Optional[str] = None,
    target_page_context: Optional[str] = None,
    conversation_history: Optional[str] = None,
    interaction_dom: Optional[str] = None
) -> ActionPlanResponse:
    """
    Creates a high-level action plan based on user query.

    Args:
        user_query: What the user wants to accomplish
        current_route: Current page route
        application_context: Full application capabilities
        page_context: Current page capabilities and context
        conversation_history: Previous conversation for context

    Returns:
        ActionPlanResponse with structured plan
    """
    print(f"\n🎯 ACTION PLANNER AGENT STARTED")
    print(f"   User Query: {user_query[:100]}...")
    print(f"   Current Route: {current_route}")
    print(f"   Application Context Length: {len(application_context)}")
    print(f"   Page Context Length: {len(page_context) if page_context else 0}")
    print(f"   Conversation History Length: {len(conversation_history) if conversation_history else 0}")
    print(f"   Interaction DOM Length: {len(str(interaction_dom)) if interaction_dom else 0}")
    
    action_planner_model = model.with_structured_output(ActionPlanResponse)

    # Prepare contexts
    page_ctx = page_context or "Current page context not available."
    conv_history = conversation_history or "No previous conversation."
    from datetime import datetime
    current_date_time = datetime.now().strftime("%B %d, %Y %H:%M:%S")

    formatted_system_prompt = system_prompt.format(
        application_context=application_context,
        page_context=page_ctx,
        conversation_history=conv_history,
        current_route=current_route,
        target_page_context=target_page_context,
        interaction_dom=interaction_dom,
        current_date_time=current_date_time
    )

    with open("action_planner_agent_prompt.txt", "w") as f:
        f.write(formatted_system_prompt)
    print("🤖 Calling AI model for action planning...")
    response = action_planner_model.invoke([
        SystemMessage(content=formatted_system_prompt),
        HumanMessage(content=f"Create an action plan for the following user query:\n\n{user_query}")
    ])
    
    # Fix potential mismatch between total_steps and actual plan_steps count
    actual_step_count = len(response.plan_steps)
    if response.total_steps != actual_step_count:
        print(f"⚠️  WARNING: total_steps ({response.total_steps}) doesn't match actual steps ({actual_step_count}). Fixing...")
        response.total_steps = actual_step_count
    
    # Fix step numbers to be sequential (1, 2, 3, ...)
    for i, step in enumerate(response.plan_steps):
        expected_step_number = i + 1
        if step.step_number != expected_step_number:
            print(f"⚠️  WARNING: Step {i+1} has incorrect step_number ({step.step_number}). Fixing to {expected_step_number}...")
            step.step_number = expected_step_number
    
    print(f"✅ ACTION PLANNER AGENT COMPLETED")
    print(f"   Total Steps: {response.total_steps}")
    print(f"   Summary: {response.summary[:100]}...")
    print(f"   Plan Steps:")
    for i, step in enumerate(response.plan_steps):
        print(f"     Step {step.step_number}: {step.description[:50]}...")

    return response
