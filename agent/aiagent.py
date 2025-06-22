import re
from typing import Any, Dict, Optional
from anthropic import Anthropic # Client for interacting with Claude AI
from agent.config import agentSettings # Application configuration
from agent.utils import api_request # Helper for making API calls
import time
from datetime import datetime, timedelta


def parse_rfm_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Parses the raw text response from Claude AI to extract RFM values and priority.
    
    RFM = Recency (days since last order), Frequency (total orders), 
    Monetary (total $ spent), Priority (High/Low)
    
    Uses multiple regex patterns to handle different response formats.
    Returns None if parsing fails.
    """
    try:
        # Clean whitespace from response text
        text = response_text.strip()
        
        # Pattern 1: Standard format with all values in one line
        # Example: "Recency: 15 days, Frequency: 3 orders, Monetary: $1500, Priority: High"
        pattern1 = r'Recency:\s*(\d+)\s*days?,\s*Frequency:\s*(\d+)\s*orders?,\s*Monetary:\s*\$?([0-9,]+\.?\d*),\s*Priority:\s*(High|Low)'
        match1 = re.search(pattern1, text, re.IGNORECASE)
        
        if match1:
            # Extract values from regex groups
            return {
                "recency": int(match1.group(1)), # Convert to integer
                "frequency": int(match1.group(2)),
                "monetary": float(match1.group(3).replace(',', '')), # Remove commas for float conversion
                "priority": match1.group(4) # Keep as string
            }
        
        # Pattern 2: Values on separate lines or different order
        recency_match = re.search(r'Recency:\s*(\d+)', text, re.IGNORECASE)
        frequency_match = re.search(r'Frequency:\s*(\d+)', text, re.IGNORECASE)
        monetary_match = re.search(r'Monetary:\s*\$?([0-9,]+\.?\d*)', text, re.IGNORECASE)
        priority_match = re.search(r'Priority:\s*(High|Low)', text, re.IGNORECASE)
        
         # Check if we found all required values
        if all([recency_match, frequency_match, monetary_match]):
            return {
                "recency": int(recency_match.group(1)),
                "frequency": int(frequency_match.group(1)),
                "monetary": float(monetary_match.group(1).replace(',', '')),
                "priority": priority_match.group(1) if priority_match else "Unknown"
            }
        
        # Pattern 3: Fallback - extract first three numbers in text
        numbers = re.findall(r'\d+\.?\d*', text.replace(',', '')) # Find all numeric values
        if len(numbers) >= 3: # Need at least three values
            return {
                "recency": int(float(numbers[0])), # First number = recency
                "frequency": int(float(numbers[1])),  # Second = frequency
                "monetary": float(numbers[2]),  # Third = monetary
                "priority": "High" if "high" in text.lower() else "Low"
            }
            
    except Exception as e:
        # Log parsing errors with context
        print(f"Error parsing RFM response: {e}")
        print(f"Response text: {response_text}")
    
    return None  # Return None if all parsing attempts fail

class MCPAgent:
    """Main agent class for customer RFM analysis and follow-up actions"""

    def __init__(self):
        # Initialize Claude client with API key from settings
        self.claude = Anthropic(api_key=agentSettings.CLAUDE_API_KEY)

    def analyze_customer(self, CustomerID: int) -> Dict[str, Any]:
        """
            Analyzes customer order history to calculate RFM scores and priority.
            
            Steps:
            1. Fetch customer orders via API
            2. Generate prompt for Claude AI
            3. Handle API retries and errors
            4. Parse and validate response
            5. Apply business rules for priority
            
            Returns dictionary with analysis results.
        """
        try:
            # Step 1: Get customer order history
            orders = api_request("GET", f"orders/customer/{CustomerID}")

            # Handle customers with no orders
            if not orders:
                return {
                    "status": "No_orders", 
                    "priority": "Low",
                    "message": "Customer has no order history"
                }

            # Get current date for recency calculation
            reference_date = datetime.now().strftime("%Y-%m-%d")
            
            # Step 2: Create AI prompt with clear instructions - HERE I WILL SUGGEST MODIFYING THE PROMPT WITH LESS INFORMATION AND CLARITY, FOR EXAMPLE DON'T SHARE A REFERENCE DATE
            prompt = f"""Analyze the order history for CustomerID {CustomerID}.
                Reference date: {reference_date}
                High-priority criteria: Recency < 30 days AND Frequency >= 3 orders AND Monetary > $5000

                Calculate:
                - Recency: Days between {reference_date} and customer's most recent order
                - Frequency: Total number of orders for this customer  
                - Monetary: Sum of all TotalDue amounts for this customer
                - Priority: High if meets criteria, otherwise Low

                Return EXACTLY in this format:
                Recency: X days, Frequency: Y orders, Monetary: $Z, Priority: High/Low

                Order data: {orders}"""
            
            # Step 3: Call Claude API with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Send prompt to Claude
                    response = self.claude.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=300,  # Limit response length
                        temperature=0.1,   # Low value = less random responses
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    )
                    
                    # Extract text from API response
                    response_text = response.content[0].text
                    # Parse RFM values from response
                    rfm_data = parse_rfm_response(response_text)
                    
                    # Step 4: Validate parsed data
                    if rfm_data and all(key in rfm_data for key in ["recency", "frequency", "monetary"]):
                        
                        # Step 5: Apply business rules to determine priority
                        calculated_priority = self._calculate_priority(rfm_data)
                        
                        # Log discrepancies between AI and business rules 
                        if rfm_data.get("priority", "").lower() != calculated_priority.lower():
                            print(f"Priority discrepancy for Customer {CustomerID}: Claude={rfm_data.get('priority')}, Calculated={calculated_priority}")
                            rfm_data["priority"] = calculated_priority  # Override with correct value
                        
                        # Return successful analysis
                        return {
                            "rfm": rfm_data,
                            "priority": calculated_priority,
                            "status": "success",
                            "message": f"Successfully analyzed customer - Priority: {calculated_priority}",
                            "attempt": attempt + 1  # Track retry count
                        }
                    else:
                        # Handle parsing failures
                        print(f"Attempt {attempt + 1} failed to parse RFM data for Customer {CustomerID}")
                        print(f"Raw response: {response_text}")

                        # On final attempt return error
                        if attempt == max_retries - 1:  # Last attempt
                            return {
                                "status": "parse_error",
                                "priority": "Low",
                                "message": "Failed to parse RFM data after multiple attempts",
                                "raw_response": response_text
                            }
                        
                except Exception as claude_error:
                    # Handle API errors
                    print(f"Claude API error on attempt {attempt + 1}: {str(claude_error)}")
                    if attempt == max_retries - 1:  # Final attempt failed
                        return {
                            "status": "api_error",
                            "priority": "Low", 
                            "message": f"Claude API error after {max_retries} attempts: {str(claude_error)}"
                        }
                    time.sleep(1)  # Wait before retrying
                        
        except Exception as e:
            # Catch-all for unexpected errors
            return {
                "status": "error",
                "priority": "Low",
                "message": f"Unexpected error analyzing customer {CustomerID}: {str(e)}"
            }


    # Custom business rule - Here is where you can override the response from the AI model
    def _calculate_priority(self, rfm_data: Dict[str, Any]) -> str:
        """
            Applies business rules to determine customer priority.
            
            Rules (different from prompt!):
            - Recency < 365 days (1 year)
            - Frequency >= 3 orders
            - Monetary > $5000
            
            Returns 'High' only if ALL conditions are met, otherwise 'Low'
        """
        is_high_priority = (
            rfm_data["recency"] < 365 and 
            rfm_data["frequency"] >= 3 and 
            rfm_data["monetary"] > 5000
        )
        return "High" if is_high_priority else "Low"


    # AI AGENT creates follow-up tasks in sales system via API
    # Add an entry in the Sales.LeadTasks table by invoking a FastAPI endpoint
    def create_task(self, CustomerID: int, task_description: str) -> bool:
        # Prepare task data with 1-week deadline
        task_data = {
            "CustomerID": CustomerID,
            "TaskDescription": task_description,
            "AssignedTo": "SalesRep1",
            "DueDate": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        }
        # POST to tasks endpoint
        response = api_request("POST", "tasks/", task_data)
        return bool(response)  # True if successful


    # AI AGENT updates customer lead status via API
    # Update the LeadStatus for each HIGH PRIORITY customer by calling a FastAPI endpoint
    def update_customer_status(self, CustomerID: int, lead_status: str) -> bool:
        # PUT to customers endpoint
        response = api_request("PUT", f"customers/{CustomerID}/?lead_status={lead_status}", None)
        return bool(response)  # True if successful


    def run(self):
            """Main execution loop for processing customers"""
            # Note: Continuous execution is commented out for testing
#        while True:
            print(f"Running agent at {datetime.now()}")

            # Retrieve all customers from API
            customers = api_request("GET", "customers/")

            total_customers = len(customers)
            processed_count = 0
            high_priority_count = 0
            errors = []

            print(f"Processing {total_customers} customers...")

            # Process each customer
            for customer in customers:
                CustomerID = customer["CustomerID"]
                try:
                    # Step 1: Analyze customer
                    analysis = self.analyze_customer(CustomerID)

                    # Display RFM values if successful
                    if analysis and analysis["status"] == "success" and "rfm" in analysis:
                        rfm_data = analysis["rfm"]
                        print(f"CustomerID: {CustomerID} | R: {rfm_data['recency']} | F: {rfm_data['frequency']} | M: ${rfm_data['monetary']:.2f} | Priority: {analysis['priority']}")

                    # Step 2: Handle high-priority customers
                    if analysis and analysis["priority"] == "High":
                        # Update customer status
                        self.update_customer_status(CustomerID, "High Priority")
                        # Create follow-up task
                        self.create_task(CustomerID, f"Follow up with customer #{CustomerID} about new products")
                        high_priority_count += 1
                    processed_count += 1
                    
                except Exception as e:
                    # Collect errors for batch reporting
                    error_msg = f"Customer {CustomerID}: {str(e)}"
                    errors.append(error_msg)
                    print(f"Error: {error_msg}")

            # Print summary report
            print(f"Completed: {processed_count}/{total_customers} customers")
            print(f"High priority customers found: {high_priority_count}")
            if errors:
                print(f"Errors: {len(errors)}")
                for error in errors[:5]:  # Show first 5 errors
                    print(f"  - {error}")

            print(f"Agent completed at {datetime.now()}")
            print("Agent execution finished. Exiting...")
            # Note: Continuous execution would sleep here
#            time.sleep(agentSettings.AGENT_INTERVAL)  

if __name__ == "__main__":
    # Entry point: Create agent and run
    agent = MCPAgent()
    agent.run()