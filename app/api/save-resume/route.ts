import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    console.log("Received save-resume request:", JSON.stringify(body, null, 2));

    const { resumeData, template, portfolioUrl } = body;

    // Enhanced validation
    if (!resumeData) {
      console.error("Missing resumeData in request");
      return NextResponse.json(
        { error: "Resume data is required" },
        { status: 400 }
      );
    }

    if (!resumeData.name) {
      console.error("Missing name in resumeData:", resumeData);
      return NextResponse.json(
        { error: "Resume data must include a name" },
        { status: 400 }
      );
    }

    // Create unique ID for the resume
    const resumeId = `resume_${Date.now()}_${Math.random()
      .toString(36)
      .substr(2, 9)}`;

    // Create resume data object
    const resumeToSave = {
      id: resumeId,
      name: resumeData.name,
      template: template || "professional",
      portfolioUrl: portfolioUrl || "",
      data: resumeData,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    // Ensure uploads directory exists
    const uploadsDir = path.join(process.cwd(), "uploads");
    if (!fs.existsSync(uploadsDir)) {
      fs.mkdirSync(uploadsDir, { recursive: true });
    }

    // Save resume data to file
    const resumeFilePath = path.join(uploadsDir, `${resumeId}.json`);
    fs.writeFileSync(resumeFilePath, JSON.stringify(resumeToSave, null, 2));

    console.log(`✅ Resume saved successfully: ${resumeId}`);

    return NextResponse.json({
      success: true,
      message: "Resume saved successfully",
      data: {
        resumeId,
        name: resumeData.name,
        template,
        savedAt: new Date().toISOString(),
      },
    });
  } catch (error: any) {
    console.error("Error saving resume:", error);

    return NextResponse.json(
      { error: error.message || "Failed to save resume" },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const resumeId = searchParams.get("id");

    if (!resumeId) {
      return NextResponse.json(
        { error: "Resume ID is required" },
        { status: 400 }
      );
    }

    // Ensure uploads directory exists
    const uploadsDir = path.join(process.cwd(), "uploads");
    if (!fs.existsSync(uploadsDir)) {
      return NextResponse.json(
        { error: "No saved resumes found" },
        { status: 404 }
      );
    }

    // Load resume data from file
    const resumeFilePath = path.join(uploadsDir, `${resumeId}.json`);

    if (!fs.existsSync(resumeFilePath)) {
      return NextResponse.json({ error: "Resume not found" }, { status: 404 });
    }

    const resumeData = JSON.parse(fs.readFileSync(resumeFilePath, "utf8"));

    console.log(`✅ Resume loaded successfully: ${resumeId}`);

    return NextResponse.json({
      success: true,
      data: resumeData,
    });
  } catch (error: any) {
    console.error("Error loading resume:", error);

    return NextResponse.json(
      { error: error.message || "Failed to load resume" },
      { status: 500 }
    );
  }
}
