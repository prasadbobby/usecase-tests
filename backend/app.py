import os
import uuid
import json
import re
import sqlite3
import logging
import zipfile
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, send_from_directory, g
from werkzeug.utils import secure_filename
from bs4 import BeautifulSoup
import google.generativeai as genai
from typing import List, Dict, Any
import subprocess
import datetime
import traceback
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'results')
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_generator.db')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyCcRxsIv0GyiRl3NtPvr1o8LdfoeDUn_HE')  # Replace with your API key

# Configure Gemini if API key is available
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Test the connection
        model = genai.GenerativeModel('gemini-1.5-flash')
        model.generate_content("Test")
        logger.info("Gemini API configured successfully")
    except Exception as e:
        logger.warning(f"Gemini API configuration failed: {str(e)}")
        # Set to None to clearly indicate it's not working
        GEMINI_API_KEY = None
else:
    logger.warning("Gemini API key not properly configured")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 256 * 1024 * 1024  # 256MB max upload
app.secret_key = os.urandom(24)

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Database setup
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def create_db_tables():
    """Create database tables if they don't exist"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Projects table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            source_file TEXT,
            source_path TEXT,
            created_at TEXT
        )
        ''')
        
        # Elements table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS elements (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            element_data TEXT,
            created_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
        ''')
        
        # POMs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS poms (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            file_path TEXT,
            pom_data TEXT,
            created_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
        ''')
        
        # Test cases table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_cases (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            pom_id TEXT NOT NULL,
            name TEXT,
            script_path TEXT,
            description TEXT,
            created_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (id),
            FOREIGN KEY (pom_id) REFERENCES poms (id)
        )
        ''')
        
        # Test executions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_executions (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            test_id TEXT NOT NULL,
            status TEXT,
            result_data TEXT,
            log_path TEXT,
            executed_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (id),
            FOREIGN KEY (test_id) REFERENCES test_cases (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

# Database helper functions
def add_project(project_id, name, description, source_file, source_path):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO projects (id, name, description, source_file, source_path, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (project_id, name, description, source_file, source_path, created_at)
    )
    conn.commit()
    conn.close()

def get_project(project_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()
    conn.close()
    return dict(project) if project else None

def get_all_projects():
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
        projects = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return projects
    except Exception as e:
        logger.error(f"Error retrieving projects: {str(e)}")
        return []

def save_elements(project_id, elements):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    element_id = str(uuid.uuid4())
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # First delete any existing elements for this project
    cursor.execute("DELETE FROM elements WHERE project_id = ?", (project_id,))
    
    # Then insert new elements
    cursor.execute(
        "INSERT INTO elements (id, project_id, element_data, created_at) VALUES (?, ?, ?, ?)",
        (element_id, project_id, json.dumps(elements), created_at)
    )
    conn.commit()
    conn.close()
    return element_id

def get_elements(project_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT element_data FROM elements WHERE project_id = ?", (project_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return json.loads(result['element_data'])
    return []

def add_pom(pom_id, project_id, file_path, pom_data):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO poms (id, project_id, file_path, pom_data, created_at) VALUES (?, ?, ?, ?, ?)",
        (pom_id, project_id, file_path, json.dumps(pom_data), created_at)
    )
    conn.commit()
    conn.close()

def get_poms(project_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM poms WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
    poms = []
    for row in cursor.fetchall():
        pom = dict(row)
        pom['elements'] = json.loads(pom['pom_data'])
        poms.append(pom)
    conn.close()
    return poms

def get_pom(pom_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM poms WHERE id = ?", (pom_id,))
    pom = cursor.fetchone()
    conn.close()
    if pom:
        result = dict(pom)
        result['elements'] = json.loads(result['pom_data'])
        return result
    return None

def add_test_case(test_id, project_id, pom_id, name, script_path, description):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO test_cases (id, project_id, pom_id, name, script_path, description, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (test_id, project_id, pom_id, name, script_path, description, created_at)
    )
    conn.commit()
    conn.close()

def get_test_cases(project_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_cases WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
    test_cases = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return test_cases

def get_test_case(test_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_cases WHERE id = ?", (test_id,))
    test_case = cursor.fetchone()
    conn.close()
    return dict(test_case) if test_case else None

def add_execution(execution_id, project_id, test_id, status, result_data, log_path):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    executed_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO test_executions (id, project_id, test_id, status, result_data, log_path, executed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (execution_id, project_id, test_id, status, json.dumps(result_data), log_path, executed_at)
    )
    conn.commit()
    conn.close()

def get_executions(project_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_executions WHERE project_id = ? ORDER BY executed_at DESC", (project_id,))
    executions = []
    for row in cursor.fetchall():
        execution = dict(row)
        execution['result'] = json.loads(execution['result_data'])
        executions.append(execution)
    conn.close()
    return executions

# Helper function for escaping strings in code
def escape_string_for_code(s):
    """Escape a string to be used in Python code within single quotes"""
    # Replace backslashes first to avoid double escaping
    s = s.replace('\\', '\\\\')
    # Replace single quotes
    s = s.replace("'", "\\'")
    # Replace double quotes
    s = s.replace('"', '\\"')
    # Replace line breaks with explicit newlines
    s = s.replace('\n', '\\n')
    # Replace tabs
    s = s.replace('\t', '\\t')
    return s

# Code Scanner Functions
def scan_source_code(file_path: str) -> List[Dict[str, Any]]:
    """Scan source code to identify UI elements"""
    elements = []
    
    # Get file extension
    _, ext = os.path.splitext(file_path)
    
    if ext.lower() in ['.html', '.jsx', '.tsx', '.vue', '.js']:
        elements = scan_component_file(file_path)
    elif ext.lower() == '.zip':
        # Extract and scan zip file
        elements = scan_zip_file(file_path)
    elif os.path.isdir(file_path):
        # Scan directory
        for root, _, files in os.walk(file_path):
            for file in files:
                if file.endswith(('.html', '.jsx', '.tsx', '.vue', '.js')):
                    file_elements = scan_component_file(os.path.join(root, file))
                    elements.extend(file_elements)
    
    return elements

def scan_zip_file(zip_path: str) -> List[Dict[str, Any]]:
    """Extract and scan files from a ZIP archive"""
    elements = []
    extract_dir = os.path.join(os.path.dirname(zip_path), "extracted_" + os.path.basename(zip_path).replace('.zip', ''))
    
    try:
        # Create extraction directory
        os.makedirs(extract_dir, exist_ok=True)
        
        # Extract all files
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Scan the extracted directory
        for root, _, files in os.walk(extract_dir):
            for file in files:
                if file.endswith(('.html', '.jsx', '.tsx', '.vue', '.js')):
                    file_elements = scan_component_file(os.path.join(root, file))
                    elements.extend(file_elements)
        
        return elements
    except Exception as e:
        logger.error(f"Error scanning ZIP file {zip_path}: {str(e)}")
        return []
    finally:
        # Clean up extracted files
        try:
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
        except Exception as e:
            logger.error(f"Error cleaning up extraction directory: {str(e)}")

def scan_component_file(file_path: str) -> List[Dict[str, Any]]:
    """Scan a single component file for UI elements"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        elements = []
        file_name = os.path.basename(file_path)
        
        # HTML files
        if file_path.endswith('.html'):
            soup = BeautifulSoup(content, 'html.parser')
            elements = extract_elements_from_html(soup, file_name)
        
        # JavaScript/React/Vue files
        elif file_path.endswith(('.jsx', '.tsx', '.vue', '.js')):
            # Extract HTML-like parts from JSX/TSX/Vue/JS
            html_pattern = r'<([a-zA-Z][a-zA-Z0-9]*)[^>]*>(.*?)</\1>'
            matches = re.findall(html_pattern, content, re.DOTALL)
            
            for tag, inner_content in matches:
                soup = BeautifulSoup(f"<{tag}>{inner_content}</{tag}>", 'html.parser')
                file_elements = extract_elements_from_html(soup, file_name)
                elements.extend(file_elements)
            
            # Also look for React component definitions
            react_component_pattern = r'(?:class|function)\s+([A-Z][a-zA-Z0-9]*)\s*(?:extends\s+React\.Component\s*)?{(.*?)}'
            react_matches = re.findall(react_component_pattern, content, re.DOTALL)
            
            for component_name, component_body in react_matches:
                # Look for elements in render method or return statement
                render_pattern = r'render\s*\(\s*\)\s*{(.*?)return\s*(.*?);?\s*}'
                render_matches = re.findall(render_pattern, component_body, re.DOTALL)
                
                for _, jsx in render_matches:
                    # Clean JSX before parsing
                    jsx = re.sub(r'{[^}]*}', '', jsx)  # Remove JS expressions
                    soup = BeautifulSoup(jsx, 'html.parser')
                    file_elements = extract_elements_from_html(soup, file_name)
                    elements.extend(file_elements)
        
        return elements
    except Exception as e:
        logger.error(f"Error scanning file {file_path}: {str(e)}")
        return []

