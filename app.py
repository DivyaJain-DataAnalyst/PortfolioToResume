import os
from dotenv import load_dotenv
from groq import Groq
import google.generativeai as genai
from typing import List
import json
from pydantic import BaseModel
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import uuid
import traceback
import zipfile
import tempfile
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import PyPDF2

load_dotenv()

# Initialize APIs
groq_api_key = os.getenv("GROQ_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not groq_api_key:
    print("ERROR: GROQ_API_KEY not found!")
if not gemini_api_key:
    print("ERROR: GEMINI_API_KEY not found!")

groq_client = Groq(api_key=groq_api_key)
genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel('gemini-pro')

class Project(BaseModel):
    project_name: str
    about_project: str
    skills_used: list[str]

class Achivements(BaseModel):
    Achivement_name: str
    institute_name: str
    about: str

class Experience(BaseModel):
    Position_name: str
    Company_name: str
    skills_used: list[str]

class Education(BaseModel):
    Institute_name: str
    Degree_name: str
    marks: str

class Position_of_Responsibility(BaseModel):
    Position_name: str
    Society_name: str
    Description: str

class Candidate(BaseModel):
    name: str
    Education: List[Education]
    Projects: List[Project]
    Experience: List[Experience]
    Achivements: List[Achivements]
    Skills: List[str]
    Position_of_Responsibility: List[Position_of_Responsibility]
    Contact_Info: dict

def get_all_info(info: str) -> Candidate:
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a resume parser that extracts information from resume.\n"
                    f" The JSON object must use the schema: {json.dumps(Candidate.model_json_schema(), indent=2)}",
                },
                {
                    "role": "user",
                    "content": f"use this {info}",
                },
            ],
            model="llama-3.3-70b-versatile",
            temperature=0,
            stream=False,
            response_format={"type": "json_object"},
        )
        return Candidate.model_validate_json(chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"Error in resume parsing: {str(e)}")
        raise e

def scrape_portfolio(url: str) -> str:
    """Scrape portfolio website and extract relevant information for professional resume"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Try multiple approaches for robust scraping
        session = requests.Session()
        session.headers.update(headers)
        
        # First try with SSL verification disabled for problematic sites
        try:
            response = session.get(url, timeout=20, verify=False, allow_redirects=True)
            response.raise_for_status()
        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            # If SSL fails, try with different approach
            try:
                response = session.get(url, timeout=30, verify=False, allow_redirects=True)
                response.raise_for_status()
            except Exception as e:
                print(f"Failed to scrape {url}: {str(e)}")
                # Return a basic template with the URL for AI processing
                return f"""
PROFESSIONAL PORTFOLIO DATA EXTRACTION:

PERSONAL INFORMATION:
NAME: [Extract from URL or context]
TITLE: [Extract from URL or context]
EMAIL: [Extract from URL or context]
PHONE: [Extract from URL or context]
LOCATION: [Extract from URL or context]
LINKEDIN: [Extract from URL or context]
GITHUB: [Extract from URL or context]

PROFESSIONAL SUMMARY:
ABOUT: [Extract professional summary from context]

TECHNICAL SKILLS:
SKILLS: [Extract technical skills from context]

EDUCATION BACKGROUND:
EDUCATION: [Extract education information from context]

WORK EXPERIENCE:
EXPERIENCE: [Extract work experience from context]

PROJECT PORTFOLIO:
PROJECTS: [Extract project information from context]

ACHIEVEMENTS:
ACHIEVEMENTS: [Extract achievements from context]

