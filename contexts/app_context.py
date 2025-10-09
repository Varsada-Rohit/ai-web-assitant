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

"""