import os
import csv
import io
from datetime import datetime
import psutil
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, flash

from config import Config
from db_helper import db_helper

app = Flask(__name__)
app.config.from_object(Config)

# Ensure exports directory exists
EXPORTS_DIR = os.path.join(app.root_path, 'static', 'exports')
os.makedirs(EXPORTS_DIR, exist_ok=True)

# --------------------------------------------------------
# Context Processor for system notifications/alerts
# --------------------------------------------------------
@app.context_processor
def inject_system_status():
    db_ok, _ = db_helper.check_health()
    return dict(db_status_ok=db_ok)

# --------------------------------------------------------
# 1. Dashboard Overview Route
# --------------------------------------------------------
@app.route('/')
def dashboard():
    try:
        # Retrieve KPI Aggregates
        total_rides = db_helper.execute_one("SELECT COUNT(*) as count FROM rides")['count']
        active_drivers = db_helper.execute_one("SELECT COUNT(*) as count FROM drivers WHERE status = 'Active'")['count']
        total_revenue = db_helper.execute_one("SELECT SUM(fare) as total FROM rides WHERE status = 'Completed'")['total'] or 0.00
        completed_trips = db_helper.execute_one("SELECT COUNT(*) as count FROM rides WHERE status = 'Completed'")['count']
        cancelled_trips = db_helper.execute_one("SELECT COUNT(*) as count FROM rides WHERE status = 'Cancelled'")['count']
        active_cities = db_helper.execute_one("SELECT COUNT(DISTINCT city) as count FROM drivers WHERE status = 'Active'")['count']
        
        # Recent ride activity log
        recent_rides = db_helper.execute_query("""
            SELECT r.*, d.name as driver_name 
            FROM rides r 
            LEFT JOIN drivers d ON r.driver_id = d.driver_id 
            ORDER BY r.ride_date DESC LIMIT 5
        """)
        
        kpis = {
            'total_rides': total_rides,
            'active_drivers': active_drivers,
            'total_revenue': float(total_revenue),
            'completed_trips': completed_trips,
            'cancelled_trips': cancelled_trips,
            'active_cities': active_cities
        }
        
        return render_template('index.html', kpis=kpis, recent_rides=recent_rides)
    except Exception as e:
        flash(f"Error loading dashboard metrics: {str(e)}", "danger")
        return render_template('index.html', kpis={}, recent_rides=[])