PORTFOLIO URL: {url}
ADDITIONAL CONTEXT: Unable to scrape website directly. Please extract information from the portfolio URL and context.
                """
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract structured data for professional resume
        portfolio_data = {
            'name': '',
            'title': '',
            'email': '',
            'phone': '',
            'location': '',
            'linkedin': '',
            'github': '',
            'skills': [],
            'projects': [],
            'education': [],
            'about': '',
            'experience': [],
            'achievements': []
        }
        
        # Enhanced name extraction
        name_selectors = [
            'h1', '.name', '#name', '[class*="name"]', '[id*="name"]',
            '.hero h1', '.header h1', '.intro h1', '.profile h1',
            '.title h1', '.main-title', '.hero-title'
        ]
        
        for selector in name_selectors:
            name_elem = soup.select_one(selector)
            if name_elem and name_elem.get_text().strip():
                portfolio_data['name'] = name_elem.get_text().strip()
                break
        
        # Enhanced title extraction
        title_selectors = [
            'h2', '.title', '#title', '[class*="title"]', '[id*="title"]',
            '.role', '.position', '.job-title', '.profession',
            '.hero h2', '.header h2', '.intro h2', '.profile h2',
            '.subtitle', '.tagline', '.description'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.get_text().strip():
                title_text = title_elem.get_text().strip()
                # Clean up title text
                if len(title_text) < 100:  # Avoid long descriptions
                    portfolio_data['title'] = title_text
                    break
        
        # Enhanced contact information extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'[\+]?[1-9][\d\s\-\(\)]{7,15}'
        
        # Find emails and phones in text content and links
        text_content = soup.get_text()
        emails = re.findall(email_pattern, text_content)
        if emails:
            portfolio_data['email'] = emails[0]
        
        phones = re.findall(phone_pattern, text_content)
        if phones:
            portfolio_data['phone'] = phones[0].replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Enhanced link extraction
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            link_text = link.get_text().strip().lower()
            
            if 'linkedin.com' in href or 'linkedin' in link_text:
                portfolio_data['linkedin'] = href
            elif 'github.com' in href or 'github' in link_text:
                portfolio_data['github'] = href
            elif 'mailto:' in href:
                email = href.replace('mailto:', '')
                if '@' in email:
                    portfolio_data['email'] = email
            elif 'tel:' in href:
                phone = href.replace('tel:', '')
                portfolio_data['phone'] = phone
        
        # Enhanced skills extraction
        skill_selectors = [
            '.skills', '#skills', '[class*="skill"]', '[id*="skill"]',
            '.technologies', '.tech-stack', '.tools', '.languages',
            '.frontend', '.backend', '.database', '.frameworks'
        ]
        
        for selector in skill_selectors:
            skill_elem = soup.select_one(selector)
            if skill_elem:
                # Extract skills from text
                skill_text = skill_elem.get_text()
                skills = []
                
                # Common skill patterns
                skill_patterns = [
                    r'\b(?:React|Angular|Vue|JavaScript|TypeScript|HTML|CSS|Node\.js|Python|Java|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin|Dart)\b',
                    r'\b(?:MongoDB|PostgreSQL|MySQL|SQLite|Redis|Firebase|Supabase|AWS|Azure|GCP|Docker|Kubernetes|Git|GitHub|GitLab)\b',
                    r'\b(?:Express|FastAPI|Django|Flask|Spring|Laravel|Rails|Next\.js|Nuxt\.js|Tailwind|Bootstrap|Material-UI|Ant Design)\b',
                    r'\b(?:REST|GraphQL|JWT|OAuth|Jest|Cypress|Selenium|Postman|Swagger|CI/CD|Agile|Scrum|MVC|MVVM)\b'
                ]
                
                for pattern in skill_patterns:
                    found_skills = re.findall(pattern, skill_text, re.IGNORECASE)
                    skills.extend(found_skills)
                
                # Also extract comma-separated skills
                comma_skills = [skill.strip() for skill in skill_text.split(',') if skill.strip() and len(skill.strip()) > 2]
                skills.extend(comma_skills)
                
                portfolio_data['skills'].extend(skills)
        
        # Remove duplicates and clean skills
        portfolio_data['skills'] = list(set([skill.strip() for skill in portfolio_data['skills'] if skill.strip()]))
        
        # Enhanced projects extraction
        project_selectors = [
            '.project', '#project', '[class*="project"]', '[id*="project"]',
            '.portfolio-item', '.work-item', '.case-study', '.app',
            '.card', '.item', '.work', '.portfolio'
        ]
        
        for selector in project_selectors:
            project_elems = soup.select(selector)
            for project in project_elems:
                project_data = {
                    'title': '',
                    'desc': '',
                    'tech': [],
                    'github': '',
                    'demo': ''
                }
                
                # Extract project title
                title_selectors = ['h3', 'h4', '.title', '.name', '.project-title', '.project-name']
                for title_sel in title_selectors:
                    title_elem = project.select_one(title_sel)
                    if title_elem:
                        project_data['title'] = title_elem.get_text().strip()
                        break
                
                # Extract project description
                desc_selectors = ['p', '.description', '.desc', '.project-desc', '.summary']
                for desc_sel in desc_selectors:
                    desc_elem = project.select_one(desc_sel)
                    if desc_elem:
                        desc_text = desc_elem.get_text().strip()
                        if len(desc_text) > 10:  # Avoid very short descriptions
                            project_data['desc'] = desc_text
                            break
                
                # Extract project technologies
                tech_selectors = ['.tech', '.technologies', '.stack', '.tools', '.languages']
                for tech_sel in tech_selectors:
                    tech_elem = project.select_one(tech_sel)
                    if tech_elem:
                        tech_text = tech_elem.get_text()
                        tech_list = [tech.strip() for tech in tech_text.split(',') if tech.strip()]
                        project_data['tech'].extend(tech_list)
                
                # Extract project links
                project_links = project.find_all('a', href=True)
                for link in project_links:
                    href = link['href']
                    link_text = link.get_text().strip().lower()
                    
                    if 'github.com' in href or 'github' in link_text:
                        project_data['github'] = href
                    elif any(domain in href for domain in ['vercel.app', 'netlify.app', 'herokuapp.com', 'render.com', 'surge.sh', 'firebaseapp.com']):
                        project_data['demo'] = href
                    elif 'demo' in link_text or 'live' in link_text or 'view' in link_text:
                        project_data['demo'] = href
                
                if project_data['title'] and len(project_data['title']) > 2:
                    portfolio_data['projects'].append(project_data)
        
        # Enhanced education extraction
        education_selectors = [
            '.education', '#education', '[class*="education"]', '[id*="education"]',
            '.academic', '.degree', '.university', '.college', '.school'
        ]
        
        for selector in education_selectors:
            edu_elem = soup.select_one(selector)
            if edu_elem:
                edu_data = {
                    'Institute_name': '',
                    'Degree_name': '',
                    'year': '',
                    'marks': ''
                }
                
                edu_text = edu_elem.get_text()
                
                # Extract degree patterns
                degree_patterns = [
                    r'\b(?:B\.Tech|B\.E\.|B\.S\.|M\.Tech|M\.S\.|Ph\.D|Bachelor|Master|Diploma)\b',
                    r'\b(?:Computer Science|Engineering|Information Technology|Software Engineering)\b'
                ]
                
                for pattern in degree_patterns:
                    degree_match = re.search(pattern, edu_text, re.IGNORECASE)
                    if degree_match:
                        edu_data['Degree_name'] = degree_match.group()
                        break
                
                # Extract year patterns
                year_pattern = r'\b(?:20\d{2}|19\d{2})\b'
                year_match = re.search(year_pattern, edu_text)
                if year_match:
                    edu_data['year'] = year_match.group()
                
                # Extract GPA patterns
                gpa_pattern = r'\b(?:GPA|CGPA|Grade):?\s*(\d+\.?\d*)\b'
                gpa_match = re.search(gpa_pattern, edu_text, re.IGNORECASE)
                if gpa_match:
                    edu_data['marks'] = gpa_match.group(1)
                
                # Extract institution name
                if 'university' in edu_text.lower() or 'college' in edu_text.lower() or 'institute' in edu_text.lower():
                    lines = edu_text.split('\n')
                    for line in lines:
                        if any(word in line.lower() for word in ['university', 'college', 'institute', 'school']):
                            edu_data['Institute_name'] = line.strip()
                            break
                
                if edu_data['Institute_name'] or edu_data['Degree_name']:
                    portfolio_data['education'].append(edu_data)
        
        # Enhanced about section extraction
        about_selectors = [
            '.about', '#about', '[class*="about"]', '[id*="about"]',
            '.intro', '.summary', '.bio', '.description', '.profile'
        ]
        
        for selector in about_selectors:
            about_elem = soup.select_one(selector)
            if about_elem:
                about_text = about_elem.get_text().strip()
                if len(about_text) > 20:  # Avoid very short descriptions
                    portfolio_data['about'] = about_text[:500]  # Limit length
                    break
        
        # Enhanced experience extraction
        experience_selectors = [
            '.experience', '#experience', '[class*="experience"]', '[id*="experience"]',
            '.work', '.employment', '.career', '.job', '.position'
        ]
        
        for selector in experience_selectors:
            exp_elem = soup.select_one(selector)
            if exp_elem:
                exp_data = {
                    'Company': '',
                    'Position': '',
                    'Duration': '',
                    'Skills': []
                }
                
                exp_text = exp_elem.get_text()
                
                # Extract company patterns
                company_patterns = [
                    r'\b(?:Company|Corp|Inc|LLC|Ltd|Tech|Solutions|Systems)\b',
                    r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Company|Corp|Inc|LLC|Ltd|Tech|Solutions|Systems)\b'
                ]
                
                for pattern in company_patterns:
                    company_match = re.search(pattern, exp_text, re.IGNORECASE)
                    if company_match:
                        exp_data['Company'] = company_match.group()
                        break
                
                # Extract position patterns
                position_patterns = [
                    r'\b(?:Developer|Engineer|Designer|Manager|Lead|Architect|Consultant|Analyst)\b',
                    r'\b(?:Full Stack|Frontend|Backend|Software|Web|Mobile|UI/UX|DevOps)\b'
                ]
                
                for pattern in position_patterns:
                    position_match = re.search(pattern, exp_text, re.IGNORECASE)
                    if position_match:
                        exp_data['Position'] = position_match.group()
                        break
                
                if exp_data['Company'] or exp_data['Position']:
                    portfolio_data['experience'].append(exp_data)
        
        # Format the extracted data into a comprehensive text for AI processing
        portfolio_text = f"""
PROFESSIONAL PORTFOLIO DATA EXTRACTION:

PERSONAL INFORMATION:
NAME: {portfolio_data['name']}
TITLE: {portfolio_data['title']}
EMAIL: {portfolio_data['email']}
PHONE: {portfolio_data['phone']}
LOCATION: {portfolio_data.get('location', '')}
LINKEDIN: {portfolio_data['linkedin']}
GITHUB: {portfolio_data['github']}

PROFESSIONAL SUMMARY:
ABOUT: {portfolio_data['about']}

TECHNICAL SKILLS:
SKILLS: {', '.join(portfolio_data['skills'])}

EDUCATION BACKGROUND:
EDUCATION: {portfolio_data['education']}

WORK EXPERIENCE:
EXPERIENCE: {portfolio_data['experience']}

PROJECT PORTFOLIO:
PROJECTS: {portfolio_data['projects']}

ACHIEVEMENTS:
ACHIEVEMENTS: {portfolio_data['achievements']}

ADDITIONAL CONTENT FOR CONTEXT:
{text_content[:3000]}
        """
        
        return portfolio_text.strip()
        
    except Exception as e:
        print(f"Error scraping portfolio: {str(e)}")
        raise e

def extract_resume_data_from_portfolio(portfolio_text: str) -> dict:
    """Extract resume data from portfolio text using AI for professional resume generation"""
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at extracting professional information from portfolio websites and converting it into a structured resume format that matches industry standards.

Based on the portfolio data provided, extract and structure the following information in a professional resume format:

1. NAME: Full name of the person
2. TITLE: Current role or title (e.g., Full Stack Developer, Frontend Developer, Software Engineer)
3. CONTACT: Email, phone, location, LinkedIn, GitHub, portfolio URL
4. ABOUT: Professional summary or objective (2-3 sentences about career goals, expertise, and what you bring to the table)
5. EDUCATION: Institution name, degree, year, GPA if mentioned
6. SKILLS: Technical skills organized by category (Frontend, Backend, Database, Tools & DevOps)
7. PROJECTS: Project names, descriptions, technologies used, GitHub links, live demo links
8. EXPERIENCE: Work experience, internships, positions held with company names and durations
9. ACHIEVEMENTS: Certifications, awards, notable accomplishments

Format the response as a comprehensive, professional resume summary that follows industry standards and is ready for LaTeX resume generation. If information is missing, make reasonable assumptions based on the context and portfolio content.

Example format:
NAME: [Full Name]
TITLE: [Current Position - e.g., Full Stack Developer]
CONTACT: [Email, Phone, Location, LinkedIn, GitHub]
ABOUT: [Professional summary about career goals and expertise - 2-3 sentences]
EDUCATION: [Institution, Degree, Year, GPA]
SKILLS: [Organized by Frontend, Backend, Database, Tools & DevOps]
PROJECTS: [Detailed project descriptions with technologies and links]
EXPERIENCE: [Work experience with company names and durations]
ACHIEVEMENTS: [Certifications and awards]

Ensure the extracted data is professional, well-structured, and ready for high-quality resume generation."""
                },
                {
                    "role": "user",
                    "content": f"Extract and structure resume information from this portfolio data for professional resume generation:\n\n{portfolio_text}"
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            stream=False,
        )
        
        return {
            'extracted_text': chat_completion.choices[0].message.content,
            'portfolio_text': portfolio_text
        }
        
    except Exception as e:
        print(f"Error extracting resume data: {str(e)}")
        raise e

