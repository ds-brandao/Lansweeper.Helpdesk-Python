import requests
import os
import functools
import json
import time
from bs4 import BeautifulSoup
import json
import logging


class HelpdeskAPI:
    """A wrapper class for the Lansweeper Helpdesk API.

    This class provides methods to interact with the Lansweeper Helpdesk API,
    including creating, retrieving, and managing tickets, adding notes, and searching users.

    Attributes:
        base_url (str): The base URL of the Lansweeper Helpdesk API.
        api_key (str): The API key for authentication.
        cert_path (str): Path to the SSL certificate file.
        session (requests.Session): A session object for making HTTP requests.
    """

    def __init__(self,
                 base_url=None, 
                 api_key=None, 
                 cert_path=None):
        """Initialize the HelpdeskAPI client.

        Args:
            base_url (str): The base URL of the Lansweeper Helpdesk API.
            api_key (str): The API key for authentication.
            cert_path (str): Path to the SSL certificate file.

        Raises:
            ValueError: If base_url or api_key is not provided.
            FileNotFoundError: If the certificate file is not found.
        """
        
        self.base_url = base_url
        self.api_key = api_key
        self.cert_path = fr"{cert_path}"

        if not self.base_url or not self.api_key:
            raise ValueError("Base URL and API key must be provided.")

        if not os.path.isfile(self.cert_path):
            raise FileNotFoundError(f"Certificate file not found: {self.cert_path}")

        self.session = requests.Session()
        self.session.verify = self.cert_path
    
    # Function to pretty-print JSON response
    def pretty_print_response(self, response):
        """Pretty print the API response in a formatted JSON structure.

        Args:
            response (dict): The API response to format and print.
        """
        if response:
            print(json.dumps(response, indent=4, sort_keys=True))
        else:
            print("No response or an error occurred.")

    def make_request(self, action, method='GET', params=None, data=None, files=None):
        """Make an HTTP request to the Lansweeper Helpdesk API.

        Args:
            action (str): The API action to perform.
            method (str, optional): HTTP method to use ('GET' or 'POST'). Defaults to 'GET'.
            params (dict, optional): Query parameters to include. Defaults to None.
            data (dict, optional): Data to send in the request body. Defaults to None.
            files (dict, optional): Files to upload. Defaults to None.

        Returns:
            dict or str: The API response, parsed as JSON if possible, otherwise as raw text.
            None: If the request fails or returns empty response.
        """
        params = params or {}
        data = data or {}
        
        params['Action'] = action
        params['Key'] = self.api_key

        url = self.base_url

        #print(f"Making {method} request to {url} with params: {params} and data: {data}")

        try:
            if method == 'GET':
                response = self.session.get(url, params=params)
            elif method == 'POST':
                response = self.session.post(url, data=params, files=files)
            
            response.raise_for_status()
            print(f"Response Status Code: {response.status_code}")
            
            # Check if the response is empty
            if not response.text:
                print("Empty response received.")
                return None
            
            # Log the raw response text for debugging
            print(f"Raw Response Text: {response.text}")

            # Attempt to parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError:
                print("Response is not in JSON format.")
                return response.text  # Return raw text if not JSON
        except requests.RequestException as e:
            print(f"An error occurred: {e}")
            return None

    def usage_decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except TypeError as e:
                print(f"Incorrect usage of {func.__name__}: {e}")
                print(f"Usage: {func.__doc__}")
                return None
        return wrapper

    @usage_decorator
    def create_ticket(self, subject, description, email):
        """Create a new ticket in the helpdesk system.

        Args:
            subject (str): The subject line of the ticket.
            description (str): Detailed description of the issue or request.
            email (str): Email address of the ticket requester.

        Returns:
            dict: The API response containing the created ticket information.
            None: If the ticket creation fails.

        Example:
            >>> api.create_ticket(
                    subject="Network Issue",
                    description="Unable to connect to internal network",
                    email="user@example.com"
                )
        """
        params = {
            'Subject': subject,
            'Description': description,
            'Email': email,
        }
        response = self.make_request('AddTicket', method='POST', params=params)
        self.pretty_print_response(response)
        return response

    @usage_decorator
    def get_ticket(self, ticket_id):
        """Retrieve details of a specific ticket.

        Args:
            ticket_id (str): The unique identifier of the ticket.

        Returns:
            dict: Ticket information including status, description, and metadata.
                 HTML in description field is automatically converted to plain text.
            None: If the ticket retrieval fails or ticket doesn't exist.

        Example:
            >>> api.get_ticket("12345")
        """
        params = {
            'TicketID': ticket_id,
        }
        response = self.make_request('GetTicket', method='GET', params=params)
        
        if response:
            #print("Raw response:", response)
            if 'Description' in response:
                soup = BeautifulSoup(response['Description'], 'html.parser')
                response['Description'] = soup.get_text()
            self.pretty_print_response(response)
        else:
            print("No response received or response is empty")
        
        return response
    
    @usage_decorator
    def get_ticket_history(self, ticket_id):
        """Retrieve the complete history of a ticket including all notes and updates.

        Args:
            ticket_id (str): The unique identifier of the ticket.

        Returns:
            str: Formatted JSON string containing the ticket's history.
                 Includes all notes with HTML content converted to plain text.
            None: If the history retrieval fails.

        Note:
            This method includes a 1-second delay between requests to prevent API rate limiting.
        """
        params = {
            'TicketID': ticket_id,
        }

        ticket_info = []

        response = self.make_request('GetNotes', method='GET', params=params)
        
        if not response:
            print("No response received or response is empty")
            return None

        # Parse HTML in 'Notes' field if it is not None
        if response.get('Notes') is not None:
            notes = []
            for note in response['Notes']:
                note_str = json.dumps(note)
                soup = BeautifulSoup(note_str, 'html.parser')
                notes.append(soup.get_text())
            response['Notes'] = '\n\n'.join(notes)

            ticket_info.append(response)

        # pause for 1 second
        time.sleep(1)

        # Parse and pretty-print the ticket history
        for ticket in ticket_info:
            if 'Notes' in ticket:
                # Parse the nested JSON string in 'Notes'
                notes = ticket['Notes'].split('\n\n')
                parsed_notes = []
                for note in notes:
                    if note.strip():
                        try:
                            parsed_notes.append(json.loads(note))
                        except json.JSONDecodeError:
                            print(f"Invalid JSON format in note: {note}")
                            parsed_notes.append(note)  # Append raw note if JSON parsing fail
                ticket['Notes'] = parsed_notes

        # Pretty-print the JSON response
        formatted_ticket_info = json.dumps(ticket_info, indent=4)
        return formatted_ticket_info

    @usage_decorator
    def add_note(self, ticket_id, text, email, type) -> dict | None:
        """Add a note to an existing ticket.

        Args:
            ticket_id (str): The unique identifier of the ticket.
            text (str): The content of the note to add.
            email (str): Email address of the note author.
            type (str): Type of note - either 'Public' or 'Internal'.

        Returns:
            dict: The API response confirming note addition.
            None: If adding the note fails.

        Example:
            >>> api.add_note(
                    ticket_id="12345",
                    text="Updated status with customer",
                    email="agent@example.com",
                    type="Public"
                )
        """
        try:
            logging.info(f"Adding note to ticket {ticket_id}")
            logging.info(f"Note text length: {len(text)}")
            logging.info(f"Email: {email}")
            logging.info(f"Note type: {type}")
            
            params = {
                'TicketID': ticket_id,
                'Text': text,
                'Email': email,
                'Type': type
            }
            
            response = self.make_request('AddNote', method='POST', params=params)
            logging.info(f"Raw API response: {response}")
            return response
        except Exception as e:
            logging.error(f"Error in add_note: {str(e)}", exc_info=True)
            return None
    
    @usage_decorator
    def search_ticket(self, state=None, FromUserId=None, AgentId=None, Description=None, Subject=None, Type=None, MaxResults=None, MinDate=None, MaxDate=None):
        """Search for tickets based on various criteria.

        Args:
            state (str, optional): Ticket state ('Open', 'Closed', etc.).
            FromUserId (str, optional): ID of the ticket creator.
            AgentId (str, optional): ID of the assigned agent.
            Description (str, optional): Search text in ticket description.
            Subject (str, optional): Search text in ticket subject.
            Type (str, optional): Ticket type (e.g., 'Hardware Repair', 'Network', etc.).
            MaxResults (int, optional): Maximum number of results to return (default 100).
            MinDate (str, optional): Start date for ticket search (format: YYYY-MM-DD).
            MaxDate (str, optional): End date for ticket search (format: YYYY-MM-DD).

        Returns:
            dict: List of matching ticket IDs and their information.
            None: If the search fails.

        Note:
            If MaxResults is set lower than the actual number of matching tickets,
            the API will return an empty list.

        Example:
            >>> api.search_ticket(
                    state="Open",
                    Type="Hardware Repair",
                    MaxResults=50
                )
        """
        params = {
            'State': state,
            'FromUserId': FromUserId,
            'AgentId': AgentId,
            'Description': Description,
            'Subject': Subject,
            'Type': Type,
            'MaxResults': MaxResults, # if lower than the tickets returned, the api will bitch about it and return an empty list.
            'MinDate': MinDate,
            'MaxDate': MaxDate
        }
        # Remove keys with None values
        params = {k: v for k, v in params.items() if v is not None}
        
        response = self.make_request('SearchTickets', method='GET', params=params)
        self.pretty_print_response(response)
        return response # returns a list of ticketIDs
    
    @usage_decorator
    def get_user(self, email):  
        """Retrieve user information by email address.

        Args:
            email (str): Email address of the user to look up.

        Returns:
            dict: User information including ID and profile details.
            None: If the user is not found or lookup fails.

        Example:
            >>> api.get_user("user@example.com")
        """
        params = {
            'Email': email
        }
        response = self.make_request('SearchUsers', method='GET', params=params)
        self.pretty_print_response(response)
        return response

    @usage_decorator
    def edit_ticket(self, ticket_id, state, type, email):
        """Update an existing ticket's properties.

        Args:
            ticket_id (str): The unique identifier of the ticket to edit.
            state (str): New state for the ticket ('Open', 'Closed', etc.).
            type (str): New type for the ticket (e.g., 'Hardware Repair', 'Network').
            email (str): Email address of the person making the edit.

        Returns:
            dict: The API response confirming ticket updates.
            None: If the ticket update fails.

        Example:
            >>> api.edit_ticket(
                    ticket_id="12345",
                    state="Closed",
                    type="Hardware Repair",
                    email="agent@example.com"
                )
        """
        params = {
            'TicketID': ticket_id,
            'State': state,
            'Type': type,
            'Email': email
        }
        response = self.make_request('EditTicket', method='POST', params=params)
        self.pretty_print_response(response)
        return response
