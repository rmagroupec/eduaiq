"""
Initial seed script for Team Members, Blog Categories, and Blog Posts.
Run via: python manage.py shell -c "import content.seed_data; content.seed_data.seed()"
"""
import os
import django
from django.utils import timezone

from content.models import TeamMember, BlogCategory, BlogPost


def seed():
    print("Seeding Content (Team Members, Categories, Blog Posts)...")

    # -------------------------------------------------------------
    # 1. Team Members
    # -------------------------------------------------------------
    members_data = [
        {
            "name": "William Smith",
            "slug": "william-smith",
            "designation": "AI & Data Science Lead",
            "quote": "Empowering young minds with practical AI skills for the next generation of technology.",
            "bio": "William Smith is a leading AI researcher and educator with over 8 years of experience mentoring students in machine learning, computer vision, and Python applications. He oversees the EduAiQ AI Lab hands-on projects.",
            "email": "william@eduaiq.com",
            "phone": "+91 98765 43210",
            "facebook_url": "https://www.facebook.com/",
            "twitter_url": "https://twitter.com/",
            "linkedin_url": "https://www.linkedin.com/",
            "whatsapp_url": "https://whatsapp.com/",
            "instagram_url": "https://www.instagram.com/",
            "qualifications": "# 2013 / 2017: Harvey Mudd College (Computer Science & AI)\n# 2017 / 2019: Stanford Online (Advanced Deep Learning)\n# 2020 / Present: Lead AI Mentor & Author at EduAiQ",
            "experiences": "8+ years in Machine Learning and Curriculum Development. Mentored over 15,000 students in practical AI deployment.",
            "skills_overview": "Completed Projects: 95, AI & Python: 98, Mentorship: 92",
            "order": 1,
            "is_active": True,
        },
        {
            "name": "Jenny White",
            "slug": "jenny-white",
            "designation": "Skill Development Head",
            "quote": "Skills are the true currency of the modern workforce. Learn deeply and build boldly.",
            "bio": "Jenny White specializes in industry-aligned skill development courses, career acceleration frameworks, and enterprise-grade learning paths. She bridges classroom learning with real-world employability.",
            "email": "jenny@eduaiq.com",
            "phone": "+91 98765 43211",
            "facebook_url": "https://www.facebook.com/",
            "twitter_url": "https://twitter.com/",
            "linkedin_url": "https://www.linkedin.com/",
            "whatsapp_url": "https://whatsapp.com/",
            "instagram_url": "https://www.instagram.com/",
            "qualifications": "# 2014 / 2018: Oxford University (Behavioral Learning & Pedagogy)\n# 2019 / 2021: Head of Skill Development at Global EdTech",
            "experiences": "Over a decade designing vocational training curricula, professional development programs, and corporate mentorship channels.",
            "skills_overview": "Program Design: 96, Student Engagement: 94, Career Strategy: 90",
            "order": 2,
            "is_active": True,
        },
        {
            "name": "George Hobbs",
            "slug": "george-hobbs",
            "designation": "Olympiad Curriculum Lead",
            "quote": "Critical thinking and competitive problem-solving begin with solid fundamentals.",
            "bio": "George Hobbs leads the mathematics and science Olympiad training curriculum, having guided national rankers, international competitors, and scholarship winners across India.",
            "email": "george@eduaiq.com",
            "phone": "+91 98765 43212",
            "facebook_url": "https://www.facebook.com/",
            "twitter_url": "https://twitter.com/",
            "linkedin_url": "https://www.linkedin.com/",
            "whatsapp_url": "https://whatsapp.com/",
            "instagram_url": "https://www.instagram.com/",
            "qualifications": "# 2012 / 2016: Indian Institute of Technology (Applied Mathematics)\n# 2017 / 2020: Senior Olympiad Trainer & Assessment Specialist",
            "experiences": "Trained over 50,000 students for National & International Olympiads with a proven 85% qualification rate.",
            "skills_overview": "Olympiad Prep: 99, Mathematics: 97, Assessment Analytics: 91",
            "order": 3,
            "is_active": True,
        },
        {
            "name": "Alice Heard",
            "slug": "alice-heard",
            "designation": "AI Books Author & Curriculum Lead",
            "quote": "Demystifying complex technology into clear, actionable books for every student.",
            "bio": "Alice Heard has authored premier AI handbooks and structured educational modules used across hundreds of partner institutions, colleges, and schools.",
            "email": "alice@eduaiq.com",
            "phone": "+91 98765 43213",
            "facebook_url": "https://www.facebook.com/",
            "twitter_url": "https://twitter.com/",
            "linkedin_url": "https://www.linkedin.com/",
            "whatsapp_url": "https://whatsapp.com/",
            "instagram_url": "https://www.instagram.com/",
            "qualifications": "# 2015 / 2019: University of Cambridge (Computational Linguistics)\n# 2020 / Present: Published Author & Head of AI Publications",
            "experiences": "Authored 12+ top-rated AI books and structured digital learning modules for K-12 and Higher Education.",
            "skills_overview": "Authoring: 98, Curriculum Design: 95, Technical Writing: 93",
            "order": 4,
            "is_active": True,
        },
        {
            "name": "Harrison Scott",
            "slug": "harrison-scott",
            "designation": "Chief Educational Architect",
            "quote": "Transforming education through scalable, student-centric digital ecosystems.",
            "bio": "Harrison Scott leads technological innovation and institutional architecture at EduAiQ, crafting scalable LMS and ERP solutions for modern educational institutions.",
            "email": "harrison@eduaiq.com",
            "phone": "+91 98765 43214",
            "facebook_url": "https://www.facebook.com/",
            "twitter_url": "https://twitter.com/",
            "linkedin_url": "https://www.linkedin.com/",
            "whatsapp_url": "https://whatsapp.com/",
            "instagram_url": "https://www.instagram.com/",
            "qualifications": "# 2010 / 2014: Harvey Mudd College (Software Architecture)\n# 2015 / 2018: Chief Supervisor of Institutional Automation",
            "experiences": "12+ years in building scalable software systems and academic LMS architectures connecting 500+ campuses.",
            "skills_overview": "Completed Projects: 80, Financial Skills: 95, Reliable & Hardworking: 85",
            "order": 5,
            "is_active": True,
        }
    ]

    team_map = {}
    for m in members_data:
        slug = m.pop("slug")
        obj, created = TeamMember.objects.update_or_create(slug=slug, defaults=m)
        team_map[slug] = obj
        action = "Created" if created else "Updated"
        print(f"[{action}] Team Member: {obj.name}")

    # -------------------------------------------------------------
    # 2. Blog Categories
    # -------------------------------------------------------------
    categories_data = [
        {"name": "AI Lab", "slug": "ai-lab", "description": "Hands-on guides and tutorials on Artificial Intelligence and Machine Learning."},
        {"name": "Olympiads", "slug": "olympiads", "description": "Preparation roadmaps, tips, and strategies for national and international Olympiads."},
        {"name": "Careers", "slug": "careers", "description": "Career roadmaps, skill acceleration, and industry hiring trends."},
        {"name": "Ecosystem", "slug": "ecosystem", "description": "Institution ERP, campus automation, LMS workflows, and modern school management."},
        {"name": "Technology", "slug": "technology", "description": "Tech developments, tools, and digital education breakthroughs."},
    ]

    cat_map = {}
    for c in categories_data:
        slug = c.pop("slug")
        obj, created = BlogCategory.objects.update_or_create(slug=slug, defaults=c)
        cat_map[slug] = obj
        action = "Created" if created else "Updated"
        print(f"[{action}] Blog Category: {obj.name}")

    # -------------------------------------------------------------
    # 3. Blog Posts
    # -------------------------------------------------------------
    posts_data = [
        {
            "title": "5 AI Skills Every Student Should Learn in 2026",
            "slug": "5-ai-skills-every-student-should-learn-in-2026",
            "category": cat_map.get("ai-lab"),
            "author_name": "William Smith",
            "author_team_member": team_map.get("william-smith"),
            "summary": "A practical starting list for students beginning in the AI Lab — no prior coding background required. Covers prompt engineering, data literacy, and building real portfolio projects.",
            "content": """<p>AI is no longer a specialist track reserved for computer science majors — it's showing up as a required or preferred skill across marketing, finance, design, healthcare, and operations job listings. The good news is that most students don't need years of coding experience to get started. What matters is knowing which skills actually translate into interview-ready proof of ability. Here are five to prioritize this year.</p>

<h3>1. Prompt Engineering & AI Tool Fluency</h3>
<p>Before writing a single line of code, learn to get reliable, useful output from AI tools themselves. This means structuring clear instructions, breaking large tasks into steps, and knowing when an AI's answer needs to be verified rather than trusted outright. Employers increasingly test for this in take-home assignments, so practicing on real work builds a habit that shows up naturally in interviews.</p>

<h3>2. Data Literacy</h3>
<p>You don't need to be a data scientist, but you do need to be comfortable reading a spreadsheet, spotting a misleading chart, and asking 'where did this number come from?' Free tools like Google Sheets and basic Python notebooks are enough to start. Once you can clean and interpret data, AI tools become far more useful because you can sanity-check what they produce.</p>

<h3>3. Python Fundamentals</h3>
<p>You don't need to master machine learning frameworks on day one. Start with basic scripting — reading files, looping through data, writing small automation scripts. This is the skill that turns 'I used ChatGPT' into 'I built something,' which is what stands out on a resume or in a portfolio project.</p>

<h3>4. Critical Evaluation of AI Output</h3>
<p>As AI tools get better at sounding confident, the skill that matters most is knowing when they're wrong. Practicing this means cross-checking facts, understanding a model's known blind spots, and being able to explain in plain language why a given output should or shouldn't be trusted.</p>

<h3>5. Communicating AI-Assisted Work</h3>
<p>Finally, learn to explain what you built and why — including where AI helped and where your own judgment shaped the result. Employers want to see that you can own the outcome, not just the prompt. A short write-up or a five-minute walkthrough of a project is often the single most convincing thing you can bring to an interview.</p>

<p>None of these require a computer science degree to start. Pick one skill, build a small project around it this month, and add the next one once it feels comfortable — that steady, project-by-project approach is what the AI Lab curriculum is built around.</p>""",
            "tags": "AI Skills, Career Development, Student Guide, Technology",
            "status": "published",
            "is_featured": True,
            "views_count": 1420,
            "published_at": timezone.now() - timezone.timedelta(days=8),
        },
        {
            "title": "How To Prepare For The Math Olympiad In 90 Days",
            "slug": "how-to-prepare-for-the-math-olympiad-in-90-days",
            "category": cat_map.get("olympiads"),
            "author_name": "George Hobbs",
            "author_team_member": team_map.get("george-hobbs"),
            "summary": "A grade-by-grade study plan built around the published Olympiad curriculum, with a suggested weekly schedule for the final three months before exam day.",
            "content": """<p>Preparing for the Math Olympiad can feel daunting, but a structured 90-day roadmap turns overwhelming syllabi into clear, weekly milestones. Here is our mentor-tested schedule to maximize your problem-solving accuracy and speed.</p>

<h3>Month 1: Foundation & Pattern Recognition (Days 1–30)</h3>
<p>The first month focuses strictly on mastering core arithmetic, number theory, algebraic manipulation, and geometric visualization. Dedicate 45 minutes daily to solving non-routine puzzles rather than standard school drills. Key topics include prime factorization, divisibility rules, angles, and modular arithmetic basics.</p>

<h3>Month 2: Timed Practice & Multi-Step Problems (Days 31–60)</h3>
<p>Shift focus toward complex, multi-concept problems. In Olympiads, questions often test geometry and algebra simultaneously. Start practicing with past papers and take one full-length mock assessment every Sunday. Analyze every error: was it a calculation mistake, or a conceptual misstep?</p>

<h3>Month 3: Speed, Accuracy & Full-Length Mocks (Days 61–90)</h3>
<p>In the final month, simulate authentic exam conditions. Work on question triage: identifying low-hanging problems first, skipping stubborn questions, and preserving time for thorough double-checking.</p>

<p>Stay consistent, maintain a personal error-log notebook, and take advantage of EduAiQ's online entrance mocks!</p>""",
            "tags": "Olympiads, Math Prep, Exam Strategy, Study Plan",
            "status": "published",
            "is_featured": True,
            "views_count": 980,
            "published_at": timezone.now() - timezone.timedelta(days=15),
        },
        {
            "title": "From Classroom To AI Lab: A Student's Journey",
            "slug": "from-classroom-to-ai-lab-a-students-journey",
            "category": cat_map.get("careers"),
            "author_name": "Jenny White",
            "author_team_member": team_map.get("jenny-white"),
            "summary": "How one student went from a first AI Lab module to a portfolio-ready project in a single semester, and what they'd do differently starting over.",
            "content": """<p>When Ankit first enrolled in the EduAiQ AI Lab module, he had never written more than ten lines of Python code. Six months later, he successfully built and deployed an automated attendance recognition model for his college departmental lab.</p>

<h3>Overcoming the Initial Intimidation</h3>
<p>'I used to think AI was only for advanced PhD researchers,' Ankit shares. 'EduAiQ's project-first structure broke it down into digestible steps: first we learned how computers see images, then how to feed data into pre-trained models, and finally how to connect the model to a simple web interface.'</p>

<h3>Building Real Artifacts Over Passing Exams</h3>
<p>Rather than memorizing theory, students in the AI Lab build tangible applications. Having a working demo on GitHub gave Ankit the confidence to apply for competitive internships, resulting in two early offers before graduation.</p>

<p>Every student has the potential to become a builder. The right guidance and structured practical curriculum make all the difference.</p>""",
            "tags": "Student Journey, Career, AI Lab, Success Story",
            "status": "published",
            "is_featured": True,
            "views_count": 1150,
            "published_at": timezone.now() - timezone.timedelta(days=23),
        },
        {
            "title": "Why Institutions Are Moving To One Connected LMS",
            "slug": "why-institutions-are-moving-to-one-connected-lms",
            "category": cat_map.get("ecosystem"),
            "author_name": "Harrison Scott",
            "author_team_member": team_map.get("harrison-scott"),
            "summary": "What happens when admission CRM, LMS, and examination management stop living in separate systems — and what to check before your institution switches.",
            "content": """<p>For years, educational institutions operated with fragmented tools: one vendor for admissions, another for student attendance, a third for online courses, and spreadsheets for fees and accounts. This fragmentation causes duplicate data entry, communication gaps, and administrative bottlenecks.</p>

<h3>The Power of Unified Education ERP</h3>
<p>When all academic and administrative pillars connect seamlessly on a unified platform like EduAiQ:</p>
<ul>
  <li><strong>Inquiry to Enrollment:</strong> Leads automatically convert into registered students with allocated course access and ID cards in one click.</li>
  <li><strong>Real-time Analytics:</strong> Principals and directors see attendance trends, exam performance, and fee collections on a single live dashboard.</li>
  <li><strong>Enhanced Student Experience:</strong> Students access Olympiad entrance tests, digital books, video lectures, and quizzes through a single unified portal.</li>
</ul>

<p>Modernize your campus with EduAiQ's all-in-one institutional suite.</p>""",
            "tags": "Education ERP, LMS, Campus Automation, Institutions",
            "status": "published",
            "is_featured": False,
            "views_count": 830,
            "published_at": timezone.now() - timezone.timedelta(days=31),
        }
    ]

    for p in posts_data:
        slug = p.pop("slug")
        obj, created = BlogPost.objects.update_or_create(slug=slug, defaults=p)
        action = "Created" if created else "Updated"
        print(f"[{action}] Blog Post: {obj.title}")

    print("Content Seeding Completed Successfully!")


if __name__ == "__main__":
    seed()
