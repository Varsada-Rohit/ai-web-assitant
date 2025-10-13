# Engage web app context.

web_app_context = """

    ReFrame Engage is a customer engagement solution designed for organizations small and large to connect with their customers or constituents anytime, anywhere, while providing the best customer experience. The solution empowers employees with faster, always-connected features like; an Advanced Appointment Scheduling Studio to configure and accept appointments of any kind with communication tools such as on-demand 2-way text messaging, internet calling, video conference, broadcast messaging, email, notes, document upload, all managed through a customer-friendly Customer Relationship Management system (CRM). The system is designed to promote both in office and remote productivity.

  ### CONTEXT: WEB APP STRUCTURE AND SECTIONS

The web application is organized into multiple sections and routes.  
Each route represents a unique page or configuration screen with its own purpose and interactive elements.

Sections:
  - Configuration
    - Route: '/calendar/configuration/config/agencyProfile'
    - Description:
        This is the configuration page for the business profile.
        It includes multiple sub-sections for different configuration aspects.

        Sub-Sections:
          - Agency Profile
              - Route: '/calendar/configuration/config/agencyProfile'
              - Description:
                  This section allows the user to configure the agency profile.
                  The user can upload or change the agency logo, edit the title, and update the agency description.

          - Location
              - Route: '/calendar/configuration/config/location'
              - Description:
                  This section displays the list of business locations.
                  The user can view existing locations and add new ones.
                  When adding a location, the user needs to provide:
                    - Location name  
                    - Address details including zip code, street, city, and state.
                    - Unit is optional.


  - Customers 
      Route : '/calendar/crm/home'
      Page Purpose
      This is a comprehensive customer management interface for managing customers in a {white-label} online appointment scheduling application. 

      Main Interface Components

      Primary Action Buttons (Top Bar)
      1. Search Functionality
      * Element: Search input field with placeholder "Search Customers"
      * Purpose: Find existing customers by searching through customer database
      2. Bulk Upload
      * Element: Button labeled "Bulk Upload"
      * Purpose: Import multiple customers at once (likely via CSV/Excel file)
      3. Filter
      * Element: Button with funnel icon labeled "Filter"
      * Purpose: Filter customers by various criteria including:
          * Flag status
          * Customer type
      4. View Logs
      * Element: Button labeled "View Logs"
      * Purpose: Access activity history and audit trails for customer interactions
      5. Message (Broadcast)
      * Element: Button with megaphone icon labeled "Message"
      * Purpose: Initiate broadcast messaging to selected customers
      * Functionality: Allows mass communication via SMS or email
      6. Add Customer
      * Element: Primary blue button labeled "Add Customer"
      * Purpose: Create new customer records manually
      * Action: Opens customer information form


      Contact column in customer table . 
      Each customer row contains 5 contact possibility:
      1. Phone Icon : call
      2. Video Icon : video
      3. Message Icon : sms
      4. Email Icon : email
      5. Document/Notes Icon : Form


      Three-Dot Menu (Action Columns)
      Located at the end of each row, provides additional options:
      * Edit: Modify customer information
      * Flag: Add/modify customer flag status
      * Delete: Remove customer from system
      * Last Note: View or add last interaction note



      Broadcast Message Interface
      Message Composition Area
      * Title: "New Message"
      * Recipient Info: Shows "1 members selected" with "Change" link
      * Template Section: Access saved message templates
          * Mail tab
          * SMS tab (currently selected)
      Message Options
      * Delivery Method:
          * Radio button: "By Mail"
          * Radio button: "By SMS" (selected)
      * Message Field: Large text area for composing message
      Action Buttons
      * Cancel: Discard message and close
      * Save Template: Save current message as template for reuse
      * Send: Deliver message to selected recipients (with dropdown for scheduling)

      Key Workflows 
      Workflow 1: Add Single Customer
      1. Click "Add Customer" button
      2. Fill required fields (First Name, Last Name, Contact Number, Email)
      3. Optionally complete address and additional details
      4. Click "Create" to save
      Workflow 2: Filter and Select Customers
      1. Click "Filter" button
      2. Set filter criteria (flag, type, location, etc.)
      3. Apply filters
      4. Use checkboxes to select specific customers from results
      Workflow 3: Broadcast Message
      1. Select customers using checkboxes (or use filters)
      2. Click "Message" button
      3. Choose delivery method (SMS/Mail)
      4. Compose or select template
      5. Click "Send" to broadcast
      Workflow 4: Manage Individual Customer
      1. Locate customer in table (search or browse)
      2. Click three-dot menu on customer row
      3. Select action: Edit, Flag, Delete, or Last Note
      4. Complete the selected action
      Workflow 5: Quick Communication
      1. Find customer in table
      2. Click appropriate icon (phone, video, message, email)
      3. Initiate communication through selected channel



"""