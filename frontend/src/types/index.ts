export interface Project {
    id: string;
    name: string;
    description: string;
    source_file: string;
    source_path: string;
    created_at: string;
  }
  
  export interface Element {
    id: string;
    name: string;
    type: string;
    purpose?: string;
    selector: string;
    selector_type: string;
    properties: {
      text: string;
      attributes: Record<string, string>;
      is_visible: boolean;
    };
  }
  
  export interface PomElement extends Element {
    parent_id?: string;
    children?: string[];
  }
  
  export interface Pom {
    id: string;
    project_id: string;
    file_path: string;
    elements: PomElement[];
    created_at: string;
    code_path?: string;
  }
  
  export interface TestCase {
    id: string;
    project_id: string;
    pom_id: string;
    name: string;
    script_path: string;
    description: string;
    created_at: string;
  }
  
  export interface TestResult {
    name: string;
    status: 'PASSED' | 'FAILED' | 'ERROR' | 'SKIPPED';
  }
  
  export interface Execution {
    id: string;
    project_id: string;
    test_id: string;
    status: 'SUCCESS' | 'FAILURE' | 'ERROR' | 'TIMEOUT';
    result: {
      return_code: number;
      tests: TestResult[];
      log: string;
    };
    log_path: string;
    executed_at: string;
  }
  
  export interface ProjectWithDetails extends Project {
    elements: Element[];
    poms: Pom[];
    tests: TestCase[];
    executions: Execution[];
  }