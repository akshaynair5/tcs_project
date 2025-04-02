import { useState } from "react";

const FileUpload = () => {
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
    <div className="p-4 border rounded-lg">
      <input type="file" accept="application/pdf" onChange={handleFileChange} />
      <button onClick={handleUpload} className="bg-blue-500 text-white px-4 py-2 rounded">
        Upload PDF
      </button>
      <p>{uploadStatus}</p>
    </div>
  );
};

export default FileUpload;
