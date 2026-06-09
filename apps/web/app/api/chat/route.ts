import { a2a } from "a2a-ai-provider";
import { convertToModelMessages, streamText, type UIMessage } from "ai";

const agentCardUrl =
  process.env.ORCHESTRATOR_AGENT_CARD_URL ??
  "http://agentgateway:3002/.well-known/agent-card.json";

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = streamText({
    model: a2a(agentCardUrl),
    messages: await convertToModelMessages(messages),
    providerOptions: {
      a2a: {
        contextId: messages[0]?.id ?? crypto.randomUUID()
      }
    }
  });

  return result.toUIMessageStreamResponse();
}
