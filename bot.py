"""
Teams Bot handler.

Receives activity from Teams, runs the Claude agent, and replies.
Maintains per-conversation history (in-memory; swap for Redis/DB in production).
"""
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount

import agent


# Simple in-memory history store keyed by conversation ID.
# For production, replace with a persistent store (Redis, CosmosDB, etc.)
_conversation_history: dict[str, list[dict]] = {}
MAX_HISTORY_TURNS = 10  # keep last N user+assistant pairs


class PipelineBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        user_text = turn_context.activity.text or ""
        conversation_id = turn_context.activity.conversation.id

        # Show a typing indicator while the agent works
        await turn_context.send_activity(
            _typing_activity(turn_context)
        )

        history = _conversation_history.get(conversation_id, [])

        try:
            response_text = await agent.run_agent(user_text, history)
        except Exception as exc:
            response_text = f"⚠️ An error occurred: {exc}"

        # Update history (keep it bounded)
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": response_text})
        if len(history) > MAX_HISTORY_TURNS * 2:
            history = history[-(MAX_HISTORY_TURNS * 2):]
        _conversation_history[conversation_id] = history

        await turn_context.send_activity(response_text)

    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    "👋 Hi! I'm your **Azure DevOps Pipeline Assistant**.\n\n"
                    "I can help you:\n"
                    "- 📋 **List** available pipelines\n"
                    "- 🚀 **Trigger** pipelines (with or without parameters)\n"
                    "- 🔍 **Check** the status of a run\n"
                    "- 📜 **View** recent run history\n\n"
                    "Try asking: *\"Show me all pipelines\"* or "
                    "*\"Run the deploy-staging pipeline on branch feature/my-branch\"*"
                )


def _typing_activity(turn_context: TurnContext):
    from botbuilder.schema import Activity, ActivityTypes
    activity = Activity(type=ActivityTypes.typing)
    activity.relates_to = turn_context.activity.relates_to
    return activity
