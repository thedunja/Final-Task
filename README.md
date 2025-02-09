# Project Dashboard

## General Description:
The **Project Management Dashboard** is a service designed to help users manage projects effectively. It allows users to create, update, share, and delete project information, including details and attached documents. The platform supports file storage, image processing, and seamless integration with cloud-based storage (AWS S3). Additionally, the service offers user authentication and management for secure access.

## Features:
- **User Login/Authentication**: Secure login and user registration.
- **Project Management**: Create, update, and delete project information.
- **Project Details**: Add/update project name, description, and other related information.
- **File Management**: Attach, update, and delete project documents (e.g., DOCX, PDF).
- **Sharing**: Share projects with other users for collaboration.
- **Cloud Storage Integration**: Projects' documents are stored securely in AWS S3.
- **Image Processing**: AWS Lambda functions trigger image processing tasks (e.g., resizing) when a file is uploaded to S3.

## Tech Stack:
- **Backend**: 
  - Python 3.10
  - FastAPI for RESTful APIs
  - PostgreSQL for database storage
  - SQLAlchemy ORM support with PostgreSQL
- **File Storage**: 
  - AWS S3 for storing project documents
- **Image Processing**: 
  - AWS Lambda functions to process images triggered by S3 events
- **Containerization**: 
  - Docker for containerizing the application
- **CI/CD**: 
  - GitHub Actions or Gitlab CI for testing, linting, building, pushing to a registry, and deploying to the cloud on merge requests.

## Docker Setup & Installation

This project uses Docker and Docker Compose to run both the application and the PostgreSQL database in containers.

### Prerequisites
Ensure the following are installed on your machine:

- Docker
- Docker Compose
- Python 3.10 (if running locally without Docker)
- AWS Account (for S3 and Lambda configuration)
- GitHub or Gitlab Account (for CI/CD setup)

### Steps to Build & Run with Docker

1. **Clone the repository**:
    ```bash
    git clone git@github.com:thedunja/Project-Dashboard.git
    cd project-dashboard
    ```

2. **Set up the .env file**:
    Create a `.env` file in the root of the project and define the necessary environment variables (e.g., database credentials, AWS credentials).

3. **Build and start the application using Docker Compose**:
    From the project root, run:
    ```bash
    docker-compose up --build
    ```
    This will:
    - Build the application image defined in `containers/app.Dockerfile`
    - Start both the FastAPI application and the PostgreSQL database containers
    - Expose the FastAPI app on `http://localhost:8000`

### Stopping the containers:
To stop the containers run:
```bash
docker-compose down
```
## Accessing the Application

Once the containers are running, you can access the FastAPI application at the following URL:

