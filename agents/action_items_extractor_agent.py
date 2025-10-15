from typing import Dict, Any, Literal, List, Optional

from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
from pydantic import Field, BaseModel
from contexts.app_context import web_app_context

load_dotenv()
model = init_chat_model("gpt-4.1-mini",model_provider="azure_openai",api_version="2024-12-01-preview")

# 
class ActionItem(BaseModel):
    action: Literal["click", "fill", "select", "navigate"] = Field(description="The action to be performed")
    element_selector: str = Field(description="The element selector to select the element to be clicked, filled, selected. Can be empty if the action is navigate.")
    value: str = Field(description="The value to be filled, selected, or navigated to (route)")
    description: str = Field(description="The description of the action to be performed")
    

class ActionItemsExtractorResponse(BaseModel):
    action_items: List[ActionItem] = Field(description="DOM actions to execute for current batch")
    message: str = Field(description="The message to be displayed to the user. Or if any information is missing, ask the user for it.")

    # Progress tracking fields
    completed_steps: List[int] = Field(description="Plan step numbers that are fully completed (verified in DOM)")
    current_batch_steps: List[int] = Field(description="Plan step numbers being executed in this batch")
    remaining_steps: List[int] = Field(description="Plan step numbers not yet executable (waiting for DOM elements)")

    # Completion tracking
    task_completed: bool = Field(description="True if all plan steps completed AND expected outcome verified in DOM")
    current_iteration: int = Field(description="Current execution iteration number")

    # Batching explanation
    batch_reason: str = Field(description="Explanation of why these steps are batched together based on DOM analysis")
    blocked_reason: Optional[str] = Field(default=None, description="If steps are blocked, explain what DOM elements are missing")

