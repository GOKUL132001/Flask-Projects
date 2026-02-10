       Event scheduling and Resource Allocation

A comprehensive Flask-based web application for scheduling events and managing resource allocations with automatic conflict detection.

Features

1. Event Management - Create, edit, and delete events
2. Resource Management - Manage rooms, instructors, equipment
3. Resource Allocation - Allocate resources to events
4. Conflict Detection - Automatic scheduling conflict detection
5. Utilization Reports - Generate resource usage reports

Installation

1. Create a folder: `mkdir event_scheduler && cd event_scheduler`
2. Create virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate` (Windows: `venv\Scripts\activate`)
4. Install: `pip install -r requirements.txt`
5. Run: `python app.py`
6. Visit: `http://127.0.0.1:5000`

 Files Needed

1. app.py - Flask routes & logic
2. models.py - Database models
3. requirements.txt - Python packages
4. templates/ folder with HTML files

 Database

Uses SQLite (events.db) - created automatically on first run

Key Features

* Event Management with datetime validation
* Multi-type resource support (rooms, instructors, equipment)
* Real-time conflict detection
* Resource utilization analytics
* User-friendly web interface
