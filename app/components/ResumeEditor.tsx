"use client";

import { useState, useEffect } from "react";
import {
  Edit3,
  Download,
  Eye,
  Mail,
  Phone,
  Github,
  Linkedin,
  Globe,
  Award,
  GraduationCap,
  Briefcase,
  Code,
  Star,
  Plus,
  Trash2,
  ExternalLink,
} from "lucide-react";
import toast, { Toaster } from "react-hot-toast";

interface ResumeData {
  name: string;
  title: string;
  about: string;
  Contact_Info: {
    email: string;
    phone: string;
    github: string;
    linkedin: string;
  };
  skills: {
    [key: string]: string[];
  };
  projects: Array<{
    name: string;
    description: string;
    technologies: string[];
    link?: string;
    github?: string;
    demo?: string;
  }>;
  education: Array<{
    degree: string;
    institution: string;
    duration: string;
    gpa: string;
  }>;
  experience: Array<{
    position: string;
    company: string;
    duration: string;
    skills: string[];
    description: string;
  }>;
  achievements: Array<{
    name: string;
    institution: string;
    description: string;
  }>;
}

interface ResumeEditorProps {
  initialData: ResumeData;
  onSave: (data: ResumeData) => void;
  onDownload: () => void;
  selectedTemplate: string;
  portfolioUrl?: string;
}

