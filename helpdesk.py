import requests
import os
import functools
import json
import time
from bs4 import BeautifulSoup
import json
import logging


class HelpdeskAPI:
    def __init__(self,
                 base_url=None, 
                 api_key=None, 
                 cert_path=None):
        
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
        if response:
            print(json.dumps(response, indent=4, sort_keys=True))
        else:
            print("No response or an error occurred.")

    def make_request(self, action, method='GET', params=None, data=None, files=None):
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
        """
        Usage: create_ticket(subject, description, email)
        - subject: The subject of the ticket.
        - description: The description of the ticket.
        - email: The email of the requester.
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
        """
        Usage: get_ticket(ticket_id)
        - ticket_id: The ID of the ticket to retrieve.
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
        """
        Usage: get_ticket_history(ticket_id)
        - ticket_id: The ID of the ticket to retrieve the history of.
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
        """
        Usage: add_note(ticket_id, text, email)
        - ticket_id: The ID of the ticket to add a note to.
        - text: The text of the note.
        - email: The email of the person adding the note.
        - type: The type of note to add. (Public or Internal)
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
        """
        Usage: search_ticket(state=None, FromUserId=None, AgentId=None, Description=None, Subject=None, Type=None, MaxResults=None, MinDate=None, MaxDate=None)
        - state: The state of the ticket. (Open, Closed, etc.)
        - FromUserId: The ID of the user who created the ticket.
        - AgentId: The ID of the agent who is assigned to the ticket.
        - Description: The description of the ticket.
        - Subject: The subject of the ticket.
        - Type: The type of ticket. (Desk Phone, Emails, Fax, General IT Support, Hardware Repair/Replacement, IPhone Project, IT Purchase Request, Network, New Hire/Transfer, Temp local PC admin access. User Account Termination)
        - MaxResults: The maximum number of results to return. (Default is 100)
        - MinDate: The minimum date for ticket search.
        - MaxDate: The maximum date for ticket search.
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
        """
        Usage: get_user(email)
        - Email: The email of the user to retrieve.
        """
        params = {
            'Email': email
        }
        response = self.make_request('SearchUsers', method='GET', params=params)
        self.pretty_print_response(response)
        return response

    @usage_decorator
    def edit_ticket(self, ticket_id, state, type, email):
        """
        Usage: edit_ticket(ticket_id, state, type, email)
        - ticket_id: The ID of the ticket to edit.
        - state: The state of the ticket. (Open, Closed, etc.)
        - type: The type of ticket. (Desk Phone, Emails, Fax, General IT Support, Hardware Repair/Replacement, IPhone Project, IT Purchase Request, Network, New Hire/Transfer, Temp local PC admin access. User Account Termination)
        - email: The email of the person editing the ticket.
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
