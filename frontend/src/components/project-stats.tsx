import { Search, Layers, FileCode } from 'lucide-react';

interface ProjectStatsProps {
  elementCount: number;
  pomCount: number;
  testCount: number;
  onScanElements: () => void;
  onGeneratePom: () => void;
  onGenerateTests: () => void;
  loading: boolean;
}

export function ProjectStats({
  elementCount,
  pomCount,
  testCount,
  onScanElements,
  onGeneratePom,
  onGenerateTests,
  loading
}: ProjectStatsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
      <div className="border rounded-lg shadow-sm hover-lift">
        <div className="p-4 text-center">
          <div className="w-14 h-14 bg-purple-600 text-white rounded-full flex items-center justify-center mx-auto mb-3">
            <Search className="h-6 w-6" />
          </div>
          <h3 className="text-lg font-medium">UI Elements</h3>
          <div className="text-4xl font-bold text-purple-600 my-2">{elementCount}</div>
          <p className="text-gray-500 mb-4">Elements detected</p>
          <button 
            className="w-full bg-purple-600 text-white py-2 px-4 rounded-lg flex items-center justify-center disabled:opacity-50"
            onClick={onScanElements}
            disabled={loading}
          >
            <Search className="mr-2 h-4 w-4" />
            Scan UI Elements
          </button>
        </div>
      </div>

      <div className="border rounded-lg shadow-sm hover-lift">
        <div className="p-4 text-center">
          <div className="w-14 h-14 bg-purple-600 text-white rounded-full flex items-center justify-center mx-auto mb-3">
            <Layers className="h-6 w-6" />
          </div>
          <h3 className="text-lg font-medium">Page Objects</h3>
          <div className="text-4xl font-bold text-purple-600 my-2">{pomCount}</div>
          <p className="text-gray-500 mb-4">POMs created</p>
          <button 
            className={`w-full py-2 px-4 rounded-lg flex items-center justify-center disabled:opacity-50 ${
              elementCount ? "bg-purple-600 text-white" : "bg-gray-200 text-gray-500"
            }`}
            onClick={onGeneratePom}
            disabled={!elementCount || loading}
          >
            <Layers className="mr-2 h-4 w-4" />
            Generate POM
          </button>
        </div>
      </div>

      <div className="border rounded-lg shadow-sm hover-lift">
        <div className="p-4 text-center">
          <div className="w-14 h-14 bg-purple-600 text-white rounded-full flex items-center justify-center mx-auto mb-3">
            <FileCode className="h-6 w-6" />
          </div>
          <h3 className="text-lg font-medium">Test Cases</h3>
          <div className="text-4xl font-bold text-purple-600 my-2">{testCount}</div>
          <p className="text-gray-500 mb-4">Tests created</p>
          <button 
            className={`w-full py-2 px-4 rounded-lg flex items-center justify-center disabled:opacity-50 ${
              pomCount ? "bg-purple-600 text-white" : "bg-gray-200 text-gray-500"
            }`}
            onClick={onGenerateTests}
            disabled={!pomCount || loading}
          >
            <FileCode className="mr-2 h-4 w-4" />
            Generate Tests
          </button>
        </div>
      </div>
    </div>
  );
}