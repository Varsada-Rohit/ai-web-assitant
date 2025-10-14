import json
import time


base_input = 50

def get_slots_mock():
    """
    Mock response to add slots
    query: Please create a booking slot for onboarding clients on October 13th, 2 hours starting from 10 AM, weekdays only for 2 months

    """
    time.sleep(2)
    yield json.dumps({"content": "Processing query", "type": "point"}) + "\n\n"
    yield json.dumps({"content":  "I can help you add a slot with the following details: Slot title: Onboarding clients, Meeting type: VIDEO, Start date: 13th Oct 2025, End date: 13th DEC 2025, Start time: 10 am, End Time: 12 pm, Slot duration: 2 hours, and all days of the week selected.","type":"answer"}) + "\n\n"
    time.sleep(2)
    yield json.dumps({"content":{"action_items":[{
    "action": "navigate",
    "element_selector": "",
    "value": "/calendar/slot",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
    },], "message": "I will first navigate to the slots page and then add the slot."}, "type": "action_items"}) + "\n\n"
    time.sleep(3)
    yield json.dumps({"content":{"action_items":[{
    "action": "click",
    "element_selector": "button.MuiButton-containedPrimary.ml-1.bg-white",
    "value": "",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
  },], "message": "I see add slot button, I will click on it to add the slot."}, "type": "action_items"}) + "\n\n"
    time.sleep(3)
    yield json.dumps({"content":{"action_items":[{
    "action": "click",
    "element_selector": ".MuiModal-root input[type='checkbox']",
    "value": "",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
  },
  {
    "action": "fill",
    "element_selector": 'input[name="description"]',
    "value": "Onboarding clients",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
  },
  {
    "action": "fill",
    "element_selector": "input[type='tel'][placeholder='MM/DD/YYYY']",
    "value": "10-13-2025",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
  },
  {
    "action": "fill",
    "element_selector": ".MuiGrid-grid-xs-6:nth-of-type(2) input[placeholder='MM/DD/YYYY']",
    "value": "12-13-2025",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
  },
  {
    "action": "fill",
    "element_selector": 'input[type="tel"][placeholder="hh:mm (a|p)m"]',
    "value": "10:00 AM",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
  },
  {
    "action": "fill",
    "element_selector": '.MuiGrid-grid-xs-6:nth-of-type(2) input[placeholder="hh:mm (a|p)m"]', 
    "value": "12:00 PM",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
  },
  {
    "action": "fill",
    "element_selector": 'input[name="meetingType"]',
    "value": "VIDEO",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
  },
  {
    "action": "click",
    "element_selector": 'button[type="submit"]',
    "value": "",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
  },], "message": "I see the form to add the slot, I will fill the form and add the slot."}, "type": "action_items"}) + "\n\n"
    time.sleep(1)
    yield json.dumps({"content": "Successfully added the slot", "type": "answer"}) + "\n\n"


