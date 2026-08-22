import os
import subprocess

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EduAiQ - Master Project Presentation, Role Blueprint & Architecture Guide</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @page {
            size: A4 portrait;
            margin: 10mm 12mm 12mm 12mm;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }

        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #1e293b;
            background: #ffffff;
            line-height: 1.5;
            font-size: 12.5px;
        }

        .page {
            page-break-after: always;
            position: relative;
            padding-bottom: 15px;
        }

        .page:last-child {
            page-break-after: avoid;
        }

        /* Header & Footer */
        .doc-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #f1f5f9;
            padding-bottom: 10px;
            margin-bottom: 18px;
        }

        .doc-logo {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 19px;
            font-weight: 800;
            color: #090D16;
            letter-spacing: -0.5px;
        }

        .doc-logo span {
            color: #fd7e14;
        }

        .doc-badge {
            background: #fff7ed;
            color: #ea580c;
            border: 1px solid #fdba74;
            font-size: 10.5px;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 20px;
            text-transform: uppercase;
        }

        /* Hero / Cover */
        .cover-hero {
            background: linear-gradient(135deg, #090D16 0%, #1e1b4b 60%, #0f172a 100%);
            color: #ffffff;
            border-radius: 14px;
            padding: 32px 28px;
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 8px 24px rgba(9, 13, 22, 0.15);
        }

        .cover-hero::after {
            content: '';
            position: absolute;
            top: -40px;
            right: -40px;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(253, 126, 20, 0.25) 0%, transparent 70%);
            border-radius: 50%;
        }

        .hero-title {
            font-size: 26px;
            font-weight: 800;
            line-height: 1.2;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }

        .hero-title span {
            background: linear-gradient(90deg, #fd7e14, #fbbf24);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero-subtitle {
            font-size: 13.5px;
            color: #cbd5e1;
            max-width: 680px;
            margin-bottom: 16px;
            line-height: 1.5;
        }

        .meta-chips {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .meta-chip {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(5px);
            padding: 5px 12px;
            border-radius: 30px;
            font-size: 11px;
            font-weight: 600;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* Section Headings */
        .section-heading {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 16px;
            font-weight: 800;
            color: #090D16;
            margin-bottom: 14px;
            padding-bottom: 6px;
            border-bottom: 2px solid #e2e8f0;
        }

        .section-heading i {
            color: #fd7e14;
            font-size: 17px;
        }

        .sub-heading {
            font-size: 13.5px;
            font-weight: 700;
            color: #0f172a;
            margin: 12px 0 8px 0;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* Grids & Cards */
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
            margin-bottom: 16px;
        }

        .grid-3 {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }

        .grid-4 {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 16px;
        }

        .feature-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 14px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
            position: relative;
        }

        .feature-card.highlight {
            border-left: 4px solid #fd7e14;
            background: #fffbf5;
        }

        .feature-card.navy-card {
            border-left: 4px solid #090D16;
            background: #f8fafc;
        }

        .feature-card.green-card {
            border-left: 4px solid #10b981;
            background: #f0fdf4;
        }

        .feature-card.purple-card {
            border-left: 4px solid #8b5cf6;
            background: #faf5ff;
        }

        .feature-card.blue-card {
            border-left: 4px solid #3b82f6;
            background: #eff6ff;
        }

        .card-icon {
            width: 34px;
            height: 34px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            margin-bottom: 8px;
        }

        .card-icon.orange { background: #fff7ed; color: #ea580c; border: 1px solid #fdba74; }
        .card-icon.navy { background: #090D16; color: #ffffff; }
        .card-icon.green { background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }
        .card-icon.purple { background: #f3e8ff; color: #7e22ce; border: 1px solid #d8b4fe; }
        .card-icon.blue { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }

        .card-title {
            font-size: 13.5px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 4px;
        }

        .card-desc {
            font-size: 11.5px;
            color: #64748b;
            line-height: 1.45;
        }

        /* Stat Counters */
        .stat-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 12px;
            text-align: center;
        }

        .stat-num {
            font-size: 20px;
            font-weight: 800;
            color: #090D16;
            margin-bottom: 2px;
        }

        .stat-num span {
            color: #fd7e14;
        }

        .stat-lbl {
            font-size: 10.5px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Tables */
        .styled-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 16px;
            font-size: 11.5px;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #e2e8f0;
        }

        .styled-table th {
            background: #090D16;
            color: #ffffff;
            text-align: left;
            padding: 8px 10px;
            font-weight: 700;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .styled-table td {
            padding: 8px 10px;
            border-bottom: 1px solid #f1f5f9;
            color: #334155;
            vertical-align: top;
        }

        .styled-table tr:nth-child(even) td {
            background: #f8fafc;
        }

        .styled-table tr:last-child td {
            border-bottom: none;
        }

        /* Badges & Tags */
        .tag {
            display: inline-block;
            padding: 2px 7px;
            border-radius: 5px;
            font-size: 10px;
            font-weight: 700;
        }
        .tag-green { background: #dcfce7; color: #166534; }
        .tag-orange { background: #ffedd5; color: #9a3412; }
        .tag-blue { background: #dbeafe; color: #1e40af; }
        .tag-purple { background: #f3e8ff; color: #6b21a8; }
        .tag-red { background: #fee2e2; color: #991b1b; }
        .tag-navy { background: #090D16; color: #ffffff; }

        /* Security Pillar Box */
        .security-banner {
            background: linear-gradient(135deg, #1e1b4b, #090D16);
            color: #ffffff;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            border: 1px solid rgba(253, 126, 20, 0.3);
        }

        .sec-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-top: 12px;
        }

        .sec-item {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 10px;
        }

        .sec-title {
            font-size: 12px;
            font-weight: 700;
            color: #fdba74;
            margin-bottom: 3px;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .sec-text {
            font-size: 10.5px;
            color: #cbd5e1;
            line-height: 1.4;
        }

        /* Role Comparison Box */
        .role-box {
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 14px;
            background: #ffffff;
            margin-bottom: 14px;
        }

        .role-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 6px;
            border-bottom: 1.5px solid #f1f5f9;
        }

        .role-title {
            font-size: 14px;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .role-url {
            font-family: 'JetBrains Mono', monospace;
            font-size: 10.5px;
            background: #f1f5f9;
            padding: 3px 8px;
            border-radius: 4px;
            color: #0f172a;
            font-weight: 600;
        }

        .role-body {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }

        .role-col h6 {
            font-size: 11.5px;
            font-weight: 700;
            color: #475569;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }

        .role-list {
            list-style: none;
            padding: 0;
        }

        .role-list li {
            font-size: 11.5px;
            color: #334155;
            margin-bottom: 4px;
            display: flex;
            align-items: flex-start;
            gap: 6px;
            line-height: 1.4;
        }

        .role-list li i {
            font-size: 10px;
            margin-top: 3px;
            flex-shrink: 0;
        }

        .role-list li i.check { color: #16a34a; }
        .role-list li i.arrow { color: #fd7e14; }

        /* Step List */
        .step-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 16px;
        }

        .step-item {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px 14px;
        }

        .step-num {
            width: 24px;
            height: 24px;
            background: #fd7e14;
            color: #ffffff;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 12px;
            flex-shrink: 0;
        }

        .step-content h5 {
            font-size: 12.5px;
            font-weight: 700;
            color: #090D16;
            margin-bottom: 2px;
        }

        .step-content p {
            font-size: 11px;
            color: #64748b;
            line-height: 1.4;
        }

        .footer-note {
            text-align: center;
            font-size: 10.5px;
            color: #94a3b8;
            border-top: 1px solid #e2e8f0;
            padding-top: 8px;
            margin-top: 12px;
        }

        code {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            background: #f1f5f9;
            padding: 1px 4px;
            border-radius: 3px;
            color: #0f172a;
        }
    </style>
</head>
<body>

    <!-- ==================== PAGE 1: EXECUTIVE OVERVIEW & PLATFORM ARCHITECTURE ==================== -->
    <div class="page">
        <div class="doc-header">
            <div class="doc-logo">
                <i class="fas fa-graduation-cap" style="color: #fd7e14;"></i> Edu<span>AiQ</span> Ecosystem
            </div>
            <div class="doc-badge">Master Presentation & Role Blueprint</div>
        </div>

        <div class="cover-hero">
            <div class="hero-title">Next-Gen AI-Powered <span>EdTech Ecosystem</span></div>
            <div class="hero-subtitle">
                EduAiQ is a multi-tenant, enterprise-grade educational ecosystem integrating Student LMS, National Olympiad Arena, Institutional B2B Network, Growth Partner Franchise Kit, and 100% DRM Content Protection.
            </div>
            <div class="meta-chips">
                <div class="meta-chip"><i class="fas fa-crown"></i> Super Admin Dashboard</div>
                <div class="meta-chip"><i class="fas fa-building-columns"></i> B2B Institution Portal</div>
                <div class="meta-chip"><i class="fas fa-chalkboard-user"></i> Teacher & Student Roles</div>
                <div class="meta-chip"><i class="fas fa-shield-alt"></i> DRM Anti-Piracy Suite</div>
                <div class="meta-chip"><i class="fas fa-handshake"></i> Franchise Growth Kit</div>
            </div>
        </div>

        <div class="grid-4">
            <div class="stat-card">
                <div class="stat-num">50<span>+</span></div>
                <div class="stat-lbl">Interactive Courses</div>
            </div>
            <div class="stat-card">
                <div class="stat-num">5<span> Roles</span></div>
                <div class="stat-lbl">RBAC Permission Matrix</div>
            </div>
            <div class="stat-card">
                <div class="stat-num">100<span>%</span></div>
                <div class="stat-lbl">DRM Content Security</div>
            </div>
            <div class="stat-card">
                <div class="stat-num">B2B<span>+</span>B2C</div>
                <div class="stat-lbl">Hybrid Revenue Model</div>
            </div>
        </div>

        <div class="section-heading"><i class="fas fa-users-gear"></i> Master Ecosystem Roles & Access Breakdown</div>
        <table class="styled-table">
            <thead>
                <tr>
                    <th style="width: 18%;">User Role</th>
                    <th style="width: 25%;">Portal / Access URL</th>
                    <th style="width: 32%;">Who Accesses It?</th>
                    <th style="width: 25%;">Primary Responsibilities</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong class="text-primary"><i class="fas fa-crown me-1 text-warning"></i> Super Admin</strong></td>
                    <td><code>/admin-panel/</code></td>
                    <td>Platform Founders, System Admins, Academic Operations Team</td>
                    <td>360° Control, Course CRUD, Financials, User RBAC, CRM Leads</td>
                </tr>
                <tr>
                    <td><strong style="color: #7e22ce;"><i class="fas fa-building-columns me-1"></i> Institution Admin</strong></td>
                    <td><code>/institution_login.html</code><br><code>/institutions/...</code></td>
                    <td>School Principals, College Deans, Academy Directors</td>
                    <td>Bulk Student Onboarding, Batch Analytics, Co-branded Certs</td>
                </tr>
                <tr>
                    <td><strong style="color: #059669;"><i class="fas fa-chalkboard-teacher me-1"></i> Teacher / Faculty</strong></td>
                    <td><code>/admin-panel/</code> (Teacher View)<br><code>/accounts/login/</code></td>
                    <td>Subject Experts, School Teachers, Course Instructors</td>
                    <td>Quiz Creation, Assignment Grading, Timetables, Doubt Solving</td>
                </tr>
                <tr>
                    <td><strong style="color: #ea580c;"><i class="fas fa-user-graduate me-1"></i> Enrolled Student</strong></td>
                    <td><code>/login.html</code><br><code>/my-learning/</code></td>
                    <td>K-12 Students, Olympiad Aspirants, Professional Learners</td>
                    <td>Watch Videos, Read PDFs, Quizzes, Submit Tasks, Download Certs</td>
                </tr>
                <tr>
                    <td><strong style="color: #2563eb;"><i class="fas fa-briefcase me-1"></i> Growth Partner</strong></td>
                    <td><code>/growth-partner-kit/</code><br><code>/apply-for-franchise/</code></td>
                    <td>Franchisees, Educational Consultants, Affiliates</td>
                    <td>Promotional Materials, Custom QR Codes, Lead Commissions</td>
                </tr>
            </tbody>
        </table>

        <div class="footer-note">EduAiQ Master Architecture & Role Guide • Confidential • Page 1 of 5</div>
    </div>

    <!-- ==================== PAGE 2: SUPER ADMIN DASHBOARD DEEP-DIVE ==================== -->
    <div class="page">
        <div class="doc-header">
            <div class="doc-logo">
                <i class="fas fa-graduation-cap" style="color: #fd7e14;"></i> Edu<span>AiQ</span> Super Admin Center
            </div>
            <div class="doc-badge">Control Center Deep-Dive</div>
        </div>

        <div class="section-heading"><i class="fas fa-crown"></i> Super Admin Dashboard Architecture (<code>/admin-panel/</code>)</div>

        <div class="feature-card navy-card" style="margin-bottom: 14px;">
            <div class="card-title"><i class="fas fa-info-circle text-primary me-1"></i> Super Admin Overview & Access Gateway</div>
            <div class="card-desc">
                The Super Admin Dashboard is the central cockpit of EduAiQ. Access is restricted to authorized platform administrators with <code>is_staff=True</code> and <code>is_superuser=True</code>. Accessible at <code>/admin-panel/login.html</code>.
            </div>
        </div>

        <div class="sub-heading"><i class="fas fa-chart-pie text-warning"></i> 1. The 8 Symmetrical Operational KPI Metric Cards</div>
        <div class="grid-4">
            <div class="stat-card" style="border-top: 3px solid #3b82f6;">
                <div class="stat-num"><i class="fas fa-building-columns text-primary"></i></div>
                <div class="stat-lbl">Institutions</div>
                <div style="font-size: 10.5px; color: #64748b; margin-top: 2px;">Partnered Schools & Colleges</div>
            </div>
            <div class="stat-card" style="border-top: 3px solid #fd7e14;">
                <div class="stat-num"><i class="fas fa-book-open text-warning"></i></div>
                <div class="stat-lbl">Courses</div>
                <div style="font-size: 10.5px; color: #64748b; margin-top: 2px;">Published Curriculums</div>
            </div>
            <div class="stat-card" style="border-top: 3px solid #10b981;">
                <div class="stat-num"><i class="fas fa-user-graduate text-success"></i></div>
                <div class="stat-lbl">Students</div>
                <div style="font-size: 10.5px; color: #64748b; margin-top: 2px;">Active Enrolled Learners</div>
            </div>
            <div class="stat-card" style="border-top: 3px solid #8b5cf6;">
                <div class="stat-num"><i class="fas fa-chalkboard-teacher text-purple"></i></div>
                <div class="stat-lbl">Teachers</div>
                <div style="font-size: 10.5px; color: #64748b; margin-top: 2px;">Instructors & Faculty</div>
            </div>
        </div>
        <div class="grid-4">
            <div class="stat-card" style="border-top: 3px solid #ef4444;">
                <div class="stat-num"><i class="fas fa-award text-danger"></i></div>
                <div class="stat-lbl">Olympiads</div>
                <div style="font-size: 10.5px; color: #64748b; margin-top: 2px;">National Contests Active</div>
            </div>
            <div class="stat-card" style="border-top: 3px solid #06b6d4;">
                <div class="stat-num"><i class="fas fa-file-signature text-info"></i></div>
                <div class="stat-lbl">Exam Registrations</div>
                <div style="font-size: 10.5px; color: #64748b; margin-top: 2px;">Student Contest Tickets</div>
            </div>
            <div class="stat-card" style="border-top: 3px solid #f59e0b;">
                <div class="stat-num"><i class="fas fa-users text-warning"></i></div>
                <div class="stat-lbl">Team Members</div>
                <div style="font-size: 10.5px; color: #64748b; margin-top: 2px;">Staff & Advisory Board</div>
            </div>
            <div class="stat-card" style="border-top: 3px solid #ec4899;">
                <div class="stat-num"><i class="fas fa-newspaper text-pink"></i></div>
                <div class="stat-lbl">Blog Posts</div>
                <div style="font-size: 10.5px; color: #64748b; margin-top: 2px;">Articles & Announcements</div>
            </div>
        </div>

        <div class="sub-heading"><i class="fas fa-sliders text-warning"></i> 2. Core Super Admin Capabilities by Module</div>
        <table class="styled-table">
            <thead>
                <tr>
                    <th style="width: 25%;">Section Name</th>
                    <th style="width: 35%;">Admin Features & Tools</th>
                    <th style="width: 40%;">Exact Impact on Main Website</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Course & Module Manager</strong></td>
                    <td>Add/Edit Courses, create sequential Modules, upload Video MP4s/PDFs, set pricing, discounts.</td>
                    <td>Directly updates <code>/courses/</code> catalog, course detail pages, and dynamic lesson player.</td>
                </tr>
                <tr>
                    <td><strong>Olympiad & Exam Engine</strong></td>
                    <td>Schedule national Olympiads, set exam date/time windows, add MCQ question banks, auto-rank.</td>
                    <td>Displays live contests on <code>/olympiads/</code>, generates digital medals and certificates.</td>
                </tr>
                <tr>
                    <td><strong>CRM & Lead Center</strong></td>
                    <td>Track student inquiries, franchise leads, school partnership requests, call logs.</td>
                    <td>Captures inputs from Contact Us, Franchise Forms, and Institutional tie-up forms.</td>
                </tr>
                <tr>
                    <td><strong>Team & Staff Management</strong></td>
                    <td>Add mentors, advisors, founders with real-time photo preview and strict 80px sizing.</td>
                    <td>Directly renders verified leadership grid on public <code>/team/</code> and <code>/about/</code> pages.</td>
                </tr>
                <tr>
                    <td><strong>Financials & Invoices</strong></td>
                    <td>Fee collections, expense heads, transaction logs, discount coupon generation.</td>
                    <td>Applies discount coupons at checkout (e.g. <code>EDUAIQ-50OFF</code>) and validates orders.</td>
                </tr>
            </tbody>
        </table>

        <div class="footer-note">EduAiQ Master Architecture & Role Guide • Confidential • Page 2 of 5</div>
    </div>

    <!-- ==================== PAGE 3: INSTITUTION & TEACHER PORTALS ==================== -->
    <div class="page">
        <div class="doc-header">
            <div class="doc-logo">
                <i class="fas fa-graduation-cap" style="color: #fd7e14;"></i> Edu<span>AiQ</span> B2B & Faculty Portals
            </div>
            <div class="doc-badge">Institution & Teacher Roles</div>
        </div>

        <div class="section-heading"><i class="fas fa-building-columns"></i> B2B Institution Portal (<code>/institution_login.html</code>)</div>

        <div class="role-box" style="border-left: 4px solid #7e22ce;">
            <div class="role-header">
                <div class="role-title" style="color: #7e22ce;">
                    <i class="fas fa-school"></i> Institution Admin Role (School Principals / College Heads)
                </div>
                <div class="role-url">Access: /institution_login.html | Role: institution_admin</div>
            </div>
            <div class="role-body">
                <div class="role-col">
                    <h6><i class="fas fa-shield-check text-success me-1"></i> What Institutions Can Do</h6>
                    <ul class="role-list">
                        <li><i class="fas fa-check-circle check"></i> <strong>Bulk Student Onboarding:</strong> Upload CSVs to register entire school grades and batches in one click.</li>
                        <li><i class="fas fa-check-circle check"></i> <strong>Batch Progress Tracking:</strong> Monitor class-level attendance, module completion %, and average quiz scores.</li>
                        <li><i class="fas fa-check-circle check"></i> <strong>Institutional Olympiad Arena:</strong> Host inter-school and intra-school competitions with customized leaderboards.</li>
                        <li><i class="fas fa-check-circle check"></i> <strong>Co-Branded Certificates:</strong> Issue certificates with School Logo + EduAiQ Certification seals.</li>
                    </ul>
                </div>
                <div class="role-col">
                    <h6><i class="fas fa-globe text-primary me-1"></i> Main Website Visibility</h6>
                    <ul class="role-list">
                        <li><i class="fas fa-arrow-right arrow"></i> <strong>Public Partner Listing:</strong> Partnered school logos appear on the homepage and <code>/institutions/</code> showcase.</li>
                        <li><i class="fas fa-arrow-right arrow"></i> <strong>Tie-Up Lead Pipeline:</strong> Prospective schools can apply via the Institutional Inquiry form on the frontend.</li>
                        <li><i class="fas fa-arrow-right arrow"></i> <strong>Custom School Subdomains:</strong> Support for white-labeled school portals and cohort access keys.</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="section-heading"><i class="fas fa-chalkboard-user"></i> Teacher & Faculty Role (<code>/accounts/login/</code>)</div>

        <div class="role-box" style="border-left: 4px solid #059669;">
            <div class="role-header">
                <div class="role-title" style="color: #059669;">
                    <i class="fas fa-chalkboard-teacher"></i> Teacher / Subject Instructor Role
                </div>
                <div class="role-url">Access: /accounts/login/ | Role: teacher / instructor</div>
            </div>
            <div class="role-body">
                <div class="role-col">
                    <h6><i class="fas fa-tasks text-success me-1"></i> Academic Operations</h6>
                    <ul class="role-list">
                        <li><i class="fas fa-check-circle check"></i> <strong>Curriculum Authoring:</strong> Add lesson descriptions, practice quiz questions, and practical assignment briefs.</li>
                        <li><i class="fas fa-check-circle check"></i> <strong>Assignment Review & Grading:</strong> Review student code, essay submissions, and project files with feedback scores.</li>
                        <li><i class="fas fa-check-circle check"></i> <strong>Timetables & Batches:</strong> Manage class schedules, live session links, and student attendance logs.</li>
                    </ul>
                </div>
                <div class="role-col">
                    <h6><i class="fas fa-star text-warning me-1"></i> Student Interaction</h6>
                    <ul class="role-list">
                        <li><i class="fas fa-arrow-right arrow"></i> <strong>Doubt Resolution:</strong> Respond to chapter questions posted by learners.</li>
                        <li><i class="fas fa-arrow-right arrow"></i> <strong>Teacher Profile on Website:</strong> Teacher bio, qualifications, and courses appear on public course pages.</li>
                        <li><i class="fas fa-arrow-right arrow"></i> <strong>Progress Audits:</strong> Flag struggling students for personalized remedial modules.</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="section-heading"><i class="fas fa-handshake"></i> Growth Partner & Franchise Ecosystem (<code>/growth-partner-kit/</code>)</div>

        <div class="role-box" style="border-left: 4px solid #2563eb;">
            <div class="role-header">
                <div class="role-title" style="color: #2563eb;">
                    <i class="fas fa-briefcase"></i> Growth Partner & Franchisee Role
                </div>
                <div class="role-url">Access: /growth-partner-kit/ | /apply-for-franchise/</div>
            </div>
            <div class="role-body">
                <div class="role-col">
                    <h6><i class="fas fa-kit-medical text-primary me-1"></i> Turnkey Franchise Assets</h6>
                    <ul class="role-list">
                        <li><i class="fas fa-check-circle check"></i> <strong>Marketing Collateral:</strong> Printable posters, brochures, pitch presentations, and flyers.</li>
                        <li><i class="fas fa-check-circle check"></i> <strong>Dynamic QR Codes:</strong> Branded QR codes linking directly to the partner's referral onboarding page.</li>
                        <li><i class="fas fa-check-circle check"></i> <strong>Franchise Playbook:</strong> Step-by-step operational guide for regional training centers.</li>
                    </ul>
                </div>
                <div class="role-col">
                    <h6><i class="fas fa-chart-line text-success me-1"></i> Revenue & Commission Engine</h6>
                    <ul class="role-list">
                        <li><i class="fas fa-arrow-right arrow"></i> <strong>Affiliate Commissions:</strong> Automated revenue-share on every student course or Olympiad enrollment.</li>
                        <li><i class="fas fa-arrow-right arrow"></i> <strong>Lead Management:</strong> Real-time tracking of leads generated in the partner's designated territory.</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="footer-note">EduAiQ Master Architecture & Role Guide • Confidential • Page 3 of 5</div>
    </div>

    <!-- ==================== PAGE 4: STUDENT PORTAL & 100% DRM SECURITY ==================== -->
    <div class="page">
        <div class="doc-header">
            <div class="doc-logo">
                <i class="fas fa-graduation-cap" style="color: #fd7e14;"></i> Edu<span>AiQ</span> Student LMS & DRM
            </div>
            <div class="doc-badge">Student Experience & Security</div>
        </div>

        <div class="section-heading"><i class="fas fa-user-graduate"></i> Enrolled Student Experience (<code>/my-learning/</code> & <code>/lesson/?id=...</code>)</div>

        <div class="grid-2">
            <div class="feature-card highlight">
                <div class="card-icon orange"><i class="fas fa-layer-group"></i></div>
                <div class="card-title">My Learning Dashboard (<code>/my-learning/</code>)</div>
                <div class="card-desc">
                    • Header shows <strong>STUDENT LOGIN</strong> button for authenticated learners.<br>
                    • Course cards with live progress bars (e.g. 45% Completed).<br>
                    • 1-Click resume button jumping directly to the student's next unread chapter.<br>
                    • Instant access to earned certificates upon achieving 100% progress.
                </div>
            </div>
            <div class="feature-card navy-card">
                <div class="card-icon navy"><i class="fas fa-trophy"></i></div>
                <div class="card-title">National Olympiad Arena (<code>/olympiads/</code>)</div>
                <div class="card-desc">
                    • Browse active and upcoming national Olympiad competitions.<br>
                    • Secure exam player with live countdown timer and anti-cheat window monitoring.<br>
                    • Automated grading with instant score calculation and rank leaderboards.<br>
                    • Downloadable verifiable digital achievement certificate & e-medal.
                </div>
            </div>
        </div>

        <div class="section-heading"><i class="fas fa-shield-virus"></i> 100% DRM-Grade Zero-Piracy Content Security Suite</div>

        <div class="security-banner">
            <div style="font-size: 14px; font-weight: 800; margin-bottom: 4px; color: #fd7e14;">
                <i class="fas fa-lock me-2"></i> Client-Side Anti-Theft & Screen Recording Protection Suite
            </div>
            <p style="font-size: 11.5px; color: #cbd5e1;">
                EduAiQ implements a defense-in-depth security barrier protecting all video lectures, PDF study materials, and written notes from unauthorized screen captures, copying, or leakage.
            </p>
            <div class="sec-grid">
                <div class="sec-item">
                    <div class="sec-title"><i class="fas fa-desktop"></i> Anti-PrintScreen Blackout</div>
                    <div class="sec-text">Captures <code>PrtScn</code>, <code>Win+Shift+S</code>, <code>Mac Cmd+Shift</code>, instantly blacking out the screen and wiping the clipboard with security warnings.</div>
                </div>
                <div class="sec-item">
                    <div class="sec-title"><i class="fas fa-eye-slash"></i> Loss-of-Focus 40px Blur</div>
                    <div class="sec-text">When Snipping Tool, OBS, or screen recording software is launched, the player triggers an immediate 40px heavy blur to prevent recording.</div>
                </div>
                <div class="sec-item">
                    <div class="sec-title"><i class="fas fa-fingerprint"></i> Dynamic User Watermark</div>
                    <div class="sec-text">Student username, User ID, and live timestamp continuously drift across the video/PDF canvas, deterring phone camera recordings.</div>
                </div>
                <div class="sec-item">
                    <div class="sec-title"><i class="fas fa-mouse-pointer"></i> Global Anti-Copy & Inspect</div>
                    <div class="sec-text">Right-click context menu, text selection, dragging, <code>F12</code>, <code>Ctrl+Shift+I</code>, View Source (<code>Ctrl+U</code>) completely blocked.</div>
                </div>
                <div class="sec-item">
                    <div class="sec-title"><i class="fas fa-file-pdf"></i> Canvas-Isolated PDF Engine</div>
                    <div class="sec-text">PDF documents render directly to isolated HTML5 canvas elements with disabled downloads, preventing raw PDF URL theft.</div>
                </div>
                <div class="sec-item">
                    <div class="sec-title"><i class="fas fa-video"></i> Multi-Format Video Stream</div>
                    <div class="sec-text">Direct MP4/WebM video streaming with strict cross-origin policies, eliminating YouTube Error 153 and download buttons.</div>
                </div>
            </div>
        </div>

        <div class="sub-heading"><i class="fas fa-play text-warning"></i> Multi-Format Lesson Player Capabilities (<code>/lesson/?id=...</code>)</div>
        <table class="styled-table">
            <thead>
                <tr>
                    <th style="width: 22%;">Content Format</th>
                    <th style="width: 48%;">Player Experience & Smart Fallback</th>
                    <th style="width: 30%;">DRM Protection Layer</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Video Lectures</strong></td>
                    <td>Full-width HTML5 player with multi-codec MP4/WebM support + YouTube/Vimeo embeds.</td>
                    <td>Download disabled (<code>nodownload noplaybackrate</code>), floating watermark.</td>
                </tr>
                <tr>
                    <td><strong>PDF Study Notes</strong></td>
                    <td>Interactive PDF.js canvas viewer with page navigation controls (Prev / Next).</td>
                    <td>Direct download links removed, right-click blocked, watermark overlay.</td>
                </tr>
                <tr>
                    <td><strong>Reading Articles</strong></td>
                    <td>Formatted typography with clear heading hierarchy and estimated reading time.</td>
                    <td>Unselectable text (<code>user-select: none !important</code>), copy blocked.</td>
                </tr>
                <tr>
                    <td><strong>Practical Tasks</strong></td>
                    <td>Module practical tasks with skip-for-now and mandatory end-of-course submission logic.</td>
                    <td>Secure file upload endpoint with teacher grading review.</td>
                </tr>
            </tbody>
        </table>

        <div class="footer-note">EduAiQ Master Architecture & Role Guide • Confidential • Page 4 of 5</div>
    </div>

    <!-- ==================== PAGE 5: BUSINESS MODEL & PRESENTATION PITCH PLAYBOOK ==================== -->
    <div class="page">
        <div class="doc-header">
            <div class="doc-logo">
                <i class="fas fa-graduation-cap" style="color: #fd7e14;"></i> Edu<span>AiQ</span> Pitch & Business Guide
            </div>
            <div class="doc-badge">Presentation Playbook</div>
        </div>

        <div class="section-heading"><i class="fas fa-chart-line"></i> Hybrid Business Model & Revenue Streams</div>

        <div class="grid-4">
            <div class="feature-card highlight">
                <div class="card-icon orange"><i class="fas fa-shopping-cart"></i></div>
                <div class="card-title">B2C Course Sales</div>
                <div class="card-desc">Direct enrollment revenue from professional skills, coding, English, and certification courses.</div>
            </div>
            <div class="feature-card green-card">
                <div class="card-icon green"><i class="fas fa-medal"></i></div>
                <div class="card-title">Olympiad Fees</div>
                <div class="card-desc">Registration charges for national-level Olympiads and certified skill assessments.</div>
            </div>
            <div class="feature-card navy-card">
                <div class="card-icon navy"><i class="fas fa-building-columns"></i></div>
                <div class="card-title">B2B School Licenses</div>
                <div class="card-desc">Annual institutional subscription packages for K-12 schools, colleges, and coaching institutes.</div>
            </div>
            <div class="feature-card purple-card">
                <div class="card-icon purple"><i class="fas fa-users-gear"></i></div>
                <div class="card-title">Partner Franchises</div>
                <div class="card-desc">Franchise onboarding kits, affiliate revenue-share & regional growth partner territory licenses.</div>
            </div>
        </div>

        <div class="section-heading"><i class="fas fa-microphone-lines"></i> How to Pitch EduAiQ: The 5-Step Live Demo Script</div>

        <div class="step-list">
            <div class="step-item">
                <div class="step-num">1</div>
                <div class="step-content">
                    <h5>Step 1: Welcome & Homepage Presentation (<code>/</code>)</h5>
                    <p>Open the homepage. Highlight the modern design, glowing capsule offer marquee banner, verified leadership team, AI books showcase, and clean header navigation (<strong>LOGIN</strong> for visitors vs <strong>STUDENT LOGIN</strong> for enrolled learners).</p>
                </div>
            </div>
            <div class="step-item">
                <div class="step-num">2</div>
                <div class="step-content">
                    <h5>Step 2: Course Exploration & Student Enrollment (<code>/courses/</code>)</h5>
                    <p>Demonstrate course discovery, filter by categories, transparent pricing with discount badges, and 1-click student enrollment leading into the personal <code>/my-learning/</code> portal.</p>
                </div>
            </div>
            <div class="step-item">
                <div class="step-num">3</div>
                <div class="step-content">
                    <h5>Step 3: The DRM-Protected Lesson Player & Live PrtScn Demo (<code>/lesson/?id=...</code>)</h5>
                    <p>Open a lesson. Show seamless video playback. Press <kbd>PrtScn</kbd> or <kbd>Win+Shift+S</kbd> on your keyboard to demonstrate the instant <strong>Blackout Security Shield</strong> and dynamic user watermark! Show how right-click and text copy are completely blocked.</p>
                </div>
            </div>
            <div class="step-item">
                <div class="step-num">4</div>
                <div class="step-content">
                    <h5>Step 4: The 8-in-1 Central Super Admin Dashboard (<code>/admin-panel/</code>)</h5>
                    <p>Log in as Super Admin. Walk through the balanced 4x2 KPI metric grid, create a new course module, demonstrate video/PDF uploads, and show the real-time photo preview on Team Member edit pages.</p>
                </div>
            </div>
            <div class="step-item">
                <div class="step-num">5</div>
                <div class="step-content">
                    <h5>Step 5: Pitching B2B Institutions & Growth Franchise Kit (<code>/growth-partner-kit/</code>)</h5>
                    <p>Showcase the ready-to-print marketing kits, branded QR codes, and institutional school partnership portals, proving that EduAiQ is ready for immediate nationwide scaling and monetization.</p>
                </div>
            </div>
        </div>

        <div class="section-heading"><i class="fas fa-server"></i> Full-Stack Technical Stack Summary</div>
        <div class="grid-3">
            <div class="feature-card">
                <div class="card-title text-primary"><i class="fab fa-python text-warning me-1"></i> Backend Architecture</div>
                <div class="card-desc">Python 3.12, Django 5.x, Django REST Framework, Custom User Model, Session & JWT Authentication.</div>
            </div>
            <div class="feature-card">
                <div class="card-title text-primary"><i class="fab fa-html5 text-danger me-1"></i> Frontend Design System</div>
                <div class="card-desc">Responsive Vanilla CSS, Vanilla JS ES6+, PDF.js Engine, FontAwesome 6, Bootstrap 5.3 Framework.</div>
            </div>
            <div class="feature-card">
                <div class="card-title text-primary"><i class="fas fa-shield-alt text-success me-1"></i> Security & Reliability</div>
                <div class="card-desc">CSRF protection, XSS sanitization, DRM client-side shields, SQLite / PostgreSQL production ready.</div>
            </div>
        </div>

        <div class="footer-note">EduAiQ Master Architecture & Presentation Blueprint • Complete Pitch Playbook • Page 5 of 5</div>
    </div>

</body>
</html>
"""

# 1. Save HTML to file
html_path = os.path.abspath("EduAiQ_Master_Presentation_and_Role_Blueprint.html")
pdf_path_project = os.path.abspath("EduAiQ_Complete_Project_Presentation_Summary.pdf")
pdf_path_drive = r"E:\EduAiQ_Complete_Project_Presentation_Summary.pdf"

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"HTML saved to: {html_path}")

# 2. Run Edge Headless to compile PDF
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(edge_path):
    edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

cmd = [
    edge_path,
    "--headless",
    "--disable-gpu",
    "--run-all-compositor-stages-before-draw",
    "--print-to-pdf-no-header",
    f"--print-to-pdf={pdf_path_project}",
    html_path
]

print("Compiling PDF with Microsoft Edge...")
result = subprocess.run(cmd, capture_output=True, text=True)

if os.path.exists(pdf_path_project) and os.path.getsize(pdf_path_project) > 1000:
    import shutil
    shutil.copyfile(pdf_path_project, pdf_path_drive)
    print(f"SUCCESS: Master PDF generated successfully at:\n{pdf_path_project}\nand copied to:\n{pdf_path_drive} (Size: {os.path.getsize(pdf_path_project)} bytes)")
else:
    print("PDF generation failed:", result.stderr)
