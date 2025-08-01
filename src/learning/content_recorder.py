#!/usr/bin/env python3
"""
Comprehensive Content Recording System
Captures all course content, test questions, and important information for user review
"""

import json
import sqlite3
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from playwright.async_api import Page
import re
import hashlib
import os
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CourseContent:
    """Represents course content item"""
    content_id: str
    course_title: str
    platform: str
    content_type: str  # 'video', 'text', 'quiz', 'assignment', 'reading'
    title: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    duration: Optional[str] = None
    difficulty: Optional[str] = None
    tags: List[str] = None


@dataclass
class TestQuestion:
    """Represents a test question and answer"""
    question_id: str
    course_id: str
    platform: str
    question_text: str
    correct_answer: str
    all_options: List[str]
    explanation: str
    difficulty: str
    topic: str
    timestamp: datetime
    user_answer: str = None
    is_correct: bool = None


@dataclass
class LearningInsight:
    """Represents key learning insights"""
    insight_id: str
    course_id: str
    platform: str
    insight_text: str
    category: str  # 'key_concept', 'tip', 'warning', 'best_practice'
    importance_score: int  # 1-10
    related_topics: List[str]
    timestamp: datetime


class ContentRecorder:
    """Records and manages all course content for later review"""

    def __init__(self, db_path: str = "data/knowledge_base.db"):
        self.db_path = db_path
        self.current_course = None
        self.current_platform = None
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for storing content"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS course_content (
                    content_id TEXT PRIMARY KEY,
                    course_title TEXT,
                    platform TEXT,
                    content_type TEXT,
                    title TEXT,
                    content TEXT,
                    metadata TEXT,
                    timestamp DATETIME,
                    duration TEXT,
                    difficulty TEXT,
                    tags TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_questions (
                    question_id TEXT PRIMARY KEY,
                    course_id TEXT,
                    platform TEXT,
                    question_text TEXT,
                    correct_answer TEXT,
                    all_options TEXT,
                    explanation TEXT,
                    difficulty TEXT,
                    topic TEXT,
                    timestamp DATETIME,
                    user_answer TEXT,
                    is_correct BOOLEAN
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_insights (
                    insight_id TEXT PRIMARY KEY,
                    course_id TEXT,
                    platform TEXT,
                    insight_text TEXT,
                    category TEXT,
                    importance_score INTEGER,
                    related_topics TEXT,
                    timestamp DATETIME
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS course_sessions (
                    session_id TEXT PRIMARY KEY,
                    course_title TEXT,
                    platform TEXT,
                    start_time DATETIME,
                    end_time DATETIME,
                    status TEXT,
                    completion_percentage REAL,
                    certificate_url TEXT
                )
            """)

    async def start_recording_session(self, course_title: str, platform: str, course_url: str):
        """Start a new recording session"""
        self.current_course = course_title
        self.current_platform = platform

        session_id = hashlib.md5(
            f"{course_title}_{platform}_{datetime.now()}".encode()).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO course_sessions 
                (session_id, course_title, platform, start_time, status, completion_percentage)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, course_title, platform, datetime.now(), 'in_progress', 0.0))

        logger.info(
            f"Started recording session for {course_title} on {platform}")
        return session_id

    async def record_page_content(self, page: Page, content_type: str = "text"):
        """Record content from current page"""
        try:
            # Extract page title
            title = await page.title() or "Untitled"

            # Extract main content based on common selectors
            content_selectors = [
                '.course-content', '.lesson-content', '.module-content',
                '.lecture-content', '.article-content', '.main-content',
                '.content-body', '.lesson-text', '.course-material'
            ]

            content = ""
            for selector in content_selectors:
                if await page.is_visible(selector):
                    content = await page.text_content(selector)
                    break

            # If no specific content found, get body text
            if not content:
                content = await page.text_content('body')

            # Clean and process content
            content = self._clean_content(content)

            # Extract metadata
            metadata = await self._extract_page_metadata(page)

            # Create content record
            content_id = hashlib.md5(
                f"{self.current_course}_{title}_{content[:100]}".encode()).hexdigest()

            course_content = CourseContent(
                content_id=content_id,
                course_title=self.current_course,
                platform=self.current_platform,
                content_type=content_type,
                title=title,
                content=content,
                metadata=metadata,
                timestamp=datetime.now(),
                tags=self._extract_tags(content)
            )

            # Save to database
            self._save_content(course_content)

            # Extract and save key insights
            await self._extract_learning_insights(content, content_id)

            logger.info(f"Recorded content: {title[:50]}...")

        except Exception as e:
            logger.error(f"Failed to record page content: {e}")

    async def record_quiz_questions(self, page: Page):
        """Record quiz questions and answers"""
        try:
            # Common quiz selectors
            quiz_selectors = [
                '.quiz-container', '.question-container', '.assessment-container',
                '.test-container', '.exam-container', '.quiz-question'
            ]

            quiz_container = None
            for selector in quiz_selectors:
                if await page.is_visible(selector):
                    quiz_container = selector
                    break

            if not quiz_container:
                return

            # Extract questions
            questions = await page.query_selector_all(f'{quiz_container} .question, {quiz_container} .quiz-item')

            for question_elem in questions:
                try:
                    # Extract question text
                    question_text = await question_elem.text_content()
                    if not question_text:
                        continue

                    # Extract options
                    options = []
                    option_elements = await question_elem.query_selector_all('input[type="radio"], input[type="checkbox"], .option')

                    for option_elem in option_elements:
                        option_text = await option_elem.get_attribute('value') or await option_elem.text_content()
                        if option_text:
                            options.append(option_text.strip())

                    # Try to determine correct answer (various methods)
                    correct_answer = await self._determine_correct_answer(question_elem, options)

                    # Create question record
                    question_id = hashlib.md5(
                        f"{question_text[:100]}_{self.current_course}".encode()).hexdigest()

                    test_question = TestQuestion(
                        question_id=question_id,
                        course_id=self.current_course,
                        platform=self.current_platform,
                        question_text=self._clean_content(question_text),
                        correct_answer=correct_answer,
                        all_options=options,
                        explanation="",  # Will be filled if available
                        difficulty="medium",  # Default
                        topic=self._extract_topic_from_question(question_text),
                        timestamp=datetime.now()
                    )

                    self._save_question(test_question)

                except Exception as e:
                    logger.error(f"Failed to process individual question: {e}")
                    continue

            logger.info(f"Recorded {len(questions)} quiz questions")

        except Exception as e:
            logger.error(f"Failed to record quiz questions: {e}")

    async def record_video_content(self, page: Page):
        """Record video content information"""
        try:
            # Extract video metadata
            video_title = await page.text_content('.video-title, .lecture-title') or "Video Content"

            # Try to get video duration
            duration = None
            duration_selectors = ['.video-duration',
                                  '.duration', '[data-duration]']
            for selector in duration_selectors:
                if await page.is_visible(selector):
                    duration = await page.text_content(selector)
                    break

            # Extract video transcript if available
            transcript = ""
            transcript_selectors = ['.transcript',
                                    '.captions', '.subtitle-text']
            for selector in transcript_selectors:
                if await page.is_visible(selector):
                    transcript = await page.text_content(selector)
                    break

            # Record as course content
            content_id = hashlib.md5(
                f"{self.current_course}_{video_title}_{datetime.now()}".encode()).hexdigest()

            video_content = CourseContent(
                content_id=content_id,
                course_title=self.current_course,
                platform=self.current_platform,
                content_type="video",
                title=video_title,
                content=transcript or f"Video: {video_title}",
                metadata={"video_url": page.url, "duration": duration},
                timestamp=datetime.now(),
                duration=duration,
                tags=self._extract_tags(transcript or video_title)
            )

            self._save_content(video_content)
            logger.info(f"Recorded video content: {video_title}")

        except Exception as e:
            logger.error(f"Failed to record video content: {e}")

    def _clean_content(self, content: str) -> str:
        """Clean and normalize content text"""
        if not content:
            return ""

        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)

        # Remove common navigation/UI elements
        ui_patterns = [
            r'Skip to main content',
            r'Cookie notice',
            r'Privacy policy',
            r'Terms of service',
            r'Navigation menu',
            r'Footer',
            r'Header'
        ]

        for pattern in ui_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)

        return content.strip()

    async def _extract_page_metadata(self, page: Page) -> Dict[str, Any]:
        """Extract metadata from page"""
        metadata = {
            "url": page.url,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Extract meta tags
            meta_elements = await page.query_selector_all('meta')
            for meta in meta_elements:
                name = await meta.get_attribute('name') or await meta.get_attribute('property')
                content = await meta.get_attribute('content')
                if name and content:
                    metadata[name] = content

            # Extract page structure info
            headings = await page.query_selector_all('h1, h2, h3')
            # First 10 headings
            metadata['headings'] = [await h.text_content() for h in headings[:10]]

        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")

        return metadata

    def _extract_tags(self, content: str) -> List[str]:
        """Extract relevant tags from content"""
        if not content:
            return []

        # Common technical terms and concepts
        tag_patterns = {
            'programming': r'\b(python|javascript|java|html|css|sql|api|database)\b',
            'cloud': r'\b(aws|azure|google cloud|kubernetes|docker|serverless)\b',
            'data_science': r'\b(machine learning|data analysis|statistics|visualization|pandas|numpy)\b',
            'marketing': r'\b(seo|sem|analytics|conversion|roi|cpc|ctr|social media)\b',
            'security': r'\b(cybersecurity|encryption|firewall|vulnerability|penetration testing)\b'
        }

        tags = []
        content_lower = content.lower()

        for category, pattern in tag_patterns.items():
            if re.search(pattern, content_lower, re.IGNORECASE):
                tags.append(category)

        # Extract specific technology mentions
        tech_keywords = re.findall(r'\b[A-Z]{2,}(?:\s+[A-Z]{2,})*\b', content)
        tags.extend([kw.lower() for kw in tech_keywords[:5]])  # Limit to 5

        return list(set(tags))

    async def _extract_learning_insights(self, content: str, content_id: str):
        """Extract key learning insights from content"""
        if not content or len(content) < 100:
            return

        # Patterns for identifying important information
        insight_patterns = [
            (r'(?:important|key|note|remember|crucial):\s*([^.!?]+[.!?])', 'key_concept'),
            (r'(?:tip|pro tip|hint):\s*([^.!?]+[.!?])', 'tip'),
            (r'(?:warning|caution|avoid):\s*([^.!?]+[.!?])', 'warning'),
            (r'(?:best practice|recommended):\s*([^.!?]+[.!?])',
             'best_practice'),
        ]

        for pattern, category in insight_patterns:
            matches = re.findall(
                pattern, content, re.IGNORECASE | re.MULTILINE)

            for match in matches[:3]:  # Limit to 3 per category
                insight_id = hashlib.md5(
                    f"{match}_{content_id}".encode()).hexdigest()

                insight = LearningInsight(
                    insight_id=insight_id,
                    course_id=self.current_course,
                    platform=self.current_platform,
                    insight_text=match.strip(),
                    category=category,
                    importance_score=8 if category == 'key_concept' else 6,
                    related_topics=self._extract_tags(match),
                    timestamp=datetime.now()
                )

                self._save_insight(insight)

    async def _determine_correct_answer(self, question_elem, options: List[str]) -> str:
        """Try to determine the correct answer from various sources"""
        try:
            # Look for indicators of correct answer
            correct_indicators = [
                '.correct', '.right-answer', '[data-correct="true"]',
                '.selected.correct', '.answer.correct'
            ]

            for indicator in correct_indicators:
                correct_elem = await question_elem.query_selector(indicator)
                if correct_elem:
                    answer_text = await correct_elem.text_content()
                    if answer_text and answer_text.strip() in options:
                        return answer_text.strip()

            # If no clear indicator, return first option as placeholder
            return options[0] if options else "Unknown"

        except Exception:
            return "Unknown"

    def _extract_topic_from_question(self, question_text: str) -> str:
        """Extract topic/subject from question text"""
        # Simple keyword-based topic extraction
        topics = {
            'python': ['python', 'pandas', 'numpy', 'matplotlib'],
            'javascript': ['javascript', 'js', 'node', 'react', 'vue'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 'serverless'],
            'data_science': ['data', 'analysis', 'statistics', 'machine learning'],
            'marketing': ['marketing', 'seo', 'analytics', 'conversion']
        }

        question_lower = question_text.lower()

        for topic, keywords in topics.items():
            if any(keyword in question_lower for keyword in keywords):
                return topic

        return 'general'

    def _save_content(self, content: CourseContent):
        """Save course content to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO course_content 
                (content_id, course_title, platform, content_type, title, content, 
                 metadata, timestamp, duration, difficulty, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                content.content_id, content.course_title, content.platform,
                content.content_type, content.title, content.content,
                json.dumps(content.metadata), content.timestamp,
                content.duration, content.difficulty, json.dumps(
                    content.tags or [])
            ))

    def _save_question(self, question: TestQuestion):
        """Save test question to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO test_questions 
                (question_id, course_id, platform, question_text, correct_answer,
                 all_options, explanation, difficulty, topic, timestamp, user_answer, is_correct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                question.question_id, question.course_id, question.platform,
                question.question_text, question.correct_answer,
                json.dumps(question.all_options), question.explanation,
                question.difficulty, question.topic, question.timestamp,
                question.user_answer, question.is_correct
            ))

    def _save_insight(self, insight: LearningInsight):
        """Save learning insight to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO learning_insights 
                (insight_id, course_id, platform, insight_text, category,
                 importance_score, related_topics, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                insight.insight_id, insight.course_id, insight.platform,
                insight.insight_text, insight.category, insight.importance_score,
                json.dumps(insight.related_topics), insight.timestamp
            ))

    def get_course_content(self, course_title: str = None, platform: str = None) -> List[CourseContent]:
        """Retrieve course content with optional filters"""
        query = "SELECT * FROM course_content WHERE 1=1"
        params = []

        if course_title:
            query += " AND course_title = ?"
            params.append(course_title)

        if platform:
            query += " AND platform = ?"
            params.append(platform)

        query += " ORDER BY timestamp DESC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)

            content_list = []
            for row in cursor.fetchall():
                content = CourseContent(
                    content_id=row['content_id'],
                    course_title=row['course_title'],
                    platform=row['platform'],
                    content_type=row['content_type'],
                    title=row['title'],
                    content=row['content'],
                    metadata=json.loads(row['metadata'] or '{}'),
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    duration=row['duration'],
                    difficulty=row['difficulty'],
                    tags=json.loads(row['tags'] or '[]')
                )
                content_list.append(content)

            return content_list

    def get_test_questions(self, course_id: str = None, topic: str = None) -> List[TestQuestion]:
        """Retrieve test questions with optional filters"""
        query = "SELECT * FROM test_questions WHERE 1=1"
        params = []

        if course_id:
            query += " AND course_id = ?"
            params.append(course_id)

        if topic:
            query += " AND topic = ?"
            params.append(topic)

        query += " ORDER BY timestamp DESC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)

            questions = []
            for row in cursor.fetchall():
                question = TestQuestion(
                    question_id=row['question_id'],
                    course_id=row['course_id'],
                    platform=row['platform'],
                    question_text=row['question_text'],
                    correct_answer=row['correct_answer'],
                    all_options=json.loads(row['all_options'] or '[]'),
                    explanation=row['explanation'],
                    difficulty=row['difficulty'],
                    topic=row['topic'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    user_answer=row['user_answer'],
                    is_correct=row['is_correct']
                )
                questions.append(question)

            return questions

    def search_content(self, query: str, content_type: str = None) -> List[Dict[str, Any]]:
        """Search through all recorded content"""
        search_query = """
            SELECT content_id, course_title, platform, content_type, title, content, timestamp
            FROM course_content 
            WHERE (title LIKE ? OR content LIKE ?)
        """
        params = [f"%{query}%", f"%{query}%"]

        if content_type:
            search_query += " AND content_type = ?"
            params.append(content_type)

        search_query += " ORDER BY timestamp DESC LIMIT 50"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(search_query, params)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'content_id': row['content_id'],
                    'course_title': row['course_title'],
                    'platform': row['platform'],
                    'content_type': row['content_type'],
                    'title': row['title'],
                    'snippet': row['content'][:200] + "..." if len(row['content']) > 200 else row['content'],
                    'timestamp': row['timestamp']
                })

            return results

    def export_knowledge_base(self, format: str = "json") -> str:
        """Export complete knowledge base"""
        if format == "json":
            return self._export_json()
        elif format == "markdown":
            return self._export_markdown()
        else:
            raise ValueError("Unsupported export format")

    def _export_json(self) -> str:
        """Export knowledge base as JSON"""
        data = {
            'content': [asdict(c) for c in self.get_course_content()],
            'questions': [asdict(q) for q in self.get_test_questions()],
            'export_timestamp': datetime.now().isoformat()
        }

        filename = f"knowledge_base_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        return filename

    def _export_markdown(self) -> str:
        """Export knowledge base as Markdown"""
        content = "# 📚 Cert Me Boi Knowledge Base\n\n"
        content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Group content by course
        courses = {}
        for item in self.get_course_content():
            if item.course_title not in courses:
                courses[item.course_title] = []
            courses[item.course_title].append(item)

        for course_title, items in courses.items():
            content += f"## 🎓 {course_title}\n\n"

            for item in items:
                content += f"### {item.title}\n"
                content += f"**Platform:** {item.platform}\n"
                content += f"**Type:** {item.content_type}\n"
                content += f"**Date:** {item.timestamp.strftime('%Y-%m-%d')}\n\n"
                content += f"{item.content[:500]}...\n\n"

                if item.tags:
                    content += f"**Tags:** {', '.join(item.tags)}\n\n"

                content += "---\n\n"

        filename = f"knowledge_base_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        return filename
