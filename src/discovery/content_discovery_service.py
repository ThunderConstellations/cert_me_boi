#!/usr/bin/env python3
"""
Smart Content Discovery Engine
AI-powered system to discover and recommend relevant courses and certifications
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import aiohttp
import sqlite3
import redis
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import nltk
import spacy
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("spaCy model not found. Installing...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

logger = logging.getLogger(__name__)


@dataclass
class CourseRecommendation:
    """Represents a course recommendation"""
    course_id: str
    title: str
    provider: str
    platform: str
    url: str
    description: str
    skills: List[str]
    difficulty: str
    duration: str
    rating: float
    reviews_count: int
    trending_score: float
    market_demand_score: float
    personalization_score: float
    total_score: float
    category: str
    subcategory: str
    certificate_type: str
    is_free: bool
    prerequisites: List[str]
    career_paths: List[str]
    last_updated: datetime


@dataclass
class TrendingTopic:
    """Represents a trending topic in tech/certification space"""
    topic: str
    trend_score: float
    growth_rate: float
    related_skills: List[str]
    job_mentions: int
    course_count: int
    avg_salary: Optional[int]
    regions: List[str]
    timestamp: datetime


@dataclass
class SkillMarketData:
    """Market data for specific skills"""
    skill: str
    demand_score: float
    supply_score: float
    avg_salary: int
    job_postings: int
    growth_projection: float
    top_companies: List[str]
    related_certifications: List[str]
    geographic_demand: Dict[str, float]


class SmartContentDiscovery:
    """AI-powered content discovery and recommendation engine"""

    def __init__(self, db_path: str = "data/knowledge_base.db", redis_url: str = "redis://localhost:6379/1"):
        self.db_path = db_path
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000, stop_words='english')
        self.app = FastAPI(
            title="Smart Content Discovery Engine", version="1.0.0")
        self._setup_routes()
        self._init_database()

        # Web scraping configuration
        self.scrapy_settings = {
            'USER_AGENT': 'CertMeBot/1.0 (+https://github.com/ThunderConstellations/cert_me_boi)',
            'ROBOTSTXT_OBEY': True,
            'DOWNLOAD_DELAY': 1,
            'RANDOMIZE_DOWNLOAD_DELAY': True,
            'CONCURRENT_REQUESTS': 8,
            'COOKIES_ENABLED': False,
        }

        # Platform-specific scraping configs
        self.platform_configs = {
            'coursera': {
                'base_url': 'https://www.coursera.org',
                'course_list_url': 'https://www.coursera.org/courses',
                'selectors': {
                    'course_cards': '.cds-CommonCard-container',
                    'title': '[data-testid="course-name"]',
                    'provider': '.cds-CommonCard-subtitle',
                    'rating': '.cds-CommonCard-ratings',
                    'difficulty': '.cds-CommonCard-difficulty'
                }
            },
            'edx': {
                'base_url': 'https://www.edx.org',
                'course_list_url': 'https://www.edx.org/search',
                'selectors': {
                    'course_cards': '.discovery-card',
                    'title': '.discovery-card-title',
                    'provider': '.discovery-card-org'
                }
            },
            'udemy': {
                'base_url': 'https://www.udemy.com',
                'course_list_url': 'https://www.udemy.com/courses/',
                'selectors': {
                    'course_cards': '[data-testid="course-card"]',
                    'title': '[data-testid="course-title"]',
                    'instructor': '[data-testid="instructor-name"]'
                }
            }
        }

        # Job market data sources
        self.job_apis = {
            'linkedin': 'https://www.linkedin.com/jobs/search/',
            'indeed': 'https://indeed.com/jobs',
            'glassdoor': 'https://www.glassdoor.com/Job/jobs.htm',
            'stackoverflow': 'https://stackoverflow.com/jobs'
        }

    def _setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        @self.app.get("/recommendations/{user_id}")
        async def get_recommendations(user_id: str, limit: int = 10):
            try:
                recommendations = await self.get_personalized_recommendations(user_id, limit)
                return {"recommendations": [asdict(r) for r in recommendations]}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/trending")
        async def get_trending_topics(limit: int = 20):
            try:
                trends = await self.get_trending_topics(limit)
                return {"trending": [asdict(t) for t in trends]}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/market-analysis/{skill}")
        async def get_market_analysis(skill: str):
            try:
                analysis = await self.analyze_skill_market_demand(skill)
                return {"analysis": asdict(analysis)}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/update-trends")
        async def update_trends():
            try:
                await self.update_trending_data()
                return {"status": "success", "message": "Trends updated successfully"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def _init_database(self):
        """Initialize database tables for discovery engine"""
        with sqlite3.connect(self.db_path) as conn:
            # Course recommendations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS course_recommendations (
                    course_id TEXT PRIMARY KEY,
                    title TEXT,
                    provider TEXT,
                    platform TEXT,
                    url TEXT,
                    description TEXT,
                    skills TEXT,
                    difficulty TEXT,
                    duration TEXT,
                    rating REAL,
                    reviews_count INTEGER,
                    trending_score REAL,
                    market_demand_score REAL,
                    total_score REAL,
                    category TEXT,
                    is_free BOOLEAN,
                    last_updated DATETIME
                )
            """)

            # Trending topics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trending_topics (
                    topic TEXT PRIMARY KEY,
                    trend_score REAL,
                    growth_rate REAL,
                    related_skills TEXT,
                    job_mentions INTEGER,
                    course_count INTEGER,
                    avg_salary INTEGER,
                    timestamp DATETIME
                )
            """)

            # Market data table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS skill_market_data (
                    skill TEXT PRIMARY KEY,
                    demand_score REAL,
                    supply_score REAL,
                    avg_salary INTEGER,
                    job_postings INTEGER,
                    growth_projection REAL,
                    top_companies TEXT,
                    related_certifications TEXT,
                    last_updated DATETIME
                )
            """)

            # User preferences table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    preferred_skills TEXT,
                    career_goals TEXT,
                    experience_level TEXT,
                    time_availability TEXT,
                    learning_style TEXT,
                    budget_preference TEXT,
                    last_updated DATETIME
                )
            """)

    async def get_personalized_recommendations(self, user_id: str, limit: int = 10) -> List[CourseRecommendation]:
        """Get personalized course recommendations for a user"""
        try:
            # Get user preferences and history
            user_profile = await self._get_user_profile(user_id)
            completed_courses = await self._get_user_completed_courses(user_id)

            # Get all available courses
            all_courses = await self._get_all_courses()

            # Calculate personalization scores
            recommendations = []
            for course in all_courses:
                personalization_score = await self._calculate_personalization_score(
                    course, user_profile, completed_courses
                )

                course.personalization_score = personalization_score
                course.total_score = (
                    course.trending_score * 0.3 +
                    course.market_demand_score * 0.3 +
                    personalization_score * 0.4
                )

                recommendations.append(course)

            # Sort by total score and return top recommendations
            recommendations.sort(key=lambda x: x.total_score, reverse=True)
            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {e}")
            return []

    async def get_trending_topics(self, limit: int = 20) -> List[TrendingTopic]:
        """Get current trending topics in tech/certification space"""
        try:
            # Check cache first
            cached_trends = self.redis_client.get("trending_topics")
            if cached_trends:
                trends_data = json.loads(cached_trends)
                return [TrendingTopic(**trend) for trend in trends_data[:limit]]

            # If not cached, generate trends
            await self.update_trending_data()

            # Retrieve from database
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM trending_topics 
                    ORDER BY trend_score DESC 
                    LIMIT ?
                """, (limit,))

                trends = []
                for row in cursor.fetchall():
                    trend = TrendingTopic(
                        topic=row['topic'],
                        trend_score=row['trend_score'],
                        growth_rate=row['growth_rate'],
                        related_skills=json.loads(
                            row['related_skills'] or '[]'),
                        job_mentions=row['job_mentions'],
                        course_count=row['course_count'],
                        avg_salary=row['avg_salary'],
                        regions=[],  # Could be added later
                        timestamp=datetime.fromisoformat(row['timestamp'])
                    )
                    trends.append(trend)

                return trends

        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
            return []

    async def analyze_skill_market_demand(self, skill: str) -> SkillMarketData:
        """Analyze market demand for a specific skill"""
        try:
            # Check cache first
            cache_key = f"market_analysis:{skill.lower()}"
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return SkillMarketData(**json.loads(cached_data))

            # Collect market data from multiple sources
            job_data = await self._scrape_job_market_data(skill)
            salary_data = await self._get_salary_insights(skill)
            growth_data = await self._analyze_skill_growth_trends(skill)

            # Calculate demand and supply scores
            demand_score = self._calculate_demand_score(job_data, growth_data)
            supply_score = self._calculate_supply_score(skill)

            market_data = SkillMarketData(
                skill=skill,
                demand_score=demand_score,
                supply_score=supply_score,
                avg_salary=salary_data.get('avg_salary', 0),
                job_postings=job_data.get('total_postings', 0),
                growth_projection=growth_data.get('growth_rate', 0),
                top_companies=job_data.get('top_companies', []),
                related_certifications=await self._get_related_certifications(skill),
                geographic_demand=job_data.get('geographic_distribution', {})
            )

            # Cache for 6 hours
            self.redis_client.setex(
                cache_key, 21600, json.dumps(asdict(market_data)))

            return market_data

        except Exception as e:
            logger.error(f"Error analyzing market demand for {skill}: {e}")
            return SkillMarketData(
                skill=skill, demand_score=0, supply_score=0, avg_salary=0,
                job_postings=0, growth_projection=0, top_companies=[],
                related_certifications=[], geographic_demand={}
            )

    async def update_trending_data(self):
        """Update trending topics and market data"""
        try:
            logger.info("Starting trending data update...")

            # Scrape multiple sources for trending topics
            tech_trends = await self._scrape_tech_trends()
            course_trends = await self._analyze_course_popularity()
            job_trends = await self._analyze_job_market_trends()

            # Combine and analyze trends
            combined_trends = self._combine_trend_sources(
                tech_trends, course_trends, job_trends)

            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                for trend in combined_trends:
                    conn.execute("""
                        INSERT OR REPLACE INTO trending_topics 
                        (topic, trend_score, growth_rate, related_skills, job_mentions, 
                         course_count, avg_salary, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trend.topic, trend.trend_score, trend.growth_rate,
                        json.dumps(trend.related_skills), trend.job_mentions,
                        trend.course_count, trend.avg_salary, trend.timestamp
                    ))

            # Cache for quick access
            trends_data = [asdict(trend) for trend in combined_trends]
            self.redis_client.setex(
                "trending_topics", 3600, json.dumps(trends_data))

            logger.info(f"Updated {len(combined_trends)} trending topics")

        except Exception as e:
            logger.error(f"Error updating trending data: {e}")

    async def _scrape_course_data(self, platform: str, category: str = None) -> List[Dict]:
        """Scrape course data from specified platform"""
        try:
            config = self.platform_configs.get(platform)
            if not config:
                logger.warning(
                    f"No configuration found for platform: {platform}")
                return []

            async with aiohttp.ClientSession() as session:
                url = config['course_list_url']
                if category:
                    url += f"?category={category}"

                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(
                            f"Failed to fetch from {platform}: {response.status}")
                        return []

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    courses = []
                    course_cards = soup.select(
                        config['selectors']['course_cards'])

                    # Limit to avoid overwhelming
                    for card in course_cards[:50]:
                        try:
                            course_data = {
                                'platform': platform,
                                'title': self._extract_text(card, config['selectors'].get('title')),
                                'provider': self._extract_text(card, config['selectors'].get('provider')),
                                'url': self._extract_link(card, config['base_url']),
                                'description': self._extract_text(card, '.description, .summary'),
                                'rating': self._extract_rating(card, config['selectors'].get('rating')),
                                'difficulty': self._extract_text(card, config['selectors'].get('difficulty')),
                                'scraped_at': datetime.now().isoformat()
                            }

                            if course_data['title']:  # Only add if we got a title
                                courses.append(course_data)

                        except Exception as e:
                            logger.warning(f"Error parsing course card: {e}")
                            continue

                    return courses

        except Exception as e:
            logger.error(f"Error scraping {platform}: {e}")
            return []

    async def _scrape_tech_trends(self) -> List[Dict]:
        """Scrape trending topics from tech news sources"""
        sources = [
            'https://stackoverflow.com/tags',
            'https://github.com/trending',
            'https://news.ycombinator.com',
            'https://techcrunch.com',
        ]

        trends = []

        async with aiohttp.ClientSession() as session:
            for source in sources:
                try:
                    async with session.get(source) as response:
                        if response.status == 200:
                            html = await response.text()
                            extracted_trends = self._extract_trends_from_html(
                                html, source)
                            trends.extend(extracted_trends)

                except Exception as e:
                    logger.warning(f"Error scraping {source}: {e}")

        return trends

    def _extract_trends_from_html(self, html: str, source: str) -> List[Dict]:
        """Extract trending topics from HTML content"""
        soup = BeautifulSoup(html, 'html.parser')
        trends = []

        if 'stackoverflow' in source:
            # Extract popular tags
            tags = soup.select('.tag-cell .post-tag')
            for tag in tags[:20]:
                trends.append({
                    'topic': tag.get_text().strip(),
                    'source': 'stackoverflow',
                    'trend_score': 0.8  # Default score
                })

        elif 'github' in source:
            # Extract trending repositories
            repos = soup.select('.repo-list-item h3 a')
            for repo in repos[:10]:
                topic = repo.get_text().strip().split('/')[-1]
                trends.append({
                    'topic': topic,
                    'source': 'github',
                    'trend_score': 0.9
                })

        return trends

    async def _analyze_job_market_trends(self) -> List[Dict]:
        """Analyze job market for trending skills"""
        # This would integrate with job APIs in a real implementation
        # For now, return sample trending job skills
        return [
            {'topic': 'artificial intelligence',
                'job_mentions': 15000, 'growth_rate': 45.2},
            {'topic': 'kubernetes', 'job_mentions': 8500, 'growth_rate': 38.7},
            {'topic': 'react', 'job_mentions': 12000, 'growth_rate': 25.3},
            {'topic': 'python', 'job_mentions': 20000, 'growth_rate': 22.1},
            {'topic': 'cloud computing', 'job_mentions': 18000, 'growth_rate': 35.8},
        ]

    def _combine_trend_sources(self, tech_trends: List[Dict], course_trends: List[Dict],
                               job_trends: List[Dict]) -> List[TrendingTopic]:
        """Combine trends from multiple sources and calculate scores"""
        trend_scores = {}

        # Process tech trends
        for trend in tech_trends:
            topic = trend['topic'].lower()
            trend_scores[topic] = trend_scores.get(
                topic, 0) + trend.get('trend_score', 0.5)

        # Process job trends
        for trend in job_trends:
            topic = trend['topic'].lower()
            job_weight = min(trend.get('job_mentions', 0) /
                             1000, 5.0)  # Cap at 5.0
            trend_scores[topic] = trend_scores.get(topic, 0) + job_weight

        # Convert to TrendingTopic objects
        trending_topics = []
        for topic, score in trend_scores.items():
            if score > 1.0:  # Only include topics with meaningful score
                trending_topic = TrendingTopic(
                    topic=topic,
                    trend_score=min(score, 10.0),  # Cap at 10.0
                    growth_rate=self._estimate_growth_rate(topic, job_trends),
                    related_skills=self._get_related_skills_for_topic(topic),
                    job_mentions=self._get_job_mentions(topic, job_trends),
                    course_count=self._get_course_count(topic),
                    avg_salary=self._estimate_avg_salary(topic),
                    regions=['Global'],  # Default
                    timestamp=datetime.now()
                )
                trending_topics.append(trending_topic)

        return sorted(trending_topics, key=lambda x: x.trend_score, reverse=True)

    def _estimate_growth_rate(self, topic: str, job_trends: List[Dict]) -> float:
        """Estimate growth rate for a topic"""
        for trend in job_trends:
            if trend['topic'].lower() == topic.lower():
                return trend.get('growth_rate', 15.0)
        return 15.0  # Default growth rate

    def _get_related_skills_for_topic(self, topic: str) -> List[str]:
        """Get related skills for a topic"""
        skill_mappings = {
            'artificial intelligence': ['machine learning', 'deep learning', 'python', 'tensorflow'],
            'kubernetes': ['docker', 'cloud computing', 'devops', 'containerization'],
            'react': ['javascript', 'frontend', 'web development', 'nodejs'],
            'python': ['data science', 'machine learning', 'backend', 'automation'],
            'cloud computing': ['aws', 'azure', 'devops', 'infrastructure']
        }
        return skill_mappings.get(topic, [])

    def _get_job_mentions(self, topic: str, job_trends: List[Dict]) -> int:
        """Get job mentions count for a topic"""
        for trend in job_trends:
            if trend['topic'].lower() == topic.lower():
                return trend.get('job_mentions', 0)
        return 0

    def _get_course_count(self, topic: str) -> int:
        """Get estimated course count for a topic"""
        # This would query actual course database in real implementation
        return np.random.randint(50, 500)

    def _estimate_avg_salary(self, topic: str) -> int:
        """Estimate average salary for a topic/skill"""
        salary_estimates = {
            'artificial intelligence': 120000,
            'kubernetes': 110000,
            'react': 95000,
            'python': 100000,
            'cloud computing': 105000,
        }
        return salary_estimates.get(topic, 80000)

    # Helper methods for text extraction
    def _extract_text(self, element, selector: str) -> str:
        """Extract text from element using selector"""
        if not selector:
            return ""
        try:
            found = element.select_one(selector)
            return found.get_text().strip() if found else ""
        except:
            return ""

    def _extract_link(self, element, base_url: str) -> str:
        """Extract link from element"""
        try:
            link_elem = element.select_one('a')
            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                if href.startswith('http'):
                    return href
                else:
                    return urljoin(base_url, href)
        except:
            pass
        return ""

    def _extract_rating(self, element, selector: str) -> float:
        """Extract rating from element"""
        if not selector:
            return 0.0
        try:
            rating_elem = element.select_one(selector)
            if rating_elem:
                rating_text = rating_elem.get_text().strip()
                # Extract number from rating text
                import re
                numbers = re.findall(r'[\d.]+', rating_text)
                if numbers:
                    return float(numbers[0])
        except:
            pass
        return 0.0

    async def run_server(self, host: str = "0.0.0.0", port: int = 8002):
        """Run the FastAPI server"""
        config = uvicorn.Config(self.app, host=host,
                                port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

# Placeholder implementations for methods referenced but not fully implemented
    async def _get_user_profile(self, user_id: str) -> Dict:
        """Get user profile and preferences"""
        return {
            'preferred_skills': ['python', 'machine learning'],
            'career_goals': ['data scientist'],
            'experience_level': 'intermediate',
            'time_availability': '10-15 hours/week'
        }

    async def _get_user_completed_courses(self, user_id: str) -> List[str]:
        """Get list of courses completed by user"""
        return []

    async def _get_all_courses(self) -> List[CourseRecommendation]:
        """Get all available courses"""
        # Return sample courses for now
        return [
            CourseRecommendation(
                course_id="python-basics",
                title="Python for Beginners",
                provider="FreeCodeCamp",
                platform="freecodecamp",
                url="https://freecodecamp.org/python",
                description="Learn Python programming from scratch",
                skills=["python", "programming"],
                difficulty="beginner",
                duration="40 hours",
                rating=4.8,
                reviews_count=15000,
                trending_score=8.5,
                market_demand_score=9.0,
                personalization_score=0.0,
                total_score=0.0,
                category="programming",
                subcategory="python",
                certificate_type="completion",
                is_free=True,
                prerequisites=[],
                career_paths=["software developer", "data scientist"],
                last_updated=datetime.now()
            )
        ]

    async def _calculate_personalization_score(self, course: CourseRecommendation,
                                               user_profile: Dict, completed_courses: List[str]) -> float:
        """Calculate personalization score for a course"""
        score = 5.0  # Base score

        # Check skill alignment
        user_skills = user_profile.get('preferred_skills', [])
        course_skills = course.skills
        skill_overlap = len(set(user_skills) & set(course_skills))
        score += skill_overlap * 2.0

        # Check difficulty alignment
        user_level = user_profile.get('experience_level', 'intermediate')
        if course.difficulty == user_level:
            score += 2.0

        # Avoid completed courses
        if course.course_id in completed_courses:
            score *= 0.1

        return min(score, 10.0)

    async def _scrape_job_market_data(self, skill: str) -> Dict:
        """Scrape job market data for a skill"""
        return {
            'total_postings': 5000,
            'top_companies': ['Google', 'Microsoft', 'Amazon'],
            'geographic_distribution': {'US': 0.4, 'Europe': 0.3, 'Asia': 0.3}
        }

    async def _get_salary_insights(self, skill: str) -> Dict:
        """Get salary insights for a skill"""
        return {'avg_salary': 95000}

    async def _analyze_skill_growth_trends(self, skill: str) -> Dict:
        """Analyze growth trends for a skill"""
        return {'growth_rate': 25.5}

    def _calculate_demand_score(self, job_data: Dict, growth_data: Dict) -> float:
        """Calculate demand score based on job and growth data"""
        job_score = min(job_data.get('total_postings', 0) / 1000, 10.0)
        growth_score = min(growth_data.get('growth_rate', 0) / 10, 10.0)
        return (job_score + growth_score) / 2

    def _calculate_supply_score(self, skill: str) -> float:
        """Calculate supply score for a skill"""
        return 6.5  # Sample score

    async def _get_related_certifications(self, skill: str) -> List[str]:
        """Get related certifications for a skill"""
        cert_mappings = {
            'python': ['Python Institute PCAP', 'Python Institute PCPP'],
            'aws': ['AWS Solutions Architect', 'AWS Developer'],
            'azure': ['Azure Fundamentals', 'Azure Administrator'],
        }
        return cert_mappings.get(skill.lower(), [])

    async def _analyze_course_popularity(self) -> List[Dict]:
        """Analyze course popularity trends"""
        return []


async def main():
    """Main function to run the discovery service"""
    discovery = SmartContentDiscovery()

    # Start background task to update trends
    asyncio.create_task(update_trends_periodically(discovery))

    # Run the server
    await discovery.run_server()


async def update_trends_periodically(discovery: SmartContentDiscovery):
    """Background task to update trends periodically"""
    while True:
        try:
            await discovery.update_trending_data()
            await asyncio.sleep(3600)  # Update every hour
        except Exception as e:
            logger.error(f"Error in periodic trend update: {e}")
            await asyncio.sleep(300)  # Retry in 5 minutes

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
