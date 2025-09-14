#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE TEST SUITE
===========================
Complete testing for Ultimate Telegram Revenue Copilot
Tests all scenarios, edge cases, and performance metrics
"""

import unittest
import json
import time
import logging
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ultimate_bot import UltimateTelegramBot, UserSession, BotMetrics

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestUltimateTelegramBot(unittest.TestCase):
    """Comprehensive test suite for the Ultimate Telegram Bot"""
    
    def setUp(self):
        """Set up test environment"""
        self.bot_token = "test_token_123456"
        self.bot = UltimateTelegramBot(self.bot_token)
        
        # Mock user message
        self.test_message = {
            'message_id': 1,
            'chat': {'id': 12345, 'type': 'private'},
            'from': {'id': 67890, 'username': 'testuser'},
            'text': 'Hello',
            'date': int(time.time())
        }
        
        logger.info("🧪 Test environment initialized")
    
    def test_01_bot_initialization(self):
        """Test bot initialization and configuration"""
        logger.info("Testing bot initialization...")
        
        # Check bot attributes
        self.assertEqual(self.bot.token, self.bot_token)
        self.assertIsNotNone(self.bot.menus)
        self.assertIsNotNone(self.bot.knowledge_base)
        self.assertIsInstance(self.bot.metrics, BotMetrics)
        
        # Check menu structure
        self.assertIn("main", self.bot.menus)
        self.assertIn("revenue", self.bot.menus)
        self.assertIn("demo", self.bot.menus)
        
        # Check knowledge base
        self.assertIn("pricing", self.bot.knowledge_base)
        self.assertIn("features", self.bot.knowledge_base)
        self.assertIn("support", self.bot.knowledge_base)
        
        logger.info("✅ Bot initialization test passed")
    
    def test_02_user_session_management(self):
        """Test user session creation and management"""
        logger.info("Testing user session management...")
        
        # Test session creation
        session = self.bot.get_user_session(self.test_message)
        
        self.assertIsInstance(session, UserSession)
        self.assertEqual(session.chat_id, 12345)
        self.assertEqual(session.username, 'testuser')
        self.assertEqual(session.current_menu, "main")
        
        # Test session persistence
        session2 = self.bot.get_user_session(self.test_message)
        self.assertEqual(session.chat_id, session2.chat_id)
        
        # Check metrics update
        self.assertEqual(self.bot.metrics.total_users, 1)
        
        logger.info("✅ User session management test passed")
    
    def test_03_intent_classification(self):
        """Test advanced intent classification"""
        logger.info("Testing intent classification...")
        
        session = UserSession(chat_id=12345, username='testuser')
        
        test_cases = [
            ("hello", "greeting"),
            ("hi there", "greeting"),
            ("show me a demo", "demo_request"),
            ("what's your pricing", "pricing_inquiry"),
            ("what features do you have", "feature_question"),
            ("I need help", "support_request"),
            ("what's your refund policy", "refund_inquiry"),
            ("book a meeting", "booking"),
            ("contact info", "lead_info"),
            ("random text", "general_inquiry")
        ]
        
        for text, expected_intent in test_cases:
            intent, confidence, patterns = self.bot.classify_intent_advanced(text, session)
            self.assertEqual(intent, expected_intent, f"Failed for text: '{text}'")
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)
        
        logger.info("✅ Intent classification test passed")
    
    def test_04_keyboard_generation(self):
        """Test inline keyboard generation"""
        logger.info("Testing keyboard generation...")
        
        options = ["Option 1", "Option 2", "Option 3", "🔙 Back"]
        keyboard = self.bot.create_keyboard(options, columns=2)
        
        self.assertIn("inline_keyboard", keyboard)
        self.assertIsInstance(keyboard["inline_keyboard"], list)
        
        # Check structure
        rows = keyboard["inline_keyboard"]
        self.assertGreater(len(rows), 0)
        
        # Check button structure
        for row in rows:
            for button in row:
                self.assertIn("text", button)
                self.assertIn("callback_data", button)
        
        logger.info("✅ Keyboard generation test passed")
    
    def test_05_smart_response_generation(self):
        """Test smart response generation for all intents"""
        logger.info("Testing smart response generation...")
        
        session = UserSession(chat_id=12345, username='testuser')
        
        intents_to_test = [
            "greeting",
            "demo_request", 
            "pricing_inquiry",
            "feature_question",
            "support_request",
            "refund_inquiry",
            "lead_info",
            "booking",
            "general_inquiry"
        ]
        
        for intent in intents_to_test:
            response, keyboard = self.bot.generate_smart_response(
                f"test message for {intent}", intent, session
            )
            
            # Check response
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
            
            # Check keyboard
            self.assertIsInstance(keyboard, dict)
            self.assertIn("inline_keyboard", keyboard)
            
            # Check context update
            self.assertEqual(session.conversation_context, intent)
        
        logger.info("✅ Smart response generation test passed")
    
    def test_06_message_processing_workflow(self):
        """Test complete message processing workflow"""
        logger.info("Testing message processing workflow...")
        
        with patch.object(self.bot, 'send_message', return_value=True) as mock_send:
            # Test various message types
            test_messages = [
                "Hello there!",
                "I want to see a demo",
                "What are your prices?",
                "I need support",
                "Tell me about features"
            ]
            
            for msg_text in test_messages:
                test_msg = self.test_message.copy()
                test_msg['text'] = msg_text
                
                # Process message
                self.bot.process_message_enhanced(test_msg)
                
                # Verify send_message was called
                self.assertTrue(mock_send.called)
                mock_send.reset_mock()
        
        # Check metrics update
        self.assertGreater(self.bot.metrics.messages_processed, 0)
        
        logger.info("✅ Message processing workflow test passed")
    
    def test_07_callback_query_handling(self):
        """Test inline keyboard callback handling"""
        logger.info("Testing callback query handling...")
        
        # Create test session
        session = UserSession(chat_id=12345, username='testuser')
        self.bot.user_sessions[12345] = session
        
        # Test callback query
        callback_query = {
            'id': 'test_callback',
            'message': {
                'chat': {'id': 12345},
                'message_id': 123
            },
            'data': 'revenue_solutions'
        }
        
        with patch.object(self.bot, 'send_message', return_value=True) as mock_send:
            result = self.bot.handle_callback_query(callback_query)
            self.assertTrue(result)
            self.assertTrue(mock_send.called)
        
        logger.info("✅ Callback query handling test passed")
    
    def test_08_metrics_tracking(self):
        """Test comprehensive metrics tracking"""
        logger.info("Testing metrics tracking...")
        
        initial_metrics = BotMetrics()
        
        # Test metrics updates
        self.bot.update_metrics(0.5, True, "demo_request")
        self.bot.update_metrics(0.3, True, "lead_info")
        self.bot.update_metrics(0.7, False, "general_inquiry")
        
        # Check metrics
        self.assertEqual(self.bot.metrics.messages_processed, 3)
        self.assertEqual(self.bot.metrics.demos_scheduled, 1)
        self.assertEqual(self.bot.metrics.leads_captured, 1)
        self.assertLess(self.bot.metrics.success_rate, 100.0)  # Due to one failure
        
        logger.info("✅ Metrics tracking test passed")
    
    def test_09_error_handling(self):
        """Test error handling and recovery"""
        logger.info("Testing error handling...")
        
        # Test with invalid message format
        invalid_message = {"invalid": "format"}
        
        try:
            self.bot.process_message_enhanced(invalid_message)
            # Should not crash
        except Exception as e:
            self.fail(f"Bot should handle invalid messages gracefully: {e}")
        
        # Test with network errors
        with patch.object(self.bot, 'make_request', return_value=None):
            result = self.bot.send_message(12345, "test message")
            self.assertFalse(result)
        
        logger.info("✅ Error handling test passed")
    
    def test_10_performance_requirements(self):
        """Test performance requirements"""
        logger.info("Testing performance requirements...")
        
        session = UserSession(chat_id=12345, username='testuser')
        
        # Test response time
        start_time = time.time()
        response, keyboard = self.bot.generate_smart_response(
            "hello", "greeting", session
        )
        response_time = time.time() - start_time
        
        # Should respond in under 100ms for cached responses
        self.assertLess(response_time, 0.1, "Response generation too slow")
        
        # Test concurrent processing capability
        import threading
        
        def test_concurrent_processing():
            session = UserSession(chat_id=12345, username='testuser')
            response, keyboard = self.bot.generate_smart_response(
                "test", "greeting", session
            )
        
        threads = []
        for i in range(10):
            thread = threading.Thread(target=test_concurrent_processing)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        logger.info("✅ Performance requirements test passed")
    
    def test_11_edge_cases(self):
        """Test edge cases and boundary conditions"""
        logger.info("Testing edge cases...")
        
        session = UserSession(chat_id=12345, username='testuser')
        
        # Test empty message
        intent, confidence, patterns = self.bot.classify_intent_advanced("", session)
        self.assertEqual(intent, "general_inquiry")
        
        # Test very long message
        long_message = "a" * 5000
        intent, confidence, patterns = self.bot.classify_intent_advanced(long_message, session)
        self.assertIsNotNone(intent)
        
        # Test special characters
        special_message = "🚀💰📊🎯"
        intent, confidence, patterns = self.bot.classify_intent_advanced(special_message, session)
        self.assertIsNotNone(intent)
        
        # Test keyboard with many options
        many_options = [f"Option {i}" for i in range(20)]
        keyboard = self.bot.create_keyboard(many_options)
        self.assertIsInstance(keyboard, dict)
        
        logger.info("✅ Edge cases test passed")
    
    def test_12_knowledge_base_accuracy(self):
        """Test knowledge base content accuracy"""
        logger.info("Testing knowledge base accuracy...")
        
        # Check all knowledge base entries have required fields
        for category, content in self.bot.knowledge_base.items():
            self.assertIn("title", content)
            self.assertIn("content", content)
            self.assertIsInstance(content["content"], str)
            self.assertGreater(len(content["content"]), 50)  # Substantial content
        
        # Test pricing information is present
        pricing_content = self.bot.knowledge_base["pricing"]["content"]
        self.assertIn("$", pricing_content)  # Has pricing info
        self.assertIn("month", pricing_content)  # Has subscription terms
        
        logger.info("✅ Knowledge base accuracy test passed")

class TestIntegration(unittest.TestCase):
    """Integration tests for complete bot functionality"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.bot = UltimateTelegramBot("test_token")
        logger.info("🔗 Integration test environment initialized")
    
    def test_complete_conversation_flow(self):
        """Test complete conversation from greeting to conversion"""
        logger.info("Testing complete conversation flow...")
        
        with patch.object(self.bot, 'send_message', return_value=True):
            # Simulate complete user journey
            messages = [
                "Hello",  # Greeting
                "I want to see pricing",  # Pricing inquiry
                "Show me a demo",  # Demo request
                "I'm interested in the enterprise plan"  # Lead conversion
            ]
            
            for i, msg_text in enumerate(messages):
                test_message = {
                    'chat': {'id': 12345},
                    'from': {'username': 'testuser'},
                    'text': msg_text
                }
                
                self.bot.process_message_enhanced(test_message)
                
                # Verify session state updates
                session = self.bot.user_sessions.get(12345)
                self.assertIsNotNone(session)
        
        # Check final metrics
        self.assertGreater(self.bot.metrics.messages_processed, 0)
        
        logger.info("✅ Complete conversation flow test passed")