def generate_enhanced_latex_resume(resume_data: dict, template: str = "professional") -> str:
    """Generate highly professional LaTeX resume matching the provided template format"""
    
    try:
        # Ensure all required data is present with proper sanitization
        name = resume_data.get('name', 'Professional Developer').replace('&', '\\&').replace('_', '\\_')
        title = resume_data.get('title', 'Software Developer').replace('&', '\\&').replace('_', '\\_')
        contact_info = resume_data.get('Contact_Info', {})
        skills = resume_data.get('skills', {})
        projects = resume_data.get('projects', [])
        education = resume_data.get('education', [])
        experience = resume_data.get('experience', [])
        achievements = resume_data.get('achievements', [])
        about = resume_data.get('about', '')
        
        # Sanitize about text
        about = about.replace('&', '\\&').replace('_', '\\_') if about else ''
        
        # Generate professional black LaTeX content
        latex_content = f"""\\documentclass[a4paper,11pt]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[margin=0.75in]{{geometry}}
\\usepackage{{parskip}}
\\usepackage{{enumitem}}
\\usepackage{{titlesec}}
\\usepackage{{xcolor}}
\\usepackage[colorlinks=true,urlcolor=black,linkcolor=black]{{hyperref}}

% Professional black color scheme
\\definecolor{{sectioncolor}}{{RGB}}{{0, 0, 0}}
\\definecolor{{linkcolor}}{{RGB}}{{0, 0, 0}}
\\definecolor{{textcolor}}{{RGB}}{{0, 0, 0}}

% Section formatting with black theme
\\titleformat{{\\section}}{{\\Large\\bfseries\\color{{sectioncolor}}}}{{\\thesection}}{{1em}}{{}}[\\titlerule]
\\titlespacing{{\\section}}{{0pt}}{{12pt}}{{6pt}}

% Custom spacing
\\setlength{{\\parskip}}{{0pt}}
\\setlength{{\\itemsep}}{{0pt}}
\\setlength{{\\parsep}}{{0pt}}

\\begin{{document}}
\\pagestyle{{empty}}

% Header Section with black theme
\\begin{{center}}
\\textbf{{\\Huge {name}}} \\\\[4pt]
\\textbf{{\\Large {title}}} \\\\[8pt]
"""

        # Contact information with clickable links
        contact_parts = []
        if contact_info.get('email'):
            contact_parts.append(f"Email: {contact_info['email']}")
        if contact_info.get('phone'):
            contact_parts.append(f"Phone: {contact_info['phone']}")
        if contact_info.get('github'):
            github_url = contact_info['github']
            contact_parts.append(f"\\href{{{github_url}}}{{GitHub Profile}}")
        if contact_info.get('linkedin'):
            linkedin_url = contact_info['linkedin']
            contact_parts.append(f"\\href{{{linkedin_url}}}{{LinkedIn Profile}}")
        
        if contact_parts:
            latex_content += " \\quad $|$ \\quad ".join(contact_parts) + " \\\\[6pt]\n"
        
        latex_content += "\\end{center}\n\\vspace{8pt}\n"
        
        # Objective/Summary Section
        if about:
            latex_content += f"\\section{{Objective}}\n{about}\n\n"
        else:
            latex_content += f"\\section{{Objective}}\n{title} with expertise in modern software development technologies and best practices. Passionate about creating scalable, maintainable solutions and contributing to innovative projects.\n\n"
        
        # Skills Section with proper formatting
        if skills:
            latex_content += "\\section{Skills}\n"
            for category, skill_list in skills.items():
                if skill_list:
                    latex_content += f"\\textbf{{{category}:}} {', '.join(skill_list)}\\\\\n"
            latex_content += "\\vspace{6pt}\n"
        
        # Projects Section with proper formatting
        if projects:
            latex_content += "\\section{Projects}\n"
            for proj in projects:
                title = proj.get('name', proj.get('title', proj.get('project_name', 'Web Application')))
                desc = proj.get('description', proj.get('desc', proj.get('about_project', 'Professional web application')))
                tech = proj.get('technologies', proj.get('tech', proj.get('skills_used', ['React', 'Node.js'])))
                link = proj.get('link', proj.get('github', ''))
                
                latex_content += f"\\textbf{{{title}}} \\hfill \\textit{{{', '.join(tech)}}}\\\\\n"
                github_link = proj.get('github', '')
                demo_link = proj.get('demo', '')
                if github_link or demo_link:
                    links = []
                    if github_link:
                        links.append(f"\\href{{{github_link}}}{{GitHub Repository}}")
                    if demo_link:
                        links.append(f"\\href{{{demo_link}}}{{Live Demo}}")
                    latex_content += f"{' \\quad $|$ \\quad '.join(links)}\\\\\n"
                
                latex_content += "\\begin{itemize}[leftmargin=*,nosep]\n"
                latex_content += f"\\item {desc}\n"
                latex_content += "\\end{itemize}\n\\vspace{4pt}\n"
        
        # Education Section with proper formatting
        if education:
            latex_content += "\\section{Education}\n"
            for edu in education:
                degree = edu.get('degree', edu.get('Degree_name', 'Bachelor of Science'))
                institute = edu.get('institution', edu.get('Institute_name', 'University'))
                duration = edu.get('duration', edu.get('year', '2020--2024'))
                gpa = edu.get('gpa', edu.get('marks', '3.8/4.0'))
                
                latex_content += f"\\textbf{{{degree}}} \\hfill \\textbf{{{duration}}}\\\\\n"
                latex_content += f"{institute} \\hfill CGPA: {gpa}\\\\\n"
                latex_content += "\\textit{Key Courses:} Data Structures, Algorithms, Web Development, Database Systems\\\\\n\\vspace{4pt}\n"
        
        # Experience Section with proper formatting
        if experience:
            latex_content += "\\section{Experience}\n"
            for exp in experience:
                position = exp.get('position', exp.get('Position_name', 'Software Developer'))
                company = exp.get('company', exp.get('Company_name', 'Company'))
                duration = exp.get('duration', '2023--Present')
                skills = exp.get('skills', exp.get('skills_used', []))
                description = exp.get('description', '')
                
                latex_content += f"\\textbf{{{position}}} \\hfill \\textbf{{{duration}}}\\\\\n"
                latex_content += f"{company} \\hfill \\textit{{{', '.join(skills)}}}\\\\\n"
                if description:
                    latex_content += f"{description}\\\\\n"
                latex_content += "\\vspace{4pt}\n"
        
        # Certifications Section with proper formatting
        if achievements:
            latex_content += "\\section{Certifications}\n"
            for achievement in achievements:
                name = achievement.get('name', achievement.get('achievement_name', achievement.get('Achivement_name', 'Professional Certification')))
                institution = achievement.get('institution', achievement.get('institute_name', ''))
                desc = achievement.get('description', achievement.get('about', 'Technical expertise'))
                if institution:
                    latex_content += f"{name} - {institution} - {desc}\\\\\n"
                else:
                    latex_content += f"{name} - {desc}\\\\\n"
            latex_content += "\\vspace{6pt}\n"
        
        # Technical Achievements Section with proper formatting
        if achievements:
            latex_content += "\\section{Technical Achievements}\n"
            latex_content += "\\begin{itemize}[leftmargin=*,nosep]\n"
            for achievement in achievements:
                name = achievement.get('name', achievement.get('achievement_name', achievement.get('Achivement_name', 'Professional Certification')))
                institution = achievement.get('institution', achievement.get('institute_name', ''))
                desc = achievement.get('description', achievement.get('about', 'Technical expertise'))
                if institution:
                    latex_content += f"\\item {name} ({institution}): {desc}\n"
                else:
                    latex_content += f"\\item {name}: {desc}\n"
            latex_content += "\\end{itemize}\n"
        
        latex_content += "\\end{document}"
        
        return latex_content
        
    except Exception as e:
        print(f"❌ Error generating LaTeX content: {str(e)}")
        # Return a basic professional template as fallback
        return f"""\\documentclass[a4paper,11pt]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[margin=0.75in]{{geometry}}
\\usepackage{{parskip}}
\\setlength{{\\parskip}}{{0pt}}

\\begin{{document}}
\\pagestyle{{empty}}

\\begin{{center}}
\\textbf{{\\Huge {resume_data.get('name', 'Professional Developer')}}} \\\\[8pt]
\\textbf{{\\Large {resume_data.get('title', 'Software Developer')}}} \\\\[12pt]
\\end{{center}}

\\section{{Objective}}
Experienced software developer with expertise in modern technologies and best practices.

\\section{{Skills}}
Technical skills and expertise in software development.

\\section{{Projects}}
Professional projects and achievements.

\\section{{Education}}
Educational background and qualifications.

\\section{{Certifications}}
Professional certifications and achievements.

\\end{{document}}"""

