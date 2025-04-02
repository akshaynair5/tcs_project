import { useState } from "react";

const AdminPanel = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadStatus("Please select a file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch("http://127.0.0.1:5000/api/pdf/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      setUploadStatus(data.message || "Upload failed.");
    } catch (error) {
      setUploadStatus("Server error.");
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-100">
      {/* Sidebar */}

      {/* Main Content */}
      <main className="fixed h-[100vh] w-[100vw] top-0 left-0 flex-1 p-10 flex-col items-center justify-items-center">
        <h2 className="text-3xl font-bold mb-6">Admin - Upload PDF</h2>
        <div className="p-6 bg-white shadow-md rounded-lg w-full max-w-lg">
          <input 
            type="file" 
            accept="application/pdf" 
            onChange={handleFileChange} 
            className="mb-4 border p-2 w-full"
          />    
          <button 
            onClick={handleUpload} 
            className="bg-blue-500 text-white px-6 py-2 rounded w-full hover:bg-blue-600 transition"
          >
            Upload PDF
          </button>
          {uploadStatus && (
            <p className="mt-4 text-sm text-gray-700">{uploadStatus}</p>
          )}
        </div>
      </main>
    </div>
  );
};

export default AdminPanel;
