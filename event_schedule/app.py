from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
from models import db, Event, Resource, EventResourceAllocation

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db.init_app(app)

with app.app_context():
    db.create_all()

def check_conflict(resource_id, start_time, end_time, exclude_event_id=None):
    """Check if a resource has conflicting bookings"""
    query = EventResourceAllocation.query.filter(
        EventResourceAllocation.resource_id == resource_id
    ).join(Event)
    
    if exclude_event_id:
        query = query.filter(Event.event_id != exclude_event_id)
    
    allocations = query.all()
    
    for alloc in allocations:
        event = alloc.event
        # Check for any overlap
        if not (end_time <= event.start_time or start_time >= event.end_time):
            return event
    return None

@app.route('/')
def index():
    events = Event.query.order_by(Event.start_time).limit(5).all()
    resources = Resource.query.all()
    return render_template('index.html', events=events, resources=resources)

# Event Routes
@app.route('/events')
def events():
    all_events = Event.query.order_by(Event.start_time).all()
    return render_template('events.html', events=all_events)

@app.route('/events/add', methods=['GET', 'POST'])
def add_event():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
        
        if start_time >= end_time:
            flash('End time must be after start time!', 'error')
            return redirect(url_for('add_event'))
        
        event = Event(title=title, description=description, 
                     start_time=start_time, end_time=end_time)
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('events'))
    
    return render_template('event_form.html', event=None)

@app.route('/events/edit/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    if request.method == 'POST':
        event.title = request.form['title']
        event.description = request.form.get('description', '')
        event.start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
        event.end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
        
        if event.start_time >= event.end_time:
            flash('End time must be after start time!', 'error')
            return redirect(url_for('edit_event', event_id=event_id))
        
        # Check conflicts for allocated resources
        for alloc in event.allocations:
            conflict = check_conflict(alloc.resource_id, event.start_time, 
                                     event.end_time, event.event_id)
            if conflict:
                flash(f'Conflict: {alloc.resource.resource_name} is booked for "{conflict.title}"', 'error')
                return redirect(url_for('edit_event', event_id=event_id))
        
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('events'))
    
    return render_template('event_form.html', event=event)

@app.route('/events/delete/<int:event_id>')
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted!', 'success')
    return redirect(url_for('events'))

# Resource Routes
@app.route('/resources')
def resources():
    all_resources = Resource.query.all()
    return render_template('resources.html', resources=all_resources)

@app.route('/resources/add', methods=['GET', 'POST'])
def add_resource():
    if request.method == 'POST':
        name = request.form['resource_name']
        rtype = request.form['resource_type']
        resource = Resource(resource_name=name, resource_type=rtype)
        db.session.add(resource)
        db.session.commit()
        flash('Resource added!', 'success')
        return redirect(url_for('resources'))
    return render_template('resource_form.html', resource=None)

@app.route('/resources/edit/<int:resource_id>', methods=['GET', 'POST'])
def edit_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    if request.method == 'POST':
        resource.resource_name = request.form['resource_name']
        resource.resource_type = request.form['resource_type']
        db.session.commit()
        flash('Resource updated!', 'success')
        return redirect(url_for('resources'))
    return render_template('resource_form.html', resource=resource)

@app.route('/resources/delete/<int:resource_id>')
def delete_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    db.session.delete(resource)
    db.session.commit()
    flash('Resource deleted!', 'success')
    return redirect(url_for('resources'))

# Allocation Routes
@app.route('/allocations')
def allocations():
    events = Event.query.order_by(Event.start_time).all()
    resources = Resource.query.all()
    return render_template('allocations.html', events=events, resources=resources)

@app.route('/allocate', methods=['POST'])
def allocate():
    event_id = int(request.form['event_id'])
    resource_id = int(request.form['resource_id'])
    
    event = Event.query.get_or_404(event_id)
    resource = Resource.query.get_or_404(resource_id)
    
    # Check if already allocated
    existing = EventResourceAllocation.query.filter_by(
        event_id=event_id, resource_id=resource_id).first()
    if existing:
        flash('Resource already allocated to this event!', 'error')
        return redirect(url_for('allocations'))
    
    # Check for conflicts
    conflict = check_conflict(resource_id, event.start_time, event.end_time)
    if conflict:
        flash(f'Conflict! {resource.resource_name} is already booked for "{conflict.title}" '
              f'({conflict.start_time.strftime("%Y-%m-%d %H:%M")} - '
              f'{conflict.end_time.strftime("%H:%M")})', 'error')
        return redirect(url_for('conflicts'))
    
    allocation = EventResourceAllocation(event_id=event_id, resource_id=resource_id)
    db.session.add(allocation)
    db.session.commit()
    flash('Resource allocated successfully!', 'success')
    return redirect(url_for('allocations'))

@app.route('/deallocate/<int:allocation_id>')
def deallocate(allocation_id):
    allocation = EventResourceAllocation.query.get_or_404(allocation_id)
    db.session.delete(allocation)
    db.session.commit()
    flash('Resource deallocated!', 'success')
    return redirect(url_for('allocations'))

# Conflict View
@app.route('/conflicts')
def conflicts():
    all_conflicts = []
    resources = Resource.query.all()
    
    for resource in resources:
        allocations = EventResourceAllocation.query.filter_by(
            resource_id=resource.resource_id).join(Event).order_by(Event.start_time).all()
        
        for i, alloc1 in enumerate(allocations):
            for alloc2 in allocations[i+1:]:
                e1, e2 = alloc1.event, alloc2.event
                if not (e1.end_time <= e2.start_time or e1.start_time >= e2.end_time):
                    all_conflicts.append({
                        'resource': resource,
                        'event1': e1,
                        'event2': e2
                    })
    
    return render_template('conflicts.html', conflicts=all_conflicts)

# Report
@app.route('/report', methods=['GET', 'POST'])
def report():
    resources = Resource.query.all()
    report_data = []
    start_date = None
    end_date = None
    
    if request.method == 'POST':
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').replace(
            hour=23, minute=59, second=59)
        
        for resource in resources:
            total_hours = 0
            upcoming = 0
            now = datetime.now()
            
            allocations = EventResourceAllocation.query.filter_by(
                resource_id=resource.resource_id).join(Event).filter(
                Event.start_time >= start_date, Event.end_time <= end_date).all()
            
            for alloc in allocations:
                event = alloc.event
                duration = (event.end_time - event.start_time).total_seconds() / 3600
                total_hours += duration
                if event.start_time > now:
                    upcoming += 1
            
            report_data.append({
                'resource': resource,
                'total_hours': round(total_hours, 2),
                'upcoming': upcoming
            })
    
    return render_template('report.html', report_data=report_data, 
                          start_date=start_date, end_date=end_date)

if __name__ == '__main__':
    app.run(debug=True)