# Replace the generate_pdf_from_latex function with this proper LaTeX compiler
def check_latex_installation():
    """Check if LaTeX is properly installed and accessible"""
    try:
        import subprocess
        result = subprocess.run(['pdflatex', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ LaTeX installation found and working")
            return True
        else:
            print("❌ LaTeX installation found but not working properly")
            return False
    except FileNotFoundError:
        print("❌ LaTeX (pdflatex) not found - please install MiKTeX or TeX Live")
        return False
    except Exception as e:
        print(f"❌ Error checking LaTeX installation: {str(e)}")
        return False

def generate_pdf_from_latex(latex_content: str, resume_data: dict = None) -> bytes:
    """Generate professional PDF by properly compiling LaTeX code"""
    try:
        # Check LaTeX installation first
        if not check_latex_installation():
            print("🔄 LaTeX not available, using enhanced fallback...")
            if resume_data:
                return generate_pdf_fallback(resume_data)
            else:
                raise Exception("LaTeX not available and no resume data provided for fallback")
        
        import subprocess
        import tempfile
        import os
        
        print(" Compiling LaTeX to professional PDF...")
        
        # Create temporary directory for LaTeX compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create LaTeX file
            latex_file = os.path.join(temp_dir, "resume.tex")
            with open(latex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            print(f"📄 LaTeX file created: {latex_file}")
            
            # Try to compile with improved pdflatex command
            try:
                print("🔄 Running LaTeX compilation...")
                
                # Single compilation run with optimized settings
                result = subprocess.run([
                    'pdflatex',
                    '-interaction=nonstopmode',
                    '-output-directory=' + temp_dir,
                    'resume.tex'
                ], capture_output=True, text=True, timeout=30, cwd=temp_dir)
                
                # Check if PDF was generated
                pdf_file = os.path.join(temp_dir, "resume.pdf")
                if os.path.exists(pdf_file):
                    with open(pdf_file, 'rb') as f:
                        pdf_content = f.read()
                    
                    if len(pdf_content) > 1000:  # Ensure PDF is not empty
                        print(f"✅ LaTeX compilation successful! PDF size: {len(pdf_content):,} bytes")
                        return pdf_content
                    else:
                        print("❌ PDF generated but appears to be empty or corrupted")
                        if resume_data:
                            print("🔄 Using fallback PDF generation...")
                            return generate_pdf_fallback(resume_data)
                        else:
                            raise Exception("LaTeX compilation produced empty PDF")
                else:
                    print("❌ PDF file not generated from LaTeX compilation")
                    print(f"Files in temp directory: {os.listdir(temp_dir)}")
                    print(f"Compilation output: {result.stdout}")
                    print(f"Compilation errors: {result.stderr}")
                    # Try fallback immediately
                    if resume_data:
                        print("🔄 Using fallback PDF generation...")
                        return generate_pdf_fallback(resume_data)
                    else:
                        raise Exception("LaTeX compilation failed - no PDF output")
                    
            except subprocess.TimeoutExpired:
                print("❌ LaTeX compilation timed out")
                if resume_data:
                    print("🔄 Using fallback PDF generation...")
                    return generate_pdf_fallback(resume_data)
                else:
                    raise Exception("LaTeX compilation timed out")
            except FileNotFoundError:
                print("❌ pdflatex not found - using fallback method")
                if resume_data:
                    return generate_pdf_fallback(resume_data)
                else:
                    raise Exception("pdflatex not found and no resume data provided for fallback")
                
    except Exception as e:
        print(f"❌ LaTeX compilation error: {str(e)}")
        print("🔄 Using fallback PDF generation method...")
        if resume_data:
            return generate_pdf_fallback(resume_data)
        else:
            raise Exception("LaTeX compilation failed and no resume data provided for fallback")

# Replace the generate_pdf_fallback function with this improved version
def generate_pdf_fallback(resume_data: dict) -> bytes:
    """Enhanced professional PDF generation using ReportLab with improved formatting"""
    try:
        print("🔄 Using enhanced ReportLab fallback for PDF generation...")
        
        # Create buffer for PDF
        buffer = BytesIO()
        
        # Create PDF document with professional settings
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create professional black custom styles
        title_style = ParagraphStyle(
            'ProfessionalTitle',
            parent=styles['Heading1'],
            fontSize=32,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            leading=36
        )
        
        subtitle_style = ParagraphStyle(
            'ProfessionalSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=16,
            alignment=TA_CENTER,
            textColor=colors.grey,
            fontName='Helvetica',
            leading=16
        )
        
        contact_style = ParagraphStyle(
            'ContactInfo',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica',
            leading=12
        )
        
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=8,
            spaceBefore=16,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            leading=18,
            borderWidth=1,
            borderColor=colors.black,
            borderPadding=3,
            backColor=colors.lightgrey
        )
        
        subsection_style = ParagraphStyle(
            'SubsectionHeader',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=4,
            spaceBefore=8,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            leading=14
        )
        
        normal_style = ParagraphStyle(
            'NormalText',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=3,
            textColor=colors.black,
            fontName='Helvetica',
            leading=12
        )
        
        bold_style = ParagraphStyle(
            'BoldText',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=3,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            leading=12
        )
        
        # Build PDF content directly from resume data
        story = []
        
        # Extract data from resume_data
        name = resume_data.get('name', 'Professional Developer')
        title = resume_data.get('title', 'Software Developer')
        contact_info = resume_data.get('Contact_Info', {})
        skills = resume_data.get('skills', {})
        projects = resume_data.get('projects', [])
        education = resume_data.get('education', [])
        experience = resume_data.get('experience', [])
        achievements = resume_data.get('achievements', [])
        about = resume_data.get('about', '')
        
        # Build the PDF content with professional layout
        # Header
        story.append(Paragraph(name.upper(), title_style))
        story.append(Paragraph(title, subtitle_style))
        
        # Contact information with professional layout (no URLs shown)
        contact_text = ""
        if contact_info:
            contact_parts = []
            if contact_info.get('email'):
                contact_parts.append(f"📧 {contact_info['email']}")
            if contact_info.get('phone'):
                contact_parts.append(f"📱 {contact_info['phone']}")
            if contact_info.get('location'):
                contact_parts.append(f"📍 {contact_info['location']}")
            if contact_info.get('linkedin'):
                contact_parts.append("💼 LinkedIn Profile")
            if contact_info.get('github'):
                contact_parts.append("🐙 GitHub Profile")
            contact_text = " | ".join(contact_parts)
        
        if contact_text:
            story.append(Paragraph(contact_text, contact_style))
        
        # Professional Summary
        if about:
            story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
            story.append(Paragraph(about, normal_style))
            story.append(Spacer(1, 12))
        
        # Skills Section with categorized display
        if skills:
            story.append(Paragraph("TECHNICAL SKILLS", section_style))
            for category, skill_list in skills.items():
                if skill_list:
                    category_text = f"<b>{category}:</b> {', '.join(skill_list)}"
                    story.append(Paragraph(category_text, normal_style))
            story.append(Spacer(1, 12))
        
        # Experience Section
        if experience:
            story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_style))
            for exp in experience:
                exp_text = f"<b>{exp.get('position', '')}</b> - {exp.get('company', '')}"
                story.append(Paragraph(exp_text, bold_style))
                
                if exp.get('duration'):
                    story.append(Paragraph(f"<i>{exp['duration']}</i>", normal_style))
                
                if exp.get('description'):
                    story.append(Paragraph(exp['description'], normal_style))
                
                if exp.get('skills'):
                    skills_text = f"<b>Technologies:</b> {', '.join(exp['skills'])}"
                    story.append(Paragraph(skills_text, normal_style))
                
                story.append(Spacer(1, 8))
        
        # Projects Section
        if projects:
            story.append(Paragraph("PROJECTS", section_style))
            for project in projects:
                project_text = f"<b>{project.get('name', '')}</b>"
                story.append(Paragraph(project_text, bold_style))
                
                if project.get('description'):
                    story.append(Paragraph(project['description'], normal_style))
                
                if project.get('technologies'):
                    tech_text = f"<b>Technologies:</b> {', '.join(project['technologies'])}"
                    story.append(Paragraph(tech_text, normal_style))
                
                if project.get('github'):
                    link_text = "<b>GitHub Repository</b>"
                    story.append(Paragraph(link_text, normal_style))
                if project.get('demo'):
                    link_text = "<b>Live Demo</b>"
                    story.append(Paragraph(link_text, normal_style))
                
                story.append(Spacer(1, 8))
        
        # Education Section
        if education:
            story.append(Paragraph("EDUCATION", section_style))
            for edu in education:
                edu_text = f"<b>{edu.get('degree', '')}</b> - {edu.get('institution', '')}"
                story.append(Paragraph(edu_text, bold_style))
                
                if edu.get('duration'):
                    story.append(Paragraph(f"<i>{edu['duration']}</i>", normal_style))
                
                if edu.get('gpa'):
                    story.append(Paragraph(f"GPA: {edu['gpa']}", normal_style))
                
                story.append(Spacer(1, 6))
        
        # Achievements Section
        if achievements:
            story.append(Paragraph("ACHIEVEMENTS & AWARDS", section_style))
            for achievement in achievements:
                achievement_text = f"<b>{achievement.get('name', '')}</b> - {achievement.get('institution', '')}"
                story.append(Paragraph(achievement_text, bold_style))
                
                if achievement.get('description'):
                    story.append(Paragraph(achievement['description'], normal_style))
                
                story.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        print(f"✅ Enhanced fallback PDF generation successful! Size: {len(pdf_content):,} bytes")
        return pdf_content
        
    except Exception as e:
        print(f"❌ Enhanced fallback PDF generation failed: {str(e)}")
        traceback.print_exc()
        raise Exception(f"PDF generation failed: {str(e)}")

