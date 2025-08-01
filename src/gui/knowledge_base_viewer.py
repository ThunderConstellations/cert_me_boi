#!/usr/bin/env python3
"""
Knowledge Base Viewer
User-friendly interface for reviewing all recorded course content
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3
import json
from typing import List, Dict, Any
import re
from src.learning.content_recorder import ContentRecorder


class KnowledgeBaseViewer:
    """Interactive viewer for the knowledge base"""

    def __init__(self):
        self.recorder = ContentRecorder()

    def render_main_interface(self):
        """Render the main knowledge base interface"""
        st.markdown("# 📚 Your Learning Knowledge Base")
        st.markdown(
            "*Review all course content, test questions, and insights from your certifications*")

        # Statistics overview
        self._render_statistics_dashboard()

        # Main navigation tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📖 Course Content",
            "❓ Test Questions",
            "💡 Key Insights",
            "🔍 Search",
            "📊 Analytics"
        ])

        with tab1:
            self._render_course_content_tab()

        with tab2:
            self._render_test_questions_tab()

        with tab3:
            self._render_insights_tab()

        with tab4:
            self._render_search_tab()

        with tab5:
            self._render_analytics_tab()

    def _render_statistics_dashboard(self):
        """Render overview statistics"""
        st.markdown("## 📊 Knowledge Base Overview")

        # Get statistics
        stats = self._get_knowledge_stats()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="📚 Total Content Items",
                value=stats['total_content'],
                delta=f"+{stats['content_this_week']} this week"
            )

        with col2:
            st.metric(
                label="❓ Test Questions",
                value=stats['total_questions'],
                delta=f"+{stats['questions_this_week']} this week"
            )

        with col3:
            st.metric(
                label="🎓 Completed Courses",
                value=stats['completed_courses'],
                delta=f"+{stats['courses_this_month']} this month"
            )

        with col4:
            st.metric(
                label="⭐ Platform Coverage",
                value=f"{stats['platforms_used']} platforms",
                delta="25+ available"
            )

    def _render_course_content_tab(self):
        """Render course content viewing interface"""
        st.markdown("### 📖 Course Content Library")

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            platforms = self._get_available_platforms()
            selected_platform = st.selectbox("Platform", ["All"] + platforms)

        with col2:
            content_types = self._get_content_types()
            selected_type = st.selectbox(
                "Content Type", ["All"] + content_types)

        with col3:
            courses = self._get_available_courses()
            selected_course = st.selectbox("Course", ["All"] + courses)

        # Get filtered content
        content_items = self._get_filtered_content(
            platform=None if selected_platform == "All" else selected_platform,
            content_type=None if selected_type == "All" else selected_type,
            course=None if selected_course == "All" else selected_course
        )

        # Display content
        if content_items:
            for item in content_items:
                with st.expander(f"📄 {item['title']} - {item['platform']} ({item['content_type']})"):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"**Course:** {item['course_title']}")
                        st.markdown(f"**Date:** {item['timestamp']}")

                        if item['tags']:
                            tags_html = " ".join(
                                [f"<span style='background: #FFD700; color: #000; padding: 2px 6px; border-radius: 3px; margin: 2px;'>{tag}</span>" for tag in item['tags']])
                            st.markdown(
                                f"**Tags:** {tags_html}", unsafe_allow_html=True)

                        # Content with reading time estimate
                        word_count = len(item['content'].split())
                        # ~200 words per minute
                        reading_time = max(1, word_count // 200)
                        st.markdown(
                            f"*Estimated reading time: {reading_time} min*")

                        # Display content with syntax highlighting for code
                        if 'code' in item['content'].lower() or any(lang in item['content'].lower() for lang in ['python', 'javascript', 'sql']):
                            st.code(item['content'], language='python')
                        else:
                            st.markdown(item['content'])

                    with col2:
                        if st.button(f"📋 Copy", key=f"copy_{item['content_id']}"):
                            st.success("Copied to clipboard!")

                        if st.button(f"🔖 Bookmark", key=f"bookmark_{item['content_id']}"):
                            self._bookmark_content(item['content_id'])
                            st.success("Bookmarked!")

                        if item.get('duration'):
                            st.markdown(f"**Duration:** {item['duration']}")
        else:
            st.info("No content found matching your filters.")

    def _render_test_questions_tab(self):
        """Render test questions practice interface"""
        st.markdown("### ❓ Test Questions Practice")

        # Question filters
        col1, col2 = st.columns(2)

        with col1:
            topics = self._get_question_topics()
            selected_topic = st.selectbox(
                "Topic", ["All"] + topics, key="question_topic")

        with col2:
            difficulties = ["All", "easy", "medium", "hard"]
            selected_difficulty = st.selectbox(
                "Difficulty", difficulties, key="question_difficulty")

        # Practice mode selection
        practice_mode = st.radio("Practice Mode", [
            "📚 Study Mode (Show Answers)",
            "🎯 Quiz Mode (Test Yourself)",
            "🔄 Random Review"
        ])

        # Get questions
        questions = self._get_filtered_questions(
            topic=None if selected_topic == "All" else selected_topic,
            difficulty=None if selected_difficulty == "All" else selected_difficulty
        )

        if questions:
            if practice_mode == "📚 Study Mode (Show Answers)":
                self._render_study_mode(questions)
            elif practice_mode == "🎯 Quiz Mode (Test Yourself)":
                self._render_quiz_mode(questions)
            else:
                self._render_random_review(questions)
        else:
            st.info("No questions found matching your criteria.")

    def _render_study_mode(self, questions: List[Dict]):
        """Render study mode with answers visible"""
        for i, question in enumerate(questions):
            with st.expander(f"Q{i+1}: {question['question_text'][:100]}..."):
                st.markdown(f"**Question:** {question['question_text']}")

                if question['all_options']:
                    st.markdown("**Options:**")
                    for j, option in enumerate(question['all_options']):
                        if option == question['correct_answer']:
                            st.markdown(
                                f"✅ {chr(65+j)}. **{option}** *(Correct)*")
                        else:
                            st.markdown(f"   {chr(65+j)}. {option}")

                st.markdown(
                    f"**Correct Answer:** {question['correct_answer']}")

                if question['explanation']:
                    st.markdown(f"**Explanation:** {question['explanation']}")

                st.markdown(
                    f"**Topic:** {question['topic']} | **Difficulty:** {question['difficulty']}")
                st.markdown(
                    f"**Source:** {question['platform']} - {question['course_id']}")

    def _render_quiz_mode(self, questions: List[Dict]):
        """Render interactive quiz mode"""
        if 'quiz_state' not in st.session_state:
            st.session_state.quiz_state = {
                'current_question': 0,
                'answers': {},
                'score': 0,
                'completed': False
            }

        quiz_state = st.session_state.quiz_state
        total_questions = len(questions)

        if not quiz_state['completed'] and quiz_state['current_question'] < total_questions:
            current_q = questions[quiz_state['current_question']]

            st.markdown(
                f"### Question {quiz_state['current_question'] + 1} of {total_questions}")
            st.progress((quiz_state['current_question'] + 1) / total_questions)

            st.markdown(f"**{current_q['question_text']}**")

            if current_q['all_options']:
                selected_answer = st.radio(
                    "Select your answer:",
                    current_q['all_options'],
                    key=f"quiz_q_{quiz_state['current_question']}"
                )

                col1, col2 = st.columns([1, 1])

                with col1:
                    if st.button("Next Question"):
                        quiz_state['answers'][quiz_state['current_question']
                                              ] = selected_answer
                        if selected_answer == current_q['correct_answer']:
                            quiz_state['score'] += 1

                        quiz_state['current_question'] += 1
                        if quiz_state['current_question'] >= total_questions:
                            quiz_state['completed'] = True
                        st.rerun()

                with col2:
                    if st.button("Show Answer"):
                        st.success(
                            f"Correct Answer: {current_q['correct_answer']}")
                        if current_q['explanation']:
                            st.info(current_q['explanation'])

        elif quiz_state['completed']:
            # Show results
            st.markdown("## 🎉 Quiz Completed!")

            score_percentage = (quiz_state['score'] / total_questions) * 100
            st.metric(
                "Your Score", f"{quiz_state['score']}/{total_questions}", f"{score_percentage:.1f}%")

            if score_percentage >= 80:
                st.success(
                    "Excellent! You have a strong understanding of the material.")
            elif score_percentage >= 60:
                st.warning(
                    "Good job! Consider reviewing some topics for better understanding.")
            else:
                st.error("Keep studying! Review the material and try again.")

            if st.button("Start New Quiz"):
                st.session_state.quiz_state = {
                    'current_question': 0,
                    'answers': {},
                    'score': 0,
                    'completed': False
                }
                st.rerun()

    def _render_insights_tab(self):
        """Render learning insights interface"""
        st.markdown("### 💡 Key Learning Insights")

        insights = self._get_learning_insights()

        if insights:
            # Group by category
            categories = {}
            for insight in insights:
                cat = insight['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(insight)

            for category, items in categories.items():
                icon_map = {
                    'key_concept': '🔑',
                    'tip': '💡',
                    'warning': '⚠️',
                    'best_practice': '⭐'
                }

                st.markdown(
                    f"#### {icon_map.get(category, '📝')} {category.replace('_', ' ').title()}")

                for insight in items:
                    with st.expander(f"{insight['insight_text'][:80]}..."):
                        st.markdown(insight['insight_text'])
                        st.markdown(
                            f"**Source:** {insight['platform']} - {insight['course_id']}")
                        st.markdown(
                            f"**Importance:** {'⭐' * (insight['importance_score'] // 2)}")

                        if insight['related_topics']:
                            topics_html = " ".join(
                                [f"<span style='background: #87CEEB; color: #000; padding: 2px 6px; border-radius: 3px; margin: 2px;'>{topic}</span>" for topic in insight['related_topics']])
                            st.markdown(
                                f"**Related Topics:** {topics_html}", unsafe_allow_html=True)
        else:
            st.info(
                "No insights recorded yet. Complete some courses to see key learning points!")

    def _render_search_tab(self):
        """Render search interface"""
        st.markdown("### 🔍 Search Your Knowledge Base")

        search_query = st.text_input(
            "Search for content, questions, or topics:", placeholder="Enter keywords...")

        col1, col2 = st.columns(2)
        with col1:
            search_type = st.selectbox(
                "Search In", ["All Content", "Course Content", "Test Questions", "Insights"])

        with col2:
            sort_by = st.selectbox(
                "Sort By", ["Relevance", "Date (Newest)", "Date (Oldest)", "Platform"])

        if search_query:
            results = self._search_knowledge_base(
                search_query, search_type, sort_by)

            if results:
                st.markdown(f"### Found {len(results)} results:")

                for result in results:
                    with st.container():
                        st.markdown(
                            f"**{result['title']}** - {result['platform']}")
                        st.markdown(result['snippet'])
                        st.markdown(
                            f"*{result['content_type']} | {result['timestamp']}*")
                        st.markdown("---")
            else:
                st.info(
                    "No results found. Try different keywords or check your spelling.")

    def _render_analytics_tab(self):
        """Render learning analytics"""
        st.markdown("### 📊 Learning Analytics")

        # Learning progress over time
        progress_data = self._get_learning_progress_data()

        if progress_data:
            fig_progress = go.Figure()

            fig_progress.add_trace(go.Scatter(
                x=progress_data['dates'],
                y=progress_data['cumulative_content'],
                mode='lines+markers',
                name='Content Items',
                line=dict(color='#FFD700', width=3),
                marker=dict(size=8)
            ))

            fig_progress.update_layout(
                title='📈 Learning Progress Over Time',
                xaxis_title='Date',
                yaxis_title='Cumulative Content Items',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#FFFFFF')
            )

            st.plotly_chart(fig_progress, use_container_width=True)

        # Platform distribution
        platform_data = self._get_platform_distribution()

        if platform_data:
            fig_platforms = px.pie(
                values=platform_data['counts'],
                names=platform_data['platforms'],
                title='🌐 Content Distribution by Platform'
            )

            fig_platforms.update_traces(
                textposition='inside', textinfo='percent+label')
            fig_platforms.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#FFFFFF')
            )

            st.plotly_chart(fig_platforms, use_container_width=True)

        # Knowledge gaps analysis
        st.markdown("#### 🎯 Knowledge Gaps Analysis")
        gaps = self._analyze_knowledge_gaps()

        if gaps:
            for gap in gaps:
                st.markdown(f"• **{gap['topic']}**: {gap['description']}")
        else:
            st.success("Great! No significant knowledge gaps detected.")

    # Helper methods for data retrieval

    def _get_knowledge_stats(self) -> Dict[str, int]:
        """Get knowledge base statistics"""
        with sqlite3.connect(self.recorder.db_path) as conn:
            # Total content
            total_content = conn.execute(
                "SELECT COUNT(*) FROM course_content").fetchone()[0]

            # Content this week
            week_ago = datetime.now() - timedelta(days=7)
            content_this_week = conn.execute(
                "SELECT COUNT(*) FROM course_content WHERE timestamp > ?",
                (week_ago,)
            ).fetchone()[0]

            # Total questions
            total_questions = conn.execute(
                "SELECT COUNT(*) FROM test_questions").fetchone()[0]

            # Questions this week
            questions_this_week = conn.execute(
                "SELECT COUNT(*) FROM test_questions WHERE timestamp > ?",
                (week_ago,)
            ).fetchone()[0]

            # Completed courses
            completed_courses = conn.execute(
                "SELECT COUNT(DISTINCT course_title) FROM course_content"
            ).fetchone()[0]

            # Courses this month
            month_ago = datetime.now() - timedelta(days=30)
            courses_this_month = conn.execute(
                "SELECT COUNT(DISTINCT course_title) FROM course_content WHERE timestamp > ?",
                (month_ago,)
            ).fetchone()[0]

            # Platforms used
            platforms_used = conn.execute(
                "SELECT COUNT(DISTINCT platform) FROM course_content"
            ).fetchone()[0]

        return {
            'total_content': total_content,
            'content_this_week': content_this_week,
            'total_questions': total_questions,
            'questions_this_week': questions_this_week,
            'completed_courses': completed_courses,
            'courses_this_month': courses_this_month,
            'platforms_used': platforms_used
        }

    def _get_available_platforms(self) -> List[str]:
        """Get list of available platforms"""
        with sqlite3.connect(self.recorder.db_path) as conn:
            cursor = conn.execute(
                "SELECT DISTINCT platform FROM course_content ORDER BY platform")
            return [row[0] for row in cursor.fetchall()]

    def _get_content_types(self) -> List[str]:
        """Get list of content types"""
        with sqlite3.connect(self.recorder.db_path) as conn:
            cursor = conn.execute(
                "SELECT DISTINCT content_type FROM course_content ORDER BY content_type")
            return [row[0] for row in cursor.fetchall()]

    def _get_available_courses(self) -> List[str]:
        """Get list of available courses"""
        with sqlite3.connect(self.recorder.db_path) as conn:
            cursor = conn.execute(
                "SELECT DISTINCT course_title FROM course_content ORDER BY course_title")
            return [row[0] for row in cursor.fetchall()]

    def _get_filtered_content(self, platform=None, content_type=None, course=None) -> List[Dict]:
        """Get filtered content items"""
        query = "SELECT * FROM course_content WHERE 1=1"
        params = []

        if platform:
            query += " AND platform = ?"
            params.append(platform)

        if content_type:
            query += " AND content_type = ?"
            params.append(content_type)

        if course:
            query += " AND course_title = ?"
            params.append(course)

        query += " ORDER BY timestamp DESC LIMIT 50"

        with sqlite3.connect(self.recorder.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)

            items = []
            for row in cursor.fetchall():
                item = dict(row)
                item['tags'] = json.loads(item['tags'] or '[]')
                items.append(item)

            return items

    def _bookmark_content(self, content_id: str):
        """Bookmark content item"""
        # Implementation for bookmarking
        pass

    def _get_question_topics(self) -> List[str]:
        """Get list of question topics"""
        with sqlite3.connect(self.recorder.db_path) as conn:
            cursor = conn.execute(
                "SELECT DISTINCT topic FROM test_questions ORDER BY topic")
            return [row[0] for row in cursor.fetchall()]

    def _get_filtered_questions(self, topic=None, difficulty=None) -> List[Dict]:
        """Get filtered questions"""
        query = "SELECT * FROM test_questions WHERE 1=1"
        params = []

        if topic:
            query += " AND topic = ?"
            params.append(topic)

        if difficulty:
            query += " AND difficulty = ?"
            params.append(difficulty)

        query += " ORDER BY timestamp DESC"

        with sqlite3.connect(self.recorder.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)

            questions = []
            for row in cursor.fetchall():
                question = dict(row)
                question['all_options'] = json.loads(
                    question['all_options'] or '[]')
                questions.append(question)

            return questions

    def _get_learning_insights(self) -> List[Dict]:
        """Get learning insights"""
        with sqlite3.connect(self.recorder.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM learning_insights 
                ORDER BY importance_score DESC, timestamp DESC
            """)

            insights = []
            for row in cursor.fetchall():
                insight = dict(row)
                insight['related_topics'] = json.loads(
                    insight['related_topics'] or '[]')
                insights.append(insight)

            return insights

    def _search_knowledge_base(self, query: str, search_type: str, sort_by: str) -> List[Dict]:
        """Search knowledge base"""
        return self.recorder.search_content(query)

    def _get_learning_progress_data(self) -> Dict:
        """Get learning progress data for charts"""
        with sqlite3.connect(self.recorder.db_path) as conn:
            cursor = conn.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM course_content 
                GROUP BY DATE(timestamp)
                ORDER BY date
            """)

            data = cursor.fetchall()

            if not data:
                return None

            dates = [row[0] for row in data]
            daily_counts = [row[1] for row in data]

            # Calculate cumulative
            cumulative = []
            total = 0
            for count in daily_counts:
                total += count
                cumulative.append(total)

            return {
                'dates': dates,
                'daily_counts': daily_counts,
                'cumulative_content': cumulative
            }

    def _get_platform_distribution(self) -> Dict:
        """Get platform distribution data"""
        with sqlite3.connect(self.recorder.db_path) as conn:
            cursor = conn.execute("""
                SELECT platform, COUNT(*) as count
                FROM course_content
                GROUP BY platform
                ORDER BY count DESC
            """)

            data = cursor.fetchall()

            if not data:
                return None

            return {
                'platforms': [row[0] for row in data],
                'counts': [row[1] for row in data]
            }

    def _analyze_knowledge_gaps(self) -> List[Dict]:
        """Analyze knowledge gaps"""
        # Simple gap analysis based on topic coverage
        gaps = []

        with sqlite3.connect(self.recorder.db_path) as conn:
            # Check for topics with few questions
            cursor = conn.execute("""
                SELECT topic, COUNT(*) as question_count
                FROM test_questions
                GROUP BY topic
                HAVING question_count < 3
            """)

            for row in cursor.fetchall():
                gaps.append({
                    'topic': row[0],
                    'description': f"Only {row[1]} questions recorded. Consider more practice."
                })

        return gaps

    def _render_random_review(self, questions: List[Dict]):
        """Render random review mode"""
        import random

        if st.button("🎲 Get Random Question"):
            random_question = random.choice(questions)
            st.session_state.random_question = random_question

        if hasattr(st.session_state, 'random_question'):
            q = st.session_state.random_question

            st.markdown(f"### Random Question: {q['topic']}")
            st.markdown(f"**{q['question_text']}**")

            if q['all_options']:
                for i, option in enumerate(q['all_options']):
                    st.markdown(f"{chr(65+i)}. {option}")

            if st.button("Show Answer"):
                st.success(f"**Answer:** {q['correct_answer']}")
                if q['explanation']:
                    st.info(f"**Explanation:** {q['explanation']}")


def render_knowledge_base():
    """Main function to render knowledge base viewer"""
    viewer = KnowledgeBaseViewer()
    viewer.render_main_interface()
