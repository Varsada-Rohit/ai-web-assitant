# Engage web app context.

web_app_context = """

    ReFrame Engage is a customer engagement solution designed for organizations small and large to connect with their customers or constituents anytime, anywhere, while providing the best customer experience. The solution empowers employees with faster, always-connected features like; an Advanced Appointment Scheduling Studio to configure and accept appointments of any kind with communication tools such as on-demand 2-way text messaging, internet calling, video conference, broadcast messaging, email, notes, document upload, all managed through a customer-friendly Customer Relationship Management system (CRM). The system is designed to promote both in office and remote productivity.

    ### CONTEXT: WEB APP STRUCTURE AND SECTIONS

    The web application is organized into multiple sections and routes.  
    Each route represents a unique page or configuration screen with its own purpose and interactive elements.
    1. APPLICATION STRUCTURE
        Base URL: /calendar/calendar/[module]/[page]
        Home Page: Dashboard (/dashboard/home) - Overview with engagement statistics and communication metrics in widget cards

    2. NAVIGATION routes and their corresponding pages

        Dashboard - Home/overview page : route: /calendar/dashboard/home
        Calendar - Calendar view of appointments : route:/calendar/calendar/home
        Customers - Customer management : route : /calendar/crm/home
        Requests - Request handling : route : /calendar/requests/home
        Engagements - Engagement management : route: /calendar/engagements/home
        Slots - Availability management : route : /calendar/calendar/slot
        Configuration - System settings : route : /calendar/configuration/config/agencyProfile
        Reports - Report access : route : /calendar/reports/home
        Forms - Form management : route : /calendar/formbuilder


    3. TOP HEADER (ALWAYS PRESENT)
        Left to Right:

        Application logo
        User profile dropdown (current user, e.g., "Sonyya T")
        Page title/welcome message
        Engage Talk button (communication feature)
        Help icon (?)
        Online/Offline status indicator
        Settings menu
        Notifications bell (with count badge)


    4. CALENDAR WIDGET (LEFT SIDEBAR)
        Location: Below user profile, above navigation menu
        Features:

        Mini calendar showing current month
        Click dates to filter/navigate
        Month navigation arrows
        Current date highlighted

"""