system_prompt = """
# ACTION ITEMS EXTRACTOR AGENT

You convert high-level plan steps into executable DOM actions based on current page state.

⸻

## INPUT CONTEXT

### Action Plan
{action_plan}

### Execution State
{execution_state}

### Current DOM Context
- distilledNodes: {distilledNodes}
- mainTree: {mainTree}
- appState: {appState}
- route: {route}

### Additional Context
- User Query: {user_query}
- Conversation History: {conversation_history}
- Web App Context: {web_app_context}
- Current Date/Time: {current_date_time}

⸻

## EXECUTION HEURISTIC

**Core Principle:** Process steps sequentially. A step is executable if its preconditions are met in the current page state.

### Step Classification Logic

For each remaining plan step, classify as:

1. **COMPLETED** - Already done (verify against current state)
   - Navigation step where current route matches target route
   - Action already reflected in current DOM state

2. **EXECUTABLE** - Can execute now with current DOM
   - Navigation step (requires route change)
   - DOM interaction where target element exists in distilledNodes

3. **BLOCKED** - Cannot execute yet (preconditions not met)
   - DOM element not present in current page
   - Depends on earlier step that hasn't executed

### Precondition Rules

**Navigation Steps:**
- Pattern: Step description contains "navigate to [route]"
- Precondition: None (navigation is always possible)
- Check: Compare current route vs target route
- If routes match → Mark COMPLETED
- If routes differ → Mark EXECUTABLE, batch immediately
- Never check target page's DOM elements before navigation completes

**DOM Interaction Steps:**
- Pattern: Steps that click/fill/select DOM elements
- Precondition: Element must exist in current distilledNodes
- Check: Search distilledNodes for matching selector (id, aria-label, etc.)
- If element found → Mark EXECUTABLE
- If element not found → Mark BLOCKED

### Batching Heuristic

**Rule 1: Navigation Blocks Everything**
- If first remaining step is navigation AND route doesn't match → Batch ONLY navigation
- Reason: Page will change, current DOM becomes invalid

**Rule 2: Batch Consecutive Executable Steps**
- If no navigation needed → Batch all consecutive executable steps
- Stop batching when you hit first BLOCKED step

**Rule 3: Never Batch Across Pages**
- Don't batch steps that require elements from different pages

⸻

## ACTION GENERATION

### Action Types

**navigate:** Route change (no DOM selector needed)
- element_selector: "" (empty)
- value: Target route path
- Example: {{"action": "navigate", "element_selector": "", "value": "/calendar/engagements/home"}}

**click:** Click a button/link
- element_selector: DOM selector (id or aria-label)
- value: "" (empty)
- Example: {{"action": "click", "element_selector": "#submit-btn", "value": ""}}

**fill:** Type text into input field
- element_selector: DOM selector
- value: Text to enter
- Example: {{"action": "fill", "element_selector": "#search-input", "value": "John Doe"}}

**select:** Select from dropdown or date picker
- element_selector: DOM selector
- value: Option to select (use format "MMM DD, YYYY" for dates)
- Example: {{"action": "select", "element_selector": "#from-date", "value": "Sep 15, 2025"}}

### Selector Extraction Best Practices

**Preference Hierarchy:**
1. **data-* attributes** (most stable across app changes)
2. **id attribute** (reliable but requires edge case handling)
3. **aria-label** (semantic and stable)
4. **class names** (last resort, may be dynamic)

**ID Selector Rules:**

1. **IDs Starting with Digits:**
   - ✅ VALID: `document.getElementById("123abc")` (no escaping needed)
   - ❌ INVALID: `querySelector("#123abc")` (CSS syntax error)
   - ✅ VALID: `querySelector("#\\31 23abc")` (escape first digit as `\3X `)
   - ✅ VALID: `querySelector("[id='123abc']")` (attribute selector fallback)

   **Decision Rule:** If ID starts with digit → Use `getElementById` in frontend OR escape first digit

2. **Special Characters in IDs:**
   - Characters requiring escaping: `. # : [ ] ( ) @ $ * + ~ > | ^ =`
   - Example: `id="user.email"` → `querySelector("#user\\.email")`
   - Example: `id="btn:submit"` → `querySelector("#btn\\:submit")`

3. **Uniqueness Validation:**
   - ALWAYS verify selector matches exactly ONE element in distilledNodes
   - If multiple matches found → Add parent context or switch to more specific selector

**Selector Generation Algorithm:**

```
FOR each DOM interaction step:
  1. Check if element has data-* attribute → Use `[data-test-id="value"]`
  2. Check if element has id:
     - If id starts with digit → Use `getElementById` notation or `[id="value"]`
     - If id contains special chars → Escape them OR use `[id="value"]`
     - Otherwise → Use `#id-value`
  3. Check if element has aria-label → Use `[aria-label="value"]`
  4. Fallback to class → Use `.class-name` (warn if dynamic)
  5. Validate: Ensure selector is unique in distilledNodes
     - If not unique → Add parent context or fail with blocked_reason
```

**Common Edge Cases:**

- **Dynamic IDs**: Avoid selectors like `#input-1234567890` (timestamp/random suffix)
- **Compound Selectors**: Use `#parent-id #child-id` only if single selector is ambiguous
- **Hidden Elements**: Verify element is not `display:none` or `visibility:hidden`
- **Iframe Context**: Note if element is inside iframe (requires special handling)

⸻

## OUTPUT STRUCTURE

Return:
- **action_items**: Array of actions for current_batch_steps
- **completed_steps**: Step numbers already done
- **current_batch_steps**: Step numbers being executed now
- **remaining_steps**: Step numbers not yet executable
- **task_completed**: true if all steps processed
- **current_iteration**: Iteration count
- **batch_reason**: Why these steps are batched together
- **blocked_reason**: Why remaining steps are blocked (null if none blocked)
- **message**: User-facing message

⸻

## DECISION TREE

```
START
  ↓
Get next remaining step
  ↓
Is it navigation?
  ├─ YES → Current route == target route?
  │         ├─ YES → Mark COMPLETED, continue to next step
  │         └─ NO  → Mark EXECUTABLE, batch [this step only], STOP
  │
  └─ NO → Is element in distilledNodes?
            ├─ YES → Mark EXECUTABLE, continue to next step
            └─ NO  → Mark BLOCKED, remaining steps also BLOCKED, STOP
```

⸻

## CRITICAL RULES

1. **Sequential Processing**: Always process steps in order (step 1, then 2, then 3...)
2. **Navigation First**: If step requires navigation, batch ONLY navigation, mark rest as remaining
3. **No Future Checking**: Don't check elements for steps after a navigation step
4. **Date Format**: Dates must be "MMM DD, YYYY" format (e.g., "Sep 15, 2025")
5. **Empty Selectors**: Navigation actions have empty element_selector

⸻

## EXECUTION STEPS

1. **Apply Decision Tree:** Process each remaining step using the decision tree above
2. **Classify Steps:** Mark each as COMPLETED, EXECUTABLE, or BLOCKED
3. **Determine Batch:** Use batching heuristic to identify current_batch_steps
4. **Generate Actions:** For EACH step in current_batch_steps, create an action item:
   - Extract route from navigation step description (text after "navigate to")
   - Extract selector from DOM step description (search distilledNodes for matching element)
   - Extract value from step description (date, text, or dropdown value)
   - Build action object with correct type, selector, value, description
5. **Return Output:** Populate all output fields including action_items array

**CRITICAL:** The action_items array MUST contain one action object for each step number in current_batch_steps. If current_batch_steps = [1], then action_items MUST have exactly 1 item.

"""

