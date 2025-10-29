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

### Item Lookup Heuristic

**When step references specific item identifier:**

STEP 1: Extract item identifier
- Pattern: Text in quotes ('[item]' or "[item]")
- This is the target to find in DOM

STEP 2: Search distilledNodes for identifier
- Search locations: text content, aria-labels, data attributes, ids
- Search contexts: table rows, list items, card elements

STEP 3: Decision tree

```
IF item found in distilledNodes:
  → Extract element selector
  → Mark step EXECUTABLE
  → Generate action

ELSE (item NOT found):
  → Detect lookup mechanisms in distilledNodes

  IF search input exists:
    → Generate fill action with item identifier
    → Mark original step BLOCKED
    → blocked_reason: "Searching for item"

  ELSE IF filter dropdowns exist:
    → Analyze filter relevance to item
    → Generate select action for relevant filter
    → Mark original step BLOCKED
    → blocked_reason: "Applying filter to find item"

  ELSE IF pagination controls exist:
    → Generate click action on Next/pagination
    → Mark original step BLOCKED
    → blocked_reason: "Item not on current page, checking next"

  ELSE:
    → Mark step BLOCKED
    → blocked_reason: "Item not found, no lookup mechanisms available"
    → task_completed: false
```

STEP 4: Next iteration after lookup action
- Re-execute STEP 2 (search distilledNodes)
- IF found → Execute original action
- IF not found → Try next lookup mechanism or terminal block

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

**navigate:**
- element_selector: "" (empty string)
- value: Target route path from step description

**click:**
- element_selector: Extracted DOM selector
- value: "" (empty string)

**fill:**
- element_selector: Extracted DOM selector for input field
- value: Text content to enter

**select:**
- element_selector: Extracted DOM selector for dropdown/picker
- value: Option value to select (dates as "MMM DD, YYYY")

### Selector Extraction Best Practices

**Preference Hierarchy:**
1. **data-* attributes** (most stable across app changes)
2. **id attribute** (reliable but requires edge case handling)
3. **aria-label** (semantic and stable)
4. **class names** (last resort, may be dynamic)

**ID Selector Rules:**

1. **CRITICAL: Digit-Starting IDs (Common Error)**
   - Pattern: id value starts with [0-9]
   - Examples: "0-actions", "123abc", "5-button"

   **NEVER use `#` prefix for digit-starting IDs:**
   - `#0-actions` ❌ INVALID - querySelector will fail
   - `[id="0-actions"]` ✅ VALID - always works

   **Reason:** CSS selector syntax does not allow `#` prefix when ID starts with digit

   **Detection Heuristic:**
   ```
   IF id[0] in '0123456789':
       selector_format = '[id="<id_value>"]'  ← REQUIRED
   ELSE:
       selector_format = '#<id_value>'  ← OK for non-digit IDs
   ```

2. **Special Character IDs:**
   - Characters: `. # : [ ] ( ) @ $ * + ~ > | ^ =`
   - Syntax: Use `[id="value"]` format OR escape characters
   - Preference: `[id="value"]` (simpler than escaping)

3. **Uniqueness Validation:**
   - Verify selector matches exactly ONE element in distilledNodes
   - IF multiple matches → Add parent context OR use more specific attribute

**Selector Generation Algorithm:**

```
FOR each DOM interaction step:
  1. Search distilledNodes for target element matching step description

  2. ⚠️ VALIDATION: Check element's attributes object
     - ONLY use attributes that exist in the attributes object
     - IF you don't see an attribute → DO NOT use it in selector
     - Example: IF attributes has role and class but no id or aria-label
       → ❌ Cannot use [id="..."] (id not in attributes)
       → ❌ Cannot use [aria-label="..."] (aria-label not in attributes)
       → ✅ Can use [role="menuitem"] (role exists in attributes)

  3. Check element attributes in order of preference:
     a) data-* attribute exists in attributes → Use [data-testid="value"]

     b) id attribute exists in attributes → CRITICAL: Check first character:
        IF id[0] in '0123456789':
          → MUST use [id="value"] format
          → NEVER use #id format (CSS syntax error)
        ELSE IF id contains special chars (. : [ ] etc):
          → Use [id="value"] format
        ELSE:
          → Use #id format

     c) aria-label attribute exists in attributes → Use [aria-label="value"]

     d) STOP HERE - do not proceed if no unique attribute found

  4. IF no unique attribute found (common for menu items):
     a) Check if element has text content
     b) Find parent menu container using aria-labelledby:
        - Menu items have parent with role="menu"
        - Menu has aria-labelledby pointing to trigger button
        - Use: ul[aria-labelledby='button-id'] NOT button-id > ul
     c) Build selector WITHOUT text matching pseudo-selectors:
        - ❌ WRONG: "[id='button'] > ul[role='menu']" (child selector)
        - ❌ WRONG: "li[role='menuitem']:has-text('Cancel')" (pseudo-selector)
        - ✅ CORRECT: "ul[aria-labelledby='button-id'] > li[role='menuitem']"
     d) Put text content in value field for frontend filtering:
        - element_selector: "ul[aria-labelledby='button-id'] > [role='menuitem']"
        - value: "Cancel"  ← Text to match goes here, not in selector
        - Frontend will: querySelectorAll(selector).find(el => el.textContent === value)

     **CRITICAL: Menu containers are NOT children of trigger buttons**
     - Modern frameworks (MUI, React) render menus in portals
     - Use aria-labelledby relationship, NOT parent-child selectors
     - Pattern: ul[aria-labelledby='X'] NOT [id='X'] > ul

  5. Validate: Ensure selector strategy is unambiguous
     - If multiple matches possible without text filtering → Use text match strategy
     - If parent context unclear → Fail with blocked_reason
```

**CRITICAL RULES:**

1. **Never invent attributes that don't exist in distilledNodes**
   - IF element has no aria-label in distilledNodes → DO NOT use [aria-label="..."]
   - IF element has no id in distilledNodes → DO NOT use #id or [id="..."]
   - Only use attributes that are explicitly present in the element's attributes object

2. **Never use pseudo-selectors for text matching**
   - ❌ NEVER use: :has-text(), :contains(), :text(), :is(), :where()
   - ❌ NEVER use: Playwright/Puppeteer/Testing Library specific syntax
   - ✅ ONLY use: Standard CSS selectors supported by querySelector()

   **Why:** Frontend uses document.querySelector() which only supports CSS Level 4

   **When element has no unique attribute but has text content:**
   - Put parent selector + role in element_selector
   - Put text content in value field
   - Frontend will filter by text matching

3. **Never use parent-child selectors for menus/dialogs**
   - ❌ NEVER use: [id="button"] > ul[role="menu"]
   - ❌ NEVER use: button > div[role="dialog"]
   - ✅ ALWAYS use: ul[aria-labelledby="button"]
   - ✅ ALWAYS use: div[role="dialog"][aria-labelledby="button"]

   **Why:** Modern frameworks render menus/dialogs in portals (React Portal, body appends)
   - They are NOT children of trigger elements
   - Use aria-labelledby relationship to find them
   - Pattern: [role="menu"][aria-labelledby="X"] NOT [id="X"] > [role="menu"]

**Edge Cases:**

- **Dynamic IDs**: Avoid timestamp/random suffixes (prefer data-* or aria-label)
- **Compound Selectors**: Only use parent context if single selector non-unique
- **Hidden Elements**: Skip if display:none or visibility:hidden
- **Iframe Context**: Note if requires iframe-specific handling

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

    with open("formatted_prompt.txt", "w") as f:
        f.write(formatted_prompt)



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