def extract_elements_from_html(soup, file_name: str) -> List[Dict[str, Any]]:
    """Extract UI elements from BeautifulSoup parsed HTML with enhanced detection"""
    elements = []
    
    # Find all relevant UI elements
    # Extended to include more element types
    interactive_elements = soup.find_all([
        'button', 'a', 'input', 'select', 'textarea', 'form', 
        'div', 'span', 'label', 'img', 'table', 'tr', 'td',
        'ul', 'li', 'nav', 'header', 'footer', 'section'
    ])
    
    for elem in interactive_elements:
        # Skip elements without attributes or text, unless they're structural elements
        if not elem.attrs and not elem.text.strip() and elem.name not in ['div', 'section', 'nav', 'header', 'footer']:
            continue
        
        element_id = str(uuid.uuid4())
        element_type = elem.name
        
        # Determine best selector with enhanced priority
        selector = ""
        selector_type = ""
        
        # Priority 1: id attribute
        if elem.get('id'):
            selector = f"#{elem.get('id')}"
            selector_type = "id"
        
        # Priority 2: data-testid, data-cy, data-test attributes (common in testing frameworks)
        elif elem.get('data-testid'):
            selector = f"[data-testid='{elem.get('data-testid')}']"
            selector_type = "data-testid"
        elif elem.get('data-cy'):
            selector = f"[data-cy='{elem.get('data-cy')}']"
            selector_type = "data-cy"
        elif elem.get('data-test'):
            selector = f"[data-test='{elem.get('data-test')}']"
            selector_type = "data-test"
        
        # Priority 3: name attribute
        elif elem.get('name'):
            selector = f"[name='{elem.get('name')}']"
            selector_type = "name"
        
        # Priority 4: class attribute
        elif elem.get('class'):
            classes = ' '.join(elem.get('class'))
            selector = f".{'.'.join(elem.get('class'))}"
            selector_type = "class"
        
        # Priority 5: role attribute (accessibility)
        elif elem.get('role'):
            selector = f"[role='{elem.get('role')}']"
            selector_type = "role"
        
        # Priority 6: tag + text content (if text is short enough)
        elif elem.text and len(elem.text.strip()) < 50:
            text = elem.text.strip()
            selector = f"//{element_type}[contains(text(), '{text}')]"
            selector_type = "xpath"
        
        # Priority 7: fallback to advanced XPath
        else:
            selector = generate_xpath(elem)
            selector_type = "xpath"
        
        # Determine element purpose/functionality based on type and attributes
        element_purpose = determine_element_purpose(elem)
        
        # Create element object with enhanced metadata
        element = {
            "id": element_id,
            "name": determine_element_name(elem, file_name),
            "type": element_type,
            "purpose": element_purpose,
            "selector": selector,
            "selector_type": selector_type,
            "properties": {
                "text": elem.text.strip() if elem.text else "",
                "attributes": {k: v for k, v in elem.attrs.items()},
                "is_visible": is_likely_visible(elem)
            }
        }
        
        elements.append(element)
    
    return elements

