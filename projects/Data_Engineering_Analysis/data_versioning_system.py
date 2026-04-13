#!/usr/bin/env python3
"""
Data Versioning System
Track and manage versions of datasets or logs over time
"""

import json
import os
import hashlib
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class DataVersioningSystem:
    """Main class for managing dataset versions"""

    def __init__(self, data_dir: str = "versions", metadata_file: str = "version_metadata.json"):
        """Initialize the versioning system"""
        self.data_dir = data_dir
        self.metadata_file = metadata_file
        self.metadata = self._load_metadata()

        # Create versions directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

    def _load_metadata(self) -> Dict[str, Any]:
        """Load version metadata from file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"versions": [], "next_id": 1}
        return {"versions": [], "next_id": 1}

    def _save_metadata(self):
        """Save version metadata to file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def _compute_hash(self, data: List[Dict]) -> str:
        """Compute SHA-256 hash of dataset"""
        # Convert to JSON string with sorted keys for consistency
        data_string = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_string.encode()).hexdigest()

    def _check_duplicate(self, data_hash: str) -> Optional[Dict]:
        """Check if dataset already exists"""
        for version in self.metadata["versions"]:
            if version["hash"] == data_hash:
                return version
        return None

    def _generate_sample_dataset(self) -> List[Dict]:
        """Generate a sample dataset for demonstration"""
        return [
            {"id": 1, "name": "Product A", "price": 99.99, "status": "active"},
            {"id": 2, "name": "Product B", "price": 149.99, "status": "active"},
            {"id": 3, "name": "Product C", "price": 49.99, "status": "inactive"},
        ]

    def create_new_version(self, dataset: Optional[List[Dict]] = None,
                           description: str = "") -> Optional[str]:
        """
        Create a new version of the dataset
        Returns version_id if successful, None otherwise
        """
        # Use sample dataset if none provided
        if dataset is None:
            print("No dataset provided. Using sample dataset.")
            dataset = self._generate_sample_dataset()

        if not dataset:
            print("Error: Cannot create version from empty dataset.")
            return None

        # Compute hash for integrity check
        data_hash = self._compute_hash(dataset)

        # Check for duplicate
        duplicate = self._check_duplicate(data_hash)
        if duplicate:
            print(f"⚠ Duplicate detected! This dataset is identical to {duplicate['version_id']}")
            overwrite = input("Do you want to save it anyway? (y/n): ").lower()
            if overwrite != 'y':
                print("Version creation cancelled.")
                return None

        # Generate version ID
        version_id = f"v{self.metadata['next_id']}"

        # Create version info
        version_info = {
            "version_id": version_id,
            "timestamp": datetime.now().isoformat(),
            "hash": data_hash,
            "description": description,
            "record_count": len(dataset)
        }

        # Save dataset to file
        version_file = os.path.join(self.data_dir, f"{version_id}.json")
        try:
            with open(version_file, 'w') as f:
                json.dump(dataset, f, indent=2)
        except IOError as e:
            print(f"Error saving version file: {e}")
            return None

        # Update metadata
        self.metadata["versions"].append(version_info)
        self.metadata["next_id"] += 1
        self._save_metadata()

        print(f"✓ Version {version_id} created successfully!")
        print(f"  Hash: {data_hash[:16]}...")
        print(f"  Records: {len(dataset)}")
        return version_id

    def list_versions(self) -> List[Dict]:
        """List all available versions"""
        if not self.metadata["versions"]:
            print("No versions found.")
            return []

        print("\n" + "=" * 80)
        print("VERSION HISTORY")
        print("=" * 80)

        for version in self.metadata["versions"]:
            print(f"\n{version['version_id']}:")
            print(f"  Timestamp: {version['timestamp']}")
            print(f"  Hash: {version['hash'][:20]}...")
            print(f"  Records: {version['record_count']}")
            if version.get('description'):
                print(f"  Description: {version['description']}")

        print("=" * 80)
        return self.metadata["versions"]

    def load_version(self, version_id: str) -> Optional[List[Dict]]:
        """Load a specific version from storage"""
        version_file = os.path.join(self.data_dir, f"{version_id}.json")

        if not os.path.exists(version_file):
            print(f"Error: Version {version_id} not found.")
            return None

        try:
            with open(version_file, 'r') as f:
                dataset = json.load(f)

            # Verify integrity
            computed_hash = self._compute_hash(dataset)
            stored_hash = self._get_version_hash(version_id)

            if computed_hash != stored_hash:
                print(f"⚠ WARNING: Integrity check failed for {version_id}!")
                print(f"  Expected: {stored_hash[:16]}...")
                print(f"  Got: {computed_hash[:16]}...")
                return None

            print(f"✓ Loaded {version_id} successfully. Integrity verified.")
            return dataset
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading version: {e}")
            return None

    def _get_version_hash(self, version_id: str) -> Optional[str]:
        """Get the stored hash for a version"""
        for version in self.metadata["versions"]:
            if version["version_id"] == version_id:
                return version["hash"]
        return None

    def compare_versions(self, version1: str, version2: str) -> Dict[str, Any]:
        """
        Compare two versions and return differences
        Returns dict with added, removed, modified records
        """
        data1 = self.load_version(version1)
        data2 = self.load_version(version2)

        if data1 is None or data2 is None:
            return {}

        # Create dictionaries keyed by 'id' field
        dict1 = {str(item.get('id', idx)): item for idx, item in enumerate(data1)}
        dict2 = {str(item.get('id', idx)): item for idx, item in enumerate(data2)}

        keys1 = set(dict1.keys())
        keys2 = set(dict2.keys())

        # Find differences
        added = {k: dict2[k] for k in keys2 - keys1}
        removed = {k: dict1[k] for k in keys1 - keys2}

        # Find modified records (same key but different content)
        modified = {}
        common_keys = keys1 & keys2
        for key in common_keys:
            if dict1[key] != dict2[key]:
                modified[key] = {
                    "old": dict1[key],
                    "new": dict2[key]
                }

        return {
            "version1": version1,
            "version2": version2,
            "added": added,
            "removed": removed,
            "modified": modified,
            "stats": {
                "added_count": len(added),
                "removed_count": len(removed),
                "modified_count": len(modified)
            }
        }

    def display_comparison(self, diff_result: Dict[str, Any]):
        """Display comparison results in a formatted way"""
        if not diff_result:
            return

        print("\n" + "=" * 80)
        print(f"COMPARISON: {diff_result['version1']} vs {diff_result['version2']}")
        print("=" * 80)

        stats = diff_result['stats']
        print(f"\n📊 Statistics:")
        print(f"  Added: {stats['added_count']}")
        print(f"  Removed: {stats['removed_count']}")
        print(f"  Modified: {stats['modified_count']}")

        if diff_result['added']:
            print(f"\n➕ Added Records ({stats['added_count']}):")
            for key, record in list(diff_result['added'].items())[:5]:
                print(f"    ID {key}: {json.dumps(record, indent=2)}")
            if stats['added_count'] > 5:
                print(f"    ... and {stats['added_count'] - 5} more")

        if diff_result['removed']:
            print(f"\n➖ Removed Records ({stats['removed_count']}):")
            for key, record in list(diff_result['removed'].items())[:5]:
                print(f"    ID {key}: {json.dumps(record, indent=2)}")
            if stats['removed_count'] > 5:
                print(f"    ... and {stats['removed_count'] - 5} more")

        if diff_result['modified']:
            print(f"\n📝 Modified Records ({stats['modified_count']}):")
            for key, changes in list(diff_result['modified'].items())[:3]:
                print(f"    ID {key}:")
                print(f"      Old: {changes['old']}")
                print(f"      New: {changes['new']}")
            if stats['modified_count'] > 3:
                print(f"    ... and {stats['modified_count'] - 3} more")

        print("=" * 80)

    def rollback_to_version(self, version_id: str) -> bool:
        """Rollback to a previous version (create new version from old data)"""
        print(f"\n⚠ Rolling back to {version_id}...")

        # Load the target version
        dataset = self.load_version(version_id)
        if dataset is None:
            return False

        # Create new version from this dataset
        description = f"Rollback from current version to {version_id}"
        new_version = self.create_new_version(dataset, description)

        if new_version:
            print(f"✓ Rollback complete! Created {new_version} from {version_id}")
            return True
        else:
            print("✗ Rollback failed.")
            return False

    def export_comparison_report(self, diff_result: Dict[str, Any], filename: str = None):
        """Export comparison results to a JSON report"""
        if not diff_result:
            print("No comparison data to export.")
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comparison_{diff_result['version1']}_{diff_result['version2']}_{timestamp}.json"

        try:
            with open(filename, 'w') as f:
                json.dump(diff_result, f, indent=2, default=str)
            print(f"✓ Comparison report exported to {filename}")
        except IOError as e:
            print(f"Error exporting report: {e}")

    def delete_version(self, version_id: str) -> bool:
        """Delete a specific version"""
        confirm = input(f"⚠ Are you sure you want to delete {version_id}? (yes/no): ")

        if confirm.lower() != 'yes':
            print("Deletion cancelled.")
            return False

        # Delete file
        version_file = os.path.join(self.data_dir, f"{version_id}.json")
        if os.path.exists(version_file):
            os.remove(version_file)

        # Remove from metadata
        self.metadata["versions"] = [v for v in self.metadata["versions"] if v["version_id"] != version_id]
        self._save_metadata()

        print(f"✓ Version {version_id} deleted.")
        return True

    def get_version_by_index(self, index: int) -> Optional[str]:
        """Get version ID by index (1-based)"""
        versions = self.metadata["versions"]
        if 1 <= index <= len(versions):
            return versions[index - 1]["version_id"]
        return None