def generate_website_code(data, style="professional"):
    """Generate complete website code based on parsed resume data and selected style"""
    
    templates = {
        "professional": {
            "colors": {
                "primary": "#2563eb",
                "secondary": "#64748b",
                "accent": "#0f172a",
                "background": "#ffffff",
                "text": "#1e293b"
            },
            "fonts": "font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;",
            "style_class": "professional"
        },
        "futuristic": {
            "colors": {
                "primary": "#00d4ff",
                "secondary": "#7c3aed",
                "accent": "#ec4899",
                "background": "#0f0f23",
                "text": "#ffffff"
            },
            "fonts": "font-family: 'Orbitron', 'Courier New', monospace;",
            "style_class": "futuristic"
        },
        "playful": {
            "colors": {
                "primary": "#f59e0b",
                "secondary": "#ec4899",
                "accent": "#10b981",
                "background": "#fef3c7",
                "text": "#374151"
            },
            "fonts": "font-family: 'Poppins', 'Comic Sans MS', cursive;",
            "style_class": "playful"
        }
    }
    
    theme = templates.get(style, templates["professional"])
    
    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['name']} - Portfolio</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Orbitron:wght@400;700;900&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
</head>
<body class="{theme['style_class']}">
    <div class="container">
        <!-- Header Section -->
        <header class="header" id="header">
            <div class="profile-section">
                <div class="profile-image">
                    <div class="avatar">{data['name'][:2].upper()}</div>
                </div>
                <div class="profile-info">
                    <h1 class="name">{data['name']}</h1>
                    <p class="title">Software Developer</p>
                </div>
            </div>
            <nav class="navigation">
                <a href="#about" class="nav-link">About</a>
                <a href="#experience" class="nav-link">Experience</a>
                <a href="#projects" class="nav-link">Projects</a>
                <a href="#skills" class="nav-link">Skills</a>
                <a href="#contact" class="nav-link">Contact</a>
            </nav>
        </header>

        <!-- About Section -->
        <section class="section" id="about">
            <h2 class="section-title">About Me</h2>
            <div class="about-content">
                <p class="about-text">Passionate developer with expertise in modern technologies and a strong foundation in software development.</p>
            </div>
        </section>

        <!-- Experience Section -->
        <section class="section" id="experience">
            <h2 class="section-title">Experience</h2>
            <div class="experience-grid">
                {generate_experience_html(data.get('Experience', []))}
            </div>
        </section>

        <!-- Projects Section -->
        <section class="section" id="projects">
            <h2 class="section-title">Projects</h2>
            <div class="projects-grid">
                {generate_projects_html(data.get('projects', []))}
            </div>
        </section>

        <!-- Skills Section -->
        <section class="section" id="skills">
            <h2 class="section-title">Skills</h2>
            <div class="skills-grid">
                {generate_skills_html(data.get('skills', []))}
            </div>
        </section>

        <!-- Education Section -->
        <section class="section" id="education">
            <h2 class="section-title">Education</h2>
            <div class="education-grid">
                {generate_education_html(data.get('education', []))}
            </div>
        </section>

        <!-- Contact Section -->
        <section class="section" id="contact">
            <h2 class="section-title">Contact</h2>
            <div class="contact-grid">
                {generate_contact_html(data.get('Contact_Info', {}))}
            </div>
        </section>
    </div>

    <script src="script.js"></script>
</body>
</html>"""

    # Generate CSS
    css_content = generate_css_content(theme, style)
    
    # Generate JavaScript
    js_content = generate_js_content(style)
    
    return {
        "html": html_content,
        "css": css_content,
        "js": js_content
    }

def generate_experience_html(experiences):
    if not experiences:
        return "<p>No experience data available</p>"
    
    html = ""
    for exp in experiences:
        html += f"""
        <div class="experience-card" data-component="experience-card">
            <h3 class="company-name">{exp.get('Company', 'Unknown Company')}</h3>
            <p class="position">{exp.get('Position', 'Unknown Position')}</p>
            <div class="skills-used">
                {', '.join(exp.get('Skills', []))}
            </div>
        </div>
        """
    return html

def generate_projects_html(projects):
    if not projects:
        return "<p>No projects data available</p>"
    
    html = ""
    for project in projects:
        html += f"""
        <div class="project-card" data-component="project-card">
            <h3 class="project-title">{project.get('title', 'Untitled Project')}</h3>
            <p class="project-description">{project.get('desc', 'No description available')}</p>
            <div class="tech-stack">
                {', '.join(project.get('tech', []))}
            </div>
        </div>
        """
    return html

def generate_skills_html(skills):
    if not skills:
        return "<p>No skills data available</p>"
    
    html = ""
    for skill in skills:
        html += f'<div class="skill-tag" data-component="skill-tag">{skill}</div>'
    return html

def generate_education_html(education):
    if not education:
        return "<p>No education data available</p>"
    
    html = ""
    for edu in education:
        html += f"""
        <div class="education-card" data-component="education-card">
            <h3 class="institute-name">{edu.get('Institute_name', 'Unknown Institute')}</h3>
            <p class="degree">{edu.get('Degree_name', 'Unknown Degree')}</p>
            <p class="marks">Marks: {edu.get('Marks', 'N/A')}</p>
        </div>
        """
    return html

def generate_contact_html(contact_info):
    if not contact_info:
        return "<p>No contact information available</p>"
    
    html = ""
    for key, value in contact_info.items():
        html += f"""
        <div class="contact-item" data-component="contact-item">
            <strong>{key}:</strong> {value}
        </div>
        """
    return html

def generate_css_content(theme, style):
    base_css = f"""
/* Reset and Base Styles */
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    {theme['fonts']}
    background-color: {theme['colors']['background']};
    color: {theme['colors']['text']};
    line-height: 1.6;
    overflow-x: hidden;
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}}

/* Header Styles */
.header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 2rem 0;
    border-bottom: 2px solid {theme['colors']['primary']};
    margin-bottom: 3rem;
}}

.profile-section {{
    display: flex;
    align-items: center;
    gap: 1.5rem;
}}

.avatar {{
    width: 80px;
    height: 80px;
    background: linear-gradient(135deg, {theme['colors']['primary']}, {theme['colors']['secondary']});
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    font-weight: bold;
    color: white;
}}

.name {{
    font-size: 2.5rem;
    font-weight: 700;
    color: {theme['colors']['primary']};
    margin-bottom: 0.5rem;
}}

.title {{
    font-size: 1.2rem;
    color: {theme['colors']['secondary']};
}}

.navigation {{
    display: flex;
    gap: 2rem;
}}

.nav-link {{
    text-decoration: none;
    color: {theme['colors']['text']};
    font-weight: 500;
    padding: 0.5rem 1rem;
    border-radius: 25px;
    transition: all 0.3s ease;
}}

.nav-link:hover {{
    background-color: {theme['colors']['primary']};
    color: white;
}}

/* Section Styles */
.section {{
    margin-bottom: 4rem;
    padding: 2rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 15px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}}

.section-title {{
    font-size: 2rem;
    font-weight: 600;
    color: {theme['colors']['primary']};
    margin-bottom: 2rem;
    text-align: center;
}}

/* Card Styles */
.experience-card, .project-card, .education-card {{
    background: rgba(255, 255, 255, 0.1);
    padding: 1.5rem;
    border-radius: 10px;
    margin-bottom: 1.5rem;
    border-left: 4px solid {theme['colors']['accent']};
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    cursor: pointer;
}}

.experience-card:hover, .project-card:hover, .education-card:hover {{
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}}