def determine_element_purpose(element):
    """Determine the functional purpose of an element"""
    element_type = element.name
    
    # Button types
    if element_type == 'button' or (element_type == 'input' and element.get('type') in ['button', 'submit', 'reset']):
        if any(word in (element.text.lower() if element.text else '') or 
               word in str(element.get('value', '')).lower() for word in ['submit', 'save', 'confirm']):
            return 'submit'
        elif any(word in (element.text.lower() if element.text else '') or 
                word in str(element.get('value', '')).lower() for word in ['cancel', 'close', 'back']):
            return 'cancel'
        else:
            return 'action'
    
    # Input types
    elif element_type == 'input':
        input_type = element.get('type', 'text')
        if input_type in ['text', 'email', 'password', 'number', 'tel', 'url']:
            return f'input_{input_type}'
        elif input_type in ['checkbox', 'radio']:
            return input_type
        else:
            return 'input'
    
    # Navigation
    elif element_type == 'a':
        return 'navigation'
    
    # Form elements
    elif element_type in ['select', 'textarea']:
        return element_type
    elif element_type == 'form':
        return 'form'
    
    # Content containers
    elif element_type in ['div', 'section']:
        if element.get('class') and any(c in str(element.get('class')) for c in ['container', 'panel', 'card', 'box']):
            return 'container'
        else:
            return 'structure'
    
    # Text elements
    elif element_type in ['span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        return 'text'
    
    # Lists
    elif element_type in ['ul', 'ol']:
        return 'list'
    elif element_type == 'li':
        return 'list_item'
    
    # Tables
    elif element_type == 'table':
        return 'table'
    elif element_type in ['tr', 'td', 'th']:
        return 'table_element'
    
    # Media
    elif element_type in ['img', 'video', 'audio']:
        return 'media'
    
    # Default fallback
    return 'unknown'

def is_likely_visible(element):
    """Attempt to determine if an element is likely visible"""
    # Check for explicit visibility attributes
    if 'hidden' in element.attrs or element.get('type') == 'hidden':
        return False
    
    # Check styling for visibility hints
    style = element.get('style', '')
    if 'display: none' in style or 'visibility: hidden' in style:
        return False
    
    # Check for ARIA hidden attribute
    if element.get('aria-hidden') == 'true':
        return False
    
    # By default, assume it's visible
    return True

def generate_xpath(element) -> str:
    """Generate a unique XPath for an element"""
    components = []
    child = element
    
    for parent in element.parents:
        if parent.name == 'html':
            break
        
        siblings = parent.find_all(child.name, recursive=False)
        if len(siblings) > 1:
            index = siblings.index(child) + 1
            components.append(f"{child.name}[{index}]")
        else:
            components.append(child.name)
        
        child = parent
    
    components.reverse()
    return '//' + '/'.join(components)

def determine_element_name(element, file_name: str) -> str:
    """Create a meaningful name for the element"""
    element_type = element.name
    
    # Try different attributes to create a meaningful name
    if element.get('id'):
        return f"{element_type}_{element.get('id')}"
    elif element.get('name'):
        return f"{element_type}_{element.get('name')}"
    elif element.get('data-testid'):
        return f"{element_type}_{element.get('data-testid')}"
    elif element.get('aria-label'):
        return f"{element_type}_{element.get('aria-label').lower().replace(' ', '_')}"
    elif element.text and len(element.text.strip()) < 30:
        # Clean text to make it a valid identifier
        clean_text = re.sub(r'[^a-zA-Z0-9_]', '_', element.text.strip().lower())
        # Remove consecutive underscores
        clean_text = re.sub(r'_+', '_', clean_text)
        # Truncate if too long
        return f"{element_type}_{clean_text[:20]}"
    else:
        # Fallback: use file name + element type + random suffix
        class_part = element.get('class', [''])[0] if element.get('class') else ''
        return f"{file_name.split('.')[0]}_{element_type}_{class_part}"

# POM Generator Functions
def generate_pom(elements: List[Dict[str, Any]], project_id: str) -> Dict[str, Any]:
    """Generate enhanced Page Object Model from extracted elements"""
    try:
        # Create results directory for the project
        project_dir = os.path.join(RESULTS_FOLDER, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        # Extract unique page/component names based on file paths and element hierarchy
        page_components = {}
        
        # First pass: group by file name as a base for page structure
        for element in elements:
            element_name = element["name"]
            parts = element_name.split('_')
            
            if len(parts) > 0:
                file_component = parts[0]
                if file_component not in page_components:
                    page_components[file_component] = []
                
                page_components[file_component].append(element)
        
        # Second pass: try to organize elements into a logical hierarchy
        # within pages based on nesting, purpose and selector types
        organized_elements = []
        page_hierarchy = {}
        
        for page_name, page_elements in page_components.items():
            page_id = str(uuid.uuid4())
            page = {
                "id": page_id,
                "name": f"{page_name.capitalize()}Page",
                "type": "page",
                "children": []
            }
            
            # Group elements by purpose/functionality
            purpose_groups = {}
            for element in page_elements:
                purpose = element.get("purpose", "unknown")
                if purpose not in purpose_groups:
                    purpose_groups[purpose] = []
                purpose_groups[purpose].append(element)
            
            # Add elements to page with enhanced structure
            for purpose, purpose_elements in purpose_groups.items():
                if len(purpose_elements) > 3:  # Create a section for related elements
                    section_id = str(uuid.uuid4())
                    section = {
                        "id": section_id,
                        "name": f"{page_name}_{purpose}_section",
                        "type": "section",
                        "parent_id": page_id,
                        "purpose": purpose,
                        "children": []
                    }
                    
                    for element in purpose_elements:
                        element_copy = element.copy()
                        element_copy["parent_id"] = section_id
                        organized_elements.append(element_copy)
                        section["children"].append(element_copy["id"])
                    
                    organized_elements.append(section)
                    page["children"].append(section_id)
                else:
                    # Add elements directly to page
                    for element in purpose_elements:
                        element_copy = element.copy()
                        element_copy["parent_id"] = page_id
                        organized_elements.append(element_copy)
                        page["children"].append(element_copy["id"])
            
            organized_elements.append(page)
            page_hierarchy[page_name] = page
        
        # Use Gemini to enhance POM structure if API key is available
        if GEMINI_API_KEY:
            try:
                enhanced_elements = generate_pom_with_gemini(organized_elements)
                if enhanced_elements:
                    organized_elements = enhanced_elements
            except Exception as e:
                logger.error(f"Error using Gemini API for POM enhancement: {str(e)}")
        
        # Save POM to file with enhanced structure
        pom_file_path = os.path.join(project_dir, "page_object_model.json")
        with open(pom_file_path, 'w', encoding='utf-8') as f:
            json.dump(organized_elements, f, indent=2)
        
        # Generate code file with class representation
        py_file_path = generate_pom_code_file(organized_elements, project_dir)
        
        # Generate a flow identification file for possible user flows
        flow_file_path = generate_flow_identification(organized_elements, project_dir)
        
        return {
            "elements": organized_elements,
            "file_path": pom_file_path,
            "code_path": py_file_path,
            "flow_path": flow_file_path
        }
    except Exception as e:
        logger.error(f"Error generating POM: {str(e)}")
        logger.error(traceback.format_exc())
        # Return minimal result to avoid breaking the flow
        return {
            "elements": elements,
            "file_path": ""
        }

def generate_flow_identification(elements, project_dir):
    """Analyze UI elements to identify potential user flows/scenarios"""
    # Group elements by page
    pages = {}
    for element in elements:
        if element.get("type") == "page":
            pages[element["id"]] = {
                "name": element["name"],
                "elements": []
            }
    
    # Assign elements to their pages
    for element in elements:
        if element.get("type") != "page" and "parent_id" in element:
            parent_id = element["parent_id"]
            
            # Find the page this element belongs to
            for page_id, page_data in pages.items():
                if page_id == parent_id or any(pid == parent_id for pid in find_parent_chain(elements, parent_id, page_id)):
                    pages[page_id]["elements"].append(element)
                    break
    
    # Identify potential flows
    flows = []
    
    # Flow type 1: Form submission flows
    for page_id, page_data in pages.items():
        page_name = page_data["name"]
        page_elements = page_data["elements"]
        
        forms = [e for e in page_elements if e.get("type") == "form"]
        inputs = [e for e in page_elements if e.get("purpose", "").startswith("input_")]
        buttons = [e for e in page_elements if e.get("purpose") in ["submit", "action"]]
        
        # If we have inputs and submit buttons, likely a form flow
        if inputs and buttons:
            flow_id = str(uuid.uuid4())
            input_fields = []
            for input_elem in inputs:
                field_name = input_elem.get("name", "unknown")
                field_type = input_elem.get("properties", {}).get("attributes", {}).get("type", "text")
                input_fields.append({
                    "id": input_elem["id"],
                    "name": field_name,
                    "type": field_type
                })
            
            flow = {
                "id": flow_id,
                "name": f"{page_name}_form_submission",
                "type": "form_submission",
                "page": page_name,
                "description": f"Submit form on {page_name}",
                "steps": [
                    {"step": 1, "action": "navigate", "target": page_name},
                    {"step": 2, "action": "fill_form", "fields": input_fields}
                ]
            }
            
            # Add submit button step
            submit_buttons = [b for b in buttons if b.get("purpose") == "submit"]
            if submit_buttons:
                flow["steps"].append({
                    "step": 3,
                    "action": "click",
                    "target": submit_buttons[0]["name"],
                    "element_id": submit_buttons[0]["id"]
                })
            elif buttons:
                flow["steps"].append({
                    "step": 3,
                    "action": "click",
                    "target": buttons[0]["name"],
                    "element_id": buttons[0]["id"]
                })
            
            flows.append(flow)
    
    # Flow type 2: Navigation flows
    navigation_flows = []
    for page_id, page_data in pages.items():
        page_name = page_data["name"]
        page_elements = page_data["elements"]
        
        links = [e for e in page_elements if e.get("type") == "a" or e.get("purpose") == "navigation"]
        
        for link in links:
            target = link.get("properties", {}).get("attributes", {}).get("href", "")
            if target and not target.startswith('#') and not target.startswith('javascript:'):
                flow_id = str(uuid.uuid4())
                flow = {
                    "id": flow_id,
                    "name": f"{page_name}_navigate_to_{link['name']}",
                    "type": "navigation",
                    "page": page_name,
                    "description": f"Navigate from {page_name} to {target}",
                    "steps": [
                        {"step": 1, "action": "navigate", "target": page_name},
                        {
                            "step": 2, 
                            "action": "click", 
                            "target": link["name"],
                            "element_id": link["id"]
                        }
                    ]
                }
                navigation_flows.append(flow)
    
    flows.extend(navigation_flows)
    
    # Flow type 3: Interactive element flows (buttons, checkboxes, etc.)
    for page_id, page_data in pages.items():
        page_name = page_data["name"]
        page_elements = page_data["elements"]
        
        interactive_elements = [e for e in page_elements 
                              if e.get("purpose") in ["action", "checkbox", "radio", "select"]]
        
        for elem in interactive_elements:
            flow_id = str(uuid.uuid4())
            action = "click"
            if elem.get("purpose") == "select":
                action = "select"
            elif elem.get("purpose") in ["checkbox", "radio"]:
                action = "toggle"
            
            flow = {
                "id": flow_id,
                "name": f"{page_name}_{action}_{elem['name']}",
                "type": "interaction",
                "page": page_name,
                "description": f"{action.capitalize()} {elem['name']} on {page_name}",
                "steps": [
                    {"step": 1, "action": "navigate", "target": page_name},
                    {
                        "step": 2, 
                        "action": action, 
                        "target": elem["name"],
                        "element_id": elem["id"]
                    }
                ]
            }
            flows.append(flow)
    
    # Save flows to file
    flows_file_path = os.path.join(project_dir, "identified_flows.json")
    with open(flows_file_path, 'w', encoding='utf-8') as f:
        json.dump(flows, f, indent=2)
    
    # Generate human-readable flow documentation
    flow_doc_path = os.path.join(project_dir, "test_flows.md")
    with open(flow_doc_path, 'w', encoding='utf-8') as f:
        f.write("# Identified Test Flows\n\n")
        
        for flow in flows:
            f.write(f"## {flow['name']}\n\n")
            f.write(f"**Type:** {flow['type']}\n\n")
            f.write(f"**Description:** {flow['description']}\n\n")
            f.write("**Steps:**\n\n")
            
            for step in flow['steps']:
                f.write(f"{step['step']}. {step['action'].capitalize()} {step['target']}\n")
            
            f.write("\n---\n\n")
    
    return flows_file_path

def find_parent_chain(elements, current_id, target_id):
    """Find chain of parents from current to target"""
    if current_id == target_id:
        return [current_id]
    
    # Find element with current_id
    current_element = next((e for e in elements if e.get("id") == current_id), None)
    if not current_element or "parent_id" not in current_element:
        return []
    
    parent_id = current_element["parent_id"]
    parent_chain = find_parent_chain(elements, parent_id, target_id)
    
    if parent_chain:
        return [current_id] + parent_chain
    else:
        return []

def generate_pom_with_gemini(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Use Gemini to enhance POM structure"""
    # Convert elements to JSON string
    elements_json = json.dumps(elements, indent=2)
    
    # Create prompt for Gemini
    prompt = f"""
As an AI specialized in UI test automation, I need your help to analyze and improve a Page Object Model (POM) structure.

Here is a JSON representation of UI elements extracted from a web application:

{elements_json}

Please analyze this structure and provide an improved version with the following enhancements:
1. Group related elements logically
2. Add meaningful names and descriptions
3. Ensure proper parent-child relationships
4. Add suggestions for best selectors to use
5. Identify any potential test cases that could be created

Return only the improved JSON structure without any additional explanations. The structure should be valid JSON and should maintain the same schema as the input with keys like "id", "name", "type", "selector", "selector_type", etc.
"""
    
    try:
        # Generate response from Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Extract and parse JSON from response
        response_text = response.text
        # Find JSON start and end indices
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                improved_elements = json.loads(json_str)
                return improved_elements
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Gemini response: {e}")
                # Try to clean up the response
                json_str = json_str.replace("```json", "").replace("```", "")
                try:
                    improved_elements = json.loads(json_str)
                    return improved_elements
                except:
                    logger.error("Failed to parse JSON even after cleanup")
                    return None
        else:
            logger.error("No valid JSON found in Gemini response")
            return None
    
    except Exception as e:
        logger.error(f"Error using Gemini API: {str(e)}")
        return None

def generate_pom_code_file(elements, project_dir: str) -> str:
    """Generate robust Python code representation of the POM"""
    # Helper function to sanitize names
    def sanitize_id(name):
        """Convert any string to a valid Python identifier"""
        import re
        # Replace all non-alphanumeric chars with underscores
        sanitized = re.sub(r'[^0-9a-zA-Z_]', '_', str(name))
        # Ensure it starts with a letter or underscore
        if sanitized and not (sanitized[0].isalpha() or sanitized[0] == '_'):
            sanitized = 'elem_' + sanitized
        # Ensure it's not empty
        if not sanitized:
            sanitized = 'element'
        return sanitized
    
    # Basic POM structure with enhanced base class
    code = """from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('PageObjects')

class BasePage:
    '''Base class for all page objects with enhanced error handling and logging'''
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.actions = ActionChains(self.driver)
    
    def navigate_to(self, url):
        '''Navigate to a specific URL'''
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            raise
    
    def find_element(self, by, value, timeout=10):
        '''Find element with explicit wait and error handling'''
        try:
            logger.debug(f"Finding element: {by}={value}")
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            logger.error(f"Error finding element {by}={value}: {e}")
            # Take screenshot for debugging
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"error_screenshot_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Screenshot saved to {screenshot_path}")
            raise
    
    def find_by_id(self, id_value, timeout=10):
        return self.find_element(By.ID, id_value, timeout)
        
    def find_by_class(self, class_name, timeout=10):
        return self.find_element(By.CLASS_NAME, class_name, timeout)
    
    def find_by_name(self, name, timeout=10):
        return self.find_element(By.NAME, name, timeout)
    
    def find_by_xpath(self, xpath, timeout=10):
        return self.find_element(By.XPATH, xpath, timeout)
    
    def find_by_css(self, css, timeout=10):
        return self.find_element(By.CSS_SELECTOR, css, timeout)
    
    def find_by_tag(self, tag, timeout=10):
        return self.find_element(By.TAG_NAME, tag, timeout)
    
    def find_by_link_text(self, text, timeout=10):
        return self.find_element(By.LINK_TEXT, text, timeout)
    
    def find_by_partial_link_text(self, text, timeout=10):
        return self.find_element(By.PARTIAL_LINK_TEXT, text, timeout)
    
    def click_element(self, element):
        '''Click element with enhanced error handling and fallbacks'''
        try:
            # Wait for element to be clickable
            self.wait_for_element_clickable(element)
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)  # Wait for scroll
            
            # Try standard click
            element.click()
            logger.info(f"Clicked element: {element}")
        except Exception as e:
            logger.warning(f"Standard click failed, trying JavaScript click: {e}")
            try:
                # Try JavaScript click as fallback
                self.driver.execute_script("arguments[0].click();", element)
                logger.info("JavaScript click successful")
            except Exception as e2:
                logger.error(f"Failed to click element: {e2}")
                raise
    
    def input_text(self, element, text):
        '''Send text to element with enhanced error handling'''
        try:
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)  # Wait for scroll
            
            # Click to focus
            self.click_element(element)
            
            # Try to clear with multiple methods
            try:
                # Standard clear
                element.clear()
            except:
                # Fallback to select all + delete
                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.DELETE).perform()
                time.sleep(0.3)
            
            # Send keys
            element.send_keys(text)
            logger.info(f"Input text: '{text}' into element")
        except Exception as e:
            logger.warning(f"Standard input failed, trying JavaScript: {e}")
            try:
                # Try JavaScript as fallback
                self.driver.execute_script(f"arguments[0].value = '{text.replace("'", "\\'")}';", element)
                logger.info("JavaScript input successful")
            except Exception as e2:
                logger.error(f"Failed to input text: {e2}")
                raise
    
    def select_option(self, select_element, option_text):
        '''Select option from dropdown by visible text'''
        try:
            from selenium.webdriver.support.ui import Select
            select = Select(select_element)
            select.select_by_visible_text(option_text)
            logger.info(f"Selected option: '{option_text}'")
        except Exception as e:
            logger.error(f"Failed to select option '{option_text}': {e}")
            raise
    
    def get_text(self, element):
        '''Get element text with fallbacks'''
        try:
            text = element.text
            if text:
                return text
            
            # Try value attribute for inputs
            value = element.get_attribute("value")
            if value:
                return value
                
            # Fallback to JavaScript
            return self.driver.execute_script("return arguments[0].textContent;", element)
        except Exception as e:
            logger.error(f"Failed to get text: {e}")
            return ""
    
    def wait_for_element_visible(self, locator, timeout=10):
        '''Wait for element to be visible with logging'''
        logger.debug(f"Waiting for element to be visible: {locator}")
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )
        
    def wait_for_element_clickable(self, element, timeout=10):
        '''Wait for element to be clickable with logging'''
        logger.debug(f"Waiting for element to be clickable")
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(element)
        )
    
    def wait_for_page_load(self, timeout=30):
        '''Wait for page to finish loading'''
        logger.debug("Waiting for page to load")
        return WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    
    def is_element_present(self, by, value, timeout=5):
        '''Check if element is present with timeout'''
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except:
            return False
    
    def is_element_visible(self, by, value, timeout=5):
        '''Check if element is visible with timeout'''
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return True
        except:
            return False
            
    def hover_over_element(self, element):
        '''Hover over an element'''
        try:
            ActionChains(self.driver).move_to_element(element).perform()
            logger.info("Hovered over element")
        except Exception as e:
            logger.error(f"Failed to hover over element: {e}")
            raise
