"use client";

import { useState } from "react";
import { Upload, Link, Download, FileText, Sparkles } from "lucide-react";
import ResumeEditor from "./components/ResumeEditor";

export default function Home() {
  const [portfolioUrl, setPortfolioUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [resumeData, setResumeData] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState("professional");
  const [error, setError] = useState("");

  const templates = [
    {
      id: "professional",
      name: "Professional Black",
      description: "Clean and professional black design",
    },
    {
      id: "executive",
      name: "Executive Black",
      description: "Premium business black format",
    },
    {
      id: "minimal",
      name: "Minimal Black",
      description: "Simple and elegant black design",
    },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!portfolioUrl.trim()) {
      setError("Please enter a portfolio URL");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const response = await fetch("/api/convert-portfolio", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          portfolioUrl: portfolioUrl.trim(),
          template: selectedTemplate,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to convert portfolio");
      }

      const data = await response.json();
      console.log("Received data from convert-portfolio:", data);

      // Extract the actual resume data from the response
      if (data.success && data.data) {
        setResumeData(data.data);
      } else {
        throw new Error("Invalid response format from server");
      }
    } catch (err: any) {
      setError("Failed to convert portfolio. Please try again.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!resumeData) return;

    try {
      console.log("Sending resume data:", {
        resumeData,
        template: selectedTemplate,
      });

      const response = await fetch("/api/download-resume", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          resumeData,
          template: selectedTemplate,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Server response:", response.status, errorText);
        throw new Error(
          `Failed to generate resume: ${response.status} - ${errorText}`
        );
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `resume-${selectedTemplate}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setError(`Failed to download resume: ${err.message}`);
      console.error("Download error:", err);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <h1 className="text-4xl font-bold text-gray-900">
              Portfolio to Resume
            </h1>
          </div>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Convert your portfolio website into a professional resume with
            multiple templates. Simply provide your portfolio URL and get a
            beautifully formatted resume.
          </p>
        </div>

        {/* Main Form */}
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Portfolio URL Input */}
              <div>
                <label
                  htmlFor="portfolioUrl"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Portfolio URL
                </label>
                <div className="relative">
                  <Link className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="url"
                    id="portfolioUrl"
                    value={portfolioUrl}
                    onChange={(e) => setPortfolioUrl(e.target.value)}
                    placeholder="https://your-portfolio-website.com"
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                    required
                  />
                </div>
              </div>

              {/* Template Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Choose Resume Template
                </label>
                <div className=" grid grid-cols-2 md:grid-cols-4 gap-3 items-center justify-center">
                  {templates.map((template) => (
                    <button
                      key={template.id}
                      type="button"
                      onClick={() => setSelectedTemplate(template.id)}
                      className={`p-4 rounded-lg border-2 transition-all duration-200 ${
                        selectedTemplate === template.id
                          ? "border-blue-500 bg-blue-50 text-blue-700"
                          : "border-gray-200 hover:border-gray-300 bg-gray-50"
                      }`}
                    >
                      <div className="text-sm font-medium">{template.name}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {template.description}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-3 px-6 rounded-lg transition-all duration-200 flex items-center justify-center"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Converting Portfolio...
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5 mr-2" />
                    Convert to Resume
                  </>
                )}
              </button>
            </form>
            {/* Error Message */}
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}
          </div>

          {/* Results Section */}
          {resumeData && (
            <ResumeEditor
              initialData={resumeData}
              onSave={(updatedData) => setResumeData(updatedData)}
              onDownload={handleDownload}
              selectedTemplate={selectedTemplate}
              portfolioUrl={portfolioUrl}
            />
          )}
        </div>

        {/* Features Section */}
        <div className="max-w-6xl mx-auto mt-16">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Why Choose Our Converter?
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Link className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Easy URL Input
              </h3>
              <p className="text-gray-600">
                Simply paste your portfolio URL and let our AI extract all the
                relevant information.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Multiple Templates
              </h3>
              <p className="text-gray-600">
                Choose from professional, creative, minimal, and classic resume
                templates.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Download className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Instant Download
              </h3>
              <p className="text-gray-600">
                Get your professionally formatted resume as a PDF ready for job
                applications.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