def run_performance_benchmark():
    """Run performance benchmark tests"""
    logger.info("🚀 Running performance benchmark...")
    
    bot = UltimateTelegramBot("test_token")
    
    # Benchmark response generation
    start_time = time.time()
    iterations = 1000
    
    session = UserSession(chat_id=12345, username='testuser')
    
    for i in range(iterations):
        response, keyboard = bot.generate_smart_response(
            "hello", "greeting", session
        )
    
    total_time = time.time() - start_time
    avg_time = total_time / iterations
    
    logger.info(f"📊 Performance Benchmark Results:")
    logger.info(f"   🔄 Iterations: {iterations}")
    logger.info(f"   ⏱️  Total time: {total_time:.2f}s")
    logger.info(f"   ⚡ Average response time: {avg_time*1000:.2f}ms")
    logger.info(f"   🎯 Responses per second: {iterations/total_time:.0f}")
    
    # Performance requirements
    assert avg_time < 0.01, f"Response time too slow: {avg_time:.3f}s"
    logger.info("✅ Performance benchmark passed!")

def generate_test_report():
    """Generate comprehensive test report"""
    logger.info("📋 Generating test report...")
    
    # Run all tests
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestUltimateTelegramBot)
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIntegration))
    
    # Custom test result collector
    class TestResultCollector(unittest.TextTestRunner):
        def __init__(self):
            super().__init__(verbosity=2)
            self.results = []
        
        def run(self, test):
            result = super().run(test)
            return result
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success_rate": ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
        "status": "PASSED" if result.wasSuccessful() else "FAILED"
    }
    
    # Save report
    with open('test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"📊 Test Report Generated:")
    logger.info(f"   ✅ Tests run: {report['total_tests']}")
    logger.info(f"   ❌ Failures: {report['failures']}")
    logger.info(f"   💥 Errors: {report['errors']}")
    logger.info(f"   📈 Success rate: {report['success_rate']:.1f}%")
    logger.info(f"   🎯 Status: {report['status']}")
    
    return report

if __name__ == "__main__":
    print("🧪 ULTIMATE TELEGRAM BOT - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print("🎯 Testing all functionality, performance, and edge cases")
    print("📊 Generating detailed test reports")
    print("⚡ Running performance benchmarks")
    print("=" * 60)
    
    try:
        # Run performance benchmark
        run_performance_benchmark()
        
        # Run comprehensive tests
        report = generate_test_report()
        
        print("\n🎉 ALL TESTS COMPLETED!")
        print(f"📊 Success Rate: {report['success_rate']:.1f}%")
        print(f"🎯 Status: {report['status']}")
        print("📋 Detailed report saved to test_report.json")
        
        if report['status'] == 'PASSED':
            print("✅ Bot is ready for production deployment!")
        else:
            print("❌ Some tests failed - review test_report.json for details")
            
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        sys.exit(1)