def interactive_menu():
    """Interactive CLI menu for the versioning system"""
    vs = DataVersioningSystem()

    while True:
        print("\n" + "=" * 50)
        print("   DATA VERSIONING SYSTEM")
        print("=" * 50)
        print("1. Create new version")
        print("2. List all versions")
        print("3. Load and display version")
        print("4. Compare two versions")
        print("5. Rollback to previous version")
        print("6. Export comparison report")
        print("7. Delete version")
        print("8. Create sample dataset")
        print("9. Exit")
        print("=" * 50)

        choice = input("\nEnter your choice (1-9): ").strip()

        if choice == '1':
            print("\n--- Create New Version ---")
            use_custom = input("Do you want to provide custom data? (y/n): ").lower()

            if use_custom == 'y':
                print("Enter data as JSON (e.g., [{\"id\":1,\"name\":\"test\"}]):")
                data_input = input().strip()
                try:
                    dataset = json.loads(data_input)
                    if not isinstance(dataset, list):
                        print("Error: Data must be a list of dictionaries.")
                        continue
                except json.JSONDecodeError:
                    print("Error: Invalid JSON format.")
                    continue
            else:
                dataset = None

            description = input("Enter description (optional): ").strip()
            vs.create_new_version(dataset, description)

        elif choice == '2':
            vs.list_versions()

        elif choice == '3':
            vs.list_versions()
            version_id = input("\nEnter version ID to load (e.g., v1): ").strip()
            data = vs.load_version(version_id)

            if data:
                print(f"\n📄 {version_id} Contents:")
                print(json.dumps(data, indent=2)[:1000])
                if len(json.dumps(data)) > 1000:
                    print("... (truncated)")

        elif choice == '4':
            vs.list_versions()
            v1 = input("\nEnter first version ID: ").strip()
            v2 = input("Enter second version ID: ").strip()

            if v1 and v2:
                diff = vs.compare_versions(v1, v2)
                if diff:
                    vs.display_comparison(diff)

        elif choice == '5':
            vs.list_versions()
            version_id = input("\nEnter version ID to rollback to: ").strip()
            vs.rollback_to_version(version_id)

        elif choice == '6':
            vs.list_versions()
            v1 = input("\nEnter first version ID: ").strip()
            v2 = input("Enter second version ID: ").strip()

            if v1 and v2:
                diff = vs.compare_versions(v1, v2)
                if diff:
                    vs.export_comparison_report(diff)

        elif choice == '7':
            vs.list_versions()
            version_id = input("\nEnter version ID to delete: ").strip()
            vs.delete_version(version_id)

        elif choice == '8':
            print("\n--- Create Sample Dataset ---")
            sample = vs._generate_sample_dataset()
            print("Sample dataset created:")
            print(json.dumps(sample, indent=2))
            vs.create_new_version(sample, "Sample dataset")

        elif choice == '9':
            print("\n👋 Goodbye!")
            break

        else:
            print("Invalid choice. Please enter 1-9.")

        input("\nPress Enter to continue...")


def main():
    """Main entry point"""
    print("🚀 Data Versioning System Starting...")
    print(f"📁 Versions will be stored in 'versions/' directory")
    print(f"📝 Metadata will be stored in 'version_metadata.json'")

    # Create initial sample if no versions exist
    vs = DataVersioningSystem()
    if not vs.metadata["versions"]:
        print("\nNo existing versions found. Creating initial sample version...")
        vs.create_new_version(None, "Initial sample dataset")

    interactive_menu()


if __name__ == "__main__":
    main()