import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

class QAManager:
    """Manages QA sample creation, storage, and retrieval for PCB inspection."""
    
    def __init__(self, qa_samples_dir: str = "qa_samples"):
        self.qa_samples_dir = Path(qa_samples_dir)
        self.qa_samples_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
    def create_qa_sample(self, 
                        board_name: str,
                        front_image_path: str,
                        back_image_path: str,
                        notes: str = "",
                        tags: List[str] = None) -> str:
        """
        Create a new QA sample with front and back images.
        
        Args:
            board_name: Name/identifier for the PCB
            front_image_path: Path to the front image
            back_image_path: Path to the back image
            notes: Additional notes about the board
            tags: List of tags for categorization
            
        Returns:
            Sample ID of the created QA sample
        """
        try:
            # Generate unique sample ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sample_id = f"sample_{timestamp}_{board_name.replace(' ', '_')}"
            
            # Create sample directory
            sample_dir = self.qa_samples_dir / sample_id
            sample_dir.mkdir(exist_ok=True)
            
            # Copy images to sample directory
            front_dest = sample_dir / "front.jpg"
            back_dest = sample_dir / "back.jpg"
            
            shutil.copy2(front_image_path, front_dest)
            shutil.copy2(back_image_path, back_dest)
            
            # Create metadata
            metadata = {
                "sample_id": sample_id,
                "board_name": board_name,
                "created_date": datetime.now().isoformat(),
                "notes": notes,
                "tags": tags or [],
                "image_paths": {
                    "front": str(front_dest),
                    "back": str(back_dest)
                },
                "version": "1.0"
            }
            
            # Save metadata
            metadata_path = sample_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Created QA sample: {sample_id}")
            return sample_id
            
        except Exception as e:
            self.logger.error(f"Failed to create QA sample: {e}")
            raise
    
    def get_qa_sample(self, sample_id: str) -> Optional[Dict]:
        """
        Retrieve QA sample metadata and image paths.
        
        Args:
            sample_id: ID of the QA sample to retrieve
            
        Returns:
            Dictionary containing sample metadata and image paths
        """
        try:
            sample_dir = self.qa_samples_dir / sample_id
            metadata_path = sample_dir / "metadata.json"
            
            if not metadata_path.exists():
                self.logger.warning(f"QA sample not found: {sample_id}")
                return None
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Verify image files exist
            front_path = Path(metadata["image_paths"]["front"])
            back_path = Path(metadata["image_paths"]["back"])
            
            if not front_path.exists() or not back_path.exists():
                self.logger.error(f"Image files missing for sample: {sample_id}")
                return None
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve QA sample {sample_id}: {e}")
            return None
    
    def list_qa_samples(self) -> List[Dict]:
        """
        List all available QA samples.
        
        Returns:
            List of sample metadata dictionaries
        """
        samples = []
        
        try:
            for sample_dir in self.qa_samples_dir.iterdir():
                if sample_dir.is_dir():
                    metadata_path = sample_dir / "metadata.json"
                    if metadata_path.exists():
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        samples.append(metadata)
            
            # Sort by creation date (newest first)
            samples.sort(key=lambda x: x["created_date"], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to list QA samples: {e}")
        
        return samples
    
    def delete_qa_sample(self, sample_id: str) -> bool:
        """
        Delete a QA sample and all its files.
        
        Args:
            sample_id: ID of the QA sample to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            sample_dir = self.qa_samples_dir / sample_id
            
            if not sample_dir.exists():
                self.logger.warning(f"QA sample not found for deletion: {sample_id}")
                return False
            
            shutil.rmtree(sample_dir)
            self.logger.info(f"Deleted QA sample: {sample_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete QA sample {sample_id}: {e}")
            return False
    
    def update_qa_sample(self, 
                        sample_id: str,
                        board_name: Optional[str] = None,
                        notes: Optional[str] = None,
                        tags: Optional[List[str]] = None) -> bool:
        """
        Update metadata for an existing QA sample.
        
        Args:
            sample_id: ID of the QA sample to update
            board_name: New board name (optional)
            notes: New notes (optional)
            tags: New tags (optional)
            
        Returns:
            True if update was successful
        """
        try:
            metadata = self.get_qa_sample(sample_id)
            if not metadata:
                return False
            
            # Update fields if provided
            if board_name is not None:
                metadata["board_name"] = board_name
            if notes is not None:
                metadata["notes"] = notes
            if tags is not None:
                metadata["tags"] = tags
            
            metadata["last_modified"] = datetime.now().isoformat()
            
            # Save updated metadata
            sample_dir = self.qa_samples_dir / sample_id
            metadata_path = sample_dir / "metadata.json"
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Updated QA sample: {sample_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update QA sample {sample_id}: {e}")
            return False
    
    def get_sample_images(self, sample_id: str) -> Optional[Tuple[str, str]]:
        """
        Get the front and back image paths for a QA sample.
        
        Args:
            sample_id: ID of the QA sample
            
        Returns:
            Tuple of (front_image_path, back_image_path) or None if not found
        """
        metadata = self.get_qa_sample(sample_id)
        if not metadata:
            return None
        
        return (
            metadata["image_paths"]["front"],
            metadata["image_paths"]["back"]
        )
    
    def validate_sample(self, sample_id: str) -> bool:
        """
        Validate that a QA sample has all required files.
        
        Args:
            sample_id: ID of the QA sample to validate
            
        Returns:
            True if sample is valid
        """
        try:
            metadata = self.get_qa_sample(sample_id)
            if not metadata:
                return False
            
            # Check if image files exist
            front_path = Path(metadata["image_paths"]["front"])
            back_path = Path(metadata["image_paths"]["back"])
            
            if not front_path.exists() or not back_path.exists():
                return False
            
            # Check if images are readable
            import cv2
            front_img = cv2.imread(str(front_path))
            back_img = cv2.imread(str(back_path))
            
            if front_img is None or back_img is None:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate QA sample {sample_id}: {e}")
            return False


if __name__ == "__main__":
    # Test QA manager functionality
    logging.basicConfig(level=logging.INFO)
    
    qa_manager = QAManager()
    
    # Test creating a sample (requires test images)
    print("QA Manager initialized")
    print("Available samples:", len(qa_manager.list_qa_samples())) 