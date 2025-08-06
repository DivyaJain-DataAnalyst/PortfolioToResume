import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    console.log(
      "Received convert-portfolio request:",
      JSON.stringify(body, null, 2)
    );

    const { portfolioUrl, template } = body;

    // Enhanced validation with detailed logging
    if (!portfolioUrl) {
      console.error("Missing portfolioUrl in request");
      return NextResponse.json(
        { error: "Portfolio URL is required" },
        { status: 400 }
      );
    }

    // Validate URL format
    try {
      new URL(portfolioUrl);
    } catch {
      return NextResponse.json(
        { error: "Invalid portfolio URL format" },
        { status: 400 }
      );
    }

    console.log(
      `🔄 Converting portfolio: ${portfolioUrl} with template: ${template}`
    );

    // Call the Flask backend with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout

    const response = await fetch("http://localhost:5000/convert-portfolio", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        portfolioUrl,
        template,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error("Backend error:", errorData);
      throw new Error(errorData.error || "Failed to convert portfolio");
    }

    const data = await response.json();

    console.log(`✅ Portfolio conversion successful for: ${portfolioUrl}`);
    console.log(`📊 Extracted data summary:`, {
      name: data.data?.name,
      skills: data.data?.skills?.length,
      projects: data.data?.projects?.length,
      education: data.data?.education?.length,
      experience: data.data?.experience?.length,
    });

    return NextResponse.json(data);
  } catch (error: any) {
    console.error("Error converting portfolio:", error);

    if (error.name === "AbortError") {
      return NextResponse.json(
        { error: "Request timeout - portfolio conversion took too long" },
        { status: 408 }
      );
    }

    return NextResponse.json(
      { error: error.message || "Failed to convert portfolio" },
      { status: 500 }
    );
  }
}