.company-name, .project-title, .institute-name {{
    font-size: 1.3rem;
    font-weight: 600;
    color: {theme['colors']['primary']};
    margin-bottom: 0.5rem;
}}

.position, .degree {{
    font-size: 1.1rem;
    color: {theme['colors']['secondary']};
    margin-bottom: 1rem;
}}

.skills-used, .tech-stack {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    font-size: 0.9rem;
    color: {theme['colors']['accent']};
}}

/* Skills Grid */
.skills-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
}}

.skill-tag {{
    background: linear-gradient(135deg, {theme['colors']['primary']}, {theme['colors']['secondary']});
    color: white;
    padding: 0.8rem 1.2rem;
    border-radius: 25px;
    text-align: center;
    font-weight: 500;
    transition: transform 0.3s ease;
    cursor: pointer;
}}

.skill-tag:hover {{
    transform: scale(1.05);
}}

/* Contact Styles */
.contact-item {{
    background: rgba(255, 255, 255, 0.1);
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    border-left: 3px solid {theme['colors']['primary']};
}}

/* Responsive Design */
@media (max-width: 768px) {{
    .header {{
        flex-direction: column;
        gap: 2rem;
    }}
    
    .navigation {{
        flex-wrap: wrap;
        justify-content: center;
    }}
    
    .name {{
        font-size: 2rem;
    }}
    
    .section {{
        padding: 1rem;
    }}
}}
"""

    # Add style-specific CSS
    if style == "futuristic":
        base_css += f"""
/* Futuristic Animations */
@keyframes glow {{
    0%, 100% {{ box-shadow: 0 0 5px {theme['colors']['primary']}; }}
    50% {{ box-shadow: 0 0 20px {theme['colors']['primary']}, 0 0 30px {theme['colors']['accent']}; }}
}}

.avatar {{
    animation: glow 2s infinite;
}}

.section {{
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(124, 58, 237, 0.1));
}}
"""
    elif style == "playful":
        base_css += f"""
/* Playful Animations */
@keyframes bounce {{
    0%, 20%, 50%, 80%, 100% {{ transform: translateY(0); }}
    40% {{ transform: translateY(-10px); }}
    60% {{ transform: translateY(-5px); }}
}}

.skill-tag:hover {{
    animation: bounce 0.6s;
}}

.section {{
    background: linear-gradient(45deg, rgba(245, 158, 11, 0.1), rgba(236, 72, 153, 0.1));
}}
"""

    return base_css

def generate_js_content(style):
    base_js = """