"""

    try:
        # Store element names for test file reference
        element_mappings = {}
        
        # Group elements by page
        pages = [element for element in elements if element["type"] == "page"]
        
        # Generate page classes
        for page in pages:
            page_name = sanitize_id(page['name'])
            page_elements = [e for e in elements if e.get("parent_id") == page["id"]]
            
            code += f"\n\nclass {page_name}(BasePage):\n"
            code += "    def __init__(self, driver, base_url='http://localhost'):\n"
            code += "        super().__init__(driver)\n"
            code += "        self.base_url = base_url\n"
            code += f"        self.page_url = f\"{{self.base_url}}/\"\n"
            
            # Add navigate method
            code += f"\n    def navigate(self):\n"
            code += f"        self.navigate_to(self.page_url)\n"
            code += f"        self.wait_for_page_load()\n"
            code += f"        return self\n"
            
            # Track used names to avoid duplicates
            used_names = set()
            page_element_mappings = {}
            
            # Create element properties and methods
            for i, element in enumerate(page_elements):
                # Generate a completely safe element name
                base_name = sanitize_id(element["name"].replace('-', '_'))
                element_name = base_name
                
                # Handle duplicate names
                counter = 1
                while element_name in used_names:
                    element_name = f"{base_name}_{counter}"
                    counter += 1
                
                used_names.add(element_name)
                element_type = element["type"]
                selector_type = element.get("selector_type", "xpath")
                selector = element.get("selector", "")
                
                # Skip if no valid selector
                if not selector:
                    continue
                
                # Important: Store the sanitized name for test file generation
                original_id = element.get("id", f"element_{i}")
                page_element_mappings[original_id] = element_name
                
                # Create robust element locator method
                code += f"\n    def _get_{element_name}(self):\n"
                code += f"        \"\"\"Get the {element_name} element\"\"\"\n"
                code += f"        try:\n"
                
                # Different selector types
                if selector_type == "id":
                    code += f"            return self.find_by_id({repr(selector.replace('#', ''))})\n"
                elif selector_type == "class":
                    class_name = selector.replace('.', '')
                    code += f"            return self.find_by_class({repr(class_name)})\n"
                elif selector_type == "name":
                    name_value = selector.replace('[name=\'', '').replace('\']', '')
                    code += f"            return self.find_by_name({repr(name_value)})\n"
                elif selector_type in ["data-testid", "data-cy", "data-test", "role"]:
                    # Extract attribute name and value
                    attr_match = re.match(r'\[([^=]+)=\'([^\']+)\'\]', selector)
                    if attr_match:
                        attr_name, attr_value = attr_match.groups()
                        code += f"            return self.find_by_css({repr(selector)})\n"
                    else:
                        code += f"            return self.find_by_css({repr(selector)})\n"
                elif selector_type == "xpath":
                    code += f"            return self.find_by_xpath({repr(selector)})\n"
                else:
                    code += f"            return self.find_by_css({repr(selector)})\n"
                
                code += f"        except Exception as e:\n"
                code += f"            logger.error(f\"Error finding {element_name}: {{e}}\")\n"
                code += f"            # Return a dummy element or re-raise\n"
                code += f"            raise\n"

                # Make all element access robust using the property pattern
                code += f"\n    @property\n"
                code += f"    def {element_name}(self):\n"
                code += f"        return self._get_{element_name}()\n"
                
                # Element action methods based on type and purpose
                purpose = element.get("purpose", "")
                
                # Click methods for clickable elements
                if element_type in ["button", "a"] or purpose in ["submit", "action", "navigation"]:
                    code += f"\n    def click_{element_name}(self):\n"
                    code += f"        \"\"\"Click the {element_name}\"\"\"\n"
                    code += f"        element = self._get_{element_name}()\n"
                    code += f"        self.click_element(element)\n"
                    code += f"        self.wait_for_page_load()\n"
                    code += f"        return self\n"
                
                # Input methods
                if element_type in ["input", "textarea"] or purpose.startswith("input_"):
                    code += f"\n    def set_{element_name}(self, text):\n"
                    code += f"        \"\"\"Set text in the {element_name}\"\"\"\n"
                    code += f"        element = self._get_{element_name}()\n"
                    code += f"        self.input_text(element, text)\n"
                    code += f"        return self\n"
                
                # Select methods for dropdowns
                if element_type == "select" or purpose == "select":
                    code += f"\n    def select_{element_name}(self, option_text):\n"
                    code += f"        \"\"\"Select option from {element_name} dropdown\"\"\"\n"
                    code += f"        element = self._get_{element_name}()\n"
                    code += f"        self.select_option(element, option_text)\n"
                    code += f"        return self\n"
                
                # Toggle methods for checkboxes and radio buttons
                if purpose in ["checkbox", "radio"]:
                    code += f"\n    def toggle_{element_name}(self):\n"
                    code += f"        \"\"\"Toggle the {element_name}\"\"\"\n"
                    code += f"        element = self._get_{element_name}()\n"
                    code += f"        self.click_element(element)\n"
                    code += f"        return self\n"
                
                # Get text methods for text-containing elements
                if purpose in ["text", "container"] or element_type in ["span", "div", "p", "h1", "h2", "h3", "h4", "h5", "h6"]:
                    code += f"\n    def get_{element_name}_text(self):\n"
                    code += f"        \"\"\"Get text from {element_name}\"\"\"\n"
                    code += f"        element = self._get_{element_name}()\n"
                    code += f"        return self.get_text(element)\n"
            
            # Add verification method for page
            code += f"\n    def verify_page_loaded(self):\n"
            code += f"        \"\"\"Verify that the {page_name} is loaded correctly\"\"\"\n"
            
            # Use an essential element for verification if available
            essential_elements = [e for e in page_elements if e.get("purpose") in ["container", "navigation"]]
            if essential_elements:
                element_name = page_element_mappings.get(essential_elements[0]["id"])
                if element_name:
                    code += f"        return self.is_element_visible(By.CSS_SELECTOR, '{essential_elements[0].get('selector')}')\n"
            else:
                # Otherwise check URL or title
                code += f"        # Check if we're on the right page by URL or title\n"
                code += f"        return self.driver.title is not None\n"
                
            element_mappings[page_name] = page_element_mappings
    
    except Exception as e:
        logger.error(f"Error generating page objects code: {str(e)}")
        logger.error(traceback.format_exc())
        code += "\n# Error occurred while generating page classes\n"
        # Generate a basic fallback class if an error occurs
        code += "\nclass FallbackPage(BasePage):\n"
        code += "    def __init__(self, driver):\n"
        code += "        super().__init__(driver)\n"
        code += "\n    def get_element(self):\n"
        code += "        return self.find_by_css('body')\n"
    
    # Save element mappings for test generation
    mappings_file_path = os.path.join(project_dir, "element_mappings.json")
    with open(mappings_file_path, 'w', encoding='utf-8') as f:
        json.dump(element_mappings, f, indent=2)
    
    # Save Python file
    py_file_path = os.path.join(project_dir, "page_objects.py")
    with open(py_file_path, 'w', encoding='utf-8') as f:
        f.write(code)
    
    return py_file_path

def generate_basic_tests(elements_by_page, project_url="http://localhost:5000", element_mappings=None):
    """Generate basic test scripts without Gemini"""
    # Helper function to sanitize names
    def sanitize_id(name):
        """Convert any string to a valid Python identifier"""
        import re
        # Replace all non-alphanumeric chars with underscores
        sanitized = re.sub(r'[^0-9a-zA-Z_]', '_', str(name))
        # Ensure it starts with a letter or underscore
        if sanitized and not (sanitized[0].isalpha() or sanitized[0] == '_'):
            sanitized = 'elem_' + sanitized
        # Ensure it's not empty
        if not sanitized:
            sanitized = 'element'
        return sanitized
    
    test_scripts = []
    
    for page_id, page_data in elements_by_page.items():
        page_name = sanitize_id(page_data["name"])
        page_elements = page_data["elements"]
        
        # Skip if no elements on the page
        if not page_elements:
            continue
        
        # Get element mappings for this page if available
        page_element_mappings = {}
        if element_mappings and page_name in element_mappings:
            page_element_mappings = element_mappings[page_name]
        
        # Create a basic test for page navigation
        navigation_code = f"""import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from page_objects import {page_name}
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('NavigationTest')

