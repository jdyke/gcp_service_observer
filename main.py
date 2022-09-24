#!/usr/bin/python3

import logging
import re
import os
from google.cloud import service_usage_v1
from google.cloud import resourcemanager_v3
from google.api_core import exceptions
from flask import Flask, render_template, request


# Configure logging format
logging.basicConfig(format='%(levelname)s:%(message)s',
                    level=logging.INFO)

# Setup flask app
app = Flask(__name__, static_folder="static", static_url_path="")


@app.route('/')
def input_page():
    """
    Main landing page
    """

    return render_template("index.html")


@app.route('/', methods=['POST'])
def project_id_input():
    """
    Processes user's input and:
        - Converts to lowercase / strips whitespace
        - Sanitizes for special characters
        - Validates the project exists and user has permissions
        - Captures any filters like enabled/disabled
        - Sets column values and renders table
    """

    # Capture user's project id input
    user_project_id = request.form["projectId"]

    # Convert to lowercase and strip whitespace
    project_id = user_project_id.strip().lower()

    # Check for special characters
    result = input_sanitation(user_project_id)

    if result:
        logging.info("No special characters found.")
    else:
        error = "Do not use special characters."
        return render_template(
            "index.html",
            error=error,
        )

    # Check user's permissions and for the existance of the project
    project_is_valid = validate_project_id(project_id)

    if not project_is_valid:
        error = "Unable to validate project ID. \
            Please check the spelling or your permissions."
        return render_template(
            "index.html",
            error=error,
        )

    # Allow filtering of API endpoint results
    user_filter = request.form["filter"]

    # Get API service data
    project_api = list_api_services(project_id, user_filter)

    # Static table column values
    columns_names = ["Title", "API Endpoint", "Status", "Documentation"]

    # Generate the table
    return render_template(
        "service_table.html",
        project_info=project_api,
        colnames=columns_names,
    )


def input_sanitation(project_id):
    """
    Checks for special characters via a regex
    """

    # special characters
    special_chars = re.compile('[@_!#$%^&*().<>?/\|}{~:]')

    # check string contains special characters or not
    if (special_chars.search(project_id) is None):
        return True
    else:
        return False


def validate_project_id(project_id):
    """
    Validates the user has the required permissions
    and the project ID exists.
    """
    # Create Resource Manager client
    client = resourcemanager_v3.ProjectsClient()

    project_name = f"projects/{project_id}"

    # Initialize request argument(s)
    request = resourcemanager_v3.GetProjectRequest(
        name=project_name,
    )

    # Validate project ID exists and
    # Validate user has permissions for project
    try:
        project_info = client.get_project(request=request)
    except exceptions.PermissionDenied as perm_denied:
        logging.error(perm_denied.message)
        return False

    # Validate the project ID that returns is the
    # same that is passed in
    if project_info.project_id == project_id:
        return True
    else:
        return False


def list_api_services(project_id, user_filter=None):
    """
    Lists the API service endpoints for a given project ID.
    """
    # Create a client
    client = service_usage_v1.ServiceUsageClient()

    # Initialize request argument(s)
    request = service_usage_v1.ListServicesRequest(
    )

    parent = f"projects/{project_id}"
    request = {
        "parent": parent,
        # The allowed filter strings are
        # ``state:ENABLED`` and ``state:DISABLED``.
        "filter": user_filter,
    }

    # Make the request
    try:
        page_result = client.list_services(request=request)
    except exceptions.PermissionDenied as perm_denied:
        logging.error(perm_denied.message)
        error = perm_denied.message
        return render_template(
            "index.html",
            error=error,
        )

    project_data_list = []
    # Handle the response
    for service in page_result:
        # Convert into value thats more human readable
        status = str(service.state).split(".")[1]

        # Create the documentation URL using the project ID and endpoint
        documentation_url = f"https://console.cloud.google.com/apis/library/{service.config.name}?project={project_id}&authuser=1"
        # Create dictionary per API service which equals one row in the table
        project_api = {
            "Title": service.config.title,
            "Name": service.config.name,
            "Status": status,
            "Documentation": documentation_url
        }
        # Add dictionary per API to a list
        project_data_list.append(project_api.copy())

    return project_data_list


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))