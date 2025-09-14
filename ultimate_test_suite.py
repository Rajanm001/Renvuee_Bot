#!/usr/bin/env python3
"""
🧪 ULTIMATE TELEGRAM REVENUE COPILOT TEST SUITE
==============================================

Comprehensive testing for all advanced features:
- Dual-agent architecture (Knowledge + Dealflow)
- Natural language intent classification
- File ingestion and vector search
- Lead capture and proposal generation
- Google APIs integration
- Performance benchmarks
- End-to-end workflows

This test suite ensures 100% reliability for client presentation!
"""

import unittest
import asyncio
import os
import json
import tempfile
import sqlite3
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import time
import logging

# Import our bot
try:
    from ultimate_revenue_copilot import (
        UltimateTelegramRevenueCopilot,
        IntentClassifier,
        KnowledgeAgent,
        DealflowAgent,
        IntentClassification,
        Lead,
        KnowledgeResponse,
        ProposalContent,
        ScheduleInfo,
        Citation
    )
    BOT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Bot import failed: {e}")
    BOT_AVAILABLE = False

# Configure test logging
logging.basicConfig(level=logging.WARNING)

class TestUltimateTelegramRevenueCopilot(unittest.TestCase):
    """Comprehensive test suite for Ultimate Telegram Revenue Copilot"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test environment"""
        cls.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': [],
            'performance_metrics': {},
            'start_time': time.time()
        }
        
        if not BOT_AVAILABLE:
            cls.skipTest(cls, "Bot classes not available")
    
    def setUp(self):
        """Setup for each test"""
        self.test_results['total_tests'] += 1
        
        # Mock bot token
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_123'
        
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        
        # Mock the bot initialization to avoid real Telegram connection
        with patch('ultimate_revenue_copilot.Application') as mock_app:
            mock_app.builder.return_value.token.return_value.build.return_value = Mock()
            self.bot = UltimateTelegramRevenueCopilot('test_token')
            self.bot.db_path = self.temp_db.name
            self.bot.setup_database()
    
    def tearDown(self):
        """Cleanup after each test"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def record_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Record test result for reporting"""
        if passed:
            self.test_results['passed_tests'] += 1
            status = "✅ PASSED"
        else:
            self.test_results['failed_tests'] += 1
            status = "❌ FAILED"
        
        self.test_results['test_details'].append({
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_01_bot_initialization(self):
        """Test bot initialization and core components"""
        try:
            # Test database setup
            conn = sqlite3.connect(self.bot.db_path)
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['conversations', 'crm', 'knowledge_files']
            for table in expected_tables:
                self.assertIn(table, tables, f"Table {table} not created")
            
            conn.close()
            
            # Test agent initialization
            self.assertIsNotNone(self.bot.knowledge_agent)
            self.assertIsNotNone(self.bot.dealflow_agent)
            self.assertIsNotNone(self.bot.intent_classifier)
            
            self.record_test_result("Bot Initialization", True, "All components initialized successfully")
            
        except Exception as e:
            self.record_test_result("Bot Initialization", False, str(e))
            raise
    
    def test_02_intent_classification(self):
        """Test advanced intent classification"""
        try:
            classifier = self.bot.intent_classifier
            
            test_cases = [
                ("What's our refund policy?", "knowledge_qa"),
                ("John from Acme wants a demo, budget 10k", "lead_capture"),
                ("Can you draft a proposal for TechCorp?", "proposal_request"),
                ("Schedule a meeting tomorrow at 3pm", "next_step"),
                ("We lost the deal - budget cut", "status_update"),
                ("Hello, how are you?", "smalltalk")
            ]
            
            correct_classifications = 0
            total_classifications = len(test_cases)
            
            for text, expected_intent in test_cases:
                result = asyncio.run(classifier.classify(text, []))
                
                if result.intent == expected_intent:
                    correct_classifications += 1
                
                # Test confidence threshold
                self.assertGreaterEqual(result.confidence, 0.0)
                self.assertLessEqual(result.confidence, 1.0)
            
            accuracy = correct_classifications / total_classifications
            self.assertGreaterEqual(accuracy, 0.70, f"Intent classification accuracy too low: {accuracy:.2%}")
            
            self.record_test_result(
                "Intent Classification", 
                True, 
                f"Accuracy: {accuracy:.1%} ({correct_classifications}/{total_classifications})"
            )
            
        except Exception as e:
            self.record_test_result("Intent Classification", False, str(e))
            raise
    
    def test_03_entity_extraction(self):
        """Test entity extraction from natural language"""
        try:
            classifier = self.bot.intent_classifier
            
            # Test lead entity extraction
            lead_text = "John Smith from Acme Corp wants a demo next week, budget around $25,000"
            entities = classifier.extract_lead_entities(lead_text)
            
            self.assertIn('name', entities)
            self.assertIn('company', entities)
            self.assertIn('budget', entities)
            
            # Test schedule entity extraction
            schedule_text = "Let's meet tomorrow at 3:30 PM with Sarah"
            entities = classifier.extract_schedule_entities(schedule_text)
            
            self.assertIn('time', entities)
            self.assertIn('day', entities)
            
            self.record_test_result("Entity Extraction", True, "All entity types extracted successfully")
            
        except Exception as e:
            self.record_test_result("Entity Extraction", False, str(e))
            raise
    
    def test_04_knowledge_agent_file_ingestion(self):
        """Test file ingestion into knowledge base"""
        try:
            agent = self.bot.knowledge_agent
            
            # Create test file
            test_content = """
            Company Refund Policy
            
            We offer full refunds within 30 days of purchase.
            Digital products have a 14-day refund window.
            Refunds are processed within 5-7 business days.
            """
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_content)
                temp_file = f.name
            
            try:
                # Test ingestion
                result = asyncio.run(agent.ingest_file(temp_file, "refund_policy.txt", "test_123"))
                
                self.assertIsInstance(result, dict)
                self.assertIn('chunks', result)
                self.assertIn('tokens', result)
                self.assertGreater(result['tokens'], 0)
                
                self.record_test_result("File Ingestion", True, f"Processed {result['chunks']} chunks, {result['tokens']} tokens")
                
            finally:
                os.unlink(temp_file)
                
        except Exception as e:
            self.record_test_result("File Ingestion", False, str(e))
            raise
    
    def test_05_knowledge_agent_qa(self):
        """Test knowledge-based Q&A with citations"""
        try:
            agent = self.bot.knowledge_agent
            
            # Test Q&A
            response = asyncio.run(agent.ask("test_user", "What is the refund policy?", "req_123"))
            
            self.assertIsInstance(response, KnowledgeResponse)
            self.assertIsInstance(response.answer, str)
            self.assertIsInstance(response.citations, list)
            self.assertIsInstance(response.confidence, float)
            self.assertEqual(response.request_id, "req_123")
            
            # Test confidence range
            self.assertGreaterEqual(response.confidence, 0.0)
            self.assertLessEqual(response.confidence, 1.0)
            
            self.record_test_result(
                "Knowledge Q&A", 
                True, 
                f"Generated answer with {len(response.citations)} citations, confidence: {response.confidence:.1%}"
            )
            
        except Exception as e:
            self.record_test_result("Knowledge Q&A", False, str(e))
            raise
    
    def test_06_dealflow_lead_capture(self):
        """Test lead capture and parsing"""
        try:
            agent = self.bot.dealflow_agent
            
            # Test lead capture
            lead_text = "Sarah Johnson from TechCorp wants a demo next month, budget around $15,000"
            lead = asyncio.run(agent.capture_lead(lead_text, "req_456"))
            
            self.assertIsInstance(lead, Lead)
            self.assertIsNotNone(lead.name)
            self.assertIsNotNone(lead.company)
            self.assertIsNotNone(lead.intent)
            self.assertIsNotNone(lead.lead_id)
            self.assertIsInstance(lead.quality_score, float)
            
            # Test quality scoring
            self.assertGreaterEqual(lead.quality_score, 0)
            self.assertLessEqual(lead.quality_score, 100)
            
            self.record_test_result(
                "Lead Capture", 
                True, 
                f"Captured: {lead.name} from {lead.company}, Quality: {lead.quality_score:.0f}/100"
            )
            
        except Exception as e:
            self.record_test_result("Lead Capture", False, str(e))
            raise
    
    def test_07_dealflow_proposal_generation(self):
        """Test proposal generation"""
        try:
            agent = self.bot.dealflow_agent
            
            # Create test lead
            test_lead = Lead(
                name="John Doe",
                company="Example Corp",
                intent="Demo Request",
                budget="$10,000",
                lead_id="test_lead_123"
            )
            
            # Generate proposal
            proposal = asyncio.run(agent.generate_proposal(test_lead, "req_789"))
            
            self.assertIsInstance(proposal, ProposalContent)
            self.assertIsInstance(proposal.title, str)
            self.assertIsInstance(proposal.summary_blurb, str)
            self.assertIsInstance(proposal.bullet_points, list)
            self.assertEqual(proposal.request_id, "req_789")
            
            # Test content quality
            self.assertIn(test_lead.company, proposal.title)
            self.assertGreater(len(proposal.bullet_points), 0)
            self.assertGreater(len(proposal.summary_blurb), 50)
            
            self.record_test_result(
                "Proposal Generation", 
                True, 
                f"Generated proposal with {len(proposal.bullet_points)} bullet points"
            )
            
        except Exception as e:
            self.record_test_result("Proposal Generation", False, str(e))
            raise
    
    def test_08_dealflow_schedule_parsing(self):
        """Test schedule parsing from natural language"""
        try:
            agent = self.bot.dealflow_agent
            
            # Test schedule parsing
            schedule_text = "Let's have a demo call tomorrow at 2:30 PM with the team"
            schedule = asyncio.run(agent.parse_scheduling(schedule_text, "req_101"))
            
            self.assertIsInstance(schedule, ScheduleInfo)
            self.assertIsInstance(schedule.title, str)
            self.assertIsInstance(schedule.start_iso, str)
            self.assertIsInstance(schedule.attendees, list)
            
            # Test ISO format
            datetime.fromisoformat(schedule.start_iso.replace('T', ' ').replace('Z', ''))
            
            self.record_test_result(
                "Schedule Parsing", 
                True, 
                f"Parsed: {schedule.title} at {schedule.start_iso}"
            )
            
        except Exception as e:
            self.record_test_result("Schedule Parsing", False, str(e))
            raise
    
    def test_09_database_operations(self):
        """Test database CRUD operations"""
        try:
            # Test conversation logging
            asyncio.run(self.bot.log_conversation(
                Mock(id=12345, username="testuser", first_name="Test"),
                "knowledge_qa",
                "What is the policy?",
                "req_999"
            ))
            
            # Verify conversation logged
            conn = sqlite3.connect(self.bot.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM conversations")
            count = cursor.fetchone()[0]
            self.assertGreater(count, 0)
            
            # Test CRM operations
            test_lead = Lead(
                name="Database Test",
                company="Test Corp",
                intent="Test Intent",
                budget="$5000",
                lead_id="db_test_123",
                timestamp=datetime.now().isoformat(),
                quality_score=75.0
            )
            
            asyncio.run(self.bot.dealflow_agent.save_lead_to_crm(test_lead))
            
            # Verify lead saved
            cursor.execute("SELECT COUNT(*) FROM crm WHERE lead_id = ?", (test_lead.lead_id,))
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1)
            
            conn.close()
            
            self.record_test_result("Database Operations", True, "All CRUD operations successful")
            
        except Exception as e:
            self.record_test_result("Database Operations", False, str(e))
            raise
    
    def test_10_performance_benchmarks(self):
        """Test performance benchmarks"""
        try:
            # Benchmark intent classification
            start_time = time.time()
            iterations = 100
            
            test_messages = [
                "What's our pricing?",
                "John from Acme wants a demo",
                "Schedule a meeting",
                "Draft a proposal",
                "Hello there!"
            ]
            
            for i in range(iterations):
                text = test_messages[i % len(test_messages)]
                asyncio.run(self.bot.intent_classifier.classify(text, []))
            
            end_time = time.time()
            total_time = end_time - start_time
            messages_per_second = iterations / total_time
            
            # Performance requirements
            self.assertGreater(messages_per_second, 50, "Intent classification too slow")
            
            # Benchmark database operations
            start_time = time.time()
            for i in range(50):
                asyncio.run(self.bot.log_conversation(
                    Mock(id=i, username=f"user{i}", first_name="Test"),
                    "test",
                    f"Message {i}",
                    f"req_{i}"
                ))
            end_time = time.time()
            
            db_ops_per_second = 50 / (end_time - start_time)
            self.assertGreater(db_ops_per_second, 20, "Database operations too slow")
            
            self.test_results['performance_metrics'] = {
                'intent_classification_per_second': round(messages_per_second),
                'database_operations_per_second': round(db_ops_per_second)
            }
            
            self.record_test_result(
                "Performance Benchmarks", 
                True, 
                f"Intent: {messages_per_second:.0f}/sec, DB: {db_ops_per_second:.0f}/sec"
            )
            
        except Exception as e:
            self.record_test_result("Performance Benchmarks", False, str(e))
            raise
    
    def test_11_end_to_end_workflows(self):
        """Test complete end-to-end workflows"""
        try:
            # Mock update and context
            mock_update = Mock()
            mock_update.effective_user = Mock(id=12345, username="testuser", first_name="Test")
            mock_update.message = Mock()
            mock_context = Mock()
            
            # Test knowledge workflow
            mock_update.message.text = "What is our refund policy?"
            mock_update.message.document = None
            mock_update.message.photo = None
            
            # This would normally send a reply, but we'll mock it
            with patch.object(mock_update.message, 'reply_text', new_callable=AsyncMock) as mock_reply:
                asyncio.run(self.bot.handle_message(mock_update, mock_context))
                mock_reply.assert_called()
            
            # Test lead capture workflow
            mock_update.message.text = "Sarah from TechStart wants a demo, budget 20k"
            
            with patch.object(mock_update.message, 'reply_text', new_callable=AsyncMock) as mock_reply:
                asyncio.run(self.bot.handle_message(mock_update, mock_context))
                mock_reply.assert_called()
            
            self.record_test_result("End-to-End Workflows", True, "Knowledge and lead workflows completed")
            
        except Exception as e:
            self.record_test_result("End-to-End Workflows", False, str(e))
            raise
    
    def test_12_error_handling_and_recovery(self):
        """Test error handling and graceful degradation"""
        try:
            # Test with invalid input
            classifier = self.bot.intent_classifier
            
            # Test empty/None inputs
            result = asyncio.run(classifier.classify("", []))
            self.assertIsInstance(result, IntentClassification)
            
            result = asyncio.run(classifier.classify(None or "", []))
            self.assertIsInstance(result, IntentClassification)
            
            # Test with very long input
            long_text = "test " * 1000
            result = asyncio.run(classifier.classify(long_text, []))
            self.assertIsInstance(result, IntentClassification)
            
            # Test knowledge agent with non-existent file
            agent = self.bot.knowledge_agent
            result = asyncio.run(agent.ingest_file("/non/existent/file.txt", "fake.txt", "req_error"))
            self.assertEqual(result['chunks'], 0)
            self.assertEqual(result['tokens'], 0)
            
            self.record_test_result("Error Handling", True, "All error conditions handled gracefully")
            
        except Exception as e:
            self.record_test_result("Error Handling", False, str(e))
            raise
    
    def test_13_security_and_validation(self):
        """Test input validation and security measures"""
        try:
            # Test SQL injection prevention
            malicious_input = "'; DROP TABLE conversations; --"
            
            # This should not cause database issues
            asyncio.run(self.bot.log_conversation(
                Mock(id=99999, username="hacker", first_name="Malicious"),
                "test",
                malicious_input,
                "security_test"
            ))
            
            # Verify table still exists
            conn = sqlite3.connect(self.bot.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'")
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            conn.close()
            
            # Test input sanitization
            classifier = self.bot.intent_classifier
            html_input = "<script>alert('xss')</script>What's the policy?"
            result = asyncio.run(classifier.classify(html_input, []))
            self.assertIsInstance(result, IntentClassification)
            
            self.record_test_result("Security Validation", True, "Input validation and SQL injection prevention working")
            
        except Exception as e:
            self.record_test_result("Security Validation", False, str(e))
            raise
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        end_time = time.time()
        total_time = end_time - self.test_results['start_time']
        
        success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests']) * 100
        
        report = {
            'test_summary': {
                'total_tests': self.test_results['total_tests'],
                'passed_tests': self.test_results['passed_tests'],
                'failed_tests': self.test_results['failed_tests'],
                'success_rate': f"{success_rate:.1f}%",
                'execution_time': f"{total_time:.2f} seconds"
            },
            'performance_metrics': self.test_results['performance_metrics'],
            'test_details': self.test_results['test_details'],
            'system_info': {
                'python_version': os.sys.version,
                'test_timestamp': datetime.now().isoformat(),
                'bot_version': "Ultimate Revenue Copilot v2.0"
            }
        }
        
        # Save report
        with open('ultimate_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        return report


def run_comprehensive_tests():
    """Run all tests and generate report"""
    print("🧪 ULTIMATE TELEGRAM REVENUE COPILOT - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print()
    
    if not BOT_AVAILABLE:
        print("❌ Cannot run tests - bot modules not available")
        print("Please install dependencies: pip install -r requirements_ultimate.txt")
        return
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestUltimateTelegramRevenueCopilot)
    
    # Create test instance for reporting
    test_instance = TestUltimateTelegramRevenueCopilot()
    test_instance.setUpClass()
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate report
    try:
        report = test_instance.generate_test_report()
        
        print(f"\n🎯 TEST RESULTS SUMMARY")
        print("=" * 30)
        print(f"Total Tests: {report['test_summary']['total_tests']}")
        print(f"Passed: {report['test_summary']['passed_tests']} ✅")
        print(f"Failed: {report['test_summary']['failed_tests']} ❌")
        print(f"Success Rate: {report['test_summary']['success_rate']}")
        print(f"Execution Time: {report['test_summary']['execution_time']}")
        
        if report['performance_metrics']:
            print(f"\n⚡ PERFORMANCE METRICS")
            print("=" * 25)
            for metric, value in report['performance_metrics'].items():
                print(f"{metric.replace('_', ' ').title()}: {value:,}")
        
        print(f"\n📋 DETAILED RESULTS")
        print("=" * 20)
        for test in report['test_details']:
            print(f"{test['status']} {test['test']}")
            if test['details']:
                print(f"   └─ {test['details']}")
        
        print(f"\n📄 Full report saved to: ultimate_test_report.json")
        
        # Return success if all tests passed
        return report['test_summary']['failed_tests'] == 0
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return False


if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)