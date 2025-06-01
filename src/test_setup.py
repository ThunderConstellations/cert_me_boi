import asyncio
import os
from src.automation.browser import BrowserAutomation
from src.monitor.screen_monitor import ScreenMonitor
from src.ai.model_handler import AIHandler
from src.utils.logger import ComponentLogger

async def test_browser():
    """Test browser automation"""
    print("\nTesting Browser Automation...")
    browser = BrowserAutomation()
    try:
        if await browser.initialize():
            print("✓ Browser initialization successful")
            await browser.navigate("https://www.example.com")
            print("✓ Navigation successful")
        else:
            print("✗ Browser initialization failed")
    except Exception as e:
        print(f"✗ Browser test failed: {str(e)}")
    finally:
        await browser.close()

def test_screen_monitor():
    """Test screen monitoring"""
    print("\nTesting Screen Monitor...")
    monitor = ScreenMonitor()
    try:
        monitor.start_monitoring()
        print("✓ Screen monitor started")
        # Wait for a few seconds to test monitoring
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(3))
        monitor.stop_monitoring()
        print("✓ Screen monitor stopped")
    except Exception as e:
        print(f"✗ Screen monitor test failed: {str(e)}")

async def test_ai():
    """Test AI handler"""
    print("\nTesting AI Handler...")
    ai = AIHandler()
    try:
        test_question = "What is the capital of France?"
        answer = await ai.generate_answer(test_question)
        if answer:
            print("✓ AI answer generation successful")
        else:
            print("✗ AI answer generation failed")
    except Exception as e:
        print(f"✗ AI test failed: {str(e)}")

def test_logger():
    """Test logging system"""
    print("\nTesting Logger...")
    try:
        logger = ComponentLogger("test")
        logger.info("Test log message")
        log_file = os.path.join("logs", "test.log")
        if os.path.exists(log_file):
            print("✓ Logger test successful")
        else:
            print("✗ Logger test failed - log file not created")
    except Exception as e:
        print(f"✗ Logger test failed: {str(e)}")

async def main():
    """Run all tests"""
    print("Starting Environment Tests...")
    
    # Test logger first as other components depend on it
    test_logger()
    
    # Test browser automation
    await test_browser()
    
    # Test screen monitor
    test_screen_monitor()
    
    # Test AI handler
    await test_ai()
    
    print("\nTests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 