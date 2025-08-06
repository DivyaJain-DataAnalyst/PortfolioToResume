import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    console.log("Received request body:", JSON.stringify(body, null, 2));

    const { resumeData, template } = body;

    // Enhanced validation with detailed logging
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

    console.log(
      `🔄 Generating PDF resume for: ${resumeData.name} with template: ${template}`
    );

    // Call the Flask backend with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 45000); // 45 second timeout

    const response = await fetch("http://localhost:5000/generate-resume-pdf", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        resumeData,
        template,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error("PDF generation error:", errorData);
      throw new Error(errorData.error || "Failed to generate resume PDF");
    }

    const pdfBuffer = await response.arrayBuffer();

    console.log(`✅ PDF generation successful: ${pdfBuffer.byteLength} bytes`);

    return new NextResponse(pdfBuffer, {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="professional-resume-${template}.pdf"`,
        "Content-Length": pdfBuffer.byteLength.toString(),
      },
    });
  } catch (error: any) {
    console.error("Error generating resume PDF:", error);

    if (error.name === "AbortError") {
      return NextResponse.json(
        { error: "Request timeout - PDF generation took too long" },
        { status: 408 }
      );
    }

    return NextResponse.json(
      { error: error.message || "Failed to generate resume PDF" },
      { status: 500 }
    );
  }
}