class TestNavigation{page_name}(unittest.TestCase):
    def setUp(self):
        self.driver = None
        try:
            # Set up Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-infobars")
            
            # Uncomment to run headless
            # chrome_options.add_argument("--headless")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.page = {page_name}(self.driver, base_url="{project_url}")
        except Exception as e:
            logger.error(f"Error in setup: {{e}}")
            if self.driver:
                self.driver.quit()
            raise
        
    def tearDown(self):
        if self.driver:
            self.driver.quit()
        
    def test_page_navigation(self):
        '''Test navigation to {page_name} and verify elements are present'''
        try:
            # Navigate to the page
            logger.info(f"Navigating to {page_name}")
            self.page.navigate()
            
            # Wait for page to load completely
            self.assertTrue(self.page.verify_page_loaded(), "Page failed to load properly")
            
            # Verify key elements are present
"""
        
        # Add assertions for each element
        for i, element in enumerate(page_elements):
            # Use the mapped element name if available, otherwise generate one
            element_id = element.get("id", f"element_{i}")
            if element_id in page_element_mappings:
                element_name = page_element_mappings[element_id]
            else:
                # Generate a completely safe element name
                element_name = sanitize_id(element["name"].replace('-', '_'))
            
            # Only test elements that have properties/methods in the page object
            navigation_code += f"            # Verify {element_name} is present\n"
            navigation_code += f"            try:\n"
            navigation_code += f"                self.assertIsNotNone(self.page.{element_name}, \"{element_name} element not found\")\n"
            navigation_code += f"                logger.info(f\"{element_name} verified\")\n"
            navigation_code += f"            except Exception as e:\n"
            navigation_code += f"                logger.warning(f\"Could not verify {element_name}: {{e}}\")\n"
        
        navigation_code += """
        except Exception as e:
            # Take screenshot on failure
            if self.driver:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"test_failure_{timestamp}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.error(f"Test failed. Screenshot saved to {screenshot_path}")
            logger.error(f"Error in test_page_navigation: {e}")
            raise

if __name__ == '__main__':
    unittest.main()
"""
        
        test_scripts.append({
            "name": f"test_navigation_{page_name.lower()}.py",
            "code": navigation_code
        })
        
        # Create interaction tests for interactive elements
        interactive_elements = [e for e in page_elements 
                             if e["type"] in ["button", "a", "input", "textarea", "select"] or
                                e.get("purpose", "") in ["action", "submit", "navigation", "checkbox", "radio", "select"]]
        
        if interactive_elements:
            interaction_code = f"""import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from page_objects import {page_name}
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('InteractionTest')

class TestInteraction{page_name}(unittest.TestCase):
    def setUp(self):
        self.driver = None
        try:
            # Set up Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-infobars")
            
            # Uncomment to run headless
            # chrome_options.add_argument("--headless")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.page = {page_name}(self.driver, base_url="{project_url}")
            
            # Navigate to the page
            self.page.navigate()
            
            # Wait for page to load
            self.assertTrue(self.page.verify_page_loaded(), "Page failed to load properly")
        except Exception as e:
            logger.error(f"Error in setup: {{e}}")
            if self.driver:
                self.driver.quit()
            raise
        
    def tearDown(self):
        if self.driver:
            self.driver.quit()
"""
            
            for i, element in enumerate(interactive_elements):
                # Use the mapped element name if available, otherwise generate one
                element_id = element.get("id", f"element_{i}")
                if element_id in page_element_mappings:
                    element_name = page_element_mappings[element_id]
                else:
                    # Generate a completely safe element name
                    element_name = sanitize_id(element["name"].replace('-', '_'))
                
                element_type = element["type"]
                element_purpose = element.get("purpose", "")
                
                # Click tests for buttons and links
                if element_type in ["button", "a"] or element_purpose in ["submit", "action", "navigation"]:
                    interaction_code += f"""
    def test_click_{element_name}(self):
        '''Test clicking the {element_name} element'''
        try:
            # Wait for page stability
            time.sleep(1)
            
            # Verify element exists
            self.assertIsNotNone(self.page.{element_name}, "{element_name} not found")
            
            # Click the element
            logger.info(f"Clicking {element_name}")
            self.page.click_{element_name}()
            
            # Wait after click to see results
            time.sleep(1)
            
            # Add assertions for expected behavior after click
            # For example, check if URL changed, new elements appeared, etc.
            pass
        except Exception as e:
            # Take screenshot on failure
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"click_{element_name}_failure_{{timestamp}}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.error(f"Test failed. Screenshot saved to {{screenshot_path}}")
            logger.error(f"Error in test_click_{element_name}: {{e}}")
            raise
"""
                # Input tests
                elif element_type in ["input", "textarea"] or element_purpose.startswith("input_"):
                    input_type = element.get("properties", {}).get("attributes", {}).get("type", "text")
                    test_value = ""
                    
                    # Set appropriate test values based on input type
                    if input_type == "email":
                        test_value = "test@example.com"
                    elif input_type == "password":
                        test_value = "TestPassword123"
                    elif input_type == "number":
                        test_value = "42"
                    elif input_type == "tel":
                        test_value = "123-456-7890"
                    elif input_type == "date":
                        test_value = "2025-01-01"
                    else:
                        test_value = "Test input text"
                    
                    interaction_code += f"""
    def test_input_{element_name}(self):
        '''Test inputting text into the {element_name} field'''
        try:
            # Wait for page stability
            time.sleep(1)
            
            # Verify element exists
            self.assertIsNotNone(self.page.{element_name}, "{element_name} not found")
            
            # Input text
            test_text = "{test_value}"
            logger.info(f"Setting text in {element_name}: {{test_text}}")
            self.page.set_{element_name}(test_text)
            
            # Wait after input to see results
            time.sleep(1)
            
            # Add assertions to verify the input was successful
            # For example, check if value attribute matches input
            # element_value = self.page.{element_name}.get_attribute("value")
            # self.assertEqual(element_value, test_text, "Input text verification failed")
        except Exception as e:
            # Take screenshot on failure
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"input_{element_name}_failure_{{timestamp}}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.error(f"Test failed. Screenshot saved to {{screenshot_path}}")
            logger.error(f"Error in test_input_{element_name}: {{e}}")
            raise
"""
                # Select tests
                elif element_type == "select" or element_purpose == "select":
                    interaction_code += f"""
    def test_select_{element_name}(self):
        '''Test selecting an option from the {element_name} dropdown'''
        try:
            # Wait for page stability
            time.sleep(1)
            
            # Verify element exists
            self.assertIsNotNone(self.page.{element_name}, "{element_name} not found")
            
            # This is a placeholder - you should replace with an actual option from your dropdown
            option = "Option 1"
            logger.info(f"Selecting option from {element_name}: {{option}}")
            self.page.select_{element_name}(option)
            
            # Wait after selection to see results
            time.sleep(1)
            
            # Add assertions to verify the selection was successful
        except Exception as e:
            # Take screenshot on failure
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"select_{element_name}_failure_{{timestamp}}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.error(f"Test failed. Screenshot saved to {{screenshot_path}}")
            logger.error(f"Error in test_select_{element_name}: {{e}}")
            raise
"""
                # Toggle tests for checkboxes and radio buttons
                elif element_purpose in ["checkbox", "radio"]:
                    interaction_code += f"""
    def test_toggle_{element_name}(self):
        '''Test toggling the {element_name} checkbox/radio button'''
        try:
            # Wait for page stability
            time.sleep(1)
            
            # Verify element exists
            self.assertIsNotNone(self.page.{element_name}, "{element_name} not found")
            
            # Toggle the element
            logger.info(f"Toggling {element_name}")
            self.page.toggle_{element_name}()
            
            # Wait after toggle to see results
            time.sleep(1)
            
            # Add assertions to verify the toggle was successful
            # For example, check if the element is selected
            # self.assertTrue(self.page.{element_name}.is_selected(), "Element was not toggled successfully")
        except Exception as e:
            # Take screenshot on failure
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"toggle_{element_name}_failure_{{timestamp}}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.error(f"Test failed. Screenshot saved to {{screenshot_path}}")
            logger.error(f"Error in test_toggle_{element_name}: {{e}}")
            raise
"""
            
            interaction_code += """
if __name__ == '__main__':
    unittest.main()