export default function ResumeEditor({
  initialData,
  onSave,
  onDownload,
  selectedTemplate,
  portfolioUrl,
}: ResumeEditorProps) {
  // Ensure all fields have proper default values to prevent controlled/uncontrolled input issues
  const sanitizedInitialData: ResumeData = {
    name: initialData.name || "",
    title: initialData.title || "",
    about: initialData.about || "",
    Contact_Info: {
      email: initialData.Contact_Info?.email || "",
      phone: initialData.Contact_Info?.phone || "",
      github: initialData.Contact_Info?.github || "",
      linkedin: initialData.Contact_Info?.linkedin || "",
    },
    skills: initialData.skills || {},
    projects:
      initialData.projects?.map((project) => ({
        name: project.name || "",
        description: project.description || "",
        technologies: Array.isArray(project.technologies)
          ? project.technologies
          : [],
        link: project.link || "",
        github: project.github || "",
        demo: project.demo || "",
      })) || [],
    education:
      initialData.education?.map((edu) => ({
        degree: edu.degree || "",
        institution: edu.institution || "",
        duration: edu.duration || "",
        gpa: edu.gpa || "",
      })) || [],
    experience:
      initialData.experience?.map((exp) => ({
        position: exp.position || "",
        company: exp.company || "",
        duration: exp.duration || "",
        skills: Array.isArray(exp.skills) ? exp.skills : [],
        description: exp.description || "",
      })) || [],
    achievements:
      initialData.achievements?.map((achievement) => ({
        name: achievement.name || "",
        institution: achievement.institution || "",
        description: achievement.description || "",
      })) || [],
  };

  const [resumeData, setResumeData] =
    useState<ResumeData>(sanitizedInitialData);
  const [isEditing, setIsEditing] = useState(false);

  // State for managing input values for array fields
  const [arrayInputValues, setArrayInputValues] = useState<{
    [key: string]: string;
  }>({});

  // Auto-save functionality
  useEffect(() => {
    if (isEditing) {
      const autoSaveTimer = setTimeout(() => {
        onSave(resumeData);
        toast.success("Changes auto-saved!", {
          duration: 2000,
          position: "top-right",
        });
      }, 2000);

      return () => clearTimeout(autoSaveTimer);
    }
  }, [resumeData, isEditing, onSave]);

  // Initialize array input values when component mounts
  useEffect(() => {
    const newInputValues: { [key: string]: string } = {};

    // Initialize skills
    Object.entries(resumeData.skills).forEach(([category, skills]) => {
      const fieldKey = `${category}-${JSON.stringify(skills)}`;
      newInputValues[fieldKey] = Array.isArray(skills) ? skills.join(", ") : "";
    });

    // Initialize project technologies
    resumeData.projects.forEach((project, index) => {
      const fieldKey = `Technologies-${JSON.stringify(project.technologies)}`;
      newInputValues[fieldKey] = Array.isArray(project.technologies)
        ? project.technologies.join(", ")
        : "";
    });

    // Initialize experience skills
    resumeData.experience.forEach((exp, index) => {
      const fieldKey = `Skills-${JSON.stringify(exp.skills)}`;
      newInputValues[fieldKey] = Array.isArray(exp.skills)
        ? exp.skills.join(", ")
        : "";
    });

    setArrayInputValues(newInputValues);
  }, []); // Only run once on mount

  const handleFieldChange = (
    section: string,
    field: string,
    value: any,
    index?: number
  ) => {
    setResumeData((prev) => {
      const newData = { ...prev };

      if (index !== undefined) {
        // Handle array fields (projects, education, experience, achievements)
        if (section === "projects" && Array.isArray(newData.projects)) {
          const array = [...newData.projects];
          array[index] = { ...array[index], [field]: value };
          newData.projects = array;
        } else if (
          section === "education" &&
          Array.isArray(newData.education)
        ) {
          const array = [...newData.education];
          array[index] = { ...array[index], [field]: value };
          newData.education = array;
        } else if (
          section === "experience" &&
          Array.isArray(newData.experience)
        ) {
          const array = [...newData.experience];
          array[index] = { ...array[index], [field]: value };
          newData.experience = array;
        } else if (
          section === "achievements" &&
          Array.isArray(newData.achievements)
        ) {
          const array = [...newData.achievements];
          array[index] = { ...array[index], [field]: value };
          newData.achievements = array;
        }
      } else {
        // Handle object fields
        if (section === "Contact_Info") {
          newData.Contact_Info = { ...newData.Contact_Info, [field]: value };
        } else if (section === "skills") {
          newData.skills = { ...newData.skills, [field]: value };
        } else if (section === "name") {
          newData.name = value;
        } else if (section === "title") {
          newData.title = value;
        } else if (section === "about") {
          newData.about = value;
        }
      }

      return newData;
    });

    // Auto-save to parent component
    setTimeout(() => {
      onSave(resumeData);
    }, 100);

    // Show real-time update notification
    toast.success("Updated!", {
      duration: 1000,
      position: "top-right",
    });
  };

  const addSkillCategory = () => {
    const category = prompt("Enter skill category name:");
    if (category && category.trim()) {
      setResumeData((prev) => ({
        ...prev,
        skills: { ...prev.skills, [category.trim()]: [] },
      }));
      toast.success(`Added ${category} category!`);
    }
  };

  const removeSkillCategory = (category: string) => {
    setResumeData((prev) => {
      const newSkills = { ...prev.skills };
      delete newSkills[category];
      return { ...prev, skills: newSkills };
    });
    toast.success(`Removed ${category} category!`);
  };

  const addProject = () => {
    setResumeData((prev) => ({
      ...prev,
      projects: [
        ...prev.projects,
        {
          name: "",
          description: "",
          technologies: [],
          github: "",
          demo: "",
        },
      ],
    }));
    toast.success("Added new project!");
  };

  const removeProject = (index: number) => {
    setResumeData((prev) => ({
      ...prev,
      projects: prev.projects.filter((_, i) => i !== index),
    }));
    toast.success("Removed project!");
  };

  const addEducation = () => {
    setResumeData((prev) => ({
      ...prev,
      education: [
        ...prev.education,
        {
          degree: "",
          institution: "",
          duration: "",
          gpa: "",
        },
      ],
    }));
    toast.success("Added new education!");
  };

  const removeEducation = (index: number) => {
    setResumeData((prev) => ({
      ...prev,
      education: prev.education.filter((_, i) => i !== index),
    }));
    toast.success("Removed education!");
  };

  const addExperience = () => {
    setResumeData((prev) => ({
      ...prev,
      experience: [
        ...prev.experience,
        {
          position: "",
          company: "",
          duration: "",
          skills: [],
          description: "",
        },
      ],
    }));
    toast.success("Added new experience!");
  };

  const removeExperience = (index: number) => {
    setResumeData((prev) => ({
      ...prev,
      experience: prev.experience.filter((_, i) => i !== index),
    }));
    toast.success("Removed experience!");
  };

  const addAchievement = () => {
    setResumeData((prev) => ({
      ...prev,
      achievements: [
        ...prev.achievements,
        {
          name: "",
          institution: "",
          description: "",
        },
      ],
    }));
    toast.success("Added new achievement!");
  };

  const removeAchievement = (index: number) => {
    setResumeData((prev) => ({
      ...prev,
      achievements: prev.achievements.filter((_, i) => i !== index),
    }));
    toast.success("Removed achievement!");
  };

  const renderField = (
    label: string,
    value: string,
    onChange: (value: string) => void,
    multiline = false,
    placeholder = ""
  ) => (
    <div className="mb-3">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      {multiline ? (
        <textarea
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
          rows={3}
          placeholder={placeholder}
        />
      ) : (
        <input
          type="text"
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
          placeholder={placeholder}
        />
      )}
    </div>
  );

  const renderArrayField = (
    label: string,
    value: string[],
    onChange: (value: string[]) => void,
    placeholder = "Enter items separated by commas"
  ) => {
    // Ensure value is always an array
    const safeValue = Array.isArray(value) ? value : [];

    // Create a unique key for this field
    const fieldKey = `${label}-${JSON.stringify(safeValue)}`;

    // Get or initialize the input value from component state
    const inputValue = arrayInputValues[fieldKey] ?? safeValue.join(", ");

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;

      // Update the input value in component state immediately
      setArrayInputValues((prev) => ({
        ...prev,
        [fieldKey]: newValue,
      }));

      // Don't parse immediately - let user type freely
      // Only parse when they finish typing (on blur)
    };

    const handleBlur = () => {
      // Only parse when user finishes typing
      const items = inputValue
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      // Update the parent state with parsed items
      onChange(items);

      // Clean up the display value
      const cleanValue = items.join(", ");
      setArrayInputValues((prev) => ({
        ...prev,
        [fieldKey]: cleanValue,
      }));
    };

    return (
      <div className="mb-3">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
        <input
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onBlur={handleBlur}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
          placeholder={placeholder}
        />
        <p className="text-xs text-gray-500 mt-1">
          Type freely with spaces and commas (e.g., Backend: Node.js, Express,
          MongoDB)
        </p>
      </div>
    );
  };

  const renderResumePreview = () => (
    <div className="bg-white border border-gray-200 rounded-lg p-8 max-w-4xl mx-auto shadow-lg">
      {/* Header */}
      <div className="text-center mb-8 border-b-2 border-gray-300 pb-6">
        <h1 className="text-4xl font-bold text-gray-900 mb-3">
          {resumeData.name}
        </h1>
        <p className="text-2xl text-gray-700 mb-6">{resumeData.title}</p>

        {/* Contact Info with Icons Only */}
        <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-600">
          {resumeData.Contact_Info.email && (
            <a
              href={`mailto:${resumeData.Contact_Info.email}`}
              className="flex items-center hover:text-blue-600 transition-colors duration-200"
              title={resumeData.Contact_Info.email}
            >
              <Mail className="w-5 h-5 mr-2 text-blue-600" />
              Email
            </a>
          )}
          {resumeData.Contact_Info.phone && (
            <a
              href={`tel:${resumeData.Contact_Info.phone}`}
              className="flex items-center hover:text-green-600 transition-colors duration-200"
              title={resumeData.Contact_Info.phone}
            >
              <Phone className="w-5 h-5 mr-2 text-green-600" />
              Phone
            </a>
          )}
          {resumeData.Contact_Info.github && (
            <a
              href={
                resumeData.Contact_Info.github.startsWith("http")
                  ? resumeData.Contact_Info.github
                  : `https://${resumeData.Contact_Info.github}`
              }
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center hover:text-gray-800 transition-colors duration-200"
              title="GitHub Profile"
            >
              <Github className="w-5 h-5 mr-2 text-gray-800" />
              GitHub
            </a>
          )}
          {resumeData.Contact_Info.linkedin && (
            <a
              href={
                resumeData.Contact_Info.linkedin.startsWith("http")
                  ? resumeData.Contact_Info.linkedin
                  : `https://${resumeData.Contact_Info.linkedin}`
              }
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center hover:text-blue-700 transition-colors duration-200"
              title="LinkedIn Profile"
            >
              <Linkedin className="w-5 h-5 mr-2 text-blue-700" />
              LinkedIn
            </a>
          )}
        </div>
      </div>

      {/* Objective */}
      {resumeData.about && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center border-b border-gray-300 pb-2">
            <Star className="w-6 h-6 mr-3 text-blue-600" />
            Objective
          </h2>
          <p className="text-gray-700 leading-relaxed text-lg">
            {resumeData.about}
          </p>
        </div>
      )}

      {/* Skills */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center border-b border-gray-300 pb-2">
          <Code className="w-6 h-6 mr-3 text-blue-600" />
          Skills
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(resumeData.skills).map(([category, skills]) => (
            <div
              key={category}
              className="bg-gray-50 p-4 rounded-lg border border-gray-200"
            >
              <h3 className="font-bold text-gray-900 mb-3 text-lg">
                {category}
              </h3>
              <p className="text-gray-700 text-base">
                {Array.isArray(skills) ? skills.join(", ") : ""}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Projects */}
      {resumeData.projects.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center border-b border-gray-300 pb-2">
            <Globe className="w-6 h-6 mr-3 text-green-600" />
            Projects
          </h2>
          <div className="space-y-6">
            {resumeData.projects.map((project, index) => (
              <div
                key={index}
                className="border-l-4 border-green-500 pl-6 bg-gray-50 p-4 rounded-r-lg"
              >
                <h3 className="font-bold text-gray-900 text-xl mb-2">
                  {project.name}
                </h3>
                <p className="text-gray-600 text-base mb-3 font-medium">
                  {Array.isArray(project.technologies)
                    ? project.technologies.join(", ")
                    : ""}
                </p>
                <p className="text-gray-700 mb-4 text-base leading-relaxed">
                  {project.description}
                </p>
                {(project.github || project.demo) && (
                  <div className="flex gap-6 text-base mt-3">
                    {project.github && (
                      <a
                        href={project.github}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 transition-colors duration-200 flex items-center font-medium"
                        title="View on GitHub"
                      >
                        <Github className="w-5 h-5 mr-2" />
                        GitHub
                      </a>
                    )}
                    {project.demo && (
                      <a
                        href={project.demo}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-green-600 hover:text-green-800 transition-colors duration-200 flex items-center font-medium"
                        title="Live Demo"
                      >
                        <Globe className="w-5 h-5 mr-2" />
                        Live Demo
                      </a>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Education */}
      {resumeData.education.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center border-b border-gray-300 pb-2">
            <GraduationCap className="w-6 h-6 mr-3 text-purple-600" />
            Education
          </h2>
          <div className="space-y-4">
            {resumeData.education.map((edu, index) => (
              <div
                key={index}
                className="flex justify-between items-start bg-gray-50 p-4 rounded-lg border border-gray-200"
              >
                <div>
                  <h3 className="font-bold text-gray-900 text-lg">
                    {edu.degree}
                  </h3>
                  <p className="text-gray-600 text-base">{edu.institution}</p>
                </div>
                <div className="text-right text-base text-gray-600">
                  <p className="font-medium">{edu.duration}</p>
                  <p>GPA: {edu.gpa}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Experience */}
      {resumeData.experience.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center border-b border-gray-300 pb-2">
            <Briefcase className="w-6 h-6 mr-3 text-orange-600" />
            Experience
          </h2>
          <div className="space-y-6">
            {resumeData.experience.map((exp, index) => (
              <div
                key={index}
                className="border-l-4 border-orange-500 pl-6 bg-gray-50 p-4 rounded-r-lg"
              >
                <div className="flex justify-between items-start mb-3">
                  <h3 className="font-bold text-gray-900 text-xl">
                    {exp.position}
                  </h3>
                  <span className="text-base text-gray-600 font-medium">
                    {exp.duration}
                  </span>
                </div>
                <p className="text-gray-600 text-lg mb-3 font-medium">
                  {exp.company}
                </p>
                <p className="text-gray-700 mb-3 text-base leading-relaxed">
                  {exp.description}
                </p>
                <p className="text-sm text-gray-600 font-medium">
                  Skills:{" "}
                  {Array.isArray(exp.skills) ? exp.skills.join(", ") : ""}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Achievements */}
      {resumeData.achievements.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center border-b border-gray-300 pb-2">
            <Award className="w-6 h-6 mr-3 text-yellow-600" />
            Achievements
          </h2>
          <div className="space-y-4">
            {resumeData.achievements.map((achievement, index) => (
              <div
                key={index}
                className="bg-gray-50 p-4 rounded-lg border border-gray-200"
              >
                <h3 className="font-bold text-gray-900 text-lg mb-2">
                  {achievement.name}
                </h3>
                <p className="text-gray-600 text-base mb-2">
                  {achievement.institution}
                </p>
                <p className="text-gray-700 text-base">
                  {achievement.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="bg-white rounded-2xl shadow-xl p-8">
      <Toaster />

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Resume Editor</h2>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <button
                onClick={() => setIsEditing(false)}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
              >
                <Eye className="w-4 h-4 mr-2" />
                Preview Resume
              </button>
              <button
                onClick={onDownload}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200"
              >
                <Download className="w-4 h-4 mr-2" />
                Download PDF
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
              >
                <Edit3 className="w-4 h-4 mr-2" />
                Edit Resume
              </button>
              <button
                onClick={onDownload}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200"
              >
                <Download className="w-4 h-4 mr-2" />
                Download PDF
              </button>
            </>
          )}
        </div>
      </div>

      {isEditing ? (
        <div className="space-y-6">
          {/* Basic Information */}
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
              <Star className="w-5 h-5 mr-2 text-blue-600" />
              Basic Information
            </h3>
            {renderField("Name", resumeData.name, (value) =>
              handleFieldChange("name", "name", value)
            )}
            {renderField("Title", resumeData.title, (value) =>
              handleFieldChange("title", "title", value)
            )}
            {renderField(
              "About/Objective",
              resumeData.about,
              (value) => handleFieldChange("about", "about", value),
              true,
              "Write a professional summary about yourself..."
            )}
          </div>

          {/* Contact Information */}
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
              <Mail className="w-5 h-5 mr-2 text-blue-600" />
              Contact Information
            </h3>
            {renderField("Email", resumeData.Contact_Info.email, (value) =>
              handleFieldChange("Contact_Info", "email", value)
            )}
            {renderField("Phone", resumeData.Contact_Info.phone, (value) =>
              handleFieldChange("Contact_Info", "phone", value)
            )}
            {renderField("GitHub", resumeData.Contact_Info.github, (value) =>
              handleFieldChange("Contact_Info", "github", value)
            )}
            {renderField(
              "LinkedIn",
              resumeData.Contact_Info.linkedin,
              (value) => handleFieldChange("Contact_Info", "linkedin", value)
            )}
          </div>

          {/* Skills */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <Code className="w-5 h-5 mr-2 text-blue-600" />
                Skills
              </h3>
              <button
                onClick={addSkillCategory}
                className="flex items-center px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors duration-200"
              >
                <Plus className="w-3 h-3 mr-1" />
                Add Category
              </button>
            </div>
            {Object.entries(resumeData.skills).map(([category, skills]) => (
              <div
                key={category}
                className="mb-4 p-3 border border-gray-200 rounded-lg"
              >
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">
                    {category}
                  </label>
                  <button
                    onClick={() => removeSkillCategory(category)}
                    className="text-red-600 hover:text-red-800 transition-colors duration-200"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                {renderArrayField(
                  category,
                  Array.isArray(skills) ? skills : [],
                  (value) => {
                    console.log(`Updating skills for ${category}:`, value); // Debug log
                    handleFieldChange("skills", category, value);
                  },
                  "Enter skills separated by commas"
                )}
              </div>
            ))}
          </div>

          {/* Projects */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <Globe className="w-5 h-5 mr-2 text-green-600" />
                Projects
              </h3>
              <button
                onClick={addProject}
                className="flex items-center px-3 py-1 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors duration-200"
              >
                <Plus className="w-3 h-3 mr-1" />
                Add Project
              </button>
            </div>
            {resumeData.projects.map((project, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4 mb-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium">Project {index + 1}</h4>
                  <button
                    onClick={() => removeProject(index)}
                    className="text-red-600 hover:text-red-800 transition-colors duration-200"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                {renderField("Project Name", project.name, (value) =>
                  handleFieldChange("projects", "name", value, index)
                )}
                {renderField(
                  "Description",
                  project.description,
                  (value) =>
                    handleFieldChange("projects", "description", value, index),
                  true
                )}
                {renderArrayField(
                  "Technologies",
                  Array.isArray(project.technologies)
                    ? project.technologies
                    : [],
                  (value) => {
                    console.log(
                      `Updating technologies for project ${index}:`,
                      value
                    ); // Debug log
                    handleFieldChange("projects", "technologies", value, index);
                  },
                  "Enter technologies separated by commas"
                )}
                {renderField("GitHub Link", project.github || "", (value) =>
                  handleFieldChange("projects", "github", value, index)
                )}
                {renderField("Demo Link", project.demo || "", (value) =>
                  handleFieldChange("projects", "demo", value, index)
                )}
              </div>
            ))}
          </div>

          {/* Education */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <GraduationCap className="w-5 h-5 mr-2 text-purple-600" />
                Education
              </h3>
              <button
                onClick={addEducation}
                className="flex items-center px-3 py-1 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors duration-200"
              >
                <Plus className="w-3 h-3 mr-1" />
                Add Education
              </button>
            </div>
            {resumeData.education.map((edu, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4 mb-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium">Education {index + 1}</h4>
                  <button
                    onClick={() => removeEducation(index)}
                    className="text-red-600 hover:text-red-800 transition-colors duration-200"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                {renderField("Degree", edu.degree, (value) =>
                  handleFieldChange("education", "degree", value, index)
                )}
                {renderField("Institution", edu.institution, (value) =>
                  handleFieldChange("education", "institution", value, index)
                )}
                {renderField("Duration", edu.duration, (value) =>
                  handleFieldChange("education", "duration", value, index)
                )}
                {renderField("GPA", edu.gpa, (value) =>
                  handleFieldChange("education", "gpa", value, index)
                )}
              </div>
            ))}
          </div>

          {/* Experience */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <Briefcase className="w-5 h-5 mr-2 text-orange-600" />
                Experience
              </h3>
              <button
                onClick={addExperience}
                className="flex items-center px-3 py-1 text-sm bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors duration-200"
              >
                <Plus className="w-3 h-3 mr-1" />
                Add Experience
              </button>
            </div>
            {resumeData.experience.map((exp, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4 mb-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium">Experience {index + 1}</h4>
                  <button
                    onClick={() => removeExperience(index)}
                    className="text-red-600 hover:text-red-800 transition-colors duration-200"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                {renderField("Position", exp.position, (value) =>
                  handleFieldChange("experience", "position", value, index)
                )}
                {renderField("Company", exp.company, (value) =>
                  handleFieldChange("experience", "company", value, index)
                )}
                {renderField("Duration", exp.duration, (value) =>
                  handleFieldChange("experience", "duration", value, index)
                )}
                {renderArrayField(
                  "Skills",
                  Array.isArray(exp.skills) ? exp.skills : [],
                  (value) => {
                    console.log(
                      `Updating skills for experience ${index}:`,
                      value
                    ); // Debug log
                    handleFieldChange("experience", "skills", value, index);
                  },
                  "Enter skills separated by commas"
                )}
                {renderField(
                  "Description",
                  exp.description,
                  (value) =>
                    handleFieldChange(
                      "experience",
                      "description",
                      value,
                      index
                    ),
                  true
                )}
              </div>
            ))}
          </div>

          {/* Achievements */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <Award className="w-5 h-5 mr-2 text-yellow-600" />
                Achievements
              </h3>
              <button
                onClick={addAchievement}
                className="flex items-center px-3 py-1 text-sm bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors duration-200"
              >
                <Plus className="w-3 h-3 mr-1" />
                Add Achievement
              </button>
            </div>
            {resumeData.achievements.map((achievement, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4 mb-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium">Achievement {index + 1}</h4>
                  <button
                    onClick={() => removeAchievement(index)}
                    className="text-red-600 hover:text-red-800 transition-colors duration-200"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                {renderField("Achievement Name", achievement.name, (value) =>
                  handleFieldChange("achievements", "name", value, index)
                )}
                {renderField("Institution", achievement.institution, (value) =>
                  handleFieldChange("achievements", "institution", value, index)
                )}
                {renderField(
                  "Description",
                  achievement.description,
                  (value) =>
                    handleFieldChange(
                      "achievements",
                      "description",
                      value,
                      index
                    ),
                  true
                )}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex justify-center">{renderResumePreview()}</div>
      )}
    </div>
  );
}