- **FastAPI Application**: [http://localhost:8000](http://localhost:8000)

### Swagger UI

The API documentation is available via Swagger UI, which is automatically generated by FastAPI:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Redoc Documentation

Alternatively, you can access the API documentation in a different format through Redoc:

- **Redoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## API Endpoints

### 1. Get User Information
- **Method**: `GET`
- **URL**: `/user/`
- **Description**: Fetches the user information based on the authenticated user.
- **Parameters**: 
  - `user` (Header or Cookie): The authenticated user's details.
- **Response**:
  - **200 OK**: Returns user details if authentication is successful.
  - **401 Unauthorized**: If authentication fails or user not found.
#### Example Request:
```GET /user/
```

### 2. Change User Password
- **Method**: `PUT`
- **URL**: `/user/password`
- **Description**: Changes the authenticated user's password. The user must provide their current password and a new password.
- **Parameters**: 
  - `user` (Header or Cookie): The authenticated user's details.
  - `password` (Body): The current password of the user.
  - `new_password` (Body): The new password the user wants to set.
- **Response**:
  - **204 No Content**: The password was successfully changed.
  - **401 Unauthorized**: Authentication failed or incorrect password provided.
  - **400 Bad Request**: The new password doesn't meet security requirements.
#### Example Request:
```PUT /user/password
   Authorization: Bearer <your_token>
   Content-Type: application/json
```

### 3. Change User Phone Number
- **Method**: `PUT`
- **URL**: `/user/phonenumber/{phone_number}`
- **Description**: Updates the authenticated user's phone number.
- **Parameters**: 
  - `user` (Header or Cookie): The authenticated user's details.
  - `phone_number` (Path): The new phone number.
- **Response**:
  - **204 No Content**: Phone number updated successfully.
  - **401 Unauthorized**: If authentication fails.
#### Example Request:
```PUT /user/phonenumber/1234567890
   Authorization: Bearer <your_token>
```

### 4. Get All Projects
- **Method**: `GET`
- **URL**: `URL: /projects/`
- **Description**: Retrieves all projects associated with the authenticated user.
- **Parameters**:
  - `user` (Header or Cookie): The authenticated user's details.
- **Response**:
  - **200 OK**: Returns a list of projects for the authenticated user.
  - **401 Unauthorized**: If authentication fails or user is not found.
#### Example Request:
```GET /projects/
   Authorization: Bearer <your_token>
```

### 5. Create Project
- **Method**: `POST`
- **URL**: `/projects/`
- **Description**: Creates a new project for the authenticated user.
- **Parameters**:
  - `user` (Header or Cookie): The authenticated user's details.
  - `project_request` (Body): The project details (name and description).
- **Response**:
  - **201 Created**: The project has been successfully created.
  - **401 Unauthorized**: If authentication fails or user is not found.
  - **400 Bad Request**: If project name or description is invalid.
#### Example Request:
```POST /projects/
   Authorization: Bearer <your_token>
   Content-Type: application/json
```

### 6. Get Project Information
- **Method**: `GET`
- **URL**: `/projects/project/{project_id}/info`
- **Description**: Retrieves details for a specific project.
- **Parameters**:
  - `user` (Header or Cookie): The authenticated user's details.
  - `project_id` (Path): The ID of the project to retrieve.
- **Response**:
  - **200 OK**: Returns the project details if found.
  - **401 Unauthorized**: If authentication fails.
  - **404 Not Found**: If the project does not exist or does not belong to the authenticated user.
#### Example Request: 
```GET /projects/project/1/info
   Authorization: Bearer <your_token>
```
### 8. Delete Project
- **Method**: `DELETE`
- **URL**: `/projects/project/{project_id}`
- **Description**: Deletes a specific project.
- **Parameters**:
  - `user` (Header or Cookie): The authenticated user's details.
  - `project_id` (Path): The ID of the project to delete.
- **Response**:
  - **204 No Content**: The project was successfully deleted.
  - **401 Unauthorized**: If authentication fails or user is not found.
  - **404 Not Found**: If the project does not exist or does not belong to the authenticated user.
#### Example Request: 
```DELETE /projects/project/1
   Authorization: Bearer <your_token>
```

### 9. Get Project Documents
- **Method**: `GET`
- **URL**: `URL: /projects/project/{project_id}/documents`
- **Description**: Retrieves all documents associated with a specific project.
- **Parameters**:
  - `user` (Header or Cookie): The authenticated user's details.
  - `project_id` (Path): The ID of the project to retrieve documents for.
- **Response**:
  - **200 OK**: Returns a list of documents for the project.
  - **401 Unauthorized**: If authentication fails.
  - **404 Not Found**: If the project does not exist or does not belong to the authenticated user.
#### Example Request: 
```GET /projects/project/1/documents
   Authorization: Bearer <your_token>
```

### 10. Upload Project Documents
- **Method**: `POST`
- **URL**: `/projects/project/{project_id}/documents`
- **Description**: Uploads a document to a specific project and stores it in AWS S3.
- **Parameters**:
  - `user` (Header or Cookie): The authenticated user's details.
  - `project_id` (Path): The ID of the project to upload the document for.
  - `file` (Form Data): The document file to upload.
  - `s3_request` (Body): Optional request for custom file path and bucket name.
- **Response**:
  - **201 Created**: The document was successfully uploaded.
  - **401 Unauthorized**: If authentication fails.
  - **404 Not Found**: If the project does not exist or does not belong to the authenticated user.
  - **400 Bad Request**: If the file is missing or too large.
#### Example Request: 
```POST /projects/project/1/documents
   Authorization: Bearer <your_token>
   Content-Type: multipart/form-data
```