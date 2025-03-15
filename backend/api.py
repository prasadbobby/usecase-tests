from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
import json
import logging
import traceback
from werkzeug.utils import secure_filename
import sys

# Import your utility functions from app.py
# Adjust the import as needed
from app import (get_all_projects, get_project, add_project, scan_source_code,
                save_elements, get_elements, generate_pom, add_pom, get_poms,
                get_pom, generate_tests, add_test_case, get_test_cases,
                get_test_case, execute_test, add_execution, get_executions)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('api.log')
    ]
)
logger = logging.getLogger('api')

# Initialize Flask app
api_app = Flask(__name__)

# Configure CORS - allow all origins for testing
CORS(api_app, resources={r"/*": {"origins": "*"}})

# Configure upload folders
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'results')
api_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
api_app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
api_app.config['MAX_CONTENT_LENGTH'] = 256 * 1024 * 1024  # 256MB max upload

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Simple route to test API is working
@api_app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({"status": "API is working"}), 200

@api_app.route('/api/projects', methods=['GET'])
def api_get_projects():
    try:
        logger.info("GET /api/projects called")
        projects = get_all_projects()
        return jsonify(projects)
    except Exception as e:
        logger.error(f"Error in GET /api/projects: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@api_app.route('/api/projects/<project_id>', methods=['GET'])
def api_get_project(project_id):
    try:
        logger.info(f"GET /api/projects/{project_id} called")
        project = get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        return jsonify(project)
    except Exception as e:
        logger.error(f"Error in GET /api/projects/{project_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@api_app.route('/api/projects', methods=['POST'])
def api_create_project():
    try:
        logger.info("POST /api/projects called")
        
        # Log headers and request details for debugging
        logger.debug(f"Request Content-Type: {request.content_type}")
        logger.debug(f"Request Headers: {dict(request.headers)}")
        logger.debug(f"Request Form: {request.form}")
        logger.debug(f"Request Files: {request.files}")
        
        if 'file' not in request.files:
            logger.warning("No file part in request")
            return jsonify({"error": "No file part"}), 400
        
        files = request.files.getlist('file')
        if not files or files[0].filename == '':
            logger.warning("No selected file")
            return jsonify({"error": "No selected file"}), 400
        
        project_id = str(uuid.uuid4())
        project_dir = os.path.join(UPLOAD_FOLDER, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        # Save all files
        file_paths = []
        for file in files:
            filename = secure_filename(file.filename)
            file_path = os.path.join(project_dir, filename)
            file.save(file_path)
            file_paths.append(file_path)
            logger.info(f"Saved file to {file_path}")
        
        # If only one file, use it as source_path
        # If multiple files, use the directory
        if len(file_paths) == 1:
            source_path = file_paths[0]
            source_filename = os.path.basename(file_paths[0])
        else:
            source_path = project_dir
            source_filename = "multiple_files"
        
        # Create project record in database
        name = request.form.get('name', 'Unnamed Project')
        description = request.form.get('description', '')
        
        logger.info(f"Adding project: name={name}, desc={description}, file={source_filename}")
        add_project(
            project_id, 
            name,
            description,
            source_filename,
            source_path
        )
        
        project = get_project(project_id)
        if not project:
            return jsonify({"error": "Failed to create project"}), 500
            
        logger.info(f"Project created successfully: {project_id}")
        return jsonify(project), 201
        
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@api_app.route('/api/projects/<project_id>/scan', methods=['POST'])
def api_scan_project(project_id):
    try:
        logger.info(f"POST /api/projects/{project_id}/scan called")
        project = get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        
        elements = scan_source_code(project["source_path"])
        
        # Store elements in the database
        save_elements(project_id, elements)
        
        return jsonify({"success": True, "elements_count": len(elements)})
    
    except Exception as e:
        logger.error(f"Error scanning project: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@api_app.route('/api/projects/<project_id>/elements', methods=['GET'])
def api_get_elements(project_id):
    try:
        logger.info(f"GET /api/projects/{project_id}/elements called")
        elements = get_elements(project_id)
        return jsonify(elements)
    except Exception as e:
        logger.error(f"Error getting elements: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@api_app.route('/api/projects/<project_id>/pom', methods=['POST'])
def api_generate_pom(project_id):
    try:
        logger.info(f"POST /api/projects/{project_id}/pom called")
        # Check if project exists
        project = get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        
        # Get elements from scan or scan again if not available
        elements = get_elements(project_id)
        if not elements:
            elements = scan_source_code(project["source_path"])
            save_elements(project_id, elements)
        
        # Generate the POM
        pom_data = generate_pom(elements, project_id)
        
        # Create POM record in database
        pom_id = str(uuid.uuid4())
        add_pom(pom_id, project_id, pom_data["file_path"], pom_data["elements"])
        
        return jsonify({"success": True, "pom_id": pom_id})
    
    except Exception as e:
        logger.error(f"Error generating POM: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@api_app.route('/api/projects/<project_id>/poms', methods=['GET'])
def api_get_poms(project_id):
    try:
        logger.info(f"GET /api/projects/{project_id}/poms called")
        poms = get_poms(project_id)
        return jsonify(poms)
    except Exception as e:
        logger.error(f"Error getting POMs: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@api_app.route('/api/projects/<project_id>/tests', methods=['POST'])
def api_generate_tests(project_id):
    try:
        logger.info(f"POST /api/projects/{project_id}/tests called")
        # Check if project exists
        project = get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        
        # Get request data
        request_data = request.get_json()
        logger.debug(f"Request data: {request_data}")
        
        # Get POM ID from request
        pom_id = request_data.get('pom_id') if request_data else None
        
        # Validate POM ID
        pom = None
        if pom_id:
            pom = get_pom(pom_id)
            if not pom or pom["project_id"] != project_id:
                return jsonify({"error": "Invalid POM ID"}), 400
        
        # Fallback to first POM if not specified
        if not pom:
            poms = get_poms(project_id)
            if not poms:
                return jsonify({"error": "No POMs available"}), 400
            pom = poms[0]
            pom_id = pom["id"]
        
        # Generate tests
        test_data = generate_tests(pom, project_id)
        
        # Check if test generation was successful
        if test_data.get("success", False) and test_data.get("script_path"):
            test_id = str(uuid.uuid4())
            
            # Save test case to database
            add_test_case(
                test_id,
                project_id,
                pom_id,
                test_data["name"],
                test_data["script_path"],
                test_data["description"]
            )
            
            return jsonify({"success": True, "test_id": test_id})
        else:
            return jsonify({"success": False, "message": test_data.get("description", "Test generation failed")}), 400
        
    except Exception as e:
        logger.error(f"Error generating tests: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@api_app.route('/api/projects/<project_id>/tests', methods=['GET'])
def api_get_tests(project_id):
    try:
        logger.info(f"GET /api/projects/{project_id}/tests called")
        tests = get_test_cases(project_id)
        return jsonify(tests)
    except Exception as e:
        logger.error(f"Error getting tests: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@api_app.route('/api/tests/<test_id>/code', methods=['GET'])
def api_view_test_code(test_id):
    try:
        logger.info(f"GET /api/tests/{test_id}/code called")
        test_case = get_test_case(test_id)
        if not test_case:
            return jsonify({"error": "Test not found"}), 404
        
        if not os.path.exists(test_case["script_path"]):
            return jsonify({"error": "Test script file not found"}), 404
        
        with open(test_case["script_path"], 'r') as f:
            code_content = f.read()
        
        return jsonify({"code": code_content})
    except Exception as e:
        logger.error(f"Error viewing code: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@api_app.route('/api/projects/<project_id>/tests/<test_id>/execute', methods=['POST'])
def api_execute_test(project_id, test_id):
    try:
        logger.info(f"POST /api/projects/{project_id}/tests/{test_id}/execute called")
        project = get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        
        test_case = get_test_case(test_id)
        if not test_case or test_case["project_id"] != project_id:
            return jsonify({"error": "Test case not found"}), 404
        
        execution_result = execute_test(test_case)
        
        execution_id = str(uuid.uuid4())
        
        # Save execution result to database
        add_execution(
            execution_id,
            project_id,
            test_id,
            execution_result["status"],
            execution_result["result"],
            execution_result["log_path"]
        )
        
        return jsonify({
            "success": True, 
            "execution_id": execution_id,
            "status": execution_result["status"]
        })
        
    except Exception as e:
        logger.error(f"Error executing test: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@api_app.route('/api/projects/<project_id>/executions', methods=['GET'])
def api_get_executions(project_id):
    try:
        logger.info(f"GET /api/projects/{project_id}/executions called")
        executions = get_executions(project_id)
        return jsonify(executions)
    except Exception as e:
        logger.error(f"Error getting executions: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@api_app.route('/api/download/<path:filename>', methods=['GET'])
def api_download_file(filename):
    try:
        logger.info(f"GET /api/download/{filename} called")
        directory = os.path.dirname(filename)
        file = os.path.basename(filename)
        return send_from_directory(directory, file, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    api_app.run(debug=True, host='0.0.0.0', port=5000)