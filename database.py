import json
import os
import tempfile
from threading import RLock
from pathlib import Path
from typing import Any, Dict

DATABASE_FILE = "database.json"
DATABASE_PATH = Path(DATABASE_FILE)
_DB_LOCK = RLock()


def load_database() -> Dict[str, Dict[str, Any]]:
	"""Load the database from database.json. Return empty dict if file doesn't exist."""
	with _DB_LOCK:
		if DATABASE_PATH.exists():
			with DATABASE_PATH.open("r", encoding="utf-8") as f:
				return json.load(f)
		return {}


def save_database(data: Dict[str, Dict[str, Any]]) -> None:
	"""Save the database to database.json."""
	with _DB_LOCK:
		# Write to a temp file and atomically replace the destination to avoid partial reads.
		with tempfile.NamedTemporaryFile(
			"w",
			encoding="utf-8",
			delete=False,
			dir=str(DATABASE_PATH.parent or Path(".")),
		) as tmp:
			json.dump(data, tmp, indent=2)
			tmp.flush()
			os.fsync(tmp.fileno())
			tmp_name = tmp.name

		os.replace(tmp_name, DATABASE_PATH)


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
	
	with _DB_LOCK:
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
	with _DB_LOCK:
		db = load_database()
		if site_id in db:
			del db[site_id]
			save_database(db)


def clear_database() -> None:
	"""Clear all data from the database."""
	save_database({})
