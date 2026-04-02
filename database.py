import json
import os
from pathlib import Path
from typing import Any, Dict

DATABASE_FILE = "database.json"


def load_database() -> Dict[str, Dict[str, Any]]:
	"""Load the database from database.json. Return empty dict if file doesn't exist."""
	if os.path.exists(DATABASE_FILE):
		with open(DATABASE_FILE, "r") as f:
			return json.load(f)
	return {}


def save_database(data: Dict[str, Dict[str, Any]]) -> None:
	"""Save the database to database.json."""
	with open(DATABASE_FILE, "w") as f:
		json.dump(data, f, indent=2)


def update_database(payload: Dict[str, Any]) -> None:
	"""
	Update the database with a new NEXRAD message payload.
	
	Args:
		payload: The parsed message dict with keys like SiteID, Key, VolumeID, etc.
	"""
	site_id = payload.get("SiteID")
	key = payload.get("Key")
	volume_id = payload.get("VolumeID")
	
	if not site_id or not key:
		raise ValueError(f"Missing SiteID or Key in payload: {payload}")
	
	db = load_database()
	
	# Initialize site entry if it doesn't exist
	if site_id not in db:
		db[site_id] = {}
	
	# Update the site's key and latest volume ID
	db[site_id]["key"] = key
	db[site_id]["latest_volume_id"] = volume_id
	
	# Optionally store additional metadata
	db[site_id]["datetime"] = payload.get("DateTime")
	db[site_id]["chunk_id"] = payload.get("ChunkID")
	db[site_id]["chunk_type"] = payload.get("ChunkType")
	db[site_id]["l2_version"] = payload.get("L2Version")
	
	save_database(db)


def get_site_data(site_id: str) -> Dict[str, Any] | None:
	"""Retrieve data for a specific site."""
	db = load_database()
	return db.get(site_id)


def get_all_sites() -> Dict[str, Dict[str, Any]]:
	"""Retrieve all site data."""
	return load_database()


def delete_site(site_id: str) -> None:
	"""Delete a site from the database."""
	db = load_database()
	if site_id in db:
		del db[site_id]
		save_database(db)


def clear_database() -> None:
	"""Clear all data from the database."""
	save_database({})