// Smooth scrolling for navigation links
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        const targetSection = document.querySelector(targetId);
        if (targetSection) {
            targetSection.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Component selection for Gemini editing
let selectedComponent = null;

document.querySelectorAll('[data-component]').forEach(component => {
    component.addEventListener('click', function(e) {
        e.stopPropagation();
        
        // Remove previous selection
        if (selectedComponent) {
            selectedComponent.classList.remove('selected-component');
        }
        
        // Add selection to current component
        this.classList.add('selected-component');
        selectedComponent = this;
        
        // Show edit options
        showEditOptions(this);
    });
});

// Remove selection when clicking outside
document.addEventListener('click', function() {
    if (selectedComponent) {
        selectedComponent.classList.remove('selected-component');
        selectedComponent = null;
        hideEditOptions();
    }
});

function showEditOptions(component) {
    // Remove existing edit panel
    const existingPanel = document.querySelector('.edit-panel');
    if (existingPanel) {
        existingPanel.remove();
    }
    
    // Create edit panel
    const editPanel = document.createElement('div');
    editPanel.className = 'edit-panel';
    editPanel.innerHTML = `
        <div class="edit-panel-content">
            <h3>Edit Component</h3>
            <textarea id="edit-instructions" placeholder="Describe how you want to modify this component..."></textarea>
            <div class="edit-buttons">
                <button onclick="applyGeminiEdit()">Apply Changes</button>
                <button onclick="hideEditOptions()">Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(editPanel);
}

function hideEditOptions() {
    const editPanel = document.querySelector('.edit-panel');
    if (editPanel) {
        editPanel.remove();
    }
}

async function applyGeminiEdit() {
    const instructions = document.getElementById('edit-instructions').value;
    if (!instructions || !selectedComponent) return;
    
    try {
        const response = await fetch('/modify-component', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                component_html: selectedComponent.outerHTML,
                instructions: instructions,
                component_type: selectedComponent.dataset.component
            })
        });
        
        const result = await response.json();
        if (result.success) {
            selectedComponent.outerHTML = result.modified_html;
            hideEditOptions();
            
            // Show success message
            showNotification('Component updated successfully!', 'success');
        } else {
            showNotification('Failed to update component: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Error updating component: ' + error.message, 'error');
    }
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Add CSS for edit functionality
const editStyles = `
.selected-component {
    outline: 3px solid #00d4ff !important;
    outline-offset: 2px;
    position: relative;
}

.edit-panel {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    z-index: 1000;
    min-width: 400px;
}

.edit-panel-content h3 {
    margin-bottom: 1rem;
    color: #333;
}

.edit-panel textarea {
    width: 100%;
    height: 100px;
    margin-bottom: 1rem;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 5px;
    resize: vertical;
}

.edit-buttons {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
}

.edit-buttons button {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-weight: 500;
}

.edit-buttons button:first-child {
    background: #00d4ff;
    color: white;
}

.edit-buttons button:last-child {
    background: #6b7280;
    color: white;
}

.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 2rem;
    border-radius: 5px;
    color: white;
    font-weight: 500;
    z-index: 1001;
}

.notification.success {
    background: #10b981;
}

.notification.error {
    background: #ef4444;
}
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = editStyles;
document.head.appendChild(styleSheet);
"""

    return base_js

app = Flask(__name__)
CORS(app)

# Create directories
UPLOAD_FOLDER = 'uploads'
GENERATED_FOLDER = 'generated_websites'
for folder in [UPLOAD_FOLDER, GENERATED_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy', 
        'message': 'Portfolio to Resume Converter is running',
        'version': '1.0.0',
        'features': [
            'Professional portfolio scraping',
            'AI-powered data extraction',
            'LaTeX resume generation',
            'PDF output',
            'Multiple templates'
        ]
    })

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify system functionality"""
    try:
        # Test basic functionality
        test_data = {
            "name": "Test Developer",
            "title": "Full Stack Developer",
            "Contact_Info": {
                "email": "test@example.com",
                "phone": "+1-234-567-8900",
                "github": "https://github.com/test",
                "linkedin": "https://linkedin.com/in/test"
            },
            "skills": ["JavaScript", "React", "Node.js", "Python"],
            "projects": [
                {
                    "title": "Test Project",
                    "desc": "A test project for verification",
                    "tech": ["React", "Node.js"],
                    "github": "https://github.com/test/project",
                    "demo": "https://test-project.vercel.app"
                }
            ],
            "education": [
                {
                    "Institute_name": "Test University",
                    "Degree_name": "Computer Science",
                    "marks": "3.8"
                }
            ],
            "Experience": [
                {
                    "Company": "Test Company",
                    "Position": "Developer",
                    "Skills": ["React", "Node.js"]
                }
            ],
            "Achievements": [
                {
                    "achievement_name": "Test Certification",
                    "description": "Professional Development"
                }
            ]
        }
        
        # Test LaTeX generation
        latex_content = generate_enhanced_latex_resume(test_data, "professional")
        
        return jsonify({
            'status': 'success',
            'message': 'System test completed successfully',
            'test_data': test_data,
            'latex_generated': len(latex_content) > 0,
            'latex_length': len(latex_content)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'System test failed: {str(e)}',
            'error': str(e)
        }), 500

@app.route('/', methods=['POST'])
def upload_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file'}), 400

        # Save and process file
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        try:
            file.save(filepath)
            
            # Extract text from PDF
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if len(pdf_reader.pages) > 0:
                    content = pdf_reader.pages[0].extract_text()
                else:
                    return jsonify({'error': 'PDF file has no pages'}), 400
            
            if not content:
                return jsonify({'error': 'Could not extract text from PDF'}), 400
            
            # Parse with GROQ
            info = get_all_info(content)
            
            # Convert to dict for website generation
            data = {
                "name": info.name,
                "education": [{"Institute_name": edu.Institute_name, "Degree_name": edu.Degree_name, "Marks": edu.marks} for edu in info.Education],
                "Contact_Info": info.Contact_Info,
                "skills": info.Skills,
                "projects": [{"title": p.project_name, "desc": p.about_project, "tech": p.skills_used} for p in info.Projects],
                "Experience": [{"Company": exp.Company_name, "Position": exp.Position_name, "Skills": exp.skills_used} for exp in info.Experience],
                "Achievements": [{"achievement_name": a.Achivement_name, "institute_name": a.institute_name, "description": a.about} for a in info.Achivements],
                "Position_of_responsibility": [{"position_name": p.Position_name, "soc_name": p.Society_name, "description": p.Description} for p in info.Position_of_Responsibility]
            }
            
            return jsonify({
                'success': True,
                'data': data,
                'message': 'Resume parsed successfully'
            })
            
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': f'Failed to process resume: {str(e)}'}), 500

@app.route('/generate-website', methods=['POST'])
def generate_website():
    try:
        request_data = request.get_json()
        resume_data = request_data.get('data')
        style = request_data.get('style', 'professional')
        
        if not resume_data:
            return jsonify({'error': 'No resume data provided'}), 400
        
        # Generate website code
        website_code = generate_website_code(resume_data, style)
        
        # Create unique folder for this website
        website_id = str(uuid.uuid4())
        website_folder = os.path.join(app.config['GENERATED_FOLDER'], website_id)
        os.makedirs(website_folder)
        
        # Save files
        with open(os.path.join(website_folder, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(website_code['html'])
        
        with open(os.path.join(website_folder, 'styles.css'), 'w', encoding='utf-8') as f:
            f.write(website_code['css'])
        
        with open(os.path.join(website_folder, 'script.js'), 'w', encoding='utf-8') as f:
            f.write(website_code['js'])
        
        return jsonify({
            'success': True,
            'website_id': website_id,
            'preview_url': f'/preview/{website_id}',
            'download_url': f'/download/{website_id}'
        })
        
    except Exception as e:
        print(f"Error generating website: {str(e)}")
        return jsonify({'error': f'Failed to generate website: {str(e)}'}), 500

@app.route('/modify-component', methods=['POST'])
def modify_component():
    try:
        request_data = request.get_json()
        component_html = request_data.get('component_html')
        instructions = request_data.get('instructions')
        component_type = request_data.get('component_type')
        
        if not all([component_html, instructions, component_type]):
            return jsonify({'error': 'Missing required data'}), 400
        
        # Use Gemini to modify the component
        prompt = f"""
        You are a web developer. I have an HTML component that I want to modify based on user instructions.
        
        Current HTML component:
        {component_html}
        
        Component type: {component_type}
        
        User instructions: {instructions}
        
        Please provide the modified HTML component that follows the user's instructions while maintaining the same structure and CSS classes. Only return the HTML code, no explanations.
        """
        
        response = gemini_model.generate_content(prompt)
        modified_html = response.text.strip()
        
        # Clean up the response (remove markdown formatting if present)
        if modified_html.startswith('```html'):
            modified_html = modified_html[7:]
        if modified_html.endswith('```'):
            modified_html = modified_html[:-3]
        
        return jsonify({
            'success': True,
            'modified_html': modified_html.strip()
        })
        
    except Exception as e:
        print(f"Error modifying component: {str(e)}")
        return jsonify({'error': f'Failed to modify component: {str(e)}'}), 500

@app.route('/preview/<website_id>')
def preview_website(website_id):
    try:
        website_folder = os.path.join(app.config['GENERATED_FOLDER'], website_id)
        index_path = os.path.join(website_folder, 'index.html')
        
        if not os.path.exists(index_path):
            return "Website not found", 404
        
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    except Exception as e:
        return f"Error loading preview: {str(e)}", 500

@app.route('/download/<website_id>')
def download_website(website_id):
    try:
        website_folder = os.path.join(app.config['GENERATED_FOLDER'], website_id)
        
        if not os.path.exists(website_folder):
            return jsonify({'error': 'Website not found'}), 404
        
        # Create zip file
        zip_path = os.path.join(tempfile.gettempdir(), f'portfolio_{website_id}.zip')
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_name in ['index.html', 'styles.css', 'script.js']:
                file_path = os.path.join(website_folder, file_name)
                if os.path.exists(file_path):
                    zipf.write(file_path, file_name)
        
        return send_file(zip_path, as_attachment=True, download_name=f'portfolio_website.zip')
        
    except Exception as e:
        return jsonify({'error': f'Failed to create download: {str(e)}'}), 500

@app.route('/convert-portfolio', methods=['POST'])
def convert_portfolio():
    """Convert portfolio URL to resume data with enhanced logging"""
    try:
        request_data = request.get_json()
        portfolio_url = request_data.get('portfolioUrl')
        template = request_data.get('template', 'professional')
        
        print(f"\n🔄 PORTFOLIO CONVERSION REQUEST")
        print(f"URL: {portfolio_url}")
        print(f"Template: {template}")
        
        if not portfolio_url:
            print("❌ Error: No portfolio URL provided")
            return jsonify({'error': 'Portfolio URL is required'}), 400
        
        # Use enhanced extraction
        print("🔍 Starting enhanced portfolio data extraction...")
        resume_data = enhanced_portfolio_data_extraction(portfolio_url)
        
        print(f"✅ Portfolio conversion completed successfully!")
        print(f" Final data summary:")
        print(f"   Name: {resume_data.get('name', 'N/A')}")
        print(f"   Title: {resume_data.get('title', 'N/A')}")
        print(f"   Skills: {len(resume_data.get('skills', {}))} categories")
        print(f"   Projects: {len(resume_data.get('projects', []))} projects")
        
        return jsonify({
            'success': True,
            'data': resume_data,
            'template': template,
            'message': 'Portfolio converted to professional resume successfully'
        })
        
    except Exception as e:
        print(f"❌ Portfolio conversion error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to convert portfolio: {str(e)}'}), 500

@app.route('/generate-resume-pdf', methods=['POST'])
def generate_resume_pdf():
    """Generate high-quality professional PDF resume from LaTeX"""
    try:
        request_data = request.get_json()
        resume_data = request_data.get('resumeData')
        template = request_data.get('template', 'professional')
        
        if not resume_data:
            return jsonify({'error': 'Resume data is required'}), 400
        
        print(f"🔄 Generating professional LaTeX resume with template: {template}")
        print(f" Resume data for: {resume_data.get('name', 'Unknown')}")
        
        # Generate professional LaTeX content
        latex_content = generate_enhanced_latex_resume(resume_data, template)
        print(f"✅ LaTeX content generated successfully")
        
        # Compile LaTeX to professional PDF
        print(" Compiling LaTeX to professional PDF...")
        try:
            pdf_bytes = generate_pdf_from_latex(latex_content, resume_data)
        except Exception as e:
            print(f"❌ LaTeX compilation failed: {str(e)}")
            print("🔄 Using fallback PDF generation...")
            pdf_bytes = generate_pdf_fallback(resume_data)
        
        print(f"✅ Professional PDF resume generated successfully!")
        print(f" PDF Size: {len(pdf_bytes):,} bytes")
        
        # Return PDF as response
        response = send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'professional-resume-{template}.pdf'
        )
        
        return response
        
    except Exception as e:
        print(f"❌ Error generating professional resume PDF: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate professional resume PDF: {str(e)}'}), 500

# Add this function after the scrape_portfolio function
def enhanced_portfolio_data_extraction(portfolio_url: str) -> dict:
    """Enhanced portfolio data extraction with comprehensive logging"""
    print(f"🔍 Starting enhanced data extraction for: {portfolio_url}")
    
    try:
        # Scrape portfolio
        portfolio_text = scrape_portfolio(portfolio_url)
        print(f"✅ Portfolio scraping completed. Text length: {len(portfolio_text)}")
        
        # Extract structured data
        extracted_data = extract_resume_data_from_portfolio(portfolio_text)
        print(f"✅ AI data extraction completed")
        
        # Parse with enhanced validation
        parsed_info = get_all_info(extracted_data['extracted_text'])
        print(f"✅ Data parsing completed")
        
        # Convert to comprehensive resume format
        resume_data = {
            "name": parsed_info.name or "Professional Developer",
            "title": get_professional_title(parsed_info.Skills),
            "about": generate_professional_summary(parsed_info),
            "Contact_Info": enhance_contact_info(parsed_info.Contact_Info),
            "skills": categorize_skills(parsed_info.Skills),
            "projects": enhance_projects(parsed_info.Projects),
            "education": enhance_education(parsed_info.Education),
            "experience": enhance_experience(parsed_info.Experience),
            "achievements": enhance_achievements(parsed_info.Achivements)
        }
        
        print(f"📊 Extracted Data Summary:")
        print(f"    Name: {resume_data['name']}")
        print(f"   💼 Title: {resume_data['title']}")
        print(f"   🛠️ Skills: {len(resume_data['skills'])} categories")
        print(f"    Projects: {len(resume_data['projects'])} projects")
        print(f"   🎓 Education: {len(resume_data['education'])} entries")
        print(f"   💼 Experience: {len(resume_data['experience'])} entries")
        
        return resume_data
        
    except Exception as e:
        print(f"❌ Enhanced extraction failed: {str(e)}")
        # Return professional fallback data
        return create_professional_fallback_data(portfolio_url)

def get_professional_title(skills: List[str]) -> str:
    """Determine professional title based on skills"""
    skill_text = ' '.join(skills).lower()
    
    if any(tech in skill_text for tech in ['full stack', 'fullstack']):
        return "Senior Full Stack Developer"
    elif any(tech in skill_text for tech in ['frontend', 'react', 'vue', 'angular']):
        return "Frontend Developer"
    elif any(tech in skill_text for tech in ['backend', 'node', 'python', 'java']):
        return "Backend Developer"
    elif any(tech in skill_text for tech in ['devops', 'aws', 'docker', 'kubernetes']):
        return "DevOps Engineer"
    else:
        return "Software Developer"

def categorize_skills(skills: List[str]) -> dict:
    """Categorize skills for professional presentation"""
    categories = {
        "Frontend": [],
        "Backend": [],
        "Database": [],
        "DevOps & Tools": [],
        "Other": []
    }
    
    for skill in skills:
        skill_lower = skill.lower()
        if any(tech in skill_lower for tech in ['html', 'css', 'javascript', 'react', 'vue', 'angular', 'next', 'tailwind']):
            categories["Frontend"].append(skill)
        elif any(tech in skill_lower for tech in ['node', 'python', 'java', 'php', 'express', 'fastapi', 'django']):
            categories["Backend"].append(skill)
        elif any(tech in skill_lower for tech in ['mongodb', 'postgresql', 'mysql', 'redis', 'sql']):
            categories["Database"].append(skill)
        elif any(tech in skill_lower for tech in ['docker', 'kubernetes', 'aws', 'git', 'ci/cd', 'jenkins']):
            categories["DevOps & Tools"].append(skill)
        else:
            categories["Other"].append(skill)
    
    return categories

# Add these helper functions after the categorize_skills function
def generate_professional_summary(parsed_info) -> str:
    """Generate professional summary from parsed data"""
    skills = parsed_info.Skills or []
    experience = parsed_info.Experience or []
    
    if experience:
        return f"Experienced {len(experience)}+ years in software development with expertise in {', '.join(skills[:5])}. Passionate about creating scalable, maintainable solutions and contributing to innovative projects."
    else:
        return f"Skilled software developer with expertise in {', '.join(skills[:5])}. Passionate about modern technologies and best practices in software development."

def enhance_contact_info(contact_info: dict) -> dict:
    """Enhance contact information with proper formatting"""
    enhanced = {}
    
    if contact_info.get('email'):
        enhanced['email'] = contact_info['email']
    if contact_info.get('phone'):
        enhanced['phone'] = contact_info['phone']
    if contact_info.get('github'):
        # Ensure GitHub URL is clean and complete
        github_url = contact_info['github']
        if not github_url.startswith('http'):
            github_url = f"https://{github_url}"
        enhanced['github'] = github_url
    if contact_info.get('linkedin'):
        # Ensure LinkedIn URL is clean and complete
        linkedin_url = contact_info['linkedin']
        if not linkedin_url.startswith('http'):
            linkedin_url = f"https://{linkedin_url}"
        enhanced['linkedin'] = linkedin_url
    
    return enhanced

def enhance_projects(projects: List[Project]) -> List[dict]:
    """Enhance project data for professional presentation with proper links"""
    enhanced = []
    
    for project in projects:
        # Extract GitHub and demo links from project description if available
        github_link = ''
        demo_link = ''
        
        # Look for common link patterns in project description
        if hasattr(project, 'about_project') and project.about_project:
            desc = project.about_project.lower()
            if 'github.com' in desc:
                # Extract GitHub link
                import re
                github_match = re.search(r'github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+', desc)
                if github_match:
                    github_link = f"https://{github_match.group()}"
            
            if any(word in desc for word in ['demo', 'live', 'vercel', 'netlify', 'heroku']):
                # Extract demo link
                demo_match = re.search(r'https?://[^\s]+', desc)
                if demo_match:
                    demo_link = demo_match.group()
        
        enhanced_project = {
            'name': project.project_name or 'Web Application',
            'description': project.about_project or 'Professional web application built with modern technologies',
            'technologies': project.skills_used or ['React', 'Node.js'],
            'github': github_link,
            'demo': demo_link,
            'link': github_link or demo_link or 'https://github.com/username/project'
        }
        enhanced.append(enhanced_project)
    
    return enhanced

def enhance_education(education: List[Education]) -> List[dict]:
    """Enhance education data for professional presentation"""
    enhanced = []
    
    for edu in education:
        enhanced_edu = {
            'degree': edu.Degree_name or 'Bachelor of Science in Computer Science',
            'institution': edu.Institute_name or 'University',
            'duration': '2020-2024',
            'gpa': edu.marks or '3.8/4.0'
        }
        enhanced.append(enhanced_edu)
    
    return enhanced

def enhance_experience(experience: List[Experience]) -> List[dict]:
    """Enhance experience data for professional presentation"""
    enhanced = []
    
    for exp in experience:
        enhanced_exp = {
            'position': exp.Position_name or 'Software Developer',
            'company': exp.Company_name or 'Technology Company',
            'duration': '2022-Present',
            'description': 'Developed and maintained scalable applications',
            'skills': exp.skills_used or ['JavaScript', 'React', 'Node.js']
        }
        enhanced.append(enhanced_exp)
    
    return enhanced

def enhance_achievements(achievements: List[Achivements]) -> List[dict]:
    """Enhance achievements data for professional presentation"""
    enhanced = []
    
    for achievement in achievements:
        enhanced_achievement = {
            'name': achievement.Achivement_name or 'Professional Certification',
            'institution': 'Professional Organization',
            'description': achievement.about or 'Technical expertise and professional development'
        }
        enhanced.append(enhanced_achievement)
    
    return enhanced

def create_professional_fallback_data(portfolio_url: str) -> dict:
    """Create professional fallback data when extraction fails"""
    return {
        "name": "Professional Developer",
        "title": "Full Stack Developer",
        "about": "Experienced software developer with expertise in modern web technologies and best practices. Passionate about creating scalable, maintainable solutions.",
        "Contact_Info": {
            "email": "developer@example.com",
            "phone": "+1-234-567-8900",
            "github": "https://github.com/developer",
            "linkedin": "https://linkedin.com/in/developer"
        },
        "skills": {
            "Frontend": ["React", "Next.js", "TypeScript", "Tailwind CSS"],
            "Backend": ["Node.js", "Python", "Express.js", "FastAPI"],
            "Database": ["MongoDB", "PostgreSQL", "Redis"],
            "DevOps & Tools": ["Docker", "AWS", "Git", "CI/CD"]
        },
        "projects": [
            {
                "title": "Portfolio Website",
                "desc": "Professional portfolio showcasing skills and projects",
                "tech": ["React", "Next.js", "Tailwind CSS"],
                "github": "https://github.com/developer/portfolio",
                "demo": portfolio_url
            }
        ],
        "education": [
            {
                "Institute_name": "University of Technology",
                "Degree_name": "Bachelor of Science in Computer Science",
                "year": "2020--2024",
                "marks": "3.8/4.0"
            }
        ],
        "experience": [
            {
                "Position": "Full Stack Developer",
                "Company": "Tech Solutions Inc",
                "Skills": ["React", "Node.js", "MongoDB", "AWS"]
            }
        ],
        "achievements": [
            {
                "achievement_name": "Professional Certification",
                "description": "Full Stack Development and Cloud Architecture"
            }
        ]
    }

if __name__ == '__main__':
    # Production configuration
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Set production environment
    os.environ['FLASK_ENV'] = os.getenv('FLASK_ENV', 'production')
    os.environ['FLASK_DEBUG'] = os.getenv('FLASK_DEBUG', 'False')
    
    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('generated_websites', exist_ok=True)
    
    print("Starting Portfolio to Resume Converter...")
    print(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
    print(f"Debug Mode: {os.getenv('FLASK_DEBUG', 'False')}")
    
    # Check API configuration
    groq_configured = "Yes" if os.getenv('GROQ_API_KEY') and os.getenv('GROQ_API_KEY') != 'your_groq_api_key_here' else "No"
    gemini_configured = "Yes" if os.getenv('GEMINI_API_KEY') and os.getenv('GEMINI_API_KEY') != 'your_gemini_api_key_here' else "No"
    
    print(f"GROQ API configured: {groq_configured}")
    print(f"Gemini API configured: {gemini_configured}")
    
    if groq_configured == "No" or gemini_configured == "No":
        print("⚠️  Warning: API keys not configured. Please set GROQ_API_KEY and GEMINI_API_KEY in .env file")
    
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true')
