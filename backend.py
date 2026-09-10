"""
backend.py - File System Engine & Data Processor
Provides core functionality for recursive directory scanning, SHA-256 hashing,
image metadata processing, inventory exporting, and safe file operations.
"""

import os
import hashlib
import datetime
import csv
import json
import shutil
from PIL import Image, UnidentifiedImageError

# Predefined file category mappings
FILE_CATEGORIES = {
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
    'Documents': ['.pdf', '.docx', '.doc', '.txt', '.xlsx', '.csv', '.pptx'],
    'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg'],
    'Video': ['.mp4', '.mkv', '.mov', '.avi', '.wmv'],
    'Archives': ['.zip', '.tar', '.gz', '.7z', '.rar']
}


def get_file_category(extension: str) -> str:
    """Categorize file extension based on predefined mapping."""
    ext_lower = extension.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext_lower in extensions:
            return category
    return 'Other'


def scan_directory(root_dir: str) -> list[dict]:
    """
    Recursively scans the directory and returns a structured list of file metadata records.
    """
    inventory = []
    
    for root, _, files in os.walk(root_dir):
        for file_name in files:
            full_path = os.path.join(root, file_name)
            ext = os.path.splitext(file_name)[1]
            
            try:
                file_stat = os.stat(full_path)
                size_bytes = file_stat.st_size
                mod_time = datetime.datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                create_time = datetime.datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            except (OSError, PermissionError):
                continue  # Skip files with read permission issues

            inventory.append({
                'name': file_name,
                'path': full_path,
                'extension': ext.lower() if ext else 'None',
                'category': get_file_category(ext),
                'size_bytes': size_bytes,
                'size_mb': round(size_bytes / (1024 * 1024), 2),
                'parent_dir': os.path.basename(root),
                'created_at': create_time,
                'modified_at': mod_time
            })
            
    return inventory


def calculate_sha256(file_path: str, chunk_size: int = 65536) -> str | None:
    """Calculates SHA-256 hash in chunks to prevent memory overload on large files."""
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as stream:
            while chunk := stream.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, PermissionError):
        return None


def find_duplicates(inventory: list[dict]) -> dict[str, list[str]]:
    """
    Identifies duplicate files using a two-pass algorithm:
    1. Group files by exact byte size.
    2. Compute SHA-256 hash only for size-matched groups.
    """
    size_groups: dict[int, list[str]] = {}
    for record in inventory:
        size = record['size_bytes']
        size_groups.setdefault(size, []).append(record['path'])

    duplicates: dict[str, list[str]] = {}
    for size, paths in size_groups.items():
        if len(paths) > 1 and size > 0:  # Skip empty files
            hash_groups: dict[str, list[str]] = {}
            for path in paths:
                file_hash = calculate_sha256(path)
                if file_hash:
                    hash_groups.setdefault(file_hash, []).append(path)
            
            for file_hash, matching_paths in hash_groups.items():
                if len(matching_paths) > 1:
                    duplicates[file_hash] = matching_paths

    return duplicates


def extract_image_metadata(file_path: str) -> dict[str, str]:
    """Extracts resolution and format specifications from image files."""
    try:
        with Image.open(file_path) as img:
            return {
                'dimensions': f"{img.width} x {img.height} px",
                'format': img.format or 'Unknown',
                'color_mode': img.mode
            }
    except (UnidentifiedImageError, OSError):
        return {'dimensions': 'N/A', 'format': 'Unsupported/Corrupted', 'color_mode': 'N/A'}


def export_inventory_csv(inventory: list[dict], output_path: str) -> bool:
    """Exports inventory dataset to CSV format."""
    if not inventory:
        return False
    
    headers = list(inventory[0].keys())
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(inventory)
        return True
    except OSError:
        return False


def export_inventory_json(inventory: list[dict], output_path: str) -> bool:
    """Exports inventory dataset to JSON format."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=4)
        return True
    except OSError:
        return False


def organize_files_safely(inventory: list[dict], target_dir: str, mode: str = 'copy') -> list[str]:
    """
    Organizes files into category folders with non-destructive conflict prevention.
    """
    operation_logs = []
    
    for record in inventory:
        category_folder = os.path.join(target_dir, record['category'])
        os.makedirs(category_folder, exist_ok=True)
        
        destination_path = os.path.join(category_folder, record['name'])
        
        # Handle filename collisions
        if os.path.exists(destination_path):
            base_name, ext = os.path.splitext(record['name'])
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            destination_path = os.path.join(category_folder, f"{base_name}_{timestamp}{ext}")

        try:
            if mode == 'copy':
                shutil.copy2(record['path'], destination_path)
                operation_logs.append(f"[COPIED] {record['name']} -> {record['category']}/")
            elif mode == 'move':
                shutil.move(record['path'], destination_path)
                operation_logs.append(f"[MOVED] {record['name']} -> {record['category']}/")
        except OSError as err:
            operation_logs.append(f"[ERROR] Failed to process {record['name']}: {str(err)}")
            
    return operation_logs