"""
            
            test_scripts.append({
                "name": f"test_interaction_{page_name.lower()}.py",
                "code": interaction_code
            })
            
        # Create a form flow test if there are multiple inputs and a submit button
        input_elements = [e for e in page_elements if e["type"] in ["input", "textarea", "select"] or 
                         e.get("purpose", "").startswith("input_") or e.get("purpose") in ["select"]]
        submit_elements = [e for e in page_elements if e.get("purpose") == "submit"]
        
        if len(input_elements) >= 2 and submit_elements:
            form_flow_code = f"""import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from page_objects import {page_name}
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('FormFlowTest')

class TestFormFlow{page_name}(unittest.TestCase):
    def setUp(self):
        self.driver = None
        try:
            # Set up Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-infobars")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.page = {page_name}(self.driver, base_url="{project_url}")
        except Exception as e:
            logger.error(f"Error in setup: {{e}}")
            if self.driver:
                self.driver.quit()
            raise
        
    def tearDown(self):
        if self.driver:
            self.driver.quit()
        
    def test_form_submission(self):
        '''Test complete form submission flow'''
        try:
            # Navigate to the page
            logger.info(f"Navigating to {page_name}")
            self.page.navigate()
            
            # Wait for page to load
            time.sleep(2)
            
            # Fill in form fields
"""
            
            # Add form filling steps
            for i, element in enumerate(input_elements):
                element_id = element.get("id", f"element_{i}")
                if element_id in page_element_mappings:
                    element_name = page_element_mappings[element_id]
                else:
                    element_name = sanitize_id(element["name"].replace('-', '_'))
                
                element_type = element["type"]
                element_purpose = element.get("purpose", "")
                
                if element_type in ["input", "textarea"] or element_purpose.startswith("input_"):
                    input_type = element.get("properties", {}).get("attributes", {}).get("type", "text")
                    test_value = ""
                    
                    # Set appropriate test values based on input type
                    if input_type == "email":
                        test_value = "test@example.com"
                    elif input_type == "password":
                        test_value = "TestPassword123"
                    elif input_type == "number":
                        test_value = "42"
                    elif input_type == "tel":
                        test_value = "123-456-7890"
                    elif input_type == "date":
                        test_value = "2025-01-01"
                    else:
                        test_value = f"Test input for {element_name}"
                    
                    form_flow_code += f"            logger.info(f\"Setting {element_name} to {test_value}\")\n"
                    form_flow_code += f"            self.page.set_{element_name}(\"{test_value}\")\n"
                elif element_type == "select" or element_purpose == "select":
                    form_flow_code += f"            logger.info(\"Selecting option from {element_name}\")\n"
                    form_flow_code += f"            self.page.select_{element_name}(\"Option 1\")  # Replace with an actual option\n"
                elif element_purpose in ["checkbox", "radio"]:
                    form_flow_code += f"            logger.info(\"Toggling {element_name}\")\n"
                    form_flow_code += f"            self.page.toggle_{element_name}()\n"
            
            # Add submit step
            if submit_elements:
                submit_id = submit_elements[0].get("id")
                if submit_id in page_element_mappings:
                    submit_name = page_element_mappings[submit_id]
                else:
                    submit_name = sanitize_id(submit_elements[0]["name"].replace('-', '_'))
                
                form_flow_code += f"""
            # Submit the form
            logger.info("Submitting form")
            self.page.click_{submit_name}()
            
            # Wait for form submission to complete
            time.sleep(2)
            
            # Add assertions to verify successful submission
            # For example, check for success message, redirection, etc.
"""
            
            form_flow_code += """
        except Exception as e:
            # Take screenshot on failure
            if self.driver:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                screenshot_path = f"form_flow_failure_{timestamp}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.error(f"Test failed. Screenshot saved to {screenshot_path}")
            logger.error(f"Error in test_form_submission: {e}")
            raise

if __name__ == '__main__':
    unittest.main()
"""
            
            test_scripts.append({
                "name": f"test_form_flow_{page_name.lower()}.py",
                "code": form_flow_code
            })
    
    return test_scripts

def generate_tests_with_gemini(elements):
    """Generate test scripts using Gemini API"""
    # Convert elements to JSON string
    elements_json = json.dumps(elements, indent=2)
    
    # Create prompt for Gemini
    prompt = f"""
As an AI specialized in UI test automation, I need your help to generate Python test scripts for a web application using Selenium.

Here is a JSON representation of a Page Object Model (POM) with UI elements extracted from the application:

{elements_json}

Based on these elements, generate complete Python test scripts following these guidelines:
1. Use unittest framework
2. For each page, create at least two test classes:
   - A navigation test to verify page elements are present
   - An interaction test that performs actions on interactive elements
3. Include proper setup and teardown methods
4. Use the ChromeDriver with webdriver-manager
5. Import from a 'page_objects.py' file that contains the POM classes
6. Add docstrings and comments to explain the test logic
7. Include assertions to verify expected behavior
8. Add proper error handling with try/except blocks
9. Include logging for better debug information
10. Add screenshot capture on test failures

Return a list of test scripts, each as a JSON object with:
- "name": The file name (e.g., "test_login_page.py")
- "code": The complete Python code for the test script

The response should be a valid JSON array of these objects.
"""
    
    try:
        # Generate response from Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Extract and parse JSON from response
        response_text = response.text
        logger.info(f"Gemini response for test generation: {response_text[:200]}...")
        
        # Find JSON start and end indices
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                test_scripts = json.loads(json_str)
                return test_scripts
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from Gemini response")
                # Try to clean up the response
                fixed_json = json_str.replace("```json", "").replace("```", "")
                try:
                    test_scripts = json.loads(fixed_json)
                    return test_scripts
                except:
                    logger.error("Failed to parse JSON even after cleanup")
                    return []
        else:
            logger.error("No valid JSON found in Gemini response")
            return []
    
    except Exception as e:
        logger.error(f"Error using Gemini API for test generation: {str(e)}")
        return []

def process_gemini_test_scripts(test_scripts):
    """Process and sanitize test scripts generated by Gemini to avoid syntax errors"""
    processed_scripts = []
    
    for script in test_scripts:
        name = script.get("name", "test.py")
        code = script.get("code", "")
        
        # Fix any potential syntax issues with quotes in XPath selectors
        # This is a simplified approach; in practice, you'd need more robust processing
        fixed_code = code
        
        processed_scripts.append({
            "name": name,
            "code": fixed_code
        })
    
    return processed_scripts

def create_test_suite(test_directory, test_scripts):
    """Create a test suite that runs all tests"""
    code = """import unittest
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TestSuite')

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
    
    # Import all test modules
    for script in test_scripts:
        module_name = script["name"].replace('.py', '')
        code += f"from {module_name} import *\n"
    
    code += """
if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    loader = unittest.TestLoader()
"""
    
    # Add each test class to the suite
    for script in test_scripts:
        # Extract class names from the script
        class_matches = re.findall(r'class\s+(\w+)\s*\(', script["code"])
        for class_name in class_matches:
            code += f"    test_suite.addTests(loader.loadTestsFromTestCase({class_name}))\n"
    
    code += """
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
"""
    
    # Save the test suite file
    suite_path = os.path.join(test_directory, "test_suite.py")
    with open(suite_path, 'w', encoding='utf-8') as f:
        f.write(code)

def generate_tests(pom, project_id: str) -> Dict[str, Any]:
    """Generate test cases from POM using Gemini API"""
    try:
        # Create results directory for the project
        project_dir = os.path.join(RESULTS_FOLDER, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        # Load element mappings if available
        element_mappings = {}
        mappings_file_path = os.path.join(project_dir, "element_mappings.json")
        if os.path.exists(mappings_file_path):
            try:
                with open(mappings_file_path, 'r', encoding='utf-8') as f:
                    element_mappings = json.load(f)
            except:
                logger.error("Failed to load element mappings")
        
        # Group elements by page
        elements_by_page = {}
        for element in pom["elements"]:
            if element["type"] == "page":
                page_id = element["id"]
                page_name = element["name"]
                elements_by_page[page_id] = {
                    "name": page_name,
                    "elements": []
                }
        
        # Add elements to their respective pages
        for element in pom["elements"]:
            if "parent_id" in element and element["parent_id"] in elements_by_page:
                elements_by_page[element["parent_id"]]["elements"].append(element)
        
        # Generate test scripts
        test_scripts = []
        
        # If Gemini API key is available, use it for test generation
        if GEMINI_API_KEY:
            try:
                test_scripts = generate_tests_with_gemini(pom["elements"])
                # Process and sanitize Gemini-generated scripts
                test_scripts = process_gemini_test_scripts(test_scripts)
                logger.info(f"Generated {len(test_scripts)} test scripts using Gemini")
            except Exception as e:
                logger.error(f"Error using Gemini API for test generation: {e}")
                test_scripts = []
        
        # Fallback to basic test generation if Gemini didn't work or produced no results
        if not test_scripts:
            logger.info("Falling back to basic test generation")
            test_scripts = generate_basic_tests(elements_by_page, "http://localhost:5000", element_mappings)
        
        # Save test scripts to files
        test_directory = os.path.join(project_dir, "tests")
        os.makedirs(test_directory, exist_ok=True)
        
        script_paths = []
        for i, script in enumerate(test_scripts):
            script_name = script.get("name", f"test_{i+1}.py")
            script_path = os.path.join(test_directory, script_name)
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script["code"])
            
            script_paths.append(script_path)
        
        # Create main test suite file
        create_test_suite(test_directory, test_scripts)
        
        # Return information about the generated tests
        return {
            "name": f"Test Suite for Project {project_id}",
            "script_path": os.path.join(test_directory, "test_suite.py"),
            "description": f"Automatically generated tests for project {project_id}",
            "success": True
        }
    except Exception as e:
        logger.error(f"Error in test generation: {e}")
        logger.error(traceback.format_exc())
        # Return a minimal result to avoid breaking the flow
        return {
            "name": f"Error generating tests for Project {project_id}",
            "script_path": "",
            "description": f"Error: {str(e)}",
            "success": False
        }

