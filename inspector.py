import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
import json

class PCBInspector:
    """Performs automated visual inspection of PCBs using computer vision."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.feature_detector = cv2.SIFT_create()
        self.matcher = cv2.BFMatcher()
        
    def align_images(self, 
                    reference_img: np.ndarray, 
                    test_img: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Align test image with reference image using feature matching.
        
        Args:
            reference_img: Reference (QA) image
            test_img: Test image to align
            
        Returns:
            Tuple of (aligned_image, alignment_info)
        """
        try:
            # Convert images to grayscale for feature detection
            ref_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY)
            test_gray = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
            
            # Detect keypoints and descriptors
            ref_kp, ref_des = self.feature_detector.detectAndCompute(ref_gray, None)
            test_kp, test_des = self.feature_detector.detectAndCompute(test_gray, None)
            
            if ref_des is None or test_des is None:
                self.logger.warning("No features detected in one or both images")
                return test_img, {"error": "No features detected"}
            
            # Match features
            matches = self.matcher.knnMatch(ref_des, test_des, k=2)
            
            # Apply ratio test to filter good matches
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.75 * n.distance:
                        good_matches.append(m)
            
            if len(good_matches) < 4:
                self.logger.warning("Insufficient good matches for alignment")
                return test_img, {"error": "Insufficient matches"}
            
            # Extract matched keypoints
            ref_pts = np.float32([ref_kp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            test_pts = np.float32([test_kp[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            
            # Find homography matrix
            H, mask = cv2.findHomography(test_pts, ref_pts, cv2.RANSAC, 5.0)
            
            if H is None:
                self.logger.warning("Could not compute homography")
                return test_img, {"error": "Homography computation failed"}
            
            # Warp test image to align with reference
            h, w = ref_gray.shape
            aligned_img = cv2.warpPerspective(test_img, H, (w, h))
            
            alignment_info = {
                "matches_count": len(good_matches),
                "homography_matrix": H.tolist(),
                "success": True
            }
            
            return aligned_img, alignment_info
            
        except Exception as e:
            self.logger.error(f"Error during image alignment: {e}")
            return test_img, {"error": str(e)}
    
    def compare_images(self, 
                      reference_img: np.ndarray, 
                      test_img: np.ndarray,
                      threshold: float = 0.95) -> Dict[str, Any]:
        """
        Compare test image with reference image to detect differences.
        
        Args:
            reference_img: Reference (QA) image
            test_img: Test image to compare
            threshold: Similarity threshold (0-1)
            
        Returns:
            Dictionary containing comparison results
        """
        try:
            # Ensure images are the same size
            if reference_img.shape != test_img.shape:
                test_img = cv2.resize(test_img, (reference_img.shape[1], reference_img.shape[0]))
            
            # Convert to grayscale for comparison
            ref_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY)
            test_gray = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
            
            # Calculate structural similarity index
            from skimage.metrics import structural_similarity as ssim
            similarity_score, diff_image = ssim(ref_gray, test_gray, full=True)
            
            # Create difference mask
            diff_mask = (diff_image < threshold).astype(np.uint8) * 255
            
            # Find contours of differences
            contours, _ = cv2.findContours(diff_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by area (remove noise)
            min_area = 100  # Minimum area for significant differences
            significant_contours = [c for c in contours if cv2.contourArea(c) > min_area]
            
            # Create regions of interest for detailed analysis
            regions_of_interest = []
            for i, contour in enumerate(significant_contours):
                x, y, w, h = cv2.boundingRect(contour)
                region = {
                    "id": i,
                    "bbox": [x, y, w, h],
                    "area": cv2.contourArea(contour),
                    "center": [x + w//2, y + h//2]
                }
                regions_of_interest.append(region)
            
            # Calculate overall statistics
            total_pixels = ref_gray.shape[0] * ref_gray.shape[1]
            diff_pixels = np.sum(diff_mask > 0)
            diff_percentage = (diff_pixels / total_pixels) * 100
            
            result = {
                "similarity_score": float(similarity_score),
                "difference_percentage": float(diff_percentage),
                "regions_of_interest": regions_of_interest,
                "total_regions": len(regions_of_interest),
                "threshold": threshold,
                "passed": similarity_score >= threshold
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during image comparison: {e}")
            return {"error": str(e)}
    
    def detect_components(self, image: np.ndarray) -> List[Dict]:
        """
        Detect potential PCB components in the image.
        
        Args:
            image: Input image to analyze
            
        Returns:
            List of detected component regions
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            components = []
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                
                # Filter by area (components should be reasonably sized)
                if 500 < area < 50000:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Calculate aspect ratio to identify component types
                    aspect_ratio = w / h if h > 0 else 0
                    
                    component_type = "unknown"
                    if 0.8 < aspect_ratio < 1.2:
                        component_type = "ic_or_resistor"
                    elif aspect_ratio > 2 or aspect_ratio < 0.5:
                        component_type = "capacitor_or_connector"
                    
                    component = {
                        "id": i,
                        "bbox": [x, y, w, h],
                        "area": area,
                        "aspect_ratio": aspect_ratio,
                        "type": component_type,
                        "center": [x + w//2, y + h//2]
                    }
                    components.append(component)
            
            return components
            
        except Exception as e:
            self.logger.error(f"Error during component detection: {e}")
            return []
    
    def analyze_defects(self, 
                       reference_img: np.ndarray,
                       test_img: np.ndarray,
                       comparison_result: Dict) -> Dict[str, Any]:
        """
        Analyze detected differences to identify specific defects.
        
        Args:
            reference_img: Reference image
            test_img: Test image
            comparison_result: Result from compare_images()
            
        Returns:
            Dictionary containing defect analysis
        """
        try:
            defects = []
            
            # Analyze each region of interest
            for region in comparison_result.get("regions_of_interest", []):
                x, y, w, h = region["bbox"]
                
                # Extract regions from both images
                ref_region = reference_img[y:y+h, x:x+w]
                test_region = test_img[y:y+h, x:x+w]
                
                # Analyze the region
                defect_info = self._analyze_region(ref_region, test_region, region)
                if defect_info:
                    defects.append(defect_info)
            
            return {
                "defects": defects,
                "total_defects": len(defects),
                "severity": self._calculate_severity(defects)
            }
            
        except Exception as e:
            self.logger.error(f"Error during defect analysis: {e}")
            return {"error": str(e)}
    
    def _analyze_region(self, 
                       ref_region: np.ndarray, 
                       test_region: np.ndarray,
                       region_info: Dict) -> Optional[Dict]:
        """Analyze a specific region for defects."""
        try:
            # Calculate region similarity
            ref_gray = cv2.cvtColor(ref_region, cv2.COLOR_BGR2GRAY)
            test_gray = cv2.cvtColor(test_region, cv2.COLOR_BGR2GRAY)
            
            from skimage.metrics import structural_similarity as ssim
            similarity, _ = ssim(ref_gray, test_gray, full=True)
            
            # Determine defect type based on similarity and region characteristics
            defect_type = "unknown"
            if similarity < 0.3:
                defect_type = "missing_component"
            elif similarity < 0.7:
                defect_type = "misaligned_component"
            elif similarity < 0.9:
                defect_type = "soldering_defect"
            
            return {
                "region_id": region_info["id"],
                "bbox": region_info["bbox"],
                "defect_type": defect_type,
                "similarity": float(similarity),
                "confidence": 1.0 - similarity
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing region: {e}")
            return None
    
    def _calculate_severity(self, defects: List[Dict]) -> str:
        """Calculate overall defect severity."""
        if not defects:
            return "none"
        
        # Count defect types
        defect_counts = {}
        for defect in defects:
            defect_type = defect["defect_type"]
            defect_counts[defect_type] = defect_counts.get(defect_type, 0) + 1
        
        # Determine severity based on defect types and counts
        if "missing_component" in defect_counts:
            return "critical"
        elif "misaligned_component" in defect_counts:
            return "high"
        elif "soldering_defect" in defect_counts:
            return "medium"
        else:
            return "low"
    
    def generate_inspection_report(self, 
                                 qa_sample_id: str,
                                 test_image_path: str,
                                 comparison_result: Dict,
                                 defect_analysis: Dict) -> Dict[str, Any]:
        """
        Generate a comprehensive inspection report.
        
        Args:
            qa_sample_id: ID of the QA sample used for comparison
            test_image_path: Path to the test image
            comparison_result: Result from compare_images()
            defect_analysis: Result from analyze_defects()
            
        Returns:
            Complete inspection report
        """
        from datetime import datetime
        
        report = {
            "inspection_id": f"insp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "qa_sample_id": qa_sample_id,
            "test_image_path": test_image_path,
            "timestamp": datetime.now().isoformat(),
            "overall_result": "PASS" if comparison_result.get("passed", False) else "FAIL",
            "similarity_score": comparison_result.get("similarity_score", 0),
            "difference_percentage": comparison_result.get("difference_percentage", 0),
            "defect_summary": defect_analysis,
            "total_regions_analyzed": comparison_result.get("total_regions", 0),
            "recommendations": self._generate_recommendations(defect_analysis)
        }
        
        return report
    
    def _generate_recommendations(self, defect_analysis: Dict) -> List[str]:
        """Generate recommendations based on defect analysis."""
        recommendations = []
        
        if defect_analysis.get("total_defects", 0) == 0:
            recommendations.append("Board passes inspection - no defects detected")
            return recommendations
        
        severity = defect_analysis.get("severity", "unknown")
        
        if severity == "critical":
            recommendations.append("CRITICAL: Missing components detected - board requires rework")
        elif severity == "high":
            recommendations.append("HIGH: Component misalignment detected - manual inspection recommended")
        elif severity == "medium":
            recommendations.append("MEDIUM: Soldering defects detected - review soldering quality")
        elif severity == "low":
            recommendations.append("LOW: Minor defects detected - board may be acceptable")
        
        recommendations.append(f"Total defects found: {defect_analysis.get('total_defects', 0)}")
        
        return recommendations


if __name__ == "__main__":
    # Test inspector functionality
    logging.basicConfig(level=logging.INFO)
    
    inspector = PCBInspector()
    print("PCB Inspector initialized") 