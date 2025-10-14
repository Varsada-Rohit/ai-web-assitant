import json
import time


def get_reminder_mock():
    """
    Mock response to send mail
    query: Please send the welcome message to Anandh-parasuram via SMS
    """
    time.sleep(2)
    yield json.dumps({"content": "Processing query", "type": "point"}) + "\n\n"
    yield json.dumps({"content": "Hi", "type": "I can help you send the welcome message to the customer with name anandh parasuram via sms"}) + "\n\n"
    time.sleep(3)
    yield json.dumps({"content":{"action_items":[{
    "action": "navigate",
    "element_selector": "",
    "value": "/calendar/crm/home",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
    },], "message": "I will first navigate to the customers page to find the customer"}, "type": "action_items"}) + "\n\n"
    time.sleep(2)
    yield json.dumps({"content":{"action_items":[{
    "action": "click",
    "element_selector": 'input[type="checkbox"][aria-label="select anandh parasuram"]',
    "value": "",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
  },], "message": "I see the customer, I will click check box to select the customer"}, "type": "action_items"}) + "\n\n"
    time.sleep(2)
    yield json.dumps({"content":{"action_items":[{
    "action": "click",
    "element_selector": 'button[aria-label="send email to anandh parasuram"]',
    "value": "",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
  },], "message": "Clicking on the send email button to send the mail"}, "type": "action_items"}) + "\n\n"
    time.sleep(4)
    yield json.dumps({"content":{"action_items":[{
    "action": "click",
    "element_selector": 'input[name="broadcastType"][aria-label="sms"]',
    "value": "",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
  },
  {
    "action": "fill",
    "element_selector": 'textarea[name="smsBody"]',
    "value": "Welcome to the platform Anandh, We are glad to have you on board. You can now book your slots and get started.",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
  },
  
  {
    "action": "click",
    "element_selector": '.loader-button',
    "value": "",
    "description":
      "Click on the 'Slots' icon to navigate to the slots management page.",
  },], "message": "I can see the form to send the sms, I will fill the form and send the sms"}, "type": "action_items"}) + "\n\n"
    time.sleep(1)
    yield json.dumps({"content": "Successfully sent the SMS", "type": "answer"}) + "\n\n"