def parse_test_results(log_content: str):
    """Parse unittest results from log content"""
    results = []
    
    # Split log by lines
    lines = log_content.split('\n')
    
    # Process each line looking for test results
    current_test = None
    for line in lines:
        line = line.strip()
        
        # Look for test method
        if line.startswith('test_') and ' (' in line:
            test_name = line.split(' (')[0]
            current_test = {
                "name": test_name,
                "status": "RUNNING"
            }
        
        # Look for test result
        elif current_test and any(result in line for result in ["ok", "FAIL", "ERROR", "skipped"]):
            if "ok" in line:
                current_test["status"] = "PASSED"
            elif "FAIL" in line:
                current_test["status"] = "FAILED"
            elif "ERROR" in line:
                current_test["status"] = "ERROR"
            elif "skipped" in line:
                current_test["status"] = "SKIPPED"
            
            results.append(current_test)
            current_test = None
    
    return results

def execute_test(test_case):
    """Execute a test case and return the results"""
    try:
        # Create results directory
        project_dir = os.path.join(RESULTS_FOLDER, test_case["project_id"])
        results_dir = os.path.join(project_dir, "execution_results")
        os.makedirs(results_dir, exist_ok=True)
        
        # Generate unique ID for this execution
        execution_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(results_dir, f"execution_{execution_id}_{timestamp}.log")
        
        # Prepare command
        script_path = test_case["script_path"]
        
        # Execute test script
        with open(log_file, 'w') as f:
            result = subprocess.run(
                ['python', script_path],
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=300  # 5 minute timeout
            )
        
        # Read log file
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        # Determine test status
        if result.returncode == 0:
            status = "SUCCESS"
        else:
            status = "FAILURE"
        
        # Parse test results
        test_results = parse_test_results(log_content)
        
        return {
            "status": status,
            "result": {
                "return_code": result.returncode,
                "tests": test_results,
                "log": log_content[:1000] + ("..." if len(log_content) > 1000 else "")
            },
            "log_path": log_file
        }
    
    except subprocess.TimeoutExpired:
        with open(log_file, 'a') as f:
            f.write("\n\nTEST EXECUTION TIMEOUT: Execution took longer than 5 minutes.")
        
        return {
            "status": "TIMEOUT",
            "result": {
                "return_code": -1,
                "tests": [],
                "log": "Test execution timed out after 5 minutes."
            },
            "log_path": log_file
        }
    
    except Exception as e:
        logger.error(f"Error executing test: {str(e)}")
        error_message = f"Error executing test: {str(e)}"
        
        # Try to create a log file for the error
        try:
            with open(log_file, 'a') as f:
                f.write(f"\n\nERROR EXECUTING TEST: {str(e)}")
        except:
            pass
        
        return {
            "status": "ERROR",
            "result": {
                "return_code": -1,
                "tests": [],
                "log": error_message
            },
            "log_path": log_file if os.path.exists(log_file) else ""
        }

# Flask Routes
@app.route('/')
def index():
    """Main page that handles everything"""
    try:
        # Get project list
        project_list = get_all_projects()
        
        # Get selected project if ID is provided
        selected_project_id = request.args.get('project')
        selected_project = None
        selected_poms = []
        selected_tests = []
        selected_executions = []
        selected_elements = []
        
        if selected_project_id:
            selected_project = get_project(selected_project_id)
            
            if selected_project:
                # Get POMs for this project
                selected_poms = get_poms(selected_project_id)
                
                # Get tests for this project
                selected_tests = get_test_cases(selected_project_id)
                
                # Get executions for this project
                selected_executions = get_executions(selected_project_id)
                
                # Get UI elements if available
                selected_elements = get_elements(selected_project_id)
        
        return render_template('index.html', 
                            projects=project_list,
                            selected_project=selected_project,
                            poms=selected_poms,
                            tests=selected_tests,
                            executions=selected_executions,
                            elements=selected_elements,
                            tab=request.args.get('tab', 'dashboard'))

    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"An error occurred: {str(e)}", "error")
        return render_template('index.html', projects=[], tab='dashboard')

