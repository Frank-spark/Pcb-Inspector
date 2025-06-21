"""
OpenAI API Integration for PCB Inspector
========================================

This module handles communication with OpenAI's GPT-4 Vision API to analyze
PCB images and detect defects, component issues, and provide detailed reports.

Features:
- Image analysis using GPT-4 Vision
- Defect detection and description
- Component identification
- Detailed inspection reports
"""

import os
import base64
import json
import logging
from typing import Dict, List, Optional, Any
import requests
from pathlib import Path

class OpenAIAnalyzer:
    """Handles OpenAI GPT-4 Vision API integration for PCB analysis."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAI analyzer.
        
        Args:
            api_key: OpenAI API key. If not provided, will look for OPENAI_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.logger = logging.getLogger(__name__)
        
        if not self.api_key:
            self.logger.warning("No OpenAI API key provided. Set OPENAI_API_KEY environment variable.")
        else:
            self.logger.info("OpenAI API key configured successfully.")
    
    def encode_image(self, image_path: str) -> Optional[str]:
        """
        Encode an image to base64 for API transmission.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string or None if error
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Error encoding image {image_path}: {e}")
            return None
    
    def analyze_pcb_image(self, 
                         image_path: str, 
                         reference_image_path: Optional[str] = None,
                         analysis_type: str = "general") -> Dict[str, Any]:
        """
        Analyze a PCB image using GPT-4 Vision.
        
        Args:
            image_path: Path to the PCB image to analyze
            reference_image_path: Path to reference image for comparison (optional)
            analysis_type: Type of analysis ("general", "defect", "component", "comparison")
            
        Returns:
            Dictionary containing analysis results
        """
        if not self.api_key:
            return {"error": "No OpenAI API key configured"}
        
        try:
            # Encode the main image
            base64_image = self.encode_image(image_path)
            if not base64_image:
                return {"error": "Failed to encode image"}
            
            # Prepare the message content
            content = [
                {
                    "type": "text",
                    "text": self._get_analysis_prompt(analysis_type)
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
            
            # Add reference image if provided
            if reference_image_path:
                ref_base64 = self.encode_image(reference_image_path)
                if ref_base64:
                    content.append({
                        "type": "text",
                        "text": "This is the reference image for comparison:"
                    })
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{ref_base64}"
                        }
                    })
            
            # Prepare the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            # Make the API request
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            analysis_text = result["choices"][0]["message"]["content"]
            
            # Parse the analysis into structured format
            structured_result = self._parse_analysis_response(analysis_text, analysis_type)
            
            return {
                "success": True,
                "analysis": structured_result,
                "raw_response": analysis_text,
                "usage": result.get("usage", {})
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return {"error": f"API request failed: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _get_analysis_prompt(self, analysis_type: str) -> str:
        """Get the appropriate prompt for the analysis type."""
        if analysis_type == "comparison":
            base_prompt = """
You are a PCB (Printed Circuit Board) inspection expert. You are comparing TWO images: a reference image (the known good board) and a current image (the board being inspected).

CRITICAL: You must compare these two images and identify ANY differences. If the boards are different, you MUST mark it as "fail".

IMPORTANT RULES:
1. If the current board is COMPLETELY DIFFERENT from the reference board, mark as "fail"
2. If components are missing, mark as "fail"
3. If components are in different positions, mark as "fail"
4. If the board layout is different, mark as "fail"
5. Only mark as "pass" if the boards are essentially identical
6. If you cannot determine due to image quality, mark as "needs_review"

Please provide your response in the following JSON format:
{
    "overall_quality": "pass/fail/needs_review",
    "defects_found": [
        {
            "type": "missing_component|misaligned|soldering_defect|different_board|other",
            "location": "description of location",
            "severity": "critical|high|medium|low",
            "description": "detailed description of the defect or difference"
        }
    ],
    "components_identified": [
        {
            "type": "resistor|capacitor|ic|connector|other",
            "location": "description of location",
            "status": "present|missing|misaligned|different"
        }
    ],
    "recommendations": [
        "list of specific recommendations"
    ],
    "confidence_score": 0.95,
    "comparison_notes": "Brief summary of what you compared and why you made your decision"
}
"""
        else:
            base_prompt = """
You are a PCB (Printed Circuit Board) inspection expert. Analyze this PCB image and provide a detailed assessment.

Please provide your response in the following JSON format:
{
    "overall_quality": "pass/fail/needs_review",
    "defects_found": [
        {
            "type": "missing_component|misaligned|soldering_defect|other",
            "location": "description of location",
            "severity": "critical|high|medium|low",
            "description": "detailed description of the defect"
        }
    ],
    "components_identified": [
        {
            "type": "resistor|capacitor|ic|connector|other",
            "location": "description of location",
            "status": "present|missing|misaligned"
        }
    ],
    "recommendations": [
        "list of specific recommendations"
    ],
    "confidence_score": 0.95
}
"""
        
        if analysis_type == "defect":
            base_prompt += "\nFocus specifically on identifying defects, missing components, and quality issues."
        elif analysis_type == "component":
            base_prompt += "\nFocus on identifying and cataloging all components present on the board."
        
        return base_prompt
    
    def _parse_analysis_response(self, response_text: str, analysis_type: str) -> Dict[str, Any]:
        """Parse the GPT response into structured format."""
        try:
            # Try to extract JSON from the response
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                return json.loads(json_str)
            else:
                # Fallback to text parsing
                return {
                    "overall_quality": "needs_review",
                    "defects_found": [],
                    "components_identified": [],
                    "recommendations": [response_text],
                    "confidence_score": 0.5
                }
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse JSON response, using text fallback")
            return {
                "overall_quality": "needs_review",
                "defects_found": [],
                "components_identified": [],
                "recommendations": [response_text],
                "confidence_score": 0.5
            }
    
    def compare_pcb_images(self, 
                          current_image_path: str, 
                          reference_image_path: str) -> Dict[str, Any]:
        """
        Compare two PCB images and identify differences.
        
        Args:
            current_image_path: Path to the current PCB image
            reference_image_path: Path to the reference (QA) image
            
        Returns:
            Dictionary containing comparison results
        """
        return self.analyze_pcb_image(
            image_path=current_image_path,
            reference_image_path=reference_image_path,
            analysis_type="comparison"
        )
    
    def detect_defects(self, image_path: str) -> Dict[str, Any]:
        """
        Detect defects in a PCB image.
        
        Args:
            image_path: Path to the PCB image
            
        Returns:
            Dictionary containing defect analysis
        """
        return self.analyze_pcb_image(
            image_path=image_path,
            analysis_type="defect"
        )
    
    def identify_components(self, image_path: str) -> Dict[str, Any]:
        """
        Identify components in a PCB image.
        
        Args:
            image_path: Path to the PCB image
            
        Returns:
            Dictionary containing component identification
        """
        return self.analyze_pcb_image(
            image_path=image_path,
            analysis_type="component"
        )
    
    def generate_inspection_report(self, 
                                 analysis_results: Dict[str, Any],
                                 board_name: str,
                                 inspection_id: str) -> str:
        """
        Generate a human-readable inspection report.
        
        Args:
            analysis_results: Results from image analysis
            board_name: Name of the inspected board
            inspection_id: Unique inspection identifier
            
        Returns:
            Formatted report string
        """
        if "error" in analysis_results:
            return f"Error during inspection: {analysis_results['error']}"
        
        analysis = analysis_results.get("analysis", {})
        
        report = f"""
PCB Inspection Report
====================
Board: {board_name}
Inspection ID: {inspection_id}
Date: {analysis_results.get('timestamp', 'N/A')}

Overall Quality: {analysis.get('overall_quality', 'Unknown')}
Confidence Score: {analysis.get('confidence_score', 0):.2f}

DEFECTS FOUND:
"""
        
        defects = analysis.get('defects_found', [])
        if defects:
            for i, defect in enumerate(defects, 1):
                report += f"""
{i}. Type: {defect.get('type', 'Unknown')}
   Location: {defect.get('location', 'Unknown')}
   Severity: {defect.get('severity', 'Unknown')}
   Description: {defect.get('description', 'No description')}
"""
        else:
            report += "No defects detected.\n"
        
        report += "\nCOMPONENTS IDENTIFIED:\n"
        components = analysis.get('components_identified', [])
        if components:
            for i, component in enumerate(components, 1):
                report += f"""
{i}. Type: {component.get('type', 'Unknown')}
   Location: {component.get('location', 'Unknown')}
   Status: {component.get('status', 'Unknown')}
"""
        else:
            report += "No components identified.\n"
        
        report += "\nRECOMMENDATIONS:\n"
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec}\n"
        else:
            report += "No specific recommendations.\n"
        
        return report


def setup_openai_api_key():
    """Helper function to guide users in setting up their API key."""
    print("""
OpenAI API Key Setup
===================

To use GPT-4 Vision for PCB analysis, you need an OpenAI API key:

1. Go to https://platform.openai.com/
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Set the environment variable:

   Windows (PowerShell):
   $env:OPENAI_API_KEY="your-api-key-here"

   Windows (Command Prompt):
   set OPENAI_API_KEY=your-api-key-here

   Linux/macOS:
   export OPENAI_API_KEY="your-api-key-here"

6. Restart your application

Note: Keep your API key secure and never commit it to version control.
""")

if __name__ == "__main__":
    # Test the OpenAI integration
    setup_openai_api_key()
    
    analyzer = OpenAIAnalyzer()
    if analyzer.api_key:
        print("OpenAI API key found!")
    else:
        print("No OpenAI API key configured.") 