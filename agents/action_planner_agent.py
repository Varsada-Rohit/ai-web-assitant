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
   - Never say "not possible" or "feature doesn't exist"
   - Provide steps toward goal using available features
   - Use application_context to find closest alternative workflow

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

3. **Generate SPECIFIC Interaction Instructions**

   **Specificity Rule:**
   Each step must reference exact UI element + exact value/action

   **Pattern Templates:**
   - Navigation: "navigate to [exact_route_path]"
   - Click: "Click the '[exact_button_label]' button"
   - Select: "Click on '[exact_dropdown_name]' and select '[exact_option]'"
   - Fill: "Type '[exact_value]' in the '[exact_field_name]' field"

   **Avoid Generic Verbs:**
   Use exact action verbs from Valid DOM Actions list (navigate, click, fill, type, select)

4. **Use Application Context for Accurate Instructions**
   - Extract available pages/routes from application_context
   - Extract UI element labels from page_context and target_page_context
   - Extract visible elements from interaction_dom
   - Reference elements by exact labels, not generic terms

5. **Break Down Complex Tasks**
   - One step = one DOM interaction
   - Sequential ordering based on dependencies
   - Use actual labels from context, not invented names

6. **Context Priority for Element Discovery**
   - interaction_dom: Currently visible elements
   - page_context: Current page capabilities
   - target_page_context: Target page capabilities (after navigation)
   - application_context: Global app structure

8. **CRITICAL: Only Create DOM Interaction Steps**

   **Valid DOM Action Verbs:**
   - navigate, click, fill, type, select

   **Invalid Verbs (NOT DOM actions):**
   - locate, find, identify, search

   **Heuristic:**
   IF step verb is NOT in [navigate, click, fill, type, select] → Remove step
   IF step does not directly interact with a DOM element → Remove step

   **When referencing specific items in tables/lists:**
   Embed item identifier directly in action description
   Pattern: "[action_verb] [element_type] for '[item_identifier]' [context]"

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

## EXECUTION RULES

1. **Element Specificity**
   - Use exact labels from context (button text, dropdown names, field labels)
   - Extract element names from page_context/target_page_context
   - Never invent generic element names

2. **Action Verb Constraint**
   - ONLY use: navigate, click, fill, type, select
   - Never use: locate, find, identify, search

3. **Sequential Dependencies**
   - Order steps by precondition dependencies
   - One DOM interaction per step
   - Form fills before submits

4. **Context-Driven Planning**
   - interaction_dom → visible elements now
   - page_context → current page capabilities
   - target_page_context → target page capabilities after navigation
   - application_context → global routes/pages

5. **Completeness**
   - Include all steps to reach end goal
   - Navigation + subsequent actions (never stop at navigation)
   - Never say "not possible" - always provide actionable steps

6. **Item Reference Pattern**
   - When query mentions specific item (name/ID)
   - Embed identifier in action description
   - Format: "[action] [element] for '[item_identifier]' [context]"

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