@app.route('/create_project', methods=['POST'])
def create_project():
    """Create a new project by uploading source code"""
    try:
        if 'file' not in request.files:
            flash("No file part", "error")
            return redirect(url_for('index'))
        
        files = request.files.getlist('file')
        if not files or files[0].filename == '':
            flash("No selected file", "error")
            return redirect(url_for('index'))
        
        project_id = str(uuid.uuid4())
        project_dir = os.path.join(app.config['UPLOAD_FOLDER'], project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        # Save all files
        file_paths = []
        for file in files:
            filename = secure_filename(file.filename)
            file_path = os.path.join(project_dir, filename)
            file.save(file_path)
            file_paths.append(file_path)
        
        # If only one file, use it as source_path
        # If multiple files, use the directory
        if len(file_paths) == 1:
            source_path = file_paths[0]
            source_filename = os.path.basename(file_paths[0])
        else:
            source_path = project_dir
            source_filename = "multiple_files"
        
        # Create project record in database
        add_project(
            project_id, 
            request.form.get('name', 'Unnamed Project'),
            request.form.get('description', ''),
            source_filename,
            source_path
        )
        
        flash(f"Project created successfully with {len(file_paths)} files", "success")
        return redirect(url_for('index', project=project_id))
        
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        flash(f"Error creating project: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/scan_project/<project_id>', methods=['POST'])
def scan_project_route(project_id):
    """Scan source code to identify UI elements"""
    try:
        project = get_project(project_id)
        if not project:
            flash("Project not found", "error")
            return redirect(url_for('index'))
        
        elements = scan_source_code(project["source_path"])
        
        # Store elements in the database
        save_elements(project_id, elements)
        
        flash(f"Scanned {len(elements)} UI elements", "success")
        return redirect(url_for('index', project=project_id, tab='elements'))
    
    except Exception as e:
        logger.error(f"Error scanning project: {str(e)}")
        flash(f"Error scanning project: {str(e)}", "error")
        return redirect(url_for('index', project=project_id))

@app.route('/generate_pom/<project_id>', methods=['POST'])
def generate_pom_route(project_id):
    """Generate Page Object Model from scanned code"""
    try:
        # Check if project exists
        project = get_project(project_id)
        if not project:
            logger.error(f"Project not found: {project_id}")
            flash("Project not found", "error")
            return redirect(url_for('index'))
        
        logger.info(f"Generating POM for project: {project['name']} (ID: {project_id})")
        
        # Get elements from scan or scan again if not available
        elements = get_elements(project_id)
        if not elements:
            logger.info("No elements found, scanning source code...")
            elements = scan_source_code(project["source_path"])
            save_elements(project_id, elements)
        
        # Generate the POM
        logger.info(f"Generating POM from {len(elements)} elements")
        pom_data = generate_pom(elements, project_id)
        
        # Create POM record in database
        pom_id = str(uuid.uuid4())
        add_pom(pom_id, project_id, pom_data["file_path"], pom_data["elements"])
        
        logger.info(f"POM generated successfully with ID: {pom_id}")
        flash("Page Object Model generated successfully", "success")
        return redirect(url_for('index', project=project_id, tab='pom'))
    
    except Exception as e:
        logger.error(f"Error generating POM: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error generating POM: {str(e)}", "error")
        return redirect(url_for('index', project=project_id))

@app.route('/generate_tests/<project_id>', methods=['POST'])
def generate_tests_route(project_id):
    """Generate test cases from POM"""
    try:
        # First check if project exists
        project = get_project(project_id)
        if not project:
            logger.error(f"Project not found: {project_id}")
            flash("Project not found", "error")
            return redirect(url_for('index'))
        
        logger.info(f"Generating tests for project: {project['name']} (ID: {project_id})")
        
        # Find a valid POM to use
        pom_id = request.form.get('pom_id')
        pom = None
        
        # Check if specified POM exists
        if pom_id:
            pom = get_pom(pom_id)
            if pom and pom["project_id"] == project_id:
                logger.info(f"Using specified POM with ID: {pom_id}")
            else:
                pom = None
        
        # Fallback to first available POM for this project
        if not pom:
            poms = get_poms(project_id)
            if poms:
                pom = poms[0]
                pom_id = pom["id"]
                logger.info(f"Using first available POM with ID: {pom_id}")
        
        # Ensure we have a valid POM
        if not pom:
            logger.error("No valid POM found for test generation")
            flash("No valid POM available. Generate a POM first.", "error")
            return redirect(url_for('index', project=project_id, tab='pom'))
        
        # Generate tests
        logger.info("Generating tests from POM...")
        test_data = generate_tests(pom, project_id)
        
        # Check if test generation was successful
        if test_data.get("success", False) and test_data.get("script_path") and os.path.exists(test_data["script_path"]):
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
            
            logger.info(f"Tests generated successfully with ID: {test_id}")
            flash("Test cases generated successfully", "success")
        else:
            logger.error(f"Test generation failed: {test_data.get('description', 'Unknown error')}")
            flash(f"Test generation warning: {test_data.get('description', 'Failed to generate tests')}", "warning")
        
        # Always return to the project's tests tab, maintaining the project in the URL
        return redirect(url_for('index', project=project_id, tab='tests'))
    
    except Exception as e:
        logger.error(f"Error in generate_tests_route: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error generating tests: {str(e)}", "error")
        # Important: Keep the project ID in the redirect to maintain context
        return redirect(url_for('index', project=project_id))

@app.route('/execute_test/<project_id>/<test_id>', methods=['POST'])
def execute_test_route(project_id, test_id):
    """Execute a test case"""
    try:
        project = get_project(project_id)
        if not project:
            flash("Project not found", "error")
            return redirect(url_for('index'))
        
        test_case = get_test_case(test_id)
        if not test_case or test_case["project_id"] != project_id:
            flash("Test case not found", "error")
            return redirect(url_for('index', project=project_id))
        
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
        
        flash(f"Test execution completed with status: {execution_result['status']}", "info")
        return redirect(url_for('index', project=project_id, tab='executions'))
        
    except Exception as e:
        logger.error(f"Error executing test: {str(e)}")
        flash(f"Error executing test: {str(e)}", "error")
        return redirect(url_for('index', project=project_id))

@app.route('/view_code/<test_id>')
def view_code(test_id):
    """View the test code"""
    try:
        test_case = get_test_case(test_id)
        if not test_case:
            return "Test not found", 404
        
        if not os.path.exists(test_case["script_path"]):
            return "Test script file not found", 404
        
        with open(test_case["script_path"], 'r') as f:
            code_content = f.read()
        return code_content, 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        logger.error(f"Error viewing code: {str(e)}")
        return f"Error reading test code: {str(e)}", 500

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download a file"""
    try:
        directory = os.path.dirname(filename)
        file = os.path.basename(filename)
        return send_from_directory(directory, file, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        flash(f"Error downloading file: {str(e)}", "error")
        return redirect(url_for('index'))

# Additional route for downloading all tests as a ZIP
@app.route('/download_all_tests/<project_id>')
def download_all_tests(project_id):
    """Download all tests for a project as a ZIP file"""
    try:
        project = get_project(project_id)
        if not project:
            flash("Project not found", "error")
            return redirect(url_for('index'))
        
        project_dir = os.path.join(RESULTS_FOLDER, project_id)
        tests_dir = os.path.join(project_dir, "tests")
        
        if not os.path.exists(tests_dir):
            flash("No tests found for this project", "error")
            return redirect(url_for('index', project=project_id, tab='tests'))
        
        # Create a ZIP file of all tests
        zip_path = os.path.join(project_dir, f"all_tests_{project_id}.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Add test files
            for root, dirs, files in os.walk(tests_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_dir)
                    zipf.write(file_path, arcname)
            
            # Also add the page_objects.py file
            page_objects_path = os.path.join(project_dir, "page_objects.py")
            if os.path.exists(page_objects_path):
                zipf.write(page_objects_path, "page_objects.py")
            
            # Add readme with instructions
            readme_content = """# Selenium UI Test Suite

## Setup Instructions
1. Install required packages: `pip install selenium webdriver-manager`
2. Make sure you have Chrome browser installed
3. Run the tests with the test_suite.py file: `python test_suite.py`
## Test Structure
- page_objects.py - Contains the Page Object Models
- tests/ - Directory containing all test files
- test_suite.py - Main test suite that runs all tests
- test_*.py - Individual test files for different features

## Notes
- These tests were automatically generated by UI Test Generator
- Modify the base URL in the page objects if needed
"""
            zipf.writestr("README.md", readme_content)
        
        return send_from_directory(project_dir, f"all_tests_{project_id}.zip", as_attachment=True)
    
    except Exception as e:
        logger.error(f"Error creating test ZIP: {str(e)}")
        flash(f"Error downloading tests: {str(e)}", "error")
        return redirect(url_for('index', project=project_id, tab='tests'))

# Route for exporting POM as CSV
@app.route('/export_pom_csv/<project_id>/<pom_id>')
def export_pom_csv(project_id, pom_id):
    """Export Page Object Model as CSV for easier use in other tools"""
    try:
        project = get_project(project_id)
        if not project:
            flash("Project not found", "error")
            return redirect(url_for('index'))
        
        pom = get_pom(pom_id)
        if not pom or pom["project_id"] != project_id:
            flash("POM not found", "error")
            return redirect(url_for('index', project=project_id))
        
        # Create CSV content
        csv_content = "Page,ElementName,ElementType,Purpose,Selector,SelectorType\n"
        
        # Group elements by page
        page_dict = {}
        for elem in pom["elements"]:
            if elem["type"] == "page":
                page_dict[elem["id"]] = elem["name"]
        
        # Add element rows
        for elem in pom["elements"]:
            if elem["type"] != "page" and "parent_id" in elem:
                page_name = page_dict.get(elem["parent_id"], "Unknown")
                element_name = elem["name"]
                element_type = elem["type"]
                purpose = elem.get("purpose", "unknown")
                selector = elem.get("selector", "")
                selector_type = elem.get("selector_type", "")
                
                # Clean fields for CSV
                csv_content += f"{page_name},{element_name},{element_type},{purpose},\"{selector}\",{selector_type}\n"
        
        # Create CSV file
        project_dir = os.path.join(RESULTS_FOLDER, project_id)
        csv_path = os.path.join(project_dir, f"pom_{pom_id}.csv")
        with open(csv_path, 'w') as f:
            f.write(csv_content)
        
        return send_from_directory(project_dir, f"pom_{pom_id}.csv", as_attachment=True)
    
    except Exception as e:
        logger.error(f"Error exporting POM to CSV: {str(e)}")
        flash(f"Error exporting POM: {str(e)}", "error")
        return redirect(url_for('index', project=project_id, tab='pom'))

@app.route('/api/projects', methods=['GET'])
def api_get_projects():
    try:
        logger.info("GET /api/projects called")
        projects = get_all_projects()
        return jsonify(projects)
    except Exception as e:
        logger.error(f"Error in GET /api/projects: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['GET'])
def api_get_project(project_id):
    try:
        logger.info(f"GET /api/projects/{project_id} called")
        project = get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        return jsonify(project)
    except Exception as e:
        logger.error(f"Error in GET /api/projects/{project_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects', methods=['POST'])
def api_create_project():
    try:
        logger.info("POST /api/projects called")
        logger.debug(f"Request form: {request.form}")
        logger.debug(f"Request files: {request.files}")
        
        if 'file' not in request.files:
            logger.warning("No file part in request")
            return jsonify({"error": "No file part"}), 400
        
        files = request.files.getlist('file')
        if not files or files[0].filename == '':
            logger.warning("No selected file")
            return jsonify({"error": "No selected file"}), 400
        
        project_id = str(uuid.uuid4())
        project_dir = os.path.join(app.config['UPLOAD_FOLDER'], project_id)
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
        add_project(
            project_id, 
            request.form.get('name', 'Unnamed Project'),
            request.form.get('description', ''),
            source_filename,
            source_path
        )
        
        project = get_project(project_id)
        logger.info(f"Project created successfully: {project_id}")
        return jsonify(project), 201
        
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        logger.error(traceback.format_exc())  # Add this to get the full traceback
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_id>/scan', methods=['POST'])
def api_scan_project(project_id):
    try:
        project = get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        
        elements = scan_source_code(project["source_path"])
        
        # Store elements in the database
        save_elements(project_id, elements)
        
        return jsonify({"success": True, "elements_count": len(elements)})
    
    except Exception as e:
        logger.error(f"Error scanning project: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_id>/elements', methods=['GET'])
def api_get_elements(project_id):
    elements = get_elements(project_id)
    return jsonify(elements)

@app.route('/api/projects/<project_id>/pom', methods=['POST'])
def api_generate_pom(project_id):
    try:
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_id>/poms', methods=['GET'])
def api_get_poms(project_id):
    poms = get_poms(project_id)
    return jsonify(poms)

@app.route('/api/projects/<project_id>/tests', methods=['POST'])
def api_generate_tests(project_id):
    try:
        # Check if project exists
        project = get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        
        # Get POM ID from request
        pom_id = request.json.get('pom_id')
        
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_id>/tests', methods=['GET'])
def api_get_tests(project_id):
    tests = get_test_cases(project_id)
    return jsonify(tests)

@app.route('/api/tests/<test_id>/code', methods=['GET'])
def api_view_test_code(test_id):
    try:
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_id>/tests/<test_id>/execute', methods=['POST'])
def api_execute_test(project_id, test_id):
    try:
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_id>/executions', methods=['GET'])
def api_get_executions(project_id):
    executions = get_executions(project_id)
    return jsonify(executions)

@app.route('/api/download/<path:filename>', methods=['GET'])
def api_download_file(filename):
    try:
        directory = os.path.dirname(filename)
        file = os.path.basename(filename)
        return send_from_directory(directory, file, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Create a simple schema.sql file
with open('schema.sql', 'w') as f:
    f.write('''
-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    source_file TEXT,
    source_path TEXT,
    created_at TEXT
);

-- Elements table
CREATE TABLE IF NOT EXISTS elements (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    element_data TEXT,
    created_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects (id)
);

-- POMs table
CREATE TABLE IF NOT EXISTS poms (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    file_path TEXT,
    pom_data TEXT,
    created_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects (id)
);

-- Test cases table
CREATE TABLE IF NOT EXISTS test_cases (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    pom_id TEXT NOT NULL,
    name TEXT,
    script_path TEXT,
    description TEXT,
    created_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects (id),
    FOREIGN KEY (pom_id) REFERENCES poms (id)
);

-- Test executions table
CREATE TABLE IF NOT EXISTS test_executions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    test_id TEXT NOT NULL,
    status TEXT,
    result_data TEXT,
    log_path TEXT,
    executed_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects (id),
    FOREIGN KEY (test_id) REFERENCES test_cases (id)
);
''')

if __name__ == '__main__':
    # Initialize database
    create_db_tables()
    
    # Make sure essential directories exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(RESULTS_FOLDER, exist_ok=True)
    
    logger.info("Starting UI Test Generator application")
    app.run(debug=True, port=5000)