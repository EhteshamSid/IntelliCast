import asyncio
import json
from typing import List, Dict, Any
from politics_bot import PoliticsChatbotSimple

class PoliticsChatbotCLI:
    """CLI interface for the politics chatbot - handles user interaction"""
    
    def __init__(self):
        # Initialize the chatbot instance
        self.chatbot = PoliticsChatbotSimple()
        # Keep track of conversation history
        self.conversation_history: List[Dict[str, Any]] = []
        
    async def start_chat(self):
        """Main chat loop - handles user input and responses"""
        print("🤖 Welcome to the Politics Chatbot!")
        print("=" * 50)
        print("I'm designed to help you with political information and current events.")
        print("I will provide balanced perspectives, proper citations, and refuse non-political requests.")
        print("Type 'quit' to exit, 'history' to see conversation history, 'summary' for stats.")
        print("=" * 50)
        
        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()
                
                # Handle exit commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Thanks for chatting! Goodbye!")
                    break
                    
                # Handle special commands
                elif user_input.lower() == 'history':
                    self._show_history()
                    continue
                    
                elif user_input.lower() == 'summary':
                    self._show_summary()
                    continue
                    
                elif not user_input:
                    print("Please enter a message.")
                    continue
                
                # Process the message through the chatbot
                print("🤔 Thinking...")
                result = await self.chatbot.chat(user_input, self.conversation_history)
                
                # Store in conversation history
                self.conversation_history.append({
                    "message": user_input,
                    "response": result["response"],
                    "is_political": result["is_political"],
                    "timestamp": result["timestamp"]
                })
                
                # Display the response
                print(f"\n🤖 Bot: {result['response']}")
                
                # Show additional info for political queries
                if result["is_political"]:
                    print(f"\n📊 Confidence Score: {result['confidence_score']}/10")
                    
                    # Check for bias warnings
                    if result.get("bias_analysis", {}).get("has_bias"):
                        print("⚠️  Bias detected in response")
                    
                    # Check citation status
                    if result.get("citation_analysis", {}).get("has_citations"):
                        print("✅ Response includes citations")
                    else:
                        print("⚠️  Response may need more citations")
                
            except KeyboardInterrupt:
                print("\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                print("Please try again.")
    
    def _show_history(self):
        """Display conversation history to user"""
        if not self.conversation_history:
            print("No conversation history yet.")
            return
            
        print("\n📚 Conversation History:")
        print("-" * 30)
        for i, entry in enumerate(self.conversation_history, 1):
            # Show truncated messages for readability
            user_msg = entry['message'][:50] + "..." if len(entry['message']) > 50 else entry['message']
            bot_msg = entry['response'][:50] + "..." if len(entry['response']) > 50 else entry['response']
            
            print(f"{i}. You: {user_msg}")
            print(f"   Bot: {bot_msg}")
            print(f"   Political: {entry['is_political']}")
            print()
    
    def _show_summary(self):
        """Show conversation statistics"""
        if not self.conversation_history:
            print("No conversation history yet.")
            return
            
        summary = self.chatbot.get_conversation_summary(self.conversation_history)
        print("\n📈 Conversation Summary:")
        print("-" * 30)
        print(f"Total queries: {summary['total_queries']}")
        print(f"Political queries: {summary['political_queries']}")
        print(f"Non-political queries: {summary['non_political_queries']}")
        print(f"Political percentage: {summary['political_percentage']:.1f}%")

async def main():
    """Entry point for the application"""
    cli = PoliticsChatbotCLI()
    await cli.start_chat()

if __name__ == "__main__":
    asyncio.run(main())