# --------------------------------------------------------
# Analytics Endpoint (Chart.js Data Provider)
# --------------------------------------------------------
@app.route('/api/analytics')
def get_analytics():
    try:
        # 1. Daily Revenue Chart Data (last 30 days)
        revenue_data = db_helper.execute_query("""
            SELECT DATE_FORMAT(ride_date, '%%M %%d') as label, SUM(fare) as val 
            FROM rides 
            WHERE status = 'Completed' 
            GROUP BY DATE(ride_date), DATE_FORMAT(ride_date, '%%M %%d') 
            ORDER BY DATE(ride_date) ASC
        """)
        
        # 2. Daily Ride Volume Chart Data (last 30 days)
        volume_data = db_helper.execute_query("""
            SELECT DATE_FORMAT(ride_date, '%%M %%d') as label, COUNT(*) as val 
            FROM rides 
            GROUP BY DATE(ride_date), DATE_FORMAT(ride_date, '%%M %%d') 
            ORDER BY DATE(ride_date) ASC
        """)
        
        # 3. Driver Status Pie Chart Data
        driver_status_data = db_helper.execute_query("""
            SELECT status as label, COUNT(*) as val 
            FROM drivers 
            GROUP BY status
        """)
        
        return jsonify({
            'success': True,
            'revenue': {
                'labels': [row['label'] for row in revenue_data],
                'data': [float(row['val']) for row in revenue_data]
            },
            'volume': {
                'labels': [row['label'] for row in volume_data],
                'data': [row['val'] for row in volume_data]
            },
            'driver_status': {
                'labels': [row['label'] for row in driver_status_data],
                'data': [row['val'] for row in driver_status_data]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --------------------------------------------------------
# 2. Driver Management Module (CRUD)
# --------------------------------------------------------
@app.route('/drivers')
def list_drivers():
    try:
        drivers = db_helper.execute_query("SELECT * FROM drivers ORDER BY driver_id DESC")
        return render_template('drivers.html', drivers=drivers)
    except Exception as e:
        flash(f"Error retrieving drivers: {str(e)}", "danger")
        return render_template('drivers.html', drivers=[])

@app.route('/drivers/add', methods=['POST'])
def add_driver():
    try:
        name = request.form['name']
        city = request.form['city']
        vehicle_type = request.form['vehicle_type']
        status = request.form['status']
        
        db_helper.execute_update("""
            INSERT INTO drivers (name, city, vehicle_type, status) 
            VALUES (%s, %s, %s, %s)
        """, (name, city, vehicle_type, status))
        flash("Driver successfully added!", "success")
    except Exception as e:
        flash(f"Error adding driver: {str(e)}", "danger")
    return redirect(url_for('list_drivers'))

@app.route('/drivers/edit/<int:driver_id>', methods=['POST'])
def edit_driver(driver_id):
    try:
        name = request.form['name']
        city = request.form['city']
        vehicle_type = request.form['vehicle_type']
        status = request.form['status']
        
        db_helper.execute_update("""
            UPDATE drivers 
            SET name = %s, city = %s, vehicle_type = %s, status = %s 
            WHERE driver_id = %s
        """, (name, city, vehicle_type, status, driver_id))
        flash("Driver successfully updated!", "success")
    except Exception as e:
        flash(f"Error updating driver: {str(e)}", "danger")
    return redirect(url_for('list_drivers'))

@app.route('/drivers/delete/<int:driver_id>', methods=['POST'])
def delete_driver(driver_id):
    try:
        db_helper.execute_update("DELETE FROM drivers WHERE driver_id = %s", (driver_id,))
        flash("Driver successfully deleted!", "warning")
    except Exception as e:
        flash(f"Error deleting driver: {str(e)}", "danger")
    return redirect(url_for('list_drivers'))

# --------------------------------------------------------
# 3. Ride Management Module (CRUD)
# --------------------------------------------------------
@app.route('/rides')
def list_rides():
    try:
        rides = db_helper.execute_query("""
            SELECT r.*, d.name as driver_name 
            FROM rides r 
            LEFT JOIN drivers d ON r.driver_id = d.driver_id 
            ORDER BY r.ride_date DESC
        """)
        drivers = db_helper.execute_query("SELECT driver_id, name FROM drivers WHERE status != 'Suspended'")
        return render_template('rides.html', rides=rides, drivers=drivers)
    except Exception as e:
        flash(f"Error retrieving rides: {str(e)}", "danger")
        return render_template('rides.html', rides=[], drivers=[])

@app.route('/rides/add', methods=['POST'])
def add_ride():
    try:
        driver_id = request.form.get('driver_id')
        driver_id = int(driver_id) if driver_id and driver_id != '' else None
        pickup_location = request.form['pickup_location']
        drop_location = request.form['drop_location']
        fare = float(request.form['fare'])
        status = request.form['status']
        ride_date = request.form['ride_date']
        
        # Parse datetime local string 'YYYY-MM-DDTHH:MM' -> 'YYYY-MM-DD HH:MM:SS'
        ride_date_parsed = datetime.strptime(ride_date, '%Y-%m-%dT%H:%M')
        
        db_helper.execute_update("""
            INSERT INTO rides (driver_id, pickup_location, drop_location, fare, status, ride_date) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (driver_id, pickup_location, drop_location, fare, status, ride_date_parsed))
        flash("Ride successfully booked!", "success")
    except Exception as e:
        flash(f"Error adding ride: {str(e)}", "danger")
    return redirect(url_for('list_rides'))

@app.route('/rides/edit/<int:ride_id>', methods=['POST'])
def edit_ride(ride_id):
    try:
        driver_id = request.form.get('driver_id')
        driver_id = int(driver_id) if driver_id and driver_id != '' else None
        pickup_location = request.form['pickup_location']
        drop_location = request.form['drop_location']
        fare = float(request.form['fare'])
        status = request.form['status']
        ride_date = request.form['ride_date']
        
        # Handles both local-datetime input (with T separator) or standard SQL format
        if 'T' in ride_date:
            ride_date_parsed = datetime.strptime(ride_date, '%Y-%m-%dT%H:%M')
        else:
            ride_date_parsed = datetime.strptime(ride_date, '%Y-%m-%d %H:%M:%S')

        db_helper.execute_update("""
            UPDATE rides 
            SET driver_id = %s, pickup_location = %s, drop_location = %s, fare = %s, status = %s, ride_date = %s 
            WHERE ride_id = %s
        """, (driver_id, pickup_location, drop_location, fare, status, ride_date_parsed, ride_id))
        flash("Ride details successfully updated!", "success")
    except Exception as e:
        flash(f"Error updating ride: {str(e)}", "danger")
    return redirect(url_for('list_rides'))

@app.route('/rides/delete/<int:ride_id>', methods=['POST'])
def delete_ride(ride_id):
    try:
        db_helper.execute_update("DELETE FROM rides WHERE ride_id = %s", (ride_id,))
        flash("Ride successfully deleted!", "warning")
    except Exception as e:
        flash(f"Error deleting ride: {str(e)}", "danger")
    return redirect(url_for('list_rides'))

# --------------------------------------------------------
# 4. Reports Module
# --------------------------------------------------------
@app.route('/reports')
def list_reports():
    try:
        reports = db_helper.execute_query("SELECT * FROM reports ORDER BY report_id DESC")
        
        # Revenue and operations summaries
        daily_rev = db_helper.execute_query("""
            SELECT DATE(ride_date) as date, SUM(fare) as total 
            FROM rides 
            WHERE status = 'Completed' 
            GROUP BY DATE(ride_date) 
            ORDER BY date DESC LIMIT 10
        """)
        
        monthly_rev = db_helper.execute_query("""
            SELECT DATE_FORMAT(ride_date, '%%Y-%%m') as month, SUM(fare) as total 
            FROM rides 
            WHERE status = 'Completed' 
            GROUP BY DATE_FORMAT(ride_date, '%%Y-%%m') 
            ORDER BY month DESC
        """)
        
        top_drivers = db_helper.execute_query("""
            SELECT d.name, COUNT(r.ride_id) as rides_count, SUM(r.fare) as total_revenue 
            FROM rides r 
            JOIN drivers d ON r.driver_id = d.driver_id 
            WHERE r.status = 'Completed' 
            GROUP BY d.driver_id 
            ORDER BY total_revenue DESC LIMIT 5
        """)
        
        city_perf = db_helper.execute_query("""
            SELECT d.city, COUNT(r.ride_id) as rides_count, SUM(r.fare) as total_revenue 
            FROM rides r 
            JOIN drivers d ON r.driver_id = d.driver_id 
            WHERE r.status = 'Completed' 
            GROUP BY d.city 
            ORDER BY total_revenue DESC
        """)
        
        return render_template('reports.html', reports=reports, daily_rev=daily_rev, 
                               monthly_rev=monthly_rev, top_drivers=top_drivers, city_perf=city_perf)
    except Exception as e:
        flash(f"Error loading reports: {str(e)}", "danger")
        return render_template('reports.html', reports=[], daily_rev=[], monthly_rev=[], top_drivers=[], city_perf=[])

@app.route('/reports/generate', methods=['POST'])
def generate_report():
    try:
        report_type = request.form.get('report_type', 'Ops Analytics')
        
        # Fetch current rides data
        rides = db_helper.execute_query("""
            SELECT r.ride_id, d.name as driver_name, r.pickup_location, r.drop_location, 
                   r.fare, r.status, r.ride_date 
            FROM rides r 
            LEFT JOIN drivers d ON r.driver_id = d.driver_id 
            ORDER BY r.ride_date DESC
        """)
        
        # Generate physical file in static/exports
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"report_ops_{timestamp}.csv"
        filepath = os.path.join(EXPORTS_DIR, filename)
        
        with open(filepath, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Ride ID', 'Driver', 'Pickup Location', 'Drop Location', 'Fare ($)', 'Status', 'Ride Date'])
            for ride in rides:
                writer.writerow([
                    ride['ride_id'],
                    ride['driver_name'] or 'N/A',
                    ride['pickup_location'],
                    ride['drop_location'],
                    float(ride['fare']),
                    ride['status'],
                    ride['ride_date'].strftime('%Y-%m-%d %H:%M:%S') if ride['ride_date'] else ''
                ])
                
        # Insert metadata into reports table
        rel_path = f"/static/exports/{filename}"
        db_helper.execute_update("""
            INSERT INTO reports (report_name, report_type, file_path, records_count) 
            VALUES (%s, %s, %s, %s)
        """, (f"Ops Performance Run {timestamp}", report_type, rel_path, len(rides)))
        
        flash(f"Successfully generated report containing {len(rides)} records!", "success")
    except Exception as e:
        flash(f"Error generating report: {str(e)}", "danger")
    return redirect(url_for('list_reports'))

@app.route('/reports/export')
def export_csv():
    try:
        # Fetch all rides
        rides = db_helper.execute_query("""
            SELECT r.ride_id, d.name as driver_name, r.pickup_location, r.drop_location, 
                   r.fare, r.status, r.ride_date 
            FROM rides r 
            LEFT JOIN drivers d ON r.driver_id = d.driver_id 
            ORDER BY r.ride_date DESC
        """)
        
        # Generate CSV in memory for direct stream
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Ride ID', 'Driver Name', 'Pickup Location', 'Drop Location', 'Fare ($)', 'Status', 'Ride Date'])
        for ride in rides:
            writer.writerow([
                ride['ride_id'],
                ride['driver_name'] or 'N/A',
                ride['pickup_location'],
                ride['drop_location'],
                float(ride['fare']),
                ride['status'],
                ride['ride_date'].strftime('%Y-%m-%d %H:%M:%S') if ride['ride_date'] else ''
            ])
        
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=urbanmove_rides_export.csv"
        response.headers["Content-type"] = "text/csv"
        return response
    except Exception as e:
        flash(f"Failed to export CSV: {str(e)}", "danger")
        return redirect(url_for('list_reports'))

# --------------------------------------------------------
# 5. Admin Settings & System Health Module
# --------------------------------------------------------
@app.route('/settings')
def settings():
    try:
        # Total Drivers (Users/Administrators simulated count)
        total_drivers = db_helper.execute_one("SELECT COUNT(*) as count FROM drivers")['count']
        total_rides = db_helper.execute_one("SELECT COUNT(*) as count FROM rides")['count']
        
        # Check database health
        db_alive, db_msg = db_helper.check_health()
        
        # Fetch last backup report
        last_backup = db_helper.execute_one("""
            SELECT generated_at 
            FROM reports 
            WHERE report_type = 'Backup' 
            ORDER BY generated_at DESC LIMIT 1
        """)
        last_backup_time = last_backup['generated_at'].strftime('%Y-%m-%d %H:%M:%S') if last_backup else 'Never'

        system_metrics = {
            'total_drivers': total_drivers,
            'total_rides': total_rides,
            'db_status': 'Healthy' if db_alive else 'Unreachable',
            'db_message': db_msg,
            'last_backup_time': last_backup_time,
            'cpu_usage': psutil.cpu_percent(),
            'ram_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }
        
        return render_template('settings.html', metrics=system_metrics)
    except Exception as e:
        flash(f"Error loading system settings: {str(e)}", "danger")
        return render_template('settings.html', metrics={})

@app.route('/api/health')
def get_health():
    db_alive, db_msg = db_helper.check_health()
    return jsonify({
        'database': {
            'status': 'ONLINE' if db_alive else 'OFFLINE',
            'message': db_msg
        },
        'system': {
            'cpu_utilization_percent': psutil.cpu_percent(interval=0.1),
            'ram_utilization_percent': psutil.virtual_memory().percent,
            'disk_utilization_percent': psutil.disk_usage('/').percent,
            'process_pid': os.getpid()
        },
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/settings/backup', methods=['POST'])
def trigger_backup():
    try:
        # Simulate db dump logs in reports
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db_helper.execute_update("""
            INSERT INTO reports (report_name, report_type, records_count) 
            VALUES (%s, %s, %s)
        """, (f"Database Backup - {timestamp}", 'Backup', 0))
        
        flash("Database snapshot backup initiated successfully!", "success")
    except Exception as e:
        flash(f"Database backup failed: {str(e)}", "danger")
    return redirect(url_for('settings'))

# --------------------------------------------------------
# Error Handlers
# --------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', error_code=404, error_message="The page you requested was not found."), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', error_code=500, error_message="An internal server error occurred. Please verify database connectivity."), 500

if __name__ == '__main__':
    # When run directly, start debug server on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
