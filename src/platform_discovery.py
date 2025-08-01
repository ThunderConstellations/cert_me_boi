#!/usr/bin/env python3
"""
Platform Discovery System
Helps users find the best free certification opportunities across all supported platforms
"""

import requests
import yaml
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class CertificationOpportunity:
    """Represents a certification opportunity"""
    platform: str
    title: str
    provider: str
    category: str
    difficulty: str
    duration: str
    url: str
    is_free: bool
    prerequisites: List[str]
    skills_covered: List[str]
    certificate_type: str
    value_score: int


class PlatformDiscovery:
    """Discovers and catalogs free certification opportunities"""

    def __init__(self):
        self.platforms = self._load_platform_config()
        self.opportunities = []

        # Pre-curated certification opportunities
        self.certification_catalog = {
            'freecodecamp': [
                {
                    'title': 'Responsive Web Design',
                    'category': 'Web Development',
                    'difficulty': 'Beginner',
                    'duration': '300 hours',
                    'skills': ['HTML', 'CSS', 'Flexbox', 'Grid'],
                    'certificate_type': 'Full Certification',
                    'value_score': 95
                },
                {
                    'title': 'JavaScript Algorithms and Data Structures',
                    'category': 'Programming',
                    'difficulty': 'Intermediate',
                    'duration': '300 hours',
                    'skills': ['JavaScript', 'ES6', 'Algorithms', 'Data Structures'],
                    'certificate_type': 'Full Certification',
                    'value_score': 98
                },
                {
                    'title': 'Front End Development Libraries',
                    'category': 'Web Development',
                    'difficulty': 'Intermediate',
                    'duration': '300 hours',
                    'skills': ['React', 'Redux', 'Bootstrap', 'jQuery'],
                    'certificate_type': 'Full Certification',
                    'value_score': 92
                },
                {
                    'title': 'Data Visualization',
                    'category': 'Data Science',
                    'difficulty': 'Intermediate',
                    'duration': '300 hours',
                    'skills': ['D3.js', 'JSON', 'APIs'],
                    'certificate_type': 'Full Certification',
                    'value_score': 88
                }
            ],
            'google_skillshop': [
                {
                    'title': 'Google Analytics Individual Qualification',
                    'category': 'Digital Marketing',
                    'difficulty': 'Beginner',
                    'duration': '4-6 hours',
                    'skills': ['Google Analytics', 'Web Analytics', 'Data Analysis'],
                    'certificate_type': 'Professional Certification',
                    'value_score': 90
                },
                {
                    'title': 'Google Ads Search Certification',
                    'category': 'Digital Marketing',
                    'difficulty': 'Intermediate',
                    'duration': '3-5 hours',
                    'skills': ['Google Ads', 'SEM', 'Keyword Research'],
                    'certificate_type': 'Professional Certification',
                    'value_score': 92
                },
                {
                    'title': 'Google Cloud Digital Leader',
                    'category': 'Cloud Computing',
                    'difficulty': 'Beginner',
                    'duration': '10-15 hours',
                    'skills': ['Cloud Computing', 'Google Cloud Platform', 'Digital Transformation'],
                    'certificate_type': 'Professional Certification',
                    'value_score': 94
                }
            ],
            'microsoft_learn': [
                {
                    'title': 'Azure Fundamentals (AZ-900)',
                    'category': 'Cloud Computing',
                    'difficulty': 'Beginner',
                    'duration': '15-20 hours',
                    'skills': ['Azure', 'Cloud Services', 'Cloud Economics'],
                    'certificate_type': 'Microsoft Certification',
                    'value_score': 96
                },
                {
                    'title': 'Power Platform Fundamentals',
                    'category': 'Business Applications',
                    'difficulty': 'Beginner',
                    'duration': '10-15 hours',
                    'skills': ['Power BI', 'Power Apps', 'Power Automate'],
                    'certificate_type': 'Microsoft Certification',
                    'value_score': 85
                }
            ],
            'ibm_skills': [
                {
                    'title': 'IBM Data Science Professional Certificate',
                    'category': 'Data Science',
                    'difficulty': 'Intermediate',
                    'duration': '100+ hours',
                    'skills': ['Python', 'Machine Learning', 'Data Analysis', 'SQL'],
                    'certificate_type': 'Professional Certificate',
                    'value_score': 94
                },
                {
                    'title': 'IBM AI Engineering Professional Certificate',
                    'category': 'Artificial Intelligence',
                    'difficulty': 'Advanced',
                    'duration': '120+ hours',
                    'skills': ['Machine Learning', 'Deep Learning', 'TensorFlow', 'Keras'],
                    'certificate_type': 'Professional Certificate',
                    'value_score': 96
                }
            ],
            'kaggle': [
                {
                    'title': 'Python',
                    'category': 'Programming',
                    'difficulty': 'Beginner',
                    'duration': '7 hours',
                    'skills': ['Python Programming', 'Data Types', 'Functions'],
                    'certificate_type': 'Micro-Course Certificate',
                    'value_score': 80
                },
                {
                    'title': 'Machine Learning',
                    'category': 'Data Science',
                    'difficulty': 'Intermediate',
                    'duration': '7 hours',
                    'skills': ['Scikit-learn', 'Model Selection', 'Validation'],
                    'certificate_type': 'Micro-Course Certificate',
                    'value_score': 85
                }
            ],
            'hackerrank': [
                {
                    'title': 'Python (Basic)',
                    'category': 'Programming',
                    'difficulty': 'Beginner',
                    'duration': '1 hour',
                    'skills': ['Python Basics', 'Data Structures', 'Algorithms'],
                    'certificate_type': 'Skills Verification',
                    'value_score': 75
                },
                {
                    'title': 'SQL (Advanced)',
                    'category': 'Database',
                    'difficulty': 'Advanced',
                    'duration': '1.5 hours',
                    'skills': ['Advanced SQL', 'Complex Queries', 'Database Optimization'],
                    'certificate_type': 'Skills Verification',
                    'value_score': 82
                }
            ],
            'cisco_netacad': [
                {
                    'title': 'Introduction to Cybersecurity',
                    'category': 'Cybersecurity',
                    'difficulty': 'Beginner',
                    'duration': '15 hours',
                    'skills': ['Cybersecurity Fundamentals', 'Network Security', 'Risk Management'],
                    'certificate_type': 'Course Completion',
                    'value_score': 88
                },
                {
                    'title': 'CCNA: Introduction to Networks',
                    'category': 'Networking',
                    'difficulty': 'Intermediate',
                    'duration': '70 hours',
                    'skills': ['Network Fundamentals', 'OSI Model', 'TCP/IP'],
                    'certificate_type': 'Course Completion',
                    'value_score': 92
                }
            ],
            'hubspot_academy': [
                {
                    'title': 'Inbound Marketing Certification',
                    'category': 'Digital Marketing',
                    'difficulty': 'Intermediate',
                    'duration': '4.5 hours',
                    'skills': ['Inbound Marketing', 'Content Marketing', 'Lead Generation'],
                    'certificate_type': 'Professional Certification',
                    'value_score': 87
                },
                {
                    'title': 'Content Marketing Certification',
                    'category': 'Digital Marketing',
                    'difficulty': 'Intermediate',
                    'duration': '4 hours',
                    'skills': ['Content Strategy', 'Content Creation', 'Content Distribution'],
                    'certificate_type': 'Professional Certification',
                    'value_score': 85
                }
            ]
        }

    def _load_platform_config(self) -> Dict[str, Any]:
        """Load platform configuration"""
        try:
            with open('config/courses.yaml', 'r') as file:
                config = yaml.safe_load(file)
                return {p['name']: p for p in config.get('platforms', [])}
        except Exception as e:
            logger.error(f"Failed to load platform config: {e}")
            return {}

    def get_recommendations_by_category(self, category: str) -> List[CertificationOpportunity]:
        """Get certification recommendations by category"""
        recommendations = []

        for platform, certs in self.certification_catalog.items():
            for cert in certs:
                if cert.get('category', '').lower() == category.lower():
                    opportunity = CertificationOpportunity(
                        platform=platform,
                        title=cert['title'],
                        provider=platform.replace('_', ' ').title(),
                        category=cert['category'],
                        difficulty=cert['difficulty'],
                        duration=cert['duration'],
                        url=self._get_platform_url(platform),
                        is_free=True,
                        prerequisites=[],
                        skills_covered=cert['skills'],
                        certificate_type=cert['certificate_type'],
                        value_score=cert['value_score']
                    )
                    recommendations.append(opportunity)

        # Sort by value score
        return sorted(recommendations, key=lambda x: x.value_score, reverse=True)

    def get_recommendations_by_skill(self, skill: str) -> List[CertificationOpportunity]:
        """Get certification recommendations by skill"""
        recommendations = []

        for platform, certs in self.certification_catalog.items():
            for cert in certs:
                if any(skill.lower() in s.lower() for s in cert['skills']):
                    opportunity = CertificationOpportunity(
                        platform=platform,
                        title=cert['title'],
                        provider=platform.replace('_', ' ').title(),
                        category=cert['category'],
                        difficulty=cert['difficulty'],
                        duration=cert['duration'],
                        url=self._get_platform_url(platform),
                        is_free=True,
                        prerequisites=[],
                        skills_covered=cert['skills'],
                        certificate_type=cert['certificate_type'],
                        value_score=cert['value_score']
                    )
                    recommendations.append(opportunity)

        return sorted(recommendations, key=lambda x: x.value_score, reverse=True)

    def get_recommendations_by_difficulty(self, difficulty: str) -> List[CertificationOpportunity]:
        """Get certification recommendations by difficulty level"""
        recommendations = []

        for platform, certs in self.certification_catalog.items():
            for cert in certs:
                if cert.get('difficulty', '').lower() == difficulty.lower():
                    opportunity = CertificationOpportunity(
                        platform=platform,
                        title=cert['title'],
                        provider=platform.replace('_', ' ').title(),
                        category=cert['category'],
                        difficulty=cert['difficulty'],
                        duration=cert['duration'],
                        url=self._get_platform_url(platform),
                        is_free=True,
                        prerequisites=[],
                        skills_covered=cert['skills'],
                        certificate_type=cert['certificate_type'],
                        value_score=cert['value_score']
                    )
                    recommendations.append(opportunity)

        return sorted(recommendations, key=lambda x: x.value_score, reverse=True)

    def get_top_certifications(self, limit: int = 10) -> List[CertificationOpportunity]:
        """Get top certification recommendations by value score"""
        all_recommendations = []

        for platform, certs in self.certification_catalog.items():
            for cert in certs:
                opportunity = CertificationOpportunity(
                    platform=platform,
                    title=cert['title'],
                    provider=platform.replace('_', ' ').title(),
                    category=cert['category'],
                    difficulty=cert['difficulty'],
                    duration=cert['duration'],
                    url=self._get_platform_url(platform),
                    is_free=True,
                    prerequisites=[],
                    skills_covered=cert['skills'],
                    certificate_type=cert['certificate_type'],
                    value_score=cert['value_score']
                )
                all_recommendations.append(opportunity)

        return sorted(all_recommendations, key=lambda x: x.value_score, reverse=True)[:limit]

    def get_career_path_recommendations(self, career_path: str) -> List[CertificationOpportunity]:
        """Get certification recommendations for specific career paths"""
        career_mappings = {
            'data_scientist': ['Programming', 'Data Science', 'Artificial Intelligence'],
            'web_developer': ['Web Development', 'Programming'],
            'digital_marketer': ['Digital Marketing'],
            'cloud_engineer': ['Cloud Computing'],
            'cybersecurity': ['Cybersecurity', 'Networking'],
            'business_analyst': ['Business Applications', 'Data Science']
        }

        categories = career_mappings.get(career_path.lower(), [])
        recommendations = []

        for category in categories:
            recommendations.extend(
                self.get_recommendations_by_category(category))

        # Remove duplicates and sort by value
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec.title not in seen:
                seen.add(rec.title)
                unique_recommendations.append(rec)

        return sorted(unique_recommendations, key=lambda x: x.value_score, reverse=True)

    def _get_platform_url(self, platform: str) -> str:
        """Get base URL for platform"""
        platform_config = self.platforms.get(platform, {})
        return platform_config.get('base_url', f'https://{platform}.com')

    def export_recommendations(self, recommendations: List[CertificationOpportunity],
                               filename: str = None) -> str:
        """Export recommendations to markdown file"""
        if not filename:
            filename = f"certification_recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        content = "# 🎓 Free Certification Recommendations\n\n"
        content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Group by category
        categories = {}
        for rec in recommendations:
            if rec.category not in categories:
                categories[rec.category] = []
            categories[rec.category].append(rec)

        for category, certs in categories.items():
            content += f"## {category}\n\n"

            for cert in certs:
                content += f"### {cert.title}\n"
                content += f"- **Provider**: {cert.provider}\n"
                content += f"- **Difficulty**: {cert.difficulty}\n"
                content += f"- **Duration**: {cert.duration}\n"
                content += f"- **Value Score**: {cert.value_score}/100\n"
                content += f"- **Skills**: {', '.join(cert.skills_covered)}\n"
                content += f"- **Certificate Type**: {cert.certificate_type}\n"
                content += f"- **URL**: {cert.url}\n\n"

        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        return filename

    def get_platform_stats(self) -> Dict[str, Any]:
        """Get statistics about supported platforms and certifications"""
        total_platforms = len(self.certification_catalog)
        total_certifications = sum(len(certs)
                                   for certs in self.certification_catalog.values())

        categories = set()
        difficulties = set()
        for certs in self.certification_catalog.values():
            for cert in certs:
                categories.add(cert['category'])
                difficulties.add(cert['difficulty'])

        return {
            'total_platforms': total_platforms,
            'total_certifications': total_certifications,
            'categories': sorted(list(categories)),
            'difficulty_levels': sorted(list(difficulties)),
            'avg_value_score': sum(cert['value_score'] for certs in self.certification_catalog.values()
                                   for cert in certs) / total_certifications
        }


