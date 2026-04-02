from flask import Flask, jsonify, request

from database import get_site_data, get_all_sites

app = Flask(__name__)


@app.route("/", methods=["GET"])
def status():
	"""Main health check endpoint."""
	return jsonify({"status": "ok"})


@app.route("/latest", methods=["GET"])
def latest():
	"""
	Retrieve the latest data for a specific station.
	
	Query Parameters:
		station (str): The station code (e.g., KTFX, KILX)
	
	Returns:
		JSON with the station data, or 400 if station parameter is missing,
		or 404 if the station is not found in the database.
	"""
	station = request.args.get("station")
	
	if not station:
		return jsonify({"error": "Missing 'station' query parameter"}), 400
	
	station = station.upper()  # Normalize to uppercase
	data = get_site_data(station)
	
	if data is None:
		return jsonify({"error": f"Station '{station}' not found"}), 404
	
	return jsonify({station: data})


@app.route("/all", methods=["GET"])
def all_stations():
	"""Retrieve all stations and their latest data."""
	data = get_all_sites()
	if not data:
		return jsonify({"message": "No stations in database"}), 200
	return jsonify(data)


if __name__ == "__main__":
	app.run(debug=True, host="0.0.0.0", port=5000)
