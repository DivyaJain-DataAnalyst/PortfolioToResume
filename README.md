# Portfolio to Resume Converter

A professional web application that converts portfolio websites into beautifully formatted, professional black resumes. The system uses AI-powered data extraction and generates high-quality PDF resumes with a clean, professional design.

## ✨ Features

### 🎯 Core Functionality

- **Portfolio URL Input**: Simply paste your portfolio URL and let AI extract all relevant information
- **Professional Black Templates**: Clean, professional black resume designs
- **Real-time Editing**: Edit all resume sections with live preview
- **Comma-separated Input**: Easy input for skills, technologies, and other lists
- **Icon-only Links**: Professional display of contact links (no URLs shown)
- **PDF Download**: Generate high-quality professional PDF resumes

### 🛠️ Technical Features

- **AI-Powered Extraction**: Uses GROQ and Gemini AI for intelligent data extraction
- **LaTeX Generation**: Professional LaTeX-based PDF generation
- **Fallback System**: ReportLab fallback for reliable PDF creation
- **Responsive Design**: Works on all devices
- **Auto-save**: Automatic saving of changes

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- LaTeX installation (optional, fallback available)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd PortToResume
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**

   ```bash
   npm install
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:

   ```env
   GROQ_API_KEY=your_groq_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

5. **Start the Flask backend**

   ```bash
   python app.py
   ```

6. **Start the Next.js frontend**

   ```bash
   npm run dev
   ```

7. **Open your browser**
   Navigate to `http://localhost:3000`

## 📋 How to Use

### 1. Portfolio Conversion

1. Enter your portfolio URL in the input field
2. Select a professional black template
3. Click "Convert to Resume"
4. Wait for AI to extract and structure your data

### 2. Resume Editing

- **Edit Mode**: Click "Edit Resume" to modify all sections
- **Input Fields**: All fields support proper comma-separated input
- **Skills**: Add categories and enter skills separated by commas
- **Projects**: Add project details with technologies and links
- **Experience**: Add work experience with descriptions
- **Education**: Add educational background
- **Achievements**: Add certifications and awards

### 3. Preview and Download

- **Preview Mode**: Click "Preview Resume" to see the final format
- **Professional Display**: Contact links show only icons and labels
- **Download PDF**: Click "Download PDF" to get your professional resume

## 🎨 Template Features

### Professional Black Design

- **Clean Layout**: Minimalist black and white design
- **Professional Typography**: Clear, readable fonts
- **Structured Sections**: Well-organized content sections
- **Icon Integration**: Professional icons for contact information
- **No URL Display**: Clean presentation without showing actual URLs

### Input Handling

- **Comma-separated Lists**: Easy input for skills, technologies, etc.
- **Real-time Validation**: Immediate feedback on input
- **Auto-save**: Changes are automatically saved
- **Add/Remove Items**: Dynamic addition and removal of sections

## 🔧 Technical Details

### Backend (Flask)

- **Portfolio Scraping**: Intelligent web scraping with fallbacks
- **AI Integration**: GROQ and Gemini for data extraction
- **LaTeX Generation**: Professional PDF generation
- **Error Handling**: Comprehensive error handling and fallbacks

### Frontend (Next.js)

- **React Components**: Modular, reusable components
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Modern, responsive styling
- **Real-time Updates**: Live preview and auto-save

### PDF Generation

- **LaTeX Engine**: Primary PDF generation method
- **ReportLab Fallback**: Reliable fallback for PDF creation
- **Professional Formatting**: Clean, industry-standard layout
- **Black Theme**: Professional black color scheme

## 🧪 Testing

Run the test suite to verify functionality:

```bash
python test_resume.py
```

This will test:

- Health check endpoint
- Portfolio conversion
- PDF generation
- Data extraction

## 📁 Project Structure

```
PortToResume/
├── app/                    # Next.js frontend
│   ├── components/        # React components
│   ├── api/              # API routes
│   └── page.tsx          # Main page
├── app.py                # Flask backend
├── requirements.txt      # Python dependencies
├── package.json          # Node.js dependencies
├── test_resume.py        # Test suite
└── README.md            # This file
```

## 🔍 Key Improvements

### ✅ Fixed Issues

1. **Comma-separated Input**: Proper handling of comma-separated lists
2. **Professional Display**: Icons only for contact links (no URLs shown)
3. **Black Template**: Professional black resume design
4. **Input Validation**: All input fields work correctly
5. **Preview Matching**: Preview matches final PDF format

### 🆕 New Features

1. **Professional Black Theme**: Clean, professional design
2. **Enhanced Input Handling**: Better comma-separated input
3. **Icon-only Links**: Professional contact display
4. **Auto-save**: Automatic saving of changes
5. **Comprehensive Testing**: Full test suite

## 🎯 Use Cases

- **Job Applications**: Create professional resumes for job applications
- **Portfolio Conversion**: Convert portfolio websites to resume format
- **Professional Branding**: Maintain consistent professional appearance
- **Quick Resume Creation**: Fast resume generation from existing portfolios

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

If you encounter any issues:

1. Check the test suite: `python test_resume.py`
2. Verify API keys are set correctly
3. Ensure both frontend and backend are running
4. Check the console for error messages

## 🎉 Success Stories

Users have successfully:

- Converted GitHub portfolios to professional resumes
- Created job-ready PDFs in minutes
- Maintained professional appearance across applications
- Streamlined their resume creation process

---

**Ready to create your professional resume? Start by entering your portfolio URL!** 🚀