def main():
    """Main function for testing platform discovery"""
    discovery = PlatformDiscovery()

    print("🎓 Cert Me Boi - Platform Discovery System")
    print("=" * 50)

    # Show platform stats
    stats = discovery.get_platform_stats()
    print(f"📊 Platform Statistics:")
    print(f"   - Total Platforms: {stats['total_platforms']}")
    print(f"   - Total Certifications: {stats['total_certifications']}")
    print(f"   - Categories: {', '.join(stats['categories'])}")
    print(f"   - Average Value Score: {stats['avg_value_score']:.1f}/100")
    print()

    # Show top recommendations
    print("🏆 Top 10 Certification Recommendations:")
    top_certs = discovery.get_top_certifications(10)
    for i, cert in enumerate(top_certs, 1):
        print(f"{i:2}. {cert.title} ({cert.provider}) - Score: {cert.value_score}")
    print()

    # Show recommendations by category
    print("💼 Data Science Career Path:")
    ds_certs = discovery.get_career_path_recommendations('data_scientist')
    for cert in ds_certs[:5]:
        print(f"   - {cert.title} ({cert.provider}) - {cert.difficulty}")

    # Export recommendations
    filename = discovery.export_recommendations(top_certs)
    print(f"\n📄 Recommendations exported to: {filename}")


if __name__ == "__main__":
    main()
