import threading
import time

# Lane counts dictionary (import from final.py or set here as global variables)
lane_counts = {'lane1': 0, 'lane2': 0, 'lane3': 0, 'lane4': 0}

# Priority queue based on lane counts (list of lanes sorted by their vehicle count)
lane_priority = ['lane1', 'lane2', 'lane3', 'lane4']

# Timer for active lane (in seconds)
lane_time = {
    'lane1': 0,
    'lane2': 0,
    'lane3': 0,
    'lane4': 0
}

# Total count for passed vehicles
passed_count = {
    'lane1': 0,
    'lane2': 0,
    'lane3': 0,
    'lane4': 0
}

# Simulate time allocation per lane
lane_time_allocation = {
    'lane1': 12,  # Time in seconds
    'lane2': 12,
    'lane3': 12,
    'lane4': 12
}

# Lane Timer Constants
TIMER_UPDATE_INTERVAL = 1  # Time to wait between updates (in seconds)

# Function to calculate time allocation for active lanes
def calculate_time_allocation():
    total_vehicles = sum(lane_counts.values())  # Total number of vehicles across all lanes
    if total_vehicles == 0:
        return {lane: 0 for lane in lane_counts}  # No vehicles, no time allocated

    time_allocations = {}
    for lane in lane_counts:
        if lane_counts[lane] > 0:  # Only allocate time to lanes with vehicles
            time_allocations[lane] = (lane_counts[lane] / total_vehicles) * 30  # Example: Total time = 30 seconds
        else:
            time_allocations[lane] = 0

    return time_allocations

# Function to update the priority of lanes based on counts
def update_lane_priority():
    global lane_priority
    lane_priority.sort(key=lambda lane: lane_counts[lane], reverse=True)  # Sort lanes by count in descending order

# Function to manage the active lane and handle the time rotation
def manage_lane_timing():
    global lane_time, passed_count, lane_time_allocation

    # Calculate new time allocation for each lane
    lane_time_allocation = calculate_time_allocation()

    # Check the active lane and update timing
    for lane in lane_priority:
        if lane_counts[lane] > passed_count[lane]:
            if lane_time[lane] < lane_time_allocation[lane]:
                lane_time[lane] += TIMER_UPDATE_INTERVAL
            else:
                # Time for the active lane is up, reset it
                passed_count[lane] += lane_time_allocation[lane]  # Add allocated time to passed count
                lane_time[lane] = 0
                break  # Break and move to next active lane
        else:
            continue

# API endpoint to get the current status of lanes
def get_traffic_status():
    global lane_counts, lane_priority, passed_count, lane_time_allocation

    # Update the priority and lane timers
    update_lane_priority()
    manage_lane_timing()

    # Create a dictionary of status to return
    status = {
        "lane_counts": lane_counts,
        "lane_priority": lane_priority,
        "lane_time_allocation": lane_time_allocation,
        "passed_count": passed_count
    }

    return status

# Function to simulate lane counting update (for testing purposes)
def update_lane_counts():
    while True:
        # Simulating vehicle count update every 3 seconds (replace with actual data from final.py)
        for lane in lane_counts:
            lane_counts[lane] += 1  # This could be based on real-time API data or a database query

        time.sleep(3)  # Update every 3 seconds (for simulation)

# Starting the lane count simulation in a separate thread (for testing)
if __name__ == "__main__":
    # Start the lane count simulation in a new thread
    threading.Thread(target=update_lane_counts, daemon=True).start()

    # Run Flask app
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route('/get_traffic_status', methods=['GET'])
    def traffic_status():
        return jsonify(get_traffic_status())

    app.run(debug=True)