def action_items_extractor_agent(
    context: Dict[str, Any],
    query: str,
    action_plan: Dict[str, Any],
    execution_state: Dict[str, Any],
    conversation_history: Optional[str] = None
) -> ActionItemsExtractorResponse:
    """
    Analyzes action plan and current DOM to determine which steps are executable and generate DOM actions.

    Args:
        context: Current DOM context (distilledNodes, mainTree, appState, route)
        query: User's original query
        action_plan: Action plan from action planner agent (dict with plan_steps, total_steps, summary)
        execution_state: Current execution state (completed_steps, remaining_steps, current_iteration)
        conversation_history: Previous conversation context

    Returns:
        ActionItemsExtractorResponse with batched actions and progress tracking
    """
    print(f"\n🎯 ACTION ITEMS EXTRACTOR AGENT STARTED")
    print(f"   User Query: {query[:100]}...")
    print(f"   Current Route: {context.get('route', 'Unknown')}")
    print(f"   Distilled Nodes Count: {len(context.get('distilledNodes', []))}")
    print(f"   Action Plan Steps: {action_plan.get('total_steps', 0)}")
    print(f"   Execution State: Completed={execution_state.get('completed_steps', [])}, Remaining={execution_state.get('remaining_steps', [])}")
    print(f"   Iteration: {execution_state.get('current_iteration', 0)}")

    action_items_extractor_model = model.with_structured_output(ActionItemsExtractorResponse)

    # Format action plan for prompt
    action_plan_formatted = f"""
Total Steps: {action_plan.get('total_steps', 0)}
Summary: {action_plan.get('summary', '')}

Plan Steps:
"""
    for step in action_plan.get('plan_steps', []):
        action_plan_formatted += f"Step {step.get('step_number', 0)}: {step.get('description', '')}\n"

    # Format execution state for prompt
    execution_state_formatted = f"""
Completed Steps: {execution_state.get('completed_steps', [])}
Remaining Steps: {execution_state.get('remaining_steps', [])}
Current Iteration: {execution_state.get('current_iteration', 0)}
"""

    # Get current date/time
    from datetime import datetime
    current_date_time = datetime.now().strftime("%B %d, %Y %H:%M:%S")

    # Prepare context values
    conv_history = conversation_history or "No previous conversation."


    formatted_prompt = system_prompt.format(
        action_plan=action_plan_formatted,
        execution_state=execution_state_formatted,
        distilledNodes=context.get('distilledNodes', []),
        mainTree=context.get('mainTree', []),
        appState=context.get('appState', {}),
        route=context.get('route', ''),
        user_query=query,
        conversation_history=conv_history,
        web_app_context=web_app_context,
        current_date_time=current_date_time
    )



    messages = [
        SystemMessage(content=formatted_prompt),
        HumanMessage(content=f"Analyze the action plan and current DOM, then generate DOM actions for executable steps.\n\nUser Query: {query}")
    ]

    print("🤖 Calling AI model for action items extraction...")
    response = action_items_extractor_model.invoke(messages)

    print(f"✅ ACTION ITEMS EXTRACTOR COMPLETED")
    print(f"   Generated {len(response.action_items)} action items")
    print(f"   Completed Steps: {response.completed_steps}")
    print(f"   Current Batch Steps: {response.current_batch_steps}")
    print(f"   Remaining Steps: {response.remaining_steps}")
    print(f"   Task Completed: {response.task_completed}")
    print(f"   Batch Reason: {response.batch_reason}")
    if response.blocked_reason:
        print(f"   Blocked Reason: {response.blocked_reason}")
    print(f"   Message: {response.message[:100]}...")

    # Print each action item
    for i, item in enumerate(response.action_items):
        print(f"   Action {i+1}: {item.action} -> {item.element_selector} - {item.description[:50]}...")

    return response