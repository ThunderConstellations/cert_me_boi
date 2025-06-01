"""Recovery management module"""

from typing import Dict, Any, Optional
import yaml
import time
from pathlib import Path
from .logger import logger, log_error_with_context
from .error_handler import ErrorHandler, AutomationError

class RecoveryManager:
    """Manages recovery operations for automation components"""

    def __init__(self, config_path: str = "config/error_handling.yaml"):
        self.config = self._load_config(config_path)
        self.error_handler = ErrorHandler(config_path)
        self.browser_instance = None
        self.monitor_instance = None
        self.ai_instance = None
        self.recovery_state = {
            'browser': {'attempts': 0, 'last_error': None},
            'monitor': {'attempts': 0, 'last_error': None},
            'ai': {'attempts': 0, 'last_error': None}
        }

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load recovery configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            log_error_with_context(e, "Failed to load recovery config")
            return {
                'recovery': {
                    'max_attempts': 3,
                    'backoff_factor': 2.0,
                    'components': {
                        'browser': {
                            'actions': ['refresh', 'restart'],
                            'timeout': 30
                        },
                        'monitor': {
                            'actions': ['recapture', 'restart'],
                            'timeout': 10
                        },
                        'ai': {
                            'actions': ['retry', 'fallback'],
                            'timeout': 60
                        }
                    }
                }
            }

    def initialize(self, **instances) -> None:
        """Initialize with component instances"""
        if 'browser_instance' in instances:
            self.browser_instance = instances['browser_instance']
        if 'monitor_instance' in instances:
            self.monitor_instance = instances['monitor_instance']
        if 'ai_instance' in instances:
            self.ai_instance = instances['ai_instance']

    def handle_error(
        self,
        error: Exception,
        component: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Handle component error and attempt recovery"""
        try:
            # Update recovery state
            state = self.recovery_state[component]
            state['attempts'] += 1
            state['last_error'] = error

            # Check if recovery is possible
            if not self._can_recover(component):
                logger.error(
                    f"Recovery limit reached for {component}",
                    module="recovery",
                    attempts=state['attempts']
                )
                return False

            # Get recovery actions
            actions = self._get_recovery_actions(component, error)
            if not actions:
                logger.warning(
                    f"No recovery actions for {component}",
                    module="recovery",
                    error_type=type(error).__name__
                )
                return False

            # Execute recovery actions
            success = self._execute_recovery_actions(component, actions, context)
            if success:
                logger.info(
                    f"Recovery successful for {component}",
                    module="recovery",
                    actions=actions
                )
                return True

            logger.error(
                f"Recovery failed for {component}",
                module="recovery",
                actions=actions
            )
            return False
        except Exception as e:
            log_error_with_context(e, f"Error in recovery handler for {component}")
            return False

    def _can_recover(self, component: str) -> bool:
        """Check if recovery is possible"""
        state = self.recovery_state[component]
        max_attempts = self.config['recovery']['max_attempts']
        return state['attempts'] < max_attempts

    def _get_recovery_actions(
        self,
        component: str,
        error: Exception
    ) -> Optional[list]:
        """Get recovery actions for component and error"""
        try:
            component_config = self.config['recovery']['components'][component]
            error_type = type(error).__name__.lower()

            # Get specific actions for error type
            for condition in component_config.get('conditions', []):
                if error_type in condition['error_types']:
                    return condition['actions']

            # Return default actions
            return component_config.get('actions', [])
        except Exception:
            return None

    def _execute_recovery_actions(
        self,
        component: str,
        actions: list,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Execute recovery actions"""
        try:
            for action in actions:
                # Get action handler
                handler = getattr(self, f"_handle_{component}_{action}", None)
                if not handler:
                    logger.warning(
                        f"No handler for {action} in {component}",
                        module="recovery"
                    )
                    continue

                # Execute action
                if not handler(context):
                    return False

                # Wait between actions
                time.sleep(self.config['recovery']['backoff_factor'])

            return True
        except Exception as e:
            log_error_with_context(e, f"Failed to execute recovery actions for {component}")
            return False

    def _handle_browser_refresh(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Handle browser refresh action"""
        try:
            if self.browser_instance:
                self.browser_instance.refresh()
                return True
            return False
        except Exception as e:
            log_error_with_context(e, "Failed to refresh browser")
            return False

    def _handle_browser_restart(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Handle browser restart action"""
        try:
            if self.browser_instance:
                self.browser_instance.cleanup()
                return self.browser_instance.start()
            return False
        except Exception as e:
            log_error_with_context(e, "Failed to restart browser")
            return False

    def _handle_monitor_recapture(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Handle monitor recapture action"""
        try:
            if self.monitor_instance:
                return self.monitor_instance.capture_screen() is not None
            return False
        except Exception as e:
            log_error_with_context(e, "Failed to recapture screen")
            return False

    def _handle_monitor_restart(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Handle monitor restart action"""
        try:
            if self.monitor_instance:
                self.monitor_instance.cleanup()
                self.monitor_instance.__init__()
                return True
            return False
        except Exception as e:
            log_error_with_context(e, "Failed to restart monitor")
            return False

    def _handle_ai_retry(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Handle AI retry action"""
        try:
            if self.ai_instance and context and 'operation' in context:
                operation = getattr(self.ai_instance, context['operation'], None)
                if operation:
                    return operation(*context.get('args', []), **context.get('kwargs', {}))
            return False
        except Exception as e:
            log_error_with_context(e, "Failed to retry AI operation")
            return False

    def _handle_ai_fallback(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Handle AI fallback action"""
        try:
            if self.ai_instance:
                self.ai_instance.cleanup()
                self.ai_instance.initialize_models()
                return True
            return False
        except Exception as e:
            log_error_with_context(e, "Failed to fallback AI")
            return False

    def reset_state(self, component: Optional[str] = None) -> None:
        """Reset recovery state"""
        if component:
            if component in self.recovery_state:
                self.recovery_state[component] = {
                    'attempts': 0,
                    'last_error': None
                }
        else:
            for component in self.recovery_state:
                self.recovery_state[component] = {
                    'attempts': 0,
                    'last_error': None
                }

    def get_state(self, component: Optional[str] = None) -> Dict[str, Any]:
        """Get recovery state"""
        if component:
            return self.recovery_state.get(component, {})
        return self.recovery_state

# Example usage:
if __name__ == "__main__":
    # Initialize recovery manager
    recovery_manager = RecoveryManager()
    
    # Mock browser instance
    class MockBrowser:
        def refresh(self):
            print("Refreshing page")
        
        def clear_cookies(self):
            print("Clearing cookies")
        
        def cleanup(self):
            print("Cleaning up browser")
        
        def start(self):
            print("Starting browser")
    
    # Initialize with mock instances
    recovery_manager.initialize(
        browser_instance=MockBrowser()
    )
    
    # Test error recovery
    try:
        raise AutomationError("Connection lost")
    except AutomationError as e:
        success = recovery_manager.handle_error(
            e,
            'browser',
            {'url': 'https://example.com'}
        )
        print(f"Recovery {'succeeded' if success else 'failed'}") 